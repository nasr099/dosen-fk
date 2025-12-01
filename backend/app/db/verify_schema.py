import logging
from typing import List, Dict
from sqlalchemy import text, inspect
from app.db.base import engine
from app.db.models import Base  # ensures models are imported

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("verify_schema")

# Expected schema description for FK verification (table -> list of FKs)
EXPECTED_FKS: Dict[str, List[Dict[str, str]]] = {
    "question_sets": [
        {"conname": "fk_question_sets_category", "columns": ["category_id"], "reftable": "categories", "refcols": ["id"]},
    ],
    "questions": [
        {"conname": "fk_questions_category", "columns": ["category_id"], "reftable": "categories", "refcols": ["id"]},
        {"conname": "fk_questions_set", "columns": ["question_set_id"], "reftable": "question_sets", "refcols": ["id"]},
    ],
    "exam_sessions": [
        {"conname": "fk_exam_sessions_user", "columns": ["user_id"], "reftable": "users", "refcols": ["id"]},
        {"conname": "fk_exam_sessions_category", "columns": ["category_id"], "reftable": "categories", "refcols": ["id"]},
        {"conname": "fk_exam_sessions_set", "columns": ["question_set_id"], "reftable": "question_sets", "refcols": ["id"]},
    ],
    "exam_answers": [
        {"conname": "fk_exam_answers_session", "columns": ["exam_session_id"], "reftable": "exam_sessions", "refcols": ["id"]},
        {"conname": "fk_exam_answers_question", "columns": ["question_id"], "reftable": "questions", "refcols": ["id"]},
    ],
}

EXPECTED_PKS: Dict[str, List[str]] = {
    "users": ["id"],
    "categories": ["id"],
    "question_sets": ["id"],
    "team_members": ["id"],
    "questions": ["id"],
    "exam_sessions": ["id"],
    "exam_answers": ["id"],
    "promo_banners": ["id"],
}

TABLES = list(EXPECTED_PKS.keys())


def ensure_tables_exist():
    log.info("Ensuring all tables exist as defined by models (create_all with checkfirst=True)...")
    Base.metadata.create_all(bind=engine)


def get_existing_constraints(schema_inspector):
    existing_fks = {}
    existing_pks = {}
    for t in TABLES:
        try:
            fks = schema_inspector.get_foreign_keys(t)
        except Exception as e:
            log.warning("Could not inspect FKs for %s: %s", t, e)
            fks = []
        existing_fks[t] = fks

        try:
            pk = schema_inspector.get_pk_constraint(t)
        except Exception as e:
            log.warning("Could not inspect PK for %s: %s", t, e)
            pk = {"constrained_columns": []}
        existing_pks[t] = pk
    return existing_fks, existing_pks


def fk_match(fk_obj, expected):
    # fk_obj keys: name, constrained_columns, referred_table, referred_columns
    return (
        set(fk_obj.get("constrained_columns", [])) == set(expected["columns"]) and
        fk_obj.get("referred_table") == expected["reftable"] and
        set(fk_obj.get("referred_columns", [])) == set(expected["refcols"])
    )


def add_missing_fk(conn, table: str, exp: Dict[str, str]):
    conname = exp["conname"]
    cols = ", ".join(exp["columns"])  # only single col here
    refcols = ", ".join(exp["refcols"])  # single col
    sql = text(
        f"ALTER TABLE \"{table}\" ADD CONSTRAINT \"{conname}\" FOREIGN KEY ({cols}) REFERENCES \"{exp['reftable']}\" ({refcols});"
    )
    log.info("Adding missing FK %s on %s -> %s(%s)", conname, table, exp["reftable"], refcols)
    conn.execute(sql)


def add_missing_pk(conn, table: str, columns: List[str]):
    # Postgres requires a constraint name; generate one
    conname = f"pk_{table}"
    cols = ", ".join(columns)
    sql = text(f"ALTER TABLE \"{table}\" ADD CONSTRAINT \"{conname}\" PRIMARY KEY ({cols});")
    log.info("Adding missing PK %s on %s(%s)", conname, table, cols)
    conn.execute(sql)


def verify_and_fix():
    ensure_tables_exist()
    insp = inspect(engine)
    existing_fks, existing_pks = get_existing_constraints(insp)

    to_add_fks = []
    to_add_pks = []

    # Compute missing PKs
    for t, pk_cols in EXPECTED_PKS.items():
        curr_pk_cols = existing_pks.get(t, {}).get("constrained_columns", []) or []
        if set(curr_pk_cols) != set(pk_cols):
            to_add_pks.append((t, pk_cols))

    # Compute missing FKs
    for t, fk_list in EXPECTED_FKS.items():
        curr_list = existing_fks.get(t, [])
        for exp in fk_list:
            if not any(fk_match(fk, exp) for fk in curr_list):
                to_add_fks.append((t, exp))

    if not to_add_fks and not to_add_pks:
        log.info("Schema OK: all PKs/FKs present.")
        return

    with engine.begin() as conn:
        for t, pk_cols in to_add_pks:
            try:
                add_missing_pk(conn, t, pk_cols)
            except Exception as e:
                log.warning("Skipping PK add for %s: %s", t, e)
        for t, exp in to_add_fks:
            try:
                add_missing_fk(conn, t, exp)
            except Exception as e:
                log.warning("Skipping FK add for %s.%s: %s", t, exp["columns"], e)

    log.info("Verification complete.")


if __name__ == "__main__":
    verify_and_fix()
