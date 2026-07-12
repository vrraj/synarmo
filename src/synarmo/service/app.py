from pathlib import Path

from synarmo.engine import SynarmoEngine


_UI_ROOT = Path(__file__).resolve().parent.parent / "ui"
_UI_TEMPLATES_DIR = _UI_ROOT / "templates"
_UI_STATIC_DIR = _UI_ROOT / "static"


def create_app(engine: SynarmoEngine):
    try:
        from fastapi import FastAPI, Request, WebSocket
        from fastapi.responses import HTMLResponse, RedirectResponse
        from fastapi.staticfiles import StaticFiles
        from fastapi.templating import Jinja2Templates
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError("Install service extras first: pip install synarmo[service]") from exc

    compose_defaults = _compose_defaults(engine)

    class SuggestRequest(BaseModel):
        text: str
        context: str | None = None

    class SuggestResponse(BaseModel):
        suggestions: list[str]
        scores: list[float]

    class AutocompleteEvalRequest(BaseModel):
        text: str
        contexts: list[str]
        choices: int = compose_defaults["choices"]
        candidate_tokens: int = compose_defaults["candidate_tokens"]
        candidate_words: int = compose_defaults["candidate_words"]
        temperature: float = compose_defaults["temperature"]
        top_p: float = compose_defaults["top_p"]
        continuation_temperature: float = compose_defaults["continuation_temperature"]
        continuation_top_p: float = compose_defaults["continuation_top_p"]
        continuation_top_k: int = compose_defaults["continuation_top_k"]
        logprob_pool: int = compose_defaults["logprob_pool"]

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

    _mount_ui(
        app,
        engine=engine,
        Request=Request,
        HTMLResponse=HTMLResponse,
        RedirectResponse=RedirectResponse,
        StaticFiles=StaticFiles,
        Jinja2Templates=Jinja2Templates,
    )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", **engine.runtime_diagnostics()}

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
            continuation_temperature=request.continuation_temperature,
            continuation_top_p=request.continuation_top_p,
            continuation_top_k=request.continuation_top_k,
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


def _mount_ui(
    app,
    *,
    engine: SynarmoEngine,
    Request,
    HTMLResponse,
    RedirectResponse,
    StaticFiles,
    Jinja2Templates,
) -> None:
    if not _UI_TEMPLATES_DIR.exists():
        return
    if not _UI_STATIC_DIR.exists():
        return

    templates = Jinja2Templates(directory=str(_UI_TEMPLATES_DIR))
    app.mount("/static", StaticFiles(directory=str(_UI_STATIC_DIR)), name="synarmo-ui-static")

    @app.get("/ui", response_class=HTMLResponse)
    def synarmo_ui(request: Request):  # type: ignore[misc]
        return templates.TemplateResponse(
            request,
            "synarmo.html",
            {"compose_defaults": _compose_defaults(engine)},
        )

    @app.get("/")
    def synarmo_ui_root():  # type: ignore[misc]
        return RedirectResponse(url="/ui")


def _compose_defaults(engine: SynarmoEngine) -> dict[str, int | float]:
    return {
        "choices": engine.config.max_suggestions,
        "candidate_tokens": engine.config.max_tokens,
        "candidate_words": engine.config.max_suggestion_words,
        "temperature": engine.config.temperature,
        "top_p": engine.config.top_p,
        "continuation_temperature": engine.config.continuation_temperature,
        "continuation_top_p": engine.config.continuation_top_p,
        "continuation_top_k": engine.config.continuation_top_k,
        "logprob_pool": engine.config.logprob_pool,
    }
