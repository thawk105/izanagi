# 段 6 裁定 — レビュー所見と fix1 の対応表 (2026-09-20 13:40 JST、親)

review A (`codex/s6-review-A.md`) / B (`codex/s6-review-B.md`) はともに **must-fix 1 = 同一 (MF1)**、受理集合の逸脱・I3 の緩和・非認証 lane の変更は発見なし。

| 所見 | real/refuted | 採否 | 状態 | 対応・根拠 |
|---|---|---|---|---|
| MF1 (A/B) spawn-site 台帳の driver sink lineno 7428 が古い | real (親の焦点走 12491 で赤) | 採用 | **closed** | fix1 が 2 箇所を 7545 へ更新 (`grep -n "summary = run_campaign("` = 7295 / 7545、後者が `run_measurement` 内。親が現物で確認)。焦点走 12519 (commit 886c19259) で `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink` の緑を確認する |
| 焦点走 12491 赤 2 `test_existing_a1_non_touch_manifest_is_empty_from_base` | real (未 commit 差分の作業木検査) | — | **closed** | commit 886c19259 で作業木 clean。焦点走 12519 で緑を確認する |
| A-S1 追補の record 仕様と拒否範囲が実装と不一致 | real | 採用 | **closed** (親 docs) | digest は自身の field を除く、先行 attempt 名は定数だけが持つ、拒否は「同 study の先行 bench 到達を解除できない」に限定、別 study の正常な先行証拠は拒否理由でない、初回投入は record 不在でも通る、完全性検査は「認可成功を理由に省略しない」に是正 |
| A-S2 / B M14 の固定値 | real | 採用 | **closed** | spec で `"b" * 40`、配線負例 `[source]` に対応 |
| A-N1 §6.4 追補の見出し | real (nit) | 採用 | **closed** | 「将来の attempt-0002 一件に対する例外の追加」に改題 |
| B-N1 digest helper の重複形式検査 | real (nit) | 採用 | **closed** | fix1 が helper を除去 + canonical hash だけに縮小。reader の形式検査 (M8 anchor) は不変 |
| B-N2 malformed `duplicate` case の過剰決定 | real (nit) | 採用 | **closed** | fix1 が digest 済み正常 JSON に同値の重複 key を挿入する case へ |
| A 被覆限界 `item-bool` | real (nit) | 採用 | **closed** | fix1 が `item-float` (2.0) へ |
| B-N3 producer namespace `[record]` と `is_create_only` の重複 | real (nit) | 不採用 (残す) | — | 段 4 の parametrize 指定どおり。検出力を足さないが受理集合も変えない |
| B-N4 dogfood log の証明範囲 | real (nit) | 採用 (記録) | **closed** | insight に複製手順 (`make_replica_base.py`: path 書換・intent digest 再計算・bench-go の ready sha 再計算) と「gate 単体の受理 / 拒否であり qsub 到達・materialize 全工程の証明ではない」を書く |
| A 被覆限界: study differs 各分岐の個別実証なし、`duplicate` の検出力 | real (nit) | 記録 | — | diff による保存確認 (2805 / 2848 / 2898 行相当は無条件のまま) を insight に書く |

焦点再レビュー子 (DW-S06-C) は起動しない: must-fix は機械的な lineno 追随 1 件で、その閉じは焦点走 12519 の緑で実測する。残りは nit と docs の文言。
