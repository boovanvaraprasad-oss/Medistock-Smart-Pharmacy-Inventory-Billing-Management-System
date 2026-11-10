from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from typing import Literal
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.database import db
from app.core.dependencies import require_permission
from app.core.permissions import REPORT_VIEW
from app.services.dashboard import get_dashboard_summary


router = APIRouter(prefix="/reports", tags=["Reports"])
INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))
TEAL = "08777B"


def _store_header(settings: dict) -> list[tuple[str, str]]:
    fields = [
        ("Pharmacy", settings.get("store_name", "")),
        ("Address", settings.get("store_address", "")),
        ("Phone", settings.get("store_phone", "")),
        ("Email", settings.get("store_email", "")),
        ("License number", settings.get("store_license_number", "")),
    ]
    return [(label, str(value).strip()) for label, value in fields if value]


def _excel_safe(value):
    """Prevent user-entered report values from being treated as spreadsheet formulas."""
    if isinstance(value, str) and value[:1] in {"=", "+", "-", "@"}:
        return "'" + value
    return value


def _sales_report_data(summary: dict, period: str, selected_year: int):
    sales = summary["sales"]
    if period == "day":
        caption = f"Sales for {sales['selected_date']}"
        rows = [
            (f"{item['hour']:02d}:00", float(item["total_amount"]), float(item["purchase_amount"]))
            for item in sales["selected_date_hourly_totals"]
        ]
        revenue = float(sales["selected_date_sales_total"])
        purchases = sum(row[2] for row in rows)
    elif period == "month":
        caption = f"Sales for {sales['selected_month']}"
        rows = [
            (f"Day {item['day']}", float(item["total_amount"]), float(item["purchase_amount"]))
            for item in sales["selected_month_daily_totals"]
        ]
        revenue = float(sales["selected_month_sales_total"])
        purchases = sum(row[2] for row in rows)
    else:
        caption = f"Sales for {selected_year}"
        yearly = next((item for item in sales["yearly_totals"] if item["year"] == selected_year), None)
        revenue = float(yearly["total_amount"]) if yearly else 0.0
        purchases = float(yearly["purchase_amount"]) if yearly else 0.0
        rows = [(str(selected_year), revenue, purchases)]
    return caption, revenue, purchases, rows


async def _inventory_report_data():
    medicines = await db.medicines.find({}, {
        "name": 1, "sku": 1, "category_id": 1, "stock": 1,
        "reorder_threshold": 1, "is_active": 1,
    }).sort("name", 1).to_list(length=None)
    categories = await db.categories.find({}, {"name": 1}).to_list(length=None)
    category_names = {str(item["_id"]): item.get("name", "Uncategorized") for item in categories}
    medicine_rows = {str(item["_id"]): item for item in medicines}
    batch_totals = {}
    today = datetime.now(INDIA_TIMEZONE).date()
    batches = db.stock_batches.find({"is_active": True, "quantity": {"$gt": 0}}, {
        "medicine_id": 1, "quantity": 1, "purchase_price": 1, "expiry_date": 1,
    })
    async for batch in batches:
        medicine_id = str(batch.get("medicine_id", ""))
        totals = batch_totals.setdefault(medicine_id, {"units": 0, "value": 0.0, "batch_count": 0, "expired_units": 0})
        quantity = int(batch.get("quantity", 0))
        totals["units"] += quantity
        totals["value"] += quantity * float(batch.get("purchase_price", 0))
        totals["batch_count"] += 1
        expiry = batch.get("expiry_date")
        if isinstance(expiry, datetime) and expiry.date() < today:
            totals["expired_units"] += quantity
        elif isinstance(expiry, date) and expiry < today:
            totals["expired_units"] += quantity

    rows = []
    for medicine_id, medicine in medicine_rows.items():
        totals = batch_totals.get(medicine_id, {"units": 0, "value": 0.0, "batch_count": 0, "expired_units": 0})
        threshold = int(medicine.get("reorder_threshold", 10))
        if medicine.get("is_active") is False:
            status = "Inactive"
        elif totals["units"] <= 0:
            status = "Out of stock"
        elif totals["units"] <= threshold:
            status = "Low stock"
        else:
            status = "Healthy"
        rows.append((
            medicine.get("name", "Unknown medicine"),
            medicine.get("sku") or "—",
            category_names.get(str(medicine.get("category_id", "")), "Uncategorized"),
            totals["units"],
            threshold,
            totals["batch_count"],
            totals["expired_units"],
            round(totals["value"], 2),
            status,
        ))
    return rows


def _build_workbook(title: str, store_fields: list[tuple[str, str]], summary_rows: list[tuple[str, object]], headers: list[str], data_rows: list[tuple]):
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Summary"
    summary_sheet.append([title])
    summary_sheet["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    summary_sheet["A1"].fill = PatternFill("solid", fgColor=TEAL)
    summary_sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)
    row_index = 3
    for label, value in store_fields:
        summary_sheet.cell(row_index, 1, _excel_safe(label))
        summary_sheet.cell(row_index, 2, _excel_safe(value))
        row_index += 1
    if store_fields:
        row_index += 1
    for label, value in summary_rows:
        summary_sheet.cell(row_index, 1, _excel_safe(label)).font = Font(bold=True, color=TEAL)
        summary_sheet.cell(row_index, 2, _excel_safe(value))
        row_index += 1
    summary_sheet.column_dimensions["A"].width = 28
    summary_sheet.column_dimensions["B"].width = 56
    summary_sheet.freeze_panes = "A3"

    data_sheet = workbook.create_sheet("Details")
    data_sheet.append(headers)
    for cell in data_sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=TEAL)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    for row in data_rows:
        data_sheet.append([_excel_safe(value) for value in row])
    data_sheet.freeze_panes = "A2"
    data_sheet.auto_filter.ref = data_sheet.dimensions
    for column in data_sheet.columns:
        width = min(34, max(12, max(len(str(cell.value or "")) for cell in column) + 2))
        data_sheet.column_dimensions[get_column_letter(column[0].column)].width = width
    for row in data_sheet.iter_rows(min_row=2):
        for cell in row:
            if isinstance(cell.value, (int, float)) and cell.column > 1:
                cell.number_format = '#,##0.00' if isinstance(cell.value, float) else '#,##0'
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def _build_pdf(title: str, store_fields: list[tuple[str, str]], summary_rows: list[tuple[str, object]], headers: list[str], data_rows: list[tuple]):
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=12 * mm, leftMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 3 * mm)]
    if store_fields:
        details = "<br/>".join(
            f"<b>{escape(label)}:</b> {escape(value).replace(chr(10), '<br/>')}"
            for label, value in store_fields
        )
        elements.extend([Paragraph(details, styles["Normal"]), Spacer(1, 4 * mm)])
    summary_table = Table([[label, value] for label, value in summary_rows], colWidths=[55 * mm, 48 * mm], hAlign="LEFT")
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF5F4")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#075D63")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E5E8")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.extend([summary_table, Spacer(1, 6 * mm)])
    table_data = [headers, *[[str(value) for value in row] for row in data_rows]]
    if len(headers) == 9:
        column_widths = [48, 28, 38, 18, 25, 25, 22, 34, 35]
    else:
        column_widths = [65, 55, 65]
    detail_table = Table(
        table_data,
        colWidths=[width * mm for width in column_widths],
        repeatRows=1,
        hAlign="LEFT",
    )
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#08777B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E5E8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F7F8")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(detail_table)
    document.build(elements)
    buffer.seek(0)
    return buffer


@router.get("/{report_type}/export")
async def export_report(
    report_type: Literal["sales", "inventory"],
    file_format: Literal["xlsx", "pdf"] = Query(alias="format"),
    period: Literal["day", "month", "year"] = "day",
    selected_date: date | None = Query(default=None, alias="date"),
    selected_month: str | None = Query(default=None, alias="month"),
    year: int | None = Query(default=None, ge=2000, le=2100),
    current_user=Depends(require_permission(REPORT_VIEW)),
):
    selected_year = year or datetime.now(INDIA_TIMEZONE).year
    if selected_month:
        try:
            datetime.strptime(selected_month, "%Y-%m")
        except ValueError as error:
            raise HTTPException(status_code=422, detail="Month must use YYYY-MM format.") from error

    settings = await db.settings.find_one({"_id": "pharmacy_settings"}) or {}
    store_fields = _store_header(settings)
    today = datetime.now(INDIA_TIMEZONE).date()
    date_for_summary = selected_date or today
    month_for_summary = selected_month or today.strftime("%Y-%m")

    if report_type == "sales":
        summary = await get_dashboard_summary(date_for_summary, month_for_summary)
        caption, revenue, purchases, data_rows = _sales_report_data(summary, period, selected_year)
        title = f"MediStock Sales Report · {caption}"
        headers = ["Period", "Revenue (INR)", "Received purchases (INR)"]
        summary_rows = [
            ("Reporting period", caption),
            ("Revenue", f"INR {revenue:,.2f}"),
            ("Received purchases", f"INR {purchases:,.2f}"),
            ("All-time sales", f"INR {summary['sales']['completed_sales_total_all_time']:,.2f}"),
            ("Generated", datetime.now(INDIA_TIMEZONE).strftime("%d %b %Y %H:%M %Z")),
        ]
        file_rows = [(label, revenue_value, purchase_value) for label, revenue_value, purchase_value in data_rows]
        filename = f"MediStock-Sales-{period}-{datetime.now(INDIA_TIMEZONE):%Y%m%d}"
    else:
        data_rows = await _inventory_report_data()
        total_units = sum(row[3] for row in data_rows)
        stock_value = sum(row[7] for row in data_rows)
        low_stock = sum(row[8] == "Low stock" for row in data_rows)
        out_of_stock = sum(row[8] == "Out of stock" for row in data_rows)
        expired_units = sum(row[6] for row in data_rows)
        title = "MediStock Inventory Report"
        headers = ["Medicine", "SKU", "Category", "Units", "Reorder at", "Active batches", "Expired units", "Stock value (INR)", "Status"]
        summary_rows = [
            ("Report date", today.isoformat()),
            ("Medicines", len(data_rows)),
            ("Units in active batches", total_units),
            ("Inventory purchase value", f"INR {stock_value:,.2f}"),
            ("Low-stock medicines", low_stock),
            ("Out-of-stock medicines", out_of_stock),
            ("Expired units in active batches", expired_units),
            ("Generated", datetime.now(INDIA_TIMEZONE).strftime("%d %b %Y %H:%M %Z")),
        ]
        file_rows = data_rows
        filename = f"MediStock-Inventory-{datetime.now(INDIA_TIMEZONE):%Y%m%d}"

    if file_format == "xlsx":
        content = _build_workbook(title, store_fields, summary_rows, headers, file_rows)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        extension = "xlsx"
    else:
        content = _build_pdf(title, store_fields, summary_rows, headers, file_rows)
        media_type = "application/pdf"
        extension = "pdf"
    return StreamingResponse(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}.{extension}"'},
    )
