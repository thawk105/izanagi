---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: dev-wave-t2865-silo-small-compare
seq: 1
title: [T-2865] silo-function-policy 軸の既知最良との小比較を 1 回走らせた — 既知最良は全 8 job で静的 10 µs (元の適用方法)、固定 16 点のうち 3 点が同 job の最良参照を 6〜7% 上回った (探索的、再測なし)。偵察 driver に compare phase・fixed10 参照・compare-aggregate を Codex author が足し、8 job を同時投入 (コード + test + 計測 JSON + insight、branch worktree-dev-wave-t2865-silo-small-compare)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `output/insights/2026-09-23/t2865-silo-policy-known-best-compare/verbatim/request.md`): D2235 項 7 = 択 (b)。段階 D と同じ 8 job 構成・同じ偵察 driver・generic dispatch で、既知最良の参照 (元の適用方法の調整済み静的 backoff・`B0-L-W0`・stock) を同じ job に置き、IR 候補が超えるかを測る。記録 = 同 insight の README、設計判断 = {{D:silo-policy-known-best-compare}}。
- 起点 = local main `620a6bb13` (fresh worktree、開始 gate rc=0)。同じ引数の wave が 22:02 JST にもう 1 本起動されたが、先方が譲って停止した (worktree・commit・計算投入 0、先方からの連絡)。wave 中に [T-2858] が ccbench pin を `68106660` へ進めた (D2236) が、計測は wave の branch (pin `e9e477ca`、段階 D と同じ) で行い、main は受入の post-claim merge でだけ取り込んだ。`cc/silo`・`cmake/Options.cmake`・`include/backoff.hh` は 2 つの pin で差分なし、`silo-backoff-fixed.patch` は新 pin にもずれ無しで当たる (親が実測)。
- 「調整済み静的 backoff」の特定: write-heavy の既存最良は 10 µs (known_axes_freeze・A-2 正式認証・D2160・未知条件転移の R2、いずれも旧 pin)。「元の適用方法」= stock 木へ `patches/silo-backoff-fixed.patch` を当てる macro 経路。現行の build 経路 (`silo_policy_coverage._source`・`_build_variant`) は BACKOFF_FIXED を扱えず、flag だけ渡すと無言で適応 backoff に落ちうるので、実効 define の検査を足した。
- **計算投入のユーザー確認:** 投入前に「計測 8 job 1.44〜1.84 + 検査で合計 約 2.06〜2.46 node 時間、walltime 上限で 約 4.6」を示し、ユーザーは「上限 4.6 h で承認 (推奨)」(再測なし) を選んだ。別 session から「検査費用も含めて 2 node 時間の線と比べる」(D2219 項 1) との補足があり、見積りに含めた。
- **段 3 相談 2 本は adopt_with_conditions。** must-fix (fixed10 の実効 define を検査して停止、参照 1 本でも不適格なら最良参照比 null、集計で fixed10 を照合、3% 超を探索的に扱う、見積り下限の訂正) を全件採用。
- **段 6:** レビュー 1 本 (NO-GO: job 7 の巡回漏れ = 6 要素へ slice 7 で基本列に戻る、BACK_OFF 重複 define を有効と判定) → fix 1。焦点走 1 回目 (21338.nqsv) は 1 failed / 804 passed: 新 test の stub が `_one` の読む build dir に compile_commands.json を書かず、owner TU を読めない例外経路で status だけが一致していた (test の欠陥、fix 2)。焦点走 2 回目は gen_S が自分の計測 8 job で埋まり queue-wait-timeout (子は未起動)、投げ直した 21493.nqsv で 161 passed / 2 skipped。
- **結果:** 既知最良は全 8 job で fixed10 (同 job 中央値 3,944〜4,011 千 txn/s、`B0-L-W0` 2,374〜2,533、stock 1,343〜1,378)。IR 16 点は全点適格、最良参照比 0.836〜1.069、3% 線を越えたのは 3 点 (1.062〜1.069、5 rep の最小が同 job の fixed10 の最大を上回る)。同じ 3 点は段階 D でも上位 3 点で throughput は 1% 以内で一致。点 ID・比は insight にだけ置き、段階 E / F の coder・planner へ渡さない (手順書 §3-D)。
- 計算ノードの使用 (job Elapse): 計測 8 job 6,180 秒 (21389〜21396.nqsv、各 768〜779 秒)、焦点走 107 + 92 秒 (queue-wait-timeout の 1 回は子なし)。変異・受入は下記と land の受領証。
- **変異 matrix:** 事前登録 13 本 (段 4 で 9、段 6 の fix 前に 4)。probe (全件 SURVIVED 期待) で 13 本すべてが事前登録した kill 点の test 1 件だけを落とし、final で 13 / 13 KILLED・期待 node と完全一致・基準走 PASSED。runner 所要は probe 5,343 秒 (計測直後の混雑で待ち行列込み)・final 461 秒。計算の合計は約 3.38 node 時間 (変異は上限値、ユーザー承認の上限 4.6 の内側)。受入は本記録の後で、結果は land の受領証に残る。
- **session 中断:** 2026-09-24〜26 に session が止まり、ユーザーの「続けて」で再開した (変異 probe は中断前に完了、final は再開後に投入)。
- 工数: Codex 子 = consult 2、author 1、review 1、fix 2 の計 6 本。Claude の調査子 1 本 (sonnet、静的 backoff の値の特定)。

## 次の一手差分

### 更新

- [T-2865] **P1・ユーザー判断待ち**: silo-function-policy 軸を段階 E (LLM ループ実装、`.claude/agents/` の変更はユーザー明示承認、D2214) へ進めるか。既知最良との小比較 ({{D:silo-policy-known-best-compare}}、insight `output/insights/2026-09-23/t2865-silo-policy-known-best-compare/README.md`) は 1 回走った: 既知最良は静的 10 µs で、固定 16 点のうち 3 点が同 job で 6〜7% 上回った (探索的、再測なし、未較正の 3% 線、多重選択の補正なし)。
  - 推奨: 進める。追加で確かめるなら、越えた点の別 job 再測 (1 点 1 job、約 0.21 node 時間ずつ) が最小。計算は投入前に確認。
  - 後段へ渡してよいのは段階 D の `projection.json` の二値と射程文だけ。小比較の点 ID・比を coder・planner の入力に流さない。
  base: 1d78532449bf85d0a97a922b921aa4040f3c735f3eb76b893cee7f559ea9a89b
