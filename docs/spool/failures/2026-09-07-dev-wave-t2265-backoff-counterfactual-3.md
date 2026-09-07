---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2265-backoff-counterfactual
seq: 3
---

## 新規

### {{F:line-pinned-ledger-restales-on-every-impl-fix}}. 行番号で sink を照合する台帳が実装 fix のたびに失効し、変異 baseline を 2 度落とした [手順漏れ]

- 事象: `orchestrator/tests/test_ccbench_spawn_sites.py` の deferred gate 台帳が赤になった。
  段 6 の 1 回目の fix で行番号を当て直したが、その後の別の fix が同じ driver へ 127 行足したため
  **再び失効**し、変異本走が baseline 赤 (`status=FAILED`) で中止した。
- 根本原因: この台帳は sink を `path・kind・scope・line` の**完全一致**で照合する。行番号は
  対象 file の行数が変わるだけで動くので、その file を触る fix が 1 つ入るたびに失効する。
  親は初回の赤を「新しい define が新しい build sink を作った」と誤って帰属し、段 6 のレビューに
  訂正された (実際は同一 sink の移動で、件数の差も新 define 2 本が同じ sink で到達不能になった分)。
- 恒久対応: 行番号 pin を持つ台帳の追随は、**その file を触る実装 fix をすべて終えた後に、
  最後の 1 回として当てる**。fix を 1 本入れるたびに当て直さない。帰属を書く前に、増えた組が
  新しい sink か既存 sink の移動かを現物で数えて確かめる。
- 再発検知: 変異本走の直前に、変異と同じ argv で baseline を 1 回実走して緑を確認する
  (harness も baseline 緑を要求するが、その中止は 25 変異ぶんの待ち時間の後に来る)。

### {{F:mutation-spec-placement-and-field-set}}. 変異 spec の置き場所と field 集合で本走が 2 度 rc=2 で中止した [手順漏れ]

- 事象: (a) repo 内へ commit した変異 spec をそのまま `--spec` に渡したところ
  `runtime artifact は試験対象 checkout 外でなければならない: --spec` で中止した。
  (b) probe の観測で期待集合を確定させた版に 1 行の `note` field を足したところ
  `mutations[0] の field 集合が不正: missing=[], unknown=['note']` で中止した。
- 根本原因: harness は runtime artifact が試験対象 checkout の外にあることを要求し、
  変異 entry の field 集合を完全一致で検査する。どちらも `DW-M05` / `DW-M07` に記載が無く、
  親は前 wave の spec の**中身**だけを手本にして置き場所と field 契約を確かめなかった。
  spec を書いた子は harness を走らせられないので、どちらも実行時まで露見しない。
- 恒久対応: 記録用の現物は repo 内に commit し、**走行には checkout 外へ写した同一 bytes を渡す**
  (sha256 は同じなので `--expected-spec-sha256` はそのまま使える)。注記は spec の field ではなく
  別 file (`mutation-notes.md` 等) に置く。
- 再発検知: spec を書き終えた時点で `--plan-only` を 1 回通し、置き場所と field 契約を
  25 変異ぶんの待ち時間の前に確かめる。
- 記載場所: `docs/dev-wave/mutation.md` の L1.5 byte 予算が満杯 (追記で 9908 > 9696) だったため、
  安全義務を削らずに本台帳へ置いた。

### {{F:guard-refuses-bash-on-dispatch-required-script}}. 計算ノード用実行体を bash に渡す指示を親が書き、fix 子が防壁拒否で不受理になった [手順漏れ]

- 事象: 親が fix 子へ「投入スクリプトを実際に bash で走らせて分類を確かめよ」と指示した。
  子は `bash -n tools/pegasus/probes/<name>.pbs` を実行しようとして
  `[guard_bash] 拒否: Pegasus dispatch-required 実行体` で止まり、その子は `not_accepted` で終わった。
- 根本原因: 機械防壁は dispatch-required 実行体の path が bash の引数に現れるだけで拒否する。
  構文検査だけの `-n` でも同じである。親はその射程を確かめずに指示を書いた。
- 恒久対応: 実挙動の歯が要るときは、**判定に関わる行の塊を現物から逐語で抜き出し、別名の script
  として書き出して実行し、抜き出しが現物の逐語部分列であることを同じテストで固定する**。
  防壁を迂回する書き方 (別 path へ copy して同名で叩く、絶対 path で呼ぶ) は取らない。
- 再発検知: 子へ「実際に走らせて確かめよ」と書く前に、その対象が防壁の管轄下にないかを親が確かめる。
