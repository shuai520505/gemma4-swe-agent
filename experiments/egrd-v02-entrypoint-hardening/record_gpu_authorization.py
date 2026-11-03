"""Record the human's explicit CPU/GPU reply; CPU pass remains mandatory."""
import json
from pathlib import Path
D=Path(__file__).resolve().parent
receipt=dict(user_answer='允许CPU和GPU',explicit_GPU_confirmation=True,model='12b',scope='One EGRD V0.2 two-public-task 12B engineering smoke after complete CPU02 acceptance',maximum_dispatches=1,retries=0,maximum_seconds=18000,formal_submission=False,actual_four_L4_required=True,CPU_acceptance_required=True,Agent_seconds=300,command_seconds=120,tool_calls=60,turns=80,conditional_31b='Only independently recorded bounded fallback if reproducible model-level entry failure is established; never for infrastructure error or one unsuccessful repair')
with (D/'GPU12_AUTHORIZATION.json').open('x',encoding='utf8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
