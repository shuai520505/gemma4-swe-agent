def compile_submission(
    submission_dir: str | Path,
    tool_registry: ToolRegistry | dict[str, Callable[..., Any]],
    model_registry: ModelRegistry,
    callback_registry: CallbackRegistry | None = None,
    limits: SubmissionLimits | None = None,
    generation_constraints: GenerationConstraints | None = None,
    code_executor: BaseCodeExecutor | None = None,
    script_timeout: int = 300,
    skill_registry: SkillRegistry | None = None,
    adapter_manifest: AdapterManifest | None = None,
    adapter_resolver_fn: Callable[[Any, AdapterInfo], Any] | None = None,
    agent_factory: AgentClassFactory | None = None,
) -> BaseAgent:
    """Compile a submission directory into a live ADK agent tree.

    Args:
        submission_dir: Path to the unpacked submission directory.
        tool_registry: Registry of available tools, or a plain
            ``dict[str, Callable]`` mapping tool names to callables.
            A dict is automatically wrapped in a :class:`ToolRegistry`.
        model_registry: Registry mapping model aliases to LLM configs.
        callback_registry: Optional registry of pre-approved callbacks.
        limits: Optional submission limits (uses defaults if not provided).
        generation_constraints: Optional organizer-defined constraints on
            which generation parameters submissions can set and their valid
            ranges. If ``None``, no restrictions on generation params.
        code_executor: Optional sandboxed code executor for running agent skills.
        script_timeout: Timeout for skill script execution in seconds.
        skill_registry: Optional registry of pre-approved skills.
        adapter_manifest: Optional manifest of discovered adapters. If ``None``,
            adapters are automatically discovered from the submission directory.
        adapter_resolver_fn: Optional callable to resolve custom model representations
            when an agent specifies both a base model and an adapter.
        agent_factory: Optional factory registry of agent classes and constructors
            for dependency injection. If ``None``, uses the module's resolved classes.

    Returns:
        The compiled root ADK agent, ready to run.

    Raises:
        SubmissionValidationError: If the submission fails validation, including
            generation parameter constraint violations, missing skill directories,
            invalid skill loading, or specifying an adapter without a base model.
        SubmissionSchemaError: If the agent configuration or any referenced
            sub-agent/tool configuration fails schema validation.
        PathTraversalError: If any configuration file, skill path, or sub-agent
            reference attempts to escape the submission root directory.
        ToolNotFoundError: If a referenced tool is not found in the registry.
        ModelNotFoundError: If a referenced model alias is not found in the registry.
        AdapterNotFoundError: If a referenced adapter is not found in discovered adapters.
        CallbackNotFoundError: If a referenced callback is not found in the registry.
        LimitExceededError: If the submission exceeds configured structural limits
            (e.g., agent count, sub-agent depth, instruction length, skill count).
        yaml.YAMLError: If any YAML configuration file is malformed.
    """
    # Coerce dict → ToolRegistry
    if isinstance(tool_registry, dict):
        reg = ToolRegistry()
        for name, fn in tool_registry.items():
            reg.register(name, fn)
        tool_registry = reg

    limits = limits or SubmissionLimits()

    # 1. Validate directory structure
    submission = validate_directory(submission_dir, limits)
    try:
        # 2. Discover adapters if not explicitly passed
        if adapter_manifest is None:
            adapter_manifest = discover_adapters(
                submission.root_dir, limits.adapter_extensions
            )

        # 3. Load root YAML with sandboxed !include
        raw_config = load_yaml(submission.config_path, submission.root_dir, limits=limits)

        # 4. Parse & validate against restricted schema
        try:
            config = SandboxedAgentConfig.model_validate(raw_config)
        except Exception as e:  # noqa: BLE001
            handle_schema_validation_error(e, context_desc="config")

        # 5. Initialize agent factory (supports direct injection and test patches)
        if agent_factory is None:
            agent_factory = AgentClassFactory(
                agent_cls=Agent,
                sequential_agent_cls=SequentialAgent,
                parallel_agent_cls=ParallelAgent,
                loop_agent_cls=LoopAgent,
                agent_tool_cls=AgentTool,
                skill_toolset_cls=SkillToolset,
                genai_types=genai_types,
            )
        else:
            agent_factory = AgentClassFactory(
                agent_cls=agent_factory.agent_cls if agent_factory.agent_cls is not None else Agent,
                sequential_agent_cls=(
                    agent_factory.sequential_agent_cls
                    if agent_factory.sequential_agent_cls is not None
                    else SequentialAgent
                ),
                parallel_agent_cls=(
                    agent_factory.parallel_agent_cls
                    if agent_factory.parallel_agent_cls is not None
                    else ParallelAgent
                ),
                loop_agent_cls=(
                    agent_factory.loop_agent_cls
                    if agent_factory.loop_agent_cls is not None
                    else LoopAgent
                ),
                agent_tool_cls=(
                    agent_factory.agent_tool_cls
                    if agent_factory.agent_tool_cls is not None
                    else AgentTool
                ),
                skill_toolset_cls=(
                    agent_factory.skill_toolset_cls
                    if agent_factory.skill_toolset_cls is not None
                    else SkillToolset
                ),
                genai_types=(
                    agent_factory.genai_types
                    if agent_factory.genai_types is not None
                    else genai_types
                ),
            )

        # 6. Compile agent tree (recursive)
        ctx = CompilationContext(
            root_dir=submission.root_dir,
            tool_registry=tool_registry,
            model_registry=model_registry,
            callback_registry=callback_registry,
            limits=limits,
            generation_constraints=generation_constraints,
            code_executor=code_executor,
            script_timeout=script_timeout,
            skill_registry=skill_registry,
            adapter_manifest=adapter_manifest,
            adapter_resolver_fn=adapter_resolver_fn,
            agent_factory=agent_factory,
        )
        return _compile_agent(config.root, ctx)
    finally:
        clear_active_limits_for_root(submission.root_dir)
