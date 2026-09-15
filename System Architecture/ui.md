IPO-LENS UI SYSTEM ARCHITECTURE

+--------------------------------------------------+
|                  MAIN PAGE                       |
|--------------------------------------------------|
| Project Name: IPO-LENS                           |
| Project Creator                                  |
|                                                  |
| [ Score & Predict ]                              |
| [ Back Test ]                                    |
| [ About ]                                        |
| [ Company Info ]                                 |
+--------------------------------------------------+
          |
          |
          +----------------------------+
          |                            |
          v                            v

+-----------------------------+   +-----------------------------+
|     SCORE & PREDICT PAGE    |   |       BACK TEST PAGE        |
|-----------------------------|   |-----------------------------|
| [ Predict Next SpaceX       |   | Placeholder / Blank Page    |
|   Tranche ]                 |   | For Future Backtesting      |
|                             |   | Features                    |
| [ Compare SpaceX to         |   +-----------------------------+
|   Historical Company ]      |
+-----------------------------+
          |
          +-------------------------------+
          |                               |
          v                               v

+-----------------------------+   +-----------------------------+
|   SPACE X PREDICTION PAGE   |   |  COMPANY SELECTION PAGE     |
|-----------------------------|   |-----------------------------|
| Runs overall prediction     |   | Select Historical Company   |
|                             |   |                             |
| Displays:                   |   | [ META ]                    |
| - Bullish / Bearish Signal  |   | [ BABA ]                    |
| - Bullish Evidence          |   | [ RKLB ]                    |
| - Bearish Evidence          |   | [ ASTS ]                    |
+-----------------------------+   +-----------------------------+
                                          |
                                          v

                                +-----------------------------+
                                | SIMILARITY RESULTS PAGE     |
                                |-----------------------------|
                                | Selected Company            |
                                |                             |
                                | Aggregate Similarity Score  |
                                |                             |
                                | SpaceX Tranche vs           |
                                | Historical Tranche Scores   |
                                +-----------------------------+


MAIN PAGE
    |
    +----------------------------------------------------------+
    |                                                          |
    v                                                          v

+-----------------------------+                     +-----------------------------+
|        ABOUT PAGE           |                     |     COMPANY INFO PAGE       |
|-----------------------------|                     |-----------------------------|
| Static Project Information  |                     | Select Company              |
|                             |                     |                             |
| - What IPO-LENS Does        |                     | [ SpaceX ]                  |
| - Methodology               |                     | [ META ]                    |
| - Project Purpose           |                     | [ BABA ]                    |
| - Creator Information       |                     | [ RKLB ]                    |
| - Disclaimer                |                     | [ ASTS ]                    |
+-----------------------------+                     +-----------------------------+
                                                               |
                                                               v

                                                    +-----------------------------+
                                                    | COMPANY DETAIL PAGE         |
                                                    |-----------------------------|
                                                    | Static Information About    |
                                                    | Selected Company            |
                                                    |                             |
                                                    | - Company Name              |
                                                    | - Ticker                    |
                                                    | - IPO Information           |
                                                    | - Lockup / Tranche Info     |
                                                    | - Other Project Context     |
                                                    +-----------------------------+