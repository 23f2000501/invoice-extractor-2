from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import re
from dateutil import parser

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


def extract(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_number(patterns, text):
    value = extract(patterns, text)

    if value is None:
        return None

    value = value.replace(",", "")
    value = re.sub(r"[^\d.]", "", value)

    try:
        return float(value)
    except:
        return None


def parse_date(date_string):
    if date_string is None:
        return None

    try:
        return parser.parse(date_string).strftime("%Y-%m-%d")
    except:
        return None


@app.post("/extract")
def extract_invoice(req: InvoiceRequest):

    text = req.invoice_text

    invoice_no = extract([
        r"Invoice\s*(?:No|#)?\s*[:#]?\s*([A-Za-z0-9\-]+)"
    ], text)

    date = parse_date(
        extract([
            r"Date\s*:\s*(.+)",
        ], text)
    )

    vendor = extract([
        r"Vendor\s*:\s*(.+)",
        r"Seller\s*:\s*(.+)"
    ], text)

    amount = extract_number([
        r"Subtotal.*?([0-9,]+\.\d{2})"
    ], text)

    tax = extract_number([
        r"(?:GST|VAT).*?([0-9,]+\.\d{2})"
    ], text)

    currency = extract([
        r"Currency\s*:\s*([A-Z]{3})",
        r"\b(INR|USD|EUR|GBP)\b"
    ], text)

    return {
        "invoice_no": invoice_no,
        "date": date,
        "vendor": vendor,
        "amount": amount,
        "tax": tax,
        "currency": currency
    }