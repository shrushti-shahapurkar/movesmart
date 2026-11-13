from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3

import os
import csv
from sklearn.ensemble import RandomForestRegressor

from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "movesmart_secret_key_2026"

DATABASE = "database.db"
DATASET_FOLDER = "dataset"
DATASET_FILE = os.path.join(DATASET_FOLDER, "movesmart_data.csv")


# ---------------------------------------------------
# DATABASE
# ---------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_name TEXT NOT NULL,
            score REAL DEFAULT 0,
            accuracy REAL DEFAULT 0,
            reaction_time REAL DEFAULT 0,
            completion_time REAL DEFAULT 0,
            errors INTEGER DEFAULT 0,
            objects_caught INTEGER DEFAULT 0,
            objects_missed INTEGER DEFAULT 0,
            path_deviation REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

    # Create dataset folder
    os.makedirs(DATASET_FOLDER, exist_ok=True)

    # Create CSV header if file doesn't exist
    if not os.path.exists(DATASET_FILE):
        with open(DATASET_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "age",
                "game_name",
                "score",
                "accuracy",
                "reaction_time",
                "completion_time",
                "errors",
                "objects_caught",
                "objects_missed",
                "path_deviation"
            ])


# ---------------------------------------------------
# LOGIN REQUIRED DECORATOR
# ---------------------------------------------------

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


# ---------------------------------------------------
# HOME
# ---------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")



# ---------------------------------------------------
# REGISTER - SECURE PASSWORD HASHING
# ---------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        age = request.form["age"]
        username = request.form["username"].strip()
        password = request.form["password"]

        if not name or not age or not username or not password:
            flash("Please fill all fields.")
            return redirect(url_for("register"))

        try:
            age = int(age)
        except ValueError:
            flash("Please enter a valid age.")
            return redirect(url_for("register"))

        if age < 5 or age > 10:
            flash("MoveSmart is designed for children aged 5–10.")
            return redirect(url_for("register"))

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO users (name, age, username, password)
                VALUES (?, ?, ?, ?)
            """, (name, age, username, hashed_password))

            conn.commit()

            flash("Registration successful! Please login.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username already exists.")

        finally:
            conn.close()

    return render_template("register.html")


# ---------------------------------------------------
# LOGIN - VERIFY HASHED AND EXISTING PASSWORDS
# ---------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()

        try:
            user = conn.execute("""
                SELECT * FROM users
                WHERE username = ?
            """, (username,)).fetchone()

            if user:
                stored_password = user["password"]
                password_valid = False

                # First, check a securely hashed password
                try:
                    password_valid = check_password_hash(
                        stored_password, password
                    )
                except (ValueError, TypeError):
                    password_valid = False

                # Support old plaintext passwords and upgrade them
                if not password_valid and stored_password == password:
                    password_valid = True

                    upgraded_password = generate_password_hash(password)

                    conn.execute("""
                        UPDATE users
                        SET password = ?
                        WHERE id = ?
                    """, (upgraded_password, user["id"]))

                    conn.commit()

                if password_valid:
                    session["user_id"] = user["id"]
                    session["user_name"] = user["name"]
                    session["user_age"] = user["age"]

                    return redirect(url_for("dashboard"))

            flash("Invalid username or password.")

        finally:
            conn.close()

    return render_template("login.html")



# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

    conn = get_db()

    results = conn.execute("""
        SELECT *
        FROM game_results
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        results=results
    )


# ---------------------------------------------------
# GAMES
# ---------------------------------------------------

@app.route("/game/target-tap")
@login_required
def target_tap():
    return render_template("target_tap.html")


@app.route("/game/catch-object")
@login_required
def catch_object():
    return render_template("catch_object.html")


@app.route("/game/sequence")
@login_required
def sequence_game():
    return render_template("sequence_game.html")


# ---------------------------------------------------
# SAVE GAME RESULT
# ---------------------------------------------------

@app.route("/save_game_result", methods=["POST"])
@login_required
def save_game_result():

    import math

    # 1. Receive JSON data from the game
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "No valid game data received."
        }), 400

    # 2. Validate the game name
    allowed_games = {
        "Target Tap",
        "Catch Object",
        "Sequence Game",
        "Maze Explorer",
        "Shape Matcher",
        "Balloon Pop",
        "Path Tracer"
    }

    game_name = str(data.get("game_name", "")).strip()

    if game_name not in allowed_games:
        return jsonify({
            "success": False,
            "message": "Invalid game name."
        }), 400

    # 3. Safely convert numeric values
    def get_number(field, default=0):
        try:
            value = float(data.get(field, default))

            if not math.isfinite(value):
                raise ValueError

            return value

        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid numeric value for {field}."
            )

    try:
        score = get_number("score")
        accuracy = get_number("accuracy")
        reaction_time = get_number("reaction_time")
        completion_time = get_number("completion_time")
        errors = get_number("errors")
        objects_caught = get_number("objects_caught")
        objects_missed = get_number("objects_missed")
        path_deviation = get_number("path_deviation")

        # 4. Validate score and accuracy
        if not 0 <= score <= 100:
            raise ValueError(
                "Score must be between 0 and 100."
            )

        if not 0 <= accuracy <= 100:
            raise ValueError(
                "Accuracy must be between 0 and 100."
            )

        # 5. Prevent negative values
        if min(
            reaction_time,
            completion_time,
            errors,
            objects_caught,
            objects_missed,
            path_deviation
        ) < 0:
            raise ValueError(
                "Times, counts, and path deviation cannot be negative."
            )

        # 6. Counts must be whole numbers
        if any(
            value != int(value)
            for value in (
                errors,
                objects_caught,
                objects_missed
            )
        ):
            raise ValueError(
                "Errors and object counts must be whole numbers."
            )

        errors = int(errors)
        objects_caught = int(objects_caught)
        objects_missed = int(objects_missed)

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400

    # 7. Get the logged-in user
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify({
            "success": False,
            "message": "Please log in again."
        }), 401

    # 8. Save the result in SQLite
    conn = get_db()

    try:
        user = conn.execute(
            """
            SELECT id, age
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if user is None:
            return jsonify({
                "success": False,
                "message": "User account not found."
            }), 404

        conn.execute(
            """
            INSERT INTO game_results (
                user_id,
                game_name,
                score,
                accuracy,
                reaction_time,
                completion_time,
                errors,
                objects_caught,
                objects_missed,
                path_deviation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                game_name,
                score,
                accuracy,
                reaction_time,
                completion_time,
                errors,
                objects_caught,
                objects_missed,
                path_deviation
            )
        )

        conn.commit()

    except Exception:
        conn.rollback()

        app.logger.exception(
            "Error saving MoveSmart game result."
        )

        return jsonify({
            "success": False,
            "message": "Could not save the game result."
        }), 500

    finally:
        conn.close()

    # IMPORTANT:
    # Do not append individual gameplay results to the CSV.
    # Keep dataset/movesmart_data.csv separate from SQLite.

    return jsonify({
        "success": True,
        "message": "Game result saved successfully.",
        "game_name": game_name,
        "score": score,
        "accuracy": accuracy
    }), 200



# ---------------------------------------------------
# RESULT PAGE
# ---------------------------------------------------

@app.route("/result")
@login_required
def result():

    user_id = session["user_id"]

    conn = get_db()

    results = conn.execute("""
        SELECT *
        FROM game_results
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 3
    """, (user_id,)).fetchall()

    conn.close()

    if len(results) == 0:
        return render_template(
            "result.html",
            results=[],
            overall_score=0,
            performance="No Data"
        )

    total_score = sum(row["score"] for row in results)
    overall_score = round(total_score / len(results), 2)

    if overall_score >= 75:
        performance = "Typical Performance"
        performance_class = "good"

    elif overall_score >= 50:
        performance = "Moderate Performance"
        performance_class = "medium"

    else:
        performance = "Further Screening Recommended"
        performance_class = "attention"

    return render_template(
        "result.html",
        results=results,
        overall_score=overall_score,
        performance=performance,
        performance_class=performance_class
    )
@app.route("/game/maze-explorer")
@login_required
def maze_explorer():
    return render_template("maze_explorer.html")

@app.route("/game/shape-matcher")
@login_required
def shape_matcher():
    return render_template("shape_matcher.html")

@app.route("/game/balloon-pop")
@login_required
def balloon_pop():
    return render_template("balloon_pop.html")

@app.route("/game/path-tracer")
@login_required
def path_tracer():
    return render_template("path_tracer.html")


# ---------------- MACHINE LEARNING ----------------


@app.route("/ml-analysis")
@login_required
def ml_analysis():
    import csv
    import os

    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score

    # --------------------------------------------------
    # 1. DATASET PATH
    # --------------------------------------------------

    dataset_file = os.path.join(
        app.root_path,
        "dataset",
        "movesmart_data.csv"
    )

    records = []

    # --------------------------------------------------
    # 2. READ AND VALIDATE CSV DATA
    # --------------------------------------------------

    print("\n========== MOVESMART ML ANALYSIS ==========")
    print("Dataset path:", dataset_file)
    print("File exists:", os.path.isfile(dataset_file))

    if os.path.isfile(dataset_file):
        try:
            with open(
                dataset_file,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                print("CSV columns:", reader.fieldnames)

                if reader.fieldnames:
                    # Remove accidental spaces from column names.
                    reader.fieldnames = [
                        name.strip() if name else ""
                        for name in reader.fieldnames
                    ]

                required_columns = {
                    "age",
                    "game_name",
                    "score"
                }

                available_columns = set(
                    reader.fieldnames or []
                )

                if not required_columns.issubset(
                    available_columns
                ):
                    print(
                        "ERROR: Required CSV columns are missing."
                    )

                else:
                    for row in reader:
                        try:
                            # Normalize column names and values.
                            clean_row = {
                                key.strip(): (
                                    value.strip()
                                    if value is not None
                                    else ""
                                )
                                for key, value in row.items()
                                if key is not None
                            }

                            age = float(clean_row["age"])
                            score = float(clean_row["score"])
                            game_name = clean_row[
                                "game_name"
                            ].strip()

                            # Reject invalid and non-finite values.
                            import math

                            if not (
                                math.isfinite(age)
                                and math.isfinite(score)
                            ):
                                continue

                            if (
                                game_name
                                and age.is_integer()
                                and 5 <= age <= 10
                                and 0 <= score <= 100
                            ):
                                records.append({
                                    "age": int(age),
                                    "game_name": game_name,
                                    "score": score
                                })

                        except (
                            ValueError,
                            KeyError,
                            TypeError
                        ):
                            continue

        except (OSError, csv.Error) as error:
            app.logger.exception(
                "Unable to read MoveSmart dataset: %s",
                error
            )

    print("Valid gameplay records:", len(records))
    print("==========================================\n")

    # --------------------------------------------------
    # 3. PREPARE PAGE VARIABLES
    # --------------------------------------------------

    games = sorted({
        record["game_name"]
        for record in records
    })

    sample_count = len(records)

    selected_game = request.args.get(
        "game_name",
        ""
    ).strip()

    if selected_game not in games and games:
        selected_game = games[0]

    prediction = None
    mae = None
    r2 = None
    evaluation_count = 0
    message = None
    evaluation_message = None

    # --------------------------------------------------
    # 4. CHECK DATA AVAILABILITY
    # --------------------------------------------------

    if sample_count == 0:

        message = (
            "No valid gameplay records were found. "
            "Check the dataset path and CSV column names."
        )

        evaluation_message = (
            "Model evaluation is unavailable because "
            "the dataset contains no valid records."
        )

    elif sample_count < 10:

        message = (
            "At least 10 valid records are required for "
            "this experimental prediction demonstration. "
            "More varied records are recommended."
        )

        evaluation_message = (
            "More gameplay data is needed before "
            "evaluating the model."
        )

    else:

        # --------------------------------------------------
        # 5. ENCODE GAME NAMES
        # --------------------------------------------------

        X = []
        y = []

        for record in records:

            features = [
                record["age"]
            ]

            # One-hot encoding for game names.
            for game in games:
                features.append(
                    1 if record["game_name"] == game else 0
                )

            X.append(features)
            y.append(record["score"])

        # --------------------------------------------------
        # 6. TRAIN RANDOM FOREST MODEL
        # --------------------------------------------------

        model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            min_samples_leaf=1
        )

        model.fit(X, y)

        # --------------------------------------------------
        # 7. PREDICT GAMEPLAY SCORE
        # --------------------------------------------------

        if selected_game in games:

            try:
                child_age = float(
                    session.get("user_age", 8)
                )

                if (
                    math.isfinite(child_age)
                    and child_age.is_integer()
                    and 5 <= child_age <= 10
                ):

                    test_features = [
                        int(child_age)
                    ]

                    for game in games:
                        test_features.append(
                            1 if game == selected_game else 0
                        )

                    predicted_score = float(
                        model.predict(
                            [test_features]
                        )[0]
                    )

                    prediction = round(
                        max(
                            0,
                            min(100, predicted_score)
                        ),
                        2
                    )

                    message = (
                        "Experimental gameplay-score estimate "
                        "generated successfully. This is not "
                        "a health prediction."
                    )

                else:
                    message = (
                        "A valid age between 5 and 10 is "
                        "required for the demonstration."
                    )

            except (TypeError, ValueError) as error:
                app.logger.warning(
                    "Prediction could not be generated: %s",
                    error
                )

                message = (
                    "Unable to generate a prediction. "
                    "Please check the child profile."
                )

        # --------------------------------------------------
        # 8. EVALUATE USING HELD-OUT RECORDS
        # --------------------------------------------------

        if sample_count >= 20:

            X_train, X_test, y_train, y_test = (
                train_test_split(
                    X,
                    y,
                    test_size=0.25,
                    random_state=42
                )
            )

            evaluation_model = RandomForestRegressor(
                n_estimators=100,
                random_state=42
            )

            evaluation_model.fit(
                X_train,
                y_train
            )

            y_pred = evaluation_model.predict(
                X_test
            )

            mae = round(
                float(
                    mean_absolute_error(
                        y_test,
                        y_pred
                    )
                ),
                2
            )

            evaluation_count = len(y_test)

            # R² requires at least two test records.
            if len(y_test) >= 2:
                r2 = round(
                    float(
                        r2_score(
                            y_test,
                            y_pred
                        )
                    ),
                    3
                )

            evaluation_message = (
                "Evaluation uses held-out gameplay records. "
                "The results are experimental and may be "
                "unreliable with a small dataset."
            )

        else:

            evaluation_message = (
                "A held-out evaluation requires at least "
                "20 valid records in this demonstration. "
                "Collect more varied data before interpreting "
                "model performance."
            )

    # --------------------------------------------------
    # 9. DISPLAY ML ANALYSIS PAGE
    # --------------------------------------------------

    return render_template(
        "ml_analysis.html",
        games=games,
        selected_game=selected_game,
        prediction=prediction,
        sample_count=sample_count,
        message=message,
        mae=mae,
        r2=r2,
        evaluation_count=evaluation_count,
        evaluation_message=evaluation_message
    )


from datetime import datetime

@app.route("/full-report")
@login_required
def full_report():
    user_id = session["user_id"]

    conn = get_db()

    try:
        user = conn.execute("""
            SELECT id, name, age
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        results = conn.execute("""
            SELECT game_name, score, accuracy, reaction_time,
                   completion_time, errors, objects_caught,
                   objects_missed, path_deviation, created_at
            FROM game_results
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()

    finally:
        conn.close()

    if not user:
        session.clear()
        flash("Please log in again.")
        return redirect(url_for("login"))

    # Convert SQLite rows into template-friendly dictionaries
    game_results = [dict(row) for row in results]

    total_games = len(game_results)

    def average(field):
        values = []
        for result in game_results:
            try:
                value = float(result[field])
                if value >= 0:
                    values.append(value)
            except (TypeError, ValueError, KeyError):
                pass

        return round(sum(values) / len(values), 2) if values else None

    total_errors = sum(
        max(0, int(r.get("errors") or 0))
        for r in game_results
    )

    # Descriptive gameplay summary, not a health diagnosis
    avg_score = average("score")
    avg_accuracy = average("accuracy")

    if total_games == 0:
        summary = (
            "No gameplay results are saved yet. "
            "Complete a game to begin your report."
        )
    else:
        summary = (
            "This report summarizes recorded gameplay performance. "
            "Scores can vary by game and are not a medical assessment."
        )

    expected_games = [
        "Target Tap",
        "Catch Object",
        "Sequence Game",
        "Maze Explorer",
        "Shape Matcher",
        "Balloon Pop",
        "Path Tracer"
    ]

    completed_games = {
        r["game_name"] for r in game_results
    }

    missing_games = [
        game for game in expected_games
        if game not in completed_games
    ]
    
    # Experimental ML estimates for the complete report
    ml_predictions = []
    ml_report_message = (
        "No estimates available. Add valid records to the dataset."
    )

    dataset_path = os.path.join(
        app.root_path, "dataset", "movesmart_data.csv"
    )

    try:
        with open(
            dataset_path, "r", encoding="utf-8-sig", newline=""
        ) as csvfile:
            reader = csv.DictReader(csvfile)

            records = []
            for row in reader:
                try:
                    age_value = int(row["age"])
                    score_value = float(row["score"])
                    game_value = row["game_name"].strip()

                    if (
                        5 <= age_value <= 10
                        and 0 <= score_value <= 100
                        and game_value
                    ):
                        records.append({
                            "age": age_value,
                            "score": score_value,
                            "game_name": game_value
                        })
                except (KeyError, TypeError, ValueError):
                    continue

        game_names = sorted({
            row["game_name"] for row in records
        })

        if len(records) >= 3 and game_names:
            # One-hot encode game names
            def make_features(age_value, game_value):
                return [
                    age_value
                ] + [
                    1 if game_value == name else 0
                    for name in game_names
                ]

            X = [
                make_features(row["age"], row["game_name"])
                for row in records
            ]
            y = [row["score"] for row in records]

            model = RandomForestRegressor(
                n_estimators=100,
                random_state=42
            )
            model.fit(X, y)

            child_age = int(user["age"])

            for game in expected_games:
                if game in game_names:
                    estimate = float(
                        model.predict([
                            make_features(child_age, game)
                        ])[0]
                    )

                    ml_predictions.append({
                        "game": game,
                        "score": round(
                            max(0, min(100, estimate)), 2
                        )
                    })

            ml_report_message = (
                "Experimental score estimates generated from the "
                "available CSV records. These are not health predictions."
            )

    except (OSError, csv.Error, ValueError) as error:
        app.logger.warning("ML report data unavailable: %s", error)


   
    return render_template(
        "full_report.html",
        child=dict(user),
        results=game_results,
        total_games=total_games,
        avg_score=avg_score,
        avg_accuracy=avg_accuracy,
        avg_reaction_time=average("reaction_time"),
        avg_completion_time=average("completion_time"),
        total_errors=total_errors,
        summary=summary,
        missing_games=missing_games,
        ml_predictions=ml_predictions,
        ml_report_message=ml_report_message,
        report_date=datetime.now().strftime("%d %B %Y")
    )




@app.route("/age-comparison")
@login_required
def age_comparison():
    import csv
    import os
    from collections import defaultdict

    user_id = session.get("user_id")

    # 1. Get the logged-in child's information
    conn = get_db()

    try:
        user = conn.execute(
            """
            SELECT id, name, age
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if user is None:
            return "User not found.", 404

        child_age = int(user["age"])

        # 2. Fetch only this child's saved gameplay results
        child_results = conn.execute(
            """
            SELECT game_name, score
            FROM game_results
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,)
        ).fetchall()

    finally:
        conn.close()

    # 3. Calculate this child's average for each game
    child_groups = defaultdict(list)

    for result in child_results:
        try:
            game_name = str(result["game_name"]).strip()
            score = float(result["score"])

            if game_name and 0 <= score <= 100:
                child_groups[game_name].append(score)

        except (ValueError, TypeError):
            continue

    # 4. Read reference scores from the CSV.
    # Do NOT append new child gameplay results to this file.
    dataset_file = os.path.join(
        app.root_path,
        "dataset",
        "movesmart_data.csv"
    )

    reference_groups = defaultdict(list)
    dataset_message = None

    if not os.path.isfile(dataset_file):
        dataset_message = (
            "Reference dataset not found. "
            "Please check dataset/movesmart_data.csv."
        )

    else:
        try:
            with open(
                dataset_file,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                required_columns = {
                    "age",
                    "game_name",
                    "score"
                }

                if not reader.fieldnames or not required_columns.issubset(
                    set(reader.fieldnames)
                ):
                    dataset_message = (
                        "The CSV is missing required columns: "
                        "age, game_name, score."
                    )

                else:
                    for row in reader:
                        try:
                            age = int(float(row["age"]))
                            game_name = str(
                                row["game_name"]
                            ).strip()
                            score = float(row["score"])

                            if (
                                age == child_age
                                and game_name
                                and 0 <= score <= 100
                            ):
                                reference_groups[game_name].append(
                                    score
                                )

                        except (ValueError, TypeError, KeyError):
                            continue

        except (OSError, csv.Error):
            dataset_message = (
                "Unable to read the reference dataset."
            )

    # 5. Compare the two independently calculated averages
    comparisons = []

    for game_name, child_scores in sorted(child_groups.items()):

        child_average = sum(child_scores) / len(child_scores)

        reference_scores = reference_groups.get(game_name, [])

        if reference_scores:
            reference_average = (
                sum(reference_scores) / len(reference_scores)
            )

            difference = child_average - reference_average

            # Use a small tolerance for floating-point calculations
            if difference > 0.01:
                comparison_label = "Above dataset average"

            elif difference < -0.01:
                comparison_label = "Below dataset average"

            else:
                comparison_label = "Equal to dataset average"

            comparisons.append({
                "game_name": game_name,
                "child_average": round(child_average, 2),
                "reference_average": round(reference_average, 2),
                "difference": round(difference, 2),
                "sessions": len(child_scores),
                "reference_count": len(reference_scores),
                "comparison_label": comparison_label
            })

        else:
            comparisons.append({
                "game_name": game_name,
                "child_average": round(child_average, 2),
                "reference_average": None,
                "difference": None,
                "sessions": len(child_scores),
                "reference_count": 0,
                "comparison_label": "Reference data unavailable"
            })

    # 6. Display the comparison page
    return render_template(
        "age_comparison.html",
        child_name=user["name"],
        child_age=child_age,
        comparisons=comparisons,
        dataset_message=dataset_message
    )


# ---------------------------------------------------
# START APPLICATION
# ---------------------------------------------------

if __name__ == "__main__":

    init_database()

    app.run(debug=True)