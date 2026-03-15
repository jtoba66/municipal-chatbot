"""
Base Action Class
Abstract class defining the interface for all action handlers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class FieldDefinition(BaseModel):
    """Definition of a single field required for an action"""
    name: str
    type: str  # text, email, phone, select, textarea
    label: str
    required: bool = True
    validation: Optional[str] = None  # regex pattern or validation type
    options: Optional[List[str]] = None  # for select fields
    max_length: Optional[int] = None
    placeholder: Optional[str] = None


class ActionSchema(BaseModel):
    """Schema defining all fields for an action"""
    action: str
    city: str  # kitchener, waterloo
    description: str
    required_fields: List[FieldDefinition]
    optional_fields: List[FieldDefinition] = []
    portal_url: str
    execution_type: str = "deep_link"  # "deep_link" or "automation"
    automation_script: Optional[str] = None


class ActionResult(BaseModel):
    """Result of executing an action"""
    success: bool
    message: str
    confirmation_number: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    fallback_url: Optional[str] = None


class ActionBase(ABC):
    """
    Abstract base class for all action handlers.
    Each action (pay_ticket, report_issue, etc.) should inherit from this.
    """
    
    def __init__(self):
        self._schema = self._get_schema()
    
    @abstractmethod
    def _get_schema(self) -> ActionSchema:
        """Return the action schema defining required fields"""
        pass
    
    @abstractmethod
    async def execute(self, fields: Dict[str, Any]) -> ActionResult:
        """
        Execute the action with the given fields.
        This is where Playwright automation would happen.
        """
        pass
    
    def validate_field(self, field_name: str, value: str) -> tuple[bool, Optional[str]]:
        """
        Validate a single field value.
        Returns (is_valid, error_message)
        """
        for field in self._schema.required_fields:
            if field.name == field_name:
                if field.validation:
                    import re
                    if not re.match(field.validation, value):
                        return False, f"Invalid format for {field.label}"
                return True, None
        
        for field in self._schema.optional_fields:
            if field.name == field_name:
                if field.validation:
                    import re
                    if not re.match(field.validation, value):
                        return False, f"Invalid format for {field.label}"
                return True, None
        
        return True, None  # Unknown field, assume valid
    
    def get_schema(self) -> ActionSchema:
        """Get the action schema"""
        return self._schema
    
    def get_required_fields(self) -> List[FieldDefinition]:
        """Get list of required fields"""
        return self._schema.required_fields
    
    def get_optional_fields(self) -> List[FieldDefinition]:
        """Get list of optional fields"""
        return self._schema.optional_fields
    
    def get_portal_url(self) -> str:
        """Get the portal URL for this action"""
        return self._schema.portal_url