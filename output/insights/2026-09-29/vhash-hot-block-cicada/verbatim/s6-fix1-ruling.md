# 段 6 fix 裁定 1 — md_23 (review-a-1.md・review-b-1.md に対して)

2026-09-30 00:40 JST / 親。対象 tip 297ad1dee。

| 所見 | 判定 | 採否 | 裁定 |
|---|---|---|---|
| B1 manifest の sort_keys で patch 適用順が名前順 (broken→variant→instr) に崩れる (driver:72, 324, 828) | real (親が実物で確認) | 採用・must-fix | build spec の patch を**順序付き配列**で manifest に保存し、適用はその配列の順だけに従う。hash は別 field で照合専用。順序を検査する test を足す |
| A1 / B2 巡回 0 の verdict に serializable を受け入れよ | **refuted** | 不採用 | driver は `--protocol cicada --ccbench-root` を付けて判定器を呼ぶ (driver:516-518)。Cicada は証拠面 (X/P/I) が無く、巡回 0 は indeterminate (rc 3) が上限 (md_3 README §1 項 5・実測表は全件 indeterminate)。serializable が返るのは証拠面評価が効いていない = 呼び方の異常なので、**fail-closed のまま**にする。ただし test の合成 trace が `rc=0, verdict=indeterminate` という実物に無い組を使っているので、実物の契約 (巡回 0 → rc 3・indeterminate、巡回 → rc 1・non-serializable) に置き換え、serializable が来たら拒否する test を足す |
| A2 / B3 COUNT の extime が 1 秒 (driver:374) | real | 採用・must-fix | COUNT は perf と同じ extime 3。extime 1 は trace / broken だけ |
| A3 / B5 見積りで smoke の build を二重計上 (driver:181, 833-840) | real | 採用・must-fix | 裁定 §4 の式に揃える: 合計 = smoke job の wall (build 込み、1 回) + 3 × (120 × smoke の perf 1 run の最大 wall + 60) + count (20 × smoke の perf 1 run の最大 wall + 60) + 2 × (trace 走数 × smoke の trace 1 走 wall)。build を別に足さない。境界例 (7,199 / 7,200) の test |
| B4 共有できないと各 job が 17 binary を黙って再 build | real | 採用・must-fix | 共有 binary が使えない (sha256・ldd の照合に失敗) job は**再 build せず停止** (fail-closed)。smoke は共有可否を記録し、estimate は共有不可なら `stop` を返す |
| A4 B1 は元の選択版が ABORTED でも changed を記録しうる (broken-cicada-vhash-stale-hot.patch:48) | real | 採用・should | 元の選択版が確定 (committed) かつ非削除で、返す版と異なるときだけ changed / committed の事象にする |
| A5 COUNT の worker 配列が cache line に揃っていない (variant patch:100, 138) | real | 採用・should | VHashStats を alignas(64) にし stride を 64 の倍数にする (COUNT build だけ。性能 build の bytes は不変であること) |
| B6 図が平均と 95% t 区間 (plot:59-78) | real | 採用・must-fix | 裁定 §2.3 どおり、全点・中央値・最小〜最大を描き、有意を述べない |
| B7 patches/README.md:930 の「壊し 3 本」の重ね方の文 | real (nit) | 採用 | 既存文の対象が md_3 の旧 3 本であると明記 (意味を変えない) |
| 親の控え (Install が先頭から探し直す) | 両レビューで反例不成立 | — | 一次資料の設計節に「hot lock の下で列が動かないので挿入位置は stock と同じ」と書く |

## 親の焦点走で出た赤 (focus-1.log、tip 297ad1dee、1800 passed / 2 failed)
| 赤 | 帰属 | 裁定 |
|---|---|---|
| test_condition_meaning_gate.py::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches (BACKOFF_REQUESTED_US の照合がずれる) | 本 wave (U3 が `if macro in ("IZANAGI_CICADA_VLIFE", "IZANAGI_CICADA_LONGTX")` を `if macro in G._CONDITIONAL_BRANCH_COMPANION_SITES` へ一般化し、BACKOFF_REQUESTED_US が専用分岐の前に一般分岐へ入った) | 一般化をやめ、4 箇所とも明示の tuple (`IZANAGI_CICADA_VLIFE`, `IZANAGI_CICADA_LONGTX`, `CICADA_VHASH_K`, `CICADA_VHASH_COUNT`, `CICADA_VHASH_WL`) に戻す。既存 macro の扱いを変えない |
| test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact (unreviewed: vhash_cicada_hot_block.py) | 本 wave (U3 が「不要」と誤判断) | `_REVIEWED_PERF_FILES` に新 driver を先例 (tools/vhash_cicada_tuning/driver.py 等) と同じ形で登録 |

## 変異の追加登録 (DW-M01、fix 前)
- M7: manifest の patch 配列の順序を無視して名前順に適用する → 順序 test が赤。
- M8: COUNT の extime を 1 に戻す → argv test が赤。
- M9: 共有 binary の照合失敗で再 build に落ちる → fail-closed test が赤。
- (M1〜M6 は s4-ruling.md §5 のとおり。anchor は fix 後の tip で確定し、単一理由性を確認できないものは登録しない)

## fix 単位 (所有は素集合、並列)
- F1 (作業木 vhb-u1、branch dev-wave-vhb-f1): patches/cicada-vhash-hot-block-variant.patch (A5 のみ)、patches/broken-cicada-vhash-stale-hot.patch (A4)、patches/README.md (B7)、orchestrator/tests/test_condition_meaning_gate.py と orchestrator/tests/test_official_perf_closure.py (焦点走の赤 2 件)。
- F2 (Python、作業木 vhb-u2、branch dev-wave-vhb-f2): orchestrator/campaign/vhash_cicada_hot_block.py、orchestrator/tests/test_vhash_cicada_hot_block.py、tools/plotting/plot_vhash_cicada_hot_block.py (B1・A1 の test・A2・A3・B4・B6)。
