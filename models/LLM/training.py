import torch
from transformers import (
    AutoTokenizer, DataCollatorForLanguageModeling, AutoModelForCausalLM,
    BitsAndBytesConfig, TrainingArguments, Trainer
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
from prompt import qa_system_prompt

# Device setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Model setup
model_name = "Qwen/Qwen2-1.5B"
print(f"Using model: {model_name}")

# Load dataset
data_filename = "/home/yosakoi/Work/chatbot/model/LLM/data/sample_data.jsonl"
dataset = load_dataset("json", data_files=data_filename)
print(f"First sample of dataset: \n{dataset['train'][0]}")

# Split dataset
split_datasets = dataset["train"].train_test_split(test_size=0.1)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Formatting function
def formatting_prompts_func(examples):
    formatted_data = {"input_ids": [], "attention_mask": [], "labels": []}
    
    for i in range(len(examples['messages'])):     
        messages = examples['messages'][i]

        formatted_chat = tokenizer.apply_chat_template(messages, tokenize=False)
        
        encoding = tokenizer(
            formatted_chat, padding="max_length", truncation=True,
            max_length=240, return_tensors="pt"
        )
        
        formatted_data["input_ids"].append(encoding["input_ids"].squeeze(0).tolist())
        formatted_data["attention_mask"].append(encoding["attention_mask"].squeeze(0).tolist())
        formatted_data["labels"].append(encoding["input_ids"].squeeze(0).tolist())
    
    return formatted_data

# Tokenize dataset
tokenized_dataset = split_datasets.map(
    formatting_prompts_func, batched=True, remove_columns=['messages']
)

print(tokenized_dataset)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# Load model with quantization
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

model = AutoModelForCausalLM.from_pretrained(
    model_name, quantization_config=quantization_config, torch_dtype="auto"
)
model = prepare_model_for_kbit_training(model)
print(f"Model specification: \n{model}")


# LoRA configuration
lora_config = LoraConfig(
    r=16, lora_alpha=32, target_modules=["q_proj"],
    lora_dropout=0.05, task_type="CAUSAL_LM"
)

# Apply LoRA
model = get_peft_model(model, lora_config)
print("Number of trainable parameters:")
model.print_trainable_parameters()

# Training arguments
args = TrainingArguments(
    output_dir="/home/yosakoi/Work/chatbot/model/LLM/output",
    logging_dir="/home/yosakoi/Work/chatbot/log",
    num_train_epochs=5,
    learning_rate=5e-4,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=8,
    save_strategy="epoch",
    evaluation_strategy="steps",
    logging_steps=10,
    gradient_checkpointing=True,
    remove_unused_columns=False,
)

# Trainer setup
trainer = Trainer(
    model=model.to(device),
    args=args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
    data_collator=data_collator,
)

# Start training
trainer.train()