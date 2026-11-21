
from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

DATABASE = "database.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_table():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_date TEXT NOT NULL,
            meal TEXT NOT NULL,
            food TEXT NOT NULL,
            created_at TEXT NOT NULL,
            confirmations INTEGER DEFAULT 0,
            reports INTEGER DEFAULT 0
        )
    """)

    # Add new columns to an existing database if needed
    columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(menus)"
        ).fetchall()
    ]

    if "confirmations" not in columns:
        connection.execute(
            "ALTER TABLE menus ADD COLUMN confirmations INTEGER DEFAULT 0"
        )

    if "reports" not in columns:
        connection.execute(
            "ALTER TABLE menus ADD COLUMN reports INTEGER DEFAULT 0"
        )

    connection.commit()
    connection.close()


def today():
    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date().isoformat()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/menu/today")
def get_today_menu():
    connection = get_db()

    rows = connection.execute(
        """SELECT id, meal, food, confirmations, reports
           FROM menus
           WHERE menu_date = ?
           ORDER BY id""",
        (today(),)
    ).fetchall()

    connection.close()

    menus = {
        "breakfast": [],
        "lunch": [],
        "snacks": [],
        "dinner": []
    }

    for row in rows:
        menus[row["meal"]].append({
            "id": row["id"],
            "food": row["food"],
            "confirmations": row["confirmations"],
            "reports": row["reports"]
        })

    return jsonify({"menus": menus})


@app.route("/api/menu", methods=["POST"])
def submit_menu():
    data = request.get_json(silent=True) or {}

    meal = data.get("meal", "")
    food = data.get("food", "")

    if not isinstance(meal, str) or not isinstance(food, str):
        return jsonify({"error": "Invalid menu details."}), 400

    food = food.strip()

    allowed_meals = ["breakfast", "lunch", "snacks", "dinner"]

    if meal not in allowed_meals:
        return jsonify({"error": "Select a valid meal."}), 400

    if not food or len(food) > 500:
        return jsonify({"error": "Enter food details within 500 characters."}), 400

    connection = get_db()

    connection.execute(
        """INSERT INTO menus
        (menu_date, meal, food, created_at)
        VALUES (?, ?, ?, ?)""",
        (
            today(),
            meal,
            food,
            datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
        )
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Menu submitted successfully!"})


@app.route("/api/menu/<int:menu_id>/confirm", methods=["POST"])
def confirm_menu(menu_id):
    connection = get_db()

    cursor = connection.execute(
        """UPDATE menus
           SET confirmations = confirmations + 1
           WHERE id = ? AND menu_date = ?""",
        (menu_id, today())
    )

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Menu entry not found."}), 404

    return jsonify({"message": "Menu confirmed!"})


@app.route("/api/menu/<int:menu_id>/report", methods=["POST"])
def report_menu(menu_id):
    connection = get_db()

    cursor = connection.execute(
        """UPDATE menus
           SET reports = reports + 1
           WHERE id = ? AND menu_date = ?""",
        (menu_id, today())
    )

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Menu entry not found."}), 404

    return jsonify({"message": "Menu reported!"})


@app.route("/api/menu/<int:menu_id>/suggest-correction", methods=["POST"])
def suggest_correction(menu_id):
    data = request.get_json(silent=True) or {}
    suggestion = data.get("suggestion", "")

    if not isinstance(suggestion, str):
        return jsonify({"error": "Invalid suggestion."}), 400

    suggestion = suggestion.strip()

    if not suggestion or len(suggestion) > 500:
        return jsonify({
            "error": "Enter a suggestion within 500 characters."
        }), 400

    connection = get_db()

    menu = connection.execute(
        "SELECT id FROM menus WHERE id = ? AND menu_date = ?",
        (menu_id, today())
    ).fetchone()

    if menu is None:
        connection.close()
        return jsonify({"error": "Menu entry not found."}), 404

    connection.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_id INTEGER NOT NULL,
            suggestion TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute(
        """INSERT INTO corrections
        (menu_id, suggestion, created_at)
        VALUES (?, ?, ?)""",
        (
            menu_id,
            suggestion,
            datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
        )
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Correction suggestion submitted!"
    })



@app.route("/corrections")
def view_corrections():
    connection = get_db()

    corrections = connection.execute("""
        SELECT
            corrections.id,
            menus.meal,
            menus.food,
            corrections.suggestion,
            corrections.created_at
        FROM corrections
        JOIN menus ON corrections.menu_id = menus.id
        ORDER BY corrections.id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "corrections.html",
        corrections=corrections
    )


if __name__ == "__main__":
    create_table()
    app.run(debug=False)
