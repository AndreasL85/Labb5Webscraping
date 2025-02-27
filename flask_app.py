from flask import Flask, jsonify, request # Importerar Flask, jsonify och request från flask
from bs4 import BeautifulSoup  # Importerar BeautifulSoup från bs4
import requests     # Importerar requests
import json         # Importerar json
import re           # Importerar re
import datetime     # Importerar datetime
import os           # Importerar os
import hashlib      # Importerar hashlib

# Variabel för hemsidan
website_url = "https://books.toscrape.com/"

app = Flask(__name__) # Skapar en instans av Flask

# Skapar en route för /api/v1/category, för metoden PUT
@app.route("/api/v1/category", methods=["PUT"])
def update_category():
    try:
        # Försöker hämta data från request.json
        link = request.json["link"]
        category = request.json["category"].lower()

        # Om det inte finns någon data, returnera ett felmeddelande
        if not link or not category:
            return jsonify({"error": "Fel JSON-data skickad"}), 400

        # Försöker öppna filen categories.json
        with open("categories.json", "r") as file_obj:
            file_data = file_obj.read()
            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                category_dict = {}
            else:
                # Annars ladda in json data
                category_dict = json.loads(file_data)

    # Om filen inte finns eller om det är fel på json data, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        category_dict = {}

    # Om kategorin existerar i dictionary
    if category in category_dict:
        category_dict[category] = link # Uppdatera länken
    else:
        # Om kategorin inte existerar, returnera ett felmeddelande
        return jsonify({"error": f"Kategorin {category} existerar inte"}), 400

    try:
        # Försöker skriva till categories.json
        with open("categories.json", "w") as file_obj:
            # Skriv till filen
            json.dump(category_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json data, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Kunde inte spara information"}), 400

    # Returnera ett success-meddelande
    return jsonify({"success": "Kategorin har blivit uppdaterad"}), 200


# Skapar en route för /api/v1/category, för metoden POST
@app.route("/api/v1/category", methods=["POST"])
def add_category():
    try:
        # Försöker hämta data från request.json
        link = request.json["link"]
        category = request.json["category"].lower()

        # Om det inte finns någon data, returnera ett felmeddelande
        if not link or not category:
            return jsonify({"error": "Fel JSON-data skickad"}), 400

        # Försöker öppna filen categories.json
        with open("categories.json", "r") as file_obj:
            file_data = file_obj.read()

            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                category_dict = {}
            else:
                # Annars ladda in json data
                category_dict = json.loads(file_data)

    # Om filen inte finns eller om det är fel på json data, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        category_dict = {}

    # Om kategorin existerar i dictionary
    if category in category_dict:
        # Returnera ett felmeddelande
        return jsonify ({"error": "Kategorin existerar redan"}), 409
    else:
        # Lägg till kategorin i dictionary
        category_dict[category] = link

    try:
        # Försöker skriva till categories.json
        with open("categories.json", "w") as file_obj:
            # Skriv till filen
            json.dump(category_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json data, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Kunde inte spara information"}), 400

    # Returnera ett success-meddelande
    return jsonify({"success": "Kategorin har blivit tillagd"}), 200


# Skapar en route för /api/v1/category, för metoden GET
@app.route("/api/v1/category", methods=["GET"])
def get_all_categories():
    # Om filen categories.json existerar
    if os.path.exists("categories.json"):
        try:
            # Försöker öppna filen categories.json
            with open("categories.json", "r") as file_obj:
                file_data = file_obj.read()

                # Om filen är tom, returnera ett felmeddelande
                if not file_data.strip():
                    return jsonify({"error": "Oväntat fel, kunde inte läsa data"}), 400
                else:
                    # Annars ladda in json data
                    json_data = json.loads(file_data)

            # Returnera json_data
            return jsonify ({"categories": json_data}), 200

        # Felhantering
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": "Fel, gick inte hämta data"}), 400
    else:
        try:
            # Försöker hämta data från webbplatsen
            response = requests.get(website_url)

            # Om det inte gick att hämta data
            if response.status_code != 200:
                # Returnera ett felmeddelande
                return jsonify({"error": f"Fel, gick inte att hämta data från {website_url}"}), response.status_code

            # Skapa ett BeautifulSoup-objekt med response.text data, använd html-parser
            soup = BeautifulSoup(response.text, "html.parser")

            # Hämta alla boktitlar och href-värden som innehåller "catalogue/category/books/"
            categories = soup.select('a[href^="catalogue/category/books/"]')
            category_dict = {}

            # Gå igenom varje bok
            for category in categories:
                # Lägg till varje bok och dess href-värde i dictionary book_dict
                category_dict.update({category.text.strip().lower(): website_url + category.attrs["href"]}) # category.attrs["href"] hämtar attributet "href"
            try:
                # Försöker skriva till categories.json
                with open("categories.json", "w") as file_obj:
                    json.dump(category_dict, file_obj, ensure_ascii=False, indent=4)
            # Felhantering
            except (FileNotFoundError, json.JSONDecodeError):
                return jsonify({"error": "Oväntat fel, kunde inte läsa data"}), 400

            # Returnera book_dict
            return jsonify({"categories": category_dict})

        # Felhantering för requests
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


# Skapar en route för /api/v1/category/<category>, för metoden GET
@app.route("/api/v1/category/<category>", methods=["GET"])
def get_books(category):
    # Hämta kategorin, ta bort mellanslag och gör om till små bokstäver
    category = category.replace("%20", " ").lower()

    # Hämta dagens datum
    date = datetime.datetime.now().strftime("%y%m%d")
    # Skapa en sträng med kategorin och dagens datum
    expr = f"{category}_{date}.json"

    # Om filen existerar
    if os.path.exists(expr):
        try:
            # Försöker öppna filen
            with open(expr, "r") as file_obj:
                file_data = file_obj.read()

                # Om filen är tom, returnera ett felmeddelande
                if not file_data.strip():
                    jsonify ({"error": "Det finns inga böcker i kategorin"}), 400
                else:
                    # Annars ladda in json data
                    json_data = json.loads(file_data)

            # Returnera json_data
            return jsonify ({"books": json_data}), 200
        # Felhantering
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": f"Kunde inte läsa från kategorin {category}"}), 400
    else:
        try:
            # Försöker öppna filen categories.json
            with open("categories.json", "r") as file_obj:
                file_data = file_obj.read()
                # Om filen är tom, returnera ett felmeddelande
                if not file_data.strip():
                    return jsonify({"error": "Det finns inga böcker i kategorin"}), 400
                else:
                    # Annars ladda in json data
                    categories = json.loads(file_data)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": "Kunde inte hämta kategorier"}), 400


        try:
            # Försöker hämta data från webbplatsen, inom vald kategori
            response = requests.get(categories[category])
            # Om det inte gick att hämta data
            if response.status_code != 200:
                # Returnera ett felmeddelande
                return jsonify({"error": f"Fel, gick inte att hämta data från kategorin {category}"}), response.status_code # returnerar ett error om det inte gick att hämta data

            # Skapa ett BeautifulSoup-objekt med response.text data, använd html-parser
            soup = BeautifulSoup(response.text, "html.parser")
            # Hitta alla artiklar med klassen "product_pod"
            books = soup.find_all("article", class_ ="product_pod")

            # URL till webbplatsen som innehåller valutakurser
            bank_url = "https://open.er-api.com/v6/latest/GBP"
            # Hämta data från bank_url
            bank_response = requests.get(bank_url)

            # Om det gick att hämta data
            if bank_response.status_code == 200:
                json_data = bank_response.json()
                # Hämta valutakursen för GBP till SEK
                exchange_rate = json_data["rates"]["SEK"]

                # Om det inte finns någon valutakurs
                if not exchange_rate:
                    # Returnera ett felmeddelande
                    return jsonify ({"error": "Gick inte att hitta valutakurs för GBP till SEK"}), 400
            else:
                # Annars returnera ett felmeddelande
                return jsonify ({"error": "Kunde inte hämta valuta-kurser"}), 400

            # Skapa en tom dictionary
            book_dict = {}

            # Gå igenom varje bok
            for book in books:
                price = book.find("p", class_="price_color").text.strip()   # Hämta priset
                real_price = float(re.sub(r"[^\d.]", "", price)) * exchange_rate    # Räkna om priset till SEK
                rating = book.find("p", class_="star-rating")["class"][1]   # Hämta rating
                link = book.find("h3").find("a")    # Hämta länk som omges av h3
                real_link = link["href"].replace("../../../", "")   # Ta bort onödiga tecken från länken
                unique_id = hashlib.md5(f"{link['title']}_{real_link}".encode()).hexdigest()[:5]    # Skapa ett unikt ID, med hjälp av hashlib, baserat på titel och länk

                # Lägg till boken i dictionary
                book_dict[unique_id] = {"title":link["title"], "link": website_url + "catalogue/" +  real_link, "price": round(real_price,2), "rating": rating}

        # Felhantering
        except (AttributeError, KeyError): # om det inte går att hitta attributet eller nyckeln
            return jsonify({"error": "Kategorin existerar inte"}), 400
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

        # Skapa en sträng med kategorin och dagens datum
        file_name = f"{category}_{date}.json"

        try:
            # Försöker skriva till filen
            with open(file_name, "w", encoding="utf-8") as file_obj:
                json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)

            # Returnera book_dict
            return jsonify({"books": book_dict}), 200
        # Felhantering
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": "Fel, gick inte att hämta data"}), 400


# Skapar en route för /api/v1/category/<category>, för metoden POST
@app.route("/api/v1/category/<category>", methods=["POST"])
def add_book(category):
    try:
        # Försöker hämta data från request.json
        link = request.json["link"]
        price = request.json["price"]
        rating = request.json["rating"]
        title = request.json["title"]
        # Skapar ett unikt ID med hjälp av hashlib
        unique_id = hashlib.md5(f"{title}_{link}".encode()).hexdigest()[:5]

        # Om det inte finns någon data, returnera ett felmeddelande
        if not link or not price or not rating or not title:
            return jsonify({"error": "Fel JSON-data skickat"}), 400

        # Hämta dagens datum
        date = datetime.datetime.now().strftime("%y%m%d")
        # Hämta kategorin, ändra mellanslag och gör om till små bokstäver
        category = category.replace("%20", " ").lower()
        # Skapa en sträng med kategorin och dagens datum
        expr = f"{category}_{date}.json"

        # Försöker öppna filen
        with open(expr, "r") as file_obj:
            file_data = file_obj.read()

            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                book_dict = {}
            else:
                # Annars ladda in json data
                book_dict = json.loads(file_data)

    # Om filen inte finns eller om det är fel på json data, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": f"Det finns ingen kategori {category} att lägga till boken i"}), 400

    # Om boken redan existerar i dictionary
    if unique_id in book_dict:
        # Returnera ett felmeddelande
        return jsonify ({"error": "Boken existerar redan"}), 409
    else:
        # Lägg till boken i dictionary
        book_dict[unique_id] = {"title":title, "link": link, "price": price, "rating": rating}

    try:
        # Försöker skriva till filem
        with open(expr, "w") as file_obj:
            # Skriv till filen
            json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)

    # Felhantering
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"Error": "Could not save information"}), 400

    # Returnera ett success-meddelande
    return jsonify({"success": "Book has been added"}), 200


# Skapar en route för /api/v1/category/<category>, för metoden PUT
@app.route("/api/v1/category/<category>", methods=["PUT"])
def update_book(category):
    try:
        # Försöker hämta data från request.json
        unique_id = request.json["id"]
        link = request.json["link"]
        price = request.json["price"]
        rating = request.json["rating"]
        title = request.json["title"]

        # Om det inte finns någon data, returnera ett felmeddelande
        if not unique_id or not link or not price or not rating or not title:
            return jsonify({"error": "Fel JSON-data skickat"}), 400

        # Hämta dagens datum
        date = datetime.datetime.now().strftime("%y%m%d")
        # Hämta kategorin, ändra mellanslag och gör om till små bokstäver
        category = category.replace("%20", " ").lower()
        # Skapa en sträng med kategorin och dagens datum
        expr = f"{category}_{date}.json"

        # Försöker öppna filen
        with open(expr, "r") as file_obj:
            file_data = file_obj.read()

            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                book_dict = {}
            else:
                # Annars ladda in json data
                book_dict = json.loads(file_data)

    # Om filen inte finns eller om det är fel på json data, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        book_dict = {}

    # Om boken existerar i dictionary
    if unique_id in book_dict:
        # Uppdatera boken
        book_dict[unique_id]["title"] = title
        book_dict[unique_id]["link"] = link
        book_dict[unique_id]["price"] = price
        book_dict[unique_id]["rating"] = rating
    else:
        # Annars returnera ett felmeddelande
        return jsonify ({"error": f"Ingen bok med ID {unique_id} existerar"}), 409

    try:
        # Försöker skriva till filen
        with open(expr, "w") as file_obj:
            json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json data, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"Error": "Could not save information"}), 400

    # Returnera ett success-meddelande
    return jsonify({"success": f"Boken {title} har uppdaterats"}), 200


# Skapar en route för /api/v1/category/<category>, för metoden DELETE
@app.route("/api/v1/category/<category>", methods=["DELETE"])
def delete_book(category):
    # Gör om kategorin till små bokstäver
    category = category.lower()

    try:
        # Försöker hämta data från request.json
        unique_id = request.json["id"]

        # Om det inte finns någon data, returnera ett felmeddelande
        if not unique_id:
            return jsonify({"error": "Fel JSON-data skickad"}), 400

        # Hämta dagens datum
        date = datetime.datetime.now().strftime("%y%m%d")
        # Gör om mellanslag och gör om till små bokstäver
        category = category.replace("%20", " ").lower()
        # Skapa en sträng med kategorin och dagens datum
        expr = f"{category}_{date}.json"

        # Försöker öppna filen
        with open(expr, "r") as file_obj:
            file_data = file_obj.read()

            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                book_dict = {}
            else:
                # Annars ladda in json data
                book_dict = json.loads(file_data)

    # Om filen inte finns eller om det är fel på json data, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        book_dict = {}

    # Om boken existerar i dictionary
    if unique_id in book_dict:
        # Ta bort boken
        del book_dict[unique_id]
    else:
        # Annars returnera ett felmeddelande
        return jsonify ({"error": f"Ingen bok med ID {unique_id} existerar"}), 409

    try:
        # Försöker skriva till
        with open(expr, "w") as file_obj:
            # Skriv till filen
            json.dump(book_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json data, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Oväntat fel, kunde inte uppdatera data"}), 400

    # Returnera ett success-meddelande
    return jsonify({"success": "Boken har tagits bort"}), 200


# Skapar en route för /api/v1/category, för metoden DELETE
@app.route("/api/v1/category", methods=["DELETE"])
def delete_category():
    try:
        # Försöker hämta data från request.json
        category = request.json["category"].lower()

        # Om det inte finns någon data, returnera ett felmeddelande
        if not category:
            return jsonify({"error": "Fel JSON-data skickad"}), 400

        # Försöker öppna filen
        with open("categories.json", "r") as file_obj:
            file_data = file_obj.read()

            # Om filen är tom, skapa en tom dictionary
            if not file_data.strip():
                category_dict = {}
            else:
                # Annars ladda in json data
                category_dict = json.loads(file_data)

    # Om filen inte finns eller om det är fel på json data, skapa en tom dictionary
    except(FileNotFoundError, json.JSONDecodeError):
        category_dict = {}

    # Om kategorin existerar i dictionary
    if category in category_dict:
        # Ta bort kategorin
        del category_dict[category]

        # Hämta dagens datum
        date = datetime.datetime.now().strftime("%y%m%d")
        # Skapa en sträng med kategorin och dagens datum
        expr = f"{category}_{date}.json"

        # Om filen existerar, ta bort filen
        if os.path.exists(expr):
            os.remove(expr)
    else:
        # Annars returnera ett felmeddelande
        return jsonify({"error": f"Kategorin {category} existerar inte"}), 400

    try:
        # Försöker skriva till categories.json
        with open("categories.json", "w") as file_obj:
            json.dump(category_dict, file_obj, ensure_ascii=False, indent=4)

    # Om filen inte finns eller om det är fel på json data, returnera ett felmeddelande
    except(FileNotFoundError, json.JSONDecodeError):
        return jsonify({"Error": "Could not save information"}), 400

    # Returnera ett success-meddelande
    return jsonify({"success": f"Kategorin {category} har tagits bort"}), 200

# Om filen körs direkt
if __name__ == "__main__":
    app.run() # Starta applikationen

