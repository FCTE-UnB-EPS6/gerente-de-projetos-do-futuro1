from datetime import date

import pytest

from gpf.domain import Project, ProjectPhase, Risk, RiskLevel, RiskRegister, Stage


def make_project(**kwargs: object) -> Project:
    defaults: dict[str, object] = {
        "name": "Piloto",
        "sponsor": "Coordenação",
        "start": date(2026, 11, 9),
        "expected_benefits": ["Reduzir em 30% o esforço de relatórios"],
    }
    defaults.update(kwargs)
    return Project(**defaults)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("probability", "impact", "level"),
    [(1, 1, RiskLevel.LOW), (2, 3, RiskLevel.MEDIUM), (3, 4, RiskLevel.HIGH), (5, 4, RiskLevel.CRITICAL)],
)
def test_risk_level(probability: int, impact: int, level: RiskLevel) -> None:
    assert Risk("R1", "x", probability, impact, "ana").level is level


@pytest.mark.parametrize(("probability", "impact"), [(0, 3), (3, 6)])
def test_risk_rejects_out_of_scale(probability: int, impact: int) -> None:
    with pytest.raises(ValueError, match="entre 1 e 5"):
        Risk("R1", "x", probability, impact, "ana")


def test_risk_requires_code() -> None:
    with pytest.raises(ValueError, match="code"):
        Risk(" ", "x", 1, 1, "ana")


def test_register_ranks_and_filters() -> None:
    register = RiskRegister()
    register.add(Risk("R1", "baixo", 1, 2, "ana"))
    register.add(Risk("R2", "crítico", 5, 5, "bia"))
    register.add(Risk("R3", "alto", 3, 4, "caio"))
    assert [r.code for r in register.ranked()] == ["R2", "R3", "R1"]
    assert [r.code for r in register.above(RiskLevel.HIGH)] == ["R2", "R3"]
    with pytest.raises(ValueError, match="já registrado"):
        register.add(Risk("R1", "dup", 1, 1, "ana"))


def test_phase_transitions() -> None:
    project = make_project()
    project.advance_to(ProjectPhase.PLANNING)
    project.advance_to(ProjectPhase.EXECUTING)
    with pytest.raises(ValueError, match="transição inválida"):
        project.advance_to(ProjectPhase.INITIATING)


def test_planning_requires_business_case() -> None:
    project = make_project(expected_benefits=[])
    with pytest.raises(ValueError, match="business case"):
        project.advance_to(ProjectPhase.PLANNING)


def test_stage_tolerance() -> None:
    within = Stage("Estágio 1", budget=100, spent=108)
    over = Stage("Estágio 2", budget=100, spent=125)
    assert not within.exceeds_tolerance
    assert over.exceeds_tolerance
    assert make_project(stages=[within, over]).stages_in_exception == [over]
    with pytest.raises(ValueError, match="budget"):
        Stage("inválido", budget=0)
