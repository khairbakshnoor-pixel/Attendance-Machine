from dataclasses import replace
import numpy as np
import pytest
from config.settings import Settings
from face.embeddings import normalize
from face.liveness import LivenessChallenge
from face.recognizer import match_embedding
from services.registration import Registration, validate_identity
from face.preprocessing import check_quality


def test_recognition_threshold_and_ambiguity():
    vector = normalize(np.arange(128))
    person = dict(id=1, employee_id="E1", name="Test", embedding=vector)
    assert match_embedding(vector, [person], .5, .06).user_id == 1
    assert match_embedding(-vector, [person], .5, .06) is None
    assert match_embedding(vector, [person, {**person, "id": 2}], .5, .06) is None
    assert match_embedding(vector, [], .5, .06) is None
    with pytest.raises(ValueError):
        normalize(np.zeros(128))


def test_static_face_never_passes_liveness():
    challenge = LivenessChallenge(Settings())
    assert not any(challenge.update(1, 0.0, i * .1) for i in range(300))


def test_random_turn_and_return_required():
    settings = Settings()
    challenge = LivenessChallenge(settings)
    for i in range(settings.verification_frames):
        assert not challenge.update(1, 0.0, i * .1)
    direction = challenge.direction
    for i in range(settings.liveness_hold_frames):
        assert not challenge.update(1, direction * .2, 1 + i * .1)
    assert challenge.stage == "return"
    for i in range(settings.liveness_hold_frames - 1):
        assert not challenge.update(1, 0.0, 2 + i * .1)
    assert challenge.update(1, 0.0, 2.3)


@pytest.mark.parametrize("identity, timestamp", [(2, .6), (1, 5.0)])
def test_identity_change_and_gap_reset_challenge(identity, timestamp):
    challenge = LivenessChallenge(Settings())
    for i in range(5):
        challenge.update(1, 0, i * .1)
    assert challenge.stage == "turn"
    assert not challenge.update(identity, .2, timestamp)
    assert challenge.stage == "center"


def test_registration_rejects_mixed_identity():
    class Backend:
        model_version = "test"
        def extract(self, frame):
            return np.zeros(15), normalize(frame)
    enrollment = Registration(Backend(), Settings())
    enrollment.add_sample(np.ones(128))
    with pytest.raises(ValueError, match="does not match"):
        enrollment.add_sample(-np.ones(128))


@pytest.mark.parametrize("value", ["", "x", "bad id", "../id", "a" * 33])
def test_invalid_id(value):
    with pytest.raises(ValueError):
        validate_identity(value, "Test")


def test_configuration_fails_closed():
    with pytest.raises(ValueError):
        replace(Settings(), verification_frames=1)


def test_quality_rejects_small_clipped_and_blurred_faces():
    frame = np.full((300, 300, 3), 128, dtype=np.uint8)
    with pytest.raises(ValueError, match="too small"):
        check_quality(frame, np.array([20, 20, 30, 30]), 90, 65)
    with pytest.raises(ValueError, match="entire face"):
        check_quality(frame, np.array([-10, 20, 120, 120]), 90, 65)
    with pytest.raises(ValueError, match="blurry"):
        check_quality(frame, np.array([20, 20, 120, 120]), 90, 65)
