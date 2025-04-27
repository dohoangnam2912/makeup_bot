"""
Langchain utilities for RAG implementation using Qdrant with support
for both Gemini API and self-hosted Hugging Face models, with Redis caching.
"""

import logging
import os
from typing import Optional, Tuple

from langchain.chains import create_history_aware_retriever, create_retrieval_chain, LLMChain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

from models.entities import GenerationModelName
from .qdrant_utils import retriever, vectorstore
from .redis_utils import test_redis_connection
from .langchain_redis import get_redis_cached_llm, get_cached_retriever
from .intent_detector import IntentDetector
from prompt import (
    rewriting_prompt,
    contextualize_q_system_prompt,
    qa_system_prompt,
    greeting_system_prompt,
    thank_you_system_prompt,
    smalltalk_system_prompt,
    feedback_system_prompt,
    fallback_system_prompt
)

# Configure logging
logger = logging.getLogger("app.langchain")

# Intent detector
intent_detector = IntentDetector()

def select_prompt_by_intent(intent: str) -> Tuple[ChatPromptTemplate, bool]:
    """
    Select the appropriate prompt template based on detected intent.
    Returns (prompt_template, requires_context)
    """
    if intent == "greeting":
        logger.info("Selected greeting prompt")
        return ChatPromptTemplate.from_messages([
            ("system", greeting_system_prompt),
            ("human", "{input}")
        ]), False
    elif intent == "thank_you":
        logger.info("Selected thank you prompt")
        return ChatPromptTemplate.from_messages([
            ("system", thank_you_system_prompt),
            ("human", "{input}")
        ]), False
    elif intent == "smalltalk":
        logger.info("Selected small talk prompt")
        return ChatPromptTemplate.from_messages([
            ("system", smalltalk_system_prompt),
            ("human", "{input}")
        ]), False
    elif intent == "technical_question":
        logger.info("Selected technical QA prompt")
        return ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            ("system", "Context: {context}"),
            ("human", "{input}")
        ]), True
    elif intent == "feedback":
        logger.info("Selected feedback prompt")
        return ChatPromptTemplate.from_messages([
            ("system", feedback_system_prompt),
            ("human", "{input}")
        ]), False
    else:
        logger.info("Selected fallback prompt")
        return ChatPromptTemplate.from_messages([
            ("system", fallback_system_prompt),
            ("human", "{input}")
        ]), False

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
    """
    logger.info(f"Loading Hugging Face model: {model_name_or_path}")

    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype="auto",
        device_map="auto",
        **kwargs
    )

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        temperature=0.7,
        top_p=0.95,
        repetition_penalty=1.1
    )

    llm = HuggingFacePipeline(pipeline=pipe)

    logger.info(f"Hugging Face model {model_name_or_path} loaded successfully")
    return llm

def get_llm(model: str):
    """
    Get the appropriate LLM based on the model identifier.
    """
    if model.startswith("gemini"):
        logger.info(f"Using Google Gemini model: {model}")
        base_llm = ChatGoogleGenerativeAI(model=model)
    else:
        model_path = os.environ.get("FINETUNED_MODEL_PATH", model)
        base_llm = get_huggingface_llm(model_path)

    return base_llm

def rewrite_prompt_with_llm(model: str, user_input: str) -> str:
    """
    Rewrite the user's input prompt using LLM (Language Model) for clarity or correction.
    
    Args:
        user_input: The original query/question from the user.
        model: The model being used to rewrite the prompt.
        
    Returns:
        str: The rewritten prompt.
    """
    # Create the LLM chain for rewriting
    logger.info(f"Using {model} to rewrite prompt")
    llm = get_llm(model)
    prompt_for_rewriting = f"System: {rewriting_prompt}. User: {user_input}"
    logger.info(f'Prompt for rewritin: {prompt_for_rewriting}')
    # Use the LLM to generate the rewritten question
    rewritten_prompt = llm.invoke(prompt_for_rewriting)
    
    logger.info(f"Rewritten prompt: {rewritten_prompt}")
    
    return rewritten_prompt.content

def get_rag_chain(model: str = GenerationModelName.GEMINI_2_FLASH, user_input: Optional[str] = None):
    """
    Create RAG chain depending on detected intent.
    """
    logger.info(f"Creating RAG chain with model: {model}, user_input: {user_input}")
    llm = get_llm(model)

    if user_input:
        intent = intent_detector.detect(user_input)
        selected_prompt, requires_context = select_prompt_by_intent(intent)
        logger.info(f"Detected intent: {intent} | Requires context: {requires_context}")
    else:
        selected_prompt, requires_context = qa_prompt, True

    if requires_context:
        cached_retriever = retriever
        if USE_REDIS_CACHE:
            cached_retriever = get_cached_retriever(cached_retriever)

        history_aware_retriever = create_history_aware_retriever(
            llm,
            cached_retriever,
            contextualize_q_prompt
        )

        question_answer_chain = create_stuff_documents_chain(
            llm,
            selected_prompt
        )

        rag_chain = create_retrieval_chain(
            history_aware_retriever,
            question_answer_chain
        )
    else:
        rag_chain = LLMChain(
            llm=llm,
            prompt=selected_prompt
        )

    logger.info(f"Successfully created chain with model: {model}")
    return rag_chain

def get_standalone_rag_chain(model: str = GenerationModelName.GEMINI_2_FLASH, k: int = 3, user_input: Optional[str] = None):
    """
    Create a standalone RAG chain depending on detected intent.
    """
    logger.info(f"Creating standalone RAG chain with model: {model}, user_input: {user_input}")
    llm = get_llm(model)

    if user_input:
        intent = intent_detector.detect(user_input)
        selected_prompt, requires_context = select_prompt_by_intent(intent)
        logger.info(f"Detected intent: {intent} | Requires context: {requires_context}")
    else:
        selected_prompt, requires_context = qa_prompt, True

    if requires_context:
        simple_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        if USE_REDIS_CACHE:
            simple_retriever = get_cached_retriever(simple_retriever)

        simple_qa_chain = create_stuff_documents_chain(
            llm,
            selected_prompt
        )

        simple_rag_chain = create_retrieval_chain(
            simple_retriever,
            simple_qa_chain
        )

        return simple_rag_chain
    else:
        simple_chain = LLMChain(
            llm=llm,
            prompt=selected_prompt
        )
        return simple_chain
