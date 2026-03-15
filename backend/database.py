"""
SQLite Database Module for Municipal Chatbot
Handles sessions, users, and messages storage
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Database path
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "municipal_chatbot.db"

# Ensure data dir exists
DATA_DIR.mkdir(exist_ok=True)


def get_db_path() -> str:
    """Get the database file path"""
    return str(DB_PATH)


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database with schema"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migration: Add address and updated_at columns to existing users table
        try:
            cursor.execute("SELECT address FROM users LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
        
        try:
            cursor.execute("SELECT updated_at FROM users LIMIT 1")
        except sqlite3.OperationalError:
            # Use NULL as default - we'll set it on updates
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        # Knowledge base table (for tracking scraped content)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_base_url ON knowledge_base(url)")
        
        # Feedback table for message ratings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_id INTEGER,
                rating INTEGER NOT NULL CHECK(rating IN (1, 2, 3, 4, 5)),
                feedback_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON feedback(session_id)")
        
        conn.commit()
        print(f"Database initialized at {DB_PATH}")


# ==================== User Operations ====================

def create_user(name: str, email: Optional[str] = None) -> int:
    """Create a new user and return their ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (name, email)
        )
        return cursor.lastrowid


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email address"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user_address(user_id: int, address: str) -> bool:
    """Update user's saved address"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET address = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (address, user_id)
        )
        return cursor.rowcount > 0


def get_user_address(user_id: int) -> Optional[str]:
    """Get user's saved address"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT address FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return row['address'] if row and row['address'] else None


# ==================== Session Operations ====================

def create_session(user_id: Optional[int] = None, session_id: Optional[str] = None) -> str:
    """Create a new session and return session_id"""
    import uuid
    
    if session_id is None:
        session_id = f"session_{uuid.uuid4().hex[:12]}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (session_id, user_id) VALUES (?, ?)",
            (session_id, user_id)
        )
        return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.*, u.name as user_name, u.email as user_email 
               FROM sessions s 
               LEFT JOIN users u ON s.user_id = u.id 
               WHERE s.session_id = ?""",
            (session_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def end_session(session_id: str) -> Optional[Dict[str, Any]]:
    """End a session by setting ended_at timestamp"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET ended_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,)
        )
        if cursor.rowcount > 0:
            return get_session(session_id)
        return None


def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """Get all messages for a session"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at",
            (session_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


# ==================== Message Operations ====================

def add_message(session_id: str, role: str, content: str):
    """Add a message to a session"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )


# ==================== Feedback Operations ====================

def add_feedback(
    session_id: str, 
    message_id: Optional[int] = None, 
    rating: int = 3, 
    feedback_text: Optional[str] = None
) -> int:
    """
    Add feedback for a message.
    Rating: 1-5 (1=thumbs down, 5=thumbs up, 3=neutral)
    Returns the feedback ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (session_id, message_id, rating, feedback_text) VALUES (?, ?, ?, ?)",
            (session_id, message_id, rating, feedback_text)
        )
        return cursor.lastrowid


def get_feedback_stats() -> Dict[str, Any]:
    """Get feedback statistics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get total feedback count
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total = cursor.fetchone()[0]
        
        # Get average rating
        cursor.execute("SELECT AVG(rating) FROM feedback")
        avg_rating = cursor.fetchone()[0] or 0
        
        # Get rating distribution
        cursor.execute("""
            SELECT rating, COUNT(*) as count 
            FROM feedback 
            GROUP BY rating 
            ORDER BY rating
        """)
        distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_feedback": total,
            "average_rating": round(avg_rating, 2),
            "distribution": distribution
        }


# ==================== Knowledge Base Operations ====================

def add_knowledge(url: str, title: str, content: str):
    """Add or update knowledge base entry"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if exists
        cursor.execute("SELECT id FROM knowledge_base WHERE url = ?", (url,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE knowledge_base SET title = ?, content = ?, last_updated = CURRENT_TIMESTAMP WHERE url = ?",
                (title, content, url)
            )
        else:
            cursor.execute(
                "INSERT INTO knowledge_base (url, title, content) VALUES (?, ?, ?)",
                (url, title, content)
            )


def get_all_knowledge() -> List[Dict[str, Any]]:
    """Get all knowledge base entries"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM knowledge_base ORDER BY last_updated DESC")
        return [dict(row) for row in cursor.fetchall()]


# ==================== Utility Functions ====================

def get_stats() -> Dict[str, int]:
    """Get database statistics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sessions")
        stats['sessions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        stats['messages'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        stats['knowledge_base'] = cursor.fetchone()[0]
        
        return stats


if __name__ == "__main__":
    init_db()
    print("Stats:", get_stats())