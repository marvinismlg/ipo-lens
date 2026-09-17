# This file is meant to be more of a repair pipeline. The issue we ran into with the original companies.csv is that plenty of fields were empty (null)
# To fix this, we need to supplement all the missing historical Financial Data from the SEC in order to keep companies.csv consistent

import requests
import csv
import datetime
from sec_share_fallback import repair_lockup_market_caps


# Sec filings might return incomplete thus error logging would be useful for sec_indigestion as well
# Because this file is slightly lengthy, we might need quite a few error messages in order to fully accommodate each potential problem spot

Error_Logs = 'error_logs.csv'

error_types = [
    "SEC Request Failure",
    "Missing Revenue Concept",
    "Missing Revenue Data",
    "TTM Revenue Failure",
    "Invalid Q4 Calculation",
    "Missing Shares Data",
    "Working CSV Failure",
    "Missing SEC Mapping",
    "Market Cap Failure",
    "Unresolved Supplemental Data"
]


function_names = [
    "get_sec_company_facts",
    "find_revenue_concept",
    "extract_revenue_facts",
    "build_ttm_revenue",
    "extract_shares_outstanding",
    "read_working_companies",
    "supplement_sec_data",
    "write_working_companies"
]

errors = {
    "sec_request_failed": {
        "Function Name": function_names[0],
        "Error Type": error_types[0],
        "Message": "SEC request failed or returned an invalid response",
        "Severity": "High"
    },
    "missing_revenue_concept": {
        "Function Name": function_names[1],
        "Error Type": error_types[1],
        "Message": "No supported SEC revenue concept was found for this company",
        "Severity": "High"
    },
    "missing_revenue_observations": {
        "Function Name": function_names[2],
        "Error Type": error_types[2],
        "Message": "SEC revenue concept exists but contains no usable USD observations",
        "Severity": "High"
    },
    "empty_ttm_input": {
        "Function Name": function_names[3],
        "Error Type": error_types[3],
        "Message": "TTM revenue cannot be calculated because no cleaned revenue records were provided",
        "Severity": "High"
    },
    "insufficient_quarters": {
        "Function Name": function_names[3],
        "Error Type": error_types[3],
        "Message": "TTM revenue cannot be calculated because fewer than four usable quarterly records exist",
        "Severity": "High"
    },
    "invalid_q4": {
        "Function Name": function_names[3],
        "Error Type": error_types[4],
        "Message": "Calculated fourth-quarter revenue was negative and cannot be trusted",
        "Severity": "Mid"
    },
    "no_ttm_records": {
        "Function Name": function_names[3],
        "Error Type": error_types[3],
        "Message": "Revenue records existed but no valid TTM revenue records could be produced",
        "Severity": "High"
    },
    "missing_shares": {
        "Function Name": function_names[4],
        "Error Type": error_types[5],
        "Message": "No usable SEC shares-outstanding records were found",
        "Severity": "High"
    },
    "empty_working_file": {
        "Function Name": function_names[5],
        "Error Type": error_types[6],
        "Message": "Working companies CSV contains zero rows",
        "Severity": "High"
    },
    "missing_sec_mapping": {
        "Function Name": function_names[6],
        "Error Type": error_types[7],
        "Message": "Ticker requires SEC supplementation but has no valid CIK or taxonomy mapping",
        "Severity": "Mid"
    },
    "missing_close": {
        "Function Name": function_names[6],
        "Error Type": error_types[8],
        "Message": "Market cap cannot be calculated because the daily close value is missing",
        "Severity": "High"
    },
    "unresolved_revenue": {
        "Function Name": function_names[6],
        "Error Type": error_types[9],
        "Message": "Revenue remains missing after SEC supplementation",
        "Severity": "Mid"
    },
    "unresolved_market_cap": {
        "Function Name": function_names[6],
        "Error Type": error_types[9],
        "Message": "Market cap remains missing after SEC supplementation",
        "Severity": "Mid"
    },
    "empty_write": {
        "Function Name": function_names[7],
        "Error Type": error_types[6],
        "Message": "Refusing to overwrite working CSV because there are zero company rows",
        "Severity": "High"
    }
}


def error_logging(error_key):
    if error_key not in errors:
        return
    with open(Error_Logs, mode="a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        error_dict = errors[error_key]
        writer.writerow([timestamp,error_dict["Function Name"],error_dict["Error Type"],error_dict["Message"],error_dict["Severity"]])

# We need to add a header in order to tell the SEC that we are not a bot

sec_headers = {
    "User-Agent": "IPO-LENS mjtchoukouahatientch@loyola.edu"
}

# CIK is the universal identifier for each one of these companies.

ticker_to_cik = {
    "META": "0001326801",
    "BABA": "0001577552",
    "ASTS": "0001780312",
    "RKLB": "0001819994",
}

ticker_to_taxonomy = {
    "META": "us-gaap",
    "BABA": "us-gaap",
    "ASTS": "us-gaap",
    "RKLB": "us-gaap",
}

us_gaap_revenue_concepts = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"]

ifrs_revenue_concepts = ["Revenue"]

def get_sec_company_facts(cik):
    padded_cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{padded_cik}.json"

    try:
        response = requests.get(url, headers=sec_headers, timeout=30)
        response.raise_for_status()
        company_facts = response.json()
    except requests.exceptions.RequestException:
        error_logging("sec_request_failed")
        raise
    return company_facts


def find_revenue_concept(company_facts, taxonomy):
    taxonomy_facts = company_facts.get("facts", {}).get(taxonomy, {})
    if taxonomy == "us-gaap":
        concept_candidates = us_gaap_revenue_concepts
    else:
        concept_candidates = ifrs_revenue_concepts
    for concept in concept_candidates:
        if concept in taxonomy_facts:
            return concept
    error_logging("missing_revenue_concept")
    return None

# We had to edit this function as a result of the errors we received when running our code on September 15th 2026

def extract_revenue_facts(company_facts, taxonomy):
    raw_revenue_records = []
    if find_revenue_concept(company_facts, taxonomy) is None:
        return raw_revenue_records
    taxonomy_facts = company_facts.get("facts", {}).get(taxonomy, {})
    if taxonomy == "us-gaap":
        concept_candidates = us_gaap_revenue_concepts
    else:
        concept_candidates = ifrs_revenue_concepts
    supported_concepts = [concept for concept in concept_candidates if concept in taxonomy_facts]
    valid_forms = {"10-Q", "10-K", "10-Q/A", "10-K/A", "20-F", "20-F/A", "6-K", "6-K/A"}
    concept_priority = {concept:index for index,concept in enumerate(concept_candidates)}
    records_by_period = {}
    for concept in supported_concepts:
        revenue_observations = (
            taxonomy_facts
            .get(concept, {})
            .get("units", {})
            .get("USD", [])
        )
        for observation in revenue_observations:
            if observation.get("form") not in valid_forms:
                continue
            if not all(observation.get(field) is not None for field in ["start", "end", "val", "filed"]):
                continue
            cleaned_record = {
                "start_date": observation["start"],
                "end_date": observation["end"],
                "available_date": observation["filed"],
                "value": float(observation["val"]),
                "form": observation.get("form"),
                "fiscal_year": observation.get("fy"),
                "fiscal_period": observation.get("fp")}
            period_key = (cleaned_record["start_date"], cleaned_record["end_date"])
            existing = records_by_period.get(period_key)
            current_priority = concept_priority[concept]
            if existing is None:
                records_by_period[period_key] = (cleaned_record,current_priority)
                continue
            existing_record,existing_priority = existing
            if cleaned_record["available_date"] < existing_record["available_date"]:
                records_by_period[period_key] = (cleaned_record,current_priority)
            elif cleaned_record["available_date"] == existing_record["available_date"] and current_priority < existing_priority:
                records_by_period[period_key] = (cleaned_record,current_priority)
    if len(records_by_period) == 0:
        error_logging("missing_revenue_observations")
        return raw_revenue_records
    raw_revenue_records = [record for record,_ in records_by_period.values()]
    raw_revenue_records.sort(key=lambda record:(record["available_date"],record["end_date"]))
    return raw_revenue_records
# Period + Revenue generation fix

def build_ttm_revenue(raw_revenue_records):
    if len(raw_revenue_records) == 0:
        error_logging("empty_ttm_input")
        return []
    quarterly_by_end = {}
    six_month_by_end = {}
    nine_month_by_end = {}
    annual_by_end = {}
    def store_best(container,key,record):
        existing = container.get(key)
        if existing is None or record["available_date"] < existing["available_date"]:
            container[key] = record
    for record in raw_revenue_records:
        start_date = datetime.date.fromisoformat(record["start_date"])
        end_date = datetime.date.fromisoformat(record["end_date"])
        duration = (end_date - start_date).days + 1
        normalized_record = {
            "start_date": record["start_date"],
            "end_date": record["end_date"],
            "available_date": record["available_date"],
            "value": record["value"],
            "fiscal_year": record["fiscal_year"]}
        if 70 <= duration <= 110:
            store_best(quarterly_by_end,record["end_date"],normalized_record)
        elif 150 <= duration <= 220:
            store_best(six_month_by_end,record["end_date"],normalized_record)
        elif 240 <= duration <= 300:
            store_best(nine_month_by_end,record["end_date"],normalized_record)
        elif 330 <= duration <= 380:
            store_best(annual_by_end,record["end_date"],normalized_record)
    for six_month in six_month_by_end.values():
        if six_month["end_date"] in quarterly_by_end:
            continue
        first_quarters = [
            quarter for quarter in quarterly_by_end.values()
            if quarter["start_date"] == six_month["start_date"] and quarter["end_date"] < six_month["end_date"]]
        if len(first_quarters) == 0:
            continue
        first_quarter = max(first_quarters,key=lambda record:record["end_date"])
        derived_value = six_month["value"] - first_quarter["value"]
        if derived_value < 0:
            continue
        derived_start = (datetime.date.fromisoformat(first_quarter["end_date"]) + datetime.timedelta(days=1)).isoformat()
        quarterly_by_end[six_month["end_date"]] = {
            "start_date": derived_start,
            "end_date": six_month["end_date"],
            "available_date": max(six_month["available_date"],first_quarter["available_date"]),
            "value": derived_value,
            "fiscal_year": six_month["fiscal_year"]}
    for nine_month in nine_month_by_end.values():
        if nine_month["end_date"] in quarterly_by_end:
            continue
        matching_six_months = [
            six_month for six_month in six_month_by_end.values()
            if six_month["start_date"] == nine_month["start_date"] and six_month["end_date"] < nine_month["end_date"]]
        if len(matching_six_months) == 0:
            continue
        six_month = max(matching_six_months,key=lambda record:record["end_date"])
        derived_value = nine_month["value"] - six_month["value"]
        if derived_value < 0:
            continue
        derived_start = (datetime.date.fromisoformat(six_month["end_date"]) + datetime.timedelta(days=1)).isoformat()
        quarterly_by_end[nine_month["end_date"]] = {
            "start_date": derived_start,
            "end_date": nine_month["end_date"],
            "available_date": max(nine_month["available_date"],six_month["available_date"]),
            "value": derived_value,
            "fiscal_year": nine_month["fiscal_year"]}
    for annual_record in annual_by_end.values():
        annual_end = annual_record["end_date"]
        if annual_end in quarterly_by_end:
            continue
        matching_nine_months = [
            nine_month for nine_month in nine_month_by_end.values()
            if nine_month["start_date"] == annual_record["start_date"] and nine_month["end_date"] < annual_end]
        fourth_quarter_value = None
        fourth_quarter_start = None
        available_date = annual_record["available_date"]
        if len(matching_nine_months) > 0:
            nine_month = max(matching_nine_months,key=lambda record:record["end_date"])
            fourth_quarter_value = annual_record["value"] - nine_month["value"]
            fourth_quarter_start = (datetime.date.fromisoformat(nine_month["end_date"]) + datetime.timedelta(days=1)).isoformat()
            available_date = max(annual_record["available_date"],nine_month["available_date"])
        else:
            usable_quarters = [
                quarter for quarter in quarterly_by_end.values()
                if annual_record["start_date"] <= quarter["start_date"] and quarter["end_date"] < annual_end]
            usable_quarters.sort(key=lambda record:record["end_date"])
            if len(usable_quarters) >= 3:
                first_three = usable_quarters[:3]
                fourth_quarter_value = annual_record["value"] - sum(record["value"] for record in first_three)
                fourth_quarter_start = (datetime.date.fromisoformat(first_three[-1]["end_date"]) + datetime.timedelta(days=1)).isoformat()
                available_date = max([annual_record["available_date"]] + [record["available_date"] for record in first_three])
        if fourth_quarter_value is None:
            continue
        if fourth_quarter_value < 0:
            error_logging("invalid_q4")
            continue
        quarterly_by_end[annual_end] = {
            "start_date": fourth_quarter_start,
            "end_date": annual_end,
            "available_date": available_date,
            "value": fourth_quarter_value,
            "fiscal_year": annual_record["fiscal_year"]}
    ttm_by_end = {}
    for annual_record in annual_by_end.values():
        fiscal_year = annual_record["fiscal_year"]
        if fiscal_year is None:
            fiscal_year = datetime.date.fromisoformat(annual_record["end_date"]).year
        ttm_by_end[annual_record["end_date"]] = {
            "available_date": annual_record["available_date"],
            "period": "TTM",
            "year": fiscal_year,
            "revenue": annual_record["value"]}
    quarterly_revenues = sorted(quarterly_by_end.values(),key=lambda record:record["end_date"])
    for index in range(3,len(quarterly_revenues)):
        four_quarters = quarterly_revenues[index - 3:index + 1]
        consecutive = True
        for quarter_index in range(1,len(four_quarters)):
            previous_end = datetime.date.fromisoformat(four_quarters[quarter_index - 1]["end_date"])
            current_end = datetime.date.fromisoformat(four_quarters[quarter_index]["end_date"])
            gap = (current_end - previous_end).days
            if gap < 60 or gap > 130:
                consecutive = False
                break
        if not consecutive:
            continue
        available_date = max(record["available_date"] for record in four_quarters)
        ttm_revenue = sum(record["value"] for record in four_quarters)
        last_quarter = four_quarters[-1]
        fiscal_year = last_quarter["fiscal_year"]
        if fiscal_year is None:
            fiscal_year = datetime.date.fromisoformat(last_quarter["end_date"]).year
        ttm_record = {
            "available_date": available_date,
            "period": "TTM",
            "year": fiscal_year,
            "revenue": ttm_revenue}
        existing_ttm = ttm_by_end.get(last_quarter["end_date"])
        if existing_ttm is None or ttm_record["available_date"] < existing_ttm["available_date"]:
            ttm_by_end[last_quarter["end_date"]] = ttm_record
    if len(ttm_by_end) == 0:
        if len(quarterly_revenues) < 4:
            error_logging("insufficient_quarters")
        error_logging("no_ttm_records")
        return []
    ttm_revenue_records = [
        record for _,record in sorted(
            ttm_by_end.items(),
            key=lambda item:(item[1]["available_date"],item[0]))]
    return ttm_revenue_records

def extract_shares_outstanding(company_facts):
    share_records = []
    share_observations = (
        company_facts
        .get("facts", {})
        .get("dei", {})
        .get("EntityCommonStockSharesOutstanding", {})
        .get("units", {})
        .get("shares", []))
    if len(share_observations) == 0:
        error_logging("missing_shares")
        return share_records
    valid_forms = {"10-Q", "10-K", "10-Q/A", "10-K/A", "20-F", "20-F/A", "6-K", "6-K/A"}
    seen_records = set()
    for observation in share_observations:
        if observation.get("form") not in valid_forms:
            continue
        if observation.get("end") is None or observation.get("filed") is None or observation.get("val") is None:
            continue
        record_key = (
            observation["end"],
            observation["filed"],
            observation["val"])
        if record_key in seen_records:
            continue
        seen_records.add(record_key)
        share_records.append({
            "period_date": observation["end"],
            "available_date": observation["filed"],
            "shares": float(observation["val"])})
    share_records.sort(key=lambda record: record["available_date"])
    if len(share_records) == 0:
        error_logging("missing_shares")
    return share_records


def read_working_companies(working_file):
    company_rows = []
    with open(working_file, mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            company_rows.append(row)
    if len(company_rows) == 0:
        error_logging("empty_working_file")
        raise ValueError("Working companies CSV contains no rows")
    return company_rows


def is_blank(value):
    if value is None:
        return True
    return str(value).strip().lower() in {"", "null", "none", "nan"}

def write_working_companies(working_file, company_rows):
    if len(company_rows) == 0:
        error_logging("empty_write")
        raise ValueError("Cannot overwrite working CSV with zero rows")
    fieldnames = [
        "ticker",
        "date",
        "close",
        "volume",
        "market_cap",
        "revenue",
        "period",
        "year",
        "benchmark_close"]
    with open(working_file, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in company_rows:
            writer.writerow(row)

def supplement_sec_data(working_file):
    company_rows = read_working_companies(working_file)
    tickers_needing_sec = {
        row["ticker"]
        for row in company_rows
        if any(is_blank(row.get(field)) for field in (
            "market_cap", "revenue", "period", "year"
        ))
    }

    for ticker in sorted(tickers_needing_sec):
        if ticker not in ticker_to_cik or ticker not in ticker_to_taxonomy:
            error_logging("missing_sec_mapping")
            continue

        # Keep this value intact. The previous diagnostic loop overwrote it.
        taxonomy = ticker_to_taxonomy[ticker]
        company_facts = get_sec_company_facts(ticker_to_cik[ticker])
        raw_revenue = extract_revenue_facts(company_facts, taxonomy)
        ttm_revenue = build_ttm_revenue(raw_revenue)

        # META classes and BABA ADS units are handled by the verified fallback.
        # A raw BABA ordinary-share count cannot be multiplied blindly by an
        # ADS price, especially after later share splits.
        share_records = (
            extract_shares_outstanding(company_facts)
            if ticker in {"ASTS", "RKLB"}
            else []
        )

        for row in company_rows:
            if row["ticker"] != ticker:
                continue
            current_date = row["date"]
            eligible_revenue = [
                record for record in ttm_revenue
                if record["available_date"] <= current_date
            ]
            if eligible_revenue:
                latest_revenue = eligible_revenue[-1]
                if is_blank(row.get("revenue")):
                    row["revenue"] = latest_revenue["revenue"]
                    row["period"] = latest_revenue["period"]
                    row["year"] = latest_revenue["year"]
                else:
                    for field in ("period", "year"):
                        if is_blank(row.get(field)):
                            row[field] = latest_revenue[field]

            if is_blank(row.get("market_cap")) and share_records:
                eligible_shares = [
                    record for record in share_records
                    if record["available_date"] <= current_date
                ]
                if is_blank(row.get("close")):
                    error_logging("missing_close")
                elif eligible_shares:
                    latest_shares = max(
                        eligible_shares,
                        key=lambda record: (
                            record["period_date"], record["available_date"]
                        )
                    )
                    row["market_cap"] = (
                        float(row["close"]) * latest_shares["shares"]
                    )

    # Reads original filings, fills required missing caps, and validates the
    # latest pre-lockup row for all five tickers before writing the CSV.
    repaired = repair_lockup_market_caps(
        company_rows, working_file, sec_headers
    )
    write_working_companies(working_file, company_rows)
    print(f"Original SEC filings repaired {repaired} daily market caps")
