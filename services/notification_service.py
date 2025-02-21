from flask import current_app
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Initialize Flask-Mail and SocketIO
mail = Mail()
socketio = SocketIO()

class NotificationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_email_notification(self, recipient: str, subject: str, body: str) -> bool:
        """
        Send email notification using Flask-Mail
        """
        try:
            msg = Message(
                subject=subject,
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[recipient],
                body=body
            )
            mail.send(msg)
            self.logger.info(f"Email sent successfully to {recipient}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient}: {str(e)}")
            return False

    def send_websocket_notification(self, event: str, data: Dict) -> None:
        """
        Send real-time notification via websockets
        """
        try:
            socketio.emit(event, data)
            self.logger.info(f"Websocket notification sent: {event}")
        except Exception as e:
            self.logger.error(f"Failed to send websocket notification: {str(e)}")

    def notify_hr_personnel(self, action_type: str, details: Dict) -> None:
        """
        Send notifications to HR personnel for review/approval
        """
        subject = f"HR Action Required: {action_type}"
        body = f"""
        Action Type: {action_type}
        Details: {json.dumps(details, indent=2)}
        Time: {datetime.now()}
        
        Please review this action in the HR dashboard.
        """
        
        # Send email to all HR personnel
        hr_emails = current_app.config['HR_NOTIFICATION_EMAILS']
        for email in hr_emails:
            self.send_email_notification(email, subject, body)
        
        # Send websocket notification
        self.send_websocket_notification('hr_review_required', {
            'action_type': action_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def notify_employee(self, employee_email: str, action_type: str, details: str) -> None:
        """
        Send notification to affected employee
        """
        subject = f"Important HR Update: {action_type}"
        body = f"""
        Dear Employee,

        This is to inform you about the following HR action:
        
        {details}

        If you have any questions, please contact HR immediately.

        Time: {datetime.now()}
        """
        
        self.send_email_notification(employee_email, subject, body)
        
        # Send websocket notification if employee is online
        self.send_websocket_notification('employee_notification', {
            'employee_email': employee_email,
            'action_type': action_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def send_access_change_alert(self, employee_email: str, access_type: str, 
                               status: str, reason: Optional[str] = None) -> None:
        """
        Send notification for access control changes
        """
        subject = f"Access Control Update: {access_type}"
        body = f"""
        Access Update Information:
        
        Type: {access_type}
        Status: {status}
        Reason: {reason if reason else 'Not specified'}
        Time: {datetime.now()}
        
        If this change was not expected, please contact HR immediately.
        """
        
        self.send_email_notification(employee_email, subject, body)
        self.notify_hr_personnel('access_change', {
            'employee_email': employee_email,
            'access_type': access_type,
            'status': status,
            'reason': reason
        })

    def send_performance_review_notification(self, employee_email: str, 
                                          review_date: datetime, 
                                          reviewer: str) -> None:
        """
        Send notification for upcoming performance review
        """
        subject = "Upcoming Performance Review"
        body = f"""
        Dear Employee,

        Your performance review has been scheduled:
        
        Date: {review_date}
        Reviewer: {reviewer}
        
        Please prepare necessary documentation and self-assessment.
        """
        
        self.send_email_notification(employee_email, subject, body)
        self.send_websocket_notification('performance_review_scheduled', {
            'employee_email': employee_email,
            'review_date': review_date.isoformat(),
            'reviewer': reviewer
        })

    def send_decision_notification(self, employee_email: str, decision_type: str, 
                                 decision: str, details: Dict) -> None:
        """
        Send notification for HR decisions
        """
        subject = f"HR Decision Notification: {decision_type}"
        body = f"""
        Dear Employee,

        A decision has been made regarding: {decision_type}
        
        Decision: {decision}
        Details: {json.dumps(details, indent=2)}
        
        If you have any questions, please contact HR.
        """
        
        self.send_email_notification(employee_email, subject, body)
        self.notify_hr_personnel('decision_made', {
            'employee_email': employee_email,
            'decision_type': decision_type,
            'decision': decision,
            'details': details
        })
