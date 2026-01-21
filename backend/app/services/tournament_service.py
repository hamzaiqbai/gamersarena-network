"""
Tournament Service
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
from datetime import datetime

from ..models.tournament import Tournament, TournamentStatus
from ..models.registration import Registration, RegistrationStatus
from ..models.wallet import Wallet
from ..models.transaction import Transaction, TransactionType, TransactionStatus
from .wallet_service import WalletService


class TournamentService:
    """Service for tournament operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.wallet_service = WalletService(db)
    
    def get_tournament(self, tournament_id: UUID) -> Optional[Tournament]:
        """Get tournament by ID"""
        return self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    def get_tournament_by_slug(self, slug: str) -> Optional[Tournament]:
        """Get tournament by slug"""
        return self.db.query(Tournament).filter(Tournament.slug == slug).first()
    
    def list_tournaments(
        self,
        game: str = None,
        status: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Tournament], int]:
        """List tournaments with filtering"""
        query = self.db.query(Tournament)
        
        if game:
            query = query.filter(Tournament.game == game)
        
        if status:
            query = query.filter(Tournament.status == status)
        else:
            # Default: show active tournaments
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
        
        return tournaments, total
    
    def register_user(
        self,
        user_id: UUID,
        tournament_id: UUID,
        player_id: str = None,
        team_name: str = None
    ) -> Tuple[bool, str, Optional[Registration]]:
        """Register a user for a tournament"""
        tournament = self.get_tournament(tournament_id)
        
        if not tournament:
            return False, "Tournament not found", None
        
        if not tournament.is_registration_open:
            return False, "Registration is not open", None
        
        # Check existing registration
        existing = self.db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.tournament_id == tournament_id,
            Registration.status != RegistrationStatus.CANCELLED.value
        ).first()
        
        if existing:
            return False, "Already registered", None
        
        # Deduct tokens
        success, transaction = self.wallet_service.deduct_tokens(
            user_id=user_id,
            amount=tournament.entry_fee,
            description=f"Entry fee for {tournament.title}",
            tournament_id=tournament_id
        )
        
        if not success:
            return False, "Insufficient token balance", None
        
        # Create registration
        registration = Registration(
            user_id=user_id,
            tournament_id=tournament_id,
            tokens_paid=tournament.entry_fee,
            player_id=player_id,
            team_name=team_name,
            transaction_id=transaction.id,
            status=RegistrationStatus.CONFIRMED.value
        )
        
        self.db.add(registration)
        tournament.current_participants += 1
        
        self.db.commit()
        self.db.refresh(registration)
        
        return True, "Registration successful", registration
    
    def get_user_registrations(
        self,
        user_id: UUID,
        status: str = None
    ) -> List[Registration]:
        """Get user's tournament registrations"""
        query = self.db.query(Registration).filter(Registration.user_id == user_id)
        
        if status:
            query = query.filter(Registration.status == status)
        
        return query.order_by(Registration.registered_at.desc()).all()
    
    def get_participants(self, tournament_id: UUID) -> List[Registration]:
        """Get tournament participants"""
        return self.db.query(Registration).filter(
            Registration.tournament_id == tournament_id,
            Registration.status.in_([
                RegistrationStatus.CONFIRMED.value,
                RegistrationStatus.CHECKED_IN.value
            ])
        ).all()
    
    def distribute_rewards(
        self,
        tournament_id: UUID,
        results: List[dict]  # [{"user_id": ..., "position": 1, "reward": 100}, ...]
    ) -> bool:
        """Distribute rewards to tournament winners"""
        tournament = self.get_tournament(tournament_id)
        
        if not tournament:
            return False
        
        for result in results:
            user_id = result["user_id"]
            position = result["position"]
            reward = result["reward"]
            
            # Update registration
            registration = self.db.query(Registration).filter(
                Registration.user_id == user_id,
                Registration.tournament_id == tournament_id
            ).first()
            
            if registration:
                registration.set_result(position, reward)
                
                if reward > 0:
                    # Add reward tokens
                    wallet, transaction = self.wallet_service.add_tokens(
                        user_id=user_id,
                        amount=reward,
                        token_type="reward",
                        description=f"Prize for {tournament.title} - Position #{position}",
                        transaction_type=TransactionType.TOURNAMENT_REWARD.value
                    )
                    registration.reward_transaction_id = transaction.id
        
        # Update tournament status
        tournament.status = TournamentStatus.COMPLETED.value
        
        self.db.commit()
        return True
