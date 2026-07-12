from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceRequest(BaseModel):
    invoice_text: str


PROMPT = """
You are an invoice extraction engine.

Extract the invoice into EXACTLY this JSON.

{
  "invoice_no": null,
  "date": null,
  "vendor": null,
  "amount": null,
  "tax": null,
  "currency": null
}

Rules:

- Return ONLY JSON.
- No markdown.
- No explanation.
- invoice_no should contain only the invoice/reference number.
- date must be YYYY-MM-DD.
- amount is subtotal before tax.
- tax is only the tax amount.
- currency should be ISO code like INR, USD, EUR.
- If unavailable return null.
"""


@app.post("/extract")
def extract(req: InvoiceRequest):

    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=PROMPT + "\n\nInvoice:\n\n" + req.invoice_text,
    )

    text = response.text.strip()

    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return {
            "invoice_no": None,
            "date": None,
            "vendor": None,
            "amount": None,
            "tax": None,
            "currency": None,
        }

    return json.loads(text[start:end + 1])


@app.get("/")
def home():
    return {"status": "running"}