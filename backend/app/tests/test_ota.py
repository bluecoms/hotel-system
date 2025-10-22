# -*- coding: utf-8 -*-
# OTA Router 기본 동작 테스트

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_channels_ok():
    """OTA 채널 목록 API 기본 동작 확인"""
    res = client.get("/api/ota/channels", headers={"X-Internal-Token": "dev-admin-token"})
    assert res.status_code == 200
    body = res.json()
    assert "items" in body
    print("✅ OTA 채널 목록:", body.get("items", []))
