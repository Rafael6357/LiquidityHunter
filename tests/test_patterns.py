import unittest
import pandas as pd
from modules.pattern_detector import PatternDetector

class TestPatternDetector(unittest.TestCase):
    def setUp(self):
        self.detector = PatternDetector()
        # Crear un DF de prueba
        data = {
            'time': pd.to_datetime(['2024-01-01 00:00', '2024-01-01 00:15', '2024-01-01 00:30']),
            'open': [1.1000, 1.1010, 1.1005],
            'high': [1.1020, 1.1030, 1.1015],
            'low': [1.0990, 1.1000, 1.0995],
            'close': [1.1010, 1.1005, 1.1010]
        }
        self.df = pd.DataFrame(data)

    def test_amd_cycle_empty(self):
        # El detector debería manejar DFs vacíos o pequeños
        result = self.detector.detect_amd_cycle(self.df)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
