import datetime
import os
import time # We are processing a lot of data and dealing with a lot of endpoints, requests etc. Importing time just makes it easier and less riskywhen running a bunch of requests
import requests # Importing from the requests function so that we can use this on the website
import openpyxl
from openpyxl.styles import Font
from openpyxl.chart import LineChart, Reference
from dotenv import load_dotenv
import csv

def read_ipo_lockups():
    with open('data/ipo_metadata.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row)

read_ipo_lockups()

SPCX = {

}