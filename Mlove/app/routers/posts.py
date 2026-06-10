from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Post, User
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    current_user = None
    user_id = request.session.get('user_id')
    if user_id:
        current_user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts, "current_user": current_user})

@router.get("/posts/new")
async def create_post_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("post_form.html", {"request": request, "post": None})

@router.post("/posts/new")
async def create_post(
    request: Request,
    title: str = Form(...),
    body: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = Post(title=title, body=body, author_id=current_user.id)
    db.add(post)
    db.commit()
    return RedirectResponse(f"/posts/{post.id}", status_code=303)

@router.get("/posts/{post_id}")
async def post_detail(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404)
    current_user = None
    user_id = request.session.get('user_id')
    if user_id:
        current_user = db.query(User).filter(User.id == user_id).first()
    is_author = current_user and current_user.id == post.author_id
    return templates.TemplateResponse("post_detail.html", {"request": request, "post": post, "current_user": current_user, "is_author": is_author})

@router.get("/posts/{post_id}/edit")
async def edit_post_page(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404)
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403)
    return templates.TemplateResponse("post_form.html", {"request": request, "post": post})

@router.post("/posts/{post_id}/edit")
async def edit_post(
    post_id: int,
    title: str = Form(...),
    body: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404)
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403)
    post.title = title
    post.body = body
    db.commit()
    return RedirectResponse(f"/posts/{post_id}", status_code=303)

@router.post("/posts/{post_id}/delete")
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404)
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403)
    db.delete(post)
    db.commit()
    return RedirectResponse("/", status_code=303)