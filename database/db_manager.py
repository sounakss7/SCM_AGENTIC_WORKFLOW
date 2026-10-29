import os
import streamlit as st
try:
    import pymysql
except ImportError:
    pymysql = None
import sqlite3
from datetime import datetime

def is_using_sqlite() -> bool:
    """Check whether SQLite mode is active with safe fallbacks."""
    try:
        if hasattr(st, "session_state") and "use_sqlite" in st.session_state:
            return bool(st.session_state.use_sqlite)
    except Exception:
        pass
    return os.getenv("USE_SQLITE", "true").lower() in ("true", "1", "yes")

def get_mysql_config():
    """Retrieve MySQL connection configuration with session_state and env fallbacks."""
    try:
        if hasattr(st, "session_state"):
            host = st.session_state.get("mysql_host", os.getenv("MYSQL_HOST", "localhost"))
            port = int(st.session_state.get("mysql_port", os.getenv("MYSQL_PORT", "3306")))
            user = st.session_state.get("mysql_user", os.getenv("MYSQL_USER", "root"))
            password = st.session_state.get("mysql_password", os.getenv("MYSQL_PASSWORD", ""))
            database = st.session_state.get("mysql_database", os.getenv("MYSQL_DATABASE", "scm_agentic_db"))
            return host, port, user, password, database
    except Exception:
        pass
    return (
        os.getenv("MYSQL_HOST", "localhost"),
        int(os.getenv("MYSQL_PORT", "3306")),
        os.getenv("MYSQL_USER", "root"),
        os.getenv("MYSQL_PASSWORD", ""),
        os.getenv("MYSQL_DATABASE", "scm_agentic_db")
    )

# Connection helper
def get_mysql_connection():
    host, port, user, password, database = get_mysql_config()
    try:
        return pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        raise ConnectionError(f"MySQL connection failed: {e}")

def get_db_cursor():
    """Returns database connection and cursor, falling back to SQLite if MySQL is disabled/unconfigured"""
    if is_using_sqlite():
        conn = sqlite3.connect("local_orders.db", timeout=30.0, check_same_thread=False)
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
    if is_using_sqlite():
        conn = sqlite3.connect("local_orders.db", timeout=30.0)
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routing_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                cycle INTEGER DEFAULT 0,
                plan_id TEXT,
                origin_supplier TEXT,
                port TEXT,
                warehouse TEXT,
                destination_retailer TEXT,
                carrier TEXT,
                total_cost REAL,
                cost_delta REAL,
                transit_days REAL,
                status TEXT,
                rejection_reason TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                threat_type TEXT,
                payload TEXT,
                agent_name TEXT,
                action_taken TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()
    else:
        # MySQL Initialization
        host, port, user, password, database = get_mysql_config()
        # First, connect without DB to create DB if it doesn't exist
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
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
                        name VARCHAR(255) NOT NULL,
                        email VARCHAR(255),
                        company VARCHAR(255),
                        address TEXT,
                        tier VARCHAR(50) DEFAULT 'Standard'
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id VARCHAR(50) PRIMARY KEY,
                        customer_id VARCHAR(50),
                        product_name VARCHAR(255) NOT NULL,
                        quantity INT NOT NULL,
                        total_price DECIMAL(12, 2) NOT NULL,
                        status VARCHAR(50) DEFAULT 'Processing',
                        order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS order_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        order_id VARCHAR(50),
                        phase VARCHAR(255),
                        agent_name VARCHAR(255),
                        action TEXT,
                        model_used VARCHAR(100),
                        cost_savings VARCHAR(255),
                        live_location VARCHAR(255),
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_reports (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        customer_id VARCHAR(50),
                        report_text LONGTEXT,
                        model_used VARCHAR(100),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS routing_decisions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        order_id VARCHAR(50),
                        cycle INT DEFAULT 0,
                        plan_id VARCHAR(50),
                        origin_supplier VARCHAR(50),
                        port VARCHAR(50),
                        warehouse VARCHAR(50),
                        destination_retailer VARCHAR(50),
                        carrier VARCHAR(50),
                        total_cost DECIMAL(12, 2),
                        cost_delta DECIMAL(12, 2),
                        transit_days DECIMAL(6, 2),
                        status VARCHAR(50),
                        rejection_reason TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS security_audit (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        order_id VARCHAR(50),
                        threat_type VARCHAR(100),
                        payload TEXT,
                        agent_name VARCHAR(100),
                        action_taken VARCHAR(100),
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
        if is_using_sqlite():
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
                ('ORD-5001', 'Order Assessment Phase', 'Supply Chain Intelligence', 'Assessment complete: Inventory available. Sourcing from Shenzhen plant.', 'Gemini 2.5 Flash', '$0.00', 'Shenzhen Manufacturing Facility', '2026-05-19 10:06:00'),
                ('ORD-5001', 'Regulatory Sandbox Verification', 'Verification & Compliance', 'Regulatory review passed. Customs classification verified.', 'Deterministic Engine', '$0.00', 'Shenzhen Manufacturing Facility', '2026-05-19 10:07:00'),
                ('ORD-5001', 'Logistics Planning Phase', 'Process Orchestration', 'Logistics plan generated: Shenzhen -> Shanghai -> San Jose. Maritime carrier booked.', 'Deterministic Engine', '$250.00 (Standard Carrier volume discount)', 'Shanghai Distribution Center', '2026-05-19 10:08:00'),
                ('ORD-5001', 'Autonomous Execution Phase', 'External Entities Node', 'Customs cleared in USA. Order delivered to TechCorp San Jose HQ.', 'Deterministic Engine', '$250.00', 'San Jose, CA (Delivered)', '2026-05-20 17:30:00'),
                
                # ORD-5003 History (Port strike disruption)
                ('ORD-5003', 'Order Intake Phase', 'UI (Customer Layer)', 'Order ORD-5003 submitted by Premium Customer Sarah Chen.', 'Deterministic Engine', '$0.00', 'Shanghai Distribution Center', '2026-05-20 14:16:00'),
                ('ORD-5003', 'Order Assessment Phase', 'Supply Chain Intelligence', 'Disruption alert: Port Strike at LA Port detected. Critical SLA breach risk of 95%.', 'Groq (Llama 3.3)', '$0.00', 'Shanghai Distribution Center', '2026-05-20 14:17:00'),
                ('ORD-5003', 'Regulatory Sandbox Verification', 'Verification & Compliance', 'Sourcing complies with domestic rules. Trade insurance rider activated.', 'Deterministic Engine', '$0.00', 'Shanghai Distribution Center', '2026-05-20 14:17:30'),
                ('ORD-5003', 'Logistics Planning Phase', 'Process Orchestration', 'Carrier Booking Rejected (Port Overcapacity) at LA. Initiating self-correction...', 'Deterministic Engine', '$0.00', 'Port of Los Angeles (Congested)', '2026-05-20 14:18:00'),
                ('ORD-5003', 'Logistics Planning Phase (Reroute)', 'Process Orchestration', 'Self-Correction (Cycle 1): Rerouted cargo to Seattle Port Authority. Alternate carrier booked.', 'Graph Node Algorithm', '$0.00', 'Diverting: Seattle Port Authority', '2026-05-20 14:19:00'),
                ('ORD-5003', 'Autonomous Execution Phase', 'External Entities Node', 'Seattle Port cleared. Trucking dispatcher dispatched. SLA breach prevented successfully.', 'Deterministic Engine', '$12,450.00 (SLA Penalty Avoided)', 'Seattle Port Authority -> Seattle, WA', '2026-05-20 20:00:00'),
            ]
            
            ai_reports = [
                ('CUST-1001', '### Executive Supply Chain Report for TechCorp Industries\n\n**Prepared by:** SCM AI Director\n**Analysis Period:** May 2026\n\n#### 1. Performance Overview\n* **Total Active Orders:** 1 (`ORD-5002` - Processing)\n* **Completed Orders:** 1 (`ORD-5001` - Fulfilled)\n* **SLA Fulfillment Rate:** 100%\n\n#### 2. Risk Sourcing Assessment\nTechCorp’s supply chain is highly resilient. Recent shipments from Shenzhen to San Jose were completed within 36 hours utilizing high-speed ocean corridors. The current order `ORD-5002` is progressing normally through the Shanghai Distribution Center.\n\n#### 3. Financial Optimization Summary\n* **Accumulated Savings:** $250.00 (Standard Carrier Volume Discount).\n* **Potential Optimization:** Upgrading `ORD-5002` to air cargo is not required unless inventory thresholds fall below 5 units. SCM Agent recommends maintaining standard routing.', 'Gemini 2.5 Flash', '2026-05-21 11:30:00'),
                ('CUST-1002', '### Executive Supply Chain Report for Global Logistics Corp\n\n**Prepared by:** SCM AI Director\n**Analysis Period:** May 2026\n\n#### 1. Performance Overview\n* **Total Active Orders:** 0\n* **Completed Orders:** 1 (`ORD-5003` - Rerouted & Fulfilled)\n* **SLA Fulfillment Rate:** 100%\n\n#### 2. Risk Sourcing Assessment\nGlobal Logistics Corp faced a severe disruption risk with `ORD-5003` due to a port strike at the Port of Los Angeles. The SCM agent autonomously identified the disruption and executed alternative logistics routing.\n\n#### 3. Financial Optimization Summary\n* **Accumulated Savings:** $12,450.00 (SLA Penalty Avoided by Diverting to Seattle Port).\n* **Potential Optimization:** Agent recommends keeping Seattle Port Authority as a primary alternative routing option for Q3 2026 due to anticipated union negotiations at LA Port.', 'Groq (Llama 3.3)', '2026-05-21 11:45:00')
            ]
            
            # Executing insertions
            if is_using_sqlite():
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

def reset_database():
    """Completely resets and re-seeds the active database (SQLite or MySQL)."""
    try:
        if is_using_sqlite():
            conn = sqlite3.connect("local_orders.db", timeout=30.0)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("DROP TABLE IF EXISTS ai_reports")
            cursor.execute("DROP TABLE IF EXISTS order_history")
            cursor.execute("DROP TABLE IF EXISTS orders")
            cursor.execute("DROP TABLE IF EXISTS customers")
            conn.commit()
            conn.close()
        else:
            conn = get_mysql_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                    cursor.execute("DROP TABLE IF EXISTS ai_reports")
                    cursor.execute("DROP TABLE IF EXISTS order_history")
                    cursor.execute("DROP TABLE IF EXISTS orders")
                    cursor.execute("DROP TABLE IF EXISTS customers")
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                conn.commit()
            finally:
                conn.close()
        return seed_database()
    except Exception as e:
        return False, f"Database reset failed: {e}"


# Helper DB Queries
def get_customer(customer_id):
    if not customer_id:
        return None
    conn, cursor = get_db_cursor()
    try:
        if is_using_sqlite():
            cursor.execute("SELECT * FROM customers WHERE UPPER(customer_id) = UPPER(?)", (customer_id.strip(),))
            res = cursor.fetchone()
            return dict(res) if res else None
        else:
            cursor.execute("SELECT * FROM customers WHERE UPPER(customer_id) = UPPER(%s)", (customer_id.strip(),))
            res = cursor.fetchone()
            return res
    except Exception as e:
        if hasattr(st, "error"):
            st.error(f"Error querying customer: {e}")
        return None
    finally:
        conn.close()

def get_orders_by_customer(customer_id):
    if not customer_id:
        return []
    conn, cursor = get_db_cursor()
    try:
        if is_using_sqlite():
            cursor.execute("SELECT * FROM orders WHERE UPPER(customer_id) = UPPER(?) ORDER BY order_date DESC", (customer_id.strip(),))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        else:
            cursor.execute("SELECT * FROM orders WHERE UPPER(customer_id) = UPPER(%s) ORDER BY order_date DESC", (customer_id.strip(),))
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        if hasattr(st, "error"):
            st.error(f"Error querying orders: {e}")
        return []
    finally:
        conn.close()

def get_order_history(order_id):
    if not order_id:
        return []
    conn, cursor = get_db_cursor()
    try:
        if is_using_sqlite():
            cursor.execute("SELECT * FROM order_history WHERE order_id = ? ORDER BY timestamp ASC", (order_id.strip(),))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        else:
            cursor.execute("SELECT * FROM order_history WHERE order_id = %s ORDER BY timestamp ASC", (order_id.strip(),))
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        if hasattr(st, "error"):
            st.error(f"Error querying order history: {e}")
        return []
    finally:
        conn.close()

def get_all_order_history(limit=50):
    conn, cursor = get_db_cursor()
    try:
        if is_using_sqlite():
            cursor.execute("SELECT * FROM order_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        else:
            cursor.execute("SELECT * FROM order_history ORDER BY id DESC LIMIT %s", (limit,))
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        if hasattr(st, "error"):
            st.error(f"Error querying all logs: {e}")
        return []
    finally:
        conn.close()

def save_order_history_record(order_id, phase, agent_name, action, model_used, cost_savings, live_location):
    conn, cursor = get_db_cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if is_using_sqlite():
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
        if is_using_sqlite():
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
        if hasattr(st, "error"):
            st.error(f"Error inserting order: {e}")
    finally:
        conn.close()

def update_order_status(order_id, status):
    conn, cursor = get_db_cursor()
    try:
        if is_using_sqlite():
            cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        else:
            cursor.execute("UPDATE orders SET status = %s WHERE order_id = %s", (status, order_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating order status: {e}")
    finally:
        conn.close()

def get_last_ai_report(customer_id):
    if not customer_id:
        return None
    conn, cursor = get_db_cursor()
    try:
        if is_using_sqlite():
            cursor.execute("SELECT * FROM ai_reports WHERE UPPER(customer_id) = UPPER(?) ORDER BY id DESC LIMIT 1", (customer_id.strip(),))
            res = cursor.fetchone()
            return dict(res) if res else None
        else:
            cursor.execute("SELECT * FROM ai_reports WHERE UPPER(customer_id) = UPPER(%s) ORDER BY id DESC LIMIT 1", (customer_id.strip(),))
            res = cursor.fetchone()
            return res
    except Exception as e:
        if hasattr(st, "error"):
            st.error(f"Error reading AI report: {e}")
        return None
    finally:
        conn.close()

def save_ai_report(customer_id, report_text, model_used):
    conn, cursor = get_db_cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if is_using_sqlite():
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
        if hasattr(st, "error"):
            st.error(f"Error saving AI report: {e}")
    finally:
        conn.close()

def insert_new_customer(customer_id, name, email, company, address, tier="Standard"):
    conn, cursor = get_db_cursor()
    try:
        clean_id = customer_id.strip().upper()
        if is_using_sqlite():
            cursor.execute("""
                INSERT INTO customers (customer_id, name, email, company, address, tier)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (clean_id, name, email, company, address, tier))
        else:
            cursor.execute("""
                INSERT INTO customers (customer_id, name, email, company, address, tier)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (clean_id, name, email, company, address, tier))
        conn.commit()
        return True, f"Customer {clean_id} registered successfully."
    except Exception as e:
        return False, f"Failed to register customer: {e}"
    finally:
        conn.close()



def save_routing_decision(order_id, cycle, plan_dict, status="PROPOSED", rejection_reason=None):
    """Save a routing decision to MySQL/SQLite audit trail with parameterized query."""
    if not plan_dict:
        return
    conn, cursor = get_db_cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plan_id = str(plan_dict.get("plan_id", ""))
        origin = str(plan_dict.get("origin_supplier_id") or plan_dict.get("supplier", ""))
        port = str(plan_dict.get("port_id") or plan_dict.get("port", ""))
        warehouse = str(plan_dict.get("warehouse_id") or plan_dict.get("warehouse", ""))
        dest = str(plan_dict.get("destination_retailer_id") or plan_dict.get("retailer", ""))
        carrier = str(plan_dict.get("carrier", ""))
        total_cost = float(plan_dict.get("total_cost_inr", plan_dict.get("total_cost", 0.0)))
        cost_delta = float(plan_dict.get("cost_delta_inr", plan_dict.get("cost_delta", 0.0)))
        transit_days = float(plan_dict.get("total_transit_days", 0.0))
        rej_str = str(rejection_reason) if rejection_reason else None

        if is_using_sqlite():
            cursor.execute("""
                INSERT INTO routing_decisions (order_id, cycle, plan_id, origin_supplier, port, warehouse, destination_retailer, carrier, total_cost, cost_delta, transit_days, status, rejection_reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, int(cycle), plan_id, origin, port, warehouse, dest, carrier, total_cost, cost_delta, transit_days, status, rej_str, now_str))
        else:
            cursor.execute("""
                INSERT INTO routing_decisions (order_id, cycle, plan_id, origin_supplier, port, warehouse, destination_retailer, carrier, total_cost, cost_delta, transit_days, status, rejection_reason, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (order_id, int(cycle), plan_id, origin, port, warehouse, dest, carrier, total_cost, cost_delta, transit_days, status, rej_str, now_str))
        conn.commit()
    except Exception as e:
        print(f"Error saving routing decision: {e}")
    finally:
        conn.close()

def get_routing_decisions(order_id):
    """Retrieve all routing decisions for an order from SQL database."""
    if not order_id:
        return []
    conn, cursor = get_db_cursor()
    try:
        if is_using_sqlite():
            cursor.execute("SELECT * FROM routing_decisions WHERE order_id = ? ORDER BY id ASC", (order_id.strip(),))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        else:
            cursor.execute("SELECT * FROM routing_decisions WHERE order_id = %s ORDER BY id ASC", (order_id.strip(),))
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        print(f"Error querying routing decisions: {e}")
        return []
    finally:
        conn.close()

def save_security_audit_record(order_id, threat_type, payload, agent_name, action_taken="QUARANTINED"):
    """Save a security threat incident to MySQL/SQLite audit trail with parameterized query."""
    conn, cursor = get_db_cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_payload = str(payload)[:500]
        if is_using_sqlite():
            cursor.execute("""
                INSERT INTO security_audit (order_id, threat_type, payload, agent_name, action_taken, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, threat_type, safe_payload, agent_name, action_taken, now_str))
        else:
            cursor.execute("""
                INSERT INTO security_audit (order_id, threat_type, payload, agent_name, action_taken, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, threat_type, safe_payload, agent_name, action_taken, now_str))
        conn.commit()
    except Exception as e:
        print(f"Error saving security audit record: {e}")
    finally:
        conn.close()

def get_security_audit_records(order_id=None, limit=50):
    """Retrieve security threat audit records from SQL database."""
    conn, cursor = get_db_cursor()
    try:
        if isinstance(order_id, int):
            limit = order_id
            order_id = None

        if order_id:
            if is_using_sqlite():
                cursor.execute("SELECT * FROM security_audit WHERE order_id = ? ORDER BY id DESC LIMIT ?", (order_id, limit))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            else:
                cursor.execute("SELECT * FROM security_audit WHERE order_id = %s ORDER BY id DESC LIMIT %s", (order_id, limit))
                rows = cursor.fetchall()
                return rows
        else:
            if is_using_sqlite():
                cursor.execute("SELECT * FROM security_audit ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            else:
                cursor.execute("SELECT * FROM security_audit ORDER BY id DESC LIMIT %s", (limit,))
                rows = cursor.fetchall()
                return rows
    except Exception as e:
        print(f"Error querying security audit records: {e}")
        return []
    finally:
        conn.close()

def log_agent_step(order_id, phase, agent_name, action, model_used="Deterministic Engine", cost_savings="$0.00", live_location="N/A"):
    """High-level helper to log an agent execution step to SQL database audit trail."""
    return save_order_history_record(order_id, phase, agent_name, action, model_used, cost_savings, live_location)
