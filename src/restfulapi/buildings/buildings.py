from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Building
from src.db.schemas import BuildingOut

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[BuildingOut])
async def list_buildings(db: AsyncSession = Depends(get_db)) -> list[BuildingOut]:
    res = await db.execute(select(Building).order_by(Building.id))
    return list(res.scalars())