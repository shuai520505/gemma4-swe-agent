import unittest
from .idle import parse_metrics


class IdleTests(unittest.TestCase):
    def test_idle_requires_both_gauges(self):
        self.assertFalse(parse_metrics('vllm:num_requests_running 0')['known'])
    def test_all_labels_must_be_idle(self):
        raw='vllm:num_requests_running{model_name="x",engine="0"} 0\nvllm:num_requests_waiting{engine="0"} 0\n'
        self.assertTrue(parse_metrics(raw)['idle'])
        self.assertFalse(parse_metrics(raw+'vllm:num_requests_running{engine="1"} 1')['idle'])
    def test_unknown_or_nonzero_is_not_idle(self):
        self.assertFalse(parse_metrics('')['idle'])
        self.assertFalse(parse_metrics('vllm:num_requests_running 1\nvllm:num_requests_waiting 0')['idle'])
