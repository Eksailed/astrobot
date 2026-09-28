from datetime import date
import random
from dataclasses import dataclass
from services.tarot.deck import TAROT_DECK, TarotCard


@dataclass
class DrawnCard:
    card: TarotCard
    is_reversed: bool

    @property
    def position_str(self) -> str:
        return "Перевернутое положение 🔄" if self.is_reversed else "Прямое положение ⬆️"

    @property
    def meaning(self) -> str:
        return self.card.reversed_meaning if self.is_reversed else self.card.upright_meaning


def draw_card_of_the_day(user_id: int | None = None) -> DrawnCard:
    if user_id is not None:
        today_str = date.today().isoformat()
        rng = random.Random(f"{user_id}:{today_str}")
        card = rng.choice(TAROT_DECK)
        is_reversed = rng.random() < 0.25
        return DrawnCard(card=card, is_reversed=is_reversed)

    card = random.choice(TAROT_DECK)
    is_reversed = random.random() < 0.25
    return DrawnCard(card=card, is_reversed=is_reversed)


def draw_three_cards_spread() -> list[tuple[str, DrawnCard]]:
    """Past, Present, Future spread."""
    selected_cards = random.sample(TAROT_DECK, 3)
    positions = [
        "1. Прошлое (фундамент ситуации)",
        "2. Настоящее (ключевая энергия)",
        "3. Будущее (наиболее вероятный итог)",
    ]
    return [
        (pos, DrawnCard(card=c, is_reversed=random.random() < 0.25))
        for pos, c in zip(positions, selected_cards)
    ]


def draw_love_spread() -> list[tuple[str, DrawnCard]]:
    """Love and relationships spread."""
    selected_cards = random.sample(TAROT_DECK, 3)
    positions = [
        "1. Ваши чувства и ожидания",
        "2. Чувства и отношение партнера",
        "3. Потенциал и совет для пары",
    ]
    return [
        (pos, DrawnCard(card=c, is_reversed=random.random() < 0.25))
        for pos, c in zip(positions, selected_cards)
    ]


def draw_career_spread() -> list[tuple[str, DrawnCard]]:
    """Career and finance spread."""
    selected_cards = random.sample(TAROT_DECK, 3)
    positions = [
        "1. Текущее финансовое/рабочее положение",
        "2. Скрытые вызовы или препятствия",
        "3. Ключ к успеху и росту дохода",
    ]
    return [
        (pos, DrawnCard(card=c, is_reversed=random.random() < 0.25))
        for pos, c in zip(positions, selected_cards)
    ]
