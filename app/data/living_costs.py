"""Typical monthly cost of living for a student, shown as separate lines until the user replaces them.

These are published estimates, not official statistics, and the calculation labels them that way. Lines
add up to each source's total. Update them once a year together with university_facts.json.

Poland: "Portfel Studenta 2026" (ZBP, WIB) puts living costs without tuition at 3,545.82 zł a month and a
rented room at 560-1,100 zł; housing is the middle of that range. Food is the middle of 700-1,200 zł from
money.pl. The report publishes no further split in its press release, so the rest stays one line.
Ukraine: the "room" budget of Finab's 2026 student estimate, 16,800 UAH a month.
"""

from __future__ import annotations

LIVING_COST_KEYS = ("housing", "food", "transport", "study_materials", "other_living")

LIVING_COSTS: dict[str, dict] = {
    "Poland": {
        "currency": "PLN",
        "source_name": "Portfel Studenta 2026, ZBP and WIB",
        "source_url": "https://bank.pl/wydatki-studentow-przekraczaja-juz-4-tys-zl-miesiecznie-raport-portfel-studenta-2026/",
        "lines": {"housing": 830, "food": 950, "other_living": 1766},
        "labels": {"other_living": "Transport, phone, study and personal"},
    },
    "Ukraine": {
        "currency": "UAH",
        "source_name": "Finab student budget estimate, 2026",
        "source_url": "https://finab.com.ua/news/skilky-hroshey-potribno-studentu-u-2026-rotsi-chy-vystachyt-stypendiyi/",
        "lines": {"housing": 6500, "food": 5500, "transport": 1000, "study_materials": 500, "other_living": 3300},
        "labels": {"other_living": "Phone, personal, leisure and reserve"},
    },
}

COST_LABELS = {
    "tuition": "Tuition",
    "mandatory_fees": "Mandatory fees",
    "housing": "Housing",
    "food": "Food",
    "transport": "Transport",
    "study_materials": "Books and study materials",
    "other_living": "Other living costs",
    "additional_training": "Additional training and courses",
    "scholarships": "Scholarships and grants",
    "pay_given_up": "Pay given up while studying",
    "income_during_study": "Income earned while studying",
}
