"""Extractor openapi documentation from app."""
import yaml
from paymaster.app.main import app


def main():
    """Extract openapi documentation from app."""
    openapi_data = app.openapi()
    with open('doc/openapi.yml', 'w') as file:  # noqa: WPS110
        yaml.dump(openapi_data, file)


if __name__ == '__main__':
    main()
