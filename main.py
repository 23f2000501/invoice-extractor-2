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
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
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
    if not date_string:
        return None

    try:
        return parser.parse(date_string, dayfirst=True).strftime("%Y-%m-%d")
    except:
        try:
            return parser.parse(date_string).strftime("%Y-%m-%d")
        except:
            return None


@app.post("/extract")
def extract_invoice(req: InvoiceRequest):

    text = req.invoice_text

    invoice_no = None

    invoice_patterns = [
        r"Invoice\s+Reference\s*[:#-]?\s*([A-Za-z0-9\-_\/]+)",
        r"Invoice\s+Ref\s*[:#-]?\s*([A-Za-z0-9\-_\/]+)",
        r"Invoice\s+Number\s*[:#-]?\s*([A-Za-z0-9\-_\/]+)",
        r"Invoice\s+No\.?\s*[:#-]?\s*([A-Za-z0-9\-_\/]+)",
        r"Invoice\s*#\s*[:#-]?\s*([A-Za-z0-9\-_\/]+)",
        r"Reference\s*[:#-]?\s*([A-Za-z0-9\-_\/]+)",
        r"Ref\.?\s*[:#-]?\s*([A-Za-z0-9\-_\/]+)",
        r"Document\s+(?:No|Number)\s*[:#-]?\s*([A-Za-z0-9\-_\/]+)"
    ]

    for pattern in invoice_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            invoice_no = m.group(1).strip()
            break

        date = parse_date(
            extract([
                r"Date\s*[:\-]\s*(.+)",
                r"Invoice Date\s*[:\-]\s*(.+)",
                r"Issue Date\s*[:\-]\s*(.+)"
            ], text)
        )

    vendor = extract([
        r"Vendor\s*[:\-]\s*(.+)",
        r"Seller\s*[:\-]\s*(.+)",
        r"Supplier\s*[:\-]\s*(.+)",
        r"From\s*[:\-]\s*(.+)",
        r"Company\s*[:\-]\s*(.+)"
    ], text)

    amount = extract_number([
        r"Subtotal\s*[:\-]?\s*.*?([0-9][0-9,]*\.\d{2})",
        r"Sub\s*Total\s*[:\-]?\s*.*?([0-9][0-9,]*\.\d{2})",
        r"Amount Before Tax\s*[:\-]?\s*.*?([0-9][0-9,]*\.\d{2})",
        r"Net Amount\s*[:\-]?\s*.*?([0-9][0-9,]*\.\d{2})"
    ], text)

    tax = extract_number([
        r"GST.*?([0-9][0-9,]*\.\d{2})",
        r"VAT.*?([0-9][0-9,]*\.\d{2})",
        r"Tax.*?([0-9][0-9,]*\.\d{2})",
        r"CGST.*?([0-9][0-9,]*\.\d{2})",
        r"SGST.*?([0-9][0-9,]*\.\d{2})",
        r"IGST.*?([0-9][0-9,]*\.\d{2})"
    ], text)

    currency = extract([
        r"Currency\s*[:\-]\s*([A-Z]{3})",
        r"\b(INR|USD|EUR|GBP|AED|AUD|CAD|JPY|CNY|SGD)\b"
    ], text)

    return {
        "invoice_no": invoice_no,
        "date": date,
        "vendor": vendor,
        "amount": amount,
        "tax": tax,
        "currency": currency
    }