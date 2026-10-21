"""Local Poe bot entrypoint. An external tunnel is needed for Poe to reach localhost."""

from poe_astra.bot import create_app

# For uvicorn: uvicorn main:app --host 0.0.0.0 --port 8080
app = create_app()
