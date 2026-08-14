import time
import customtkinter as ctk

user_interface = ctk.CTk()
user_interface.geometry("1000x1000")

frame = ctk.CTkFrame(master=user_interface, width=750, height=500)
frame.pack()

title = ctk.CTkLabel(master=frame, text="SpaceX IPO Lens", font=("Arial Bold", 30))
title.pack(pady=20, padx=20)

subtitle = ctk.CTkLabel(master=frame, text=" IPO Lockup Event Study by Marvin Tientcheu", font=("Arial Bold", 15))
subtitle.pack(pady=20, padx=20)

predict_page = ctk.CTkButton(master=frame, text="Run Prediction", font=("Arial Bold", 25))
predict_page.pack(pady=40, padx=40)

research_page = ctk.CTkButton(master=frame, text="View Company Data", font=("Arial Bold", 25))
research_page.pack(pady=20, padx=20)

user_interface.mainloop()