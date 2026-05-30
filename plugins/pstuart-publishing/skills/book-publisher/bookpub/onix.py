"""bookpub.onix — ONIX 3.0 metadata export for distributors.

IngramSpark, Apple Books, and aggregators ingest ONIX. The forked pipeline had no
metadata feed at all. This emits a well-formed ONIX 3.0 reference message (one
Product per format that has an ISBN) from the same ``book.toml`` the engines read,
so store metadata cannot drift from the books.

Scope: the core, widely-required fields (identifiers, title, contributors, language,
BISAC subjects, description, publisher, price). It is well-formed XML; validate
against the ONIX 3.0 schema with ``onixcheck`` before submission.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.dom import minidom

from bookpub.config import isbn_for

# ONIX product-form codes
_FORM = {"paperback": "BC", "hardcover": "BB", "ebook": "EB"}
_PRODUCT_FORM_DETAIL = {"ebook": "E101"}  # EPUB


def _sub(parent, tag, text=None):
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = str(text)
    return el


def _product(message, cfg: dict, fmt: str, isbn: str, seq: int) -> None:
    p = _sub(message, "Product")
    _sub(p, "RecordReference", f"{cfg.get('slug', 'book')}-{fmt}")
    _sub(p, "NotificationType", "03")  # confirmed
    pid = _sub(p, "ProductIdentifier")
    _sub(pid, "ProductIDType", "15")   # ISBN-13
    _sub(pid, "IDValue", isbn.replace("-", "").replace(" ", ""))

    desc = _sub(p, "DescriptiveDetail")
    _sub(desc, "ProductComposition", "00")
    _sub(desc, "ProductForm", _FORM.get(fmt, "BC"))
    if fmt in _PRODUCT_FORM_DETAIL:
        _sub(desc, "ProductFormDetail", _PRODUCT_FORM_DETAIL[fmt])

    title = _sub(desc, "TitleDetail")
    _sub(title, "TitleType", "01")
    te = _sub(title, "TitleElement")
    _sub(te, "TitleElementLevel", "01")
    _sub(te, "TitleText", cfg["title"])
    if cfg.get("subtitle"):
        _sub(te, "Subtitle", cfg["subtitle"])

    contributors = cfg.get("contributors") or [{"name": cfg["author"], "role": "A01"}]
    for i, c in enumerate(contributors, 1):
        con = _sub(desc, "Contributor")
        _sub(con, "SequenceNumber", i)
        _sub(con, "ContributorRole", c.get("role", "A01"))
        _sub(con, "PersonName", c.get("name", cfg["author"]))

    _sub(desc, "Language")  # placeholder element kept minimal
    lang = desc.find("Language")
    _sub(lang, "LanguageRole", "01")
    _sub(lang, "LanguageCode", cfg.get("language", "eng"))

    for code in cfg.get("bisac", []):
        subj = _sub(desc, "Subject")
        _sub(subj, "SubjectSchemeIdentifier", "10")  # BISAC
        _sub(subj, "SubjectCode", code)
    for kw in (cfg.get("keywords") or []):
        subj = _sub(desc, "Subject")
        _sub(subj, "SubjectSchemeIdentifier", "20")  # keywords
        _sub(subj, "SubjectHeadingText", kw)

    if cfg.get("description"):
        coll = _sub(p, "CollateralDetail")
        txt = _sub(coll, "TextContent")
        _sub(txt, "TextType", "03")  # description
        _sub(txt, "ContentAudience", "00")
        _sub(txt, "Text", cfg["description"])

    pub = _sub(p, "PublishingDetail")
    publisher = _sub(pub, "Publisher")
    _sub(publisher, "PublishingRole", "01")
    _sub(publisher, "PublisherName", cfg.get("publisher", cfg["author"]))

    prices = cfg.get("prices") or {}
    if prices:
        supply = _sub(p, "ProductSupply")
        market = _sub(supply, "SupplyDetail")
        for currency, amount in prices.items():
            price = _sub(market, "Price")
            _sub(price, "PriceType", "01")
            _sub(price, "PriceAmount", amount)
            _sub(price, "CurrencyCode", currency)


def generate_onix(cfg: dict) -> str:
    """Return a well-formed ONIX 3.0 reference message for all ISBN'd formats."""
    message = ET.Element("ONIXMessage", {"release": "3.0"})
    header = _sub(message, "Header")
    sender = _sub(header, "Sender")
    _sub(sender, "SenderName", cfg.get("publisher", cfg["author"]))

    seq = 0
    for fmt in ("paperback", "hardcover", "ebook"):
        isbn = isbn_for(cfg, fmt)
        if isbn:
            seq += 1
            _product(message, cfg, fmt, isbn, seq)

    raw = ET.tostring(message, encoding="unicode")
    return minidom.parseString(raw).toprettyxml(indent="  ")
