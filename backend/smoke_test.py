from fastapi.testclient import TestClient

from app.main import app


with TestClient(app) as client:
    print(client.get("/health").json())
    print(client.post("/api/admin/seed").json())
    for query in ["노트북", "품질", "리콜", "전기"]:
        docs = client.get("/api/documents", params={"query": query}).json()
        print(query, len(docs), [doc["title"] for doc in docs])
    print("sources", len(client.get("/api/sources").json()))
