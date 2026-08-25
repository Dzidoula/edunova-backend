from unittest.mock import MagicMock

from app.services.tutor import Tutor, format_api_error


def test_tutor_without_api_key_is_unavailable_and_falls_back():
    tutor = Tutor(api_key="", api_base="", model="")
    assert tutor.available is False

    reply = tutor.reply(
        message="résume le document",
        document_text="Les fractions représentent une division entre deux nombres.",
        document_title="Cours de fractions",
        retrieved_chunks=[],
        pedagogical_snippets=[],
        history=[],
        active_adaptation=None,
    )
    assert "Cours de fractions" in reply


def test_tutor_uses_llm_client_when_available(monkeypatch):
    tutor = Tutor(api_key="fake-key", api_base="https://api.example.com/v1", model="test-model")
    assert tutor.available is True

    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="Réponse générée par le modèle."))]
    tutor.client = MagicMock()
    tutor.client.chat.completions.create.return_value = fake_response

    reply = tutor.reply(
        message="explique les fractions",
        document_text="Les fractions représentent une division entre deux nombres.",
        document_title="Cours de fractions",
        retrieved_chunks=["Les fractions représentent une division entre deux nombres."],
        pedagogical_snippets=[],
        history=[],
        active_adaptation=None,
    )
    assert reply == "Réponse générée par le modèle."
    tutor.client.chat.completions.create.assert_called_once()


def test_format_api_error_recognizes_401():
    class FakeError(Exception):
        status_code = 401

    message = format_api_error(FakeError("unauthorized"))
    assert "401" in message


def test_analyze_error_falls_back_to_heuristic_without_client():
    tutor = Tutor(api_key="", api_base="", model="")
    analysis = tutor.analyze_error(message="erreur de calcul sur le signe", notion="Fractions", subject="Mathématiques")
    assert analysis.error_type.value == "calculation"
    assert analysis.source == "heuristic"
