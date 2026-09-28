from aiogram.fsm.state import State, StatesGroup


class SynastrySetup(StatesGroup):
    waiting_for_partner_date = State()
    waiting_for_partner_time = State()
    waiting_for_partner_place = State()
