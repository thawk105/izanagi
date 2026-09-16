# 段 1 brief — [T-2640] 未記帳の到達不能 commit 30 件を記帳し、救出か喪失受容かを判断する

## 研究前進

土台。止めている研究は `/cleanup-branches` の掃除判断である。`docs/unreachable-object-ledger.md` は
entry 0 件のまま監査が未記帳 commit を 30 件報告し続け、`ledger_notification_due` が毎回立つ。
常時 due の通知は判断材料として機能せず、無視する習慣を作る。最小差分は台帳へ 30 entry を記帳し、
各件を解決 status まで進めること。**完了判定:** `python3 tools/check_branch_rescue.py --ledger-check`
が rc=0 かつ `decision_inputs.ledger_notification_due=false` を返す。

## 確定済みユーザー裁定

`docs/decisions.md` D2044 項 7 (2026-09-16)。逐語: 「未記帳の到達不能 commit 30 件を既存 schema で
記帳し、救出または喪失受容を具体的に判断する。台帳契約は変えない。」理由文は起草の
「既知良性の類型を記帳なしで認める契約へ変える」を相談が反証したと述べ、「台帳には人間の明示的な
喪失受容を記録する仕組みが既にあり、entry 0 件は既存策をまだ使っていない証拠」と書く。

## 本 wave で取った一次資料 (すべて実測。docs は根拠にしない)

1. **未記帳 30 件。** `python3 tools/audit_dangling_commits.py` 単独 = rc 1、`elapsed_seconds=85.194`、
   「要確認の到達不能変更 30 commit」、finding_pairs 53。`check_branch_rescue.py --ledger-check` =
   rc 3、`entry_count 0`、`unledgered_commits` 30、`audit.complete true`、
   `audit.report_sha256 b7202e6f16e2ec3acd7d5fbaedd62999ef3f4e66a40f5ea826a108d6ed767e71`、
   通知 30 件すべて `unledgered-audit-finding`、`issues` 0 件。**2 経路の OID 集合は完全一致。**
2. **全 30 は `object_type=commit`。** 26 が packed、4 が loose (2026-09-09 の 4 件)。
3. **`check_branch_landed.py` は本 repo で必ず `indeterminate` を返す。** 4 件で確認。reason は
   `assessment-timeout`、issue は `git command timed out: log`。原因は CLI から変えられない固定値
   `COMMAND_TIMEOUT_SECONDS = 5.0` (`tools/check_branch_landed.py:38`)。`--timeout-seconds 300` を
   渡しても 9.7 秒で倒れる。**この wave は判定器を直さない (scope 外)。**
4. **53 path のうち 37 path は main に blob sha1 完全一致で残っている。** main は insight を
   `output/insights/<日付>_<task>/` から `output/insights/<日付>/<task>/` へ再編し、さらに
   `[T-201] output/insights/ の tracked bytes を gzip 圧縮で削減した` (`114c5c4dfc8e`) で `.gz` 化した。
   path 一致では不在に見えるが、basename と gunzip 後の blob sha1 で照合すると一致する。
   残り 16 path は main のどこにも同一内容が無い。
5. **commit 単位では 16 件が全 path 保全、14 件が未保全を含む。**
6. **gc 実測:** git 2.34.1、`gc.auto` 未設定 → 実効 6700、`gc_auto_sample_threshold` = 27、
   fanout `17` の loose 実測 18、`gc.pruneExpire` 未設定 → 実効 2 週間。8〜9 月の object は既に
   期限超過なので `loss_possible_not_before` は `max(now, mtime+2週)` = 評価時刻。
   **`pending` は休止状態にならない。**
7. **pin 閉包 (`DW-O09`)。** 台帳を pin するのは `orchestrator/tests/test_branch_rescue_ledger.py` と
   `orchestrator/tests/test_check_branch_rescue.py`。前者は schema 表の field 順、解決 field 契約の
   散文、stale 通知契約の散文、schema 名と retention 主張の逐語、覆わない範囲の 3 項目を pin する。
   **entry 件数・`## entry` 節本文・全文 sha256 を pin するものは無い。** `tools/check_docs.py` の
   byte / 最長行予算に本台帳は登録されていない。

## 不変条件 (破ったら停止)

1. 台帳契約 (26 field、状態遷移、rc 表、rescue gate 運用契約、覆わない範囲) の逐語を 1 bit も変えない。
   追記は `## entry` 節への `- {JSON}` 行だけ。`現在、記録済み entry はない。` の行の扱いも
   契約変更に当たらない範囲に留める。
2. 規律 2 を緩めない。判定を甘くして通す変更をしない。
3. gate・検査・台帳・一般化を新設しない (依頼の明示。`DW-G05`)。
4. `assessment_verdict` は実測どおり `indeterminate` を書く。保全の証拠は `resolution_note` へ書き、
   verdict を `landed` と詐称しない。`assessment_report_sha256` は当該 OID に対する
   `check_branch_landed.py` の stdout の sha256 とする (実装 `_landed_assessment` と同じ定義)。
5. 救出する場合は ref を作り、**その ref から到達可能であることを再検査してから** `rescued` にする。
6. 素性の信頼できない作業物 (到達不能 commit の中身) は救出・取り込み前に内容を監査する (規律 6)。
   本 wave は repo へ内容を取り込まない。ref を作るだけで working tree へは展開しない。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) `accepted-loss` を AI が設定してよいか。** 台帳は「人間が喪失を明示的に受容した場合」と
  定める。一方 D2044 項 7 は AI に「具体的に判断する」ことを命じ、理由文で既存の喪失受容機構を
  使えと述べる。**親の裁定: D2044 項 7 を当該 30 件についての人間の受容授権と読む。** ただし
  受容は「内容が main に完全一致で保全されている」ことを示せた件に限る。
- **(P2) 未保全 14 件の扱い。** **親の裁定: 救出 ref を作り `rescued` にする。** ref は
  `refs/rescue/t2640/<40 桁 oid>`。攻撃対象 — ref 名前空間の妥当性、恒久 ref を 14 本増やすこと、
  14 件のうち 5 件が同一 file `docs/handoff/2026-08-21-rulings-calibration-main-land.md` で、
  handoff は設計上「正常終了時に worklog へ吸収して削除する」ものであること。
- **(P3) 記帳の生成器を repo へ入れるか。** **親の裁定: 入れない。** job dir に置き、出力と逐語を
  insight へ残す。実装面差分ゼロの docs-only wave とする。攻撃対象 — 再現性を犠牲にしていないか、
  `probe を repo へ入れない` の規律と D95 のどちらが優先か。

## 成果物の形

- `docs/unreachable-object-ledger.md` の `## entry` 節へ 30 行の `- {JSON}`。全件が
  `rescued` または `accepted-loss`。`pending` を残さない。
- 救出 ref (採否は段 4)。
- `output/insights/2026-09-16_t2640-unreachable-ledger/` に一次資料 (監査 stdout、ledger-check JSON、
  内容照合 JSON、子の逐語) と README。
- spool fragment (worklog 1 本、decisions 1 本)。

## 並列分割方針

docs-only。実装面の差分がゼロなので段 5 の Codex 実装子は置かない。`DW-S04` により変異 matrix は
免除、**受入全走は免除しない**。段 2 は plan 1 本、段 3 は異なるレンズ 2 本。
