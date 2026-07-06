# -*- coding: utf-8 -*-
"""submodule (ccbench) の **現行 pin** を 1 箇所に集約する (後続段 3, D38)。

なぜ集約するか: 後続段 3 で izanagi-trace ブランチに write_set 被覆 assert を足した
ため pin が dff0f1e → 028f34d に前進した。`ccbench_commit` は campaign-id の
pre-image (ident.canonical_preimage) に入るので、pin 前進は新 campaign の
campaign-id を移動させる (decisions.md:327 の ODR-fix gitlink 前進と同型 = 既知・
正直な content-addressed 挙動、バグではない)。

**この定数を使うのは pin 前進後に新設された driver だけ** (現行 = s3 lock-coverage)。
歴史的 driver (p3_kickoff / p3_s4_red / p2_2 / backoff_* / sanity_silo / demo /
s2_verify_calibration) は**自分の literal pin (dff0f1e) を保持**する — それぞれの
campaign はその pin で凍結・push 済みで、再走するには submodule を dff0f1e に checkout
してから回す (現 working-tree が 028f34d のとき dff0f1e-pin driver を回すと
patchharness の pinned-clean assert が fails-closed で止まる = 正しい安全側動作)。
一律に全 driver をこの定数に張り替えると歴史的 campaign が現 config で孤立するため
**しない** (IDENT-1/IDENT-3 の裁定)。

push は人間 (この環境に認証なし、D16)。新 izanagi-trace commit (028f34d) は human
push まで un-clonable — その pin を指す superproject gitlink も push 完了まで解決
不能。凍結済み歴史的 campaign は push 済みの dff0f1e を指し続けるので再現可能。
"""

# 現行 pin = izanagi-trace HEAD (write_set 被覆 assert 込み、後続段 3, D38)。
CURRENT_PIN = "028f34d"

# 歴史的 pin (kickoff/s4-red 等が凍結された基準。参照用・張り替え禁止)。
KICKOFF_PIN = "dff0f1e"
# その full 40-char hash。cache_key backward-compat golden は full hash で計算された
# ため、pin 前進 (D38) 後もこの固定値で導出安定性を pin 非依存に検証する (裁定12)。
# 注: 歴史的 driver は 7-char KICKOFF_PIN を ccbench_commit に渡すため cache_key は
# golden と別値になる (full/short 表現の既存不整合。段 3 とは独立の潜在課題)。
KICKOFF_PIN_FULL = "dff0f1ef2a4b84746f6463839e85b24301f4b16d"
