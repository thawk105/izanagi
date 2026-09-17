# [T-2724] 凍結 v2 g1 の chain を main へ運ぶ wave — merge は準備できたが land せず、非 hold 5 node の受入赤を実測して再裁定へ戻す (退避 (e) は完了)

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-18
- wave: dev-wave-t2724-freeze-g1-chain-land (branch `worktree-dev-wave-t2724-freeze-g1-chain-land`)
- 起点の裁定: D2120 項 2 (a)(d)(e) (ユーザー裁定 2026-09-17)、D2098 (chain の保存形)、D2077 / D2078 (退避・再配置の順序と固定退避先)、D636 (growth hold の解除はユーザー明示専用)
- 基準: 着手直前の local main `d2ebef7a407dc6be61622ed596cf08b8b518f606`、保存 branch `freeze-g1-chain-t2724` = P `3b0b75496` (main 包含済み) → X1' `cc82edc8c9f90a9ee659c2d27f71b75b19a56490` → X2 `4d8fb93b7c8d5466e9ad91b1bc5b600a2fdd7ac8`
- 一次証拠: 同 dir `evidence/` (走査要約・焦点走の要約と失敗本文・退避前後の bundle manifest・cleanup log)。生 log は job dir (`/home/SFC/tanab/.claude/dev-wave-artifacts/t2724-freeze-g1-chain-land/`、寿命保証なし)
- 可逆正規化 (D88 / DW-S07、可視文字不変): `evidence/focus-a4-failure-rank1-excerpt.txt` (原文 = 生 log `focus-a4.log` 行 775〜816、sha256 `df74b395084a3da5010ed1ec7d4c9607ca1f09cb0bbe8b1b76053597f75067b9`、4,622 byte) と `evidence/focus-a4-summary.txt` (原文 = 同 log 行 760〜775、sha256 `291e69ac08caefe4f7dde8564c53d59c83e26c5c5e1509d915ea72ed3826cc70`、2,516 byte) は `git diff --check` 抵触のため行末の空白・tab だけを除去した (`sed 's/[ \t]*$//'`、除去後 4,608 / 2,515 byte)。復元は原文 log の該当行を再抽出する

## 0. 結論

| 項 | 状態 |
|---|---|
| (a) chain の main 取り込み | **保留 (D2120 (a) は有効・履行保留)**。merge commit `b227d0d91a64e0b12759c056b9bdcd1256efccef` (親 = main `d2ebef7a4` + X2 `4d8fb93b7`、X1'/X2 の SHA・blob 不変) を作り検証したが、その木で **hold に載っていない 5 node が production gate の正しい拒否で赤**になることを実測した (§3)。並行 wave (G 作成側) の実測を親が一次 log で検算したところ、X1' を含む木では **非 hold の赤は少なくとも 45 node (oracle_driver 40 + floor_campaign 5)** で、**production の oracle gate (runbook §2 P3 gate-check) も同じ holdout hit で refuse** する (§3.1)。land すると main の受入全走が恒久的に赤になり以後の全 wave の land が止まるため、本 wave は land しない。merge commit は branch `freeze-g1-chain-t2724-merge-prepared` として保存 (§2.3) |
| (d) growth hold の帰結の記録 | 完了 (§2.2)。hold・test・除外集合は不変 |
| (e) T-1851 の失敗 run 3 件の退避と worktree 撤去 | **退避は完了** (固定 bundle は 4 run / 11 file、既存 5 file の sha 保持)。**worktree の撤去は未完了** — `dev_wave_cleanup.py` rc=20 `wave worktree is dirty` (claims / submissions の untracked が理由)、裁定どおり迂回せず残置 (§4) |
| 再裁定 | §5 に裁定パッケージ。推奨は **上流 = production 側の整合設計 (T-080 receipt の live scan が要求する zero-hit と v2 closure の矛盾、並行 wave の 択 A) を先に裁定**し、その下流で択 1 (5 node の fixture を起動可能 base から作り直し chain 有り tree の拒否を負例に足す test 変更) を別 wave で実証してから chain を land |

本 wave が変えたもの: docs (本 insight と spool fragment) のみ。実装面 0 byte。走査除外・allowlist・growth hold・test の期待値は 1 byte も変えていない。

## 1. 本 wave が判定しないこと

- 是正案 (§5 の択 1〜4) の採否。特に 5 node の fixture 変更・hold 追加・除外拡大は、いずれも規律 2 の射程に (一部) 入る (相談 C の判定: 択 1 = c、択 2 = a、択 3 = a、択 4 = b) ため親は決めない。
- 世代導入 G の作成、承認 A / pointer X (人間 commit)。
- D2120 (a) の撤回 (択 4)。D2120 は「保存 branch のまま = 8b 再開が止まる」として却下しており、AI が恒久方針として撤回できない。
- claims / submissions (T-1851 worktree に残る untracked) の整理。

## 2. 実施したこと

### 2.1 merge の準備と検証 (06:40 JST)

- `git merge --no-ff --no-commit freeze-g1-chain-t2724` → staged は X1'/X2 由来の 7 file ちょうど (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/{journal.jsonl,launch_certificate.json,manifest.json,result.json,result.md}`、`output/s8b-freeze-budget-inputs/g1.json`、`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`)。gitlink `external/ccbench` は main と同じ `511c9538`。
- staged 7 blob の OID を X2 tree (`git ls-tree -r 4d8fb93b7`) と突き合わせ **全 7 件一致**。
- `commit -F` (integrator trailer) → `b227d0d91`。`check_ai_provenance.py --range d2ebef7a4..b227d0d91` = 3 件違反なし rc=0。
- 相談 A2 (A-1): 批准側 `s8b_ratified_freeze.py` は `rev-list --parents` で全 DAG を取り first-parent を要求しない。G は親数 1・親 == `frozen_at_head` (= X1') を要求するので、**G は merge commit の子ではなく X1' から分岐して作り、通常 merge で main へ入れる** (D2098 と同じ)。merge が挟まっても `_immutable_introductions` は壊れない。

### 2.2 (d) の実測 — 権威 CLI の三軸走査

`python3 -m orchestrator.campaign.s8b_holdout_freeze search` (`evidence/scan-summary.json`):

| 木 | rr80 hit | rr20 hit | positive control | file 数 | rc |
|---|---|---|---|---|---|
| 対照 main `d2ebef7a4` (chain 無し) | 0 | 0 | 188 | 27,691 | 0 |
| merge 済み `b227d0d91` | 4 | 4 | 189 | 27,698 | 1 |

hit 4 path (両 holdout 同一): 上記 run dir の `journal.jsonl` / `manifest.json` / `result.json` と `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`。`launch_certificate.json` / `result.md` / budget input は hit しない (相談 B-1 の静的予測と一致)。

hold 下の node が解除時に赤になる機構 (相談 B-2 / B-3、静的。解除 env `IZANAGI_RUN_GROWTH_HELD_TESTS` はユーザー明示専用 (D636) で本 wave は触っていない):

- `orchestrator/tests/test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control` — `KNOWN_CONJUNCTION_HITS = {rr80: [], rr20: []}` (:21) に対し `actual_hits == KNOWN_CONJUNCTION_HITS` (:34) が上記 4 path で不一致。
- `orchestrator/tests/test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan` — wave 集合 (s8c 対象) の hit assert (:641) ではなく、全列挙後の `_assert_search_pass(report)` (:644) が `FreezeError` を raise。
- **D2120 (d) が挙げていない第 3 の held node**: `orchestrator/tests/test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null` (hold 台帳 `growth_test_holds.py:197`、軸 commits) — 実 gate (`t080_freeze_migration.py:2490` の live scan) が `_assert_search_pass` で失敗し `holdout.unknownness_layer2` として拒否理由が増えるため、`floor-null` / `budget-null` との完全一致検査 (`test_s8b_oracle_driver.py:3466`) が赤になる。

### 2.3 保存 branch

- `freeze-g1-chain-t2724-merge-prepared` = `b227d0d91a64e0b12759c056b9bdcd1256efccef`。用途: §3 の実測対象を到達可能に保つ (規律 7: 測定時点の事実の記録)。**G の親にしない** (G の親は X1')。次 wave は `freeze-g1-chain-t2724` (X2) を当時の main へ再 merge すればよく、この branch を再利用する必要はない。削除条件: 択 1 の後続 wave が chain を land し worklog に記録した後 (branch 削除はユーザー指示時のみ)。
- wave branch は main `d2ebef7a4` へ戻し、本 insight と fragment だけを積んで land する (D2098 と同型)。

## 3. 新事実 — 非 hold 5 node が chain の hit で赤になる (相談 A-4 → 親が実測)

焦点走 `tools/run_tests.py orchestrator/tests/test_s8b_floor_campaign.py -k <5 node>` を merge 済み木 `b227d0d91` で実走 (計算ノード dispatch、request 4968.nqsv、23.73 秒、`evidence/focus-a4-summary.txt`):

```
5 failed
test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e
test_s8b_floor_campaign.py::test_public_official_preflight_accepts_versioned_protocol
test_s8b_floor_campaign.py::test_public_official_preflight_accepts_legacy_protocol
test_s8b_floor_campaign.py::test_public_official_preflight_rejects_resolved_protocol_byte_drift
test_s8b_floor_campaign.py::test_public_official_preflight_rejects_legacy_byte_drift_after_capture
```

失敗理由は 5 件共通 (`evidence/focus-a4-failure-rank1-excerpt.txt`): test が実 ROOT の committed HEAD 全体を clone し (`test_s8b_floor_campaign.py:2291` / `:15625`)、production の `clean_scan_digest` (`s8b_floor_campaign.py:5532〜5540`) が `FloorCampaignError: launch certificate: clean scan 拒否: rr80: holdout hit 4 件 …; rr20: …` を raise する。E2E と accepts 2 本はこの例外そのもの、rejects 2 本は「期待する拒否理由 (allowlist hash 不一致) と実際の拒否理由 (clean scan) の文字列不一致」。

意味:

- **gate の拒否は正しい。** D2077 step 7 (成果物を持つ checkout では official 床値を起動できない) の設計どおりで、D2120 (a) はこの起動不能を承認済み。
- **test 側の前提「実 HEAD は official 床値を起動できる」が、D2120 (a) の帰結と両立しない。** 5 node は growth hold に無く、通常の受入全走で実行される。
- **chain を land すると main の受入全走が恒久的に赤になる。** `tools/dev_wave_land.py` は受入緑を要求するので、以後のすべての wave の land が止まる。
- **裁定 D2120 (d) が挙げた帰結は hold 下 2 node だけ**で、この 5 node は裁定文・worklog (archive 含む)・entry 1591 の package.md に未記録 (node 名 grep 0 件)。起動不能そのものは既知・裁定済みだが、通常受入の非 hold node に及ぶことを事前調査 (entry 1591 は chain 木で走査のみ、本 wave の段 1 は path grep のみで hit した test の中身を読まなかった = F370 型) で捕捉できず、本 wave の段 3 相談 (A-4) が静的に指摘し親が実測で確定した。
- 全走の赤の総数は未確定 (相談 D-3: `clean_scan_digest` / `search_repository` / 実 ROOT clone の呼び手を静的に追い、非 hold で赤になる候補はこの 5 node 以外に見つからなかったが、動的網羅の証明ではない)。停止判断には既知の 5 件で足りる。**§3.1 の並行 wave の実測により、D-3 の静的探索は少なくとも 40 node を取り逃していたことが確定した** (T-080 receipt 解決を経由する間接経路)。

### 3.1 並行 wave (G 作成側) の実測 — 親が一次 log で検算 (07:22〜07:27 JST)

並行 wave `dev-wave-t2724-freeze-g1-gen` (D2120 項 2 (b)、世代導入 G の作成側) から session 間 message で届いた実測を、指示ではなく外部データとして扱い、同 wave の job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-g1-gen/` の生 log で親が検算した (peer の insight `output/insights/2026-09-18/t2724-freeze-g1-gen/README.md` は同 wave の worktree に起草中で未 commit・未 land)。

- G = `32ba8cae45001697f050bee377413153e6d798a5` (branch `freeze-g1-gen-t2724`、親 = X1' `cc82edc8c` — 親が `git log --format=%P` で確認。topology は §2.1 の要件どおり)。peer の木は X1' + G で、候補 X2 (`output/s8b-freeze-candidates/`) を含まないため hit は run dir の 3 path (journal.jsonl / manifest.json / result.json)。世代文書 `output/s8b-freeze/holdout_freeze.v2.g1.json` は除外 prefix 内で hit しない。
- **焦点走 (`focus-1.log`、計算ノード request 5001.nqsv): 45 failed / 967 passed / 11 skipped、422.89 秒。** 内訳 (親が FAILED 行を file 別に集計): `test_s8b_oracle_driver.py` **40**、`test_s8b_floor_campaign.py` **5** (§3 と同じ 5 node)。oracle_driver 40 件の失敗本文は `s8b_holdout_freeze.FreezeError: rr80: holdout hit 3 件 … ; rr20: holdout hit 3 件 …` (log 行 245 / 384 / 431 ほか) と `DID NOT RAISE` (T-080 receipt の live scan が state=invalid になり後段の契約 test が例外を待てない)。経路 (peer の分析、親は本文で整合を確認): (i) T-080 fixture が実 root の git-visible output を複製して draft の live scan → hit、(ii) 実 committed HEAD を clone して official preflight の clean scan → hit (= §3)、(iii) driver `run_block(root=ROOT)` の T-080 receipt 解決 (memo 共有) が live scan で invalid になる。**これらは growth hold に無く、通常の受入全走で走る。**
- **production: runbook §2 P3 gate-check (`p3-gate-check.log`) が rc=2**、refusals に `holdout-freeze-verify: [holdout.unknownness_layer2] FreezeError: rr80: holdout hit 3 件: [同 3 path]` が混入 (親が grep で確認)。peer の分析: `_make_gate_decision` が receipt の refusal を無条件に merge するため、**X1' を含む checkout では承認 A / pointer X を作っても oracle は refuse される**。v2 の `launch_validate` は closure の hit を期待集合にするが、T-080 の live scan は zero-hit を要求しており、production 側で矛盾している。
- 意味: chain を main に載せる前提には、test fixture の是正 (択 1) だけでなく **production の T-080 receipt live scan と v2 closure の整合設計** が要る。この設計は受理集合を変える (規律 2 の射程) ため人間裁定。peer は受入を投入せず G を branch に保全して正式停止し、裁定パッケージ (択 A = 整合設計を production 側で先に行う) を返すと述べている。
- 両 wave は旧 main `d2ebef7a4` から独立に merge している。後発の land は merge-base が 2 つになり rc=23 になりうる (先発の fold 後 main を固定 SHA で merge して再受入)。

## 4. (e) 退避と撤去

- 退避 (06:43:41 JST): main 版 `python3 -m orchestrator.campaign.s8b_floor_evacuation evacuate --repo-root <T-1851 worktree> --env-tag pegasus` (T-1851 の tip `0709a4018` に module は無いため、自 worktree の main 版 module を使用。bundle root は指定 root の git common dir から導出され、main の `.git/izanagi/s8b-floor-evacuation/pegasus/` と同一)。rc=0。
  - 退避前 (`evidence/bundle-manifest-before.json`): run 1 件 (`20260916T111925Z-2c8cf9be`、5 file)。
  - 退避後 (`evidence/evacuate-t1851-bundle-manifest.json`): run 4 件 (辞書順 `20260915T063232Z` / `074211Z` / `075821Z` / `20260916T111925Z`)、11 file。既存 5 file の sha256 は不変 (親が照合)。追加 3 run は各 `journal.jsonl` + `launch_certificate.json` のみ (result.json 無し = 最早適格 result 選定 `_official_earlier_floor_results` は skip、候補判定に影響しない — この主張は earlier-result 選定に限る)。
  - module の設計どおり、公開後に T-1851 側の `output/env/pegasus/calibration/s8b-floor-official/` (3 run dir) は除去された。
- 撤去 (06:46:24 JST): `python3 tools/dev_wave_cleanup.py --main-worktree /work/1/SFC/tanab/izanagi --wave-worktree <T-1851 worktree> --wave-branch worktree-dev-wave-t1851-c3c-official-floor --tested-wave-tip-sha 0709a4018ead6da495391674d76284fe479cf983` → **rc=20 `status=rejected phase=preflight reason=wave worktree is dirty`** (`evidence/cleanup-t1851.log.txt`)。裁定どおり迂回せず残置。
  - dirty の内訳 (親が 06:1x JST に実測、退避前): `output/claims/2026091{5T063232Z,5T074211Z,5T075821Z}-2c8cf9be.claim` 3 件、`output/env/pegasus/floor/attempts/submissions/{83ec41df…,acb88122…,d198cec4…}/` 3 dir (各約 41MB、大半は hydrate 済み第三者ソース複製 `masstree-payload/`、ほかに qsub / qstat / pegasusinfo / rbudgetcheck / check_quota の rc・stdout・stderr、`pre-submit.json`、`submit-receipt.json`、`evidence-index-status.json`)。tracked の変更は無し。
  - この untracked は D2120 (e) の名指し (journal + cert) に無く、親は整理を scope 外とした。別 checkout の holdout 走査には混入しない (走査は指定 root と ccbench に限る、相談 B-6)。T-1851 の branch tip は main 包含済み、worktree は lock (理由空)、admin 配下に hardlink 31 本 (dirty が解消しても nlink 検査で rc=20 になる見込み、memory `cleanup-rc20-admin-entry-nlink-submodule-packs`)。
  - 撤去は `/cleanup-branches` (ユーザー指示) の退避付き手順へ引き渡す。

## 5. 裁定パッケージ — D2120 項 2 (a) の履行形

**問い:** chain を main に載せると非 hold で少なくとも 45 node が正しい拒否で赤になり (§3 / §3.1)、production の oracle gate も X1' を含む checkout では refuse する (§3.1)。どの形で (a) を履行するか。

**上流 (先に裁定): production 側の整合設計。** T-080 receipt の live scan が zero-hit を要求し、v2 の closure は hit を期待集合に持つ — この矛盾は test の是正では解けず、`test_s8b_oracle_driver.py` の 40 node と P3 gate-check の refuse の共通原因である。並行 wave の裁定パッケージ (択 A: T-080 receipt live scan と v2 closure の整合を production 側で先に設計する) がこれを担う。受理集合を変える設計なので規律 2 の射程で人間裁定。**本パッケージの択 1〜4 はその下流**であり、択 1 は 5 node (floor_campaign) の是正であって oracle_driver 40 node と gate の refuse には効かない。

- **択 1 (下流の推奨): 5 node の fixture を「official 成果物を持たない起動可能な base」から作り直す test 変更を別 wave (Codex author) で実装・実証し、上流の整合設計が閉じた後に chain を land する。** production gate (`clean_scan_digest`、走査除外、allowlist、hold) は 0 byte。相談 C の必須条件: (i) fixture は committed HEAD の clone から official namespace 全体と候補の exact path だけを外す (走査 hit を見て削除対象を増やさない、候補 dir の無条件削除もしない)、(ii) 変更前後の tree 差分が宣言した削除集合だけであることを独立に検査、(iii) 既存の正例・hash drift 負例・`bypass_drift_gate` 対照を残す、(iv) **chain 有り tree の拒否を負例として同 test に足す** (official 成果物だけ / 候補だけ / 両方の 3 ケース)、(v) 変異 matrix で search 拒否を外すと負例が失敗することを確認。射程 = c (実 HEAD の検出を落とす部分が規律 2 の射程)。
  - やらない理由の最も強い形 (相談 C / D-2): 赤を見た同じ AI が入力 tree と期待値を変えれば、汚染を fixture の外へ追い出して緑を作れる — 「急いでいる主体が自分の正しさ検査を減らす」形。負例・差分検査・変異検査で抑えられなければ、production 無変更でも採用しない。
- 択 2: 5 node を growth hold 台帳へ追加 (skip)。射程 = a (D532「テストの削除・skip・selection の縮小 — 規律 2 に反する」、hold は `correctness_gate=True`)。**推奨しない。**
- 択 3: 走査の除外集合を official namespace / 候補 dir へ広げる。射程 = a (D2077 が却下、D2120 (d) も不採用)。**推奨しない。**
- 択 4: chain を main に載せず、G / A / X と批准・oracle を保存 branch 上で運用する (D2120 (a) の改訂)。射程 = b だが、D2120 が「8b 再開が止まる」として却下済みで、保存 branch 上で批准・oracle が成立するかは未確認。

**AI が裁定を待たずに進められる部分 (相談 C):** 択 1 の詳細設計と、隔離 worktree での実装 + 検出力保存の実証 (負例・差分検査・変異 matrix、chain 無し / 有り両 tree での焦点走)。**land は本裁定の後** (裁定後に別 context が段 4 から再開する型、DW-S04)。検出力削減の容認・hold / 除外の拡大・main 配置の恒久変更・T-080 live scan の受理集合の変更は先取りしない。

**やらない理由の最も強い形 (上流に対して):** 「v2 closure に含まれる hit は T-080 live scan で許容する」という整合は、走査の受理集合を広げる形になりうる。D2077 / D2120 (d) が却下した「除外の拡大」と同じ帰結にならない設計 (例: closure の exact hash 束縛だけを許容し、閉包外の hit は従来どおり zero-hit 要求) を、production 側の負例付きで示せない限り採らない。

## 6. 段 3 / 段 4 相談の要約 (全 5 本 `gpt-6-astra` / `medium` / read-only、生成物は job dir)

- A (初回): 親の射影の file 名誤り (`s8b_ratified_verify.py` → 実在は `s8b_ratified_freeze.py`) で fail-closed 停止。A2 で再投入。
- A2: A-1 topology refuted、A-2 provenance refuted (X1'/X2 の `.json` / `.jsonl` / `.md` は実装面外、integrator で可)、A-3 land 監査列は第 2 親側 2 commit を含む (rc=23 の条件)、**A-4 real must-fix (§3)**、A-5 数値は時点付きで、A-6 scope 外混入なし。
- B: B-1 chain 由来 hit = 4 path (実測と一致)、B-2 2 node の機構、**B-3 real must-fix: 第 3 の held node (§2.2)**、B-4 evacuate 整合、B-5 nit cleanup の最初の拒否は dirty tree (実測と一致)、B-6 claims / submissions は残置で他 checkout に影響なし、B-7 fragment は worklog のみで可、B-8 数値は時点付き。
- C (設計 / 射程): 択 1 = c、択 2 = a、択 3 = a、択 4 = b。推奨 択 1 (§5)。
- D (攻撃): yes 0 / partial 3 (D-2 択 1 を規律 2 違反と断定しない、D-4 起動不能は既知・非 hold 受入への波及が未提示、D-5 保存 ref と再開手順を記録) / no 3 (D-1 land 保留は正しい、D-3 追加の非 hold 赤は静的に見つからず、D-6 退避は授権内)。すべて本 insight に反映。

## 7. 実走一覧 (親、login node = 三軸走査・退避・cleanup・provenance、計算ノード = 焦点走)

| 時刻 (JST) | 操作 | 結果 |
|---|---|---|
| 06:36 | 三軸走査 (対照 main) | rc=0、hit 0 / 0 |
| 06:40 | merge `--no-ff --no-commit` → blob 照合 → `commit -F` | b227d0d91、7 blob 一致 |
| 06:41 | provenance `--range d2ebef7a4..b227d0d91` | 3 件違反なし rc=0 |
| 06:42 | 三軸走査 (merge 済み) | rc=1、hit 4 / 4 |
| 06:43 | 焦点走 5 node (request 4968.nqsv) | 5 failed / 23.73 s |
| 06:43:41 | evacuate (T-1851 → 固定 bundle) | rc=0、4 run / 11 file |
| 06:46:24 | dev_wave_cleanup (T-1851) | rc=20 dirty |
| 07:03〜07:19 | 受入全走 1 回目 (docs 木 cf8c28b7d) | rc=70、26 error = `test_t1259_qsub_env_delivery_probe.py` の setup で `git ls-files --others` / `git status` の 30 秒 timeout (F945 型、非帰属)、24,798 passed |
| 07:20〜07:41 | 受入全走 2 回目 (同) | child-green、24,824 passed / 69 skipped (受領証取得後、§3.1 の改訂のため lease を release して再受入) |
| 07:22〜07:27 | 並行 wave の log 検算 (§3.1) | 45 failed の内訳・P3 refusal・G の親を一次資料で確認 |
| land 前 | `check_docs.py`、`spool_fold.py --dry-run`、受入全走 3 回目 (改訂後の docs 木) | 結果は worklog / land の受領証 |

工数: codex 子 5 本 (consult A・A2・B・C・D)。変異 matrix は免除 (実装面差分ゼロ)。

## 8. 次 wave の出発点

1. **ユーザー裁定 (上流、§3.1 / §5)**: T-080 receipt live scan の zero-hit 要求と v2 closure の整合を production 側でどう設計するか (並行 wave `dev-wave-t2724-freeze-g1-gen` の裁定パッケージ 択 A と同じ問い。同 wave は G `32ba8cae4` を branch `freeze-g1-gen-t2724` に保全して正式停止)。
2. **ユーザー裁定 (下流、§5)**: 択 1 を採るか。採るなら「(a) 有効・履行保留」を「(a) 履行 = 上流の整合設計 land → 択 1 の test 変更 land → chain land」へ更新。
3. **AI 手番 (裁定前に着手可)**: 択 1 の設計・実装・実証 wave (Codex author、`orchestrator/tests/test_s8b_floor_campaign.py` の `_clone_committed_head_with_ccbench` :2291 と `_protocol_binding_public_preflight` :15609、負例 3 ケース、変異 matrix)。land は裁定後。上流の設計に依存する oracle_driver 40 node は本 wave の scope に入れない。
4. **chain land wave (両裁定後)**: 当時の main から fresh worktree → `git merge --no-ff freeze-g1-chain-t2724` → 三軸走査 hit 4 / 4 の再確認 → 受入全走 (45 node が緑になっていること) → land。G は X1' から分岐する別 wave (既に `freeze-g1-gen-t2724` に在る)。
5. **T-1851 worktree**: `/cleanup-branches` (ユーザー指示) で退避付き撤去。claims 3 件 + submissions 3 dir (約 123MB) が untracked のまま。
