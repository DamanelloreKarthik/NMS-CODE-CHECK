def safe_commit(db):
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise