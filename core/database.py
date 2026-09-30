"""SQLite/MySQL persistence layer for Indian E-Commerce Orders and Dispatch Audit Ledger."""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.config import settings
from core.schema import AuditLogEntry, OrderRecord, WhatsAppVerificationResult


class DatabaseManager:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or settings.DATABASE_URL
        # SQLite path extraction
        if "sqlite:///" in self.db_url:
            self.sqlite_path = self.db_url.replace("sqlite:///", "")
        else:
            self.sqlite_path = "indian_ecom_rto.db"
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables for orders, audit logs, and WhatsApp interactions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    customer_name TEXT,
                    phone TEXT,
                    payment_mode TEXT,
                    city_tier TEXT,
                    pincode TEXT,
                    address_quality_score REAL,
                    order_value_inr REAL,
                    status TEXT,
                    allocated_carrier TEXT,
                    predicted_rto_risk REAL,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    event_type TEXT,
                    order_id TEXT,
                    details TEXT,
                    financial_impact_inr REAL,
                    operator_approved INTEGER,
                    operator_notes TEXT
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS whatsapp_interactions (
                    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    language TEXT,
                    action_taken TEXT,
                    discount_applied_inr REAL,
                    chat_transcript TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def log_event(self, entry: AuditLogEntry) -> None:
        """Append an immutable entry to the audit log."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO audit_logs (
                    log_id, timestamp, event_type, order_id, details,
                    financial_impact_inr, operator_approved, operator_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                entry.log_id,
                entry.timestamp or datetime.utcnow().isoformat(),
                entry.event_type,
                entry.order_id,
                json.dumps(entry.details),
                entry.financial_impact_inr,
                1 if entry.operator_approved else 0,
                entry.operator_notes
            ))
            conn.commit()

    def save_order(self, order: OrderRecord, status: str = "INGESTED", carrier: Optional[str] = None, rto_risk: float = 0.0) -> None:
        """Store or update order status and allocation details."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO orders (
                    order_id, customer_name, phone, payment_mode, city_tier,
                    pincode, address_quality_score, order_value_inr, status,
                    allocated_carrier, predicted_rto_risk, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                order.order_id,
                order.customer_name,
                order.phone,
                order.payment_mode.value,
                order.city_tier.value,
                order.address.pincode,
                order.address.address_completeness_score,
                order.order_value_inr,
                status,
                carrier,
                rto_risk,
                json.dumps(order.model_dump())
            ))
            conn.commit()

    def log_whatsapp_result(self, result: WhatsAppVerificationResult) -> None:
        """Save buyer WhatsApp interaction log."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO whatsapp_interactions (
                    order_id, language, action_taken, discount_applied_inr, chat_transcript
                ) VALUES (?, ?, ?, ?, ?);
            """, (
                result.order_id,
                result.language.value,
                result.action_taken.value,
                result.discount_applied_inr,
                json.dumps(result.chat_transcript)
            ))
            conn.commit()

    def get_recent_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent audit logs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?;", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored order by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE order_id = ?;", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


db = DatabaseManager()
