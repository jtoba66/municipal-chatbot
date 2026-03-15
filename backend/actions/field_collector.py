"""
Field Collection Engine
Manages state machine for collecting missing fields per action
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class ConversationState:
    """Tracks the state of an action in a conversation"""
    
    def __init__(self, session_id: str, action: str, city: str = "kitchener"):
        self.session_id = session_id
        self.action = action
        self.city = city
        self.fields: Dict[str, Any] = {}
        self.missing_fields: List[str] = []
        self.current_field_index: int = 0
        self.state: str = "collecting"  # collecting, awaiting_confirmation, executing, completed, failed
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.confirmation_number: Optional[str] = None
        self.error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "action": self.action,
            "city": self.city,
            "fields": self.fields,
            "missing_fields": self.missing_fields,
            "current_field_index": self.current_field_index,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confirmation_number": self.confirmation_number,
            "error_message": self.error_message
        }
    
    def __repr__(self):
        return f"ConversationState(session={self.session_id}, action={self.action}, state={self.state}, fields={list(self.fields.keys())})"


class ActionStateManager:
    """
    Manages conversation state for all active action flows.
    Uses in-memory storage (can be replaced with Redis/DB for production).
    """
    
    def __init__(self):
        # In-memory store: {session_id: ConversationState}
        self._states: Dict[str, ConversationState] = {}
    
    def start_action(self, session_id: str, action: str, required_fields: List[str], city: str = "kitchener") -> ConversationState:
        """Start a new action flow for a session"""
        # Clear any existing state for this session
        if session_id in self._states:
            del self._states[session_id]
        
        state = ConversationState(session_id, action, city)
        state.missing_fields = required_fields.copy()
        self._states[session_id] = state
        return state
    
    def get_state(self, session_id: str) -> Optional[ConversationState]:
        """Get the current state for a session"""
        return self._states.get(session_id)
    
    def update_field(self, session_id: str, field_name: str, value: Any) -> bool:
        """Update a field value for a session's action"""
        state = self._states.get(session_id)
        if not state or state.state != "collecting":
            return False
        
        # Store the field value
        state.fields[field_name] = value
        
        # Remove from missing fields if present
        if field_name in state.missing_fields:
            state.missing_fields.remove(field_name)
        
        state.updated_at = datetime.now()
        return True
    
    def set_state(self, session_id: str, new_state: str) -> bool:
        """Update the state machine state"""
        state = self._states.get(session_id)
        if not state:
            return False
        
        state.state = new_state
        state.updated_at = datetime.now()
        return True
    
    def set_confirmation_number(self, session_id: str, confirmation: str) -> bool:
        """Set the confirmation number after successful execution"""
        state = self._states.get(session_id)
        if not state:
            return False
        
        state.confirmation_number = confirmation
        state.state = "completed"
        state.updated_at = datetime.now()
        return True
    
    def set_error(self, session_id: str, error: str) -> bool:
        """Set an error message"""
        state = self._states.get(session_id)
        if not state:
            return False
        
        state.error_message = error
        state.state = "failed"
        state.updated_at = datetime.now()
        return True
    
    def clear_state(self, session_id: str) -> bool:
        """Clear the state for a session"""
        if session_id in self._states:
            del self._states[session_id]
            return True
        return False
    
    def get_missing_fields(self, session_id: str) -> List[str]:
        """Get the list of missing fields for a session"""
        state = self._states.get(session_id)
        if not state:
            return []
        return state.missing_fields
    
    def is_complete(self, session_id: str) -> bool:
        """Check if all required fields have been collected"""
        state = self._states.get(session_id)
        if not state:
            return False
        return len(state.missing_fields) == 0 and state.state == "collecting"
    
    def get_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the collected fields for confirmation"""
        state = self._states.get(session_id)
        if not state:
            return None
        
        return {
            "action": state.action,
            "city": state.city,
            "fields": state.fields,
            "state": state.state
        }


# Global instance
action_state_manager = ActionStateManager()


class FieldCollector:
    """
    Helper class for collecting fields in a conversation.
    Designed to work with the LLM to ask for all missing fields at once.
    """
    
    def __init__(self, state_manager: ActionStateManager = None):
        self.state_manager = state_manager or action_state_manager
    
    def start_collection(self, session_id: str, action: str, required_fields: List[str], city: str = "kitchener") -> str:
        """Start field collection and return the first prompt"""
        state = self.state_manager.start_action(session_id, action, required_fields, city)
        return self._generate_prompt(state)
    
    def process_response(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process user response and extract field values.
        Returns dict with:
        - prompt: next prompt to show user (if more fields needed)
        - is_complete: whether all fields are collected
        - summary: summary of collected fields (if complete)
        - state: current conversation state
        """
        state = self.state_manager.get_state(session_id)
        if not state:
            return {
                "prompt": "Sorry, I lost track of our conversation. Let's start over. What would you like to do?",
                "is_complete": False,
                "state": None
            }
        
        if state.state != "collecting":
            return {
                "prompt": "I'm waiting for confirmation. Please say yes or no.",
                "is_complete": False,
                "state": state.state
            }
        
        # Try to extract field values from the user message using simple heuristics
        # In production, this would use the LLM
        extracted = self._extract_fields_from_message(user_message, state.missing_fields)
        
        # Update state with extracted values
        for field_name, value in extracted.items():
            if value:
                self.state_manager.update_field(session_id, field_name, value)
        
        # Check if we're done collecting
        if self.state_manager.is_complete(session_id):
            state = self.state_manager.get_state(session_id)
            return {
                "prompt": None,
                "is_complete": True,
                "summary": self._generate_summary(state),
                "state": "awaiting_confirmation"
            }
        
        # Generate next prompt for remaining fields
        state = self.state_manager.get_state(session_id)
        return {
            "prompt": self._generate_prompt(state),
            "is_complete": False,
            "missing_fields": state.missing_fields,
            "collected_fields": list(state.fields.keys()),
            "state": "collecting"
        }
    
    def _extract_fields_from_message(self, message: str, missing_fields: List[str]) -> Dict[str, Optional[str]]:
        """
        Extract field values from user message.
        This is a simple implementation - in production, use the LLM.
        """
        extracted = {}
        message_lower = message.lower()
        
        for field in missing_fields:
            # Simple heuristics for common fields
            if field == "ticket_number":
                # Look for patterns like A123456
                import re
                match = re.search(r'[A-Z]\d{6,}', message, re.IGNORECASE)
                if match:
                    extracted[field] = match.group().upper()
                elif "ticket" in message_lower:
                    # Try to extract from context
                    parts = message.split()
                    for part in parts:
                        if len(part) >= 6 and part.replace('-', '').isalnum():
                            extracted[field] = part.upper()
                            break
            
            elif field == "license_plate":
                import re
                match = re.search(r'[A-Z]{1,3}\d{2,5}[A-Z]?', message, re.IGNORECASE)
                if match:
                    extracted[field] = match.group().upper()
            
            elif field == "email":
                import re
                match = re.search(r'[\w.-]+@[\w.-]+\.\w+', message)
                if match:
                    extracted[field] = match.group()
            
            elif field == "phone" or field == "contact_phone":
                import re
                match = re.search(r'\d{3}-\d{3}-\d{4}', message)
                if match:
                    extracted[field] = match.group()
            
            elif field == "location" or field == "address":
                # Take the whole message as location if it looks like an address
                if len(message) > 5 and any(x in message_lower for x in ['street', 'ave', 'road', 'drive', 'king', 'queen']):
                    extracted[field] = message.strip()
            
            else:
                # For other fields, use the whole message if it seems relevant
                if len(message) > 2:
                    extracted[field] = message.strip()
        
        return extracted
    
    def _generate_prompt(self, state: ConversationState) -> str:
        """Generate a prompt asking for the missing fields"""
        if not state.missing_fields:
            return "I have all the information I need. Should I proceed?"
        
        # Ask for all missing fields at once
        field_labels = []
        for field in state.missing_fields:
            # Get the label from the schema (would need to pass schema in)
            field_labels.append(field.replace('_', ' ').title())
        
        if len(field_labels) == 1:
            prompt = f"Please provide: {field_labels[0]}"
        else:
            prompt = "Please provide the following information:\n"
            for i, label in enumerate(field_labels, 1):
                prompt += f"{i}. {label}\n"
        
        return prompt
    
    def _generate_summary(self, state: ConversationState) -> str:
        """Generate a summary of collected fields for confirmation"""
        summary = f"**Action: {state.action.replace('_', ' ').title()}**\n\n"
        summary += "Here's what I've collected:\n\n"
        
        for field_name, value in state.fields.items():
            label = field_name.replace('_', ' ').title()
            summary += f"• **{label}**: {value}\n"
        
        summary += "\nShould I proceed with submitting this?"
        
        return summary
    
    def confirm(self, session_id: str, confirmed: bool) -> Dict[str, Any]:
        """Handle user confirmation"""
        state = self.state_manager.get_state(session_id)
        if not state:
            return {"success": False, "message": "No active action to confirm"}
        
        if not confirmed:
            # User said no - cancel the action
            self.state_manager.clear_state(session_id)
            return {"success": True, "message": "Action cancelled. What else can I help you with?"}
        
        # User said yes - move to executing
        self.state_manager.set_state(session_id, "executing")
        return {
            "success": True,
            "ready_to_execute": True,
            "action": state.action,
            "fields": state.fields
        }
    
    def get_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an action"""
        state = self.state_manager.get_state(session_id)
        if not state:
            return None
        
        return state.to_dict()