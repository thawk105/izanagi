# [T-2854] 単位 11 段 6 裁定 (親) — レビュー 2 本と親の検算の所見、fix 1 巡目の仕様

入力: 実装子 B の報告 `out/s5-author-B.md` (py_compile の `__pycache__` 削除を拒否されて停止。改修は 4 file に入っており login の selftest 184/184。差分全文・弱化の確認は未了で、親が `review/probe-diff-v1.patch.txt` を作ってレビューに渡した)、レビュー A `out/s6-review-A-1.md` (NO-GO)、B `out/s6-review-B-1.md` (GO)、親の selftest `evidence/parent-selftest-1.txt` (rc=0)、anchor 照合 `check_anchors.log` (4 件とも C2' の実 bytes で出現 1 回、RESULT OK)。
fix 前の統合 snapshot: `probe-snapshot-pre-fix1/` (sha256 = `evidence/probe-sha256-v1.txt`)。

## 1. 所見の裁定

| # | 出所 | 所見 | 判定 | 放置時の成果物影響 | 処置 |
|---|---|---|---|---|---|
| F1 | 親の検算 | `mutation_verdict` の H-line が TPC-C consumer を `target.startswith('tpcc_')` で選ぶ。実際の 21 entry (前例 `dev-wave-t2854-mocc-v3-emitter/evidence/compute-1/C1-preprocess.json`) では該当が 12 件 (`tpcc_<p>.cc` 9 件 + silo・si・mocc の `transaction.cc` の `tpcc_<p>.exe` 3 件) で、`nine_tpcc_entries` と `other_12_entries_equal` が必ず偽になる | real、must-fix。レビュー 2 本とも見逃した (selftest の合成 row が実構成を写していない) | H-line が正しく検出しても WRONG_REASON になり C6 が不合格 | fix: TPC-C consumer を source で選ぶ (`cc/<p>/tpcc_<p>.cc`、9 件)。selftest の H-line 合成 row を実際の 21 entry の (source, target) の組にし、旧 filter なら H-line-valid が通らないこと (陰性) を 1 case で持つ |
| F2 | A | probe は 4 OID を形式だけで検査し、裁定済みの値に固定していない | real、must-fix (A の許した最小形で) | 別の整合した系列を渡すと C2' を検査せずに緑 | 親の投入 script `run-compute.sh` で 4 OID を裁定済みの定数と照合し、不一致なら投入しない。probe は変えない |
| F3 | B | C4 が不合格でも集約結果に `result_name = structure+witness+content pass` が残る | real、should | 不合格の成果物に「pass」の表示が残る (合否は `passed` で落ちる) | fix: 両 run が合格したときだけその名、他は `fail` |
| F4 | B | 削った D1/M2 用の `DIAG_MARKER` 計数が残る | real、nit | 判定は不変、記録に不要な値 | fix: 定数と計数を削る (判定に使っていないことを確かめて) |
| F5 | B | selftest の説明文が旧「stage six」 | real、nit | 不変 | fix: 単位 11 の 4 変異を指す説明へ |
| F6 | A | spec の `anchor_status` が provisional のまま | real、nit | 不変 | 親が spec を更新 (anchor 自体は変えない) |
| — | 実装子の変更 | zstd が無いときの gzip fallback を削った | 疑い | zstd が無い node では C4/C5 が ERROR (偽緑ではない、fail-closed) | 採らない (前例 2 走とも zstd で保持、検査の弱化ではない)。記録だけ |
| — | 実装子の変更 | selftest の「verdict の reasons / first_reason が入力と一致」照合を外した | 疑い | H-set の reasons が protocol 別 dict になったための変更。判定値の照合は status で残る | 採らない。F1 の fix で H-set 以外の case にこの照合を戻す (H-set は protocol 別に照合) |

不成立 (A・B): C1 の片木比較・一部 entry 比較、protocol・binary・witness の取り違え、H-set・S-table・M-type の誤 kill、anchor 重複・復元検査の欠落、C0 の祖先・raw diff・tree 照合と R 行 0 件拒否・`clean_env` の弱化、見積りの誤り。

## 2. fix 1 巡目の仕様 (Codex fix、author B の子木、段 5 の実装子契約を全文継承)

- 対象: F1・F3・F4・F5 と、表末尾の「reasons / first_reason の照合を戻す」。
- 編集面は子木の `output/runs/t2854-u11/probe/` の run_probe.py・selftest.py・mutation-spec.template.json だけ (v3check.py は触らない)。
- 既存 selftest case の期待 (KILLED / NOT_ACCEPTED) は変えない。H-line の合成 row の構成を実構成に改めるのは F1 の意味変更として許す。変えた case は全件列挙する。
- 受理集合の変更は F1 (H-line の選び方) と F3 (結果名) だけ。
- 自己確認: `python3 -B selftest.py` の rc と件数。py_compile は `-B` 相当で `__pycache__` を作らない形で (作ってしまったら削除を試みず、そのまま報告する)。

## 3. kill 条件 (段 4 裁定 §3 のまま、F1 で H-line の consumer 選択だけ明確化)

- H-line: `cc/<p>/tpcc_<p>.cc` の 9 entry の完全展開が全件不一致、他 12 entry は両 mode とも一致、include 活性は 21 / 21 一致、entry は重複なく 21 件。
