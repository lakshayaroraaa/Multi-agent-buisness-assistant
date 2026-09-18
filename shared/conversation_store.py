"""Cosmos DB persistence for orchestrator conversation turns."""

from __future__ import annotations

import os
from typing import Any

from shared.schemas import ConversationTurn


class ConversationStore:
    """Store and retrieve turns, partitioned by ``session_id`` in Cosmos DB."""

    def __init__(self, container: Any) -> None:
        self._container = container

    @classmethod
    def from_environment(cls) -> "ConversationStore":
        from azure.cosmos import CosmosClient, PartitionKey

        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        database_name = os.getenv("COSMOS_DATABASE_NAME")
        container_name = os.getenv("COSMOS_CONTAINER_NAME")
        missing = [name for name, value in {
            "COSMOS_ENDPOINT": endpoint, "COSMOS_KEY": key,
            "COSMOS_DATABASE_NAME": database_name, "COSMOS_CONTAINER_NAME": container_name,
        }.items() if not value]
        if missing:
            raise RuntimeError(f"Missing Cosmos configuration: {', '.join(missing)}.")
        client = CosmosClient(endpoint, credential=key)
        database = client.create_database_if_not_exists(id=database_name)
        container = database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/session_id"),
        )
        return cls(container)

    def save_turn(self, turn: ConversationTurn) -> None:
        self._container.upsert_item(turn.model_dump(mode="json"))

    def get_recent_history(self, session_id: str, turns: int = 5) -> list[ConversationTurn]:
        if not session_id.strip():
            raise ValueError("session_id must not be blank.")
        if turns < 1:
            raise ValueError("turns must be at least 1.")
        items = list(self._container.query_items(
            query="SELECT TOP @turns * FROM c WHERE c.session_id = @session_id ORDER BY c.timestamp DESC",
            parameters=[
                {"name": "@turns", "value": turns},
                {"name": "@session_id", "value": session_id},
            ],
            partition_key=session_id,
        ))
        return [ConversationTurn.model_validate(item) for item in reversed(items)]


class InMemoryConversationStore:
    """Small test double with the same public contract as ``ConversationStore``."""

    def __init__(self) -> None:
        self._turns: dict[str, list[ConversationTurn]] = {}

    def save_turn(self, turn: ConversationTurn) -> None:
        self._turns.setdefault(turn.session_id, []).append(turn)

    def get_recent_history(self, session_id: str, turns: int = 5) -> list[ConversationTurn]:
        return self._turns.get(session_id, [])[-turns:]
