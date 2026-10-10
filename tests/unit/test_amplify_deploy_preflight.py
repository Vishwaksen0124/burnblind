from pathlib import Path

import pytest

from scripts.deploy_amplify_manual import validate_frontend_configuration


@pytest.fixture
def build_dir(tmp_path: Path) -> Path:
    assets = tmp_path / "assets"
    assets.mkdir()
    return tmp_path


def settings() -> dict[str, str]:
    return {
        "VITE_API_BASE_URL": "https://api.example.test/prod/api",
        "VITE_COGNITO_REGION": "us-east-2",
        "VITE_COGNITO_USER_POOL_ID": "us-east-2_example",
        "VITE_COGNITO_CLIENT_ID": "exampleclientid",
    }


def test_preflight_accepts_bundle_with_deployment_configuration(build_dir: Path) -> None:
    values = settings()
    # Vite can fold this ID away because the frontend uses it only as a
    # boolean switch for reviewer authentication.
    values.pop("VITE_COGNITO_USER_POOL_ID")
    (build_dir / "assets" / "app.js").write_text(" ".join(values.values()))

    validate_frontend_configuration(build_dir, settings())


def test_preflight_rejects_missing_api_configuration(build_dir: Path) -> None:
    values = settings()
    values["VITE_API_BASE_URL"] = ""
    (build_dir / "assets" / "app.js").write_text(" ".join(settings().values()))

    with pytest.raises(ValueError, match="VITE_API_BASE_URL"):
        validate_frontend_configuration(build_dir, values)


def test_preflight_rejects_bundle_built_with_wrong_api(build_dir: Path) -> None:
    (build_dir / "assets" / "app.js").write_text(" ".join(settings().values()).replace("api.example.test", "wrong.example.test"))

    with pytest.raises(ValueError, match="VITE_API_BASE_URL"):
        validate_frontend_configuration(build_dir, settings())
