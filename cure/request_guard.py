"""Research request observer, reusing r12's fail-closed tokenizer admission."""
from copy import deepcopy
import hashlib
import json
from harness_v2.context_budget import RequestGuard


class ConfiguredGuard(RequestGuard):
    def __init__(self, counter, generate, *, core_issue, config, emit=lambda event: None):
        super().__init__(counter, generate, core_issue=core_issue, emit=emit)
        self.config = config

    async def acompletion(self, **kwargs):
        args = deepcopy(kwargs)
        config = self.config
        value = args.get('max_completion_tokens', args.get('max_tokens'))
        missing_cap = value is None
        if missing_cap:
            args['max_completion_tokens'] = config.output_tokens
        elif value != config.output_tokens:
            raise ValueError('Outgoing output cap differs from registration')
        extra = dict(args.get('extra_body') or {})
        args['extra_body'] = extra
        template = extra.setdefault('chat_template_kwargs', {})
        enabled = config.thinking_budget > 0
        if 'enable_thinking' in template and template['enable_thinking'] != enabled:
            raise ValueError('Outgoing thinking mode differs from registration')
        template['enable_thinking'] = enabled
        if enabled:
            if extra.get('thinking_token_budget', config.thinking_budget) != config.thinking_budget:
                raise ValueError('Outgoing thinking cap differs from registration')
            extra['thinking_token_budget'] = config.thinking_budget
        elif 'thinking_token_budget' in extra:
            raise ValueError('Thinking-off request still contains thinking tokens')
        if args.get('seed') is not None and args['seed'] != config.seed:
            raise ValueError('Outgoing seed differs from registration')
        args['seed'] = config.seed
        self.emit(dict(kind='research_request_parameters', max_output_tokens=config.output_tokens,
            thinking_budget=config.thinking_budget, seed=config.seed, enable_thinking=enabled,
            uncapped_request_defaulted=missing_cap,
            messages_sha256=hashlib.sha256(json.dumps(args.get('messages'), sort_keys=True).encode()).hexdigest()))
        return await super().acompletion(**args)
