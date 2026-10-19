"""Student task (slides 43-44): repair four unsafe mapping decisions."""

STARTER = {
    "resourceType": "Observation",
    "id": "mimic-lab-1001",
    "status": "final",  # TODO: Is this status supported by source evidence?
    "code": {"text": "Creatinine"},  # TODO: retain the local item code/system.
    "subject": {"reference": "Patient/10000032"},
    "encounter": {"reference": "Encounter/UNKNOWN"},  # TODO: hadm_id is null.
    "valueQuantity": {
        "value": 2.1,
        "unit": "mg/dL",
        # TODO: assert UCUM only after the unit has been recognized.
    },
    # TODO: restore source labevent_id as an identifier.
}

print(STARTER)
