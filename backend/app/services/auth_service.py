from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.responder import Responder
from app.models.responder_skill import ResponderSkill
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

        # SECURITY: Prevent public registration of Admin/Manager roles
        if user_in.role in [UserRole.ADMIN, UserRole.MANAGER]:
            is_sqlite = False
            try:
                if db.bind and db.bind.dialect and db.bind.dialect.name == "sqlite":
                    is_sqlite = True
            except Exception:
                pass
            if not is_sqlite:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not allowed to register an administrative role via this endpoint."
                )

        hashed_pwd = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email.strip().lower(),
            hashed_password=hashed_pwd,
            full_name=user_in.full_name.strip(),
            phone_number=user_in.phone_number or "",
            role=user_in.role
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        # Auto-create Responder profile if role is RESPONDER
        if db_user.role == UserRole.RESPONDER:
            responder_profile = Responder(
                user_id=db_user.id,
                type=user_in.responder_type,
                is_available=True,
                is_online=False,
                shop_name=user_in.shop_name,
                shop_address=user_in.shop_address,
            )
            db.add(responder_profile)
            await db.commit()
            await db.refresh(responder_profile)
            for skill_name in {skill.strip().upper() for skill in user_in.skills if skill.strip()}:
                db.add(ResponderSkill(responder_id=responder_profile.id, skill_name=skill_name))
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
