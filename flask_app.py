from flask import Flask, jsonify, request
from bs4 import BeautifulSoup
import requests
import json
import re
import datetime
import os
import hashlib
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
        #new_link = re.sub(r"(_\d+)(?=/index\.html$)", "", book.attrs["href"])
        # Lägg till varje bok och dess href-värde i dictionaryn book_dict
        book_dict.update({book.text.strip().lower(): website_url + book.attrs["href"]}) # book.attrs["href"] hämtar attributet "href"

    with open("categories.json", "w") as file_obj:
        json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)

    # Returnera book_dict
    return jsonify({"books": book_dict})

@app.route("/app/v1/books/<category>", methods=["GET"])
def get_books(category):
    category = category.lower()

    date = datetime.datetime.now().strftime("%y%m%d")
    expr = f"{category}_{date}.json"

    if os.path.exists(expr):
        with open(expr, "r") as file_obj:
            file_data = file_obj.read()
            if not file_data.strip():
                print("Rejält fel")
            else:
                categories = json.loads(file_data)
                print("rejält rätt")
        json_data = json.loads(file_data)
        return jsonify ({"books": json_data}), 200
    else:
        with open("categories.json", "r") as file_obj:
            file_data = file_obj.read()
            if not file_data.strip():
                print("Rejält fel")
            else:
                categories = json.loads(file_data)
                print("rejält rätt")

        response = requests.get(categories[category])
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
            unique_id = hashlib.md5(f"{link['title']}_{real_link}".encode()).hexdigest()[:5]
            book_dict[unique_id] = {"title":link["title"], "link": website_url + "catalogue/" +  real_link, "price": round(real_price,2), "rating": rating}

        file_name = f"{category}_{date}.json"

        with open(file_name, "w") as file_obj:
            json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)
        return jsonify({"books": book_dict})

@app.route("/app/v1/books/<category>", methods=["POST"])
def add_book(category):
    try:
        link = request.json["link"]
        price = request.json["price"]
        rating = request.json["rating"]
        title = request.json["title"]
        unique_id = hashlib.md5(f"{title}_{link}".encode()).hexdigest()[:5]



        # Om det inte finns någon data, returnera ett felmeddelande
        if not link or not price or not rating or not title:
            return jsonify({"Error": "Wrong input"}), 400

        date = datetime.datetime.now().strftime("%y%m%d")
        expr = f"{category}_{date}.json"

    # Försöker öppna filen ------

        with open(expr, "r") as file_obj:
            file_data = file_obj.read()
            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                book_dict = {}
            else:
                # Annars ladda in json datan
                book_dict = json.loads(file_data)
    # Om filen inte finns eller om det är fel på json datan, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        book_dict = {}
    if unique_id in book_dict:
        return jsonify ({"error": "Boken existerar redan"}), 409
    else:
        book_dict[unique_id] = {"title":title, "link": link, "price": price, "rating": rating}

    try:
        # Försöker skriva till
        with open(expr, "w") as file_obj:
            #
            json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json datan, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"Error": "Could not save information"}), 400

    #
    return jsonify({"success": "Book has been added"}), 200


if __name__ == "__main__":
    app.run(debug=True)

