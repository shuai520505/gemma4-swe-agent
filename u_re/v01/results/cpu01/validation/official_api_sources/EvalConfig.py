@dataclass
class EvalConfig:
    """Configuration for an evaluation run."""

    tasks_path: Path
    snapshots_dir: Path
    results_dir: Path
    submission_dir: Path
    models: ModelRegistry
    image: str = 'swebench-sandbox:latest'
    sandbox: str = 'docker'  # 'docker' (default) or 'subprocess' (Kaggle/notebooks)
    wheels_dir: Path | None = None
    graph_dir: str = 'data/graphs'
    embeddings_dir: str = 'data/embeddings'
    budget: EvaluationBudget = field(default_factory=EvaluationBudget)
    harness: HarnessLimits = field(default_factory=HarnessLimits)
    # Direct convenience kwargs for flat configuration
    timeout_seconds: int | None = None
    verification_timeout_seconds: int | None = None
    max_time_minutes: int | float | None = None
    max_tool_calls: int | None = None
    max_turns: int | None = None
    max_llm_calls: int | None = None
    task_ids: list[str] | None = None
    verbose: bool = False
    skip_agent_patch: bool = False
    limits: SubmissionLimits | None = None
    generation_constraints: GenerationConstraints | None = None
    adapter_manifest: AdapterManifest | None = None
    context_cache_config: ContextCacheConfig | None = None
    events_compaction_config: EventsCompactionConfig | None = None
    concurrency: int = 1
    shard_index: int | None = None
    num_shards: int | None = None
    display_mode: Literal['auto', 'dashboard', 'single', 'quiet'] | str = 'auto'
    enable_sandbox_testing: bool = True

    def __post_init__(self) -> None:
        """Merge flat kwargs into budget and harness if explicitly provided."""
        valid_modes = {'auto', 'dashboard', 'single', 'quiet'}
        if self.display_mode not in valid_modes:
            raise ValueError(
                f"Invalid display_mode {self.display_mode!r}, must be one of {valid_modes}"
            )

        if self.num_shards is not None and self.num_shards < 1:
            raise ValueError(f'num_shards must be >= 1, got {self.num_shards}')
        if self.shard_index is not None:
            if self.num_shards is None or self.num_shards < 1:
                raise ValueError('shard_index requires num_shards >= 1')
            if self.shard_index < 0 or self.shard_index >= self.num_shards:
                raise ValueError(
                    f'shard_index ({self.shard_index}) must be in range [0, {self.num_shards})'
                )

        default_limits, default_gen_constraints = build_submission_limits()
        if self.limits is None:
            self.limits = default_limits
        if self.generation_constraints is None:
            self.generation_constraints = default_gen_constraints

        t_min = (
            self.max_time_minutes
            if self.max_time_minutes is not None
            else self.budget.time_minutes
        )
        tc = (
            self.max_tool_calls
            if self.max_tool_calls is not None
            else self.budget.tool_calls
        )
        turns = (
            self.max_turns
            if self.max_turns is not None
            else (
                self.max_llm_calls
                if self.max_llm_calls is not None
                else self.budget.turns
            )
        )
        object.__setattr__(
            self,
            'budget',
            EvaluationBudget(
                time_minutes=t_min,
                tool_calls=tc,
                turns=turns,
                cost_usd=self.budget.cost_usd,
                total_tokens=self.budget.total_tokens,
            ),
        )

        cmd_timeout = (
            self.timeout_seconds
            if self.timeout_seconds is not None
            else self.harness.command_timeout_seconds
        )
        ver_timeout = (
            self.verification_timeout_seconds
            if self.verification_timeout_seconds is not None
            else self.harness.verification_timeout_seconds
        )
        object.__setattr__(
            self,
            'harness',
            HarnessLimits(
                command_timeout_seconds=cmd_timeout,
                max_stdout_chars=self.harness.max_stdout_chars,
                max_file_lines=self.harness.max_file_lines,
                max_file_chars=self.harness.max_file_chars,
                verification_timeout_seconds=ver_timeout,
            ),
        )

        if self.tasks_path is not None:
            tasks_parent = Path(self.tasks_path).parent
            if self.graph_dir == 'data/graphs' and not Path(self.graph_dir).exists():
                cand_graphs = tasks_parent / 'graphs'
                if cand_graphs.is_dir():
                    object.__setattr__(self, 'graph_dir', str(cand_graphs))
            if (
                self.embeddings_dir == 'data/embeddings'
                and not Path(self.embeddings_dir).exists()
            ):
                cand_emb = tasks_parent / 'embeddings'
                if cand_emb.is_dir():
                    object.__setattr__(self, 'embeddings_dir', str(cand_emb))
