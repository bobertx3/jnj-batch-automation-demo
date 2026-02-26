from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from ..db import db

router = APIRouter()


class SignOffRequest(BaseModel):
    batch_id: str
    signed_by: str = "QA Reviewer"


@router.get("/batches")
async def get_batches(search: Optional[str] = Query(None), status: Optional[str] = Query(None)):
    pool = await db.get_pool()
    query = "SELECT * FROM batch_disposition"
    conditions = []
    args = []
    idx = 1

    if search:
        conditions.append(f"(batch_id ILIKE ${idx} OR drug_name ILIKE ${idx})")
        args.append(f"%{search}%")
        idx += 1

    if status and status != "All":
        conditions.append(f"status = ${idx}")
        args.append(status)
        idx += 1

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY last_updated DESC"

    rows = await pool.fetch(query, *args)
    return [dict(r) for r in rows]


@router.get("/batches/{batch_id}")
async def get_batch(batch_id: str):
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM batch_disposition WHERE batch_id = $1", batch_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Batch not found")
    return dict(row)


@router.get("/kpis")
async def get_kpis():
    pool = await db.get_pool()
    pending = await pool.fetchval(
        "SELECT COUNT(*) FROM batch_disposition WHERE status = 'Pending'"
    )
    avg_cycle = await pool.fetchval(
        "SELECT ROUND(AVG(cycle_time_hours)::numeric, 1) FROM batch_disposition"
    )
    total = await pool.fetchval("SELECT COUNT(*) FROM batch_disposition")
    released = await pool.fetchval(
        "SELECT COUNT(*) FROM batch_disposition WHERE status = 'Released'"
    )
    rejected = await pool.fetchval(
        "SELECT COUNT(*) FROM batch_disposition WHERE status = 'Rejected'"
    )
    exceptions = await pool.fetchval(
        "SELECT COUNT(*) FROM batch_disposition WHERE temp_check = false OR purity_check = false"
    )
    return {
        "pending_count": pending or 0,
        "avg_cycle_time": float(avg_cycle) if avg_cycle else 0.0,
        "total_batches": total or 0,
        "released_count": released or 0,
        "rejected_count": rejected or 0,
        "exception_count": exceptions or 0,
    }


@router.post("/batches/{batch_id}/release")
async def release_batch(batch_id: str, req: SignOffRequest):
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM batch_disposition WHERE batch_id = $1", batch_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Batch not found")
    if row["status"] != "Pending":
        raise HTTPException(status_code=400, detail=f"Batch is already {row['status']}")

    await pool.execute(
        """UPDATE batch_disposition
           SET status = 'Released',
               last_updated = NOW(),
               signed_by = $2
           WHERE batch_id = $1""",
        batch_id,
        req.signed_by,
    )
    return {"message": f"Batch {batch_id} released successfully", "signed_by": req.signed_by}


@router.post("/batches/{batch_id}/reject")
async def reject_batch(batch_id: str):
    pool = await db.get_pool()
    await pool.execute(
        """UPDATE batch_disposition
           SET status = 'Rejected', last_updated = NOW()
           WHERE batch_id = $1 AND status = 'Pending'""",
        batch_id,
    )
    return {"message": f"Batch {batch_id} rejected"}


@router.get("/quality-events")
async def get_quality_events():
    """Return batches that have exceptions (temp or purity failures)."""
    pool = await db.get_pool()
    rows = await pool.fetch(
        """SELECT batch_id, drug_name, batch_name, status, temp_actual, temp_check,
                  purity_actual, purity_check, cycle_time_hours, last_updated, exceptions
           FROM batch_disposition
           WHERE temp_check = false OR purity_check = false
           ORDER BY last_updated DESC"""
    )
    events = []
    for r in rows:
        row = dict(r)
        event_type = []
        if not row["temp_check"]:
            event_type.append("Temperature Excursion")
        if not row["purity_check"]:
            event_type.append("Purity Failure")
        severity = "Critical" if (row["temp_actual"] and abs(row["temp_actual"] - 37.0) > 1.0) or (row["purity_actual"] and row["purity_actual"] < 96) else "Major"
        row["event_type"] = ", ".join(event_type)
        row["severity"] = severity
        events.append(row)
    return events


@router.get("/reports/summary")
async def get_reports_summary():
    """Return summary statistics for the reports tab."""
    pool = await db.get_pool()

    # Status breakdown
    status_rows = await pool.fetch(
        "SELECT status, COUNT(*) as count FROM batch_disposition GROUP BY status ORDER BY status"
    )

    # Monthly trend (batches by manufactured month)
    trend_rows = await pool.fetch(
        """SELECT TO_CHAR(manufactured_date, 'YYYY-MM') as month,
                  COUNT(*) as total,
                  COUNT(*) FILTER (WHERE status = 'Released') as released,
                  COUNT(*) FILTER (WHERE status = 'Pending') as pending,
                  COUNT(*) FILTER (WHERE status = 'Rejected') as rejected
           FROM batch_disposition
           GROUP BY TO_CHAR(manufactured_date, 'YYYY-MM')
           ORDER BY month"""
    )

    # Exception rate
    total = await pool.fetchval("SELECT COUNT(*) FROM batch_disposition")
    with_exceptions = await pool.fetchval(
        "SELECT COUNT(*) FROM batch_disposition WHERE temp_check = false OR purity_check = false"
    )
    temp_fails = await pool.fetchval("SELECT COUNT(*) FROM batch_disposition WHERE temp_check = false")
    purity_fails = await pool.fetchval("SELECT COUNT(*) FROM batch_disposition WHERE purity_check = false")

    # Avg cycle time by status
    cycle_rows = await pool.fetch(
        """SELECT status, ROUND(AVG(cycle_time_hours)::numeric, 1) as avg_cycle,
                  ROUND(MIN(cycle_time_hours)::numeric, 1) as min_cycle,
                  ROUND(MAX(cycle_time_hours)::numeric, 1) as max_cycle
           FROM batch_disposition GROUP BY status ORDER BY status"""
    )

    return {
        "status_breakdown": [dict(r) for r in status_rows],
        "monthly_trend": [dict(r) for r in trend_rows],
        "exception_rate": {
            "total": total or 0,
            "with_exceptions": with_exceptions or 0,
            "rate_pct": round((with_exceptions or 0) / (total or 1) * 100, 1),
            "temp_fails": temp_fails or 0,
            "purity_fails": purity_fails or 0,
        },
        "cycle_time_by_status": [dict(r) for r in cycle_rows],
    }
