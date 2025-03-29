
from flask import Flask, render_template, send_file, request
import io
from openpyxl import Workbook
import random
import string
import os
import sqlite3
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
DB_NAME = "history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_history(password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO history (password) VALUES (?)', (password,))
    conn.commit()
    conn.close()

def generate_password(digit_length=5):
    custom_alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"

    def has_consecutive_sequence(s):
        for i in range(len(s) - 2):
            if int(s[i+1]) == int(s[i]) + 1 and int(s[i+2]) == int(s[i+1]) + 1:
                return True
        return False

    def has_same_digit_repeat(s):
        for i in range(len(s) - 1):
            if s[i] == s[i+1]:
                return True
        return False

    def has_repeated_characters(s):
        for i in range(len(s) - 1):
            if s[i] == s[i + 1]:
                return True
        return False

    def generate_non_consecutive_digits(length):
        digits = string.digits
        while True:
            result = ''.join(random.choices(digits, k=length))
            if not has_consecutive_sequence(result) and not has_same_digit_repeat(result):
                return result

    while True:
        first_char = random.choice(custom_alphabet[:24])
        next_two_chars = ''.join(random.choices(custom_alphabet[24:], k=2))
        first_three = first_char + next_two_chars
        if has_repeated_characters(first_three):
            continue
        last_digits = generate_non_consecutive_digits(digit_length)
        return first_three + '-' + last_digits

@app.route("/", methods=["GET", "POST"])
def index():
    passwords = []
    if request.method == "POST":
        count = int(request.form.get("count", 10))
        digit_length = int(request.form.get("digit_length", 5))
        last_two = None
        for _ in range(count):
            while True:
                pw = generate_password(digit_length=digit_length)
                pw_last_two = pw[-2:]
                if pw_last_two != last_two:
                    passwords.append(pw)
                    save_history(pw)
                    last_two = pw_last_two
                    break
    return render_template("index.html", passwords=passwords)

@app.route("/history")
def history():
    page = int(request.args.get('page', 1))
    per_page = 500
    offset = (page - 1) * per_page

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT password, created_at FROM history ORDER BY id DESC LIMIT ? OFFSET ?', (per_page, offset))
    rows = c.fetchall()
    conn.close()

    jst = timezone(timedelta(hours=9))
    converted = []
    for pw, created_at in rows:
        utc_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        jst_time = utc_time.replace(tzinfo=timezone.utc).astimezone(jst)
        converted.append((pw, jst_time.strftime('%Y-%m-%d %H:%M:%S')))
    return render_template("history.html", logs=converted, current_page=page)

@app.route("/download", methods=["POST"])
def download():
    passwords = request.form.getlist("passwords")
    wb = Workbook()
    ws = wb.active
    for pw in passwords:
        ws.append([pw])
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return send_file(
        stream,
        as_attachment=True,
        download_name="passwords.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
