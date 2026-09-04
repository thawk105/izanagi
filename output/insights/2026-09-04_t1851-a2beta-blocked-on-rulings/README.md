# [T-1851] 実装単位 A の後半 A2β — 子を起動する前に止めた。引数の前提 2 点を実測が覆し、残る E1 / E2 はユーザー裁定 3 件待ちである

2026-09-04。branch `worktree-dev-wave-t1851-unit-a`。**land していない (D1341)。**

- 継承 tip: `520b1ddba` (A2α まで)
- 本 wave の commit: `7771c9e65` (local main `1b7822110` の取り込み、integrator) と記録 commit
- 実装面の差分: 0 (merge 以外)。codex 子: 0 本
- 逐語: `verbatim/s1-brief.md`、`verbatim/s4-adjudication.md`、`parent-measurements.md`

## 1. 引数の前提 2 点が現物と食い違い、段 1 で止めた

引数は「次段 = E1 / E2 / E3 (必須 — 現行は v1 固定で v2 profile が 5 箇所で全拒否) / E4」と書いた。

- **E3 / E4 の構造面は A2α (`69497db66`〜`9df7105f6`) で済んでいる。** `_assert_profile()` は
  schema identity で分岐する exact validator になり、新 2 field も比較に含まれる。path の世代分岐
  11 呼出し、create-only publish、claim v3、capability 消費、v2 resume も積まれている
  (`../2026-09-03_t1851-a2alpha-generation-open/README.md`、変異 21/21 一致、受入 child-green)。
- **E1 / E2 はユーザー裁定 3 件待ちで着手できない。** A1' 段 4 が固定した 2 つの封印 terminal API の
  signature では、同じ裁定が承認した「起動層所有の生の事実から再導出し、自己申告 field は比較にだけ
  使う」を実装できない、と A2α の 3 者 (段 2 plan / レンズ A / レンズ B) が独立に結論し、A2α README
  13 節が裁定パッケージ 3 件をユーザーへ返した。`docs/decisions.md` (D1622 まで) に該当する裁定は無く、
  /rulings 第 7 回 (worklog 1260) の索引 15 件にも入っていない。補正は受理面と public API 面の
  拡大を伴い親では裁定できないため、`DW-STOP` の「ユーザー裁定待ち」で停止した。

`DW-S01` の「確認前に子を起動しない」に従い、段 2・3 の codex 子は起動していない。

## 2. 前提が古かった経路

A1' の job dir handoff (`dev-wave-jobs/2026-09-02_t1851-unit-a/handoff.md`) は A1' 終了時の
「次の一手 = A2' (E1〜E4)、E3 必須」のまま残り、同じ branch を継承した A2α wave はこれを更新して
いなかった。A2α の状態は branch 上の README と worklog fragment (未 land) にだけある。
引数は「再開手順は同 handoff 末尾」を根拠にしており、その末尾を写したと判断する。
本 wave は A1' の handoff 冒頭に「以後の正本は branch の README」の追記を施した。
failures 台帳へ 1 件 (fragment `docs/spool/failures/2026-09-04-dev-wave-t1851-unit-a-8.md`) を送った。

## 3. main 取り込み — Codex author の合成監査は発火しない

local main `1b7822110` (merge-base `36406d376` から 146 commit) を `--no-ff --no-commit` で取り込み、
`7771c9e65` として commit した。

- main 側の実装面の変更は verifier (core / model / cli)、b10 / backoff sweep とその consumer、
  p3_b4 producer auth、p3_s4_loop、layer3_report、s8b_oracle_manifest、pipeline、acceptance の
  issuer / signature、tools/pegasus の投入 script。**単位 A の編集面 4 file
  (attempt_registry_core / s8b_attempt_profile / s8b_attempt_registry / s8b_holdout_admission) と
  consumer 2 file (s8b_floor_attempt_launcher / trial_registry) に 1 file も交差しない。**
- 重なった file は `docs/dev-wave/operations.md` だけ (自動 merge、競合なし)。
- 実装面で両親のいずれとも異なる file が無いので、`docs/ai-provenance.md` の実装面契約と `DW-O17` の
  発火条件 (両親と異なる実装面) を満たさず、integrator で記録した。
- 合成の意味的健全性は焦点走と受入全走で実測した (4 節)。`external/ccbench` の gitlink は main と
  同じ `511c9538e`。

## 4. 検査の実測

`parent-measurements.md` が一次資料。

| 検査 | 結果 |
|---|---|
| `check_wave_startup.py --mode resume --external-handoff` | rc=0 |
| provenance `--message-file` 事前検査 | rc=0 |
| 全史 provenance (`check_ai_provenance.py`、計算ノード 977068.nqsv) | rc=0、8,167 件、新規違反なし |
| `check_docs.py` | rc=0 |
| `spool_fold.py --dry-run` | rc=0 |
| 焦点走 15 file (編集面 4 file の consumer 14 file を参照関係で引いた + plain_runner_coverage) | 1,720 passed / 5 skipped / rc=0 (計算ノード) |
| 受入全走 (`dev_wave_wait.py acceptance`) | attempt 4 (D612 上書き 3600/600): `child-green`、**20,469 passed / 68 skipped / rc=0**、tested_main `1b7822110`、tested_tip `7771c9e65`。attempt 3 は gen_S 混雑で shard dispatch が signal-abort (`rc=70 source_rc=16`、テスト本体は未走行) |

## 5. ユーザーへ返す裁定パッケージ (A2α 13 節の再提示。新しい選択肢は無い)

1. **E1 の境界 signature を補正してよいか。** (推奨) 起動層が生の事実を snapshot して発行する
   evidence-bound handle を第 9 の境界として追加し、resume 可能な durable evidence digest も持たせる /
   (代案 a) 2 つの sealed API へ `probe_outcome` / `throughputs` / `execution_failures` /
   `repetition_evidence` の keyword-only 引数を直接足す / (代案 b) 境界を変えず E1 を単位 C と
   同じ変更単位へ送る (D1530 の形)。併せて `record_sealed_classified_failure_terminal()` は
   呼び手 0 件であり、単位 C で呼び手を名指しできるか API を落とすかを land 前条件にする。
2. **E1 の分類 policy の権威をどこに置くか** — `expected_use_perf` の束縛先、`probe_outcome` の
   計測前 probe の扱い、`repetition_evidence` を到達可能にする起動層 sink の変更単位。
3. **v2 の分類 claim / 回復 row を marker capability で囲むか。**

裁定 1 で (代案 b) なら単位 A の残りは無く、次段は B2 / D1 / C / D2。(推奨) か (代案 a) なら
A2β = E1 + E2 (+ 第 9 境界) を次 wave で積む。E2 の literal 4 語は A2α README 14 節の候補で確定してよい。

## 6. 次 wave の出発点

- 裁定 1〜3 が先。裁定後、branch `worktree-dev-wave-t1851-unit-a` を継承し、main を取り込んでから
  着手する。継承元の状態は本 README と worklog fragment が正本で、job dir handoff ではない。
- 6 段すべてを積んだ後に D1341 に従って 1 変更単位で land する。
