# 段 1 棚卸し調査 s1-survey-3 (read-only、2026-09-30 01:2x JST 時点)

調査は repo (main f0869d953 同一) の grep / Read と、対象 path の ls / stat / cat で行った。何も変更していない。
grep 範囲は `docs/**`・`output/insights/**`・`tools/**`・`orchestrator/**`・`.claude/**`・`hooks/**` (系列 1 は `patches/`・`src/` も)。

### 系列 1: T-2724 (t2724-chain-scratch / t2724-g1-gen)
- worktree / branch / HEAD:
  - `.codex/worktrees/t2724-chain-scratch` / `scratch-t2724-chain-check` / `8298f7430` (locked。mtime 2026-09-18 10:57)。
    最後の commit は 2026-09-18 14:23「実装 commit 7a763575f を chain 有り scratch へ merge (land しない)」。main の祖先ではない (merge-base --is-ancestor が rc=1)。
  - `.codex/worktrees/t2724-g1-gen` / `freeze-g1-gen-t2724` / `32ba8cae4` (G。locked。mtime 2026-09-18 06:34)。**main の祖先である** (`git merge-base --is-ancestor 32ba8cae4 HEAD` が rc=0)。
  - どちらも tree には `output/` の未追跡らしい dir 群 (campaigns, pegasus-dispatch, s8b-freeze, task-runs 等) が見えるが、tracked の `output/` と区別できていない。
    唯一 `output/pegasus-dispatch/` は G 生成時の dispatch receipt / orphan-hold を置く先 (`output/insights/2026-09-18/t2724-freeze-g1-gen/evidence/g-commit.log:35,41,42` が path を記録)。中身は詳細に数えていない。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | output/insights/2026-09-26/carry-triage/README.md:88-89 | `.codex/worktrees/t2724-g1-gen`・`t2724-chain-scratch` | 経緯の記述 (残置と判断) | 「取り下げた T-1851・T-2724 には worktree が残る…稼働 wave ではなく残置と判断」 |
  | output/insights/2026-09-26/carry-triage/withdrawn.tsv:472 | T-2724 (取り下げ) | 経緯の記述 | 「旧系列を再開するとき再起票」 |
  | output/insights/2026-09-18/t2724-freeze-g1-gen/README.md:31 | `.codex/worktrees/t2724-g1-gen` (HEAD X1') | 再現手順 (blob 取り出し) | `git cat-file blob 15861416… > output/s8b-freeze/holdout_freeze.v2.g1.json` |
  | output/insights/2026-09-18/t2724-freeze-g1-gen/evidence/g-commit.log:35,41,42 | 同 worktree 内 `output/pegasus-dispatch/...` | 経緯の記述 (ログの path) | receipt の保存先の記録 |
  | output/insights/2026-09-21/t2344-closure-emitters/overlap_scan.log:20-38 | 両 worktree | 経緯の記述 (編集面重複検査の出力) | `DIFF 09-18 10:56 ... in .../t2724-chain-scratch/` |
  | output/insights/2026-09-19/t2778-child-worktree-cleanup/verbatim/measurements-overlap.txt:18-19 | 両 worktree・branch | 経緯の記述 | `t2724-g1-gen [freeze-g1-gen-t2724] committed=none dirt=none` |
  | docs/decisions.md:68802 | G `32ba8cae4` | 固定 (発効版 ref。commit は main の祖先) | 「G 32ba8cae4 と X1' cc82edc8c が main の祖先であることは成立 (実測)」 |
  | docs/archive/worklog-phase3-0918-1640.md:21-22, 652 | G・branch `freeze-g1-gen-t2724` | 経緯の記述 | 「G は peer が保全して正式停止」 |
  | docs/archive/worklog-phase3-0920-1717.md:1,3,4 | G `32ba8cae4`・一次資料 | 経緯の記述 | 「G は作った。land はしていない」 |
  | docs/archive/worklog-phase3-0919-1688.md:3 / 0920-1716.md:589 | chain/X2/G の main 取り込み | 経緯の記述 | 「chain/X2/G は main に着地」 |
  | output/insights/2026-09-21/t2812-old-series-realignment/{README.md:29, evidence/probe-2.json:438, verbatim/*}、2026-09-21/t2824-g1-candidate-removal/{README.md:33, evidence/reverify-*.json:8, verbatim/*} | G `32ba8cae45001697…` (generation_commit) | 発効版 (ref) / 経緯。SHA は commit 名で、worktree の path ではない | `"generation_commit": "32ba8cae4…"` |
  | docs/paper-story/2026-09-17.md:698,2448、2026-09-19.md:51,140-148,651,741-765,955,1241,1716-1717 | [T-2724] (branch 名は `freeze-g1-chain-t2724` で別) | 経緯の記述 | 一次資料は `output/insights/2026-09-17/t2724-…`・`2026-09-18/t2724-…` の README を指す (worktree は指さない) |
  - branch `scratch-t2724-chain-check` を名指すのは measurements-overlap.txt:18 の括弧書きだけ。SHA `8298f7430` を名指す file は 0 件。
- 研究での使用判定: **不要**。
  - (a) 当たらない: paper-story は T-2724 を引くが、根拠先は repo 内の insight README (`t2724-freeze-v2-g1-candidate` / `t2724-freeze-g1-chain-land` / `t2724-t080-defer-active-v2`) で、worktree の中身を数値・図の原本にしていない。
  - (b) 当たらない: `docs/phase3.md`・`docs/worklog.md` に T-2724 の記述は無い (grep 0 件)。T-2724 自体が carry-triage で「取り下げ」済み (withdrawn.tsv:472)。
  - (c) 当たらない: 凍結 v2 g1 の批准は G の commit SHA を束縛するが、G は main の祖先なので `freeze-g1-gen-t2724` branch が消えても SHA は main の履歴から解決できる。
  - `scratch-t2724-chain-check` は「land しない」scratch の merge で、main に無い commit が 2 本以上ある。中身は 2026-09-18 の chain 検証用の実験木。名指しも consumer も無い。
- consumer (コード・テストが読む): **なし** (orchestrator / tools / hooks / .claude / patches / src を worktree path・branch 名・SHA で grep して 0 件。G の SHA 全桁は insight の JSON にだけある)。
- 回収するなら写すべき中身: なし。ただし scratch branch は main に無い commit を持つので、撤去は bundle 退避 → branch -D が既定手順 (memory の掃除規律)。
- 不確実な点: 各 tree の `output/` 内の未追跡物の有無と量は `find` の guard 制約で軽い一覧しか取れず、pegasus-dispatch 以下の receipt の量は未確認。carry-triage の「稼働なし」判断は 2026-09-26 時点で、本調査では両 tree の最終 mtime (09-18) 以降 12 日変化なしを確認しただけ。

### 系列 2: T-2853 R2 の作図木 (fig8b 系 3 本 + fig6 系 1 本)
- worktree / branch / HEAD (いずれも main と同内容の tree + 未追跡 `scratch/`):
  - `.codex/worktrees/t2853-r2-plot-author` / `t2853-r2-plot-author` / `cb241cf43` (mtime 09-28 08:16)
  - `.codex/worktrees/t2853-r2-plot-fix1` / `t2853-r2-plot-fix1` / `58c35f73a` (09-29 02:32)
  - `.codex/worktrees/t2853-r2-plot-fix2` / `t2853-r2-plot-fix2` / `e21f84c1c` (09-29 02:47)
  - `.codex/worktrees/t2853-r2-fig6-author` / `codex/t2853-r2-fig6-author` / `aee09255a` (09-29 15:06、branch 参照の mtime 15:09)
  - 各木の `scratch/` の中身 (`find -maxdepth 3`): fig8b 系は `t2853_r2_fig8b_plot.py` と `out/` (PNG・PDF・provenance・表 md。author は `__pycache__` も)。
    fig6 系は `t2853_r2_fig6_plot.py` と `out/` (PNG・PDF・provenance・wrapper.json・比較 md) と `tmp/certification-one-byte.json`。campaign dir・WAL・receipt は tree の `scratch/` には無い。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | output/insights/2026-09-28/t2853-r2-fig8b/verbatim/s5-author-report.md:1,9,11,16,25,37 | `t2853-r2-plot-author/scratch/...`・`.../tools/plotting/plot_b10_static_tail_formal.py` | 経緯の記述 (実装子の報告の逐語) | 「作成した使い捨て wrapper は scratch/t2853_r2_fig8b_plot.py のみ」 |
  | 同 verbatim/s6-fix1-report.md:1,16,17 | `t2853-r2-plot-fix1/scratch/...` | 経緯の記述 (逐語) | 同上 |
  | 同 verbatim/s6-fix2-report.md:1,17 | `t2853-r2-plot-fix2/scratch/...` | 経緯の記述 (逐語) | 「r2-single と r2 は…」 |
  | output/insights/2026-09-28/t2853-r2-fig8b/README.md:239-243 (§5.2)、:281 | wrapper の「repo 外の使い捨て」・永続の保管先 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/tools/` | 原本の所在 (repo 外 durable) | 「repo には入れていない」。木の path は名指しせず |
  | output/insights/2026-09-29/t2853-r2-fig6/verbatim/s5-author-prompt.md:1-22 | `t2853-r2-fig6-author` の path・`WT/scratch/…` | 経緯の記述 (逐語の依頼文) | 「`scratch/` は untracked のまま置く。commit しない」 |
  | 同 verbatim/s5-author-report.md:1,6,13,20,24 | `t2853-r2-fig6-author/scratch/...` | 経緯の記述 (逐語) | wrapper sha256 `e3367d04…` |
  | 同 README.md:138 | 子 worktree の `scratch/` | 経緯の記述 | 「子 worktree の scratch/ に書き、親が実行後に repro-archive/tools/ へ写した」 |
  | 同 README.md:78,123,132-133,171-172、figures/README.md:19、figures/fig6_r2_a2_certification.provenance.json:11-29,754-759 | `/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/` | 原本の所在・再現手順 (repo 外 durable) | 図・collect-root・wrapper はここにある |
  | docs/phase3.md:44-51 | T-2853 R2 の fig8b・fig6 単位 (記録 = 上記 insight README) | 経緯の記述 | 「fig6・fig8b 以外の R2 と job body の opt-in は残り」 |
  | docs/paper-story/2026-09-29.md:16-17,32,59,73,213-215 | R2 fig8b (path は `output/insights/2026-09-28/…` を指す) | 経緯の記述 | 「R2 の wave が insight に残した fig8 形の図 2 枚は論文図ではなく、§8 B-10 から path で指すだけ」 |
  - 木の path・branch 名・HEAD SHA を名指しするのは、上記の逐語 (verbatim) と README:138 のみ。docs / tools / orchestrator / .claude には 0 件 (grep `t2853-r2-plot`・`t2853-r2-fig6-author`・`t2853_r2`)。
- 研究での使用判定: **不要** (4 本とも)。
  - 確認した事実 (repo 外 durable が既にある):
    - fig8b 系: wrapper の永続版 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/tools/t2853_r2_fig8b_plot.py` の sha256 = `c6aa8117…`。fix2 木の `scratch/t2853_r2_fig8b_plot.py` と**一致**。
      図 (PNG・PDF・provenance ×2・`four_group_table.md`) も同 dir の `figure/` にある。fix2 が最終版。author・fix1 の wrapper は旧版で、それらの `out/` は fix2 で置き換わった途中経過。
    - fig6 系: `/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/tools/t2853_r2_fig6_plot.py` の sha256 = `e3367d04…`。fig6-author 木の wrapper と**一致**。
      同 archive に `figure/`・`control/`・`collect-root/`・README がある。
    - 図そのものは repo 内にも派生物がある: `output/insights/2026-09-28/t2853-r2-fig8b/figures/` (PNG・provenance 各 2) と `output/insights/2026-09-29/t2853-r2-fig6/figures/` (PNG・provenance・表 md)。README は insight 側が原本と bytes 一致と記す (fig8b README:230-231、fig6 README:123)。
  - (a) 当たらない: paper-story は R2 fig8 形の図を「論文図ではない、path で指すだけ」と明記 (paper-story/2026-09-29.md:32)。fig6 R2 を論文図として引く記述は paper-story に無い (grep `t2853-r2-fig6` で 0 件)。仮に使っても、図・wrapper とも repo 内 insight と repo 外 durable にあり木の中身は provenance に過ぎない。
  - (b) 当たらない: phase3.md:44-51 は R2 fig8b・fig6 を完了の記録として書くだけで、木の path を今後の入力としていない。worklog 末尾 (1952〜1954) は VHash 系で T-2853 の R2 を入力に取らない。
  - (c) 当たらない (該当する事前登録は各 insight の R2 地位の記述で、入力は repo 外 durable path 側)。
- consumer (コード・テストが読む): **なし** (grep 0 件)。
- 回収するなら写すべき中身: なし (要らない判定)。念のため、4 木の `scratch/out/` にある途中経過の図・wrapper 旧版だけは repo にも repo 外 durable にも無いが、いずれも最終版に置き換わった旧版で、研究上の主張の根拠にはならない。
- 不確実な点: fix2 木の `scratch/out/` と durable `figure/` の全 file の sha256 照合は wrapper 以外は行っていない (insight README が PNG・PDF・provenance の bytes 一致を review 済みと記す。fig8b README:298-311 の review 記述を信用)。fig6 R2 の図が今後の論文稿で fig6 として引かれるかは paper-story に現れず未確認。

### 系列 3: vhb-mw9 / vhb-mw10 (VHash hot-block 系の計測木)
- worktree / branch / HEAD: `.claude/worktrees/vhb-mw9` と `vhb-mw10`。どちらも detached `b42cba01e` (**main の祖先**)。mtime は mw9 が 09-29 08:17、mw10 が 09-29 10:04。約 15〜17 時間前で止まっている。
- 特定: wave `dev-wave-vhash-hot-block-microbench` (T-2878、docs/archive/worklog-phase3-0929-1919.md:1〜14。一次資料 `output/insights/2026-09-29/vhash-hot-block-microbench/README.md`) の本走 2 (run2、`b42cba01e`) の計測木。
  raw の `raw/run2-b42cba01e/20260928T232237Z-4a650961.json:16` が mw9、`…232340Z-00bc28d9.json:16` が mw10 の `tools/vhash_microbench/hot_block_bench.cc` を bench 実体の path として記録している。
  兄弟の mw4・mw5・mw6 も run1 の raw が同様に名指す (本担当外)。
- 稼働 wave か: **稼働中ではない**。
  - wave の完了記録: worklog archive の 0929-1919 entry (T-2878、着地済み。branch 名の D2285 で置き場を裁定)。`b42cba01e` が main の祖先であることを確認。
  - 稼働中の VHash wave は `dev-wave-vhash-hot-block-cicada` (job dir、2026-09-30 01:22 に `run-dispatch.sh perf1b` が `vhb-m0` と scratch `/work/SFC/tanab/tmp/vhash-hot-block-2026-09-29/scratch/perf1` で走行中、ps で確認)。
    この wave は `vhb-m0` (locked)・`.codex/worktrees/vhb-u1/u2` を使い、job dir 内に `vhb-mw` の名指しは無い (grep `vhb-mw` 0 件)。**mw9/mw10 は別 wave (microbench) の残置**。
  - `dev-wave-jobs` に `dev-wave-vhash-hot-block-microbench*` の job dir は既に無い。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | output/insights/2026-09-29/vhash-hot-block-microbench/raw/run2-b42cba01e/20260928T232237Z-4a650961.json:16 | `.claude/worktrees/vhb-mw9/tools/vhash_microbench/hot_block_bench.cc` | 経緯の記述 (raw の bench 実体 path。データ) | 計測 shard の記録項目 |
  | 同 …/20260928T232340Z-00bc28d9.json:16 | `.claude/worktrees/vhb-mw10/tools/vhash_microbench/hot_block_bench.cc` | 同上 | 同上 |
  - この 2 件以外に mw9 / mw10 を名指す file は repo に無い (docs・tools・orchestrator・.claude を grep)。SHA `b42cba01e` は README:165,195-196,213-214 と archive worklog:9 に載るが、commit として main に在り、木の所在ではない。
- 研究での使用判定: **不要** (稼働中でもない)。
  - (a) 当たらない: 数値・図は repo 内 insight の `raw/run2-b42cba01e/*.json`・`figures/`・README にあり、README 側が一次資料。木は bench 実体を置いた場所の記録。
  - (b) 当たらない: worklog 末尾 (1952〜1954) と phase3.md は microbench の木を入力にしていない。worklog:T-2891 の「延長」は insight README §6 を参照するだけ。
  - (c) 当たらない。
- consumer (コード・テストが読む): **なし**。
- 木の中身: 通常の repo checkout + 未追跡 `output/`。mw10 の `output/pegasus-dispatch/` に約 18 個の request dir (09-29 08:42〜10:04 の dispatch receipt)、mw9 は 1 個 (08:46)。insight への写しは raw JSON 側にある。receipt 本体は repo に無く、名指しもされていない (再現手順に要るとは書かれていない)。
- 回収するなら写すべき中身: なし。
- 不確実な点: pegasus-dispatch の receipt を将来の監査で使うかは、microbench README §7 (無効にした走の経緯) が receipt path を名指ししているかを本調査では全文確認していない (`vhb-mw` での grep 0 件なので木経由の path はない)。

### 系列 4: vhash-readonly-share の mutation scratch2 と branch md2-pack-hint-fix
#### 4-a `/work/1/SFC/tanab/tmp/vhash-readonly-share-2026-09-29/mutation/scratch2/.izanagi-mutation-worktree/repo`
- worktree / branch / HEAD: `.git` は `.git/worktrees/repo` を指し、HEAD は detached `1ec90f6d3`。mtime は scratch2 が 09-29 18:50、repo が 18:51。5 時間強前。
- どの wave か: **`dev-wave-vhash-readonly-share`** (worklog 1946「read-only tx が…86 条件」、md_15、一次資料 `output/insights/2026-09-29/vhash-readonly-share/`)。
  `mutation/run-final.sh:3-13` が `--task mutation --scratch-root "$M/scratch2" --commit 1ec90f6d3`、投入元 `vhash-ros-mu0` を明記 (`final.log` の dispatch も 35877.nqsv)。mutation harness の固定名 `.izanagi-mutation-worktree/repo` は harness が作る使い捨て木。
- 終わっているか: **終わっている**。同 dir の `handoff.md` に「wave 完了: land 済み main 895765609、撤去済み。本 file は記録として残す」(最終更新 09-29 20:54)。
  `land.log` は `"status":"landed"`・`main_after 89576560…`・`landing_tip b11ad0f30…`。`cleanup.log` は mu0・wave 木とも `removed` (20:51/20:53)。
  変異結果は handoff に「20 件すべて登録どおり」。この後に scratch2 の mtime が更新された形跡は無い (最新 mtime は 18:51)。稼働中の対象ではない。
  なお scratch3〜5 は別の再走用 dir で、scratch2 の repo は final (probe) の残置。現在稼働中の mutation は `dev-wave-land-cleanup-enforce` の `mutation-scratch-final` (ps で確認、別 wave) で、こちらの scratch2 とは無関係。
- 名指し表 (`mutation/scratch2` の path 断片 / `.izanagi-mutation-worktree`):
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | (repo 内) `output/insights/2026-09-29/vhash-readonly-share/README.md` ほか | `tmp/vhash-readonly-share-2026-09-29/raw/measure-m*.json` は名指すが `mutation/scratch2` は名指さない | — | grep `mutation/scratch`・`vhash-readonly-share-2026` の該当は raw と figures の provenance のみ |
  | docs/failures.md:14913,15460,17559,25825,27929 と docs/pegasus-runbook.md:1538 | `.izanagi-mutation-worktree` (一般論) | 経緯の記述 (harness の固定名の説明) | 「container 名が固定なので --scratch-root を N 個に分ける」 |
  - この scratch2 の path を名指す repo 内 file は 0 件 (docs / output/insights / tools / orchestrator / .claude を grep)。
- 研究での使用判定: **不要**。(a)〜(c) いずれも当たらない。変異の判定は insight README に取り込み済みで、木は harness の実行残置。
- consumer: **なし** (コード・テストは path 固定でなく `--scratch-root` 引数で受ける)。
- 回収するなら写すべき中身: なし。ledger は `mutation/ledger-final*.json` が同じ dir に別に在る (この scratch2 の外)。
- 不確実な点: `.git/worktrees/repo` という汎用名の admin dir が repo 本体の `.git/worktrees/` にあり、撤去は `git worktree remove` (または rm + prune) で admin entry も消す必要がある。他の mutation harness が同じ名前 `repo` を再利用する可能性 (`.git/worktrees/repo` は 1 個だけで、他 wave のものかは未確認)。

#### 4-b branch `md2-pack-hint-fix` (`md2-pack-hint` は存在しない)
- branch: `md2-pack-hint-fix` → `e3ae6bbbf` (作成 2026-09-29 18:40、wave の fix 子の commit)。`md2-pack-hint`・`md2-pack-hint-author` の branch は既に無く、`.git/worktrees/` にも md2 の entry は無い (木は撤去済み)。
- どの wave か: **`dev-wave-md2-push-pack-hint`** (md_2、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-md2-push-pack-hint/`)。
  `child-worktrees.json` が author 子と fix 子 (`.codex/worktrees/md2-pack-hint-fix`、branch `refs/heads/md2-pack-hint-fix`) を登録。目的は `/cleanup-branches` §5 に「push が loose object corrupt で落ちたとき送信範囲を pack 化する 1 行」を足すこと。
- 終わっているか: **終わっている (land 済み)**。`land-1.log` は `"status":"landed"`・`main_before 799cd8fa5…`→`main_after 2e9514b7…`・`landing_tip 8d995083f…`。`cleanup-wave.log` は wave 木を `removed`。job dir の最終 mtime は 09-29 19:49。
  - main に反映済みの証拠: `tools/check_docs.py:288` に `".claude/commands/cleanup-branches.md": TextLimit(7_437, 110)` (fix 子が入れた 7_437。元は 7_058)。
  - branch 先端 `e3ae6bbbf` 自体は main の祖先ではない (`git merge-base --is-ancestor` rc=1)。fix 子の commit を wave 側へ「patch を diff -u で取り出して apply」する運用のため (handoff-final:「fix 統合 a9a96fd2a」)。差分は `tools/check_docs.py`・`orchestrator/tests/test_check_docs.py` の 2 file、13 行追加 12 行削除。内容は上記のとおり main に入っている。
- 名指し表: `md2-pack-hint-fix`・SHA `e3ae6bbbf` を名指す repo 内 file は 0 件 (docs / output / tools / orchestrator / .claude を grep)。job dir 側 (`child-worktrees.json`、`handoff-final.md`) のみ。
- 研究での使用判定: **不要** (wave 完了、内容は main、名指し 0)。
- consumer: **なし**。
- 回収するなら写すべき中身: なし。branch 先端は main に SHA として無いため、撤去は bundle 退避 → `branch -D` が既定。
- 不確実な点: 親 wave の `md2-pack-hint-author` branch と 2 木が撤去済みなのに fix branch だけ残った理由は cleanup ログから読めなかった (`cleanup-wave.log` は wave 木のみ removed)。

## 1 行要約表

| 系列 | 判定 | 主根拠 |
|---|---|---|
| 1 T-2724 (`t2724-chain-scratch` / `t2724-g1-gen`) | 不要 (撤去可。scratch branch は bundle 退避してから) | G `32ba8cae4` は main の祖先。T-2724 は withdrawn (`carry-triage/withdrawn.tsv:472`)。名指しは経緯のみで consumer 0、phase3.md・worklog に該当なし |
| 2 T-2853 R2 (`t2853-r2-plot-author`/`-fix1`/`-fix2`/`-fig6-author`) | 不要 | wrapper は repo 外 durable (`b10-backoff-grid-t2853-r2-20260928/tools/`、`izanagi-repro-archive/t2853-r2-fig6-20260929/tools/`) に sha256 一致で既在。図は insight にも既在。author・fix1 は旧版。paper-story は R2 fig8 形を論文図としない |
| 3 `vhb-mw9` / `vhb-mw10` | 不要 (稼働中でもない) | wave `dev-wave-vhash-hot-block-microbench` (T-2878、着地済み、HEAD `b42cba01e` は main の祖先) の run2 計測木。名指しは raw JSON の bench path 2 件のみ。稼働中の VHash wave は `dev-wave-vhash-hot-block-cicada` で `vhb-m0` を使い mw9/10 を使わない |
| 4-a `vhash-readonly-share-2026-09-29/mutation/scratch2/.izanagi-mutation-worktree/repo` | 不要 (稼働中でもない) | `dev-wave-vhash-readonly-share` (md_15) の変異 harness 残置、HEAD `1ec90f6d3`。wave は 09-29 20:23 land・20:53 撤去済み (handoff.md・land.log)。repo 内名指し 0 |
| 4-b branch `md2-pack-hint-fix` (`md2-pack-hint` は不存在) | 不要 | `dev-wave-md2-push-pack-hint` (md_2) は land 済み (land-1.log)。内容は main (`tools/check_docs.py:288` の 7_437)。branch 先端 `e3ae6bbbf` は main の祖先でないので bundle 退避が要る |
