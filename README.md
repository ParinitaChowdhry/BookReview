Project 1: Web Programming with Python and JavaScript

<!-- Project set-up -->
run the below commands in cmd to set-up the project
set application as flask application
set FLASK_APP=application.py
set debug to true
set FLASK_DEBUG=1
set db to online heroku
set DATABASE_URL= 'url of your db here'
flask run
webpages are rendered from inside templates folder 

<!-- Database set-up -->
three tables in DB: Users, Books, Reviews
CREATE TABLE users (
        id serial primary key, 
        name varchar(80),
        password varchar(80),
        email varchar(80)
);

CREATE TABLE books (
        id serial primary key, 
        title varchar(80),
        isbn int,
        author varchar(80),
        pub_year int
);

CREATE TABLE reviews (
        id serial primary key,
        user_id serial references users(id),
        book_id serial references books(id)
);

<!-- Insert records in DB from books.csv -->
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

Set up database for import of data
engine = create_engine('url of your db here')
db = scoped_session(sessionmaker(bind=engine))

with open('./books.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            # print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            isbn = row[0]
            title = row[1]
            author = row[2]
            year = row[3]
            db.execute("INSERT INTO books (title,isbn,author,pub_year) VALUES (:title, :isbn, :author, :year)",
            {"isbn": isbn, "title": title, "author": author, "year": year})
            print(f'\t{row[0]} ISBN {row[1]} Title {row[2]} Author {row[3]} Year')
            line_count += 1
    db.commit()
    print(f'Processed {line_count} lines.') 

