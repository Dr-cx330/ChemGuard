from fastapi.testclient import TestClient
from chemguard.main import app
from chemguard.safety import evaluate
from chemguard.schemas import Decision, Operation

client = TestClient(app)


def op(**overrides):
    values = dict(device_id="Reactor_01", action="stir", parameters={"rpm": 200}, duration_seconds=600, chemicals=["ethanol"], description="stir ethanol")
    values.update(overrides)
    return Operation(**values)


def test_unknown_device_denied():
    assert evaluate(op(device_id="Unknown")).decision == Decision.DENY


def test_acid_water_mixing_denied():
    result = evaluate(op(chemicals=["concentrated sulfuric acid", "water"], action="add", description="mix acid and water"))
    assert result.decision == Decision.DENY


def test_ethanol_heating_held():
    assert evaluate(op(action="heat_and_stir", description="heat ethanol to 80 C")).decision == Decision.HOLD


def test_ambiguous_operation_held():
    assert evaluate(op(chemicals=[], description="unknown process")).decision == Decision.HOLD


def test_invalid_json_shape_rejected():
    response = client.post("/api/v1/evaluate", json={"device_id": "Reactor_01", "action": "stir", "parameters": {}, "duration_seconds": 60, "extra": "no"})
    assert response.status_code == 422


def test_real_hardware_is_disabled():
    assert client.get("/health").json()["hardware_enabled"] is False
