from aiogram.fsm.state import State, StatesGroup


class AdminState(StatesGroup):
    waiting_for_broadcast_text = State()
    confirm_broadcast = State()
    waiting_for_grant_pro = State()
