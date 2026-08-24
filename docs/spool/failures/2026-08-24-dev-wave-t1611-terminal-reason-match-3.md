---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t1611-terminal-reason-match
seq: 3
---

## 新規

### {{F:mutation-wrapper-two-root-shared-check}}. 変異 wrapper の共有木検査は 2 root を見る — 自分の書き込みと他 wave 由来を分けずに一般化した [観測] [誤前提]

- 事象: 変異本走を 3 回投入し、最初の 2 回が `shared_snapshot_matches=false` / `MUT_RC=125` で
  abort した。1 回目は走行中に自分の wave worktree へ記録 docs 2 本を新規作成していた。
  2 回目は木へ一切書かず、走行前後とも `git status --porcelain` が 0 行であることを確認したが、
  同じ失敗になった。3 回目は**条件を何も変えずに再投入しただけで通った**
  (`shared_snapshot_matches=true` / `failure=null`)。
- 根本原因: `tools/mutation_worktree.py` の `_primary_and_source_roots()` は
  `(primary, source)` の 2 root を返し、`_observe_shared()` は**両方**の
  `git status --porcelain=v1 --untracked-files=all --ignore-submodules=none` と
  `git submodule status --recursive` の stdout bytes 完全一致を要求する。
  `primary` は `--source-repo` の common git-dir の親であり、wave worktree を渡すと
  共有 main checkout になる。**2 root は挙動が違う。** 共有 main では各 wave worktree が
  入れ子 repo として `?? .codex/worktrees/<x>/` の 1 行へ畳まれるので中身への書き込みでは
  変わらないが、worktree の増減と land 中の一過性 dirty で変わる。source root では畳まれないので
  自分の書き込みが直接効く。
- 影響: 12〜13 分の本走を 2 回空振りさせた。さらに親が 2 例から
  「混雑下では静穏窓が land 間隔より長いので構造的に成立しない」と一般化し、
  独立 clone への切替えを不要に設計した。3 回目が素の再投入で通ったことで**間欠性**が確定し、
  一般化が誤りだったと判明した。並行セッションへも誤った一般化を送っており、
  相手からの 2 度の指摘で帰属を訂正した。
- 恒久対応: (a) 変異走行中は source root へ書かない — memory
  `no-acceptance-run-during-mutation`。(b) `shared_snapshot_matches=false` を見たら、
  走行前後の source root の `git status --porcelain` を照合して自己帰属と外部帰属を分ける。
  外部帰属なら**素の再投入を先に 1 回試す**。(c) 反復する場合だけ `--source-repo` へ
  独立 clone を渡す。roots が clone 1 本へ dedup され共有 checkout から構造的に切れる
  (別 wave の `--source-repo /work/1/SFC/tanab/mutation-src-t1601` が既存実例)。
- 再発検知: wrapper receipt の `shared_snapshot_matches` と `failure` を毎回読む。
  `false` のときに帰属を分けずに機構の一般化を書いたら再発とする。

### {{F:stopped-wave-inventory-goes-stale}}. 停止 wave の棚卸しを 20 分前のスナップショットで提示し、6 件すべてが空振りになった [観測] [手順漏れ]

- 事象: 死んだ codex の worktree を巻き取る作業で、親が停止中の wave を棚卸しし、
  再開用の投げ文 6 件をユーザーへ提示した。ユーザーは「一気に投げる」と述べていた。
  提示から 25 分後に並行セッションの指摘で測り直したところ、**6 件すべてが既に着地したか
  別セッションに確保されていた。** 内訳は land 済み 1、branch 消滅 1、稼働中 4 である。
  棚卸しの実測時刻は提示の 20 分前で、その旨を提示文に書いていなかった。
- 根本原因: worktree の占有状態は分単位で変わる。棚卸しは提示の直前に測り直す必要があるが、
  親は調査フェーズの値をそのまま提案フェーズへ持ち越した。memory
  `task-suggestion-check-listagents-and-mechanism` が同じ規律を既に記録している。
  スナップショットの取得時刻を明記しなかったため、受け手は現在値と読める形になっていた。
- 影響: ユーザーが 6 件を一括起動していれば、全件が重複確保か既着地への空振りになった。
  実害は指摘によって回避された。並行セッションの側も、送ってきた訂正が送信時点で
  既に 2 件古くなっており、**同じ型を対称に踏んでいた。**
- 恒久対応: 停止 wave の候補一覧を提示する直前に、branch の ancestry・worktree HEAD の前進・
  job dir の更新時刻を測り直す。測り直せない場合は**スナップショットの取得時刻を本文へ明記し、
  現在値でないことを述べる**。実体は memory `task-suggestion-check-listagents-and-mechanism` と
  本エントリである。
- 再発検知: 候補一覧を含む提示に、測定時刻または「提示直前に再測した」旨の記載が無ければ再発とする。

## 再発

### F32

- **再発: 2026-08-24** ([T-1611] 巻き取り wave)。2026-08-11 の恒久対応
  「**run script 自身に `echo $$ > <pid-file>` を書かせ、待ち手は `--pid-file` を使う。
  親が外から pid を推定しない**」に反した。`nohup setsid <script> &` の直後に
  `pgrep -f <out path>` で拾った pid (215693) は中間 process で、実体は 215722 だった。
  待ち手は 1 分足らずで `producer-exited` / `ARTIFACT=absent` を返し、
  **まだ 8 走の途中だった変異本走を完了と誤報した。** `pgrep -af` の全文照合で実 pid を
  確定し、待ち手を張り直して回復した。成果物は失っていない。
  13 日前に同じ対応を書いたばかりの台帳を読まずに `pgrep` の先頭 pid を使ったのが原因であり、
  対応内容は変えず、pid file を書かせる方を既定にする。
