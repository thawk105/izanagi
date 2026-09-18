# 段 4 裁定 — [T-1170] (2026-09-18、親)

## 所見の裁定

| 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|
| B MF1 / A nit1 | 変異 M1〜M3 は「比較右辺を `_producer_module().SCHEMA_VERSION` へ戻す」退行を検出しない (双方 v4) | real | 採用 (scope 内 = 本題の依存そのものの回帰検査)。独立性 test を追加し、変異 M4 を登録 |
| plan F2 訂正 | 現行 run-start は seq/ts 込みで非 binding 16 key / binding 23 key。「新形 20 key」は不正確 | real | 採用 (brief 訂正) |
| plan/A F3 訂正 | 「版を直接照合する箇所は 1 つ」に限定。間接 consumer の不在は主張しない | real | 採用 |
| plan/A/B F5 訂正 | 「読み手 0 件」は「確認できた読み手なし (直接参照の検索)」に限定 | real | 採用 |
| plan/A/B P1 訂正 | D1851 は「形を変えない bump の禁止」ではない。v5 不要の根拠は「v4 が既に v3 と現行出力を分け、新たな形変更がない」。T-304 が T-1170 を完了したとは記録しない | real | 採用 |
| plan/A/B P5 訂正 | 直接の原因は consumer が producer の生きた定数を受理条件に使うこと。共有定数は波及要因 | real | 採用 |
| A nit2 | 「構造化」は例外文言内の明示であり、機械可読属性の追加ではない。成果報告で「構造化データを追加」と書かない | real | 採用 (記録の書き方) |
| A nit3 / B nit3 | 世代診断は版 gate に到達した場合の保証 (report 版・journal hash・順序が先行) | real | 採用 (記録に限定を書く) |
| B nit4 | docs は worklog fragment + F332 追記で足りる。decisions fragment 不要 | 一部採用 | 親判断: consumer 所有の run-start 版定数は consumer 契約 (interface) の変更で、D1898 の版上げが 4c6f03048 で実体化した事実も未記録のため、短い decisions fragment を書く (routing 2) |
| A 変異所見 | kill node は代表例で完全集合ではない。M1 の旧形検出は「拒否理由が別 gate に移った」検出 | real | 採用: probe 走で完全集合を実測して登録、台帳に区別を書く |
| plan M0 | docstring 変異は `__doc__` が変わるので非等価。comment 変異へ | real | 採用 |

## plan v2 (確定)

- 実装 (author 1 本、所有 = `orchestrator/campaign/autonomous_trial_completeness.py`、`orchestrator/tests/test_autonomous_trial_completeness.py`):
  1. `C:427` `_ROLE_SCHEMA_VERSION` の直後に `_RUN_START_SCHEMA_VERSION = "p3-autonomous-workload-trial/v4"` (独立リテラル、producer / role 定数を参照しない、1 行 comment 付き)。
  2. `C:2240-2241` を plan の具体案 (recorded / generation=legacy|unknown / consumer_supported を名指す `_fail`) へ置換。legacy は実在を確認した v3 の文字列だけ。版番号の大小解釈はしない。report 版検査 (2238-2239) は触らない。
  3. test: 既存 2 node の run-start 側期待文言更新 (report 側は据え置き)、新規 4 node:
     (a) v4・binding 無しの明示正例 (無条件 3 field の実在と binding 7 field の不在を assert してから `_verify`)、
     (b) v3・旧形 13 key (実在 artifact の key 形を合成) → legacy 全文、
     (c) v99・現行形 → unknown 全文、
     (d) 独立性: `monkeypatch.setattr(A, "SCHEMA_VERSION", <別文字列>)` の下で v4 fixture が通り、その別文字列を版に持つ run-start は unknown で拒否される。
     全文期待は `pytest.raises(...) as exc` + `str(exc.value) ==` の独立リテラル。
- 受理集合: v4 のみで不変。v4 の形は既存 gate が従来どおり検査 (exact-key 契約の新設なし)。
- docs (親): worklog fragment、failures F332 副次的所見への恒久対応追記、decisions fragment (短)。

## 変異事前登録 (期待 node は probe 走で完全集合を実測してから spec に固定)

| ID | category | 変異 | 期待 |
|---|---|---|---|
| M1 | negative | run-start 版検査 block 全体を削除 (report 版検査は残す) | KILLED |
| M2 | negative | `_RUN_START_SCHEMA_VERSION` の値を v3 に変更 | KILLED |
| M3 | negative | legacy / unknown の割当てを交換 | KILLED |
| M4 | negative | 比較右辺を `_producer_module().SCHEMA_VERSION` へ戻す (定数は残す) | KILLED (独立性 test が kill) |
| M0 | positive | 新定数の comment の句点だけ変更 | SURVIVED |

runner: `orchestrator/tests/test_autonomous_trial_completeness.py` + `orchestrator/tests/test_p3_autonomous_workload_trial.py` (統合正例を含む) を dispatch で。
台帳には「M1 の旧形 v3 node は拒否理由が別 gate へ移ることの検出」「M2 は複数の診断期待が同時に壊れる」を書く。

## 焦点走 (親、統合後)
plan の 8 本 + 間接 5 本 + `test_reflux_originless_compatibility.py` = 14 file。受入全走は最終 tip で dispatch。
