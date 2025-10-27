import os
from typing import List, Optional, Tuple
import mysql.connector
from mysql.connector import pooling


class DBManager:
    """
    Pooled MySQL/MariaDB connector.
    Reads password from Docker secret file once at init.
    """

    def __init__(
        self,
        database: str | None = None,
        host: str | None = None,
        user: str | None = None,
        password_file: str | None = None,
        pool_name: str = "blogpool",
        pool_size: int = 5,
    ):
        self.database = database or os.getenv("MYSQL_DATABASE", "example")
        self.host = host or os.getenv("MYSQL_HOST", "db")
        self.user = user or os.getenv("MYSQL_USER", "root")
        self.password_file = password_file or os.getenv(
            "MYSQL_PASSWORD_FILE", "/run/secrets/db-password"
        )

        with open(self.password_file, "r") as pf:
            password = pf.read().strip()

        self.pool = pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            user=self.user,
            password=password,
            host=self.host,
            database=self.database,
            auth_plugin="mysql_native_password",
        )

    def _conn(self):
        return self.pool.get_connection()

    # ------- existing demo (blog) -------
    def populate_db(self) -> None:
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("DROP TABLE IF EXISTS blog")
            cur.execute(
                """
                CREATE TABLE blog (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255)
                )
                """
            )
            rows = [(i, f"Blog post #{i}") for i in range(1, 5)]
            cur.executemany("INSERT INTO blog (id, title) VALUES (%s, %s)", rows)
            conn.commit()
        finally:
            conn.close()

    def query_titles(self) -> List[str]:
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT title FROM blog")
            return [row[0] for row in cur.fetchall()]
        finally:
            conn.close()

    # ------- users table helpers -------
    def ensure_users_table(self) -> None:
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def insert_user(self, username: str, password_hash: str) -> int:
        """
        Returns inserted user id.
        Raises IntegrityError on duplicate username.
        """
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_user_by_username(self, username: str) -> Optional[Tuple[int, str, str]]:
        """
        Returns (id, username, created_at_str) or None.
        """
        conn = self._conn()
        try:
            cur = conn.cursor()
            # NOTE: Use %%S (uppercase) for seconds to avoid clashing with Python %s placeholder
            cur.execute(
                "SELECT id, username, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%S') "
                "FROM users WHERE username = %s",
                (username,),
            )
            row = cur.fetchone()
            return row if row else None
        finally:
            conn.close()

    def list_users(self) -> List[Tuple[int, str, str]]:
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%S') "
                "FROM users ORDER BY id ASC"
            )
            return cur.fetchall()
        finally:
            conn.close()

# --- add auth method inside class DBManager ---

    def get_user_auth(self, username: str) -> Optional[Tuple[int, str, str, str]]:
        """
        Returns (id, username, password_hash, created_at_str) or None.
        """
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, password_hash, "
                "DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%S') "
                "FROM users WHERE username = %s",
                (username,),
            )
            row = cur.fetchone()
            return row if row else None
        finally:
            conn.close()
