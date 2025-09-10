# Back-End/Modules/Models/postgressSQL.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(200), nullable=True)
    platform_id = db.Column(db.String(200), nullable=True)  # caso você precise mapear um id externo
    status = db.Column(db.String(50), default="active")  # 'active', 'banned', etc.
    last_seen = db.Column(db.DateTime, nullable=True)     # corresponde a 'lastSeen' do firebase
    ban_reason = db.Column(db.Text, nullable=True)
    ban_duration = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships - FIXED
    messages = db.relationship("Message", backref="user", lazy=True, foreign_keys="Message.user_id")
    alfred_files = db.relationship("AlfredFile", backref="user", lazy=True, foreign_keys="AlfredFile.uploaded_by_user_id")
    configs = db.relationship("Config", backref="user", lazy=True, foreign_keys="Config.user_id")
    activities = db.relationship("Activity", backref="user", lazy=True, foreign_keys="Activity.user_id")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AgentStatus(db.Model):
    __tablename__ = "agent_status"

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)  # Removed unique=True for user-specific agents
    status = db.Column(db.String(50), nullable=False, default="offline")  # 'online', 'offline', 'degraded'
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    image_name = db.Column(db.String(200), nullable=True)
    container_name = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # FIXED: Integer + ForeignKey

    # Add unique constraint for platform per user
    __table_args__ = (db.UniqueConstraint('platform', 'user_id', name='unique_platform_per_user'),)

class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # FIXED: Integer + ForeignKey
    role = db.Column(db.String(50), nullable=False)  # "user" ou "assistant"
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # opcional: meta (JSON) para armazenar campos extras
    meta = db.Column(db.JSON, nullable=True)

class Config(db.Model):
    __tablename__ = "configurations"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False)  # Removed unique=True to allow per-user configs
    value = db.Column(db.JSON, nullable=False)  # guarda botConfig, moderationConfig, alfredConfig como JSON
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # FIXED: Integer + ForeignKey

    # Add unique constraint for key per user
    __table_args__ = (db.UniqueConstraint('key', 'user_id', name='unique_key_per_user'),)

class AlfredFile(db.Model):
    __tablename__ = "alfred_files"

    id = db.Column(db.Integer, primary_key=True)
    unique_filename = db.Column(db.String(255), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    channel_id = db.Column(db.String(100), nullable=True)
    caption = db.Column(db.Text, nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_local = db.Column(db.DateTime, nullable=True)
    local_path = db.Column(db.String(500), nullable=False)
    url_download = db.Column(db.String(500), nullable=False)
    url_content = db.Column(db.String(500), nullable=False)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # FIXED: Integer + ForeignKey

class Activity(db.Model):
    """
    Model opcional para persistir logs/atividades estruturadas no banco.
    (A API continuará montando a lista dinamicamente a partir de Message/User/AlfredFile,
    mas esse model permite gravar eventos explícitos no futuro.)
    """
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)   # message, ban, unban, file, response, error, info
    user_name = db.Column(db.String(200), nullable=True)  # Renamed from 'user' to avoid confusion
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="info")  # success, warning, error, info
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # FIXED: Integer + ForeignKey