# This is where the client will actually test our model. To view the UI flow, click on ui.md in this folder
# For the UI we want a seamless, sleek, simplistic looking interface to represent the Saas nature of the project.
# Also, "build_companies.csv" creation will be handled by a small widget that is meant to call build_companies.csv
# This is where the client will actually test our model. To view the UI flow, click on ui.md in this folder.
# UI.py will use some logic, the file is responsible for calling build_companies.

import os
import sys
import threading
import importlib.util
import customtkinter as ctk

project_root = os.path.dirname(os.path.dirname(__file__))
os.chdir(project_root)

# Because we wanted to make the files look nice and have spaces, we need to use operating system in order to access them, slightly inconvenient, however no big deal
engine_path = os.path.join(project_root, "Prediction Engine", "engine.py")
spec = importlib.util.spec_from_file_location("engine", engine_path)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

# Defining the financial data folder as a variable so we do not have to reuse the Operating System lab every time we call it
financial_data_folder = os.path.join(project_root, "Financial Data")
if financial_data_folder not in sys.path:
    sys.path.insert(0, financial_data_folder)

build_path = os.path.join(financial_data_folder, "build_companies.py")
build_spec = importlib.util.spec_from_file_location("build_companies", build_path)
build_companies_module = importlib.util.module_from_spec(build_spec)
build_spec.loader.exec_module(build_companies_module)

companies_file = os.path.join(financial_data_folder, "companies.csv")

# Easier on the eyes, plus makes the application look more like a Saas
ctk.set_appearance_mode("dark")

# Defining a set of colors, not necessary but important for the User Experience, we also don't want to have to write the Hex out everytime we make a page
BG = "#0B0D10"
PANEL = "#11151A"
PANEL_2 = "#171B21"
TEXT = "#F5F7FA"
MUTED = "#8B949E"
ACCENT = "#4F8CFF"
HOVER = "#3B73DA"
BORDER = "#252B33"

# Defining the full user interface function

app = ctk.CTk()
app.title("IPO LENS")
app.geometry("1100x760")
app.minsize(900, 650)
app.configure(fg_color=BG)

# We should create a global list for pages in order to keep our architecture clean and in one place instead of scattered
pages = []
selected_compare_ticker = ctk.StringVar(value="META")
selected_info_ticker = ctk.StringVar(value="SPCX")

# This is the company information that will be present on the "Info" page, we want to give some background information to the user on these companies.

company_information = {
    "SPCX": {
        "name": "SpaceX",
        "subtitle": "Target IPO used by the IPO-LENS forecasting model",
        "details": "Project Ticker: SPCX\nIPO Date: June 12, 2026\nIPO Price: $135\nModeled Lockup Tranches: 4\n\nSpaceX is the target company in the IPO-LENS project. The application evaluates SpaceX lockup tranches against historical IPO lockup behavior from the comparable-company universe. SPCX and its modeled IPO timeline are used as part of the project's forecasting scenario."
    },
    "META": {
        "name": "Meta Platforms",
        "subtitle": "Historical comparable company",
        "details": "Ticker: META\nIPO Date: May 18, 2012\nIPO Price: $38\nLockup Tranches in Dataset: 5\n\nMeta, formerly Facebook at the time of its IPO, provides multiple historical lockup events for comparison. IPO-LENS evaluates its pre-lockup market behavior and post-lockup returns against the modeled SpaceX tranches."
    },
    "BABA": {
        "name": "Alibaba",
        "subtitle": "Historical comparable company",
        "details": "Ticker: BABA\nIPO Date: September 19, 2014\nIPO Price: $68\nLockup Tranches in Dataset: 3\n\nAlibaba contributes multiple lockup-event observations to the historical comparison universe used by IPO-LENS."
    },
    "RKLB": {
        "name": "Rocket Lab",
        "subtitle": "Historical aerospace comparable",
        "details": "Ticker: RKLB\nIPO Date: August 25, 2021\nReference IPO Price: $10\nLockup Tranches in Dataset: 1\n\nRocket Lab provides an aerospace-oriented historical comparison for the SpaceX forecasting model."
    },
    "ASTS": {
        "name": "AST SpaceMobile",
        "subtitle": "Historical space-industry comparable",
        "details": "Ticker: ASTS\nIPO Date: April 6, 2021\nReference IPO Price: $10\nLockup Tranches in Dataset: 1\n\nAST SpaceMobile contributes another space-industry lockup event to the historical comparison universe."
    }
}

def show_page(page):
    for item in pages:
        item.pack_forget()
    page.pack(fill="both", expand=True)

def page_frame():
    frame = ctk.CTkFrame(app, fg_color=BG, corner_radius=0)
    pages.append(frame)
    return frame

def page_header(parent, title, subtitle="", back_command=None):
    top = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    top.pack(fill="x", padx=42, pady=(32, 10))
    if back_command:
        ctk.CTkButton(top, text="← Back", width=90, height=34, corner_radius=6, fg_color=PANEL_2, hover_color=BORDER, command=back_command).pack(anchor="w", pady=(0, 22))
    ctk.CTkLabel(top, text=title, font=ctk.CTkFont(size=30, weight="bold"), text_color=TEXT).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(top, text=subtitle, font=ctk.CTkFont(size=14), text_color=MUTED).pack(anchor="w", pady=(7, 0))
    return top

def primary_button(parent, text, command):
    return ctk.CTkButton(parent, text=text, height=46, corner_radius=7, fg_color=ACCENT, hover_color=HOVER, font=ctk.CTkFont(size=14, weight="bold"), command=command)

def secondary_button(parent, text, command):
    return ctk.CTkButton(parent, text=text, height=46, corner_radius=7, fg_color=PANEL_2, hover_color=BORDER, border_width=1, border_color=BORDER, font=ctk.CTkFont(size=14), command=command)

# This is essential, we need flow control for build_companes.py, as we dont want to generate it automatically at runtime, however we dont want to wait until scoring to generate either
def create_loading_popup():
    popup = ctk.CTkToplevel(app)
    popup.title("Building companies.csv...")
    popup.geometry("390x170")
    popup.resizable(False, False)
    popup.configure(fg_color=PANEL)
    popup.transient(app)
    popup.grab_set()
    ctk.CTkLabel(popup, text="Building companies.csv...", font=ctk.CTkFont(size=19, weight="bold"), text_color=TEXT).pack(pady=(30, 6))
    ctk.CTkLabel(popup, text="Refreshing Yahoo, SpaceX and SEC financial data.", font=ctk.CTkFont(size=12), text_color=MUTED).pack()
    progress = ctk.CTkProgressBar(popup, width=300, mode="indeterminate")
    progress.pack(pady=24)
    progress.start()
    return popup, progress

def show_error(message, return_page):
    error_text.configure(text=message)
    error_back.configure(command=lambda: show_page(return_page))
    show_page(error_page)

# Below is one of our logic functions, run_backend's purpose is to verify the financial data exists and run our engine_controller, flow control function that we created in Engine
def run_backend(mode, ticker=None):
    popup, progress = create_loading_popup()

    def worker():
        try:
            build_companies_module.build_companies()
            if not os.path.exists(companies_file) or os.path.getsize(companies_file) == 0:
                raise FileNotFoundError("Financial Data/companies.csv was not successfully generated.")
            controller_ticker = ticker if ticker else "META"
            result = engine.engine_controller(controller_ticker)
            app.after(0, lambda: finish_success(mode, result, ticker, popup, progress))
        except Exception as exc:
            app.after(0, lambda: finish_error(str(exc), popup, progress))

    threading.Thread(target=worker, daemon=True).start()

# Next we need to verify that the prediction ran successfully and there were no errors or interruptions when generating the SpaceX prediction or similarity score comparison

def finish_success(mode, result, ticker, popup, progress):
    progress.stop()
    popup.grab_release()
    popup.destroy()

    if mode == "prediction":
        prediction_result.configure(text=result["ui_component_2"])
        show_page(prediction_page)
    elif mode == "comparison":
        comparison_title.configure(text=f"SpaceX vs {ticker}")
        comparison_aggregate.configure(text=result["ui_component_1"])
        comparison_box.configure(state="normal")
        comparison_box.delete("1.0", "end")
        for line in result["ui_components"]:
            comparison_box.insert("end", line + "\n\n")
        comparison_box.configure(state="disabled")
        show_page(comparison_results_page)

def finish_error(message, popup, progress):
    progress.stop()
    popup.grab_release()
    popup.destroy()
    show_error(message, score_page)

# MAIN PAGE
main_page = page_frame()
hero = ctk.CTkFrame(main_page, fg_color="transparent", corner_radius=0)
hero.pack(expand=True)
ctk.CTkLabel(hero, text="IPO LENS", font=ctk.CTkFont(size=42, weight="bold"), text_color=TEXT).pack(pady=(0, 8))
ctk.CTkLabel(hero, text="IPO Lockup Event & Narrative Similarity", font=ctk.CTkFont(size=16), text_color=MUTED).pack(pady=(0, 5))
ctk.CTkLabel(hero, text="Created by Marvin Tientcheu", font=ctk.CTkFont(size=12), text_color=MUTED).pack(pady=(0, 35))
main_buttons = ctk.CTkFrame(hero, fg_color="transparent")
main_buttons.pack()
primary_button(main_buttons, "Score & Predict", lambda: show_page(score_page)).pack(fill="x", pady=6)
secondary_button(main_buttons, "Back Test", lambda: show_page(backtest_page)).pack(fill="x", pady=6)
secondary_button(main_buttons, "Company Info", lambda: show_page(company_select_page)).pack(fill="x", pady=6)
secondary_button(main_buttons, "About", lambda: show_page(about_page)).pack(fill="x", pady=6)

# SCORE & PREDICT PAGE
score_page = page_frame()
page_header(score_page, "Score & Predict", "Choose whether to generate the universal SpaceX forecast or compare SpaceX with a historical IPO.", lambda: show_page(main_page))
score_body = ctk.CTkFrame(score_page, fg_color="transparent")
score_body.pack(fill="x", padx=42, pady=35)
predict_card = ctk.CTkFrame(score_body, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8)
predict_card.pack(fill="x", pady=8)
ctk.CTkLabel(predict_card, text="Predict Next SpaceX Tranche", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT).pack(anchor="w", padx=25, pady=(22, 4))
ctk.CTkLabel(predict_card, text="Run the universal historical lockup model and return the bullish or bearish evidence signal.", text_color=MUTED, wraplength=760, justify="left").pack(anchor="w", padx=25)
primary_button(predict_card, "Run Prediction", lambda: run_backend("prediction")).pack(anchor="w", padx=25, pady=22)

compare_card = ctk.CTkFrame(score_body, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8)
compare_card.pack(fill="x", pady=8)
ctk.CTkLabel(compare_card, text="Compare SpaceX to a Historical Company", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT).pack(anchor="w", padx=25, pady=(22, 4))
ctk.CTkLabel(compare_card, text="Select one historical company and view aggregate and tranche-by-tranche similarity scores.", text_color=MUTED).pack(anchor="w", padx=25)
secondary_button(compare_card, "Choose Company", lambda: show_page(compare_select_page)).pack(anchor="w", padx=25, pady=22)

# PREDICTION RESULTS PAGE
prediction_page = page_frame()
page_header(prediction_page, "SpaceX Lockup Forecast", "Universal forecast generated from the historical comparable-company universe.", lambda: show_page(score_page))
prediction_panel = ctk.CTkFrame(prediction_page, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8)
prediction_panel.pack(fill="x", padx=42, pady=35)
ctk.CTkLabel(prediction_panel, text="Forecast Result", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT).pack(anchor="w", padx=25, pady=(24, 10))
prediction_result = ctk.CTkLabel(prediction_panel, text="", font=ctk.CTkFont(size=17), text_color=TEXT, wraplength=900, justify="left")
prediction_result.pack(anchor="w", padx=25, pady=(0, 24))
ctk.CTkLabel(prediction_page, text="This is a pseudo-predictive research model and is not investment advice.", text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=42)

# COMPARISON SELECTION PAGE
compare_select_page = page_frame()
page_header(compare_select_page, "Historical Comparison", "Select the company you want to compare against SpaceX.", lambda: show_page(score_page))
compare_select_panel = ctk.CTkFrame(compare_select_page, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8)
compare_select_panel.pack(fill="x", padx=42, pady=35)
ctk.CTkLabel(compare_select_panel, text="Comparable Company", text_color=TEXT, font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=25, pady=(24, 10))
ctk.CTkOptionMenu(compare_select_panel, values=["META", "BABA", "RKLB", "ASTS"], variable=selected_compare_ticker, width=260, height=40, corner_radius=6).pack(anchor="w", padx=25)
primary_button(compare_select_panel, "Run Similarity Score", lambda: run_backend("comparison", selected_compare_ticker.get())).pack(anchor="w", padx=25, pady=24)

# COMPARISON RESULTS PAGE
comparison_results_page = page_frame()
page_header(comparison_results_page, "Similarity Results", "Similarity across the six-factor lockup profile.", lambda: show_page(compare_select_page))
comparison_content = ctk.CTkFrame(comparison_results_page, fg_color="transparent")
comparison_content.pack(fill="both", expand=True, padx=42, pady=(20, 35))
comparison_title = ctk.CTkLabel(comparison_content, text="", font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT)
comparison_title.pack(anchor="w")
comparison_aggregate = ctk.CTkLabel(comparison_content, text="", text_color=TEXT, wraplength=950, justify="left", font=ctk.CTkFont(size=15))
comparison_aggregate.pack(anchor="w", pady=(10, 22))
comparison_box = ctk.CTkTextbox(comparison_content, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8, text_color=TEXT, font=ctk.CTkFont(size=14))
comparison_box.pack(fill="both", expand=True)
comparison_box.configure(state="disabled")

# COMPANY INFO SELECTION PAGE
company_select_page = page_frame()
page_header(company_select_page, "Company Info", "View static information about companies included in the IPO-LENS dataset.", lambda: show_page(main_page))
company_select_panel = ctk.CTkFrame(company_select_page, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8)
company_select_panel.pack(fill="x", padx=42, pady=35)
ctk.CTkLabel(company_select_panel, text="Select Company", font=ctk.CTkFont(size=17, weight="bold"), text_color=TEXT).pack(anchor="w", padx=25, pady=(24, 10))
ctk.CTkOptionMenu(company_select_panel, values=["SPCX", "META", "BABA", "RKLB", "ASTS"], variable=selected_info_ticker, width=260, height=40, corner_radius=6).pack(anchor="w", padx=25)

def open_company_info():
    info = company_information[selected_info_ticker.get()]
    company_name_label.configure(text=info["name"])
    company_subtitle_label.configure(text=info["subtitle"])
    company_details_box.configure(state="normal")
    company_details_box.delete("1.0", "end")
    company_details_box.insert("end", info["details"])
    company_details_box.configure(state="disabled")
    show_page(company_detail_page)

primary_button(company_select_panel, "View Company", open_company_info).pack(anchor="w", padx=25, pady=24)

# COMPANY DETAIL PAGE
company_detail_page = page_frame()
page_header(company_detail_page, "Company Profile", "", lambda: show_page(company_select_page))
company_detail_panel = ctk.CTkFrame(company_detail_page, fg_color="transparent")
company_detail_panel.pack(fill="both", expand=True, padx=42, pady=25)
company_name_label = ctk.CTkLabel(company_detail_panel, text="", font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT)
company_name_label.pack(anchor="w")
company_subtitle_label = ctk.CTkLabel(company_detail_panel, text="", font=ctk.CTkFont(size=14), text_color=MUTED)
company_subtitle_label.pack(anchor="w", pady=(4, 20))
company_details_box = ctk.CTkTextbox(company_detail_panel, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8, text_color=TEXT, font=ctk.CTkFont(size=14))
company_details_box.pack(fill="both", expand=True)
company_details_box.configure(state="disabled")

# ABOUT PAGE
about_page = page_frame()
page_header(about_page, "About IPO-LENS", "A technical portfolio project exploring IPO lockup-event similarity and forecasting while using SpaceX as its case study.", lambda: show_page(main_page))
about_panel = ctk.CTkFrame(about_page, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8)
about_panel.pack(fill="both", expand=True, padx=42, pady=30)
about_text = (
    "IPO-LENS is a rule-based pseudo-predictive system designed to evaluate SpaceX lockup-event behavior against historical IPO lockup events.\n\n"
    "The model compares six factors: momentum, volatility, unlock-to-volume ratio, market capitalization, price-to-sales, and revenue growth.\n\n"
    "Historical companies provide both similarity evidence and post-lockup outcomes. The engine uses these observations to construct an aggregate bullish or bearish evidence signal for SpaceX while separately producing company-specific similarity scores.\n\n"
    "Financial data is assembled through Yahoo Finance and SEC filing data, validated, and written into a single companies.csv dataset before the prediction engine runs.\n\n"
    "Purpose\nIPO-LENS is an educational and portfolio project intended to demonstrate Python, data engineering, financial-data processing, quantitative reasoning, system design, and desktop UI development.\n\n"
    "Disclaimer\nIPO-LENS is not designed for real investment decisions and its outputs should not be interpreted as financial advice."
)
ctk.CTkLabel(about_panel, text=about_text, text_color=TEXT, font=ctk.CTkFont(size=14), wraplength=930, justify="left").pack(anchor="nw", padx=28, pady=28)

# BACKTEST PAGE
backtest_page = page_frame()
page_header(backtest_page, "Back Test", "Reserved for future historical validation of the forecasting model.", lambda: show_page(main_page))
backtest_panel = ctk.CTkFrame(backtest_page, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8)
backtest_panel.pack(fill="both", expand=True, padx=42, pady=35)
ctk.CTkLabel(backtest_panel, text="Backtesting module coming later.", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT).pack(expand=True)

# ERROR PAGE
error_page = page_frame()
page_header(error_page, "Unable to Complete Request", "The data build or prediction engine returned an error.")
error_panel = ctk.CTkFrame(error_page, fg_color=PANEL, border_width=1, border_color=BORDER, corner_radius=8)
error_panel.pack(fill="x", padx=42, pady=35)
error_text = ctk.CTkLabel(error_panel, text="", text_color=TEXT, wraplength=900, justify="left")
error_text.pack(anchor="w", padx=25, pady=(25, 15))
error_back = secondary_button(error_panel, "Go Back", lambda: show_page(main_page))
error_back.pack(anchor="w", padx=25, pady=(0, 25))

show_page(main_page)
app.mainloop()