from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RoleChecker
from app.db.database import get_db
from app.services.analytics_service import AnalyticsService
from app.utils.enums import UserRole

router = APIRouter(
    prefix="/analytics",
    tags=["ERP & CRM Analytics"],
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.MANAGER]))]
)


@router.get("/overview")
async def get_overview_kpis(
    service_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    days: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Executive KPI summary across operational, fleet, and financial metrics."""
    return await AnalyticsService.get_overview(
        db=db,
        service_type=service_type,
        status=status,
        days=days
    )


@router.get("/operations")
async def get_operations_analytics(
    days: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Operational distributions by service category, status, priority, and daily volume."""
    return await AnalyticsService.get_operations_analytics(db=db, days=days)


@router.get("/mechanics")
async def get_mechanics_performance(
    db: AsyncSession = Depends(get_db)
):
    """Mechanic performance ledger with jobs completed, active tasks, and average rating."""
    return await AnalyticsService.get_mechanics_analytics(db=db)


@router.get("/revenue")
async def get_revenue_analytics(
    days: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Financial intelligence with gross paid, pending, parts vs service revenue, and ledger."""
    return await AnalyticsService.get_financial_analytics(db=db, days=days)


@router.get("/crm")
async def get_crm_insights(
    db: AsyncSession = Depends(get_db)
):
    """Customer CRM insights with repeat rates, top service demands, and recent customer reviews."""
    return await AnalyticsService.get_crm_insights(db=db)
