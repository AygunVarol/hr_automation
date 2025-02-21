from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='active')
    
    # Relationships
    access_controls = relationship('AccessControl', back_populates='employee')
    performance_reviews = relationship('PerformanceReview', back_populates='employee')
    decision_logs = relationship('DecisionLog', back_populates='employee')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AccessControl(db.Model):
    __tablename__ = 'access_controls'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    access_type = db.Column(db.String(50), nullable=False)  # building, system
    access_level = db.Column(db.String(20), nullable=False)  # full, restricted, none
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default='active')
    last_modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_by = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # Relationships
    employee = relationship('Employee', back_populates='access_controls', foreign_keys=[employee_id])
    modifier = relationship('Employee', foreign_keys=[modified_by])

class PerformanceReview(db.Model):
    __tablename__ = 'performance_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    review_date = db.Column(db.DateTime, nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    metrics = db.Column(JSONB, nullable=False)
    overall_score = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship('Employee', back_populates='performance_reviews', foreign_keys=[employee_id])
    reviewer = relationship('Employee', foreign_keys=[reviewer_id])

class DecisionLog(db.Model):
    __tablename__ = 'decision_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    decision_type = db.Column(db.String(50), nullable=False)  # promotion, termination, access_change
    decision_data = db.Column(JSONB, nullable=False)
    automated_decision = db.Column(db.Boolean, nullable=False)
    hr_review_status = db.Column(db.String(20), nullable=False, default='pending')
    hr_reviewer_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    review_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship('Employee', back_populates='decision_logs', foreign_keys=[employee_id])
    hr_reviewer = relationship('Employee', foreign_keys=[hr_reviewer_id])
