"""Parameterize r12 admission without changing its Issue preservation or tokenizer."""
from copy import deepcopy
from harness_v2.context_budget import RequestGuard


class Guard(RequestGuard):
    def __init__(self, counter, generate, *, config, **kwargs):
        super().__init__(counter,generate,**kwargs)
        self.config=config

    async def acompletion(self, **kwargs):
        args=deepcopy(kwargs); c=self.config
        cap=args.get('max_completion_tokens',args.get('max_tokens'))
        if cap is not None and cap!=c.output_tokens:
            raise ValueError('Output cap drift')
        # ADK compaction also uses this client; its otherwise uncapped request
        # receives the same registered allowance and thinking/seed semantics.
        if cap is None: args['max_completion_tokens']=c.output_tokens
        extra=args.setdefault('extra_body',{})
        template=extra.setdefault('chat_template_kwargs',{})
        enabled=c.thinking_budget>0
        if template.get('enable_thinking',enabled)!=enabled:
            raise ValueError('Thinking mode drift')
        template['enable_thinking']=enabled
        if enabled:
            if extra.get('thinking_token_budget',c.thinking_budget)!=c.thinking_budget:
                raise ValueError('Thinking budget drift')
            extra['thinking_token_budget']=c.thinking_budget
        elif 'thinking_token_budget' in extra:
            raise ValueError('Thinking-off still has budget')
        if args.get('seed',c.seed)!=c.seed:
            raise ValueError('Seed drift')
        if c.seed is not None: args['seed']=c.seed
        self.emit(dict(kind='research_parameters',output_tokens=c.output_tokens,
            thinking_budget=c.thinking_budget,include_thoughts=c.include_thoughts,
            seed=c.seed,uncapped_summary=cap is None))
        return await super().acompletion(**args)
