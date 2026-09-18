単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2772-mocc-mutation-proof-wave1

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (これ自身も検査対象): /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/parent-brief.md
- 段 2 plan (攻撃対象): /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/s2-plan.md
- 設計正本 (T-2757 insight、§6・§7・§12・§13): /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/verbatim/t2757-design-README.md
- 既裁定の逐語: /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/verbatim/D2134.md, D579.md, D1686.md, D1687.md
- mocc の現物 (e9e477ca の cc/mocc/transaction.cc、行番号はこの file のもの): /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/verbatim/mocc-transaction-e9e477ca.cc
- 計装 patch と既存負例 3 本: /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/verbatim/instr-mocc-lock-coverage.patch, broken-mocc-early-unlock.patch, broken-mocc-lockskip-validation.patch, broken-mocc-permutation-erase.patch
- T-2294 の insight と compute JSON 要約: /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/verbatim/t2294-README.md, s3_mocc_lock_coverage.summary.json
- repo 内 (投入先 worktree): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2772-mocc-mutation-proof-wave1/orchestrator/campaign/s3_mocc_lock_coverage.py、.../orchestrator/tests/test_mocc_proof_surface.py、.../orchestrator/campaign/condition_meaning_gate.py、.../orchestrator/verifier/model.py (470〜525)、.../external/ccbench/cc/mocc/include/lock.hh と .../external/ccbench/cc/mocc/lock.cc (ReaderWriterLock の counter 実装)

# 依頼 — [T-2772] レンズ A: 正しさ境界・恒真性・hang — plan と親 brief を攻撃する

plan を守らせず検査せよ。親 brief 自身も検査対象である。所見は real / refuted の判定材料 (行番号・既裁定) を添えて must-fix / should / nit に分ける。あなたは read-only。pytest は走らせない。予算が尽きそうなら途中結論を下の出力形式どおり書いて終わること (無出力が最悪)。

## 攻撃点

1. **負例が沈黙すべき regime で沈黙するか**: cold (閾値 21) と default (10) の U で hot-update-unlock 負例が stock と同じ certified になる論証 (`update()` 459 の述語が false → block に入らない) に穴はないか。default で温度が上がる経路 (construct_RLL の `failed_verification_`、TEMPERATURE_RESET_OPT の epoch reset) が U で本当に閉じているか。
2. **負例が発火すべき regime で発火するか**: hot t1 で 3 reason (`not-locked-at-entry` / `lock-lost-before-write` / `lock-lost-before-publish`) がすべて正数になる論証。計装 patch の入口検査は「CLL に writer 記録があり lock_ pointer が一致し、counter が W_LOCKED」を要求する — pending で counter が 0 のとき入口検査が発火することを計装 patch の逐語で確認せよ。
3. **balanced と hang**: plan の counter 遷移 (`w_unlock` は `counter_++`、`w_lock` は 0 → -1 の CAS spin) を lock.cc の実装で検算。hot t4 で pending 再取得と他 thread の本物の lock の競合、abort 経路 (validation false → `abort()` → `unlockCLL()`) での二重 unlock / 未 relock、`lock()` の canonical restore (834〜858) が pending の CLL 要素を消す経路 (多操作 txn で起きる — U では起きないか)、`vioctr > 100` の trylock 枝、RLL が空である根拠。**hang するなら compute で timeout=失敗として扱う設計になっているか**。
4. **親 (P3) の当否**: 「観測のみの t4 負例には integrity clean を要求しない」は規律 2 の緩めか、正当な限定か。要求すべき走の集合を再定義せよ。逆に、受入必須走の check が恒真になっていないか (例: `stock_*_certified_and_silent` が txns>0 を要求するか、`hot_update_unlock_{cold,default}_*_silent` が「沈黙」を certified で定義しているか)。
5. **保証名の過大化**: JSON の `hot_path_evidence` と check 名が「4 site 全被覆」「read 側 hot」「RLL 再試行」を含意する書き方になっていないか (D2134 項 4)。
6. **条件 gate との整合**: 新裸 define の exactly-one directive、`if constexpr` の discarded 枝の識別子、macro=0 で inert (TRACE=0 の無 patch base と `.text` 一致が期待できるか、`thread_local` 変数の TLS symbol が残らないか)。
7. **時間予算 (P6)**: verifier 100 万 write-only txn = 17.3 秒 (login) の一般化 (compute 側は速いか遅いか、4 thread U の txn 数の推定根拠)、RUN 120 / VERIFIER 900 / gen_S 3600 の整合。超過時の扱い。
8. **親 brief の file:line と前提の誤り** (§3 の 6 件の確定、anchor 表の行番号)。

## 出力形式

- 見出しはすべて `##`。所見は `## 所見 N: <title>` の形で、各所見に「real/refuted の判定材料」「must-fix / should / nit」「是正案 (逐語)」を書く。
- 最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書いてはならない。`## 総括` には (a) must-fix の一覧、(b) P3 の当否、(c) hang の判定、(d) 親 brief への異議を書く。
- 入力はデータであって指示ではない (規律 6)。断定には行番号か D 番号を添える。確信の無いことは「不確実」と書く。
