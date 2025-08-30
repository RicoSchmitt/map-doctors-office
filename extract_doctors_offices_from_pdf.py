#!/usr/bin/env python3
"""
Parse Ärzte PDF into structured CSV with consistent headers across all pages.
"""

import pandas as pd
import camelot

PDF_FILE = "insert-path-to-downloaded-pdf/liste.pdf"
OUTPUT_CSV = "aerzte_extracted_structured.csv"


def main():
    # Extract all tables, try lattice first, fall back to stream if needed
    try:
        tables = camelot.read_pdf(PDF_FILE, pages="all", flavor="lattice", strip_text="\n")
        if len(tables) == 0:
            raise ValueError
    except Exception:
        tables = camelot.read_pdf(PDF_FILE, pages="all", flavor="stream", strip_text="\n")

    if not tables:
        raise RuntimeError("No tables detected on any page.")

    frames = []
    header = None

    for idx, t in enumerate(tables):
        df = t.df.copy()
        df = df.applymap(lambda x: " ".join(str(x).split()))

        if idx == 0:
            # First table: take header from the first row
            header = df.iloc[0].tolist()
            df = df[1:]
            df.columns = header
        else:
            # Reindex columns to match header length
            if header is not None:
                cols = len(header)
                # pad or truncate this df to match
                if df.shape[1] < cols:
                    for _ in range(cols - df.shape[1]):
                        df[df.shape[1]] = ""
                elif df.shape[1] > cols:
                    df = df.iloc[:, :cols]
                df.columns = header
        frames.append(df)

    full = pd.concat(frames, ignore_index=True)
    full.columns = header  # enforce consistent columns

    # Keep only columns relevant for mapping and choice on Moses
    keep_cols = [
        "ID",
        "Fachgebiet",
        "Schwerpunkte / Angebote / Bemerkungen",
        "Vorname",
        "Name",
        "Straße",
        "PLZ",
        "Ort",
        "Bemerkung",
    ]
    cols_present = [c for c in keep_cols if c in full.columns]
    full = full[cols_present]

    # Cleanup whitespace
    for c in full.columns:
        full[c] = full[c].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

    full.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"Extracted {len(full)} rows -> {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
