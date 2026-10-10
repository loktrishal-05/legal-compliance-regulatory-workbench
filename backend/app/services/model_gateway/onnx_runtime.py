"""Allow-listed local CPU GenAI adapter. A bounded subprocess enforces a real wall deadline."""
import json
from pathlib import Path
import subprocess
import sys
from threading import BoundedSemaphore
from time import monotonic

from app.services.model_gateway.errors import ModelConfigurationError, ModelRuntimeError, ModelTimeoutError, ModelUnavailableError
from app.services.model_gateway.types import GenerationResult, GenerationUsage, GenerationTimings, ModelInfo, RuntimeHealth

MODEL_ID = "Qwen/Qwen3-0.6B"
EXPORT_REPO = "onnx-community/Qwen3-0.6B-ONNX"
EXPORT_REVISION = "1e0a4a196ecabdf9a879664110574563d3f372d3"
EXPORT_SUBDIRECTORY = "onnxruntime/cpu_and_mobile/cpu-int4-kld-block-128"
_SLOT = BoundedSemaphore(1)


class OnnxRuntime:
    name = "onnx"

    def __init__(self, settings):
        self.settings = settings

    def _files(self):
        root = Path(self.settings.model_onnx_path).resolve()
        allowed = Path(self.settings.model_onnx_allowed_root).resolve()
        if root != allowed:
            raise ModelConfigurationError("ONNX path is outside the configured local allowlist")
        required = ("genai_config.json", "model.onnx", "tokenizer.json", "tokenizer_config.json", "provenance.json")
        if not all((root/name).is_file() and not (root/name).is_symlink() for name in required):
            raise ModelUnavailableError("Pinned ONNX model files are not available")
        try:
            manifest = json.loads((root/"provenance.json").read_text())
            config = json.loads((root/"genai_config.json").read_text())
        except (OSError, ValueError):
            raise ModelUnavailableError("ONNX model metadata is invalid") from None
        if (manifest.get("repo_id"), manifest.get("revision"), manifest.get("base_model"), manifest.get("license")) != (
                EXPORT_REPO, EXPORT_REVISION, MODEL_ID, "apache-2.0"):
            raise ModelConfigurationError("ONNX model provenance is not allow-listed")
        if config.get("model", {}).get("decoder", {}).get("filename") != "model.onnx":
            raise ModelConfigurationError("ONNX graph filename is not allow-listed")
        if config.get("model", {}).get("decoder", {}).get("session_options", {}).get("provider_options"):
            raise ModelConfigurationError("Help runtime requires the CPU export")
        return root

    def chat(self, *, messages, model, temperature, seed, max_output_tokens, context_window,
             stop, json_schema, tools, think, timeout_seconds):
        if model != MODEL_ID or temperature != 0 or tools or think:
            raise ModelConfigurationError("ONNX help profile permits only its local model, greedy output, no tools or reasoning")
        if not 1 <= (max_output_tokens or 128) <= 128 or not 1 <= timeout_seconds <= 30:
            raise ModelConfigurationError("ONNX output or deadline exceeds the bounded help profile")
        if context_window is not None and not 256 <= context_window <= 2048:
            raise ModelConfigurationError("ONNX context exceeds the help profile")
        if not messages or any(m.role not in {"system", "user", "assistant"} for m in messages):
            raise ModelConfigurationError("Invalid ONNX help messages")
        prompt = "".join(f"<|im_start|>{m.role}\n{m.content}<|im_end|>\n" for m in messages)
        prompt += "<|im_start|>assistant\n<think>\n\n</think>\n\n"
        if len(prompt) > 16000:
            raise ModelConfigurationError("ONNX help prompt exceeds input bounds")
        root = self._files()
        if not _SLOT.acquire(blocking=False):
            raise ModelUnavailableError("ONNX help runtime is busy")
        started = monotonic()
        try:
            payload = {"prompt": prompt, "max_tokens": max_output_tokens or 128,
                "context_window": context_window or 2048, "timeout_seconds": timeout_seconds}
            try:
                done = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).with_name("onnx_worker.py")), str(root)],
                    input=json.dumps(payload).encode(), capture_output=True, timeout=timeout_seconds,
                    env={"LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8", "OMP_NUM_THREADS": "2", "HF_HUB_OFFLINE": "1"})
            except subprocess.TimeoutExpired:
                raise ModelTimeoutError("ONNX help deadline exceeded") from None
            except OSError:
                raise ModelUnavailableError("ONNX help process is unavailable") from None
            if done.returncode or len(done.stdout) > 64000:
                raise ModelUnavailableError("ONNX help generation is unavailable")
            try:
                value = json.loads(done.stdout)
                text = value["text"]
                if not isinstance(text, str) or len(text) > 16000:
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                raise ModelRuntimeError("ONNX help response is invalid") from None
            return GenerationResult(text=text, finish_reason="length" if value.get("truncated") else "stop",
                truncated=bool(value.get("truncated")), model=model, runtime=self.name,
                usage=GenerationUsage(prompt_tokens=value.get("prompt_tokens"), completion_tokens=value.get("completion_tokens")),
                timings=GenerationTimings(total_ms=(monotonic()-started)*1000), warnings=[])
        finally:
            _SLOT.release()

    def health(self):
        try:
            self._files()
            present = True
        except (ModelConfigurationError, ModelUnavailableError):
            present = False
        return RuntimeHealth(runtime=self.name, reachable=present, configured_model=MODEL_ID,
            configured_model_present=present, available_models=[MODEL_ID] if present else [],
            detail="Pinned local CPU files present; generation is checked separately" if present else "Pinned local help model unavailable")

    def list_models(self):
        return [ModelInfo(name=MODEL_ID, digest=EXPORT_REVISION, parameter_size="0.6B", quantization="int4")] if self.health().configured_model_present else []
