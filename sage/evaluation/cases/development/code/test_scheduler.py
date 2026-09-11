import unittest
from scheduler import ready

class SchedulerTest(unittest.TestCase):
    def test_all_dependencies_are_required(self):
        self.assertFalse(ready({"dependencies": ["a", "b"]}, {"a"}))
        self.assertTrue(ready({"dependencies": ["a", "b"]}, {"a", "b"}))

if __name__ == "__main__": unittest.main()
