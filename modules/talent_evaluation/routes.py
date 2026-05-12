from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user

from decorators import permission_required
from modules.talent_evaluation.services import (
    list_talents,
    get_talent,
    create_talent,
    update_talent,
    delete_talent,
    list_evaluations,
    get_evaluation,
    create_evaluation,
    delete_evaluation,
    update_evaluation,
)

talent_evaluation_bp = Blueprint(
    "talent_evaluation",
    __name__,
    url_prefix="/talent-evaluation",
)


@talent_evaluation_bp.route("")
@login_required
@permission_required("view_talent_evaluation")
def index():
    database_url = current_app.config["DATABASE_URL"]
    status = (request.args.get("status") or "").strip()
    talents = list_talents(database_url, status)

    return render_template(
        "talent_evaluation/index.html",
        talents=talents,
        status=status,
    )


@talent_evaluation_bp.route("/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_talent_evaluation")
def create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        data = {
            "stage_name": (request.form.get("stage_name") or "").strip(),
            "real_name": (request.form.get("real_name") or "").strip() or None,
            "gender": (request.form.get("gender") or "").strip() or None,
            "nationality": (request.form.get("nationality") or "").strip() or None,
            "birthday": (request.form.get("birthday") or "").strip() or None,
            "team_name": (request.form.get("team_name") or "").strip() or None,
            "agency_name": (request.form.get("agency_name") or "").strip() or None,
            "instagram_url": (request.form.get("instagram_url") or "").strip() or None,
            "tiktok_url": (request.form.get("tiktok_url") or "").strip() or None,
            "youtube_url": (request.form.get("youtube_url") or "").strip() or None,
            "contact_info": (request.form.get("contact_info") or "").strip() or None,
            "status": (request.form.get("status") or "").strip() or "active",
            "notes": (request.form.get("notes") or "").strip() or None,
            "created_by": int(current_user.id),
        }

        if not data["stage_name"]:
            flash("請輸入藝名 / 顯示名稱", "danger")
            return redirect(url_for("talent_evaluation.create"))

        talent_id = create_talent(database_url, data)
        flash("藝人資料新增成功", "success")
        return redirect(url_for("talent_evaluation.detail", talent_id=talent_id))

    return render_template("talent_evaluation/create.html")


@talent_evaluation_bp.route("/<int:talent_id>")
@login_required
@permission_required("view_talent_evaluation")
def detail(talent_id: int):
    database_url = current_app.config["DATABASE_URL"]
    talent = get_talent(database_url, talent_id)

    if not talent:
        abort(404)

    evaluations = list_evaluations(database_url, talent_id)

    return render_template(
        "talent_evaluation/detail.html",
        talent=talent,
        evaluations=evaluations,
    )


@talent_evaluation_bp.route("/<int:talent_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_talent_evaluation")
def edit(talent_id: int):
    database_url = current_app.config["DATABASE_URL"]
    talent = get_talent(database_url, talent_id)

    if not talent:
        abort(404)

    if request.method == "POST":
        data = {
            "stage_name": (request.form.get("stage_name") or "").strip(),
            "real_name": (request.form.get("real_name") or "").strip() or None,
            "gender": (request.form.get("gender") or "").strip() or None,
            "nationality": (request.form.get("nationality") or "").strip() or None,
            "birthday": (request.form.get("birthday") or "").strip() or None,
            "team_name": (request.form.get("team_name") or "").strip() or None,
            "agency_name": (request.form.get("agency_name") or "").strip() or None,
            "instagram_url": (request.form.get("instagram_url") or "").strip() or None,
            "tiktok_url": (request.form.get("tiktok_url") or "").strip() or None,
            "youtube_url": (request.form.get("youtube_url") or "").strip() or None,
            "contact_info": (request.form.get("contact_info") or "").strip() or None,
            "status": (request.form.get("status") or "").strip() or "active",
            "notes": (request.form.get("notes") or "").strip() or None,
        }

        if not data["stage_name"]:
            flash("請輸入藝名 / 顯示名稱", "danger")
            return redirect(url_for("talent_evaluation.edit", talent_id=talent_id))

        update_talent(database_url, talent_id, data)
        flash("藝人資料更新成功", "success")
        return redirect(url_for("talent_evaluation.detail", talent_id=talent_id))

    return render_template("talent_evaluation/edit.html", talent=talent)


@talent_evaluation_bp.route("/<int:talent_id>/delete", methods=["POST"])
@login_required
@permission_required("delete_talent_evaluation")
def delete(talent_id: int):
    database_url = current_app.config["DATABASE_URL"]
    talent = get_talent(database_url, talent_id)

    if not talent:
        abort(404)

    delete_talent(database_url, talent_id)
    flash("藝人資料已刪除", "success")
    return redirect(url_for("talent_evaluation.index"))


@talent_evaluation_bp.route("/evaluations")
@login_required
@permission_required("view_talent_evaluation")
def evaluations_index():
    database_url = current_app.config["DATABASE_URL"]
    evaluations = list_evaluations(database_url)

    return render_template(
        "talent_evaluation/evaluations_index.html",
        evaluations=evaluations,
    )


@talent_evaluation_bp.route("/<int:talent_id>/evaluations/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_talent_evaluation")
def evaluation_create(talent_id: int):
    database_url = current_app.config["DATABASE_URL"]
    talent = get_talent(database_url, talent_id)

    if not talent:
        abort(404)

    if request.method == "POST":
        data = {
            "talent_id": talent_id,
            "report_title": (request.form.get("report_title") or "").strip(),
            "evaluation_date": (request.form.get("evaluation_date") or "").strip(),
            "appearance_score": int(request.form.get("appearance_score") or 0),
            "performance_score": int(request.form.get("performance_score") or 0),
            "social_score": int(request.form.get("social_score") or 0),
            "commercial_score": int(request.form.get("commercial_score") or 0),
            "team_fit_score": int(request.form.get("team_fit_score") or 0),
            "growth_score": int(request.form.get("growth_score") or 0),
            "risk_score": int(request.form.get("risk_score") or 0),
            "instagram_followers": int(request.form.get("instagram_followers") or 0),
            "tiktok_followers": int(request.form.get("tiktok_followers") or 0),
            "youtube_subscribers": int(request.form.get("youtube_subscribers") or 0),
            "engagement_rate": float(request.form.get("engagement_rate") or 0),
            "business_value": (request.form.get("business_value") or "").strip() or None,
            "social_analysis": (request.form.get("social_analysis") or "").strip() or None,
            "team_fit_analysis": (request.form.get("team_fit_analysis") or "").strip() or None,
            "signing_review": (request.form.get("signing_review") or "").strip() or None,
            "investment_model": (request.form.get("investment_model") or "").strip() or None,
            "executive_notes": (request.form.get("executive_notes") or "").strip() or None,
            "status": (request.form.get("status") or "").strip() or "draft",
            "created_by": int(current_user.id),
        }

        if not data["report_title"]:
            flash("請輸入評估報告標題", "danger")
            return redirect(url_for("talent_evaluation.evaluation_create", talent_id=talent_id))

        evaluation_id = create_evaluation(database_url, data)
        flash("評估報告新增成功", "success")
        return redirect(url_for("talent_evaluation.evaluation_detail", evaluation_id=evaluation_id))

    return render_template(
        "talent_evaluation/evaluation_create.html",
        talent=talent,
    )


@talent_evaluation_bp.route("/evaluations/<int:evaluation_id>")
@login_required
@permission_required("view_talent_evaluation")
def evaluation_detail(evaluation_id: int):
    database_url = current_app.config["DATABASE_URL"]
    evaluation = get_evaluation(database_url, evaluation_id)

    if not evaluation:
        abort(404)

    return render_template(
        "talent_evaluation/evaluation_detail.html",
        evaluation=evaluation,
    )

@talent_evaluation_bp.route("/evaluations/<int:evaluation_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_talent_evaluation")
def evaluation_edit(evaluation_id: int):
    database_url = current_app.config["DATABASE_URL"]
    evaluation = get_evaluation(database_url, evaluation_id)

    if not evaluation:
        abort(404)

    if request.method == "POST":
        try:
            data = {
                "report_title": (request.form.get("report_title") or "").strip(),
                "evaluation_date": (request.form.get("evaluation_date") or "").strip(),
                "appearance_score": int(request.form.get("appearance_score") or 0),
                "performance_score": int(request.form.get("performance_score") or 0),
                "social_score": int(request.form.get("social_score") or 0),
                "commercial_score": int(request.form.get("commercial_score") or 0),
                "team_fit_score": int(request.form.get("team_fit_score") or 0),
                "growth_score": int(request.form.get("growth_score") or 0),
                "risk_score": int(request.form.get("risk_score") or 0),
                "instagram_followers": int(request.form.get("instagram_followers") or 0),
                "tiktok_followers": int(request.form.get("tiktok_followers") or 0),
                "youtube_subscribers": int(request.form.get("youtube_subscribers") or 0),
                "engagement_rate": float(request.form.get("engagement_rate") or 0),
                "business_value": (request.form.get("business_value") or "").strip() or None,
                "social_analysis": (request.form.get("social_analysis") or "").strip() or None,
                "team_fit_analysis": (request.form.get("team_fit_analysis") or "").strip() or None,
                "signing_review": (request.form.get("signing_review") or "").strip() or None,
                "investment_model": (request.form.get("investment_model") or "").strip() or None,
                "executive_notes": (request.form.get("executive_notes") or "").strip() or None,
                "status": (request.form.get("status") or "").strip() or "draft",
            }
        except ValueError:
            flash("分數、粉絲數或互動率格式錯誤", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if not data["report_title"]:
            flash("請輸入評估報告標題", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if not data["evaluation_date"]:
            flash("請選擇評估日期", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        for field in [
            "appearance_score",
            "performance_score",
            "social_score",
            "commercial_score",
            "team_fit_score",
            "growth_score",
            "risk_score",
        ]:
            if data[field] < 0:
                flash("分數不可小於 0", "danger")
                return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["appearance_score"] > 20:
            flash("外型形象分數不可超過 20", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["performance_score"] > 20:
            flash("表演 / 鏡頭感分數不可超過 20", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["social_score"] > 20:
            flash("社群影響力分數不可超過 20", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["commercial_score"] > 20:
            flash("商業價值分數不可超過 20", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["team_fit_score"] > 10:
            flash("球團 / 品牌適性分數不可超過 10", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["growth_score"] > 10:
            flash("成長潛力分數不可超過 10", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["risk_score"] > 20:
            flash("風險扣分不可超過 20", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["instagram_followers"] < 0 or data["tiktok_followers"] < 0 or data["youtube_subscribers"] < 0:
            flash("社群粉絲數不可小於 0", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["engagement_rate"] < 0:
            flash("互動率不可小於 0", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        if data["status"] not in ["draft", "reviewing", "approved", "rejected"]:
            flash("報告狀態不合法", "danger")
            return redirect(url_for("talent_evaluation.evaluation_edit", evaluation_id=evaluation_id))

        update_evaluation(database_url, evaluation_id, data)

        flash("評估報告更新成功", "success")
        return redirect(url_for("talent_evaluation.evaluation_detail", evaluation_id=evaluation_id))

    return render_template(
        "talent_evaluation/evaluation_edit.html",
        evaluation=evaluation,
    )

@talent_evaluation_bp.route("/evaluations/<int:evaluation_id>/delete", methods=["POST"])
@login_required
@permission_required("delete_talent_evaluation")
def evaluation_delete(evaluation_id: int):
    database_url = current_app.config["DATABASE_URL"]
    evaluation = get_evaluation(database_url, evaluation_id)

    if not evaluation:
        abort(404)

    talent_id = evaluation["talent_id"]
    delete_evaluation(database_url, evaluation_id)

    flash("評估報告已刪除", "success")
    return redirect(url_for("talent_evaluation.detail", talent_id=talent_id))