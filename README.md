# HR Automation

## AI-powered HR automation platform that manages key employment decisions—including performance reviews, promotions, and terminations—while also controlling building and system access. In light of the incident, the project emphasizes embedding human oversight and transparent decision-making criteria to prevent unjust terminations. Alerts would be sent to both HR personnel and the affected employee before any critical action (e.g., account deactivation, building access revocation).

The HR automation platform will be built using Python with Flask as the web framework, following a modular MVC architecture. The core system consists of five main components: 1) 'app.py' serves as the main application entry point, handling route configurations and middleware setup, including authentication via Flask-Login. 2) 'models.py' defines SQLAlchemy ORM models for Employee, AccessControl, PerformanceReview, and DecisionLog entities, with PostgreSQL as the primary database using Flask-SQLAlchemy for robust data management. 3) 'hr_controller.py' contains the business logic for HR operations, implementing decision-making algorithms with human oversight triggers, and manages the workflow for performance reviews and access control modifications. 4) 'access_manager.py' handles building and system access control, integrating with external security systems via APIs and maintaining an audit trail of all access changes. 5) 'notification_service.py' manages the alert system using Flask-Mail for email notifications and websockets for real-time alerts to both HR personnel and employees. The system uses JWT for API authentication and implements rate limiting through Flask-Limiter. Database connections are managed through a connection pool to ensure efficient resource utilization, with database credentials stored in environment variables. The architecture implements event-driven patterns for critical actions, where any automated decision triggers a mandatory review queue in the HR dashboard before execution. Data flows from the controllers through service layers, which apply business rules and validation before persisting to the database, ensuring all decisions have proper oversight and documentation.

```
hr_automation/
  - app.py
  - config/
    - config.py
  - models/
    - models.py
  - controllers/
    - hr_controller.py
    - access_manager.py
  - services/
    - notification_service.py
    - decision_service.py
  - templates/
    - dashboard/
      - hr_dashboard.html
      - review_queue.html
  - static/
    - js/
      - websocket_handler.js
```
