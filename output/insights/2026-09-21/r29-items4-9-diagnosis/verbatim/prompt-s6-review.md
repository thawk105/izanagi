単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 検査対象 1 (insight、commit 64b148b21): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis/output/insights/2026-09-21/r29-items4-9-diagnosis/README.md
- 検査対象 2 (worklog fragment): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis/docs/spool/worklog/2026-09-21-dev-wave-r29-items4-9-diagnosis-1.md
- 逐語の写し (同 insight の verbatim/): brief.md、parent-notes.md、s2-plan.md、s3-consult.md、s4-ruling.md、origin-rulings-full29.md、rulings29-consult-a-out.md、contract/ の 7 file、
  measure/ の S01〜S10 の log・chain.log・table.md・compute-visible/*.json、NORMALIZATION.md、scripts.sha256
- 計測 log の原本 (正規化前): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/measure/ (S*.log、chain.log、run-measure.sh)
- 前回診断 (repo 内): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis/output/insights/2026-09-21/focus-run-count-diagnosis/README.md と同 dir の verbatim/focus_runs_table.md、verbatim/changed_files.txt
- 項 9 の一次資料: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/acceptance-child-final-1.log、/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/acceptance-child-final-1.log、
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/focus/run-focus.sh
- 台帳 (worktree、read-only): docs/decisions.md の D325・D2194 (項 8)・D2206、docs/worklog.md の [T-2842]・[T-2843]・[T-2832]・[T-2820] の本文
- コード (worktree、read-only。README の file:line は起点 d99c556df の値と明記されているが、現 HEAD の差分は docs のみなので同じ行を指すはず): tools/run_tests.py、
  tools/pegasus/dispatch_compute.py、orchestrator/campaign/site_policy.py、orchestrator/campaign/login_headroom.py、tools/update_acceptance_duration_ledger.py、conftest.py、
  tools/check_docs.py、orchestrator/tests/test_check_docs.py、orchestrator/tests/acceptance_duration_ledger.json

## 前置き — この依頼の性質

自分たちの開発運用手順 (dev-wave) の診断記録のレビューである。実装はしない。セキュリティでも攻撃でもなく、外部入力も扱わない。
書込可能 tmp が無いので静的検査でよい — テスト・計算ノード job の実測は親が行う。git の読み取り (`git show`、`git log`、`git grep`) は使ってよい。
**README と fragment を守らずに点検すること。** 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

# 依頼 — レンズ A (一次資料との一致・派生値の検算) と レンズ B (過剰・削除・言い過ぎ) を 1 本で

所見ごとに **real / refuted / 判定不能** と、real なら **must-fix / should / nit**、根拠 (file:line または log の行)、「放置時に再提示の何がどう変わるか」を 1 行で書け。

1. **§4 の表と派生値。** S01〜S10 の 4 区間 (投入前 / 待ち / RUN / collection)、wall、pytest 集計、rc を log の start / end 行と NQSV footer (Created / Started / Ended) から再計算し、
   表と一致するか。node 名を compute-visible/*.json と request 番号で照合。派生値 (単独 7 本の wall 1,336 = RUN 128 + 固定費 1,208、投入前 9 + 待ち 1,107 + collection 92、
   S07 の 1,066 = 88 %、他 6 本 142 秒 = 1 本 18〜26 秒、pytest 合計 120.42、差 7.6、chain 2,887 秒 = 10 本の wall の和、10 本中 8 本が 7〜20 秒、長待ち 2 本の時刻、
   S09 − S10 = RUN +13 / pytest +11.58 / +78 passed / +2 skipped、S01 − S10 = 27 秒) をすべて検算せよ。行末空白の正規化 (NORMALIZATION.md) が原本と整合するか (sha256・bytes の抜き取り)。
2. **§2 の上下限。** 集合走 job 数 (t2803 = 4、t2344 = 3 など) と k・s を前回 verbatim から再導出し、置換上限 10 / 残件 10〜20 を検算せよ。式 (min(k − s, 集合走 − 1)、max(0, (k − s) − (集合走 − 1))) の前提
   (1 job = 1 invocation、集合走を最低 1 本残す) が README に明示され、「証明していない」の限定が十分か。held job を置換対象に数えることの書き方。
3. **§3 と §5 の引用。** file:line・関数名・数値 (36 file、8 file、130 file、13,519 秒、74.8 %、47 entry、224.5 秒、74 node、git grep の hit 0、受入赤 5 node と集計行) を一次資料で照合せよ。
   plan 由来の記述を親が検証せず断定していないか (特に `conftest.py:1936–1948`、`login_headroom.py` の 4 GiB / 1 GiB、`check_docs.py:618–628`、`update_acceptance_duration_ledger.py:124–143`)。
4. **§0・§6 の結論と推奨。** 1 試行の値から言い過ぎていないか (「88 %」「長い待ちの帯」「17 分半」「前回と同じ帯」の書き方、R2 を「今は実装しない」とする根拠の強さ、M3 の費用欄)。
   推奨の蹴った帰結・再提示の目安が、新しい台帳・gate を作らない依頼の制約と両立するか。L / G の制約の書き方は事実 (`/tmp/.git` の現存、generic の env・receipt) と一致するか。
   項 9 の「新しい択は不要、既裁定 [T-2820] の実装で覆える」は D2194 項 8 の文面 (発火条件・対象 2 file) と一致するか。
5. **fragment。** [T-2843] の `完了` (remaining: none) は、依頼 ([T-2843] の本文) の完了条件を満たすか。[T-2842] の `更新` 本文は insight と数値・表現が一致するか。
   title・本文の数値の一貫性。worklog に git に入り得ない情報だけを書く規約 (`docs/worklog.md` 冒頭) に反する重複が無いか。
6. **過剰・削除。** 依頼 (項 4 の 3 点、項 9 の 2 点) を超える記述、逆に取りこぼし、仮想リスク向けの gate・検査・台帳・一般化の提案が紛れていないか。

## 出力形式
- `## 所見` (番号、real/refuted/判定不能、must-fix/should/nit、根拠、放置時の影響 1 行)、`## 派生値の検算表` (値、README の値、再計算値、一致/不一致)、`## 訂正案` (箇所と訂正文)、
  `## 判定` (GO / NO-GO)、`## 総括` (必須)。
