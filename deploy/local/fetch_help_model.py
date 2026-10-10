"""Build-time download of the pinned public help model (application help only; never sees tenant data).

Pins: onnx-community/Qwen3-0.6B-ONNX @ 1e0a4a19 (CPU int4 export), base Qwen/Qwen3-0.6B @ c1899de2 (Apache-2.0).
Writes flat files + provenance.json, exactly what app/services/model_gateway/onnx_runtime.py allow-lists.
"""
import json
from pathlib import Path
import shutil
import sys

from huggingface_hub import hf_hub_download

EXPORT_REPO, EXPORT_REVISION = "onnx-community/Qwen3-0.6B-ONNX", "1e0a4a196ecabdf9a879664110574563d3f372d3"
BASE_REPO, BASE_REVISION = "Qwen/Qwen3-0.6B", "c1899de289a04d12100db370d81485cdf75e47ca"
SUBDIR = "onnxruntime/cpu_and_mobile/cpu-int4-kld-block-128"
FILES = ["genai_config.json", "model.onnx", "tokenizer.json", "tokenizer_config.json", "config.json", "chat_template.jinja"]

target = Path(sys.argv[1])
target.mkdir(parents=True, exist_ok=True)
for name in FILES:
    shutil.copyfile(hf_hub_download(EXPORT_REPO, f"{SUBDIR}/{name}", revision=EXPORT_REVISION), target / name)
shutil.copyfile(hf_hub_download(BASE_REPO, "LICENSE", revision=BASE_REVISION), target / "LICENSE")
(target / "provenance.json").write_text(json.dumps({"repo_id": EXPORT_REPO, "revision": EXPORT_REVISION, "subdirectory": SUBDIR,
    "base_model": BASE_REPO, "base_revision": BASE_REVISION, "license": "apache-2.0",
    "note": "Community ONNX export of the official base; weights licensed by the base model."}, indent=2))
print("help model ready:", sorted(p.name for p in target.iterdir()))
