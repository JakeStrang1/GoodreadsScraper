from selenium.webdriver.common.by import By
from utils import *

class BookScraper:
    def __init__(self, webdriver):
        self.webdriver = webdriver

    def scrape_book(self, book_url):
        # Assumed to already be at the book_url, we won't navigate there.
        book_url = ensure_rel_link(book_url)
        book = {
            "url": book_url # The Goodreads URL where this book is located
        }

        # Title
        title = self.__get_title()
        if title == "":
            raise Exception("title cannot be blank")
        book["title"] = title

        # Author
        author = self.__get_author()
        if author == "":
            raise Exception("author cannot be blank")
        book["author"] = author

        # Series
        is_series, series, series_number = self.__get_series()
        book["is_series"] = is_series
        if series != "":
            book["series"] = series
        if series_number != "":
            book["series_number"] = series_number
        
        # Image
        image_url = self.__get_image_url()
        if image_url == "":
            raise Exception("image_url cannot be blank")
        book["image_url"] = image_url

        # Description
        description = self.__get_description()
        if description != "":
            book["description"] = description

        # Published Date
        published_date = self.__get_published_date()
        if published_date != "":
            book["published_date"] = published_date

        # Pages
        pages = self.__get_pages()
        if pages != "":
            book["pages"] = pages

        # Rating
        rating = self.__get_rating()
        if rating != "":
            book["rating"] = rating
        
        # Rating Quantity
        rating_quantity = self.__get_rating_quantity()
        if rating_quantity != "":
            book["rating_quantity"] = rating_quantity
        
        # ISBN
        isbn = self.__get_isbn()
        if isbn != "":
            book["isbn"] = isbn
        
        # Genres
        genres = self.__get_genres()
        if genres != "":
            book["genres"] = genres
        
        return book

    def __get_title(self):
        try:
            return self.webdriver.find_element(By.CLASS_NAME, "Text__title1").text
        except:
            return ""
    
    def __get_author(self):
        try:
            return self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__contributor > h3 > div > span:nth-child(1) > a:nth-child(1) > span.ContributorLink__name").text
        except:
            return ""

    def __get_series(self):
        is_series = False
        series = ""
        series_number = ""
        try:
            series = self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageTitleSection > div.BookPageTitleSection__title > h3 > a").text
            is_series = True
        except:
            return is_series, series, series_number

        if is_series:
            series_sections = series.split("#") # "Ender's Saga #4"
            if len(series_sections) != 2:
                series_sections.append("") # The series number is blank in this case
            series = series_sections[0].strip()
            series_number = series_sections[1].strip()

        return is_series, series, series_number
        
    def __get_image_url(self):
        try:
            return self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__leftColumn > div > div.BookPage__bookCover > div > div > div > div > div > div > img").get_attribute("src")
        except:
            return ""

    def __get_description(self):
        try:
            return self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__description > div > div.TruncatedContent__text.TruncatedContent__text--large > div > div > span").text
        except:
            return ""

    def __get_published_date(self):
        published_date = ""
        try:
            published_date = self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookDetails > div > span:nth-child(1) > span > div > p:nth-child(2)").text
        except:
            return ""
        
        if published_date == "":
            return ""
        
        published_sections = published_date.split("published") # "First published May 1, 1990"
        if len(published_sections) == 2:
            return published_sections[1].strip()
        
        published_sections = published_date.split("publication") # "Expected publication October 31, 2023"
        if len(published_sections) == 2:
            return published_sections[1].strip()
        
        published_sections = published_date.split("Published") # "Published March 21, 2023"
        if len(published_sections) == 2:
            return published_sections[1].strip()
        
        return ""

    def __get_pages(self):
        pages = ""
        try:
            pages = self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookDetails > div > span:nth-child(1) > span > div > p:nth-child(1)").text
        except:
            return ""
        
        if pages == "":
            return ""
        
        pages_sections = pages.split("pages")
        if len(pages_sections) == 2:
            return pages_sections[0].strip()
        
        pages_sections = pages.split("Audio") # "Audio CD"
        if len(pages_sections) == 2:
            return "N/A"
        
        return ""

    def __get_rating(self):
        try:
            return self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__ratingStats > a > div:nth-child(1) > div").text
        except:
            return ""

    def __get_rating_quantity(self):
        rating_quantity = ""
        try:
            rating_quantity = self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__ratingStats > a > div:nth-child(2) > div > span:nth-child(1)").text
        except:
            return ""
        
        if rating_quantity == "":
            return ""

        rating_quantity_sections = rating_quantity.split("ratings") # "100 ratings"
        if len(rating_quantity_sections) == 2:
            return rating_quantity_sections[0].strip()
        
        rating_quantity_sections = rating_quantity.split("rating") # "1 rating"
        if len(rating_quantity_sections) == 2:
            return rating_quantity_sections[0].strip()
        
        return ""

    def __get_isbn(self):
        try:
            return self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookDetails > div > span:nth-child(2) > div.BookDetails__list > span > div > dl > div:nth-child(3) > dd > div > div.TruncatedContent__text.TruncatedContent__text--small").text
        except:
            return ""

    def __get_genres(self):
        try:
            genre_span = self.webdriver.find_element(By.CSS_SELECTOR, "#__next > div.PageFrame.PageFrame--siteHeaderBanner > main > div.BookPage__gridContainer > div.BookPage__rightColumn > div.BookPage__mainContent > div.BookPageMetadataSection > div.BookPageMetadataSection__genres > ul > span:nth-child(1)")
            return list(map(lambda x: x.text, genre_span.find_elements(By.CLASS_NAME, "Button__labelItem")))
        except:
            return []
