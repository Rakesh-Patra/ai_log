#!/bin/bash
cd /mnt/c/ai_log/k8s-kind-voting-app/agent
source venv/bin/activate
python -c "
import traceback
try:
    from app.config import get_settings
    s = get_settings()
    print('Config OK:', s.app_name)
    print('Model:', s.model_name)
    print('Guardrails:', s.guardrails_enabled)
except Exception as e:
    traceback.print_exc()

try:
    from app.guardrails.validators import validate_input, validate_output
    r = validate_input('list all pods')
    print('Input validation OK:', r.is_valid, r.message)
    r2 = validate_output('Here are your pods')
    print('Output validation OK:', r2.is_valid)
except Exception as e:
    traceback.print_exc()

try:
    from app.main import app
    print('FastAPI app OK:', app.title)
except Exception as e:
    traceback.print_exc()

try:
    import uvicorn
    print('Uvicorn version:', uvicorn.__version__)
except Exception as e:
    traceback.print_exc()
"
