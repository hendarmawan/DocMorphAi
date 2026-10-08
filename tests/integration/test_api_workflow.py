"""The Release-1 vertical slice through the HTTP API:
upload DOCX -> inspect structure -> select template -> render HTML ->
prompt a design change -> undo/redo/restore -> export."""

from __future__ import annotations

from fixtures.factory import make_docx

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _upload(client, data=None, name="report.docx", tenant=None):
    headers = {"X-Tenant-ID": tenant} if tenant else {}
    return client.post("/v1/documents", files={"file": (name, data or make_docx(), DOCX_MIME)}, headers=headers)


def test_health_and_readiness(client):
    assert client.get("/health").json()["status"] == "ok"
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["checks"] == {"database": True, "storage": True}


def test_templates_endpoint(client):
    ids = {t["id"] for t in client.get("/v1/templates").json()}
    assert ids >= {"academic", "corporate", "bilingual", "presentation"}


def test_docx_vertical_slice(client):
    # 1. upload
    res = _upload(client)
    assert res.status_code == 201, res.text
    body = res.json()
    doc_id = body["document"]["id"]
    assert body["document"]["title"] == "Quarterly Strategy Report"

    # 2. inspect structure (+ AI understanding)
    structure = client.get(f"/v1/documents/{doc_id}/structure").json()
    titles = [o["title"] for o in structure["outline"]]
    assert "Executive summary" in titles and "Budget" in titles
    assert structure["counts"]["table"] == 1
    assert structure["analysis"]["suggested_template"] == "corporate"
    content_before = client.get(f"/v1/documents/{doc_id}/content").json()

    # 3. select a template
    state = client.post(f"/v1/documents/{doc_id}/design/template", json={"template_id": "academic"}).json()
    assert state["current"]["design"]["template_id"] == "academic"
    assert state["can_undo"] and not state["can_redo"]

    # 4. render HTML
    render = client.get(f"/v1/documents/{doc_id}/render")
    assert render.status_code == 200
    assert "sandbox" in render.headers["content-security-policy"]
    assert "Executive summary" in render.text

    # 5. change the design through a prompt
    result = client.post(
        f"/v1/documents/{doc_id}/design/prompt", json={"prompt": "Make it dark with bigger text and swipe like slides"}
    )
    assert result.status_code == 200, result.text
    result = result.json()
    assert result["content_unchanged"] is True
    assert result["design"]["design"]["reader"]["mode"] == "swipe"
    assert result["design"]["origin"] == "ai"
    assert client.get(f"/v1/documents/{doc_id}/content").json() == content_before

    # 6. versioning: undo / redo / restore
    undone = client.post(f"/v1/documents/{doc_id}/design/undo").json()
    assert undone["current"]["design"]["template_id"] == "academic"
    assert undone["current"]["design"]["reader"]["mode"] == "scroll"
    redone = client.post(f"/v1/documents/{doc_id}/design/redo").json()
    assert redone["current"]["design"]["reader"]["mode"] == "swipe"
    restored = client.post(f"/v1/documents/{doc_id}/design/restore", json={"version": 1}).json()
    assert restored["current"]["origin"] == "restore"
    assert restored["current"]["design"]["template_id"] == "corporate"
    history = client.get(f"/v1/documents/{doc_id}/design/versions").json()
    assert [v["origin"] for v in history] == ["template", "template", "ai", "restore"]

    # 7. export standalone HTML
    export = client.get(f"/v1/documents/{doc_id}/export")
    assert export.status_code == 200
    assert 'filename="quarterly-strategy-report.html"' in export.headers["content-disposition"]
    assert export.text.startswith("<!doctype html>")
    assert "Revenue grew" in export.text


def test_redo_branch_is_discarded_after_new_edit(client):
    doc_id = _upload(client).json()["document"]["id"]
    client.post(f"/v1/documents/{doc_id}/design/template", json={"template_id": "academic"})
    client.post(f"/v1/documents/{doc_id}/design/undo")
    state = client.post(f"/v1/documents/{doc_id}/design/template", json={"template_id": "bilingual"}).json()
    assert not state["can_redo"]
    assert client.post(f"/v1/documents/{doc_id}/design/redo").json()["error"]["code"] == "nothing_to_redo"


def test_content_edit_prompt_is_refused(client):
    doc_id = _upload(client).json()["document"]["id"]
    res = client.post(f"/v1/documents/{doc_id}/design/prompt", json={"prompt": "translate this into French"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "content_edit_refused"
    assert client.get(f"/v1/documents/{doc_id}/design").json()["current"]["version"] == 1


def test_tenant_isolation(client):
    doc_id = _upload(client, tenant="acme").json()["document"]["id"]
    assert client.get(f"/v1/documents/{doc_id}", headers={"X-Tenant-ID": "acme"}).status_code == 200
    other = client.get(f"/v1/documents/{doc_id}", headers={"X-Tenant-ID": "globex"})
    assert other.status_code == 404
    assert client.get(f"/v1/documents/{doc_id}/export", headers={"X-Tenant-ID": "globex"}).status_code == 404
    assert client.get("/v1/documents", headers={"X-Tenant-ID": "globex"}).json() == []


def test_delete_document(client):
    doc_id = _upload(client).json()["document"]["id"]
    assert client.delete(f"/v1/documents/{doc_id}").status_code == 204
    assert client.get(f"/v1/documents/{doc_id}").status_code == 404
