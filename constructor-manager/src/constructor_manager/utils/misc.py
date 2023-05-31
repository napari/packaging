import logging
from typing import Any, Tuple

logger = logging.getLogger(__name__)


def dedup(items: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """Deduplicate an list of items."""
    # FIXME remove code after checking and moving this func where it is used 
    # new_items: Tuple[Any, ...] = ()
    # for item in items:
    #     if item not in new_items:
    #         new_items += (item,)

    # return new_items

    return tuple(dict.fromkeys(items))