import sqlite3

def initialize(database_connection: sqlite3.Connection):
    cursor: sqlite3.Cursor = database_connection.cursor()
    cursor.execute("""
        create table if not exists `registered_users` (
          `id` integer not null primary key autoincrement,
          `user_id` int not null,
          `guild_id` int not null,
          `support_channel_id` int not null
        )
    """)

# Returns True if the passed Discord user is registered in a selected Guild, otherwise returns False.
def is_user_registered(database_connection: sqlite3.Connection, user_id: int, guild_id: int) -> bool:
    cursor: sqlite3.Cursor = database_connection.cursor()
    cursor.execute("SELECT id FROM registered_users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))

    if not cursor.fetchone():
        return False

    return True


# Registers a new user to the SQLite database.
def register_user(database_connection: sqlite3.Connection, user_id: int, guild_id: int, support_channel_id: int):
    cursor: sqlite3.Cursor = database_connection.cursor()
    cursor.execute("INSERT INTO registered_users (user_id, guild_id, support_channel_id) VALUES (?, ?, ?)", (user_id, guild_id, support_channel_id))
    database_connection.commit()
