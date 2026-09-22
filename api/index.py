from fastapi import (
    Depends,
    FastAPI,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from api.profile import (
    CurrentProfile,
    get_current_profile,
)
from api.routes.analytics import (
    router as analytics_router,
)
from api.routes.opportunities import (
    router as opportunity_router,
)
from api.routes.resumes import (
    router as resume_router,
)
from api.routes.search import (
    router as search_router,
)


from api.routes.manual_jobs import router as manual_jobs_router

app = FastAPI(
    title="CareerCompass API",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    search_router
)

app.include_router(
    resume_router
)

app.include_router(
    analytics_router
)

app.include_router(
    opportunity_router
)


@app.get("/api")
def api_root():
    return {
        "name":
            "CareerCompass API",

        "status":
            "running",
    }


@app.get("/api/health")
def health():
    return {
        "status":
            "healthy",
    }


@app.get("/api/me")
def get_me(
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    return {
        "profile_id":
            profile.profile_id,

        "user_id":
            str(
                profile.user_id
            ),

        "profile_name":
            profile.profile_name,
    }


app.include_router(manual_jobs_router)
