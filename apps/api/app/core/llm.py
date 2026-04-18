from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


class LLMError(RuntimeError):
    pass


class LLMProvider:
    """Unified LLM interface.

    Primary path: OpenAI Codex CLI (`codex exec`) — uses user's authenticated Codex session.
    Backup path: Anthropic SDK (if ANTHROPIC_API_KEY + credits).
    """

    def __init__(
        self, model: str | None = None, backup: str | None = None, temperature: float = 0.4
    ):
        self.model = model or settings.default_model
        self.backup = backup or settings.backup_model
        self.temperature = temperature

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        retry=retry_if_not_exception_type(LLMError),
        reraise=True,
    )
    def generate(self, system: str, user: str, *, json_mode: bool = False) -> str:
        try:
            return self._call(self.model, system, user, json_mode)
        except LLMError:
            raise
        except Exception as e:
            log.warning("llm.fallback", model=self.model, backup=self.backup, error=str(e))
            return self._call(self.backup, system, user, json_mode)

    def generate_json(self, system: str, user: str) -> dict[str, Any]:
        raw = self.generate(system, user, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                return json.loads(raw[start : end + 1])
            raise LLMError(f"invalid JSON from LLM: {raw[:300]}")

    def _call(self, model: str, system: str, user: str, json_mode: bool) -> str:
        if model.startswith("claude"):
            return self._anthropic(model, system, user, json_mode)
        if not shutil.which("codex"):
            raise LLMError("codex CLI not installed – cannot use codex-based model")
        return self._codex(model, system, user, json_mode)

    def _codex(self, model: str, system: str, user: str, json_mode: bool) -> str:
        """Invoke `codex exec` non-interactively and capture last message."""
        prompt = f"<system>\n{system}\n</system>\n\n<task>\n{user}\n</task>"
        if json_mode:
            prompt += (
                "\n\n중요: 응답은 반드시 유효한 JSON 객체 하나만. "
                "코드펜스·서두·결론 금지. JSON 객체만 출력."
            )

        with tempfile.NamedTemporaryFile(
            "w+", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            out_path = Path(tmp.name)

        cmd = [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--color",
            "never",
            "--ephemeral",
            "--output-last-message",
            str(out_path),
        ]
        if model and not model.startswith("default") and model != "codex":
            cmd += ["--model", model]
        cmd.append(prompt)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
            if proc.returncode != 0:
                raise LLMError(
                    f"codex exec failed rc={proc.returncode}: "
                    f"{(proc.stderr or proc.stdout)[-400:]}"
                )
            text = ""
            if out_path.exists():
                text = out_path.read_text(encoding="utf-8").strip()
            if not text:
                text = _extract_last_codex_reply(proc.stdout)
            if not text:
                raise LLMError("empty response from codex")
            return text.strip()
        except subprocess.TimeoutExpired:
            raise LLMError("codex exec timeout")
        finally:
            try:
                out_path.unlink()
            except OSError:
                pass

    def _anthropic(self, model: str, system: str, user: str, json_mode: bool) -> str:
        import anthropic

        if not settings.anthropic_api_key:
            raise LLMError("ANTHROPIC_API_KEY missing")
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        prompt_user = user
        if json_mode:
            prompt_user += "\n\n출력은 반드시 JSON 객체만."
        msg = client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": prompt_user}],
        )
        parts = [b.text for b in msg.content if hasattr(b, "text")]
        return "".join(parts)


def _extract_last_codex_reply(stdout: str) -> str:
    marker = "\ncodex\n"
    idx = stdout.rfind(marker)
    if idx < 0:
        return ""
    tail = stdout[idx + len(marker) :]
    stop = tail.find("\ntokens used")
    return tail[:stop].strip() if stop >= 0 else tail.strip()


def llm(temperature: float = 0.4) -> LLMProvider:
    return LLMProvider(temperature=temperature)
