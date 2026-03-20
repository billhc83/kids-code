from flask import Flask, render_template, session
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)