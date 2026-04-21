from .beggar import Beggar
from .courtesan import Courtesan
from .constable import Constable
from .taoist import Taoist

CHARACTER_MAP = {
    "乞丐": Beggar,
    "花魁": Courtesan,
    "捕快": Constable,
    "道士": Taoist,
}
