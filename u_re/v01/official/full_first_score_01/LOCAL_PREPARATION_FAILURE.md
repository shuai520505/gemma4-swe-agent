Local preparation failures, no hidden retries:
- Initial filesystem-script invocation failed importing u_re before any API/dispatch; module invocation fixed import routing.
- Collector initially had a quote SyntaxError before any request; corrected in local source.
- Owned-profile list returned id=0 for all rows. Exact observed canonical title/ref was then checked via GetKernel,which returned ID140121936,version1,frozen semantic source and candidate bytes. No source/ID was inferred from the list alone.
- Formal submission preflight stopped on numAllowedNow=0 before any CreateCodeSubmission transport. Subsequent readonly list showed57505115; user confirmed manually submitting the named Notebook. No scoring request was retried or sent by this controller.
