from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from models.models import Employee, DecisionLog, PerformanceReview
from services.notification_service import NotificationService
from config.config import Config
from flask import current_app
import logging

class DecisionService:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.logger = logging.getLogger(__name__)

    def evaluate_performance_review(self, review: PerformanceReview) -> Tuple[str, float]:
        """
        Evaluates a performance review and returns a decision recommendation
        """
        try:
            # Calculate weighted score
            metrics = {
                'goals_achieved': 0.3,
                'quality_of_work': 0.3, 
                'attendance': 0.2,
                'teamwork': 0.2
            }
            
            total_score = sum(
                getattr(review, metric) * weight 
                for metric, weight in metrics.items()
            )

            # Decision thresholds
            if total_score >= 4.0:
                return "promotion_recommended", total_score
            elif total_score <= 2.0:
                return "performance_improvement_needed", total_score
            else:
                return "satisfactory", total_score

        except Exception as e:
            self.logger.error(f"Error evaluating performance review: {str(e)}")
            raise

    def validate_decision(self, decision_type: str, employee_id: int, 
                         criteria: Dict) -> Tuple[bool, str]:
        """
        Validates automated decisions against defined criteria and policies
        """
        try:
            employee = Employee.query.get(employee_id)
            if not employee:
                return False, "Employee not found"

            if decision_type == "termination":
                # Require multiple documented performance issues
                performance_issues = DecisionLog.query.filter_by(
                    employee_id=employee_id,
                    decision_type="performance_improvement_needed"
                ).count()
                
                if performance_issues < 2:
                    return False, "Insufficient documentation for termination"
                
                # Require recent performance review
                latest_review = PerformanceReview.query.filter_by(
                    employee_id=employee_id
                ).order_by(PerformanceReview.review_date.desc()).first()
                
                if not latest_review or \
                   (datetime.now() - latest_review.review_date).days > 90:
                    return False, "Recent performance review required"

            elif decision_type == "promotion":
                # Verify tenure and performance criteria
                if employee.tenure_years < 1:
                    return False, "Minimum tenure not met"
                
                high_performance_count = DecisionLog.query.filter_by(
                    employee_id=employee_id,
                    decision_type="promotion_recommended"
                ).count()
                
                if high_performance_count < 2:
                    return False, "Insufficient high performance records"

            return True, "Decision criteria met"

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in decision validation: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error in decision validation: {str(e)}")
            raise

    def log_decision(self, employee_id: int, decision_type: str, 
                    outcome: str, criteria_met: bool, 
                    reviewer_id: Optional[int] = None) -> DecisionLog:
        """
        Logs decisions and their justifications
        """
        try:
            decision_log = DecisionLog(
                employee_id=employee_id,
                decision_type=decision_type,
                outcome=outcome,
                criteria_met=criteria_met,
                reviewer_id=reviewer_id,
                timestamp=datetime.now()
            )
            
            current_app.db.session.add(decision_log)
            current_app.db.session.commit()

            # Notify relevant parties
            self.notification_service.send_decision_notification(
                employee_id=employee_id,
                decision_type=decision_type,
                outcome=outcome
            )

            return decision_log

        except SQLAlchemyError as e:
            current_app.db.session.rollback()
            self.logger.error(f"Database error in decision logging: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error logging decision: {str(e)}")
            raise

    def get_pending_decisions(self) -> List[Dict]:
        """
        Retrieves pending decisions requiring human review
        """
        try:
            pending_decisions = DecisionLog.query.filter_by(
                reviewed=False
            ).order_by(DecisionLog.timestamp.desc()).all()
            
            return [{
                'id': d.id,
                'employee_id': d.employee_id,
                'decision_type': d.decision_type,
                'outcome': d.outcome,
                'criteria_met': d.criteria_met,
                'timestamp': d.timestamp
            } for d in pending_decisions]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving pending decisions: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving pending decisions: {str(e)}")
            raise
