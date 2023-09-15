# GoodreadsScraper
![goodreads](https://github.com/JakeStrang1/GoodreadsScraper/assets/16689756/4caa8a85-6e47-4d5a-a763-69ea20a70360)

A web scraper to compile book data from Goodreads.

## Motivation
1. Create a function web scraper using Selenium.
2. Get some juicy Goodreads book data.

## Requirements
Our end goal is to download every single book listed on Goodreads.
We want to collect all the data related to each book, as well as the image links (we won't download the images themselves).
The tool will be run on a local machine, and the data will be stored in MongoDB.

The output data should live in a MongoDB collection called `books` and each document will look something like:
```
{
  "title": "Children of the Mind",
  "author": "Orson Scott Card",
  "series": true,
  "series_name": "Ender's Saga",
  "series_number": "4",
  "image_url": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1390362338i/31360.jpg",
  "rating": "3.77",
  ...
}
```

The web scraper should rate limit itself.
The web scraper should skip books that it has already saved.
