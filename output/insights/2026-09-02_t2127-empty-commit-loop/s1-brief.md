# [T-2127] 段 1 brief — 証拠なし certified view を閉じる

wave: `dev-wave-t2127-empty-commit-loop` / branch `worktree-dev-wave-t2127-empty-commit-loop`
base local main: `28ebff456b9f57a927854950b5030fa77aec6529`
起票の正本: `docs/archive/worklog-phase3-0901-1130.md` の [T-2127] 項
背景: `output/insights/2026-09-01_t2060-current-closure-unknown`
Codex author = D95。

## 欠陥 (実測で確定)

`orchestrator/campaign/artifact_admission.py` の `_require_admitted_campaign` は、
`CERTIFIED_ACCEPTANCE` のとき WAL record を走査して `stage == STAGE_COMMIT` の record だけに
`require_persisted_certified_commit` を当てる。**commit record が 0 件だと loop 本体が一度も
実行されず、証拠検査を 1 度も通さないまま `CertifiedCampaignView` が発行される。**

生死実験 (`DW-G01`): v2 authority を持つ campaign から commit record を全削除しても
`CERTIFIED_ACCEPTANCE` は成功し `CertifiedCampaignView records=3 commit=0` を返した。

## 親の実測 (前提の裏取り)

1. **保存済み成果物では現在未発火。** `output/campaigns/*/runs/wal.jsonl` 30 件のうち
   commit record 0 件は 2 件 (`backoff-sweep-silo-read-heavy-sweep-8ff95955`、
   `p3-s4-red-s4-red-consumer-9a1897c4`)。両者とも `CERTIFIED_ACCEPTANCE` は上流の epoch gate が
   先に拒否する (`CampaignVerifierEpochRejected: state=E0 reason=v1-authority-absent`)。
   → 本 wave で既存 certified 成果物の値は変わらない。変わるのは**将来 v2 campaign が
   commit 0 件で certified 経路へ入ったときの受理/拒否**である (`DW-G05`)。
2. **「既存テストもこの受理を要求している」は本当。** 受理集合を等価に縮小する probe
   (`_require_admitted_campaign` を包み、certified かつ commit 0 件だけを拒否) を当てると、
   baseline 全緑の consumer テストが **126 node 赤**になった。
   - `test_artifact_admission.py` 1 (`test_persisted_commit_gate_accepts[no-commit-campaign]`)
   - `test_autonomous_trial_completeness.py` + `test_backoff_consumers.py` + `test_critic.py` 36
     (baseline 411 passed)
   - `test_p3_autonomous_workload_trial.py` + `test_p3_b4_closed_critic.py`
     + `test_p3_s4_loop.py` 82 (baseline 664 passed)
   - `test_p3_s4_loop_sort.py` + `test_p3_s4_loop_trigger_gating.py`
     + `test_s1_9pair_figure_provenance.py` 7 (baseline 190 passed)
   - `test_s6_sort_sweep.py` + `test_s8a_trigger_sweep.py` + `test_bench_first_real_wal.py` 0
   赤の中身は「全試行が abort した campaign の棄却を報告する」正当な経路である。
   → **「admission で commit 1 件以上を必須にする」直し方は誤り。**

   **この 126 という数の射程 (親自身による限定):** これは「admission で一律拒否」案に対する
   測定であって、下の (P1) が提案する案に対する測定ではない。(P1) は admission を素通しにし
   主張を作る consumer 側でだけ非ゼロを要求するので、**壊れる node 数は 126 より小さいはずである。**
   126 は「一律案の被害の上界」としてだけ使う。(P1) 案の実際の影響は段 5 の実装後に測る。
3. **consumer 在庫** (`.claude/worktrees` を除外、`grep -rl` で file 数として再測定)。
   **初回の記載は出現行数を file 数と取り違えていた。段 2 子の指摘を受けて測り直した値が正本:**
   - `CERTIFIED_ACCEPTANCE` を名前で参照する production file: **20** (初回記載の 22 は誤り)。
   - `require_persisted_certified_commit` を呼ぶ production file: **9**
     (外部 8 + 定義元 `artifact_admission.py`。初回記載の 10 は誤り)。
     外部 8 は `s6_sort_sweep`、`backoff_requested_us`、`backoff_repro`、`s8b_oracle_report`、
     `paper_story_a2_certification`、`s1_report`、`p3_s4_loop`、`s8a_trigger_sweep`。
   - **両入口の和集合 = 22 file。** 差分の 2 件は `backoff_repro.py` と
     `paper_story_a2_certification.py` で、`CERTIFIED_ACCEPTANCE` を名前で参照せず
     helper だけを呼ぶ。**名前 grep を 1 本だけ引くと落ちる型である。**
   - test file: `CERTIFIED_ACCEPTANCE` 13、helper 3 (3 は 13 の内数)。
   - この 22 は名前検索の和集合であって権威ある閉包ではない。別名束縛・再 export・
     view の中継受け渡しは段 3 レンズ B に探させる。

   **親が exact 述語まで辿った 7 件 (段 2 子の照合表と突き合わせる用)。いずれも
   commit 0 件を自前で処理しており、誤った certified 主張は出さない:**
   - `s6_sort_sweep.py:541` — `certified = commit is not None` を variant ごとに判定。
     0 件なら全行 `certified: False`。
   - `s1_report.py:338-345` — `len(commits) != 1` を明示拒否 (理由 `certified_commit_missing`)。
   - `layer3_report.py:634-637` — commit の無い variant を `commit-event-absent` で棄却側へ。
   - `critic/digest.py:701-746` (`load_workload`) — commit のある variant だけを返す。0 件なら空。
   - `backoff_sweep_report.py:65,77-79` — `load_workload` が空なら `静的点が無い → skip`。
   - `p3_s4_red.py:231-234` — 棄却の読み出しにだけ使う。
   - `autonomous_trial_completeness.py:4916-4926` — **負例側の制御**。failure campaign は
     `CERTIFIED_ACCEPTANCE` で**拒否されなければならない**。拒否されれば `continue`、
     admission が通れば `failure campaign remains independently admitted` で落とす。

   → **admission 層で commit 0 件を拒否すると、この負例制御が abort-only campaign に対して
   恒真になる** (常に `continue` へ落ち、意図した gate を一度も通らなくなる)。
   受理集合を縮めたつもりが正しさ検査を 1 本殺す。(P1) を支持する最も強い根拠である。
4. **依頼文の前提が 1 つ食い違う。** 依頼は「対象は `artifact_admission.py` と
   `certified_writer_*` 周辺」と書くが、`orchestrator/campaign/certified_writer_admission.py`
   (415 行) と `orchestrator/campaign/certified_writer_preflight.py` (196 行) は
   `artifact_admission`・`CertifiedCampaignView`・`CERTIFIED_ACCEPTANCE`・`STAGE_COMMIT` の
   **いずれも参照していない** (全文検索で 0 件)。これらは compute/calibration/floor/t126 提出の
   writer 受入であり、campaign admission とは別の関心事である。
   → **本 wave の編集面から `certified_writer_*` を外す。** 段 4 で再裁定する。

5. **pin 閉包 (`DW-O09`)**: `artifact_admission.py` は `CONTRACT_LOADER_RELATIVE_PATHS` の
   exact 24 path の 1 つであり、`p3_b4_closed_critic.projection_closure_manifest` の
   projection closure にも入る。ただし `docs/phase3-b4-reflux-ablation-preregistration.md` の
   `expected_closed_critic_projection_closure_sha256[*]` 欄は**未記入**で、
   埋まった hash pin は無い。編集を止める凍結 pin は無い。
   `orchestrator/tests/acceptance_duration_ledger.json` は
   `test_persisted_commit_gate_accepts[no-commit-campaign]` を node 名で登録している。
6. **HEAD blob 束縛**: 同 file は contract-loader 束縛のため、未 commit のままでは certified 経路の
   焦点走が contract-loader-drift で赤くなる。実装の回帰ではない。段 6 の焦点走前に commit する。

## scope

**含む** — 証拠なし certified view の閉鎖に必要な最小:

- `_require_admitted_campaign` の commit 走査を D1246 の**共通 admission helper 1 本**へ寄せ、
  そこが検査を通した commit record の**件数を確定値として返す**。
- `CertifiedCampaignView` が「certified 証拠を何件検査したか」を持ち、0 件を偽装できないようにする。
- **commit 由来の certified 主張を作る consumer** が、その件数の非ゼロを明示的に要求する経路を
  1 本用意し、既存 consumer を**全数照合**して要否を決める。照合は名前 grep でなく
  各 consumer の exact 述語まで見る。
- 上記に必要なテスト。既存の受理を変える node は、変えた理由を assertion 本文に持たせる。

**含まない** (scope 外、`DW-G05`):

- 仮想リスク向けの gate・検査・台帳・一般化の新設。
- `CampaignVerifierEpoch`、epoch gate、overlay ledger、certified token 発行、exact 型拒否の変更。
- 「棄却を報告する」consumer を certified 経路から追い出す再分類 (D1245 が未裁定として
  裁定パッケージへ送った論点。本 wave では触らない)。
- 126 赤の consumer 群を一括で受理集合外にすること。

## 親の provisional 裁定 (段 3 の攻撃対象)

- **(P1)** 正しい閉じ方は「admission で commit 0 件を一律拒否」ではなく、
  **証拠件数を view に持たせ、certified 主張を作る consumer だけが非ゼロを要求する**である。
  根拠は実測 2 (126 赤が正当な棄却報告経路)。
- **(P2)** D1246 の「共通 admission helper」とは `require_persisted_certified_commit` そのものでなく、
  **それを呼ぶ loop を 1 本に閉じ込めた入口**である。取り残しは loop 側にあり helper 側ではない。
- **(P3)** 「commit 由来の certified 主張を作る consumer」の判定は、
  `require_persisted_certified_commit` を呼ぶ production 10 file を出発点にするが、
  それが必要十分とは限らない。`CertifiedCampaignView` を受けて commit record を読む
  consumer は全数見る。
- **(P4)** 既存テスト `test_persisted_commit_gate_accepts[no-commit-campaign]` は、
  現行仕様の pin である。これを削除するのではなく、
  「admission は通るが certified 証拠要求は通らない」の 2 命題へ**分ける**。
  `acceptance_duration_ledger.json` の node 名整合も同じ commit で見る。

## 不変条件

- 規律 2 を緩めない。anomaly 検出 variant の即 reject は不変。
- 受理集合を**広げない**。本 wave の変更で今まで拒否されていた入力が通ってはならない。
- 既存の epoch gate・overlay ledger・token 発行の受理集合を変えない。
- 保存済み campaign 成果物の bytes を変えない。
- 絶対規律 7: 過去の測定・判定を遡って無効化しない。

## 成果物の形

- `orchestrator/campaign/artifact_admission.py` の変更 (共通入口 + 証拠件数 + 要求 helper)。
- 要求 helper を呼ぶ consumer の変更 (全数照合の結果で確定)。
- `orchestrator/tests/test_artifact_admission.py` ほか、受理集合の 2 命題を分ける test。
- 変異 matrix、受入全走、worklog / decisions fragment、insight。

## 分割方針

段 5 は 2 単位に分けない。共通入口・証拠件数・要求 helper・consumer 配線は
producer/consumer 契約が 1 本に繋がっており、並行 fix は契約を壊す。**単一 author 子**とする。

## 受入・実測環境

`tools/run_tests.py` の受入形。投入は `tools/dev_wave_wait.py acceptance --lease-optional`。
段 1 の probe は login node の bounded local で走った (1〜3 file 単位、最長 61 秒)。
dispatch 経路は `PYTHONPATH` を伝播しないため、repo 外 plugin を使う probe は局所実行に限る。
