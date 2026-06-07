import os
import sqlite3
from functools import wraps
from datetime import datetime

import requests
from flask import Flask, jsonify, redirect, render_template, request, session, url_for, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "koci_tinder.db")
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-zmien-mnie")
    app.config["CAT_API_KEY"] = os.environ.get("CAT_API_KEY", "")

    @app.before_request
    def before_request():
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row

    @app.teardown_request
    def teardown_request(exception=None):
        db = getattr(g, "db", None)
        if db is not None:
            db.close()

    def login_required(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if "user_id" not in session:
                flash("Najpierw zaloguj się na konto.", "error")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped_view

    def current_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        return g.db.execute("SELECT id, username, created_at FROM users WHERE id = ?", (user_id,)).fetchone()

    def fetch_random_cat():
        headers = {}
        if app.config["CAT_API_KEY"]:
            headers["x-api-key"] = app.config["CAT_API_KEY"]

        params = {
            "size": "med",
            "mime_types": "jpg,png,gif",
            "format": "json",
            "order": "RANDOM",
            "limit": 1,
        }
        response = requests.get(CAT_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        cats = response.json()
        if not cats:
            raise ValueError("CAT API nie zwróciło zdjęcia.")
        cat = cats[0]
        return {
            "cat_id": cat.get("id"),
            "url": cat.get("url"),
            "width": cat.get("width"),
            "height": cat.get("height"),
        }

    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("swipe"))
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or not password:
                flash("Podaj nazwę użytkownika i hasło.", "error")
                return render_template("register.html", username=username)
            existing = g.db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing:
                flash("Taki użytkownik już istnieje.", "error")
                return render_template("register.html", username=username)
            g.db.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), datetime.utcnow().isoformat(timespec="seconds")),
            )
            g.db.commit()
            flash("Konto utworzone. Możesz się zalogować.", "success")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = g.db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user is None or not check_password_hash(user["password_hash"], password):
                flash("Niepoprawny login lub hasło.", "error")
                return render_template("login.html", username=username)
            session.clear()
            session["user_id"] = user["id"]
            flash("Zalogowano.", "success")
            return redirect(url_for("swipe"))
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        flash("Wylogowano.", "success")
        return redirect(url_for("index"))

    @app.route("/account")
    @login_required
    def account():
        user = current_user()
        stats = g.db.execute(
            """
            SELECT
                SUM(CASE WHEN direction = 'right' THEN 1 ELSE 0 END) AS likes,
                SUM(CASE WHEN direction = 'left' THEN 1 ELSE 0 END) AS dislikes,
                COUNT(*) AS total
            FROM swipes WHERE user_id = ?
            """,
            (user["id"],),
        ).fetchone()
        return render_template("account.html", user=user, stats=stats)

    @app.route("/account/delete", methods=["POST"])
    @login_required
    def delete_account():
        user_id = session["user_id"]
        g.db.execute("DELETE FROM swipes WHERE user_id = ?", (user_id,))
        g.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        g.db.commit()
        session.clear()
        flash("Konto i wszystkie dane zostały usunięte.", "success")
        return redirect(url_for("index"))

    @app.route("/swipe")
    @login_required
    def swipe():
        return render_template("swipe.html")

    @app.route("/history")
    @login_required
    def history():
        rows = g.db.execute(
            "SELECT * FROM swipes WHERE user_id = ? ORDER BY id DESC LIMIT 50",
            (session["user_id"],),
        ).fetchall()
        return render_template("history.html", swipes=rows)

    # ---------------- WŁASNE API APLIKACJI ----------------
    @app.route("/api/cat/random")
    @login_required
    def api_random_cat():
        try:
            return jsonify(fetch_random_cat())
        except Exception as exc:
            return jsonify({"error": "Nie udało się pobrać kota", "details": str(exc)}), 502

    @app.route("/api/swipes", methods=["POST"])
    @login_required
    def api_create_swipe():
        data = request.get_json(silent=True) or {}
        cat_id = data.get("cat_id")
        cat_url = data.get("cat_url")
        direction = data.get("direction")
        if direction not in ("left", "right"):
            return jsonify({"error": "direction musi mieć wartość left albo right"}), 400
        if not cat_id or not cat_url:
            return jsonify({"error": "Brakuje cat_id albo cat_url"}), 400
        g.db.execute(
            "INSERT INTO swipes (user_id, cat_id, cat_url, direction, created_at) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], cat_id, cat_url, direction, datetime.utcnow().isoformat(timespec="seconds")),
        )
        g.db.commit()
        return jsonify({"ok": True, "direction": direction})

    @app.route("/api/swipes")
    @login_required
    def api_list_swipes():
        rows = g.db.execute(
            "SELECT id, cat_id, cat_url, direction, created_at FROM swipes WHERE user_id = ? ORDER BY id DESC",
            (session["user_id"],),
        ).fetchall()
        return jsonify([dict(row) for row in rows])

    @app.route("/api/account", methods=["DELETE"])
    @login_required
    def api_delete_account():
        user_id = session["user_id"]
        g.db.execute("DELETE FROM swipes WHERE user_id = ?", (user_id,))
        g.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        g.db.commit()
        session.clear()
        return jsonify({"ok": True})

    return app


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS swipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cat_id TEXT NOT NULL,
                cat_url TEXT NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('left', 'right')),
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        db.commit()


app = create_app()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
