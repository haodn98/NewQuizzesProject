from typing import Type

from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count, func
from starlette import status

from src.database import get_db_session


async def paginate(model: Type,
                   page: int = 1,
                   page_size: int = 10,
                   db: AsyncSession = Depends(get_db_session)) -> dict:
    if page < 1 or page_size < 1:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = 'Page size must be greater than 0.'
        )

    offset = (page - 1) * page_size
    query = select(model).offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    total_query = select(func.count()).select_from(model)
    total = await db.scalar(total_query)

    return {
        'total': total,
        'items': items,
        'page': page,
        'page_size': page_size,
    }