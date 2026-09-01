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
#     lockWriteSet() は #if/#elif のみで #else 句が無い (cc/silo/transaction.cc の
#     lockWriteSet() 内ブロック。行番号は submodule pin 前進でずれるため記さない):
#       (1,0) 競合で即 abort  /  (0,1) 自ロック解放して全体 retry
#       (1,1) #elif が dead code で (1,0) と挙動同一 → 冗長
#       (0,0) #if/#elif どちらも非展開で競合分岐が空。expected を再読みしないまま
#             無限スピン (livelock)。thread≥2 で計測不能
#       → 有効なのは XOR (ちょうど一方が 1) の 2 組のみ
#       (insight 2026-06-22_silo-both-no-wait-zero-livelock.md)
#   - WAL: commit 時 write-ahead log (durability。perf コスト)
# 生の 2^4=16 から no-wait の XOR 制約 (両 1=冗長 + 両 0=livelock を計 8 除外) で 8 が有効空間。

def _no_wait_xor(flags: Dict[str, int]) -> bool:
    """NO_WAIT_LOCKING_IN_VALIDATION と NO_WAIT_OF_TICTOC は XOR (ちょうど一方が 1)。

    両 1 は #elif が dead code で (1,0) と挙動同一の冗長。両 0 は lockWriteSet() の
    競合分岐が空 (#else 句が無い) になり expected を再読みしないまま無限スピンする
    (livelock) ため thread≥2 で計測不能。どちらも探索空間から除外する。
    """
    return (flags.get("NO_WAIT_LOCKING_IN_VALIDATION", 0)
            != flags.get("NO_WAIT_OF_TICTOC", 0))


SILO_SPACE = GenomeSpace(
    protocol="silo",
    axes={
        "BACK_OFF": [0, 1],
        "NO_WAIT_LOCKING_IN_VALIDATION": [0, 1],
        "NO_WAIT_OF_TICTOC": [0, 1],
        "WAL": [0, 1],
    },
    constraints=[_no_wait_xor],
    notes="silo の live 最適化 (anatomy §3)。死にフラグ・計測撹乱ノブは除外。"
          "生 2^4=16、no-wait XOR (両 1=冗長 + 両 0=livelock を除外) で 8 有効。",
)

# mocc の現行 CMake から直交操作できる YCSB 向け空間。
# RWLOCK は live なコード分岐だが cc/mocc/CMakeLists.txt の bare define であり、cache
# option から off にできない。INSERT_*_DELAY_MS は計測撹乱ノブなので探索から除外する
# (絶対規律4)。KEY_SORT の live site は include/ycsb.hh に限られるため、8 通りという
# 数は YCSB workload での数である。
MOCC_SPACE = GenomeSpace(
    protocol="mocc",
    axes={
        "BACK_OFF": [0, 1],
        "TEMPERATURE_RESET_OPT": [0, 1],
        "KEY_SORT": [0, 1],
    },
    constraints=[],
    notes="mocc の現行 CMake から直交操作できる YCSB 向け空間。"
          "RWLOCK は live 分岐だが bare define で直交操作できないため軸にしない。"
          "INSERT_*_DELAY_MS は計測撹乱ノブとして除外する (絶対規律4)。"
          "8 通りは YCSB workload での数であり、KEY_SORT の live site は "
          "include/ycsb.hh に限られる。",
)


# protocol 名 → 空間。D1360 の初手 mocc までを登録し、tictoc/cicada はまだ登録しない。
SPACES: Dict[str, GenomeSpace] = {
    "silo": SILO_SPACE,
    "mocc": MOCC_SPACE,
}


def space_for(protocol: str) -> GenomeSpace:
    if protocol not in SPACES:
        raise KeyError(f"未登録の protocol: {protocol} (登録済み: {sorted(SPACES)})")
    return SPACES[protocol]


def protocol_from_floor_genome(value: object) -> str:
    """floor JSON の canonical genome から protocol を取り出す共有規則。

    floor consumer が不正な値を別々に解釈しないための最小 helper である。
    ``Genome.canonical()`` が生成する、非空 body の正準形だけを受理する。
    """
    if type(value) is not str or "|" not in value:
        raise ValueError("floor genome が canonical 文字列でない")
    protocol, body = value.split("|", 1)
    if not protocol or not body:
        raise ValueError("floor genome が canonical 文字列でない")
    flags: Dict[str, int] = {}
    for assignment in body.split(","):
        if "=" not in assignment:
            raise ValueError("floor genome が canonical 文字列でない")
        name, encoded = assignment.split("=", 1)
        if not name or name in flags:
            raise ValueError("floor genome が canonical 文字列でない")
        try:
            flags[name] = int(encoded)
        except ValueError as exc:
            raise ValueError("floor genome が canonical 文字列でない") from exc
    try:
        canonical = Genome(protocol=protocol, flags=flags).canonical()
    except (TypeError, ValueError) as exc:
        raise ValueError("floor genome が canonical 文字列でない") from exc
    if canonical != value:
        raise ValueError("floor genome が canonical 文字列でない")
    return protocol
