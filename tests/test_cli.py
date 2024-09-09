# tests/test_cli.py
import unittest
from cliapp.cli import parse_args

class TestCLI(unittest.TestCase):
    def test_parse_args(self):
        """Test argument parsing."""
        # Mock command-line arguments
        test_args = ['--name', 'Alice']
        parsed_args = parse_args(test_args)
        self.assertEqual(parsed_args.name, 'Alice')

if __name__ == '__main__':
    unittest.main()
