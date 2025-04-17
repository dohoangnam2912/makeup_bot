# What does a sidebar do? Upload document, list document, delete document
import streamlit as st
import logging
from api_utils import upload_document, list_documents, delete_document

logger = logging.getLogger('streamlit_app.sidebar')

def display_sidebar():
    # Model selection
    model_options = ["gemini-2.0-flash"]
    st.sidebar.selectbox("Select Model", options=model_options, key="model")
    
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "html"])
    if uploaded_file and st.sidebar.button("Upload"):
        with st.spinner("Uploading..."):
            upload_response = upload_document(uploaded_file)
            if upload_response:
                st.sidebar.success(f"File uploaded successfully with ID{upload_response["file_id"]}.")
                st.session_state.documents = list_documents()
            else:
                logger.warning("Failed to upload file.")

    st.sidebar.header("Uploaded Documents")

    if st.sidebar.button("Refresh documents list"):
        st.session_state.documents = list_documents()

    if "documents" in st.session_state and st.session_state.documents:
        for doc in st.session_state.documents:
            st.sidebar.text(f"{doc['file_name']}")
        selected_file_id = st.sidebar.selectbox(
            "Select a document to delete", 
            options=st.session_state.documents, 
            format_func=lambda doc: doc['file_name']
        )['id']

        if st.sidebar.button("Delete Selected Document"):
            delete_response = delete_document(selected_file_id)
            if delete_response:
                st.sidebar.success(f"Document deleted successfully.")
                st.session_state.documents = list_documents()
