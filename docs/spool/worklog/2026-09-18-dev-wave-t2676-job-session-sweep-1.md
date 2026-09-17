---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2676-job-session-sweep
seq: 1
title: [T-2676] 計算ノード job の終了遅延への局所対処 — job body が session に残る process を入れ子 user ns で帰属させ pidfd で回収する — 陽性対照の `E − J` 69.5 秒 → −0.38 秒、残存子の消滅を pidfd で独立確認 (コード + テスト + docs、branch dev-wave-t2676-job-session-sweep、変異 matrix = baseline PASSED・M0 SURVIVED・M1〜M7 KILLED 期待 node 完全一致 (M2 は diagnostic pin 別枠)・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2676] 計算ノード job の終了遅延 (NQSV は job の session に生きた process がある間 RUN に留める、[T-2675] の setsid / setpgid 実験 2 本で実測) への局所対処 — 遅延の原因 process を job body 側で特定し、job 終了時に残さない最小の局所修正を入れて計算ノードで実測する。subreaper は採らない (F973)。一般的な process 管理機構へ広げない。Codex author (D95)。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の局所対処だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-18/t2676-job-session-sweep/README.md`。設計判断は {{D:job-session-sweep}}。失敗の型は F1012 の再発 (fixture が SIGTERM 既定動作を継承状態に依存、計算ノード dispatch で露見)。実装 commit `1e4d0bbd1` (2 file、+777/−1、Codex author)。
- **結論 (事前登録どおり、2 軸):** 計算ノード実測 (generic 単一子 probe = T-2675 と同器具、untracked 配置・投入後削除) で、統制 no-child (`5077.nqsv`) は残存 0・`E − J` −0.468 秒、陽性対照 keep (`5086.nqsv`、子 75 秒) は残存 1 (probe の子、入れ子 ns、ppid 1) を TERM (無視) → 5 秒 → KILL で回収し pidfd で終了を独立観測 (G − t0 = 10.0 秒)、`E − J` −0.381 秒・`J − W` 5.08 秒・`E − W` 4.70 秒。前 2 wave の同条件は 69.5 / 69.7 秒。会計短縮と残存子消滅の両軸が合格。
- **新事実 (投入前に期待を改訂した):** 計算ノード job 内の全 process (nqs_shpd → bash → dispatcher → 子) は SIGTERM を SIG_IGN で継承する (request 5043 の SigIgn 採取)。handler を持たない残存子は TERM で死なず 5 秒後の KILL で死ぬ。keep の期待を TERM 終了から KILL 終了へ改めたのは keep 投入 (07:49) の前 (07:45、`verbatim/s4-ruling.md` §3′)。session leader は NQSV の `nqs_shpd` がユーザー uid で走る process で、dispatcher は leader ではない (4 job で同形の祖先鎖を trace で採取)。
- 段 3 レンズ A/B の must-fix をすべて採用: 帰属を session 所属から「session 所属 かつ 入れ子 user ns」へ (A-1、login で述語の可読性を実測)、opt-in の値を request SHA-256 に束縛 (A-2、ambient `1` で in-process テストが login の pytest session を走査する経路を塞ぐ)、signal と終了観測を pidfd へ (A-3)、M6 を巡数固定へ・M2 を別枠へ (A-4 / B-2)、heartbeat 条件を `H ≤ G` へ (A-5 / B-1)、`J − W` / `E − W` の閾値追加 (B-3)、テスト期限の絶対打切り化 (B-4)、祖先断定の撤回 (B-5)。refuted 8 件は同意。段 6 レビュー A (real 3) / B (real 2) も全採用 → fix 1 巡 (fixture の SIG_DFL + unblock、期限 15/20/10 秒、production 定数のまま、finally の全員終了確認、`session_unknown` と status の分離)。
- 実走: 焦点走 1 (段 5 版、計算ノード 5015) 14 passed / 1 failed → 原因は上記の SIG_IGN 継承 (login 再現は緑)。焦点走 2 (fix 後、login、file 全体) 353 passed / 27.2 秒。全史 provenance 11,207 件新規違反なし。変異 matrix: baseline PASSED (353 node、47.8 秒)、M0 SURVIVED (drift mask 0)、M1〜M7 は probe 走の観測集合を期待に登録して本走で KILLED 期待 node 完全一致、MISMATCH 0。受入全走は docs commit 後の最終 tip に land 前に 1 回 (結果は land の受領証)。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1、全段 `gpt-6-astra` / medium)。親の実測: login probe 3 (ns 帰属 / pidfd、term 再現、SigIgn)、計算ノード dispatch 5 走 (焦点走 1、SigIgn 1、no-child 1、keep 1、変異は別に 18 走)、login 焦点走 1、変異 probe / 本走 各 9 走。

## 次の一手差分

### 完了

- [T-2676] job body の session 回収を実装し計算ノードで両軸合格 (統制 −0.468 秒 / 陽性対照 −0.381 秒、残存子は pidfd で消滅確認)。残る候補 (dispatcher で SIGTERM を SIG_DFL に戻す案、受入全走の `session-sweep-complete` 集計) は insight §8 に記録、起票しない。
  remaining: none
  base: d0eaf2bfc8e35a5e64b2225f88ffce04c0779f35a49f19ab120f4469ab873cae
