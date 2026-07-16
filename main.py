from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, Session, select
from typing import List, Optional
from datetime import datetime

from database.session import engine, get_session
from models.book import Book, BookCreate, BookUpdate

# Create database tables
SQLModel.metadata.create_all(engine)

app = FastAPI(
    title="Bookstore Inventory API",
    description="A CRUD API for managing bookstore inventory",
    version="1.0.0"
)


# ==========================
# Home
# ==========================
@app.get("/")
def root():
    return {"message": "Welcome to the Bookstore Inventory API"}


# ==========================
# Create Book
# ==========================
@app.post("/books", response_model=Book, status_code=201)
def create_book(
    book: BookCreate,
    session: Session = Depends(get_session)
):
    existing = session.exec(
        select(Book).where(Book.isbn == book.isbn)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="ISBN already exists"
        )

    db_book = Book(**book.model_dump())

    session.add(db_book)
    session.commit()
    session.refresh(db_book)

    return db_book


# ==========================
# List Books
# ==========================
@app.get("/books", response_model=List[Book])
def list_books(
    skip: int = 0,
    limit: int = 10,
    available: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    session: Session = Depends(get_session)
):
    query = select(Book)

    if available is not None:
        query = query.where(Book.available == available)

    if min_price is not None:
        query = query.where(Book.price >= min_price)

    if max_price is not None:
        query = query.where(Book.price <= max_price)

    books = session.exec(
        query.offset(skip).limit(limit)
    ).all()

    return books


# ==========================
# Get Book by ID
# ==========================
@app.get("/books/{book_id}", response_model=Book)
def get_book(
    book_id: int,
    session: Session = Depends(get_session)
):
    book = session.get(Book, book_id)

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    return book


# ==========================
# Update Book
# ==========================
@app.patch("/books/{book_id}", response_model=Book)
def update_book(
    book_id: int,
    book_update: BookUpdate,
    session: Session = Depends(get_session)
):
    book = session.get(Book, book_id)

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    update_data = book_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(book, field, value)

    book.updated_at = datetime.utcnow()

    session.add(book)
    session.commit()
    session.refresh(book)

    return book


# ==========================
# Delete Book
# ==========================
@app.delete("/books/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    session: Session = Depends(get_session)
):
    book = session.get(Book, book_id)

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    session.delete(book)
    session.commit()

    return None


# ==========================
# Search Books
# ==========================
@app.get("/books/search", response_model=List[Book])
def search_books(
    q: str,
    session: Session = Depends(get_session)
):
    query = select(Book).where(
        (Book.title.contains(q)) |
        (Book.author.contains(q))
    )

    return session.exec(query).all()