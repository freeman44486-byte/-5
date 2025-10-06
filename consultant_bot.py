"""Utility functions for generating structured consultation responses.

The module implements the formatting rules described in the system prompt for the
paid consultation bot.  It focuses on handling the high level logic that does
not depend on a specific specialist knowledge base, such as dealing with unpaid
sessions, validating the selected role, and guiding the user when there are no
external sources available.

The goal is to keep the response builder deterministic so that a calling
service can rely on predictable structure and wording.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


ALLOWED_ROLES = {"Юрист", "Медицинский консультант", "Автомеханик", "Сантехник", "Электрик"}


@dataclass(frozen=True)
class Source:
    """Representation of a single snippet returned by the retrieval layer."""

    title: str
    url: str
    date: str | None
    snippet: str

    @classmethod
    def from_mapping(cls, mapping: dict) -> "Source":
        """Create a ``Source`` instance from a mapping with lenient keys."""

        return cls(
            title=str(mapping.get("title", "")),
            url=str(mapping.get("url", "")),
            date=(mapping.get("date") if mapping.get("date") else None),
            snippet=str(mapping.get("snippet", "")),
        )


def _normalise_sources(context: Iterable[Source | dict]) -> List[Source]:
    sources: List[Source] = []
    for entry in context:
        if isinstance(entry, Source):
            sources.append(entry)
        else:
            sources.append(Source.from_mapping(entry))
    return sources


def _format_sources(context: Sequence[Source]) -> str:
    if not context:
        return "Источники:\n• Источники не переданы; предоставьте релевантные материалы."  # noqa: E501

    lines = ["Источники:"]
    for src in context:
        date = src.date or "дата не указана"
        title = src.title or "Без названия"
        url = src.url or "URL не предоставлен"
        lines.append(f"• {title} ({date}) {url}")
    return "\n".join(lines)


def _intro_line() -> str:
    return "0) ⚠️ Консультация справочная и не заменяет обращение к врачу/юристу/сертифицированному специалисту."


def _format_section(header: str, body: Sequence[str]) -> str:
    lines = [header]
    lines.extend(body)
    return "\n".join(lines)


def _role_prompt() -> str:
    lines = [
        "Короткий итог",
        "• Выберите специалиста из списка: Юрист, Медицинский консультант, Автомеханик, Сантехник, Электрик.",
        "• После выбора специалиста опишите вопрос детально.",
    ]
    details = [
        "Подробный разбор",
        "• Текущий выбор роли отсутствует или выходит за допустимые рамки сервиса.",
        "• Укажите точное направление, чтобы получить профильную консультацию.",
        "• Приведите ключевые факты, документы или симптомы для более предметного диалога.",
    ]
    steps = [
        "Практические шаги",
        "1. Выберите одного из доступных специалистов в интерфейсе бота.",
        "2. Переформулируйте запрос с учётом выбранного направления.",
        "3. При необходимости подготовьте уточняющую информацию (даты, модели, симптомы).",
    ]
    limits = [
        "Ограничения и когда нужна очная помощь",
        "• Без указания роли бот не может предоставить тематическую информацию.",
        "• Очная консультация обязательна, если ситуация требует немедленной помощи.",
    ]
    sections = [
        _intro_line(),
        "\n".join(lines),
        "\n".join(details),
        "\n".join(steps),
        "\n".join(limits),
        "Источники:\n• Источники не переданы; предоставьте релевантные материалы.",
    ]
    return "\n".join(sections)


def _unpaid_response(role: str, price: str, currency: str) -> str:
    examples = {
        "Юрист": [
            "Как расторгнуть договор с контрагентом без штрафов?",
            "Какие сроки ответа на претензию предусмотрены законом?",
        ],
        "Медицинский консультант": [
            "Как контролировать артериальное давление дома?",
            "Когда кашель требует срочного обращения к врачу?",
        ],
        "Автомеханик": [
            "Что делать, если двигатель теряет мощность на высоких оборотах?",
            "Какие признаки у изношенных тормозных колодок?",
        ],
        "Сантехник": [
            "Как устранить протечку под мойкой?",
            "Почему греется стояк отопления неравномерно?",
        ],
        "Электрик": [
            "Что делать при систематическом выбивании автомата?",
            "Как безопасно подключить мощный бытовой прибор?",
        ],
    }

    sample_questions = examples.get(role, [
        "Какой вопрос можно задать выбранному специалисту?",
        "Какие данные подготовить для консультации?",
    ])

    sections = [
        _intro_line(),
        _format_section(
            "Короткий итог",
            [
                "• Доступ к консультации открыт после оплаты услуги.",
                f"• Оплатите {price} {currency}, затем задайте вопрос специалисту {role}.",
            ],
        ),
        _format_section(
            "Подробный разбор",
            [
                "• До подтверждения оплаты информация по сути вопроса не раскрывается.",
                "• После оплаты бот подключит профильного консультанта и сохранит историю диалога.",
                "• Чем конкретнее запрос и факты, тем точнее будет справочная консультация.",
            ],
        ),
        _format_section(
            "Практические шаги",
            [
                "1. Перейдите к оплате в интерфейсе бота и подтвердите транзакцию.",
                "2. После оплаты выберите профильного специалиста и сформулируйте вопрос.",
                "3. Подготовьте документы, фотографии или измерения, чтобы ускорить консультацию.",
            ],
        ),
        _format_section(
            "Ограничения и когда нужна очная помощь",
            [
                "• До оплаты бот не предоставляет содержательных рекомендаций.",
                "• Для срочных или опасных ситуаций сразу обращайтесь к офлайн-специалисту.",
                "• При технических проблемах с оплатой используйте официальный канал поддержки.",
            ],
        ),
        "Источники:\n• Источники не переданы; предоставьте релевантные материалы.",
        _format_section(
            "Примеры вопросов",
            [f"• {question}" for question in sample_questions],
        ),
    ]
    return "\n".join(sections)


def _insufficient_context(role: str, context: Sequence[Source]) -> str:
    sections = [
        _intro_line(),
        _format_section(
            "Короткий итог",
            [
                "• Недостаточно данных из источников, чтобы подготовить развёрнутый ответ.",
                f"• Уточните детали запроса для роли {role} и приложите проверенные материалы.",
            ],
        ),
        _format_section(
            "Подробный разбор",
            [
                "• Отсутствие источников не позволяет сослаться на нормативные документы или руководства.",
                "• Для точного ответа нужны факты: даты, модели, симптомы, результаты диагностики.",
                "• Соблюдение требований к цитированию возможно только при наличии структурированных выдержек.",
            ],
        ),
        _format_section(
            "Практические шаги",
            [
                "1. Соберите релевантные источники (документы, руководства, протоколы).",
                "2. Уточните ключевые параметры вопроса и переформулируйте запрос.",
                "3. Отправьте дополнительные материалы, чтобы получить индивидуальную консультацию.",
            ],
        ),
        _format_section(
            "Ограничения и когда нужна очная помощь",
            [
                "• Без подтверждённых данных бот предоставит только общие рекомендации.",
                "• При срочных рисках немедленно обратитесь к профильному специалисту офлайн.",
            ],
        ),
        _format_sources(context),
    ]
    return "\n".join(sections)


def generate_response(
    *,
    role: str,
    language: str,
    session_paid: bool,
    price: str,
    currency: str,
    context: Iterable[Source | dict],
    question: str,
) -> str:
    """Generate a bot response that complies with the system level instructions.

    The function focuses on the control flow shared by all specialists.  It does
    not attempt to summarise domain specific snippets—that responsibility remains
    with the specialist models.  Instead, it ensures that structural and
    compliance requirements are respected before a specialised component is
    invoked.
    """

    if language.lower() != "ru":
        raise ValueError("Currently only Russian language responses are supported.")

    if role not in ALLOWED_ROLES:
        return _role_prompt()

    normalised_context = _normalise_sources(context)

    if not session_paid:
        return _unpaid_response(role, price, currency)

    if not normalised_context:
        return _insufficient_context(role, normalised_context)

    # The detailed, citation rich answer should be produced elsewhere.  Here we
    # provide a protective fallback to guarantee deterministic behaviour.
    return _insufficient_context(role, normalised_context)


__all__ = [
    "ALLOWED_ROLES",
    "Source",
    "generate_response",
]

