from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.domains.ldap.services.ldap_service import LdapService
from app.domains.ldap.services.source_service import SourceService

router = APIRouter(prefix="/ldap", tags=["ldap / FreeIPA"])


@router.post("/users/sync")
async def sync_mssql_to_ldap( background_tasks: BackgroundTasks,  dry_run: bool = True):
    """Add all users from MSSQL to FreeIPA."""
    try:
        if dry_run:
            source_service = SourceService()
            return await source_service.return_modified_users()
        else:
            ldap_service = LdapService()
            background_tasks.add_task(ldap_service.sync_all_users)
            return "Sync queued"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# #
# #
# @router.post("/groups/sync")
# async def sync_groups(session: AsyncSession = Depends(get_session)):
#     """Add all groups from MSSQL to FreeIPA."""
#     try:
#         service = LdapService(session)
#         added = service.add_all_groups()
#         return {"added_groups": added, "count": len(added)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.delete("/users/{uid}")
# async def delete_user(uid: str, session: AsyncSession = Depends(get_session)):
#     """Delete a user from FreeIPA."""
#     try:
#         service = LdapService(session)
#         service.delete_user(uid)
#         return {"message": f"User {uid} deleted successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.get("/users/{uid}/exists")
# async def check_user(uid: str, session: AsyncSession = Depends(get_session)):
#     """Check if user exists in FreeIPA."""
#     try:
#         service = LdapService(session)
#         exists = service.check_user_exists(uid)
#         return {"uid": uid, "exists": exists}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/source")
# async def get_users_from_source( session: Annotated[AsyncSession, Depends(get_session)]):
#     try:
#         service = SourceService(session=session)
#         return await service.return_modified_users()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
