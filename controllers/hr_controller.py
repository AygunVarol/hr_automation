from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from models.models import Employee, AccessControl, PerformanceReview, DecisionLog, db
from services.notification_service import NotificationService
from services.decision_service import DecisionService
from controllers.access_manager import AccessManager
from sqlalchemy.exc import SQLAlchemyError
import logging

hr_controller = Blueprint('hr_controller', __name__)
notification_service = NotificationService()
decision_service = DecisionService()
access_manager = AccessManager()

logger = logging.getLogger(__name__)

@hr_controller.route('/api/employees', methods=['GET'])
def get_employees():
    try:
        employees = Employee.query.all()
        return jsonify([emp.to_dict() for emp in employees]), 200
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving employees: {str(e)}")
        return jsonify({"error": "Failed to retrieve employees"}), 500

@hr_controller.route('/api/employees/<int:employee_id>/review', methods=['POST'])
def create_performance_review(employee_id):
    try:
        data = request.get_json()
        employee = Employee.query.get_or_404(employee_id)
        
        review = PerformanceReview(
            employee_id=employee_id,
            review_date=datetime.now(),
            performance_score=data['performance_score'],
            review_notes=data['review_notes'],
            reviewer_id=data['reviewer_id']
        )
        
        automated_decision = decision_service.evaluate_performance(
            employee_id, 
            data['performance_score']
        )
        
        review.automated_decision = automated_decision
        review.requires_hr_review = True
        
        db.session.add(review)
        
        decision_log = DecisionLog(
            employee_id=employee_id,
            decision_type="performance_review",
            decision_details=automated_decision,
            timestamp=datetime.now()
        )
        db.session.add(decision_log)
        db.session.commit()

        notification_service.send_review_notification(
            employee.email,
            review.to_dict()
        )
        
        return jsonify(review.to_dict()), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating review: {str(e)}")
        return jsonify({"error": "Failed to create performance review"}), 500

@hr_controller.route('/api/reviews/pending', methods=['GET'])
def get_pending_reviews():
    try:
        pending_reviews = PerformanceReview.query.filter_by(
            requires_hr_review=True,
            hr_reviewed=False
        ).all()
        return jsonify([review.to_dict() for review in pending_reviews]), 200
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving pending reviews: {str(e)}")
        return jsonify({"error": "Failed to retrieve pending reviews"}), 500

@hr_controller.route('/api/reviews/<int:review_id>/approve', methods=['POST'])
def approve_review(review_id):
    try:
        review = PerformanceReview.query.get_or_404(review_id)
        data = request.get_json()
        
        review.hr_reviewed = True
        review.hr_notes = data.get('hr_notes', '')
        review.hr_decision = data['hr_decision']
        review.review_date = datetime.now()
        
        if review.hr_decision == 'terminate':
            employee = Employee.query.get(review.employee_id)
            access_manager.initiate_access_revocation(employee.id)
            
            notification_service.send_critical_action_notification(
                employee.email,
                'termination',
                data.get('hr_notes', '')
            )
        
        db.session.commit()
        return jsonify(review.to_dict()), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error approving review: {str(e)}")
        return jsonify({"error": "Failed to approve review"}), 500

@hr_controller.route('/api/employees/<int:employee_id>/access', methods=['PUT'])
def modify_access(employee_id):
    try:
        data = request.get_json()
        employee = Employee.query.get_or_404(employee_id)
        
        access_control = AccessControl.query.filter_by(
            employee_id=employee_id
        ).first()
        
        if not access_control:
            access_control = AccessControl(employee_id=employee_id)
            db.session.add(access_control)
        
        access_control.building_access = data.get('building_access', 
                                                access_control.building_access)
        access_control.system_access = data.get('system_access', 
                                              access_control.system_access)
        access_control.last_modified = datetime.now()
        
        decision_log = DecisionLog(
            employee_id=employee_id,
            decision_type="access_modification",
            decision_details=str(data),
            timestamp=datetime.now()
        )
        db.session.add(decision_log)
        
        db.session.commit()
        
        notification_service.send_access_modification_notification(
            employee.email,
            access_control.to_dict()
        )
        
        return jsonify(access_control.to_dict()), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error modifying access: {str(e)}")
        return jsonify({"error": "Failed to modify access"}), 500
