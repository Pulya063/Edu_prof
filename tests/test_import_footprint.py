import os
import subprocess
import sys


def test_api_start_does_not_load_numpy_or_pandas():
    # They add ~260 MB per process and are needed only while a market snapshot is being built.
    code = "import sys, app.main; print([name for name in ('numpy', 'pandas') if name in sys.modules])"
    env = {**os.environ, "DATABASE_URL": "sqlite:///:memory:"}
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=120)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "[]"
