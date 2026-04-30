#!/usr/bin/env python3
"""
Palantir Foundry to Veza OAA Integration Script

Collects resource definitions, datasets, workspaces, and access control information
from Palantir Foundry and pushes to Veza via the Open Authorization API (OAA).
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from oaaclient.client import OAAClient, OAAClientError
from oaaclient.templates import CustomApplication, OAAPermission

log = logging.getLogger(__name__)


def _setup_logging(log_level: str = "INFO") -> None:
    """Configure file-only logging with hourly rotation to the logs/ folder."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%d%m%Y-%H%M")
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    log_file = os.path.join(log_dir, f"{script_name}_{timestamp}.log")

    handler = TimedRotatingFileHandler(
        log_file,
        when="h",
        interval=1,
        backupCount=24,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.addHandler(handler)


class PalantirFoundryClient:
    """Palantir Foundry API client."""

    def __init__(self, base_url: str, api_token: str):
        """
        Initialize Palantir Foundry client.
        
        Args:
            base_url: Palantir Foundry base URL (e.g., https://westrock.palantirfoundry.com)
            api_token: API token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._test_connection()

    def _test_connection(self) -> None:
        """Verify the API token is accepted by Palantir Foundry."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v2/admin/users",
                headers=self.headers,
                params={"pageSize": 1},
                timeout=10,
            )
            response.raise_for_status()
            log.info("Successfully authenticated with Palantir Foundry at %s", self.base_url)
        except requests.RequestException as e:
            log.error("Failed to connect to Palantir Foundry: %s", e)
            sys.exit(1)

    def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict] = None
    ) -> Dict:
        """Make an API request to Palantir Foundry and return the JSON body."""
        # urljoin requires the base to end with '/' and the path to have no leading '/'
        url = self.base_url.rstrip("/") + "/" + endpoint.lstrip("/")
        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error("API request failed (%s %s): %s", method, endpoint, e)
            raise

    def get_paginated_results(
        self,
        endpoint: str,
        items_key: Optional[str] = None,
        params: Optional[Dict] = None,
    ) -> List[Dict]:
        """Fetch all pages from a paginated Foundry endpoint."""
        results = []
        page_token = None
        params = dict(params or {})

        while True:
            if page_token:
                params["pageToken"] = page_token

            try:
                data = self._make_request("GET", endpoint, params=params)

                # Resolve items key: use caller hint, then auto-detect from response keys
                key = items_key
                if key is None:
                    for candidate in ("datasets", "projects", "workspaces", "resources", "items", "data"):
                        if candidate in data:
                            key = candidate
                            break

                items = data.get(key, []) if key else []
                results.extend(items)

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            except requests.RequestException:
                log.warning(
                    "Pagination stopped at %d items due to request error", len(results)
                )
                break

        return results

    def get_workspaces(self) -> List[Dict]:
        """Fetch all workspaces from Palantir Foundry."""
        log.info("Fetching workspaces...")
        try:
            results = self.get_paginated_results(
                "/api/foundry/workspaces/v1/workspaces", items_key="workspaces"
            )
            log.info("Retrieved %d workspaces", len(results))
            return results
        except requests.RequestException:
            log.error("Failed to fetch workspaces")
            return []

    def get_projects(self) -> List[Dict]:
        """Fetch all projects from Palantir Foundry."""
        log.info("Fetching projects...")
        try:
            results = self.get_paginated_results(
                "/api/foundry/projects/v1/projects", items_key="projects"
            )
            log.info("Retrieved %d projects", len(results))
            return results
        except requests.RequestException:
            log.error("Failed to fetch projects")
            return []

    def get_datasets(self) -> List[Dict]:
        """Fetch all datasets from Palantir Foundry."""
        log.info("Fetching datasets...")
        try:
            results = self.get_paginated_results(
                "/api/foundry/datasets/v1/datasets", items_key="datasets"
            )
            log.info("Retrieved %d datasets", len(results))
            return datasets
        except requests.RequestException:
            log.error("Failed to fetch datasets")
            return []

    def get_resources(self) -> List[Dict]:
        """Fetch all resources from Palantir Foundry."""
        log.info("Fetching resources...")
        try:
            results = self.get_paginated_results(
                "/api/foundry/resources/v1/resources", items_key="resources"
            )
            log.info("Retrieved %d resources", len(results))
            return results
        except requests.RequestException:
            log.error("Failed to fetch resources")
            return []

    def get_access_policies(self, resource_id: str) -> List[Dict]:
        """Fetch access policies for a specific resource."""
        try:
            endpoint = f"/api/foundry/resources/v1/resources/{resource_id}/access-policies"
            data = self._make_request("GET", endpoint)
            return data.get("policies", [])
        except requests.RequestException as e:
            log.debug("No access policies for resource %s: %s", resource_id, e)
            return []


def _apply_resource_properties(resource, data: Dict) -> None:
    """Set common metadata properties on an OAA resource object."""
    if description := data.get("description"):
        resource.add_property("description", description, "str")
    if owner := data.get("owner"):
        resource.add_property("owner", owner, "str")
    if created := data.get("createdAt"):
        resource.add_property("created_at", str(created), "str")
    if rtype := data.get("type"):
        resource.add_property("resource_type", rtype, "str")


def build_oaa_payload(
    foundry_data: Dict,
    provider_name: str = "Palantir Foundry",
    datasource_name: str = "palantir-foundry",
) -> CustomApplication:
    """Build OAA CustomApplication from Palantir Foundry data."""
    app = CustomApplication(
        name=datasource_name,
        application_type=provider_name,
    )

    app.add_custom_permission("viewer", [OAAPermission.DataRead])
    app.add_custom_permission("editor", [OAAPermission.DataRead, OAAPermission.DataWrite])
    app.add_custom_permission(
        "admin",
        [
            OAAPermission.DataRead,
            OAAPermission.DataWrite,
            OAAPermission.MetadataRead,
            OAAPermission.MetadataWrite,
        ],
    )

    resource_lookup: Dict[str, object] = {}
    user_lookup: Dict[str, object] = {}
    group_lookup: Dict[str, object] = {}

    # ── Workspaces ────────────────────────────────────────────────────────────
    log.info("Processing workspaces...")
    for workspace in foundry_data.get("workspaces", []):
        rid = workspace.get("rid") or workspace.get("id")
        if not rid:
            log.warning("Workspace missing rid/id — skipping")
            continue
        name = workspace.get("displayName") or workspace.get("name") or rid
        resource = app.add_resource(resource_id=rid, resource_name=name, resource_type="Workspace")
        resource_lookup[rid] = resource
        _apply_resource_properties(resource, workspace)
        log.debug("Added workspace: %s (%s)", name, rid)

    # ── Projects ──────────────────────────────────────────────────────────────
    log.info("Processing projects...")
    for project in foundry_data.get("projects", []):
        rid = project.get("rid") or project.get("id")
        if not rid:
            log.warning("Project missing rid/id — skipping")
            continue
        name = project.get("displayName") or project.get("name") or rid
        resource = app.add_resource(resource_id=rid, resource_name=name, resource_type="Project")
        resource_lookup[rid] = resource
        _apply_resource_properties(resource, project)
        log.debug("Added project: %s (%s)", name, rid)

    # ── Datasets ──────────────────────────────────────────────────────────────
    log.info("Processing datasets...")
    for dataset in foundry_data.get("datasets", []):
        rid = dataset.get("rid") or dataset.get("id")
        if not rid:
            log.warning("Dataset missing rid/id — skipping")
            continue
        name = dataset.get("displayName") or dataset.get("name") or rid
        resource = app.add_resource(resource_id=rid, resource_name=name, resource_type="Dataset")
        resource_lookup[rid] = resource
        _apply_resource_properties(resource, dataset)
        if row_count := dataset.get("rowCount"):
            resource.add_property("row_count", str(row_count), "str")
        log.debug("Added dataset: %s (%s)", name, rid)

    # ── Generic resources ─────────────────────────────────────────────────────
    log.info("Processing resources...")
    for res in foundry_data.get("resources", []):
        rid = res.get("rid") or res.get("id")
        if not rid:
            log.warning("Resource missing rid/id — skipping")
            continue
        name = res.get("displayName") or res.get("name") or rid
        rtype = res.get("type", "Resource")
        resource = app.add_resource(resource_id=rid, resource_name=name, resource_type=rtype)
        resource_lookup[rid] = resource
        _apply_resource_properties(resource, res)
        log.debug("Added resource: %s (%s)", name, rid)

    # ── Access policies ───────────────────────────────────────────────────────
    log.info("Processing access policies...")
    total_permissions = 0
    for resource_id, policies in foundry_data.get("access_policies", {}).items():
        oaa_resource = resource_lookup.get(resource_id)
        if oaa_resource is None:
            continue
        for policy in policies:
            principal = policy.get("principal", {})
            role = policy.get("role", "viewer").lower()
            p_type = principal.get("type", "").upper()
            p_id = principal.get("userId") or principal.get("groupId") or principal.get("id")
            p_name = principal.get("username") or principal.get("name") or p_id

            if not p_id or not p_name:
                continue

            if p_type == "USER":
                if p_id not in user_lookup:
                    user = app.add_local_user(p_name, unique_id=p_id)
                    if "@" in p_name:
                        user.email = p_name
                    user_lookup[p_id] = user
                user_lookup[p_id].add_permission(role, resources=[oaa_resource])
                total_permissions += 1
            elif p_type in ("GROUP", "TEAM"):
                if p_id not in group_lookup:
                    group_lookup[p_id] = app.add_local_group(p_name, unique_id=p_id)
                group_lookup[p_id].add_permission(role, resources=[oaa_resource])
                total_permissions += 1

    log.info(
        "Payload: %d workspaces, %d projects, %d datasets, %d resources, "
        "%d users, %d groups, %d permissions",
        len(foundry_data.get("workspaces", [])),
        len(foundry_data.get("projects", [])),
        len(foundry_data.get("datasets", [])),
        len(foundry_data.get("resources", [])),
        len(user_lookup),
        len(group_lookup),
        total_permissions,
    )
    return app


def push_to_veza(
    veza_url: str,
    veza_api_key: str,
    provider_name: str,
    datasource_name: str,
    app: CustomApplication,
    save_json: bool = False,
) -> None:
    """Push the OAA payload to Veza. Exits with code 1 on failure."""
    if save_json:
        out_path = f"{datasource_name.lower().replace(' ', '_')}_oaa_payload.json"
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(app.get_payload(), fh, indent=2)
        log.info("OAA payload saved to %s", out_path)

    veza_con = OAAClient(url=veza_url, token=veza_api_key)
    try:
        response = veza_con.push_application(
            provider_name=provider_name,
            data_source_name=datasource_name,
            application_object=app,
            create_provider=True,
        )
        if response and response.get("warnings"):
            for w in response["warnings"]:
                log.warning("Veza warning: %s", w)
        log.info("Successfully pushed to Veza")
    except OAAClientError as e:
        log.error("Veza push failed: %s — %s (HTTP %s)", e.error, e.message, e.status_code)
        if hasattr(e, "details"):
            for detail in e.details:
                log.error("  Detail: %s", detail)
        sys.exit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Palantir Foundry to Veza OAA Integration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Source
    parser.add_argument("--foundry-url", help="Palantir Foundry base URL (overrides FOUNDRY_BASE_URL)")
    parser.add_argument("--foundry-token", help="Palantir Foundry API token (overrides FOUNDRY_API_TOKEN)")
    # Veza
    parser.add_argument("--veza-url", help="Veza tenant URL (overrides VEZA_URL)")
    parser.add_argument("--veza-api-key", help="Veza API key (overrides VEZA_API_KEY)")
    parser.add_argument("--provider-name", default="Palantir Foundry", help="Provider name in Veza")
    parser.add_argument("--datasource-name", default="palantir-foundry", help="Datasource name in Veza")
    # Runtime
    parser.add_argument("--env-file", default=".env", help="Path to .env configuration file")
    parser.add_argument("--dry-run", action="store_true", help="Build payload without pushing to Veza")
    parser.add_argument("--save-json", action="store_true", help="Save OAA payload as JSON for inspection")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def _load_config(args: argparse.Namespace) -> Dict[str, Optional[str]]:
    """Load configuration with precedence: CLI arg → env var → .env file."""
    if os.path.exists(args.env_file):
        load_dotenv(args.env_file)
        log.info("Loaded .env from %s", args.env_file)
    else:
        log.info(".env not found at %s — using environment variables only", args.env_file)
    return {
        "foundry_base_url": args.foundry_url or os.getenv("FOUNDRY_BASE_URL"),
        "foundry_api_token": args.foundry_token or os.getenv("FOUNDRY_API_TOKEN"),
        "veza_url": args.veza_url or os.getenv("VEZA_URL"),
        "veza_api_key": args.veza_api_key or os.getenv("VEZA_API_KEY"),
    }


def main() -> None:
    """Main entry point."""
    args = _parse_args()
    _setup_logging(args.log_level)

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  Palantir Foundry → Veza OAA Integration\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    config = _load_config(args)

    if not config["foundry_base_url"] or not config["foundry_api_token"]:
        log.error("Missing required config: FOUNDRY_BASE_URL and FOUNDRY_API_TOKEN")
        sys.exit(1)

    if not args.dry_run and (not config["veza_url"] or not config["veza_api_key"]):
        log.error("Missing required config: VEZA_URL and VEZA_API_KEY")
        sys.exit(1)

    # Connect and collect data
    log.info("Connecting to Palantir Foundry at %s", config["foundry_base_url"])
    foundry = PalantirFoundryClient(
        base_url=config["foundry_base_url"],
        api_token=config["foundry_api_token"],
    )

    log.info("Collecting data from Palantir Foundry...")
    workspaces = foundry.get_workspaces()
    projects = foundry.get_projects()
    datasets = foundry.get_datasets()
    resources = foundry.get_resources()

    # Fetch access policies for every discovered entity
    access_policies: Dict[str, List] = {}
    for entity in workspaces + projects + datasets + resources:
        rid = entity.get("rid") or entity.get("id")
        if rid:
            policies = foundry.get_access_policies(rid)
            if policies:
                access_policies[rid] = policies

    foundry_data = {
        "workspaces": workspaces,
        "projects": projects,
        "datasets": datasets,
        "resources": resources,
        "access_policies": access_policies,
    }

    log.info("Building OAA payload...")
    app = build_oaa_payload(foundry_data, args.provider_name, args.datasource_name)

    if args.dry_run:
        log.info("[DRY RUN] Payload built — skipping Veza push")
        if args.save_json:
            out = f"{args.datasource_name.lower().replace(' ', '_')}_oaa_payload.json"
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(app.get_payload(), fh, indent=2)
            log.info("Payload saved to %s", out)
        sys.exit(0)

    push_to_veza(
        veza_url=config["veza_url"],
        veza_api_key=config["veza_api_key"],
        provider_name=args.provider_name,
        datasource_name=args.datasource_name,
        app=app,
        save_json=args.save_json,
    )
    log.info("Integration completed successfully")


if __name__ == "__main__":
    main()
