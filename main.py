import os


# Flask Import
from flask import Flask, render_template


# My Modules import


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

@app.route('/')
def home():
    return render_template("index.html", msg="Test app")


if __name__ == "__main__":
    app.run()