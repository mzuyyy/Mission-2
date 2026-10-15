import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest


@pytest.fixture(scope="module")
def server_url() -> Iterator[str]:
    """Run a fresh app process so Python module caching cannot mask source changes."""
    artifacts = Path("eval/runs/browser")
    artifacts.mkdir(parents=True, exist_ok=True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = {**os.environ, "LLM_API_BASE": "", "LLM_API_KEY": "", "LLM_MODEL": ""}
    with (artifacts / "server.log").open("w", encoding="utf-8") as output:
        process = subprocess.Popen(  # noqa: S603 -- fixed Streamlit process, no shell or untrusted flags.
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.address=127.0.0.1",
                f"--server.port={port}",
                "--server.headless=true",
                "--server.fileWatcherType=none",
            ],
            env=env,
            stdout=output,
            stderr=output,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        try:
            url = f"http://127.0.0.1:{port}"
            deadline = time.monotonic() + 30
            with httpx.Client(timeout=1, trust_env=False) as client:
                while True:
                    try:
                        if client.get(url + "/_stcore/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        if time.monotonic() >= deadline or process.poll() is not None:
                            raise
                    if time.monotonic() >= deadline:
                        pytest.fail("Streamlit server did not become healthy")
                    time.sleep(0.1)
            yield url
        finally:
            process.terminate()
            process.wait(timeout=10)
