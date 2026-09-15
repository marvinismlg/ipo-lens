# As the final python file of our Financial Data folder, build_companies is meant to act as flow control for our entire Financial Data pipeline.
# The job of this file is not to calculate metrics, understand tranches or merge Financial Data, but it is meant to organize Financial Data from all three of our main Financial Data files (sec_pipeline, spacex_pipeline, tickers_pipeline) and create one singular csv (companies.csv) with all the financial Financial Data necessary for our forecast.
# The structure has 5 parts:

# 1. Create a temporary working CSV, tell tickers_pipeline.py to generate the historical Yahoo comparable-company rows into that file
# 2. Tell spacex_pipeline.py to append the single continuous SPCX daily history
# 3. Tell sec_pipeline.py to repair missing historical fundamentals inside that same working file
# 4. Validate that the finished file has the structure the engine requires
# 5. Replace the temporary file Financial Data/companies.csv.

import csv
import os

# Here are the main data gathering functions that we will import. We will later run these functions in sequences so they do not overwrite our target csv file

from tickers_pipeline import generate_yahoo
from spacex_pipeline import generate_spacex
from sec_pipeline import supplement_sec_data

final_file = "Financial Data/companies.csv"
working_file = "Financial Data/temp.csv"

# A simple checker function in order to pinpoint potential minute errors

def check_csv(working_file):
    if not os.path.exists(working_file):
        raise ValueError("Working_file does not exist")

    with open(working_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)

        expected_fields = [
            "ticker", "date", "close", "volume", "market_cap", "revenue", "period", "year", "benchmark_close"
        ]

        if reader.fieldnames != expected_fields:
            raise ValueError("Incorrect Column Names")

        rows = list(reader)

        if len(rows) == 0:
            raise ValueError("Incorrect Number of Rows")

        found_tickers = set()

        for row in rows:
            found_tickers.add(row["ticker"])

        required_tickers = {"META", "BABA", "RKLB", "ASTS", "SPCX"}

        if not required_tickers.issubset(found_tickers):
            raise ValueError("Missing required tickers")
    return True

def build_companies():
    generate_yahoo(working_file)
    generate_spacex(working_file)
    supplement_sec_data(working_file)
    check_csv(working_file)
    os.replace(working_file, final_file)