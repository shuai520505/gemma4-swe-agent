"""Author-created micro scenarios, NOT public Kaggle tasks or training data.

Edits are supplied scripted actors to isolate scheduling, not generated repairs.
Both policies receive the same implementation, probes, tests and edit actor.
"""
CASES = {
    'interface': dict(requirement='CLI render_text entry must work; preserve render(value).',
        source="def render(value):\n    return '[' + value + ']'\n",
        caller="from app import render_text\ndef main(): return render_text('x')\n",
        probe="from caller import main\nassert main() == '[x]'\n",
        verify="from app import render, render_text\nfrom caller import main\nassert render('old') == '[old]'\nassert render_text('x') == '[x]'\nassert main() == '[x]'\n",
        replacement="def render(value):\n    return '[' + value + ']'\n\nrender_text = render\n", contradiction=True),
    'dependency_injection': dict(requirement='Use the caller supplied factory without constructing the default client.',
        source="class Default:\n    def read(self): return 'default'\ndef load(factory=None):\n    return Default().read()\n",
        caller="from app import load\nclass Fake:\n    def read(self): return 'injected'\ndef main(): return load(lambda: Fake())\n",
        probe="from caller import main\nassert main() == 'injected', 'factory bypassed'\n",
        verify="from app import load\nfrom caller import main\nassert main() == 'injected'\nassert load() == 'default'\n",
        replacement="class Default:\n    def read(self): return 'default'\ndef load(factory=None):\n    return (factory() if factory is not None else Default()).read()\n", contradiction=True),
    'zero_boundary': dict(requirement='Zero is an explicit upper limit, None means no limit; negative values unchanged.',
        source="def cap(value, limit=None):\n    return min(value, limit) if limit else value\n",
        caller="from app import cap\ndef main(): return cap(4, 0)\n",
        probe="from caller import main\nassert main() == 0, 'zero limit ignored'\n",
        verify="from app import cap\nassert cap(4, 0) == 0\nassert cap(-2, None) == -2\nassert cap(4, 3) == 3\n",
        replacement="def cap(value, limit=None):\n    return min(value, limit) if limit is not None else value\n", contradiction=False),
    'old_behavior': dict(requirement='Empty string returns None; preserve integer zero, negative and invalid input behavior.',
        source="def parse(value):\n    return int(value)\n",
        caller="from app import parse\ndef main(): return parse('')\n",
        probe="from caller import main\nassert main() is None\n",
        verify="from app import parse\nassert parse('') is None\nassert parse(0) == 0\nassert parse('-2') == -2\ntry: parse('bad')\nexcept ValueError: pass\nelse: raise AssertionError('invalid input accepted')\n",
        replacement="def parse(value):\n    return None if value == '' else int(value)\n", contradiction=False),
}
