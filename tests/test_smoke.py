"""Smoke tests so CI is green from day one."""

import alys


def test_version():
    assert alys.__version__


def test_config_imports():
    from alys import config

    assert config.MIN_LISTEN_MS > 0
    assert config.SESSION_GAP_SECONDS > 0
