IPO-LENS FINANCIAL DATA FLOW


                    EXTERNAL / STATIC DATA SOURCES
                    ==============================

       ┌──────────────────────┐
       │   ipo_metadata.csv   │
       │                      │
       │ Ticker               │
       │ IPO date             │
       │ IPO price            │
       │ Tranche              │
       │ Lockup date          │
       │ Shares unlocked      │
       └──────────┬───────────┘
                  │
        Used throughout pipeline
                  │
          ┌───────┴────────┐
          │                │
          ▼                ▼

┌───────────────────┐   ┌───────────────────┐
│ Yahoo / yfinance  │   │ SEC Company Facts │
│                   │   │                   │
│ Prices            │   │ Revenue           │
│ Volume            │   │ Shares            │
│ Market data       │   │ Historical filings│
│ Benchmark prices  │   │ Fundamentals      │
└─────────┬─────────┘   └─────────┬─────────┘
          │                       │
          │                       │
          ▼                       ▼

========================================================
               INDIVIDUAL DATA PIPELINES
========================================================

┌──────────────────────────┐
│   tickers_pipeline.py    │
│                          │
│ Historical comparables:  │
│                          │
│ META                     │
│ BABA                     │
│ RKLB                     │
│ ASTS                     │
│                          │
│ SPCX is skipped here     │
└────────────┬─────────────┘
             │
             │ Generates base rows
             ▼
      ┌─────────────────┐
      │    temp.csv     │
      │                 │
      │ Initial Yahoo   │
      │ financial data  │
      └────────┬────────┘
               │
               ▼

┌──────────────────────────┐
│   spacex_pipeline.py     │
│                          │
│ Handles SPCX separately  │
│                          │
│ Builds one continuous    │
│ SpaceX daily history     │
└────────────┬─────────────┘
             │
             │ Appends SPCX rows
             ▼
      ┌─────────────────┐
      │    temp.csv     │
      │                 │
      │ Historical IPOs │
      │       +         │
      │ SpaceX          │
      └────────┬────────┘
               │
               ▼

┌──────────────────────────┐
│     sec_pipeline.py      │
│                          │
│ Supplements / repairs    │
│ missing fundamentals     │
│                          │
│ Revenue                  │
│ Shares outstanding       │
│ Market-cap inputs        │
└────────────┬─────────────┘
             │
             │ Fills missing data
             │ without rebuilding
             ▼
      ┌─────────────────┐
      │    temp.csv     │
      │                 │
      │ Completed       │
      │ working dataset │
      └────────┬────────┘
               │
               ▼


========================================================
                  PIPELINE ORCHESTRATOR
========================================================

                 ┌────────────────────────┐
                 │   build_companies.py   │
                 │                        │
                 │ Controls execution     │
                 │ order of all 3         │
                 │ pipelines              │
                 └───────────┬────────────┘
                             │
                             ▼

                 1. generate_yahoo()
                             │
                             ▼
                 2. generate_spacex()
                             │
                             ▼
                 3. supplement_sec_data()
                             │
                             ▼
                 4. check_csv()
                             │
                             ▼
               ┌──────────────────────────┐
               │       VALIDATION         │
               │                          │
               │ Correct columns?         │
               │ Rows exist?              │
               │ Required tickers exist?  │
               └────────────┬─────────────┘
                            │
                      ┌─────┴─────┐
                      │           │
                    FAIL        PASS
                      │           │
                      ▼           ▼
             ┌──────────────┐  ┌──────────────────┐
             │ STOP BUILD   │  │ os.replace()     │
             │              │  │                  │
             │ Keep old     │  │ temp.csv becomes│
             │ companies.csv│  │ companies.csv    │
             └──────────────┘  └────────┬─────────┘
                                        │
                                        ▼

                              ┌────────────────────┐
                              │   companies.csv    │
                              │                    │
                              │ FINAL DATASET      │
                              │                    │
                              │ ticker             │
                              │ date               │
                              │ close              │
                              │ volume             │
                              │ market_cap         │
                              │ revenue            │
                              │ period             │
                              │ year               │
                              │ benchmark_close    │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │     engine.py      │
                              │                    │
                              │ Reads companies.csv│
                              │ and metadata       │
                              │ for calculations   │
                              └────────────────────┘