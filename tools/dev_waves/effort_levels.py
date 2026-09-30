"""reasoning / effort 語彙に関する izanagi の repo policy。

この 2 定数は izanagi の repo policy であり、CLI の capability 集合の
attest ではない。``CLAUDE_EFFORTS`` の出典は ``claude --help`` が文書化した
語彙 (``low, medium, high, xhigh, max``) であり、実受理集合の実測ではない。

Codex の受理集合は model 依存である。``docs/failures.md`` の F56 が記録する
とおり、``gpt-5.4-mini`` は ``max`` を拒否し ``none`` を受理する。本 module を
使う検査は requested token だけを見ており、model×reasoning の対応も served
model の identity も保証しない。
``ultra`` は luna 系が非対応である (依頼が指定した事実であり、独立実測ではない)。
この定数への収載は全 model の受理を意味せず、本 module は model×reasoning の互換を保証しない。
model×reasoning の非対応組を起動前に拒否する恒久対応の所有は T-183 / T-184 にある。

本 module を ``tools/dev_waves/`` に置くのは、``tools/dev_waves/daemon.py`` の
``_supervisor_digest()`` が同 directory 直下の ``*.py`` / ``*.json`` を hash
しており、受理集合を supervisor の完全性閉包の内側へ入れるためである。
"""

CLAUDE_EFFORTS: tuple[str, ...] = ("low", "medium", "high", "xhigh", "max")
CODEX_REASONING_EFFORTS: tuple[str, ...] = (
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
    "ultra",
)

__all__ = ["CLAUDE_EFFORTS", "CODEX_REASONING_EFFORTS"]
