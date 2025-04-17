import streamlit as st
import logging
from api_utils import get_api_response

logger = logging.getLogger("streamlit_app.chat_interface")

def display_chat_interface():
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
        
    # Handle new user input
    if prompt := st.chat_input("Ask anything"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            logger.info(f"Received message content {prompt}")

        # TODO This is crap
        with st.spinner("Generating response..."):
            response = get_api_response(prompt, st.session_state.session_id, st.session_state.model)
            logger.info(f"GET response {response}.")
            if response:
                st.session_state.session_id = response.get('session_id')
                st.session_state.messages.append({"role": "assistant", "content": response['response']})

                with st.chat_message("assistant"):
                    st.markdown(response['response'])
                
                with st.expander("Details"):
                    st.subheader("Generated response")
                    st.code(response['response'])
                    st.subheader("Model Used")
                    st.code(response['model'])
                    st.subheader("Session ID")
                    st.code(response['session_id'])
            else:
                logger.info("Failed to get a response from the API. Please try again")
                st.error('Failed to get a response from the API. Please try again')