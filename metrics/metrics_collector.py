"""
AUTOBOT Metrics Collection System
Advanced metrics collection with automatic database creation and performance tracking
"""
import os
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'metrics.db')
DB_DIR = os.path.dirname(DB_PATH)

# Thread lock for database operations
db_lock = threading.Lock()

def ensure_database_exists():
    """Create database and tables if they don't exist"""
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT NOT NULL,
                    duration REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    status_code INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    request_size INTEGER DEFAULT 0,
                    response_size INTEGER DEFAULT 0
                )
            ''')
            
            # Create operation metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    duration REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # Create system metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    active_connections INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create error logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    endpoint TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create performance indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_timestamp ON api_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_endpoint ON api_metrics(endpoint)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation_timestamp ON operation_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_timestamp ON error_logs(timestamp)')
            
            # Create cleanup trigger for old data (keep last 30 days)
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS cleanup_old_metrics
                AFTER INSERT ON api_metrics
                BEGIN
                    DELETE FROM api_metrics WHERE timestamp < datetime('now', '-30 days');
                    DELETE FROM operation_metrics WHERE timestamp < datetime('now', '-30 days');
                    DELETE FROM system_metrics WHERE timestamp < datetime('now', '-30 days');
                    DELETE FROM error_logs WHERE timestamp < datetime('now', '-30 days');
                END
            ''')
            
            conn.commit()
            logger.info("Metrics database initialized successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize metrics database: {e}")

@contextmanager
def get_db_connection():
    """Thread-safe database connection context manager"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()

def collect_api_metrics(endpoint: str, duration: float, success: bool, status_code: int = 200, 
                       request_size: int = 0, response_size: int = 0):
    """Collect API performance metrics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO api_metrics (endpoint, duration, success, status_code, request_size, response_size)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (endpoint, duration, success, status_code, request_size, response_size))
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to collect API metrics: {e}")

def collect_metrics(operation: str, duration: float, success: bool, metadata: Dict[str, Any] = None):
    """Collect general operation metrics"""
    try:
        metadata_json = json.dumps(metadata) if metadata else None
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO operation_metrics (operation, duration, success, metadata)
                VALUES (?, ?, ?, ?)
            ''', (operation, duration, success, metadata_json))
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to collect operation metrics: {e}")

def log_operation(operation: str):
    """Simple operation logging"""
    logger.info(f"Operation started: {operation}")

def collect_system_metrics():
    """Collect system performance metrics"""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Count active network connections (approximate)
        try:
            connections = len(psutil.net_connections(kind='inet'))
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            connections = 0
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_metrics (cpu_percent, memory_percent, disk_percent, active_connections)
                VALUES (?, ?, ?, ?)
            ''', (cpu_percent, memory.percent, disk.percent, connections))
            conn.commit()
            
    except ImportError:
        logger.warning("psutil not available - system metrics collection disabled")
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")

def log_error(error_type: str, error_message: str, stack_trace: str = None, endpoint: str = None):
    """Log errors to the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO error_logs (error_type, error_message, stack_trace, endpoint)
                VALUES (?, ?, ?, ?)
            ''', (error_type, error_message, stack_trace, endpoint))
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to log error to database: {e}")

def get_metrics_summary(hours: int = 24) -> Dict[str, Any]:
    """Get comprehensive metrics summary"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # API metrics summary
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(duration) as avg_duration,
                    MAX(duration) as max_duration,
                    MIN(duration) as min_duration,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_requests
                FROM api_metrics 
                WHERE timestamp > ?
            ''', (cutoff_time,))
            
            api_stats = dict(cursor.fetchone())
            
            # Top endpoints by request count
            cursor.execute('''
                SELECT endpoint, COUNT(*) as count, AVG(duration) as avg_duration
                FROM api_metrics 
                WHERE timestamp > ?
                GROUP BY endpoint
                ORDER BY count DESC
                LIMIT 10
            ''', (cutoff_time,))
            
            top_endpoints = [dict(row) for row in cursor.fetchall()]
            
            # Recent errors
            cursor.execute('''
                SELECT error_type, error_message, endpoint, timestamp
                FROM error_logs
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (cutoff_time,))
            
            recent_errors = [dict(row) for row in cursor.fetchall()]
            
            # System metrics (latest)
            cursor.execute('''
                SELECT cpu_percent, memory_percent, disk_percent, active_connections, timestamp
                FROM system_metrics
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            
            system_stats = cursor.fetchone()
            system_stats = dict(system_stats) if system_stats else {}
            
            # Performance trends (hourly averages for the last 24 hours)
            cursor.execute('''
                SELECT 
                    strftime('%H', timestamp) as hour,
                    AVG(duration) as avg_duration,
                    COUNT(*) as request_count
                FROM api_metrics
                WHERE timestamp > ?
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            ''', (cutoff_time,))
            
            performance_trends = [dict(row) for row in cursor.fetchall()]
            
            return {
                'period_hours': hours,
                'api_stats': api_stats,
                'top_endpoints': top_endpoints,
                'recent_errors': recent_errors,
                'system_stats': system_stats,
                'performance_trends': performance_trends,
                'generated_at': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to generate metrics summary: {e}")
        return {'error': str(e)}

def get_health_metrics() -> Dict[str, Any]:
    """Get current health status based on metrics"""
    try:
        cutoff_time = datetime.now() - timedelta(minutes=5)  # Last 5 minutes
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Recent error rate
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
                FROM api_metrics 
                WHERE timestamp > ?
            ''', (cutoff_time,))
            
            row = cursor.fetchone()
            total_requests = row[0] if row else 0
            error_count = row[1] if row else 0
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
            
            # Average response time
            cursor.execute('''
                SELECT AVG(duration) as avg_duration
                FROM api_metrics 
                WHERE timestamp > ? AND success = 1
            ''', (cutoff_time,))
            
            avg_duration = cursor.fetchone()[0] or 0
            
            # System status
            cursor.execute('''
                SELECT cpu_percent, memory_percent, disk_percent
                FROM system_metrics
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            
            system_row = cursor.fetchone()
            
            # Determine health status
            health_score = 100
            issues = []
            
            if error_rate > 10:
                health_score -= 30
                issues.append(f"High error rate: {error_rate:.1f}%")
            
            if avg_duration > 5:
                health_score -= 20
                issues.append(f"Slow response time: {avg_duration:.2f}s")
            
            if system_row:
                cpu, memory, disk = system_row
                if cpu > 80:
                    health_score -= 20
                    issues.append(f"High CPU usage: {cpu:.1f}%")
                if memory > 80:
                    health_score -= 20
                    issues.append(f"High memory usage: {memory:.1f}%")
                if disk > 90:
                    health_score -= 10
                    issues.append(f"High disk usage: {disk:.1f}%")
            
            status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"
            
            return {
                'status': status,
                'health_score': max(0, health_score),
                'error_rate': error_rate,
                'avg_response_time': avg_duration,
                'total_requests_5min': total_requests,
                'issues': issues,
                'system': dict(system_row) if system_row else None
            }
            
    except Exception as e:
        logger.error(f"Failed to get health metrics: {e}")
        return {
            'status': 'unknown',
            'error': str(e)
        }

def cleanup_old_metrics(days: int = 30):
    """Manually cleanup old metrics data"""
    try:
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Clean up old data
            cursor.execute('DELETE FROM api_metrics WHERE timestamp < ?', (cutoff_time,))
            api_deleted = cursor.rowcount
            
            cursor.execute('DELETE FROM operation_metrics WHERE timestamp < ?', (cutoff_time,))
            operation_deleted = cursor.rowcount
            
            cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff_time,))
            system_deleted = cursor.rowcount
            
            cursor.execute('DELETE FROM error_logs WHERE timestamp < ?', (cutoff_time,))
            error_deleted = cursor.rowcount
            
            conn.commit()
            
            # Vacuum database to reclaim space
            cursor.execute('VACUUM')
            
            logger.info(f"Cleaned up metrics older than {days} days: "
                       f"API={api_deleted}, Operations={operation_deleted}, "
                       f"System={system_deleted}, Errors={error_deleted}")
            
            return {
                'api_deleted': api_deleted,
                'operation_deleted': operation_deleted,
                'system_deleted': system_deleted,
                'error_deleted': error_deleted
            }
            
    except Exception as e:
        logger.error(f"Failed to cleanup old metrics: {e}")
        return {'error': str(e)}

# Initialize database on module import
ensure_database_exists()

# Start system metrics collection in background
def start_system_metrics_collection(interval: int = 60):
    """Start background system metrics collection"""
    def collect_loop():
        while True:
            try:
                collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"System metrics collection error: {e}")
                time.sleep(interval)
    
    thread = threading.Thread(target=collect_loop, daemon=True)
    thread.start()
    logger.info(f"Started system metrics collection (interval: {interval}s)")

if __name__ == "__main__":
    # Test the metrics system
    print("Testing metrics system...")
    
    # Test basic operations
    collect_api_metrics("/test", 0.5, True, 200)
    collect_metrics("test_operation", 1.2, True, {"test": "data"})
    log_error("TestError", "This is a test error", "Stack trace here", "/test")
    
    # Get summary
    summary = get_metrics_summary(1)  # Last hour
    print(f"Metrics summary: {json.dumps(summary, indent=2, default=str)}")
    
    # Get health
    health = get_health_metrics()
    print(f"Health status: {health}")
    
    print("Metrics system test completed!")