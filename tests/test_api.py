import pytest
from fastapi.testclient import TestClient

from hf_edu.api.main import app, get_llm, get_store


@pytest.fixture
def client(fake_llm, store):
    app.dependency_overrides[get_llm] = lambda: fake_llm
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_extract(client, note):
    r = client.post("/v1/extract", json=note.model_dump())
    assert r.status_code == 200 and r.json()["hf_type"] == "HFrEF"


def test_education_json(client, note):
    r = client.post("/v1/education", json=note.model_dump())
    assert r.status_code == 200
    body = r.json()
    assert {"context", "retrieved_chunk_ids", "material"} <= set(body)


def test_education_html(client, note):
    r = client.post("/v1/education/html", json=note.model_dump())
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    assert "심부전 퇴원 안내" in r.text


def test_validation_error(client):
    assert client.post("/v1/education", json={"text": "x"}).status_code == 422
