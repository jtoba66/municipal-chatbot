"""
Action Registry
Maps action names to handler modules and field schemas
"""
from typing import Dict, Optional, List
from .base import ActionSchema, ActionBase


# Action schemas - defines field requirements for each action
ACTION_SCHEMAS: Dict[str, ActionSchema] = {
    "pay_ticket": ActionSchema(
        action="pay_ticket",
        city="kitchener",
        description="Pay a parking ticket online",
        required_fields=[
            {
                "name": "ticket_number",
                "type": "text",
                "label": "Ticket Number",
                "required": True,
                "validation": r"^[A-Z0-9]{6,}$",
                "placeholder": "e.g., A123456"
            }
        ],
        optional_fields=[],
        portal_url="https://portal.gtechna.com/userportal/kitchener/ticketSearch1.xhtml",
        automation_script="kitchener/pay_ticket.py"
    ),
    "pay_ticket_waterloo": ActionSchema(
        action="pay_ticket_waterloo",
        city="waterloo",
        description="Pay a parking ticket online in Waterloo",
        required_fields=[
            {
                "name": "license_plate",
                "type": "text",
                "label": "License Plate",
                "required": True,
                "validation": r"^[A-Z0-9\-]{2,10}$",
                "placeholder": "e.g., ABCD123"
            },
            {
                "name": "penalty_number",
                "type": "text",
                "label": "Penalty Notice Number",
                "required": True,
                "validation": r"^[0-9]{6,}$",
                "placeholder": "e.g., 123456"
            }
        ],
        optional_fields=[],
        portal_url="https://amps.waterloo.ca/pay",
        automation_script="waterloo/pay_ticket.py"
    ),
    "report_issue": ActionSchema(
        action="report_issue",
        city="kitchener",
        description="Report a municipal issue (pothole, graffiti, etc.)",
        required_fields=[
            {
                "name": "issue_type",
                "type": "select",
                "label": "Issue Type",
                "required": True,
                "options": [
                    "Graffiti", "Illegal sign", "Litter in a playground, park or trail",
                    "Needles", "Parking complaint", "Property standards complaint",
                    "Pothole", "Sidewalk snow clearing", "Sidewalk trip hazard",
                    "Trail surface maintenance", "Other"
                ]
            },
            {
                "name": "location",
                "type": "text",
                "label": "Location",
                "required": True,
                "placeholder": "Street address or cross streets"
            },
            {
                "name": "description",
                "type": "textarea",
                "label": "Description",
                "required": True,
                "max_length": 500,
                "placeholder": "Describe the issue in detail"
            },
            {
                "name": "contact_name",
                "type": "text",
                "label": "Contact Name",
                "required": True
            },
            {
                "name": "contact_email",
                "type": "email",
                "label": "Email Address",
                "required": True,
                "validation": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            },
            {
                "name": "contact_phone",
                "type": "phone",
                "label": "Phone Number",
                "required": False,
                "validation": r"^\d{3}-\d{3}-\d{4}$"
            }
        ],
        optional_fields=[
            {
                "name": "photo",
                "type": "file",
                "label": "Photo",
                "required": False
            }
        ],
        portal_url="https://form.kitchener.ca/CSD/CCS/Report-a-problem",
        automation_script="kitchener/report_issue.py"
    ),
    "book_parking_permit": ActionSchema(
        action="book_parking_permit",
        city="kitchener",
        description="Book a monthly parking permit",
        required_fields=[
            {
                "name": "parking_location",
                "type": "select",
                "label": "Parking Location",
                "required": True,
                "options": [
                    "Queen Street South (Lot 7)",
                    "Charles Street West (Lot 15)",
                    "Transit (Lot 22)",
                    "King Street East (Lot 23)",
                    "Bramm Street Yards (Lot 24)",
                    "Charles & Benton parking garage",
                    "Civic District parking garage",
                    "Duke & Ontario parking garage",
                    "Kitchener Market parking garage",
                    "City Hall parking garage",
                    "Water Street South (Lot 3)",
                    "Ontario Street South (Lot 9)",
                    "Green Street (Lot 12)",
                    "Rotary (Lot 13)",
                    "Centre In The Square (Lot 19A)"
                ]
            },
            {
                "name": "email",
                "type": "email",
                "label": "Email Address",
                "required": True,
                "validation": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            },
            {
                "name": "license_plate",
                "type": "text",
                "label": "License Plate Number",
                "required": True,
                "validation": r"^[A-Z0-9\-]{2,10}$"
            },
            {
                "name": "phone",
                "type": "phone",
                "label": "Phone Number",
                "required": True,
                "validation": r"^\d{3}-\d{3}-\d{4}$"
            }
        ],
        optional_fields=[],
        portal_url="https://kitchener.parkingpermit.site/signup",
        automation_script="kitchener/book_parking_permit.py"
    ),
    "check_permit_status": ActionSchema(
        action="check_permit_status",
        city="kitchener",
        description="Check building permit status",
        required_fields=[
            {
                "name": "search_type",
                "type": "select",
                "label": "Search Type",
                "required": True,
                "options": ["Address", "Permit Number"]
            },
            {
                "name": "search_value",
                "type": "text",
                "label": "Address or Permit Number",
                "required": True,
                "placeholder": "Enter the address or permit number"
            }
        ],
        optional_fields=[],
        portal_url="https://onlineserviceportal2.kitchener.ca/citizenportal/app/landing",
        automation_script="kitchener/check_permit_status.py"
    ),
    "schedule_inspection": ActionSchema(
        action="schedule_inspection",
        city="kitchener",
        description="Schedule a building inspection",
        required_fields=[
            {
                "name": "permit_number",
                "type": "text",
                "label": "Permit Number",
                "required": True,
                "validation": r"^[A-Z0-9]{5,}$",
                "placeholder": "e.g., BLP2025-001"
            },
            {
                "name": "inspection_type",
                "type": "select",
                "label": "Inspection Type",
                "required": True,
                "options": [
                    "Foundation inspection",
                    "Framing inspection",
                    "Electrical inspection",
                    "Plumbing inspection",
                    "HVAC inspection",
                    "Final inspection"
                ]
            },
            {
                "name": "preferred_date",
                "type": "text",
                "label": "Preferred Date",
                "required": True,
                "placeholder": "YYYY-MM-DD"
            },
            {
                "name": "preferred_time",
                "type": "select",
                "label": "Preferred Time",
                "required": True,
                "options": ["Morning (8AM-12PM)", "Afternoon (12PM-4PM)"]
            }
        ],
        optional_fields=[],
        portal_url="https://onlineserviceportal2.kitchener.ca/citizenportal/app/landing",
        automation_script="kitchener/schedule_inspection.py"
    )
}


# Action handler registry - maps action names to handler classes
ACTION_HANDLERS: Dict[str, type] = {}


def register_action_handler(action_name: str, handler_class: type):
    """Register a handler class for an action"""
    ACTION_HANDLERS[action_name] = handler_class


def get_action_schema(action_name: str) -> Optional[ActionSchema]:
    """Get the schema for a specific action"""
    return ACTION_SCHEMAS.get(action_name)


def get_all_actions() -> List[str]:
    """Get list of all available actions"""
    return list(ACTION_SCHEMAS.keys())


def get_handler(action_name: str) -> Optional[type]:
    """Get the handler class for an action"""
    return ACTION_HANDLERS.get(action_name)


# Registry for external access
ACTION_REGISTRY = {
    "schemas": ACTION_SCHEMAS,
    "handlers": ACTION_HANDLERS,
    "register": register_action_handler,
    "get_schema": get_action_schema,
    "get_all": get_all_actions,
    "get_handler": get_handler
}