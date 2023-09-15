import os
import time
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
from pymongo import MongoClient
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, urldefrag
from scraper import GoodreadsScraper
from config import loadConfig

def main():
    configs = loadConfig()
    scraper = GoodreadsScraper(configs)
    scraper.run()

if __name__ == "__main__":
    main()
