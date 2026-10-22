"""End-to-End integration tests for Forgejo Actions / runner workflow files.

This test file executes the repository's Forgejo workflows using `act` / `forgejo-runner`
and verifies that:
1. `.forgejo/workflows/pr-staging.yaml` runs (linting, building and deploying dev
   containers via compose.dev.yaml, and running integration tests).
2. `.forgejo/workflows/push-production.yaml` runs (building and deploying prod
   containers via compose.prod.yaml).
3. The actual Docker containers are spun up and in running state on the local Docker engine.
4. Resources are safely cleaned up after test execution.

Execution modes supported:
- Native `act` CLI (e.g. installed via `brew install act`)
- Native `forgejo-runner` CLI (e.g. `forgejo-runner exec`)
- Dockerized `act` runner (`ghcr.io/nektos/act:latest`), allowing testing with
  only Mac + Docker Engine installed without requiring act binary.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
from typing import Generator
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".forgejo" / "workflows"
PR_STAGING_WORKFLOW = WORKFLOWS_DIR / "pr-staging.yaml"
PUSH_PRODUCTION_WORKFLOW = WORKFLOWS_DIR / "push-production.yaml"

DEV_CONTAINERS = [
    "school-db-dev",
    "school-redis-dev",
    "school-fastapi-dev",
    "school-worker-dev",
]

PROD_CONTAINERS = [
    "school-db-prod",
    "school-redis-prod",
    "school-fastapi-prod",
    "school-worker-prod",
]


@dataclass
class WorkflowResult:
    """Result of running a workflow command."""

    returncode: int
    stdout: str
    stderr: str
    command: list[str]

    @property
    def failed_step_logs(self) -> str:
        """Extract only the lines output by the specific workflow step that failed."""
        lines = self.stdout.splitlines()
        failure_indices = [
            i for i, line in enumerate(lines) if "Failure -" in line or "exitcode" in line
        ]
        if not failure_indices:
            return ""

        first_failure = failure_indices[0]
        # Look backwards to find where this step started
        start_idx = max(0, first_failure - 80)
        for i in range(first_failure, -1, -1):
            if "⭐ Run " in lines[i] or "Run " in lines[i]:
                start_idx = i
                break

        end_idx = min(len(lines), failure_indices[-1] + 3)
        relevant_lines = lines[start_idx:end_idx]

        cleaned: list[str] = []
        for line in relevant_lines:
            if "]" in line and line.startswith("["):
                line = line.split("]", 1)[1]
            line = line.strip()
            if line.startswith("|"):
                line = line[1:].strip()
            cleaned.append(line)

        return "\n".join(cleaned)

    @property
    def failure_summary(self) -> str:
        """Extract key error lines from stdout and stderr for concise display."""
        step_logs = self.failed_step_logs
        if step_logs:
            return step_logs
        failed_lines: list[str] = []
        for line in self.stdout.splitlines():
            if any(term in line.lower() for term in ("failure -", "failed", "exitcode", "error", "traceback", "exception", "assert")):
                failed_lines.append(line)
        if self.stderr.strip():
            failed_lines.append(f"STDERR:\n{self.stderr.strip()}")
        return "\n".join(failed_lines) if failed_lines else "No specific failure lines extracted."

    @property
    def combined_output(self) -> str:
        return (
            f"\n--- FAILED STEP LOGS ---\n{self.failure_summary}\n\n"
            f"--- FULL STDOUT ---\n{self.stdout}\n\n"
            f"--- FULL STDERR ---\n{self.stderr}"
        )


def find_docker_socket() -> Path:
    """Locate the active Docker socket on macOS or Linux."""
    docker_host = os.environ.get("DOCKER_HOST", "")
    if docker_host.startswith("unix://"):
        host_path = Path(docker_host.replace("unix://", ""))
        if host_path.exists():
            return host_path

    candidates = [
        Path("/var/run/docker.sock"),
        Path.home() / ".docker" / "run" / "docker.sock",
        Path.home() / ".colima" / "default" / "docker.sock",
        Path.home() / ".orbstack" / "run" / "docker.sock",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return Path("/var/run/docker.sock")


def check_docker_engine() -> bool:
    """Verify that Docker Engine is running and responsive."""
    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return res.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_docker_container_state(container_name: str) -> str | None:
    """Query docker for container state (e.g. 'running', 'exited', or None if not found)."""
    try:
        res = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", container_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip()
        return None
    except Exception:
        return None


def run_docker_compose_down(compose_file: str) -> None:
    """Bring down docker compose stack and remove volumes."""
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            compose_file,
            "down",
            "-v",
            "--remove-orphans",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class WorkflowRunner:
    """Abstraction for executing Forgejo / GitHub Actions workflows locally."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.docker_sock = find_docker_socket()

        # Determine execution backend
        explicit_bin = os.environ.get("FORGEJO_RUNNER_BIN") or os.environ.get("ACT_BIN")
        if explicit_bin:
            self.backend = explicit_bin
        elif shutil.which("act"):
            self.backend = "act"
        elif shutil.which("forgejo-runner"):
            self.backend = "forgejo-runner"
        elif shutil.which("docker"):
            self.backend = "docker"
        else:
            self.backend = "none"

        # Platform images configuration
        # catthehacker/ubuntu:act-latest is the standard full act runner image
        # with Docker CLI, compose, python, node, and git preinstalled.
        self.ubuntu_image = os.environ.get(
            "ACT_IMAGE_UBUNTU", "catthehacker/ubuntu:act-latest"
        )

        # For 'host' target:
        # If running via native act/forgejo-runner on macOS, '-self-hosted' runs directly on host Mac,
        # which calls host docker compose.
        # If running via docker container, 'host' should map to catthehacker/ubuntu:act-latest
        # which uses the mounted docker daemon socket.
        if "ACT_IMAGE_HOST" in os.environ:
            self.host_target = os.environ["ACT_IMAGE_HOST"]
        elif self.backend in ("act", "forgejo-runner"):
            self.host_target = "-self-hosted"
        else:
            self.host_target = self.ubuntu_image

        self.act_docker_image = os.environ.get(
            "ACT_DOCKER_IMAGE", "ghcr.io/nektos/act:latest"
        )
        self.verbose = os.environ.get("ACT_VERBOSE", "0") == "1"

    def _create_mock_event_payload(self, event: str) -> Path:
        """Create a temporary GitHub/Forgejo webhook event payload to satisfy branch filters."""
        event_file = self.repo_root / f".mock_event_{event}.json"
        if event == "pull_request":
            payload = {
                "action": "opened",
                "pull_request": {
                    "number": 1,
                    "title": "Local Integration Test PR",
                    "base": {
                        "ref": "main",
                        "sha": "0000000000000000000000000000000000000000",
                    },
                    "head": {
                        "ref": "integration-test",
                        "sha": "0000000000000000000000000000000000000000",
                    },
                },
            }
        else:
            payload = {
                "ref": "refs/heads/main",
                "before": "0000000000000000000000000000000000000000",
                "after": "0000000000000000000000000000000000000000",
            }
        event_file.write_text(json.dumps(payload, indent=2))
        return event_file

    def run(
        self,
        workflow_file: Path,
        event: str = "push",
        job: str | None = None,
        extra_flags: list[str] | None = None,
        timeout: int = 900,
    ) -> WorkflowResult:
        """Execute a workflow file and capture results."""
        if self.backend == "none":
            pytest.fail("Neither 'act', 'forgejo-runner', nor 'docker' CLI is available in PATH.")

        temp_workflow_file: Path | None = None
        target_workflow = workflow_file

        # 'act' strictly expects action references formatted as '{org}/{repo}[/path]@ref'.
        # Full URLs like 'https://github.com/...' are supported in Forgejo but cause act syntax errors.
        # If running via act/docker, create a temporary normalized workflow copy if needed.
        if self.backend in ("act", "docker"):
            content = workflow_file.read_text(encoding="utf-8")
            sanitized = re.sub(r"(uses:\s*)https?://github\.com/", r"\1", content)
            if sanitized != content:
                temp_workflow_file = workflow_file.parent / f".tmp_{workflow_file.name}"
                temp_workflow_file.write_text(sanitized, encoding="utf-8")
                target_workflow = temp_workflow_file

        event_payload_file = self._create_mock_event_payload(event)
        rel_workflow = target_workflow.relative_to(self.repo_root)
        rel_event = event_payload_file.relative_to(self.repo_root)

        cmd: list[str] = []

        if self.backend == "docker":
            # Running act inside a Docker container
            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{self.docker_sock}:/var/run/docker.sock",
                "-v",
                f"{self.repo_root}:{self.repo_root}",
                "-w",
                str(self.repo_root),
                self.act_docker_image,
                event,
                "-W",
                str(rel_workflow),
                "-e",
                str(rel_event),
                "--defaultbranch",
                "main",
                "-P",
                f"ubuntu-latest={self.ubuntu_image}",
                "-P",
                f"host={self.host_target}",
                "--container-daemon-socket",
                "/var/run/docker.sock",
            ]
        elif self.backend == "forgejo-runner":
            # Forgejo Runner CLI native
            cmd = [
                "forgejo-runner",
                "exec",
                "-W",
                str(rel_workflow),
                "-e",
                str(rel_event),
                "-P",
                f"ubuntu-latest={self.ubuntu_image}",
                "-P",
                f"host={self.host_target}",
            ]
        else:
            # act CLI native
            cmd = [
                "act",
                event,
                "-W",
                str(rel_workflow),
                "-e",
                str(rel_event),
                "--defaultbranch",
                "main",
                "-P",
                f"ubuntu-latest={self.ubuntu_image}",
                "-P",
                f"host={self.host_target}",
                "--container-daemon-socket",
                str(self.docker_sock),
            ]

        # Add architecture override if on ARM Mac and configured
        arch = os.environ.get("ACT_CONTAINER_ARCH")
        if not arch and platform.machine() in ("arm64", "aarch64"):
            arch = "linux/arm64"
        if arch and self.backend != "forgejo-runner":
            cmd.extend(["--container-architecture", arch])

        # Optional GitHub Token to bypass unauthenticated API rate limits
        gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if gh_token:
            cmd.extend(["-s", f"GITHUB_TOKEN={gh_token}"])

        # Specific job targeting
        if job:
            cmd.extend(["-j", job])

        # Optional verbose logging
        if self.verbose:
            cmd.append("-v")

        # Custom flags
        if extra_flags:
            cmd.extend(extra_flags)

        try:
            res = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return WorkflowResult(
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                command=cmd,
            )
        finally:
            if event_payload_file.exists():
                event_payload_file.unlink(missing_ok=True)
            if temp_workflow_file and temp_workflow_file.exists():
                temp_workflow_file.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def docker_engine():
    """Ensure Docker Engine is running before executing any workflow test."""
    # Prevent recursive execution: when 'uv run pytest' is invoked inside an act/CI container,
    # skip workflow-testing-workflows to avoid attempting to spawn nested runners.
    if (
        os.environ.get("ACT") == "true"
        or os.environ.get("GITHUB_ACTIONS") == "true"
        or os.environ.get("CI") == "true"
    ):
        pytest.skip(
            "Running inside an Action/Runner container: skipping workflow execution tests."
        )

    if not check_docker_engine():
        pytest.skip(
            "Docker Engine is not running or not responsive. "
            "Please start Docker Desktop/Colima/OrbStack before running workflow integration tests."
        )
    return True


@pytest.fixture
def workflow_runner(docker_engine) -> WorkflowRunner:
    """Fixture providing initialized WorkflowRunner instance."""
    return WorkflowRunner(REPO_ROOT)


@pytest.fixture
def cleanup_dev_stack() -> Generator[None, None, None]:
    """Ensure dev containers are torn down before and after tests."""
    run_docker_compose_down("compose.dev.yaml")
    try:
        yield
    finally:
        if os.environ.get("KEEP_CONTAINERS", "0") != "1":
            run_docker_compose_down("compose.dev.yaml")


@pytest.fixture
def cleanup_prod_stack() -> Generator[None, None, None]:
    """Ensure prod containers are torn down before and after tests."""
    run_docker_compose_down("compose.prod.yaml")
    try:
        yield
    finally:
        if os.environ.get("KEEP_CONTAINERS", "0") != "1":
            run_docker_compose_down("compose.prod.yaml")


def assert_workflow_success(result: WorkflowResult, workflow_name: str) -> None:
    """Assert workflow success, saving the full log and presenting the exact failed step error."""
    if result.returncode != 0:
        safe_name = workflow_name.replace("/", "_")
        log_file = REPO_ROOT / f"workflow_failure_{safe_name}.log"
        log_file.write_text(
            f"COMMAND:\n{' '.join(result.command)}\n\n"
            f"{result.combined_output}\n",
            encoding="utf-8",
        )
        step_logs = result.failed_step_logs or result.failure_summary
        import sys
        sys.stderr.write(
            f"\n{'='*20} {workflow_name} FAILED STEP LOGS {'='*20}\n"
            f"{step_logs}\n"
            f"{'='*70}\n"
        )
        pytest.fail(
            f"\nWorkflow '{workflow_name}' failed with exit code {result.returncode}.\n\n"
            f"--- FAILED STEP LOGS ---\n{step_logs}\n\n"
            f"(Full log saved to {log_file.name})"
        )


@pytest.mark.workflow
class TestForgejoWorkflows:
    """Integration test suite executing both Forgejo YAML workflow files."""

    @pytest.fixture(autouse=True)
    def skip_if_in_runner_container(self) -> None:
        """Prevent recursive workflow execution when tests run inside act or CI container."""
        if (
            os.environ.get("ACT") == "true"
            or os.environ.get("GITHUB_ACTIONS") == "true"
            or os.environ.get("CI") == "true"
        ):
            pytest.skip("Skipping workflow runner test inside CI/act container.")

    def test_pr_staging_workflow_e2e(
        self,
        workflow_runner: WorkflowRunner,
        cleanup_dev_stack: None
    ) -> None:
        """Test full execution of .forgejo/workflows/pr-staging.yaml.

        Workflow steps:
        1. job 'test' (runs ruff, pyrefly, sqlfluff lint on ubuntu-latest).
        2. job 'deploy-dev' (spins up Docker Compose dev stack on host).
        3. job 'integration_test' (runs pytest suite on ubuntu-latest).
        4. Verifies all dev containers (db, redis, api, worker) are running on Docker engine.
        """
        assert PR_STAGING_WORKFLOW.exists(), f"Workflow file not found: {PR_STAGING_WORKFLOW}"

        result = workflow_runner.run(
            workflow_file=PR_STAGING_WORKFLOW,
            event="pull_request",
        )

        assert_workflow_success(result, "pr-staging.yaml")

        # Verify that dev containers were actually spun up and are running on Docker engine
        for container in DEV_CONTAINERS:
            state = get_docker_container_state(container)
            assert state == "running", (
                f"Expected container '{container}' to be running, but state is '{state}'.\n"
                f"{result.combined_output}"
            )

    def test_push_production_workflow_e2e(
        self,
        workflow_runner: WorkflowRunner,
        cleanup_prod_stack: None,
    ) -> None:
        """Test full execution of .forgejo/workflows/push-production.yaml.

        Workflow steps:
        1. job 'deploy-prod' (spins up Docker Compose prod stack on host).
        2. Verifies all prod containers (db, redis, api, worker) are running on Docker engine.
        """
        assert PUSH_PRODUCTION_WORKFLOW.exists(), f"Workflow file not found: {PUSH_PRODUCTION_WORKFLOW}"

        result = workflow_runner.run(
            workflow_file=PUSH_PRODUCTION_WORKFLOW,
            event="push",
        )

        assert_workflow_success(result, "push-production.yaml")

        # Verify that prod containers were actually spun up and are running on Docker engine
        for container in PROD_CONTAINERS:
            state = get_docker_container_state(container)
            assert state == "running", (
                f"Expected container '{container}' to be running, but state is '{state}'.\n"
                f"{result.combined_output}"
            )

    @pytest.mark.parametrize(
        "job_name",
        ["test", "deploy-dev"],
    )
    def test_pr_staging_individual_jobs(
        self,
        workflow_runner: WorkflowRunner,
        cleanup_dev_stack: None,
        job_name: str,
    ) -> None:
        """Test running individual jobs within pr-staging.yaml for faster debugging."""
        result = workflow_runner.run(
            workflow_file=PR_STAGING_WORKFLOW,
            event="pull_request",
            job=job_name,
        )

        assert_workflow_success(result, f"pr-staging.yaml [{job_name}]")

        if job_name == "deploy-dev":
            for container in DEV_CONTAINERS:
                state = get_docker_container_state(container)
                assert state == "running", (
                    f"Container '{container}' was expected to be running after deploy-dev job."
                )
