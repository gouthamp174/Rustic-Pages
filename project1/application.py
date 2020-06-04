import os
import hashlib
import requests
from base64 import b64encode

from flask import Flask, session, request, render_template, redirect, url_for, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# utility funtion to generate a hashed user password.
def hash_password(password):
    salt = b64encode(os.urandom(64)).decode()
    return hashlib.sha512(salt.encode() + password.encode()).hexdigest(), salt


# utility function to validate user password to saved hashed password.
def check_password(user_password, hashed_password, salt):
    new_hashed_password = hashlib.sha512(salt.encode() + user_password.encode()).hexdigest()
    return hashed_password == new_hashed_password


# utility funtion to get book details from "www.goodreads.com" using ISBN number.
def get_book_info_goodreads(isbn):
    url = "https://www.goodreads.com/book/review_counts.json"
    response = requests.get(url, params={"key": "HKKIUV7MdBBoiCzHmhFuw", "isbns": isbn}, timeout=10)
    if response.status_code == 200:
        books = response.json().get('books')
        return books.pop()
    else:
        return dict()


# definition of all APIs starts here.
@app.route("/")
def index():
    return render_template("index.html"), 200


@app.route("/signup", methods=["POST"])
def signup():
    # Read input information.
    input_info = dict()
    for attr in ["First name", "Last name", "Username", "Password"]:
        try:
            input_info[attr] = request.form.get(attr)
        except KeyError:
            return render_template("pre_login_error.html", error_msg=f"{attr} was not provided.")

    # get a secure hashed password from user password.
    hashed_password, salt = hash_password(input_info["Password"])

    # store new user information into database.
    db.execute("INSERT INTO users (user_name, password, password_salt, first_name, last_name) \
        VALUES (:user, :pwd, :salt, :fname, :lname)",
        {"user": input_info['Username'], "pwd": hashed_password, "salt": salt,
        "fname": input_info['First name'].capitalize(), "lname": input_info['Last name'].capitalize()})
    db.commit()

    # get back newly created user information.
    user = db.execute("SELECT * FROM users WHERE user_name=:user",
        {"user": input_info['Username']}).fetchone()

    if not user:
        return render_template("pre_login_error.html",
            error_msg= f"Failed to create new account for '{input_info['Username']}' user.")

    session.clear()
    session['user'] = user
    return redirect(url_for('home'))


@app.route("/login", methods=["POST"])
def login():
    # Read input information.
    input_info = dict()
    for attr in ["Username", "Password"]:
        try:
            input_info[attr] = request.form.get(attr)
        except KeyError:
            return render_template("pre_login_error.html", error_msg=f"{attr} was not provided.")

    # get existing user based on input information.
    user = db.execute("SELECT * FROM users WHERE user_name=:user", {"user": input_info['Username']}).fetchone()

    if not user or not check_password(input_info['Password'], user.password, user.password_salt):
        return render_template("pre_login_error.html", error_msg=f"Sorry! that username or password isn't right. Please try again or signup as a new user before logging in.")

    session.clear()
    session['user'] = user
    return redirect(url_for('home'))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route("/delete", methods=["POST"])
def delete_account():
    user = session['user']
    db.execute("DELETE FROM reviews WHERE user_id=:id", {"id": user.id})
    db.execute("DELETE FROM users WHERE id=:id", {"id": user.id})
    db.commit()

    session.clear()
    return redirect(url_for('index'))


@app.route("/home")
def home():
    # check if user is logged in.
    try:
        user = session['user']
    except KeyError:
        return redirect(url_for('index'))

    return render_template("home.html"), 200


@app.route("/search", methods=["GET", "POST"])
def search():
    # check if user is logged in.
    try:
        user = session['user']
    except KeyError:
        return redirect(url_for('index'))

    if request.method == "POST":
        # Read input information
        input_info = dict()
        for attr in ["criteria", "q"]:
            try:
                input_info[attr] = request.form.get(attr)
            except KeyError:
                return render_template("post_login_error.html", error_msg=f"{attr} was not provided.")

        return redirect(url_for('search', criteria=input_info["criteria"], q=input_info["q"]), code=303)
    else:
        criteria = request.args.get('criteria', '')
        q = request.args.get('q', '')

        books = None
        if criteria == 'isbn':
            books = db.execute("SELECT * FROM books WHERE isbn ILIKE :isbn", {"isbn": f"%{q}%"}).fetchall()
        elif criteria == 'title':
            books = db.execute("SELECT * FROM books WHERE title ILIKE :title", {"title": f"%{q}%"}).fetchall()
        elif criteria == 'author':
            books = db.execute("SELECT * FROM books WHERE author ILIKE :author", {"author": f"%{q}%"}).fetchall()

        return render_template('search.html', q=q, books=books), 200


@app.route("/books/<isbn>")
def book(isbn):
    # check if user is logged in.
    try:
        user = session['user']
    except KeyError:
        return redirect(url_for('index'))

    # Check if book with provided ISBN exists.
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    if not book:
        return render_template("post_login_error.html", error_msg=f"Book with ISBN: '{isbn}' was not found.")

    gr_info = get_book_info_goodreads(book.isbn)
    review_count, average_score = gr_info.get('work_ratings_count', '0'), gr_info.get('average_rating', '0.0')

    user = session['user']
    my_review = db.execute("SELECT * FROM reviews WHERE book_id=:book_id AND user_id=:user_id",
        {"book_id": book.id, "user_id": user.id}).fetchone()

    community_reviews = db.execute("SELECT reviews.id, reviews.created_at, reviews.book_id, \
        users.user_name,reviews.rating, reviews.title, reviews.review FROM reviews JOIN users \
        ON reviews.user_id = users.id WHERE reviews.book_id=:book_id AND reviews.user_id!=:user_id \
        ORDER BY reviews.created_at DESC",
        {"book_id": book.id, "user_id": user.id}).fetchall()

    return render_template("book.html", book=book, review_count=review_count, average_score=average_score, my_review=my_review, community_reviews=community_reviews), 200


@app.route("/review/add", methods=["POST"])
def add_review():
    # check if user is logged in.
    try:
        user = session['user']
    except KeyError:
        return redirect(url_for('index'))

    # Read input information
    input_info = dict()
    for attr in ["ISBN", "Rating", "Title", "Review"]:
        try:
            input_info[attr] = request.form.get(attr)
        except KeyError:
            return render_template("post_login_error.html", error_msg=f"{attr} was not provided.")

    # Get book information.
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": input_info['ISBN']}).fetchone()
    if not book:
        return render_template("post_login_error.html", error_msg=f"Failed to add review. Unable to retrieve corresponding book information.")

    db.execute("INSERT INTO reviews (book_id, user_id, rating, title, review) \
        VALUES (:book_id, :user_id, :rating, :title, :review)",
        {"book_id": book.id, "user_id": user.id, "rating": input_info['Rating'],
        "title": input_info['Title'], "review": input_info['Review']})
    db.commit()
    return redirect(url_for('book', isbn=book.isbn))


@app.route("/review/<int:id>/delete", methods=["POST"])
def delete_review(id):
    # check if user is logged in.
    try:
        user = session['user']
    except KeyError:
        return redirect(url_for('index'))

    # check if review exists.
    review = db.execute("SELECT * FROM reviews WHERE id=:id AND user_id=:user_id", {"id": id, "user_id": user.id}).fetchone()
    if not review:
        return render_template("post_login_error.html", error_msg="Either review doesn't exist or you don't have permissions to access this review.")

    # get a reference to book. (required to redirect to correct book page after deleting review.)
    book = db.execute("SELECT * FROM books WHERE id=:id", {"id": review.book_id}).fetchone()

    # delete the review.
    db.execute("DELETE FROM reviews WHERE id=:id", {"id": review.id})
    db.commit()

    if book:
        return redirect(url_for('book', isbn=book.isbn))
    else:
        return redirect(url_for('index'))


# API Access
@app.route("/api/<isbn>")
def rest_api_book(isbn):
    # Check if book with provided ISBN exists.
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    if not book:
        return abort(404, description="Resource not found")

    gr_info = get_book_info_goodreads(book.isbn)

    book_info = dict()
    book_info['title'] = book.title
    book_info['author'] = book.author
    book_info['year'] = book.published
    book_info['isbn'] = book.isbn
    book_info['review_count'] = gr_info.get('work_ratings_count', '')
    book_info['average_score'] = gr_info.get('average_rating', '')
    return book_info
