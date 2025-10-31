# app/features/ldap/routers/ldap_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.dependecies import get_session
from app.features.ldap.services.ldap_service import LdapService

router = APIRouter(prefix="/ldap", tags=["ldap / FreeIPA"])


@router.post("/users/add-all")
async def add_all_users(session: AsyncSession = Depends(get_session)):
    """Add all users from MSSQL to FreeIPA."""
    try:
        service = LdapService(session)
        added = await service.add_all_users()
        return {"added_users": added, "count": len(added)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/add-all")
async def add_all_groups(session: AsyncSession = Depends(get_session)):
    """Add all groups from MSSQL to FreeIPA."""
    try:
        service = LdapService(session)
        added = service.add_all_groups()
        return {"added_groups": added, "count": len(added)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{uid}")
async def delete_user(uid: str, session: AsyncSession = Depends(get_session)):
    """Delete a user from FreeIPA."""
    try:
        service = LdapService(session)
        service.delete_user(uid)
        return {"message": f"User {uid} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{uid}/exists")
async def check_user(uid: str, session: AsyncSession = Depends(get_session)):
    """Check if user exists in FreeIPA."""
    try:
        service = LdapService(session)
        exists = service.check_user_exists(uid)
        return {"uid": uid, "exists": exists}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{uid}/ou-number")
async def get_ou_number(uid: str, session: AsyncSession = Depends(get_session)):
    """Get user's OU number."""
    try:
        service = LdapService(session)
        ou = service.get_user_ou_number(uid)
        if ou is None:
            raise HTTPException(status_code=404, detail="User not found or no OU number")
        return {"uid": uid, "ou_number": ou}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
