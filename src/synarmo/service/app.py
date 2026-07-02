from synarmo.engine import SynarmoEngine


def create_app(engine: SynarmoEngine):
    try:
        from fastapi import FastAPI, WebSocket
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError("Install service extras first: pip install synarmo[service]") from exc

    class SuggestRequest(BaseModel):
        text: str
        context: str | None = None

    class SuggestResponse(BaseModel):
        suggestions: list[str]
        scores: list[float]

    app = FastAPI(title="Synarmo", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "backend": engine.backend.name}

    @app.post("/suggest", response_model=SuggestResponse)
    def suggest(request: SuggestRequest) -> SuggestResponse:
        suggestions = engine.suggest(text=request.text, context=request.context)
        return SuggestResponse(
            suggestions=[item.text for item in suggestions],
            scores=[item.score for item in suggestions],
        )

    @app.websocket("/ws/suggest")
    async def suggest_ws(websocket: WebSocket) -> None:
        await websocket.accept()
        while True:
            payload = await websocket.receive_json()
            request = SuggestRequest.model_validate(payload)
            suggestions = engine.suggest(text=request.text, context=request.context)
            await websocket.send_json(
                {
                    "suggestions": [item.text for item in suggestions],
                    "scores": [item.score for item in suggestions],
                }
            )

    return app
