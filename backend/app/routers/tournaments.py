"""
Tournaments Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.wallet import Wallet
from ..models.tournament import Tournament, TournamentStatus
from ..models.registration import Registration, RegistrationStatus
from ..models.transaction import Transaction, TransactionType, TransactionStatus
from ..schemas.tournament import (
    TournamentResponse,
    TournamentDetailResponse,
    TournamentListResponse,
    RegistrationRequest,
    RegistrationResponse,
    RegistrationWithTournament,
    ParticipantResponse
)
from ..utils.security import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])


@router.get("", response_model=TournamentListResponse)
async def list_tournaments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    game: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    List all tournaments with optional filtering.
    Public endpoint - no auth required.
    """
    query = db.query(Tournament)
    
    # Filter by game
    if game:
        query = query.filter(Tournament.game == game)
    
    # Filter by status
    if status_filter:
        query = query.filter(Tournament.status == status_filter)
    else:
        # By default, show upcoming and active tournaments
        query = query.filter(
            Tournament.status.in_([
                TournamentStatus.UPCOMING.value,
                TournamentStatus.REGISTRATION_OPEN.value,
                TournamentStatus.ACTIVE.value
            ])
        )
    
    total = query.count()
    
    tournaments = query.order_by(Tournament.start_date.asc())\
        .offset((page - 1) * per_page)\
        .limit(per_page)\
        .all()
    
    return TournamentListResponse(
        tournaments=[TournamentResponse.model_validate(t.to_dict()) for t in tournaments],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/my-registrations", response_model=List[RegistrationWithTournament])
async def get_my_registrations(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's tournament registrations"""
    query = db.query(Registration).filter(Registration.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Registration.status == status_filter)
    
    registrations = query.order_by(Registration.registered_at.desc()).all()
    
    return [
        RegistrationWithTournament(
            **reg.to_dict(),
            tournament=TournamentResponse.model_validate(reg.tournament.to_dict())
        )
        for reg in registrations
    ]


@router.get("/{tournament_id}")
async def get_tournament(
    tournament_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get tournament details.
    If user is registered, includes room info.
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    
    response = tournament.to_dict()
    response["user_registered"] = False
    response["user_registration"] = None
    
    # Check if user is registered
    if current_user:
        registration = db.query(Registration).filter(
            Registration.user_id == current_user.id,
            Registration.tournament_id == tournament.id
        ).first()
        
        if registration:
            response["user_registered"] = True
            response["user_registration"] = registration.to_dict()
            # Include room info for registered users after registration closes
            if tournament.status in [TournamentStatus.ACTIVE.value, TournamentStatus.REGISTRATION_CLOSED.value]:
                response["room_id"] = tournament.room_id
                response["room_password"] = tournament.room_password
    
    return response


@router.post("/{tournament_id}/register", response_model=RegistrationResponse)
async def register_for_tournament(
    tournament_id: str,
    registration_data: RegistrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register for a tournament.
    Deducts entry fee tokens from user's wallet.
    """
    # Get tournament
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    
    # Check if registration is open
    if not tournament.is_registration_open:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration is not open for this tournament"
        )
    
    # Check if already registered
    existing_reg = db.query(Registration).filter(
        Registration.user_id == current_user.id,
        Registration.tournament_id == tournament.id,
        Registration.status != RegistrationStatus.CANCELLED.value
    ).first()
    
    if existing_reg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already registered for this tournament"
        )
    
    # Get user's wallet
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Check balance
    if not wallet.has_sufficient_balance(tournament.entry_fee):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "insufficient_balance",
                "message": "Insufficient token balance",
                "required": tournament.entry_fee,
                "available": wallet.total_balance
            }
        )
    
    # Record balance before
    balance_before = wallet.total_balance
    
    # Deduct tokens
    wallet.deduct_tokens(tournament.entry_fee)
    
    # Create registration
    player_id = registration_data.player_id or current_user.player_id
    
    registration = Registration(
        user_id=current_user.id,
        tournament_id=tournament.id,
        tokens_paid=tournament.entry_fee,
        player_id=player_id,
        team_name=registration_data.team_name,
        status=RegistrationStatus.CONFIRMED.value
    )
    db.add(registration)
    
    # Update tournament participant count
    tournament.current_participants += 1
    
    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        type=TransactionType.TOURNAMENT_ENTRY.value,
        status=TransactionStatus.COMPLETED.value,
        token_amount=tournament.entry_fee,
        tournament_id=tournament.id,
        description=f"Entry fee for {tournament.title}",
        balance_before=balance_before,
        balance_after=wallet.total_balance
    )
    transaction.mark_completed()
    db.add(transaction)
    
    # Link transaction to registration
    db.flush()
    registration.transaction_id = transaction.id
    
    db.commit()
    db.refresh(registration)
    
    return registration


@router.get("/{tournament_id}/participants", response_model=List[ParticipantResponse])
async def get_participants(
    tournament_id: str,
    db: Session = Depends(get_db)
):
    """Get list of tournament participants"""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    
    registrations = db.query(Registration).filter(
        Registration.tournament_id == tournament.id,
        Registration.status.in_([
            RegistrationStatus.CONFIRMED.value,
            RegistrationStatus.CHECKED_IN.value
        ])
    ).all()
    
    participants = []
    for reg in registrations:
        participants.append(ParticipantResponse(
            id=reg.user.id,
            full_name=reg.user.full_name,
            avatar_url=reg.user.avatar_url,
            player_id=reg.player_id,
            team_name=reg.team_name,
            position=reg.position,
            reward_earned=reg.reward_earned,
            checked_in=reg.checked_in
        ))
    
    return participants


@router.post("/{tournament_id}/check-in")
async def check_in(
    tournament_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check in for a tournament"""
    registration = db.query(Registration).filter(
        Registration.user_id == current_user.id,
        Registration.tournament_id == tournament_id
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found"
        )
    
    if registration.checked_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked in"
        )
    
    registration.check_in()
    db.commit()
    
    return {"message": "Checked in successfully"}
