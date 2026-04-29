from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.cloud.api_routes import router
from app.cloud.database import Base, engine
from app.common.config import load_config
from app.common.utils import ensure_dir
from fastapi.middleware.cors import CORSMiddleware

cfg = load_config()

app = FastAPI(title="Driver Behavior Hybrid Cloud")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

templates = Jinja2Templates(directory="templates")

upload_dir = ensure_dir(cfg["storage"]["cloud_upload_dir"])
static_dir = ensure_dir("static")

app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Driver Behavior Monitoring Dashboard",
        },
    )