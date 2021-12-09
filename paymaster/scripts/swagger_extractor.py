"""Extractor openapi documentation from app."""
import yaml
from paymaster.scripts.main import app

if __name__ == '__main__':
    openapi_data = app.openapi()
    with open('doc/openapi.yml', 'w') as file:  # noqa: WPS110
        yaml.dump(openapi_data, file)
