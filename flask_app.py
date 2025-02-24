from flask import Flask, jsonify
from bs4 import BeautifulSoup
import requests
import json
import re
import datetime
website_url = "https://books.toscrape.com/"

app = Flask(__name__)


@app.route("/app/v1/books", methods=["GET"])
def get_all_books():

    response = requests.get(website_url)

    # Om det inte gick att hämta data
    if response.status_code != 200:
        return jsonify({"error": "Fel, gick inte att hämta data"}), response.status_code # returnerar ett error om det inte gick att hämta data

    # Skapa ett BeautifulSoup-objekt med response.text data, använd html-parser
    soup = BeautifulSoup(response.text, "html.parser")

    # Hämta alla boktitlar
    books = soup.select('a[href^="catalogue/category/books/"]')
    book_dict = {}

    # Gå igenom varje bok
    for book in books:
        # Lägg till varje bok och dess href-värde i dictionaryn book_dict
        book_dict.update({book.text.strip().lower(): book.attrs["href"]}) # book.attrs["href"] hämtar attributet "href"

    with open("categories.json", "w") as file_obj:
        json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)

    # Returnera book_dict
    return jsonify({"books": book_dict})

@app.route("/app/v1/books/<category>", methods=["GET"])
def get_books(category):
    category = category.lower()
    with open("categories.json", "r") as file_obj:
        file_data = file_obj.read()
        if not file_data.strip():
            print("Rejält fel")
        else:
            categories = json.loads(file_data)
            print("rejält rätt")

    response = requests.get(website_url + categories[category])
    if response.status_code != 200:
        return jsonify({"error": "Fel, gick inte att hämta data"}), response.status_code # returnerar ett error om det inte gick att hämta data

    # Skapa ett BeautifulSoup-objekt med response.text data, använd html-parser
    soup = BeautifulSoup(response.text, "html.parser")

    books = soup.find_all("article", class_ ="product_pod")

    bank_url = "https://open.er-api.com/v6/latest/GBP"
    bank_response = requests.get(bank_url)
    if bank_response.status_code == 200:
        json_data = bank_response.json()

        exchange_rate = json_data["rates"]["SEK"]
        if not exchange_rate:
            return jsonify ({"error": "Gick inte att hitta valutakurs för GBP till SEK"})
    else:
        return jsonify ({"error": "Kunde inte hämta valuta-kurser"})

    book_dict = {}
    for book in books:
        price = book.find("p", class_="price_color").text.strip()
        real_price = float(re.sub(r"[^\d.]", "", price)) * exchange_rate
        rating = book.find("p", class_="star-rating")["class"][1]
        link = book.find("h3").find("a")
        real_link = link["href"].replace("../../../", "")
        book_dict[link["title"]] = {"title":link["title"], "link": website_url + "catalogue/" + real_link, "price": real_price, "rating": rating}

    date = datetime.datetime.now().strftime("%y%m%d")
    file_name = f"{category}_{date}.json"

    with open(file_name, "w") as file_obj:
        json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)
    return jsonify({"books": book_dict})


if __name__ == "__main__":
    app.run(debug=True)

