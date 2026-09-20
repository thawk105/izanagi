---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: waiter-collect-latency
seq: 1
title: 計算ノード job の END → 待ち手の回収遅延を直近 landed 12 wave の job dir で実測した — END → producer の `.done` は中央値 14 秒・最大 56 秒、正本待ち手 (`dev_wave_wait.py producer`、poll 5 秒) の戻りは `.done` から 0〜5 秒、周期の内側に入りうる区間の寄与率は 17〜25% で主因の証拠なし → 周期の局所修正は実装しない (診断のみ・実装 0 行、branch worktree-waiter-collect-latency)
---

## 本文

- 依頼 (dispatch した計算ノード job の END から待ち手が `.done` を回収するまでの遅延を直近 landed 12 wave で実測し、大部分が周期由来なら周期の局所修正 1 件を Codex author で実装) を軽量版 + 診断 wave の型で処理した: 段 1 brief → 段 3 相談 1 本 (codex read-only) → 段 4 裁定「実装しない」(4 → 7 → 8 → 9、段 5・6 の実装子なし) → docs-only の read-only review 1 本 + 焦点再レビュー 3 巡 (NO-GO → NO-GO → GO) → 記録。一次資料は `output/insights/2026-09-21/waiter-collect-latency/README.md` (+ `verbatim/`)。
- 実測 (残存資料から観測できた compute job 254 本 = 焦点走 27 / 単発 10 / 受入 shard 58 / 変異 attempt 159、producer 68 本。変異 attempt 66 本は evidence が撤去済み worktree 側で欠測): END → NQSV の stderr file の mtime は 217 本すべて 9〜11 秒、spool → dispatcher receipt は中央値 2・最大 5 秒 (dispatcher の収集 poll 5 秒の内側)、END → producer の `.done` は中央値 14・p90 37・最大 56 秒 (焦点走 10〜15 / 受入 19〜39 / 変異 29〜56)、`.done` → 正本待ち手の戻りは 0〜5 秒 (n=34)。同一 producer 群 (spool を観測できた 13 本) で周期の内側に入りうる区間の上限は中央値 5・最大 9 秒、END → 待ち手戻り合計への寄与率は中央値 17%・最大 25%。
- 裁定: 依頼の条件「大部分が周期由来」は成立しない → 実装しない。効果試算 (観測可能部分、代理値含む) は 2 定数 (`DEFAULT_POLL_INTERVAL_S = 5.0`、`_PRODUCER_POLL_SECONDS = 5`) の poll を 0 にしても wave あたり平均 48 秒・最大 159 秒 (旧標本平均 154 分への参考比較 0.52% / 1.72%)、5 → 1 秒の条件付き期待値は変異 67 attempt の wave で 134 秒。依頼の括弧書き (3 分 / 30 分) は親の起床周期の規則で process 内部の poll には当てはまらない。再訪条件は insight §10。
- 棄却・限定 (段 3 must-fix 3 / should 2、段 6 review must-fix 4 / should 4 / nit 1、焦点再レビュー 1 巡目 partial 3 / regressed 1 / 新規 3、2 巡目 partial 1): 「周期由来は約 1/4」は別標本の中央値の和 → 同一 producer 群で分解し直した。「254 本 = 全 compute job」→ 観測できた本数に限定し被覆表を付けた。効果試算に t2797 の自前 wrapper の 2 秒が混入 → receipt json の待ち手 34 本に限定 (最大 161 → 159 秒)。「こちらの code に周期は無い」「NFS 1 秒粒度」「無相関」「秒切り捨て」の断定を観測の範囲に限定した。wall-decomp §4 の「END 後の後処理 6 秒」と本 wave の同 producer の END → receipt 10〜14 秒は未解決の不一致として残した。
- 例外 2 型は待ち手の周期でなく親の運用: t2797 の自前 `wait-file.sh` (poll 20 秒、[T-740] からの逸脱、`.done` → 戻り 2〜18 秒、誤検知は未観測、既存防壁の破れに当たるか・failures 台帳へ追記すべきかは未判断、台帳追加は依頼の scope 外なので本 wave では追記しない)、t2807 の `wait-all.sh` が 2 TAG を直列に待ち 2 本目の検知が 47〜361 秒遅れた。親の起床は job dir から見えない (t2814 の transcript で待ち手の通知 → 次 turn 3〜18 秒、参考値)。
- 落とし穴: wall-decomp の `list_landed.py` は `land*.json` だけを見るので `land-1.stdout` 形式 (t2817) を落とす。`.wait.log` は size 0 だと mtime が待ち手の起動時刻。焦点走の `.e` file と変異 evidence の一部は撤去済み worktree 側にしか無い。効果試算の除外条件は待ち手 file の種類 (receipt json か自前 wrapper か) を mtime 一致で逆引きしないと崩れる。
- 検査: `tools/check_docs.py` 違反なし (08:22 JST と、fragment・正規化を加えた記録 commit 直前の 08:31 JST の 2 回)。verbatim 6 file の行末空白を可逆に除去した (`verbatim/NORMALIZATION.md`)。三軸走査 (`s8b_holdout_freeze search`) の hit は既知の official 成果物 4 file × 2 holdout のみで、本 wave の insight 配下は 0。実装面の差分ゼロなので変異 matrix は免除。
- 工数: codex 子 5 本 (consult 7 call / 140 秒、review 5 call / 148 秒、focus 6 / 139、4 / 94、4 / 86 秒)、計算ノード job 0、親の実測 script 7 本 (job dir、repo 外、逐語は insight の verbatim)。壁時計は開始 gate 07:37 JST → 記録 commit まで。受入全走と land の結果は fold 後に確定するため本 entry には書けない。

## 次の一手差分
