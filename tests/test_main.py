from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import ac


async def test_return_health_check(ac:AsyncSession):
    response = await ac.get("/healthy")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status_code": 200,
        "detail": "ok",
        "result": "working"
    }
