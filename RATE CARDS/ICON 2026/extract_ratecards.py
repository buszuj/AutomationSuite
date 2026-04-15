import re
from pathlib import Path

import pandas as pd
import pdfplumber

PDF_PATH = Path(r"D:\BP TECH\Python apps\REPOs\AutomationSuite\RATE CARDS\ICON 2026\ICON_MSA_rates_28Jan2026_Internal_Temp 1.pdf")
OUT_PATH = PDF_PATH.with_name("ICON_2026_ratecards.xlsx")


def group_lines(words, y_tolerance=2.0):
    lines = []
    for w in sorted(words, key=lambda x: (x["top"], x["x0"])):
        if not lines or abs(lines[-1][0] - w["top"]) > y_tolerance:
            lines.append((w["top"], [w]))
        else:
            lines[-1][1].append(w)
    return lines


def extract_columns(lines, columns):
    rows = []
    for _, ws in lines:
        row = {name: [] for name, _, _ in columns}
        for w in ws:
            x = w["x0"]
            for name, min_x, max_x in columns:
                if min_x <= x < max_x:
                    row[name].append(w["text"])
                    break
        row = {k: " ".join(v).strip() for k, v in row.items()}
        if any(row.values()):
            rows.append(row)
    return rows


def is_header_row(text):
    header_markers = [
        "Language",
        "Translation",
        "Price List",
        "Attachment",
        "Hourly Service Charge",
        "UoM",
        "Rate",
    ]
    return any(marker.lower() in text.lower() for marker in header_markers)


def normalize_rate_text(rate_text):
    if not rate_text:
        return ""
    return rate_text.replace("$ ", "$").replace("$", "$")


def split_rates(rate_text):
    if not rate_text:
        return ["", "", "", ""]
    # Keep percentages or N/A as single rate
    if "%" in rate_text and "$" not in rate_text:
        return [rate_text.strip(), "", "", ""]
    if "N/A" in rate_text and "$" not in rate_text:
        return [rate_text.strip(), "", "", ""]

    # Split multiple $ rates like $235/$245
    parts = re.split(r"\s*/\s*", rate_text)
    parts = [p.strip() for p in parts if p.strip()]
    parts += [""] * (4 - len(parts))
    return parts[:4]


def build_per_word_rows(rows, rate_type_label, rate_cols):
    output = []
    for row in rows:
        combined = " ".join(row.values()).strip()
        if not combined or is_header_row(combined):
            continue
        if "$" not in combined:
            continue
        language = row.get("Language", "").strip()
        if not language:
            # Try to pull language from the leftmost column in case of parsing issues
            language = next((v for v in row.values() if v and not v.startswith("$")), "")
        rates = [row.get(col, "").strip() for col in rate_cols]
        output.append({
            "Rate Type": rate_type_label,
            "Service/Language": language,
            "UoM": "",
            "Rate 1": rates[0] if len(rates) > 0 else "",
            "Rate 2": rates[1] if len(rates) > 1 else "",
            "Rate 3": rates[2] if len(rates) > 2 else "",
            "Rate 4": rates[3] if len(rates) > 3 else "",
        })
    return output


def build_hourly_rows(rows, rate_type_label):
    output = []
    for row in rows:
        combined = " ".join(row.values()).strip()
        if not combined or is_header_row(combined):
            continue
        service = row.get("Service", "").strip()
        uom = row.get("UoM", "").strip()
        rate_text = normalize_rate_text(row.get("Rate", "").strip())
        if not service:
            continue
        rates = split_rates(rate_text)
        output.append({
            "Rate Type": rate_type_label,
            "Service/Language": service,
            "UoM": uom,
            "Rate 1": rates[0],
            "Rate 2": rates[1],
            "Rate 3": rates[2],
            "Rate 4": rates[3],
        })
    return output


def main():
    per_word_non_pfizer = []
    per_word_pfizer = []
    hourly_non_pfizer = []
    hourly_pfizer = []

    with pdfplumber.open(PDF_PATH) as pdf:
        # Page 1: per word rates
        page = pdf.pages[0]
        mid = page.width / 2
        words = page.extract_words()
        left_words = [w for w in words if w["x0"] < mid]
        right_words = [w for w in words if w["x0"] >= mid]

        left_lines = group_lines(left_words)
        right_lines = group_lines(right_words)

        left_columns = [
            ("Language", 0, 120),
            ("Rate1", 120, 160),
            ("Rate2", 160, 195),
            ("Rate3", 195, 230),
            ("Rate4", 230, 295),
        ]
        right_columns = [
            ("Language", 300, 380),
            ("Rate1", 380, 440),
            ("Rate2", 440, 490),
            ("Rate3", 490, 560),
        ]

        left_rows = extract_columns(left_lines, left_columns)
        right_rows = extract_columns(right_lines, right_columns)

        per_word_non_pfizer = build_per_word_rows(
            left_rows, "Per Word Rates", ["Rate1", "Rate2", "Rate3", "Rate4"]
        )
        per_word_pfizer = build_per_word_rows(
            right_rows, "Per Word Rates", ["Rate1", "Rate2", "Rate3"]
        )

        # Page 2: hourly service charge
        page = pdf.pages[1]
        mid = page.width / 2
        words = page.extract_words()
        left_words = [w for w in words if w["x0"] < mid]
        right_words = [w for w in words if w["x0"] >= mid]

        left_lines = group_lines(left_words)
        right_lines = group_lines(right_words)

        left_columns = [
            ("Service", 0, 150),
            ("UoM", 150, 240),
            ("Rate", 240, 300),
        ]
        right_columns = [
            ("Service", 300, 430),
            ("UoM", 430, 490),
            ("Rate", 490, 560),
        ]

        left_rows = extract_columns(left_lines, left_columns)
        right_rows = extract_columns(right_lines, right_columns)

        hourly_non_pfizer = build_hourly_rows(left_rows, "Hourly Service Charge")
        hourly_pfizer = build_hourly_rows(right_rows, "Hourly Service Charge")

    non_pfizer_table = pd.DataFrame(per_word_non_pfizer + hourly_non_pfizer)
    pfizer_table = pd.DataFrame(per_word_pfizer + hourly_pfizer)

    with pd.ExcelWriter(OUT_PATH, engine="openpyxl") as writer:
        non_pfizer_table.to_excel(writer, sheet_name="ICON_MSA_Price_List", index=False)
        pfizer_table.to_excel(writer, sheet_name="ICON_Pfizer_Price_List", index=False)

    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
