import datetime
import os
import time # We are processing a lot of data and dealing with a lot of endpoints, requests etc. Importing time just makes it easier and less riskywhen running a bunch of requests
import requests # Importing from the requests function so that we can use this on the website
import openpyxl
from openpyxl.styles import Font
from openpyxl.chart import LineChart, Reference
from dotenv import load_dotenv
import csv

load_dotenv(".env.local")
API_KEY = os.getenv("API_KEY")
Stocklist = "ipo_metadata.csv"
Output = "companies.csv"

# Get Endpoint is the function responsible from pulling the raw company data in JSON format

def getEndpoint(endpoint, parameters):
    baseUrl = "https://financialmodelingprep.com/stable" # The FMP website that I am pulling all the company data from
    endpointUrl = f"{baseUrl}/{endpoint}"

    request_parameters = parameters.copy()
    request_parameters["apikey"] = API_KEY

    response = requests.get(endpointUrl, params=request_parameters, timeout=20)
    response.raise_for_status()
    return response.json()

def read_metadata():
    with open(Stocklist, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        ticker_list = []
        for row in reader:
            ticker_list.append(row["ticker"])
        return ticker_list

tickers = read_metadata()

# for ticker in tickers:
    #profile_data = getEndpoint("profile", {"symbol": ticker})
    #print(profile_data)

# The following functions are meant for cleaning and structuring the raw JSON data from FMP into cleaned, structured fields that engine.py can use for scoring

# Historical pricing data function
def get_historical_prices(ticker):
    historical_prices = getEndpoint("historical-price-eod/full", {"symbol": ticker})
    cleaned_historical_prices = []
    for record in historical_prices:
        cleaned_record = {
            "date": record["date"],
            "close": record["close"],
            "volume": record["volume"]
        }
        cleaned_historical_prices.append(cleaned_record)
    return cleaned_historical_prices

# Market cap function
def get_market_cap(ticker):
    market_cap = getEndpoint("market-cap-eod", {"symbol": ticker})
    cleaned_market_cap = []
    for record in market_cap:
        cleaned_record = {
            "date": record["date"],
            "market_cap": record["marketCap"]
        }
        cleaned_market_cap.append(cleaned_record)
    return cleaned_market_cap

# Company revenue
def get_revenue(ticker):
    revenue = getEndpoint("income-statement", {"symbol": ticker})
    cleaned_revenue = []
    for record in revenue:
        cleaned_record = {
            "date": record["date"],
            "period": record["period"],
            "year": record["calendarYear"],
            "revenue": record["revenue"]
        }
        cleaned_revenue.append(cleaned_record)
    return cleaned_revenue