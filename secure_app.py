"""Production entrypoint; app.py remains the unchanged research pipeline."""
from app import app as original_app
from backend_guard import configured_guard
app = configured_guard(original_app)
