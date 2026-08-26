from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.core.dependencies import get_current_user_claims
from app.models.user import User
from app.schemas.auth import UserRegister, UserAuthResponse, LoginResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Register a new user (Customer, Responder, Manager, Admin).
    """
    user = await AuthService.register_user(db, user_in)
    return user


@router.post("/login", response_model=LoginResponse)
@router.post("/token", response_model=LoginResponse, include_in_schema=False)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login, gets an access token for future requests.
    """
    return await AuthService.authenticate_user(db, form_data.username, form_data.password)


@router.get("/me", response_model=UserAuthResponse)
async def get_current_user(
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch details for the currently authenticated user based on JWT token.
    """
    user_id = claims.get("user_id")
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    return user
