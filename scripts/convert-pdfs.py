#!/usr/bin/env python
import pdfplumber
import pandas as pd
import re
import sys, os

# MIN_YR = 2018
MIN_YR = 2007
# MAX_YR = 2019
MAX_YR = 2019
COLUMNS = [
    "club", "last_name", "first_name",
    "position", "base_salary", "guaranteed_compensation"
]

NON_MONEY_CHAR_PAT = re.compile(r"[^\d\.]")


def parse_money(money_str):
    stripped = re.sub(NON_MONEY_CHAR_PAT, "", money_str)
    if len(stripped):
        return float(stripped)
    else:
        return None


def apply_alias(club_str):
    aliases = {
        "CHI": "Chicago Fire",
        "CLB": "Columbus Crew",
        "COL": "Colorado Rapids",
        "DAL": "FC Dallas",
        "DC": "DC United",
        "HOU": "Houston Dynamo",
        "KC": "Sporting Kansas City",
        "LA": "LA Galaxy",
        "NE": "New England Revolution",
        "NY": "New York Red Bulls",
        "RSL":"Real Salt Lake",
        "TFC":"Toronto FC",
        "SJ":"San Jose Earthquakes",
        "SEA":"Seattle Sounders FC",
        "PHI":"Philadelphia Union",
        "VAN":"Vancouver Whitecaps",
        "POR":"Portland Timbers",
        "TOR":"Toronto FC",
        "MTL": "Montreal Impact",
        "ORL": "Orlando City SC",
        "NYCFC": "New York City FC",
        "ATL": "Atlanta United",
        "NYRB": "New York Red Bulls",
        "MNUFC": "Minnesota United",
    }
    return aliases.get(club_str, club_str)

def get_data_bbox(page, year):
    words = page.extract_words()
    last_cell_ix = len(words) - 1
    first_cell_ix = 1

    # they changed the format in 2019... headers only show up on the first page
    if year >= 2019:
        if page.page_number == 1:
            first_cell_ix = 22
    else:
        texts = [w["text"] for w in words]
        first_cell_ix = texts.index("Compensation") + 1
        last_cell_ix = texts.index("Source:")

    data_words = words[first_cell_ix:last_cell_ix]
    dw_df = pd.DataFrame(data_words)

    # print(first_cell_ix, last_cell_ix)
    # print(words[first_cell_ix])
    # print(words[last_cell_ix])

    return (
        dw_df["x0"].min(),
        dw_df["top"].min(),
        dw_df["x1"].max(),
        dw_df["bottom"].max(),
    )


def get_gutters(cropped):
    x0s = pd.DataFrame(cropped.chars)["x0"].astype(float) \
        .sort_values() \
        .drop_duplicates()

    gutter_ends = pd.DataFrame({
        "x0": x0s,
        "dist": x0s - x0s.shift(1),
    }).sort_values("dist", ascending=False) \
        .pipe(lambda x: x[x["dist"] > 10])["x0"].sort_values() \
        .astype(int).tolist()

    return gutter_ends


def parse_page(page, year):
    sys.stdout.write("{}, page {}\n".format(year, page.page_number))

    data_bbox = get_data_bbox(page, year)
    cropped = page.within_bbox(data_bbox)
    gutters = get_gutters(cropped)

    v_lines = [cropped.bbox[0]] + gutters + [cropped.bbox[2]]

    table = cropped.extract_table({
        "vertical_strategy": "explicit",
        "explicit_vertical_lines": v_lines,
        "horizontal_strategy": "text",
    })

    df = pd.DataFrame(table, columns=COLUMNS)
    df["club"] = df["club"].apply(apply_alias)
    df["base_salary"] = df["base_salary"].apply(parse_money)
    df["guaranteed_compensation"] = df["guaranteed_compensation"].apply(parse_money)

    return df


def parse_pdf(path, year):
    with pdfplumber.open(path) as pdf:
        df = pd.concat([parse_page(page, year) for page in pdf.pages])
    return df


def main():
    HERE = os.path.dirname(os.path.abspath(__file__))
    for year in range(MIN_YR, MAX_YR + 1):
        print(year)
        pdf_path = os.path.join(HERE, "../pdfs/mls-salaries-{0}.pdf".format(year))
        csv_path = os.path.join(HERE, "../csvs/mls-salaries-{0}.csv".format(year))
        df = parse_pdf(pdf_path, year)
        df.to_csv(csv_path, index=False)


if __name__ == "__main__":
    main()
