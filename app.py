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
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_history(password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO history (password) VALUES (?)', (password,))
    conn.commit()
    conn.close()

# 連続する文字や数字をチェックする
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

def generate_password(length, use_uppercase, use_lowercase, use_numbers):
    # 使用する文字を決定
    allowed_chars = ''
    if use_uppercase:
        allowed_chars += string.ascii_uppercase
    if use_lowercase:
        allowed_chars += string.ascii_lowercase
    if use_numbers:
        allowed_chars += string.digits
    
    while True:
        password = ''.join(random.choices(allowed_chars, k=length))

        # 連続する文字や数字、2桁同じ文字を禁止
        if has_consecutive_sequence(password) or has_same_digit_repeat(password):
            continue
        
        return password

@app.route("/", methods=["GET", "POST"])
def index():
    passwords = []
    if request.method == "POST":
        length = int(request.form.get("length", 10))
        use_uppercase = "uppercase" in request.form
        use_lowercase = "lowercase" in request.form
        use_numbers = "numbers" in request.form

        # パスワード生成
        for _ in range(10):  # 10個生成（数は自由に変更可能）
            pw = generate_password(length, use_uppercase, use_lowercase, use_numbers)
            passwords.append(pw)
            save_history(pw)
    
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

    # JST変換
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
    return send_file(stream, as_attachment=True, download_name="passwords.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
