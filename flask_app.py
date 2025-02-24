from flask import Flask, jsonify
from bs4 import BeautifulSoup
import requests
import json
import re

app = Flask(__name__)


@app.route("/app/v1/books")
def get_all_books():
    url = "https://books.toscrape.com/"
    response = requests.get(url)

    # Om det inte gick att hämta data
    if response.status_code != 200:
        return jsonify({"error": "Fel, gick inte att hämta data"}), response.status_code # returnerar ett error om det inte gick att hämta data

    # Skapa ett soup-objekt med response.text data
    soup = BeautifulSoup(response.text, "html.parser")

    # Hämta alla boktitlar
    books = soup.select('a[href^="catalogue/category/books/"]')
    book_dict = {}

    # Gå igenom varje bok
    for book in books:
        # Lägg till varje bok och dess href-värde i dictionaryn book_dict
        book_dict.update({book.text.strip(): book.attrs["href"]})

    # Returnera book_dict
    return jsonify({"books": book_dict})


if __name__ == "__main__":
    app.run(debug=True)