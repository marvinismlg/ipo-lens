# IPO-LENS
## IPO Lockup Event & Similarity Analysis

### Summary:
IPO-LENS is a Python-based quantitative simulation designed to explore how SpaceX stock could behave around future IPO lockup expirations. The system compares SpaceX with historical IPOs including Meta, Alibaba, Rocket Lab, and AST SpaceMobile using pre-lockup market and fundamental data.

The project uses a multi-stage financial data pipeline that combines Yahoo Finance market data, SEC Company Facts fundamentals, and manually researched IPO lockup metadata. `build_companies.py` orchestrates the pipeline, builds a temporary working dataset, validates the required structure and tickers, and only then replaces the final `companies.csv` dataset used by the prediction engine.

`engine.py` creates 30-trading-day pre-lockup profiles using six factors: momentum, volatility, unlock-to-volume ratio, market capitalization, price-to-sales, and revenue growth. SpaceX tranches are compared against historical lockup tranches using an equal-weight similarity model. Historical 20-trading-day post-lockup returns are then weighted by similarity to generate a simulated Bullish, Bearish, or Mixed signal.

IPO-LENS also includes a CustomTkinter interface that allows users to run the prediction engine, compare SpaceX with individual historical companies, view aggregate and tranche-level similarity scores, and inspect project and company information.

### Technical Features:
- Python backend
- Yahoo Finance / `yfinance` market-data integration
- SEC Company Facts fundamentals integration
- Multi-stage financial data pipeline
- Temporary-file validation before dataset replacement
- CSV-based IPO and lockup metadata
- 30-trading-day pre-lockup analysis
- Six-factor similarity scoring
- 20-trading-day historical outcome analysis
- Rule-based weighted prediction engine
- CustomTkinter desktop interface
- Error logging and missing-data validation
- Separation of data collection, modeling, and presentation layers
- Matplotlib-generated pre-lockup volatility visualizations

### Project Purpose:
IPO-LENS was built as an introductory quantitative research, data engineering, and software development project.

Its purpose is to demonstrate the ability to combine external financial data, structured metadata, quantitative calculations, pipeline orchestration, rule-based modeling, and UI development into one working Python system.

### DISCLAIMER:
IPO-LENS is not a real stock prediction or investment recommendation tool.

The project is designed to demonstrate technical depth, quantitative reasoning, financial-data processing, and software architecture rather than produce reliable investment forecasts. Its signals are simulated outputs generated from historical similarity and rule-based assumptions and should not be used for real investing, trading, or short-selling decisions.