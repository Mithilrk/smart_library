from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for sessions

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mysql",  # ✅ Use your actual MySQL password
        database="smart_library"
    )

# -------------------- LOGIN --------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (uname, pwd))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            session['admin'] = uname
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))

# -------------------- INDEX --------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    books = []
    keyword = ''
    if request.method == 'POST':
        keyword = request.form['search']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM books WHERE title LIKE %s OR author LIKE %s"
        cursor.execute(query, ('%' + keyword + '%', '%' + keyword + '%'))
        books = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('index.html', books=books, keyword=keyword)

# -------------------- ADD BOOK --------------------
@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if 'admin' not in session:
        return redirect(url_for('login'))

    message = None
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        rack_location = request.form['rack_location']
        available_copies = request.form['available_copies']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO books (title, author, rack_location, available_copies) VALUES (%s, %s, %s, %s)",
                           (title, author, rack_location, available_copies))
            conn.commit()
            message = "✅ Book added successfully!"
        except mysql.connector.Error as err:
            message = f"❌ Error: {err}"
        finally:
            cursor.close()
            conn.close()

    return render_template('add_book.html', message=message)

# -------------------- EDIT BOOK --------------------
@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        rack_location = request.form['rack_location']
        available_copies = request.form['available_copies']

        cursor.execute("UPDATE books SET title=%s, author=%s, rack_location=%s, available_copies=%s WHERE id=%s",
                       (title, author, rack_location, available_copies, book_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("✅ Book updated successfully!", "success")
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    cursor.close()
    conn.close()
    if book:
        return render_template('edit_book.html', book=book)
    else:
        flash("❌ Book not found!", "danger")
        return redirect(url_for('index'))

# -------------------- DELETE BOOK --------------------
@app.route('/delete/<int:book_id>', methods=['GET'])
def delete_book(book_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("🗑️ Book deleted successfully!", "warning")
    return redirect(url_for('index'))

# -------------------- RUN APP --------------------
if __name__ == '__main__':
    app.run(debug=True)
