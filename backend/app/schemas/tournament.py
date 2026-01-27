"""
Tournament Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TournamentBase(BaseModel):
    """Base tournament schema"""
    title: str
    game: str
    description: Optional[str] = None
    rules: Optional[str] = None
    entry_fee: int = 0
    prize_pool: int = 0


class TournamentCreate(TournamentBase):
    """Schema for creating a tournament (admin)"""
    slug: str
    first_place_reward: int = 0
    second_place_reward: int = 0
    third_place_reward: int = 0
    fourth_place_reward: int = 0
    fifth_place_reward: int = 0
    max_participants: int = 100
    min_participants: int = 2
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    banner_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class TournamentUpdate(BaseModel):
    """Schema for updating a tournament"""
    title: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[str] = None
    entry_fee: Optional[int] = None
    prize_pool: Optional[int] = None
    status: Optional[str] = None
    room_id: Optional[str] = None
    room_password: Optional[str] = None


class TournamentResponse(BaseModel):
    """Tournament response schema"""
    id: UUID
    title: str
    slug: str
    game: str
    description: Optional[str] = None
    rules: Optional[str] = None
    entry_fee: int
    prize_pool: int
    first_place_reward: int
    second_place_reward: int
    third_place_reward: int
    fourth_place_reward: int = 0
    fifth_place_reward: int = 0
    max_participants: int
    current_participants: int
    slots_available: int
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str
    is_registration_open: bool
    banner_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TournamentDetailResponse(TournamentResponse):
    """Tournament detail with room info (for registered users)"""
    room_id: Optional[str] = None
    room_password: Optional[str] = None
    user_registered: bool = False
    user_registration: Optional['RegistrationResponse'] = None


class TournamentListResponse(BaseModel):
    """List of tournaments"""
    tournaments: List[TournamentResponse]
    total: int
    page: int
    per_page: int


class RegistrationRequest(BaseModel):
    """Request to register for a tournament"""
    player_id: Optional[str] = None  # Optional: use profile player_id if not provided
    team_name: Optional[str] = None


class RegistrationResponse(BaseModel):
    """Registration response"""
    id: UUID
    user_id: UUID
    tournament_id: UUID
    status: str
    tokens_paid: int
    player_id: Optional[str] = None
    team_name: Optional[str] = None
    position: Optional[int] = None
    reward_earned: int = 0
    checked_in: bool = False
    registered_at: datetime
    
    class Config:
        from_attributes = True


class RegistrationWithTournament(RegistrationResponse):
    """Registration with tournament details"""
    tournament: TournamentResponse


class ParticipantResponse(BaseModel):
    """Participant info for tournament"""
    id: UUID
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    player_id: Optional[str] = None
    team_name: Optional[str] = None
    position: Optional[int] = None
    reward_earned: int = 0
    checked_in: bool = False


# Update forward reference
TournamentDetailResponse.model_rebuild()
