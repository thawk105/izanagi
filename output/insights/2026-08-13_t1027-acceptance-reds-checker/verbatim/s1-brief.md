# 段 1 brief — [T-1027] 非帰属 checker を実運用へ到達させる

- wave: `dev-wave-t1027-acceptance-reds-checker`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker`
- branch: `worktree-dev-wave-t1027-acceptance-reds-checker` (base = local main `a3168d85`)
- 起票: 2026-08-13 08:30 JST

## scope

`tools/check_acceptance_reds.py` が実 repo の受入 log に対し
`rc=2 (logged pytest nodeid has no exact collected selector)` で止まる P1 バグを直し、
実運用に到達させる。**編集面は `tools/check_acceptance_reds.py` と
`orchestrator/tests/test_check_acceptance_reds.py` に限る。**

## 確定済みユーザー裁定 (前提・変更不可)

- 裁定控え `2026-08-13-rulings9-29rulings.md` #1: 受入 receipt 問題は
  **(b) の変形 = checker 統合**。批准既知赤 registry は作らない。receipt 条件を
  「rc=0 または非帰属 checker 緑」へ拡張する。**[T-1027] の修正を先行させる。**
- 同 #16 = [T-1028] **採用**: gate を新設する wave の完了条件に
  **「親が実データで 1 回通す」** を入れる。本 wave の完了条件に必ず含める。
- 同 #9 = [T-1019] waiter の receipt へ log hash 束縛 —— **本 wave の scope 外**
  (t907-t908-t910 回収 wave の担当)。receipt 条件の拡張 (`tools/dev_wave_land.py` /
  `tools/dev_wave_wait.py`) も **本 wave では触らない**。

## 親の実測 (2026-08-13 08:19–08:23 JST、上記 worktree、dispatch 経由)

一次資料は本 job dir の `evidence-*.txt` / `evidence-redcheck.log`。

1. **失敗した実 reference** (`evidence-redcheck.log`、known-red-octopus wave の実走):
   `orchestrator/tests/test_codex_worker_launch.py::test_parallel_jobs_preserve_both_manifest_entries`
2. **根本原因 = dispatch relay の stdout 打ち切り。**
   `tools/pegasus/dispatch_compute.py:34` `DEFAULT_SUCCESS_RELAY_LIMIT_BYTES = 4 * 1024`。
   child rc=0 の成功走では relay が末尾 4 KiB しか親へ流さない。
   当該 file の `--collect-only -q` 出力は 12,098 bytes あり、実測 relay 行は
   `child stdout begin (size=12098 bytes, omitted_bytes=8002)`。
   `114 tests collected` に対し親へ届いた nodeid は約 40 件だけで、
   **先頭 payload 行は途中で切れた nodeid 片** (`| _docs_authority_alone_rejects_...`)。
   `_default_collection_runner` はこの部分集合を完全な collection として扱い、
   `_selector_from_collection` が exact match を見つけられず rc=2 になる。
3. **完全な出力は disk に残っている** (`evidence-collect-truncated.txt` の receipt 行が指す先)。
   `output/pegasus-dispatch/<hash>/receipt.json` の
   `scheduler_logs.stdout` = `{"path": "<...>.o<jobid>", "size": 12098,
   "omitted_bytes": 0, "tail": "<全文 12,098 chars>"}`。
   欠けていた nodeid はこの `tail` に **存在する** (親が実測)。`DW-O13` の入力実在確認は
   この実 receipt に対して済み。
4. **依頼が挙げたもう一方の原因候補 (xdist group suffix) は refuted。**
   t907-t908-t910 wave の実 acceptance log の赤
   `...::test_candidate_freeze_matches_contract_and_generation_chain@s8c-preregistration-candidate`
   を実 collect 出力と突き合わせたところ、`_selector_from_collection` は
   **正しく match した** (`evidence-collect-small.txt`、8 nodeid、`omitted_bytes` なし)。
   `| ` 行前置の除去 (`_payload_line`) も正しく動いている。
   **打ち切りは出力が relay 上限を超える file でだけ起きる** —— 小さい file では再現しない。
5. **relay 上限を上げる調整弁は存在しない。** `dispatch_compute.py` に relay limit の
   CLI flag も環境変数も無い (定数 2 個のみ)。`tools/pegasus/` は本 wave の scope 外でもある。

## 不変条件 (緩めてはならない)

- **規律 2。** 検査を通すために期待値を書き換えず、production を fail-open にしない。
  **打ち切られた/完全性を確認できない collection から `attributable` を出してはならない。**
  判定不能は rc=2 のまま止まるのが正しい。「match しなかったから非帰属」も禁止。
- 既存テストの期待値を変更しない。赤なら実装側が誤りとする。
- scope 外 (`dev_wave_land.py`、`dev_wave_wait.py`、`tools/pegasus/**`) を編集しない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 完全な collect 出力は dispatch receipt から取る。**
  relay された stdout を collection の権威にせず、relay 行が告知する `receipt.json` を読み、
  `scheduler_logs.stdout.omitted_bytes == 0` を必須にしたうえで `tail` から nodeid を導く。
  receipt を特定できない・`omitted_bytes > 0` なら fail-closed。
- **(P2) 完全性 gate を別に張る。** pytest の `N tests collected` footer と、
  path に match した nodeid 件数を突き合わせ、不一致なら fail-closed。
  P1 が効いていても残す —— 黙って部分的な collection が match を生む経路を
  構造的に閉じるのが目的 (規律 2)。
- **(P3) 打ち切りを検出したときの診断を分ける。** 「exact selector が無い」ではなく
  「collection が打ち切られている」と述べる。現状のメッセージは原因を誤導し、
  実際 3 時間分の誤診を生んだ。

P1〜P3 はいずれも親の暫定判断であり、段 3 の攻撃対象である。
特に P1 は `check_acceptance_reds.py` を dispatch receipt の schema へ結合させる —
この結合が正当か、より疎な seam があるかは争点。

## 成果物影響 (DW-G05)

直さなければ非帰属 checker は rc=2 のまま実運用に到達せず、裁定 #1 が定めた
receipt 条件「rc=0 または非帰属 checker 緑」を t907-t908-t910 wave が実装できない。
その結果 **main に既知赤があるあいだ全 wave が land できない構造** が残る
(`2026-08-13-acceptance-receipt-vs-known-red.md` が実証した停止)。
直せば、既知赤の非帰属を機械が判定でき、land 経路が既知赤で全滅しなくなる。

## 完了条件

1. 上記バグが直り、変異 matrix で新検査の発火が裏取りされている。
2. **親が実データで 1 回通す** ([T-1028])。具体的には
   `known-red-octopus/acceptance.log` (打ち切りを踏んだ当の log) に対し checker を実走し、
   rc と status を worklog へ記録する。t907 の acceptance log も可能なら通す。
   **子の静的レビューや単体テストの緑では代替しない** —— 前 wave では
   静的レビュー 2 本が実環境欠陥を 1 件も出せず、親の実走で 3 件出た。
3. 受入全走、`tools/check_docs.py`、記録、land。

## 分割方針

編集面が 1 file + 1 test file と小さいため、段 5 は Codex 実装子 1 単位。
段 3 の敵対相談は 2 レンズ並列。
