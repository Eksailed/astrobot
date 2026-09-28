from aiogram.fsm.state import State, StatesGroup


class ProfileSetup(StatesGroup):
    waiting_for_consent = State()
    waiting_for_birth_date = State()
    waiting_for_birth_time = State()
    waiting_for_birth_place = State()


class AIChatState(StatesGroup):
    in_dialog = State()
