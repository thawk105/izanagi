# -*- coding: utf-8 -*-
"""variant の遺伝子空間 (最適化フラグ超立方体) と制約付き列挙器。

CCBench の最適化は protocol ごとのブール超立方体 (anatomy §3: silo 2^4, cicada 2^6,
oze 2^7 ... ≈ 258 binaries)。Phase 2 の「全探索」(roadmap §2(a)) はこの空間の列挙。
Phase 1 タスク6 ではまず silo を実体化し、骨格 (列挙→ビルド→検証) を配線する。

mutual-exclusion など「ビルドはできるが意味のない/無効な」組合せは constraint で弾く
(anatomy: NO_WAIT_LOCKING_IN_VALIDATION と NO_WAIT_OF_TICTOC は #if/#elif で相互排他)。
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from .model import Genome


@dataclass
class GenomeSpace:
    """1 protocol の遺伝子空間 = 軸 (flag→候補値) + 制約。"""
    protocol: str
    axes: Dict[str, List[int]]                       # flag -> 候補値リスト
    constraints: List[Callable[[Dict[str, int]], bool]] = field(default_factory=list)
    notes: str = ""

    def raw_size(self) -> int:
        n = 1
        for vs in self.axes.values():
            n *= len(vs)
        return n

    def enumerate(self) -> List[Genome]:
        """制約を満たす全 genome を決定論的順序で返す (flag 名順 × 値順)。"""
        keys = sorted(self.axes)
        out: List[Genome] = []
        for combo in itertools.product(*(self.axes[k] for k in keys)):
            flags = dict(zip(keys, combo))
            if all(c(flags) for c in self.constraints):
                out.append(Genome(self.protocol, flags))
        return out


# ---- silo の遺伝子空間 (Phase 1 タスク6 で配線する最初の protocol) ----
#
# anatomy §3 / cc/silo/CMakeLists.txt の live な最適化フラグ。死にフラグ
# (PARTITION_TABLE / PROCEDURE_SORT = print のみ) と計測撹乱ノブ (SLEEP_READ_PHASE /
# INSERT_*_DELAY_MS) は除外 (探索しても意味が無い・perf を歪めるだけ、絶対規律4)。
#   - BACK_OFF: abort 後の指数バックオフ (delay-on-conflict)
#   - NO_WAIT_LOCKING_IN_VALIDATION / NO_WAIT_OF_TICTOC: validation 競合の扱い。
#     #if/#elif で相互排他 → 両 1 は無効 (constraint で除外)
#   - WAL: commit 時 write-ahead log (durability。perf コスト)
# 生の 2^4=16 から相互排他違反 (両 no-wait=1) を除いた 12 が silo の有効空間。

def _no_wait_mutual_exclusion(flags: Dict[str, int]) -> bool:
    """NO_WAIT_LOCKING_IN_VALIDATION と NO_WAIT_OF_TICTOC を同時に 1 にしない。"""
    return not (flags.get("NO_WAIT_LOCKING_IN_VALIDATION", 0) == 1
                and flags.get("NO_WAIT_OF_TICTOC", 0) == 1)


SILO_SPACE = GenomeSpace(
    protocol="silo",
    axes={
        "BACK_OFF": [0, 1],
        "NO_WAIT_LOCKING_IN_VALIDATION": [0, 1],
        "NO_WAIT_OF_TICTOC": [0, 1],
        "WAL": [0, 1],
    },
    constraints=[_no_wait_mutual_exclusion],
    notes="silo の live 最適化 (anatomy §3)。死にフラグ・計測撹乱ノブは除外。"
          "生 2^4=16、相互排他で 12 有効。",
)

# protocol 名 → 空間。Phase 2 で cicada/oze/... を足す (今は silo のみ = 段階導入 規律5)。
SPACES: Dict[str, GenomeSpace] = {
    "silo": SILO_SPACE,
}


def space_for(protocol: str) -> GenomeSpace:
    if protocol not in SPACES:
        raise KeyError(f"未登録の protocol: {protocol} (登録済み: {sorted(SPACES)})")
    return SPACES[protocol]
