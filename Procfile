# Procfile for Heroku/Railway/Render deployment
web: python run_dashboard.py
worker: celery -A harmonix_splitter.core.orchestrator worker --loglevel=info
