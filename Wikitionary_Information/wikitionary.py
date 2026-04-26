# -*- coding: utf-8 -*-
"""
Spyder Editor

This file scans wikitionary, then pastes the information into a spreadsheet
ready for manual verification that information provided is valid

@author willO
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# -----------------------------
#  ENGLISH HEADER DETECTION
# -----------------------------
def find_english_header(soup):
    return soup.find(id=re.compile(r"^English(_\d+)?$"))


# -----------------------------
#  DEFINITION EXTRACTION
# -----------------------------
def extract_definitions(soup, section_name):
    nodes = extract_section(soup, section_name)  # or Verb, Adjective, etc.
    definitions = []

    for node in nodes:
        if node.name == "ol":
            for li in node.find_all("li", recursive=False):
                text = li.get_text(" ", strip=True)
                if text:
                    definitions.append(text)

    return definitions


# -----------------------------
#  ETYMOLOGY EXTRACTION
# -----------------------------
def extract_information(soup, section_name):
    nodes = extract_section(soup, section_name)
    etym = []

    for node in nodes:
        if node.name == "p":
            text = node.get_text(" ", strip=True)
            if text:
                etym.append(text)

    return etym


# -----------------------------
#  PRONUNCIATION EXTRACTION
# -----------------------------
def extract_pronunciation(soup, section_name):
    nodes = extract_section(soup, section_name)
    ipa_list = []

    for node in nodes:
        for span in node.find_all("span", class_="IPA"):
            ipa = span.get_text(strip=True)
            if ipa:
                ipa_list.append(ipa)

    return ipa_list


def extract_section(soup, section_name):
    """
    Generalised DOM-aware extractor for any <h3 id="SectionName"> section.
    Returns a list of nodes belonging to that section.
    """

    target_div = None

    # 1. Find the heading wrapper div whose <h3> id matches section_name
    for div in soup.find_all("div", class_="mw-heading3"):
        h3 = div.find("h3")
        if not h3:
            continue
        sec_id = h3.get("id", "")
        if re.match(rf"^{section_name}(_\d+)?$", sec_id):
            target_div = div
            break

    if not target_div:
        return []

    # 2. Collect all nodes until the next heading div or <h2>
    nodes = []
    node = target_div.find_next_sibling()

    while node and not (
        (node.name == "div" and "mw-heading3" in (node.get("class") or []))
        or node.name == "h2"
    ):
        nodes.append(node)
        node = node.find_next_sibling()

    return nodes


# -----------------------------
#  FETCH PAGE
# -----------------------------
def fetch_wiktionary_entry(word):
    url = f"https://en.wiktionary.org/wiki/{word}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, features="html.parser")

    definitions = extract_definitions(soup, "Noun")
    etymology = extract_information(soup, "Etymology")
    pronunciation = extract_pronunciation(soup, "Pronunciation")

    return definitions, etymology, pronunciation


# -----------------------------
#  SAVE TO EXCEL
# -----------------------------
def save_to_excel(data, filename="wiktionary_data.xlsx"):
    df = pd.DataFrame(data, columns=["Word", "Definition", "Etymology", "Pronunciation"])
    df.to_excel(filename, index=False)
    print(f"Data saved to {filename}")


# -----------------------------
#  MAIN
# -----------------------------
if __name__ == "__main__":
    words_to_check = ["python", "algorithm", "computer"]

    collected_data = []

    for word in words_to_check:
        definitions, etymology, pronunciation = fetch_wiktionary_entry(word)

        ety = etymology[0] if etymology else "No etymology found"
        pron = pronunciation[0] if pronunciation else "No pronunciation found"
        if definitions:
            for d in definitions:
                collected_data.append([word, d, ety, pron])
        else:
            collected_data.append([word, "No definition found", ety, pron])

    save_to_excel(collected_data)


