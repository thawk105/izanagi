# 段 1 棚卸し調査 (担当系列 2: T-2847 / T-2849 / T-2850 / T-2865 / T-2871 / T-2868) — read-only

調査日: 2026-09-30。repo = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration` (main f0869d953 同内容)。
検索: 3 種 (path 断片 = job dir 名・tree 名 / branch 名 / HEAD SHA 先頭 9 桁) を `docs`・`output`・`tools`・`orchestrator`・`hooks`・`.claude`・`src`・`patches` に掛けた (`external` と `.git` は除外)。
以下 `<insight>` = `output/insights/`、job = `/work/1/SFC/tanab/dev-wave-jobs/`。

## 0. 全系列に共通する所見 (先に読む)

1. **consumer (コード・テストが読む) は全系列でなし。** `tools`・`orchestrator`・`hooks`・`.claude`・`src`・`patches` に、`dev-wave-t2847|t2849|t2850|t2865|t2871`・`t2868-mocc-g2`・`t2868-probe` を含む file は 0 件 (grep -l で確認)。`tools/known_violations/` に本系列の HEAD SHA で始まる file も無い。
2. **HEAD SHA は「固定 checkout の commit」であり、tree の実体ではない。** 下記の tree の HEAD (`cadaf3805`・`18f379f0d`・`6c3913bc5`・`299aa022e`・`ffab56d15`・`f180c9de8`・`7ea9aa09d`・`3205dd93e`・`1887f56e4`・`b815183af`・`d7161a2a1`・`339d7c188`) は **すべて main の祖先** (`git merge-base --is-ancestor <sha> main` が rc=0、`b815183af`・`6c3913bc5`・`299aa022e` は T-2853 の記録 `<insight>/2026-09-27/t2853-repro-rest/README.md` §2.1 にも同記述)。tree を撤去しても commit は残る。**唯一の例外は branch `t2868-probe-author` の `d86ec8f48`** (main の祖先でない、系列 8)。
3. **T-2853 (repro-rest) がすでに、次の 3 組の checkout 内の未追跡 campaign 原本と job dir 固有分を repo 外の `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260927/` に写し、sha256・bytes を全件照合済み** (`<insight>/2026-09-27/t2853-repro-rest/README.md` §0 項 1・§2.2 の表 :60-68、`verify.ok=True`・mismatch なし。manifest `t2853-20260927/manifests/*.json` を実読):
   - T-2850 試走 v2 の 19 checkout (`trial-v2/trees/*`、1,728 file、archive 側は `data/dev-wave-t2850-trace-concurrent-verify/trial-v2/trees/` に 18 dir = tree-01..18。`parent-tree` は campaign 原本なし)
   - T-2849 MOCC 疎通の 22 checkout のうち campaign を持つ 21 本 (555 file、`llm-parent` は campaign なし)
   - T-2865 段階 F の `trees/e2e` (13 file)
   これ以外の系列 (T-2847・T-2849 mocc 挿入・T-2850 実装 wave の submit-tree・T-2850 試走 v1・T-2865 系列 B/C・T-2871・T-2868 段階 B) の checkout 内原本は、どの archive にも写されていない (trace の保全先 `izanagi-repro-archive/t2865-iter2-20260927/`・`t2865-series-c-20260929/`・`t2871-liveness-20260929/`・`t2868-mocc-stock-20260927/` は圧縮 trace であって campaign 原本ではない)。ただし下記のとおり、それらの数値は repo の insight に転記済みで、論文ストーリーの使用箇所も insight を一次資料にしている。
4. **論文ストーリー (`docs/paper-story/`) の使用状況:** `docs/paper-story/{figures,results,claim-evidence}` の本文・図・provenance に本系列の path・T-ID は 0 件 (grep -l で確認。`figures/*.provenance.json` の入力 path は b10・a2/a6 cert・b7・mocc-witlight-arm-run 等で本系列に無い)。版 stories (`2026-09-2x.md`) は本系列を **insight README と D 番号を一次資料として引く**形でのみ使う (例: `docs/paper-story/2026-09-29.md:3922,3973,3977,4003,4331,4407,4410,4459,7651`)。数値の出所は repo 内の insight である。job dir の path を数値の出所に挙げている箇所は無い (`docs/paper-story/2026-09-26.md:6804` の `consult-option/decision.md` は「採用の記録の所在」で、job dir 全体の path)。
5. **worklog 末尾 2 エントリ (1953・1954) の「次の一手」と `docs/phase3.md` の現行タスク:** 本系列の path / ref を今後の入力として使う項は 0 件。worklog.md に `dev-wave-t28xx` の path 名指しは無く、[T-2850]・[T-2865] は「(番号) だけの持ち越し」行 (`docs/worklog.md:1760,1768` ほか) で、本文は archive (`docs/archive/worklog-phase3-0929-1912.md:116` と `…-1923.md:112` の [T-2865] 項、`…-1906.md:114` の [T-2850] 項)。その本文の中身は各系列の節で確認した。
6. (c) 有効な事前登録・凍結: `docs/search-repetition-trial-preregistration-addendum-{1,2,3}.md` が T-2850 の固定 commit (`299aa022e`・`7ea9aa09d`・`f180c9de8`) を名指しするが、**commit 単位の束縛** (job ごとに新しい repo 外 checkout を作る) で、既存の tree の path は入力に取っていない。commit は main の祖先で残る。詳細は系列 4。

---

### 系列 1: T-2847 verifier-capacity (submit-tree-A / submit-tree-B)
- worktree / branch / HEAD:
  - `job/dev-wave-t2847-verifier-capacity/submit-tree-A` (gitdir 名 `submit-tree-A`)、`…/submit-tree-B` (同 `submit-tree-B`)。どちらも detached、HEAD `cadaf3805e75bb0d02744955469ef588aabcd5c6` (main の祖先)。branch 名は無い (`git branch --list '*t2847*'` 0 件)。
- 中身: どちらも repo の checkout。`output/` の未追跡物は `pegasus-dispatch/` (A: 2 dir + `submission.lock`、B: 1 dir) と `s1-budget/time_ledger.json` だけ。`output/exploration/campaigns` は無い。job dir 側 `runs/cap-{A,B,C,D}/` に `capacity.json`・`meta.json`・`preflight.json`・`verifier/0001.json…` (verifier の stdout 全文) があるが、これは tree の外 (job dir)。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 (1 行) |
  |---|---|---|---|
  | `<insight>/2026-09-23/t2847-verifier-capacity/README.md:4` | HEAD `cadaf3805` | 固定 checkout (投入元の commit) | 「起点: local main `cadaf3805` (記録の前に `76d0a0c92` へ fast-forward)」 |
  | 同 `:53` | job dir `dev-wave-t2847-verifier-capacity/` の `launch_capacity.v1.py`・`launch_capacity.py` | 再現手順 (repo に入れない起動器の所在) | 「起動器: job dir … の `launch_capacity.v1.py` (sha256 `53c1bb7e…`)」 |
  | 同 `:56` | job dir `runs/cap-*/verifier/` | 原本の所在 (verifier stdout 全文) | 「全文は job dir の `runs/cap-*/verifier/`」 |
  | `…/raw/cap-A-meta.json:20,28,30,45,58` と `cap-B-meta.json`・`cap-C-meta.json`・`cap-D-meta.json` (各 5 行) | `submit-tree-A` / `runs/cap-A` の絶対 path | 経緯の記述 (当時の実行 meta を転記した記録値) | `"repo_root": "…/dev-wave-t2847-verifier-capacity/submit-tree-A"` |
  | `…/raw/cap-A-capacity.json` (38 行)・`cap-B-capacity.json` (38 行)・`cap-C-capacity.json:24`・`cap-D-capacity.json` | `submit-tree-A/external/ccbench` 等 | 経緯の記述 (記録値に含まれる path) | `"…/submit-tree-A/external/ccbench"` |
  | `docs/search-repetition-trial-preregistration-addendum-1.md:46` | 上記 README §5 (path でなく insight を名指し) | 経緯の記述 | 「固定 5 µs の既存記録 (…`t2847-verifier-capacity/README.md` §5)」 |
- 研究での使用判定: **不要**。(a): 論文ストーリーは insight README を一次資料に引く (`docs/paper-story/2026-09-29.md:3922,4410`、`2026-09-26.md:3176,3491`、`2026-09-27.md:3676,4099`、`2026-09-23.md:2939,3175`) だけで、数値は repo 内の `raw/cap-{A..D}-capacity.json` と README §4〜§5 に派生済み → 原本 (tree) は provenance に過ぎない。(b)(c): 該当なし (`docs/phase3.md`、worklog 末尾 2 件、prereg に tree path なし)。確認範囲 = 上記 3 種検索。
- consumer: なし。
- 回収するなら写すべき中身: 不要。参考として tree の外にある `runs/cap-*/verifier/*.json` (verifier stdout 全文) と `launch_capacity*.py` は job dir 側 (tree ではない)。
- 不確実な点: `raw/*-meta.json` の絶対 path は記録値であって参照ではない (読み手の code は無い)。

### 系列 2: T-2849 mocc (submit-tree / submit-tree-b) — MOCC 差し込みの実装 wave
- worktree / branch / HEAD:
  - `job/dev-wave-t2849-mocc/submit-tree` (gitdir 名 `submit-tree6`)、`…/submit-tree-b` (gitdir 名 `submit-tree-b`)。どちらも detached、HEAD `18f379f0d666ed2a1198db6a7cb0712a294c9043` (main の祖先、fix 2 の commit)。wave branch は現存 0 件 (`git branch --list '*t2849*'` 0 件)。
- 中身: `submit-tree`: `output/exploration/campaigns/` に p3-s4-loop 6 本 (liveness の系列 2 = random arm 1,575 s と block 対照 = 未追跡)、`submit-tree-b`: 1 本 (`…-d1d80ad8`)。`output/campaigns/s1-direct-*` は追跡済みの共通物。job dir 側 `liveness/` (cohort・evidence・hydrate 等) と `certify-rr{5,50,95}.log` は tree の外。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `<insight>/2026-09-26/t2849-mocc-insertion/README.md:86` | submit-tree (job dir 下の detached worktree、`18f379f0d`)、`dev-wave-jobs/dev-wave-t2849-mocc/liveness/` | 固定 checkout・原本の所在 (台帳・証跡は job dir) | 「submit-tree (…`18f379f0d`、ccbench = C) から job body を harness mode で直接 qsub した」 |
  | 同 `:5,57,62,79` | `18f379f0d` (fix 2 の commit) | 経緯の記述 (commit 名指し) | 「fix 2 `18f379f0d`」 |
  | 同 `:108-111` | submit-tree の置き場の失敗経緯 | 経緯の記述 | 「submit-tree を `.codex/worktrees` 下から job dir 下へ移した」 |
  | `docs/paper-story/2026-09-29.md:4331`、`docs/phase3.md:28-30` | insight `t2849-mocc-insertion/README.md` (path でなく insight) | 経緯の記述 | 「(一次資料: `output/insights/2026-09-26/t2849-mocc-insertion/README.md`…)」 |
- 研究での使用判定: **不要**。(a): 生死確認 (1 系列・N_eval 1、write-heavy) の値は README §6 の表 (:88-96、throughput・判定・wall) に全件転記済み。README 自身が「性能の主張ではない」と書き、paper-story は insight を引くだけ → 原本は provenance。(b)(c): 該当なし (worklog 末尾・phase3 は T-2849 を完了項として insight path で記録)。
- consumer: なし。
- 回収するなら写すべき中身: 不要。
- 不確実な点: 同 README :125-140 の「submit-tree の作法は段 8 で記載先を決める」は tree 自体の入力ではなく作法の記述。

### 系列 3: T-2849 mocc-conn (`trees/` の 22 本: llm-parent、m-{bal,rh,wh}-{block,bo,evolution,llm,random,sweep} 18、p-{bal,rh,wh} 3)
- worktree / branch / HEAD: `job/dev-wave-t2849-mocc-conn/trees/<名>` の 22 本 (+ 各 `.hydrate.json`)。すべて detached、HEAD `6c3913bc5b0c67cb13cf6e38e0d9d55ecf9426d2` (main の祖先)。branch なし。
- 中身: T-2853 の実測で campaign を持つのは 21 本 (llm-parent は持たない)、555 file・2,473,948 B の未追跡原本 (campaign・claim) が **すでに archive に写し済み** (`izanagi-repro-archive/t2853-20260927/data/dev-wave-t2849-mocc-conn/trees/` に 21 dir、manifest `manifests/t2849-mocc-conn-originals.json` の `verify.ok=True`・mismatch `[]` を実読)。job dir 固有分 (`main/`・`probe/`・`materials/`・`parents/` 等、1,538 file) も `t2849-mocc-conn-jobdir` として写し済み。trace は別途 `izanagi-repro-archive/t2849-mocc-conn-20260926/` に保全。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `<insight>/2026-09-27/t2849-mocc-conn/README.md:3,6` | HEAD `6c3913bc5` | 固定 checkout | 「全 job の submit-tree は `6c3913bc5` (ccbench = pin C …)」 |
  | 同 `:7` | job dir `dev-wave-t2849-mocc-conn/` (`main/cohort`・`main/aggregate.json`・`main/job-costs.json`) | 原本の所在 | 「台帳・証跡・集計は repo 外の job dir …」 |
  | 同 `:8` | `izanagi-repro-archive/t2849-mocc-conn-20260926/` | 原本の所在 (trace) | 「trace の保全先は …」 |
  | 同 `:33` | `trees/m-<wl>-<arm>`、`trees/llm-parent` | 経緯の記述 (投入形) | 「submit-tree | job ごとに 1 本、job dir 下 (`trees/m-<wl>-<arm>`)…」 |
  | 同 `:91` | `trees/m-rh-bo/output/exploration/campaigns/p3-s4-loop-s4-autonomous-c90fb5b6/` | 原本の所在 (例示、anomaly 反復の campaign) | 「(例: bo の初期点 = `trees/m-rh-bo/…`)」 |
  | `<insight>/2026-09-27/t2853-repro-rest/README.md:45,63,66` | 22 checkout の未追跡原本・job dir | 原本の所在 (写し済みの記録) | 「[T-2849] MOCC 疎通 (D2261) | `dev-wave-t2849-mocc-conn/` …22 本の checkout `trees/*` の未追跡 campaign 原本」 |
  | 同 `:85,197` ほか | 「job dir 内の checkout 本体」を写さなかった理由 | 経緯の記述 | 「repo の写し (commit は local main の祖先)」 |
  | `<insight>/2026-09-27/t2853-repro-rest/verbatim/tree-heads.log` (22 行相当) | 各 tree の HEAD | 経緯の記述 (HEAD 一覧) | `dev-wave-t2849-mocc-conn/trees/… 6c3913bc5b0c…` |
  | `<insight>/2026-09-28/t2852-p5-intervention-prereg-draft/README.md:29` | `dev-wave-t2849-mocc-conn/materials/` | 原本の所在 (job dir の materials、tree ではない) | 「(`dev-wave-jobs/dev-wave-t2849-mocc-conn/materials/`、…)」 |
  | `docs/decisions.md:72834` | `dev-wave-jobs/dev-wave-t2849-mocc-conn/user-compute-confirmation.md` | 経緯の記述 (job dir 内 file の所在、tree ではない) | 「repo 外 `…/user-compute-confirmation.md`」(同 file は `<insight>/2026-09-27/t2849-mocc-conn/verbatim/user-compute-confirmation.md` に逐語あり) |
  | `docs/decisions.md:72847` | `izanagi-repro-archive/t2849-mocc-conn-20260926/` | 原本の所在 (trace) | 「保全先は repo 外の …」 |
  | `docs/archive/worklog-phase3-0927-1882-1884.md:1` | 系列全体 | 経緯の記述 | 「[T-2849] 残り (3) … 15 系列すべて b-complete」 |
- 研究での使用判定: **不要**。(a): 論文ストーリーが使うのは 15 系列の stock 比の範囲 (write-heavy 0.66〜1.06・balanced 0.97〜1.20・read-heavy 0.99〜1.76)・G2 の件数 (read-heavy 候補 slot 25 件中 6 件、stock 7 件は 0)・node 時間 13.65 で (`docs/paper-story/2026-09-29.md:7651-7656`、:3977)、いずれも `<insight>/2026-09-27/t2849-mocc-conn/README.md` に派生済み。かつ campaign 原本はすでに archive に sha256 照合つきで写し済みなので、tree は二重の意味で provenance。(b)(c): 該当なし (`docs/phase3.md:32-34` は完了項)。D2277 項 2・T-2868・T-2872 は insight を参照するが tree path は入力に取らない。
- consumer: なし。
- 回収するなら写すべき中身: 不要 (写し済み)。念のため、撤去前に archive 側の manifest 再照合 (`sha256sum -c manifests/t2849-mocc-conn-originals.sha256`) を 1 回行えば足りる。
- 不確実な点: (i) archive 作成 (2026-09-27 19:44) 以降に tree 内へ書かれたものがあるかは、tree 全体の走査を避けたので未確認。T-2868 (9/27)・T-2872 (9/29) の probe は別 tree (系列 8) と別 archive を使っており、mocc-conn の tree を再利用した記録は grep で見つからない。(ii) `llm-parent` は campaign を持たないが `trees/llm-parent` の中身の LLM 親状態は job dir `parents/` に写し済み (T-2853 の組 `t2849-mocc-conn-jobdir`)。

### 系列 4: T-2850 trace-concurrent-verify (submit-tree / submit-tree-2 と trial-v2/trees の 19 本)
- worktree / branch / HEAD:
  - `job/dev-wave-t2850-trace-concurrent-verify/submit-tree` (gitdir 名 `submit-tree7`) HEAD `ffab56d1567f79897c86292ebe891fb39c0425bf` (fix 4)。
  - `…/submit-tree-2` (gitdir 名 `submit-tree-2`) HEAD `f180c9de8d7496af5c4c14add1d940a03469b6b9` (fix 5)。
  - `…/trial-v2/trees/{parent-tree,tree-01..tree-18}` 19 本、HEAD すべて `299aa022ef08fca35ee4625e847cc25b49397ee6` (本実装を取り込んだ fold commit)。
  - 3 種の commit はすべて main の祖先。branch なし。
- 中身: `submit-tree`: smoke campaign 1 本 (`…-6bc9dc53`)、`submit-tree-2`: 5 本 (再 smoke、上限 120 秒) — いずれも未追跡で archive 未写し。`trial-v2/trees` の 18 本 (tree-01..18) の campaign 原本 (1,728 file、7,865,228 B) は **archive 写し済み** (`t2850-trial-v2-originals`、照合一致)。job dir 側 (`trial-v2/` の cohort・evidence・state・materials・parents・投入台帳、4,317 file) も `t2850-trial-v2-rundir` として写し済み。`dev-wave-t2850-trial-v2-followup/` (集計) は別 job dir で写し済み (`t2850-trial-v2-followup-jobdir`)。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `<insight>/2026-09-26/t2850-trace-concurrent-verify/README.md:5` | job dir 全体 | 原本の所在 | 「job dir (repo 外) = `…/dev-wave-t2850-trace-concurrent-verify/`」 |
  | 同 `:15,16,37,38,49,71,106,120,124` | `ffab56d15`・`f180c9de8` | 経緯の記述 (commit 名指し、smoke・変異の対象 commit) | 「`f180c9de8` | fix 5: 同時検査 mode の初回静定待ちの上限 60 → 120 秒」 |
  | 同 `:133,147` | 固定 commit `299aa022e`、`trial-v2/` | 固定 checkout・原本の所在 | 「固定 commit `299aa022ef…`。job ごとに 1 本の repo 外 detached checkout」「所在はすべて repo 外の job dir `…/trial-v2/`」 |
  | `<insight>/2026-09-27/t2850-trial-v2-analysis/README.md:6,8,80` | `dev-wave-t2850-trial-v2-followup/`・`glue-v4/` | 原本の所在 (集計、glue) | 「集計は repo 外の job dir `…/dev-wave-t2850-trial-v2-followup/` で行った」 |
  | `<insight>/2026-09-27/t2850-trial-v2-analysis/verbatim/{s2-plan,s3-consult-a,s3-consult-b,scripts}.md` (計 38 行) | `trial-v2/` 配下の path | 経緯の記述 (相談・plan の引用) | 「`…/trial-v2/…`」 |
  | `<insight>/2026-09-27/t2853-repro-rest/README.md:44,64,68,89,197` | 19 checkout・`trial-v2/` | 原本の所在 (写し済みの記録) | 「19 本の checkout `trial-v2/trees/{tree-01..18,parent-tree}` の未追跡 campaign 原本」 |
  | 同 `verbatim/tree-heads.log` (19 行) | 各 tree の HEAD | 経緯の記述 | `…/trial-v2/trees/tree-01 299aa022ef08…` |
  | `<insight>/2026-09-28/t2852-p5-intervention-prereg-draft/README.md:22,29` | `trial-v2/parents/header.md:7`・`trial-v2/materials/` | 原本の所在 (job dir 内 file、tree ではない) | 「repo 外 `/work/…/trial-v2/parents/header.md:7`」 |
  | `docs/search-repetition-trial-preregistration-addendum-2.md:19,49,86` | `299aa022e`・`f180c9de8`・`dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/estimate/estimate_v2.py` | 固定 checkout (commit)・原本の所在 (見積り script は job dir) | 「計算は … `estimate_v2.py` (repo 外、結果 `estimate_v2.json`)」 |
  | `docs/search-repetition-trial-preregistration-addendum-3.md:19,80` | 固定 commit `299aa022e`、「job ごとに repo 外の checkout 1 本」 | 固定 checkout (commit、投入元の設計) | 「試走 v2 と同じ commit `299aa022e` の repo 外 checkout で …」 |
  | `docs/workload-description-critic-intervention-preregistration.md:162` | `f180c9de8` | 固定 checkout (commit) | 「`f180c9de8d7496af…` と同一で、差は test だけ」 |
  | `docs/decisions.md:72455,72558,72789` | 記録 insight・所在 (§6)・待ち区間 | 経緯の記述 | 「記録と repo 外の成果物の所在は `…/t2850-trace-concurrent-verify/README.md` §6」 (注: その README に §6 の見出しは無く、所在は §5 末・:147 相当。名指しの中身は job dir 全体) |
  | `docs/archive/worklog-phase3-0926-1873-0927-1876.md:1893` | `trial-v2/`、固定 commit `299aa022e` | 経緯の記述 | 「request 30122〜30139、固定 commit `299aa022e`、repo 外の job dir `…/trial-v2/`」 |
- 研究での使用判定: **不要** (tree について)。(a): 論文ストーリーの試走 v2 数値 (18 job の Elapse 計 28.70 node 時間、評価 1 回の内訳など、`docs/paper-story/2026-09-29.md:2430,4459`) の出所は `<insight>/2026-09-27/t2850-trial-v2-analysis/README.md` と `<insight>/2026-09-26/t2850-trial-pause-cost-options/README.md` で、集計は `trial-v2-followup` (別 job dir、archive 写し済み)。checkout 内の campaign 原本も写し済み → 原本 tree は provenance。`submit-tree`・`submit-tree-2` の smoke 値は README §3.1・§3.3 (:49-:71 以降) に転記済み (job 29777・29854 の Elapse・時刻等)。(b): worklog 末尾 2 件・phase3 に該当なし。(c) **要注意の留保:** addendum-3 と `docs/workload-description-critic-intervention-preregistration.md:162` は T-2850 本比較 (D2272 項 2 で「今は投入しない」、glue v4 は未投入) の入力として **commit `299aa022e`** を名指しする。これは commit 束縛で、投入時に新しい checkout を作るので、既存 tree の撤去とは無関係。commit は main の祖先で残る。(c) の該当条件「path / ref を入力に取る」に**当たるのは ref (`299aa022e`) だけ**で、この ref は無傷。
- consumer: なし。
- 回収するなら写すべき中身: 不要。`submit-tree`・`submit-tree-2` の smoke campaign (合計 6 本、未追跡・未写し) は README §3 の値の原本だが、値は転記済み。
- 不確実な点: (i) `trial-v2` の trace の保全先は T-2853 が「特定できなかった」と記録 (`t2853-repro-rest/README.md:89`)。tree 撤去で失われる trace は無い (trace は tree の外) が、trace 自体の所在不明は別問題として残る。(ii) archive 作成後に `trial-v2/trees` へ追加が無いかは未走査。(iii) 上表 decisions.md:72558 の「§6」は現 README の節番号と合わない可能性 (README の節構成は未精査、目的に影響なし)。

### 系列 5: T-2850 trial-run (試走 v1) の tree と vprobe
- worktree / branch / HEAD:
  - `job/dev-wave-t2850-trial-run/submit-tree` (gitdir 名 `submit-tree2`) HEAD `7ea9aa09dad0012aebd5464c70a9e468c409dd92`。
  - `…/vprobe/submit-tree-vp` (gitdir 名 `submit-tree-vp`) HEAD 同 `7ea9aa09d`。
  - 両方 detached。`7ea9aa09d` は main の祖先。wave branch (`worktree-t2850-trial-run`) は現存せず。
- 中身: `submit-tree/output/exploration/campaigns/` に p3-s4-loop 64 本 (block 1 の試走 v1、未追跡、**どの archive にも未写し** — T-2853 が「依頼は試走 v2。v1 の block 1 は v2 が旧 block 1 として比べるだけ」として除外、`t2853-repro-rest/README.md:87`)。`vprobe/submit-tree-vp` は campaign なし。job dir 側: `cohort-trial/write-heavy/`・`evidence-trial/t2850-trial-v1/`・`estimate/`(block1-breakdown.json 等)・`vprobe/runs/*/probe.json`(生データ)・`consult-option/decision.md`・`glue*`。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `<insight>/2026-09-23/t2850-trial-effect-bundle/README.md:5,6` | wave `worktree-t2850-trial-run`、job dir `dev-wave-t2850-trial-run/` | 経緯の記述・原本の所在 | 「job dir (repo 外): `…/dev-wave-t2850-trial-run/` (brief・…・submit-tree・台帳…)」 |
  | 同 `:11` と `bundle/glue-sha256.txt`(7 行)・`bundle/t2850-trial-effect-bundle.json`(3 行)・`bundle/trial-schedule-wh.json`(18 行)・`bundle/t2850-llm-parent-template.md`(1 行) | `7ea9aa09d`、job dir の glue・`materials/`・`parents/` | 発効版 (ref)・原本の所在 (glue の SHA-256 を発効束に写した記録) | 「固定 commit の実装・検査器・役割定義 29 file の SHA-256 (`files-sha256-at-7ea9aa09d.txt`)」 |
  | 同 `:32` | `dev-wave-t2850-trial-run/estimate/estimate_v1.py` | 再現手順 (計算 script の所在) | 「計算は `/work/…/dev-wave-t2850-trial-run/estimate/estimate_v1.py`」 |
  | `<insight>/2026-09-26/t2850-trial-pause-cost-options/README.md:6,7,36` | job dir の `cohort-trial/`・`evidence-trial/`・`estimate/`・`vprobe/runs/*/probe.json`、`7ea9aa09d` | 原本の所在・固定 checkout | 「block 1 の台帳 `cohort-trial/`・`evidence-trial/`、内訳 `estimate/block1-breakdown.json`…生データ `vprobe/runs/*/probe.json`」「評価 1 回の内訳 (block 1、S1 write-heavy、commit `7ea9aa09d`)」 |
  | `<insight>/2026-09-26/t2797-b5-cost-options/README.md:132,227` | `dev-wave-jobs/dev-wave-t2850-trial-run/vprobe/runs/vp-rh-b0lw0-c2/probe.json` | 原本の所在 (生データ) | 「(生データ `dev-wave-jobs/dev-wave-t2850-trial-run/vprobe/runs/vp-rh-b0lw0-c2/probe.json`)」 |
  | `<insight>/2026-09-23/t2850-trial-prereg/README.md:48` ほか | 受領証の job dir `dev-wave-t2850-trial-prereg/` | 原本の所在 (別 job dir) | 「受領証は wave の job dir …」 |
  | `docs/search-repetition-trial-preregistration-addendum-1.md:9,58` | `7ea9aa09dad0…`、`dev-wave-t2850-trial-run/estimate/` | 発効版 (ref)・再現手順 | 「実装 (commit `7ea9aa09dad0012aebd5464c70a9e468c409dd92`、D2233 …)」「計算は repo 外の `dev-wave-t2850-trial-run/estimate/` (発効束に写す)」 |
  | `docs/decisions.md:72426`、`docs/paper-story/2026-09-26.md:6804`、`<insight>/2026-09-26/t2850-trace-concurrent-verify/README.md:3` | `dev-wave-t2850-trial-run/consult-option/decision.md` | 原本の所在 (親裁定の**唯一の記録**、「job dir にだけ記録され」) | 「(`…/consult-option/decision.md`)。計算投入の確認は後継 wave が取る」 |
- 研究での使用判定: **不要** (tree について)。(a): 論文ストーリーが試走 v1 から使う数値 — 「評価 1 回の約 91 %が検査」(`docs/paper-story/2026-09-29.md:1760`、:2430 付近の block 1 の記述) — は `<insight>/2026-09-26/t2850-trial-pause-cost-options/README.md` §2 (:36-) の表に派生済み。v2 analysis も「旧 block 1 (直列検査) では約 91%」と同 insight から引く (`t2850-trial-v2-analysis/README.md:32`)。tree 内の campaign 64 本は原本 (block 1 の 18 job 系列と smoke)。(b)(c): 該当なし。addendum-1 の `estimate/` は job dir 内 file で tree ではなく、しかも試走 v1 の発効束は D2258・D2259 で閉じられ v2 は見送りの経緯 (`docs/paper-story/2026-09-29.md:2706`)。
- consumer: なし。
- 回収するなら写すべき中身: tree としては不要。**ただし tree の外だが同 job dir にあり、repo に無く、insight が「生データ・唯一の記録」と名指ししているもの**を、job dir を消す/動かす段があるなら別途扱う必要がある: `vprobe/runs/*/probe.json` (`t2797-b5-cost-options` と `t2850-trial-pause-cost-options` が生データとして名指し)、`consult-option/decision.md` (decisions.md:72426・paper-story 2026-09-26.md:6804 が「にだけ記録」と書く親裁定)、`estimate/{estimate_v1.py,block1-breakdown.json,cost_options.py,cost-options-*.json}`、`glue*`。これは本調査の tree 撤去対象外だが、job dir 単位の移行 wave では要確認。
- 不確実な点: (i) `submit-tree` 内 64 campaign のうち追跡済み共通物との切り分けは未実施 (`ls` の件数)。(ii) `vprobe/submit-tree-vp` の中身は campaign を持たない (`exploration/campaigns` 不在を実確認)。

### 系列 6: T-2865 系列 B (iter2/trees/b)・系列 C (series-c/trees/c)・段階 F (stage-f/trees/e2e)
- worktree / branch / HEAD (いずれも detached、branch なし、HEAD は main の祖先):
  - `job/dev-wave-t2865-iter2/trees/b` (gitdir 名 `b`) HEAD `3205dd93e34cb1e42da77f9fcd5bc4783046ff5b` (系列 B)。
  - `job/dev-wave-t2865-series-c/trees/c` (gitdir 名 `c`) HEAD `1887f56e46c9e43b94f02572fe13d9b16ba39e41` (系列 C、**2026-09-29 の作成で最も新しい**)。
  - `job/dev-wave-t2865-stage-f/trees/e2e` (gitdir 名 `e2e`) HEAD `b815183af696d1ec18abcbd5a0881548a91657f3` (main の祖先、段階 F・旧系列 A)。
- 中身: いずれも `output/exploration/campaigns/p3-silo-policy-loop-silo-policy-autonomous-*` の未追跡 campaign と `output/env/pegasus/claims/*.claim`。
  - `b`: `…-877344a7` (loop、`loop_state.json`・`policy_history.jsonl`・`silo_policy_loop_digest.txt`)・`…-a84dd632` (bootstrap)。
  - `c`: `…-877344a7`・`…-a84dd632`・`…-4e8009c5`・`…-8a9c885c`・`…-f6ac2c7c` の 5 本 (bootstrap 1 + 計測 campaign 3 + loop 1)、claim 多数。job dir 側に `evidence/{pair-c2,c3,c4,stock-c0}`・`llm/`・`qstate.log` 等。
  - `e2e`: `…-798ec179`・`…-877344a7`・`…-a84dd632` の 3 本 (**archive 写し済み**、`t2865-stage-f-originals` 13 file・81,266 B、照合一致、`t2853-repro-rest/README.md:62`)。
  - `b`・`c` の campaign 原本は archive 未写し (trace は `izanagi-repro-archive/t2865-iter2-20260927/`・`t2865-series-c-20260929/` に別途あり)。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `<insight>/2026-09-27/t2865-silo-policy-iter2/README.md:41,43` | `trees/b` (HEAD `3205dd93e`)、`trees/e2e` (HEAD `b815183af`)、trace 保全先 | 固定 checkout・原本の所在 | 「submit checkout: `…/dev-wave-t2865-iter2/trees/b` (HEAD `3205dd93e`、骨格 patch SHA-256 `9cb54552…`、locked)」「旧系列 A …`trees/e2e` (HEAD `b815183af`)」 |
  | 同 `:35,96` | `3205dd93e` | 経緯の記述 (commit 名指し) | 「final (main = `3205dd93e`)」 |
  | 同 `:55-63` | 値 (5 rep・中央値・abort 率) | (参考) 数値の転記先 | 「stock (bootstrap campaign) 31833 | 1,355,352 | 1,355,352・1,367,130・…」 |
  | `<insight>/2026-09-27/t2865-silo-policy-iter2/{mutation/final-results.json (13 行)・mutation/probe-results.json (13 行)・verbatim/s2-plan.md (21)・s3-consult-A/B.md (8)・s6-review-*.md}` | `dev-wave-t2865-iter2/…` の path | 経緯の記述 (plan・相談・変異記録に含まれる path) | — |
  | `<insight>/2026-09-27/t2865-silo-policy-stage-f/README.md:43` | `trees/e2e` (HEAD `b815183af`)、保全先 | 固定 checkout・原本の所在 | 「submit checkout: job dir の `trees/e2e` (HEAD `b815183af`…)。保全先は repo 外の `izanagi-repro-archive/t2865-stage-f-20260927/`」 |
  | `<insight>/2026-09-27/t2865-silo-policy-stage-f/{mutation/*.json (計 71 行)・verbatim/s6-focus-1.md (18)・s6-review-*.md}` | `dev-wave-t2865-stage-f/…` の path | 経緯の記述 | — |
  | `<insight>/2026-09-27/t2853-repro-rest/README.md:46,62,67` | `trees/e2e` の未追跡 campaign 原本 | 原本の所在 (写し済みの記録) | 「[T-2865] 段階 F …と、checkout `trees/e2e` の未追跡 campaign 原本」 |
  | `<insight>/2026-09-29/t2865-silo-policy-series-c/README.md:4,6,29` | `trees/c` (HEAD `1887f56e4`)、job dir `dev-wave-t2865-series-c/` の親専用 script・`evidence/<attempt>/`、trace 保全先 `t2865-series-c-20260929/` | 固定 checkout・原本の所在・再現手順 | 「submit checkout `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/trees/c` (HEAD `1887f56e4`、CCBench `6810666`…locked)」「親専用の運用 script と job の evidence は repo 外 …」 |
  | 同 `verbatim/{s1-brief.md,s3-consult-prompt.md (6),s7-focus-1.md (5),s7-focus-2.md (5),llm/auditor-prompt-{2,3,4}.md (各 4)}` | `trees/c` 等の path | 経緯の記述 (prompt・review の引用) | — |
  | `docs/archive/worklog-phase3-0927-1902.md:8` | `trees/b`、HEAD `3205dd93e` | 経緯の記述・原本の所在 | 「系列 B (submit checkout `…/dev-wave-t2865-iter2/trees/b`、HEAD `3205dd93e`)」 |
  | `docs/archive/worklog-phase3-0927-1894-1895.md:130` | 段階 F の path | 経緯の記述 | 「[T-2865] silo-function-policy 軸を段階 F へ進め…」 |
  | `docs/archive/worklog-phase3-0929-1923.md:1,11,112` | `trees/c` (HEAD `1887f56e4`) | 経緯の記述・**次の一手 (持ち越し)** | 下記 (b) の検討を参照 |
  | `docs/spool/FOLDED.md:5504,5505` | fragment の allocation | 経緯の記述 | — |
  | `<insight>/2026-09-29/gen-opt-evolution-design/README.md:5(wave 起点として `1887f56e4`)` | commit のみ | 経緯の記述 | 「起点 local main `1887f56e4`」 |
- 研究での使用判定:
  - **系列 B (`b`)・段階 F (`e2e`): 不要。** (a) paper-story は insight を引くのみ (`docs/paper-story/2026-09-29.md:4407` 「一次資料: `t2865-silo-policy-iter2/README.md`、`t2871…§5`、D2274、D2281」)。値 (5 rep 中央値・abort 率・stock 比 3.19、段階 F 2.80) は `<insight>/2026-09-27/t2865-silo-policy-iter2/README.md:49-63` と stage-f README に転記済みで、**論文の主張には使わない旨も明記** (「1 回の観測・1 候補であり、性能主張ではない」:63)。`e2e` の原本は archive 写し済み。(b)(c) 該当なし。
  - **系列 C (`c`、16〜21 時間前): 不要 (継続使用の予定は無い)。** 根拠を分けて示す。
    1. (b) 次の一手: worklog 末尾 2 件 (1953・1954) の [T-2865] は「(番号) だけの持ち越し」(`docs/worklog.md:1768` = (1953) 群、`:1620`(1952) 群など) で、実体は `docs/archive/worklog-phase3-0929-1923.md:112` の項: 「次は iteration 2〜4 の候補の R2 再測定 (runbook §3.1) で並びの再現を確かめるか、新しい系列で iteration を重ねる」。**この 2 択はどちらも `trees/c` を入力に取らない。** R2 の入力は proposal file `{coder, auditor}` であり (`docs/phase3-silo-policy-runbook.md:188-196`「入力は (e) の proposal file … そのもの」)、series-c の 3 候補の proposal は repo 内に転記済み (`<insight>/2026-09-29/t2865-silo-policy-series-c/verbatim/llm/prop-{2,3,4}.json`・`auditor-output-{2,3,4}.json`・`coder-{1..4}.raw.json`・`preview-{1..4}.json`・`record-reject-1.json`)。新しい系列は runbook §3 が「新しい submit checkout を作り新しい系列として回す」「止まった系列を後から続けることはできない」と定める (`docs/phase3-silo-policy-runbook.md:162-186`) ため、`trees/c` の再利用は前提にならない。`docs/phase3.md` に T-2865・T-2871 の現行タスク項は無い (grep 0 件。phase3.md:76 は [T-2871] を「経路の到達」としてのみ言及)。
    2. (a) 数値: series-c の値 (bootstrap stock 1,368,676、候補 2,988,984/2,556,839/3,614,547、同 job stock 1,376,465/1,371,220/1,368,428、比 2.17/1.86/2.64、5 rep 全値、abort 率、Elapse) は `<insight>/2026-09-29/t2865-silo-policy-series-c/README.md:2.4 表` に転記済み。論文ストーリーの版 (`2026-09-29.md`) は series-c より前 (起点 `1887f56e4`) で series-c の値を使っておらず、README も「性能主張ではない」。
    3. R2 を将来やる場合に tree 内の campaign が要るか: R2 は別 campaign (`evaluation_purpose=r2`) で新しく評価し「元の判定の再確認ではない」(runbook §3.1)。**元の campaign 原本は入力にならない。**
    4. (c): series-c を入力に取る事前登録は無い (`docs/silo-policy-generator-contrast-preregistration.md` は arm 設計で、grep に `series-c`・`trees/c` なし)。
  - 留保 (系列 C): `<insight>/2026-09-29/t2865-silo-policy-series-c/README.md` は「同じ候補の再測定が無いので候補間の差として読めない」と結論するので、**将来 R2 で並びの再現を確かめる場合に、R2 の結果と比べるための「元の 5 rep の生値」が要る**が、それも README §2.4 に全値が転記済み。WAL の各 slot の時刻 (性能構成の検査 5 本の所要など) は gen-opt が使ったのは系列 C でなく系列 live (系列 7)。
- consumer: なし (path・SHA は `tools`・`orchestrator` に 0 件)。ただし **運用上の依存**: `trees/c` の `output/env/pegasus/claims/*.claim` は「計測 identity ごとに一度きり」(runbook §3)。`c` を撤去しても他 checkout の claim には影響しない (claim は checkout ごと)。`c` を残したまま同じ計測 identity を再使用すると `ClaimError` になるが、これは撤去の理由でなく残す場合の注意。
- 回収するなら写すべき中身: 不要 (`b`・`e2e` は insight 転記済み+`e2e` は archive 済み、`c` は insight に proposal・値・ログ転記済み)。仮に「16〜21 時間前で念のため」残すなら、`c` の `output/exploration/campaigns/…-877344a7/{loop_state.json,policy_history.jsonl,silo_policy_loop_digest.txt}` と各計測 campaign の WAL (`runs/wal.jsonl`) と `output/env/pegasus/claims/*.claim` だけで、合計は小さい (未計測)。
- 不確実な点: (i) 系列 C の campaign 原本は archive 未写しで、series-c 以外の新しい wave (この session と並行する他 wave) が `trees/c` を読んでいないかは repo からは分からない (`ListAgents`/handoff 相当は本調査の範囲外。`docs/handoff/` は読んだ範囲で本系列を名指ししない)。(ii) worklog (1953)(1954) の [T-2865] 番号行の全文は archive にあり、`docs/archive/` の最新の [T-2865] 全文項は 1923 と読んだが、1924〜1942 の archive に別の [T-2865] 全文項が無いことは `grep -ln '^- \[T-2865\] \*\*'` (1902・1912・1923 の 3 件のみ) で確認した。

### 系列 7: T-2871 policy-loop-iter (trees/live)
- worktree / branch / HEAD: `job/dev-wave-t2871-policy-loop-iter/trees/live` (gitdir 名 `live`) HEAD `d7161a2a13c9638af326f2062a14fc4c03e14475` (実装 tip の fix-4、main の祖先)。detached、branch は現存 `worktree-dev-wave-t2871-policy-loop-iter` の有無は未確認 (`git branch --list '*t2871*'` は 0 件)。
- 中身: `output/exploration/campaigns/` に `…-877344a7` (loop、`loop_state.json`・`policy_history.jsonl`・`silo_policy_loop_digest.txt`・`runs`)・`…-4e8009c5` (計測 campaign 2、iteration 2)・`…-c4efe427` (iteration 1) の 3 本。未追跡、archive 未写し (trace のみ `izanagi-repro-archive/t2871-liveness-20260929/` に別途)。job dir 側に `evidence/{live-pair-1,live-pair-2}`・`proposals/`・`liveness-chain.log` 等。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `<insight>/2026-09-29/t2871-policy-loop-iter/README.md:64` | `trees/live` (HEAD `d7161a2a1`) | 固定 checkout・原本の所在 | 「submit checkout `/work/…/dev-wave-t2871-policy-loop-iter/trees/live` (HEAD `d7161a2a1`、骨格 patch SHA-256 `9cb54552…`、locked)」 |
  | 同 `:4,5,32,58` ほか | `d7161a2a1` | 経緯の記述 (commit) | 「fix-4: 代役を評価ごとの模擬 pipeline…」「source は wave tip の独立 clone (`d7161a2a1`)」 |
  | 同 `:69-72,77` | 生死確認 2 job の値・trace 保全先 | (参考) 数値の転記先 | 「`33730.nqsv` … 候補 `145e3d73315a` certified、中央値 4,396,363 txn/s…」 |
  | `<insight>/2026-09-29/t2871-policy-loop-iter/verbatim/codex-*.md` (計 80 行)・`s6-ruling-*.md`・`mutation/*.json` | `dev-wave-t2871-policy-loop-iter/…` の path・`d7161a2a1` | 経緯の記述 | — |
  | `<insight>/2026-09-29/gen-opt-evolution-design/README.md:43` | `trees/live/output/exploration/campaigns/p3-silo-policy-loop-silo-policy-autonomous-{c4efe427,4e8009c5}/runs/wal.jsonl` | **原本の所在 (数値の出所)** | 「pair の内訳は生死確認系列の WAL (…`trees/live/…/runs/wal.jsonl`) の各行の `ts` の差から親が読んだ (§6.1)」 |
  | `<insight>/2026-09-29/t2867-silo-policy-contrast-impl/verbatim/codex-{consult-a,plan}.md` | `t2871-policy-loop-iter/trees/live` の path (相談・plan の引用) | 経緯の記述 | — |
  | `docs/archive/worklog-phase3-0929-1912.md:1,8,13,116,128` | `d7161a2a1`・生死確認系列 | 経緯の記述・持ち越し (T-2865 の 1912 版の項: 「Pegasus で 2 iteration 目以降を回せる状態になった → 次は研究系列を複数 iteration 回す」) | 「新しい submit checkout (`d7161a2a1`) で t2865 の proposal 2 本を `33730.nqsv` …」 |
  | `docs/decisions.md:73483`、`docs/failures.md:22246,28647`、`docs/pegasus-runbook.md:1831`、`docs/phase3-silo-policy-runbook.md:121` | insight `t2871-policy-loop-iter/README.md` (§3・§5) | 経緯の記述 (insight 名指し) | 「記録は `output/insights/2026-09-29/t2871-policy-loop-iter/README.md`」 |
- 研究での使用判定: **不要** (tree について、ただし 1 点だけ留保)。
  - (a): 論文ストーリーは insight を引くのみ (`docs/paper-story/2026-09-29.md:4003-4005` 「生死確認は研究系列ではなく、値は系列 A・B と合算しない」)。値は `<insight>/2026-09-29/t2871-policy-loop-iter/README.md:69-72` に転記済み。
  - (b): worklog 末尾 2 件 (1953・1954) に [T-2871] の次の一手なし (`grep T-2871 docs/worklog.md` は :76 (完了項の言及) と :1073 (焦点走の非帰属赤) のみ)。`docs/phase3.md:76` は「[T-2871] の複数 iteration 化は経路の到達」と書くだけで path・ref を入力にしない。後続 T-2881 (予算の数え方) は `docs/archive/worklog-phase3-0929-1912.md:128` 起票の項で、`trees/live` を入力に取らない。
  - (c): 該当なし。
  - **留保 (数値の出所の生データ):** 上表 `gen-opt-evolution-design/README.md:43` が名指す 2 本の `runs/wal.jsonl` は、README §6.1 の**新事実**「方策 pair の候補 1 本の評価 434〜491 秒のうち約 9 割 (88〜90%) が性能構成の検査 5 本 (直列、各 74〜89 秒)」の生データ (README 冒頭 :16 と :208 が「(§6.1)」として前提に使う)。派生値 (434〜491・88〜90%・74〜89) は repo 内 README に書かれているので **規則上は「不要」** だが、この派生値は gen-opt の設計 (「予備評価はほとんど安くならない」:208) の前提であり、他所 (`docs/worklog.md` の gen-opt 系エントリ) にも波及しうる。WAL は 2 本で小さい (数百行規模と推定、未計測) ので、撤去前に `evidence/` 側へ 2 file だけ複製する選択肢がある — 判断は依頼元へ。
- consumer: なし。
- 回収するなら写すべき中身 (要否は上の留保): `dev-wave-jobs/dev-wave-t2871-policy-loop-iter/trees/live/output/exploration/campaigns/p3-silo-policy-loop-silo-policy-autonomous-c4efe427/runs/wal.jsonl` と `…-4e8009c5/runs/wal.jsonl`。
- 不確実な点: 上記 WAL の行数・大きさは未計測 (tree 全体の find を避けた)。t2871 の wave branch が現存しているかは未確認 (`git branch --list` に 0 件だったが、別 worktree で checkout 中なら見えるはずで、見えなかった)。

### 系列 8: T-2868 mocc-g2-cause (tmp/t2868-mocc-g2-20260927/trees/sb1〜sb4 と `t2868-probe-author` worktree・branch)
- worktree / branch / HEAD:
  - `/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/trees/sb{1,2,3,4}` (gitdir 名 `sb1`〜`sb4`) HEAD すべて `339d7c18831176d431e1f634621aa06d940ddd70` (main の祖先、論文ストーリー版の起点でもある commit)。detached。
  - worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2868-probe-author`、branch `t2868-probe-author` 先端 `d86ec8f4842065802226ecaa3ff285c3611d257b` (base `339d7c188`、**main の祖先ではない** = `git merge-base --is-ancestor d86ec8f48 main` が rc=1)。コミット題は `[T-2638] 起動器/待ち手の終端契約 (D2044 項 16): 実装子の作業木残差を記録` (中身と題が食い違う。差分は 1 file `t2868_probe/t2868_recheck.py` 465 行の追加 (`git diff --stat main...t2868-probe-author`)。worklog 記述 (`docs/archive/worklog-phase3-0927-1905.md:11` 「probe 465 行、branch `t2868-probe-author` `d86ec8f48`、land しない」) と行数は一致)。
- 中身: `sb1`〜`sb4`: `output/exploration/campaigns/` に段階 B の p3-s4-loop 計 16 本 (`8fbbe1d5`・`b76a41da`・`df70bfb6`・`79922deb`・`070e66b3`・`37580c0d`・`dff8128b`・`28361e07`・`cda942b3`・`0720fbab`・`45916435`・`996a8735`・`e82a4f9b`・`5d4feb10`・`df2b3009`・`746f971e`。名は insight の表 (README :62-72 相当) と一致)。未追跡、archive 未写し。trace は別に `izanagi-repro-archive/t2868-mocc-stock-20260927/` (35 GB)。job dir 側 (`tmp/t2868-mocc-g2-20260927/`) に `probe/t2868_recheck.py` (sha256 は branch の blob と一致: `ca989f99…112a82`)・`recheck-output/`・`stageB/`・cases 等。`t2868-probe-author` worktree は clean 想定の checkout (`t2868_probe/t2868_recheck.py` のみが差分)。
- 名指し表:
  | file:line | 名指し対象 | 目的分類 | 抜粋 |
  |---|---|---|---|
  | `<insight>/2026-09-27/t2868-mocc-g2-cause/README.md:8` | branch `t2868-probe-author` (`d86ec8f48`)、probe sha256 `ca989f99…` | 原本の所在 (probe の repo 側の唯一の保存先) | 「再検査の probe (`t2868_recheck.py`…) は repo に入れず、branch `t2868-probe-author` (commit `d86ec8f48`) と job dir に置いた」 |
  | 同 `:9` | job dir `/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/`、trace 保全 `t2868-mocc-stock-20260927/` (35 GB) | 原本の所在 | 「job dir (repo 外、probe・投入 script・件ごとの全出力・submit 木): …」 |
  | 同 `:35` | `recheck-output/`・`recheck-output.sha256` | 原本の所在 (件ごとの全出力、各 23〜48 MB) | 「件ごとの全出力は job dir `recheck-output/`」 |
  | 同 `:60-72` | 段階 B の campaign 名 16 個・cohort `t2868-mocc-stock-v1`、submit 木は `339d7c188` | 経緯の記述 (結果の表) | 「cohort `t2868-mocc-stock-v1`、block 1〜4、submit 木は `339d7c188`」 |
  | `<insight>/2026-09-27/t2868-mocc-g2-cause/verbatim/s1-brief.md` (2)・`s3-parent-facts.md` (1)・`s6-review.md` (7) | `tmp/t2868-mocc-g2-20260927/`・probe | 経緯の記述 | — |
  | `docs/archive/worklog-phase3-0927-1905.md:11,12` | branch・unit 木 `.claude/worktrees/t2868-probe-author`、job dir の submit 木 4 本 | 経緯の記述・残置物の記録 (掃除の対象と明記) | 「残置物 (掃除の対象): unit 木 `.claude/worktrees/t2868-probe-author` (未統合の probe branch なので remove-child は rc=20 の見込み)、job dir の submit 木 4 本」 |
  | `docs/spool/FOLDED.md:5462` | 割当 `T:mocc-readheavy-anomaly-cause` | 経緯の記述 | — |
  | `<insight>/2026-09-29/t2872-mocc-g2-split/README.md:7,10,26,55,71` | t2868 の insight と値 (G2 3/109 等)、保全 inventory の argv | 経緯の記述 (insight 名指し・値の参照。tree・branch は名指しせず) | 「t2868 の harness 走 (同 pin・同 argv・同 cell、probe 無し) の 3/7…」 |
  | `docs/decisions.md:73366`、`docs/paper-story/2026-09-29.md:4331` | insight `t2868-mocc-g2-cause/README.md` §0・§3・§4・§6 | 経緯の記述 (insight 名指し) | 「(一次資料: `…/t2868-mocc-g2-cause/README.md` §0・§3・§6、D2236、D2248、D2261、D2277 項 2)」 |
- 研究での使用判定: **不要** (sb1〜sb4)。**probe (branch `t2868-probe-author`) は tool の保存で、研究データではないが、repo 側の唯一の保存先** (job dir 側にも同一 bytes がある)。
  - (a): 論文ストーリーは insight §0・§3・§6 を引く (`docs/paper-story/2026-09-29.md:4331`)。段階 A の再検査 6 件 (verifier の再実行で全件 rc=1・witness が digest と一致) と段階 B の 16 slot の結果は `<insight>/2026-09-27/t2868-mocc-g2-cause/README.md` と `verbatim/{stageA-recheck-compact.json, stageA-summary.md, stageB-recheck-compact.json, stageB-recheck-summary.md}` に派生済み。sb1〜sb4 内の campaign は原本 (provenance)。read-heavy の G2 の原因未確定は T-2872 (9/29) の insight (`t2872-mocc-g2-split`) が別の probe と別 archive (`t2872-mocc-g2-split-20260929/`) で扱い、sb1〜sb4 を入力に取らない。
  - (b)(c): 該当なし。
  - `t2868-probe-author`: probe (465 行) は repo に入れない裁定 (README :8、memory `probe-must-not-enter-repo-without-codex-author`)。job dir の写し (`tmp/t2868-mocc-g2-20260927/probe/t2868_recheck.py`、sha256 一致を確認) が残る限り、branch を削除しても再現可能。ただし job dir は **`/work/1/SFC/tanab/tmp/` (使い捨て領域の可能性、F1034 が使い捨て領域の撤去を扱う)** にあり、そこが撤去されると probe の保存先が消える。
- consumer: なし。
- 回収するなら写すべき中身: (不要 — sb1〜sb4)。branch を消す前に、probe の写しを撤去されない場所 (例 `izanagi-repro-archive/t2868-mocc-stock-20260927/` の隣) に置く選択肢を依頼元が判断する。bundle 退避は memory `clean-up-own-worktrees-and-branches` の方針 (bundle 退避 → branch -D) に沿う。
- 不確実な点: (i) branch のコミット題 (`[T-2638] …`) と中身 (T-2868 の probe) の食い違いの理由は未調査 (規律 6 の「説明と中身が食い違うもの」に当たるが、本調査は read-only で、差分 1 file が README の記述と一致することのみ確認)。(ii) `t2868-probe-author` worktree に未コミット変更があるか (`git status` は他 path のため実行不可)。ls では `t2868_probe/t2868_recheck.py` 以外は通常の checkout に見える。

---

## 1 行要約表

| 系列 | 判定 | 主根拠 |
|---|---|---|
| 1. T-2847 verifier-capacity (submit-tree-A/B) | 不要 | (a) 数値は insight `raw/cap-*.json`+README §4〜5 に派生済み、paper-story は insight を引くだけ。consumer なし |
| 2. T-2849 mocc (submit-tree/-b) | 不要 | (a) 生死確認値は `t2849-mocc-insertion/README.md` §6 に転記済み、性能主張でない。consumer なし |
| 3. T-2849 mocc-conn (22 本) | 不要 | (a) 15 系列の値は `t2849-mocc-conn/README.md`、原本は T-2853 が archive `t2853-20260927/` に sha256 照合つきで写し済み。consumer なし |
| 4. T-2850 trace-concurrent-verify (2 本 + trial-v2 19 本) | 不要 | (a) 値は insight に派生済み、trial-v2 の原本 (18 本) は archive 写し済み。(c) addendum-3 は commit `299aa022e` 束縛で tree 非依存 (commit は main の祖先) |
| 5. T-2850 trial-run (submit-tree + vprobe) | 不要 (tree)。job dir 内の probe.json・consult-option/decision.md は別途注意 | (a) 「約 91%」は `t2850-trial-pause-cost-options/README.md` §2 に派生済み。block 1 の campaign 64 本は未写しだが provenance のみ |
| 6a. T-2865 系列 B (iter2/b)・段階 F (stage-f/e2e) | 不要 | (a) 値は insight に転記済み・性能主張でない、e2e は archive 写し済み |
| 6b. T-2865 系列 C (series-c/c、最新) | 不要 (継続使用の予定なし) | (b) 次の一手 (R2 再測定 / 新系列) は proposal file を入力に取り (runbook §3.1)、新系列は新 checkout を作る (runbook §3)。proposal・値・ログは insight に転記済み |
| 7. T-2871 policy-loop-iter (trees/live) | 不要 (ただし WAL 2 本は gen-opt README §6.1 の数値の生データ、複製を推奨候補) | (a) 値は insight に転記済み。(b) 次の一手に入力としての名指しなし。留保 = `gen-opt-evolution-design/README.md:43` |
| 8. T-2868 sb1〜sb4 と t2868-probe-author | sb1〜sb4 は不要。branch は main 未統合 (probe の repo 側唯一の保存先) | (a) 段階 B の値は `t2868-mocc-g2-cause/README.md`+verbatim に転記済み。probe は job dir の `tmp/` に同一 bytes があるが使い捨て領域の可能性 |
