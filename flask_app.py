from flask import Flask
import requests
import json

app = Flask(__name__)


@app.route("/app/v1/knark")
def knark():
    return "Knark"

if __name__ == "__main__":
    app.run(debug=True)