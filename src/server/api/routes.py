from flask import Flask, jsonify, request, Blueprint, current_app, session, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flasgger import Swagger, swag_from
from datetime import datetime
from src.server.models.data_models import db
from src.server.data_manager import DataManager
from src.server.models.api import (
    UserCreateRequest, UserCreateResponse, UserResponse,
    SentenceCreateRequest, SentenceCreateResponse, SentenceResponse
)
from pydantic import ValidationError


# creating blueprint
api_bp = Blueprint('api', __name__)


# ------------------- LOGIN / CREATE USER -------------------
@api_bp.route("/", methods=["GET", "POST"])
def create_or_login_user():
    if request.method == "POST":
        username = request.form.get("username")
        native_language = request.form.get("native_language")
        target_languages = request.form.get("target_languages").split(",")  # z.B. "en,it,fr"

        # User erstellen oder abrufen
        user = current_app.manager.get_user_by_username(username)
        if not user:
            user = current_app.manager.create_user(username, native_language)
            for lang_code in target_languages:
                current_app.manager.add_target_language(user.id, lang_code.strip())

        # Session speichern
        session["user_id"] = user.id
        return redirect(url_for("ui.index"))

    user = None
    if "user_id" in session:
        user = current_app.manager.get_user_by_id(session["user_id"])
        # User Target Languages
        langs = current_app.manager.get_user_languages(user.id)
        user.target_languages = [l.language_code for l in langs]

    return render_template("index.html", user=user)


@api_bp.route('/get_all_users')
def index_users():
    """
    Get all users
    ---
    tags:
      - Users
    summary: List all users
    description: Returns a list of all user profiles.
    responses:
      200:
        description: A list of user objects
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              username:
                type: string
              native_language:
                type: string
              created_at:
                type: string
    """
    users = current_app.manager.get_users()
    return jsonify(users), 200



# ------------------- INDEX -------------------
@api_bp.route("/index")
def index():
    if "user_id" not in session:
        return redirect(url_for("api.create_or_login_user"))

    user = current_app.manager.get_user_by_id(session["user_id"])
    langs = current_app.manager.get_user_languages(user.id)
    user.target_languages = [l.language_code for l in langs]
    return render_template("index.html", user=user)

# ==================== USER MANAGEMENT ENDPOINTS ====================

@api_bp.route('/users/create', methods=['POST'])
def create_user():
    """
    Create a new user
    ---
    tags:
      - Users
    summary: Create a new user
    description: Creates a new user with username and native language
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              minLength: 3
              maxLength: 50
              example: "john_doe"
              description: "Unique username for the user"
            native_language:
              type: string
              minLength: 2
              maxLength: 5
              example: "de"
              description: "User's native language code (e.g., 'en', 'de', 'fr')"
          required:
            - username
            - native_language
          example:
            username: "john_doe"
            native_language: "de"
    responses:
      201:
        description: User created successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
              description: "Indicates if the operation was successful"
            message:
              type: string
              example: "User created successfully"
              description: "Success message"
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                  description: "Unique user ID"
                username:
                  type: string
                  example: "john_doe"
                  description: "User's username"
                native_language:
                  type: string
                  example: "de"
                  description: "User's native language code"
                created_at:
                  type: string
                  format: date-time
                  example: "2024-01-01T10:00:00"
                  description: "Timestamp when user was created"
          example:
            success: true
            message: "User created successfully"
            user:
              id: 1
              username: "john_doe"
              native_language: "de"
              created_at: "2024-01-01T10:00:00"
      400:
        description: Invalid input data or username already exists
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Username already exists"
            details:
              type: array
              items:
                type: object
              example: []
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Server error"
            details:
              type: string
              example: "Internal server error details"
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate input using Pydantic
        try:
            user_request = UserCreateRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Validation failed', 'details': e.errors()}), 400
        
        # Create user
        try:
            user = current_app.manager.create_user(
                username=user_request.username,
                native_language=user_request.native_language
            )
        except ValueError as e:
            # This handles the "Username already exists" error from DataManager
            return jsonify({'error': str(e)}), 400
        
        # Create response using Pydantic model
        user_response = UserResponse.model_validate(user)
        response = UserCreateResponse(
            success=True,
            message="User created successfully",
            user=user_response
        )
        
        return jsonify(response.model_dump()), 201
        
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500


@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get user details
    ---
    tags:
      - Users
    summary: Get user by ID
    description: Returns details of a specific user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user to retrieve
    responses:
      200:
        description: User details
        schema:
          type: object
          properties:
            id:
              type: integer
            username:
              type: string
            native_language:
              type: string
            created_at:
              type: string
      404:
        description: User not found
    """
    user = current_app.manager.get_user_by_id(user_id)
    if user:
        return jsonify({
            'id': user.id,
            'username': user.username,
            'native_language': user.native_language,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    else:
        return jsonify({'error': 'User not found'}), 404

@api_bp.route('/users/<int:user_id>/languages/<string:language_code>', methods=['POST'])
def add_user_language(user_id, language_code):
    """
    Add a target language to a user
    ---
    tags:
      - Users
    summary: Add target language
    description: Adds a target language to a user's profile.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
      - name: language_code
        in: path
        type: string
        required: true
        description: Language code to add (e.g., 'fr', 'es')
    responses:
      201:
        description: Language added successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            user_id:
              type: integer
            language_code:
              type: string
            created_at:
              type: string
      400:
        description: Invalid input or language already added
      404:
        description: User not found
    """
    try:
        lang = current_app.manager.add_target_language(user_id, language_code)
        return jsonify({
            'id': lang.id,
            'user_id': lang.user_id,
            'language_code': lang.language_code,
            'created_at': lang.created_at.isoformat() if lang.created_at else None
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500


@api_bp.route('/users/<int:user_id>/languages', methods=['GET'])
def get_user_languages(user_id):
    """
    Get user's target languages
    ---
    tags:
      - Users
    summary: Get user languages
    description: Returns all target languages for a user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
    responses:
      200:
        description: List of user's target languages
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              user_id:
                type: integer
              language_code:
                type: string
              created_at:
                type: string
      404:
        description: User not found
    """
    try:
        user_languages = current_app.manager.get_user_languages(user_id)
        languages_list = []
        for lang in user_languages:
            languages_list.append({
                'id': lang.id,
                'user_id': lang.user_id,
                'language_code': lang.language_code,
                'created_at': lang.created_at.isoformat() if lang.created_at else None
            })
        return jsonify(languages_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/users/<int:user_id>/languages/<string:language_code>', methods=['DELETE'])
def delete_user_language(user_id, language_code):
    """
    Remove a target language from a user
    ---
    tags:
      - Users
    summary: Remove target language
    description: Removes a target language from a user's profile.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
      - name: language_code
        in: path
        type: string
        required: true
        description: Language code to remove
    responses:
      200:
        description: Language removed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
      404:
        description: User or language not found
    """
    # This would require implementing a delete method in DataManager
    return jsonify({'error': 'Not implemented yet'}), 501


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user
    ---
    tags:
      - Users
    summary: Delete a user
    description: Deletes a user and all associated data (sentences, translations, progress).
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user to delete
    responses:
      200:
        description: User deleted successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
      404:
        description: User not found
    """
    success = current_app.manager.delete_user(user_id)
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'User not found'}), 404


# ==================== SENTENCES MANAGEMENT ENDPOINTS ====================

@api_bp.route("/add_sentence", methods=["GET", "POST"])
def add_sentence_page():
    if "user_id" not in session:
        return redirect(url_for("ui.create_or_login_user"))

    user = current_app.manager.get_user_by_id(session["user_id"])
    langs = current_app.manager.get_user_languages(user.id)
    user.target_languages = [l.language_code for l in langs]

    if request.method == "POST":
        original_text = request.form.get("original_text")
        sentence = current_app.manager.create_sentence(user.id, original_text, category="general")

        # Create initial session with translations if provided
        session_input = {}
        for lang_code in user.target_languages:
            translation_text = request.form.get(f"translation_{lang_code}")
            if translation_text:
                if 'translations' not in session_input:
                    session_input['translations'] = {}
                session_input['translations'][lang_code] = translation_text
        
        if session_input:
            current_app.manager.create_session(user.id, sentence.id, session_input)

        return redirect(url_for("ui.index"))

    return render_template("add_sentence.html", user=user)


@api_bp.route('/sentences/create', methods=['POST'])
def create_sentence():
    """
    Create a new sentence
    ---
    tags:
      - Sentences
    summary: Create a new sentence
    description: Creates a new sentence for a user with initial progress values (score=0, review_count=0, last_review=null, next_review=null, category can be null)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
              example: 1
              description: "ID of the user who owns this sentence"
            original_text:
              type: string
              minLength: 1
              maxLength: 200
              example: "Ich lerne Deutsch"
              description: "The original sentence text"
            category:
              type: string
              maxLength: 50
              example: "Lernen"
              description: "Optional category for organizing sentences (can be null)"
          required:
            - user_id
            - original_text
          example:
            user_id: 1
            original_text: "Ich lerne Deutsch"
            category: "Lernen"
    responses:
      201:
        description: Sentence created successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
              description: "Indicates if the operation was successful"
            message:
              type: string
              example: "Sentence created successfully"
              description: "Success message"
            sentence:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                  description: "Unique sentence ID"
                user_id:
                  type: integer
                  example: 1
                  description: "ID of the user who owns this sentence"
                original_text:
                  type: string
                  example: "Ich lerne Deutsch"
                  description: "The original sentence text"
                language_code:
                  type: string
                  example: "de"
                  description: "Language code from user's native language"
                category:
                  type: string
                  nullable: true
                  example: "Lernen"
                  description: "Category for organizing sentences (can be null)"
                score:
                  type: number
                  format: float
                  example: 0.0
                  description: "Current learning score (starts at 0.0)"
                last_review:
                  type: string
                  format: date-time
                  nullable: true
                  example: null
                  description: "When sentence was last reviewed (null initially)"
                next_review:
                  type: string
                  format: date-time
                  nullable: true
                  example: null
                  description: "When sentence should be reviewed next (null initially)"
                review_count:
                  type: integer
                  example: 0
                  description: "Number of times sentence has been reviewed (starts at 0)"
                created_at:
                  type: string
                  format: date-time
                  example: "2024-01-01T10:00:00"
                  description: "Timestamp when sentence was created"
          example:
            success: true
            message: "Sentence created successfully"
            sentence:
              id: 1
              user_id: 1
              original_text: "Ich lerne Deutsch"
              language_code: "de"
              category: "Lernen"
              score: 0.0
              last_review: null
              next_review: null
              review_count: 0
              created_at: "2024-01-01T10:00:00"
      400:
        description: Invalid input data
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Validation failed"
            details:
              type: array
              items:
                type: object
              example: [{"field": "original_text", "message": "Field required"}]
          example:
            error: "Validation failed"
            details: [{"field": "original_text", "message": "Field required"}]
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "User not found"
          example:
            error: "User not found"
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Server error"
            details:
              type: string
              example: "Internal server error details"
          example:
            error: "Server error"
            details: "Internal server error details"
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate input using Pydantic
        try:
            sentence_request = SentenceCreateRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Validation failed', 'details': e.errors()}), 400
        
        # Check if user exists
        user = current_app.manager.get_user_by_id(sentence_request.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Create sentence with default progress values
        sentence = current_app.manager.create_sentence(
            user_id=sentence_request.user_id,
            original_text=sentence_request.original_text,
            category=sentence_request.category
        )
        
        # Create response using Pydantic model
        sentence_response = SentenceResponse.model_validate(sentence)
        response = SentenceCreateResponse(
            success=True,
            message="Sentence created successfully",
            sentence=sentence_response
        )
        
        return jsonify(response.model_dump()), 201
        
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500


@api_bp.route('/sentences/<int:user_id>', methods=['GET'])
def get_sentences(user_id):
    """
    Get all sentences for a user
    ---
    tags:
      - Sentences
    summary: Get user sentences
    description: Returns all sentences for a specific user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
    responses:
      200:
        description: List of user's sentences
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              user_id:
                type: integer
              original_text:
                type: string
              language_code:
                type: string
              category:
                type: string
              created_at:
                type: string
      404:
        description: User not found
    """
    try:
        sentences = current_app.manager.get_sentences_for_user(user_id)
        sentences_list = []
        for sentence in sentences:
            sentences_list.append({
                'id': sentence.id,
                'user_id': sentence.user_id,
                'original_text': sentence.original_text,
                'language_code': sentence.language_code,
                'category': sentence.category,
                'score': sentence.score,
                'last_review': sentence.last_review.isoformat() if sentence.last_review else None,
                'next_review': sentence.next_review.isoformat() if sentence.next_review else None,
                'review_count': sentence.review_count,
                'created_at': sentence.created_at.isoformat() if sentence.created_at else None
            })
        return jsonify(sentences_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route("/get_sentence", methods=["GET", "POST"])
def get_sentence_page():
    if "user_id" not in session:
        return redirect(url_for("ui.create_or_login_user"))

    user_id = session["user_id"]
    due_sentences = current_app.manager.get_due_sentences(user_id)
    sentence = due_sentences[0] if due_sentences else None

    if request.method == "POST" and sentence:
        user_answers = {}
        # Get user answers from form - you'll need to adapt this based on your form structure
        user_answer = request.form.get("user_answer")
        
        # Create session to track this attempt
        session_input = {
            'user_answer': user_answer,
            'review_type': 'sentence_practice'
        }
        
        # Simple scoring for now
        score = 0.8  # Placeholder
        is_success = score >= 0.7
        
        current_app.manager.create_session(user_id, sentence.id, session_input, score)
        current_app.manager.update_sentence_progress(sentence.id, score, is_success)
        return redirect(url_for("ui.index"))

    return render_template("get_sentence.html", sentence=sentence)


@api_bp.route('/sentences/<int:sentence_id>', methods=['DELETE'])
def delete_sentence(sentence_id):
    """
    Delete a sentence
    ---
    tags:
      - Sentences
    summary: Delete a sentence
    description: Deletes a sentence and all its associated translations.
    parameters:
      - name: sentence_id
        in: path
        type: integer
        required: true
        description: ID of the sentence to delete
    responses:
      200:
        description: Sentence deleted successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
      404:
        description: Sentence not found
    """
    success = current_app.manager.delete_sentence(sentence_id)
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Sentence not found'}), 404


# ------------------- EDIT SENTENCES -------------------
@api_bp.route("/edit_sentences", methods=["GET"])
def edit_sentences_page():
    if "user_id" not in session:
        return redirect(url_for("ui.create_or_login_user"))

    user_id = session["user_id"]
    sentences = current_app.manager.get_sentences_for_user(user_id)
    return render_template("edit_sentences.html", sentences=sentences)


@api_bp.route("/edit_sentence/<int:sentence_id>", methods=["GET", "POST"])
def edit_sentence_page(sentence_id):
    if "user_id" not in session:
        return redirect(url_for("ui.create_or_login_user"))

    sentence = current_app.manager.get_sentence_by_id(sentence_id)
    if request.method == "POST":
        new_text = request.form.get("original_text")
        current_app.manager.update_sentence_text(sentence_id, new_text)
        
        # Note: Translation editing would need to be handled through sessions now
        # This is a simplified version - you may want to add session creation here
        
        return redirect(url_for("ui.edit_sentences_page"))

    return render_template("edit_sentence_form.html", sentence=sentence)

# ==================== LEARNING MANAGEMENT ENDPOINTS ====================

from flask import current_app, request, jsonify
from src.server.api.llm_adapter import LLMAdapter

llm = LLMAdapter()

@api_bp.route("/evaluate_sentence", methods=["POST"])
def evaluate_sentence():
    """
    Evaluate user's translations for a sentence across all target languages
    ---
    tags:
      - Learning
    summary: Evaluate a sentence
    description: Returns scores for each translation and a combined score.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              sentence_id:
                type: integer
              user_translations:
                type: object
                additionalProperties:
                  type: string
            required:
              - sentence_id
              - user_translations
    responses:
      200:
        description: Evaluation result
        content:
          application/json:
            schema:
              type: object
              properties:
                scores:
                  type: object
                  additionalProperties:
                    type: number
                combined_score:
                  type: number
    """
    data = request.get_json()
    sentence_id = data.get("sentence_id")
    user_translations = data.get("user_translations")

    if not sentence_id or not user_translations:
        return jsonify({"error": "Missing sentence_id or user_translations"}), 400

    # Simplified evaluation with session tracking
    # Create session to track this evaluation attempt
    session_input = {
        'user_translations': user_translations,
        'evaluation_type': 'sentence_evaluation'
    }
    
    # For now, use simple scoring - this can be enhanced with LLM later
    scores = {}
    for lang_code, user_text in user_translations.items():
        # Simple scoring placeholder - enhance with actual translation comparison
        scores[lang_code] = 0.8  # Placeholder score

    # Kombinierten Score berechnen (z. B. Durchschnitt)
    if scores:
        combined_score = sum(scores.values()) / len(scores)
    else:
        combined_score = 0.0

    # Create session record
    current_app.manager.create_session(
        user_id=None,  # Should get from session/auth
        sentence_id=sentence_id,
        input_data=session_input,
        score=combined_score
    )
    
    return jsonify({"scores": scores, "combined_score": combined_score}), 200




@api_bp.route('/learn/review/<int:sentence_id>', methods=['POST'])
def review_sentence(sentence_id):
    """
    Submit a review answer for a translation
    ---
    tags:
      - Learning
    parameters:
      - name: sentence_id
        in: path
        type: integer
        required: true
      - name: user_answer
        in: formData
        type: string
        required: true
    """
    try:
        user_answer = request.form.get('user_answer')
        if not user_answer:
            return jsonify({'error': 'user_answer is required'}), 400

        # Get sentence instead of translation
        sentence = current_app.manager.get_sentence_by_id(sentence_id)
        if not sentence:
            return jsonify({'error': 'Sentence not found'}), 404

        # Simple scoring for now - can be enhanced with LLM
        score = 0.8  # Placeholder score
        is_success = score >= 0.7
        
        # Create session to track this review
        session_input = {
            'user_answer': user_answer,
            'review_type': 'translation_review'
        }
        current_app.manager.create_session(
            user_id=sentence.user_id,
            sentence_id=sentence.id,
            input_data=session_input,
            score=score
        )
        
        # Update sentence progress
        updated_sentence = current_app.manager.update_sentence_progress(sentence.id, score, is_success)

        return jsonify({
            'sentence_id': sentence.id,
            'user_answer': user_answer,
            'score': score,
            'next_review': updated_sentence.next_review.isoformat() if updated_sentence.next_review else None
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/learn/user/<int:user_id>/due', methods=['GET'])
def get_due_reviews(user_id):
    """
    Get due progress groups for a user
    ---
    tags:
      - Learning
    summary: Get due reviews
    description: Returns all progress groups that are due for review for a user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
    responses:
      200:
        description: List of due progress groups
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              sentence_id:
                type: integer
              user_id:
                type: integer
              group_score:
                type: number
              next_review:
                type: string
              last_reviewed:
                type: string
              review_count:
                type: integer
              created_at:
                type: string
      404:
        description: User not found
    """
    try:
        due_sentences = current_app.manager.get_due_sentences(user_id)
        sentences_list = []
        for sentence in due_sentences:
            sentences_list.append({
                'id': sentence.id,
                'user_id': sentence.user_id,
                'original_text': sentence.original_text,
                'category': sentence.category,
                'score': sentence.score,
                'next_review': sentence.next_review.isoformat() if sentence.next_review else None,
                'last_review': sentence.last_review.isoformat() if sentence.last_review else None,
                'review_count': sentence.review_count,
                'created_at': sentence.created_at.isoformat() if sentence.created_at else None
            })
        return jsonify(sentences_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/learn/stats/<int:user_id>', methods=['GET'])
def get_learning_stats(user_id):
    """
    Get learning statistics for a user
    ---
    tags:
      - Learning
    summary: Get learning stats
    description: Returns learning statistics for a user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
    responses:
      200:
        description: User learning statistics
        schema:
          type: object
          properties:
            total_reviews:
              type: integer
            avg_success_rate:
              type: number
      404:
        description: User not found
    """
    try:
        stats = current_app.manager.get_learning_stats(user_id)
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

llm = LLMAdapter()

@api_bp.route("/evaluate", methods=["POST"])
def evaluate_answer():
    data = request.get_json()
    user_answer = data.get("user_answer")
    correct_answer = data.get("correct_answer")

    if not user_answer or not correct_answer:
        return jsonify({"error": "Missing fields"}), 400

    score = llm.score_answer(user_answer, correct_answer)
    return jsonify({"score": score}), 200
