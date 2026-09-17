# This py file is a separate file meant solely for generating the SpaceX tranches.
# SpaceX was added to ipo_metadata.csv later, thus, we had to generate the tranches every we generated companies.csv

import csv
import yfinance as yf

Stocklist = "Financial Data/ipo_metadata.csv"
Output = "Financial Data/companies.csv"
SPACEX_TICKER = "SPCX"


# Get Endpoint is the function responsible from pulling the raw company Financial Data in JSON format
# FMP is no longer used. This function now creates the yfinance Ticker object
# that the remaining Financial Data functions use.

def getEndpoint(endpoint, parameters):
    ticker = parameters["symbol"]
    company = yf.Ticker(ticker)
    return company


# Reads only the SpaceX rows from ipo_metadata.csv.
# The four rows remain separate because engine.py uses their separate tranche and lockup dates.
def read_spacex_metadata():
    spacex_rows = []
    with open(Stocklist, mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["ticker"] == SPACEX_TICKER:
                spacex_rows.append(row)
    if len(spacex_rows) == 0:
        raise ValueError("No SPCX rows found in ipo_metadata.csv")
    return spacex_rows

spacex_metadata = read_spacex_metadata()

# All four SPCX metadata rows represent the same IPO,
# so we use the IPO date from the first SpaceX metadata row.
spacex_ipo_date = spacex_metadata[0]["ipo_date"]


# The following functions are meant for cleaning and structuring the raw JSON Financial Data from FMP into cleaned, structured fields that engine.py can use for scoring

# Historical pricing Financial Data function
def get_historical_prices(ticker):
    company = getEndpoint("historical_prices", {"symbol": ticker})
    historical_prices = company.history(start=spacex_ipo_date,interval="1d",auto_adjust=False)
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
        start=spacex_ipo_date,
        interval="1d",
        auto_adjust=False)
    cleaned_market_cap = []
    if historical_prices.empty:
        return cleaned_market_cap
    shares = company.get_shares_full(
        start=spacex_ipo_date)
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
            "market_cap": calculated_market_cap}
        cleaned_market_cap.append(cleaned_record)
    return cleaned_market_cap

# Company revenue
def get_revenue(ticker):
    company = getEndpoint("revenue", {"symbol": ticker})
    income_statement = company.get_income_stmt(freq="quarterly")
    earnings_dates = company.get_earnings_dates(limit=100)
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
        quarterly_revenues.append({"period_date": period_date,"revenue": float(revenue_value)})
    quarterly_revenues.sort(
        key=lambda record: record["period_date"])
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
    benchmark = getEndpoint(
        "benchmark_prices",
        {"symbol": "SPY"}
    )
    benchmark_prices = benchmark.history(start=spacex_ipo_date,interval="1d",auto_adjust=False)
    cleaned_benchmark_prices = []
    for date, record in benchmark_prices.iterrows():
        cleaned_record = {
            "date": date.strftime("%Y-%m-%d"),
            "close": float(record["Close"])
        }
        cleaned_benchmark_prices.append(cleaned_record)
    return cleaned_benchmark_prices


# The function to organize all the API Financial Data into the fields that go into companies.csv
def collect_company_data():
    ticker = SPACEX_TICKER
    hp = get_historical_prices(ticker)
    if not hp:
        raise ValueError(
            f"{ticker}: no price rows from {spacex_ipo_date}"
        )
    mc = get_market_cap(ticker)
    r = get_revenue(ticker)
    company_record = {
        "ticker": ticker,
        "historical_prices": hp,
        "market_cap": mc,
        "revenue": r
    }

    return [company_record]

# Checks companies.csv so rerunning this file does not duplicate existing SpaceX dates.
def get_existing_spacex_dates(output_file):
    existing_spacex_dates = set()
    with open(output_file, mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["ticker"] == SPACEX_TICKER:
                existing_spacex_dates.add(row["date"])
    return existing_spacex_dates


# Writes the companies into the companies.csv in order to be prepared for scoring

def write_company_data(companies_input, output_file):
    existing_spacex_dates = get_existing_spacex_dates(output_file)
    benchmark_prices = get_benchmark_prices()
    benchmark_by_date = {}
    for record in benchmark_prices:
        benchmark_by_date[record["date"]] = record["close"]
    with open(output_file, mode="a", newline="") as csvfile:
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
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
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
                if current_date in existing_spacex_dates:
                    continue
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
                    "benchmark_close": benchmark_by_date.get(current_date)}
                writer.writerow(company_row)

def generate_spacex(output_file):
    companies_input = collect_company_data()
    write_company_data(companies_input, output_file)