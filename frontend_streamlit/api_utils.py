import requests
import streamlit as st
import logging
import json
from datetime import datetime

logger = logging.getLogger("streamlit_app.api_utils")

def serialize_datetime(obj): 
    if isinstance(obj, datetime): 
        return obj.isoformat() 
    raise TypeError("Type not serializable") 

def get_api_response(question, session_id, model):
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = {"question": question, "model": model}
    if session_id:
        data["session_id"] = session_id
    logger.info(f"GETTING api response with {data}")
    try:
        response = requests.post("http://localhost:8000/chat", headers=headers, json=data)
        if response.status_code == 200:
            logger.info("Got the response")
            return response.json()
        else:
            logger.warning(f"API request failed with status code {response.status_code}: {response.text}")
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.warning(f"An error occurred: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        return None

def upload_document(file):
    try:
        logger.info(f"Uploading document with file {file.name} - {file.type}")

        files = {"file": (file.name, file, file.type)}
        response = requests.post("http://localhost:8000/upload-doc", files=files)
        if response.status_code == 200:
            logger.info(f"DONE uploading file {file.name}")
            return response.json()
        else:
            st.error(f"An error occurred while uploading the file. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {str(e)}")
        return None

def list_documents():
    logger.info(f"Listing documents")
    try:
        response = requests.get("http://localhost:8000/list-docs")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch document list. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching the document list: {str(e)}")
        return []

def delete_document(file_id):
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = {"file_id": file_id}

    try:
        response = requests.post("http://localhost:8000/delete-doc", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete document. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while deleting the document: {str(e)}")
        return None