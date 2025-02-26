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

@app.route("/api/v1/category", methods=["PUT"])
def update_category():
    try:
        link = request.json["link"]
        category = request.json["category"]

        # Om det inte finns någon data, returnera ett felmeddelande
        if not link or not category:
            return jsonify({"Error": "Wrong input"}), 400

        # Försöker öppna filen ------
        with open("categories.json", "r") as file_obj:
            file_data = file_obj.read()
            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                category_dict = {}
            else:
                # Annars ladda in json datan
                category_dict = json.loads(file_data)

    # Om filen inte finns eller om det är fel på json datan, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        category_dict = {}

    if category in category_dict:
        category_dict[category] = link
    else:
        return jsonify({"error": f"Kategorin {category} existerar inte"}), 400

    try:
        # Försöker skriva till
        with open("categories.json", "w") as file_obj:
            #
            json.dump(category_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json datan, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"Error": "Could not save information"}), 400

    #
    return jsonify({"success": "Kategorin har blivit uppdaterad"}), 200


@app.route("/api/v1/category", methods=["POST"])
def add_category():
    try:
        link = request.json["link"]
        category = request.json["category"].lower()

        # Om det inte finns någon data, returnera ett felmeddelande
        if not link or not category:
            return jsonify({"Error": "Wrong input"}), 400

        # Försöker öppna filen ------
        with open("categories.json", "r") as file_obj:
            file_data = file_obj.read()
            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                category_dict = {}
            else:
                # Annars ladda in json datan
                category_dict = json.loads(file_data)

    # Om filen inte finns eller om det är fel på json datan, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        category_dict = {}

    if category in category_dict:
        return jsonify ({"error": "Kategorin existerar redan"}), 409
    else:
        category_dict[category] = link

    try:
        # Försöker skriva till
        with open("categories.json", "w") as file_obj:
            #
            json.dump(category_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json datan, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"Error": "Could not save information"}), 400

    #
    return jsonify({"success": "Kategorin har blivit tillagd"}), 200

@app.route("/api/v1/category", methods=["GET"])
def get_all_categories():

    if os.path.exists("categories.json"):
        try:
            with open("categories.json", "r") as file_obj:
                file_data = file_obj.read()
                if not file_data.strip():
                    print("Rejält fel")
                else:
                    categories = json.loads(file_data)
                    print("rejält rätt")
            json_data = json.loads(file_data)
            return jsonify ({"categories": json_data}), 200

        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": "Fel, gick inte hämta data"}), 400
    else:
        try:
            response = requests.get(website_url)

            # Om det inte gick att hämta data
            if response.status_code != 200:
                return jsonify({"error": "Fel, gick inte att hämta data"}), response.status_code # returnerar ett error om det inte gick att hämta data

            # Skapa ett BeautifulSoup-objekt med response.text data, använd html-parser
            soup = BeautifulSoup(response.text, "html.parser")

            # Hämta alla boktitlar
            categories = soup.select('a[href^="catalogue/category/books/"]')
            category_dict = {}

            # Gå igenom varje bok
            for category in categories:
                # Lägg till varje bok och dess href-värde i dictionaryn book_dict
                category_dict.update({category.text.strip().lower(): website_url + category.attrs["href"]}) # book.attrs["href"] hämtar attributet "href"
            try:
                with open("categories.json", "w") as file_obj:
                    json.dump(category_dict, file_obj, ensure_ascii=False, indent=4)
            except (FileNotFoundError, json.JSONDecodeError):
                return jsonify({"error": "Fel, gick inte att hämta data"}), 400

            # Returnera book_dict
            return jsonify({"categories": category_dict})
            # Felhantering
        except requests.ConnectionError:  # om det inte går att ansluta till servern
            return jsonify({"error": "Fel, kunde inte ansluta till servern"}), 400
        except requests.Timeout:  # om det tar för lång tid att ansluta
            return jsonify({"error":"Fel, tog för lång tid att ansluta"}), 400
        except requests.HTTPError:  # om det blir ett HTTP-fel
            return jsonify({"error":"Fel, HTTP fel"}), 400
        except requests.JSONDecodeError:  # om det inte går att avkoda JSON-data
            return jsonify({"error":"Fel, kunde inte avkoda JSON data"}), 400
        except requests.RequestException:  # om det blir ett okänt fel
            return jsonify({"error": "Fel, okänt fel inträffade"}), 400

@app.route("/api/v1/category/<category>", methods=["GET"])
def get_books(category):
    category = category.replace("%20", " ").lower()

    date = datetime.datetime.now().strftime("%y%m%d")
    expr = f"{category}_{date}.json"
    print(f"'{expr}'")

    if os.path.exists(expr):
        try:
            with open(expr, "r") as file_obj:
                file_data = file_obj.read()
                if not file_data.strip():
                    return jsonify({"error": "Filen är tom"}), 400
                else:
                    categories = json.loads(file_data)
            json_data = json.loads(file_data)
            return jsonify ({"books": json_data}), 200

        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": f"File Exists - Kunde inte läsa från kategorin {category}"}), 400
    else:
        try:
            with open("categories.json", "r") as file_obj:
                file_data = file_obj.read()
                if not file_data.strip():
                    return jsonify({"error": "Filen är tom"}), 400
                else:
                    categories = json.loads(file_data)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": "Kunde inte hämta kategorier"}), 400


        try:
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
        except (AttributeError, KeyError):
            return jsonify({"error": "Kategorin existerar inte"}), 400
        # Felhantering
        except requests.ConnectionError:  # om det inte går att ansluta till servern
            return jsonify({"error": "Fel, kunde inte ansluta till servern"}), 400
        except requests.Timeout:  # om det tar för lång tid att ansluta
            return jsonify({"error": "Fel, tog för lång tid att ansluta"}), 400
        except requests.HTTPError:  # om det blir ett HTTP-fel
            return jsonify({"error": "Fel, HTTP fel"}), 400
        except requests.JSONDecodeError:  # om det inte går att avkoda JSON-data
            return jsonify({"error": "Fel, kunde inte avkoda JSON data"}), 400
        except requests.RequestException:  # om det blir ett okänt fel
            return jsonify({"error": "Fel, okänt fel inträffade"}), 400

        file_name = f"{category}_{date}.json"

        try:
            with open(file_name, "w", encoding="utf-8") as file_obj:
                json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)
            return jsonify({"books": book_dict})
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": "Fel, gick inte att hämta data"}), 400

@app.route("/api/v1/category/<category>", methods=["POST"])
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
        category = category.replace("%20", " ").lower()
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
        return jsonify({"error": f"Det finns ingen kategori {category} att lägga till boken i"}), 400

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

@app.route("/api/v1/category/<category>", methods=["PUT"])
def update_book(category):
    try:
        unique_id = request.json["id"]
        link = request.json["link"]
        price = request.json["price"]
        rating = request.json["rating"]
        title = request.json["title"]

        # Om det inte finns någon data, returnera ett felmeddelande
        if not unique_id or not link or not price or not rating or not title:
            return jsonify({"Error": "Wrong input"}), 400

        date = datetime.datetime.now().strftime("%y%m%d")
        category = category.replace("%20", " ").lower()
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
        book_dict[unique_id]["title"] = title
        book_dict[unique_id]["link"] = link
        book_dict[unique_id]["price"] = price
        book_dict[unique_id]["rating"] = rating
    else:
        return jsonify ({"error": f"Ingen bok med ID {unique_id} existerar"}), 409

    try:
        # Försöker skriva till
        with open(expr, "w") as file_obj:
            #
            json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json datan, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"Error": "Could not save information"}), 400

    #
    return jsonify({"success": f"Boken {title} har uppdaterats"}), 200

@app.route("/api/v1/category/<category>", methods=["DELETE"])
def delete_book(category):
    category = category.lower()
    try:
        unique_id = request.json["id"]

        # Om det inte finns någon data, returnera ett felmeddelande
        if not unique_id:
            return jsonify({"Error": "Wrong input"}), 400

        date = datetime.datetime.now().strftime("%y%m%d")
        category = category.replace("%20", " ").lower()
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
        del book_dict[unique_id]
    else:
        return jsonify ({"error": f"Ingen bok med ID {unique_id} existerar"}), 409

    try:
        # Försöker skriva till
        with open(expr, "w") as file_obj:
            #
            json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json datan, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"Error": "Could not save information"}), 400

    #
    return jsonify({"success": "Boken har tagits bort"}), 200



@app.route("/api/v1/category", methods=["DELETE"])
def delete_category():
    try:
        category = request.json["category"].lower()

        # Om det inte finns någon data, returnera ett felmeddelande
        if not category:
            return jsonify({"Error": "Wrong input"}), 400

        # Försöker öppna filen ------
        with open("categories.json", "r") as file_obj:
            file_data = file_obj.read()
            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                category_dict = {}
            else:
                # Annars ladda in json datan
                category_dict = json.loads(file_data)

    # Om filen inte finns eller om det är fel på json datan, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        category_dict = {}


    if category in category_dict:
        del category_dict[category]

        date = datetime.datetime.now().strftime("%y%m%d")
        expr = f"{category}_{date}.json"

        if os.path.exists(expr):
            os.remove(expr)
    else:
        return jsonify({"error": f"Kategorin {category} existerar inte"}), 400

    try:
        # Försöker skriva till
        with open("categories.json", "w") as file_obj:
            #
            json.dump(category_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json datan, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"Error": "Could not save information"}), 400

    #
    return jsonify({"success": f"Kategorin {category} har tagits bort"}), 200

if __name__ == "__main__":
    app.run(debug=True)

