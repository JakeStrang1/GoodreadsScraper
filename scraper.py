import time
from book_scraper import BookScraper
from functools import reduce
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, urldefrag
from utils import *

class GoodreadsScraper:
    def __init__(self, configs):
        # Save configs
        self.configs = configs

        # Connect to local db
        self.db = MongoClient("mongodb://localhost:27017")[self.configs.mongo_db_name]

        # Set up selenium
        self.webdriver = start_driver()
        self.wait = WebDriverWait(self.webdriver, 30)

        # Other dependencies
        self.book_scraper = BookScraper(self.webdriver)
  
    def run(self):
        self.__sign_in()

        while True:
            url = self.__get_next_url()
            self.__scrape_url(url)
            time.sleep(2)
    
    def __get_next_url(self):
        # 1. Look for any incomplete book links with less than 3 attempts
        result = self.db.links.find_one({"complete": False, "is_book": True, "$or": [{"attempts": {"$exists": False}},{"attempts": {"$lt": 3}}]})
        if result != None:
            return result["url"]
        
        # 2. Look for any incomplete non-book links with less than 3 attempts
        result = self.db.links.find_one({"complete": False, "is_book": False, "$or": [{"attempts": {"$exists": False}},{"attempts": {"$lt": 3}}]})
        if result != None:
            return result["url"]
        
        # 3. Is the links collection empty? Then use the home page
        if self.db.links.count_documents({}) == 0:
            return "/"
        
        # 4. Otherwise, all the links have been scraped (not expecting to ever hit this)
        raise Exception("There aren't any more links to scrape. Are we done or is this an error?")
    
    def __scrape_url(self, current_url):
        # Navigate to page
        current_url = ensure_absolute_link(current_url)
        self.webdriver.get(current_url)
        time.sleep(2) # extra time for loading

        # Scrape page links
        links = self.__scrape_links()
        for link in links:
            self.__save_link(link)
        
        # Scrape book data
        if is_book(current_url):
            self.__scrape_book(current_url)
        
        # Save page status as completed
        current_url = ensure_rel_link(current_url)
        self.db.links.update_one({"url": current_url}, {"$set": {"complete": True}})
    
    def __scrape_links(self):
        # Find and save all links on page
        attempts = 0
        all_links = []

        # Loop because we've hit exceptions here before (if max attempts is reached, we treat as having no links)
        while attempts <= 2:
            try:
                elems = self.webdriver.find_elements(By.XPATH, "//a[@href]")
                all_links = list(map(lambda x: x.get_attribute("href"), elems))
                break # move on
            except:
                time.sleep(1)
                attempts = attempts + 1

        goodreads_links = filter(lambda x: x.startswith('https://www.goodreads.com'), all_links) # Filter out non-goodreads links
        relative_links = list(map(lambda x: x.removeprefix('https://www.goodreads.com'), goodreads_links)) # Get relative links
        relevant_links = filter(lambda x: self.__is_relevant_link(x), relative_links) # filter out links from the ignored list
        return relevant_links

    def __save_link(self, link):
        link = format_link(link)
        if self.db.links.count_documents({'url': link}) > 0:
            return # already saved
        linkDocument = {
            "url": link,
            "complete": False,
            "is_book": is_book(link)
        }
        self.db.links.insert_one(linkDocument)
    
    def __sign_in(self):
        # Open sign in page (seems like all these query parameters are important)
        goodreads_sign_in_url = 'https://www.goodreads.com/ap/signin?language=en_US&openid.assoc_handle=amzn_goodreads_web_na&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.goodreads.com%2Fap-handler%2Fsign-in&siteState=1aad3e0863b9f621de0f7ccc0da34a7f'
        self.webdriver.get(goodreads_sign_in_url)

        # Interaction
        username = self.webdriver.find_element(By.NAME, "email")
        username.send_keys(self.configs.goodreads_username)
        password = self.webdriver.find_element(By.NAME, "password")
        password.send_keys(self.configs.goodreads_password)
        submit_button = self.webdriver.find_element(By.CSS_SELECTOR, "#signInSubmit")
        submit_button.click()
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'siteHeader__topLevelLink')))
    
    def __scrape_book(self, book_url):
        book = {}
        try:
            book = self.book_scraper.scrape_book(book_url)
        except:
            # keep track of attempts instead of crashing
            self.db.links.update_one({"url": book_url}, {"$inc": {"attempts": 1}})
            return
        
        self.db.books.insert_one(book)

    def __is_relevant_link(self, relative_link):
        # filter out certain links that we've decided aren't worth tracking
        if relative_link.startswith("/author/quotes/"):
            return False

        if relative_link.startswith("/notes/"):
            return False

        if relative_link.startswith("/review/list/") and "shelf=" in relative_link:
            return False

        return True

def start_driver():
    options = Options()
    options.headless = False # Switch to True later
    options.add_argument("--window-size=1920,1200")
    options.add_experimental_option("detach", True) # keep open
    return webdriver.Chrome(options=options)