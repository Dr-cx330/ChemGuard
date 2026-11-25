from .schemas import Decision, Evaluation, Operation

REGISTERED_DEVICES = {"Reactor_01": {"simulation_only": True}}
HIGH_RISK_TERMS = ("concentrated sulfuric acid", "浓硫酸", "sulfuric acid", "硫酸")
WATER_TERMS = ("water", "水")


def evaluate(op: Operation) -> Evaluation:
    if op.device_id not in REGISTERED_DEVICES:
        return Evaluation(decision=Decision.DENY, reasons=["Device is not registered."])

    chemicals_text = " ".join(op.chemicals).casefold()
    description = op.description.casefold()
    text = f"{chemicals_text} {description}"
    has_acid = any(term in text for term in HIGH_RISK_TERMS)
    has_water = any(term in text for term in WATER_TERMS)
    if has_acid and has_water and any(x in text for x in ("mix", "add", "加入", "混合", "迅速")):
        return Evaluation(decision=Decision.DENY, reasons=["Potentially hazardous acid-water mixing detected."])

    if any(x in op.action.casefold() for x in ("heat", "加热")) and any(x in text for x in ("ethanol", "乙醇")):
        return Evaluation(decision=Decision.HOLD, reasons=["Flammable solvent heating requires qualified human review and equipment-specific risk assessment."])

    # This prototype cannot validate chemistry or process conditions. No physical operation is approved.
    return Evaluation(decision=Decision.HOLD, reasons=["The prototype cannot establish chemical and equipment safety; human review is required."])
