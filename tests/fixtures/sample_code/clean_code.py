"""Sample well-written code that should have minimal findings."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Represents a user in the system.

    Attributes:
        id: Unique identifier for the user.
        name: User's display name.
        email: User's email address.
        is_active: Whether the user account is active.
    """

    id: int
    name: str
    email: str
    is_active: bool = True


class UserRepository:
    """Repository for user data access.

    Provides methods to fetch and store user data using
    parameterized queries to prevent SQL injection.
    """

    def __init__(self, database_connection):
        """Initialize the repository with a database connection.

        Args:
            database_connection: Active database connection instance.
        """
        self._db = database_connection

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch a user by their ID.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            User instance if found, None otherwise.
        """
        query = "SELECT id, name, email, is_active FROM users WHERE id = ?"
        result = self._db.execute(query, (user_id,))

        if result:
            return User(**result)
        return None

    def get_active_users(self) -> list[User]:
        """Fetch all active users.

        Returns:
            List of active User instances.
        """
        query = "SELECT id, name, email, is_active FROM users WHERE is_active = ?"
        results = self._db.execute_many(query, (True,))

        return [User(**row) for row in results]

    def save(self, user: User) -> bool:
        """Save a user to the database.

        Args:
            user: User instance to save.

        Returns:
            True if save was successful, False otherwise.
        """
        query = """
            INSERT INTO users (id, name, email, is_active)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                is_active = EXCLUDED.is_active
        """

        return self._db.execute(
            query,
            (user.id, user.name, user.email, user.is_active),
        )


def find_duplicates(items: list) -> set:
    """Find duplicate items in a list efficiently.

    Uses a set for O(n) time complexity.

    Args:
        items: List of items to check for duplicates.

    Returns:
        Set of items that appear more than once.
    """
    seen = set()
    duplicates = set()

    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)

    return duplicates


def calculate_average(values: list[float]) -> float:
    """Calculate the average of a list of values.

    Args:
        values: List of numeric values.

    Returns:
        The arithmetic mean of the values.

    Raises:
        ValueError: If the list is empty.
    """
    if not values:
        raise ValueError("Cannot calculate average of empty list")

    return sum(values) / len(values)
