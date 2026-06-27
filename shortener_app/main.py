import os  # <-- Make sure this is at the very top
import validators
from sqlalchemy.orm import Session
from starlette.datastructures import URL

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse  # <-- Make sure HTMLResponse is here

from . import crud, models, schemas
from .config import get_settings
from .database import SessionLocal, engine

# 1. First, create the app instance!
app = FastAPI()
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint = app.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)

def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)


# 2. Now it is safe to use @app.get("/") since 'app' is defined above!
@app.get("/", response_class=HTMLResponse)
def read_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "..", "index.html")
    
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Error: index.html is missing outside the shortener_app folder."
@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    db_url = crud.create_db_url(db=db, url=url)
    return get_admin_info(db_url)


@app.get("/{url_key}")
def forward_to_target_url(
    url_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@app.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo,
)
def get_url_info(
    secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)


@app.delete("/admin/{secret_key}")
def delete_url(
    secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.deactivate_db_url_by_secret_key(
        db, secret_key=secret_key
    ):
        message = (
            f"Successfully deleted shortened URL for '{db_url.target_url}'"
        )
        return {"detail": message}
    else:
        raise_not_found(request)