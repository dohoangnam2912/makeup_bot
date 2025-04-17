"""
Langchain utilities for RAG implementation using Qdrant with support
for both Gemini API and self-hosted Hugging Face models, with Redis caching.
"""

import logging
import os
from typing import Optional

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

from entities import GenerationModelName
from prompt import contextualize_q_system_prompt, qa_system_prompt
from qdrant_utils import retriever, vectorstore
from redis_utils import test_redis_connection
from langchain_redis import get_redis_cached_llm, get_cached_retriever

# Configure logging
logger = logging.getLogger("app.langchain")

# Create prompt templates
contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "Question: {input}")
])

logger.info(f"Contextualize prompt: {contextualize_q_prompt} \n QA_prompt: {qa_prompt}")
# Check if Redis is available
USE_REDIS_CACHE = test_redis_connection()


def get_huggingface_llm(model_name_or_path, **kwargs):
    """
    Create a LangChain wrapper for a Hugging Face model.
    
    Args:
        model_name_or_path: Name or path of the model on Hugging Face or local path
        **kwargs: Additional arguments to pass to the model
        
    Returns:
        HuggingFacePipeline: LangChain compatible model
    """
    logger.info(f"Loading Hugging Face model: {model_name_or_path}")
    
    # Load the tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path, 
        torch_dtype="auto",
        device_map="auto",
        **kwargs
    )
    
    # Create a text generation pipeline
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        temperature=0.7,
        top_p=0.95,
        repetition_penalty=1.1
    )
    
    # Create a LangChain wrapper
    llm = HuggingFacePipeline(pipeline=pipe)
    
    logger.info(f"Hugging Face model {model_name_or_path} loaded successfully")
    return llm


def get_llm(model: str):
    """
    Get the appropriate LLM based on the model identifier.
    
    Args:
        model: Model name or path
        
    Returns:
        LLM: A LangChain compatible language model
    """
    if model.startswith("gemini"):
        logger.info(f"Using Google Gemini model: {model}")
        base_llm = ChatGoogleGenerativeAI(model=model)
    else:
        # For Hugging Face models or local paths
        model_path = os.environ.get("FINETUNED_MODEL_PATH", model)
        base_llm = get_huggingface_llm(model_path)
    
    # # Wrap with Redis caching if available 
    # if USE_REDIS_CACHE:
    #     logger.info("Using Redis cache for LLM")
    #     return get_redis_cached_llm(base_llm)
    # else:
    return base_llm


def get_rag_chain(model: str = GenerationModelName.GEMINI_2_FLASH):
    """
    Create and return a RAG chain using the specified LLM model.
    
    Args:
        model: Model name to use for generation
        
    Returns:
        Chain: A complete RAG chain for question answering
    """
    logger.info(f"Creating RAG chain with model: {model}")
    # Initialize the LLM
    llm = get_llm(model)
    # Get retriever with caching if Redis is available
    cached_retriever = retriever
    logger.info(f"Cached_retriever: {cached_retriever}")
    # Create a history-aware retriever that uses chat history for context
    history_aware_retriever = create_history_aware_retriever(
        llm, 
        cached_retriever, 
        contextualize_q_prompt
    )
    
    # Create a chain to process retrieved documents and generate an answer
    question_answer_chain = create_stuff_documents_chain(
        llm, 
        qa_prompt
    )
    # Combine the retriever and question answering components
    rag_chain = create_retrieval_chain(
        history_aware_retriever, 
        question_answer_chain
    )
    
    logger.info(f"Successfully created RAG chain with model: {model}")
    return rag_chain

def get_standalone_rag_chain(model: str = GenerationModelName.GEMINI_2_FLASH, k: int = 3):
    """
    Create a simplified RAG chain without history awareness.
    
    Args:
        model: Model name to use for generation
        k: Number of documents to retrieve
        
    Returns:
        Chain: A simplified RAG chain for direct question answering
    """
    logger.info(f"Creating standalone RAG chain with model: {model}")
    
    # Initialize the LLM
    llm = get_llm(model)
    
    # Create a simple retriever with specified k value
    simple_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    
    # Apply caching if Redis is available
    if USE_REDIS_CACHE:
        simple_retriever = get_cached_retriever(simple_retriever)
    
    # Create a simpler prompt template without chat history
    simple_qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        ("system", "Context: {context}"),
        ("human", "{input}")
    ])
    
    # Create the question answering chain
    simple_qa_chain = create_stuff_documents_chain(llm, simple_qa_prompt)
    
    # Create the retrieval chain
    simple_rag_chain = create_retrieval_chain(
        simple_retriever,
        simple_qa_chain
    )
    
    logger.info("Standalone RAG chain created successfully")
    return simple_rag_chain