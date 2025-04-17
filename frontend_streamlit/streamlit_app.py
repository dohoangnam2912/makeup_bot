import streamlit as st
import logging
from sidebar import display_sidebar
from chat_interface import display_chat_interface

logger = logging.getLogger('streamlit_app')
logger.setLevel('DEBUG')
file_handler = logging.FileHandler('streamlit_app.log')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


st.title("Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []
    logger.info("Created messages")

if "session_id" not in st.session_state:
    st.session_state.session_id = None
    logger.info("Created session id")

display_sidebar()

display_chat_interface()