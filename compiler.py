# compiler.py
#
# Wraps the free, open-source `arduino-cli` tool to ACTUALLY compile
# generated sketches server-side. This turns "the AI wrote code that looks
# right" into "the code compiled successfully for this exact chip" — a real
# correctness signal instead of just trusting the model's output.
#
# Requires arduino-cli + the relevant board cores to be installed in the
# deployment image (see the Dockerfile). Everything used here — arduino-cli
# itself, and every board core in board_registry.py — is free and
# open-source; there is no paid dependency.

import subprocess
import tempfile
import os
import shutil

ARDUINO_CLI_BIN = "arduino-cli"  # assumes it's on PATH inside the container


def compile_sketch(sketch_code: str, fqbn: str, core: str) -> tuple[bool, str, str]:
    """Compiles `sketch_code` for the given FQBN using arduino-cli.

    Returns (success, binary_path_or_empty, log_output).
    Never raises — any failure (timeout, missing binary, missing arduino-cli
    binary, compile error) is caught and returned as a readable log message
    instead of crashing the Gradio callback.
    """
    workdir = tempfile.mkdtemp(prefix="zes_sketch_")
    sketch_dir = os.path.join(workdir, "sketch")
    os.makedirs(sketch_dir, exist_ok=True)

    sketch_path = os.path.join(sketch_dir, "sketch.ino")
    with open(sketch_path, "w") as f:
        f.write(sketch_code)

    log_lines = []
    compile_result = None

    try:
        # Only install the core if it's not already present (cores are
        # normally pre-installed at Docker build time).
        list_result = subprocess.run(
            [ARDUINO_CLI_BIN, "core", "list"], capture_output=True, text=True, timeout=30
        )
        if core not in list_result.stdout:
            install_result = subprocess.run(
                [ARDUINO_CLI_BIN, "core", "install", core],
                capture_output=True, text=True, timeout=300
            )
            log_lines.append(f"[core install: {core}]\n{install_result.stdout}\n{install_result.stderr}")
        else:
            log_lines.append(f"[core already installed: {core}]")

        # Free-tier cloud CPUs are slow — give the compiler generous room
        # (5 minutes) rather than risk an uncaught timeout mid-compile.
        # --build-cache-path reuses compiled core object files across
        # requests (and across the Docker build's cache-warming step), so
        # only the FIRST-EVER compile of a given board is genuinely slow.
        os.makedirs("/opt/arduino-cache", exist_ok=True)
        compile_result = subprocess.run(
            [ARDUINO_CLI_BIN, "compile", "--fqbn", fqbn, sketch_dir,
             "--export-binaries", "--build-cache-path", "/opt/arduino-cache"],
            capture_output=True, text=True, timeout=300
        )
        log_lines.append(f"[compile --fqbn {fqbn}]\n{compile_result.stdout}\n{compile_result.stderr}")

    except FileNotFoundError:
        shutil.rmtree(workdir, ignore_errors=True)
        return False, "", "\n".join(log_lines) + "\n[arduino-cli binary not found on PATH — check the Dockerfile install step]"
    except subprocess.TimeoutExpired as e:
        shutil.rmtree(workdir, ignore_errors=True)
        return False, "", "\n".join(log_lines) + f"\n[Timed out after {e.timeout}s — the free-tier CPU may be too slow for this compile, try again or upgrade the instance]"
    except Exception as e:
        shutil.rmtree(workdir, ignore_errors=True)
        return False, "", "\n".join(log_lines) + f"\n[Unexpected error during compile: {type(e).__name__}: {str(e)}]"

    if compile_result is None or compile_result.returncode != 0:
        shutil.rmtree(workdir, ignore_errors=True)
        return False, "", "\n".join(log_lines)

    # arduino-cli exports compiled binaries into a 'build' subfolder
    build_dir = os.path.join(sketch_dir, "build")
    binary_path = None
    if os.path.isdir(build_dir):
        for root, _, files in os.walk(build_dir):
            for fname in files:
                if fname.endswith((".bin", ".hex", ".uf2")):
                    binary_path = os.path.join(root, fname)
                    break
            if binary_path:
                break

    if not binary_path:
        shutil.rmtree(workdir, ignore_errors=True)
        return False, "", "\n".join(log_lines) + "\n[No binary artifact found after compile]"

    return True, binary_path, "\n".join(log_lines)
