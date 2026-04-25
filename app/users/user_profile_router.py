# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from app.core.database import get_db
# from app.models.user_profile import UserProfile
# from app.users.user_profile_schema import UserProfileCreate, UserProfileOut

# router = APIRouter(
#     prefix="/user-profiles",
#     tags=["User Profiles"]
# )


# # ✅ CREATE
# @router.post("/", response_model=UserProfileOut)
# def create_user_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):

#     new_profile = UserProfile(
#         name=profile.name,
#         description=profile.description,
#         scope_by=profile.scope_by,
#         user_id=profile.user_id,
#         role_id=profile.role_id,
#         group_id=profile.group_id
#     )

#     db.add(new_profile)
#     db.commit()
#     db.refresh(new_profile)

#     return UserProfileOut(
#         id=new_profile.id,
#         name=new_profile.name,
#         description=new_profile.description,
#         scope_by=new_profile.scope_by,
#         user=new_profile.user.first_name if new_profile.user else None,
#         role=new_profile.role.name if new_profile.role else None,
#         group=new_profile.group.name if new_profile.group else None
#     )


# # ✅ GET ALL
# @router.get("/", response_model=list[UserProfileOut])
# def list_user_profiles(db: Session = Depends(get_db)):

#     profiles = db.query(UserProfile).all()

#     result = []
#     for p in profiles:
#         result.append(
#             UserProfileOut(
#                 id=p.id,
#                 name=p.name,
#                 description=p.description,
#                 scope_by=p.scope_by,
#                 user=p.user.first_name if p.user else None,
#                 role=p.role.name if p.role else None,
#                 group=p.group.name if p.group else None
#             )
#         )

#     return result


# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from app.core.database import get_db
# from app.models.user_profile import UserProfile

# from app.users.user_profile_schema import UserProfileCreate, UserProfileResponse
# from app.models.user import User
# from app.models.user import Role
# from app.models.group import Group

# router = APIRouter(
#     prefix="/user-profiles",
#     tags=["User Profiles"]
# )

# @router.post("/", response_model=UserProfileResponse)
# def create_user_profile(data: UserProfileCreate, db: Session = Depends(get_db)):

#     user = db.query(User).filter(User.id == str(data.user_id)).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     role = db.query(Role).filter(Role.id == str(data.role_id)).first()
#     if not role:
#         raise HTTPException(status_code=404, detail="Role not found")

#     if data.group_id:
#         group = db.query(Group).filter(Group.id == str(data.group_id)).first()
#         if not group:
#             raise HTTPException(status_code=404, detail="Group not found")

#     profile = UserProfile(
#         name=data.name,
#         description=data.description,
#         scope_by=data.scope_by,
#         user_id=str(data.user_id),
#         role_id=str(data.role_id),
#         group_id=str(data.group_id) if data.group_id else None
#     )

#     db.add(profile)
#     db.commit()
#     db.refresh(profile)

#     return profile


# @router.get("/", response_model=list[UserProfileResponse])
# def get_user_profiles(db: Session = Depends(get_db)):
#     return db.query(UserProfile).all()


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user_profile import UserProfile
from app.users.user_profile_schema import UserProfileCreate, UserProfileResponse

from app.models.user import User
from app.models.user import Role
from app.models.group import Group


router = APIRouter(
    prefix="/user-profiles",
    tags=["User Profiles"]
)


# ✅ CREATE USER PROFILE
@router.post("/", response_model=UserProfileResponse)
def create_user_profile(data: UserProfileCreate, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == str(data.user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == str(data.role_id)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    group = None
    if data.group_id:
        group = db.query(Group).filter(Group.id == str(data.group_id)).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

    profile = UserProfile(
        name=data.name,
        description=data.description,
        scope_by=data.scope_by,
        user_id=str(data.user_id),
        role_id=str(data.role_id),
        group_id=str(data.group_id) if data.group_id else None
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "scope_by": profile.scope_by,

        "user_id": profile.user_id,
        "user": f"{user.first_name} {user.last_name}",

        "role_id": profile.role_id,
        "role": role.name,

        "group_id": profile.group_id,
        "group": group.name if group else None
    }


# ✅ GET ALL USER PROFILES
@router.get("/", response_model=list[UserProfileResponse])
def get_user_profiles(db: Session = Depends(get_db)):

    profiles = db.query(UserProfile).all()
    result = []

    for profile in profiles:
        user = db.query(User).filter(User.id == profile.user_id).first()
        role = db.query(Role).filter(Role.id == profile.role_id).first()

        group = None
        if profile.group_id:
            group = db.query(Group).filter(Group.id == profile.group_id).first()

        result.append({
            "id": profile.id,
            "name": profile.name,
            "description": profile.description,
            "scope_by": profile.scope_by,

            "user_id": profile.user_id,
            "user": f"{user.first_name} {user.last_name}" if user else None,

            "role_id": profile.role_id,
            "role": role.name if role else None,

            "group_id": profile.group_id,
            "group": group.name if group else None
        })

    return result