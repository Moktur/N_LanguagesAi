from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta
from src.server.extensions import db
from src.server.models.data_models import (
    User, User_Languages, Sentences, Sessions
)
from src.server.api.llm_adapter import LLMAdapter


class DataManager:
    def __init__(self):
        self.db = db
        self.llm = LLMAdapter()

    def _commit(self):
        try:
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise e

    # User Management
    def create_user(self, username, native_language):
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists")
        user = User(username=username, native_language=native_language, created_at=datetime.utcnow())
        self.db.session.add(user)
        self._commit()
        return user

    def get_user_by_id(self, user_id):
        return User.query.get(user_id)

    def get_user_by_username(self, username):
        return User.query.filter_by(username=username).first()

    # get all users for test reasons
    def get_users(self):
        users = User.query.all()
        return [{
            'id': user.id,
            'username': user.username,
            'native_language': user.native_language,
            'created_at': user.created_at.isoformat() if user.created_at else None
        } for user in users]

    def add_target_language(self, user_id, language_code):
        if not self.get_user_by_id(user_id):
            raise ValueError("User not found")
        if User_Languages.query.filter_by(user_id=user_id, language_code=language_code).first():
            raise ValueError("Language already added")
        lang = User_Languages(user_id=user_id, language_code=language_code, created_at=datetime.utcnow())
        self.db.session.add(lang)
        self._commit()
        return lang

    def get_user_languages(self, user_id):
        return User_Languages.query.filter_by(user_id=user_id).all()

    # Sentences Management

    def add_sentence_with_translations(self, user_id, original_text, category=None):
        # Create sentence with default progress values
        sentence = self.create_sentence(user_id, original_text, category)
        return sentence



    def get_user_categories(self, user_id):
        # returns all identified categories of a user
        categories = Sentences.query.filter_by(user_id=user_id).with_entities(Sentences.category).distinct().all()
        return [category[0] for category in categories if category[0]]

    def create_sentence(self, user_id, original_text, category=None):
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        sentence = Sentences(
            user_id=user_id,
            original_text=original_text,
            language_code=user.native_language,
            category=category,
            score=0.0,
            last_review=None,
            next_review=datetime.utcnow(),
            review_count=0,
            created_at=datetime.utcnow()
        )
        self.db.session.add(sentence)
        self._commit()
        return sentence

    def get_sentences_for_user(self, user_id):
        return Sentences.query.filter_by(user_id=user_id).all()

    def get_sentences_by_category(self, user_id, category):
        return Sentences.query.filter_by(user_id=user_id, category=category).all()

    def delete_sentence(self, sentence_id):
        sentence = Sentences.query.get(sentence_id)
        if sentence:
            # delete all dependent sessions
            Sessions.query.filter_by(sentence_id=sentence_id).delete()
            self.db.session.delete(sentence)
            self._commit()
            return True
        return False


    def delete_user(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Delete all dependent data in correct order
        # Sessions for user
        Sessions.query.filter_by(user_id=user_id).delete()
        
        # User_Languages for user
        User_Languages.query.filter_by(user_id=user_id).delete()
        
        # All sentences for user (sessions already deleted above)
        user_sentences = Sentences.query.filter_by(user_id=user_id).all()
        for sentence in user_sentences:
            self.db.session.delete(sentence)
        
        # Delete user
        self.db.session.delete(user)
        self._commit()
        return True
            

    # Sessions Management
    def create_session(self, user_id, sentence_id, input_data=None, score=None):
        session = Sessions(
            user_id=user_id,
            sentence_id=sentence_id,
            input=input_data,
            score=score,
            created_at=datetime.utcnow()
        )
        self.db.session.add(session)
        self._commit()
        return session

    def get_sessions_for_user(self, user_id):
        return Sessions.query.filter_by(user_id=user_id).all()

    def get_sessions_for_sentence(self, sentence_id):
        return Sessions.query.filter_by(sentence_id=sentence_id).all()

    def get_session_by_id(self, session_id):
        return Sessions.query.get(session_id)

    # Sentence Progress Management
    def update_sentence_progress(self, sentence_id, new_score, is_success):
        sentence = Sentences.query.get(sentence_id)
        if not sentence:
            raise ValueError("Sentence not found")
            
        sentence.score = new_score
        sentence.review_count += 1
        sentence.last_review = datetime.utcnow()
        
        # Simple Anki algorithm
        if is_success:
            # Increase interval based on review count
            interval_days = max(1, sentence.review_count * 2)
        else:
            # Reset to 1 day for failed reviews
            interval_days = 1
            
        sentence.next_review = datetime.utcnow() + timedelta(days=interval_days)
        self._commit()
        return sentence

    def get_due_sentences(self, user_id):
        now = datetime.utcnow()
        return Sentences.query.filter(
            and_(Sentences.user_id == user_id, 
                 Sentences.next_review <= now)
        ).all()

    def get_sentence_by_id(self, sentence_id):
        return Sentences.query.get(sentence_id)

    def update_sentence_text(self, sentence_id, new_text):
        sentence = Sentences.query.get(sentence_id)
        if sentence:
            sentence.original_text = new_text
            self._commit()
            return sentence
        return None

    def get_learning_stats(self, user_id):
        total_sentences = Sentences.query.filter_by(user_id=user_id).count()
        total_sessions = Sessions.query.filter_by(user_id=user_id).count()
        avg_score = db.session.query(func.avg(Sentences.score)).filter_by(user_id=user_id).scalar() or 0
        
        stats = {
            'total_sentences': total_sentences,
            'total_sessions': total_sessions,
            'avg_score': float(avg_score)
        }
        return stats