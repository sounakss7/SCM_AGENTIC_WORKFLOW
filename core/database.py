import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import pymysql
except ImportError:
    pymysql = None

from core.config import settings

def is_using_sqlite() -> bool:
    return settings.USE_SQLITE

def get_db_connection():
    """Returns database connection and cursor with SQLite / MySQL abstraction."""
    if is_using_sqlite():
        conn = sqlite3.connect(settings.SQLITE_PATH, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn, conn.cursor()
    else:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn, conn.cursor()

def init_database() -> None:
    """Initializes tables for orders, disruptions, recovery plans, and audit trail."""
    conn, cursor = get_db_connection()
    try:
        if is_using_sqlite():
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    cost_impact REAL NOT NULL,
                    requires_approval INTEGER DEFAULT 0,
                    approval_status TEXT DEFAULT 'AUTO_APPROVED',
                    details TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recovery_plans (
                    plan_id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    solver_time_sec REAL NOT NULL,
                    total_recovery_cost REAL NOT NULL,
                    total_penalty_cost REAL NOT NULL,
                    total_combined_cost REAL NOT NULL,
                    average_delay_days REAL NOT NULL,
                    service_level_pct REAL NOT NULL,
                    orders_on_time INTEGER NOT NULL,
                    orders_delayed INTEGER NOT NULL,
                    is_feasible INTEGER NOT NULL,
                    allocations_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disruptions (
                    event_id TEXT PRIMARY KEY,
                    disruption_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    severity REAL NOT NULL,
                    duration_days INTEGER NOT NULL,
                    affected_node TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_ledger (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    scenario_id VARCHAR(100) NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    phase VARCHAR(100) NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    action_taken TEXT NOT NULL,
                    model_used VARCHAR(100) NOT NULL,
                    cost_impact DECIMAL(12, 2) NOT NULL,
                    requires_approval TINYINT(1) DEFAULT 0,
                    approval_status VARCHAR(50) DEFAULT 'AUTO_APPROVED',
                    details TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recovery_plans (
                    plan_id VARCHAR(100) PRIMARY KEY,
                    scenario_id VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    solver_time_sec DECIMAL(8, 4) NOT NULL,
                    total_recovery_cost DECIMAL(12, 2) NOT NULL,
                    total_penalty_cost DECIMAL(12, 2) NOT NULL,
                    total_combined_cost DECIMAL(12, 2) NOT NULL,
                    average_delay_days DECIMAL(6, 2) NOT NULL,
                    service_level_pct DECIMAL(6, 2) NOT NULL,
                    orders_on_time INT NOT NULL,
                    orders_delayed INT NOT NULL,
                    is_feasible TINYINT(1) NOT NULL,
                    allocations_json LONGTEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disruptions (
                    event_id VARCHAR(100) PRIMARY KEY,
                    disruption_type VARCHAR(100) NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    severity DECIMAL(4, 2) NOT NULL,
                    duration_days INT NOT NULL,
                    affected_node VARCHAR(255),
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    finally:
        conn.close()

def log_audit_entry(
    scenario_id: str,
    phase: str,
    agent_name: str,
    action_taken: str,
    model_used: str,
    cost_impact: float,
    requires_approval: bool = False,
    approval_status: str = "AUTO_APPROVED",
    details: str = ""
) -> int:
    """Inserts a record into the immutable decision audit ledger."""
    init_database()
    conn, cursor = get_db_connection()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if is_using_sqlite():
            cursor.execute("""
                INSERT INTO audit_ledger (scenario_id, timestamp, phase, agent_name, action_taken, model_used, cost_impact, requires_approval, approval_status, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (scenario_id, now_str, phase, agent_name, action_taken, model_used, cost_impact, 1 if requires_approval else 0, approval_status, details))
            entry_id = cursor.lastrowid
        else:
            cursor.execute("""
                INSERT INTO audit_ledger (scenario_id, timestamp, phase, agent_name, action_taken, model_used, cost_impact, requires_approval, approval_status, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (scenario_id, now_str, phase, agent_name, action_taken, model_used, cost_impact, 1 if requires_approval else 0, approval_status, details))
            entry_id = cursor.lastrowid
        conn.commit()
        return entry_id
    finally:
        conn.close()

def save_recovery_plan(plan_dict: Dict[str, Any]) -> None:
    """Persists an evaluated optimizer plan to the database."""
    init_database()
    conn, cursor = get_db_connection()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        allocations_str = json.dumps(plan_dict.get("allocations", []))
        if is_using_sqlite():
            cursor.execute("""
                INSERT OR REPLACE INTO recovery_plans 
                (plan_id, scenario_id, status, solver_time_sec, total_recovery_cost, total_penalty_cost, total_combined_cost, average_delay_days, service_level_pct, orders_on_time, orders_delayed, is_feasible, allocations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan_dict["plan_id"],
                plan_dict["scenario_id"],
                plan_dict["status"],
                plan_dict["solver_time_sec"],
                plan_dict["total_recovery_cost"],
                plan_dict["total_penalty_cost"],
                plan_dict["total_combined_cost"],
                plan_dict["average_delay_days"],
                plan_dict["service_level_pct"],
                plan_dict["orders_on_time"],
                plan_dict["orders_delayed"],
                1 if plan_dict.get("is_feasible", True) else 0,
                allocations_str,
                now_str
            ))
        else:
            cursor.execute("""
                INSERT INTO recovery_plans 
                (plan_id, scenario_id, status, solver_time_sec, total_recovery_cost, total_penalty_cost, total_combined_cost, average_delay_days, service_level_pct, orders_on_time, orders_delayed, is_feasible, allocations_json, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status=%s, total_combined_cost=%s
            """, (
                plan_dict["plan_id"],
                plan_dict["scenario_id"],
                plan_dict["status"],
                plan_dict["solver_time_sec"],
                plan_dict["total_recovery_cost"],
                plan_dict["total_penalty_cost"],
                plan_dict["total_combined_cost"],
                plan_dict["average_delay_days"],
                plan_dict["service_level_pct"],
                plan_dict["orders_on_time"],
                plan_dict["orders_delayed"],
                1 if plan_dict.get("is_feasible", True) else 0,
                allocations_str,
                now_str,
                plan_dict["status"],
                plan_dict["total_combined_cost"]
            ))
        conn.commit()
    finally:
        conn.close()

def get_audit_trail(limit: int = 50, scenario_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches audit trail entries."""
    init_database()
    conn, cursor = get_db_connection()
    try:
        if scenario_id:
            if is_using_sqlite():
                cursor.execute("SELECT * FROM audit_ledger WHERE scenario_id = ? ORDER BY id DESC LIMIT ?", (scenario_id, limit))
            else:
                cursor.execute("SELECT * FROM audit_ledger WHERE scenario_id = %s ORDER BY id DESC LIMIT %s", (scenario_id, limit))
        else:
            if is_using_sqlite():
                cursor.execute("SELECT * FROM audit_ledger ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT * FROM audit_ledger ORDER BY id DESC LIMIT %s", (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def update_approval_status(scenario_id: str, new_status: str) -> None:
    """Updates approval status for pending plans."""
    conn, cursor = get_db_connection()
    try:
        if is_using_sqlite():
            cursor.execute("UPDATE audit_ledger SET approval_status = ? WHERE scenario_id = ? AND requires_approval = 1", (new_status, scenario_id))
        else:
            cursor.execute("UPDATE audit_ledger SET approval_status = %s WHERE scenario_id = %s AND requires_approval = 1", (new_status, scenario_id))
        conn.commit()
    finally:
        conn.close()

def reset_all_tables() -> None:
    """Wipes tables for a clean slate in test runs."""
    conn, cursor = get_db_connection()
    try:
        if is_using_sqlite():
            cursor.execute("DROP TABLE IF EXISTS audit_ledger")
            cursor.execute("DROP TABLE IF EXISTS recovery_plans")
            cursor.execute("DROP TABLE IF EXISTS disruptions")
            conn.commit()
        else:
            cursor.execute("DROP TABLE IF EXISTS audit_ledger")
            cursor.execute("DROP TABLE IF EXISTS recovery_plans")
            cursor.execute("DROP TABLE IF EXISTS disruptions")
            conn.commit()
        init_database()
    finally:
        conn.close()
