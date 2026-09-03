# pip install torch transformers

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "textattack/bert-base-uncased-SST-2"
LABELS = {
    0: "NEGATIVE",
    1: "POSITIVE",
}

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()


def classify(text):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    ).to(device)

    with torch.inference_mode():
        logits = model(**inputs).logits
        probabilities = torch.softmax(logits, dim=-1)[0]

    predicted_id = probabilities.argmax().item()

    return {
        "text": text,
        "label": LABELS[predicted_id],
        "confidence": probabilities[predicted_id].item(),
    }


if __name__ == "__main__":
    text = input("Enter text to classify: ")
    result = classify(text)

    print(f"Label: {result['label']}")
    print(f"Confidence: {result['confidence']:.2%}")