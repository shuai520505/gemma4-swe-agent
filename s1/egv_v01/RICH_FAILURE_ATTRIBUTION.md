# Read-only attribution of the two residual assertions

**Confirmed proximal cause: dependency-theme color values disagree with the
fixed golden ANSI strings.** This is established for these two assertions,
not a blanket attribution of every failing Rich test to infrastructure. The
historical dependency/version transition remains **root_cause_unknown**.
No scoring result,test,expected string,production code or dependency was
changed to make either assertion pass.

## Observed historical facts

The frozen rich_3130 GPU clean baseline had1pass5fail;Control and E3 each had
4pass2fail. test_markdown_render and test_inline_code fail in all three,with
identical native JUnit failure messages. The original STOP/history,TaskResult,
resolved=false/test_exit_code=1,raw XML and Patches remain immutable.

## Actual independent Linux CPU reproduction

CPU03 created three separate disposable native verifier sandboxes:clean base,
the exact observed Control Patch,and the exact observed E3 Patch. The original
public task evaluator overlay and complete six-case native command ran without
changes. Native results reproduce1pass5fail,4pass2fail,4pass2fail respectively,
zero errors. Both residual JUnit messages in each state exactly equal the
historical message. All three sandbox cleanup records pass.

After the native result,and before cleanup,a separate diagnostic process runs
the same full public test file with Python tracing. It records failing-function
locals,rendered/expected strings,style-return values,source/test hashes,paths,
versions,environment and source excerpts. This additional run is explicitly
diagnostic,not a replacement Phase2 or a model repair trial. Native uses its
original PYTHONSAFEPATH=1/PYTHONNOUSERSITE=1 command;diagnostics use python -s,
record PYTHONSAFEPATH unset/PYTHONNOUSERSITE=1,and independently verify the same
workspace implementation. That transparent invocation difference is retained.

Effective versions in all three:Rich13.5.2,Pygments2.20.0,pytest8.4.2,
markdown-it-py4.0.0. Rich markdown resolves inside each distinct workspace;
Pygments resolves to the shared image's
/usr/local/lib/python3.12/dist-packages/pygments. Presence of cached2.21.0 and
2.20.0 wheels does not mean either was reinstalled. Effective imports,not wheel
filenames alone,establish the executing dependency. Native import provenance
and diagnostic __file__/sys.path agree on workspace Rich. Source/test hashes
before and after every diagnostic are equal.

## Confirmed rendering path and exact differences

| Assertion | Actual Pygments/Rich style return | Golden value | Other text |
|---|---|---|---|
| test_markdown_render | monokai Token.Keyword.Namespace foreground #ff4689 (255,70,137) | #f92672 (249,38,114) | equal after removing SGR |
| test_inline_code | emacs Token.Text.Whitespace foreground #bbbbbb (187,187,187) | #000000 (0,0,0) | equal after removing SGR |

The first case uses Markdown's code_theme="monokai". The second explicitly
requests inline_code_lexer="python",inline_code_theme="emacs" for `import this`.
Actual tracing records PygmentsSyntaxTheme.get_style_for_token returning those
foregrounds,with the same backgrounds and other style returns in all three
code states. Its captured source calls the Pygments style class's
style_for_token,constructs Rich Style with that color,and caches it. The
resulting SGR color values exactly match the actual test strings. This is a
direct data-flow explanation of the observed assertion mismatches,not an
inference from error keywords or from a package version alone.

The original test render helper explicitly fixes width,color_system="truecolor",
StringIO output and legacy_windows=False. Baseline diagnostic variants TERM=dumb
and TERM=xterm-256color reproduce the same two color differences and plain-text
equality. Original TERM=xterm-color,COLORTERM/NO_COLOR/FORCE_COLOR unset. This
does not prove that every environment variable or terminal mode is irrelevant;
it rules out these TERM variants as the explanation under the fixed helper.

Full string locals,ANSI inventories,function returns,versions,source excerpts
and path evidence are in results/cpu03/validation/rich_attribution/*/diagnostic-*.json.
analysis/rich_attribution_summary.json joins native historical equality with
those observations. Comparing strings with SGR removed is an analytic operation
only:it was never used to change test assertions or official pass/fail.

## Interpretation and unresolved questions

Confirmed:these residual failures are preexisting exact-color incompatibilities
between the current theme behavior and the expected ANSI output;they are not
new regressions caused by either table-only Patch. They remain ordinary
assertion_failure events and official failures. This diagnosis does not repair
the task or retroactively convert the earlier pair to resolved/unknown.

Possible historical explanation:goldens were produced under different theme
data. **Not verified:**which Pygments release/commit changed those values,whether
an older dependency reproduces the goldens,or what policy an official scoring
environment should adopt. No downgrade,theme monkeypatch or expected-output
edit was attempted. No reference repair or hidden answer was inspected.
These questions remain root_cause_unknown at the version-history/policy level.
The historical GPU trace did not separately record the effective Pygments
module version/bytes. Identical failure messages and the pinned image support
reproduction,not an invented historical package observation. The direct style
return/version evidence above belongs to the new independent CPU investigation.
Do not hardcode these colors or dependency findings into EGV or future tasks.
