---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t688-job-kill-evidence-r2
seq: 3
---

## 新規

### {{F:floor-signal-trap-unreachable}}. 床値 job の signal trap が最初から到達不能だった [恒真ゲート] [テスト代表性]

- 事象: `tools/pegasus/floor_campaign.sh` は INT / TERM / HUP に trap を張り、受信時に
  `failure.json` を書いて `128 + signal` で終了する設計だった。しかしこの trap は一度も
  発火しえなかった。NQSV は既定で `Accept Sigterm = No` であり、SIGTERM が job script へ
  配送されない。`kill -TERM $$` は builtin として成功し rc=0 を返すため `set -e` も ERR trap も
  発火せず、shell はそのまま正常終了する。
- 根本原因: signal 受信を有効化する `#PBS --accept-sigterm=yes` を job script が持たず、
  「trap を書けば受信できる」という前提を誰も実測で確かめていなかった。無効化された signal 状態は
  PBS job から pytest、xdist worker、`subprocess.run()`、`bash -c` まで継承されるため、
  テスト側でも同じ盲点が再現していた。
- 影響: kill 時の診断を残す設計上の経路が 1 本、宣言だけで存在し続けた。恒真ゲートの一種であり、
  「保証があるように見えて発火しない」形そのものである。
- 恒久対応: {{D:floor-job-accept-sigterm}} 決定 (1) で `#PBS --accept-sigterm=yes` を置く。
  対応するテストは外側の signal 状態へ依存せず、新しい process で TERM を `SIG_DFL` へ戻して
  mask から外し、`execvp` で bash へ置換してから実際の `kill -TERM $$` を実行する形へ変えた。
  trap が消えれば rc が `-15` になり `143` の assertion が赤になる。
- 再発検知: 変異 V4 (`rejected` checkpoint の削除) と、上記 signal 経路テストの
  `[false-1]` / `[kill -TERM $$-143]` の 2 param。変異本走で KILLED を実測済み。
- 併せて記録: 同一 commit に対しログインノードでは 168 tests / 0 failures、計算ノードでは
  1 failed / 132 passed だった。**ログインノードだけで判定していれば緑に見え、受入全走で
  初めて落ちていた。** signal・scheduler に触る検査は実行環境をまたいで測る。

### {{F:mutation-local-mode-truncates-collection}}. 変異 harness の local mode が collection を切り、期待 node を不在と誤判定した [テスト代表性]

- 事象: 期待 node 16 件すべてが「pytest collection に実在しない」として変異本走が rc=2 で中止した。
  16 件はいずれも直前の probe 走が実際に観測した node である。
- 根本原因: `--runner-mode local` で runner が自己判断で計算ノードへ dispatch すると、
  成功時の relay が出力を上限で切る。`--collect-only -q` の出力が途中で切れ、
  133 件中 34 件しか collection に見えなかった。harness は残りを「不在」と判定した。
- 影響: 実在する検査を不在と誤判定し、変異本走を 1 回空振りさせた。誤判定の向きが
  fail-closed だったため偽の緑は生じていない。
- 恒久対応: 本走は `--runner-mode dispatch` を既定とし runner argv へ `--force-dispatch` を
  入れる、という既存手順に従う。この経路は relay ではなく job stdout 全文を読む。
- 再発検知: 手順どおりの dispatch mode で本走し直し、baseline PASSED・10/10 KILLED を実測した。

### {{F:codex-transient-death-misread-as-exhaustion}}. codex 子の一過性即死を資源枯渇と断定し wave を畳んだ [セッション死・救出] [捏造/幻覚]

- 事象: 段 3 の codex 子 2 本が即死し、events に `You've hit your usage limit ... try again at
  Aug 20th` が出ていた。親はこれを恒久的な枠切れと断定し、wave を fail-closed 停止として
  worktree まで畳んだ。実際には一過性で、**8 分後には回復していた**。
- 根本原因: 表層メッセージの日付表記を額面どおり受け取り、再投入で確かめずに恒久性を結論した。
  外形 (`codex_exit_code=1` / `model_calls=0` / token 0 / log 0 byte) だけでは一過性か恒久かを
  区別できない。
- 影響: 実装可能な wave を停止扱いにし、worktree の作り直しと段 3 の再投入を要した。
  成果物は repo 外へ保全していたため失われなかった。
- 併せて判明: 同時刻に並行 2 wave が**別症状**で同じ即死をしていた。一方は同じ usage limit 型、
  もう一方は `401 Unauthorized: Missing bearer or basic authentication in header` の連打型で、
  `codex login status` は正常のままだった。**外形は両者とも同一で、log の空だけでは区別できない。**
  いずれも数分で自然回復した。独立 2 例が揃うため一般化してよい。
- 恒久対応: 停止を断定する前に (1) receipt の `codex_exit_code` を読む、(2)
  `attempt-*.events.jsonl` の message 本文で症状を確定する、(3) 数分あけて 1 度だけ再投入する。
  再投入は prompt bytes を変える必要がある (job-id が prompt hash から決まるため)。
  この手順の dev-wave 入口への明文化は {{T:codex-transient-stop-rule}} で裁定する。
- 再発検知: 現時点では機械検査が無い。手順の明文化と併せて裁定へ返す。
