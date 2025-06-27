# backend/utils/intent_classifier.py

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os
import logging

logger = logging.getLogger("app.intent_classifier")

class IntentClassifier:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "..", "llm_models", "finetuned-model")

        print(f"Loading fine-tuned model from: {model_path}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        self.labels = list(self.model.config.id2label.values())
        


    def classify(self, text: str):
        """
        Classifies the intent of a given text using the fine-tuned BERT model.
        (This method requires no changes)
        """
        # Tokenize the input text
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)

        # Get model outputs (logits)
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Get the predicted class index by finding the max logit
        logits = outputs.logits
        predicted_class_idx = torch.argmax(logits, dim=1).item()

        # Return the corresponding label from the model's configuration
        intent = self.model.config.id2label[predicted_class_idx]
        logger.info(f"RECEVIED INTENT: {intent}")
        return intent
