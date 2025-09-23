from flask import Blueprint, render_template, request, redirect, url_for, current_app
from src.server.extensions import db
from src.server.models.data_models import User, User_Languages, Sentences, Sessions

web_bp = Blueprint("ui", __name__)

# --- Login / Create User ---
@web_bp.route("/", methods=["GET", "POST"])
@web_bp.route("/index", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username")

        if action == "login":
            # User nach Username suchen
            user = User.query.filter_by(username=username).first()
            if user:
                return redirect(url_for("ui.dashboard", user_id=user.id))
            else:
                return "User nicht gefunden", 404

        elif action == "register":
            native_language = request.form.get("native_language")

            # neuen User anlegen
            user = User(username=username, native_language=native_language)
            db.session.add(user)
            db.session.commit()

            # Lernsprachen speichern
            for field in ["target_language_1", "target_language_2"]:
                lang = request.form.get(field)
                if lang:
                    db.session.add(User_Languages(user_id=user.id, language_code=lang))

            db.session.commit()
            return redirect(url_for("ui.dashboard", user_id=user.id))

    return render_template("index.html")


@web_bp.route("/login", methods=["POST"])
def login():
    """Login mit bestehendem Usernamen"""
    username = request.form.get("username")

    user = current_app.manager.get_user_by_username(username)
    if not user:
        # Falls der User nicht existiert → zurück zur Startseite mit Fehler
        return redirect(url_for("ui.index"))

    return redirect(url_for("ui.dashboard", user_id=user.id))


@web_bp.route("/create", methods=["POST"])
def create_user():
    """Neuen User erstellen"""
    username = request.form.get("username")
    native_language = request.form.get("native_language")

    user = current_app.manager.create_user(username, native_language)
    return redirect(url_for("ui.dashboard", user_id=user.id))


@web_bp.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("dashboard.html", user_id=user.id, username=user.username)


@web_bp.route("/add_sentence/<int:user_id>", methods=["GET", "POST"])
def add_sentence(user_id):
    user = User.query.get_or_404(user_id)
    target_languages = User_Languages.query.filter_by(user_id=user_id).all()

    if request.method == "POST":
        original_text = request.form["original_text"]

        sentence = Sentences(
            user_id=user.id,
            original_text=original_text,
            language_code=user.native_language
        )
        db.session.add(sentence)
        db.session.commit()

        # Create session with translations
        session_input = {}
        for lang in target_languages:
            translated_text = request.form.get(f"translation_{lang.language_code}")
            if translated_text:
                if 'translations' not in session_input:
                    session_input['translations'] = {}
                session_input['translations'][lang.language_code] = translated_text
        
        if session_input:
            manager.create_session(user_id, sentence.id, session_input)

        db.session.commit()
        return redirect(url_for("ui.dashboard", user_id=user.id))

    return render_template("get_sentences.html", user_id=user.id, target_languages=target_languages)


    return render_template('add_sentence.html', user_id=user_id)