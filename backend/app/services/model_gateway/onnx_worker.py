"""Secret-free child for public application-help text only; never imports application/tenant services."""
import json
from pathlib import Path
import sys
from time import monotonic


def generate(root, payload):
    import onnxruntime_genai as oga
    model = oga.Model(str(root))
    tokenizer = oga.Tokenizer(model)
    tokens = tokenizer.encode(payload["prompt"])
    limit = min(int(payload["max_tokens"]), 128)
    if len(tokens) + limit > min(int(payload["context_window"]), 2048):
        raise ValueError("help context limit")
    params = oga.GeneratorParams(model)
    params.set_search_options(do_sample=False, max_length=len(tokens)+limit, num_beams=1)
    generator = oga.Generator(model, params)
    generator.append_tokens(tokens)
    stream = tokenizer.create_stream()
    output, count = [], 0
    started = monotonic()
    while not generator.is_done() and count < limit:
        if monotonic()-started > min(float(payload["timeout_seconds"]), 30):
            raise TimeoutError()
        generator.generate_next_token()
        output.append(stream.decode(int(generator.get_next_tokens()[0])))
        count += 1
    return {"text": "".join(output), "prompt_tokens": len(tokens), "completion_tokens": count,
        "truncated": count >= limit and not generator.is_done()}


if __name__ == "__main__":
    try:
        value = json.loads(sys.stdin.buffer.read(32000))
        print(json.dumps(generate(Path(sys.argv[1]), value), ensure_ascii=False))
    except Exception:
        raise SystemExit(1) from None  # parent exposes only a stable degraded code, never native diagnostics/prompt
