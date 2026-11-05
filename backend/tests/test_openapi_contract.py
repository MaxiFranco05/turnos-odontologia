import pytest
from app.infrastructure.config import Settings
from app.main import create_app


@pytest.fixture(scope="module")
def app_instance():
    test_settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="test_jwt_secret_key_for_hs256_signing_minimum_length_32_chars",
        JWT_ALGORITHM="HS256",
        JWT_EXPIRE_MINUTES=60,
    )
    return create_app(settings=test_settings)


def test_openapi_spec_generation(app_instance):
    """Verify that FastAPI generates a valid OpenAPI 3.x specification."""
    spec = app_instance.openapi()
    assert isinstance(spec, dict), "OpenAPI spec must be a dictionary"
    assert spec.get("openapi", "").startswith("3."), f"Expected OpenAPI 3.x but got {spec.get('openapi')}"
    assert "info" in spec, "OpenAPI spec must contain 'info' metadata"
    assert "paths" in spec, "OpenAPI spec must define 'paths'"
    assert len(spec["paths"]) > 0, "OpenAPI spec must contain registered routes"


def test_openapi_hard_rule_8_noun_based_uris(app_instance):
    """Hard Rule #8: NUNCA verbos en paths -> URIs basadas en sustantivos.
    
    Any historical route containing an action verb must be formally flagged as deprecated.
    Canonical routes must be strictly noun-based without action verbs.
    """
    spec = app_instance.openapi()
    paths = spec.get("paths", {})
    
    verb_blacklist = {
        "crear",
        "borrar",
        "eliminar",
        "actualizar",
        "modificar",
        "cancelar",
        "confirmar",
        "solicitar",
        "marcar",
        "cambiar",
    }
    
    # Verify canonical noun-based password route exists and is active
    assert "/api/auth/password" in paths, "Canonical noun route /api/auth/password must be present"
    password_ops = paths["/api/auth/password"]
    assert "post" in password_ops, "POST /api/auth/password must be implemented"
    assert not password_ops["post"].get("deprecated", False), "/api/auth/password must NOT be deprecated"
    
    # Audit all paths against verbs
    for path, operations in paths.items():
        # Strip path parameters like {id}
        clean_segments = [
            seg.lower()
            for seg in path.strip("/").split("/")
            if not (seg.startswith("{") and seg.endswith("}"))
        ]
        
        found_verbs = [seg for seg in clean_segments if any(verb in seg for verb in verb_blacklist)]
        
        if found_verbs:
            # If path contains a verb, it MUST be an explicitly deprecated compatibility alias
            for method, op in operations.items():
                if method.lower() in {"get", "post", "put", "patch", "delete"}:
                    is_deprecated = op.get("deprecated", False)
                    assert is_deprecated, (
                        f"Path '{path}' [{method.upper()}] violates Hard Rule #8: contains verb segments "
                        f"{found_verbs} but is not marked as deprecated=True"
                    )


def test_openapi_hard_rule_9_no_put_for_partial_mutations(app_instance):
    """Hard Rule #9: NUNCA PUT para updates parciales -> PATCH.
    
    Verifies that no partial updates use PUT and that PATCH is strictly employed for state mutations.
    """
    spec = app_instance.openapi()
    paths = spec.get("paths", {})
    
    # State update endpoint MUST exist and use PATCH
    assert "/api/turnos/{id}" in paths, "Endpoint /api/turnos/{id} must exist"
    turno_ops = paths["/api/turnos/{id}"]
    assert "patch" in turno_ops, "Status modification must use PATCH method (Hard Rule #9)"
    assert "put" not in turno_ops, "Status modification must NOT use PUT method (Hard Rule #9)"
    
    # Global check: ensure no PUT operations exist anywhere in the API contracts
    for path, operations in paths.items():
        assert "put" not in operations, (
            f"Path '{path}' declares HTTP PUT method, which violates Hard Rule #9. Use PATCH instead."
        )


def test_openapi_security_schemes(app_instance):
    """Verify OpenAPI security scheme includes HTTPBearer for JWT authentication."""
    spec = app_instance.openapi()
    components = spec.get("components", {})
    assert "securitySchemes" in components, "OpenAPI spec must define securitySchemes in components"
    
    schemes = components["securitySchemes"]
    assert any(
        s.get("type") == "http" and s.get("scheme", "").lower() == "bearer"
        for s in schemes.values()
    ), f"Expected HTTP Bearer security scheme in components, got {schemes}"
