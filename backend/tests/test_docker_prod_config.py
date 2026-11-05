import os
from pathlib import Path
import pytest
import yaml

# Root directory of the repository
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_docker_compose_prod_exists_and_valid():
    """Verify docker-compose.prod.yml exists and parses as valid YAML."""
    compose_path = REPO_ROOT / "docker-compose.prod.yml"
    assert compose_path.exists(), "docker-compose.prod.yml must exist at repo root"
    
    with open(compose_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    assert isinstance(data, dict), "docker-compose.prod.yml must parse into a dictionary"
    assert "services" in data, "compose file must define services"
    assert set(data["services"].keys()) == {"postgres", "api", "frontend"}, (
        f"Expected services postgres, api, frontend but got {list(data['services'].keys())}"
    )


def test_docker_compose_prod_rule_10_healthchecks_on_all_services():
    """Hard Rule #10: Every service MUST declare a healthcheck."""
    compose_path = REPO_ROOT / "docker-compose.prod.yml"
    with open(compose_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    services = data.get("services", {})
    for service_name, config in services.items():
        assert "healthcheck" in config, f"Service '{service_name}' violates Hard Rule #10: missing healthcheck"
        hc = config["healthcheck"]
        assert "test" in hc, f"Service '{service_name}' healthcheck missing 'test'"
        assert "interval" in hc, f"Service '{service_name}' healthcheck missing 'interval'"
        assert "timeout" in hc, f"Service '{service_name}' healthcheck missing 'timeout'"
        assert "retries" in hc, f"Service '{service_name}' healthcheck missing 'retries'"


def test_docker_compose_prod_rule_10_resource_limits_on_all_services():
    """Hard Rule #10: Every service MUST declare CPU and memory limits."""
    compose_path = REPO_ROOT / "docker-compose.prod.yml"
    with open(compose_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    services = data.get("services", {})
    for service_name, config in services.items():
        assert "deploy" in config, f"Service '{service_name}' missing deploy configuration"
        deploy = config["deploy"]
        assert "resources" in deploy, f"Service '{service_name}' missing deploy.resources"
        resources = deploy["resources"]
        assert "limits" in resources, f"Service '{service_name}' missing deploy.resources.limits"
        limits = resources["limits"]
        assert "cpus" in limits, f"Service '{service_name}' missing CPU limit"
        assert "memory" in limits, f"Service '{service_name}' missing memory limit"


def test_docker_compose_prod_network_isolation_and_ports():
    """Postgres must not expose host ports, frontend exposes 80, api internal only."""
    compose_path = REPO_ROOT / "docker-compose.prod.yml"
    with open(compose_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    services = data.get("services", {})
    postgres = services.get("postgres", {})
    assert "ports" not in postgres, "PostgreSQL in prod must NOT expose any host ports (5432)"
    
    api = services.get("api", {})
    assert "ports" not in api, "API service in prod must NOT expose host ports (only reached via reverse proxy)"
    
    frontend = services.get("frontend", {})
    assert "ports" in frontend, "Frontend service must expose HTTP port to host"
    exposed = frontend["ports"]
    assert any("80:80" in str(p) for p in exposed), "Frontend must publish port 80:80"
    
    # Volumes check
    assert "volumes" in data, "compose file must define top-level volumes"
    assert "postgres_data" in data["volumes"], "compose file must declare postgres_data named volume"


def test_docker_compose_prod_dependencies_and_network_wiring():
    """Triangulation: Services must depend on health of dependencies and share internal network."""
    compose_path = REPO_ROOT / "docker-compose.prod.yml"
    with open(compose_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    services = data.get("services", {})
    api = services.get("api", {})
    frontend = services.get("frontend", {})
    
    assert "depends_on" in api, "api must declare depends_on"
    assert api["depends_on"]["postgres"]["condition"] == "service_healthy"
    
    assert "depends_on" in frontend, "frontend must declare depends_on"
    assert frontend["depends_on"]["api"]["condition"] == "service_healthy"
    
    # Check shared network
    assert "networks" in data, "compose file must declare networks"
    assert "app_network" in data["networks"], "compose file must define app_network"
    for s_name in ["postgres", "api", "frontend"]:
        assert "app_network" in services[s_name].get("networks", []), f"service {s_name} must connect to app_network"


def test_frontend_dockerfile_multi_stage_and_healthcheck():
    """Frontend Dockerfile must be multi-stage with builder and runner, and declare HEALTHCHECK."""
    dockerfile_path = REPO_ROOT / "frontend" / "Dockerfile"
    assert dockerfile_path.exists(), "frontend/Dockerfile must exist"
    
    content = dockerfile_path.read_text(encoding="utf-8")
    from_lines = [line for line in content.splitlines() if line.strip().upper().startswith("FROM ")]
    assert len(from_lines) >= 2, "frontend/Dockerfile must be multi-stage (at least 2 FROM instructions)"
    
    assert "HEALTHCHECK" in content, "frontend/Dockerfile must declare HEALTHCHECK instruction (Rule #10)"
    assert "nginx" in content.lower(), "frontend runner stage must use nginx"
    assert "npm run build" in content, "frontend builder stage must execute build command"
    assert "/usr/share/nginx/html" in content, "frontend runner must copy to nginx html directory"


def test_frontend_nginx_conf_routing_and_proxy():
    """Nginx configuration must configure SPA fallback, reverse proxy to api, and /healthz."""
    nginx_path = REPO_ROOT / "frontend" / "nginx.conf"
    assert nginx_path.exists(), "frontend/nginx.conf must exist"
    
    content = nginx_path.read_text(encoding="utf-8")
    assert "try_files $uri $uri/ /index.html" in content, "nginx.conf must contain SPA fallback routing"
    assert "proxy_pass" in content, "nginx.conf must configure reverse proxy pass"
    assert "/api/" in content, "nginx.conf must route /api/ traffic"
    assert "/healthz" in content, "nginx.conf must define /healthz endpoint"
    assert "200" in content, "nginx.conf /healthz must return 200 status code"
    assert "gzip on" in content, "nginx.conf must enable gzip compression"
    assert "X-Frame-Options" in content, "nginx.conf must include security headers"


def test_env_prod_example_clean_and_synthetic():
    """Verify .env.prod.example exists, defines production variables, and has no real secrets."""
    env_path = REPO_ROOT / ".env.prod.example"
    assert env_path.exists(), ".env.prod.example must exist"
    
    content = env_path.read_text(encoding="utf-8")
    assert "APP_ENV=production" in content or "APP_ENV" in content
    assert "DATABASE_URL" in content
    assert "JWT_SECRET" in content
    assert "POSTGRES_PASSWORD" in content
    assert "TIMEZONE=" in content
    
    # Ensure placeholder / synthetic patterns
    assert "CHANGE_THIS_IN_PRODUCTION" in content or "change_this" in content.lower() or "example" in content.lower()
