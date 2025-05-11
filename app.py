import sqlite3
import string
import random
import os
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = 'urls.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_id TEXT NOT NULL UNIQUE
            )
        ''')
        db.commit()

def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['url']
        db = get_db()
        cur = db.cursor()

        # Verifica se a URL já foi encurtada antes
        cur.execute("SELECT short_id FROM urls WHERE original_url = ?", (original_url,))
        existing = cur.fetchone()
        if existing:
            short_id = existing[0]
        else:
            short_id = generate_short_id()
            while True:
                cur.execute("SELECT 1 FROM urls WHERE short_id = ?", (short_id,))
                if not cur.fetchone():
                    break
                short_id = generate_short_id()
            cur.execute("INSERT INTO urls (original_url, short_id) VALUES (?, ?)", (original_url, short_id))
            db.commit()

        short_url = request.host_url + short_id
        return render_template('index.html', short_url=short_url)
    return render_template('index.html')

@app.route('/<short_id>')
def redirect_short_url(short_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT original_url FROM urls WHERE short_id = ?", (short_id,))
    result = cur.fetchone()
    if result:
        return redirect(result[0])
    return f'<h1>URL not found for: {short_id}</h1>', 404

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 443))  # 443 localmente, variável PORT na produção
    app.run(host='0.0.0.0', port=port)
