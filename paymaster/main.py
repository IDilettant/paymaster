"""Main app module."""
from dotenv import load_dotenv
from fastapi import FastAPI
from paymaster.api_router import router
from paymaster.events import create_start_app_handler, create_stop_app_handler

load_dotenv()


def get_application() -> FastAPI:
    """Get app instance with handlers and routes.
    
    Returns:
        application instance
    """
    application = FastAPI()
    application.add_event_handler(
        'startup',
        create_start_app_handler(application),
    )
    application.add_event_handler(
        'shutdown',
        create_stop_app_handler(application),
    )
    application.include_router(router)
    return application


app = get_application()
