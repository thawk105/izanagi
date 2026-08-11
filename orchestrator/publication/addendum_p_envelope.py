"""追補 P の exact-key envelope 検査。

production caller は存在せず、現時点では単体検査のみで使う。追補 P は未凍結で
あり、本 module は production 経路で機械執行されていない。
"""

from __future__ import annotations

from orchestrator.preregistration.addendum_envelope import (
    parse_addendum_fields,
    require_exact_fields,
)


__all__ = (
    "ADDENDUM_P_EXACT_FIELDS",
    "require_addendum_p_exact_fields",
)


ADDENDUM_P_EXACT_FIELDS = frozenset({"p01", "p02", "p03"})


def require_addendum_p_exact_fields(blob: bytes) -> None:
    """追補 P envelope の key が p01〜p03 と過不足なく一度ずつ一致することを課す。"""

    # parser は共有実装を再利用し、P 固有の固定集合だけをこの wrapper が所有する。
    require_exact_fields(blob, ADDENDUM_P_EXACT_FIELDS)
