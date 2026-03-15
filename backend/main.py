"""
Municipal Chatbot Backend - FastAPI + LangChain RAG Pipeline
Self-hosted with Ollama for local LLM inference

Kitchener/Waterloo region citizen services chatbot
"""
import os
# Disable CUDA - use CPU for embeddings
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import json
import re
import time
import requests
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain imports
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

# Try Ollama imports for embeddings only
try:
    from langchain_ollama import OllamaEmbeddings
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Always import fallback embeddings (available even if Ollama package is installed but service is down)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFaceHub
    
# Local imports
import database
import email_service

# Agentic Actions imports
from actions import ACTION_REGISTRY, get_action_schema, get_all_actions
from actions import FieldCollector, action_state_manager
from actions.intent_detector import (
    IntentClassificationRequest, 
    IntentClassificationResponse,
    classify_intent_with_llm,
    classify_intent_simple
)

# Load environment
load_dotenv()

# ==================== French Translation Support ====================

# Simple language detection based on common French words
FRENCH_INDICATORS = [
    'bonjour', 'merci', 's\'il vous plaît', 'excusez', 'je', 'vous', 'nous',
    'les', 'des', 'une', 'pour', 'dans', 'avec', 'sur', 'cette', 'ce',
    'être', 'avoir', 'faire', 'déchets', 'poubelle',
    'recyclage', 'stationnement', 'payer', 'horaire',
    'après-midi', 'aujourd\'hui', 'demain', 'problème', 'aide', 'renseignements'
]

# In-memory session language preferences
# Format: {session_id: "fr" | "en"}
session_language_preference = {}


def detect_language(message: str) -> str:
    """
    Detect if message is primarily French or English.
    Returns: "fr" for French, "en" for English
    """
    message_lower = message.lower()
    
    # Count French indicators
    french_count = sum(1 for word in FRENCH_INDICATORS if word in message_lower)
    
    # If more than 2 French indicators, likely French
    if french_count >= 2:
        return "fr"
    
    # Also check for French-specific punctuation and patterns
    french_patterns = ['répondez en français', 'en français', 'répondrez en français', 
                       'parlez français', 'français s\'il vous plaît', 'francais',
                       'je voudrais', 'pouvez-vous', 'auriez-vous', 'je suis à']
    
    for pattern in french_patterns:
        if pattern in message_lower:
            return "fr"
    
    # Check for French question marks and accents in words
    if '?' in message and french_count >= 1:
        return "fr"
    
    return "en"


def set_language_preference(session_id: str, language: str):
    """Set user's language preference for this session"""
    session_language_preference[session_id] = language
    print(f"Set language preference for session {session_id}: {language}")


def get_language_preference(session_id: str) -> str:
    """Get user's language preference for this session"""
    return session_language_preference.get(session_id, "en")


def clear_language_preference(session_id: str):
    """Clear user's language preference"""
    if session_id in session_language_preference:
        del session_language_preference[session_id]


def translate_to_french(text: str) -> str:
    """
    Translate English text to French using the LLM.
    """
    llm_model = get_llm()
    
    prompt = f"""Translate the following text to French. 
Only provide the translation, no explanations or additional text.

Text to translate:
{text}

French translation:"""
    
    try:
        response = llm_model.invoke(prompt)
        translation = response.content if hasattr(response, 'content') else str(response)
        
        # Clean up the response - remove any prefixes the LLM might add
        translation = translation.strip()
        
        # If the LLM added extra text, try to extract just the translation
        if '\n' in translation:
            # Take the first non-empty line
            lines = [line.strip() for line in translation.split('\n') if line.strip()]
            if lines:
                translation = lines[0]
        
        return translation
    except Exception as e:
        print(f"Translation error: {e}")
        # Return original text if translation fails
        return text


def translate_response(text: str, target_language: str) -> str:
    """
    Translate response to target language if needed.
    """
    if target_language == "fr":
        return translate_to_french(text)
    return text

app = FastAPI(title="Municipal Chatbot API", version="1.0.0")

# CORS - Allow all origins for testing
cors_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
DOCS_DIR = DATA_DIR / "documents"

# Ollama configuration (for embeddings only)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# OpenRouter configuration (for LLM)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

# Initialize database
try:
    database.init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")

# Global state
embeddings = None
vectorstore = None
llm = None


# ==================== LLM-Based Intent Classification ====================

def classify_intent(message: str, session_id: str = None) -> dict:
    """
    Use LLM to classify user intent and extract entities.
    Returns: {"intent": "garbage_collection|ticket_info|location|general_query|unknown", "entities": {...}}
    """
    llm_model = get_llm()
    
    # Load conversation history if session_id provided
    session_history = ""
    if session_id:
        session_history = get_session_history(session_id, limit=4)
    
    # Load user's saved address from profile (cross-session memory)
    user_address = ""
    if session_id:
        saved_address = get_user_profile_address(session_id)
        # Also check current session cache
        cached_address, _ = get_user_address(session_id)
        address = cached_address or saved_address
        if address:
            user_address = f"\nUser's saved address: {address}"
    
    history_section = f"\n\nPrevious conversation (for context):\n{session_history}" if session_history else ""
    user_section = f"\n\nUser profile info:{user_address}" if user_address else ""
    
    prompt = f"""Classify this municipal chatbot message and extract entities.{user_section}{history_section}

Current message: "{message}"

Options:
- garbage_collection: user asks about garbage, trash, waste, recycling, collection day, bin pickup
- ticket_info: user asks about parking ticket, fine, pay ticket, ticket status (Kitchener)
- ticket_info_waterloo: user asks about Waterloo parking ticket specifically
- location: user asks about location of facility (recycling depot, city hall, library, etc.)
- road_closures: user asks about road closures, street closures, road work, construction delays
- community_events: user asks about events, things to do, festivals, activities
- permit_status: user asks about building permits for a specific address
- general_query: any other question about city services

IMPORTANT: If the user refers to "my address", "my area", "for me", etc., use the previous conversation to find their address if provided.

If garbage_collection: extract "address" (street number + name like "110 Fergus Ave") - use from previous conversation if user said "my" or "for me"
If ticket_info: extract "ticket_number" (digits only)
If ticket_info_waterloo: extract "ticket_number" (digits only)
If location: extract "facility_type" (recycling, city hall, library, etc.)
If road_closures: no entities needed (get all closures)
If community_events: extract "city" (kitchener or waterloo), default to kitchener
If permit_status: extract "address" (street number + name like "110 Fergus Ave")
If no entity found, return null for that field.

Return ONLY valid JSON like this (no other text):
{{"intent": "garbage_collection", "entities": {{"address": "110 Fergus Ave"}}}}
{{"intent": "ticket_info", "entities": {{"ticket_number": "123456"}}}}
{{"intent": "ticket_info_waterloo", "entities": {{"ticket_number": "123456"}}}}
{{"intent": "location", "entities": {{"facility_type": "recycling"}}}}
{{"intent": "road_closures", "entities": {{}}}}
{{"intent": "community_events", "entities": {{"city": "kitchener"}}}}
{{"intent": "permit_status", "entities": {{"address": "110 Fergus Ave"}}}}
{{"intent": "general_query", "entities": {{}}}}
{{"intent": "unknown", "entities": {{}}}}
"""
    
    try:
        response = llm_model.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON from response
        # Find JSON in response (in case LLM adds extra text)
        import json
        import re
        
        # Try direct parse first
        try:
            result = json.loads(response_text.strip())
            return result
        except:
            pass
        
        # Try to find the FULL JSON object with nested entities - look for pattern with intent key
        # Match the outer braces while allowing nested braces for entities
        json_match = re.search(r'\{.*"intent".*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                if "intent" in result:
                    return result
            except:
                pass
        
        # Try to find JSON with intent at the start
        json_match2 = re.search(r'\{"intent":\s*"[^"]+",\s*"entities":\s*\{[^}]*\}\}', response_text)
        if json_match2:
            try:
                result = json.loads(json_match2.group())
                return result
            except:
                pass
        
        # Fallback to general query if parsing fails
        print(f"Warning: Could not parse LLM intent classification: {response_text}")
        return {"intent": "general_query", "entities": {}}
        
    except Exception as e:
        print(f"Error in intent classification: {e}")
        # Fallback to regex-based detection
        return {"intent": "fallback", "entities": {}}


# ==================== Address-Based Garbage Collection Lookup ====================

# Common Kitchener addresses mapped to collection days (for fallback)
# Format: normalized address -> collection day
# These are sample addresses - in production this would be populated from the Region's data
ADDRESS_COLLECTION_DAYS = {
    "110 fergus": "Tuesday",
    "110 fergus ave": "Tuesday",
    "200 king": "Monday",
    "200 king st": "Monday",
    "75 victoria": "Wednesday",
    "75 victoria st": "Wednesday",
    "50 queen": "Thursday",
    "50 queen st": "Thursday",
    "225 marsland": "Tuesday",
    "225 marsland dr": "Tuesday",
    "101 pfaff": "Wednesday",
    "101 pfaff way": "Wednesday",
    "425 king st": "Monday",
    "75 victoria st n": "Wednesday",
    "150 king st w": "Monday",
    "235 king st": "Monday",
    "50 weber st": "Thursday",
    "100 brava": "Friday",
    "99 st leger": "Wednesday",
    "99 reg st": "Wednesday",
}

# Days of week for reference
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# In-memory session storage for user address (enhanced to persist in DB for cross-session memory)
# Format: {session_id: {"address": "110 Fergus Ave", "collection_day": "Tuesday"}}
session_address_cache = {}


def get_user_profile_address(session_id: str) -> Optional[str]:
    """Get user's saved address from their profile (cross-session memory)"""
    try:
        session = database.get_session(session_id)
        if session and session.get('user_id'):
            return database.get_user_address(session['user_id'])
    except Exception as e:
        print(f"Warning: Could not get user profile address: {e}")
    return None


def save_user_address(session_id: str, address: str, collection_day: str = None):
    """Save user's address to session cache AND user profile (for cross-session memory)"""
    session_address_cache[session_id] = {
        "address": address,
        "collection_day": collection_day
    }
    print(f"Saved address for session {session_id}: {address}")
    
    # Also save to user profile for cross-session persistence
    try:
        session = database.get_session(session_id)
        if session and session.get('user_id'):
            database.update_user_address(session['user_id'], address)
            print(f"Saved address to user profile: {address}")
    except Exception as e:
        print(f"Warning: Could not save address to user profile: {e}")


def get_user_address(session_id: str) -> tuple:
    """Get user's saved address from session cache"""
    if session_id in session_address_cache:
        data = session_address_cache[session_id]
        return data.get("address"), data.get("collection_day")
    return None, None


def clear_user_address(session_id: str):
    """Clear user's saved address from session cache"""
    if session_id in session_address_cache:
        del session_address_cache[session_id]


# ==================== Session History ====================

def get_session_history(session_id: str, limit: int = 10) -> str:
    """
    Load previous conversation messages from the database.
    Returns formatted string of previous messages for LLM context.
    """
    try:
        messages = database.get_session_messages(session_id)
        if not messages:
            return ""
        
        # Limit to most recent messages
        recent_messages = messages[-limit:] if len(messages) > limit else messages
        
        # Format as conversation history
        history_parts = []
        for msg in recent_messages:
            role = "User" if msg['role'] == 'user' else "Assistant"
            content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
            history_parts.append(f"{role}: {content}")
        
        return "\n".join(history_parts)
    except Exception as e:
        print(f"Warning: Could not load session history: {e}")
        return ""


# ==================== Location Finder ====================

# Facility data for location finder
FACILITIES = {
    # Recycling & Waste
    "recycling depot": {
        "name": "Kitchener Waste Management Facility",
        "address": "101 Shoemaker St, Kitchener",
        "hours": "Mon-Sat 8am-5pm",
        "description": "Drop off recycling, household waste, and green bin materials."
    },
    "recycling": {
        "name": "Kitchener Waste Management Facility",
        "address": "101 Shoemaker St, Kitchener",
        "hours": "Mon-Sat 8am-5pm",
        "description": "Drop off recycling, household waste, and green bin materials."
    },
    "electronics": {
        "name": "Kitchener Waste Management Facility",
        "address": "101 Shoemaker St, Kitchener",
        "hours": "Mon-Sat 8am-5pm",
        "description": "Accepts e-waste including computers, TVs, phones, and batteries."
    },
    "e-waste": {
        "name": "Kitchener Waste Management Facility",
        "address": "101 Shoemaker St, Kitchener",
        "hours": "Mon-Sat 8am-5pm",
        "description": "Accepts e-waste including computers, TVs, phones, and batteries."
    },
    "computer": {
        "name": "Kitchener Waste Management Facility",
        "address": "101 Shoemaker St, Kitchener",
        "hours": "Mon-Sat 8am-5pm",
        "description": "Accepts e-waste including computers, TVs, phones, and batteries."
    },
    "old electronics": {
        "name": "Kitchener Waste Management Facility",
        "address": "101 Shoemaker St, Kitchener",
        "hours": "Mon-Sat 8am-5pm",
        "description": "Accepts e-waste including computers, TVs, phones, and batteries."
    },
    "landfill": {
        "name": "Waterloo Waste Management Facility",
        "address": "1001 Erb St, Waterloo",
        "hours": "Mon-Sat 8am-5pm",
        "description": "Regional landfill for household waste. Fees apply for non-residential waste."
    },
    "waste facility": {
        "name": "Waterloo Waste Management Facility",
        "address": "1001 Erb St, Waterloo",
        "hours": "Mon-Sat 8am-5pm",
        "description": "Regional landfill for household waste. Fees apply for non-residential waste."
    },
    "transfer station": {
        "name": "Cambridge Waste Management Facility",
        "address": "1500 Dickson St, Cambridge",
        "hours": "Mon-Sat 8am-5pm",
        "description": "Transfer station for household waste and recycling."
    },
    # City Services
    "city hall": {
        "name": "City Hall Kitchener",
        "address": "200 King St W, Kitchener",
        "hours": "Mon-Fri 8:30am-4:30pm",
        "description": "Main city office for permits, taxes, and city services."
    },
    "city hall waterloo": {
        "name": "City Hall Waterloo",
        "address": "100 Regina St S, Waterloo",
        "hours": "Mon-Fri 8:30am-4:30pm",
        "description": "City office for Waterloo residents."
    },
    # Recreation
    "community centre": {
        "name": "Kitchener Recreation",
        "address": "Multiple locations",
        "hours": "Varies by location",
        "description": "Visit kitchener.ca/recreation for locations and programs."
    },
    "recreation": {
        "name": "Kitchener Recreation",
        "address": "Multiple locations",
        "hours": "Varies by location",
        "description": "Visit kitchener.ca/recreation for locations and programs."
    },
    "pool": {
        "name": "Kitchener Recreation",
        "address": "Multiple locations",
        "hours": "Varies by location",
        "description": "Visit kitchener.ca/recreation for pool locations and schedules."
    },
    "arena": {
        "name": "Kitchener Recreation",
        "address": "Multiple locations",
        "hours": "Varies by location",
        "description": "Visit kitchener.ca/recreation for arena locations and schedules."
    },
    "library": {
        "name": "Kitchener Public Library",
        "address": "85 Queen St N, Kitchener",
        "hours": "Mon-Thu 9am-8pm, Fri-Sat 9am-5pm, Sun 12pm-4pm",
        "description": "Public library with books, media, computers, and programs."
    },
}


def is_location_query(message: str) -> bool:
    """Detect if a message is asking about a location"""
    message_lower = message.lower()
    
    # Keywords that indicate location query
    location_keywords = ["where", "nearest", "location", "find", "address", "directions", "drop off", "take my"]
    facility_keywords = list(FACILITIES.keys())
    
    # Check for location question patterns
    location_patterns = [
        r"where (is|can|do|does)",
        r"where('s| is) the",
        r"where can i",
        r"is there a",
        r"is there an",
        r"is there any",
        r"nearest",
        r"closest",
        r"drop off",
        r"how do i get to",
        r"directions to",
    ]
    
    has_location_kw = any(kw in message_lower for kw in location_keywords)
    has_facility = any(fac in message_lower for fac in facility_keywords)
    has_location_pattern = any(re.search(pat, message_lower) for pat in location_patterns)
    
    return (has_location_kw and has_facility) or has_location_pattern


def extract_facility_type(message: str) -> Optional[str]:
    """Extract the facility type from the message"""
    message_lower = message.lower()
    
    # Priority: check for multi-word matches first
    multi_word_facilities = [
        "city hall waterloo", "old electronics", "waste facility", 
        "transfer station", "community centre", "city hall"
    ]
    
    for facility in multi_word_facilities:
        if facility in message_lower:
            return facility
    
    # Then check single-word facilities
    single_word_facilities = [
        "recycling", "electronics", "e-waste", "computer", "landfill",
        "city hall", "recreation", "pool", "arena", "library"
    ]
    
    for facility in single_word_facilities:
        if facility in message_lower:
            return facility
    
    return None


def get_location_response(facility_type: str) -> str:
    """Get formatted response for a facility type"""
    if facility_type and facility_type in FACILITIES:
        facility = FACILITIES[facility_type]
        return (f"**{facility['name']}**\n"
                f"📍 {facility['address']}\n"
                f"🕐 Hours: {facility['hours']}\n"
                f"ℹ️ {facility['description']}")
    else:
        return ("I couldn't find that facility type. "
                "Try asking about recycling depots, landfills, City Hall, community centres, or libraries. "
                "For more options, visit kitchener.ca or call 519-741-2345.")


# ==================== Property Tax Lookup ====================

# Sample property tax data for common Kitchener addresses
PROPERTY_TAX_SAMPLE = {
    "110 fergus ave": {
        "estimated": "$3,200-3,500/year",
        "due_dates": "Mar 2, May 1, Jul 2, Sep 1, Oct 1"
    },
    "200 king st": {
        "estimated": "$4,100-4,400/year",
        "due_dates": "Mar 2, May 1, Jul 2, Sep 1, Oct 1"
    },
    "75 victoria st": {
        "estimated": "$2,900-3,100/year",
        "due_dates": "Mar 2, May 1, Jul 2, Sep 1, Oct 1"
    },
    "50 queen st": {
        "estimated": "$3,500-3,700/year",
        "due_dates": "Mar 2, May 1, Jul 2, Sep 1, Oct 1"
    },
    "225 marsland dr": {
        "estimated": "$3,300-3,500/year",
        "due_dates": "Mar 2, May 1, Jul 2, Sep 1, Oct 1"
    },
    "101 pfaff way": {
        "estimated": "$3,800-4,000/year",
        "due_dates": "Mar 2, May 1, Jul 2, Sep 1, Oct 1"
    },
}

def is_property_tax_query(message: str) -> bool:
    """Detect if a message is asking about property taxes"""
    message_lower = message.lower()
    
    # Keywords that indicate property tax query
    tax_keywords = [
        "property tax", "property taxes", "property tax amount",
        "tax amount", "tax due", "taxes due", "how much tax",
        "annual tax", "tax bill", "taxes owed", "pay tax"
    ]
    
    # Check if message contains property tax keywords
    return any(kw in message_lower for kw in tax_keywords)


def lookup_property_tax(address: str) -> Optional[dict]:
    """Look up property tax info for an address"""
    if not address:
        return None
    
    # Normalize address for lookup
    address_normalized = address.lower().strip()
    
    # Try exact match first
    for addr_key, tax_info in PROPERTY_TAX_SAMPLE.items():
        if addr_key in address_normalized or address_normalized in addr_key:
            return tax_info
    
    # Try partial match on street name
    address_parts = address_normalized.split()
    if len(address_parts) >= 2:
        street_num = address_parts[0]
        street_name = address_parts[1]
        
        for addr_key, tax_info in PROPERTY_TAX_SAMPLE.items():
            if street_name in addr_key:
                return tax_info
    
    return None


def get_property_tax_response(address: Optional[str] = None) -> str:
    """Generate response for property tax query"""
    if address:
        tax_info = lookup_property_tax(address)
        
        if tax_info:
            return (f"Based on your address ({address}), your estimated property tax is **{tax_info['estimated']}**. "
                    f"Due dates are: {tax_info['due_dates']}. "
                    f"You can pay online at kitchener.ca/taxes, by phone at 519-741-2345, or in person at City Hall.")
        else:
            return (f"I don't have the exact tax amount for {address} in my sample data. "
                    f"Would you like me to provide the payment due dates and methods for Kitchener property taxes? "
                    f"You can also check your property tax at kitchener.ca/taxes or call 519-741-2345.")
    else:
        # No address provided - offer to help with dates and methods
        return ("To look up your specific property tax amount, I'd need your address. "
                "In the meantime, here's what you need to know about Kitchener property taxes:\n\n"
                "📅 **Due Dates**: March 2, May 1, July 2, September 1, and October 1\n\n"
                "💳 **Payment Methods**:\n"
                "- Online: kitchener.ca/taxes\n"
                "- Phone: 519-741-2345\n"
                "- In Person: City Hall, 200 King St W\n"
                "- By Mail: City of Kitchener, PO Box 1118, Kitchener ON N2G 4G7\n\n"
                "Would you like to provide your address for a more specific estimate?")


# ==================== Parking Ticket Lookup ====================

def is_ticket_query(message: str) -> bool:
    """Detect if a message is asking about parking tickets"""
    message_lower = message.lower()
    
    # Keywords that indicate parking ticket query
    ticket_keywords = ["ticket", "parking ticket", "parking fine", "fine", "infraction"]
    
    # Payment-related keywords
    payment_keywords = ["pay", "payment", "pay online", "how much", "cost", "fee"]
    
    # Status-related keywords  
    status_keywords = ["status", "check", "look up", "find", "search", "info", "details"]
    
    # Check if message contains ticket keywords
    has_ticket = any(kw in message_lower for kw in ticket_keywords)
    
    # Also check for common ticket question patterns
    ticket_patterns = [
        r"my ticket",
        r"ticket #?",
        r"parking ticket",
        r"i have a ticket",
        r"ticket number",
        r"ticket status",
        r"how do i pay",
        r"how much.*ticket",
        r"pay.*ticket",
    ]
    has_ticket_pattern = any(re.search(pat, message_lower) for pat in ticket_patterns)
    
    return has_ticket or has_ticket_pattern


def extract_ticket_number(message: str) -> Optional[str]:
    """Extract ticket number from message (6-8 digits)"""
    # Pattern: 6-8 digit ticket number, optionally with prefix like ABC or #
    # Examples: 123456, 12345678, ABC123456, #123456
    patterns = [
        r'\b([A-Z]{1,3}?\d{6,8})\b',  # ABC123456 or 123456
        r'#(\d{6,8})\b',               # #123456
        r'ticket[:\s#]+(\d{6,8})',     # ticket 123456 or ticket: 123456
        r'#?\s*(\d{6,8})\b',           # standalone 6-8 digits
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def get_ticket_response(ticket_number: Optional[str] = None) -> str:
    """Generate response for ticket query"""
    if ticket_number:
        return (f"I found your ticket #{ticket_number}. You can pay it online at **kitchener.ca/paytickets**, "
                f"by phone at **519-741-2345**, or in person at **City Hall, 200 King St W** (open Mon-Fri 8:30 AM - 4:30 PM). "
                f"Please have your ticket number ready when contacting us.")
    else:
        return ("To pay a parking ticket, visit **kitchener.ca/paytickets**, "
                "call **519-741-2345**, or visit **City Hall, 200 King St W** in person. "
                "You'll need your ticket number to look up or pay your fine. "
                "If you have a ticket number, you can ask me like 'What's my ticket status? #123456'")


def is_address_query(message: str) -> bool:
    """Detect if a message is asking about garbage collection for a specific address"""
    message_lower = message.lower()
    
    # Keywords that indicate garbage/waste collection query
    garbage_keywords = ["garbage", "trash", "waste", "collection", "pickup", "bin", "recycling", "green bin", "organic"]
    
    # Check if message contains garbage-related terms
    has_garbage = any(kw in message_lower for kw in garbage_keywords)
    
    # Check for street number pattern (e.g., "110 Fergus")
    has_street_number = bool(re.search(r'\b\d+\s+[a-zA-Z]{2,}', message))
    
    # Check for "my" patterns - user asking about their own address
    # NEW: Detect "my home", "my address", "for me", "my garbage"
    my_patterns = [
        r"\bmy\s+home\b",
        r"\bmy\s+address\b",
        r"\bmy\s+garbage\b",
        r"\bmy\s+trash\b",
        r"\bmy\s+area\b",
        r"\bfor\s+me\b",
        r"\bfor\s+my\b",
        r"\bwhen\s+is\s+.*\s+collected\s+for\s+me\b",
        r"\bwhat('s| is)\s+my\s+collection\b",
    ]
    has_my_pattern = any(re.search(pat, message_lower) for pat in my_patterns)
    
    # Check for common address question patterns
    address_patterns = [
        r"i live(at| in)?\s",
        r"at my",
        r"what('s| is) my garbage",
        r"when (is|does) .* collected",
        r"collection day",
        r"\bwhat day\b",
        r"\bwhen day\b",
    ]
    has_address_pattern = any(re.search(pat, message_lower) for pat in address_patterns)
    
    # It's an address query if:
    # 1. Has garbage keywords AND (has address pattern OR has street number OR has my_pattern)
    # OR 2. Just a bare address (street number + street name) - user might be responding to "what's your address?"
    # Also include cases like "I stay at 110 fergus avenue" (up to 8 words)
    is_bare_address = has_street_number and len(message.split()) <= 8 and not has_garbage
    
    return has_garbage and (has_address_pattern or has_street_number or has_my_pattern) or is_bare_address


def needs_address_clarification(message: str) -> bool:
    """Check if user is asking about their garbage but didn't provide a specific address"""
    message_lower = message.lower()
    
    # First check if it's an address query
    if not is_address_query(message):
        return False
    
    # Now check if they provided a specific address
    address = extract_address(message)
    if address:
        return False  # They provided an address
    
    # Check for "my" patterns that indicate they want personalized info but didn't give address
    my_patterns = [
        r"\bmy\s+home\b",
        r"\bmy\s+address\b",
        r"\bmy\s+garbage\b",
        r"\bmy\s+trash\b",
        r"\bfor\s+me\b",
        r"\bfor\s+my\b",
        r"\bwhen\s+is\s+.*\s+collected\s+for\s+me\b",
        r"\bwhat('s| is)\s+my\s+collection\b",
        r"\bwhen\s+is\s+my\s+garbage\b",
        r"\bwhen\s+is\s+my\s+trash\b",
    ]
    has_my_pattern = any(re.search(pat, message_lower) for pat in my_patterns)
    
    return has_my_pattern


def extract_address(message: str) -> Optional[str]:
    """Extract street address from message"""
    message_lower = message.lower()
    
    # Pattern: number + street name (e.g., "110 Fergus Ave", "225 Marsland Drive")
    # Match patterns like: 110 fergus, 110 fergus ave, 225 marsland dr
    patterns = [
        r'\b(\d+)\s+([a-zA-Z]+(?:\s+(?:ave|avenue|st|street|dr|drive|way|blvd|road|rd|court|ct|place|pl))?)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            street_num = match.group(1)
            street_name = match.group(2).strip()
            return f"{street_num} {street_name}"
    
    return None


def lookup_garbage_collection_day(address: str) -> Optional[str]:
    """Look up garbage collection day for an address using Region of Waterloo API or local fallback"""
    if not address:
        return None
    
    # Normalize address for lookup
    address_normalized = address.lower().strip()
    
    # Try Region of Waterloo Open Data API first
    try:
        # The Region of Waterloo has an open data portal with waste collection info
        # Using their ArcGIS Open Data API
        base_url = "https://open-kitchenergis.opendata.arcgis.com/api/v3"
        
        # Search for address in the waste collection dataset
        # This is a simplified query - in production you'd use the full address lookup
        search_url = f"{base_url}/datasets/PTKS::waste-collection-schedule/execute"
        
        # Try alternate endpoint format
        params = {
            "where": f"address LIKE '%{address}%'",
            "outFields": "*",
            "f": "json"
        }
        
        # Try direct query to the dataset
        dataset_url = "https://services1.arcgis.com/eDxsOhzfD2Mh2d7i/arcgis/rest/services/Address_Point/FeatureServer/0/query"
        test_params = {
            "where": f"street_num='{address.split()[0]}' AND street_name LIKE '%{address.split()[1]}%'",
            "outFields": "*",
            "f": "json"
        }
        
        response = requests.get(dataset_url, params=test_params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("features") and len(data["features"]) > 0:
                # Extract collection info if available
                attrs = data["features"][0].get("attributes", {})
                collection_day = attrs.get("collection_day") or attrs.get("garbage_day")
                if collection_day:
                    return collection_day
    except Exception as e:
        print(f"API lookup failed: {e}")
    
    # Fallback to local lookup table
    # Try exact match first
    for addr_key, day in ADDRESS_COLLECTION_DAYS.items():
        if addr_key in address_normalized:
            return day
    
    # Try partial match on street name
    address_parts = address_normalized.split()
    if len(address_parts) >= 2:
        street_num = address_parts[0]
        street_name = address_parts[1]
        
        for addr_key, day in ADDRESS_COLLECTION_DAYS.items():
            if street_name in addr_key:
                return day
    
    return None


def get_generic_garbage_info() -> str:
    """Get generic garbage collection info for Kitchener"""
    return ("In Kitchener, garbage is collected weekly. Your collection day depends on your address. "
            "To find your specific day, please provide your street address (e.g., '110 Fergus Ave'). "
            "You can also check at kitchener.ca/waste or call 519-741-2345.")


def get_embeddings():
    """Get or create embeddings instance"""
    global embeddings
    if embeddings is None:
        if OLLAMA_AVAILABLE:
            try:
                embeddings = OllamaEmbeddings(
                    model="nomic-embed-text",
                    base_url=OLLAMA_BASE_URL
                )
                # Test connection
                embeddings.embed_query("test")
            except Exception as e:
                print(f"Ollama embeddings unavailable: {e}. Using HuggingFace fallback.")
                embeddings = None
        
        if embeddings is None:
            # Fallback to sentence-transformers
            try:
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'}
                )
            except Exception as e:
                print(f"Error creating embeddings: {e}")
                raise HTTPException(503, f"Embeddings unavailable: {e}")
    return embeddings


def get_llm():
    """Get or create LLM instance using OpenRouter"""
    global llm
    
    if llm is None:
        # Use OpenRouter for LLM responses
        try:
            llm = ChatOpenAI(
                model=OPENROUTER_MODEL,
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.3,
                timeout=120,
                max_tokens=500
            )
            # Test connection with a simple prompt
            llm.invoke("Hello")
            print(f"OpenRouter connected successfully with model: {OPENROUTER_MODEL}")
        except Exception as e:
            print(f"OpenRouter unavailable: {e}")
            raise HTTPException(503, f"OpenRouter LLM unavailable: {str(e)}")
    
    return llm


def get_vectorstore():
    """Get or create Chroma vectorstore"""
    global vectorstore
    if vectorstore is None:
        emb = get_embeddings()
        if CHROMA_DIR.exists() and list(CHROMA_DIR.iterdir()):
            try:
                vectorstore = Chroma(
                    persist_directory=str(CHROMA_DIR), 
                    embedding_function=emb
                )
            except Exception as e:
                print(f"Error loading existing vectorstore: {e}")
                # Try to rebuild
                vectorstore = None
        
        if vectorstore is None:
            # Rebuild from documents
            try:
                rebuild_index_sync()
                vectorstore = Chroma(
                    persist_directory=str(CHROMA_DIR), 
                    embedding_function=emb
                )
            except Exception as e:
                raise HTTPException(
                    404, 
                    f"Knowledge base not initialized. Error: {str(e)}. POST /rebuild-index to create it."
                )
    return vectorstore


def rebuild_index_sync():
    """Synchronous version of index rebuild"""
    emb = get_embeddings()
    
    # Load all text files from documents dir
    docs = []
    if DOCS_DIR.exists():
        for txt_file in DOCS_DIR.glob("*.txt"):
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                loaded_docs = loader.load()
                for doc in loaded_docs:
                    doc.metadata = {"source": f"local:{txt_file.name}"}
                docs.extend(loaded_docs)
            except Exception as e:
                print(f"Error loading {txt_file}: {e}")
    
    if not docs:
        # Create sample documents for demo
        sample_docs = [
            Document(
                page_content="Garbage is collected weekly. Place bins at the curb by 7 AM on your collection day. Check your schedule at kitchener.ca/waste",
                metadata={"source": "local:sample_garbage.txt"}
            ),
            Document(
                page_content="Parking tickets can be paid online at kitchener.ca/parking or in person at City Hall. Payment deadline is 30 days.",
                metadata={"source": "local:sample_parking.txt"}
            ),
            Document(
                page_content="Building permits are required for renovations over $10,000. Apply at kitchener.ca/permits or visit City Hall.",
                metadata={"source": "local:sample_permits.txt"}
            )
        ]
        docs = sample_docs
    
    # Split documents
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splits = splitter.split_documents(docs)
    
    # Create and persist vectorstore
    global vectorstore
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=emb,
        persist_directory=str(CHROMA_DIR)
    )
    vectorstore.persist()
    
    return len(docs), len(splits)


# ==================== Municipal Portal Automation ====================
# Browser automation for public municipal portals (no login required)

# --- Road Closures ---
async def get_road_closures() -> List[dict]:
    """
    Get current road closures from Region of Waterloo open data.
    Returns list of active road closures.
    """
    try:
        # Try Region of Waterloo open data API for traffic closures
        url = "https://services1.arcgis.com/eDxsOhzfD2Mh2d7i/ArcGIS/rest/services/Traffic_Closures/FeatureServer/0/query"
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "json"
        }
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                closures = []
                for feature in data.get("features", [])[:20]:  # Limit to 20
                    attrs = feature.get("attributes", {})
                    closures.append({
                        "street": attrs.get("street_name", "Unknown"),
                        "location": attrs.get("location", ""),
                        "type": attrs.get("closure_type", "Road Closure"),
                        "start_date": attrs.get("start_date", ""),
                        "end_date": attrs.get("end_date", ""),
                        "reason": attrs.get("reason", "Construction"),
                        "detour": attrs.get("detour_available", False)
                    })
                return closures
    except Exception as e:
        print(f"Road closures API error: {e}")
    
    # Fallback: try Waterloo website
    try:
        url = "https://www.waterloo.ca/roads-and-cycling/check-road-sidewalk-and-trail-closures/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try to find closure tables
            tables = soup.find_all('table')
            closures = []
            for table in tables[:3]:  # First 3 tables
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:5]:  # 5 rows per table
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        closures.append({
                            "street": cells[0].get_text(strip=True),
                            "location": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                            "type": "Road Closure",
                            "start_date": "",
                            "end_date": "",
                            "reason": cells[-1].get_text(strip=True) if cells else "Construction",
                            "detour": False
                        })
            if closures:
                return closures
    except Exception as e:
        print(f"Road closures fallback error: {e}")
    
    # Return sample data if both fail
    return [
        {"street": "King Street", "location": "Between Queen and Wellington", "type": "Road Closure", "start_date": "2025-03-10", "end_date": "2025-03-25", "reason": "Water main repair", "detour": True},
        {"street": "University Avenue", "location": "Near Phillip Street", "type": "Lane Reduction", "start_date": "2025-03-15", "end_date": "2025-03-30", "reason": "Paving", "detour": False}
    ]


# --- Community Events ---
async def get_community_events(city: str = "kitchener") -> List[dict]:
    """
    Get upcoming community events from Kitchener or Waterloo.
    """
    city = city.lower()
    
    if city == "waterloo":
        url = "https://www.waterloo.ca/create-waterloo/city-events/"
    else:
        # Default to Kitchener
        url = "https://www.kitchener.ca/en/things-to-do.aspx"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'lxml')
            
            events = []
            
            # Look for event listings (various selectors)
            event_containers = soup.find_all(['div', 'li'], class_=lambda x: x and ('event' in str(x).lower() if x else False))
            
            # Also look for items in lists
            if not event_containers:
                event_containers = soup.find_all('li')
            
            for item in event_containers[:10]:
                text = item.get_text(strip=True)
                if len(text) > 30:  # Filter out short items
                    # Try to extract event details
                    title = text[:100]
                    events.append({
                        "title": title,
                        "date": "",
                        "location": "",
                        "description": text[:200]
                    })
            
            # If still no events, try finding h3/h4 headings
            if not events:
                headings = soup.find_all(['h3', 'h4'])
                for heading in headings[:10]:
                    text = heading.get_text(strip=True)
                    if len(text) > 10:
                        events.append({
                            "title": text,
                            "date": "",
                            "location": "",
                            "description": ""
                        })
            
            if events:
                return events[:10]  # Limit to 10 events
                
    except Exception as e:
        print(f"Community events error: {e}")
    
    # Return sample data if scraping fails
    if city == "waterloo":
        return [
            {"title": "Waterloo Park Summer Concert Series", "date": "Every Friday in July", "location": "Waterloo Park", "description": "Free live music performances"},
            {"title": "Farmers Market", "date": "Saturdays 7am-3pm", "location": "Waterloo Town Square", "description": "Local produce and artisan goods"},
            {"title": "Canada Day Celebration", "date": "July 1st", "location": "Waterloo Park", "description": "Festivities and fireworks"}
        ]
    else:
        return [
            {"title": "Kitchener Market", "date": "Saturdays 7am-3pm", "location": "Kitchener Market", "description": "Farmers market and local vendors"},
            {"title": "Doors Open Kitchener", "date": "Annually in September", "location": "Various locations", "description": "Free access to historic buildings"},
            {"title": "Kitchener Blues Festival", "date": "August", "location": "Downtown Kitchener", "description": "Live blues music"}
        ]


# --- Permit Status (Kitchener) ---
async def get_permit_status(address: str) -> dict:
    """
    Get building permit status for a Kitchener address.
    Uses the open data API.
    """
    if not address:
        return {"status": "error", "message": "Address required"}
    
    try:
        # Normalize address for API query
        address_parts = address.lower().split()
        if len(address_parts) >= 2:
            street_num = address_parts[0]
            street_name = address_parts[1]
        else:
            street_num = address
            street_name = ""
        
        # Try Kitchener Open Data API for building permits
        url = "https://services1.arcgis.com/eDxsOhzfD2Mh2d7i/ArcGIS/rest/services/Building_Permits/FeatureServer/0/query"
        
        # Try to find permits for this street number
        params = {
            "where": f"address LIKE '%{street_num}%{street_name}%' OR civic_number = '{street_num}'",
            "outFields": "*",
            "f": "json",
            "resultRecordCount": 10
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            
            if features:
                permits = []
                for feature in features:
                    attrs = feature.get("attributes", {})
                    permits.append({
                        "permit_number": attrs.get("permit_number", ""),
                        "address": attrs.get("address", address),
                        "permit_type": attrs.get("permit_type", ""),
                        "status": attrs.get("status", ""),
                        "issue_date": attrs.get("issue_date", ""),
                        "description": attrs.get("description", "")
                    })
                
                return {
                    "status": "found",
                    "address": address,
                    "permits": permits
                }
        
        # Try alternate API endpoint
        alt_url = "https://open-kitchenergis.opendata.arcgis.com/api/v3/datasets/PTKS::building-permits/execute"
        params2 = {
            "where": f"address LIKE '%{address}%'",
            "outFields": "*",
            "f": "json"
        }
        
        response2 = requests.get(alt_url, params=params2, timeout=15)
        # If API doesn't return data, return not found
        
    except Exception as e:
        print(f"Permit status error: {e}")
    
    # Sample response for demo
    return {
        "status": "not_found",
        "address": address,
        "message": "No active permits found for this address. Permits may be available at kitchener.ca/maps"
    }


# --- Parking Ticket (Waterloo) ---
async def get_waterloo_parking_ticket(ticket_number: str) -> dict:
    """
    Look up a parking ticket from Waterloo's AMPS system.
    Requires ticket number and license plate for verification.
    """
    if not ticket_number:
        return {"status": "error", "message": "Ticket number required"}
    
    try:
        # Try Waterloo AMPS payment lookup
        url = "https://amps.waterloo.ca/pay"
        
        # We can try to access the lookup endpoint
        lookup_url = "https://amps.waterloo.ca/api/parking/ticket"
        
        # Try POST to lookup ticket
        response = requests.post(
            lookup_url,
            json={"ticketNumber": ticket_number},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "found",
                "ticket_number": ticket_number,
                "amount": data.get("amount", ""),
                "status": data.get("status", ""),
                "due_date": data.get("due_date", "")
            }
            
    except Exception as e:
        print(f"Parking ticket API error: {e}")
    
    # Return info about how to pay
    return {
        "status": "lookup_unavailable",
        "ticket_number": ticket_number,
        "message": "To look up your Waterloo parking ticket, please visit https://amps.waterloo.ca/pay",
        "payment_options": [
            "Online: https://amps.waterloo.ca/pay",
            "Phone: 519-746-XXXX",
            "In Person: City of Waterloo, 100 Regina St S"
        ]
    }


# --- Request/Response Models for Municipal Services ---

class PermitStatusRequest(BaseModel):
    address: str


class PermitStatusResponse(BaseModel):
    status: str
    address: str
    permits: Optional[List[dict]] = None
    message: Optional[str] = None


class ParkingTicketRequest(BaseModel):
    ticket_number: str


class ParkingTicketResponse(BaseModel):
    status: str
    ticket_number: str
    amount: Optional[str] = None
    message: Optional[str] = None
    payment_options: Optional[List[str]] = None


class RoadClosuresResponse(BaseModel):
    status: str
    count: int
    closures: List[dict]


class CommunityEventsResponse(BaseModel):
    status: str
    city: str
    count: int
    events: List[dict]


# ==================== Request/Response Models ====================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    include_sources: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[dict]] = None
    session_id: str
    response_time_ms: int


class CreateSessionRequest(BaseModel):
    name: str
    email: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    started_at: str
    ended_at: Optional[str] = None
    messages: List[dict] = []


class EndSessionResponse(BaseModel):
    status: str
    session_id: str
    email_sent: bool
    message_count: int


class HealthResponse(BaseModel):
    status: str
    ollama: str
    db: str
    kb_docs: int


class RebuildResponse(BaseModel):
    status: str
    documents: int
    chunks: int


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: Optional[int] = None
    rating: int  # 1-5 scale (1=thumbs down, 5=thumbs up)
    feedback_text: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str
    feedback_id: int


# ==================== API Endpoints ====================

@app.get("/", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with service status"""
    openrouter_status = "disconnected"
    kb_docs = 0
    
    # Check OpenRouter
    try:
        test_llm = get_llm()
        test_llm.invoke("test")
        openrouter_status = "connected"
    except Exception as e:
        openrouter_status = f"error: {str(e)[:50]}"
    
    # Count knowledge base docs
    try:
        vs = get_vectorstore()
        kb_docs = vs._collection.count()
    except:
        pass
    
    # Database stats
    db_status = "connected"
    try:
        stats = database.get_stats()
    except:
        db_status = "error"
    
    return HealthResponse(
        status="running",
        ollama=openrouter_status,
        db=db_status,
        kb_docs=kb_docs
    )


@app.post("/api/session", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new chat session with optional user info"""
    try:
        user_id = None
        user_address = None
        
        # Create or get user
        if request.email:
            existing_user = database.get_user_by_email(request.email)
            if existing_user:
                user_id = existing_user['id']
                user_address = existing_user.get('address')
            else:
                user_id = database.create_user(request.name, request.email)
        
        # Create session
        session_id = database.create_session(user_id=user_id)
        
        # If user has a saved address, load it into session cache
        if user_id and user_address:
            collection_day = lookup_garbage_collection_day(user_address)
            save_user_address(session_id, user_address, collection_day)
            print(f"Loaded saved address for user {user_id}: {user_address}")
        
        session = database.get_session(session_id)
        
        return SessionResponse(
            session_id=session['session_id'],
            user_id=session['user_id'],
            user_name=request.name,
            user_email=request.email,
            started_at=session['started_at'],
            messages=[]
        )
        
    except Exception as e:
        raise HTTPException(500, f"Error creating session: {str(e)}")


@app.get("/api/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session details and message history"""
    try:
        session = database.get_session(session_id)
        
        if not session:
            raise HTTPException(404, "Session not found")
        
        messages = database.get_session_messages(session_id)
        
        return SessionResponse(
            session_id=session['session_id'],
            user_id=session.get('user_id'),
            user_name=session.get('user_name'),
            user_email=session.get('user_email'),
            started_at=session['started_at'],
            ended_at=session.get('ended_at'),
            messages=messages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error getting session: {str(e)}")


@app.post("/api/session/{session_id}/end", response_model=EndSessionResponse)
async def end_session(session_id: str):
    """End a chat session and optionally send email summary"""
    try:
        session = database.get_session(session_id)
        
        if not session:
            raise HTTPException(404, "Session not found")
        
        # Get all messages
        messages = database.get_session_messages(session_id)
        
        # End the session
        database.end_session(session_id)
        
        # Send email if user provided email
        email_sent = False
        user_email = session.get('user_email')
        user_name = session.get('user_name') or "Valued Resident"
        
        if user_email:
            email_sent = email_service.send_conversation_summary(
                to_email=user_email,
                user_name=user_name,
                session_id=session_id,
                messages=messages,
                started_at=session['started_at'],
                ended_at=datetime.now().isoformat()
            )
        
        return EndSessionResponse(
            status="ended",
            session_id=session_id,
            email_sent=email_sent,
            message_count=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error ending session: {str(e)}")


class AddressRequest(BaseModel):
    address: str


class AddressResponse(BaseModel):
    status: str
    address: str
    collection_day: Optional[str] = None


@app.post("/api/session/{session_id}/address", response_model=AddressResponse)
async def save_session_address(session_id: str, request: AddressRequest):
    """Save user's address for garbage collection lookup"""
    try:
        # Validate address by looking up collection day
        collection_day = lookup_garbage_collection_day(request.address)
        
        # Save to session cache
        save_user_address(session_id, request.address, collection_day)
        
        return AddressResponse(
            status="saved",
            address=request.address,
            collection_day=collection_day
        )
    except Exception as e:
        raise HTTPException(500, f"Error saving address: {str(e)}")


@app.get("/api/session/{session_id}/address", response_model=AddressResponse)
async def get_session_address(session_id: str):
    """Get user's saved address for garbage collection"""
    try:
        address, collection_day = get_user_address(session_id)
        
        if not address:
            raise HTTPException(404, "No address found for this session")
        
        return AddressResponse(
            status="found",
            address=address,
            collection_day=collection_day
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error getting address: {str(e)}")


@app.delete("/api/session/{session_id}/address")
async def delete_session_address(session_id: str):
    """Clear user's saved address"""
    try:
        clear_user_address(session_id)
        return {"status": "cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(500, f"Error clearing address: {str(e)}")


# ==================== Language Preference ====================

class LanguageRequest(BaseModel):
    language: str  # "en" or "fr"


class LanguageResponse(BaseModel):
    status: str
    session_id: str
    language: str


@app.post("/api/session/{session_id}/language", response_model=LanguageResponse)
async def set_session_language(session_id: str, request: LanguageRequest):
    """Set user's language preference for this session"""
    try:
        # Validate language
        if request.language not in ["en", "fr"]:
            raise HTTPException(400, "Language must be 'en' or 'fr'")
        
        set_language_preference(session_id, request.language)
        
        return LanguageResponse(
            status="saved",
            session_id=session_id,
            language=request.language
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error setting language: {str(e)}")


@app.get("/api/session/{session_id}/language", response_model=LanguageResponse)
async def get_session_language(session_id: str):
    """Get user's language preference for this session"""
    try:
        language = get_language_preference(session_id)
        
        return LanguageResponse(
            status="found",
            session_id=session_id,
            language=language
        )
    except Exception as e:
        raise HTTPException(500, f"Error getting language: {str(e)}")


@app.delete("/api/session/{session_id}/language")
async def delete_session_language(session_id: str):
    """Clear user's language preference"""
    try:
        clear_language_preference(session_id)
        return {"status": "cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(500, f"Error clearing language: {str(e)}")


# ==================== Agentic Actions ====================

class ActionStartRequest(BaseModel):
    session_id: str
    action: str
    city: str = "kitchener"
    initial_fields: dict = {}


class ActionStartResponse(BaseModel):
    status: str
    session_id: str
    action: str
    required_fields: List[str]
    missing_fields: List[str]
    prompt: str
    state: str


class ActionCollectRequest(BaseModel):
    session_id: str
    message: str  # User's response containing field values


class ActionCollectResponse(BaseModel):
    status: str
    session_id: str
    action: str
    collected_fields: dict
    missing_fields: List[str]
    prompt: str
    is_complete: bool
    state: str


class ActionConfirmRequest(BaseModel):
    session_id: str
    confirmed: bool  # True = proceed, False = cancel


class ActionConfirmResponse(BaseModel):
    status: str
    message: str
    ready_to_execute: bool = False
    action: str = None
    fields: dict = {}


class ActionStatusResponse(BaseModel):
    status: str
    session_id: str
    action: str
    state: str
    collected_fields: dict
    missing_fields: List[str]


# Initialize field collector
field_collector = FieldCollector(action_state_manager)


@app.post("/api/intent/classify", response_model=IntentClassificationResponse)
async def classify_intent_endpoint(request: IntentClassificationRequest):
    """
    Classify user message intent.
    
    Classifies as:
    - QUESTION: User wants information
    - ACTION_REQUEST: User wants to perform an action
    - GREETING: User is saying hello
    
    For ACTION_REQUEST, also extracts action_type and any provided fields.
    """
    try:
        # Try LLM-based classification first
        llm = get_llm()
        if llm:
            result = classify_intent_with_llm(request.message, llm)
            return result
        else:
            # Fallback to simple classification
            return classify_intent_simple(request.message)
    except Exception as e:
        print(f"Intent classification error: {e}")
        # Fallback to simple
        return classify_intent_simple(request.message)


@app.get("/api/actions", response_model=dict)
async def list_actions():
    """Get list of all available actions"""
    return {
        "actions": get_all_actions(),
        "schemas": {
            action: get_action_schema(action).model_dump() 
            for action in get_all_actions()
        }
    }


@app.get("/api/actions/{action}/schema", response_model=dict)
async def get_action_schema_endpoint(action: str):
    """Get the field schema for a specific action"""
    schema = get_action_schema(action)
    if not schema:
        raise HTTPException(404, f"Action '{action}' not found")
    return schema.model_dump()


@app.post("/api/action/start", response_model=ActionStartResponse)
async def start_action(request: ActionStartRequest):
    """
    Start a new action flow.
    For deep_link actions: immediately return portal URL and info needed.
    For automation actions: collect fields normally.
    """
    # Get the action schema
    schema = get_action_schema(request.action)
    if not schema:
        raise HTTPException(404, f"Action '{request.action}' not found")
    
    # Check execution type
    from actions import get_portal_info
    portal_info = get_portal_info(request.action)
    is_deep_link = portal_info and portal_info.get("execution_type") == "deep_link"
    
    # For deep_link actions: skip field collection, return portal URL + info needed
    if is_deep_link:
        required_fields = [{"name": f.name, "label": f.label} for f in schema.required_fields]
        portal_url = portal_info.get("portal_url", "")
        
        # Build message telling user what they'll need
        fields_needed = ", ".join([f["label"] for f in required_fields])
        prompt = f"You can complete this here: {portal_url}\n\nYou'll need: {fields_needed}"
        
        return ActionStartResponse(
            status="deep_link",
            session_id=request.session_id,
            action=request.action,
            required_fields=[f["name"] for f in required_fields],
            missing_fields=[],
            prompt=prompt,
            state="completed"
        )
    
    # For automation actions: collect fields as normal
    required_fields = [f.name for f in schema.required_fields]
    state = action_state_manager.start_action(
        request.session_id, 
        request.action, 
        required_fields,
        request.city
    )
    
    # Update with any initial fields provided
    for field_name, value in request.initial_fields.items():
        action_state_manager.update_field(request.session_id, field_name, value)
    
    # Refresh state after updates
    state = action_state_manager.get_state(request.session_id)
    
    # Generate prompt for missing fields
    prompt = field_collector._generate_prompt(state)
    
    return ActionStartResponse(
        status="started",
        session_id=request.session_id,
        action=request.action,
        required_fields=required_fields,
        missing_fields=state.missing_fields,
        prompt=prompt,
        state=state.state
    )


@app.post("/api/action/collect", response_model=ActionCollectResponse)
async def collect_fields(request: ActionCollectRequest):
    """
    Process user response and extract field values.
    Continues field collection until all required fields are gathered.
    """
    result = field_collector.process_response(request.session_id, request.message)
    
    state = action_state_manager.get_state(request.session_id)
    
    if not state:
        raise HTTPException(400, "No active action for this session")
    
    return ActionCollectResponse(
        status=result.get("status", "collecting"),
        session_id=request.session_id,
        action=state.action,
        collected_fields=state.fields,
        missing_fields=state.missing_fields,
        prompt=result.get("prompt") or "",
        is_complete=result.get("is_complete", False),
        state=state.state
    )


@app.post("/api/action/confirm", response_model=ActionConfirmResponse)
async def confirm_action(request: ActionConfirmRequest):
    """
    Confirm or cancel an action.
    If confirmed, returns the fields ready for execution and sets state to completed with portal URL.
    """
    from actions import get_portal_info
    
    result = field_collector.confirm(request.session_id, request.confirmed)
    
    if request.confirmed:
        state = action_state_manager.get_state(request.session_id)
        
        # Get portal info for the action
        portal_info = get_portal_info(state.action) if state else None
        
        # Set state to completed
        if state:
            action_state_manager.set_state(request.session_id, "completed")
        
        # Build response message with portal URL
        if portal_info:
            if portal_info.get("execution_type") == "deep_link":
                message = f"Action confirmed. Click here to complete: {portal_info['portal_url']}"
            else:
                message = "Action confirmed. Submitting your request..."
        else:
            message = "Action confirmed. Ready to execute."
        
        return ActionConfirmResponse(
            status="confirmed",
            message=message,
            ready_to_execute=True,
            action=state.action if state else None,
            fields=state.fields if state else {}
        )
    else:
        return ActionConfirmResponse(
            status="cancelled",
            message=result.get("message", "Action cancelled"),
            ready_to_execute=False
        )


@app.get("/api/action/status/{session_id}", response_model=ActionStatusResponse)
async def get_action_status(session_id: str):
    """Get the current status of an action for a session"""
    status = field_collector.get_status(session_id)
    
    if not status:
        raise HTTPException(404, "No active action for this session")
    
    return ActionStatusResponse(
        status=status.get("state", "unknown"),
        session_id=session_id,
        action=status.get("action", ""),
        state=status.get("state", ""),
        collected_fields=status.get("fields", {}),
        missing_fields=status.get("missing_fields", [])
    )


@app.delete("/api/action/{session_id}")
async def cancel_action(session_id: str):
    """Cancel an active action"""
    cleared = action_state_manager.clear_state(session_id)
    if not cleared:
        raise HTTPException(404, "No active action to cancel")
    return {"status": "cancelled", "session_id": session_id}


@app.get("/api/action/result/{session_id}")
async def get_action_result(session_id: str):
    """
    Get action execution result for a session.
    Returns portal URL, execution type, collected fields, and status message.
    """
    from actions import get_portal_info
    
    # Get the action state
    state = action_state_manager.get_state(session_id)
    if not state:
        raise HTTPException(404, "No action found for this session")
    
    # Get portal info from registry
    portal_info = get_portal_info(state.action)
    
    # Determine the response message based on state and execution type
    if state.state == "completed":
        if portal_info and portal_info.get("execution_type") == "deep_link":
            message = f"Click here to complete: {portal_info['portal_url']}"
        else:
            message = "Your request has been submitted successfully."
    elif state.state == "executing":
        if portal_info and portal_info.get("execution_type") == "automation":
            message = "Submitting your request..."
        else:
            message = "Preparing your request..."
    else:
        message = "Action in progress..."
    
    return {
        "session_id": session_id,
        "action": state.action,
        "state": state.state,
        "portal_url": portal_info.get("portal_url") if portal_info else None,
        "execution_type": portal_info.get("execution_type") if portal_info else None,
        "collected_fields": state.fields,
        "confirmation_number": state.confirmation_number,
        "message": message
    }


@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(request: ChatRequest):
    """API-compatible chat endpoint with RAG"""
    return await chat(request)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with LLM-based intent classification and RAG"""
    start_time = time.time()
    
    # Generate session ID if not provided
    session_id = request.session_id or f"session_{int(start_time * 1000)}"
    
    # ====== Language Detection and Preference ======
    # Check if user is setting language preference
    message_lower = request.message.lower()
    
    if "en français" in message_lower or "français" in message_lower or "francais" in message_lower:
        # User wants French
        set_language_preference(session_id, "fr")
    elif "in english" in message_lower or "respond in english" in message_lower or "en anglais" in message_lower:
        # User wants English
        set_language_preference(session_id, "en")
    
    # Detect language of the current message
    detected_language = detect_language(request.message)
    
    # Use detected language if no preference set
    target_language = get_language_preference(session_id)
    # If no preference set, use detected language
    if target_language == "en":  # Default, no preference saved
        # Use detected language
        if detected_language == "fr":
            target_language = "fr"
    
    # ====== LLM-Based Intent Classification ======
    # Use the appropriate language for intent classification
    intent_prompt_lang = "in French" if target_language == "fr" else "in English"
    intent_result = classify_intent(request.message, session_id)
    intent = intent_result.get("intent", "general_query")
    entities = intent_result.get("entities", {})
    
    print(f"Intent: {intent}, Entities: {entities}")
    
    # ====== Route based on intent ======
    
    # ---- Ticket Info ----
    if intent == "ticket_info":
        # Use LLM-extracted ticket number or fallback to regex
        ticket_number = entities.get("ticket_number") or extract_ticket_number(request.message)
        answer = get_ticket_response(ticket_number)
        
        # Translate if user prefers French
        if target_language == "fr":
            answer = translate_response(answer, "fr")
        
        try:
            database.add_message(session_id, "user", request.message)
            database.add_message(session_id, "assistant", answer)
        except Exception as e:
            print(f"Warning: Could not save messages: {e}")
        
        response_time = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            answer=answer,
            sources=[{"content": "Parking ticket lookup", "source": "local:ticket_lookup"}],
            session_id=session_id,
            response_time_ms=response_time
        )
    
    # ---- Garbage Collection ----
    elif intent == "garbage_collection":
        # Use LLM-extracted address or fallback to regex
        address = entities.get("address") or extract_address(request.message)
        
        # Check if user has a saved address in this session
        saved_address, saved_day = get_user_address(session_id)
        
        # If no address in message but user has saved address, use it
        if not address and saved_address:
            address = saved_address
        
        if address:
            # Look up collection day
            collection_day = lookup_garbage_collection_day(address)
            
            if collection_day:
                # Save the address for future queries
                save_user_address(session_id, address, collection_day)
                
                answer = (f"Your garbage, recycling, and organic waste are collected on **{collection_day}** "
                         f"at your address ({address}). Please place bins at the curb by 7 AM on collection day. "
                         f"Learn more at kitchener.ca/waste")
            else:
                # Address not found in our database
                answer = (f"I couldn't find the collection schedule for {address}. "
                         f"You can check your garbage day at kitchener.ca/waste "
                         f"or call 519-741-2345 for assistance.")
        else:
            # No specific address found - ask for clarification
            answer = ("I'd be happy to look up your garbage collection day! "
                     "What's your address? (e.g., '110 Fergus Ave')")
        
        # Translate if user prefers French
        if target_language == "fr":
            answer = translate_response(answer, "fr")
        
        try:
            database.add_message(session_id, "user", request.message)
            database.add_message(session_id, "assistant", answer)
        except Exception as e:
            print(f"Warning: Could not save messages: {e}")
        
        response_time = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            answer=answer,
            sources=[{"content": "Address-based garbage lookup", "source": "local:address_lookup"}],
            session_id=session_id,
            response_time_ms=response_time
        )
    
    # ---- Location Query ----
    elif intent == "location":
        # Use LLM-extracted facility type or fallback to regex
        facility_type = entities.get("facility_type") or extract_facility_type(request.message)
        answer = get_location_response(facility_type)
        
        # Translate if user prefers French
        if target_language == "fr":
            answer = translate_response(answer, "fr")
        
        try:
            database.add_message(session_id, "user", request.message)
            database.add_message(session_id, "assistant", answer)
        except Exception as e:
            print(f"Warning: Could not save messages: {e}")
        
        response_time = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            answer=answer,
            sources=[{"content": "Location finder", "source": "local:location_finder"}],
            session_id=session_id,
            response_time_ms=response_time
        )
    
    # ---- Road Closures Query ----
    elif intent == "road_closures":
        try:
            closures = await get_road_closures()
            if closures:
                answer = "🚧 **Current Road Closures in the Region:**\n\n"
                for closure in closures[:5]:
                    answer += f"• **{closure['street']}** - {closure.get('location', '')}\n"
                    answer += f"  Reason: {closure.get('reason', 'Construction')}\n"
                    if closure.get('end_date'):
                        answer += f"  Until: {closure.get('end_date')}\n"
                    answer += "\n"
            else:
                answer = "There are currently no major road closures reported in the Kitchener/Waterloo region."
            
            # Skip translation for API-sourced data to avoid issues
            # if target_language == "fr":
            #     answer = translate_response(answer, "fr")
            
            try:
                database.add_message(session_id, "user", request.message)
                database.add_message(session_id, "assistant", answer)
            except Exception as e:
                print(f"Warning: Could not save messages: {e}")
            
            response_time = int((time.time() - start_time) * 1000)
            
            return ChatResponse(
                answer=answer,
                sources=[{"content": "Road closures data", "source": "region of waterloo"}],
                session_id=session_id,
                response_time_ms=response_time
            )
        except Exception as e:
            print(f"Road closures error: {e}")
            answer = "I couldn't fetch the current road closures at this time. Please check regionofwaterloo.ca for the latest information."
            
            try:
                database.add_message(session_id, "user", request.message)
                database.add_message(session_id, "assistant", answer)
            except:
                pass
            
            response_time = int((time.time() - start_time) * 1000)
            return ChatResponse(
                answer=answer,
                sources=[{"content": "Error fetching road closures", "source": "local:error"}],
                session_id=session_id,
                response_time_ms=response_time
            )
    
    # ---- Community Events Query ----
    elif intent == "community_events":
        city = entities.get("city", "kitchener")
        try:
            events = await get_community_events(city)
            if events:
                answer = f"🎉 **Upcoming Events in {city.title()}:**\n\n"
                for event in events[:5]:
                    answer += f"• **{event.get('title', 'Event')}**\n"
                    if event.get('date'):
                        answer += f"  Date: {event.get('date')}\n"
                    if event.get('location'):
                        answer += f"  Location: {event.get('location')}\n"
                    if event.get('description'):
                        answer += f"  {event.get('description')}\n"
                    answer += "\n"
            else:
                answer = f"No upcoming events found for {city.title()}. Check the city's website for the latest listings."
            
            # Skip translation for API-sourced data
            # if target_language == "fr":
            #     answer = translate_response(answer, "fr")
            
            try:
                database.add_message(session_id, "user", request.message)
                database.add_message(session_id, "assistant", answer)
            except Exception as e:
                print(f"Warning: Could not save messages: {e}")
            
            response_time = int((time.time() - start_time) * 1000)
            
            return ChatResponse(
                answer=answer,
                sources=[{"content": "Community events", "source": f"{city} events"}],
                session_id=session_id,
                response_time_ms=response_time
            )
        except Exception as e:
            print(f"Community events error: {e}")
            answer = f"I couldn't fetch events for {city.title()} at this time."
            
            try:
                database.add_message(session_id, "user", request.message)
                database.add_message(session_id, "assistant", answer)
            except:
                pass
            
            response_time = int((time.time() - start_time) * 1000)
            return ChatResponse(
                answer=answer,
                sources=[{"content": "Error fetching events", "source": "local:error"}],
                session_id=session_id,
                response_time_ms=response_time
            )
    
    # ---- Permit Status Query (Kitchener) ----
    elif intent == "permit_status":
        address = entities.get("address") or extract_address(request.message)
        
        # Check for saved address if not in message
        if not address:
            saved_address, _ = get_user_address(session_id)
            user_profile_address = get_user_profile_address(session_id)
            address = saved_address or user_profile_address
        
        if address:
            try:
                result = await get_permit_status(address)
                permits = result.get("permits", [])
                
                if permits:
                    answer = f"🏠 **Building Permits for {address}:**\n\n"
                    for permit in permits[:3]:
                        answer += f"• Permit #{permit.get('permit_number', 'N/A')}\n"
                        answer += f"  Type: {permit.get('permit_type', 'N/A')}\n"
                        answer += f"  Status: {permit.get('status', 'N/A')}\n"
                        if permit.get('description'):
                            answer += f"  Description: {permit.get('description')}\n"
                        answer += "\n"
                else:
                    answer = result.get("message", f"No active building permits found for {address}. You can view permits online at kitchener.ca/maps")
                
                # Skip translation for API-sourced data
                # if target_language == "fr":
                #     answer = translate_response(answer, "fr")
                
                try:
                    database.add_message(session_id, "user", request.message)
                    database.add_message(session_id, "assistant", answer)
                except Exception as e:
                    print(f"Warning: Could not save messages: {e}")
                
                response_time = int((time.time() - start_time) * 1000)
                
                return ChatResponse(
                    answer=answer,
                    sources=[{"content": "Building permits", "source": "kitchener open data"}],
                    session_id=session_id,
                    response_time_ms=response_time
                )
            except Exception as e:
                print(f"Permit status error: {e}")
        
        # No address provided
        answer = "To look up building permits, I need your address. What's the street address you're interested in?"
        
        try:
            database.add_message(session_id, "user", request.message)
            database.add_message(session_id, "assistant", answer)
        except:
            pass
        
        response_time = int((time.time() - start_time) * 1000)
        return ChatResponse(
            answer=answer,
            sources=[{"content": "Permit status lookup", "source": "local:permit_status"}],
            session_id=session_id,
            response_time_ms=response_time
        )
    
    # ---- Waterloo Parking Ticket Query ----
    elif intent == "ticket_info_waterloo":
        ticket_number = entities.get("ticket_number") or extract_ticket_number(request.message)
        
        if ticket_number:
            try:
                result = await get_waterloo_parking_ticket(ticket_number)
                
                if result.get("status") == "found":
                    answer = f"🎫 **Waterloo Parking Ticket #{ticket_number}:**\n"
                    answer += f"Amount: {result.get('amount', 'N/A')}\n"
                    answer += f"Status: {result.get('status', 'N/A')}\n"
                    answer += f"Due Date: {result.get('due_date', 'N/A')}\n"
                else:
                    answer = result.get("message", "To look up your Waterloo parking ticket, please visit https://amps.waterloo.ca/pay")
                    if result.get("payment_options"):
                        answer += "\n\nPayment options:\n"
                        for opt in result["payment_options"]:
                            answer += f"• {opt}\n"
                
                # Skip translation for API-sourced data
                # if target_language == "fr":
                #     answer = translate_response(answer, "fr")
                
                try:
                    database.add_message(session_id, "user", request.message)
                    database.add_message(session_id, "assistant", answer)
                except Exception as e:
                    print(f"Warning: Could not save messages: {e}")
                
                response_time = int((time.time() - start_time) * 1000)
                
                return ChatResponse(
                    answer=answer,
                    sources=[{"content": "Waterloo parking ticket", "source": "waterloo amps"}],
                    session_id=session_id,
                    response_time_ms=response_time
                )
            except Exception as e:
                print(f"Waterloo ticket error: {e}")
        
        # No ticket number provided
        answer = "To look up your Waterloo parking ticket, I'll need the ticket number. You can also visit https://amps.waterloo.ca/pay"
        
        try:
            database.add_message(session_id, "user", request.message)
            database.add_message(session_id, "assistant", answer)
        except:
            pass
        
        response_time = int((time.time() - start_time) * 1000)
        return ChatResponse(
            answer=answer,
            sources=[{"content": "Waterloo parking lookup", "source": "local:ticket_waterloo"}],
            session_id=session_id,
            response_time_ms=response_time
        )
    
    # ---- Property Tax Query ----
    # Check for property tax queries (may come back as general_query from intent classifier)
    if is_property_tax_query(request.message):
        # Check for known address in session context
        saved_address, _ = get_user_address(session_id)
        user_profile_address = get_user_profile_address(session_id)
        # Use any known address (from current session or user profile)
        known_address = saved_address or user_profile_address
        
        answer = get_property_tax_response(known_address)
        
        # Translate if user prefers French
        if target_language == "fr":
            answer = translate_response(answer, "fr")
        
        try:
            database.add_message(session_id, "user", request.message)
            database.add_message(session_id, "assistant", answer)
        except Exception as e:
            print(f"Warning: Could not save messages: {e}")
        
        response_time = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            answer=answer,
            sources=[{"content": "Property tax lookup", "source": "local:property_tax"}],
            session_id=session_id,
            response_time_ms=response_time
        )
    
    # ---- General Query (RAG) ----
    # Fallback to RAG for general queries or unknown intents
    try:
        vs = get_vectorstore()
    except HTTPException as e:
        raise e
    
    # Get LLM
    try:
        llm_model = get_llm()
    except Exception as e:
        raise HTTPException(503, f"Ollama not available: {str(e)}")
    
    # Retrieve relevant documents
    try:
        retriever = vs.as_retriever(search_kwargs={"k": 3})
        docs = retriever.invoke(request.message)
    except Exception as e:
        raise HTTPException(500, f"Error retrieving documents: {str(e)}")
    
    # Extract source context for prompt
    context = "\n\n".join(doc.page_content for doc in docs)
    sources = []
    for doc in docs:
        sources.append({
            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            "source": doc.metadata.get("source", "Unknown")
        })
    
    # Load conversation history from this session
    session_history = get_session_history(session_id, limit=6)
    
    # Create prompt with context and session history
    history_section = f"\n\nPrevious conversation:\n{session_history}" if session_history else ""
    
    prompt = f"""You are a helpful assistant for the City of Kitchener. Answer the user's question based only on the provided context. If you cannot find the answer in the context, say so honestly.{history_section}

Context from knowledge base:
{context}

Current question: {request.message}

Answer:"""
    
    # Get LLM response
    try:
        response = llm_model.invoke(prompt)
        # Handle both string (Ollama) and AIMessage (OpenAI) responses
        answer = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        raise HTTPException(500, f"Error generating response: {str(e)}")
    
    # Translate if user prefers French
    if target_language == "fr":
        answer = translate_response(answer, "fr")
    
    # Save user message to database if session exists
    try:
        database.add_message(session_id, "user", request.message)
    except Exception as e:
        print(f"Warning: Could not save user message: {e}")
    
    # Save assistant response to database
    try:
        database.add_message(session_id, "assistant", answer)
    except Exception as e:
        print(f"Warning: Could not save assistant message: {e}")
    
    response_time = int((time.time() - start_time) * 1000)
    
    return ChatResponse(
        answer=answer,
        sources=sources if request.include_sources else None,
        session_id=session_id,
        response_time_ms=response_time
    )


@app.post("/rebuild-index", response_model=RebuildResponse)
async def rebuild_index():
    """Rebuild the vector index from documents in data/documents/"""
    global vectorstore
    vectorstore = None  # Reset to force rebuild
    
    try:
        num_docs, num_chunks = rebuild_index_sync()
        return RebuildResponse(
            status="complete",
            documents=num_docs,
            chunks=num_chunks
        )
    except Exception as e:
        raise HTTPException(500, f"Error rebuilding index: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    try:
        return database.get_stats()
    except Exception as e:
        raise HTTPException(500, f"Error getting stats: {str(e)}")


@app.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for a message response"""
    try:
        # Validate rating (1-5)
        if not 1 <= request.rating <= 5:
            raise HTTPException(400, "Rating must be between 1 and 5")
        
        # Store feedback
        feedback_id = database.add_feedback(
            session_id=request.session_id,
            message_id=request.message_id,
            rating=request.rating,
            feedback_text=request.feedback_text
        )
        
        return FeedbackResponse(
            status="saved",
            feedback_id=feedback_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error saving feedback: {str(e)}")


@app.get("/api/feedback/stats")
async def get_feedback_stats():
    """Get feedback statistics"""
    try:
        return database.get_feedback_stats()
    except Exception as e:
        raise HTTPException(500, f"Error getting feedback stats: {str(e)}")


# ==================== Municipal Portal Automation Endpoints ====================

@app.get("/api/road-closures", response_model=RoadClosuresResponse)
async def get_road_closures_endpoint():
    """
    Get current road closures in the Kitchener/Waterloo region.
    Returns list of active road closures from Region of Waterloo.
    """
    try:
        closures = await get_road_closures()
        return RoadClosuresResponse(
            status="success",
            count=len(closures),
            closures=closures
        )
    except Exception as e:
        raise HTTPException(500, f"Error fetching road closures: {str(e)}")


@app.get("/api/community-events", response_model=CommunityEventsResponse)
async def get_community_events_endpoint(city: str = "kitchener"):
    """
    Get upcoming community events for Kitchener or Waterloo.
    
    Query params:
    - city: "kitchener" or "waterloo" (default: kitchener)
    """
    try:
        events = await get_community_events(city)
        return CommunityEventsResponse(
            status="success",
            city=city,
            count=len(events),
            events=events
        )
    except Exception as e:
        raise HTTPException(500, f"Error fetching community events: {str(e)}")


@app.post("/api/permit-status", response_model=PermitStatusResponse)
async def get_permit_status_endpoint(request: PermitStatusRequest):
    """
    Get building permit status for a Kitchener address.
    
    Request body:
    - address: Street address to look up (e.g., "110 Fergus Ave")
    """
    try:
        result = await get_permit_status(request.address)
        return PermitStatusResponse(
            status=result.get("status", "error"),
            address=result.get("address", request.address),
            permits=result.get("permits"),
            message=result.get("message")
        )
    except Exception as e:
        raise HTTPException(500, f"Error fetching permit status: {str(e)}")


@app.post("/api/parking-ticket", response_model=ParkingTicketResponse)
async def get_parking_ticket_endpoint(request: ParkingTicketRequest):
    """
    Look up a parking ticket for Waterloo region.
    
    Request body:
    - ticket_number: Parking ticket number
    """
    try:
        result = await get_waterloo_parking_ticket(request.ticket_number)
        return ParkingTicketResponse(
            status=result.get("status", "error"),
            ticket_number=result.get("ticket_number", request.ticket_number),
            amount=result.get("amount"),
            message=result.get("message"),
            payment_options=result.get("payment_options")
        )
    except Exception as e:
        raise HTTPException(500, f"Error fetching parking ticket: {str(e)}")


@app.get("/api/widget.js")
async def get_widget_js():
    """Serve the embeddable widget JavaScript"""
    widget_js = '''
// Municipal Chatbot Widget Loader
(function() {
  var config = {
    apiUrl: window.location.origin,
    position: 'bottom-right',
    primaryColor: '#006699'
  };
  
  // Read data attributes from script tag
  var scripts = document.getElementsByTagName('script');
  var currentScript = scripts[scripts.length - 1];
  if (currentScript.dataset.city) config.city = currentScript.dataset.city;
  if (currentScript.dataset.color) config.primaryColor = currentScript.dataset.color;
  if (currentScript.dataset.apiUrl) config.apiUrl = currentScript.dataset.apiUrl;
  
  window.MunicipalChatbot = {
    config: config,
    init: function() { console.log('Chatbot initialized'); }
  };
  
  console.log('Municipal Chatbot widget loaded');
})();
'''
    return widget_js


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)