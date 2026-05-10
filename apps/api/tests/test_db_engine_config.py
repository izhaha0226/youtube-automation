from app.core.db import engine


def test_db_engine_pre_pings_pooled_connections():
    assert getattr(engine.pool, "_pre_ping", False) is True
