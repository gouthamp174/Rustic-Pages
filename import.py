import os
import sys
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

filename = "books.csv"

try:
    with open(filename, 'r') as f:
        reader = csv.reader(f)

        for line_no, line in enumerate(reader):
            if line_no > 0:
                isbn, title, author, year = line

                db.execute("INSERT INTO books (isbn, title, author, published) \
                    VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})

                print(f"Added book-{line_no} information for ISBN: {isbn}.")
        db.commit()
except IOError:
    print(f"Error: Failed to open {filename} file.")
    sys.exit(1)
