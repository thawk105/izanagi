
### 項12 — 受入の既存運用を整理し、fixtureの待機上限を局所的に見直す設計を行う

対象: 未採番候補。資料: repo外inbox `2026-09-18-acceptance-gate-no-canonical-source-manager-thread.md`。
**決定:** 既存運用の整理と、受入用走査処理の待機上限を局所的に見直す設計を採る。120秒への変更は候補値であり、
実測で確かめるまで確定値にしない。走査対象・拒否能力を維持し、productionのtimeoutまで一律に変えない。
F945の従来のtimeout拡大見送りに対する再検討は、この受入fixtureの設計・検証範囲に限る。即時の数値変更ではない。
新しい投入slot機構、untracked等の走査削減、投入後のlive main照合条件変更は現時点では採らない。
inboxの門番条件値、FIFO、自動再投入、追加L2節を丸ごと採用した裁定でもない。既存DW-O18/O27の判定主体と
再走制限を維持する。原因や成功をload・他ユーザーprocessの本数だけで断定しない。

## D1877. 未追跡走査の時間切れは負荷に見合う値へ上げる (2026-09-09)

**決定:** `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` の setup が使う
`git ls-files --others --exclude-standard -z` の 30 秒 timeout を、混雑時の実所要に見合う値へ上げる。
値は据え置きの推測でなく、混雑下の完了時間を測って有界に決める。fixture の共有範囲は変えない。

**理由:**

- 単独走は緑で、他 wave の受入 session でも同じ file が赤になる。変更に帰属しない負荷の問題である。
- fixture の untracked 走査を session 単位へ寄せる案は、受入の並行性に新しい交絡を作る。
- hold 登録は赤を隠すだけで「混雑時に受入が取れない」を解かない。

**却下した選択肢:**

- 走査を session 単位へ寄せる — 設計変更で交絡が増える。
- 専用 F を起こして hold 登録する — 赤は消えるが受入は取れないまま。

### 項43 — 受入の実repo重複走査をmodule単位へ減らす

対象: T-2579。

**決定:** D1877の共有範囲固定・timeout延長方針を本件に限って変更し、実repo走査をmoduleごと1回へ減らして各testへ独立copyを渡す。未land案の既存real-repo inventory等への登録を使い、production timeoutと走査範囲は維持する。

**理由・採らない案:** 51回の取得直後にtest用値へ上書きしており重複走査に検査力が無い。取得処理がsiteを読まないので追加のsite偽装は課さない。未land案とD1877の衝突はこのユーザー裁定で限定解消する。
### F945. 受入のt1259 fixtureでGitの未追跡走査が30秒を超えて28件のsetup errorになった [テスト代表性] [計測汚染]

- 事象: T-2340 docs waveのtip59b932731の受入で、test_t1259_qsub_env_delivery_probe.pyの28件がテスト本体の前に落ちた。22563passed/68skipped/28error。
- 根本原因: autouse fixtureの_clean_detached_source_snapshotが実repoの_repo_snapshotを呼び、git ls-files --others --exclude-standard -zが30秒TimeoutExpiredとなった。個別の判定失敗ではなく共有走査の時間境界であり、遅延のI/O要因までは分離していない。
- 切り分け: 同tip・同fileをrun_tests.py --force-dispatchで単独再走し、991541.nqsvで51passed/15.45秒、job Elapse21S、rc0。waveの変更はdocsのみで、当該fixture・probe・Git呼出しは変更していない。
- 恒久対応: docs/dev-wave/operations.mdのDW-O18へ従い、単独非再現を確認して受入を再走する。timeout拡大・fixtureのstub化・除外・汎用gateの新設は行わない。
- 再発検知: setup tracebackのGit argvと30秒TimeoutExpiredを確認し、同tipの単独走と受入を区別して記録する。ログは専用handoffが指すacceptance-child-3とfocus-t1259.log。
- **再発: 2026-09-18** — T-2724/T-2776回収tip `d899c86aa` の受入shard0（6425.nqsv）で、T-1259のmodule fixtureが `git ls-files --others --exclude-standard -z` の30秒TimeoutExpiredとなり12 setup errors。全体は25153 passed / 69 skipped。test本体に入る前で、当該test/probeには今回の差分がない。正規runnerの同tip単独走でも51 setup errors（247.47秒）を再現したため、DW-O18に従い受入2を投入せず停止した。timeout/hold/除外は変更せず、T-2790の既存の設計・検証手番に範囲を残す。一次資料は `output/insights/2026-09-18/t2724-t080-defer-active-v2/README.md` の停止記録と回収jobの生log。
## DW-S05-A — 段 5 所有と投入

所有 path が素集合の単位ごとに別 worktree。依存完了後、所有 path 限定 patch
（`git add -A`→`git diff --cached <base> --output=<f> -- <所有パス>`→`git apply`、`<base>`=子作成 SHA。隔離 session は `git -C` 不可）だけ展開し並列投入。
worktree は`-b`必須(detachedは midflight rc=1)。
投入先へ cd せず直前に `tools/check_wave_startup.py --repo <abs> --mode midflight`。rc≠0 で停止。
乖離量は非関門。gate 実測 NOTE≠0 なら anchor 再読。
起動器は author/fix の投入先全残差を終端 commit、待ち手は呼出側指定 `--commit-worktree <abs>`。記録のみ (D2044 項 16)。
codex は `reasoning=medium`、`sandbox=workspace-write` とする。

## DW-S05-B — 段 5 権限と赤

権限は入口の凍結境界に従う。親・他単位の成果物の land まで意図的に赤になるテストを
xfail 化せず、既存テストの期待値も変えない。赤の内訳を報告に明記する。

## DW-S05-C — 段 5 実装子の検査・報告

実装子の prompt に次を全部入れる。

- 緑には実走 nodeid・範囲を併記。子の実走は親の全走を代替せず、実走不能なら
  `closed` でなく「実装済み・未実走」と書く。
- テスト新設・改名は親の名指しを網羅と見なさず、制約 meta-test を自ら洗い出し走らせる（F42）。
- fixture への現行 hash 差し込み等、テストを甘くして緑にしない（F27）。
  機構の正例・負例は実体を名指しし依存先を stub しない（F649）。
- 期待値へ揮発 payload (tree hash 等) を焼き込まず、理由と件数を固定して揮発部分を
  外し、揮発源を編集しても緑か確認する。
- 報告に所有外 caller・共有 fixture・consumer test への波及を静的列挙。
- 指示外の受理集合変更をせず、scope 前に現行の受理・拒否挙動を明記。
- 親 docs 未 land なら期待赤の finding 集合を事前指定し、他は回帰と報告する。
