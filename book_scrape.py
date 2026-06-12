'''
Landon Pack
IS-303 A07

Book Market web scraping program

Inputs:books.toscrape.com (3 pages of book listings)

Processes: scrape book data, store in SQLite via Peewee,
           query and analyze with Pandas, create an average price by rating chart

Outputs: Average price by rating printed table, number of books per rating printed table, Most expensive book,
        total amount of books in the db, price_by_rating.png, books.db

'''

import requests
from bs4 import BeautifulSoup
from peewee import SqliteDatabase, Model, CharField, FloatField, IntegerField, BooleanField
import pandas as pd
import matplotlib.pyplot as plt
import time

BASE_URL = "https://books.toscrape.com/"

db = SqliteDatabase("books.db")

class Book(Model):
    title = CharField()
    price = FloatField()
    instock = BooleanField()
    rating = IntegerField()
    class Meta:
        database = db



def fetch_and_parse(url):
    """Fetch a URL, return BeautifulSoup or None."""
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    return None




def scrape_books(num_pages=3):
    """Scrape each webpage and pull the data needed for the table"""
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    all_books = []
    for page_num in range(1, num_pages + 1):
        if page_num == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}catalogue/page-{page_num}.html"
        print(f"Scraping page {page_num}...")
        soup = fetch_and_parse(url)

        if soup is None:
            print(f"Failed to fetch page {page_num}... Skipping")
            continue

        books = soup.find_all("article", class_="product_pod")

        for book in books:
            title = book.find("h3").find("a")["title"]
            price = float(book.find("p", class_="price_color").text.strip()[1:].replace("£", ""))
            in_stock = "In stock" in book.find("p", class_="instock availability").text
            rating = rating_map[book.find("p", class_="star-rating")["class"][1]]

            all_books.append({
                "title": title,
                "price": price,
                "instock": in_stock,
                "rating": rating
            })

        time.sleep(5)

    return all_books


def store_books(book_list):
    """Store books in the data and skip if they already exist"""
    for data in book_list:
        existing = Book.get_or_none(Book.title == data["title"])
        if existing:
            print(f"Skipping: {data['title']}")
            continue
        Book.create(**data)
        print(f"Stored: {data['title']}")

def analyze():
    """Query DB, build DataFrame, run groupby, print results."""
    # Query all books from the database
    df = pd.DataFrame(list(Book.select().dicts()))

    # Average price by rating
    avg_price = df.groupby("rating")["price"].mean()
    print("\nAverage price by rating:")
    print(avg_price)

    # Count of books per rating
    count_by_rating = df.groupby("rating")["title"].count()
    print("\nNumber of books per rating:")
    print(count_by_rating)

    # Most expensive book
    most_expensive = df[df["price"] == df["price"].max()]
    print("\nMost expensive book:")
    print(most_expensive[["title", "price"]])
    # Amount of books in the db
    print(f"\nTotal books in database: {len(df)}")

    return df


def visualize(df):
    """Create and save a chart."""
    price_by_rating = df.groupby("rating")["price"].mean()
    price_by_rating.plot(kind="bar", color = "lightgreen")
    plt.title("Average Price by Rating")
    plt.xlabel("Rating")
    plt.ylabel("Average Price")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig("price_by_rating.png")
    plt.show()
   

def main():
    """Define the main flow"""
    db.connect()
    db.create_tables([Book])
    books = scrape_books()
    store_books(books)
    df = analyze()
    visualize(df)
    db.close()

main()