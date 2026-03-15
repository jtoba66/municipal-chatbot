"""
Intent Detection Middleware
Intercepts messages and classifies them as QUESTION, ACTION_REQUEST, or GREETING
"""
import json
import re
from typing import Dict, Optional, Any
from pydantic import BaseModel


# Intent classification prompt
INTENT_PROMPT = """You are a municipal chatbot intent classifier for the Kitchener/Waterloo region.
Classify the user's message as one of:
- QUESTION: User wants information (garbage day, parking rules, facility locations, etc.)
- ACTION_REQUEST: User wants to DO something (report issue, book permit, pay ticket, schedule inspection)
- GREETING: User is saying hello or making small talk

For ACTION_REQUEST, also identify:
- action_type: The specific action (report_issue, book_parking_permit, pay_ticket, check_permit_status, schedule_inspection)
- city: Detected city (kitchener, waterloo, or unknown)
- fields: Any fields already provided by user

Respond ONLY in JSON format:
{{"intent": "QUESTION|ACTION_REQUEST|GREETING", "action_type": "...", "city": "...", "fields": {{}}}}"""


class IntentClassificationRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class IntentClassificationResponse(BaseModel):
    intent: str  # QUESTION, ACTION_REQUEST, GREETING
    action_type: Optional[str] = None
    city: Optional[str] = None
    fields: Dict[str, Any] = {}
    confidence: float = 1.0


def classify_intent_with_llm(message: str, llm) -> IntentClassificationResponse:
    """
    Use the LLM to classify the intent of a message.
    """
    # Build the prompt with few-shot examples
    prompt = f"""{INTENT_PROMPT}

Examples:
User: "When is my garbage collected?"
{{"intent": "QUESTION", "action_type": null, "city": null, "fields": {{}}}}

User: "I want to pay a parking ticket A123456"
{{"intent": "ACTION_REQUEST", "action_type": "pay_ticket", "city": "kitchener", "fields": {{"ticket_number": "A123456"}}}}

User: "There's a pothole on King Street"
{{"intent": "ACTION_REQUEST", "action_type": "report_issue", "city": "kitchener", "fields": {{"location": "King Street"}}}}

User: "book me a parking permit for the downtown garage"
{{"intent": "ACTION_REQUEST", "action_type": "book_parking_permit", "city": "kitchener", "fields": {{"location": "downtown"}}}}

User: "Hi there"
{{"intent": "GREETING", "action_type": null, "city": null, "fields": {{}}}}

User: "{message}"
"""
    
    try:
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        # Find JSON block in the response
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            # Try to find a complete JSON object
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                
                return IntentClassificationResponse(
                    intent=result.get("intent", "QUESTION"),
                    action_type=result.get("action_type"),
                    city=result.get("city", "unknown"),
                    fields=result.get("fields", {}),
                    confidence=0.9
                )
        
        # Fallback: try to parse the whole response
        result = json.loads(response_text)
        return IntentClassificationResponse(
            intent=result.get("intent", "QUESTION"),
            action_type=result.get("action_type"),
            city=result.get("city", "unknown"),
            fields=result.get("fields", {}),
            confidence=0.8
        )
    except Exception as e:
        print(f"Intent classification error: {e}")
        # Fallback to rule-based classification
        return fallback_intent_classification(message)


def fallback_intent_classification(message: str) -> IntentClassificationResponse:
    """
    Fallback rule-based intent classification if LLM fails.
    """
    message_lower = message.lower()
    
    # Action keywords
    action_keywords = {
        "pay_ticket": ["pay ticket", "pay my ticket", "pay parking", "pay a ticket"],
        "report_issue": ["report", "pothole", "graffiti", "issue", "problem", "complaint"],
        "book_parking_permit": ["parking permit", "book permit", "monthly parking", "parking pass"],
        "check_permit_status": ["permit status", "check permit", "building permit"],
        "schedule_inspection": ["schedule inspection", "book inspection", "inspection"]
    }
    
    # City keywords
    city_keywords = {
        "kitchener": ["kitchener"],
        "waterloo": ["waterloo"]
    }
    
    # Check for action intent
    for action, keywords in action_keywords.items():
        if any(kw in message_lower for kw in keywords):
            # Check for city
            city = "unknown"
            for city_name, city_kws in city_keywords.items():
                if any(ck in message_lower for ck in city_kws):
                    city = city_name
                    break
            
            # Extract simple fields using regex
            fields = {}
            
            # Ticket number pattern
            ticket_match = re.search(r'[A-Z]\d{5,}', message, re.IGNORECASE)
            if ticket_match:
                fields["ticket_number"] = ticket_match.group().upper()
            
            # License plate pattern
            plate_match = re.search(r'[A-Z]{1,3}\d{2,4}[A-Z]?', message, re.IGNORECASE)
            if plate_match:
                fields["license_plate"] = plate_match.group().upper()
            
            # Email pattern
            email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', message)
            if email_match:
                fields["email"] = email_match.group()
            
            return IntentClassificationResponse(
                intent="ACTION_REQUEST",
                action_type=action,
                city=city,
                fields=fields,
                confidence=0.7
            )
    
    # Check for greeting
    greeting_keywords = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    if any(gw in message_lower for gw in greeting_keywords):
        return IntentClassificationResponse(
            intent="GREETING",
            action_type=None,
            city=None,
            fields={},
            confidence=0.9
        )
    
    # Default to question
    return IntentClassificationResponse(
        intent="QUESTION",
        action_type=None,
        city=None,
        fields={},
        confidence=0.5
    )


# Simple keyword-based classifier for use without LLM
def classify_intent_simple(message: str) -> IntentClassificationResponse:
    """
    Simple rule-based intent classification without LLM.
    """
    return fallback_intent_classification(message)