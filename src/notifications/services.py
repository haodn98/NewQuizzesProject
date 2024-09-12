from select import select

from src.notifications.models import Notification


async def get_users_notifications_service(user, db):
    notifications = await db.execute(select(Notification).where(Notification.user_id == user.get("id")))
    notifications = notifications.scalars().all
    return notifications


async def user_make_notification_read_service(notification_id, user, db):
    notification = await db.execute(select(Notification).where(Notification.user_id == user.get("id"),
                                                               Notification.id == notification_id))
    notification = notification.scalar_one_or_none()
    notification.is_read = True
    db.add(notification)
    await db.commit()
    return notification


async def create_notifications_service(user, company_id, title, content, db):
    notification = Notification(user_id=user.get("id"),
                                company_id=company_id,
                                title=title,
                                content=content,
                                is_read=False)
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification
