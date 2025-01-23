from enum import Enum

class Tariff(Enum):
    HOURS_12 = 0
    DAY = 1
    WORKER = 2
    INCOGNITA_DAY = 3
    INCOGNITA_HOURS = 4
    SUBSCRIPTION = 5
    # TODO: have to remove. Do not use in tariff_rete.json.
    GIFT = 6