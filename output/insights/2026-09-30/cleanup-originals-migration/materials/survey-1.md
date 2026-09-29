# 段 1 棚卸し調査 系列 1 (T-1505 / T-2489 / T-2792 / T-2795 / T-2797 / T-2273)

調査時点: 2026-09-30 JST。repo = `dev-wave-cleanup-originals-migration` (main `f0869d953` と同一内容)。read-only。
検索は 3 種 (job dir / tree 名の path 断片、branch 名、HEAD SHA) で `docs/` `output/` `orchestrator/` `tools/` `hooks/` `.claude/` `.codex/` `src/` `patches/` を全走査した。
名指しの全数は付録 A (系列別、file 数と file:line の一覧) に置く。本文の表は目的分類ごとに束ねた代表行と件数である。

## 0. 先に読む要点

1. **コード・テストが系列 1〜8 の worktree path / branch / SHA を読む consumer は 0 件。** `orchestrator/` `tools/` `hooks/` `.claude/` `.codex/` `src/` `patches/` を
   `submit-tree-r4|submit-tree-pair|b5-main-run|b5-contrast|t1505-a1|t2489|t2792|b5-effect|6fce61d6|t2273-shard0` で検索し、当たったのは
   `orchestrator/tests/test_b5_llm_round.py:22` (`PILOT = ROOT / "output/insights/2026-09-20/t2797-b5-contrast"`) の 1 件だけで、これは repo 内 insight を読むもので worktree ではない。
   `dev-wave-jobs` を含むコードは A-1 policy json・test 数本にあるが、名指しは T-1505 / T-2792 の tree ではない (下記系列 1・3 の確認範囲)。
2. **(a)(b)(c) のどれにも当たる系列は無い。** paper-story が使う数値・図はすべて repo 内に派生物がある (結果稿・insight の表と script 出力・図の provenance json)。
   `docs/phase3.md` と `docs/worklog.md` 末尾 2 エントリ (entry 1953・1954、および 1952 まで見た) に、これらの path / ref を今後の入力にする記述は無い。
   有効な事前登録で入力に取るものも無い (B-5 v1 は §15 erratum で閉鎖、v2 は D2259 で発効せず)。
3. **campaign 原本の repo 外保全先が既にある:** `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/` (T-2853、原本と写しの sha256 全件一致、9,107 file)。
   B-5 試走 (系列 5)・K2 (系列 4)・A-1 durable authority (系列 1・3 の測定本体) が入っている。**B-5 本走 (系列 6・7) の tree と T-2489 は入っていない** (本走は 2026-09-23 21:53 投入で、写しの 08:25〜08:51 より後)。
4. **B-5 (T-2797) の論文での使い方:** 論文ストーリーが使うのは (i) 試走 (系列 5) の限定付き観測 C38、(ii) 本走 v1 の「投入・中断・6 比較すべて判定不能・費用 (12 job 計 126,426 s = 35.1 node 時間、非 LLM の計算の 95.0 % が検証)」だけ。
   数値の一次抽出は `output/insights/2026-09-26/t2797-b5-cost-options/` (README と `data/b1s1-jobs.tsv`・`b1s1-sessions.tsv`・`cost-model.txt`) にあり、repo 内に派生物が既にある。
   **v1 の生成器比較の結果 (throughput・優劣) は論文に使われていない** (判定不能で確定、v1 §15)。
5. **K2 (T-2795 / T-2860):** 論文ストーリーが使う 4 巡の値・図 12・結果稿は repo 内にある。原本 (WAL・lock 等) は repo に入れられない (guard の防護対象) ので、結果稿 §5.1 が原本 path と sha256 を「所在記録」として書く。
   その原本は (1) 各 submit-tree、(2) job dir 内の byte 複製 `originals-copy-2026092{0,2}/`、(3) repro-archive の写し、(4) T-2860 job root の `ao-root/` (AO 取込み済みの写し) の 4 か所にある。
   3 巡分 (巡 1〜3) の原本は F1034 で消失済みで、本系列のどの tree にも無い。

## 1. 系列一覧の実測 (git worktree list)

| 系列 | worktree / branch | HEAD | lock | 備考 |
|---|---|---|---|---|
| 1 T-1505 A-1 sized | `dev-wave-jobs/dev-wave-t1505-a1-sized-submit/submit-tree` (gitdir `submit-tree1`) | `d2ebef7a4` detached | locked | 依頼の path と一致 |
| 2 T-2489 A-2 nodes5 | `dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree` (gitdir `submit-tree3`) | branch `probe/t2489-a2-nodes5-submit` = `3f61c3408` | locked | branch は main 先行 1 commit (`git log main..` で 1 行) |
| 3 T-2792 A-1 attempt2 | `dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/submit-tree` (gitdir `submit-tree5`) | `fec4a8187` detached | locked | |
| 4 T-2795 K2 pair | `dev-wave-t2795-k2-pair/submit-tree-pair` | `6a3e15809` detached | locked | |
| 4 T-2795 再投入 | `dev-wave-t2795-k2-pair-resubmit/submit-tree-pair2`・`submit-tree-r4` | いずれも `8fd2a2f5c` detached | locked | K2 4 巡目 = r4 |
| 5 T-2797 B-5 試走 | `dev-wave-t2797-b5-contrast/submit-tree` | `11d46a74a` detached | locked | 同 dir の `mutation-source/`・`mutation-scratch-*` は登録 worktree ではない (独立 clone / scratch) |
| 6 T-2797 B-5 本走 | `dev-wave-t2797-b5-main-run/submit-trees/{calib,t01..t12,t15,t16,t17}` = 16 本 | いずれも `6fce61d6e` detached | locked | 依頼の「16 本」と一致 (t13・t14 は EINTR で作成失敗のため無い) |
| 7 発効木 | `izanagi/.claude/worktrees/t2797-b5-effect` | `6fce61d6e` detached | locked | branch `worktree-dev-wave-t2797-b5-main-run` = `b3eb51327` |
| 8 T-2273 | checkout 無し。branch `worktree-t2273-shard0-local-copy` = `5c51e958e` | (`eb65d322f` + main `620a6bb13` の merge) | — | main 先行 2 commit (`eb65d322f`・`5c51e958e`) |

注: 依頼の「dev-wave-t2489-a2-nodes5-probe/submit-tree」は実在する (branch 付き)。`6fce61d6e` を含む ref は `git branch -a --contains` で `worktree-dev-wave-t2797-b5-main-run` の 1 本だけ
(`git merge-base --is-ancestor 6fce61d6e main` は rc=1、main の祖先でない)。

## 2. 系列別

### 系列 1: T-1505 A-1 sized attempt-0001 (`dev-wave-t1505-a1-sized-submit/submit-tree`)
- worktree / branch / HEAD: 上表。local main `d2ebef7a4` の固定 checkout。job dir に `run-*.sh`・`third-party-hydrated/`・`hydrate*.json`・受領証・`wave-usage.json` 等 (job dir 自体は撤去対象の外)。
- 中身の概要: 追跡済みの main 写し + 未追跡は `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` の 4 file (README.md・receipt.json・result.json・.complete.json、materializer が排他作成) と、`.gitignore` 対象の `output/env/pegasus/silo_ladder_rung1/job-staging/`。
  **4 file は repo の同 path の 4 file と `cmp` で byte 一致** (実測)。campaign 原本は tree に無い (測定本体は `dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001` = repro-archive に写し済み、系列 1・3 とも)。
- 名指し表 (代表。全数は付録 A の p1):
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md:23` | submit-tree path・`d2ebef7a4` | 固定 checkout (投入元) | 「submit-tree: ... = local main `d2ebef7a...` の detached worktree」 |
  | 同 `:8`・`:29` | 公開 leaf の destination | 原本の所在 | 「materializer が submit-tree に排他作成したものを byte 保持で複製」 |
  | 同 `:84` | submit-tree | 原本の所在 (撤去禁止の当時方針) | 「submit-tree と耐久 base は本 wave では撤去しない (原本の所在。撤去は別途の掃除判断)」 |
  | 同 `MANIFEST.tsv` (15 行)・`receipts/attempt-0001.intent.json` (12)・`receipts/submission.json` (12)・`receipts/job-terminal-*.json` (3)・`verbatim/hydrate*.json` (2) | tree path 文字列 | 経緯の記述 (受領証・sha256 束縛 bytes に path が埋まる) | path は記録の一部で、tree の存否は検査しない |
  | `output/insights/2026-09-13/paper-story-a1-balanced5-sized/{receipt,.complete}.json` | destination の tree path | 経緯の記述 (公開 leaf 内) | 結果稿 §5.2 が sha256 で束縛する bytes |
  | `docs/failures.md:20505` | tree path | 経緯の記述 (F1034 再発 6 例目) | 「path `<job dir>/dev-wave-t1505-a1-sized-submit/submit-tree`」 |
  | `output/insights/2026-09-21/land-roundtrip-diagnosis/{README.md:103,land-attempts-timeline.txt}`、`2026-09-19/a1-sized-attempt2/verbatim/precheck.log:136`、`2026-09-20/t2792-a1-sized-attempt2/verbatim/extract-attempt1.md:49`、`2026-09-18/t2775-a1-sized-results-draft/verbatim/arms-and-recheck-1.txt` | tree path | 経緯の記述 (診断・逐語) | |
  | `docs/archive/worklog-phase3-0918-1636-1637.md`、`docs/spool/FOLDED.md` (2) | wave 名 `dev-wave-t1505-a1-sized-submit` | 経緯の記述 | |
- 研究での使用判定: **不要**。(a) 論文ストーリーの数値・図 (`docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`、図 9) は repo 内に派生物があり (leaf 4 file が repo に byte 一致で在る、MANIFEST・receipts・結果稿)、
  tree から新たに得るものが無い。(b)(c) 該当なし (確認範囲: `docs/phase3.md`、`docs/worklog.md` の entry 1952〜1954 の各「次の一手」、`docs/*preregistration*` を `t1505` / tree path で検索して 0 件)。
- consumer: なし。`orchestrator/campaign/paper_story_a1_paired*.json` 等の `dev-wave-jobs` 参照は durable base (`dev-wave-paper-story-a1-balanced5-sized-20260913`) であり、`dev-wave-t1505-a1-sized-submit` の名指しは 0 件 (grep)。
- 回収するなら写すべき中身: 不要 (leaf 4 file は repo に在る)。job dir 側の `run-*.sh` 等は job dir 内なので tree 撤去と無関係。
- 不確実な点: tree 内の未追跡物の全数は `git status` を打たず (read-only 縛り)、`output/insights/2026-09-13/` の leaf と `job-staging` を見た範囲。他の未追跡物の有無は未確認。

### 系列 2: T-2489 A-2 nodes=5 probe (`dev-wave-t2489-a2-nodes5-probe/submit-tree` + branch `probe/t2489-a2-nodes5-submit`)
- worktree / branch / HEAD: 上表。branch の 1 commit `3f61c3408` = 「A-2 policy の `scheduler.nodes` を 5 にした使い捨て submit-tree commit (main へ入れない)」。`3f61c3408` を含む ref はこの branch のみ。
- 中身の概要: main `d2ebef7a4` + 上記 1 行編集の checkout。測定本体 (attempt `t2489-20260918a`) は tree 内ではなく `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2489-20260918a/` (README:12)。repro-archive には入っていない。
- 名指し表 (代表。全数は付録 A の p2):
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:9-12` | branch・`3f61c3408` | 経緯の記述 + 発効版 (ref) | 「実走した source commit: `3f61c3408` ... 使い捨て commit (branch `probe/t2489-a2-nodes5-submit`、main / wave branch へ入れない)」 |
  | 同 `:52`・`:277` | submit-tree path・HEAD | 固定 checkout (投入元) / 再現手順 | 「投入元 ... (git worktree、branch ..., `git worktree lock` 済み)」 |
  | 同 `:228` | `3f61c3408` | 原本の所在 | 「使い捨て commit `3f61c3408` は submit-tree の branch にだけ在る」 |
  | `output/insights/2026-09-18/t2489-a2-nodes5-probe/verbatim/{s1-brief,s4-ruling,s5-author}.md` | branch・path | 経緯の記述 | |
  | `output/insights/2026-09-19/t2489-a2-nodes5-local-lock/README.md:1 件`、同 `evidence/*` (mutation-results 12・qstat 4・acceptance1) | wave 名 | 経緯の記述 | |
  | `docs/paper-story/2026-09-21b.md:2583,2630,3019,3208,3576,3634,3900` | insight 名 (path・branch は名指さない) | 経緯の記述 | 「A-2 の nodes=5 probe ... を A-2 の attempt に数えない」 |
  | `docs/archive/worklog-phase3-0918-1647.md` (3)、`docs/spool/FOLDED.md`、`docs/unreachable-object-ledger.md:256-257,345` (別 branch `impl-dev-wave-t2489-nodes5-local-lock` の記録) | wave 名 | 経緯の記述 | |
- 研究での使用判定: **不要**。(a) 論文ストーリーは probe の所要 (約 50 分 → 12 分 08 秒、node 秒 +16 %) を「運用素材」として書くだけで A-2 の判定に数えない (2026-09-21b.md:3576,3634)。その数値は insight README にある。
  branch の中身は 1 行編集で README が内容を述べる (再構成できる)。(b)(c) 該当なし (確認範囲: phase3.md・worklog 末尾・`docs/*preregistration*`)。
- consumer: なし。
- 回収するなら写すべき中身: 不要。branch を消す場合の唯一の失われる物は commit `3f61c3408` (1 行編集の使い捨て commit)。惜しむなら `git bundle` 1 本で足りる。
- 不確実な点: attempt root (`izanagi-measurements/.../t2489-20260918a/`) は本系列の範囲外で存否を確認していない。probe の数値 (12 分 08 秒等) の一次はそちらで、repo 内 README に転記済み。

### 系列 3: T-2792 A-1 sized attempt-0002 (`dev-wave-t2792-a1-sized-attempt2/submit-tree`)
- worktree / branch / HEAD: 上表 (`fec4a8187` detached、locked)。
- 中身の概要: 系列 1 と同型。未追跡は `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` の 4 file で、**repo の同 path 4 file と byte 一致** (`cmp`、実測)。repro-archive README §2.4 も「4 file とも現行 repo の追跡下の同じ path の file と sha256 一致」と記す。
  測定本体は `dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002` (repro-archive に写し済み)。
- 名指し表 (代表。全数は付録 A の p3):
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md` (5 行)、`MANIFEST.tsv` (21)、`receipts/attempt-0002.intent.json` (12)・`submission.json` (12)・`job-terminal-*.json` (3) | tree path | 固定 checkout / 経緯の記述 (受領証に path が埋まる) | |
  | 同 `verbatim/*` (29 行、prompt-review 25・hydrate 2・extract 2・startup-gate 1) | tree path | 経緯の記述 (逐語) | |
  | `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/{receipt,.complete}.json` | destination path | 経緯の記述 (公開 leaf 内) | |
  | `output/insights/2026-09-23/t2853-repro-package-archive/README.md:73,…` (2) | `dev-wave-t2792-a1-sized-attempt2/` (`submit-tree/` を除く) | 原本の所在 (写し済みの記録) | 「a1-attempt2-jobdir ... 一致」 |
  | `docs/failures.md:20505` | tree path | 経緯の記述 (F1034 7 例目) | |
  | `output/insights/2026-09-20/t2243-collection-contention/verbatim/*` (6)、`2026-09-21/acceptance-gate-wait-diagnosis/verbatim/*` (14)、`land-roundtrip-diagnosis` (2)、`t2853-repro-package-estimate` (1) | tree path | 経緯の記述 (診断の生ログ) | |
  | `docs/archive/worklog-phase3-0920-1755.md` (2)、`docs/spool/FOLDED.md` (2) | wave 名 | 経緯の記述 | |
- 研究での使用判定: **不要**。(a) 結果稿 `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` と図 14 は repo 内の派生物 (leaf 4 file・MANIFEST・receipts) で足り、
  結果稿 §5.2 が sha256 を列挙する一次資料は durable base (tree ではない) にある。結果稿 :429・:442 は「submit-tree に排他作成した 4 file を byte 保持で複製」と書く所在記録。(b)(c) 該当なし (系列 1 と同じ確認範囲)。
- consumer: なし。
- 回収するなら写すべき中身: 不要。
- 不確実な点: 系列 1 と同じ (未追跡物の全数は未確認)。

### 系列 4: T-2795 K2 pair (`t2795-k2-pair/submit-tree-pair`、`t2795-k2-pair-resubmit/submit-tree-pair2`・`submit-tree-r4`)
- worktree / branch / HEAD: 上表。`submit-tree-pair` (`6a3e15809`) = 初回 pair (2026-09-20、stock が one-shot claim で停止し pair 不成立)。`pair2`・`r4` (`8fd2a2f5c`) = 再投入と 4 巡目 (campaign `p3-s4-loop-s4-autonomous-b24749ae`)。
- 中身の概要: 各 tree の `output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` (campaign.lock・loop_state.json・s4_loop_digest.txt・runs/wal.jsonl・knowledge_manifest_receipt.json・spec・variants・reports・insights) と `output/env/pegasus/claims/*.claim`、`output/exploration/namespace.json`。
  **repro-archive t2853-20260923 に 3 組とも写し済み** (`k2-pair-first-originals` 7 file・`k2-resubmit-pair2-originals` 8 file・`k2-resubmit-r4-originals` 8 file、sha256 全件一致)。
  job dir 内にも byte 複製 `originals-copy-20260920/` (pair)・`originals-copy-20260922/{pair,r4}/` (`MANIFEST.sha256` 付き) がある。T-2860 job root の `ao-root/output/exploration/campaigns/...b24749ae/` は r4 原本に AO (`runs/agent_outputs.jsonl` 3 行 32,549 B) を取り込んだ写し。
- 名指し表 (代表。全数は付録 A の p4):
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `docs/paper-story/results/2026-09-23-k2-manual-loop-four-rounds.md:174` | `submit-tree-r4/.../runs/wal.jsonl` (sha256 `6444159d…`、14,885 B) | **原本の所在** (結果稿 §5.1 の権威 bytes) | 「原本 `dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/submit-tree-r4/output/exploration/...`」 |
  | 同 `:175-178`・`:180` | r4 の lock・loop_state・digest・受領証、pair 再投入 WAL の byte 複製 (`originals-copy-20260922/pair/...`、sha256 `5415d01a…`) | 原本の所在 | |
  | 同 `:32,133-134,145,164` | r4 原本と写し `ao-root/` | 経緯の記述 (取込みは原本でなく写しの上) | 「巡 4 の取込み先は原本ではない」 |
  | `output/insights/2026-09-23/t2860-k2-round4-reflux/README.md:24,37,131` | lock 済み `submit-tree-r4` | 原本の所在 + 経緯 | 「原本 (lock 済み `submit-tree-r4`) には何も書いていない」「写しは job root の `ao-root/`」 |
  | 同 `materials/critic-input-4.json:20`・`critic-prompt-4.md:25` (critic-4 の入力に書かれた文) | 「別 submit-tree・別 WAL」 | 経緯の記述 (critic に送った bytes、改変不可) | |
  | `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:44,75,101,207` | pair2・r4・pair の path | 固定 checkout (投入元) / 原本の所在 (§9) | 「submit-tree は pair 走とは別の `submit-tree-r4` (同じ SHA・同じ PIN・別 out_root ...)」 |
  | 同 `evidence/attempt-{pair,r4}-0001/*` (job.stdout 各 7・reservation・masstree receipt)、`materials/epoch-diff-*.json`・`wal-outcomes-*.json` | tree path | 経緯の記述 (受領・所要の生記録) | |
  | `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md` (6)・`evidence/attempt-0001/*` (15)・`materials/*` (2)・`reviews/*` (49) | `submit-tree-pair` | 固定 checkout / 経緯 | |
  | `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:31,51,63-64,88,98-99,131,163,183` + `materials/reconstruction-*` (5) + `reviews/*` (5) | `submit-tree-pair` | 原本の所在 (F1034 の事後復元。当時「現存」の根拠) と再現手順 (`git worktree lock` の付随項) | 「pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5 一致)」 |
  | `output/insights/2026-09-21/t2795-pair-repair/README.md` (2)・`reviews/*` (5)・`verbatim/*` (1)、`t2795-pair-launcher/README.md` (1)、`t2812-old-series-realignment/evidence/probe-2.json` (13) | `submit-tree-pair` | 経緯の記述 (no-touch 指定・probe 記録) | `s1-brief.md:58`「no-touch ... submit-tree-pair」 |
  | `output/insights/2026-09-23/t2853-repro-package-archive/README.md` (8)・`verbatim/*` (26) | 3 tree の campaign 原本 | 原本の所在 (写しの記録) | 「k2-resubmit-r4-originals ... 一致」 |
  | `output/insights/2026-09-21/t2814-cleanup-command/{README.md,verbatim/*}` (4)、`2026-09-26/t2838-gate-argv-unify/verbatim/*` (21)、`2026-09-27/t2104-campaign-flock-scope/verbatim/*` (6)、`2026-09-29/t2871-policy-loop-iter/*` (3)、`t2243-collection-contention`・`acceptance-gate-wait-diagnosis` 等の診断生ログ | tree path | 経緯の記述 | |
  | `docs/paper-story/` の本文 (`2026-09-*.md`) | tree path・`submit-tree-pair/r4` の名指しは 0 件 (`docs/paper-story/results/2026-09-23-k2-...:174-180` の 2 行だけ、上記) | — | |
- 研究での使用判定: **不要**。(a) 論文ストーリー (結果稿 `2026-09-23-k2-manual-loop-four-rounds.md`、図 12 `fig12_k2_manual_loop_dataflow`) は 4 巡の値・判定・sha256 を結果稿・insight (`t2860-k2-round4-reflux/materials/run-summary-{r4,pair}.json`・`wal-refs-*.json`・`layer3_report.json`、`t2795-k2-pair-resubmit/materials/`・`evidence/`) に持つ。
  repo 内に派生物が既にあり、原本 (WAL 等) は「所在記録と sha256」を書く対象で、論文の数値を tree からしか得られないという状態ではない。
  さらに原本は tree 以外に 3 か所 (job dir の byte 複製、repro-archive、`ao-root/`) ある。(b) worklog 末尾 2 エントリ・phase3.md に K2 の次の一手が tree を入力とする記述は無い (T-2860 は完了して着地済み)。(c) 該当なし。
  **注意:** 撤去後も結果稿 :174-180 の path は古くなる (存在しない path を「原本」と書く)。撤去するなら結果稿の所在記録を追記で訂正するか、撤去しない判断が要る。ただし「消えたことを理由に測定を無効にしない」(規律 7) ので、sha256 は残る。
- consumer: なし (コード・テストに 0 件)。
- 回収するなら写すべき中身 (撤去する場合の最小): 既に 3 か所に複製があるので新規複製は不要。**r4 について、repro-archive の写しが「tree 撤去後に残る唯一の外部の写し」になる** (job dir の `originals-copy` も job dir 撤去時に消える)。
  内容確認は `t2853-20260923/manifests/k2-resubmit-r4-originals.{json,sha256}` の存在で足りる。
- 不確実な点: repro-archive の写しと `originals-copy-20260922/r4/` を本調査で再照合してはいない (insight §2.5 の記述による)。`namespace.json` は前日写しに無く repro-archive にだけある。

### 系列 5: T-2797 B-5 試走 (`dev-wave-t2797-b5-contrast/` 配下の tree)
- worktree / branch / HEAD: 登録 worktree は `submit-tree` の 1 本 (`11d46a74a` detached、locked)。`mutation-source/` (約 1.6 GB)・`mutation-scratch-{plan,probe,final,final2}/`・`mutation-source-task-runs/` は登録 worktree でなく独立 clone / scratch。
- 中身の概要: `submit-tree/output/` に試走の campaign 53・claim 53・`namespace.json` (未追跡)。job dir の `ledgers/`・`materials/`・`llm/`・`pilot/`・`evidence/`・`report-pilot-final.json`・codex 記録。
  **repro-archive t2853-20260923 に写し済み** (`b5-pilot-jobdir` 1,683 file・`b5-pilot-originals` = campaign 53 + claim 53 + namespace.json の 274 file、一致)。B-5 試走の trace は標準経路で削除済み (写しに無い)。
  さらに repo 内 insight `output/insights/2026-09-20/t2797-b5-contrast/` に `ledgers/`・`llm/`・`pilot/report-pilot-final.json`・`mutation/`・`verbatim/` が入っている (paper-story の C38 の派生物)。
- 名指し表 (全数は付録 A の p5。insight `t2797-b5-contrast` 内の `ledgers/{block-stock,llm,random,sweep-matched}/events/*.json` 約 100 file が事象ごとに path を含む):
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `output/insights/2026-09-20/t2797-b5-contrast/README.md` (3 行) | submit-tree・job dir | 固定 checkout / 経緯 | 「submit-tree = 統合 commit `11d46a74a`」 |
  | 同 `ledgers/*/events/*.json`・`series.json`、`llm/round-*/request.json`・`*-prompt.md`、`llm/verbatim/critic-*.md`、`pilot/evidence/*/reservation.json`、`pilot/report-pilot-final.json` (696 行)、`mutation/*-summary.txt` | job dir・tree path 文字列 | 経緯の記述 (生記録に path が埋まる) | 改変不可 |
  | 同 `verbatim/*` (s2〜s6 の prompt と出力) | path | 経緯の記述 (逐語) | |
  | `docs/paper-story/claim-evidence/2026-09-21.md:187`・`2026-09-21b.md:195` (C38) | job dir `dev-wave-t2797-b5-contrast/` (`report-pilot-final.json` sha256 `e30afbe0…`・`pilot/timing-table.md`・`pilot/qsub-pilot.log`) と submit-tree の統合 commit `11d46a74a` | 原本の所在 + 発効版 (ref) の記録 (`[導出索引]` は repo 内 insight README §6・§6.3・§8 を引く。`report-pilot-final.json` は repo 内 `pilot/` と `cmp` で byte 一致、sha256 も同値を実測) | 「〔限定付き観測 — 上限付き試走・主標本外・n = 1 系列 / arm〕」 |
  | `output/insights/2026-09-23/t2853-repro-package-archive/README.md:65,66,152` ほか (10) | `dev-wave-t2797-b5-contrast/`・`submit-tree/output/` | 原本の所在 (写しの記録) | 「b5-pilot-originals ... 一致」 |
  | `output/insights/2026-09-21/t2797-tier0/*` (probe 243 行ほか) | contrast job dir | 経緯の記述 (再利用元の参照・生記録) | |
  | `output/insights/2026-09-22/t2797-effect-bundle/{verbatim,mutation}/*` (計 16 行)、他診断 insight の生ログ (`acceptance-gate-wait-diagnosis`・`provenance-receipt-land-chain-diag`・`t2838-gate-argv-unify`・`t2853-repro-package-estimate` ほか) | contrast job dir | 経緯の記述 | |
  | `orchestrator/tests/test_b5_llm_round.py:22` | repo 内 insight (`output/insights/2026-09-20/t2797-b5-contrast`) | **consumer (ただし repo 内 insight。worktree ではない)** | `PILOT = ROOT / "output/insights/2026-09-20/t2797-b5-contrast"` |
- 研究での使用判定: **不要**。(a) 試走の数値・図は repo 内 insight (README §6、`pilot/report-pilot-final.json`、`ledgers/`) に既にあり、C38 も「主標本外・n = 1」の限定観測。原本 (submit-tree の campaign 53) は provenance で、repro-archive にも写しがある。
  (b) worklog 末尾・phase3.md に入力としての記述なし (phase3.md:1747 は「発効せず」の見送り一覧で入力ではない)。(c) B-5 v1 事前登録は §15 erratum で閉鎖、v2 は D2259 で発効せず (`docs/decisions.md` D2259)。
- consumer: worktree を読むコード・テストなし。`test_b5_llm_round.py:22` は repo 内 insight を読む (撤去の影響なし)。
- 回収するなら写すべき中身: 不要 (repro-archive に 274 file の写しあり)。
- 不確実な点: 試走の trace は当時から無い (§2.4 の記録)。`mutation-source/` は名指し 0 件で、別途の要否は未確認。

### 系列 6: T-2797 B-5 本走 submit-trees (16 本、HEAD `6fce61d6e`)
- worktree / branch / HEAD: `dev-wave-t2797-b5-main-run/submit-trees/{calib,t01〜t12,t15,t16,t17}`。すべて detached `6fce61d6e`、locked。
- 中身の概要 (`ls` で確認): 追跡済み main 写し + 未追跡の `output/exploration/campaigns/p3-s4-loop-s4-autonomous-*` (実走した tree だけ): calib 2、t01 2、t02 1、t03 1、**t04 16、t05 6、t06 16、t07 16、t08 16**、t09 3、t10 3、**t11 16、t12 16**。t15〜t17 は campaign 無し (未使用)。
  各 campaign dir は `campaign.lock`・`loop_state.json`・`s4_loop_digest.txt`・`runs/`・`spec/`・`variants/`・`insights/`・`reports/` を持つ (t01 の 1 本で確認)。`output/env/pegasus/claims/*.claim`、`output/env/pegasus/silo_ladder_rung1/job-staging/` (依存 source)。
  **B-5 本走の台帳 `ledgers/b5-registered-v1/block-1/{balanced,read-heavy,write-heavy}/r0{1..4}/`・`driver-state/b1-s1/`・`materials/b1-*-llm/`・`evidence/`・`llm_parent_driver.py`・`handoff-t2797-b5-main-run.md` は tree の外 (job dir)。** repro-archive にも入っていない。
- 名指し表 (全数は付録 A の p6):
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `output/insights/2026-09-26/t2797-b5-cost-options/README.md:32,216-217` (+ `verbatim/s1-brief.md`・`s6-review-1.md`) | 本走 job dir (`dev-wave-t2797-b5-main-run/`、読むだけ) の台帳・evidence・driver-state | 原本の所在 (tree ではなく job dir) | 「一次資料は本走 wave の job dir ... の台帳 `ledgers/b5-registered-v1/block-1/*/*/*/events/*.json`」 |
  | `output/insights/2026-09-26/t2797-b5-v2-prep/README.md:18`・`verbatim/d-cause.md:3`・`verbatim/s1-brief.md:14` | 本走 job dir の `driver-state`・`materials`・`llm_parent_driver.py` | 原本の所在 / 再現手順 (job dir) | |
  | `output/insights/2026-09-22/t2853-repro-package-*` の du 記録 | job dir | 経緯の記述 | |
  | 直接 `submit-trees/tNN` を名指す file | **0 件** (検索語 `b5-main-run/submit`・`submit-trees` で repo の docs/output/コードに無し。付録 A の p6 に `dev-wave-t2797-b5-main-run` の全件) | — | |
- 研究での使用判定: **不要**。(a) 論文ストーリーが本走から使うのは投入・中断・6 比較判定不能・費用 (126,426 s、95.0 %、2,703 s、429) の**事実**だけで、その数値は
  `t2797-b5-cost-options/README.md` §1〜§3 と `data/b1s1-jobs.tsv`・`b1s1-sessions.tsv` が repo に持つ (時間だけを抜いた derived。抽出元は job dir の台帳で、tree ではない)。
  生成器の比較結果 (throughput・優劣) は判定不能で確定し論文に使われない (v1 §15、`docs/b5-generator-contrast-preregistration.md:598-`)。tree の campaign 原本 (WAL・variants) は論文のどの数値・図にも引かれていない。
  (b) 該当なし: `docs/phase3.md:1747` は「v2 を発効しない (D2259)、v1 cohort は閉鎖済み」。worklog 末尾 2 エントリ (1953・1954) に B-5 の記述なし。(c) 有効な事前登録が入力に取る記述なし (v1 は閉鎖、v2 は未発効)。
- consumer: なし。
- 回収するなら写すべき中身 (要否の判断に付す情報、判定は「不要」): 撤去で失うのは tree 内の campaign 原本 (計 12 job 分、特に t04/t06/t07/t08/t11/t12 の 16 campaign 級) の WAL・variants・trace 由来物。
  **一方、job dir 側の `ledgers/`・`driver-state/`・`materials/`・`evidence/` は tree 撤去と無関係に残る。** 将来 v2 系 (関数単位軸での対照) が「v1 の候補値・critic 診断」を再読するなら job dir 側が要る (v2-prep が既に読んだ)。tree 側の要否は本調査の基準では「不要」。
- 不確実な点: (1) 12 job の campaign が tree のどれに対応するか (t04 等の 16 campaign は LLM 系列の各評価か) は台帳の突合せをしておらず、tree 別の中身の意味は未確認。(2) 各 campaign の大きさ (`du`) は未測定。
  (3) 論文の「95.0 %」等が tree 内 WAL を再集計しても出るかは未確認だが、抽出は job dir の台帳 event の `timing` と NQSV `Elapse` から行われたと README:32 が書く。

### 系列 7: 発効木 `.claude/worktrees/t2797-b5-effect` と branch `worktree-dev-wave-t2797-b5-main-run`
- worktree / branch / HEAD: 発効木は `6fce61d6e` detached、locked。branch = `b3eb51327` (= 発効 commit を wave へ merge した commit)。main 先行は 2 commit のみ (`b3eb51327` merge、`6fce61d6e` 発効 commit)。
  `6fce61d6e` を含む ref はこの branch だけ (`git branch -a --contains`)。main の祖先ではない (rc=1)。
- 発効 commit の中身 (`git show --stat`): 1 file (`output/insights/2026-09-22/t2797-effect-bundle/bundle/b5-effective-bundle.draft.json`) の +23 −2 行だけ。`status: draft → effective` と `effective` 節の追加
  (D2227 項 2 の裁定への参照、approval_date 2026-09-23、recording_commits 2 件、approved_object = land_commit `0b0e00ee1e6d5c069cd36e2c12d526fe9f7d2d59`、approved_k 3、W_s 63,777・W_stock_s 16,341、cap 2,450,440 s、authorized_runs ほか)。
  **この差分そのものは repo の他所に無い** (main の同 json は `status: draft`。数値は D2227・paper-story・cost-options に散文で記述されている)。
- 名指し表 (`6fce61d6e` = 先頭 9 桁 `6fce61d6e` で全文検索。全数は付録 A の p7 と冒頭の a.txt):
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `docs/paper-story/2026-09-29.md:4225,4844,5405,5796,6651,6752` | `6fce61d6e` | 経緯の記述 (発効 commit の所在) | 「B-5 の発効 commit `6fce61d6e` は main の祖先でない本走 wave の branch にあり、本走 wave は未着地」 |
  | `docs/paper-story/2026-09-27.md:3946,4498,5037,5417,6236,6337`、`2026-09-26.md:3382,3845,4349,4714,5391,5480` | 同上 (旧版) | 経緯の記述 | 同上 |
  | `output/insights/2026-09-26/paper-methods-ja/implementation.md:51`、`output/insights/2026-09-22/comsys2026-manuscript/README.md:263`、`docs/archive/worklog-phase3-0926-1859.md:6` | `6fce61d6e`・branch 名 | 経緯の記述 (論文稿の provenance 注記) | 「B-5 の発効 commit (`6fce61d6e`) は未着地の branch `worktree-dev-wave-t2797-b5-main-run` にだけあり」 |
  | `output/insights/2026-09-26/paper-results-ja/results-discussion.md:775` | (SHA 無し) | 経緯の記述 | 「B-5 の発効 commit は main の祖先でない」 |
  | `output/insights/2026-09-22/t2797-effect-bundle/{mutation,verbatim}/*` (計 379 行) | 部分一致 (wave 名 `t2797-b5-effect-bundle`)。`6fce61d6e`・発効木 path の名指しではない | — (誤検出) | |
  | `docs/decisions.md` | `6fce61d6e` の名指しは 0 件 (D2227 項 2 は認可を記す) | — | |
- 研究での使用判定: **不要** (ref としての要否は下記の但し書き付き)。(a) 論文ストーリーは発効 commit の**所在 (main の祖先でない)** を書くだけで、commit の中身を数値・図として使わない。
  発効の対象・k・W・cap は D2227 と cost-options の散文に repo 内で既にある。(b) 該当なし。(c) v1 は §15 で閉鎖済みで、発効 commit を入力に取る有効な事前登録は無い (v2 は未発効・見送り)。
  **但し書き:** 発効 commit `6fce61d6e` の唯一の ref が本 branch なので、branch を削除すると (reflog 無しの場合) commit は unreachable になる。
  論文稿の provenance 注記は「commit `6fce61d6e` は main の祖先でない」と書き、commit を開く検証を求めるものではない。規律 7 により「消えたから無効」とはならないが、束縛 (どの commit で本走を認可したか) の検証手段を失う。
- consumer: なし (worktree・branch・SHA を読むコード・テストは 0 件、grep 済み)。
- 回収するなら写すべき中身 (保全するなら最小): 発効 commit の差分 (25 行、`git show 6fce61d6e` の出力) と `b3eb51327` の親関係。`git bundle create ... 6fce61d6e` 1 本で全体を保全できる (parent は既に main 履歴の `0b0e00ee1`)。
  unreachable 化する場合の記録先は `docs/unreachable-object-ledger.md` (既存の運用) が適する。
- 不確実な点: (1) 論文ストーリー 2026-09-29.md:6752 は「本走 wave の記録は main の祖先でない branch にある」と書くが、branch の実体は発効 commit と merge の 2 commit だけで、
  本走 wave の記録 (handoff・台帳) は job dir にある。文面と実体が食い違う (どちらの記述が古いかは未確認)。(2) 発効木 `t2797-b5-effect` の中身は系列 6 の tree と同一 commit で、未追跡物は未確認。

### 系列 8: branch `worktree-t2273-shard0-local-copy` (checkout 無し)
- worktree / branch / HEAD: worktree 無し (`git worktree list` に無い)。branch tip `5c51e958e` = 実装 `eb65d322f` + main `620a6bb13` の merge。main 先行 2 commit。
- **D2242 の本文 (`docs/decisions.md:72110-72128`):** 題「t080 共有 base の可視 output を session 局所の写しから複製する実装は、事前登録の land 条件を満たさなかったので land しない (2026-09-26)」。
  決定 1 = `orchestrator/tests/test_s8b_oracle_driver.py` の共有 base builder の複製元を計算ノード局所の写し (`_T080SharedBases.copy_visible_output`) に替える実装 (branch `worktree-t2273-shard0-local-copy`、実装 commit `eb65d322f`) を **local main へ入れない。branch は残す。**
  決定 2 = 隣接 3 対 (A = main `620a6bb13`、B = A + 実装) の shard-0 W_0 の対差 +19.111 / +19.679 / −4.341 秒、対率中央値 5.2 % で、「3 対すべて短縮」と「対率中央値 ≥ 10 %」の両方を外した。
  決定 3 = 事前登録は「性能改善としての land」だけを定めていたので、中立な整理として land するかは新しい判断で、次の一手の候補と並べてユーザー裁定へ置く。
  **「branch は残す」の理由は D2242 の理由節には明示されていない** (理由節は land しない理由 = 効果が事前登録の閾値を外れた、写しの期待値が診断の −123.9 秒と別、正しさ側 M1〜M5 全件 KILLED で land しない理由は効果だけ)。
  「残す」の趣旨は決定 3 (中立整理としての land を別判断に残す) と、実装 branch を証拠 (insight §2「実装 (branch に保存、land しない)」) として保存することから読める。
  **その後の裁定:** D2243 項 (`docs/decisions.md:72165-`) は「候補 (c) (D2242 の実装を改善なしの中立な整理として land) は採らない」と決めた (候補 (a) 前倒しの写しの効果を先に測る)。すなわち決定 3 の「新しい判断」は D2243 で (c) 不採用として出ている。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `docs/decisions.md:72114` | branch・`eb65d322f` | 経緯の記述 + 発効版 (ref) | 「local main へ入れない。branch は残す」 |
  | `docs/decisions.md:72165` | D2242・insight `t2273-shard0-local-copy-ab` | 経緯の記述 | D2243 の資料欄 |
  | `output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md:3,20-22` | branch・tip `5c51e958e`・`eb65d322f` | 原本の所在 (実装の実体は branch) | 「実装 branch ... tip `5c51e958e` = 実装 `eb65d322f` + main `620a6bb13` の取り込み、local main へは入れない」「+100 / −2 (Codex author ...)」 |
  | 同 insight の `verbatim/*` (s2〜s6 の prompt・出力ほか約 90 行)、`mutation/*`、`runs/measurement-tips.json`、`analysis/analysis-compact.json` | branch 名・SHA | 経緯の記述 (逐語・計測 tip) | |
  | `output/insights/2026-09-27/t2273-shard0-precopy-impl/verbatim/*`、`2026-09-26/t2273-shard0-precopy-ab/verbatim/*` | 前回 probe (job dir `dev-wave-t2273-shard0-local-copy/probe/`) と insight | 経緯の記述 / 再現手順 (移植元の参照) | 「移植元 — 前回 wave の Codex author 製」 |
  | `docs/spool/FOLDED.md` の `record-t2273-shard0-local-copy` (wave_ref)、`docs/unreachable-object-ledger.md` | 記録 branch 名 | 経緯の記述 | |
- 研究での使用判定: **不要** (但し書き付き)。(a) 論文ストーリーの grep 0 件 (`docs/paper-story` を `shard0`・`t2273` で検索、0 件)。(b) phase3.md・worklog 末尾 (1952〜1954) に branch を今後の入力にする記述無し。
  D2243 が (c) 「中立な整理として land」を採らない、次は別実装 (前倒し写し) と決めており、この branch を入力とするタスクは無い。前回 wave の probe は job dir (`dev-wave-t2273-shard0-local-copy/probe/`) にあり branch とは別物で、移植元として引かれた。(c) 凍結・事前登録: 該当なし。
  **ただし D2242 決定 1 は「branch は残す」と明記している裁定であり、撤去は D2242 の文言と衝突する。** 削除するなら、D2242 (または後続裁定) を根拠に「残す」の解除をユーザーが決める必要がある (撤去側で決められない)。
- consumer: なし (`orchestrator/`・`tools/`・`hooks/` に branch 名・SHA の名指し 0 件)。
- 回収するなら写すべき中身 (保全するなら): 実装 commit `eb65d322f` (`orchestrator/tests/test_s8b_oracle_driver.py` の +100/−2、1 file)。insight README §2 は「branch に保存」と書く。`git bundle` か patch 1 本で足りる。
  patch を repo の insight へ写すのは `insight-patch-copies-need-codex-author` (記憶) により Codex author が要る。
- 不確実な点: (1) 「残す」の理由の一次資料は D2242 の理由節に無く、insight §2・§7 が補足する可能性があるが本調査は README 冒頭・§2 の一部だけを読んだ。(2) `record-t2273-shard0-local-copy` 記録 branch は本系列の対象外で未確認。

## 3. 1 行要約表

| 系列 | 判定 | 主根拠 |
|---|---|---|
| 1 T-1505 A-1 attempt1 (submit-tree) | 不要 | leaf 4 file が repo と byte 一致 (`cmp`)。結果稿・図 9 は repo 内派生物。consumer 0 |
| 2 T-2489 A-2 nodes5 probe (tree + branch) | 不要 (branch は 1 行編集の使い捨て commit) | paper-story は運用素材として insight を引くのみ。commit `3f61c3408` は README が内容を述べる |
| 3 T-2792 A-1 attempt2 (submit-tree) | 不要 | leaf 4 file が repo と byte 一致。repro-archive §2.4 にも記録。consumer 0 |
| 4 T-2795 K2 pair / pair2 / r4 | 不要 (但し結果稿 :174-180 の所在 path が古くなる) | 数値・図 12・結果稿は repo 内。原本は repro-archive・`originals-copy`・`ao-root/` に複製済み。consumer 0 |
| 5 T-2797 B-5 試走 (contrast/submit-tree ほか) | 不要 | 数値は insight `t2797-b5-contrast` (ledgers・pilot report) に在る。campaign 原本は repro-archive に写し済み。`test_b5_llm_round.py:22` は repo 内 insight |
| 6 T-2797 B-5 本走 submit-trees 16 本 | 不要 | 論文が使うのは費用・判定不能の事実のみで、数値は `t2797-b5-cost-options/data/` に在り抽出元は job dir の台帳 (tree ではない)。v1 は §15 で閉鎖・v2 は D2259 で見送り。repro-archive には未収録 |
| 7 発効木 `t2797-b5-effect` + branch `…-b5-main-run` | 不要 (但し `6fce61d6e` の唯一の ref) | 論文は「main の祖先でない」所在を書くだけ。差分は json 25 行で bundle 1 本で保全可。consumer 0 |
| 8 branch `worktree-t2273-shard0-local-copy` | 不要 (但し D2242 が「branch は残す」と明記) | paper-story 0 件、D2243 が (c) 中立 land を不採用。撤去は D2242 の文言と衝突するのでユーザー裁定 |

## 付録 A. 名指し全数 (系列別、file:line + 先頭 150 字)

各節は `grep -rHnIF` の生出力から機械的に作った (検索語は節の見出しに記す)。`docs/archive/worklog-*` と `docs/spool/FOLDED.md` は経緯の記述、
`output/insights/**/verbatim/*`・`reviews/*`・`evidence/*`・`ledgers/*` は各 insight の生記録・逐語に path 文字列が埋まったもの (経緯の記述) で、いずれも consumer ではない。

### A-1. 系列 1 (T-1505): 検索語 dev-wave-t1505-a1-sized-submit (計 59 行)

個別行 (README・docs・台帳):

- `output/insights/2026-09-21/land-roundtrip-diagnosis/README.md:103` — - **仮説 (未検証):** handler 付きの SIGALRM が、Lustre 上の遅い metadata 呼び出し (interruptible になる wait) を中断し、`InterruptedError` がそのまま上がった。整合する観測: 2 回とも 09-20 22:36〜2
- `output/insights/2026-09-21/land-roundtrip-diagnosis/land-attempts-timeline.txt:187` — 09-20 22:36:34 LAND      land-1.json                              status=fold-gate-failed retry_same=False waited=0.0 win=149.66949789389037 mb=fff438
- `output/insights/2026-09-13/paper-story-a1-balanced5-sized/.complete.json:2` — "destination": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1505-a1-sized-submit/submit-tree/output/insights/2026-09-13/paper-story-a1-balanced5-sized",
- `output/insights/2026-09-13/paper-story-a1-balanced5-sized/receipt.json:99` — "destination": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1505-a1-sized-submit/submit-tree/output/insights/2026-09-13/paper-story-a1-balanced5-sized",
- `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md:23` — - submit-tree: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1505-a1-sized-submit/submit-tree` = local main `d2ebef7a407dc6be61622ed596cf08b8b518f606` の 
- `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md:24` — - 記録用 wave worktree (`.claude/worktrees/dev-wave-t1505-a1-sized-submit`、同じ SHA) と分離。
- `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md:26` — - 起動 script (`run-hydrate.sh` / `run-submit.sh` / `run-watch.sh` / `run-stepc.sh` / `run-stepm.sh` / `detach.sh`) は実行可能 script なので repo へは複製せず job dir
- `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md:27` — - submit (`run-submit.sh`、submit-tree を cwd に): `python3 -B -m orchestrator.campaign.paper_story_a1_paired submit --study-id paper-story-a1-20260901-b
- `docs/failures.md:20505` — - **再発: 2026-09-20 (6・7 例目、事後集計で判明)** — 22:36:34 JST の k2-loop-originals-lost-downstream (land it=1、path `<job dir>/dev-wave-t1505-a1-sized-submit/sub
- `docs/spool/FOLDED.md:4744` — - {"allocations":{"T:a1-sized-status-column":"[T-2775]"},"authored":"2026-09-18","base":"d2ebef7a407dc6be61622ed596cf08b8b518f606","content_sha256":"5
- `docs/spool/FOLDED.md:4745` — - {"allocations":{},"authored":"2026-09-18","base":"d2ebef7a407dc6be61622ed596cf08b8b518f606","content_sha256":"0110570bae8e7be51b2ba89ed909a9936394a2
- `docs/archive/worklog-phase3-0918-1636-1637.md:1` — ## 2026-09-18 (1636) — [T-1505] A-1 balanced5 sized 本走 attempt-0001 を D2120 項 3 の認可どおり 1 回投入し、3 workload とも valid で完走した — 登録済み解析の分類は 3 本とも resolved-ab

生記録・逐語・台帳 (path 文字列が埋まっているだけ。dir 別の行数):

- `output/insights/2026-09-18/t1505-a1-sized-attempt1//MANIFEST.tsv` : 15
- `output/insights/2026-09-18/t1505-a1-sized-attempt1/receipts` : 27
- `output/insights/2026-09-18/t1505-a1-sized-attempt1/verbatim` : 2
- `output/insights/2026-09-18/t2775-a1-sized-results-draft/verbatim` : 1
- `output/insights/2026-09-19/a1-sized-attempt2/verbatim` : 1
- `output/insights/2026-09-20/t2792-a1-sized-attempt2/verbatim` : 1

### A-2. 系列 2 (T-2489): 検索語 dev-wave-t2489-a2-nodes5 / probe/t2489 / 3f61c3408 (計 23 行)

個別行 (README・docs・台帳):

- `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:10` — - wave: `worktree-dev-wave-t2489-a2-nodes5-probe` (local main `d2ebef7a4` から、wave branch の実装面差分ゼロ)
- `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:11` — - 実走した source commit: `3f61c3408` — main tip `d2ebef7a4` に「A-2 policy の `scheduler.nodes` 1→5」の
- `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:12` — 1 行だけを足した**使い捨て commit** (branch `probe/t2489-a2-nodes5-submit`、main / wave branch へ入れない)
- `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:51` — \| policy \| `orchestrator/campaign/paper_story_a2_certification.v2.json` の `scheduler.nodes` を 5 にした使い捨て commit `3f61c3408` (bytes sha256 `f8a77806…4
- `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:52` — \| 投入元 \| `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree` (git worktree、branch `probe/t2489-a2-nodes5-submit`、`git worktr
- `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:206` — \| source_commit \| `31ec382a7` \| `3f61c3408` (使い捨て) \| 当然異なる \|
- `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:228` — 5. 使い捨て commit `3f61c3408` は submit-tree の branch にだけ在る。テストの policy sha256 pin
- `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:277` — \| 投入元 \| `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree` (HEAD `3f61c3408`) \|
- `output/insights/2026-09-20/t2344-closure-stage1/exact63-locks-verify.json:92` — "contract_loader_commit": "3f61c34084addf7befadcf9a0f72c7a7e9b789d3",
- `output/insights/2026-09-20/t2344-closure-stage1/exact63-locks-verify.json:99` — "contract_loader_commit": "3f61c34084addf7befadcf9a0f72c7a7e9b789d3",
- `output/insights/2026-09-20/t2344-closure-stage1/exact63-declared-order.json:14` — "3f61c34084addf7befadcf9a0f72c7a7e9b789d3": {
- `docs/spool/FOLDED.md:4780` — - {"allocations":{},"authored":"2026-09-18","base":"49a9887ff3d201cf8d48e2c0946dc01433a1e520","content_sha256":"46b4ffab72ea086ef50d9415412e01e4c99dc8
- `docs/archive/worklog-phase3-0918-1647.md:1` — ## 2026-09-18 (1647) — [T-2489] A-2 認証を nodes=5 で 1 attempt 実走し判断材料を揃えた — 50 分が 12 分 08 秒 (4.17 倍)、検査 24 件・遠隔 16 件すべて受理、node 秒 +16 %。副産物として 2 request 
- `docs/archive/worklog-phase3-0918-1647.md:5` — - 実走: attempt `t2489-20260918a` (request `4978.nqsv` = rr5、`4979.nqsv` = rr50、各 5 ノード、gen_S)。投入元は job dir の使い捨て submit-tree (main tip `d2ebef7a4` + A-
- `docs/archive/worklog-phase3-0918-1647.md:10` — - 残置: 使い捨て submit-tree (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree`、worktree lock 済み) と branch `probe/t2489-a2-nodes5

生記録・逐語・台帳 (path 文字列が埋まっているだけ。dir 別の行数):

- `output/insights/2026-09-18/t2489-a2-nodes5-probe/verbatim` : 3
- `output/insights/2026-09-19/a1-sized-attempt2/verbatim` : 3
- `output/insights/2026-09-19/t2778-child-worktree-cleanup/verbatim` : 2

### A-3. 系列 3 (T-2792): 検索語 dev-wave-t2792-a1-sized-attempt2 (計 116 行)

個別行 (README・docs・台帳):

- `output/insights/2026-09-21/land-roundtrip-diagnosis/land-attempts-timeline.txt:175` — 09-20 22:39:11 LAND      land-2.json                              status=fold-gate-failed retry_same=False waited=0.0 win=106.61160607403144 mb=fff438
- `output/insights/2026-09-21/land-roundtrip-diagnosis/README.md:103` — - **仮説 (未検証):** handler 付きの SIGALRM が、Lustre 上の遅い metadata 呼び出し (interruptible になる wait) を中断し、`InterruptedError` がそのまま上がった。整合する観測: 2 回とも 09-20 22:36〜2
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:73` — \| a1-attempt2-jobdir \| A-1 attempt-0002 の wave 記録 \| `dev-wave-t2792-a1-sized-attempt2/` (`submit-tree/`・`third-party-hydrated/` を除く) \| 123 \| 198,
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:176` — \| 写し \| `data/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/` (attempt-0001・0002 の durable authority、結果稿 §5.2 が sha256 を列挙する一次資料)、`dat
- `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/receipt.json:99` — "destination": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/submit-tree/output/insights/2026-09-13/paper-story-a1-balanced5-sized
- `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/.complete.json:2` — "destination": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/submit-tree/output/insights/2026-09-13/paper-story-a1-balanced5-sized
- `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md:49` — - submit-tree: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/submit-tree` = local main `fec4a818741e5464fffcd11e4b094c125dfe5280`
- `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md:52` — 既存 tracked bytes を変えていない。書き込みは materialize が新規 leaf (兄弟 dir) へ出力したものだけ。記録用 wave worktree (`.claude/worktrees/dev-wave-t2792-a1-sized-attempt2`、同じ SHA)
- `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md:57` — repo へは複製せず job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/` に残す (逐語は `verbatim/*.py.txt`)。argv は以下に逐語で写す。
- `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md:64` — /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/third-party-hydrated`。
- `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md:168` — - job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/` (起動 script、log、待ち手、抽出・検算 script の原本、handoff)。
- `docs/failures.md:20505` — - **再発: 2026-09-20 (6・7 例目、事後集計で判明)** — 22:36:34 JST の k2-loop-originals-lost-downstream (land it=1、path `<job dir>/dev-wave-t1505-a1-sized-submit/sub
- `docs/spool/FOLDED.md:5078` — - {"allocations":{},"authored":"2026-09-20","base":"7baf3f37589111d421294f63cc194bbb2d69613f","content_sha256":"6541acae5263c5a1a6eb0f914c86b73ff6d7bd
- `docs/spool/FOLDED.md:5079` — - {"allocations":{},"authored":"2026-09-20","base":"7baf3f37589111d421294f63cc194bbb2d69613f","content_sha256":"0cd334ab1290ed98b640caa4e11b1295cd0cad
- `docs/archive/worklog-phase3-0920-1755.md:1` — ## 2026-09-20 (1755) — [T-2792] A-1 balanced5 sized attempt-0002 (D2172 項 2 の認可済み独立再現) を exact な認可 record 経由で 1 回投入し、3 workload とも valid で完走 — 登録済み解析は
- `docs/archive/worklog-phase3-0920-1755.md:8` — decisions fragment は無し (新しい設計判断なし)。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/HANDOFF.md`。

生記録・逐語・台帳 (path 文字列が埋まっているだけ。dir 別の行数):

- `output/insights/2026-09-20/t2243-collection-contention/verbatim` : 6
- `output/insights/2026-09-20/t2792-a1-sized-attempt2//MANIFEST.tsv` : 21
- `output/insights/2026-09-20/t2792-a1-sized-attempt2/receipts` : 27
- `output/insights/2026-09-20/t2792-a1-sized-attempt2/verbatim` : 29
- `output/insights/2026-09-21/acceptance-gate-wait-diagnosis/verbatim` : 14
- `output/insights/2026-09-22/t2853-repro-package-estimate/verbatim` : 1
- `output/insights/2026-09-23/t2853-repro-package-archive/verbatim` : 2

### A-4. 系列 4 (T-2795): 検索語 dev-wave-t2795-k2-pair / submit-tree-pair / submit-tree-r4 (計 350 行)

個別行 (README・docs・台帳):

- `output/insights/2026-09-21/t2795-pair-repair/README.md:9` — - wave: `dev-wave-t2795-k2-pair-repair`、branch `worktree-dev-wave-t2795-k2-pair-repair`、着手時 local main `5efd69367b641b9bfbd6fb426478f66ae5762783` (開始 
- `output/insights/2026-09-21/t2795-pair-repair/README.md:11` — - job root (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-repair/`
- `output/insights/2026-09-21/t2814-cleanup-command/README.md:59` — A3 (§2 高い条件、fix 2、「削除直前に status 空と非施錠を再確認」— 同日 00:20〜00:36 JST の `/cleanup-branches` 実行中に /rulings session が submit-tree-pair を lock した罠。
- `output/insights/2026-09-23/t2860-k2-round4-reflux/README.md:24` — 3. 原本 (lock 済み `submit-tree-r4`) には何も書いていない。取込み後も原本の `runs/` は `wal.jsonl` 1 file だけである (§3)。
- `output/insights/2026-09-23/t2860-k2-round4-reflux/README.md:37` — - 原本: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/submit-tree-r4/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/`
- `output/insights/2026-09-23/t2860-k2-round4-reflux/README.md:131` — - **repo へ複製していないもの:** campaign の WAL・lock・digest・loop_state・受領証・`runs/agent_outputs.jsonl` (guard の防護対象)。写しは job root の `ao-root/`、原本は lock 済み `submi
- `output/insights/2026-09-23/t2860-k2-round4-reflux/layer3_report.json:1` — {"aborts":[],"acceptance_receipt":null,"admission_decision":{"admission_status":"admitted","attempt_receipt_sha256s":["bac7f4fa5f6e113f5a7057676250b86
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:67` — \| k2-resubmit-jobdir \| K2 再投入・4 巡目 \| `dev-wave-t2795-k2-pair-resubmit/` (submit-tree 2 本を除く、`originals-copy-20260922/` を含む) \| 163 \| 1,538,269 \| 
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:68` — \| k2-resubmit-pair2-originals \| K2 再投入 (campaign 原本) \| `…/submit-tree-pair2/output/` の campaign・claim・`namespace.json` \| 8 \| 31,597 \| 一致 \| 0.4 
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:69` — \| k2-resubmit-r4-originals \| K2 4 巡目 (campaign 原本) \| `…/submit-tree-r4/output/` の同上 \| 8 \| 31,584 \| 一致 \| 0.4 / 0.0 \|
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:70` — \| k2-pair-first-jobdir \| K2 pair 初回 (不成立) \| `dev-wave-t2795-k2-pair/` (`submit-tree-pair/` を除く) \| 130 \| 2,322,714 \| 一致 \| 6.9 / 0.4 \|
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:71` — \| k2-pair-first-originals \| K2 pair 初回 (campaign 原本) \| `…/submit-tree-pair/output/` の同上 \| 7 \| 19,231 \| 一致 \| 0.6 / 0.0 \|
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:90` — \| `dev-wave-t2795-k2-pair-repair` \| driver 修復の実装 wave で、実機の pair 投入をしていない (`output/insights/2026-09-21/t2795-pair-repair/README.md` §0)。実験データが無い \|
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:97` — K2 再投入の原本 14 file は、前日の wave が作った写し `dev-wave-t2795-k2-pair-resubmit/originals-copy-20260922/MANIFEST.sha256` と、
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:164` — \| 写し \| `data/dev-wave-t2795-k2-pair-resubmit/` (`materials/`・`verbatim/`・`originals-copy-20260922/`・集計 script)、submit-tree 2 本の campaign 原本と claim。初
- `output/insights/2026-09-19/k2-loop-round3/README.md:192` — (wave `dev-wave-t2795-k2-pair`、job `13339.nqsv`、host `bnode032`、Elapse 74 秒、fresh submit-tree HEAD `6a3e15809` = 当日の local main、CCBench `511c9538…`)。
- `output/insights/2026-09-29/t2871-policy-loop-iter/README.md:10` — 2. **先例の実測:** backoff 軸の K2 (T-2795) は job ごとに新しい空の submit checkout (= 別 out_root) で同じ identity を通していた (`dev-wave-t2795-k2-pair-resubmit/setup-submit-
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:9` — - wave: `dev-wave-t2795-k2-pair-resubmit`、branch `worktree-dev-wave-t2795-k2-pair-resubmit`、着手時 local main `8fd2a2f5c775954d6a32cee019ac7ce276298e4d` 
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:13` — - job root (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/`
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:44` — 固定 SHA の専用 submit-tree (`submit-tree-pair2`、HEAD `8fd2a2f5c`、superproject tracked clean (submodule 除外)、CCBench を `p3_s4_loop.PIN` = `511c9538…` へ chec
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:75` — pair 初投入の byte 複製 `dev-wave-t2795-k2-pair/originals-copy-20260920/` を読んだ。lock 済み `submit-tree-pair` には触れていない) と一致した。
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:101` — submit-tree は pair 走とは別の `submit-tree-r4` (同じ SHA・同じ PIN・別 out_root。同 identity の one-shot claim と同 campaign の stock skip を避けるため)。env は pair 走と同じで prop
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:207` — `submit-tree-pair2` / `submit-tree-r4` の `output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` と `output/env/pegasus/claims/`、byte 複製は `or
- `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:9` — - wave: `dev-wave-t2795-k2-pair`、branch `worktree-dev-wave-t2795-k2-pair`、着手時 local main `482f19b88dbbe255fc2bb0dcc95b14c1681c1a83` → 開始直後に
- `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:13` — - job root (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/` (HANDOFF、brief、診断メモ、裁定、glue、submit-tree、campaign 原本)
- `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:45` — 固定 SHA の専用 submit-tree (`submit-tree-pair`、HEAD `6a3e15809`、superproject tracked clean (submodule 除外)、CCBench を `p3_s4_loop.PIN` = `511c9538…` へ
- `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:62` — \| stock \| driver 2 起動目 `p3_s4_loop --isolate-worktree --fetchcontent-prebuild-receipt R --knowledge-manifest M --knowledge-classification C --knowle
- `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:168` — `submit-tree-pair/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` と `submit-tree-pair/output/env/pegasus/claims/`。
- `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:170` — 4 巡目用の `submit-tree-r4` は構築したが未使用 (撤去)。
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:31` — - [T-2795] pair 走 (campaign `b24749ae`) の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5 一致) だが、その worktree は unlocked で撤去された候補 1 と同型である。
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:51` — \| 1 \| 受領証 \| `c42dc712…` (1,317) \| 消失 \| **bytes 一致**: 3 巡と pair 走で同一 bytes。scratch (round 2) と `submit-tree-pair` に現物 \|
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:63` — \| 3 \| 受領証 \| `c42dc712…` \| 消失 \| **bytes 一致**: scratch / `submit-tree-pair` \|
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:64` — \| pair (T-2795、campaign `b24749ae`) \| WAL / lock / loop_state / digest / 受領証 \| `b5754f98…` / `962ef7d7…` / `a8c6a8b6…` / `8bde66fa…` / `c42dc712…` 
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:83` — \| **B-6 (d)** 同 job stock 対照は未達 (3 巡とも、pair 初投入でも) \| 3 巡: 各巡の記録 (未達の理由 = 既存 S4 口に stock 結線なし、各巡 README と 3 巡稿 §2.2 表) と各巡 WAL (stock record 不在)。pair
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:88` — \| **[T-2795] 4 巡目** (round 3 からの再開、D2172 項 3 (iv)) \| 親の射影入力: round 3 の whiteboard・`current_perf`・critic-3 逐語・knowledge-input・受領証 bytes・identity の lo
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:98` — - **親の代替照合 (round 3 が CLI の代わりに行ったもの) に要る bytes:** 受領証 (`c42dc712…`、3 巡 + pair で同一 bytes、scratch と `submit-tree-pair` に現物)、K2 射影
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:99` — (`knowledge-input.json` `05f2b267…`、repo)、campaign identity の preimage (現行 pin では `b24749ae`。lock は `submit-tree-pair` に現物。旧 identity `409e13f8` は scr
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:131` — - **付随 1 項 (P2) — `dev-wave-jobs/dev-wave-t2795-k2-pair/submit-tree-pair` を `git worktree lock` する。** pair 走の原本 5 file + claim の現物で、worktree は unlocke
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:163` — - ListAgents (20:55 JST): 稼働 17 session に [T-2795] の session は無い (entry 1754 で着地済み、`submit-tree-pair` だけ残存)。編集面の重複: `docs/paper-story/README.md` は
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md:183` — - repo 外: t2746 job dir `scratch-campaign/`、`dev-wave-t2795-k2-pair/submit-tree-pair/`、`cleanup-20260920/candidates-*.txt`。
- `output/insights/2026-09-20/t2795-pair-launcher/README.md:34` — **追記 (2026-09-20、後続 wave `dev-wave-t2795-k2-pair`):** 本 launcher の初投入 (`13339.nqsv`) で候補は certified、stock は同 job・同 campaign の 2 起動目が `campaign_claim.a
- `docs/decisions.md:69700` — 再提示する (D2172 項 3 の元の認可は撤回しない)。付随項 (`submit-tree-pair` の lock) は本 wave が実施した。
- `docs/spool/FOLDED.md:5074` — - {"allocations":{},"authored":"2026-09-20","base":"771f6dde827bd3a1373e93bec1ff61fc74a8606f","content_sha256":"89f406ecef684450b9c94cd3b34848eb6645ea
- `docs/spool/FOLDED.md:5075` — - {"allocations":{},"authored":"2026-09-20","base":"771f6dde827bd3a1373e93bec1ff61fc74a8606f","content_sha256":"d5624eae07be1322f79b7e736811c040c32b36
- `docs/spool/FOLDED.md:5076` — - {"allocations":{"D:k2-pair-one-shot-claim":"D2187"},"authored":"2026-09-20","base":"771f6dde827bd3a1373e93bec1ff61fc74a8606f","content_sha256":"5a13
- `docs/spool/FOLDED.md:5190` — - {"allocations":{},"authored":"2026-09-21","base":"9c07395c18e46b8fa75f802a0586b5b911843662","content_sha256":"05b99d92f9e5cef3b8a1d066354269991c5d39
- `docs/spool/FOLDED.md:5191` — - {"allocations":{"D:k2-pair-authorization-session":"D2205"},"authored":"2026-09-21","base":"9c07395c18e46b8fa75f802a0586b5b911843662","content_sha256
- `docs/spool/FOLDED.md:5192` — - {"allocations":{},"authored":"2026-09-21","base":"9c07395c18e46b8fa75f802a0586b5b911843662","content_sha256":"f6bac38a3ef1dbb522f8bf00c975de3909ac87
- `docs/spool/FOLDED.md:5275` — - {"allocations":{"T:k2-round4-reflux":"[T-2860]","T:pegasus-readme-pair-text":"[T-2861]"},"authored":"2026-09-22","base":"f6b94e01bf87e932b322dc92a99
- `docs/spool/FOLDED.md:5276` — - {"allocations":{"F:compute-estimate-forbidden-extrapolation":"F1041"},"authored":"2026-09-22","base":"f6b94e01bf87e932b322dc92a9920854d2e3c7c0","con
- `docs/paper-story/2026-09-26.md:1162` — 原本 5 file は `submit-tree-pair` に無傷で job dir へ byte 複製した。**3 巡の値・判定・稿・図 12 は変えない (規律 7)。変わるのは「原本
- `docs/paper-story/2026-09-26.md:5560` — 判定は当時の記録による」。**B-6 (d)** 同 job stock 対照の未達 — pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5) で job dir
- `docs/paper-story/2026-09-26.md:5572` — (`submit-tree-pair` の `git worktree lock`) は第 27 回の /rulings session が打った (entry 1771)。
- `docs/paper-story/2026-09-21b.md:1107` — 原本 5 file は `submit-tree-pair` に無傷で job dir へ byte 複製した。**3 巡の値・判定・稿・図 12 は変えない (規律 7)。変わるのは「原本
- `docs/paper-story/2026-09-21b.md:4476` — 判定は当時の記録による」。**B-6 (d)** 同 job stock 対照の未達 — pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5) で job dir
- `docs/paper-story/2026-09-21b.md:4488` — (`submit-tree-pair` の `git worktree lock`) は第 27 回の /rulings session が打った (entry 1771)。
- `docs/paper-story/2026-09-21.md:231` — (bytes の再検算は受領証以外不可)。[T-2795] pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5) で、21:24 JST に job dir
- `docs/paper-story/2026-09-21.md:1184` — 原本 5 file は `submit-tree-pair` に無傷で job dir へ byte 複製した。**3 巡の値・判定・稿・図 12 は変えない (規律 7)。変わるのは「原本
- `docs/paper-story/2026-09-21.md:4262` — 判定は当時の記録による」。**B-6 (d)** 同 job stock 対照の未達 — pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5) で job dir
- `docs/paper-story/2026-09-21.md:4268` — 捨てる) / 択 C pair 走を直前巡にする (診断と実測の出所が混ざる)。付随: `submit-tree-pair` の `git worktree lock` を非隔離 session が打つ。
- `docs/paper-story/2026-09-29.md:1391` — 原本 5 file は `submit-tree-pair` に無傷で job dir へ byte 複製した。**3 巡の値・判定・稿・図 12 は変えない (規律 7)。変わるのは「原本
- `docs/paper-story/2026-09-29.md:6906` — 判定は当時の記録による」。**B-6 (d)** 同 job stock 対照の未達 — pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5) で job dir
- `docs/paper-story/2026-09-29.md:6918` — (`submit-tree-pair` の `git worktree lock`) は第 27 回の /rulings session が打った (entry 1771)。
- `docs/paper-story/2026-09-21c.md:1118` — 原本 5 file は `submit-tree-pair` に無傷で job dir へ byte 複製した。**3 巡の値・判定・稿・図 12 は変えない (規律 7)。変わるのは「原本
- `docs/paper-story/2026-09-21c.md:4721` — 判定は当時の記録による」。**B-6 (d)** 同 job stock 対照の未達 — pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5) で job dir
- `docs/paper-story/2026-09-21c.md:4733` — (`submit-tree-pair` の `git worktree lock`) は第 27 回の /rulings session が打った (entry 1771)。
- `docs/paper-story/2026-09-27.md:1343` — 原本 5 file は `submit-tree-pair` に無傷で job dir へ byte 複製した。**3 巡の値・判定・稿・図 12 は変えない (規律 7)。変わるのは「原本
- `docs/paper-story/2026-09-27.md:6449` — 判定は当時の記録による」。**B-6 (d)** 同 job stock 対照の未達 — pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5) で job dir
- `docs/paper-story/2026-09-27.md:6461` — (`submit-tree-pair` の `git worktree lock`) は第 27 回の /rulings session が打った (entry 1771)。
- `docs/paper-story/2026-09-22.md:1102` — 原本 5 file は `submit-tree-pair` に無傷で job dir へ byte 複製した。**3 巡の値・判定・稿・図 12 は変えない (規律 7)。変わるのは「原本
- `docs/paper-story/2026-09-22.md:4998` — 判定は当時の記録による」。**B-6 (d)** 同 job stock 対照の未達 — pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5) で job dir
- `docs/paper-story/2026-09-22.md:5010` — (`submit-tree-pair` の `git worktree lock`) は第 27 回の /rulings session が打った (entry 1771)。
- `docs/paper-story/2026-09-23.md:1090` — 原本 5 file は `submit-tree-pair` に無傷で job dir へ byte 複製した。**3 巡の値・判定・稿・図 12 は変えない (規律 7)。変わるのは「原本
- `docs/paper-story/2026-09-23.md:5048` — 判定は当時の記録による」。**B-6 (d)** 同 job stock 対照の未達 — pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5) で job dir
- `docs/paper-story/2026-09-23.md:5060` — (`submit-tree-pair` の `git worktree lock`) は第 27 回の /rulings session が打った (entry 1771)。
- `docs/paper-story/results/2026-09-23-k2-manual-loop-four-rounds.md:174` — \| 巡 4 WAL \| 原本 `dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/submit-tree-r4/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/runs/wal
- `docs/paper-story/results/2026-09-23-k2-manual-loop-four-rounds.md:180` — \| pair 再投入 WAL \| byte 複製 `dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/originals-copy-20260922/pair/campaign/runs/wal.jsonl` (14,897 B) \| `5415d01
- `docs/archive/worklog-phase3-0920-1764.md:8` — - **ListAgents (20:55 JST): 稼働 17 session に [T-2795] wave は無い** (entry 1754 で着地済み、job dir の `submit-tree-pair` だけ残存)。編集面の重複:
- `docs/archive/worklog-phase3-0920-1764.md:19` — `submit-tree-pair` に無傷 (sha 5/5) だが worktree は unlocked・未追跡 `output/exploration/` あり = 撤去された候補 1 と同型 (16:26 の候補 list には無い)。
- `docs/archive/worklog-phase3-0920-1764.md:29` — 付随: `submit-tree-pair` の `git worktree lock` を次の非隔離 session が打つ (本 wave の隔離 session では guard が他 worktree への git 操作を拒否)。
- `docs/archive/worklog-phase3-0920-1764.md:644` — やらない理由は `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md` §4。修復 wave の段 1 で `dev-wave-jobs/dev-wave-t2795-k2-pair/submit-tree-p
- `docs/archive/worklog-phase3-0921-1795.md:1` — ## 2026-09-21 (1795) — "[T-2795] K2 同 job pair launcher と one-shot claim の整合を直した — 1 process・1 回の認可 / claim 所有期間で候補→stock を評価する driver へ (コード + テスト + 
- `docs/archive/worklog-phase3-0922-1823.md:1` — ## 2026-09-22 (1823) — [T-2795] K2 の同 job pair を再投入して初めて成立させ (候補 10 と stock がともに certified、stock の source は STOCK)、続けて 4 巡目 1 job (round 3 の派生物から入力、生成
- `docs/archive/worklog-phase3-0922-1823.md:4` — - 段構成は軽量版 (段 2・3 省略、段 4 は「実装しない」で停止規則と P1〜P4 を結果の前に固定、段 6 は read-only レビュー 1 本)。submit-tree 2 本は着手時の local main `8fd2a2f5c` から job root に切り、CCBench だけ
- `docs/archive/worklog-phase3-0922-1823.md:642` — `dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/submit-tree-r4` (byte 複製 `originals-copy-20260922/r4/`)。その後に 4 巡の results 稿と論文ストーリー B-6 (d)「同 job stock
- `docs/archive/worklog-phase3-0921-1775.md:20` — (2) 稼働中だった cleanup session (00:20〜00:36 JST 完走) の final の罠「棚卸し後に lock 状態が変わる (実行中に /rulings session が submit-tree-pair を lock)」を
- `docs/archive/worklog-phase3-0921-1771.md:38` — - **運用操作 1 件 (可逆、先例あり):** `dev-wave-jobs/dev-wave-t2795-k2-pair/submit-tree-pair` (pair 走の原本 5 file + claim の唯一の現物) を
- `docs/archive/worklog-phase3-0921-1771.md:657` — rename、別 out_root。`submit-tree-pair` (pair 走の原本、byte 複製は同 job dir `originals-copy-20260920/`) は 2026-09-21 に lock 済み。
- `docs/archive/worklog-phase3-0920-1754.md:1` — ## 2026-09-20 (1754) — [T-2795] K2 手動 loop の同 job pair を初投入した — 候補 10 の再評価は certified (811,956 tps)、stock は one-shot claim leaf で認可前に停止し pair 不成立 (STO
- `docs/archive/worklog-phase3-0920-1754.md:6` — `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/HANDOFF.md`。引数が指した `docs/phase3-s4b-runbook.md` の「同 job pair」節は不在で、正本は
- `docs/archive/worklog-phase3-0923-1832.md:3` — - 依頼 (ユーザー直接起動の `/dev-wave`): [T-2860] 項どおり critic-4 1 回、AO 取込み、層 3、4 巡の results 稿、B-6 (d) の更新。原本 (lock 済み `submit-tree-r4`) は動かさない (同時刻の [T-2853] が読み

生記録・逐語・台帳 (path 文字列が埋まっているだけ。dir 別の行数):

- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/materials` : 5
- `output/insights/2026-09-20/k2-loop-originals-lost-downstream/reviews` : 5
- `output/insights/2026-09-20/t2243-collection-contention/verbatim` : 3
- `output/insights/2026-09-20/t2795-k2-pair-attempt/evidence` : 15
- `output/insights/2026-09-20/t2795-k2-pair-attempt/materials` : 2
- `output/insights/2026-09-20/t2795-k2-pair-attempt/reviews` : 49
- `output/insights/2026-09-20/t2797-b5-contrast/verbatim` : 5
- `output/insights/2026-09-21/acceptance-gate-wait-diagnosis/verbatim` : 13
- `output/insights/2026-09-21/t2632-b4-evidence-carrier/verbatim` : 1
- `output/insights/2026-09-21/t2795-pair-repair/reviews` : 5
- `output/insights/2026-09-21/t2795-pair-repair/verbatim` : 1
- `output/insights/2026-09-21/t2812-old-series-realignment/evidence` : 13
- `output/insights/2026-09-21/t2814-cleanup-command/verbatim` : 3
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/evidence` : 18
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/materials` : 6
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/reviews` : 29
- `output/insights/2026-09-22/t2795-k2-pair-resubmit/verbatim` : 1
- `output/insights/2026-09-22/t2853-repro-package-estimate/verbatim` : 1
- `output/insights/2026-09-23/t2853-repro-package-archive/verbatim` : 26
- `output/insights/2026-09-23/t2860-k2-round4-reflux/logs` : 17
- `output/insights/2026-09-23/t2860-k2-round4-reflux/materials` : 8
- `output/insights/2026-09-23/t2860-k2-round4-reflux/reviews` : 4
- `output/insights/2026-09-26/t2838-gate-argv-unify/verbatim` : 21
- `output/insights/2026-09-27/t2104-campaign-flock-scope/verbatim` : 6
- `output/insights/2026-09-29/t2871-policy-loop-iter/verbatim` : 2

### A-5. 系列 5 (T-2797 試走): 検索語 dev-wave-t2797-b5-contrast (計 1371 行)

個別行 (README・docs・台帳):

- `output/insights/2026-09-21/land-roundtrip-diagnosis/land-attempts-timeline.txt:2` — WAVE dev-wave-t2797-b5-contrast
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.stdout.txt:101` — dev-wave-t2797-b5-contrast \| accept-preclaim \| 2026-09-21T04:21:32+09:00 / 2026-09-21T04:29:06+09:00 \| 454.0 \| e4f4c900c2a5 \| 70/None \| 2.93 \| 
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.stdout.txt:103` — dev-wave-t2797-b5-contrast \| accept-preclaim \| 2026-09-21T04:40:32+09:00 / 2026-09-21T04:52:36+09:00 \| 724.0 \| 088bbdec71e4 \| 0/None \| 2.39 \| c
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.stdout.txt:104` — dev-wave-t2797-b5-contrast \| land \| 2026-09-21T04:54:42+09:00 / 2026-09-21T04:54:43+09:00 \| 1.0 \| cf1c90e1faf9 \| 23/rejected \| None \| None: \| 
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.stdout.txt:105` — dev-wave-t2797-b5-contrast \| accept-preclaim \| 2026-09-21T04:57:50+09:00 / 2026-09-21T05:20:47+09:00 \| 1377.0 \| cf1c90e1faf9 \| 0/None \| 1.44 \| 
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.stdout.txt:106` — dev-wave-t2797-b5-contrast \| land \| 2026-09-21T05:21:30+09:00 / 2026-09-21T05:26:06+09:00 \| 276.0 \| cf1c90e1faf9 \| 0/landed \| None \| 4608b76141
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.jsonl:99` — {"wave": "dev-wave-t2797-b5-contrast", "stage": "accept-preclaim", "source": "acceptance-final-1.started.txt", "start": "2026-09-21T04:21:32+09:00", "
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.jsonl:101` — {"wave": "dev-wave-t2797-b5-contrast", "stage": "accept-preclaim", "source": "acceptance-final2-1.started.txt", "start": "2026-09-21T04:40:32+09:00", 
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.jsonl:102` — {"wave": "dev-wave-t2797-b5-contrast", "stage": "land", "source": "land-loop-try1.log", "start": "2026-09-21T04:54:42+09:00", "end": "2026-09-21T04:54
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.jsonl:103` — {"wave": "dev-wave-t2797-b5-contrast", "stage": "accept-preclaim", "source": "acceptance-final3-1.started.txt", "start": "2026-09-21T04:57:50+09:00", 
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/measurements/p3-attempts.jsonl:104` — {"wave": "dev-wave-t2797-b5-contrast", "stage": "land", "source": "land-loop.log", "start": "2026-09-21T05:21:30+09:00", "end": "2026-09-21T05:26:06+0
- `output/insights/2026-09-21/r29-items4-9-diagnosis/README.md:113` — 集合 21 file は t2797 の launcher (`dev-wave-t2797-b5-contrast/focus/run-focus.sh`) の既定 argv で、件数は同 wave の焦点走と一致するが focus-3 と同一 argv とは主張しない
- `output/insights/2026-09-21/r29-items4-9-diagnosis/README.md:148` — `test_define_sink_cross_product_t2520_certify_entry_removal`、`test_patch_define_inventory_matches_condition_gate_registry`)。T-2797 `dev-wave-t2797-b5-
- `output/insights/2026-09-21/t2344-closure-emitters/stale-tree-locks.json:18` — "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-03876f43/campaign.lock",
- `output/insights/2026-09-21/t2344-closure-emitters/stale-tree-locks.json:19` — "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-04c83810/campaign.lock",
- `output/insights/2026-09-21/t2344-closure-emitters/stale-tree-locks.json:20` — "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-182f07a6/campaign.lock"
- `output/insights/2026-09-21/acceptance-gate-wait-diagnosis/README.md:110` — \| dev-wave-t2797-b5-contrast \| 実装 \| 3 \| 3 \| 2 \| 415 \| 0 \|
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:65` — \| b5-pilot-jobdir \| B-5 試走 \| `dev-wave-t2797-b5-contrast/` (`submit-tree/`・`mutation-source/` を除く) \| 1,683 \| 27,358,224 \| 一致 \| 85.1 / 2.4 \|
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:66` — \| b5-pilot-originals \| B-5 試走 (campaign 原本) \| `dev-wave-t2797-b5-contrast/submit-tree/output/` の campaign 53・claim 53・`namespace.json` \| 274 \| 1,
- `output/insights/2026-09-23/t2853-repro-package-archive/README.md:152` — \| 写し \| `data/dev-wave-t2797-b5-contrast/` (台帳 `ledgers/`、入力素材 `materials/`、LLM 入出力、`pilot/` の報告と所要、codex の段記録)、submit-tree 内の campaign 原本 53 と claim
- `output/insights/2026-09-22/t2853-repro-package-estimate/README.md:126` — - job dir にある系列の dir 全体は大きいが、多くは repo の写しである。例: B-5 試走 `dev-wave-t2797-b5-contrast` 全体 2,661,132,881 B のうち、
- `output/insights/2026-09-20/t2797-b5-contrast/README.md:3` — wave `dev-wave-t2797-b5-contrast` (branch `worktree-dev-wave-t2797-b5-contrast`)、起点 local main `6a3e15809` → 着手中に `b9904a5f8` へ ff。
- `output/insights/2026-09-20/t2797-b5-contrast/README.md:5` — 専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/HANDOFF.md`。
- `output/insights/2026-09-20/t2797-b5-contrast/README.md:264` — - job dir (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/` (HANDOFF.md、codex artifact、focus、mutation 結果 JSON 全文、submit-tree、led
- `docs/spool/FOLDED.md:5149` — - {"allocations":{"T:b5-job-body-node-local-lock":"[T-2830]"},"authored":"2026-09-20","base":"3dbe5a41e92a17fa2169338e0516ccdb7ab1d207","content_sha25
- `docs/spool/FOLDED.md:5150` — - {"allocations":{"D:b5-pilot-execution-facts":"D2199","D:b5-slot-subprocess-driver":"D2198"},"authored":"2026-09-20","base":"3dbe5a41e92a17fa2169338e
- `docs/spool/FOLDED.md:5151` — - {"allocations":{},"authored":"2026-09-20","base":"3dbe5a41e92a17fa2169338e0516ccdb7ab1d207","content_sha256":"e50bad4a2a5f76279c28704f87bba03fb2694c
- `docs/paper-story/claim-evidence/2026-09-21.md:187` — \| C38 \| 〔限定付き観測 — 上限付き試走・主標本外・n = 1 系列 / arm〕B-5 生成器対照の上限付き試走 (β、D2172 項 4 (β) の認可、[T-2797]、2026-09-20 22:01 〜 09-21 04:02 JST) は、3 arm (random / sw
- `docs/paper-story/claim-evidence/2026-09-21b.md:195` — \| C38 \| 〔限定付き観測 — 上限付き試走・主標本外・n = 1 系列 / arm〕B-5 生成器対照の上限付き試走 (β、D2172 項 4 (β) の認可、[T-2797]、2026-09-20 22:01 〜 09-21 04:02 JST) は、3 arm (random / sw
- `docs/archive/worklog-phase3-0921-1779.md:1` — ## 2026-09-21 (1779) — [T-2797] B-5 生成器対照の (α) §10 残部品を Codex author で段階実装し (β) 上限付き試走 53 論理 session を完走した — 3 arm の score 4.00〜4.05M tps (floor 内、n=1

生記録・逐語・台帳 (path 文字列が埋まっているだけ。dir 別の行数):

- `output/insights/2026-09-20/t2243-collection-contention/verbatim` : 1
- `output/insights/2026-09-20/t2797-b5-contrast/ledgers` : 113
- `output/insights/2026-09-20/t2797-b5-contrast/llm` : 77
- `output/insights/2026-09-20/t2797-b5-contrast/mutation` : 3
- `output/insights/2026-09-20/t2797-b5-contrast/pilot` : 701
- `output/insights/2026-09-20/t2797-b5-contrast/verbatim` : 93
- `output/insights/2026-09-21/acceptance-gate-wait-diagnosis/verbatim` : 27
- `output/insights/2026-09-21/acceptance-resubmit-causes/verbatim` : 1
- `output/insights/2026-09-21/focus-run-count-diagnosis/verbatim` : 2
- `output/insights/2026-09-21/login-check-count-wall/verbatim` : 7
- `output/insights/2026-09-21/provenance-receipt-land-chain-diag/verbatim` : 12
- `output/insights/2026-09-21/r29-items4-9-diagnosis/verbatim` : 7
- `output/insights/2026-09-21/t2344-closure-emitters/verbatim` : 1
- `output/insights/2026-09-21/t2632-b4-evidence-carrier/verbatim` : 1
- `output/insights/2026-09-21/t2797-tier0/probe` : 243
- `output/insights/2026-09-21/t2830-b5-node-local-lock/verbatim` : 1
- `output/insights/2026-09-21/waiter-collect-latency/verbatim` : 2
- `output/insights/2026-09-21/wave-startup-cost/verbatim` : 7
- `output/insights/2026-09-22/t2797-effect-bundle/mutation` : 8
- `output/insights/2026-09-22/t2797-effect-bundle/verbatim` : 8
- `output/insights/2026-09-22/t2853-repro-package-estimate/verbatim` : 11
- `output/insights/2026-09-23/t2853-repro-package-archive/verbatim` : 2
- `output/insights/2026-09-26/t2838-gate-argv-unify/verbatim` : 12
- `output/insights/2026-09-27/t2104-campaign-flock-scope/verbatim` : 1

### A-6. 系列 6 (T-2797 本走): 検索語 dev-wave-t2797-b5-main-run / b5-main-run/submit (submit-trees/tNN を名指す行は 0 件) (計 7 行)

個別行 (README・docs・台帳):

- `output/insights/2026-09-26/t2797-b5-v2-prep/README.md:18` — 一次資料 (読むだけ): 本走 wave の job dir `dev-wave-t2797-b5-main-run/` の `driver-state/b1-s1/b1-write-heavy-r01-llm/a-{1..14}/`、`materials/b1-write-heavy-r01-ll
- `output/insights/2026-09-26/t2797-b5-cost-options/README.md:32` — 一次資料は本走 wave の job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-main-run/`、読むだけ) の台帳 `ledgers/b5-registered-v1/block-1/*/*/*/events/*.json`
- `output/insights/2026-09-22/comsys2026-manuscript/README.md:263` — - **(c) で書かなかったこと (親の裁定):** B-5 の発効 commit (`6fce61d6e`) は未着地の branch `worktree-dev-wave-t2797-b5-main-run` にだけあり (main の祖先でないことを 2026-09-26 に実測)、同 wa
- `docs/archive/worklog-phase3-0926-1859.md:6` — - 親の provisional 裁定 (段 1): (P1) 7 節 (c) は「本走は認可したが本稿の時点で結果は無い」に留めた。B-5 の発効 commit `6fce61d6e` は未着地の branch `worktree-dev-wave-t2797-b5-main-run` にだけあり

生記録・逐語・台帳 (path 文字列が埋まっているだけ。dir 別の行数):

- `output/insights/2026-09-26/t2797-b5-cost-options/verbatim` : 1
- `output/insights/2026-09-26/t2797-b5-v2-prep/verbatim` : 2

### A-7. 系列 7 (発効木・branch): 検索語 t2797-b5-effect / 6fce61d6e / worktree-dev-wave-t2797-b5-main-run。t2797-b5-effect は wave 名 t2797-b5-effect-bundle にも部分一致するため、6fce61d6e または branch 名を含む行だけを個別列挙し、他は束ねた (計 409 行)

個別行 (README・docs・台帳):

- `output/insights/2026-09-26/paper-methods-ja/implementation.md:51` — LLM 親の週次上限 = F1050。発効 commit `6fce61d6e` は採用時点の main の祖先でない (親 wave が `git merge-base --is-ancestor` で実測)。
- `output/insights/2026-09-22/comsys2026-manuscript/README.md:263` — - **(c) で書かなかったこと (親の裁定):** B-5 の発効 commit (`6fce61d6e`) は未着地の branch `worktree-dev-wave-t2797-b5-main-run` にだけあり (main の祖先でないことを 2026-09-26 に実測)、同 wa
- `docs/paper-story/2026-09-29.md:4225` — B-5 の発効 commit `6fce61d6e` は main の祖先でない本走 wave の branch にあり、本走 wave は未着地)。12 job の Elapse 計 126,426 s (35.1 node 時間)、
- `docs/paper-story/2026-09-29.md:4844` — **2026-09-26 版の起点で、本走 v1 の block 1 stage 1 (12 job) は投入された後に中断しており (entry 1866、D2243 の索引外。発効 commit `6fce61d6e` は main 未着地の
- `docs/paper-story/2026-09-29.md:5405` — **2026-09-26 版の更新: 本走は D2227 項 2 で認可され、block 1 stage 1 (12 job) が投入された後に中断している (entry 1866。発効 commit `6fce61d6e` は main 未着地の
- `docs/paper-story/2026-09-29.md:5796` — - [ ] **B-5 本走 v1 の判定不能を「結果」「差が無かった」「LLM が負けた」と書かない** — 本走の block 1 stage 1 (12 job) は投入後に中断し、LLM 親 4 本の週上限 (429) による提案待ちの時間切れと write-heavy random 2 系
- `docs/paper-story/2026-09-29.md:6651` — 発効 commit (`6fce61d6e`) は前版の起点でも本版の起点でも main の祖先でない本走 wave の branch にある。対照は未取得のままである。別に、VLDB 方針の
- `docs/paper-story/2026-09-29.md:6752` — **発効 commit `6fce61d6e` と本走 wave の記録は main の祖先でない branch にあり (本走 wave は未着地)、着地済みの正典が記すのは投入・中断と、費用案の稿が本走 wave の
- `docs/paper-story/2026-09-26.md:3382` — B-5 の発効 commit `6fce61d6e` は main の祖先でない本走 wave の branch にあり、本走 wave は未着地)。12 job の Elapse 計 126,426 s (35.1 node 時間)、
- `docs/paper-story/2026-09-26.md:3845` — **この版の起点で、本走 v1 の block 1 stage 1 (12 job) は投入された後に中断しており (entry 1866、D2243 の索引外。発効 commit `6fce61d6e` は main 未着地の
- `docs/paper-story/2026-09-26.md:4349` — **この版の更新: 本走は D2227 項 2 で認可され、block 1 stage 1 (12 job) が投入された後に中断している (entry 1866。発効 commit `6fce61d6e` は main 未着地の
- `docs/paper-story/2026-09-26.md:4714` — - [ ] **B-5 本走 v1 の判定不能を「結果」「差が無かった」「LLM が負けた」と書かない** — 本走の block 1 stage 1 (12 job) は投入後に中断し、LLM 親 4 本の週上限 (429) による提案待ちの時間切れと write-heavy random 2 系
- `docs/paper-story/2026-09-26.md:5391` — B: n = 9 / C: read-heavy を外す / D: 見送り) である。発効 commit (`6fce61d6e`) は main の祖先でない本走 wave の branch にある。対照は未取得のままである。別に、VLDB 方針の
- `docs/paper-story/2026-09-26.md:5480` — **発効 commit `6fce61d6e` と本走 wave の記録は main の祖先でない branch にあり (本走 wave は未着地)、着地済みの正典が記すのは投入・中断と、費用案の稿が本走 wave の
- `docs/paper-story/2026-09-27.md:3946` — B-5 の発効 commit `6fce61d6e` は main の祖先でない本走 wave の branch にあり、本走 wave は未着地)。12 job の Elapse 計 126,426 s (35.1 node 時間)、
- `docs/paper-story/2026-09-27.md:4498` — **前版の起点で、本走 v1 の block 1 stage 1 (12 job) は投入された後に中断しており (entry 1866、D2243 の索引外。発効 commit `6fce61d6e` は main 未着地の
- `docs/paper-story/2026-09-27.md:5037` — **前版の更新: 本走は D2227 項 2 で認可され、block 1 stage 1 (12 job) が投入された後に中断している (entry 1866。発効 commit `6fce61d6e` は main 未着地の
- `docs/paper-story/2026-09-27.md:5417` — - [ ] **B-5 本走 v1 の判定不能を「結果」「差が無かった」「LLM が負けた」と書かない** — 本走の block 1 stage 1 (12 job) は投入後に中断し、LLM 親 4 本の週上限 (429) による提案待ちの時間切れと write-heavy random 2 系
- `docs/paper-story/2026-09-27.md:6236` — 発効 commit (`6fce61d6e`) は本版の起点でも main の祖先でない本走 wave の branch にある。対照は未取得のままである。別に、VLDB 方針の
- `docs/paper-story/2026-09-27.md:6337` — **発効 commit `6fce61d6e` と本走 wave の記録は main の祖先でない branch にあり (本走 wave は未着地)、着地済みの正典が記すのは投入・中断と、費用案の稿が本走 wave の
- `docs/archive/worklog-phase3-0926-1859.md:6` — - 親の provisional 裁定 (段 1): (P1) 7 節 (c) は「本走は認可したが本稿の時点で結果は無い」に留めた。B-5 の発効 commit `6fce61d6e` は未着地の branch `worktree-dev-wave-t2797-b5-main-run` にだけあり

生記録・逐語・台帳 (path 文字列が埋まっているだけ。dir 別の行数):

- `docs/archive` : 1
- `docs/spool` : 3
- `output/insights/2026-09-22/t2797-effect-bundle` : 1
- `output/insights/2026-09-22/t2797-effect-bundle/mutation` : 286
- `output/insights/2026-09-22/t2797-effect-bundle/verbatim` : 93
- `output/insights/2026-09-26/t2838-gate-argv-unify/verbatim` : 4

### A-8. 系列 8 (T-2273): 検索語 worktree-t2273-shard0-local-copy / eb65d322f / 5c51e958e (計 32 行)

個別行 (README・docs・台帳):

- `output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md:3` — wave `dev-wave-t2273-shard0-local-copy`。実装 branch `worktree-t2273-shard0-local-copy` (tip `5c51e958e` = 実装 `eb65d322f` + main `620a6bb13` の取り込み、**loca
- `output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md:22` — `orchestrator/tests/test_s8b_oracle_driver.py` の 1 file、+100 / −2 (Codex author、子 branch `author-t2273lc-impl` の `48c441a0f` を所有 path 限定 patch で `eb65
- `output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md:38` — 独立 clone (D1009) の固定 commit `5c51e958e`、`tools/mutation_worktree.py --runner-mode dispatch`。期待 node は login の pytest が hook で拒否されるため、初回 dispatch probe
- `output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md:53` — 測定形 (段 4 事前登録 + E1): A = `620a6bb13` (測定開始時の local main、clean worktree `t2273lc-base-a`)、B = `5c51e958e` (A + 実装 1 file、wave 木)。`IZANAGI_ACCEPTANCE_SH
- `docs/decisions.md:72114` — 1. `orchestrator/tests/test_s8b_oracle_driver.py` の共有 base builder の複製元を、xdist session ごとに最初の builder が作る計算ノード局所の写し (`_T080SharedBases.copy_visible_ou
- `docs/archive/worklog-phase3-0926-1860.md:358` — session で最初の builder が写しを作る形で実装し (branch `worktree-t2273-shard0-local-copy`、`eb65d322f`)、隣接 3 対の実受入で測った。shard-0 W_0 の対差 +19.111 / +19.679 / −4.341 秒、
- `docs/archive/worklog-phase3-0926-1858.md:1` — ## 2026-09-26 (1858) — [T-2273] [T-2560] 共有 base の可視 output 複製元を session 局所の写しへ替える実装を隣接 3 対の実受入で測り、事前登録の land 条件を満たさなかったので実装は land しない (記録 + insight、実
- `docs/archive/worklog-phase3-0926-1858.md:4` — - 結果: 有効 3 対の shard-0 W_0 の対差 +19.111 / +19.679 / −4.341 秒、対率中央値 5.2 %。事前登録の land 条件 (3 対すべて短縮 ∧ 対率中央値 ≥ 10 %) を満たさず、実装 (`eb65d322f`、Codex author) は l
- `docs/archive/worklog-phase3-0926-1858.md:348` — - [T-2273] **P1・律速対処の 1 案を実受入で棄却、次の一手はユーザー裁定待ち**: 第 4 回診断の次の一手「t080 共有 base の可視 output 複製元を局所に置く」を、session で最初の builder が写しを作る形で実装し (branch `worktree-

生記録・逐語・台帳 (path 文字列が埋まっているだけ。dir 別の行数):

- `output/insights/2026-09-26/t2273-shard0-local-copy-ab/mutation` : 13
- `output/insights/2026-09-26/t2273-shard0-local-copy-ab/runs` : 1
- `output/insights/2026-09-26/t2273-shard0-local-copy-ab/verbatim` : 7
- `output/insights/2026-09-26/t2273-shard0-precopy-ab/verbatim` : 2
