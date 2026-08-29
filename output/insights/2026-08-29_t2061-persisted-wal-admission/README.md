# [T-2061] 保存済み実行記録の判定と受領証を共通 admission helper へ通す

D1246 の実装。基準 main `d03855e92`、wave branch `worktree-dev-wave-t2061-wal-admission`。

## 何が壊れていたか

実行中の経路 (`orchestrator/campaign/pipeline.py`) は、verifier が認証しなければ即座に中断する。
絶対規律 2 はここで守られている。しかし **保存済みの実行記録を後から読む経路には、その束縛が無かった。**

`artifact_admission._claims_certified_execution()` は v1 lock の格下げ検出専用であり、
一般の認証判定ではない。認証済みとして読み出す入口 (`_require_admitted_campaign()` の
`CERTIFIED_ACCEPTANCE` 分岐) は、記録・環境契約・source binding・epoch を検査するが、
**COMMIT に対応する verify の判定 (`certified` / `anomalies`) も、COMMIT の受領証も再検査しない。**

さらに、同じ判断が consumer ごとに重複実装されていた。`s6_sort_sweep.py` と
`s8a_trigger_sweep.py` は行単位で `certified = commit is not None` と書いていた。
これが D1246 の理由文にある「consumer ごとの重複実装は取り残しを実際に生んだ」の実体である。

出所は `output/insights/2026-08-28_t2008-d1163-closure-mismatch/verbatim/s3-lens-a.md` の A-01 / A-03。

## 何を作ったか

`orchestrator/campaign/artifact_admission.py` に小さい共通 helper
`require_persisted_certified_commit(records, commit_record, *, campaign_lock_sha256)` を 1 つ置いた。
新しい module も、新しい台帳も、新しい署名主体も、新しい受領証 schema も作っていない。
既存の受領証 validator (`orchestrator/verifier/commit_receipt.py`) を再利用している。

helper が要求するのは次の 7 つだけである。

1. COMMIT の `build_attempt_id` が非空 exact str
2. 同一 variant・同一 attempt・COMMIT より前の verify が 1 件以上
3. 各 verify の `verdict == "serializable"` かつ `certified is True`
4. `anomalies` が exact int の 0
5. `workload.tag` が非空 str
6. 既存の受領証 validator を `sink_kind="campaign-wal"`・実 lock SHA・variant・terminal payload で通す
7. 受領証の `operation_identity` が COMMIT の attempt と一致し、
   受領証の証拠列 `(workload_tag, verdict, certified)` が記録側の verify 列と完全一致する

## 採用しなかった述語と、その理由

段 2 のプランは次も要求していた。段 3 の独立検証 2 本が一致して過剰と判定し、親が削った。

`commits > 0` / `aborts >= 0` / `commit_witness` の exact 2 key・件数一致・batch 件数 0 /
`workload` の exact key 集合 / `verify_configs` の順序保持 deduplicate 一致。

いずれも D1246 が求める「判定と受領証の束縛」に不要で、実行側の診断 schema を将来にわたって
固定してしまう。特に `batch_commit_counts == 0` は、CCBench が batch commit を独立に集計して
性能値にも加える (`external/ccbench/common/result.cc:47-61`) ため、将来 batch trace を正当に
認証できるようになったときに正しい成果物を拒否する。実行側の既存 gate は一切変更していない。

## 対象とした certified consumer の全件閉包 (21 module / 30 site)

ユーザー指示に従い、識別子 key と編集面 path の両軸で全件検索した。

### A. 共通入口 `require_admitted_campaign(purpose=CERTIFIED_ACCEPTANCE)` 経由 (16 module / 22 site)

helper を入口 1 箇所へ置くだけで全部が守られる。

`critic/digest.py:1586` / `p3_b4_closed_critic.py:740,1779` /
`p3_autonomous_workload_trial.py:3088` / `s6_sort_sweep.py` / `backoff_extended_sweep_report.py:459` /
`backoff_sweep_report.py:57` / `backoff_overthrottle.py:145` / `p3_b4_wiring_probe.py:1475` /
`p3_s4_loop_sort.py:546,743` / `autonomous_trial_completeness.py:4423,4912,4959` /
`p3_s4_loop_trigger_gating.py:1088` / `p3_s4_loop.py:1240,1576,1791` / `s8a_trigger_sweep.py` /
`replay.py:184` / `layer3_report.py:685` / `p3_s4_red.py:191`

### B. lock だけを読んで記録を独自に読む経路 (3 site) — 個別に結線した

`backoff_requested_us.py` / `s1_report.py` / `s8b_oracle_report.py`

### C. 識別子検索では出ず、編集面 path 検索でだけ出た経路 (4 site) — 個別に結線した

`s6_sort_sweep.py` の `_replay_outcome()` / `s8a_trigger_sweep.py` の `_replay_outcome()` /
`backoff_repro.py` の `_bench_tps()` / `paper_story_a2_certification.py` の `_raw_cell_from_wal()`

### D. 段 6 の敵対レビューが見つけた 30 番目 — 個別に結線した

`p3_s4_loop.py` の `_resolve_duplicate()`。保存済み記録の COMMIT payload だけで whiteboard へ
「成功」を射影し、性能値と verdict を復元していた。`p3_s4_loop_sort.py` と
`p3_s4_loop_trigger_gating.py` が同じ関数を re-export しているため、共有実装 1 箇所で 3 driver に届く。

**ユーザー指示が警告したとおり、識別子 key だけの検索では C の 4 site が落ちた。**
D は段 3 の 2 本のレンズでも落ち、段 6 のレビューで初めて出た。

### 除外した実在 consumer

`tools/plotting/plot_backoff.py:269`、`tools/plotting/plot_s1_9pair.py:562`、
`critic/online_digest.py:42`、`p2_2_report.py` はいずれも歴史 (`HISTORICAL_RAW`) 専用で
認証済みだと主張しない。`plot_b10_extended_backoff.py` は凍結済み歴史 bytes の consumer である。
`verifier/commit_receipt.py:398` は exact 型検査だけで入口を呼ばない。

## 読み取り時点の同一性契約

B と C と D の 7 site では、epoch の判定・lock の SHA 取得・記録の読み取りが別々の読み取りだった。
lock bytes を 1 回取得して SHA を導き、記録を読んだ後に lock を再取得して SHA の一致を要求する形にした。
判定に使った lock と受領証が束縛する lock が別物になる窓を閉じる。

**限界:** 二度読みの SHA 比較は A→B→A の入れ替えと、二度目の読み取り以降の差し替えを検出しない。
段 6 のレビュー A がこれを指摘し、無効な受領証を受理へ変える具体的経路は確認されなかった。
保証の射程はここまでである。

## 受理集合の変化

縮む方向にだけ動く。新たに拒否されるのは次である。

- COMMIT に対応する同一 attempt の verify が無い記録
- verify の判定が非認証、または異常件数が 0 でない記録
- 受領証が欠落・不正、あるいは実 lock・variant・attempt・terminal payload に束縛されていない記録
- 受領証の証拠列が記録側の verify 列と一致しない記録

変わらないのは次である。歴史読み出し、COMMIT の無い試行、異常後に中断した赤い attempt、
中断件数が 0 でない正常な verify、既に epoch で拒否される記録。

## 実 artifact での値域の実測 (母集合と除外を明記する)

母集合は repo 内 `output/campaigns/*/runs/wal.jsonl` の全 30 campaign。除外なし。

- verify の値域: `{certified:true, anomalies:0}` が 571 件、`{certified:false, anomalies:1}` が 1 件。
  実在する負例は `output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/runs/wal.jsonl`。
- COMMIT 459 件のうち受領証を持つものは 0 件。`contract_sha256` も `build_attempt_id` も無い。
- `campaign.lock` 30 件すべてに `schema_version` が無く、全件 v1。v1 は authority が無いため
  epoch が E0 になり、認証済み読み出し自体が拒否される。

**したがって repo 内に「通る正例」は存在しない。** 段 2 が repo 外の official campaign
`b10-backoff-grid-silo-balanced-sweep-9ded73c4` に 93 verify / 93 COMMIT の正例を見つけ、
全件が認証済み・異常 0・受領証ありだった。fixture 側の正例はこれとは別に合成で組んでいる。

## 段 6 のレビューで不採用にした所見

A-2 の `_classify_verify_repetition()` にある `commit_counts > 0` と `batch_commit_counts == 0` を
外すべきという指摘があった。**現物を確認したところ基準 commit `d03855e92` に既に存在し、
本 wave の差分は触れていない。** D1246 が禁じたのは helper へその述語を実装することであって、
A-2 が元から持つ意味を変えることではない。外すと A-2 の受理集合が広がる。
**別裁定の候補として残す** — 将来 batch trace を認証できるようにするかは、
実行側と verifier 側の裁定であって本 wave の範囲ではない。

## 実装と検査

| commit | 内容 |
|---|---|
| `17f365d4f` | helper 本体と共通入口の結線、負例 6 + 正例 4 のテスト、既存 fixture 追随 |
| `62d8ef86d` | B の 3 site と C の 4 site の結線、同一性契約、凍結 pin 追随、負例 8 |
| `d4b6adeb2` | D の 30 番目の結線、旧形式記録の拒否と正例の対、例外種別の是正 |

親が実走した焦点走 (すべて `tools/run_tests.py` 経由)。

| 対象 | 結果 |
|---|---|
| `test_artifact_admission.py` | 129 passed |
| `test_bench_first_real_wal.py` + `test_s6_sort_sweep.py` + `test_s8a_trigger_sweep.py` | 74 passed |
| `test_critic.py` + source closure / import / plain-runner / spawn-site の 4 検査 | 286 passed / 6 skipped |
| `test_s1_report.py` + `test_s6_sort_sweep.py` + `test_s8a_trigger_sweep.py` + backoff 系 2 file | 137 passed |
| `test_s8b_oracle_report.py` + `test_s8b_oracle_manifest.py` + `test_paper_story_a2_certification.py` | 468 passed |
| `test_artifact_admission.py` + `test_bench_first_real_wal.py` + `test_p3_s4_loop.py` | 467 passed |

`check_ai_provenance.py` の全史監査は新規違反なし。

## 実装中に出た赤と、その帰属

- **27 件 (本 wave 帰属):** fixture が有効な `campaign.lock` を置く前に受領証つき COMMIT を
  書いていた。fixture の順序を直した。実装側は変更していない。
- **11 件 (本 wave 帰属):** 壊れた記録の後に正常な COMMIT を追記すると、受領証の書き手が
  既存行を再 parse して consumer の分類前に例外化していた。壊れた履歴を再 parse しない形へ直した。
- **20 件 (本 wave 帰属、過剰拒否):** helper を「COMMIT が 1 件ある」だけで起動していたため、
  認証対象として適格でない window・旧形式・既に別の理由で拒否済みの行にまで関門が掛かっていた。
  適格性・attempt 束縛・COMMIT の一意性・既存の指摘なしをすべて要求する形へ絞った。
- **11 件 + 18 件 + 229 件 (非帰属):** 環境要因。詳細は下記。

## 受入全走で出た赤 30 件 (本 wave 帰属、実装の回帰ではない)

1 回目の受入全走は **18868 passed / 67 skipped / 30 failed**。全件が本 wave 帰属だった。

- **29 件** (`test_autonomous_trial_completeness.py` 27、`test_trial_registry.py` 2):
  `ArtifactAdmissionError: persisted COMMIT has no preceding verify_done for its attempt`
  が共通入口の呼び出し位置から出ている。fixture が「同一 attempt の verify 記録を持たない COMMIT」を
  作っており、**新しい関門が正しく発火した**。fixture に正常な verify と受領証を足して閉じた。
- **1 件** (`test_s8b_oracle_driver.py`): `assert 'indeterminate' == 'determinate'`。
  **COMMIT の証拠不足ではない。** epoch 判定を差し替える mock の対象が旧経路のままで、
  現行の実装が呼ぶ入口には効いていなかった。実 bytes が v1 lock
  (`state=E0`、`reason_code=v1-authority-absent`、`certified_eligible=False`) と判定され、
  判定が確定に至らなかった。mock の対象を現行の入口へ付け替えて閉じた。

いずれも production を 1 行も変えずに fixture 側で閉じた。

**段 2 プラン、段 3 の 2 レンズ、段 6 の 2 レビューのいずれもこの 3 file を追随対象として
挙げていなかった。共通入口へ関門を置く変更の波及は、静的レビューだけでは尽くせない。**
受入全走が唯一これを見つけた。

## 非帰属の赤 3 種 (次の wave が踏むもの)

1. **未 commit の enforcement closure member。** `artifact_admission.py` は
   `campaign_lock.py` の exact 24 path 閉包の member であり、編集して未 commit のまま検査を走らせると
   `contract-loader-drift: disk bytes が HEAD blob と不一致` で必ず赤になる。commit すれば解消する。
2. **`/tmp/.git` の点滅生成。** 空の `.git` directory が `/tmp` に現れると
   `_has_git_ancestor()` が真になり、pytest の一時領域がすべて「リポジトリ内」と判定されて
   `official output_root は repository 外でなければならない` で落ちる。他 session のテストが
   一時的に作っては消しているもので、`rmdir` しても再生成される。
3. **一時領域の置き場所。** 対策として `TMPDIR` を移すとき、
   `/work/1/SFC/tanab/dev-wave-jobs/` の下には `.git` があるため同じ罠に落ちる。
   `.git` の祖先が無い場所 (今回は `/work/1/SFC/tanab/t2061-tmpdir`) を選ぶ必要がある。

## 変異事前登録と走行結果

`mutation-spec.json` に 15 件。負例 10 / **過剰拒否を殺す正例 4** / S8A 再開経路 1。
判定は失敗 node の完全一致 (`tools/mutation_harness.py` の `_observed_status`) なので、
二重に殺す変異を避けるよう 2 件を作り直した。登録した node id は全件 grep で実在照合済み。

### probe 走 (`mutation-probe-out.json`)

初回は期待 node を 1 件ずつ登録して走らせた。baseline PASSED。
**15 件すべてで、登録した期待 node が実際に発火した。関門は全部効いている。**

ただし consumer 結線の 5 件 (M7 / M8 / M9 / M14 / M15) が期待どおり 1 node ずつ正確に殺したのに対し、
helper 内部の 10 件は 57〜161 node を殺した。helper が共有 fixture 経由で test corpus 全体に効くためで、
関門が効いていないのではなく期待集合が不足していた。

`DW-M08` は「期待 node は完全集合」「確定できない場合に限り初回を probe と明記し erratum を残して
再登録・再走する」と定める。この初回走を probe として記録し、観測 node をそのまま完全集合にした
`mutation-spec-v2.json` を作って再走した。

### 本走 (`mutation-result.json`、spec v2、HEAD = fix 3 後の実装最終 commit)

**baseline PASSED、15/15 KILLED、期待との不一致 0。**

| 変異 | 種別 | 殺した node 数 |
|---|---|---|
| M1 異常件数 0 の検査除去 | 負例 | 62 |
| M2 受領証 validator 呼び出し除去 | 負例 | 58 |
| M3 受領証 operation 一致除去 | 負例 | 57 |
| M4 受領証証拠列の比較除去 | 負例 | 57 |
| M5 verify の attempt 束縛除去 | 負例 | 66 |
| M6 中央関門を先頭 COMMIT だけに | 負例 | 57 |
| M7 S1 の結線除去 | 負例 | 1 |
| M8 A-2 の結線除去 | 負例 | 1 |
| M9 S6 再開の結線除去 | 負例 | 1 |
| M10 全 verify を正常必須へ拡大 | **正例** | 58 |
| M11 COMMIT を必須へ拡大 | **正例** | 57 |
| M12 歴史読み出しにも関門を適用 | **正例** | 83 |
| M13 中断件数 0 へ過剰強化 | **正例** | 161 |
| M14 閉包 30 番目の結線除去 | 負例 | 1 |
| M15 S8A 再開の結線除去 | 負例 | 1 |

**consumer 結線の 5 件が 1 node ずつを正確に殺したことは、単一理由性の実証である。**
正例 4 件が殺されたことは、実装が承認された範囲を越えて受理集合を縮めていないことの実証である。
