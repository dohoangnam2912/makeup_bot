"""
Langchain utilities for RAG implementation using Qdrant.
"""

import logging
from typing import Optional

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from entities import GenerationModelName
from prompt import contextualize_q_system_prompt, qa_system_prompt
from qdrant_utils import retriever, vectorstore

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
    llm = ChatGoogleGenerativeAI(model=model)
    
    # Create a history-aware retriever that uses chat history for context
    history_aware_retriever = create_history_aware_retriever(
        llm, 
        retriever, 
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
    
    logger.info("RAG chain created successfully")
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
    llm = ChatGoogleGenerativeAI(model=model)
    
    # Create a simple retriever with specified k value
    simple_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    
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