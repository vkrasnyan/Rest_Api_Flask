from dataclasses import dataclass
import sqlite3
from typing import Any, Optional, List, Union


def enable_foreign_keys(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()

DATA: List[dict] = [
    {'id': 1, 'title': 'A Byte of Python', 'author': 1},
    {'id': 2, 'title': 'Moby-Dick; or, The Whale', 'author': 2},
    {'id': 3, 'title': 'War and Peace', 'author': 3},
]

DATA_AUTHORS: List[dict] = [
    {'id': 1, 'first_name': 'C', 'middle_name': 'H', 'last_name': 'Swaroop'},
    {'id': 2, 'first_name': 'Henry',  'middle_name': ' ', 'last_name': 'Melville'},
    {'id': 3, 'first_name': 'Lev', 'middle_name': 'Nikolaevich', 'last_name': 'Tolstoi'},
]


@dataclass
class Author:
    first_name: str
    middle_name: str
    last_name: str
    author_id: Optional[int] = None

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


@dataclass
class Book:
    title: str
    author: str
    id: Optional[int] = None

    def __getitem__(self, item: str) -> Union[int, str]:
        return getattr(self, item)


def init_db_authors(initial_records: List[dict]) -> None:
    with sqlite3.connect('table_books.db') as conn:
        enable_foreign_keys(conn)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='table_authors'; 
            """
        )
        exists = cursor.fetchone()
        if not exists:
            cursor.executescript(
                """
                CREATE TABLE `table_authors` (
                    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name VARCHAR(50) NOT NULL,
                    middle_name VARCHAR(50),
                    last_name VARCHAR(50) NOT NULL
                )
                """
            )
        cursor.executemany(
                """
                INSERT INTO 'table_authors' (first_name, middle_name, last_name) VALUES (?, ?, ?)
                """,
                [
                    (item['first_name'], item['middle_name'], item['last_name'])
                    for item in initial_records
                ]
            )

def init_db_books(initial_records: List[dict]) -> None:
    with sqlite3.connect('table_books.db') as conn:
        enable_foreign_keys(conn)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='table_books'; 
            """
        )
        exists = cursor.fetchone()
        if not exists:
            cursor.executescript(
                """
                CREATE TABLE `table_books` (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author INTEGER NOT NULL REFERENCES table_authors(author_id) ON DELETE CASCADE
                )
                """
            )
        cursor.executemany(
                """
                INSERT INTO 'table_books' (title, author) VALUES (?, ?)
                """,
                [
                    (item['title'], item['author'])
                    for item in initial_records
                ]
            )


def _get_book_obj_from_row(row) -> Book:
    book_id = row[0]
    title = row[1]
    author_id = row[2]

    author = get_author_by_id(author_id)

    if author:
        book = Book(id=book_id, title=title, author=author)
    else:
        book = Book(id=book_id, title=title, author="Author details not found")

    return book

def _get_author_obj_from_row(row) -> Author:
    return Author(author_id=row[0], first_name=row[1], middle_name=row[2], last_name=row[3])

def get_all_books() -> List[Book]:
    with sqlite3.connect('table_books.db') as conn:
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * from 'table_books'
            """
        )
        all_books: List[Book] = cursor.fetchall()
        return [_get_book_obj_from_row(row) for row in all_books]

def get_all_authors() -> List[Author]:
    with sqlite3.connect('table_books.db') as conn:
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * from 'table_authors'
            """
        )
        all_authors: List[Author] = cursor.fetchall()
        return [_get_author_obj_from_row(row) for row in all_authors]

def add_book(title: str, author_id: int) -> Book:
    with sqlite3.connect('table_books.db') as conn:
        enable_foreign_keys(conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO 'table_books' (title, author) VALUES (?, ?)
            """,
            (title, author_id)
        )
        book_id = cursor.lastrowid

    book = Book(id=book_id, title=title, author=author_id)
    return book



def add_book_with_author(book_data: dict) -> Book:
    title = book_data['title']
    author_data = book_data['author']

    existing_author = get_author_by_name(author_data.first_name, author_data.last_name, author_data.middle_name)

    if existing_author:
        author_id = existing_author['author_id']
        book = add_book(title, author_id)


    else:
        # Add new author to 'table_authors'
        new_author = Author(
            first_name=author_data.first_name,
            middle_name=author_data.middle_name,
            last_name=author_data.last_name
        )
        book_author = add_author(new_author)
        author_id = book_author.author_id
        book = add_book(title, author_id)

    return book


def add_author(author: Author) -> Author:
    with sqlite3.connect('table_books.db') as conn:
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            f"""
                    INSERT INTO 'table_authors'
                    (first_name, middle_name, last_name) VALUES (?, ?, ?)
                    """,
            (author.first_name, author.middle_name, author.last_name,),
        )
        author.author_id = cursor.lastrowid
        return author

def get_book_by_id(book_id: int) -> Optional[Book]:
    with sqlite3.connect('table_books.db') as conn:
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(f"""SELECT * from 'table_books' WHERE id= "%s" """ % book_id)
        book = cursor.fetchone()
        if book:
            return _get_book_obj_from_row(book)

def get_author_by_id(author_id: int) -> Optional[Author]:
    with sqlite3.connect('table_books.db') as conn:
        enable_foreign_keys(conn)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(f"""SELECT * from 'table_authors' WHERE author_id= "%s" """ % author_id)
        author = cursor.fetchone()
        if author:
            return _get_author_obj_from_row(author)


def get_author_by_name(first_name: str, last_name: str, middle_name: Optional[str] = None) -> Optional[dict]:
    with sqlite3.connect('table_books.db') as conn:
        cursor = conn.cursor()
        if middle_name:
            cursor.execute(
                """
                SELECT * FROM table_authors
                WHERE first_name = ? AND middle_name = ? AND last_name = ?
                """,
                (first_name, middle_name, last_name)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM table_authors
                WHERE first_name = ? AND last_name = ?
                """,
                (first_name, last_name)
            )

        author = cursor.fetchone()
        if author:
            return {
                'author_id': author[0],
                'first_name': author[1],
                'middle_name': author[2],
                'last_name': author[3]
            }
        else:
            return None
def update_book_by_id(book: Book) -> Book:
    with sqlite3.connect('table_books.db') as conn:
        enable_foreign_keys(conn)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE 'table_books'
            SET title = ?, author = ?
            WHERE id = ?
            """, (book.title, book.author, book.id),
        )
        conn.commit()
        return book

def update_author_by_id(author: Author) -> Author:
    with sqlite3.connect('table_books.db') as conn:
        enable_foreign_keys(conn)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            f"""
                    UPDATE 'table_authors'
                    SET first_name = ?, middle_name = ?, last_name = ?
                    WHERE author_id = ?
                    """, (author.first_name, author.middle_name, author.last_name, author.author_id),
        )
        conn.commit()

def delete_book_by_id(book_id: int) -> None:
    with sqlite3.connect('table_books.db') as conn:
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            f"""
            DELETE FROM 'table_books'
            WHERE id = ?
            """, (book_id,)
        )
        conn.commit()

def delete_author_by_id(author_id: int) -> None:
    with sqlite3.connect('table_books.db') as conn:
        enable_foreign_keys(conn)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            f"""
                    DELETE FROM 'table_authors'
                    WHERE author_id = ?
                    """, (author_id,)
        )
        conn.commit()

def get_book_by_title(title: str) -> Optional[Book]:
    with sqlite3.connect('table_books.db') as conn:
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(f"SELECT * from 'table_books' WHERE title = '%s'" % title)
        book = cursor.fetchone()
        if book:
            return _get_book_obj_from_row(book)

def get_books_by_author_id(author_id: int) -> List[Book]:
    with sqlite3.connect('table_books.db') as conn:
        enable_foreign_keys(conn)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * from 'table_books'
            WHERE author = ?
            """, (author_id,)
        )
        books: List[Book] = cursor.fetchall()
        return [_get_book_obj_from_row(row) for row in books]


if __name__ == '__main__':
    init_db_authors(DATA_AUTHORS)
    init_db_books(DATA)