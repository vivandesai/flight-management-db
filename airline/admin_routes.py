"""Server-rendered DBA pages and read-only management views."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
import mysql.connector

from .db import connection, query
from .dba import ENTITIES, STATEMENTS, dependencies, form_values, get_record, key_values, mutate, record_key, row_token, run
from .view_catalogue import VIEWS
from .workflows import STATUSES

admin = Blueprint("admin", __name__)


@admin.get("/dba")
def home():
    return redirect(url_for("admin.records", entity="Airline"))


def entity_spec(name):
    if name not in ENTITIES:
        abort(404)
    return ENTITIES[name]


@admin.get("/dba/<entity>")
def records(entity):
    spec = entity_spec(entity)
    search = request.args.get("q", "").strip()[:200]
    try:
        page = max(1, min(1000000, int(request.args.get("page", "1"))))
    except ValueError:
        abort(400)
    with connection() as conn:
        total = run(conn, entity + ".count", {"search": search})[0]["total"]
        rows = run(conn, entity + ".list", {"search": search, "limit": 50, "offset": (page-1)*50})
    return render_template("dba_records.html", title="Database administrator", entity=spec, entities=ENTITIES,
                           rows=rows, record_key=record_key, search=search, page=page, total=total)


@admin.route("/dba/<entity>/<key>/<operation>", methods=["GET", "POST"])
def record_form(entity, key, operation):
    spec = entity_spec(entity)
    if operation not in ("edit", "delete"):
        abort(404)
    try:
        key_values(spec, key)
    except ValueError:
        abort(404)
    sql_operation = "update" if operation == "edit" else "delete"
    error, status = None, 200
    with connection() as conn:
        try:
            row = get_record(conn, spec, key)
        except LookupError:
            abort(404)
        token = request.form.get("row_token", "") if request.method == "POST" else row_token(spec, row, sql_operation)
        values = request.form.to_dict() if request.method == "POST" else form_values(row)
        if request.method == "POST":
            try:
                if operation == "delete" and request.form.get("confirmed") != "yes":
                    raise ValueError("Confirm this single-record deletion before continuing.")
                mutate(conn, spec, key, sql_operation, token, request.form)
                flash(f"{entity} {key} {'updated' if operation == 'edit' else 'deleted'}. Change committed successfully.", "success")
                return redirect(url_for("admin.records", entity=entity))
            except (ValueError, LookupError) as exc:
                error, status = str(exc) + " No changes were saved. Reload the record to try again.", 409
            except mysql.connector.Error as exc:
                error, status = f"MySQL {exc.errno} / SQLSTATE {exc.sqlstate}: {exc.msg}. The change was rolled back.", 409
        blocked = dependencies(conn, spec, key)
    statement = STATEMENTS[entity + "." + sql_operation]
    return render_template("dba_form.html", title=f"{'Edit' if operation == 'edit' else 'Delete'} {entity.lower()}",
                           entity=spec, key=key, row=row, fields=spec.fields, values=values, token=token,
                           operation=operation, dependencies=blocked, has_dependencies=any(r["row_count"] for r in blocked),
                           choices={"status": [(s, s) for s in STATUSES]}, error=error, statement=statement), status


def installed_views(conn):
    return {r["TABLE_NAME"] for r in query(conn,
        "SELECT TABLE_NAME FROM information_schema.VIEWS WHERE TABLE_SCHEMA = DATABASE()")} & set(VIEWS)


@admin.get("/views")
def view_list():
    with connection() as conn:
        installed = installed_views(conn)
    return render_template("views.html", title="SQL views", views=VIEWS, installed=installed)


@admin.get("/views/<name>")
def view_detail(name):
    view = VIEWS.get(name)
    if view is None:
        abort(404)
    rows, missing, error = [], False, None
    with connection() as conn:
        missing = name not in installed_views(conn)
        if not missing:
            try:
                # The identifier is checked exclusively against the source catalogue above.
                rows = query(conn, f"SELECT * FROM `{name}` ORDER BY 1")
            except mysql.connector.Error as exc:
                error = f"MySQL {exc.errno}: {exc.msg}"
    return render_template("view.html", title=view["title"], view=view, rows=rows, missing=missing, error=error)
