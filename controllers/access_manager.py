from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from hr_automation.models.models import AccessControl, Employee, DecisionLog
from hr_automation.services.notification_service import NotificationService
from hr_automation.services.decision_service import DecisionService
from hr_automation.config.config import Config

logger = logging.getLogger(__name__)

class AccessManager:
    def __init__(self):
        self.notification_service = NotificationService()
        self.decision_service = DecisionService()
        
    def modify_access(self, employee_id: int, access_type: str, 
                     action: str, reason: str) -> Tuple[bool, str]:
        """
        Modify building or system access for an employee
        
        Args:
            employee_id: ID of employee
            access_type: Type of access (building/system)
            action: Grant or revoke access
            reason: Reason for access modification
            
        Returns:
            Tuple of (success boolean, message string)
        """
        try:
            employee = Employee.query.get(employee_id)
            if not employee:
                return False, "Employee not found"
                
            access_record = AccessControl.query.filter_by(
                employee_id=employee_id,
                access_type=access_type
            ).first()
            
            # Create new access record if doesn't exist
            if not access_record:
                access_record = AccessControl(
                    employee_id=employee_id,
                    access_type=access_type,
                    is_active=False
                )
                current_app.db.session.add(access_record)
            
            # Update access status
            prev_status = access_record.is_active
            access_record.is_active = (action == 'grant')
            access_record.last_modified = datetime.utcnow()
            
            # Log the decision
            decision_log = DecisionLog(
                employee_id=employee_id,
                decision_type=f"{action}_{access_type}_access",
                reason=reason,
                timestamp=datetime.utcnow()
            )
            current_app.db.session.add(decision_log)
            
            # Notify relevant parties
            self.notification_service.send_access_notification(
                employee=employee,
                access_type=access_type,
                action=action,
                reason=reason
            )
            
            current_app.db.session.commit()
            
            return True, f"Successfully {action}ed {access_type} access"
            
        except SQLAlchemyError as e:
            current_app.db.session.rollback()
            logger.error(f"Database error modifying access: {str(e)}")
            return False, "Database error occurred"
        except Exception as e:
            logger.error(f"Error modifying access: {str(e)}")
            return False, "Error occurred while modifying access"

    def check_access(self, employee_id: int, access_type: str) -> bool:
        """Check if employee has specific access"""
        try:
            access = AccessControl.query.filter_by(
                employee_id=employee_id,
                access_type=access_type
            ).first()
            return access.is_active if access else False
        except Exception as e:
            logger.error(f"Error checking access: {str(e)}")
            return False

    def get_employee_access_status(self, employee_id: int) -> Dict:
        """Get all access statuses for an employee"""
        try:
            access_records = AccessControl.query.filter_by(
                employee_id=employee_id
            ).all()
            
            return {
                record.access_type: record.is_active 
                for record in access_records
            }
        except Exception as e:
            logger.error(f"Error getting access status: {str(e)}")
            return {}

    def bulk_modify_access(self, employee_ids: List[int], 
                          access_type: str, action: str, 
                          reason: str) -> Dict[int, bool]:
        """
        Modify access for multiple employees
        Returns dict of employee_id: success_status
        """
        results = {}
        for emp_id in employee_ids:
            success, _ = self.modify_access(
                emp_id, access_type, action, reason
            )
            results[emp_id] = success
        return results

    def revoke_all_access(self, employee_id: int, 
                         reason: str) -> Dict[str, bool]:
        """Revoke all access types for an employee"""
        access_types = ['building', 'system']
        results = {}
        for access_type in access_types:
            success, _ = self.modify_access(
                employee_id, access_type, 'revoke', reason
            )
            results[access_type] = success
        return results

    def get_access_history(self, employee_id: int, 
                          access_type: Optional[str] = None) -> List[Dict]:
        """Get access modification history for an employee"""
        try:
            query = DecisionLog.query.filter(
                DecisionLog.employee_id == employee_id,
                DecisionLog.decision_type.like('%_access')
            )
            
            if access_type:
                query = query.filter(
                    DecisionLog.decision_type.like(f'%_{access_type}_access')
                )
                
            logs = query.order_by(DecisionLog.timestamp.desc()).all()
            
            return [{
                'decision_type': log.decision_type,
                'reason': log.reason,
                'timestamp': log.timestamp
            } for log in logs]
            
        except Exception as e:
            logger.error(f"Error getting access history: {str(e)}")
            return []
