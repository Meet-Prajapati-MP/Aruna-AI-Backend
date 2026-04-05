"""
app/integrations/e2b_client.py
────────────────────────────────
FIX B3: stdout extraction was completely wrong.

Original bug:
  stdout = "\n".join(r.text for r in (execution.results or []) if hasattr(r, "text"))
  → execution.results contains rich display outputs (DataFrames, plots, etc.)
  → print() output goes to execution.logs.stdout — this was NEVER captured.
  → Every code execution returned empty output even when code ran correctly.

Fix:
  stdout = "".join(execution.logs.stdout)   ← actual print() output
  stderr = "".join(execution.logs.stderr)   ← error output
  execution.results                         ← display data (kept separately)
"""

import asyncio
from typing import Optional

from e2b_code_interpreter import CodeInterpreter

from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.sanitizer import sanitize_code, InputSanitizationError

logger = get_logger(__name__)

_EXEC_TIMEOUT_SECONDS = 30


class E2BExecutionResult:
    def __init__(
        self,
        stdout: str,
        stderr: str,
        error: Optional[str],
        success: bool,
        display_output: Optional[str] = None,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.error = error
        self.success = success
        self.display_output = display_output

    def to_dict(self) -> dict:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "success": self.success,
            "display_output": self.display_output,
        }


async def execute_code(code: str, language: str = "python") -> E2BExecutionResult:
    """
    Execute code inside an E2B sandbox.

    Returns E2BExecutionResult with:
      - stdout: output from print() statements  ← FIX B3
      - stderr: standard error stream           ← FIX B3
      - display_output: rich outputs (DataFrames, plots as text)
      - error: exception message if execution failed
      - success: True if no exception was raised
    """
    try:
        code = sanitize_code(code)
    except (InputSanitizationError, ValueError) as exc:
        return E2BExecutionResult(stdout="", stderr="", error=str(exc), success=False)

    if language.lower() != "python":
        return E2BExecutionResult(
            stdout="",
            stderr="",
            error=f"Language '{language}' is not supported. Only Python is supported.",
            success=False,
        )

    logger.info("e2b_execution_start", code_length=len(code))

    def _run_in_sandbox() -> E2BExecutionResult:
        settings = get_settings()
        sandbox = None
        try:
            sandbox = CodeInterpreter(api_key=settings.E2B_API_KEY)
            execution = sandbox.notebook.exec_cell(
                code,
                timeout=_EXEC_TIMEOUT_SECONDS,
            )

            # ── FIX B3: Read stdout/stderr from execution.logs ────────────────
            # execution.logs.stdout → list of strings from print()
            # execution.logs.stderr → list of strings from stderr
            stdout = "".join(execution.logs.stdout) if execution.logs and execution.logs.stdout else ""
            stderr = "".join(execution.logs.stderr) if execution.logs and execution.logs.stderr else ""

            # execution.results → rich display outputs (e.g. DataFrame reprs, plots)
            display_parts = []
            for result in (execution.results or []):
                if hasattr(result, "text") and result.text:
                    display_parts.append(result.text)
            display_output = "\n".join(display_parts) if display_parts else None

            # execution.error → exception details if execution threw
            error_msg: Optional[str] = None
            if execution.error:
                error_msg = f"{execution.error.name}: {execution.error.value}"
                if execution.error.traceback:
                    error_msg += f"\n{execution.error.traceback}"

            success = execution.error is None

            logger.info(
                "e2b_execution_complete",
                success=success,
                stdout_len=len(stdout),
                stderr_len=len(stderr),
            )
            return E2BExecutionResult(
                stdout=stdout,
                stderr=stderr,
                error=error_msg,
                success=success,
                display_output=display_output,
            )

        except Exception as exc:
            logger.error("e2b_execution_error", error=str(exc))
            return E2BExecutionResult(
                stdout="", stderr="", error="Sandbox execution failed.", success=False
            )
        finally:
            if sandbox:
                try:
                    sandbox.close()
                except Exception:
                    pass

    return await asyncio.get_event_loop().run_in_executor(None, _run_in_sandbox)
