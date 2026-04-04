from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user

from decorators import permission_required
from modules.finance.services import (
    list_finance_records,
    get_finance_record,
    create_finance_record,
    update_finance_record,
    delete_finance_record,
    list_projects_for_select,
)
from modules.finance.category_services import (
    get_finance_categories,
    get_finance_category,
    create_finance_category,
    update_finance_category,
)
from modules.finance.ar_ap_services import (
    list_ar_ap_records,
    get_ar_ap_record,
    create_ar_ap_record,
    update_ar_ap_record,
    mark_ar_ap_completed,
    create_finance_record_from_ar_ap,
)
from modules.finance.report_services import (
    get_finance_dashboard_data,
    get_monthly_report_data,
)

finance_bp = Blueprint("finance", __name__)


@finance_bp.route("/finance")
@login_required
@permission_required("view_finance")
def finance_index():
    database_url = current_app.config["DATABASE_URL"]
    month = (request.args.get("month") or "").strip()

    records, _, _ = list_finance_records(database_url, month)

    total_income = sum(float(r["amount"]) for r in records if r["category_type"] == "income")
    total_expense = sum(float(r["amount"]) for r in records if r["category_type"] == "expense")

    return render_template(
        "finance/index.html",
        records=records,
        month=month,
        total_income=total_income,
        total_expense=total_expense,
        net_amount=total_income - total_expense,
    )


@finance_bp.route("/finance/dashboard")
@login_required
@permission_required("view_finance")
def finance_dashboard():
    database_url = current_app.config["DATABASE_URL"]
    today = datetime.now()
    month = f"{today.year:04d}-{today.month:02d}"

    data = get_finance_dashboard_data(database_url, month)
    return render_template("finance/dashboard.html", **data)


@finance_bp.route("/finance/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_finance")
def finance_create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        record_date = (request.form.get("record_date") or "").strip()
        category_type = (request.form.get("category_type") or "").strip()
        category_id = (request.form.get("category_id") or "").strip()
        item_name = (request.form.get("item_name") or "").strip()
        amount = (request.form.get("amount") or "").strip()
        payment_method = (request.form.get("payment_method") or "").strip()
        counterparty = (request.form.get("counterparty") or "").strip()
        note = (request.form.get("note") or "").strip()
        project_id = (request.form.get("project_id") or "").strip()

        if not record_date:
            flash("請輸入日期", "danger")
            return redirect(url_for("finance.finance_create"))

        if category_type not in ["income", "expense"]:
            flash("請選擇正確的收支類型", "danger")
            return redirect(url_for("finance.finance_create"))

        if not category_id:
            flash("請選擇分類", "danger")
            return redirect(url_for("finance.finance_create"))

        selected_category = None
        for c in get_finance_categories(database_url, None, True):
            if c["id"] == int(category_id):
                selected_category = c
                break

        if not selected_category:
            flash("分類不存在", "danger")
            return redirect(url_for("finance.finance_create"))

        if selected_category["category_type"] != category_type:
            flash("分類類型與收支類型不一致", "danger")
            return redirect(url_for("finance.finance_create"))

        if not item_name:
            flash("請輸入項目名稱", "danger")
            return redirect(url_for("finance.finance_create"))

        try:
            amount_value = float(amount)
        except ValueError:
            flash("金額格式錯誤", "danger")
            return redirect(url_for("finance.finance_create"))

        project_id_value = int(project_id) if project_id else None

        create_finance_record(
            database_url=database_url,
            record_date=record_date,
            category_type=category_type,
            category_id=selected_category["id"],
            category_name=selected_category["name"],
            item_name=item_name,
            amount=amount_value,
            payment_method=payment_method,
            counterparty=counterparty,
            note=note,
            created_by=int(current_user.id),
            project_id=project_id_value,
        )

        flash("財務紀錄新增成功", "success")
        return redirect(url_for("finance.finance_index"))

    income_categories = get_finance_categories(database_url, "income", "true")
    expense_categories = get_finance_categories(database_url, "expense", "true")
    projects = list_projects_for_select(database_url)

    return render_template(
        "finance/create.html",
        income_categories=income_categories,
        expense_categories=expense_categories,
        projects=projects,
    )


@finance_bp.route("/finance/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_finance")
def finance_edit(record_id: int):
    database_url = current_app.config["DATABASE_URL"]
    record = get_finance_record(database_url, record_id)

    if not record:
        abort(404)

    if request.method == "POST":
        record_date = (request.form.get("record_date") or "").strip()
        category_type = (request.form.get("category_type") or "").strip()
        category_id = (request.form.get("category_id") or "").strip()
        item_name = (request.form.get("item_name") or "").strip()
        amount = (request.form.get("amount") or "").strip()
        payment_method = (request.form.get("payment_method") or "").strip()
        counterparty = (request.form.get("counterparty") or "").strip()
        note = (request.form.get("note") or "").strip()
        project_id = (request.form.get("project_id") or "").strip()

        if not record_date:
            flash("請輸入日期", "danger")
            return redirect(url_for("finance.finance_edit", record_id=record_id))

        if category_type not in ["income", "expense"]:
            flash("請選擇正確的收支類型", "danger")
            return redirect(url_for("finance.finance_edit", record_id=record_id))

        if not category_id:
            flash("請選擇分類", "danger")
            return redirect(url_for("finance.finance_edit", record_id=record_id))

        selected_category = get_finance_category(database_url, int(category_id))
        if not selected_category:
            flash("分類不存在", "danger")
            return redirect(url_for("finance.finance_edit", record_id=record_id))

        if selected_category["category_type"] != category_type:
            flash("分類類型與收支類型不一致", "danger")
            return redirect(url_for("finance.finance_edit", record_id=record_id))

        if not item_name:
            flash("請輸入項目名稱", "danger")
            return redirect(url_for("finance.finance_edit", record_id=record_id))

        try:
            amount_value = float(amount)
        except ValueError:
            flash("金額格式錯誤", "danger")
            return redirect(url_for("finance.finance_edit", record_id=record_id))

        project_id_value = int(project_id) if project_id else None

        update_finance_record(
            database_url=database_url,
            record_id=record_id,
            record_date=record_date,
            category_type=category_type,
            category_id=selected_category["id"],
            category_name=selected_category["name"],
            item_name=item_name,
            amount=amount_value,
            payment_method=payment_method,
            counterparty=counterparty,
            note=note,
            project_id=project_id_value,
        )

        flash("財務紀錄更新成功", "success")
        return redirect(url_for("finance.finance_index"))

    income_categories = get_finance_categories(database_url, "income", True)
    expense_categories = get_finance_categories(database_url, "expense", True)
    projects = list_projects_for_select(database_url)

    return render_template(
        "finance/edit.html",
        record=record,
        income_categories=income_categories,
        expense_categories=expense_categories,
        projects=projects,
    )


@finance_bp.route("/finance/<int:record_id>/delete", methods=["POST"])
@login_required
@permission_required("edit_finance")
def finance_delete(record_id: int):
    database_url = current_app.config["DATABASE_URL"]
    record = get_finance_record(database_url, record_id)

    if not record:
        abort(404)

    delete_finance_record(database_url, record_id)
    flash("財務紀錄已刪除", "success")
    return redirect(url_for("finance.finance_index"))


@finance_bp.route("/finance/categories")
@login_required
@permission_required("view_finance")
def finance_category_index():
    database_url = current_app.config["DATABASE_URL"]
    active_filter = (request.args.get("is_active") or "").strip()
    category_type = (request.args.get("category_type") or "").strip()

    categories = get_finance_categories(
        database_url,
        category_type if category_type else None,
        active_filter if active_filter else "",
    )

    return render_template(
        "finance/categories_index.html",
        categories=categories,
        active_filter=active_filter,
        category_type=category_type,
    )

@finance_bp.route("/finance/categories/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_finance")
def finance_category_create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        category_type = (request.form.get("category_type") or "").strip()
        name = (request.form.get("name") or "").strip()
        sort_order = (request.form.get("sort_order") or "0").strip()
        is_active = request.form.get("is_active") == "on"

        if category_type not in ["income", "expense"]:
            flash("請選擇正確的分類類型", "danger")
            return redirect(url_for("finance.finance_category_create"))

        if not name:
            flash("請輸入分類名稱", "danger")
            return redirect(url_for("finance.finance_category_create"))

        try:
            sort_order_value = int(sort_order)
        except ValueError:
            flash("排序格式錯誤", "danger")
            return redirect(url_for("finance.finance_category_create"))

        create_finance_category(database_url, category_type, name, sort_order_value, is_active)
        flash("財務分類新增成功", "success")
        return redirect(url_for("finance.finance_category_index"))

    return render_template("finance/category_create.html")


@finance_bp.route("/finance/categories/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_finance")
def finance_category_edit(category_id: int):
    database_url = current_app.config["DATABASE_URL"]
    category = get_finance_category(database_url, category_id)

    if not category:
        abort(404)

    if request.method == "POST":
        category_type = (request.form.get("category_type") or "").strip()
        name = (request.form.get("name") or "").strip()
        sort_order = (request.form.get("sort_order") or "0").strip()
        is_active = request.form.get("is_active") == "on"

        if category_type not in ["income", "expense"]:
            flash("請選擇正確的分類類型", "danger")
            return redirect(url_for("finance.finance_category_edit", category_id=category_id))

        if not name:
            flash("請輸入分類名稱", "danger")
            return redirect(url_for("finance.finance_category_edit", category_id=category_id))

        try:
            sort_order_value = int(sort_order)
        except ValueError:
            flash("排序格式錯誤", "danger")
            return redirect(url_for("finance.finance_category_edit", category_id=category_id))

        update_finance_category(database_url, category_id, category_type, name, sort_order_value, is_active)
        flash("財務分類更新成功", "success")
        return redirect(url_for("finance.finance_category_index"))

    return render_template("finance/category_edit.html", category=category)


@finance_bp.route("/finance/reports/monthly")
@login_required
@permission_required("view_finance")
def finance_monthly_report():
    database_url = current_app.config["DATABASE_URL"]
    month = (request.args.get("month") or "").strip()

    data = get_monthly_report_data(database_url, month)

    return render_template(
        "finance/monthly_report.html",
        month=month,
        **data,
    )


@finance_bp.route("/ar-ap")
@login_required
@permission_required("view_finance")
def ar_ap_index():
    database_url = current_app.config["DATABASE_URL"]
    record_type = (request.args.get("type") or "").strip()
    status = (request.args.get("status") or "").strip()

    records = list_ar_ap_records(database_url, record_type, status)

    total_receivable = sum(float(r["amount"]) for r in records if r["record_type"] == "receivable" and r["status"] == "pending")
    total_payable = sum(float(r["amount"]) for r in records if r["record_type"] == "payable" and r["status"] == "pending")

    return render_template(
        "ar_ap/index.html",
        records=records,
        record_type=record_type,
        status=status,
        total_receivable=total_receivable,
        total_payable=total_payable,
    )


@finance_bp.route("/ar-ap/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_finance")
def ar_ap_create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        record_type = (request.form.get("record_type") or "").strip()
        title = (request.form.get("title") or "").strip()
        counterparty = (request.form.get("counterparty") or "").strip()
        amount = (request.form.get("amount") or "").strip()
        due_date = (request.form.get("due_date") or "").strip()
        status = (request.form.get("status") or "").strip()
        note = (request.form.get("note") or "").strip()
        project_id = (request.form.get("project_id") or "").strip()

        if record_type not in ["receivable", "payable"]:
            flash("請選擇正確的帳款類型", "danger")
            return redirect(url_for("finance.ar_ap_create"))

        if not title:
            flash("請輸入標題", "danger")
            return redirect(url_for("finance.ar_ap_create"))

        try:
            amount_value = float(amount)
        except ValueError:
            flash("金額格式錯誤", "danger")
            return redirect(url_for("finance.ar_ap_create"))

        if status not in ["pending", "completed", "cancelled"]:
            status = "pending"

        project_id_value = int(project_id) if project_id else None

        create_ar_ap_record(
            database_url=database_url,
            record_type=record_type,
            title=title,
            counterparty=counterparty,
            amount=amount_value,
            due_date=due_date or None,
            status=status,
            note=note,
            project_id=project_id_value,
            created_by=int(current_user.id),
        )

        flash("應收 / 應付紀錄建立成功", "success")
        return redirect(url_for("finance.ar_ap_index"))

    projects = list_projects_for_select(database_url)
    return render_template("ar_ap/create.html", projects=projects)


@finance_bp.route("/ar-ap/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_finance")
def ar_ap_edit(record_id: int):
    database_url = current_app.config["DATABASE_URL"]
    record = get_ar_ap_record(database_url, record_id)

    if not record:
        abort(404)

    if request.method == "POST":
        record_type = (request.form.get("record_type") or "").strip()
        title = (request.form.get("title") or "").strip()
        counterparty = (request.form.get("counterparty") or "").strip()
        amount = (request.form.get("amount") or "").strip()
        due_date = (request.form.get("due_date") or "").strip()
        status = (request.form.get("status") or "").strip()
        note = (request.form.get("note") or "").strip()
        project_id = (request.form.get("project_id") or "").strip()

        if record_type not in ["receivable", "payable"]:
            flash("請選擇正確的帳款類型", "danger")
            return redirect(url_for("finance.ar_ap_edit", record_id=record_id))

        if not title:
            flash("請輸入標題", "danger")
            return redirect(url_for("finance.ar_ap_edit", record_id=record_id))

        try:
            amount_value = float(amount)
        except ValueError:
            flash("金額格式錯誤", "danger")
            return redirect(url_for("finance.ar_ap_edit", record_id=record_id))

        if status not in ["pending", "completed", "cancelled"]:
            status = "pending"

        project_id_value = int(project_id) if project_id else None

        update_ar_ap_record(
            database_url=database_url,
            record_id=record_id,
            record_type=record_type,
            title=title,
            counterparty=counterparty,
            amount=amount_value,
            due_date=due_date or None,
            status=status,
            note=note,
            project_id=project_id_value,
        )

        flash("應收 / 應付紀錄更新成功", "success")
        return redirect(url_for("finance.ar_ap_index"))

    projects = list_projects_for_select(database_url)
    return render_template("ar_ap/edit.html", record=record, projects=projects)


@finance_bp.route("/ar-ap/<int:record_id>/mark-completed", methods=["POST"])
@login_required
@permission_required("edit_finance")
def ar_ap_mark_completed(record_id: int):
    database_url = current_app.config["DATABASE_URL"]

    record = get_ar_ap_record(database_url, record_id)
    if not record:
        abort(404)

    mark_ar_ap_completed(database_url, record_id)

    try:
        finance_record_id = create_finance_record_from_ar_ap(
            database_url=database_url,
            record_id=record_id,
            created_by=int(current_user.id),
        )
    except Exception as e:
        flash(f"已標記完成，但轉正式財務紀錄失敗：{str(e)}", "danger")
        return redirect(url_for("finance.ar_ap_index"))

    if finance_record_id:
        flash("已完成，並成功轉入正式財務紀錄", "success")
    else:
        flash("已更新為完成狀態", "success")

    return redirect(url_for("finance.ar_ap_index"))