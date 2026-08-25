from app.services.error_analysis import (
    ErrorType,
    classify_error_heuristic,
    ErrorAnalysis,
    ADAPTATION_STRATEGIES,
)


def test_classifies_calculation_errors():
    assert classify_error_heuristic("j'ai fait une erreur de calcul") == ErrorType.CALCULATION


def test_classifies_reading_errors():
    assert classify_error_heuristic("je n'ai pas bien lu la consigne") == ErrorType.READING


def test_classifies_method_errors():
    assert classify_error_heuristic("je ne sais pas quelle formule utiliser") == ErrorType.METHOD


def test_classifies_concept_errors():
    assert classify_error_heuristic("je confonds les deux définitions") == ErrorType.CONCEPT


def test_defaults_to_unknown():
    assert classify_error_heuristic("") == ErrorType.UNKNOWN


def test_error_analysis_memory_text_includes_notion_and_strategy():
    analysis = ErrorAnalysis(
        error_type=ErrorType.CALCULATION,
        notion="Fractions",
        subject="Mathématiques",
        summary="Erreur de signe.",
        strategy=ADAPTATION_STRATEGIES[ErrorType.CALCULATION],
    )
    text = analysis.as_memory_text()
    assert "Fractions" in text
    assert "Erreur de signe." in text
