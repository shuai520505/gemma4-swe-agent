# Planning budget, not measured GPU cost

|Component|Seconds reserved|
|---|---:|
|Approved offline initialization|300|
|Native task baseline/recheck|300|
|Model startup cap|1200|
|One300s Agent worker, setup/Phase2/persistence included|1350|
|Export|300|
|Model/process cleanup|180|
|Safety|600|
|Total planning slot|4230|

Proposed window5400s. Agent300s begins after environment preparation; it is not the model-load or Notebook window. The inherited stage caps are prepare180,Agent330(includes cancellation slack),save60,prepareVerifier180,apply60,Verifier300,persist60,cleanup120 plus outer60 =1350. Current adapter uses the inherited historical task admission, not a silent extra task screen. An independently authorized runtime baseline recheck must preserve exact tests and reserve its300s slot.

Minimum planning account quota10800 reported seconds uses a conservative factor2, not an established per-device billing formula. Actual quota units, reservation and remaining full window must be checked at execution. No empirical P50/P95, memory peak, consumption or success rate is claimed. Future GPU SaveKernel maximum1, only after distinct authorization. This CPU-only interface check is a separate Notebook and consumes no GPU quota.
