# [T-2797] 段 6 裁定 — レビュー A / B (2026-09-21 21:1x JST、統合 commit b5935b88e)

入力: `codex/s6-review-A.md` (NO-GO、must-fix 3)、`codex/s6-review-B.md` (NO-GO、must-fix 3 / should 2)、焦点走 f1 (`focus-f1.log`、3 failed / 4,747 passed / 20 skipped)。
両レビューとも「Tier0 が verify / anomaly reject / bench を迂回する経路」「smoke 数値の性能値・event・handshake への流入」は無いと確認 (A 末尾の照合、B の削除表)。

| # | 所見 | 判定 | 裁定 | fix |
|---|---|---|---|---|
| F1 (A1 / B1) | 実挿入点の順序・perf binary・拒否 (rc 3・submission なし・digest なし)・例外伝播の検査が `test_live_*` (receipt 無しで skip) にしかない。M2 / M3 / M9 / M10 の通常 kill 先が無い | real・must-fix | 通常走で動く挿入点 test を所有内 (`test_b5_tier0.py`) に置く。差し替えてよいのは CCBench の build (`buildcache.build_v2` / `buildcache.build`) と source evidence・admission の準備 (`_b5_tier0_build_inputs`) だけ。Tier0 の配線・`_run_b5_tier0_smoke`・`run_once`・既存パーサ・`_write_b5_sidecar`・`drive_iteration` の早期 return・CLI の rc 3 は実物を通す。build の `RuntimeError` / `SubprocessError` が `build-error` sidecar と rc 3 に至る正例も通常走で置く。live test は親の生死確認用として残してよい (通常 kill 先には数えない) | fix1 |
| F2 (A2 / B2) | 既存 `test_p3_s4_loop.py` の B-5 seam 2 件が Tier0 の準備段で落ちる (consumer 取り残し) | real・must-fix | 所有外 `test_p3_s4_loop.py` の共通 fixture (`_b5_candidate_fixture` 付近) 1 箇所で Tier0 の準備・build・smoke を提供し、両 test の期待値は変えない。本番に「偽 checkout なら Tier0 を飛ばす」分岐を入れない。**同 file は T-2632 の所有予定 (子 A) なので T-2632 の land 後の main を取り込んでから当てる** | fix2 (T-2632 land 後) |
| F3 (A3 / B3) | 新規 `test_b5_tier0.py` に自走入口が無い (`test_plain_runner_coverage` 赤) | real・must-fix | 隣接 test と同じ `if __name__ == "__main__":` の pytest 自走入口を足す | fix1 |
| F4 (B4) | Tier0 前の `require_certified_writer_authorization` 追加呼出しは裁定に無い追加の関門 | real・採用 (削除) | 削除する。後続 pipeline の既存認可はそのまま。Tier0 は certified 記録を書かない | fix1 |
| F5 (B5) | `_b5_tier0_build_inputs` の ReviewReceipt 分岐は B-5 に不要 | real・採用 (削除) | GeneratorReceipt と None と不正型の拒否は残し、ReviewReceipt の import・分岐を削る (B-5 の capability は machine = GeneratorReceipt、LLM = None) | fix1 |
| B nit | `[sweep-matched]` / `[applies_to]` の重複 param、smoke test の gateway 重複 assert | nit | 採らない (削っても成果物は変わらない) | — |
| A 補足 | 後続 perf build の cache hit と hash 一致の実証が任意 live test にしか無い | real (実効性の証拠) | 親の生死確認 (s4 §3.5) で実測する | 親 |

## 追補 (21:58 JST) — 変異 probe で判明した F6

| # | 所見 | 判定 | 裁定 | fix |
|---|---|---|---|---|
| F6 (親の変異 probe、DW-M02 / M03) | probe (`mutation-probe-results.json`、main=8469b6d4b、19 件全 SURVIVED 期待) で、**等価変異 M0 (comment 1 行) を含む `p3_s4_loop.py` の全変異が挿入点 test 16 node を落とす**。原因は `main` → `drive_iteration` 入口 → `ident.ensure_resumable_attempts` → `ensure_campaign_identity` の contract-loader-drift (作業木の bytes ≠ HEAD blob、`mutation-probe-m0-stdout.txt`)。M2 / M3 / M9 / M10 / M10b はこの 16 node だけで、kill を変異の内容へ帰属できない | real・must-fix | 挿入点 fixture (`test_b5_tier0.py` の `insertion_case`) で、Tier0 より手前の identity 準備 (`ident.ensure_resumable_attempts`、drive_iteration 入口と `_run_one_iteration_resolved` 内の両方) を差し替え、test が `p3_s4_loop.py` の作業木変化そのものに反応しないようにする。identity / contract-loader 検証の正しさは既存の別 test が担う。修正後に probe を取り直し、M0 が SURVIVED になることを確かめる | fix1d |

## 追補 2 (22:20 JST) — probe2 の結果と M4 の再照準 (erratum、DW-M02)

- probe2 (`mutation-probe2-results.json`、main=051dae5cb = fix1d 統合後): **M0 (等価) SURVIVED・失敗 0 件** → F6 は閉じた。実変異 18 件はすべて固有の node で落ちた
  (M1 17 / M2 16 / M3 5 / M4 15 / M5 3 / M6 1 / M7 1 / M8 5 / M9 6 / M10 6 / M10b 6 / M11 3 / M12 6 / M13 5 / M14 2 / M15 6 / M16 4 / M17 2)。
- **M4 (rr20) は単一理由でない:** rr20 は holdout 保護 ratio で、gateway の保護層が smoke 全体を拒否し smoke 系 test 11 件がまとめて落ちた (固定 argv 検査以外の層が同じ入力を拒否)。
  事前登録の意図 (「smoke の rratio を workload の値にする」) に沿って、保護対象でない workload 値 **rr95 へ再照準**する (`m4-smoke-rratio-95`)。rr20 の結果は保護層の観測として残す (初回結果は消さない)。

## 追補 3 (23:15 JST) — [T-2632] land 後の取り込みで判明した F7

| # | 所見 | 判定 | 裁定 | fix |
|---|---|---|---|---|
| F7 (親の取り込み照合) | [T-2632] が `drive_iteration` に足した base provenance の記録は outcome を閉じた集合 `_PROVENANCE_OUTCOMES` (certified / aborted / rejected / dry-pass / duplicate / duplicate-skip / rejected-preprocess) で検証し、未知 outcome は `ValueError("invalid base provenance outcome")`。取り込み後、B-5 の Tier0 拒否 (`rejected-tier0`) は provenance 記録で子が落ち、driver は `rejected-tier0` (A のみ・継続) でなく分類不能欠測 (系列停止) と判定する | real・must-fix | `_PROVENANCE_OUTCOMES` に `rejected-tier0` を足す (Tier0 拒否は WAL を書かないので `_wal_attempt_provenance` は variant None の既存分岐で wal_refs 空を返す)。[T-2632] の `test_base_provenance_records_b5_early_returns` の parametrize に `rejected-tier0` を足す (ケースの追加、既存期待値は不変)。F2 (seam fixture) と同じ fix2 で、main 取り込みの merge 状態の中で Codex author が行う (自動 merge の結果が両親と異なる実装面になるため、DW-O17) | fix2 |

- **変異 M18 の事前登録 (DW-M01、fix 前):** `p3_s4_loop.py` の `_PROVENANCE_OUTCOMES` から `"rejected-tier0"` を外す → 落ちるべき検査 = `test_p3_s4_loop.py::test_base_provenance_records_b5_early_returns[rejected-tier0]` と
  `test_b5_tier0.py` の拒否 test (`test_insertion_rejection_rc3_no_submission_wal_or_digest`)。
## 追補 4 (23:32 JST) — 焦点再レビュー (`codex/s6-focus.md`、NO-GO・must-fix 1) の裁定

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| F1〜F6 | closed (焦点再レビューの対応表) | — | 閉じた |
| F7 | 実装確認済み、M18 の実測未提示 | real (実測で閉じる) | probe4 (`mutation-probe4-results.json`、main=83732738b) で M0 SURVIVED、M18 は `test_insertion_rejection_rc3_no_submission_wal_or_digest` 6 ケースで落ちる → 閉じた |
| F7 の影響説明 (erratum) | 追補 3 の「driver は分類不能欠測 (系列停止) と判定する」は誤り。driver は rc でなく sidecar で分類するので、`tier0.json` (rejected) の公開後に provenance で子が落ちても `rejected-tier0` (A のみ・継続) と分類する | real・訂正 | F7 の実害は「子が異常終了し (rc 3 でなく例外)、その iteration の provenance と loop state を公開しない」こと。是正 (outcome 集合への追加) は変えない。追補 3 の文は消さず本行で訂正する |
| N1 | 投入済み (pipeline-submitted あり) の `duplicate-skip` を driver が `submitted=False` に戻し B が増えない (D:367、既存 test も B=0 を期待) | real・**scope 外** (Tier0 ではなく D2198 の試走実装の既存挙動) | B-5 は slot ごとに campaign identity が別で、通常運用では duplicate-skip に到達しない。到達しても系列は分類不能欠測で止まり certified 誤採用はない。本 wave では直さず insight に記録し、発効束の段で D2198 / D2200 項 1 (2) 4「重複 skip 拒否と B 消費を維持」の読みと合わせて確認する事項とする (研究前進を止める実測欠陥ではないので裁定パッケージにしない) |
| 親の生死確認 | not-addressed | 既知 (追補外) | 本 wave では実施しない (handoff 記載の理由)。校正 job で live test を走らせる |

- 変異の事前登録 (DW-M01): 新しい変異は足さない。M1〜M17 のうち M1〜M3・M9〜M11 の kill 先を fix1 の通常走 test へ再照準する (実装後に単一理由性を確かめて期待 node を確定)。
- fix の分割 (DW-S06-B): fix1 と fix2 は file 集合が素 (fix1 = 所有 7 file、fix2 = `test_p3_s4_loop.py` のみ)。fix2 は T-2632 land 後。
