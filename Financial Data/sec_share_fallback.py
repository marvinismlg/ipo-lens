# We need to create a secondary file that imports HTML libraries in order to ensure the SEC API gives us the correct data

import csv
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import time
from html.parser import HTMLParser
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


DATE_PATTERN = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}"
BABA_IPO_URL = "https://www.sec.gov/Archives/edgar/data/1577552/000119312514347620/d709111d424b4.htm"
BABA_RATIO_AVAILABLE = "2014-09-22"
BABA_EARLY_WINDOW_END = "2015-06-24"
EXPECTED_CIKS = {"META": "0001326801", "BABA": "0001577552"}


def positive_number(value):
    try:
        return math.isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def fetch_sec_document(url, headers, cache_dir):
    """Cache successful immutable filing responses; fail visibly on HTTP errors."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    destination = cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".data")
    if destination.is_file():
        return destination.read_text(encoding="utf-8")
    for attempt in range(3):
        # Sequential access below the SEC's published 10 requests/second limit.
        time.sleep(0.30)
        try:
            with urlopen(Request(url, headers=dict(headers)), timeout=30) as response:
                content = response.read(20_000_001)
            if len(content) > 20_000_000:
                raise ValueError(f"SEC document exceeds diagnostic size limit: {url}")
            text = content.decode("utf-8", errors="replace")
            if not text.strip():
                raise ValueError(f"SEC returned an empty document: {url}")
            temporary = destination.with_suffix(".tmp")
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(destination)
            return text
        except HTTPError as exc:
            if exc.code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(f"SEC HTTP {exc.code}: {url}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"SEC request failed: {url}: {exc}") from exc


class FilingTextParser(HTMLParser):
    """Flatten filing text while excluding script and style contents."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignore_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.ignore_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.ignore_depth:
            self.ignore_depth -= 1

    def handle_data(self, data):
        if not self.ignore_depth:
            self.parts.append(data)


def filing_text(document):
    parser = FilingTextParser()
    parser.feed(document)
    text = " ".join(parser.parts).replace("\u200b", "").replace("\ufeff", "")
    return re.sub(r"\s+", " ", text).strip()


def parse_report_date(value):
    value = re.sub(r"\s+", " ", value).replace(",", "").strip()
    return datetime.datetime.strptime(value, "%B %d %Y").date().isoformat()


def extract_meta_filing_shares(document, filed_date, source_url):
    """Sum the two exact cover-page classes on the SAME reported date."""
    text = filing_text(document)[:20_000]
    if "facebook" not in text.lower() and "meta platforms" not in text.lower():
        raise ValueError(f"Unexpected META filing identity: {source_url}")
    by_date = {}
    pattern = (
        r"Class\s+([AB])\s+Common\s+Stock.{0,150}?"
        r"([\d,]+)\s+shares\s+outstanding\s+as\s+of\s+(" + DATE_PATTERN + r")"
    )
    for match in re.finditer(pattern, text, re.IGNORECASE):
        class_name, value, reported = match.groups()
        reported = parse_report_date(reported)
        bucket = by_date.setdefault(reported, {})
        value = int(value.replace(",", ""))
        if class_name.upper() in bucket and bucket[class_name.upper()] != value:
            raise ValueError(f"Conflicting META cover-page counts: {source_url}")
        bucket[class_name.upper()] = value
    # Verified alternate wording in Facebook's 2012 annual report.
    narrative = (
        r"On\s+(" + DATE_PATTERN + r").{0,100}?"
        r"([\d,]+)\s+shares\s+of\s+Class\s+A\s+common\s+stock\s+and\s+"
        r"([\d,]+)\s+shares\s+of\s+Class\s+B\s+common\s+stock\s+outstanding"
    )
    for match in re.finditer(narrative, text, re.IGNORECASE):
        reported, a, b = match.groups()
        reported = parse_report_date(reported)
        values = {"A": int(a.replace(",", "")), "B": int(b.replace(",", ""))}
        if reported in by_date and by_date[reported] != values:
            raise ValueError(f"Conflicting META share disclosures: {source_url}")
        by_date[reported] = values
    complete = [(date, values) for date, values in by_date.items() if set(values) == {"A", "B"}]
    if not complete:
        return []
    reported, classes = max(complete, key=lambda pair: pair[0])
    if reported > filed_date or not all(positive_number(value) for value in classes.values()):
        raise ValueError(f"Invalid META date/count: {source_url}")
    return [{
        "period_date": reported, "available_date": filed_date,
        "shares": float(classes["A"] + classes["B"]),
        "source_url": source_url, "basis": "Class A + Class B common shares",
        "ordinary_per_ads": "", "ratio_source_url": "",
    }]


def verify_baba_early_ads_ratio(headers, cache_dir):
    """Verify the historical unit in the original prospectus; never guess it."""
    text = filing_text(fetch_sec_document(BABA_IPO_URL, headers, cache_dir))
    if "alibaba" not in text.lower() or not re.search(
        r"Each\s+ADS\s+represents\s+one\s+ordinary\s+share", text, re.IGNORECASE
    ):
        raise ValueError("Cannot verify BABA's early 1:1 ADS conversion from its IPO prospectus")
    return 1.0


def extract_baba_filing_shares(document, filed_date, source_url, ordinary_per_ads):
    """Read actual issued/outstanding balance-sheet counts, not IPO projections."""
    if not BABA_RATIO_AVAILABLE <= filed_date <= BABA_EARLY_WINDOW_END:
        raise ValueError("BABA source falls outside the verified early ADS-conversion scope")
    if ordinary_per_ads != 1.0:
        raise ValueError("Unexpected BABA early ADS ratio")
    text = filing_text(document)
    if "alibaba group holding" not in text.lower():
        raise ValueError(f"Unexpected BABA filing identity: {source_url}")
    pattern = (
        r"Ordinary\s+shares,.{0,350}?;\s*([\d,]+)\s+and\s+([\d,]+)\s+shares\s+"
        r"issued\s+and\s+outstanding\s+as\s+of\s+(" + DATE_PATTERN + r")\s+and\s+"
        r"(" + DATE_PATTERN + r"),?\s+respectively"
    )
    counts = {}
    for match in re.finditer(pattern, text, re.IGNORECASE):
        first, second, first_date, second_date = match.groups()
        for value, reported in [(first, first_date), (second, second_date)]:
            reported = parse_report_date(reported)
            value = int(value.replace(",", ""))
            if reported in counts and counts[reported] != value:
                raise ValueError(f"Conflicting BABA balance-sheet counts: {source_url}")
            counts[reported] = value
    if not counts:
        return []
    reported = max(counts)
    if reported > filed_date or not positive_number(counts[reported]):
        raise ValueError(f"Invalid BABA date/count: {source_url}")
    return [{
        "period_date": reported, "available_date": filed_date,
        "shares": float(counts[reported]) / ordinary_per_ads,
        "source_url": source_url, "basis": "Actual ordinary shares / ordinary shares per ADS",
        "ordinary_per_ads": ordinary_per_ads, "ratio_source_url": BABA_IPO_URL,
    }]


def read_filing_catalog(ticker, first_date, last_date, headers, cache_dir):
    """Use submissions plus historical pages, not only the recent filing list."""
    cik = EXPECTED_CIKS[ticker]
    submissions = json.loads(fetch_sec_document(
        f"https://data.sec.gov/submissions/CIK{cik}.json", headers, cache_dir
    ))
    if str(submissions.get("cik", "")).zfill(10) != cik:
        raise ValueError(f"SEC submissions CIK mismatch for {ticker}")
    earliest = (datetime.date.fromisoformat(first_date) - datetime.timedelta(days=365)).isoformat()
    pages = [submissions.get("filings", {}).get("recent", {})]
    for page in submissions.get("filings", {}).get("files", []):
        if page.get("filingTo", "9999-12-31") < earliest or page.get("filingFrom", "0001-01-01") > last_date:
            continue
        name = page.get("name", "")
        if not name or Path(name).name != name:
            raise ValueError("Invalid SEC historical submissions filename")
        pages.append(json.loads(fetch_sec_document(
            "https://data.sec.gov/submissions/" + name, headers, cache_dir
        )))
    forms = {"10-Q", "10-K"} if ticker == "META" else {"6-K"}
    selected = {}
    for page in pages:
        accessions = page.get("accessionNumber", [])
        for index, accession in enumerate(accessions):
            form = page["form"][index]
            filed = page["filingDate"][index]
            if form in forms and earliest <= filed <= last_date:
                base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/"
                selected[accession] = {
                    "filed": filed, "accession": accession, "base": base,
                    "primary_url": base + quote(page["primaryDocument"][index], safe="/"),
                }
    return sorted(selected.values(), key=lambda filing: (filing["filed"], filing["accession"]))


def get_original_share_records(ticker, first_date, last_date, headers, cache_dir):
    if ticker not in EXPECTED_CIKS:
        raise ValueError(f"No verified original-filing parser configured for {ticker}")
    if ticker == "BABA" and last_date > BABA_EARLY_WINDOW_END:
        raise ValueError("Missing BABA market cap outside verified early windows; verify the later ADS ratio before extending this repair")
    ratio = verify_baba_early_ads_ratio(headers, cache_dir) if ticker == "BABA" else None
    records = []
    for filing in read_filing_catalog(ticker, first_date, last_date, headers, cache_dir):
        if ticker == "BABA" and filing["filed"] < BABA_RATIO_AVAILABLE:
            continue
        primary = fetch_sec_document(filing["primary_url"], headers, cache_dir)
        if ticker == "META":
            records.extend(extract_meta_filing_shares(primary, filing["filed"], filing["primary_url"]))
            continue
        found = extract_baba_filing_shares(primary, filing["filed"], filing["primary_url"], ratio)
        # Financial statements are often in EX-99 attachments rather than the
        # short primary 6-K. Inspect the filing's own document list.
        index = json.loads(fetch_sec_document(filing["base"] + "index.json", headers, cache_dir))
        for item in index.get("directory", {}).get("item", []):
            name = item.get("name", "")
            if "99" not in name.lower() or not name.lower().endswith((".htm", ".html")):
                continue
            if "/" in name or "\\" in name:
                raise ValueError("Invalid SEC exhibit filename")
            url = filing["base"] + quote(name)
            document = fetch_sec_document(url, headers, cache_dir)
            # Some EX-99 attachments have no share disclosure or identify a
            # speaker rather than the company; they cannot provide a count.
            if "alibaba group holding" not in filing_text(document).lower():
                continue
            found.extend(extract_baba_filing_shares(document, filing["filed"], url, ratio))
        records.extend(found)
    # A repeated same-period disclosure is not an economic share update.
    # On any public date, select the latest reported period, not whichever
    # attachment or comparative column happened to be listed last.
    by_public_date = {}
    for record in records:
        current = by_public_date.get(record["available_date"])
        if current is None or record["period_date"] > current["period_date"]:
            by_public_date[record["available_date"]] = record
        elif record["period_date"] == current["period_date"] and record["shares"] != current["shares"]:
            raise ValueError(f"Conflicting original share counts for {ticker} on {record['available_date']}")
    return sorted(by_public_date.values(), key=lambda record: (record["available_date"], record["period_date"]))


def repair_lockup_market_caps(company_rows, working_file, headers):
    """Repair META/BABA in memory; write provenance, never invented shares."""
    folder = Path(working_file).resolve().parent
    metadata_path = folder / "ipo_metadata.csv"
    with metadata_path.open(newline="", encoding="utf-8-sig") as stream:
        metadata = list(csv.DictReader(stream))
    targets = {}
    for lockup in metadata:
        ticker = lockup["ticker"].strip().upper()
        if ticker not in EXPECTED_CIKS:
            continue
        lockup_date = datetime.datetime.strptime(lockup["lockup_date"].strip(), "%Y-%m-%d").date().isoformat()
        history = sorted((row for row in company_rows if row["ticker"] == ticker and row["date"] < lockup_date), key=lambda row: row["date"])
        window = history[-30:]
        if not window:
            raise ValueError(f"{ticker}: no prices before lockup {lockup_date}")
        if not positive_number(window[-1].get("market_cap")):
            targets.setdefault(ticker, set()).update(row["date"] for row in window)
    audit = []
    for ticker, dates in targets.items():
        records = get_original_share_records(ticker, min(dates), max(dates), headers, folder / "sec_filing_cache")
        for row in company_rows:
            if row["ticker"] != ticker or row["date"] not in dates or positive_number(row.get("market_cap")):
                continue
            eligible = [
                record for record in records
                if record["available_date"] <= row["date"]
                and 0 <= (
                    datetime.date.fromisoformat(row["date"])
                    - datetime.date.fromisoformat(record["period_date"])
                ).days <= 365
            ]
            if not eligible:
                continue
            # Compare the reported dates as well: a later filing repeating an
            # older comparative count must not roll the estimate backwards.
            latest = max(eligible, key=lambda record: (record["period_date"], record["available_date"]))
            if not positive_number(row.get("close")):
                raise ValueError(f"{ticker}: invalid close on {row['date']}")
            row["market_cap"] = float(row["close"]) * latest["shares"]
            audit.append({"ticker": ticker, "date": row["date"], **latest, "market_cap": row["market_cap"]})
    # Always replace the report, so an earlier successful run is not mistaken
    # for evidence from the current build.
    with (folder / "sec_share_sources.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["ticker", "date", "period_date", "available_date", "shares", "market_cap", "basis", "ordinary_per_ads", "source_url", "ratio_source_url"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(audit)
    validate_lockup_market_caps(company_rows, metadata)
    return len(audit)


def validate_lockup_market_caps(company_rows, metadata):
    """Require a valid market cap on the latest pre-lockup price row."""
    required = {"META", "BABA", "ASTS", "RKLB", "SPCX"}
    problems = []
    for lockup in metadata:
        ticker = lockup["ticker"].strip().upper()
        if ticker not in required:
            continue
        date = datetime.datetime.strptime(lockup["lockup_date"].strip(), "%Y-%m-%d").date().isoformat()
        rows = sorted((row for row in company_rows if row["ticker"] == ticker and row["date"] < date), key=lambda row: row["date"])
        if not rows:
            problems.append(f"{ticker} tranche {lockup['tranche']}: no pre-lockup prices")
        elif not positive_number(rows[-1].get("market_cap")):
            problems.append(f"{ticker} tranche {lockup['tranche']}: market cap unavailable on {rows[-1]['date']}")
    if problems:
        raise ValueError("Required lockup market-cap coverage failed: " + "; ".join(problems))
