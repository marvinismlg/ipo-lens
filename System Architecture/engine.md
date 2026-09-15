IPO-LENS PREDICTION ENGINE SYSTEM ARCHITECTURE

                         ┌──────────────────────┐
                         │        ui.py         │
                         │                      │
                         │ User clicks Predict │
                         │ or Compare Company   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  engine_controller() │
                         │                      │
                         │ Main engine entry    │
                         │ point from the UI    │
                         └──────────┬───────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  │                                   │
                  ▼                                   ▼
        ┌─────────────────────┐             ┌─────────────────────┐
        │  read_companies()   │             │ read_ipo_lockups()  │
        │                     │             │                     │
        │ Loads companies.csv │             │ Loads metadata.csv  │
        └──────────┬──────────┘             └──────────┬──────────┘
                   │                                   │
                   └─────────────────┬─────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │ Build SpaceX Windows   │
                        │                        │
                        │ company_filter()       │
                        │ lockup_filter()        │
                        │ date_window()          │
                        └───────────┬────────────┘
                                    │
                                    ▼
             ┌───────────────────────────────────────────┐
             │      Calculate SpaceX Factor Metrics      │
             │                                           │
             │  momentum                                 │
             │  volatility                               │
             │  average trading volume                   │
             │  unlock-to-volume ratio                   │
             │  market cap                               │
             │  price-to-sales                           │
             │  revenue growth                           │
             └────────────────────┬──────────────────────┘
                                  │
                                  ▼
                       ┌───────────────────────┐
                       │    SPACEX_PROFILE     │
                       │                       │
                       │ One profile per       │
                       │ SpaceX tranche        │
                       └──────────┬────────────┘
                                  │
                ┌─────────────────┴──────────────────┐
                │                                    │
                │                                    │
                ▼                                    ▼
     UNIVERSAL PREDICTION PATH              USER COMPARISON PATH
     =========================              ====================

┌──────────────────────────────┐       ┌────────────────────────────┐
│ prediction_historical_       │       │ user_interface_controller │
│ universe()                   │       │ (selected_ticker)          │
│                              │       └──────────────┬─────────────┘
│ Loops through:               │                      │
│ META                         │                      ▼
│ BABA                         │           ┌────────────────────────┐
│ RKLB                         │           │ analyze_ticker()       │
│ ASTS                         │           │                        │
└──────────────┬───────────────┘           │ Build selected ticker │
               │                           │ tranche profiles       │
               ▼                           └────────────┬───────────┘
    ┌──────────────────────┐                             │
    │   analyze_ticker()   │                             ▼
    │                      │                ┌────────────────────────┐
    │ Builds historical    │                │ analyze_spacex_data() │
    │ tranche profiles     │                │                        │
    └──────────┬───────────┘                │ Pair SpaceX tranches   │
               │                            │ with historical ones   │
               ▼                            └────────────┬───────────┘
    ┌──────────────────────┐                             │
    │ Historical Universe  │                             ▼
    │                      │                  ┌─────────────────────┐
    │ Profiles + actual    │                  │ scoring_function()  │
    │ post-lockup returns  │                  │                     │
    └──────────┬───────────┘                  │ Six-factor          │
               │                              │ similarity scoring  │
               ▼                              └──────────┬──────────┘
    ┌──────────────────────┐                             │
    │ prediction_function │                             ▼
    │                      │                  ┌─────────────────────┐
    │ Weight historical    │                  │ Similarity Results  │
    │ outcomes by similarity│                 │                     │
    └──────────┬───────────┘                  │ Aggregate score     │
               │                              │ + tranche pairings  │
               ▼                              └──────────┬──────────┘
    ┌──────────────────────┐                             │
    │ Universal Forecast   │                             │
    │                      │                             │
    │ Bullish %            │                             │
    │ Bearish %            │                             │
    │ Prediction label     │                             │
    └──────────┬───────────┘                             │
               │                                         │
               └──────────────────┬──────────────────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │ user_interface_        │
                     │ controller() returns   │
                     │                        │
                     │ ui_component_1         │
                     │ Aggregate similarity   │
                     │                        │
                     │ ui_component_2         │
                     │ Universal prediction   │
                     │                        │
                     │ ui_components          │
                     │ Pairwise similarities  │
                     └───────────┬────────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │       ui.py          │
                      │                      │
                      │ Displays results to  │
                      │ the user             │
                      └──────────────────────┘