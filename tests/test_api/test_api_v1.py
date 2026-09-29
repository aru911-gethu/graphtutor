import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_demo_session_creation(client: AsyncClient):
    response = await client.post("/api/v1/demo/session")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "guest_id" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["platform"] == "web_guest"


@pytest.mark.asyncio
async def test_me_profile_and_update(client: AsyncClient):
    demo_res = await client.post("/api/v1/demo/session")
    token = demo_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = await client.get("/api/v1/me", headers=headers)
    assert me_res.status_code == 200
    profile = me_res.json()
    assert "id" in profile
    assert profile["explanation_level"] == "intermediate"

    update_res = await client.put(
        "/api/v1/me",
        json={"explanation_level": "advanced", "interests": ["Quantum AI", "Robotics"]},
        headers=headers
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["explanation_level"] == "advanced"
    assert "Quantum AI" in updated["interests"]


@pytest.mark.asyncio
async def test_cytoscape_graph(client: AsyncClient):
    response = await client.get("/api/v1/graph")
    assert response.status_code == 200
    data = response.json()
    assert "elements" in data
    assert "nodes" in data["elements"]
    assert "edges" in data["elements"]
    assert "summary" in data
    assert data["summary"]["total_nodes"] > 0

    first_node = data["elements"]["nodes"][0]
    assert "data" in first_node
    assert "id" in first_node["data"]
    assert "label" in first_node["data"]
    assert "status" in first_node["data"]


@pytest.mark.asyncio
async def test_lesson_seed_and_streaming(client: AsyncClient):
    res = await client.get("/api/v1/lessons/transformers")
    assert res.status_code == 200
    data = res.json()
    assert data["concept_slug"] == "transformers"
    assert data["theme"] == "ai_pipeline"
    assert "intuition_anchor" in data
    assert len(data["tensor_pipeline_steps"]) > 0

    stream_res = await client.get("/api/v1/lessons/transformers?stream=1")
    assert stream_res.status_code == 200
    assert "text/event-stream" in stream_res.headers.get("content-type", "")
    content = stream_res.text
    assert "data: " in content
    assert "[DONE]" in content


@pytest.mark.asyncio
async def test_reviews_due_and_submission(client: AsyncClient):
    due_res = await client.get("/api/v1/reviews/due")
    assert due_res.status_code == 200
    due_items = due_res.json()
    assert isinstance(due_items, list)

    sub_res = await client.post(
        "/api/v1/reviews/transformers",
        json={"rating": 3, "target_depth": "working"}
    )
    assert sub_res.status_code == 200
    review_data = sub_res.json()
    assert "mastery" in review_data
    assert "stability" in review_data
    assert "due" in review_data


@pytest.mark.asyncio
async def test_learning_path(client: AsyncClient):
    res = await client.get("/api/v1/path?goal=transformers")
    assert res.status_code == 200
    path = res.json()
    assert path["goal"] == "transformers"
    assert "steps" in path
    assert len(path["steps"]) > 0
    assert "next_step" in path


@pytest.mark.asyncio
async def test_ingest_endpoint(client: AsyncClient):
    res = await client.post(
        "/api/v1/ingest",
        json={
            "source_type": "text",
            "content": "Self-attention transforms query and key vectors through dot products to compute context."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["source_type"] == "text"
    assert "concepts" in data


@pytest.mark.asyncio
async def test_assessment_endpoints(client: AsyncClient):
    q_res = await client.get("/api/v1/assessment/questions/transformers")
    assert q_res.status_code == 200
    questions = q_res.json()
    assert len(questions) > 0
    q = questions[0]
    assert "id" in q
    assert "prompt" in q

    sub_res = await client.post(
        "/api/v1/assessment/submit",
        json={
            "question_id": q["id"],
            "concept_slug": "transformers",
            "selected_index": q["correct_index"],
            "response_time_ms": 4200,
            "current_theta": 0.5
        }
    )
    assert sub_res.status_code == 200
    result = sub_res.json()
    assert result["is_correct"] is True
    assert result["new_theta"] > 0.5
    assert result["skill_tag"] in ["unseen", "exposed", "recognizes", "applies", "explains", "mastered"]

    rep_res = await client.get("/api/v1/assessment/report")
    assert rep_res.status_code == 200
    report = rep_res.json()
    assert "overall_ability" in report
    assert "radar_chart" in report

    chl_res = await client.post(
        "/api/v1/assessment/challenge",
        json={
            "concept_slug": "transformers",
            "score": 0.85,
            "question_ids": [q["id"]]
        }
    )
    assert chl_res.status_code == 200
    chl = chl_res.json()
    assert "challenge_id" in chl
    assert "/challenge/" in chl["share_url"]
