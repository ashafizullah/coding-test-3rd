"""
Chat API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
from datetime import datetime, timezone
from app.db.session import get_db
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ConversationCreate,
    Conversation,
    ChatMessage
)
from app.services.query_engine import QueryEngine
from app.models.conversation import Conversation as ConversationModel
from app.models.conversation import ConversationMessage as ConversationMessageModel

router = APIRouter()


@router.post("/query", response_model=ChatQueryResponse)
async def process_chat_query(
    request: ChatQueryRequest,
    db: Session = Depends(get_db)
):
    """Process a chat query using RAG"""

    # Get conversation history if conversation_id provided
    conversation_history = []
    conversation_db = None

    if request.conversation_id:
        conversation_db = db.query(ConversationModel).filter(
            ConversationModel.conversation_id == request.conversation_id
        ).first()

        if conversation_db:
            # Load message history
            messages = db.query(ConversationMessageModel).filter(
                ConversationMessageModel.conversation_id == conversation_db.id
            ).order_by(ConversationMessageModel.timestamp).all()

            conversation_history = [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in messages
            ]

    # Process query
    query_engine = QueryEngine(db)
    response = await query_engine.process_query(
        query=request.query,
        fund_id=request.fund_id,
        conversation_history=conversation_history
    )

    # Save conversation history to database
    if request.conversation_id:
        if not conversation_db:
            # Create new conversation
            conversation_db = ConversationModel(
                conversation_id=request.conversation_id,
                fund_id=request.fund_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(conversation_db)
            db.commit()
            db.refresh(conversation_db)

        # Save user message
        user_message = ConversationMessageModel(
            conversation_id=conversation_db.id,
            role="user",
            content=request.query,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(user_message)

        # Save assistant message with metadata
        assistant_message = ConversationMessageModel(
            conversation_id=conversation_db.id,
            role="assistant",
            content=response["answer"],
            metadata={
                "sources": [
                    {"content": src.get("content", ""), "metadata": src.get("metadata", {})}
                    for src in response.get("sources", [])
                ],
                "metrics": response.get("metrics"),
                "processing_time": response.get("processing_time")
            },
            timestamp=datetime.now(timezone.utc)
        )
        db.add(assistant_message)

        # Update conversation timestamp
        conversation_db.updated_at = datetime.now(timezone.utc)

        db.commit()

    return ChatQueryResponse(**response)


@router.post("/conversations", response_model=Conversation)
async def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())

    # Create conversation in database
    conversation_db = ConversationModel(
        conversation_id=conversation_id,
        fund_id=request.fund_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(conversation_db)
    db.commit()
    db.refresh(conversation_db)

    return Conversation(
        conversation_id=conversation_id,
        fund_id=request.fund_id,
        messages=[],
        created_at=conversation_db.created_at,
        updated_at=conversation_db.updated_at
    )


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get conversation history"""
    conversation_db = db.query(ConversationModel).filter(
        ConversationModel.conversation_id == conversation_id
    ).first()

    if not conversation_db:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Load messages
    messages = db.query(ConversationMessageModel).filter(
        ConversationMessageModel.conversation_id == conversation_db.id
    ).order_by(ConversationMessageModel.timestamp).all()

    return Conversation(
        conversation_id=conversation_id,
        fund_id=conversation_db.fund_id,
        messages=[
            ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            )
            for msg in messages
        ],
        created_at=conversation_db.created_at,
        updated_at=conversation_db.updated_at
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    conversation_db = db.query(ConversationModel).filter(
        ConversationModel.conversation_id == conversation_id
    ).first()

    if not conversation_db:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete conversation (cascade will delete messages)
    db.delete(conversation_db)
    db.commit()

    return {"message": "Conversation deleted successfully"}
