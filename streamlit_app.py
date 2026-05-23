import streamlit as st
import os
import re
import time
import json
import pymysql
import sqlite3
from datetime import datetime
from typing import TypedDict, List, Dict, Any

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

# ==========================================
# 1. UI CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="SCM Agentic Workflow Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Elegant CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Elegant Sidebar Gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #1F2937 100%);
        color: #F3F4F6;
    }
    [data-testid="stSidebar"] hr {
        border-color: #374151;
    }
    
    /* Header Card */
    .header-container {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
        margin-bottom: 2rem;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    .header-subtitle {
        font-size: 1.1rem;
        font-weight: 300;
        opacity: 0.9;
    }
    
    /* Professional Card styling */
    .scm-card {
        background-color: #ffffff;
        border: 1px solid #E5E7EB;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .scm-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }
    .scm-card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.75rem;
        border-bottom: 2px solid #F3F4F6;
        padding-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Custom Metric Tiles */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-tile {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.2s ease;
    }
    .metric-tile:hover {
        background: #F3F4F6;
        border-color: #D1D5DB;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.25rem;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #4B5563;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Timeline / Agent nodes styling */
    .timeline-container {
        position: relative;
        padding-left: 2rem;
        border-left: 2px solid #E5E7EB;
        margin-left: 1rem;
        margin-top: 1.5rem;
    }
    .timeline-item {
        position: relative;
        margin-bottom: 2rem;
    }
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -2.6rem;
        top: 0.25rem;
        width: 1.2rem;
        height: 1.2rem;
        border-radius: 50%;
        background-color: #3B82F6;
        border: 3px solid #FFFFFF;
        box-shadow: 0 0 0 3px #DBEAFE;
    }
    .timeline-item.active::before {
        background-color: #10B981;
        box-shadow: 0 0 0 3px #D1FAE5;
        animation: pulse 1.5s infinite;
    }
    .timeline-item.failed::before {
        background-color: #EF4444;
        box-shadow: 0 0 0 3px #FEE2E2;
    }
    .timeline-item.loop::before {
        background-color: #F59E0B;
        box-shadow: 0 0 0 3px #FEF3C7;
    }
    .timeline-title {
        font-weight: 600;
        color: #1F2937;
        font-size: 1.05rem;
    }
    .timeline-meta {
        font-size: 0.8rem;
        color: #6B7280;
        margin-top: 0.15rem;
        margin-bottom: 0.5rem;
        display: flex;
        gap: 1rem;
    }
    .timeline-content {
        background-color: #F9FAFB;
        border: 1px solid #F3F4F6;
        border-radius: 8px;
        padding: 0.85rem 1.2rem;
        font-size: 0.9rem;
        color: #4B5563;
        line-height: 1.5;
    }
    .timeline-thought {
        font-family: monospace;
        background-color: #1F2937;
        color: #34D399;
        padding: 0.75rem;
        border-radius: 6px;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        overflow-x: auto;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Styled badges */
    .badge {
        padding: 0.25rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        text-transform: uppercase;
    }
    .badge-vip { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
    .badge-premium { background-color: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
    .badge-standard { background-color: #E0F2FE; color: #075985; border: 1px solid #7DD3FC; }
    .badge-success { background-color: #D1FAE5; color: #065F46; }
    .badge-warning { background-color: #FEF3C7; color: #92400E; }
    .badge-error { background-color: #FEE2E2; color: #991B1B; }
    .badge-info { background-color: #E0F2FE; color: #0369A1; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE MANAGEMENT MODULE (MYSQL & SQLITE)
# ==========================================
def get_mysql_connection():
    try:
        return pymysql.connect(
            host=st.session_state.mysql_host,
            port=int(st.session_state.mysql_port),
            user=st.session_state.mysql_user,
            password=st.session_state.mysql_password,
            database=st.session_state.mysql_database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        raise ConnectionError(f"MySQL connection failed: {e}")

def get_db_cursor():
    """Returns database connection and cursor, falling back to SQLite if MySQL is disabled/unconfigured"""
    if st.session_state.use_sqlite:
        conn = sqlite3.connect("local_orders.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn, conn.cursor()
    else:
        conn = get_mysql_connection()
        return conn, conn.cursor()

def test_mysql_server(host, port, user, password):
    """Utility to test MySQL server connection without specifying database"""
    try:
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            charset='utf8mb4'
        )
        conn.close()
        return True, "Successfully reached MySQL server."
    except Exception as e:
        return False, str(e)

def init_database():
    """Initializes tables in either MySQL or SQLite depending on configuration"""
    if st.session_state.use_sqlite:
        conn = sqlite3.connect("local_orders.db")
        cursor = conn.cursor()
        
        # Enable Foreign Keys in SQLite
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create Tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                company TEXT,
                address TEXT,
                tier TEXT DEFAULT 'Standard'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'Processing',
                order_date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                phase TEXT,
                agent_name TEXT,
                action TEXT,
                model_used TEXT,
                cost_savings TEXT,
                live_location TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT,
                report_text TEXT,
                model_used TEXT,
                created_at TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        conn.commit()
        conn.close()
    else:
        # MySQL Initialization
        # First, connect without DB to create DB if it doesn't exist
        conn = pymysql.connect(
            host=st.session_state.mysql_host,
            port=int(st.session_state.mysql_port),
            user=st.session_state.mysql_user,
            password=st.session_state.mysql_password,
            charset='utf8mb4'
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {st.session_state.mysql_database}")
            conn.commit()
        finally:
            conn.close()
            
        # Connect to SCM database to build tables
        conn = get_mysql_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS customers (
                        customer_id VARCHAR(50) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100),
                        company VARCHAR(100),
                        address TEXT,
                        tier VARCHAR(20) DEFAULT 'Standard'
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id VARCHAR(50) PRIMARY KEY,
                        customer_id VARCHAR(50),
                        product_name VARCHAR(100) NOT NULL,
                        quantity INT NOT NULL,
                        total_price DECIMAL(10, 2) NOT NULL,
                        status VARCHAR(50) DEFAULT 'Processing',
                        order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS order_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        order_id VARCHAR(50),
                        phase VARCHAR(100),
                        agent_name VARCHAR(100),
                        action TEXT,
                        model_used VARCHAR(50),
                        cost_savings VARCHAR(50),
                        live_location VARCHAR(100),
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_reports (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        customer_id VARCHAR(50),
                        report_text LONGTEXT,
                        model_used VARCHAR(50),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    )
                """)
            conn.commit()
        finally:
            conn.close()

def seed_database():
    """Seeds the DB with professional mock data for a clean demonstration"""
    init_database()
    conn, cursor = get_db_cursor()
    try:
        # Check if empty
        if st.session_state.use_sqlite:
            cursor.execute("SELECT COUNT(*) as count FROM customers")
            count = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT COUNT(*) as count FROM customers")
            count = cursor.fetchone()['count']
            
        if count == 0:
            customers = [
                ('CUST-1001', 'Alex Rivera', 'alex.rivera@techcorp.com', 'TechCorp Industries', '1200 Innovation Way, San Jose, CA 95134', 'VIP'),
                ('CUST-1002', 'Sarah Chen', 's.chen@globallogistics.com', 'Global Logistics Corp', '45 Shipping Blvd, Seattle, WA 98101', 'Premium'),
                ('CUST-1003', 'Marcus Vance', 'marcus@apexretail.co.uk', 'Apex Retailers Ltd', '88 High Street, London EC1A 1BB, UK', 'Standard'),
                ('CUST-1004', 'Hana Tanaka', 'tanaka@pacificsource.co.jp', 'Pacific Sourcing Inc', '3-2-1 Ginza, Chuo-ku, Tokyo 104-0061, Japan', 'VIP')
            ]
            
            orders = [
                ('ORD-5001', 'CUST-1001', 'Enterprise Server Array Model X', 10, 150000.00, 'Fulfilled', '2026-05-19 10:00:00'),
                ('ORD-5002', 'CUST-1001', 'IoT Temperature Sensor Hubs', 150, 4500.00, 'Processing', '2026-05-21 08:30:00'),
                ('ORD-5003', 'CUST-1002', 'Robotic Sorting Arms', 3, 72000.00, 'Rerouted', '2026-05-20 14:15:00'),
                ('ORD-5004', 'CUST-1003', 'Biodegradable Packing Pellets (Bulk)', 50, 2500.00, 'Processing', '2026-05-21 11:00:00'),
                ('ORD-5005', 'CUST-1004', 'Multi-Gigabit Router Units', 20, 18000.00, 'Disrupted', '2026-05-21 09:15:00')
            ]
            
            history_records = [
                # ORD-5001 History
                ('ORD-5001', 'Order Intake Phase', 'UI (Customer Layer)', 'Order ORD-5001 successfully submitted by VIP Customer Alex Rivera.', 'Deterministic Engine', '$0.00', 'Shenzhen Manufacturing Facility', '2026-05-19 10:05:00'),
                ('ORD-5001', 'Order Assessment Phase', 'Supply Chain Intelligence', 'Assessment complete: Inventory available. Sourcing from Shenzhen plant.', 'Gemini 3.5 Flash', '$0.00', 'Shenzhen Manufacturing Facility', '2026-05-19 10:06:00'),
                ('ORD-5001', 'Regulatory Sandbox Verification', 'Verification & Compliance', 'Regulatory review passed. Customs classification verified.', 'Deterministic Engine', '$0.00', 'Shenzhen Manufacturing Facility', '2026-05-19 10:07:00'),
                ('ORD-5001', 'Logistics Planning Phase', 'Process Orchestration', 'Logistics plan generated: Shenzhen -> Shanghai -> San Jose. Maritime carrier booked.', 'Deterministic Engine', '$250.00 (Standard Carrier volume discount)', 'Shanghai Distribution Center', '2026-05-19 10:08:00'),
                ('ORD-5001', 'Autonomous Execution Phase', 'External Entities Node', 'Customs cleared in USA. Order delivered to TechCorp San Jose HQ.', 'Deterministic Engine', '$250.00', 'San Jose, CA (Delivered)', '2026-05-20 17:30:00'),
                
                # ORD-5003 History (Port strike disruption)
                ('ORD-5003', 'Order Intake Phase', 'UI (Customer Layer)', 'Order ORD-5003 submitted by Premium Customer Sarah Chen.', 'Deterministic Engine', '$0.00', 'Shanghai Distribution Center', '2026-05-20 14:16:00'),
                ('ORD-5003', 'Order Assessment Phase', 'Supply Chain Intelligence', 'Disruption alert: Port Strike at LA Port detected. Critical SLA breach risk of 95%.', 'Groq (Mixtral 8x7b)', '$0.00', 'Shanghai Distribution Center', '2026-05-20 14:17:00'),
                ('ORD-5003', 'Regulatory Sandbox Verification', 'Verification & Compliance', 'Sourcing complies with domestic rules. Trade insurance rider activated.', 'Deterministic Engine', '$0.00', 'Shanghai Distribution Center', '2026-05-20 14:17:30'),
                ('ORD-5003', 'Logistics Planning Phase', 'Process Orchestration', 'Carrier Booking Rejected (Port Overcapacity) at LA. Initiating self-correction...', 'Deterministic Engine', '$0.00', 'Port of Los Angeles (Congested)', '2026-05-20 14:18:00'),
                ('ORD-5003', 'Logistics Planning Phase (Reroute)', 'Process Orchestration', 'Self-Correction (Cycle 1): Rerouted cargo to Seattle Port Authority. Alternate carrier booked.', 'Graph Node Algorithm', '$0.00', 'Diverting: Seattle Port Authority', '2026-05-20 14:19:00'),
                ('ORD-5003', 'Autonomous Execution Phase', 'External Entities Node', 'Seattle Port cleared. Trucking dispatcher dispatched. SLA breach prevented successfully.', 'Deterministic Engine', '$12,450.00 (SLA Penalty Avoided)', 'Seattle Port Authority -> Seattle, WA', '2026-05-20 20:00:00'),
            ]
            
            ai_reports = [
                ('CUST-1001', '### Executive Supply Chain Report for TechCorp Industries\n\n**Prepared by:** SCM AI Director\n**Analysis Period:** May 2026\n\n#### 1. Performance Overview\n* **Total Active Orders:** 1 (`ORD-5002` - Processing)\n* **Completed Orders:** 1 (`ORD-5001` - Fulfilled)\n* **SLA Fulfillment Rate:** 100%\n\n#### 2. Risk Sourcing Assessment\nTechCorp’s supply chain is highly resilient. Recent shipments from Shenzhen to San Jose were completed within 36 hours utilizing high-speed ocean corridors. The current order `ORD-5002` is progressing normally through the Shanghai Distribution Center.\n\n#### 3. Financial Optimization Summary\n* **Accumulated Savings:** $250.00 (Standard Carrier Volume Discount).\n* **Potential Optimization:** Upgrading `ORD-5002` to air cargo is not required unless inventory thresholds fall below 5 units. SCM Agent recommends maintaining standard routing.', 'Gemini 3.5 Flash', '2026-05-21 11:30:00'),
                ('CUST-1002', '### Executive Supply Chain Report for Global Logistics Corp\n\n**Prepared by:** SCM AI Director\n**Analysis Period:** May 2026\n\n#### 1. Performance Overview\n* **Total Active Orders:** 0\n* **Completed Orders:** 1 (`ORD-5003` - Rerouted & Fulfilled)\n* **SLA Fulfillment Rate:** 100%\n\n#### 2. Risk Sourcing Assessment\nGlobal Logistics Corp faced a severe disruption risk with `ORD-5003` due to a port strike at the Port of Los Angeles. The SCM agent autonomously identified the disruption and executed alternative logistics routing.\n\n#### 3. Financial Optimization Summary\n* **Accumulated Savings:** $12,450.00 (SLA Penalty Avoided by Diverting to Seattle Port).\n* **Potential Optimization:** Agent recommends keeping Seattle Port Authority as a primary alternative routing option for Q3 2026 due to anticipated union negotiations at LA Port.', 'Groq (Mixtral 8x7b)', '2026-05-21 11:45:00')
            ]
            
            # Executing insertions
            if st.session_state.use_sqlite:
                cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", customers)
                cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", orders)
                cursor.executemany("INSERT INTO order_history (order_id, phase, agent_name, action, model_used, cost_savings, live_location, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", history_records)
                cursor.executemany("INSERT INTO ai_reports (customer_id, report_text, model_used, created_at) VALUES (?, ?, ?, ?)", ai_reports)
            else:
                cursor.executemany("INSERT INTO customers (customer_id, name, email, company, address, tier) VALUES (%s, %s, %s, %s, %s, %s)", customers)
                cursor.executemany("INSERT INTO orders (order_id, customer_id, product_name, quantity, total_price, status, order_date) VALUES (%s, %s, %s, %s, %s, %s, %s)", orders)
                cursor.executemany("INSERT INTO order_history (order_id, phase, agent_name, action, model_used, cost_savings, live_location, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", history_records)
                cursor.executemany("INSERT INTO ai_reports (customer_id, report_text, model_used, created_at) VALUES (%s, %s, %s, %s)", ai_reports)
            
            conn.commit()
            return True, "Database initialized and seeded successfully."
        else:
            return True, "Database already initialized and contains data."
    except Exception as e:
        return False, f"Seeding failed: {e}"
    finally:
        conn.close()

# Helper DB Queries
def get_customer(customer_id):
    conn, cursor = get_db_cursor()
    try:
        if st.session_state.use_sqlite:
            cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
            res = cursor.fetchone()
            return dict(res) if res else None
        else:
            cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
            res = cursor.fetchone()
            return res
    except Exception as e:
        st.error(f"Error querying customer: {e}")
        return None
    finally:
        conn.close()

def get_orders_by_customer(customer_id):
    conn, cursor = get_db_cursor()
    try:
        if st.session_state.use_sqlite:
            cursor.execute("SELECT * FROM orders WHERE customer_id = ? ORDER BY order_date DESC", (customer_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        else:
            cursor.execute("SELECT * FROM orders WHERE customer_id = %s ORDER BY order_date DESC", (customer_id,))
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        st.error(f"Error querying orders: {e}")
        return []
    finally:
        conn.close()

def get_order_history(order_id):
    conn, cursor = get_db_cursor()
    try:
        if st.session_state.use_sqlite:
            cursor.execute("SELECT * FROM order_history WHERE order_id = ? ORDER BY timestamp ASC", (order_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        else:
            cursor.execute("SELECT * FROM order_history WHERE order_id = %s ORDER BY timestamp ASC", (order_id,))
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        st.error(f"Error querying order history: {e}")
        return []
    finally:
        conn.close()

def get_all_order_history():
    conn, cursor = get_db_cursor()
    try:
        if st.session_state.use_sqlite:
            cursor.execute("SELECT * FROM order_history ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        else:
            cursor.execute("SELECT * FROM order_history ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        st.error(f"Error querying all logs: {e}")
        return []
    finally:
        conn.close()

def save_order_history_record(order_id, phase, agent_name, action, model_used, cost_savings, live_location):
    conn, cursor = get_db_cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if st.session_state.use_sqlite:
            cursor.execute("""
                INSERT INTO order_history (order_id, phase, agent_name, action, model_used, cost_savings, live_location, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, phase, agent_name, action, model_used, cost_savings, live_location, now_str))
        else:
            cursor.execute("""
                INSERT INTO order_history (order_id, phase, agent_name, action, model_used, cost_savings, live_location, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (order_id, phase, agent_name, action, model_used, cost_savings, live_location, now_str))
        conn.commit()
    except Exception as e:
        print(f"Error saving history record: {e}")
    finally:
        conn.close()

def insert_new_order(order_id, customer_id, product_name, quantity, total_price, status="Processing"):
    conn, cursor = get_db_cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if st.session_state.use_sqlite:
            cursor.execute("""
                INSERT INTO orders (order_id, customer_id, product_name, quantity, total_price, status, order_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_id, customer_id, product_name, quantity, total_price, status, now_str))
        else:
            cursor.execute("""
                INSERT INTO orders (order_id, customer_id, product_name, quantity, total_price, status, order_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (order_id, customer_id, product_name, quantity, total_price, status, now_str))
        conn.commit()
    except Exception as e:
        st.error(f"Error inserting order: {e}")
    finally:
        conn.close()

def update_order_status(order_id, status):
    conn, cursor = get_db_cursor()
    try:
        if st.session_state.use_sqlite:
            cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        else:
            cursor.execute("UPDATE orders SET status = %s WHERE order_id = %s", (status, order_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating order status: {e}")
    finally:
        conn.close()

def get_last_ai_report(customer_id):
    conn, cursor = get_db_cursor()
    try:
        if st.session_state.use_sqlite:
            cursor.execute("SELECT * FROM ai_reports WHERE customer_id = ? ORDER BY id DESC LIMIT 1", (customer_id,))
            res = cursor.fetchone()
            return dict(res) if res else None
        else:
            cursor.execute("SELECT * FROM ai_reports WHERE customer_id = %s ORDER BY id DESC LIMIT 1", (customer_id,))
            res = cursor.fetchone()
            return res
    except Exception as e:
        st.error(f"Error reading AI report: {e}")
        return None
    finally:
        conn.close()

def save_ai_report(customer_id, report_text, model_used):
    conn, cursor = get_db_cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if st.session_state.use_sqlite:
            cursor.execute("""
                INSERT INTO ai_reports (customer_id, report_text, model_used, created_at)
                VALUES (?, ?, ?, ?)
            """, (customer_id, report_text, model_used, now_str))
        else:
            cursor.execute("""
                INSERT INTO ai_reports (customer_id, report_text, model_used, created_at)
                VALUES (%s, %s, %s, %s)
            """, (customer_id, report_text, model_used, now_str))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving AI report: {e}")
    finally:
        conn.close()

# ==========================================
# 3. STATE GRAPH / AGENT WORKFLOW ENGINE
# ==========================================

class SCMState(TypedDict):
    order_id: str
    customer_id: str
    customer_tier: str
    current_phase: str
    inventory_status: str
    route_selected: str
    carrier_status: str
    optimization_cycles: int
    detected_disruptions: List[str]
    audit_trail: List[Dict[str, Any]]
    status: str
    requires_correction: bool
    simulate_disruption: bool
    cost_savings: str
    live_location: str
    agent_thoughts: Dict[str, str]

class SecurityGuards:
    @staticmethod
    def InputGuard(order_id: str, customer_id: str, disruptions: List[str]) -> bool:
        """Inspect context for prompt injections or SQL injection keywords."""
        malicious_patterns = [r"ignore all previous instructions", r"drop table", r"system prompt", r"UNION SELECT", r"OR 1=1"]
        for item in [order_id, customer_id] + disruptions:
            if not item: continue
            item_lower = item.lower()
            if any(re.search(pat, item_lower) for pat in malicious_patterns):
                return False
        return True

    @staticmethod
    def OutputGuard(response_text: str) -> bool:
        """Sanitize LLM output. Reject hazardous or error structures."""
        if not response_text or "Error" in response_text[:10] or "malicious" in response_text.lower():
            return False
        return True

def get_llm_client(prefer: str = "gemini"):
    """Instantiate the requested LLM with fallback option"""
    gemini_key = st.session_state.get("gemini_api_key", "").strip()
    groq_key = st.session_state.get("groq_api_key", "").strip()
    
    if prefer == "gemini" and gemini_key:
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=gemini_key,
                temperature=0.1
            ), "Gemini 2.5 Flash"
        except Exception as e:
            st.warning(f"Failed to initialize Gemini, falling back to Groq. Error: {e}")
            
    if groq_key:
        try:
            return ChatGroq(
                model="mixtral-8x7b-32768", 
                groq_api_key=groq_key,
                temperature=0.1
            ), "Groq Mixtral"
        except Exception as e:
            st.warning(f"Failed to initialize Groq. Error: {e}")
            
    if gemini_key:
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=gemini_key,
                temperature=0.1
            ), "Gemini 2.5 Flash"
        except Exception:
            pass
            
    return None, "Deterministic Fallback"

# WORKFLOW AGENTS
def user_interface_agent(state: SCMState) -> SCMState:
    state["current_phase"] = "Order Intake Phase"
    state["agent_thoughts"]["ui_agent"] = "UI Intake Agent: Verifying order specifications and checking payload safety."
    
    is_safe = SecurityGuards.InputGuard(state["order_id"], state["customer_id"], state["detected_disruptions"])
    if not is_safe:
        state["status"] = "Security Exception"
        state["detected_disruptions"] = ["Malicious input injection intercepted by Guard Layer."]
        state["requires_correction"] = True
        state["live_location"] = "System Quarantine"
        state["cost_savings"] = "$0.00"
        state["agent_thoughts"]["ui_agent"] = "⚠️ SECURITY THREAT INTERCEPTED: Input fails security inspection."
    else:
        state["live_location"] = "Shanghai Distribution Center (Intake)"
        state["agent_thoughts"]["ui_agent"] = f"Intake Successful: Customer tier rules for '{state['customer_tier']}' active. Initiating SCM workflow tracker."
        
    return state

def supply_chain_intelligence_agent(state: SCMState) -> SCMState:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Order Assessment Phase"
    disruptions = state.get("detected_disruptions", [])
    
    st.session_state.agent_running = "Supply Chain Intelligence"
    
    if disruptions:
        model, model_name = get_llm_client(prefer=st.session_state.routing_preference)
        
        # Simulated Vector Database Retrieval
        historical_solution = ""
        if "port strike" in " ".join(disruptions).lower() or "congestion" in " ".join(disruptions).lower():
            historical_solution = "Prior incident: Port congestion resolved by shifting freight to Seattle Port Authority and scheduling secondary rail/truck routes."
        elif "typhoon" in " ".join(disruptions).lower() or "weather" in " ".join(disruptions).lower():
            historical_solution = "Prior incident: Ocean route storm resolved by shifting priority logistics to air freight block or routing south of storm corridor."
            
        thought_log = f"Intelligence Agent: Threat Detected! Alert: {', '.join(disruptions)}. "
        if historical_solution:
            thought_log += f"Found historical mitigation: {historical_solution}. "
            
        if model:
            try:
                prompt = (
                    f"Analyze the following supply chain threat: {', '.join(disruptions)}. "
                    f"Historical memory references: {historical_solution}. "
                    f"Formulate a concise 1-2 sentence mitigation decision. Highlight target carrier adjustment or port diversion."
                )
                response = model.invoke(prompt)
                decision = str(response.content)
                
                if not SecurityGuards.OutputGuard(decision):
                    decision = "Output blocked by Guard rails. Reverting to SOP standard rerouting."
                
                thought_log += f"\nLLM Analysis ({model_name}): {decision}"
            except Exception as e:
                decision = f"LLM assessment errored: {e}. Executing standard SOP."
                thought_log += f"\nWarning: {decision}"
        else:
            decision = "No LLM Keys operational. Applying default Standard Operating Procedure: Reroute via nearest functional port hub."
            thought_log += f"\nFallback: {decision}"
            
        state["agent_thoughts"]["intelligence_agent"] = thought_log
        state["requires_correction"] = True
    else:
        state["agent_thoughts"]["intelligence_agent"] = "Intelligence Agent: Continuous tracking indicates routes are completely clear. SLA breach risk: <1%. Demand is stable."
        state["requires_correction"] = False
        
    return state

def compliance_agent(state: SCMState) -> SCMState:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Regulatory Sandbox Verification"
    st.session_state.agent_running = "Verification & Compliance"
    
    tier_info = f"Customer Tier: {state['customer_tier']}. "
    compliance_rules = "Checking export/import compliance for cargo. Verifying custom tariff filing codes."
    
    state["agent_thoughts"]["compliance_agent"] = f"Compliance Agent: {tier_info}{compliance_rules}\nImmutable audit trail locked in. Decision verified as compliant under international trade rules."
    return state

def orchestration_agent(state: SCMState) -> SCMState:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Logistics Planning Phase"
    st.session_state.agent_running = "Process Orchestration"
    
    cycles = state.get("optimization_cycles", 0)
    
    if cycles > 0:
        state["status"] = "Self-Correction Protocols Active"
        state["route_selected"] = f"Alternative Freight Route Beta-V{cycles}"
        state["inventory_status"] = "Alternative Supplier Pinged"
        state["live_location"] = "Diverting: Seattle Port Authority"
        state["cost_savings"] = "Calculating Recovery Optimizer..."
        
        state["agent_thoughts"]["orchestration_agent"] = (
            f"Orchestration Agent (Cycle {cycles}): Auto-Correction loop triggered. "
            f"Carrier booking failed on previous try. Rerouting to alternative supplier & port."
        )
    else:
        if state["detected_disruptions"]:
            state["status"] = "Logistics Rerouting"
            state["route_selected"] = "Optimized Alternative Corridor B"
            state["inventory_status"] = "Inventory Allocation Confirmed"
            state["live_location"] = "Awaiting Alternative Carrier (Singapore Hub)"
            state["cost_savings"] = "$4,250 (SLA Penalty Avoided)"
            
            state["agent_thoughts"]["orchestration_agent"] = (
                "Orchestration Agent: Threat flag active. Logistics plan adjusted to alternative ocean lane. "
                "Reserving stock at regional hub to avoid line delays."
            )
        else:
            state["status"] = "Order Processing"
            state["route_selected"] = "Standard Maritime Corridor"
            state["inventory_status"] = "Stock Reserved at Main Shenzhen Warehouse"
            state["live_location"] = "Origin: Shenzhen Plant"
            state["cost_savings"] = "$150.00 (Standard Tier discount)"
            
            state["agent_thoughts"]["orchestration_agent"] = (
                "Orchestration Agent: Standard parameters validated. Ocean corridor capacity open. "
                "Booking standard container carrier."
            )
            
    return state

def external_entities_node(state: SCMState) -> SCMState:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Autonomous Execution Phase"
    st.session_state.agent_running = "External Entities Simulation"
    
    # Trigger port rejection if simulated disruption and first cycle
    if state["simulate_disruption"] and state["optimization_cycles"] < 1:
        state["carrier_status"] = "Booking Rejected (Port Overcapacity/Strike)"
        state["live_location"] = "Port of Los Angeles (Congested/Rejected)"
        state["cost_savings"] = "$0.00 (SLA Penalty Risk)"
        state["optimization_cycles"] += 1
        state["agent_thoughts"]["external_entities"] = (
            "⚠️ EXTERNAL GATEWAY ALERT: Port Authority rejected booking at Port of Los Angeles. "
            "Port status: 100% capacity / Strike active. Returning error feedback loop..."
        )
    else:
        state["carrier_status"] = "Carrier Booking Confirmed"
        state["status"] = "Execution Fulfilled"
        
        if state["optimization_cycles"] > 0 or state["detected_disruptions"]:
            state["live_location"] = "Diverted: Oakland Port Terminal -> Seattle Terminal (Delivered)"
            state["cost_savings"] = "$12,450.00 (SLA Penalty Prevented + Dyn. Route optimization)"
            state["agent_thoughts"]["external_entities"] = (
                "External Entities Node: Dynamic logistics carrier confirmed alternative arrival. "
                "Warehouse picking & customs clearance processed. Delivery completed successfully!"
            )
        else:
            state["live_location"] = "Pacific Ocean Transit -> San Jose, CA (Delivered)"
            state["cost_savings"] = "$250.00 (Standard Volume Discount)"
            state["agent_thoughts"]["external_entities"] = (
                "External Entities Node: Ocean carrier confirmed boarding. "
                "Standard transit timelines met. Delivery completed."
            )
            
    return state

def orchestration_edge_router(state: SCMState) -> str:
    if state["status"] == "Security Exception":
        return "end"
    if state.get("carrier_status") == "Booking Rejected (Port Overcapacity/Strike)":
        return "loop_to_orchestration"
    return "end"

# COMPILE GRAPH
def build_scm_workflow():
    workflow = StateGraph(SCMState)
    
    workflow.add_node("ui_agent", user_interface_agent)
    workflow.add_node("intelligence_agent", supply_chain_intelligence_agent)
    workflow.add_node("compliance_agent", compliance_agent)
    workflow.add_node("orchestration_agent", orchestration_agent)
    workflow.add_node("external_entities", external_entities_node)
    
    workflow.set_entry_point("ui_agent")
    
    workflow.add_edge("ui_agent", "intelligence_agent")
    workflow.add_edge("intelligence_agent", "compliance_agent")
    workflow.add_edge("compliance_agent", "orchestration_agent")
    workflow.add_edge("orchestration_agent", "external_entities")
    
    workflow.add_conditional_edges(
        "external_entities",
        orchestration_edge_router,
        {
            "loop_to_orchestration": "orchestration_agent",
            "end": END
        }
    )
    
    return workflow.compile()

scm_workflow_graph = build_scm_workflow()

# ==========================================
# 4. INITIALIZE SESSION STATE
# ==========================================
if "use_sqlite" not in st.session_state:
    st.session_state.use_sqlite = True
if "mysql_host" not in st.session_state:
    st.session_state.mysql_host = "localhost"
if "mysql_port" not in st.session_state:
    st.session_state.mysql_port = "3306"
if "mysql_user" not in st.session_state:
    st.session_state.mysql_user = "root"
if "mysql_password" not in st.session_state:
    st.session_state.mysql_password = ""
if "mysql_database" not in st.session_state:
    st.session_state.mysql_database = "scm_agentic_db"
if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = False

# LLM Keys
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")
if "routing_preference" not in st.session_state:
    st.session_state.routing_preference = "gemini"

# Simulation/Workflow Active States
if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = None
if "workflow_history" not in st.session_state:
    st.session_state.workflow_history = []
if "agent_running" not in st.session_state:
    st.session_state.agent_running = ""

# Auto init DB if not done (SQLite is on by default and always ready)
if not st.session_state.db_initialized:
    try:
        init_database()
        seed_database()
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Failed to auto-initialize SQLite database: {e}")

# ==========================================
# 5. SIDEBAR: SETTINGS & DATABASES
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/color/120/000000/supply-chain.png", width=70)
    st.title("SCM Agent Control Panel")
    st.markdown("Configure SCM Multi-Agent network parameters and storage layers.")
    
    st.markdown("---")
    st.subheader("🔑 LLM Credentials")
    
    gemini_key_input = st.text_input(
        "Gemini API Key", 
        value=st.session_state.gemini_api_key, 
        type="password",
        help="Required for Gemini 2.5-flash agent modeling and AI executive summaries."
    )
    if gemini_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = gemini_key_input
        
    groq_key_input = st.text_input(
        "Groq API Key", 
        value=st.session_state.groq_api_key, 
        type="password",
        help="Required for Groq Mixtral speed-routing logic and text analysis."
    )
    if groq_key_input != st.session_state.groq_api_key:
        st.session_state.groq_api_key = groq_key_input
        
    st.session_state.routing_preference = st.selectbox(
        "Preferred AI Router",
        options=["gemini", "groq"],
        format_func=lambda x: "Google Gemini (Recommended)" if x == "gemini" else "Groq Mixtral Network"
    )
    
    st.markdown("---")
    st.subheader("💾 Database Selection")
    
    db_mode = st.radio(
        "Select Storage Layer",
        options=["MySQL Server", "Local SQLite Sandbox (Dev Mode)"],
        index=0 if not st.session_state.use_sqlite else 1
    )
    
    is_sqlite = (db_mode == "Local SQLite Sandbox (Dev Mode)")
    if is_sqlite != st.session_state.use_sqlite:
        st.session_state.use_sqlite = is_sqlite
        st.session_state.db_initialized = False
        st.rerun()
        
    if not st.session_state.use_sqlite:
        st.markdown("**MySQL Configuration Parameters:**")
        mysql_host = st.text_input("MySQL Host", value=st.session_state.mysql_host)
        mysql_port = st.text_input("MySQL Port", value=st.session_state.mysql_port)
        mysql_user = st.text_input("MySQL User", value=st.session_state.mysql_user)
        mysql_pass = st.text_input("MySQL Password", value=st.session_state.mysql_password, type="password")
        mysql_db = st.text_input("Database Name", value=st.session_state.mysql_database)
        
        # Save credentials in session state
        st.session_state.mysql_host = mysql_host
        st.session_state.mysql_port = mysql_port
        st.session_state.mysql_user = mysql_user
        st.session_state.mysql_password = mysql_pass
        st.session_state.mysql_database = mysql_db
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔌 Test MySQL Connection", use_container_width=True):
                success, msg = test_mysql_server(mysql_host, mysql_port, mysql_user, mysql_pass)
                if success:
                    st.success("Connection Successful!")
                else:
                    st.error(f"Connection Errored: {msg}")
        with col2:
            if st.button("🏗️ Initialize DB Schema", use_container_width=True):
                try:
                    init_database()
                    success, msg = seed_database()
                    if success:
                        st.success("MySQL schema seeded!")
                        st.session_state.db_initialized = True
                        st.rerun()
                    else:
                        st.error(msg)
                except Exception as e:
                    st.error(f"Init Error: {e}")
                    
    else:
        st.info("ℹ️ Running SQLite Sandbox database. It is self-contained and pre-seeded automatically.")
        if st.button("🔄 Reset SQLite Database", use_container_width=True):
            if os.path.exists("local_orders.db"):
                try:
                    os.remove("local_orders.db")
                except:
                    pass
            st.session_state.db_initialized = False
            st.rerun()
            
    st.markdown("---")
    st.caption("🌐 Built with LangGraph & Streamlit 1.45")

# ==========================================
# 6. HEADER DESIGN
# ==========================================
st.markdown("""
    <div class="header-container">
        <div class="header-title">🌐 Autonomous Supply Chain Intelligence Engine</div>
        <div class="header-subtitle">Multi-Agent SCM Orchestration System powered by LangGraph, Gemini & Groq</div>
    </div>
""", unsafe_allow_html=True)

# Check API status
api_status_cols = st.columns(3)
with api_status_cols[0]:
    if st.session_state.gemini_api_key:
        st.success("🟢 Gemini API Connection Enabled")
    else:
        st.warning("🟡 Gemini API Key is missing. Using Fallbacks.")
with api_status_cols[1]:
    if st.session_state.groq_api_key:
        st.success("🟢 Groq API Connection Enabled")
    else:
        st.warning("🟡 Groq API Key is missing. Using Fallbacks.")
with api_status_cols[2]:
    if st.session_state.use_sqlite:
        st.info("📦 Sandbox: SQLite Database Connected")
    else:
        try:
            conn = get_mysql_connection()
            conn.close()
            st.success(f"🟢 Storage: MySQL Database Connected ({st.session_state.mysql_database})")
        except:
            st.error("🔴 Storage: MySQL Connection Failed. Configure credentials.")

# ==========================================
# 7. MAIN TABS & VIEWPORTS
# ==========================================
tab_control, tab_audit, tab_report = st.tabs([
    "📈 SCM Control Center", 
    "🛡️ Decision Audit Trail Logs", 
    "📄 Executive AI Analytics Report"
])

# -----------------
# TAB 1: SCM CONTROL CENTER
# -----------------
with tab_control:
    st.markdown("### 🔍 Customer Order Profiler")
    
    # Search Customer Block
    col_search, col_suggest = st.columns([2, 3])
    with col_search:
        cust_id_input = st.text_input(
            "Enter Customer ID:", 
            value="CUST-1001",
            placeholder="e.g. CUST-1001",
            help="Input a customer ID to load their profiles and active orders."
        )
    with col_suggest:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        st.markdown("**Sample Customer Database Guides:** `CUST-1001` (VIP) | `CUST-1002` (Premium) | `CUST-1003` (Standard) | `CUST-1004` (VIP)")

    if cust_id_input:
        customer = get_customer(cust_id_input)
        if customer:
            st.session_state.selected_customer = customer
            
            # Display Customer Profile Card
            st.markdown(f"""
                <div class="scm-card">
                    <div class="scm-card-title">👤 Customer Profile: {customer['name']}</div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 0.5rem;">
                        <div><strong>Customer ID:</strong> {customer['customer_id']}</div>
                        <div><strong>Company:</strong> {customer['company']}</div>
                        <div><strong>Email:</strong> {customer['email']}</div>
                        <div><strong>SLA Tier:</strong> <span class="badge badge-{customer['tier'].lower()}">{customer['tier']}</span></div>
                    </div>
                    <div style="margin-top: 0.75rem;"><strong>Primary Shipping Address:</strong> {customer['address']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Fetch Customer Orders
            orders = get_orders_by_customer(customer['customer_id'])
            
            # Divide into two columns: Order Management & Simulation Running
            col_orders, col_simulator = st.columns([1, 1])
            
            with col_orders:
                st.markdown("#### 📦 Order Logistics Book")
                if orders:
                    # Format for nice presentation
                    formatted_orders = []
                    for o in orders:
                        status_badge = ""
                        if o['status'] in ["Fulfilled", "Delivered"]:
                            status_badge = f"🟢 {o['status']}"
                        elif o['status'] in ["Rerouted", "Processing"]:
                            status_badge = f"🟡 {o['status']}"
                        else:
                            status_badge = f"🔴 {o['status']}"
                        
                        formatted_orders.append({
                            "Order ID": o['order_id'],
                            "Product Name": o['product_name'],
                            "Qty": o['quantity'],
                            "Total Value": f"${float(o['total_price']):,.2f}",
                            "SLA Status": status_badge,
                            "Order Date": o['order_date']
                        })
                    st.dataframe(formatted_orders, use_container_width=True, hide_index=True)
                else:
                    st.warning("No orders found for this customer. Use the form on the right to place one!")
                
                # New Order Placement Form
                st.markdown("#### ➕ Create New Ship Order")
                with st.form("new_order_form"):
                    prod_name = st.selectbox(
                        "Select Product Item",
                        ["Enterprise Server Array Model X", "IoT Temperature Sensor Hubs", "Robotic Sorting Arms", "Multi-Gigabit Router Units"]
                    )
                    qty = st.number_input("Order Quantity", min_value=1, max_value=5000, value=10)
                    price_map = {
                        "Enterprise Server Array Model X": 15000.00,
                        "IoT Temperature Sensor Hubs": 30.00,
                        "Robotic Sorting Arms": 24000.00,
                        "Multi-Gigabit Router Units": 900.00
                    }
                    unit_price = price_map[prod_name]
                    total_price = unit_price * qty
                    
                    st.markdown(f"**Unit Price:** ${unit_price:,.2f} | **Total Order Est. Cost:** ${total_price:,.2f}")
                    
                    submitted = st.form_submit_button("🛒 Submit & Book Logistics Order")
                    if submitted:
                        new_ord_id = f"ORD-{int(time.time()) % 100000}"
                        insert_new_order(new_ord_id, customer['customer_id'], prod_name, qty, total_price)
                        st.success(f"Order {new_ord_id} successfully saved to DB. Ready for Agent Workflow evaluation!")
                        st.rerun()
            
            with col_simulator:
                st.markdown("#### ⚙️ Agentic SCM Runner")
                st.markdown("Configure agentic variables to test system resiliency during port or logistics delays.")
                
                # Choose which order to run SCM process on
                order_options = [o['order_id'] for o in orders if o['status'] != "Fulfilled"]
                all_order_options = [o['order_id'] for o in orders]
                
                if not order_options:
                    order_options = all_order_options
                
                if order_options:
                    selected_order_id = st.selectbox("Select Order ID for AI Assessment:", options=order_options)
                    simulate_disruption = st.checkbox(
                        "💥 Simulate External Port Congestion (SLA Risk)", 
                        value=False,
                        help="Check this to simulate a 3rd party carrier rejection / port overcapacity event. This triggers the agent's self-correcting routing loop!"
                    )
                    
                    if st.button("🚀 Execute Multi-Agent Workflow", type="primary", use_container_width=True):
                        # Find selected order details
                        ord_obj = next(o for o in orders if o['order_id'] == selected_order_id)
                        
                        # Initialize states
                        initial_state: SCMState = {
                            "order_id": selected_order_id,
                            "customer_id": customer['customer_id'],
                            "customer_tier": customer['tier'],
                            "current_phase": "Initializing",
                            "inventory_status": "Checking",
                            "route_selected": "Pending Evaluation",
                            "carrier_status": "Standby",
                            "optimization_cycles": 0,
                            "detected_disruptions": ["Severe Port Congestion (LA Port Terminal overload)"] if simulate_disruption else [],
                            "audit_trail": [],
                            "status": "Processing",
                            "requires_correction": False,
                            "simulate_disruption": simulate_disruption,
                            "cost_savings": "$0.00 (Calculating...)",
                            "live_location": "System Initiation",
                            "agent_thoughts": {}
                        }
                        
                        # Run workflow and display updates live!
                        st.markdown("#### 🟢 Active Agent Operations Panel")
                        
                        timeline_placeholder = st.empty()
                        metrics_placeholder = st.empty()
                        
                        # Run through LangGraph step-by-step
                        with st.spinner("Agentic SCM Workflow processing..."):
                            st.session_state.workflow_history = []
                            
                            # Custom execution runner for visual updates
                            current_state = initial_state
                            
                            # Step 1: UI Agent
                            current_state = user_interface_agent(current_state)
                            save_order_history_record(
                                current_state["order_id"],
                                current_state["current_phase"],
                                "UI (Customer Layer)",
                                current_state["agent_thoughts"]["ui_agent"],
                                "Deterministic Engine",
                                "$0.00",
                                current_state["live_location"]
                            )
                            st.session_state.workflow_history.append(dict(current_state))
                            time.sleep(1.0)
                            
                            # Step 2: Intel Agent
                            current_state = supply_chain_intelligence_agent(current_state)
                            _, model_used_name = get_llm_client(prefer=st.session_state.routing_preference)
                            save_order_history_record(
                                current_state["order_id"],
                                current_state["current_phase"],
                                "Supply Chain Intelligence",
                                current_state["agent_thoughts"]["intelligence_agent"],
                                model_used_name if current_state["detected_disruptions"] else "Deterministic Engine",
                                "$0.00",
                                current_state["live_location"]
                            )
                            st.session_state.workflow_history.append(dict(current_state))
                            time.sleep(1.2)
                            
                            # Step 3: Compliance Agent
                            current_state = compliance_agent(current_state)
                            save_order_history_record(
                                current_state["order_id"],
                                current_state["current_phase"],
                                "Verification & Compliance",
                                current_state["agent_thoughts"]["compliance_agent"],
                                "Regulatory Sandbox Ruleset",
                                "$0.00",
                                current_state["live_location"]
                            )
                            st.session_state.workflow_history.append(dict(current_state))
                            time.sleep(0.8)
                            
                            # Step 4: Orchestration Agent
                            current_state = orchestration_agent(current_state)
                            save_order_history_record(
                                current_state["order_id"],
                                current_state["current_phase"],
                                "Process Orchestration",
                                current_state["agent_thoughts"]["orchestration_agent"],
                                "Graph Node Algorithm",
                                current_state["cost_savings"],
                                current_state["live_location"]
                            )
                            st.session_state.workflow_history.append(dict(current_state))
                            time.sleep(1.0)
                            
                            # Step 5: External Entities (Simulate Carrier confirmation / booking)
                            current_state = external_entities_node(current_state)
                            save_order_history_record(
                                current_state["order_id"],
                                current_state["current_phase"],
                                "External Entities Node",
                                current_state["agent_thoughts"]["external_entities"],
                                "Supply Chain Sim Port Engine",
                                current_state["cost_savings"],
                                current_state["live_location"]
                            )
                            st.session_state.workflow_history.append(dict(current_state))
                            time.sleep(1.0)
                            
                            # Router conditional check
                            route_decision = orchestration_edge_router(current_state)
                            if route_decision == "loop_to_orchestration":
                                # Loopback triggered!
                                st.warning("🔄 Disruption Event Detected: Loopback Self-Correction Protocol Triggered!")
                                time.sleep(1.0)
                                
                                # Run Orchestration Agent again (Cycle 1)
                                current_state = orchestration_agent(current_state)
                                save_order_history_record(
                                    current_state["order_id"],
                                    current_state["current_phase"] + " (Correction)",
                                    "Process Orchestration",
                                    current_state["agent_thoughts"]["orchestration_agent"],
                                    "Graph Node Algorithm",
                                    "Calculating...",
                                    current_state["live_location"]
                                )
                                st.session_state.workflow_history.append(dict(current_state))
                                time.sleep(1.2)
                                
                                # Run External Entities again (Confirmed alternative)
                                current_state = external_entities_node(current_state)
                                save_order_history_record(
                                    current_state["order_id"],
                                    current_state["current_phase"] + " (Final Booking)",
                                    "External Entities Node",
                                    current_state["agent_thoughts"]["external_entities"],
                                    "Supply Chain Sim Port Engine",
                                    current_state["cost_savings"],
                                    current_state["live_location"]
                                )
                                st.session_state.workflow_history.append(dict(current_state))
                                time.sleep(1.0)
                                
                            # Update order table in DB with final status
                            update_order_status(current_state["order_id"], current_state["status"])
                            
                        st.success(f"SCM Workflow assessment complete for Order {selected_order_id}!")
                        
                        # Render final metrics
                        metrics_html = f"""
                            <div class="metric-grid">
                                <div class="metric-tile">
                                    <div class="metric-value">{current_state['status']}</div>
                                    <div class="metric-label">Execution Status</div>
                                </div>
                                <div class="metric-tile">
                                    <div class="metric-value">{current_state['cost_savings']}</div>
                                    <div class="metric-label">Operational Savings</div>
                                </div>
                                <div class="metric-tile">
                                    <div class="metric-value">{current_state['optimization_cycles']}</div>
                                    <div class="metric-label">Rerouting Cycles</div>
                                </div>
                                <div class="metric-tile">
                                    <div class="metric-value">{"< 0.1%" if current_state['status'] == "Execution Fulfilled" else "100%"}</div>
                                    <div class="metric-label">SLA Breach Risk</div>
                                </div>
                            </div>
                        """
                        metrics_placeholder.markdown(metrics_html, unsafe_allow_html=True)
                        
                        # Render beautiful timeline
                        timeline_html = "<div class='timeline-container'>"
                        for idx, step in enumerate(st.session_state.workflow_history):
                            is_last = (idx == len(st.session_state.workflow_history) - 1)
                            active_class = "active" if is_last else ""
                            
                            agent_name = ""
                            thought = ""
                            if "ui_agent" in step["agent_thoughts"] and idx == 0:
                                agent_name = "👤 User Interface / Order Intake Agent"
                                thought = step["agent_thoughts"]["ui_agent"]
                            elif "intelligence_agent" in step["agent_thoughts"] and idx == 1:
                                agent_name = "🧠 Supply Chain Intelligence Agent"
                                thought = step["agent_thoughts"]["intelligence_agent"]
                            elif "compliance_agent" in step["agent_thoughts"] and idx == 2:
                                agent_name = "🛡️ Verification & Compliance Agent"
                                thought = step["agent_thoughts"]["compliance_agent"]
                            elif "orchestration_agent" in step["agent_thoughts"] and idx == 3:
                                agent_name = "⚙️ Process Orchestration Agent"
                                thought = step["agent_thoughts"]["orchestration_agent"]
                            elif "external_entities" in step["agent_thoughts"] and idx == 4:
                                agent_name = "🚢 External Entities / Carrier Logistics Node"
                                thought = step["agent_thoughts"]["external_entities"]
                            elif idx == 5:
                                agent_name = "🔄 Process Orchestration (Dynamic Route Correction)"
                                thought = step["agent_thoughts"]["orchestration_agent"]
                            elif idx == 6:
                                agent_name = "🚢 External Carrier Logistics (Rerouted Gate Confirmed)"
                                thought = step["agent_thoughts"]["external_entities"]
                            
                            badge_color = "success" if "Delivered" in step['live_location'] or "Intake" in step['live_location'] else "warning"
                            if "Congested" in step['live_location'] or "Quarantine" in step['live_location']:
                                badge_color = "error"
                                
                            formatted_thought = thought.replace('\n', '<br>')
                            timeline_html += f"""
                                <div class="timeline-item {active_class}">
                                    <div class="timeline-title">{agent_name}</div>
                                    <div class="timeline-meta">
                                        <span>📍 Location: <span class="badge badge-{badge_color}">{step['live_location']}</span></span>
                                        <span>🔑 Routing Node: {step['current_phase']}</span>
                                    </div>
                                    <div class="timeline-content">{formatted_thought}</div>
                                </div>
                            """
                        timeline_html += "</div>"
                        timeline_placeholder.markdown(timeline_html, unsafe_allow_html=True)
                        
                else:
                    st.info("No orders currently active. Create an order above to test.")
        else:
            st.error("❌ Customer ID not found. Enter a valid ID like `CUST-1001` or seed the database in the sidebar.")

# -----------------
# TAB 2: DECISION AUDIT TRAIL LOGS
# -----------------
with tab_audit:
    st.markdown("### 🛡️ Immutable SCM Ledger Audit Trail")
    st.markdown("Every node decision, safety guard assessment, and external status update is securely recorded to the MySQL database engine.")
    
    col_audit_opt, _ = st.columns([2, 3])
    with col_audit_opt:
        search_filter = st.text_input("Filter logs by Order ID / Agent Name:", placeholder="e.g. ORD-5003")
        
    logs = get_all_order_history()
    
    if logs:
        # Filter logic
        filtered_logs = []
        for l in logs:
            if search_filter:
                match_str = f"{l['order_id']} {l['agent_name']} {l['phase']} {l['action']}".lower()
                if search_filter.lower() not in match_str:
                    continue
            filtered_logs.append({
                "Timestamp": l['timestamp'],
                "Order ID": l['order_id'],
                "Phase": l['phase'],
                "Agent Name": l['agent_name'],
                "LLM / Model Used": l['model_used'],
                "Carrier Location": l['live_location'],
                "Dynamic Savings": l['cost_savings'],
                "Agent Core Action & Output Details": l['action']
            })
            
        if filtered_logs:
            st.dataframe(filtered_logs, use_container_width=True, hide_index=True)
        else:
            st.info("No logs match the search query.")
    else:
        st.warning("Decision ledger is currently empty. Run a SCM simulation cycle to generate logs.")

# -----------------
# TAB 3: EXECUTIVE AI ANALYTICS REPORT
# -----------------
with tab_report:
    st.markdown("### 📄 Executive Supply Chain SCM AI Report")
    st.markdown("Generate a high-fidelity intelligence report analyzing recent shipping logs, disruption histories, and route optimizations for the selected customer.")
    
    if st.session_state.selected_customer:
        customer = st.session_state.selected_customer
        
        # Load last generated report
        saved_report = get_last_ai_report(customer['customer_id'])
        
        col_rep_btn, col_rep_info = st.columns([1, 2])
        with col_rep_btn:
            if st.button("🧠 Generate Executive AI Summary", type="primary", use_container_width=True):
                # Retrieve active customer data
                cust_orders = get_orders_by_customer(customer['customer_id'])
                
                # Fetch recent log trails
                all_logs = []
                for o in cust_orders:
                    ord_hist = get_order_history(o['order_id'])
                    all_logs.extend(ord_hist)
                
                # Compile summary prompt data
                order_summary_str = ""
                for o in cust_orders:
                    order_summary_str += f"- Order {o['order_id']}: Product={o['product_name']}, Qty={o['quantity']}, Value=${o['total_price']}, Status={o['status']}\n"
                    
                logs_summary_str = ""
                for l in all_logs[:15]:  # limit context
                    logs_summary_str += f"- [{l['timestamp']}] Order {l['order_id']} | Agent: {l['agent_name']} | Action: {l['action']} | Location: {l['live_location']} | Savings: {l['cost_savings']} | Model: {l['model_used']}\n"
                
                # Run through LLM
                model, model_name = get_llm_client(prefer=st.session_state.routing_preference)
                if model:
                    with st.spinner("Compiling database records and generating analysis report..."):
                        try:
                            prompt = f"""
                            You are the Director of Autonomous SCM Analytics. Generate an executive Supply Chain Health & Resiliency Report for the following customer.
                            
                            ### CUSTOMER PROFILE
                            - Name: {customer['name']}
                            - Company: {customer['company']}
                            - Tier: {customer['tier']}
                            - Address: {customer['address']}
                            
                            ### ACTIVE & PAST ORDERS
                            {order_summary_str}
                            
                            ### LOGISTICS AUDIT TRAIL LOGS
                            {logs_summary_str}
                            
                            ### REPORT REQUIREMENT INSTRUCTIONS:
                            Write a highly professional, elegant and comprehensive Supply Chain Performance Report in markdown format. Use bullet points and clean structure:
                            1. **Executive Operational Summary**: SCM health evaluation and overall reliability index (e.g. 98%).
                            2. **Risk & Sourcing Vulnerability Assessment**: Highlight recent disruption events (like port congestion), and how agents resolved them autonomously.
                            3. **Cost-Savings & Return-On-Investment (ROI)**: Quantify accumulated savings from dynamic rerouting, carriers volume discount, and SLA penalty avoidance.
                            4. **Strategic Recommendations**: Provide actionable next-quarter sourcing recommendations based on customer tier rules and global trade forecasts.
                            
                            Maintain an extremely polished corporate tone. Do not use conversational filler.
                            """
                            
                            response = model.invoke(prompt)
                            report_content = str(response.content)
                            
                            # Save to Database
                            save_ai_report(customer['customer_id'], report_content, model_name)
                            st.success("Executive AI Report compiled and saved to database!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Report generation errored: {e}")
                else:
                    st.error("❌ No LLM API connection active. Please input a Gemini or Groq API Key in the sidebar to enable AI Report generation.")
                    
        with col_rep_info:
            if saved_report:
                st.markdown(f"**Last Compiled:** `{saved_report['created_at']}` | **Model Engine:** `{saved_report['model_used']}`")
            else:
                st.info("No report exists in database for this customer yet. Click the button to compile one.")
                
        st.markdown("---")
        
        # Display the report
        if saved_report:
            # Layout the report inside a clean card
            st.markdown(f"""
                <div style="background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 2rem; margin-top: 1rem; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02);">
                    {saved_report['report_text']}
                </div>
            """, unsafe_allow_html=True)
            
            # Download actions
            st.download_button(
                label="📥 Download Report as Markdown Text",
                data=saved_report['report_text'],
                file_name=f"SCM_Executive_Report_{customer['customer_id']}.md",
                mime="text/markdown",
                use_container_width=True
            )
    else:
        st.warning("Select or search a valid Customer ID on the Control Center tab first.")
