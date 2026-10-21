"""Deploy the authenticated Poe Astra ASGI adapter to Modal.

Setup once:
  modal token new --source poe
  modal secret create poe-astra POE_ACCESS_KEY=... POE_BOT_NAME=...
Deploy:
  modal deploy modal_deploy.py

Set POE_MODEL in the same secret to override the default model.
Never put the values of these secrets in GitHub.
"""

import modal

modal_app = modal.App("poe-astra")
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi-poe>=0.0.63,<1")
    .add_local_python_source("poe_astra")
)


@modal_app.function(image=image, secrets=[modal.Secret.from_name("poe-astra")], timeout=120)
@modal.asgi_app()
def fastapi_app():
    from poe_astra.bot import create_app

    return create_app()
