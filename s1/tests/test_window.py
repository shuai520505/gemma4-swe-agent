import inspect
import unittest
from s1.window import SessionWindow


class WindowTests(unittest.TestCase):
    def test_complete_slot_boundary_and_one_second_late(self):
        self.assertTrue(SessionWindow(0,clock=lambda:8550).admission(1350)['allow'])
        self.assertFalse(SessionWindow(0,clock=lambda:8551).admission(1350)['allow'])

    def test_install_and_hash_time_not_reset_at_server_start(self):
        window=SessionWindow(0,clock=lambda:9000)
        self.assertFalse(window.admission(1350)['allow'])
        self.assertEqual(window.admission(1350)['elapsed_seconds'],9000)

    def test_bootstrap_needs_server_plus_complete_slot(self):
        self.assertTrue(SessionWindow(0,clock=lambda:7350).admission(1200+1350)['allow'])
        self.assertFalse(SessionWindow(0,clock=lambda:7351).admission(1200+1350)['allow'])

    def test_invalid_clock_or_slot_rejected(self):
        with self.assertRaises(ValueError):SessionWindow(float('nan'))
        with self.assertRaises(ValueError):SessionWindow(2,clock=lambda:1).admission(10)
        with self.assertRaises(ValueError):SessionWindow(0,clock=lambda:1).admission(0)

    def test_actual_session_requires_Notebook_origin(self):
        from s1.session import run
        signature=inspect.signature(run)
        with self.assertRaises(TypeError):signature.bind(None,None,'smoke')
        self.assertEqual(signature.bind(None,None,'smoke',session_started=0).arguments['session_started'],0)
