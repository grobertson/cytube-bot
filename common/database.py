#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite database for bot state persistence and statistics tracking"""
import sqlite3
import logging
import time
from pathlib import Path


class BotDatabase:
    """Database for tracking bot state and user statistics"""
    
    def __init__(self, db_path='bot_data.db'):
        """Initialize database connection and create tables
        
        Args:
            db_path: Path to SQLite database file
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.logger.info('Connected to database: %s', self.db_path)
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # User statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                username TEXT PRIMARY KEY,
                first_seen INTEGER NOT NULL,
                last_seen INTEGER NOT NULL,
                total_chat_lines INTEGER DEFAULT 0,
                total_time_connected INTEGER DEFAULT 0,
                current_session_start INTEGER
            )
        ''')
        
        # User actions/PM log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                username TEXT NOT NULL,
                action_type TEXT NOT NULL,
                details TEXT
            )
        ''')
        
        # High water mark table (single row with channel stats)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                max_users INTEGER DEFAULT 0,
                max_users_timestamp INTEGER,
                max_connected INTEGER DEFAULT 0,
                max_connected_timestamp INTEGER,
                last_updated INTEGER
            )
        ''')
        
        # Initialize channel_stats if empty
        cursor.execute('SELECT COUNT(*) FROM channel_stats')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO channel_stats (id, max_users, last_updated)
                VALUES (1, 0, ?)
            ''', (int(time.time()),))
        else:
            # Migrate existing database - add new columns if they don't exist
            cursor.execute('PRAGMA table_info(channel_stats)')
            columns = [col[1] for col in cursor.fetchall()]
            if 'max_connected' not in columns:
                cursor.execute('''
                    ALTER TABLE channel_stats 
                    ADD COLUMN max_connected INTEGER DEFAULT 0
                ''')
            if 'max_connected_timestamp' not in columns:
                cursor.execute('''
                    ALTER TABLE channel_stats 
                    ADD COLUMN max_connected_timestamp INTEGER
                ''')
        
        self.conn.commit()
        self.logger.info('Database tables initialized')
    
    def user_joined(self, username):
        """Record a user joining the channel
        
        Args:
            username: Username that joined
        """
        cursor = self.conn.cursor()
        now = int(time.time())
        
        # Check if user exists
        cursor.execute('SELECT username FROM user_stats WHERE username = ?',
                      (username,))
        exists = cursor.fetchone() is not None
        
        if exists:
            # Update existing user - start new session
            cursor.execute('''
                UPDATE user_stats
                SET last_seen = ?,
                    current_session_start = ?
                WHERE username = ?
            ''', (now, now, username))
        else:
            # New user - create entry
            cursor.execute('''
                INSERT INTO user_stats
                (username, first_seen, last_seen, current_session_start)
                VALUES (?, ?, ?, ?)
            ''', (username, now, now, now))
        
        self.conn.commit()
    
    def user_left(self, username):
        """Record a user leaving the channel
        
        Args:
            username: Username that left
        """
        cursor = self.conn.cursor()
        now = int(time.time())
        
        # Get session start time
        cursor.execute('''
            SELECT current_session_start, total_time_connected
            FROM user_stats WHERE username = ?
        ''', (username,))
        
        row = cursor.fetchone()
        if row and row['current_session_start']:
            session_duration = now - row['current_session_start']
            new_total = row['total_time_connected'] + session_duration
            
            # Update user stats
            cursor.execute('''
                UPDATE user_stats
                SET last_seen = ?,
                    total_time_connected = ?,
                    current_session_start = NULL
                WHERE username = ?
            ''', (now, new_total, username))
            
            self.conn.commit()
    
    def user_chat_message(self, username):
        """Increment chat message count for user
        
        Args:
            username: Username that sent a message
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE user_stats
            SET total_chat_lines = total_chat_lines + 1,
                last_seen = ?
            WHERE username = ?
        ''', (int(time.time()), username))
        self.conn.commit()
    
    def log_user_action(self, username, action_type, details=None):
        """Log a user action (PM command, etc.)
        
        Args:
            username: Username performing the action
            action_type: Type of action (e.g., 'pm_command', 'kick', 'ban')
            details: Optional details about the action
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO user_actions
            (timestamp, username, action_type, details)
            VALUES (?, ?, ?, ?)
        ''', (int(time.time()), username, action_type, details))
        self.conn.commit()
    
    def update_high_water_mark(self, current_user_count, 
                               current_connected_count=None):
        """Update high water mark if current count exceeds it
        
        Args:
            current_user_count: Current number of users in chat
            current_connected_count: Current number of connected viewers
        """
        cursor = self.conn.cursor()
        now = int(time.time())
        
        # Get current max
        cursor.execute('''
            SELECT max_users, max_connected 
            FROM channel_stats WHERE id = 1
        ''')
        row = cursor.fetchone()
        current_max_users = row['max_users'] if row else 0
        current_max_connected = row['max_connected'] if row else 0
        
        updated = False
        
        # Update max users (chat) if exceeded
        if current_user_count > current_max_users:
            cursor.execute('''
                UPDATE channel_stats
                SET max_users = ?,
                    max_users_timestamp = ?,
                    last_updated = ?
                WHERE id = 1
            ''', (current_user_count, now, now))
            updated = True
            self.logger.info('New high water mark (chat): %d users', 
                           current_user_count)
        
        # Update max connected if exceeded
        if current_connected_count and current_connected_count > current_max_connected:
            cursor.execute('''
                UPDATE channel_stats
                SET max_connected = ?,
                    max_connected_timestamp = ?,
                    last_updated = ?
                WHERE id = 1
            ''', (current_connected_count, now, now))
            updated = True
            self.logger.info('New high water mark (connected): %d viewers', 
                           current_connected_count)
        
        if updated:
            self.conn.commit()
    
    def get_user_stats(self, username):
        """Get statistics for a specific user
        
        Args:
            username: Username to look up
            
        Returns:
            dict with user stats or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM user_stats WHERE username = ?
        ''', (username,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_high_water_mark(self):
        """Get the high water mark (max users ever in chat)
        
        Returns:
            tuple: (max_users, timestamp) or (0, None)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT max_users, max_users_timestamp
            FROM channel_stats WHERE id = 1
        ''')
        row = cursor.fetchone()
        
        if row:
            return (row['max_users'], row['max_users_timestamp'])
        return (0, None)
    
    def get_high_water_mark_connected(self):
        """Get the high water mark for connected viewers
        
        Returns:
            tuple: (max_connected, timestamp) or (0, None)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT max_connected, max_connected_timestamp
            FROM channel_stats WHERE id = 1
        ''')
        row = cursor.fetchone()
        
        if row:
            return (row['max_connected'], row['max_connected_timestamp'])
        return (0, None)
    
    def get_top_chatters(self, limit=10):
        """Get top chatters by message count
        
        Args:
            limit: Number of results to return
            
        Returns:
            list of tuples: (username, chat_lines)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT username, total_chat_lines
            FROM user_stats
            WHERE total_chat_lines > 0
            ORDER BY total_chat_lines DESC
            LIMIT ?
        ''', (limit,))
        
        return [(row['username'], row['total_chat_lines']) 
                for row in cursor.fetchall()]
    
    def get_total_users_seen(self):
        """Get total number of unique users ever seen
        
        Returns:
            int: Total unique users
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM user_stats')
        return cursor.fetchone()['count']
    
    def close(self):
        """Close database connection"""
        if self.conn:
            # Update any active sessions before closing
            cursor = self.conn.cursor()
            now = int(time.time())
            cursor.execute('''
                UPDATE user_stats
                SET total_time_connected = total_time_connected + (? - current_session_start),
                    current_session_start = NULL,
                    last_seen = ?
                WHERE current_session_start IS NOT NULL
            ''', (now, now))
            self.conn.commit()
            
            self.conn.close()
            self.logger.info('Database connection closed')
