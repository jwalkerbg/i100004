# tests/test_core.py

import unittest
from cliapp.core import hello_world

class TestCore(unittest.TestCase):
    def test_hello_world(self):
        """Test the hello_world function."""
        self.assertEqual(hello_world('Alice'), 'Hello, Alice!')

if __name__ == '__main__':
    unittest.main()
