# [T-2515] write-heavy (rr5) の accepted 認定較正を取得した

2026-09-16。wave branch `worktree-dev-wave-t2515-rr5-accepted-calibration`。
**コードもテストも 1 行も変えていない。** 変えたのは docs 1 file と、job が生成した `output/` 配下の
成果物だけである。

## 1. 何が届いたか

`registered/calibration-2b7ba072b88023ae.json` (silo / rr5 / t48 / pegasus、`quality.status=accepted`)。
これで t48 / pegasus の 3 workload セル (rr5 / rr50 / rr95) が揃った。

**届かなかったもの:** 非 silo の rr5 (mocc / tictoc) は取っていない。T-2224 が
「本題の必要条件でない」として外した残件であり、本 wave も scope に入れていない。

**性能を比較していない。** 取ったのは物差し (レコード数と within-run 雑音床) であって
throughput の優劣ではない。雑音床の平均値を他 protocol と横に並べても性能比較にはならない。

## 2. なぜ今まで取れず、今回取れたのか

2026-09-14 の投入 (`0_995806.nqsv`、silo / rr5) は `selection-invalid` で棄却された。
原因は**選択器**である。書き込み主体の workload では作業集合の代理指標 (maxrss) と実際の
LLC miss 率が食い違い、D15 の下限基準が選ぶ N=1,000,000 の miss 率 0.364% が品質検査の下限
0.50% を割った。品質検査は正しく却下していた。

D1986 項 1 (ユーザー裁定) がこの選択器を直すことを決め、D2026 がその規則を登録した。
**規則は「候補集合の中で LLC miss 率が `cache_floor` 以上である最小のレコード数を採る」であって、
下限 0.50% は 1 bit も動いていない。** 直ったのは選択器の側であり、検査は従来と同じ点を却下する。

| 事項 | commit | 着地 | 本走との順序 |
|---|---|---|---|
| 選択器の実装 | `632754bbc` | 2026-09-15 15:50 | 本走より前 |
| D2026 本文の decisions.md への収録 | `3c87bafdc` | 2026-09-15 18:35 | 本走より前 |
| 本 wave の投入 | request `478.nqsv` | 2026-09-16 10:58 | — |

D1986 項 1 の条件「走らせ直す前に規則を登録する」は、実装・収録とも本走より前に main へ
着地していることで満たされている (両 commit が `refs/heads/main` の祖先であることを実測)。

**2026-09-14 の却下記録は却下のまま残している。** `attempts/0_995806.nqsv/calibration.json` は
今も `{"status": "rejected", "reasons": ["selection-invalid"]}` である。再解析も上書きもしていない。
同項の条件「今回の rr5 の却下記録は却下のまま残し緑へ読み替えない」を満たす。

## 3. 段 1 の生死確認 — 旧系列への規則適用は「予測」であって測定ではない

投入前に、却下試行の実測系列へ現行 `find_saturation` をそのまま当てる probe を repo 外で走らせた。

| | 当時の判定 (2026-09-14) | 旧系列へ現行規則を適用 |
|---|---|---|
| 採用点 | 1,000,000 | 2,000,000 |
| 採用点の miss 率 | 0.364% | 1.392% |
| `cache_floor_warning` | true | false |
| 品質 | rejected `['selection-invalid']` | 警告なし |

**この probe が示したのは「旧系列なら選択警告が解消する」までである。** 新しい run は新しい測定で
あり、採用点が動けば雑音床も取り直される (`sweep.py` は選択後の N で反復する)。旧 run の
CV=0.013535 は N=1,000,000 の値であって、新しい選択点 N=2,000,000 の品質を裏づけない。
段 3 のレンズ A がこの点を指摘し、親が裁定で採用した。

## 4. 実測値 (request `478.nqsv`)

共通条件: threads 48 / cpuset_size 48 / HT off、`ycsb_zipf_skew=0.9`、`ycsb_rratio=5`、
`ycsb_rmw=0`、`clocks_per_us=2100`、L3 総量 110,100,480 bytes、`l3_multiple=4.0`、
queue `gen_S`、`elapstim_req_s=7200`、ノード `bnode013`、
CCBench `511c9538e4e8efa54b45cda62e72389ed3b706ec` を `pinned_clean=true`、
genome `silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`。

倍々スイープ (3 反復の中央値):

| N | LLC miss 率 | maxrss | 作業集合 / L3 | 隣接差 | throughput 中央値 (tps) | 1 run 実時間 |
|---:|---:|---:|---:|---:|---:|---:|
| 1,000,000 | 0.339807% | 517 MB | 4.93 | — | 2,511,241 | 3.45 s |
| **2,000,000** | **1.566765%** | **1,023 MB** | **9.75** | 1.2270 pp | 2,803,093 | 3.86 s |
| 4,000,000 | 4.707082% | 1,958 MB | 18.64 | 3.1403 pp | 3,241,137 | 4.54 s |

選択結果: `records=2,000,000` / `saturated=false` / `lower_bound_selected=true` /
`cache_floor_warning=false` / `miss_rate_at=0.015668`。
成果物の `notes` は採用点の移動を逐語で残している —
「cache_floor 下限 0.50% を満たす最小 N を同じ下限基準候補から選択: N=1,000,000 (LLC miss 0.340%)
→ N=2,000,000 (LLC miss 1.567%)。」

within-run 雑音床: n=10、平均 2,767,078.7 tps、中央値 2,761,684.0、標準偏差 26,859.57、
**CV = 0.9707%** (上限 5%)、`high_variance=false`。`scale_sensitivity` は `not-measured`。

**隣接差は両区間とも飽和閾値 1 pp を超えるので飽和候補は無く、下限基準へ進んでいる。**
D2026 の射程の限界が言う「飽和候補が全て下限未満で最終点だけが適合する系列」には当たらない。

## 5. 「accepted を取得した」と書くために照合した証拠

段 4 の裁定が定めた最小証拠集合を、すべて現物で照合した。

- submit receipt (`attempts/submissions/49ff53d06efaf533a9ee0daaf588e831/submit-receipt.json`) と
  acquisition receipt。request `478.nqsv`、`job_script_sha256 =
  3fc75c03fb66b4c284b70d6558b7fbe6eb081a2d02b3f10c07a1c99bb570e110`、
  `binary_sha256 = 2135d54cb96324c2ce7e3760e2dd1776e8e9b3e116ec4f376763bb265fe12972`、
  `known_values_check.passed = true`。
- registered の実 bytes の SHA-256 =
  `2b7ba072b88023aecb4361781229bb5343dbfa489f4c7cc3dd8369c33bd3a067`。
  file 名の先頭 16 桁と一致し、attempt 側 `calibration.json` と **byte 単位で同一**。
- `publish.json` の `method=link-unlink` / `target=calibration-2b7ba072b88023ae.json`、
  `published-self-comparison.json` の `passed=true` / `input_sha256` が上記と一致。
- `job-result.json` の `calibrate_rc=0`、`pbs_jobid=0:478.nqsv`。
- request 固有の終端会計 (`izanagi-job-evidence/calibration-certify/<nonce>.scheduler.stderr`) が
  `Ended Request Time: Wed Sep 16 11:01:29 2026` / `Elapse: 185S`。
- `failure.json` / `rejection.json` は 0 件。`worktree-remove.stderr` は空。

**publish は計算ノード上の `orchestrator/calibrate.py --certify` が行った。** 親は registered へ
1 byte も書いていない。手で publish する経路は使っていない。

## 6. 失効していた前提 — 先行 3 本と同一の実行物ではない

`certify_calibration.sh` の SHA-256 は、2026-09-15 の先行 3 本が記録した
`08bbc498e36d1c9361d8f421d3dfce22cff1efc3c2553d22da6c773bc7e754ad` から
`3fc75c03fb66b4c284b70d6558b7fbe6eb081a2d02b3f10c07a1c99bb570e110` へ変わっていた。
差分は `f5ba28378` による**予約式のコメントと receipt の `walltime.formula` 文面だけ**で、
`frozen_required_s` (6610) も timeout 値も不変である。実行手順は転用できるが、
先行の所要 184 / 177 / 238 秒は参考値であって本走の保証ではない。本走は 185 秒だった
(会計の Elapse。要求枠 7200 秒に対する 1 回の観測であり、最大経路の完遂を示す証明ではない)。

`submit_certify.sh` も相対 job path の絶対化と `cd "$REPO_ROOT"` 後の qsub が入っており、
現在は `--repo-root` 指定と実行 root が束縛される。本 wave は wave worktree を root に指定して
投入したので、submission・job-staging・attempt・registered はすべて wave worktree 配下に出た。

## 7. 走らなかった検査 — v1 コーパスの乖離は本 wave より前からある

`orchestrator/tests/test_env_attestation.py::test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies`
は `calibration/attempts/*/calibration.md` の集合を `_V1_CORPUS_DOCS` と**完全一致**で比較する。

この node は `orchestrator/tests/growth_test_holds.py:300` に `hold_axis=output_artifacts` で
登録されており、実走すると
`IZANAGI_GROWTH_HOLD_SUMMARY_V1 {"collected_hold_functions":1,"opted_in":false}` を出して
**skip される** (親が本 wave で実測。1 skipped)。解除条件は explicit-user-command-only である。

**したがって本 wave の attempt 追加はこの検査を赤にしない。しかし「整合性を確認した」とも言えない。**
実測した乖離は次のとおりである。

| | 件数 |
|---|---:|
| `_V1_CORPUS_DOCS` の `calibration.md` | 3 |
| 投入前に実在した `calibration.md` | 9 |
| 本 wave の追加後 | 10 |

投入前から 6 件の乖離があり、本 wave はそれを 7 件にした。hold の `collateral_note` は、
この node を止めると固定件数 48・成功/失敗集合の非交差・JSON pair の完全分割の検査も
同時に止まると明記している。**hold の解除はユーザー指示専用なので本 wave では触っていない。**
この事実は記録として残す。

## 8. 依頼の前提のうち、一次資料と食い違った点

依頼は「branch `worktree-dev-wave-t2515-calib-rr95-rr5` (tip `559bcbc29`) の未着地 6 commit を
回収する」としていた。**内容で照合した結果、回収はすでに完了していたので行っていない。**

| commit | 現状 |
|---|---|
| `ad002de1b` / `bcfd2b931` / `3dbf7ea1d` / `18704ae18` / `ec17af5dc` | `35a740cd4` (2026-09-10) が必要差分を現行 main へ合成済み |
| `ec17af5dc` の insights / spool の残余 17 file | 2026-09-15 の `worktree-dev-wave-t2515-record-recovery` (main の祖先) が byte 一致で回収済み。着地先は `output/insights/2026-09-10/t2515-rr95-rr5-calibration/` (D1941 の日付別配置)。依頼が指す平坦名 `2026-09-10_t2515-...` は存在しない |
| `559bcbc29` の conftest / t1259 部分 | T-2579 が D1936 項 43 に従って実装済み。`test_t1259_qsub_env_delivery_probe.py` は main と branch で blob が同一 |
| `3dbf7ea1d` の条件関門 argv 修正 | **失効**。D1936 項 6 (`b3c62ee7f`) が `run_condition_gate` ごと撤去したため対象が存在しない。逐語回収は誤りになる |

`git cherry main <branch>` が 6 件すべてを `+` と出すのは patch-id 判定だからであり、
着地判定には使えない。

## 9. 一次資料

- registered record: `output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json`
- attempt: `output/env/pegasus/calibration/attempts/0_478.nqsv/`
- 生証拠: `output/env/pegasus/calibration/job-staging/0:478.nqsv/`
- 投入受領証: `output/env/pegasus/calibration/attempts/submissions/49ff53d06efaf533a9ee0daaf588e831/`
- 却下試行 (据え置き): `output/env/pegasus/calibration/attempts/0_995806.nqsv/`
- 先行記録: `output/insights/2026-09-13/t2515-t2534-backoff-withdraw/README.md`、
  `output/insights/2026-09-15/t2224-nonsilo-calibration/README.md`
- 子の逐語: `verbatim/`
- 裁定: D15 / D1986 項 1 / D2026 / D1641 決定 2

## 10. 限界 (謳わないために書く)

- 所要 185 秒は 1 回の観測であって分布でも再現性の主張でもない。
- `scale_sensitivity` は `not-measured` である。
- 倍々スイープは下限充足で打ち切るので、未観測の点まで含めた最適性は主張しない。
- 選択器と判定器を合わせた挙動は D2026 の前後で変わっている。D1986 項 1 の裁定は、
  別系統モデルが「受理範囲は変わっている」として現状維持を推した両論を記録したうえで
  ユーザーが改定を採ったものである。本記録は旧測定の遡及認定ではない。
- 本 wave は 1 本だけ投入した。却下が再発した場合に備えた自動再投入は行っていない。
