from fastapi import HTTPException, status
from sqlalchemy import select

from companies.models import CompanyMember, Company
from notifications.models import Notification
from notifications.schemas import NotificationSchema


async def get_users_notifications_service(user, db):
    notifications = await db.execute(select(Notification).where(Notification.user_id == user.get("id")))
    notifications = notifications.scalars().all()
    return notifications


async def user_make_notification_read_service(notification_id, user, db):
    notification = await db.execute(select(Notification).where(Notification.user_id == user.get("id"),
                                                               Notification.id == notification_id))
    notification = notification.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Notification not found ")
    notification.is_read = True
    db.add(notification)
    await db.commit()
    return notification


async def create_notifications_service(notification_data, db):
    notification = Notification(user_id=notification_data.user_id,
                                company_id=notification_data.company_id,
                                title=notification_data.title,
                                content=notification_data.content,
                                is_read=False)
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def quiz_created_notification_service(company_id, quiz_data, db):
    company_members = await db.execute(select(CompanyMember).where(CompanyMember.company_id == company_id))
    company = await db.execute(select(Company).where(Company.id == company_id))
    company_members = company_members.scalars().all()
    company = company.scalar_one_or_none()
    for members in company_members:
        notification = {
            "title": f"New quiz created by {company.name}",
            "content": f'New quiz "{quiz_data["name"]}" was created by {company.name}',
            "company_id": company_id,
            "user_id": members.user_id,
        }
        NotificationSchema.model_validate(notification)
        notification_to_db = Notification(
            title=notification["title"],
            content=notification["content"],
            company_id=notification["company_id"],
            user_id=notification["user_id"],
        )
        db.add(notification_to_db)

    await db.commit()
