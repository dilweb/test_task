from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.db.session import get_db
from src.db.models import Activity
from src.db.schemas import ActivityOut


router = APIRouter(prefix="/activities", tags=["activities"])


class ActivityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parent_id: int | None = None


@router.get("", response_model=list[ActivityOut])
async def list_activities(db: AsyncSession = Depends(get_db)) -> list[ActivityOut]:
    res = await db.execute(select(Activity).order_by(Activity.id))
    return list(res.scalars().all())


@router.post("", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
async def create_activity(payload: ActivityCreate, db: AsyncSession = Depends(get_db)) -> ActivityOut:
    if payload.parent_id is not None:
        parent = await db.execute(select(Activity).where(Activity.id == payload.parent_id))
        if parent.scalar_one_or_none() is None:
            raise HTTPException(status_code=400, detail="parent_id not found")

    a = Activity(name=payload.name, parent_id=payload.parent_id)
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a