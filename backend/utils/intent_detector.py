from transformers import AutoTokenizer, AutoModelForSequenceClassification
from models.entities import IntentClassificationModel
import torch
import logging

logger = logging.getLogger("app.intent_detector")
model_path = IntentClassificationModel.BERT_BASE_FINETUNED

class IntentDetector:
    def __init__(self, model_name="google-bert/bert-base-multilingual-cased", device="cpu"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=6)  # placeholder
        self.device = device
        self.model.to(device)
        
        # Temporary mapping, need update after fine-tune
        self.id2label = {
            0: "chào hỏi",
            1: "nói chuyện phiếm",
            2: "câu hỏi chuyên môn",
            3: "cảm ơn",
            4: "phản hồi",
            5: "không liên quan"
        }

    def detect(self, text: str) -> str:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True).to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits
        predicted_class_id = logits.argmax().item()
        predicted_label = self.id2label.get(predicted_class_id, "other")
        logger.info(f"Detected intent: {predicted_label} for input: {text}")
        return predicted_label