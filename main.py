from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    borrowed_books = db.relationship('Borrow', backref='user', cascade='all, delete-orphan')

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    books = db.relationship('Book', backref='author', cascade='all, delete-orphan')

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    borrows = db.relationship('Borrow', backref='book', cascade='all, delete-orphan')

class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# ==================== USER CRUD ====================

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email exists'}), 400
    
    user = User(name=data['name'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email}), 201

@app.route('/users')
def get_all_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'name': u.name, 'email': u.email} for u in users])

@app.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email})

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.json
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email})

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ==================== BOOK CRUD ====================

@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    Author.query.get_or_404(data['author_id'])  # Check author exists
    
    book = Book(title=data['title'], author_id=data['author_id'])
    db.session.add(book)
    db.session.commit()
    return jsonify({'id': book.id, 'title': book.title, 'author_id': book.author_id}), 201

@app.route('/books')
def get_all_books():
    books = Book.query.all()
    return jsonify([{'id': b.id, 'title': b.title, 'author': b.author.name} for b in books])

@app.route('/books/author/<int:author_id>')
def get_books_by_author(author_id):
    author = Author.query.get_or_404(author_id)
    return jsonify([{'id': b.id, 'title': b.title} for b in author.books])

@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ==================== AUTHOR CRUD ====================

@app.route('/authors', methods=['POST'])
def add_author():
    data = request.json
    author = Author(name=data['name'])
    db.session.add(author)
    db.session.commit()
    return jsonify({'id': author.id, 'name': author.name}), 201

@app.route('/authors')
def get_all_authors():
    authors = Author.query.all()
    return jsonify([{'id': a.id, 'name': a.name} for a in authors])

@app.route('/authors/<int:id>/books')
def get_author_books(id):
    author = Author.query.get_or_404(id)
    return jsonify({
        'author': author.name,
        'books': [{'id': b.id, 'title': b.title} for b in author.books]
    })

# ==================== BORROW CRUD ====================

@app.route('/borrows', methods=['POST'])
def borrow_book():
    data = request.json
    User.query.get_or_404(data['user_id'])
    Book.query.get_or_404(data['book_id'])
    
    borrow = Borrow(user_id=data['user_id'], book_id=data['book_id'])
    db.session.add(borrow)
    db.session.commit()
    return jsonify({'id': borrow.id, 'user_id': borrow.user_id, 'book_id': borrow.book_id}), 201

@app.route('/borrows/user/<int:user_id>')
def get_user_borrows(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify([{
        'book_id': b.book_id,
        'book_title': b.book.title,
        'borrow_date': b.borrow_date.isoformat()
    } for b in user.borrowed_books])

@app.route('/borrows/book/<int:book_id>')
def get_book_borrowers(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify([{
        'user_id': b.user_id,
        'user_name': b.user.name,
        'borrow_date': b.borrow_date.isoformat()
    } for b in book.borrows])

# ==================== INIT ====================

@app.route('/')
def index():
    return jsonify({'message': 'Library Management System API'})

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)