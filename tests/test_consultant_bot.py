from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from consultant_bot import ALLOWED_ROLES, Source, generate_response


def test_invalid_role_prompts_user():
    response = generate_response(
        role="Астролог",
        language="ru",
        session_paid=True,
        price="1000",
        currency="RUB",
        context=[],
        question="",
    )

    assert "Выберите специалиста" in response
    assert response.count("Короткий итог") == 1


def test_unpaid_session_contains_price_and_examples():
    role = next(iter(ALLOWED_ROLES))
    response = generate_response(
        role=role,
        language="ru",
        session_paid=False,
        price="990",
        currency="RUB",
        context=[],
        question="Какой вопрос можно задать?",
    )

    assert "Оплатите 990 RUB" in response
    assert "Примеры вопросов" in response


def test_paid_session_without_context_requests_more_data():
    role = next(iter(ALLOWED_ROLES))
    response = generate_response(
        role=role,
        language="ru",
        session_paid=True,
        price="990",
        currency="RUB",
        context=[],
        question="",
    )

    assert "Недостаточно данных" in response
    assert "Источники" in response


def test_non_russian_language_is_rejected():
    role = next(iter(ALLOWED_ROLES))
    try:
        generate_response(
            role=role,
            language="en",
            session_paid=True,
            price="990",
            currency="RUB",
            context=[],
            question="",
        )
    except ValueError as exc:  # pragma: no cover - defensive branch
        assert "only Russian" in str(exc)
    else:  # pragma: no cover - guard against silent success
        raise AssertionError("Expected ValueError for unsupported language")

