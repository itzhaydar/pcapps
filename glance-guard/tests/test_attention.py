import unittest
from glance_guard.attention import AttentionPolicy, Classifier, Observation, Signal
from glance_guard.settings import Settings

class AttentionTests(unittest.TestCase):
    def setUp(self):
        self.settings=Settings()
        self.policy=AttentionPolicy(self.settings)
    def send(self,signal,t):
        return self.policy.update(Observation(signal),t)
    def test_away_then_return(self):
        self.assertFalse(self.send(Signal.AWAY,0))
        self.assertFalse(self.send(Signal.AWAY,.7))
        self.assertTrue(self.send(Signal.AWAY,.9))
        self.assertTrue(self.send(Signal.LOOKING,1))
        self.assertFalse(self.send(Signal.LOOKING,1.4))
    def test_brief_blink(self):
        self.send(Signal.BLINK,0)
        self.assertFalse(self.send(Signal.BLINK,.2))
        self.assertFalse(self.send(Signal.LOOKING,.3))
    def test_blink_cannot_reveal(self):
        self.send(Signal.AWAY,0); self.send(Signal.AWAY,1)
        self.send(Signal.LOOKING,2)
        self.assertTrue(self.send(Signal.BLINK,2.4))
        self.assertTrue(self.send(Signal.LOOKING,2.5))
        self.assertFalse(self.send(Signal.LOOKING,2.9))
    def test_closed_eyes_conceal(self):
        self.send(Signal.BLINK,0); self.send(Signal.BLINK,.5)
        self.assertTrue(self.send(Signal.BLINK,1.4))
    def test_natural_movements_cancel_pending(self):
        for t in range(10):
            self.assertFalse(self.send(Signal.AWAY,t))
            self.assertFalse(self.send(Signal.LOOKING,t+.2))
    def test_fail_safe_policies(self):
        for signal,setting in [(Signal.MISSING,"missing_face_protect"),
                               (Signal.FAILURE,"camera_failure_protect"),
                               (Signal.UNCERTAIN,"uncertain_protect")]:
            for enabled in (True,False):
                settings=Settings(**{setting:enabled})
                policy=AttentionPolicy(settings)
                policy.update(Observation(signal),0)
                self.assertEqual(policy.update(Observation(signal),2),enabled)
    def test_head_and_eye_directions(self):
        for features in [(35,0,.5,.5),(-35,0,.5,.5),(0,30,.5,.5),
                         (0,-30,.5,.5),(0,0,.85,.5),(0,0,.15,.5),(0,0,.5,.9)]:
            self.assertEqual(Classifier(self.settings).classify(features).signal,Signal.AWAY)
    def test_center_and_blink(self):
        classifier=Classifier(self.settings)
        self.assertEqual(classifier.classify((0,0,.5,.5)).signal,Signal.LOOKING)
        self.assertEqual(classifier.classify((0,0,.5,.5),True).signal,Signal.BLINK)
    def test_calibration_offsets(self):
        settings=Settings(calibration=[10,10,.65,.65])
        self.assertEqual(Classifier(settings).classify((10,10,.65,.65)).signal,Signal.LOOKING)
    def test_invalid_features_are_uncertain(self):
        self.assertEqual(Classifier(self.settings).classify((float("nan"),0,.5,.5)).signal,Signal.UNCERTAIN)

if __name__ == "__main__":
    unittest.main()
