#!/usr/bin/env python
import glob

import pandas as pd
import re
import sys, os

def extract_year(filename):
    return int(re.search(r'\d+', filename)[0])

def main():
    HERE = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(HERE, "../csvs")
    # combine all files in the list
    os.chdir(csv_path)
    extension = 'csv'
    all_filenames = [i for i in glob.glob('*.csv')]

    combined_csv = pd.concat([pd.read_csv(f).assign(year=extract_year(os.path.basename(f))) for f in all_filenames])
    # export to csv
    combined_csv.to_csv("../combined_csv.csv", index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    main()
