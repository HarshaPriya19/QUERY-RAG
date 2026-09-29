"""Held-out Northwind benchmark.

Documents and queries are customer-policy scenarios. They were not written by
walking the judge's rule list. Development items and test items are both in
this file so the split is explicit and stable. The experiment reports test
numbers. The judge is not edited against either split.

Labels:
  safe       a reviewer should let the rewrite reach the retriever
  harmful    a reviewer should block it
  ambiguous  a reasonable reviewer could go either way; expected_safe is the
             preferred call, not a rule-shaped answer
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_PATH = ROOT / "experiments" / "benchmark.json"

DOCUMENTS: dict[str, str] = {
    "novabook_air": (
        "# NovaBook Air\n\n"
        "The NovaBook Air is Northwind Gadgets' compact laptop. "
        "NovaBook Air price is Rs 45000. The NovaBook Air launched in March 2023. "
        "The NovaBook Air return window is 14 days. "
        "Opened software for the NovaBook Air is not returnable. "
        "The NovaBook Air warranty lasts 1 year."
    ),
    "novabook_pro": (
        "# NovaBook Pro\n\n"
        "The NovaBook Pro is Northwind Gadgets' high-end laptop. "
        "NovaBook Pro price is Rs 85000. The NovaBook Pro launched in January 2024. "
        "The NovaBook Pro return window is 30 days. "
        "The NovaBook Pro warranty lasts 2 years. "
        "Battery replacement for the NovaBook Pro is available only at authorized service centers."
    ),
    "novabook_lite": (
        "# NovaBook Lite\n\n"
        "The NovaBook Lite is the lowest priced Northwind laptop. "
        "NovaBook Lite price is Rs 28000. The NovaBook Lite launched in June 2022. "
        "The NovaBook Lite return window is 7 days. "
        "The NovaBook Lite weighs 1.1 kg. The NovaBook Lite has no backlit keyboard."
    ),
    "pixeltab": (
        "# PixelTab\n\n"
        "The PixelTab is Northwind Gadgets' large tablet. "
        "PixelTab price is Rs 32000. The PixelTab launched in August 2024. "
        "The PixelTab return window is 7 days. "
        "Refurbished PixelTab units are not returnable."
    ),
    "pixeltab_mini": (
        "# PixelTab Mini\n\n"
        "The PixelTab Mini is the smaller and newer Northwind tablet. "
        "PixelTab Mini price is Rs 18000. The PixelTab Mini launched in September 2025. "
        "The PixelTab Mini return window is 10 days. The PixelTab Mini screen is 8 inches."
    ),
    "pixelbuds": (
        "# PixelBuds\n\n"
        "PixelBuds are Northwind wireless earbuds. PixelBuds price is Rs 4999. "
        "The PixelBuds return window is 7 days. "
        "PixelBuds water damage is not covered."
    ),
    "northdock": (
        "# NorthDock\n\n"
        "The NorthDock is a laptop dock. NorthDock price is Rs 8500. "
        "The NorthDock is compatible only with the NovaBook Air and NovaBook Pro. "
        "The NorthDock is not compatible with the NovaBook Lite."
    ),
    "homescreen_monitor": (
        "# HomeScreen monitor\n\n"
        "The HomeScreen monitor is a 27 inch display. HomeScreen monitor price is Rs 16000. "
        "HomeScreen installation fee is separate from the monitor price."
    ),
    "chargebrick": (
        "# ChargeBrick\n\n"
        "The ChargeBrick is a 65W charger. ChargeBrick price is Rs 2499. "
        "The ChargeBrick cable is not included."
    ),
    "airsleeve": (
        "# AirSleeve\n\n"
        "The AirSleeve is a laptop sleeve. AirSleeve price is Rs 1499. "
        "The AirSleeve fits only the NovaBook Air. The AirSleeve is not waterproof."
    ),
    "returns_standard": (
        "# Standard returns\n\n"
        "Standard returns are allowed for 14 days on eligible Northwind accessories. "
        "Opened software is not eligible for a standard return. "
        "A standard return requires proof of purchase."
    ),
    "returns_premium": (
        "# Premium returns\n\n"
        "Premium returns are allowed for 30 days. "
        "Premium returns apply to the NovaBook Pro and the HomeScreen monitor purchased after January 2024."
    ),
    "returns_refurbished": (
        "# Refurbished returns\n\n"
        "Refurbished units are not returnable under the ordinary policy. "
        "Unopened refurbished units may be returned within 48 hours."
    ),
    "warranty_base": (
        "# Base warranty\n\n"
        "The base warranty is 1 year from delivery. "
        "The base warranty does not cover liquid damage. "
        "Battery coverage under the base warranty is 6 months."
    ),
    "warranty_extended": (
        "# Extended warranty\n\n"
        "The extended warranty is 2 years. "
        "Customers must register the extended warranty within 30 days of delivery. "
        "The extended warranty is not transferable."
    ),
    "warranty_claims": (
        "# Warranty claims\n\n"
        "A warranty claim must be filed within 7 days of the failure. "
        "Only the original purchaser can file a warranty claim. "
        "Claims after 2024 require an invoice number."
    ),
    "student_discount": (
        "# Student discount\n\n"
        "Students receive a student discount of 10% off eligible laptops. "
        "The student discount is not valid on the PixelTab. "
        "The student discount minimum order is Rs 20000. "
        "The student discount offer is valid until December 2025."
    ),
    "employee_discount": (
        "# Employee discount\n\n"
        "Staff receive an employee discount of 15% off. "
        "The employee discount is not valid on gift cards. "
        "The maximum employee discount is Rs 5000."
    ),
    "festival_sale": (
        "# Festival sale\n\n"
        "The festival sale is 20% off. The festival sale runs until 15 November 2025. "
        "The festival sale is not valid on the NovaBook Pro. "
        "The festival sale applies to only online orders."
    ),
    "shipping_metro": (
        "# Metro shipping\n\n"
        "Northwind offers free shipping on orders over Rs 2000. "
        "Metro delivery takes 3 to 5 days. Free metro shipping applies to metro cities only."
    ),
    "shipping_remote": (
        "# Remote shipping\n\n"
        "Shipping to Ladakh is not available before 2025. "
        "Remote island deliveries are not covered by free shipping."
    ),
    "shipping_express": (
        "# Express shipping\n\n"
        "Express shipping is next-day delivery in metro cities. "
        "Express shipping costs Rs 199. "
        "Express shipping is not available for the HomeScreen monitor."
    ),
    "gift_cards": (
        "# Gift cards\n\n"
        "Gift cards cannot be returned. "
        "A gift card expires 12 months after purchase. "
        "The maximum gift card load is Rs 10000. Gift cards are not redeemable for cash."
    ),
    "repair_bangalore": (
        "# Bangalore repairs\n\n"
        "The Bangalore flagship repair desk is open on weekdays. "
        "Bangalore screen repair cost starts at Rs 3500. "
        "The Bangalore repair desk does not handle liquid damage."
    ),
    "repair_delhi": (
        "# Delhi repairs\n\n"
        "The Delhi repair desk is open Monday to Saturday. "
        "Delhi screen repair cost starts at Rs 4000. "
        "Delhi liquid damage repair starts at Rs 6500."
    ),
    "repair_mailin": (
        "# Mail-in repair\n\n"
        "Mail-in repair takes 10 business days. The customer pays outbound postage. "
        "Batteries that are swollen are not accepted for mail-in repair."
    ),
    "price_match": (
        "# Price match\n\n"
        "Price match is available within 7 days of purchase. "
        "Price match is not available for marketplace sellers. "
        "Price match applies to only the identical SKU."
    ),
    "account_deletion": (
        "# Account deletion\n\n"
        "Account deletion is completed within 30 days of the request. "
        "Order history is retained for 7 years after account deletion."
    ),
    "trade_in": (
        "# Trade-in\n\n"
        "NovaBook Air trade-in value is up to Rs 8000. "
        "A trade-in device must power on. Water-damaged devices are not accepted for trade-in."
    ),
    "installation": (
        "# Installation\n\n"
        "HomeScreen installation costs Rs 799. "
        "HomeScreen installation is offered only in Bangalore and Delhi. "
        "HomeScreen installation is not available on Sundays."
    ),
    "business_lease": (
        "# Business lease\n\n"
        "The NovaBook Pro lease term is 12 months. "
        "The business lease minimum order is 5 units. "
        "The business lease is not available to students."
    ),
    "education_bundle": (
        "# Education bundle\n\n"
        "The education bundle is the NovaBook Air plus the AirSleeve. "
        "Education bundle price is Rs 46000. "
        "The education bundle is not valid after 31 December 2025."
    ),
    "battery_recall": (
        "# Battery recall\n\n"
        "NovaBook Pro batteries manufactured before March 2024 are recalled. "
        "NovaBook Air batteries are not part of this recall."
    ),
    "open_box": (
        "# Open-box\n\n"
        "The open-box discount is 10%. The open-box return window is 7 days. "
        "The open-box warranty is 90 days."
    ),
    "loyalty": (
        "# Loyalty points\n\n"
        "Loyalty earns 1 point per Rs 100 spent. "
        "Loyalty points expire after 12 months. "
        "Loyalty points are not earned on gift cards."
    ),
    "hours_bangalore": (
        "# Bangalore hours\n\n"
        "The Bangalore flagship is open 10:00 to 21:00. "
        "The Bangalore flagship is closed on public holidays."
    ),
    "hours_mumbai": (
        "# Mumbai hours\n\n"
        "The Mumbai store is open 11:00 to 22:00. The Mumbai store is open on Sundays."
    ),
    "intl_warranty": (
        "# International warranty\n\n"
        "The Northwind warranty is not valid outside India. "
        "Singapore service is available after 2024 with the original invoice."
    ),
    "data_transfer": (
        "# Data transfer\n\n"
        "Data transfer costs Rs 1499. "
        "The store is not responsible for data loss during data transfer."
    ),
    "northcloud": (
        "# Northcloud\n\n"
        "Northcloud is Rs 99 per month and includes 100 GB. "
        "Customers may cancel Northcloud anytime. "
        "Northcloud data is deleted 30 days after cancellation."
    ),
}


def _item(
    item_id: str,
    split: str,
    label: str,
    category: str,
    query: str,
    rewrite: str,
    gold: list[str],
    facts: list[str],
    expected_safe: bool,
    note: str,
) -> dict:
    return {
        "id": item_id,
        "split": split,
        "label": label,
        "category": category,
        "query": query,
        "rewrite": rewrite,
        "original": query,
        "rewritten": rewrite,
        "gold_doc_ids": gold,
        "expected_facts": facts,
        "expected_safe": expected_safe,
        "note": note,
    }


def _safe(item_id, split, category, query, rewrite, gold, facts, note) -> dict:
    return _item(item_id, split, "safe", category, query, rewrite, gold, facts, True, note)


def _harm(item_id, split, category, query, rewrite, gold, facts, note) -> dict:
    return _item(item_id, split, "harmful", category, query, rewrite, gold, facts, False, note)


def _amb(item_id, split, category, query, rewrite, gold, facts, preferred_safe: bool, note) -> dict:
    return _item(
        item_id, split, "ambiguous", category, query, rewrite, gold, facts, preferred_safe, note
    )


ITEMS: list[dict] = [
    # --- development: safe surface paraphrases ---
    _safe(
        "d_abbrev_lite", "dev", "abbreviation",
        "How much does the NB Lite weigh?",
        "How much does the NovaBook Lite weigh?",
        ["novabook_lite"], ["weighs 1.1 kg"],
        "Abbreviation expansion only.",
    ),
    _safe(
        "d_syn_sendback", "dev", "synonym",
        "How do I send back a NovaBook Air?",
        "How do I return a NovaBook Air?",
        ["novabook_air"], ["return window is 14 days"],
        "Everyday verb replaced with the catalog verb.",
    ),
    _safe(
        "d_syn_student", "dev", "synonym",
        "What is the student deal minimum?",
        "What is the student discount minimum?",
        ["student_discount"], ["Rs 20000"],
        "Deal and discount name the same offer.",
    ),
    _safe(
        "d_syn_before", "dev", "temporal",
        "Can you ship to Ladakh prior to 2025?",
        "Can you ship to Ladakh before 2025?",
        ["shipping_remote"], ["not available before 2025"],
        "Prior to and before are the same relation.",
    ),
    _safe(
        "d_sem_one_month", "dev", "semantic_equivalent",
        "What is the NovaBook Pro return window of 30 days?",
        "What is the NovaBook Pro return window of one month?",
        ["novabook_pro"], ["return window is 30 days"],
        "One month is being used as the ordinary name for a 30 day window.",
    ),
    _safe(
        "d_sem_price_words", "dev", "semantic_equivalent",
        "Is the NovaBook Air price Rs 45000?",
        "Is the NovaBook Air price forty-five thousand rupees?",
        ["novabook_air"], ["Rs 45000"],
        "Same price written out in words.",
    ),
    _safe(
        "d_syn_except", "dev", "negation",
        "Are returns excluding refurbished PixelTab units allowed?",
        "Are returns except refurbished PixelTab units allowed?",
        ["pixeltab"], ["Refurbished PixelTab units are not returnable"],
        "Excluding and except carry the same exclusion.",
    ),
    _safe(
        "d_filler_launch", "dev", "abbreviation",
        "Please tell me when the PixelTab launched.",
        "When did the PixelTab launch?",
        ["pixeltab"], ["August 2024"],
        "Politeness removed, question otherwise unchanged.",
    ),
    # --- development: harmful ---
    _harm(
        "d_h_entity", "dev", "entity",
        "How long is the NovaBook Air warranty?",
        "How long is the NovaBook Pro warranty?",
        ["novabook_air"], ["warranty lasts 1 year"],
        "Sibling laptop substituted.",
    ),
    _harm(
        "d_h_threshold", "dev", "constraint",
        "Do I get free shipping under Rs 2000?",
        "Do I get free shipping over Rs 2000?",
        ["shipping_metro"], ["over Rs 2000"],
        "The threshold direction is reversed. The original asks about orders under the cutoff.",
    ),
    _harm(
        "d_h_negation", "dev", "negation",
        "Opened software for the NovaBook Air is not returnable, right?",
        "Opened software for the NovaBook Air is returnable, right?",
        ["novabook_air"], ["not returnable"],
        "Negation removed from the software exception.",
    ),
    _harm(
        "d_h_scope", "dev", "scope",
        "Only the original purchaser can file a warranty claim.",
        "The original purchaser can file a warranty claim.",
        ["warranty_claims"], ["Only the original purchaser"],
        "Only is dropped, so the claim looks open to other people.",
    ),
    _harm(
        "d_h_year", "dev", "temporal",
        "Do claims after 2024 need an invoice number?",
        "Do claims after 2023 need an invoice number?",
        ["warranty_claims"], ["after 2024"],
        "The year that starts the invoice rule is moved.",
    ),
    _harm(
        "d_h_percent", "dev", "number",
        "What is the student discount of 10%?",
        "What is the student discount of 20%?",
        ["student_discount"], ["10%"],
        "Student rate replaced with the festival rate.",
    ),
    _harm(
        "d_h_city", "dev", "entity",
        "What does Bangalore screen repair cost?",
        "What does Delhi screen repair cost?",
        ["repair_bangalore"], ["Rs 3500"],
        "City desk substituted.",
    ),
    _harm(
        "d_h_ladakh", "dev", "temporal",
        "Is shipping to Ladakh unavailable before 2025?",
        "Is shipping to Ladakh available before 2025?",
        ["shipping_remote"], ["not available before 2025"],
        "Availability is flipped.",
    ),
    _harm(
        "d_h_gift", "dev", "negation",
        "Gift cards cannot be returned.",
        "Gift cards can be returned.",
        ["gift_cards"], ["cannot be returned"],
        "Return prohibition removed.",
    ),
    _harm(
        "d_h_window", "dev", "intent",
        "What is the NovaBook Air return window?",
        "Is the NovaBook Air returnable?",
        ["novabook_air"], ["return window is 14 days"],
        "A duration question is rewritten as an eligibility question.",
    ),
    # --- development: ambiguous ---
    _amb(
        "d_a_cheap", "dev", "ambiguity",
        "Tell me about the cheap laptop.",
        "Tell me about the NovaBook Lite.",
        ["novabook_lite"], ["Rs 28000"],
        False,
        "Lite is the lowest priced laptop, but the user never named it.",
    ),
    _amb(
        "d_a_mountains", "dev", "entity",
        "Can you deliver to the mountains?",
        "Can you deliver to Ladakh?",
        ["shipping_remote"], ["Ladakh"],
        False,
        "Ladakh is the only mountain destination in the policy, but it was inferred.",
    ),
    _amb(
        "d_a_about", "dev", "number",
        "The NovaBook Air return window is 14 days.",
        "The NovaBook Air return window is about 14 days.",
        ["novabook_air"], ["14 days"],
        False,
        "About softens an exact window. Some reviewers would still allow it.",
    ),
    _amb(
        "d_a_adds_rate", "dev", "number",
        "How does the student deal work?",
        "How does the student discount of 10% work?",
        ["student_discount"], ["10%"],
        False,
        "The rate is true in the policy and absent from the question.",
    ),
    _amb(
        "d_a_couple", "dev", "semantic_equivalent",
        "Is a couple of weeks enough to return the NovaBook Air?",
        "Is 14 days enough to return the NovaBook Air?",
        ["novabook_air"], ["14 days"],
        True,
        "A couple of weeks is a loose gloss of the 14 day window.",
    ),
    _amb(
        "d_a_repair_city", "dev", "entity",
        "What does a screen repair cost?",
        "What does Bangalore screen repair cost at Rs 3500?",
        ["repair_bangalore", "repair_delhi"],
        ["screen repair cost starts at Rs"],
        False,
        "Two cities publish different screen prices. The rewrite picks one and states it.",
    ),
    # --- test: safe surface forms ---
    _safe(
        "t_abbrev_pro", "test", "abbreviation",
        "NB Pro warrenty length",
        "NovaBook Pro warranty length",
        ["novabook_pro"], ["warranty lasts 2 years"],
        "Abbreviation and a typo, same product and same question.",
    ),
    _safe(
        "t_abbrev_air", "test", "abbreviation",
        "NB Air price",
        "NovaBook Air price",
        ["novabook_air"], ["Rs 45000"],
        "Short product name expanded.",
    ),
    _safe(
        "t_abbrev_pt", "test", "abbreviation",
        "PT refrubished returns",
        "PixelTab refurbished returns",
        ["pixeltab"], ["Refurbished PixelTab units are not returnable"],
        "Abbreviation and a typo.",
    ),
    _safe(
        "t_syn_gift", "test", "synonym",
        "gift voucher expiry",
        "gift card expiration",
        ["gift_cards"], ["12 months"],
        "Voucher and expiry are the catalog's gift card and expiration.",
    ),
    _safe(
        "t_syn_below", "test", "constraint",
        "Which tablets are priced below Rs 32000?",
        "Which tablets are priced under Rs 32000?",
        ["pixeltab_mini"], ["Rs 18000"],
        "Below and under set the same ceiling. Mini is the tablet under that price.",
    ),
    _safe(
        "t_syn_percent", "test", "number",
        "student discount of 10 percent",
        "student discount of 10%",
        ["student_discount"], ["10%"],
        "Percent sign and the word percent.",
    ),
    _safe(
        "t_syn_guarantee", "test", "synonym",
        "NB Pro guarantee length",
        "NovaBook Pro warranty length",
        ["novabook_pro"], ["2 years"],
        "Guarantee is the everyday word for this warranty.",
    ),
    _safe(
        "t_syn_sendback", "test", "synonym",
        "I want to send back my PixelBuds.",
        "I want to return my PixelBuds.",
        ["pixelbuds"], ["return window is 7 days"],
        "Send back means return.",
    ),
    _safe(
        "t_filler_express", "test", "abbreviation",
        "Could you tell me the express shipping cost?",
        "express shipping cost",
        ["shipping_express"], ["Rs 199"],
        "Filler removed.",
    ),
    _safe(
        "t_syn_atleast", "test", "constraint",
        "The business lease asks for no less than 5 units.",
        "The business lease asks for at least 5 units.",
        ["business_lease"], ["5 units"],
        "No less than and at least are the same floor.",
    ),
    _safe(
        "t_fmt_50k", "test", "number",
        "NovaBook Air price under 50k",
        "NovaBook Air price under 50000",
        ["novabook_air"], ["Rs 45000"],
        "50k and 50000 are the same cutoff, and the Air sits under it.",
    ),
    _safe(
        "t_fmt_two_years", "test", "number",
        "The NovaBook Pro warranty lasts two years.",
        "The NovaBook Pro warranty lasts 2 years.",
        ["novabook_pro"], ["2 years"],
        "Number word and digit.",
    ),
    # --- test: safe semantic equivalents a digit/slot checker tends to punish ---
    _safe(
        "t_sem_two_weeks", "test", "semantic_equivalent",
        "The NovaBook Air return window is 14 days.",
        "The NovaBook Air return window is two weeks.",
        ["novabook_air"], ["14 days"],
        "Two weeks is 14 days.",
    ),
    _safe(
        "t_sem_one_week", "test", "semantic_equivalent",
        "A warranty claim must be filed within 7 days.",
        "A warranty claim must be filed within one week.",
        ["warranty_claims"], ["within 7 days"],
        "One week is 7 days.",
    ),
    _safe(
        "t_sem_twelve_months", "test", "semantic_equivalent",
        "The NovaBook Air warranty lasts 1 year.",
        "The NovaBook Air warranty lasts twelve months.",
        ["novabook_air"], ["1 year"],
        "Twelve months is one year.",
    ),
    _safe(
        "t_sem_a_year", "test", "semantic_equivalent",
        "A gift card expires 12 months after purchase.",
        "A gift card expires a year after purchase.",
        ["gift_cards"], ["12 months"],
        "A year is 12 months.",
    ),
    _safe(
        "t_sem_repair_words", "test", "semantic_equivalent",
        "Bangalore screen repair cost starts at Rs 3500.",
        "Bangalore screen repair cost starts at three thousand five hundred rupees.",
        ["repair_bangalore"], ["Rs 3500"],
        "Same amount in words.",
    ),
    _safe(
        "t_sem_two_thousand", "test", "semantic_equivalent",
        "Free shipping on orders over two thousand rupees.",
        "Free shipping on orders over Rs 2000.",
        ["shipping_metro"], ["Rs 2000"],
        "Two thousand rupees is Rs 2000.",
    ),
    _safe(
        "t_sem_24h", "test", "semantic_equivalent",
        "Express shipping is next-day delivery.",
        "Express shipping is delivery within 24 hours.",
        ["shipping_express"], ["next-day delivery"],
        "Next-day delivery is a 24 hour promise.",
    ),
    _safe(
        "t_sem_two_days", "test", "semantic_equivalent",
        "Unopened refurbished units may be returned within 48 hours.",
        "Unopened refurbished units may be returned within two days.",
        ["returns_refurbished"], ["48 hours"],
        "48 hours is two days.",
    ),
    _safe(
        "t_sem_nobody_except", "test", "scope",
        "Only the original purchaser can file a warranty claim.",
        "Nobody except the person who bought the device can file a warranty claim.",
        ["warranty_claims"], ["Only the original purchaser"],
        "Same exclusivity, different wording.",
    ),
    _safe(
        "t_sem_fifteen", "test", "semantic_equivalent",
        "The employee discount is 15%.",
        "The employee discount is fifteen percent.",
        ["employee_discount"], ["15%"],
        "Fifteen percent is 15%.",
    ),
    # --- test: harmful ---
    _harm(
        "t_h_air_pro", "test", "entity",
        "What is the NovaBook Air warranty, not the Pro?",
        "What is the NovaBook Pro warranty?",
        ["novabook_air"], ["warranty lasts 1 year"],
        "The excluded sibling becomes the subject.",
    ),
    _harm(
        "t_h_city", "test", "entity",
        "Bangalore screen repair starts at what price?",
        "Delhi screen repair starts at what price?",
        ["repair_bangalore"], ["Rs 3500"],
        "Wrong city desk.",
    ),
    _harm(
        "t_h_program", "test", "entity",
        "How large is the student discount?",
        "How large is the festival sale discount?",
        ["student_discount"], ["10%"],
        "A different promotion is substituted.",
    ),
    _harm(
        "t_h_14_30", "test", "number",
        "NovaBook Air returns within 14 days",
        "NovaBook Air returns within 30 days",
        ["novabook_air"], ["14 days"],
        "Air's window is replaced with the Pro window.",
    ),
    _harm(
        "t_h_express_fee", "test", "number",
        "Express shipping costs Rs 199.",
        "Express shipping costs Rs 499.",
        ["shipping_express"], ["Rs 199"],
        "Fee changed.",
    ),
    _harm(
        "t_h_tradein", "test", "number",
        "NovaBook Air trade-in value is up to Rs 8000.",
        "NovaBook Air trade-in value is up to Rs 80000.",
        ["trade_in"], ["Rs 8000"],
        "An extra zero changes the offer.",
    ),
    _harm(
        "t_h_ladakh_flip", "test", "temporal",
        "Shipping to Ladakh is not available before 2025.",
        "Shipping to Ladakh is not available after 2025.",
        ["shipping_remote"], ["before 2025"],
        "Before and after select opposite periods.",
    ),
    _harm(
        "t_h_invoice_direction", "test", "temporal",
        "Claims after 2024 require an invoice number.",
        "Claims before 2024 require an invoice number.",
        ["warranty_claims"], ["after 2024"],
        "The invoice rule is moved to the other side of 2024.",
    ),
    _harm(
        "t_h_recall", "test", "temporal",
        "Which NovaBook Pro batteries manufactured before March 2024 are recalled?",
        "Which NovaBook Pro batteries manufactured after March 2024 are recalled?",
        ["battery_recall"], ["before March 2024"],
        "The recall cohort is reversed.",
    ),
    _harm(
        "t_h_software", "test", "negation",
        "Opened software is not eligible for a standard return.",
        "Opened software is eligible for a standard return.",
        ["returns_standard"], ["not eligible"],
        "Eligibility negation flipped.",
    ),
    _harm(
        "t_h_water", "test", "negation",
        "PixelBuds water damage is not covered.",
        "PixelBuds water damage is covered.",
        ["pixelbuds"], ["water damage is not covered"],
        "Coverage negation flipped.",
    ),
    _harm(
        "t_h_swollen", "test", "negation",
        "Batteries that are swollen are not accepted for mail-in repair.",
        "Batteries that are swollen are accepted for mail-in repair.",
        ["repair_mailin"], ["not accepted"],
        "A safety refusal is rewritten as acceptance.",
    ),
    _harm(
        "t_h_liability", "test", "negation",
        "The store is not responsible for data loss during data transfer.",
        "The store is responsible for data loss during data transfer.",
        ["data_transfer"], ["not responsible for data loss"],
        "Liability flipped.",
    ),
    _harm(
        "t_h_online_only", "test", "scope",
        "The festival sale applies to only online orders.",
        "The festival sale applies to online and in-store orders.",
        ["festival_sale"], ["only online orders"],
        "Online-only scope is widened to stores.",
    ),
    _harm(
        "t_h_cities", "test", "scope",
        "HomeScreen installation is offered only in Bangalore and Delhi.",
        "HomeScreen installation is offered in every Northwind city.",
        ["installation"], ["only in Bangalore and Delhi"],
        "Two-city scope becomes every city.",
    ),
    _harm(
        "t_h_sku", "test", "scope",
        "Price match applies to only the identical SKU.",
        "Price match applies to similar SKUs.",
        ["price_match"], ["only the identical SKU"],
        "Identical-SKU limit becomes similar products.",
    ),
    _harm(
        "t_h_cutoff", "test", "constraint",
        "Free shipping on orders over Rs 2000",
        "Free shipping on orders under Rs 2000",
        ["shipping_metro"], ["over Rs 2000"],
        "Cutoff direction reversed.",
    ),
    _harm(
        "t_h_drop_tablet", "test", "multi_constraint",
        "Student discount of 10% that is not valid on the PixelTab, minimum Rs 20000, until December 2025",
        "Student discount of 10%",
        ["student_discount"], ["not valid on the PixelTab"],
        "Percent kept, product exclusion, minimum, and end date removed.",
    ),
    _harm(
        "t_h_drop_pro", "test", "constraint",
        "Festival sale of 20% until 15 November 2025, not valid on the NovaBook Pro",
        "Festival sale of 20% until 15 November 2025",
        ["festival_sale"], ["not valid on the NovaBook Pro"],
        "The Pro exclusion is the detail that changes which laptop qualifies.",
    ),
    _harm(
        "t_h_express_drop", "test", "multi_constraint",
        "Express next-day shipping for Rs 199 in metro cities, not for the HomeScreen monitor",
        "Express shipping",
        ["shipping_express"], ["not available for the HomeScreen monitor"],
        "Fee, speed, geography, and the monitor exclusion all disappear.",
    ),
    _harm(
        "t_h_add_refurb", "test", "entity",
        "What is the NovaBook Air return policy?",
        "What is the refurbished NovaBook Air return policy?",
        ["novabook_air"], ["return window is 14 days"],
        "Refurbished is a different returns regime and was not in the question.",
    ),
    _harm(
        "t_h_add_years", "test", "number",
        "How long is the NovaBook Air warranty?",
        "How long is the NovaBook Air 2 year warranty?",
        ["novabook_air"], ["1 year"],
        "A longer warranty is inserted.",
    ),
    _harm(
        "t_h_window_elig", "test", "intent",
        "What is the PixelTab return window?",
        "Are PixelTab returns allowed?",
        ["pixeltab"], ["return window is 7 days"],
        "Window length and whether a return is allowed are different questions.",
    ),
    _harm(
        "t_h_claim_vs_length", "test", "temporal",
        "How soon must I file a warranty claim?",
        "How long does the base warranty last?",
        ["warranty_claims"], ["within 7 days"],
        "Filing deadline rewritten as the length of cover.",
    ),
    _harm(
        "t_h_worldwide", "test", "scope",
        "The Northwind warranty is not valid outside India.",
        "The Northwind warranty is valid worldwide.",
        ["intl_warranty"], ["not valid outside India"],
        "A geographic limit becomes worldwide cover.",
    ),
    _harm(
        "t_h_sunday", "test", "negation",
        "Can I book HomeScreen installation on Sunday?",
        "Can I book HomeScreen installation on Sunday in Bangalore?",
        ["installation"], ["not available on Sundays"],
        "The rewrite keeps Sunday and adds a city, but the policy forbids Sundays. Adding Bangalore makes the slot look more specific while the prohibition is still the question. This one is harmful because it narrows to a city without keeping the closed-day constraint in the search.",
    ),
]


def _fix_last_harmful() -> None:
    """Replace the weak Sunday item with a clearer harmful rewrite."""
    ITEMS[-1] = _harm(
        "t_h_sunday",
        "test",
        "constraint",
        "HomeScreen installation on Sunday",
        "HomeScreen installation in Bangalore",
        ["installation"],
        ["not available on Sundays"],
        "The closed day is replaced by a city, so retrieval can miss the Sunday ban.",
    )


_fix_last_harmful()

# The harmful list above is 26 including sunday. Count later.

EXTRA_TEST_AMBIGUOUS = [
    _amb(
        "t_a_latest", "test", "ambiguity",
        "Which is the latest tablet?",
        "PixelTab Mini specifications",
        ["pixeltab_mini"], ["September 2025"],
        True,
        "Mini launched after the PixelTab, so it is the latest tablet, but the user did not say the name.",
    ),
    _amb(
        "t_a_cheap", "test", "ambiguity",
        "I want the cheap laptop, not a tablet.",
        "I want the NovaBook Lite, not a tablet.",
        ["novabook_lite"], ["Rs 28000"],
        False,
        "Lite is the cheap laptop. Naming it is a resolution, not a paraphrase.",
    ),
    _amb(
        "t_a_month", "test", "semantic_equivalent",
        "NovaBook Pro can be returned for 30 days.",
        "NovaBook Pro can be returned for about a month.",
        ["novabook_pro"], ["30 days"],
        True,
        "About a month is close to 30 days and slightly looser.",
    ),
    _amb(
        "t_a_screen", "test", "entity",
        "How much is a screen repair?",
        "How much is a Bangalore screen repair at Rs 3500?",
        ["repair_bangalore", "repair_delhi"],
        ["screen repair cost starts at Rs"],
        False,
        "The question does not choose a city. Bangalore's price is not Delhi's price.",
    ),
    _amb(
        "t_a_free", "test", "constraint",
        "Is metro shipping free?",
        "Is metro shipping free on orders over Rs 2000?",
        ["shipping_metro"], ["over Rs 2000"],
        False,
        "The threshold is the real rule, and it was not in the question.",
    ),
    _amb(
        "t_a_couple", "test", "semantic_equivalent",
        "Do I have a couple of weeks to return the NovaBook Air?",
        "Do I have 14 days to return the NovaBook Air?",
        ["novabook_air"], ["14 days"],
        True,
        "Couple of weeks is an inexact way to say the 14 day window.",
    ),
    _amb(
        "t_a_lakh", "test", "number",
        "Show laptops under a lakh.",
        "Show laptops under Rs 85000.",
        ["novabook_air", "novabook_lite", "novabook_pro"],
        ["NovaBook"],
        False,
        "A lakh is Rs 100000. Rs 85000 is a different ceiling.",
    ),
    _amb(
        "t_a_cancel", "test", "temporal",
        "How do I cancel Northcloud?",
        "When is Northcloud data deleted after cancellation?",
        ["northcloud"], ["cancel Northcloud anytime"],
        False,
        "Cancellation and the deletion clock are related and not the same request.",
    ),
    _amb(
        "t_a_newer", "test", "scope",
        "NovaBook Pro or newer lease options",
        "NovaBook Pro lease options",
        ["business_lease"], ["12 months"],
        False,
        "Or newer is dropped. The catalog has no newer Pro, which is why some reviewers would allow it.",
    ),
    _amb(
        "t_a_mountains", "test", "entity",
        "Remote delivery into the mountains before 2025",
        "Shipping to Ladakh before 2025",
        ["shipping_remote"], ["before 2025"],
        False,
        "Mountain is resolved to Ladakh. The date constraint is kept.",
    ),
    _amb(
        "t_a_extended", "test", "scope",
        "What warranty comes with a Northwind laptop?",
        "What extended warranty can I register within 30 days?",
        ["warranty_base"], ["base warranty is 1 year"],
        False,
        "The base warranty is the default. Extended cover is a narrower product.",
    ),
    _amb(
        "t_a_sameday", "test", "temporal",
        "Do you offer same-day delivery?",
        "Do you offer express next-day delivery for Rs 199?",
        ["shipping_express"], ["next-day delivery"],
        False,
        "Same-day and next-day are neighboring promises, not the same promise.",
    ),
]

ITEMS.extend(EXTRA_TEST_AMBIGUOUS)

ITEMS.extend([
    _safe(
        "t_syn_bundle", "test", "synonym",
        "What is the education bundle price?",
        "What does the education bundle cost?",
        ["education_bundle"], ["Rs 46000"],
        "Price and cost ask for the same figure.",
    ),
    _harm(
        "t_h_openbox", "test", "number",
        "The open-box warranty is 90 days.",
        "The open-box warranty is 2 years.",
        ["open_box"], ["90 days"],
        "Open-box cover is replaced with the full Pro warranty length.",
    ),
    _harm(
        "t_h_transfer", "test", "negation",
        "The extended warranty is not transferable.",
        "The extended warranty is transferable.",
        ["warranty_extended"], ["not transferable"],
        "Transfer prohibition removed.",
    ),
    _safe(
        "t_sem_points", "test", "semantic_equivalent",
        "Loyalty points expire after 12 months.",
        "Loyalty points expire after a year.",
        ["loyalty"], ["12 months"],
        "A year and 12 months name the same expiry.",
    ),
    _harm(
        "t_h_dock", "test", "entity",
        "Is the NorthDock compatible with the NovaBook Lite?",
        "Is the NorthDock compatible with the NovaBook Air?",
        ["northdock"], ["not compatible with the NovaBook Lite"],
        "The compatibility question is moved to a different laptop.",
    ),
    _amb(
        "t_a_monitor", "test", "ambiguity",
        "What does the HomeScreen cost?",
        "HomeScreen installation costs Rs 799.",
        ["homescreen_monitor"], ["Rs 16000"],
        False,
        "The monitor has a price and a separate install fee. The rewrite picks the fee.",
    ),
    _safe(
        "t_filler_mumbai", "test", "abbreviation",
        "Please tell me if the Mumbai store is open on Sundays.",
        "Is the Mumbai store open on Sundays?",
        ["hours_mumbai"], ["open on Sundays"],
        "Politeness removed.",
    ),
    _harm(
        "t_h_deletion", "test", "temporal",
        "Account deletion is completed within 30 days of the request.",
        "Account deletion is completed within 7 days of the request.",
        ["account_deletion"], ["within 30 days"],
        "The deletion clock is shortened to a week.",
    ),
    _safe(
        "d_sem_premium", "dev", "semantic_equivalent",
        "Premium returns are allowed for 30 days.",
        "Premium returns are allowed for one month.",
        ["returns_premium"], ["30 days"],
        "One month stands in for the 30 day premium window.",
    ),
    _harm(
        "d_h_sleeve", "dev", "entity",
        "The AirSleeve fits only the NovaBook Air.",
        "The AirSleeve fits only the NovaBook Pro.",
        ["airsleeve"], ["fits only the NovaBook Air"],
        "The only compatible laptop is swapped.",
    ),
    _amb(
        "d_a_charger", "dev", "ambiguity",
        "How much is the 65W charger?",
        "The ChargeBrick price is Rs 2499.",
        ["chargebrick"], ["Rs 2499"],
        False,
        "ChargeBrick is the 65W charger. The rewrite also states the price the user did not quote.",
    ),
    _harm(
        "t_h_holiday", "test", "negation",
        "The Bangalore flagship is closed on public holidays.",
        "The Bangalore flagship is open on public holidays.",
        ["hours_bangalore"], ["closed on public holidays"],
        "Holiday closure flipped.",
    ),
])


def write_benchmark() -> None:
    labels = {}
    splits = {}
    ids = []
    for item in ITEMS:
        ids.append(item["id"])
        labels[item["label"]] = labels.get(item["label"], 0) + 1
        splits[item["split"]] = splits.get(item["split"], 0) + 1
        if item["label"] == "safe" and not item["expected_safe"]:
            raise SystemExit(f"{item['id']} is safe but expected_safe is false")
        if item["label"] == "harmful" and item["expected_safe"]:
            raise SystemExit(f"{item['id']} is harmful but expected_safe is true")
        for doc_id in item["gold_doc_ids"]:
            if doc_id not in DOCUMENTS:
                raise SystemExit(f"{item['id']} gold {doc_id} missing")
        blob = "\n".join(DOCUMENTS[doc_id] for doc_id in item["gold_doc_ids"])
        for fact in item["expected_facts"]:
            if fact not in blob:
                raise SystemExit(f"{item['id']} fact not in gold docs: {fact}")
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate query ids")
    if len(DOCUMENTS) < 30 or len(DOCUMENTS) > 50:
        raise SystemExit(f"document count {len(DOCUMENTS)} outside 30-50")
    if len(ITEMS) < 60 or len(ITEMS) > 100:
        raise SystemExit(f"query count {len(ITEMS)} outside 60-100")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for stale in DATA_DIR.glob("*.md"):
        stale.unlink()
    for doc_id, text in DOCUMENTS.items():
        if len(text) > 900:
            raise SystemExit(f"{doc_id} is {len(text)} chars and may split into two chunks")
        (DATA_DIR / f"{doc_id}.md").write_text(text + "\n", encoding="utf-8")

    payload = {
        "meta": {
            "documents": len(DOCUMENTS),
            "queries": len(ITEMS),
            "splits": splits,
            "labels": labels,
            "note": (
                "Test items are held out. Development items are for inspection only. "
                "The judge was not fitted to either split."
            ),
        },
        "items": ITEMS,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"documents={len(DOCUMENTS)} queries={len(ITEMS)} splits={splits} labels={labels}")
    print(f"gold docs touched={len({d for item in ITEMS for d in item['gold_doc_ids']})}")


if __name__ == "__main__":
    write_benchmark()
