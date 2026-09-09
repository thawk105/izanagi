---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2249-role-example-delta
seq: 2
---

## 新規

### {{F:codex-child-cannot-write-dot-codex}}. Codex 実装子が `.codex/**` へ書けず段 5 が途中停止した [手順漏れ] [誤前提]

- 事象: [T-2249] wave の段 5 実装子が、role 定義と `SOURCE_FILE_SHA256` の更新までは終えたが、
  生成物 `.codex/role-adapters/{coder-v4-autonomous,planner-v4}.json` の更新で
  `patch rejected: writing outside of the project; rejected by user approval settings` を受けて停止した。
  `test -w` も rc=1 だった。作業 root を `.codex/worktrees/t2249-author` から
  `.claude/worktrees/dev-wave-t2249-role-example-delta` へ移して継続子を投げても同じだった。
  段 5 が 2 本の実装子を消費し、adapter は 1 bit も書けなかった。
- 根本原因: `codex exec --sandbox workspace-write` は `.codex/` を自身の設定領域として
  書込禁止にしている。**path 依存ではない構造的制約**で、作業 root を変えても直らない。
  段 1 の変更面棚卸しは「`.codex/` 配下の非 `.md` は D95 の実装面だから実装子が書く」と
  分類したが、**実装子が実際に書けるかを起動前に実測していなかった**。
  1 回目の拒否を「作業 root が `.codex/` 配下だから」と読んだのも誤前提だった。
- 恒久対応: memory `codex-children-cannot-write-dot-codex` — 段 1 の変更面棚卸しで `.codex/**` の
  非 `.md` を含む wave は実装子起動前に `test -w` を実測し、書けないなら段 4 で「誰が書くか」を
  決める。生成物は親が repo 自身の renderer の出力で render し、**書く前に**旧版との field 単位比較で
  「変わる pointer 集合が exact 一致・key set 不変」を検算してから書く。
  `AI-Agent: product=claude; ...; role=integrator; scope=patch-and-render` で記録する。
  `.codex/**` を D95 の適用外と明文化するか D105 の `AI-Agent-Waiver` を要求するかは
  {{D:codex-cannot-write-dot-codex}} で裁定パッケージへ送った。
- 再発検知: 段 6 の敵対レビュー 1 本へ「親が書いた bytes が renderer の出力そのもので人手の判断が
  混じっていないこと」を独立に再計算させる。本 wave では byte 一致・4 pointer・key set 不変を
  レビューが独立に確認した (レビューは著者性の代替にしないので、機構で確かめさせる)。

### {{F:mutation-wrapper-shared-observation-churn}}. 変異 wrapper の共有木不変検査が並行 wave の worktree 増減で破れ、2 分の走行が中止した [手順漏れ]

- 事象: [T-2249] wave の変異本走を `tools/mutation_worktree.py` で投げ、約 2 分で
  `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した`
  (`shared_snapshot_matches: false`) で中止した。container が保持され、8 走のうち 0 走が完了した。
- 根本原因: 同 wrapper は `git status --porcelain=v1 --untracked-files=all --ignore-submodules=none` の
  stdout bytes を source worktree と**主 checkout**の両方で取り、前後一致を要求する。
  主 checkout のこの出力は `?? .codex/worktrees/<name>/` を 1 行ずつ含み、実測 **171 行**あった。
  並行 session が codex 実装子・fix 子の worktree を作る/消すたびに bytes が変わる。
  19 job が並走する状況では、2 分でも破れる。HEAD の前進では破れない
  (`--porcelain=v1` は branch/HEAD を出さない) — 破るのは `.codex/worktrees/` の増減である。
- 恒久対応: memory `mutation-worktree-shared-observation-fails-under-churn` — 変異本走は
  `tools/mutation_harness.py` を job dir 内の専用 detached worktree
  (`git worktree add --detach <job dir>/mutation-tree <統合 commit>`) に対して直接使う。
  主 tree を変異させない性質 (DW-O19 の目的) と、harness 自身の固定 HEAD 束縛・起動/復元の内容比較・
  `flock` 単一走行・signal 復元は保たれる。失うのは wrapper の共有木 attestation だけで、
  それはこの環境では成立しない。wrapper 経路を選ぶ前に主 checkout で
  `git status --porcelain=v1 --untracked-files=all --ignore-submodules=none | wc -l` を数える。
- 再発検知: 上記の行数計測が数十行を超えていたら wrapper 経路を選ばない。中止した wrapper の
  container は `rm -rf <scratch>/.izanagi-mutation-worktree` の後 `git worktree prune` まで行う。

### {{F:dispatch-override-exceeds-mutation-timeout}}. D612 の dispatch 上書きを変異 spec の timeout より大きくして、変異走行が 1 走も始まらなかった [手順漏れ]

- 事象: dispatch 混雑を避けるため D612 の
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` /
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600` を設定して変異本走を投げたところ、harness が
  `mutation harness aborted: mutation collection の外側 timeout が明示された dispatch 待機契約より短い:
  timeout_seconds=900.0, queue_wait_timeout_s=3600.0, overall_grace_s=600.0`
  で起動時に fail-closed した。8 走のうち 0 走が始まらなかった。
- 根本原因: `DW-O13` の「内側予算の和 + 終了余裕 < 外側 watchdog」を、**dispatch 待機 (内側) と
  変異 collection の `timeout_seconds` (外側) の関係**へ適用していなかった。受入走行で有効だった
  上書きを、spec を見直さずに変異走行へ持ち込んだ。
- 恒久対応: memory `mutation-timeout-includes-dispatch-queue-wait` へ追記 —
  spec の `timeout_seconds` は `queue_wait_timeout_s + overall_grace_s` より大きくする。
  実際に通した組は queue_wait=1200 / grace=300 / `timeout_seconds`=2400 /
  `hang_timeout_seconds`=3000 (job walltime 3600 未満、`DW-M06`)。
- 再発検知: harness 自身が起動時に fail-closed で拒否する (既に機械化済み)。
  spec を変えると sha256 が変わり `--resume` は使えないので、新しい `--out` / `--attempt-out` で走り直す。

## 再発

### F169

- **再発: 2026-09-09** ([T-2249] wave)。pin 閉包の件数を `git grep -c` で数えて
  「bytes を pin する箇所は 3 系統 6 hit だけ」と段 1 brief に断定した。段 3 のレンズ B が反証した。
  `git grep -c` は**一致した行数**を数えるため、`orchestrator/tests/test_reflux_originless_compatibility.py:372`
  の凍結 baseline (物理 1 行の巨大 JSON) に**同じ sha が 7 回**あるのを `1` と数えていた。
  literal 出現の実数は coder 3 + planner 10 = 13 件だった。F169 と同じ「pin 閉包の検索が
  silent に取りこぼす」型であり、取りこぼしの機序が検索起点でなく**計数単位**だった点が新しい。
  同じ brief は「この凍結 baseline は保存済み `output/` の値なので role file 編集では動かない」とも
  書いていたが、これも誤りで、同 test は `run_trial()` を実走して journal を作るため live な
  role bytes が届く。恒久対応は memory `closure-and-search-discipline` へ
  「`git grep -c` は行数であって出現回数ではない。件数は `grep -o | wc -l` で数える」を追記した。
