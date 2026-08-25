from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.responder import Responder
from app.schemas.auth import UserRegister, LoginResponse, UserAuthResponse
from app.utils.enums import UserRole, ResponderType


class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserRegister) -> User:
        result = await db.execute(select(User).filter(User.email == user_in.email))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered."
            )

        hashed_pwd = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_pwd,
            full_name=user_in.full_name,
            phone_number=user_in.phone_number,
            role=user_in.role
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        # Auto-create Responder profile if role is RESPONDER
        if db_user.role == UserRole.RESPONDER:
            responder_profile = Responder(
                user_id=db_user.id,
                type=ResponderType.ROADSIDE_TECHNICIAN,
                is_available=True,
                is_online=False
            )
            db.add(responder_profile)
            await db.commit()

        return db_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> LoginResponse:
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )

        access_token = create_access_token(subject=user.id, role=user.role.value)
        user_response = UserAuthResponse.model_validate(user)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )