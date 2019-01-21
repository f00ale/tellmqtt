import unittest

import tellmqtt.tellstickhandler
import json

class TestFineoffset(unittest.TestCase):
    def setUp(self):
        self.handler = tellmqtt.tellstickhandler.TellstickHandler()

    def testFineoffsetTemperatureSensor(self):
        r = self.handler.decode(b'+Wclass:sensor;protocol:fineoffset;data:49801AFF9E;\r\n')
        self.assertIsNotNone(r)
        self.assertEqual(('fineoffset',152), r.path)
        self.assertIn('temperature', r.values)
        self.assertAlmostEqual(r.values['temperature'], 2.6)
        self.assertNotIn('humidity', r.values)

        self.assertIn('json', r.values)
        vals = json.loads(r.values['json'])
        self.assertIn('temperature', vals)
        self.assertAlmostEqual(vals['temperature'], 2.6)
        self.assertNotIn('humidity', vals)

    def testFineoffsetTemperatureSensorNegative(self):
        r = self.handler.decode(b'+Wclass:sensor;protocol:fineoffset;data:49881FFFBB;\r\n')
        self.assertIsNotNone(r)
        self.assertEqual(('fineoffset',152), r.path)
        self.assertIn('temperature', r.values)
        self.assertAlmostEqual(r.values['temperature'], -3.1)
        self.assertNotIn('humidity', r.values)

        self.assertIn('json', r.values)
        vals = json.loads(r.values['json'])
        self.assertIn('temperature', vals)
        self.assertAlmostEqual(vals['temperature'], -3.1)
        self.assertNotIn('humidity', vals)

    def testFineoffsetTemperatureHumiditySensor(self):
        r = self.handler.decode(b'+Wclass:sensor;protocol:fineoffset;data:4970D82884;\r\n')
        self.assertIsNotNone(r)
        self.assertEqual(('fineoffset',151), r.path)
        self.assertIn('temperature', r.values)
        self.assertAlmostEqual(r.values['temperature'], 21.6)
        self.assertIn('humidity', r.values)
        self.assertAlmostEqual(r.values['humidity'], 40)

        self.assertIn('json', r.values)
        vals = json.loads(r.values['json'])
        self.assertIn('temperature', vals)
        self.assertAlmostEqual(vals['temperature'], 21.6)
        self.assertIn('humidity', vals)
        self.assertAlmostEqual(vals['humidity'], 40)
