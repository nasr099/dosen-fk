import logging
from typing import List, Dict
from sqlalchemy import text
from app.db.base import engine

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("repair_constraints")

# Define constraints we expect to exist
FKS = [
    # question_sets
    {
        "name": "fk_question_sets_category",
        "table": "question_sets",
        "columns": ["category_id"],
        "reftable": "categories",
        "refcols": ["id"],
        "ondelete": "CASCADE",
    },
    # questions
    {
        "name": "fk_questions_category",
        "table": "questions",
        "columns": ["category_id"],
        "reftable": "categories",
        "refcols": ["id"],
        "ondelete": "CASCADE",
    },
    {
        "name": "fk_questions_set",
        "table": "questions",
        "columns": ["question_set_id"],
        "reftable": "question_sets",
        "refcols": ["id"],
        "ondelete": "SET NULL",
    },
    # exam_sessions
    {
        "name": "fk_exam_sessions_user",
        "table": "exam_sessions",
        "columns": ["user_id"],
        "reftable": "users",
        "refcols": ["id"],
        "ondelete": "CASCADE",
    },
    {
        "name": "fk_exam_sessions_category",
        "table": "exam_sessions",
        "columns": ["category_id"],
        "reftable": "categories",
        "refcols": ["id"],
        "ondelete": "SET NULL",
    },
    {
        "name": "fk_exam_sessions_set",
        "table": "exam_sessions",
        "columns": ["question_set_id"],
        "reftable": "question_sets",
        "refcols": ["id"],
        "ondelete": "SET NULL",
    },
    # exam_answers
    {
        "name": "fk_exam_answers_session",
        "table": "exam_answers",
        "columns": ["exam_session_id"],
        "reftable": "exam_sessions",
        "refcols": ["id"],
        "ondelete": "CASCADE",
    },
    {
        "name": "fk_exam_answers_question",
        "table": "exam_answers",
        "columns": ["question_id"],
        "reftable": "questions",
        "refcols": ["id"],
        "ondelete": "CASCADE",
    },
]

PKS = {
    "users": ["id"],
    "categories": ["id"],
    "question_sets": ["id"],
    "team_members": ["id"],
    "questions": ["id"],
    "exam_sessions": ["id"],
    "exam_answers": ["id"],
    "promo_banners": ["id"],
}

CHECK_CONSTRAINT_SQL = text(
    """
    SELECT 1 FROM pg_constraint c
    WHERE c.conname = :name
    """
)

CHECK_PK_SQL = text(
    """
    SELECT 1 FROM pg_constraint c
    JOIN pg_class rel ON rel.oid = c.conrelid
    WHERE rel.relname = :table AND c.contype = 'p'
    """
)

ADD_FK_SQL_TMPL = (
    "ALTER TABLE \"{table}\" ADD CONSTRAINT \"{name}\" "
    "FOREIGN KEY ({cols}) REFERENCES \"{reftable}\" ({refcols}) ON DELETE {ondelete};"
)

ADD_PK_SQL_TMPL = "ALTER TABLE \"{table}\" ADD CONSTRAINT \"pk_{table}\" PRIMARY KEY ({cols});"

CREATE_INDEX_TMPL = "CREATE INDEX IF NOT EXISTS idx_{table}_{col} ON \"{table}\"({col});"

INDEX_COLUMNS = [
    ("questions", "category_id"),
    ("questions", "question_set_id"),
    ("question_sets", "category_id"),
    ("exam_sessions", "user_id"),
    ("exam_sessions", "category_id"),
    ("exam_sessions", "question_set_id"),
    ("exam_answers", "exam_session_id"),
    ("exam_answers", "question_id"),
]


def repair():
    with engine.begin() as conn:
        # Ensure PKs
        for table, cols in PKS.items():
            has_pk = conn.execute(CHECK_PK_SQL, {"table": table}).scalar() is not None
            if not has_pk:
                log.info("Adding PK on %s(%s)", table, ",".join(cols))
                conn.execute(text(ADD_PK_SQL_TMPL.format(table=table, cols=", ".join(cols))))

        # Ensure FKs
        for fk in FKS:
            exists = conn.execute(CHECK_CONSTRAINT_SQL, {"name": fk["name"]}).scalar() is not None
            if not exists:
                sql = ADD_FK_SQL_TMPL.format(
                    table=fk["table"],
                    name=fk["name"],
                    cols=", ".join(fk["columns"]),
                    reftable=fk["reftable"],
                    refcols=", ".join(fk["refcols"]),
                    ondelete=fk["ondelete"],
                )
                log.info("Adding missing FK %s", fk["name"])
                conn.execute(text(sql))

        # Helpful indexes
        for table, col in INDEX_COLUMNS:
            conn.execute(text(CREATE_INDEX_TMPL.format(table=table, col=col)))

    log.info("Schema repair complete.")


if __name__ == "__main__":
    repair()
