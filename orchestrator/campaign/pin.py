# -*- coding: utf-8 -*-
"""submodule (ccbench) の **現行 pin** を 1 箇所に集約する (後続段 3, D38)。

なぜ集約するか: 後続段 3 で izanagi-trace ブランチに write_set 被覆 assert を足した
ため pin が dff0f1e → 028f34d に前進した。段 5 で同ブランチに permutation 保存
assert (D41) を足し 028f34d → d706650 に再前進した。
2026-08-12 に d706650 → 511c953、2026-09-20 [T-2304] に D2150 項 1 の
承認で 511c953 → e9e477c に前進した (mocc trace v2 hook・T-1943 lineage
witness・TRACE=0 include identity fix の 4 commit)。2026-09-23 [T-2858] に
D2227 項 1 の承認で e9e477c → 6810666 へ前進した (mocc X/P 計装 1 commit)。`ccbench_commit` は campaign-id
の pre-image (ident.canonical_preimage) に入るので、pin 前進は新 campaign の
campaign-id を移動させる (decisions.md:327 の ODR-fix gitlink 前進と同型 = 既知・
正直な content-addressed 挙動、バグではない)。

**この定数を使うのは pin 前進後に新設された driver と現行で再走する driver だけ**
(backoff_sweep を含む)。歴史的 driver (p3_kickoff / p3_s4_red / p2_2 /
backoff_repro / sanity_silo / demo / s2_verify_calibration) は**自分の literal pin
(dff0f1e) を保持**する — それぞれの campaign はその pin で凍結・push 済みで、再走するには submodule を
dff0f1e に checkout してから回す (現 working-tree が 6810666 のとき dff0f1e-pin driver
を回すと patchharness の pinned-clean assert が fails-closed で止まる = 正しい安全側
動作)。一律に全 driver をこの定数に張り替えると歴史的 campaign が現 config で孤立する
ため **しない** (IDENT-1/IDENT-3 の裁定)。

push は人間 (この環境に認証なし、D16)。新 izanagi-trace commit (511c953、028f34d も
同様) は human push まで un-clonable — その pin を指す superproject gitlink も push
完了まで解決不能。凍結済み歴史的 campaign は push 済みの dff0f1e を指し続けるので
再現可能。候補 e9e477ca は 2026-09-20 に GitHub から取得可能と確認済み。
"""

# 現行 pin = 6810666 (e9e477ca の単一の子、mocc X/P 計装)。
# D2227 項 1、2026-09-23 [T-2858]。
CURRENT_PIN = "6810666"

# 直前の pin (write_set 被覆 assert のみ、後続段 3, D38)。s3_lock_coverage.py など
# 段3時点の driver はこちらを literal 保持する形にはしていない (pin.CURRENT_PIN を
# 参照する現行 driver 群は前進を自動的に追う設計、上記コメント参照)。参照用にのみ残す。
PREVIOUS_PIN = "028f34d"

# 歴史的 pin (kickoff/s4-red 等が凍結された基準。参照用・張り替え禁止)。
KICKOFF_PIN = "dff0f1e"
# その full 40-char hash。cache_key backward-compat golden は full hash で計算された
# ため、pin 前進 (D38) 後もこの固定値で導出安定性を pin 非依存に検証する (裁定12)。
# 注: 歴史的 driver は 7-char KICKOFF_PIN を ccbench_commit に渡すため cache_key は
# golden と別値になる (full/short 表現の既存不整合。段 3 とは独立の潜在課題)。
KICKOFF_PIN_FULL = "dff0f1ef2a4b84746f6463839e85b24301f4b16d"
