import sqlalchemy as sa
from marshmallow_sqlalchemy import ModelSchema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref

engine = sa.create_engine("sqlite:///:memory:")
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class Author(Base):
    __tablename__ = "authors"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)

    def __repr__(self):
        return "<Author(name={self.name!r})>".format(self=self)


class Book(Base):
    __tablename__ = "books"
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String)
    author_id = sa.Column(sa.Integer, sa.ForeignKey("authors.id"))
    author = relationship("Author", backref=backref("books"))


Base.metadata.create_all(engine)


class AuthorSchema(ModelSchema):
    class Meta:
        model = Author


class BookSchema(ModelSchema):
    class Meta:
        model = Book
        # optionally attach a Session
        # to use for deserialization
        sqla_session = session

author = Author(name="Chuck Paluhniuk")
author_schema = AuthorSchema()
book = Book(title="Fight Club", author=author)
session.add(author)
session.add(book)
session.commit()

dump_data = author_schema.dump(author)
print(dump_data)
print(dump_data)

load_data = author_schema.load(dump_data, session=session)
print(load_data)

