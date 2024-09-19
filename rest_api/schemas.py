from marshmallow import validates, ValidationError, post_load
from flasgger import Schema, fields, ValidationError
from models import get_book_by_title, Book, Author


class AuthorSchema(Schema):
    author_id = fields.Int()
    first_name = fields.Str(required=True)
    middle_name = fields.Str()
    last_name = fields.Str(required=True)

    @validates('first_name')
    def validate_first_name(self, first_name):
        if not first_name:
            raise ValidationError("First name is required.")

    @validates('last_name')
    def validate_last_name(self, last_name):
        if not last_name:
            raise ValidationError("Last name is required.")


    @post_load
    def create_author(self, data, **kwargs):
        return Author(**data)


class BookSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    author = fields.Nested(AuthorSchema, required=True)

    @validates('title')
    def validate_title(self, title):
        if get_book_by_title(title) is not None:
            raise ValidationError(
                f"A book with this title {title} already exists.".format(title=title)
            )

    @post_load
    def create_book(self, data, **kwargs):
        return Book(**data)

class AuthorDetailSchema(AuthorSchema):
    books = fields.List(fields.Nested(BookSchema))


class BookDetailSchema(BookSchema):
    author = fields.Nested(AuthorSchema, required=True)
