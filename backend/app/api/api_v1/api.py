from fastapi import APIRouter
from .endpoints import auth, users, categories, questions, exams, promos, sets, team, posts, zoom_discussions, essays, analytics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(exams.router, prefix="/exams", tags=["exams"])
api_router.include_router(promos.router, prefix="/promos", tags=["promos"])
api_router.include_router(sets.router, prefix="/sets", tags=["sets"])
api_router.include_router(team.router, prefix="/team", tags=["team"]) 
api_router.include_router(posts.router, prefix="/posts", tags=["posts"]) 
api_router.include_router(zoom_discussions.router, prefix="/zoom-discussions", tags=["zoom"]) 
api_router.include_router(essays.router, prefix="", tags=["essays"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
