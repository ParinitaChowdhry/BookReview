import os
from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import json
from flask import jsonify

app = Flask(__name__)
# Check for environment variable set as database_url
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# Base route for the app is the registration page
@app.route("/")
def index():
    return render_template("register.html")

# Registration of new user and saving into users table
@app.route("/register", methods=["POST"])
def register():
    name_form = request.form.get("name")
    email_form = request.form.get("email")
    password_form = request.form.get("password")
    if db.execute("SELECT * FROM users WHERE email = :email", {"email": email_form}).rowcount != 0:
        return render_template("error.html", message="Email id exists ")
    if db.execute("SELECT * FROM users WHERE name = :name", {"name": name_form}).rowcount != 0:
        return render_template("error.html", message="User name exists ")
    db.execute("INSERT INTO users (name, email, password) VALUES (:name, :email, :password)",
    {"name": name_form, "email": email_form, "password": password_form})
    db.commit()
    return render_template("login.html")

# Render login page and validation from users table
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email_form = request.form.get("email")
        password_form = request.form.get("password")
        user_db = db.execute("SELECT * FROM users WHERE email = :email", {"email": email_form}).fetchall()
        for user in user_db :
            if user.password!= password_form :
                return render_template("error.html", message=" Something went wrong with your credentials. ")
            user = db.execute("SELECT * FROM users WHERE email = :email", {"email": email_form}).fetchone()
            name = user.name
            session['id'] = user.id
            return render_template("search.html", name = name)

# Render search page and results from books table
@app.route("/search", methods = ["POST"])
def search():
    if session.get('id') is not None:
        if request.method == "POST":
            search_form = ('%' + request.form.get("search") + '%').lower()
            result_db = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn  OR lower(title) LIKE :title OR pub_year LIKE :year OR lower(author) LIKE :author",{"isbn": search_form, "title": search_form,"year": search_form,"author": search_form}).fetchall()
            if len(result_db)==0:
                return render_template("error.html", message = " No such book exists ")
            return render_template("book.html", results=result_db)              
    return render_template("login.html")

# Render details when a particular book is selected from a search page 
# details from books table, reviews from reviews table and Good Reads API
# save user review in reviews table
@app.route('/detail/<isbn>', methods = ["GET", "POST"])
def show_detail(isbn):
    if session.get('id') is not None:
        if request.method == "GET":
            # get results from API when you provide isbn of particular book
            result_api = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
            # display details from db
            result_db = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn": isbn}).fetchone()
            review_db= db.execute("SELECT * FROM reviews INNER JOIN users on reviews.user_id = users.id WHERE book_id = :book_id",{"book_id": result_db.id}).fetchall()
            # check if user has already created review for that particular book
            # display the option to write a review only if flag is True 
            flag = True
            for review in review_db:
                if review.user_id == session.get('id'):
                    flag = False
            return render_template("detail.html", results= result_db, books = result_api.json(), reviews=review_db, flag = flag)
        else:
            rating_form = request.form.get("rating")
            review_form = request.form.get("review")
            book_db = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn": isbn}).fetchone()
            book_id = book_db.id
            db.execute("INSERT INTO reviews (user_id, book_id, rating, review) VALUES (:user_id, :book_id, :rating, :review)",
            {"user_id": session.get('id'), "book_id": book_id, "rating": rating_form, "review": review_form})
            db.commit()
            return render_template("search.html")
    return render_template("login.html")

@app.route('/logout', methods = ["GET"])
def logout():
    if session.get('id') is not None:
        # remove the username from the session if it's there
        session.pop('id', None)
        return render_template("login.html")
    return render_template("login.html")

# return json object
@app.route('/api/<isbn>')
def api(isbn):
    # get results from API when you provide isbn of particular book
     result_api = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    if result_api.status_code != 200:
        return jsonify({"error": "Not found"}), 404
        # display details from db
    result_db = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn": isbn}).fetchone()
    if result_db is not None:
        return jsonify({"title":result_db.title, "author":result_db.author, 
        "year":result_db.pub_year, "review_count":result_api.json()['books'][0]['reviews_count'],
        "average_score":result_api.json()['books'][0]['average_rating']})
    return jsonify({"error": "Not found"}), 404





        

