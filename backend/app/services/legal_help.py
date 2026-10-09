"""Public in-repo guide retrieval only. Model selects permitted sections; server returns exact text."""
from collections import Counter, deque
import hashlib
import json
import math
from pathlib import Path
import re
from threading import Lock
from time import monotonic

from pydantic import BaseModel, ConfigDict, Field
from app.services.model_gateway.errors import ModelGatewayError
from app.services.model_gateway.types import ChatMessage

INJECTION = re.compile(r"ignore\s+(?:all\s+)?(?:previous|system)\s+instructions|reveal\s+(?:secrets|tenant)|system\s*prompt|<\|im_(?:start|end)\|>|jailbreak", re.I)
ADVICE = re.compile(r"legal advice|enforceable|under\s+.+\s+law|should\s+i\s+sign|can\s+i\s+sue|am\s+i\s+liable|is\s+(?:it|this)\s+legal|summari[sz]e\s+my|show\s+my\s+(?:contracts|documents)|what\s+does\s+my", re.I)
APP_TOPIC = re.compile(r"upload|download|quarantin|scanner|ocr|source viewer|citation|review|proposal|workspace|dashboard|sign\s*in|log\s*in|login|password|terms|summary|summaries|conversation|history|notification|task|obligation|regulatory|compliance|evidence|export|platform|application", re.I)
STOP = {"how", "do", "i", "a", "the", "to", "is", "can", "my", "what", "of", "and", "in", "for"}


class HelpSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    section_ids: list[str] = Field(min_length=1, max_length=3)


class HelpRateLimited(ValueError):
    pass


def words(value):
    return [w for w in re.findall(r"[a-z0-9]+", value.casefold()) if w not in STOP]


def chunk_document(source, path):
    text = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode()).hexdigest()
    result, title, lines = [], "Overview", []
    def flush():
        body = "\n".join(lines).strip()
        if not body or "integration notes" in title.casefold():
            return
        for offset in range(0, len(body), 1600):
            quote = body[offset:offset+1600]
            slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
            result.append({"section_id": f"{source}:{slug}:{offset//1600+1}", "title": title,
                "source": source, "source_filename": path.name, "source_sha256": digest, "quote": quote,
                "document_status": "draft_not_in_force" if source == "terms-draft" else "development_guide",
                "href": "/app/help?guide_section=" + slug})
    for line in text.splitlines():
        if line.startswith(("## ", "### ")):
            flush()
            title, lines = line.lstrip("# ").strip(), []
        else:
            lines.append(line)
    flush()
    return result


class HelpService:
    def __init__(self, paths, *, gateway=None):
        self.sections = []
        for source, path in paths.items():
            try:
                self.sections.extend(chunk_document(source, Path(path)))
            except OSError:
                pass
        self.gateway = gateway
        self._rates, self._lock = {}, Lock()
        self._tokens = [Counter(words(s["title"] + " " + s["quote"])) for s in self.sections]

    def _rate(self, user_id):
        now = monotonic()
        with self._lock:
            for key in list(self._rates):
                while self._rates[key] and now-self._rates[key][0] >= 60:
                    self._rates[key].popleft()
                if not self._rates[key]:
                    del self._rates[key]
            key = str(user_id)
            if key not in self._rates and len(self._rates) >= 4096:
                raise HelpRateLimited("help_rate_capacity")
            bucket = self._rates.setdefault(key, deque())
            if len(bucket) >= 10:
                raise HelpRateLimited("help_rate_limited")
            bucket.append(now)

    def matches(self, question):
        query = set(words(question))
        n = len(self.sections)
        scores = []
        for index, token_counts in enumerate(self._tokens):
            score = 0.0
            for token in query:
                frequency = token_counts[token]
                if frequency:
                    document_frequency = sum(token in counts for counts in self._tokens)
                    score += math.log(1 + (n-document_frequency+0.5)/(document_frequency+0.5)) * frequency/(frequency+1.2)
                    if token in words(self.sections[index]["title"]):
                        score += 2
            if score:
                scores.append((score, index))
        return [self.sections[i] for _,i in sorted(scores, key=lambda pair: (-pair[0], pair[1]))[:5]]

    def answer(self, question, *, user_id):
        self._rate(user_id)
        result = {"status": "refused", "answer": "I can help with using this application, not legal advice or your documents.",
            "citations": [], "reason": "application_help_only", "scope": "public_application_guide_only",
            "model": None, "profile_version": "legal-help-guide-selection-v1"}
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1200 or "\0" in question:
            result["reason"] = "invalid_help_question"
            return result
        if INJECTION.search(question) or ADVICE.search(question) or not APP_TOPIC.search(question):
            return result
        matches = self.matches(question)
        if not matches:
            result.update(status="degraded", answer="No matching guide section is available. Open Help & Resources or try another application-use question.", reason="help_corpus_unavailable_or_no_match")
            return result
        chosen = matches[:3]
        result.update(status="degraded", reason="help_model_unavailable")
        if self.gateway is not None:
            # Neither identity nor workspace/matter/document/context enters the model payload.
            intent = ", ".join(sorted({m.group().casefold() for m in APP_TOPIC.finditer(question)}))
            payload = {"question": "Application-use instructions for: " + intent,
                "sections": [{"section_id": s["section_id"], "title": s["title"], "quote": s["quote"][:1000]} for s in matches]}
            try:
                response = self.gateway.generate_structured(messages=[
                    ChatMessage(role="system", content="You help users operate the application. Select up to 3 relevant section_ids from the supplied public guide only. Return JSON {\"section_ids\":[\"id\"]}. No prose, advice, tools, authority, or invented IDs. The terms document is a draft, not in force. /no_think"),
                    ChatMessage(role="user", content=json.dumps(payload))], schema=HelpSelection, temperature=0,
                    max_output_tokens=128, repair_attempts=0, think=False, timeout_seconds=20)
                allowed = {s["section_id"]: s for s in matches}
                if any(s not in allowed for s in response.value.section_ids):
                    raise ValueError("invalid_help_citations")
                chosen = [allowed[s] for s in dict.fromkeys(response.value.section_ids)]
                result.update(status="answered", reason="onnx_selected_verified_guide_sections", model=response.result.model)
            except (ModelGatewayError, ValueError, TimeoutError, ConnectionError):
                result.update(status="degraded", reason="help_model_unavailable_or_output_rejected")
        result["citations"] = chosen
        result["answer"] = "\n\n".join(("Draft — not in force. " if s["document_status"] == "draft_not_in_force" else "") +
            s["title"] + "\n" + s["quote"] for s in chosen)
        return result


def default_help_service():
    from app.core.config import settings
    gateway = None
    if settings.legal_help_model_enabled:
        from app.services.model_gateway.gateway import ModelGateway
        config = settings.model_copy(update={"model_runtime": "onnx", "model_name": "Qwen/Qwen3-0.6B",
            "model_temperature": 0, "model_context_window": 2048, "model_max_output_tokens": 128,
            "model_timeout_seconds": 20, "model_first_load_timeout_seconds": 20, "model_structured_repair_attempts": 0,
            "model_log_prompts": False})
        gateway = ModelGateway(config)
    root = settings.legal_help_docs_root
    return HelpService({"guide": root/"LEGAL_PLATFORM_USER_GUIDE.md",
        "terms-draft": root/"LEGAL_PLATFORM_TERMS_AND_CONDITIONS_v2.0_DRAFT.md"}, gateway=gateway)
