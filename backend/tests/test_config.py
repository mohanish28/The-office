from app.config import settings


def test_settings_load():
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_EXPIRE_MINUTES > 0
