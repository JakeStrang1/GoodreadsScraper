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

def scrape_page(url):
    # Navigate to page
    url = ensure_absolute_link(url)
    driver.get(url)
    
    # Find and save all links on page
    attempts = 0
    links = []

    # Loop because we've hit exceptions here before
    while attempts <= 2:
        try:
            elems = driver.find_elements(By.XPATH, "//a[@href]")
            links = list(map(lambda x: x.get_attribute("href"), elems))
            break # move on
        except:
            time.sleep(1)
            attempts = attempts + 1

    goodreads_links = filter(lambda x: x.startswith('https://www.goodreads.com'), links)
    rel_links = list(map(lambda x: x.removeprefix('https://www.goodreads.com'), goodreads_links))
    for link in rel_links:
        save_link(link)
    
    # Scrape book data
    if is_book(url):
        scrape_book(url)
    
    # Update status of current link to complete
    url = ensure_rel_link(url)
    linksCollection.update_one({"url": url}, {"$set": {"complete": True}})

def ensure_absolute_link(link):
    if link.startswith('/'):
        return "https://www.goodreads.com" + link
    return link

def ensure_rel_link(link):
    if link.startswith('https://www.goodreads.com'):
        return link.removeprefix('https://www.goodreads.com')
    return link

def format_link(link):
    # Remove 'ref' query and fragement
    parsed_url = urlparse(link)
    query_params = parse_qs(parsed_url.query)
    query_params.pop('ref', None)
    parsed_url = parsed_url._replace(query=urlencode(query_params, True))
    return urldefrag(urlunparse(parsed_url))[0]

def save_link(link):
    link = format_link(link)
    if linksCollection.count_documents({'url': link}) > 0:
        return # already saved
    linkDocument = {
        "url": link,
        "complete": False,
        "is_book": is_book(link)
    }
    linksCollection.insert_one(linkDocument)

def is_book(link):
    link = ensure_rel_link(link)

    sections = link.split("/")
    if len(sections) == 4 and sections[1] == "book" and sections[2] == "show":
        return True
    return False

def scrape_book(book_url):
    time.sleep(2) # extra time for loading

    book_url = ensure_rel_link(book_url)

    bookDocument = {
        "url": book_url # The Goodreads URL where this book is located
    }

    # Get title
    try:
        title = driver.find_element(By.CLASS_NAME, "Text__title1").text
        if title == "":
            raise Exception("The title for this book is blank.")
        bookDocument["title"] = title
    except:
        # keep track of attempts instead of crashing
        linksCollection.update_one({"url": url}, {"$inc": {"attempts": 1}})
        return
    
    # Get author
    author = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__contributor > h3 > div > span:nth-child(1) > a:nth-child(1) > span.ContributorLink__name").text
    if author == "":
        raise Exception("The author for this book is blank.")
    bookDocument["author"] = author

    # Get series
    series = ""
    is_series = False
    try:
        series = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageTitleSection > div.BookPageTitleSection__title > h3 > a").text
        if series == "":
            raise Exception("The series for this book is blank.")
        is_series = True
    except:
        # Not all books are part of a series
        pass

    if is_series:
        series_sections = series.split("#") # "Ender's Saga #4"
        if len(series_sections) != 2:
            series_sections.append("") # The series number is blank in this case
        bookDocument["is_series"] = True
        bookDocument["series"] = series_sections[0].strip()
        bookDocument["series_number"] = series_sections[1].strip()
    else:
        bookDocument["is_series"] = False
    

    # Get image url
    image_url = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__leftColumn > div > div.BookPage__bookCover > div > div > div > div > div > div > img").get_attribute("src")
    if image_url == "":
        raise Exception("The image_url for this book is blank.")
    bookDocument["image_url"] = image_url

    # Get description
    try:
        description = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__description > div > div.TruncatedContent__text.TruncatedContent__text--large > div > div > span").text
        if description == "":
            raise Exception("The description for this book is blank.")
        bookDocument["description"] = description
    except:
        # Sometimes a book just doesn't have this
        bookDocument["description"] = ""

    # Get published date
    try:
        published_date = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookDetails > div > span:nth-child(1) > span > div > p:nth-child(2)").text
        if published_date == "":
            raise Exception("The published date for this book is blank.")
        published_sections = published_date.split("published") # "First published May 1, 1990"
        if len(published_sections) != 2:
            published_sections = published_date.split("publication") # "Expected publication October 31, 2023"
            if len(published_sections) != 2:
                published_sections = published_date.split("Published") # "Published March 21, 2023"
                if len(published_sections) != 2:
                    raise Exception("The published date for this book is unexpected format.")
        bookDocument["published_date"] = published_sections[1].strip()
    except:
        # Sometimes a book just doesn't have this
        bookDocument["published_date"] = ""

    # Get pages
    pages = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookDetails > div > span:nth-child(1) > span > div > p:nth-child(1)").text
    if pages == "":
        raise Exception("The pages for this book is blank.")
    pages_sections = pages.split("pages")
    if len(pages_sections) != 2:
        pages_sections = pages.split("Audio") # "Audio CD"
        if len(pages_sections) != 2:
            # if pages != "Hardcover" and pages != "Paperback" and pages != "ebook" and pages != "Kindle Edition":
            #     raise Exception("The pages for this book is unexpected format.")
            # else:
            pages_sections[0] = "" # unknown page number
        else:
            pages_sections[0] = "N/A"
    bookDocument["pages"] = pages_sections[0].strip()

    # Get rating
    rating = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__ratingStats > a > div:nth-child(1) > div").text
    if rating == "":
        raise Exception("The rating for this book is blank.")
    bookDocument["rating"] = rating

    # Get rating quantity
    rating_quantity = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__ratingStats > a > div:nth-child(2) > div > span:nth-child(1)").text
    if rating_quantity == "":
        raise Exception("The rating_quantity for this book is blank.")
    rating_quantity_sections = rating_quantity.split("ratings")
    if len(rating_quantity_sections) != 2:
        rating_quantity_sections = rating_quantity.split("rating") # "1 rating"
        if len(rating_quantity_sections) != 2:
            raise Exception("The rating_quantity for this book is unexpected format.")
    bookDocument["rating_quantity"] = rating_quantity_sections[0].strip()

    # Get ISBN
    try:
        isbn = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookDetails > div > span:nth-child(2) > div.BookDetails__list > span > div > dl > div:nth-child(3) > dd > div > div.TruncatedContent__text.TruncatedContent__text--small").text
        if isbn == "":
            raise Exception("The isbn for this book is blank.")
        bookDocument["isbn"] = isbn
    except:
        # skip, sometimes the isbn is collapsed and I don't feel like hunting it down
        pass

    # Get genres
    try:
        genre_span = driver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__genres > ul > span:nth-child(1)")
        genres = list(map(lambda x: x.text, genre_span.find_elements(By.CLASS_NAME, "Button__labelItem")))
        if len(genres) == 0:
            raise Exception("The genres for this book is blank.")
        bookDocument["genres"] = genres
    except:
        # Sometimes newer books don't have genres listed yet
        bookDocument["genres"] = []
    
    booksCollection.insert_one(bookDocument)

# Load env vars
load_dotenv()
GOODREADS_USERNAME = os.getenv('GOODREADS_USERNAME')
GOODREADS_PASSWORD = os.getenv('GOODREADS_PASSWORD')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')

# Connect to local db
client = MongoClient("mongodb://localhost:27017")
database = client[MONGO_DB_NAME]
booksCollection = database.books
linksCollection = database.links

# Set of book links to follow
book_links = set()

# Set of other links (not books) to follow
other_links = set()

# List of goodreads link templates
# {
#   "template": "/book/show/*",
#   "ignore": False,
#   "queries": [
#       {
#           "name": "ref",
#           "ignore": True
#       }
#   ]      
# }
link_templates = []

# Setup selenium
options = Options()
options.headless = False # Switch to True later
options.add_argument("--window-size=1920,1200")
options.add_experimental_option("detach", True) # keep open
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

# Open Sign In Page
goodreads_sign_in_url = 'https://www.goodreads.com/ap/signin?language=en_US&openid.assoc_handle=amzn_goodreads_web_na&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.goodreads.com%2Fap-handler%2Fsign-in&siteState=1aad3e0863b9f621de0f7ccc0da34a7f'
driver.get(goodreads_sign_in_url)

# Sign In interaction
username = driver.find_element(By.NAME, "email")
username.send_keys(GOODREADS_USERNAME)
password = driver.find_element(By.NAME, "password")
password.send_keys(GOODREADS_PASSWORD)
submit_button = driver.find_element(By.CSS_SELECTOR, "#signInSubmit")
submit_button.click()
wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'siteHeader__topLevelLink')))


while True:
    url = ""
    result = linksCollection.find_one({"complete": False, "is_book": True, "$or": [{"attempts": {"$exists": False}},{"attempts": {"$lt": 2}}]})
    if result == None:
        result = linksCollection.find_one({"complete": False})
        if result == None:
            if linksCollection.count_documents({}) == 0:
                result = { "url": "/"}
            else:
                print()
                print("Everything is complete...?")
                break
    scrape_page(result["url"])
    time.sleep(2)
