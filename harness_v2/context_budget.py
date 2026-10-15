"""Count the final ADK/LiteLLM chat request using the serving vLLM tokenizer."""
import asyncio
from copy import deepcopy
from dataclasses import dataclass
import json
import urllib.request


class ContextBudgetExceeded(RuntimeError):
    pass


class ContextCountingError(RuntimeError):
    pass


@dataclass(frozen=True)
class ContextPolicy:
    max_model_len: int = 32768
    safety_tokens: int = 1024

    def check(self, input_tokens, output_tokens):
        if (type(input_tokens) is not int or input_tokens < 0 or
                type(output_tokens) is not int or not 1 <= output_tokens <= 32768):
            raise ContextCountingError('Invalid or missing token count/output allowance')
        total = input_tokens + output_tokens + self.safety_tokens
        result = dict(input_tokens=input_tokens, output_reserved=output_tokens,
                      safety_tokens=self.safety_tokens, max_model_len=self.max_model_len,
                      total_reserved=total, decision='allow' if total <= self.max_model_len else 'reject')
        if total > self.max_model_len:
            raise ContextBudgetExceeded(json.dumps(result, sort_keys=True))
        return result


class VllmCounter:
    def __init__(self, base_url, api_key, timeout=15):
        # /tokenize is at the server root, outside /v1.
        self.url = base_url.rstrip('/').removesuffix('/v1') + '/tokenize'
        self.api_key, self.timeout = api_key, timeout

    async def __call__(self, body):
        def request():
            req = urllib.request.Request(self.url, data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + self.api_key, 'Content-Type': 'application/json'})
            # Bypass external proxies: this endpoint must be local.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req, timeout=self.timeout) as response:
                return json.load(response)
        return await asyncio.to_thread(request)


class RequestGuard:
    """No approximate fallback, history truncation, or output cap override."""
    def __init__(self, counter, generate, *, core_issue, emit=lambda event: None, policy=None):
        self.counter, self.generate, self.core_issue = counter, generate, core_issue
        self.emit, self.policy = emit, policy or ContextPolicy()

    async def acompletion(self, **kwargs):
        args = deepcopy(kwargs)
        messages = args.setdefault('messages', [])
        # ADK compaction can replace the original task with a lossy summary.
        # Restore the exact Issue body, never a rewritten or shorter version.
        restored = bool(self.core_issue) and not any(
            self.core_issue in m.get('content', '') for m in messages
            if m.get('role') == 'user' and isinstance(m.get('content'), str))
        if restored:
            position = next((i for i,m in enumerate(messages) if m.get('role') not in ('system','developer')), len(messages))
            messages.insert(position, dict(role='user', content=self.core_issue))
        body = dict(model=args['model'].removeprefix('openai/'), messages=messages,
                    add_generation_prompt=True, add_special_tokens=False)
        if args.get('tools') is not None:
            body['tools'] = args['tools']
        extra = args.get('extra_body') or {}
        for key in ('chat_template_kwargs','add_generation_prompt','continue_final_message','add_special_tokens'):
            if key in extra:
                body[key] = extra[key]
        output = args.get('max_completion_tokens', args.get('max_tokens'))
        # ADK's built-in summarizer constructs an uncapped LlmRequest. Make the
        # organizer default explicit so it too has a measurable reservation.
        if output is None:
            output=16384
            args['max_completion_tokens']=output
        try:
            count = await self.counter(body)
            if count.get('max_model_len') != self.policy.max_model_len:
                raise ContextCountingError('Serving context capacity differs from registered capacity')
            event = self.policy.check(count.get('count'), output)
        except ContextBudgetExceeded as exc:
            event = json.loads(str(exc))
            self.emit(dict(kind='context_admission', core_restored=restored, **event))
            raise
        except Exception as exc:
            self.emit(dict(kind='context_admission', decision='count_error', core_restored=restored,
                           error_type=type(exc).__name__))
            raise ContextCountingError('Token counting failed; generation was not sent') from exc
        self.emit(dict(kind='context_admission', core_restored=restored, **event))
        return await self.generate(**args)
