from flask import Flask, render_template, send_file, request
import io
from openpyxl import Workbook
import random
import string
import os

app = Flask(__name__)

def generate_password():
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

    custom_alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"
    while True:
        first_char = random.choice(custom_alphabet[:24])
        next_two_chars = ''.join(random.choices(custom_alphabet[24:], k=2))
        first_three = first_char + next_two_chars
        if has_repeated_characters(first_three):
            continue
        last_digits = generate_non_consecutive_digits(4)
        return first_three + '-' + last_digits

@app.route("/", methods=["GET", "POST"])
def index():
    passwords = []
    if request.method == "POST":
        count = int(request.form.get("count", 10))
        last_two = None
        for _ in range(count):
            while True:
                pw = generate_password()
                pw_last_two = pw[-2:]
                if pw_last_two != last_two:
                    passwords.append(pw)
                    last_two = pw_last_two
                    break
    return render_template("index.html", passwords=passwords)

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)