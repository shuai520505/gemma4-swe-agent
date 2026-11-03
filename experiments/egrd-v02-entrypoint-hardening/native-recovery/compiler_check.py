"""Run unchanged official-Compiler acceptance without overwriting prior receipts."""
import asyncio,importlib.util,shutil
from pathlib import Path
R=Path(__file__).resolve().parent;D=R.parent
work=R/'compiler-work';work.mkdir(exist_ok=False);(work/'evidence').mkdir()
shutil.copytree(D/'packages',work/'packages');shutil.copyfile(D/'PACKAGE_MANIFEST.json',work/'PACKAGE_MANIFEST.json')
spec=importlib.util.spec_from_file_location('recovery_compiler_acceptance',D/'sdk_acceptance.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.D=work
asyncio.run(module.main())
