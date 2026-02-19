import json
import subprocess
import tempfile
from pathlib import Path

MINIZINC_BIN = Path("/Applications/MiniZincIDE.app/Contents/Resources/minizinc")


def _extract_last_json(stdout: str) -> dict:
    s = stdout.strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    last_ok = None
    start = 0
    while True:
        i = s.find("{", start)
        if i == -1:
            break
        for j in range(len(s), i, -1):
            chunk = s[i:j].strip()
            if not chunk.endswith("}"):
                continue
            try:
                obj = json.loads(chunk)
                last_ok = obj
                start = i + 1
                break
            except json.JSONDecodeError:
                continue
        else:
            start = i + 1

    if last_ok is None:
        raise RuntimeError("Impossible de parser la sortie JSON MiniZinc.")
    return last_ok


def solve_allocation_minizinc(data, model_path="models/allocation.mzn",
                             solver_id="org.gecode.gecode", time_limit_ms=8000):
    model_path = Path(model_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        data_file = tmpdir / "data.json"
        data_file.write_text(json.dumps(data), encoding="utf-8")

        cmd = [
            str(MINIZINC_BIN),
            "--solver", solver_id,
            "--output-mode", "json",
            "--time-limit", str(time_limit_ms),
            str(model_path),
            str(data_file),
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True)

        if proc.returncode != 0:
            raise RuntimeError(
                "MiniZinc a échoué.\n"
                f"STDOUT:\n{proc.stdout}\n"
                f"STDERR:\n{proc.stderr}\n"
                f"CMD:\n{' '.join(cmd)}"
            )

        out = _extract_last_json(proc.stdout)

        if "assign" not in out:
            raise RuntimeError(f"Sortie JSON MiniZinc inattendue: {out}")

        return out
