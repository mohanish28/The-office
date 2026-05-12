from app.security.api_key_vault import decrypt_key, encrypt_key, get_nim_api_key


def test_encrypt_decrypt_roundtrip():
    raw = "nvapi-supersecret-abc123"
    enc = encrypt_key(raw)
    assert enc != raw
    assert decrypt_key(enc) == raw


def test_get_nim_api_key_reads_env(monkeypatch):
    monkeypatch.setenv("NIM_API_KEY", "nvapi-test-key")
    assert get_nim_api_key() == "nvapi-test-key"
