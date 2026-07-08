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

    class AutocompleteEvalRequest(BaseModel):
        text: str
        contexts: list[str]
        choices: int = 3
        candidate_tokens: int = 10
        candidate_words: int = 1
        temperature: float = 0.5
        top_p: float = 0.95
        logprob_pool: int = 12

    class AutocompleteCandidateResponse(BaseModel):
        text: str
        starter: str
        rest: str
        logprob: float

    class LogprobTokenResponse(BaseModel):
        text: str
        logprob: float

    class AutocompleteEvalItemResponse(BaseModel):
        context: str
        prompt: str
        candidates: list[AutocompleteCandidateResponse]
        top_tokens: list[LogprobTokenResponse]

    class AutocompleteEvalResponse(BaseModel):
        results: list[AutocompleteEvalItemResponse]

    app = FastAPI(title="Synarmo", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        model = ""
        if engine.config.model_path is not None:
            model = str(engine.config.model_path)
        elif engine.config.model_filename is not None:
            model = engine.config.model_filename
        elif engine.config.model_repo_id is not None:
            model = engine.config.model_repo_id
        return {"status": "ok", "backend": engine.backend.name, "model": model}

    @app.post("/suggest", response_model=SuggestResponse)
    def suggest(request: SuggestRequest) -> SuggestResponse:
        suggestions = engine.suggest(text=request.text, context=request.context)
        return SuggestResponse(
            suggestions=[item.text for item in suggestions],
            scores=[item.score for item in suggestions],
        )

    @app.post("/evaluate/autocomplete", response_model=AutocompleteEvalResponse)
    def evaluate_autocomplete(request: AutocompleteEvalRequest) -> AutocompleteEvalResponse:
        results = engine.evaluate_autocomplete(
            text=request.text,
            contexts=request.contexts,
            choices=request.choices,
            max_tokens=request.candidate_tokens,
            max_words=request.candidate_words,
            temperature=request.temperature,
            top_p=request.top_p,
            logprob_pool=request.logprob_pool,
        )
        return AutocompleteEvalResponse(
            results=[
                AutocompleteEvalItemResponse(
                    context=result.context,
                    prompt=result.prompt,
                    candidates=[
                        AutocompleteCandidateResponse(
                            text=candidate.text,
                            starter=candidate.starter,
                            rest=candidate.rest,
                            logprob=candidate.logprob,
                        )
                        for candidate in result.candidates
                    ],
                    top_tokens=[
                        LogprobTokenResponse(text=token.text, logprob=token.logprob)
                        for token in result.top_tokens
                    ],
                )
                for result in results
            ]
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
