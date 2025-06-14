import uuid
import logging
import requests
import json
from models.entities import QueryInput, QueryResponse
from dotenv import load_dotenv
import os

load_dotenv()

DIFY_API_BASE_URL = os.getenv("DIFY_API_BASE_URL", "http://localhost:80")
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_CHAT_ENDPOINT = f"{DIFY_API_BASE_URL}/v1/chat-messages"

logger = logging.getLogger("app.chat_controller")

if not DIFY_API_KEY:
    logger.error("DIFY_API_KEY is not set. Please configure it in your environment.")

def handle_chat(query_input: QueryInput) -> QueryResponse:
    logger.info(f"handle_chat received query: {query_input.question} for session: {query_input.session_id}")
    session_id = query_input.session_id or str(uuid.uuid4())
    query = query_input.question
    
    # Default answer in case of any failure
    answer_text = "Sorry, I encountered an error while processing your request."
    response_type = None  # Default type
    dify_request_successful = False

    if not DIFY_API_KEY:
        answer_text = "AI service is not configured (API key missing)."
        return QueryResponse(
            response=answer_text,
            session_id=session_id,
            query=query,
            type=response_type
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DIFY_API_KEY}"
    }

    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "user": session_id,
    }

    try:
        logger.debug(f"Sending request to Dify: {DIFY_CHAT_ENDPOINT} with payload: {payload}")
        response = requests.post(DIFY_CHAT_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        dify_response_data = response.json()
        logger.debug(f"Dify raw response data: {dify_response_data}")

        # Get the answer, which contains the JSON string with type and response
        answer = dify_response_data.get("answer")
        
        if answer is None:
            dify_error = dify_response_data.get("error", {}).get("message") or dify_response_data.get("message")
            if dify_error:
                logger.error(f"Dify API returned an error: {dify_error} - Full Dify Response: {dify_response_data}")
                answer_text = f"AI service error: {dify_error}"
            elif "status" in dify_response_data and dify_response_data["status"] != 200 and dify_response_data["status"] != "succeeded":
                logger.error(f"Dify API indicated failure: {dify_response_data}")
                answer_text = "AI service failed to process the request."
            else:
                logger.warning("Dify response did not contain an 'answer' key and no clear error message. Using fallback.")
                answer_text = "Sorry, I received a response, but it was not in the expected format."
        else:
            try:
                # Preprocess the answer to remove markdown code block markers
                cleaned_answer = answer.strip()
                if cleaned_answer.startswith("```json"):
                    cleaned_answer = cleaned_answer.replace("```json", "").replace("```", "").strip()
                
                # Parse the JSON string
                parsed_answer = json.loads(cleaned_answer)
                
                # Extract type and response
                answer_text = parsed_answer.get("response", "No response provided in the answer.")
                response_type = parsed_answer.get("type")
                
                dify_request_successful = True
                logger.info(f"Successfully parsed Dify answer: response='{answer_text[:100]}...', type='{response_type}'")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Dify answer as JSON: {answer} - Error: {e}")
                answer_text = "Sorry, the AI response was not in the expected JSON format."
            except Exception as e:
                logger.error(f"Error processing Dify answer: {e}")
                answer_text = "Sorry, an error occurred while processing the AI response."

    except requests.exceptions.Timeout:
        logger.error(f"Request to Dify timed out for query: {query}")
        answer_text = "Sorry, the request to the AI service timed out."
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to Dify at {DIFY_CHAT_ENDPOINT}. Is Dify running and accessible?")
        answer_text = "Sorry, I could not connect to the AI service. Please check if Dify is running."
    except requests.exceptions.HTTPError as e:
        logger.error(f"Dify API HTTP error: {e.response.status_code} - {e.response.text}")
        try:
            error_details = e.response.json()
            msg = error_details.get("message", e.response.text)
            answer_text = f"AI service error ({e.response.status_code}): {msg}"
        except ValueError:
            answer_text = f"AI service error ({e.response.status_code}): {e.response.text}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Dify API request error: {e}")
        answer_text = f"Sorry, there was an issue communicating with the AI service: {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred during Dify interaction: {e}", exc_info=True)
        answer_text = "An unexpected error occurred while I was trying to get an answer."

    # Ensure answer_text is always a string
    if answer_text is None:
        logger.error("Critical: answer_text became None despite checks. Fallback to generic error.")
        answer_text = "A critical error occurred, and the answer could not be determined."

    logger.info(f"Returning QueryResponse: response='{answer_text[:100]}...', session_id='{session_id}', type='{response_type}'")
    
    return QueryResponse(
        response=answer_text,
        session_id=session_id,
        query=query,
        type=response_type
    )