from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.companies.permissions import is_company_admin
from src.database.database import get_db_session
from src.notifications.schemas import NotificationSchema
from src.notifications.services import get_users_notifications_service, user_make_notification_read_service, \
    create_notifications_service
from src.utils.utils_auth import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.get("/all")
async def get_users_notifications(user: dict = Depends(get_current_user),
                                  db: AsyncSession = Depends(get_db_session)):
    return await get_users_notifications_service(user=user, db=db)


@router.post("/{notification_id}/read")
async def user_make_notification_read(notification_id: int,
                                  user: dict = Depends(get_current_user),
                                  db: AsyncSession = Depends(get_db_session)):
    return await user_make_notification_read_service(notification_id=notification_id,user=user, db=db)

@router.post('/')
async def create_notification(notification_request: NotificationSchema,
                              user: dict = Depends(get_current_user),
                              db: AsyncSession = Depends(get_db_session)):
    await is_company_admin(company_id=notification_request.company_id,user=user,db=db)
    return await create_notifications_service(notification_request)