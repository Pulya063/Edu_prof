"""Build app/data/university_facts.json: verified facts for the top universities.

    uv run --no-sync --with pypdf python -m app.scripts.build_university_facts

Run once a year before the admission campaign, review the diff, commit it. The app only reads the JSON,
so a page never depends on a third-party site being up and every change is visible in review.

Sources, per field:
  address, faculties  Poland: RAD-on (POL-on open data). Ukraine: EDEBO register (address only).
  fees                Poland: the rector's order. Ukraine: ZAXID.NET lists of each university's approved
                      prices, marked as press in the output because they are not the original document.
Amounts are copied, never estimated. Semester fees are doubled to a year because the document says so.
"""

from __future__ import annotations

import io
import json
import re
import time
from pathlib import Path
from typing import Any

import httpx

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "university_facts.json"
USER_AGENT = "FenceUniversityFacts/1.0 (education ROI research)"
RADON = "https://radon.nauka.gov.pl/opendata/polon"
RADON_PAGE = "https://radon.nauka.gov.pl/dane/wykaz-uczelni-i-instytucji-szkolnictwa-wyzszego-i-nauki"
EDEBO = "https://registry.edbo.gov.ua/api/opendata"
ACADEMIC_YEAR = "2026/2027"

POLAND = [
    {"domain": "uw.edu.pl", "registry_name": "Uniwersytet Warszawski", "fees": {"parser": "uw", "title": "Order 78 of the Rector, 9 June 2026, with order 105", "url": "https://monitor.uw.edu.pl/Lists/Uchway/Attachments/7859/M.2026.209.Zarz.78.pdf", "amendments": ["https://bok.uw.edu.pl/wp-content/uploads/sites/68/2026/08/M.2026.296.Zarz_.105.pdf"]}},
    {"domain": "pw.edu.pl", "registry_name": "Politechnika Warszawska", "fees": {"parser": "pw", "title": "Decision 132/2026 of the Rector", "url": "https://www.bip.pw.edu.pl/var/pw/storage/original/application/7292c711d655c43a6cd0be24e3268aa2.pdf"}},
    {"domain": "uj.edu.pl", "registry_name": "Uniwersytet Jagielloński w Krakowie", "fees": {"parser": "uj", "title": "Order 11 of the Rector, 12 February 2026", "url": "https://bip.uj.edu.pl/documents/1384597/160279914/zarz_11_2026.pdf/3d82dde4-af56-4ab6-b5d9-2086611f4def"}},
    {"domain": "agh.edu.pl", "registry_name": "Akademia Górniczo-Hutnicza im. Stanisława Staszica w Krakowie", "fees": {"parser": "agh", "title": "Order 39/2026 of the Rector, annex 1", "url": "https://rekrutacja.agh.edu.pl/wp-content/uploads/2026/05/zarzadzenie_rektora_39_2026_oplaty_2026_2027_zalacznik_1.pdf"}},
    {"domain": "pwr.edu.pl", "registry_name": "Politechnika Wrocławska", "fees": {"parser": "pwr", "html": True, "title": "Admissions page: fees under internal order 72/2026", "url": "https://rekrutacja.pwr.edu.pl/po-rekrutacji/oplaty/"}},
    {"domain": "uwr.edu.pl", "registry_name": "Uniwersytet Wrocławski", "fees": {"parser": "uwr", "title": "Order 14/2026 of the Rector", "url": "https://prawo.uwr.edu.pl/wp-content/uploads/sites/210/2026/02/Nr-14-2026-z-dnia-02.02.2026_oplaty-za-studia_2026_2027.pdf"}},
    {"domain": "amu.edu.pl", "registry_name": "Uniwersytet im. Adama Mickiewicza w Poznaniu", "fees": {"parser": "amu", "title": "Order 176/2025/2026 of the Rector, annex 1", "url": "https://prawo.amu.edu.pl/wp-content/uploads/2026/09/Zalacznik-nr-1-do-Zarzadzenia-Nr-176_2025_2026.pdf"}},
    {"domain": "pg.edu.pl", "registry_name": "Politechnika Gdańska", "fees": {"parser": "pg", "title": "Order 34/2026 of the Rector, annex 5", "url": "https://cdn.files.pg.edu.pl/main/Rekrutacja/Akty%20prawne/Oplaty%20za%20uslugi%20edukacyjne/2026.2027/ZR%2034-2026.pdf"}},
    {"domain": "put.poznan.pl", "registry_name": "Politechnika Poznańska", "fees": {"parser": "put", "title": "Order 18/2026 of the Rector, annex 1", "url": "https://put.poznan.pl/sites/default/files/2026-05/Zarz%C4%85dzenie%20nr%2018%20-%202026%20-%20Za%C5%82%C4%85cznik%20nr%201.pdf"}},
    {"domain": "uni.lodz.pl", "registry_name": "Uniwersytet Łódzki", "fees": {"parser": "ul", "multi": "https://www.wsmip.uni.lodz.pl/strefa-studenta/studia/oplaty-pobierane-od-studentow-1", "title": "Order 124 of the Rector, 30 April 2026, faculty annexes", "url": "https://www.bip.uni.lodz.pl/fileadmin/user_upload/zarz._nr_124_z_30.04.2026_r.pdf"}},
    {"domain": "polsl.pl", "registry_name": "Politechnika Śląska", "fees": {"register": True}},
    {"domain": "sgh.waw.pl", "registry_name": "Szkoła Główna Handlowa w Warszawie", "fees": {"register": True}},
    {"domain": "ug.edu.pl", "registry_name": "Uniwersytet Gdański", "fees": {"parser": "ug", "title": "Order 74/R/26 of the Rector, annex 1", "url": "https://bip.ug.edu.pl/sites/default/files/nodes/akty_normatywne/120364/files/zalacznik_nr_1.pdf"}},
    {"domain": "umcs.pl", "registry_name": "Uniwersytet Marii Curie-Skłodowskiej w Lublinie", "fees": {"parser": "umcs", "title": "Order 23/2026 of the Rector, annex 2, with order 45/2026", "url": "https://phavi.umcs.pl/at/attachments/2026/0402/125258-zalacznik-nr-1-4-nabor-2026-2027-do-zarzadzenia-oplaty-zal-2.pdf", "amendments": ["https://phavi.umcs.pl/at/attachments/2026/0703/111729-zr-nr-45-2026-zalacznik-zm-zarzadz-nr-23-2026-02-04-2026-wersja-2-06-2026.pdf"]}},
    {"domain": "p.lodz.pl", "registry_name": "Politechnika Łódzka", "fees": {"parser": "lodz", "title": "Notice of the Vice-Rector, 2 June 2026", "url": "https://rekrutacja.p.lodz.pl/sites/default/files/2026-06/komunikat_prorektora_oplaty_pl_2026_02.06.2026.pdf"}},
]
# expected: the range ZAXID.NET published separately for the university, in thousands of UAH. A mismatch stops the build.
UKRAINE = [
    {"domain": "lpnu.ua", "edebo": "Національний університет \"Львівська політехніка\"", "region": 46, "press": "lvivska_politehnika_vartist_navchannya_na_bakalavrati_2026_tsini_na_usi_spetsialnosti_n1638273", "expected": (52, 100)},
    {"domain": "lnu.edu.ua", "edebo": "Львівський національний університет імені Івана Франка", "region": 46, "press": "lnu_imeni_ivana_franka_vartist_navchannya_na_bakalavrati_2026_tsini_na_usi_spetsialnosti_n1638215", "expected": (51.4, 86.7)},
    {"domain": "kpi.ua", "edebo": "Національний технічний університет України «Київський політехнічний інститут імені Ігоря Сікорського»", "region": 80, "press": "kpi_kiyivskiy_politehnichniy_institut_vartist_navchannya_na_bakalavrati_2026_tsini_na_usi_spetsialnosti_n1638506", "expected": (50, 83.7)},
    {"domain": "knu.ua", "edebo": "Київський національний університет імені Тараса Шевченка", "region": 80, "press": "podorozhchannya_do_27_knu_imeni_shevchenka_zatverdiv_vartist_navchannya_dlya_vstupnikiv_2026_roku_n1640555", "expected": (54.6, 119)},
    {"domain": "ukma.edu.ua", "edebo": "Національний університет \"Києво-Могилянська академія\"", "region": 80, "press": "kiyevo_mogilyanska_akademiya_vartist_navchannya_na_bakalavrati_2026_tsini_na_usi_spetsialnosti_n1638417"},
    {"domain": "karazin.ua", "edebo": "Харківський національний університет імені В.Н. Каразіна", "region": 63, "press": "harkivskiy_universitet_karazina_vartist_navchannya_na_bakalavrati_2026_usi_spetsialnosti_n1638637"},
    {"domain": "kneu.edu.ua", "edebo": "Київський національний економічний університет імені Вадима Гетьмана", "region": 80, "press": "vartist_navchannya_u_kiyivskomu_universiteti_imeni_vadima_getmana_zrosla_do_40_n1641784", "expected": (45, 67)},
    {"domain": "onu.edu.ua", "edebo": "Одеський національний університет імені І. І. Мечникова", "region": 51, "press": "odeskiy_universitet_mechnikova_vartist_navchannya_dlya_vstupnikiv_2026_tsini_na_usi_programi_n1642695"},
    {"domain": "dnu.dp.ua", "edebo": "Дніпровський національний університет імені Олеся Гончара", "region": 12, "press": "dniprovskiy_universitet_gonchara_vartist_navchannya_dlya_vstupnikiv_2026_tsini_na_usi_programi_n1642696"},
    {"domain": "knute.edu.ua", "edebo": "Державний торговельно-економічний університет", "region": 80, "press": "torgovelno_ekonomichniy_universitet_vartist_navchannya_dlya_vstupnikiv_2026_tsini_na_usi_programi_n1642832", "expected": (45, 59)},
    {"domain": "nmuofficial.com", "edebo": "Національний медичний університет імені О.О. Богомольця", "region": 80, "press": "podorozhchannya_do_60_medichniy_universitet_bogomoltsya_zatverdiv_tsini_dlya_vstupnikiv_n1641682"},
    {"domain": "sumdu.edu.ua", "edebo": "Сумський державний університет", "region": 59, "press": "podorozhchannya_mayzhe_na_tretinu_sumskiy_derzhavniy_universitet_zatverdiv_tsini_dlya_vstupnikiv_n1639349"},
    {"domain": "nubip.edu.ua", "edebo": "Національний університет біоресурсів і природокористування України", "region": 80, "press": "universitet_bioresursiv_i_prirodokoristuvannya_vartist_navchannya_2026_tsini_na_usi_spetsialnosti_n1639694"},
    {"domain": "nmu.org.ua", "edebo": "Національний технічний університет \"Дніпровська політехніка\"", "region": 12, "press": "dniprovska_politehnika_vartist_navchannya_dlya_vstupnikiv_2026_tsini_na_usi_programi_n1642677"},
    {"domain": "wunu.edu.ua", "edebo": "Західноукраїнський національний університет", "region": 61, "press": "zahidnoukrayinskiy_universitet_vartist_navchannya_dlya_vstupnikiv_2026_tsini_na_usi_programi_n1642333"},
]

# Older domains the open university directory still lists for the same institution.
DIRECTORY_DOMAINS = {
    "pwr.edu.pl": ["pwr.wroc.pl"], "uwr.edu.pl": ["uni.wroc.pl"], "pg.edu.pl": ["pg.gda.pl"], "ug.edu.pl": ["univ.gda.pl"], "umcs.pl": ["umcs.lublin.pl"],
    "polsl.pl": ["polsl.gliwice.pl"], "lpnu.ua": ["lp.edu.ua"], "knu.ua": ["univ.kiev.ua"], "ukma.edu.ua": ["ukma.kiev.ua"], "kneu.edu.ua": ["kneu.kiev.ua"],
    "karazin.ua": ["student.karazin.ua", "univer.kharkov.ua"], "wunu.edu.ua": ["tane.edu.ua"],
}

client = httpx.Client(timeout=90, follow_redirects=True, headers={"User-Agent": USER_AGENT})


def item(name: str, amount: float, faculty: str | None = None, level: str | None = None, mode: str | None = None) -> dict[str, Any]:
    return {"programme": re.sub(r"\s+", " ", name).strip(" ,.;-–"), "faculty": faculty, "level": level, "study_mode": mode, "amount_per_year": round(amount, 2)}


def pdf_text(url: str) -> str:
    from pypdf import PdfReader

    response = client.get(url)
    response.raise_for_status()
    return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(response.content)).pages)


# ── Fee parsers. Each one reads the layout of one document. ───────────────────────────────────
def parse_pw(text: str) -> tuple[list[dict], int]:
    """Table 1: per-semester fee, part-time column then English-taught column."""
    items, free, faculty = [], 0, None
    body = text[text.index("Tabela 1"):]
    body = body[:body.index("Tabela 2")] if "Tabela 2" in body else body
    for raw in body.splitlines():
        line = raw.strip()
        match = re.match(r"^(.+?) / (I{1,2}) stopnia\s+(\d+|–|bez opłaty)\s+(\d+|–|bez opłaty)\s*$", line)
        if match:
            name, degree, part_time, english = match.groups()
            level = "first cycle" if degree == "I" else "second cycle"
            for value, mode in ((part_time, "part-time"), (english, "full-time in English")):
                if value == "bez opłaty":
                    free += 1
                elif value != "–":
                    items.append(item(name, int(value) * 2, faculty, level, mode))
        elif line.isupper() and len(line) > 4 and "PLN" not in line:
            faculty = line.title().replace(" I ", " i ")
    return items, free


def parse_put(text: str) -> tuple[list[dict], int]:
    """Section A, points 3 and 4: names listed above a '- 3900 zł za semestr' line."""
    items: list[dict] = []
    section = text[:text.index("B. Opłaty")]
    for level, start, end in (("first cycle", "3) na studiach niestacjonarnych", "4) na studiach niestacjonarnych"), ("second cycle", "4) na studiach niestacjonarnych", "5) potwierdzenie")):
        block = section[section.index(start):section.index(end)]
        block = block[block.index("kierunkach:") + len("kierunkach:"):]
        for names, amount in re.findall(r"(.*?)-\s*(\d{3,5})\s*zł za semestr", block, re.S):
            for name in re.split(r",\s*\n|,\s+|\n", names):
                if name.strip(" ,"):
                    items.append(item(name, int(amount) * 2, None, level, "part-time"))
    return items, 0


def parse_uwr(text: str) -> tuple[list[dict], int]:
    """Annexes 1-7: yearly fee per programme, by faculty. Where the first and later years differ, the first year."""
    items: list[dict] = []
    annexes = re.split(r"(?=Załącznik Nr \d+\s*\n\s*do zarządzenia)", text)
    for annex in annexes:
        heading = re.search(r"Wysokość rocznej opłaty za studia niestacjonarne.*?(WYDZIAŁ [^\n]+)\n", annex, re.S)
        if not heading:
            continue
        faculty = heading.group(1).strip().title().replace(" I ", " i ").replace(" Na ", " na ")
        table = annex[heading.end():]
        for name, degree, amount in re.findall(r"\d+\.\s*\n?\s*([^\n]+(?:\n[^\n\d]+?)??)\s*\n\s*(pierwszego stopnia|drugiego stopnia|jednolite studia magisterskie)\s*\n?\s*(?:I\s*[–-]\s*)?(\d{4,5})", table):
            items.append(item(name, int(amount), faculty, {"pierwszego stopnia": "first cycle", "drugiego stopnia": "second cycle"}.get(degree, "long-cycle master's"), "part-time"))
        for name, amount in re.findall(r"Roczna opłata w złotych\s*\n\s*([^\n\d]+?)\s*\n\s*jednolite studia magisterskie\s+(\d{4,5})", table):
            items.append(item(name, int(amount), faculty, "long-cycle master's", "part-time"))
    return items, 0


def parse_lodz(text: str) -> tuple[list[dict], int]:
    """Annex table: per-semester fee; the last column is the 2026/27 intake."""
    items: list[dict] = []
    table = text[text.index("Rekrut. 2026/27"):]
    lines = [line.strip() for line in table.splitlines() if line.strip()][1:]
    pending: list[str] = []
    for line in lines:
        amounts = re.findall(r"\d[  ]?\d{3},00", line)
        if amounts:
            before = line[:line.index(amounts[0])].strip()
            parts = pending + ([before] if before else [])
            text_name = " ".join(parts)
            level = "second cycle" if "Drugiego" in text_name else "first cycle" if "Pierwszego" in text_name else None
            name = re.sub(r"(Pierwszego|Drugiego)\s*stopnia", " ", text_name).strip()
            amount = float(amounts[-1].replace(" ", "").replace(" ", "").replace(",", "."))
            if name and len(name) < 80 and name[0].isupper():
                items.append(item(name, amount * 2, None, level, "part-time"))
            pending = []
        else:
            pending.append(line)
            pending = pending[-3:]
    return items, 0


def parse_uw(text: str) -> tuple[list[dict], int]:
    """One block per field of study; the single yearly payment for each part-time degree."""
    items: list[dict] = []
    body = text[text.index("Spis treści"):] if "Spis treści" in text else text
    starts = list(re.finditer(r"\n\s*\d+[a-z]?\. kierunek studiów\s*:\s*([^\n.]+?(?:\n[^\n.]+?)?)\s*\n(?=\s*(?:Lp\.|Tabela))", body))
    for index, start in enumerate(starts):
        block = body[start.end():starts[index + 1].start() if index + 1 < len(starts) else len(body)]
        section = re.search(r"Studia niestacjonarne.*?(?=\n\s*\d\)\s*Powtarzanie|\Z)", block, re.S)
        if not section:
            continue
        for degree, amount in re.findall(r"(pierwszego stopnia|drugiego stopnia|jednolite magisterskie)[^\n]*opłata za rok studiów\s*opłata jednorazowa[^\d]*?(\d{4,5})\s*zł", section.group(0), re.S):
            items.append(item(start.group(1), int(amount), None, {"pierwszego stopnia": "first cycle", "drugiego stopnia": "second cycle"}.get(degree, "long-cycle master's"), "part-time"))
    return items, 0


def parse_pwr(html: str) -> tuple[list[dict], int]:
    """Two tables on the admissions page, first then second cycle: fee per semester."""
    items: list[dict] = []
    for level, table in zip(("first cycle", "second cycle"), re.findall(r"<table.*?</table>", html, re.S)):
        faculty = None
        for row in re.findall(r"<tr.*?</tr>", table, re.S)[1:]:
            cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cell)).strip() for cell in re.findall(r"<td.*?</td>", row, re.S)]
            if len(cells) == 4:
                faculty = cells[0]
            if len(cells) >= 3 and re.fullmatch(r"\d[\d ]*", cells[-1]):
                items.append(item(cells[-3], int(cells[-1].replace(" ", "")) * 2, faculty, level, "part-time"))
    return items, 0


# Row names and levels of annex 5, in table order; the wrapped bilingual cells cannot be split reliably.
PG_ROWS = [
    ("Technologie materiałowe i recykling", "Chemiczny", ["second cycle"]), ("Informatyka", "Elektroniki, Telekomunikacji i Informatyki", ["first cycle", "second cycle"]),
    ("Automatyka, robotyka i systemy sterowania", "Elektrotechniki i Automatyki", ["second cycle"]), ("Elektrotechnika", "Elektrotechniki i Automatyki", ["first cycle", "second cycle"]),
    ("Budownictwo", "Inżynierii Lądowej i Środowiska", ["first cycle", "second cycle"]), ("Inżynieria środowiska", "Inżynierii Lądowej i Środowiska", ["first cycle", "second cycle"]),
    ("Mechanika i budowa maszyn", "Inżynierii Mechanicznej i Okrętownictwa", ["second cycle"]), ("Budowa maszyn i okrętów", "Inżynierii Mechanicznej i Okrętownictwa", ["first cycle"]),
    ("Okręty i konstrukcje morskie", "Inżynierii Mechanicznej i Okrętownictwa", ["second cycle"]), ("Analityka gospodarcza", "Zarządzania i Ekonomii", ["first cycle", "second cycle"]),
    ("Zarządzanie", "Zarządzania i Ekonomii", ["second cycle"]), ("Zarządzanie inżynierskie", "Zarządzania i Ekonomii", ["first cycle"]),
]


def parse_pg(text: str) -> tuple[list[dict], int]:
    """Annex 5: 'per semester' and 'per hour' pairs; the row list above fails loudly if the table changes."""
    table = text[text.rfind("Wysokość opłat za studia niestacjonarne"):]
    rows = [re.findall(r"(\d \d{3}),00 \d{2},00", line) for line in table.splitlines()]
    rows = [row for row in rows if row]
    if [len(row) for row in rows] != [len(levels) for _, _, levels in PG_ROWS]:
        raise ValueError(f"Annex 5 changed: {rows}")
    return [item(name, int(amount.replace(" ", "")) * 2, faculty, level, "part-time") for (name, faculty, levels), row in zip(PG_ROWS, rows) for level, amount in zip(levels, row)], 0


def parse_agh(text: str) -> tuple[list[dict], int]:
    """Annex 1: faculty rows without amounts, programme rows with one fee per semester."""
    items: list[dict] = []
    level, faculty = None, None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("Tabela"):
            level = "second cycle" if "DRUGIEGO" in line else "first cycle"
            continue
        match = re.match(r"^(.+?)\s+(\d{4})(?:\s+(?:\d{4}|-))+\s*$", line)
        if match:
            items.append(item(re.sub(r"(?<=[a-ząćęłńóśźż])\d$", "", match.group(1)), int(match.group(2)) * 2, faculty, level, "part-time"))
        elif level and re.match(r"^[A-ZŁŚŻŹ]", line) and not re.search(r"WYDZIAŁ|semestr|Strona|Załącznik|STUDIA|^I\s", line) and not re.search(r"\d", line):
            faculty = line
    return items, 0


def parse_amu(text: str) -> tuple[list[dict], int]:
    """Annex 1: per-semester fee by year of study (the register records these as semester fees). First year."""
    items = []
    for name, degree, amount in re.findall(r"^\d+\.\s+(.+?)\s+[\d,]+-letnie\s+(I stopnia|II stopnia|jednolite magisterskie)\s+(\d \d{3}|\d{3,4})\b", text, re.M):
        level = {"I stopnia": "first cycle", "II stopnia": "second cycle"}.get(degree, "long-cycle master's")
        items.append(item(name, int(amount.replace(" ", "")) * 2, None, level, "part-time"))
    return items, 0


def parse_ug(text: str) -> tuple[list[dict], int]:
    """Annex 1: instalment amounts; the notes say 6 instalments a year, 3 where a row carries '**'."""
    items = []
    level = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("Opłaty na"):
            level = "first cycle" if "pierwszego" in line else "second cycle" if "drugiego" in line else "long-cycle master's"
            continue
        match = re.match(r"^(.*?\S)\s+(\d \d{3}|\d{3}),00 zł$", line)
        if match and level and "**" not in match.group(1):
            name = re.sub(r"^\(.*?\)\s*", "", match.group(1)) or "Podatki i doradztwo podatkowe"
            items.append(item(name, int(match.group(2).replace(" ", "")) * 6, None, level, "part-time"))
    return items, 0


def parse_umcs(text: str) -> tuple[list[dict], int]:
    """Annex 2: first amount is the yearly fee; the name cell starts with the faculty."""
    faculties = ("Biologii i Biotechnologii", "Chemii", "Ekonomiczny", "Filologiczny", "Filozofii i Socjologii", "Historii i Archeologii", "Matematyki, Fizyki i Informatyki", "Nauk o Ziemi i Gospodarki Przestrzennej", "Pedagogiki i Psychologii", "Politologii i Dziennikarstwa", "Prawa i Administracji", "Artystyczny")
    items = []
    for cell, degree, amount in re.findall(r"^\d+\.\s+(.+?)\s+(pierwszy|piewszy|drugi|jednolite studia magisterskie)\s+niestacjonarne\s+(\d+ \d{3}),00 zł", text, re.M):
        faculty = next((name for name in faculties if cell.startswith(name)), None)
        name = cell[len(faculty):].strip() if faculty else cell
        level = {"pierwszy": "first cycle", "piewszy": "first cycle", "drugi": "second cycle"}.get(degree, "long-cycle master's")
        items.append(item(name, int(amount.replace(" ", "")), faculty, level, "part-time"))
    return items, 0


def parse_uj(text: str) -> tuple[list[dict], int]:
    """Annex: the first money group is Polish citizens, the second foreigners. Citizens pay only where the
    first group has amounts: part-time, or a foreign-language programme. First-year fee, in PLN."""
    items = []
    levels = {"1 st": "first cycle", "2 st": "second cycle", "jm": "long-cycle master's", "jsm": "long-cycle master's"}
    for line in text.splitlines():
        match = re.match(r"^\s*\d+\s+(.+?)\s+(1 st|2 st|jsm|jm)\s+(polski|obcy)\s+.*?PLN\s*(?:[A-Z]\d\s+)?PLN\s+(\d{1,3} \d{3}|\d{4,6})\s+(\d{1,2} \d{3}|\d{4,6})\b", line)
        if match:
            name, level, language, _total, first_year = match.groups()
            items.append(item(name, int(first_year.replace(" ", "")), None, levels[level], "part-time" if language == "polski" else "full-time in a foreign language"))
    return items, 0


def parse_ul(texts: list[str]) -> tuple[list[dict], int]:
    """Faculty annexes: a heading with the level, 'Kierunek: X', then the row for the 2026/2027 intake."""
    items = []
    for text in texts:
        faculty_match = re.search(r"WYDZIA[ŁL][^\n]*", text)
        for block in re.split(r"(?=STUDIA NIESTACJONARNE)", text):
            heading = block[:120].upper()
            level = "first cycle" if "PIERWSZEGO" in heading else "second cycle" if "DRUGIEGO" in heading else "long-cycle master's" if "JEDNOLITE" in heading else None
            for name, amount in re.findall(r"Kierunek(?:i)?:\s*([^\n]+?)\s*\n.*?2026/2027\s+I\s+(\d{1,2}\.\d{3}) zł", block, re.S):
                items.append(item(name.capitalize(), int(amount.replace(".", "")), None, level, "part-time"))
    return items, 0


_register_fees: list[dict] | None = None


def register_fees(name: str) -> tuple[list[dict], str]:
    """RAD-on 'fees charged to students': part-time fees of the latest year the university reported."""
    global _register_fees
    if _register_fees is None:
        rows, token = [], None
        for _ in range(200):
            page = client.get(f"{RADON}/courseFees", params={"resultNumbers": 100, **({"token": token} if token else {})}).json()
            rows += page["results"]
            token = page["pagination"].get("token")
            if not token or not page["results"]:
                break
        _register_fees = rows
    fees = [(row, fee) for row in _register_fees if row.get("institutionName") == name for fee in row.get("fees") or [] if fee.get("kindCode") == 1 and fee.get("frequency") in ("Semestralna", "Roczna")]
    if not fees:
        return [], ""
    year = max(fee["academicYear"] for _, fee in fees)
    levels = {"pierwszego stopnia": "first cycle", "drugiego stopnia": "second cycle"}
    items = [item(row["courseName"], fee["amount"] * (2 if fee["frequency"] == "Semestralna" else 1), None, levels.get(row.get("levelName"), "long-cycle master's"), "part-time") for row, fee in fees if fee["academicYear"] == year]
    return items, year


PARSERS = {"agh": parse_agh, "amu": parse_amu, "ug": parse_ug, "umcs": parse_umcs, "uj": parse_uj, "ul": parse_ul, "pw": parse_pw, "put": parse_put, "uwr": parse_uwr, "lodz": parse_lodz, "uw": parse_uw, "pwr": parse_pwr, "pg": parse_pg}


def parse_press(path: str) -> tuple[list[dict], str]:
    """Lines 'Programme – 67 тис. грн' from the article with all programmes of the university."""
    url = f"https://zaxid.net/{path}"
    response = client.get(url)
    response.raise_for_status()
    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", response.text, flags=re.S)
    html = html.replace("&nbsp;", " ").replace("&#8211;", "–").replace("&ndash;", "–")
    parts = [re.sub(r"\s+", " ", part).strip() for part in re.split(r"<[^>]+>", html)]
    items = []
    for part in parts:
        match = re.match(r"^(.{3,160}?)\s*[–—-]\s*(?:від\s+)?(\d+(?:[,.]\d+)?)\s*тис\.?\s*грн\.?$", part)
        if match and not re.search(r"вартість|коледж|молодш\w+ (?:бакалавр|спеціаліст)|для іноземців", match.group(1), re.I):
            items.append(item(match.group(1), float(match.group(2).replace(",", ".")) * 1000, None, "first cycle", "full-time"))
    return items, url


def summarise(items: list[dict], free: int, source: dict[str, str], kind: str, currency: str, academic_year: str = ACADEMIC_YEAR) -> dict[str, Any] | None:
    # A later row (an amendment) replaces an earlier one for the same programme, level and mode.
    latest = {(row["programme"].casefold(), row["level"], row["study_mode"]): row for row in items}
    paid = [row for row in latest.values() if row["amount_per_year"] > 0]
    if not paid:
        return None
    cheapest = min(paid, key=lambda row: row["amount_per_year"])
    dearest = max(paid, key=lambda row: row["amount_per_year"])
    return {
        "academic_year": academic_year, "currency": currency, "source_kind": kind, "source_title": source["title"], "source_url": source["url"],
        "min_per_year": cheapest["amount_per_year"], "max_per_year": dearest["amount_per_year"], "cheapest": cheapest, "most_expensive": dearest,
        "paid_programme_count": len(paid), "free_programme_count": free, "programmes": sorted(paid, key=lambda row: (row["amount_per_year"], row["programme"])),
    }


# ── Registers ──────────────────────────────────────────────────────────────────────────────────
def poland_entry(spec: dict) -> dict[str, Any]:
    name = spec["registry_name"]
    results = client.get(f"{RADON}/institutions", params={"name": name, "resultNumbers": 3}).json()["results"]
    record = next(row for row in results if row["name"] == name)
    # The registered seat, not the first historic row.
    address = next((row for row in record.get("addresses") or [] if row.get("street") == record.get("street")), {})
    number = address.get("bNumber") or record.get("building")
    street = " ".join(str(part) for part in (record.get("street"), number) if part)
    units: set[str] = set()
    names: set[tuple[str, str]] = set()
    programmes = 0
    token = None
    for _ in range(40):
        params = {"leadingInstitutionName": name, "resultNumbers": 100, **({"token": token} if token else {})}
        page = client.get(f"{RADON}/courses", params=params).json()
        for row in page["results"]:
            if row.get("currentStatusName") != "prowadzone" or row.get("leadingInstitutionName") != name:
                continue
            programmes += 1
            names.add((row.get("courseName") or "", {"pierwszego stopnia": "first cycle", "drugiego stopnia": "second cycle"}.get(row.get("levelName"), "long-cycle master's")))
            for unit in row.get("organizationalUnits") or []:
                units.add((unit.get("organizationalUnitFullName") or "").split(";")[-1].strip())
        token = page["pagination"].get("token")
        if not token or not page["results"]:
            break
    faculties = sorted(unit for unit in units if re.match(r"^(Międzyuczelniany )?Wydział", unit))
    entry = {
        "domain": spec["domain"], "directory_domains": DIRECTORY_DOMAINS.get(spec["domain"], []), "country": "Poland", "registry_name": name,
        "address": {"street": street, "postal_code": record.get("postalCd"), "city": record.get("city"), "source": "RAD-on (POL-on)", "source_url": RADON_PAGE},
        "faculties": faculties, "faculties_source": "RAD-on (POL-on)" if faculties else None, "programme_count": programmes, "fees": None,
        "study_programmes": [{"name": name, "level": level} for name, level in sorted(names) if name],
    }
    fee_spec = spec.get("fees")
    if fee_spec and fee_spec.get("register"):
        items, year = register_fees(name)
        entry["fees"] = summarise(items, 0, {"title": f"RAD-on register of student fees, {year}", "url": "https://radon.nauka.gov.pl/dane/oplaty-pobierane-od-studentow"}, "official", "PLN", year or ACADEMIC_YEAR)
    elif fee_spec and fee_spec.get("multi"):
        links = re.findall(r'href="([^"]+2026_2027\.pdf)"', client.get(fee_spec["multi"]).text)
        base = re.match(r"https://[^/]+", fee_spec["multi"]).group(0)
        items, free = PARSERS[fee_spec["parser"]]([pdf_text(base + link) for link in dict.fromkeys(links)])
        entry["fees"] = summarise(items, free, fee_spec, "official", "PLN")
    elif fee_spec:
        document = client.get(fee_spec["url"]).text if fee_spec.get("html") else pdf_text(fee_spec["url"])
        items, free = PARSERS[fee_spec["parser"]](document)
        for amendment in fee_spec.get("amendments", []):
            items += PARSERS[fee_spec["parser"]](pdf_text(amendment))[0]
        entry["fees"] = summarise(items, free, fee_spec, "official", "PLN")
    # The register's previous year is a sanity check on what was parsed from this year's document.
    if fee_spec and not fee_spec.get("register") and entry["fees"]:
        previous, year = register_fees(name)
        if previous:
            amounts = [row["amount_per_year"] for row in previous]
            print(f"  register {year}: {min(amounts):.0f}-{max(amounts):.0f} n={len(amounts)}")
    return entry


_regions: dict[int, list[dict]] = {}


def ukraine_entry(spec: dict) -> dict[str, Any]:
    region = spec["region"]
    if region not in _regions:
        _regions[region] = client.get(f"{EDEBO}/universities/", params={"ut": 1, "rg": region, "exp": "json"}).json()
    rows = _regions[region]
    wanted = re.sub(r"[\W_]+", " ", spec["edebo"]).casefold().strip()
    record = next((row for row in rows if wanted in re.sub(r"[\W_]+", " ", row["Назва закладу освіти"]).casefold() and not row.get("Код головного закладу")), None)
    if record is None:
        raise LookupError(f"{spec['edebo']} not in EDEBO region {region}; close: {[row['Назва закладу освіти'] for row in rows if wanted.split()[-1] in row['Назва закладу освіти'].casefold()][:4]}")
    items, url = parse_press(spec["press"])
    entry = {
        "domain": spec["domain"], "directory_domains": DIRECTORY_DOMAINS.get(spec["domain"], []), "country": "Ukraine", "registry_name": record["Назва закладу освіти"], "registry_name_en": record.get("Назва закладу освіти (англ.)"),
        "address": {"street": record["Адреса (місцезнаходження)"], "postal_code": record["Поштовий індекс (місцезнаходження)"], "city": record["Населений пункт (місцезнаходження)"],
                    "source": "EDEBO register", "source_url": f"https://registry.edbo.gov.ua/university/{record['Код']}/"},
        "founded": (record.get("Рік заснування") or "")[-4:] or None,
        "faculties": [], "faculties_source": None, "programme_count": len(items),
        "fees": summarise(items, 0, {"title": "ZAXID.NET list of approved prices, bachelor's full-time", "url": url}, "press", "UAH"),
    }
    expected = spec.get("expected")
    fees = entry["fees"]
    if expected and (not fees or abs(fees["min_per_year"] / 1000 - expected[0]) > .5 or abs(fees["max_per_year"] / 1000 - expected[1]) > .5):
        print(f"  CHECK {spec['domain']}: parsed {fees and (fees['min_per_year'], fees['max_per_year'])} but the press summary says {expected}")
    return entry


def main() -> None:
    entries, problems = [], []
    for spec, build in [(spec, poland_entry) for spec in POLAND] + [(spec, ukraine_entry) for spec in UKRAINE]:
        try:
            entry = build(spec)
            entries.append(entry)
            fees = entry["fees"]
            print(f"{entry['domain']:16} {entry['address']['street']}, {entry['address']['postal_code']} {entry['address']['city']} | faculties {len(entry['faculties'])} programmes {entry['programme_count']} | "
                  + (f"{fees['min_per_year']:.0f}-{fees['max_per_year']:.0f} {fees['currency']} n={fees['paid_programme_count']} free={fees['free_programme_count']} ({fees['cheapest']['programme'][:32]} .. {fees['most_expensive']['programme'][:32]})" if fees else "no fees"))
        except Exception as error:  # A failed source is reported and left out, never guessed.
            problems.append(f"{spec['domain']}: {type(error).__name__}: {str(error)[:240]}")
        time.sleep(.2)
    OUTPUT.write_text(json.dumps({"academic_year": ACADEMIC_YEAR, "universities": entries}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {len(entries)} universities to {OUTPUT}")
    for problem in problems:
        print("PROBLEM", problem)


if __name__ == "__main__":
    main()
