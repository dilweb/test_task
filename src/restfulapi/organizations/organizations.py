from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status

from src.db.session import get_db
from src.db.models import Activity, Building, Organization, OrganizationPhone, organization_activity
from src.db.schemas import ActivityOut, BuildingOut, OrganizationCreate, OrganizationOut

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _org_to_out(org: Organization) -> OrganizationOut:
    return OrganizationOut(
        id=org.id,
        name=org.name,
        building=BuildingOut.model_validate(org.building),
        phones=[p.phone for p in org.phones],
        activities=[ActivityOut.model_validate(a) for a in org.activities],
    )


@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(org_id: int, db: AsyncSession = Depends(get_db)) -> OrganizationOut:
    stmt = (
        select(Organization)
        .where(Organization.id == org_id)
        .options(joinedload(Organization.building), selectinload(Organization.phones), selectinload(Organization.activities))
    )
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return _org_to_out(org)


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(payload: OrganizationCreate, db: AsyncSession = Depends(get_db)) -> OrganizationOut:
    b = await db.execute(select(Building).where(Building.id == payload.building_id))
    building = b.scalar_one_or_none()
    if building is None:
        raise HTTPException(status_code=400, detail="building_id not found")

    activities: list[Activity] = []
    if payload.activity_ids:
        ares = await db.execute(select(Activity).where(Activity.id.in_(payload.activity_ids)))
        activities = list(ares.scalars().all())
        if len(activities) != len(set(payload.activity_ids)):
            raise HTTPException(status_code=400, detail="Some activity_ids not found")

    org = Organization(name=payload.name, building_id=payload.building_id)
    org.activities = activities
    org.phones = [OrganizationPhone(phone=p) for p in payload.phones]

    db.add(org)
    await db.commit()
    await db.refresh(org)

    # загрузим связи для ответа
    stmt = (
        select(Organization)
        .where(Organization.id == org.id)
        .options(joinedload(Organization.building), selectinload(Organization.phones), selectinload(Organization.activities))
    )
    res = await db.execute(stmt)
    org2 = res.scalar_one()
    return _org_to_out(org2)


def _apply_filters(
    stmt: Select[tuple[Organization]],
    *,
    building_id: int | None,
    name: str | None,
    activity_id: int | None,
    include_children: bool,
) -> Select[tuple[Organization]]:
    if building_id is not None:
        stmt = stmt.where(Organization.building_id == building_id)

    if name:
        stmt = stmt.where(func.lower(Organization.name).contains(func.lower(name)))

    if activity_id is not None:
        if include_children:
            # recursive CTE to get all descendant activity IDs (including self)
            act = select(Activity.id, Activity.parent_id).where(Activity.id == activity_id).cte(recursive=True)
            act_alias = act.alias()
            act = act.union_all(select(Activity.id, Activity.parent_id).where(Activity.parent_id == act_alias.c.id))
            stmt = stmt.join(organization_activity, organization_activity.c.organization_id == Organization.id).where(
                organization_activity.c.activity_id.in_(select(act.c.id))
            )
        else:
            stmt = stmt.join(organization_activity, organization_activity.c.organization_id == Organization.id).where(
                organization_activity.c.activity_id == activity_id
            )
    return stmt


@router.get("", response_model=list[OrganizationOut])
async def list_organizations(
    building_id: int | None = Query(default=None),
    name: str | None = Query(default=None, min_length=1),
    activity_id: int | None = Query(default=None),
    include_children: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationOut]:
    stmt = (
        select(Organization)
        .options(joinedload(Organization.building), selectinload(Organization.phones), selectinload(Organization.activities))
        .order_by(Organization.id)
    )
    stmt = _apply_filters(stmt, building_id=building_id, name=name, activity_id=activity_id, include_children=include_children)

    res = await db.execute(stmt)
    orgs = res.scalars().unique().all()
    return [_org_to_out(o) for o in orgs]


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return r * c


@router.get("/geo/radius", response_model=list[OrganizationOut])
async def organizations_in_radius(
    lat: float,
    lon: float,
    radius_m: float = Query(gt=0, le=200_000),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationOut]:
    # грубый prefilter по bbox (ускоряет), потом точный haversine на питоне
    lat_delta = radius_m / 111_000.0
    lon_delta = radius_m / (111_000.0 * max(cos(radians(lat)), 0.1))

    min_lat, max_lat = lat - lat_delta, lat + lat_delta
    min_lon, max_lon = lon - lon_delta, lon + lon_delta

    stmt = (
        select(Organization)
        .join(Building, Building.id == Organization.building_id)
        .where(
            and_(
                Building.latitude >= min_lat,
                Building.latitude <= max_lat,
                Building.longitude >= min_lon,
                Building.longitude <= max_lon,
            )
        )
        .options(joinedload(Organization.building), selectinload(Organization.phones), selectinload(Organization.activities))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    orgs = res.scalars().unique().all()

    filtered = [
        o for o in orgs if _haversine_m(lat, lon, o.building.latitude, o.building.longitude) <= radius_m
    ]
    return [_org_to_out(o) for o in filtered]


@router.get("/geo/bbox", response_model=list[OrganizationOut])
async def organizations_in_bbox(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationOut]:
    if min_lat > max_lat or min_lon > max_lon:
        raise HTTPException(status_code=400, detail="Invalid bbox bounds")

    stmt = (
        select(Organization)
        .join(Building, Building.id == Organization.building_id)
        .where(
            and_(
                Building.latitude >= min_lat,
                Building.latitude <= max_lat,
                Building.longitude >= min_lon,
                Building.longitude <= max_lon,
            )
        )
        .options(joinedload(Organization.building), selectinload(Organization.phones), selectinload(Organization.activities))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    orgs = res.scalars().unique().all()
    return [_org_to_out(o) for o in orgs]