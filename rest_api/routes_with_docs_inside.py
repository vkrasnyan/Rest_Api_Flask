from dataclasses import asdict
from werkzeug.serving import WSGIRequestHandler

from flasgger import Swagger, APISpec
from apispec_webframeworks.flask import FlaskPlugin
from apispec.ext.marshmallow import MarshmallowPlugin

from flask import Flask, request
from flask_restful import Api, Resource, abort
from marshmallow import ValidationError

from models import (get_all_books, get_all_authors, add_author, get_book_by_id, update_book_by_id,
                    delete_book_by_id, get_author_by_id, update_author_by_id, delete_author_by_id,
                    get_books_by_author_id, Author, add_book_with_author)
from schemas import BookSchema, AuthorSchema, AuthorDetailSchema, BookDetailSchema

app = Flask(__name__)
api = Api(app)

spec = APISpec(
    title='BookList API',
    version='1.0.0',
    openapi_version='2.0',
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)


class BookList(Resource):
    def get(self):
        """
            An endpoint that lists books
            ---
            tags:
              - books
            responses:
              200:
                description: List of books
                schema:
                  type: array
                  items:
                    $ref: '#/definitions/Book'
        """
        schema = BookDetailSchema(many=True)
        return schema.dump(get_all_books())

    def post(self):
        """
            An endpoint that creates a new book
            ---
            tags:
              - books
            parameters:
              - in: body
                name: new book params
                schema:
                  $ref: '#/definitions/Book'
            responses:
              201:
                description: The book has been created
                schema:
                  $ref: '#/definitions/Book'
              400:
                description: No input data provided
              422:
                description: The book could not be created
        """
        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, 400

        try:
            data = BookSchema().load(json_data)
        except ValidationError as err:
            return err.messages, 422

        try:
            book = add_book_with_author(data)
        except ValidationError as err:
            return err.messages, 422

        result = BookSchema().dump(book)
        return {"message": "Book created", "book": result}, 201


class BookResource(Resource):
    def get(self, book_id):
        """
            An endpoint that retrieves a book by id
            ---
            tags:
              - books
            parameters:
              - in: path
                name: book_id
                description: The book id
            responses:
              200:
                description: The book has been retrieved
                schema:
                  type: object
                  items:
                    $ref: '#/definitions/Book'
              404:
                description: Book not found
        """
        book_schema = BookSchema()
        book = get_book_by_id(book_id)
        if book is None:
            abort(404, message=f"Book {book_id} doesn't exist")
        return book_schema.dump(book)

    def put(self, book_id):
        """
                An endpoint that updates a book
                ---
                tags:
                  - books
                parameters:
                  - in: body
                    name: updated book params
                    schema:
                      $ref: '#/definitions/Book'
                responses:
                  200:
                    description: The book has been updated
                    schema:
                      $ref: '#/definitions/Book'
                  400:
                    description: No input data provided
                  404:
                    description: Book not found
                  422:
                    description: The book could not be updated
        """
        book_schema = BookSchema()
        json_data = request.get_json()
        if not json_data:
            abort(400, message="No input data provided")

        try:
            book_data = book_schema.load(json_data)
        except ValidationError as err:
            return err.messages, 422

        book = get_book_by_id(book_id)
        if book is None:
            abort(404, message=f"Book {book_id} doesn't exist")

        book.title = book_data["title"]
        book_author_data = book_data["author"]
        author_id = book_author_data["author_id"]
        existing_author = get_author_by_id(author_id)
        if existing_author:
            book.author = existing_author['author_id']
            book = update_book_by_id(book)
        else:
            new_author = Author(
                first_name=book_author_data["first_name"],
                middle_name=book_author_data["middle_name"],
                last_name=book_author_data["last_name"]
            )
            book.author = add_author(new_author)
            author_id = new_author.author_id
            book.author = author_id
            book = update_book_by_id(book)

        return book_schema.dump(book), 200

    def delete(self, book_id):
        """
            An endpoint that deletes a book
            ---
            tags:
              - books
            parameters:
              - in: path
                name: book_id
                description: The book id
            responses:
              204:
                description: The book has been deleted
                schema:
                  type: object
                  items:
                    $ref: '#/definitions/Book'
              404:
                description: Book not found
        """
        book = get_book_by_id(book_id)
        if book is None:
            abort(404, message=f"Book {book_id} doesn't exist")
        delete_book_by_id(book_id)
        return '', 204


class AuthorList(Resource):
    def get(self):
        """
            An endpoint that lists authors
            ---
            tags:
              - authors
            responses:
              200:
                description: List of authors
                schema:
                  type: array
                  items:
                    $ref: '#/definitions/Author'
        """
        schema = AuthorSchema(many=True)
        return schema.dump(get_all_authors())

    def post(self):
        """
        An endpoint that creates a new author
            ---
            tags:
              - authors
            parameters:
              - in: body
                name: new author params
                schema:
                  $ref: '#/definitions/Author'
            responses:
              201:
                description: The author has been created
                schema:
                  $ref: '#/definitions/Author'
              400:
                description: No input data provided
        """
        data = request.json
        schema = AuthorSchema()
        try:
            author = schema.load(data)
        except ValidationError as err:
            return err.messages, 400

        author = add_author(author)
        return schema.dump(author), 201


class AuthorResource(Resource):
    def get(self, author_id):
        """
                    An endpoint that retrieves an author by id
                    ---
                    tags:
                      - authors
                    parameters:
                      - in: path
                        name: author_id
                        description: The author id
                    responses:
                      200:
                        description: The author has been retrieved
                        schema:
                          type: object
                          items:
                            $ref: '#/definitions/Author'
                      404:
                        description: Author not found
        """
        author = get_author_by_id(author_id)
        if not author:
            abort(404, message=f"Author {author_id} doesn't exist")

        books = get_books_by_author_id(author_id)
        author_detail = asdict(author)
        author_detail['books'] = [asdict(book) for book in books]

        schema = AuthorDetailSchema()
        return schema.dump(author_detail)

    def put(self, author_id):
        """
                        An endpoint that updates an author
                        ---
                        tags:
                          - authors
                        parameters:
                          - in: body
                            name: updated author params
                            schema:
                              $ref: '#/definitions/Author'
                        responses:
                          200:
                            description: The author has been updated
                            schema:
                              $ref: '#/definitions/Author'
                          400:
                            description: No input data provided
                          404:
                            description: Author not found
                          422:
                            description: The author could not be updated
        """
        schema = AuthorSchema()
        json_data = request.get_json()
        if not json_data:
            abort(400, message="No input data provided")
        try:
            author_data = schema.load(json_data)
        except ValidationError as err:
            return err.messages, 422

        author = get_author_by_id(author_id)
        if author is None:
            abort(404, message=f"Author {author_id} doesn't exist")

        author.first_name = author_data.first_name
        author.middle_name = author_data.middle_name
        author.last_name = author_data.last_name
        update_author_by_id(author)
        return schema.dump(author)

    def delete(self, author_id):
        """
                    An endpoint that deletes an author by id
                    ---
                    tags:
                      - authors
                    parameters:
                      - in: path
                        name: author_id
                        description: The author id
                    responses:
                      204:
                        description: The author has been deleted
                        schema:
                          type: object
                          items:
                            $ref: '#/definitions/Author'
                      404:
                        description: Author not found
                """
        schema = AuthorSchema()
        author = get_author_by_id(author_id)
        if author is None:
            abort(404, message=f"Author {author_id} doesn't exist")
        delete_author_by_id(author_id)
        return '', 204


template = spec.to_flasgger(
    app,
    definitions=[BookSchema]
)

swagger = Swagger(app, template=template)

api.add_resource(BookList, '/api/books')
api.add_resource(BookResource, '/api/books/<book_id>')
api.add_resource(AuthorList, '/api/authors')
api.add_resource(AuthorResource, '/api/authors/<author_id>')

if __name__ == '__main__':
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(debug=True)



