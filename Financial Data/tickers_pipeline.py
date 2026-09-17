import datetime

import time # We are processing a lot of Financial Data and dealing with a lot of endpoints, requests etc. Importing time just makes it easier and less riskywhen running a bunch of requests
import requests # Importing from the requests function so that we can use this on the website
import openpyxl
from openpyxl.styles import Font
from openpyxl.chart import LineChart, Reference
from dotenv import load_dotenv
import csv
import yfinance as yf
import os
load_dotenv(".env.local")
API_KEY = os.getenv("API_KEY")
Stocklist = "ipo_metadata.csv"
Output = "companies.csv"

# Get Endpoint is the function responsible from pulling the raw company Financial Data in JSON format
# FMP is no longer used. This function now creates the yfinance Ticker object
# that the remaining Financial Data functions use.

def getEndpoint(endpoint, parameters):
    ticker = parameters["symbol"]
    company = yf.Ticker(ticker)
    return company


def read_metadata():
    with open(Stocklist, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        ticker_list = []
        for row in reader:
            ticker_list.append(row["ticker"])
        return ticker_list

# for ticker in tickers:
    #profile_data = getEndpoint("profile", {"symbol": ticker})
    #print(profile_data)

# The following functions are meant for cleaning and structuring the raw JSON Financial Data from FMP into cleaned, structured fields that engine.py can use for scoring

# Historical pricing Financial Data function
def get_historical_prices(ticker):
    company = getEndpoint("historical_prices", {"symbol": ticker})
    historical_prices = company.history(
        period="max",
        interval="1d",
        auto_adjust=False
    )
    cleaned_historical_prices = []
    for date, record in historical_prices.iterrows():
        cleaned_record = {
            "date": date.strftime("%Y-%m-%d"),
            "close": float(record["Close"]),
            "volume": int(record["Volume"])
        }
        cleaned_historical_prices.append(cleaned_record)
    return cleaned_historical_prices


# Market cap function
def get_market_cap(ticker):
    company = getEndpoint("market_cap", {"symbol": ticker})
    historical_prices = company.history(
        period="max",
        interval="1d",
        auto_adjust=False
    )
    cleaned_market_cap = []
    if historical_prices.empty:
        return cleaned_market_cap
    start_date = historical_prices.index.min().strftime("%Y-%m-%d")
    shares = company.get_shares_full(
        start=start_date
    )
    if shares is None or shares.empty:
        return cleaned_market_cap
    shares = shares.sort_index()
    for date, record in historical_prices.iterrows():
        available_shares = shares[shares.index <= date]
        if available_shares.empty:
            continue
        historical_shares = float(available_shares.iloc[-1])
        historical_price = float(record["Close"])
        calculated_market_cap = historical_price * historical_shares
        cleaned_record = {
            "date": date.strftime("%Y-%m-%d"),
            "market_cap": calculated_market_cap
        }
        cleaned_market_cap.append(cleaned_record)
    return cleaned_market_cap


# Company revenue
def get_revenue(ticker):
    company = getEndpoint("revenue", {"symbol": ticker})
    income_statement = company.get_income_stmt(
        freq="quarterly"
    )

    earnings_dates = company.get_earnings_dates(
        limit=100
    )
    cleaned_revenue = []
    if income_statement is None or income_statement.empty:
        return cleaned_revenue
    if earnings_dates is None or earnings_dates.empty:
        return cleaned_revenue
    if "Total Revenue" in income_statement.index:
        revenue_row = income_statement.loc["Total Revenue"]
    elif "TotalRevenue" in income_statement.index:
        revenue_row = income_statement.loc["TotalRevenue"]
    else:
        return cleaned_revenue
    quarterly_revenues = []
    for period_date, revenue_value in revenue_row.items():
        if revenue_value != revenue_value:
            continue
        quarterly_revenues.append({
            "period_date": period_date,
            "revenue": float(revenue_value)
        })
    quarterly_revenues.sort(
        key=lambda record: record["period_date"]
    )
    cleaned_earnings_dates = []
    for earnings_date in earnings_dates.index:
        if earnings_date.tzinfo is not None:
            earnings_date = earnings_date.tz_localize(None)
        cleaned_earnings_dates.append(earnings_date)
    cleaned_earnings_dates.sort()
    for index in range(3, len(quarterly_revenues)):
        current_quarter = quarterly_revenues[index]

        ttm_revenue = (
            quarterly_revenues[index]["revenue"]
            + quarterly_revenues[index - 1]["revenue"]
            + quarterly_revenues[index - 2]["revenue"]
            + quarterly_revenues[index - 3]["revenue"]
        )
        quarter_end = current_quarter["period_date"]
        reporting_date = None
        for earnings_date in cleaned_earnings_dates:
            if earnings_date >= quarter_end:
                reporting_date = earnings_date
                break
        if reporting_date is None:
            continue
        cleaned_record = {
            "date": reporting_date.strftime("%Y-%m-%d"),
            "period": "TTM",
            "year": quarter_end.year,
            "revenue": ttm_revenue
        }
        cleaned_revenue.append(cleaned_record)
    return cleaned_revenue


def get_benchmark_prices():
    benchmark = getEndpoint("benchmark_prices", {"symbol": "SPY"})

    benchmark_prices = benchmark.history(
        period="max",
        interval="1d",
        auto_adjust=False
    )
    cleaned_benchmark_prices = []
    for date, record in benchmark_prices.iterrows():
        cleaned_record = {
            "date": date.strftime("%Y-%m-%d"),
            "close": float(record["Close"]),
        }
        cleaned_benchmark_prices.append(cleaned_record)
    return cleaned_benchmark_prices


# The function to organize all the API Financial Data into the fields that go into companies.csv
def collect_company_data():
    metadata_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ipo_metadata.csv"
    )

    with open(metadata_path, newline="", encoding="utf-8-sig") as csvfile:
        metadata_rows = list(csv.DictReader(csvfile))

    ticker_dates = {}
    for row in metadata_rows:
        ticker = row["ticker"].strip().upper()
        if ticker and ticker != "SPCX":
            ticker_dates.setdefault(ticker, row["ipo_date"].strip())

    required = {"META", "BABA", "RKLB", "ASTS"}
    missing = required - set(ticker_dates)

    if missing:
        raise ValueError(
            f"Metadata missing {sorted(missing)}. "
            f"Reading: {metadata_path}. "
            f"Metadata rows: {len(metadata_rows)}"
        )

    results = []

    for ticker, ipo_date in ticker_dates.items():
        prices = get_historical_prices(ticker)
        hp = [
            record for record in prices
            if record["date"] >= ipo_date
        ]

        if not hp:
            raise ValueError(
                f"{ticker}: Yahoo returned {len(prices)} price rows; "
                f"0 remain after IPO date {ipo_date}"
            )

        results.append({
            "ticker": ticker,
            "historical_prices": hp,
            "market_cap": get_market_cap(ticker),
            "revenue": get_revenue(ticker),
        })

    return results

# Writes the companies into the companies.csv in order to be prepared for scoring

def write_company_data(companies_input, output_file):
    benchmark_prices = get_benchmark_prices()
    benchmark_by_date = {}
    for record in benchmark_prices:
        benchmark_by_date[record["date"]] = record["close"]
    with open(output_file, mode="w", newline="") as csvfile:
        fieldnames = [
            "ticker",
            "date",
            "close",
            "volume",
            "market_cap",
            "revenue",
            "period",
            "year",
            "benchmark_close"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for company in companies_input:
            ticker = company["ticker"]
            historical_prices = company["historical_prices"]
            market_caps = company["market_cap"]
            revenues = company["revenue"]
            market_cap_by_date = {}
            for record in market_caps:
                market_cap_by_date[record["date"]] = record["market_cap"]
            revenues_sorted = sorted(
                revenues,
                key=lambda record: record["date"])
            for price_record in historical_prices:
                current_date = price_record["date"]
                most_recent_revenue = None
                for revenue_record in revenues_sorted:
                    if revenue_record["date"] <= current_date:
                        most_recent_revenue = revenue_record
                    else:
                        break
                if most_recent_revenue is not None:
                    revenue = most_recent_revenue["revenue"]
                    period = most_recent_revenue["period"]
                    year = most_recent_revenue["year"]
                else:
                    revenue = None
                    period = None
                    year = None
                company_row = {
                    "ticker": ticker,
                    "date": current_date,
                    "close": price_record["close"],
                    "volume": price_record["volume"],
                    "market_cap": market_cap_by_date.get(current_date),
                    "revenue": revenue,
                    "period": period,
                    "year": year,
                    "benchmark_close": benchmark_by_date.get(current_date),
                }
                writer.writerow(company_row)

def generate_yahoo(output_file):
    companies_input = collect_company_data()
    write_company_data(companies_input, output_file)

