# [T-2288] B-4 床値 (floor-pair) の w2 と finalize を同じ submit-tree から走らせ、証拠確認を通して集約を発行した — 床値の候補 0.09691 (rr50 w2 由来)

`authority: none`
`default_effect: no-state-change`

2026-09-29。wave `dev-wave-t2288-floor-pair-w2`、branch `worktree-dev-wave-t2288-floor-pair-w2` (基点 local main
`035fc11fa601547f5d68e54f5661c5daa70b93a5`)。可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。時刻は特記なき限り UTC
(`date -u`、launcher の meta、receipt の epoch、`qstat -f` / NQSV accounting の JST 表示から採り、推定していない)。

## 依頼と答え

依頼は「[T-2288] 床値 (official floor) 対測定の w2 と finalize を進める。w2 の窓は 2026-09-29T00:00Z から開いている (条件は
now + 24h <= 2026-10-07T00:00Z)。投入元は既存の submit-tree (detached at `2ba4000870c63254132410b3002b5298c0c6a210`、locked のまま
HEAD を進めず削除もしない)。`run-submit.sh <wl> w2` を rr95 / rr50 / rr5 の 3 本投げ、finalize は両窓が terminal になった後に
`--finalize` (walltime 30 分)。w1 の job Elapse から見積もりを示してユーザー確認後に投入する。その後、証拠確認 (24 h 分離・n = 62・
欠測率、D1641 項 1) → 集約発行 (D1974) まで進め、採用裁定 (D1641 決定 2) の材料を返す。窓 JSONL は 3 段が終わるまで commit しない。
規律 2 は緩めない。本題だけ」だった。

**答え: w2 の 3 job はいずれも 69〜77 分で terminal `complete` (124 / 124 session、62 / 62 標本、欠落 0) になり、finalize 3 job は
いずれも `status generated` の summary を書いた。証拠確認の 4 項目 (24 h 分離・n = 62・欠測率・環境) はすべて満たした。集約は
D2138 項 8 の予測名どおりに発行され、床値の候補は `436449544102615 / 2^52` ≈ 0.09691 (出所 = rr50 の summary、その w2 の
標本最大値)。** 採用裁定 (D 記録・§5 floor 欄の記入) は行っておらず、その材料を末尾に置く。実装面の差分はゼロ。

## 計算の承認と実使用

- 見積り (投入前に提示、ユーザー承認 2026-09-29T05:27Z「w2 と finalize を承認」、job dir の `approval.log`): w2 = w1 の Elapse
  実測 4182 + 4145 + 4607 = 12,934 s ≈ 3.6 node 時間 (各 job が w1 最長 4607 s でも 3.84)、finalize = 実測単価が無いので walltime
  30 分 × 3 = 上限 1.5 node 時間、受入 1 回 ≈ 0.25 node 時間。合計 ≈ 3.9〜5.6 node 時間。
- 実使用 (NQSV accounting の Elapse): w2 = 4184 + 4151 + 4580 = 12,915 s、finalize = 5 + 5 + 5 = 15 s。計 12,930 s ≈ 3.59 node 時間
  (受入を除く)。

## 投入元 checkout と段の順序

- 投入元は w1 と同じ `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1/submit-tree` (detached、locked)。w2・finalize の
  投入時点の HEAD はどちらも `H` = `2ba4000870c63254132410b3002b5298c0c6a210` (submitter の checkout gate と job-result の
  `expected_head` で確認)。binary は w1 で place 済みのものを再利用した (再 place していない)。
- 起動 script は w1 job dir の `run-submit.sh` (stdout / stderr / rc / meta は w1 job dir の `submit-<wl>-w2[-dry].*`)。finalize は
  submit-tree の root で `bash tools/pegasus/submit_floor_pair.sh --workload <wl> --finalize [--dry-run]` を直接起動した (出力は本 wave の
  job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w2/finalize-<wl>-{dry,real}.*`)。
- 順序: w2 dry-run ×3 (05:26:10〜05:26:31Z) → ユーザー承認 (05:27Z) → w2 実投入 ×3 (05:27:00〜05:27:25Z) → w2 終端 (最後は
  06:43:53Z) → 6 窓の terminal を読む → finalize dry-run・実投入を workload ごとに交互 (06:48:26〜06:49:12Z) → 証拠確認 → 集約発行 →
  commit。
- 成果物 10 本 (窓 JSONL 6・summary 3・集約 1) は 3 段と集約の後に submit-tree 上で commit `f315186c8cecdbada3fde75bb109b9562696266e`
  (親 = `H`) とし、wave branch へ `--no-ff` で取り込んだ (merge `7a8997027081e1e357f7ad7c38b7e426e2780ecd`)。bytes は driver と発行器が
  書いたままで、追加 10 本以外の file は変えていない。submit-tree の HEAD はこの commit で `f315186c8` へ進んだ (3 段の後なので申し送り
  2 の「測定の途中で HEAD を進めない」には触れない)。

## w2 の投入と完走 (runbook §7.8、D2145)

| 項目 | rr95 | rr50 | rr5 |
|---|---|---|---|
| dry-run (rc、nonce) | rc=0、`f3ffdc35880744d16395ef115f67f7b6` | rc=0、`189c95e7b57f9ef484922ce39c0f6311` | rc=0、`30e5847b6c5a1403a3d211db6d60a1d1` |
| 実投入 (rc、nonce) | rc=0、`711b68134c39dea8cf76e5d5f94d36ad` | rc=0、`7c9631966a4d44cb448232d1ff2172cf` | rc=0、`4de14b0f02d7b27eac548adc57c0b662` |
| request / `submit-receipt.json` `status` | `35164.nqsv` / `submitted` | `35235.nqsv` / `submitted` | `35275.nqsv` / `submitted` |
| `qstat -f` (JST) Created → Started | 14:27:10 → 14:27:18 | 14:27:18 → 14:27:25 | 14:27:25 → 14:27:37 |
| `qstat -f` 要求 walltime / Accept Sigterm | 86400S / Yes | 86400S / Yes | 86400S / Yes |
| `job-result.json` `job_rc` / `gate` / `reason` / `driver_rc` | 0 / `driver` / `completed` / 0 | 同左 | 同左 |
| 同 `hostname` / `pbs_jobid` / `window_id` | `bnode046` / `0:35164.nqsv` / `rr95-w2` | `bnode096` / `0:35235.nqsv` / `rr50-w2` | `bnode097` / `0:35275.nqsv` / `rr5-w2` |
| NQSV Elapse (Ended、JST) | 4184S (15:36:58) | 4151S (15:36:32) | 4580S (15:43:53) |
| `driver.stdout` | `status complete`、`session_count 124` | 同左 | 同左 |
| `driver.stderr` | 0 byte | 0 byte | 0 byte |
| 窓 JSONL (行数 / sha256) | 126 / `4157181666cf2aca2abee1dc3876e5c28ec3c79106d6dec733ff8810f6417fa2` | 126 / `2e0c285a845795a8d5afc0aa713fb12d9d7cf4277a190a3d72c585748dbc3da3` | 126 / `ca2d79eb813c8a9d4d9104fe0b2cbd5cef722b30ab7b356d43ea8d1c3df61199` |

- `job-result.json` の `spec_sha256` は D2138 項 7 の表の値と 3 job とも一致。
- `qstat` の走行中は 3 job とも別 node で並走した (本 wave の監視 `run-watch.sh`、5 分周期、`watch.log`)。
- signal については w1 と同じく、trap による観測記録なし (`reason completed`) で walltime 到達もなく、配送の有無と SIG_IGN 継承 (F1012)
  は判定できない。

## finalize (両窓の terminal を読んでから投入)

投入前に 6 本の窓 JSONL の末尾行を読み、6 本とも `event terminal`・`status complete`・`complete_sample_count 62`・`dropped_sample_count 0`・
`recorded_session_count 124 / 124`・`recorded_measurement_count 248 / 248` であることを確認した。w1 の 3 本の sha256 先頭 16 hex
(`fa06e2130b0d15cd` / `8bdd909394fa2bce` / `12fbe874c2899de9`) は w1 insight の記録と一致した (w1 以後の変化なし)。

| 項目 | rr95 | rr50 | rr5 |
|---|---|---|---|
| dry-run (rc、nonce) | rc=0、`c846763bb935b64f6f1cb987cc403a81` | rc=0、`7be49c65a10733d4a81ca340118b70e7` | rc=0、`76b2b693818d38e249fffb22cae4e301` |
| 実投入 (rc、nonce、request) | rc=0、`5ab00fac60dde031676cb7b458e5d518`、`35475.nqsv` | rc=0、`7ec41b215d1c7ed5b1e32b55b3ba01a7`、`35476.nqsv` | rc=0、`77d354a14be9524864f7ebe9b04c352f`、`35477.nqsv` |
| qsub の walltime | `elapstim_req=00:30:00` | 同左 | 同左 |
| `job-result.json` `mode` / `job_rc` / `driver_rc` / `hostname` | `finalize` / 0 / 0 / `bnode021` | `finalize` / 0 / 0 / `bnode001` | `finalize` / 0 / 0 / `bnode017` |
| NQSV Elapse | 5S | 5S | 5S |
| `driver.stdout` `status` / `upper` | `generated` / 0.03701773176636991 | `generated` / 0.09691126658997518 | `generated` / 0.03881010837532495 |
| summary sha256 | `4945caf63ab3f01a06e08ab6b1d04e34f7801fece5c59977cb1682f2e491a320` | `fab94a54a63e1f60878bba393d4a9008f141bec993198dcc08334bfd7e7727a9` | `f62f0ff587234f284e9db7f2bd592d3afbaadcc5640fd6328cc19a51b7347066` |

summary の `upper` は窓ごとの stratum (62 差分) の標本最大値 (`upper_function sample_max/v1`) の大きい方である:

| workload | w1 の最大 | w2 の最大 | summary `upper` |
|---|---|---|---|
| rr95 | 0.03701773176636991 | 0.024304445249327067 | 0.03701773176636991 (w1) |
| rr50 | 0.07711891095333845 | 0.09691126658997518 | 0.09691126658997518 (w2) |
| rr5 | 0.030882792507505252 | 0.03881010837532495 | 0.03881010837532495 (w2) |

## 証拠確認 (D1641 決定 1・3 の証拠確認者、D1974 項 3 が人手に残した項目)

証拠確認者は D1641 決定 1 のとおり thawk105 名義で AI が務め、独立検査者ではなく「凍結どおりに測られたことの確認責任者」である。
確認は 6 本の窓 JSONL と summary を読む使い捨ての読み取り script (repo 外 `…/dev-wave-t2288-floor-pair-w2/evidence_check.py`、
sha256 `63ca57115c7c90868fc0173cd6a2618e20ed9b925c701ef8c9b183cf254b0a65`) で行い、その出力を `evidence/evidence-check.json` に置く。

| 項目 (D1641 決定 3) | rr95 | rr50 | rr5 | 判定 |
|---|---|---|---|---|
| 24 時間以上の分離: w1 の最後の session `finished_at` → w2 の最初の session `started_at` | 13:41:57.3Z (09-19) → 05:27:20.6Z (09-29) = 231.76 h | 13:41:29.2Z → 05:27:26.8Z = 231.77 h | 13:49:12.9Z → 05:27:38.5Z = 231.64 h | 満たす |
| 1 campaign・1 セルあたり n (complete sample、c1 / c2) | 62 / 62 | 62 / 62 | 62 / 62 | n = 62 (D1695) を満たす |
| 欠測 (落ちた標本、campaign ごと) | 0 / 62、0 / 62 | 0 / 62、0 / 62 | 0 / 62、0 / 62 | 5% 以下 (summary の `admissible true`、threshold `1/20`) |
| 上限 < 1 | 0.0370 | 0.0969 | 0.0388 | 満たす (`not_generated_upper_out_of_domain` でない) |
| 事前・中間・事後 probe | 両窓とも 124 / 124 session で pre / mid / post すべて `clear` | 同左 | 同左 | 競合検出なし |
| rep の rc / throughput | rc 非 0 = 0、throughput 1,240 値 / 窓 (124 session × 2 測定 × 5 rep) がすべて有限の正値 | 同左 | 同左 | 非有限値・欠測なし |
| 環境 | env_tag `pegasus`、site = gen_S 計算ノード (両窓とも `bnodeNNN`)、両窓とも header の `loaded_head` = `runtime_head` = `H`、binary sha256 は両窓とも `7cdf0dc3…` の 1 種 | 同左 | 同左 | 凍結 spec どおり |

- node は窓ごと・workload ごとに異なる (w1 = `bnode022` / `bnode080` / `bnode081`、w2 = `bnode046` / `bnode096` / `bnode097`)。
  D1641 決定 3 の site は「Pegasus 計算ノード (gen_S)」で、node の同一は要求していない。
- 予定外 retry: session の `status` は 6 窓とも 124 `complete` だけで、`dropped_by_session_id` 付きの記録は無い。
- 24 h 分離は D2138 項 2 の窓の定義 (開始許容帯の差 48 h) からは機械保証されないので、上の実 timestamp で確認した。

## 集約発行 (D1974、D2138 項 8)

submit-tree の root で、H の版の発行器 (`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`。H と本 wave の基点 main で差分なし) を
login node で起動した。`expected_specs` は `--expected-spec` 引数で 3 組を渡した (summary から導出する経路は発行器に無い)。親は
D2138 項 7 の表を `awk` / `sed` で切り出した値を引数にしたが、**実行 argv はファイルに保存していない** (`aggregate.meta` は時刻と rc
だけ)。一次資料で確かめられるのは、集約が記録した `aggregation.expected_specs` の 3 組 (rr5 `d13c3844…` / rr50 `b582d20c…` / rr95
`990e3a6f…`、発行器が relpath 順に並べ替えて記録) が D2138 項 7 の表の (relpath, sha256) と全桁一致すること、までである
(段 6 レビュー所見 1)。

```
python3 -B -m orchestrator.campaign.p3_b4_floor_artifact_issuer --repo-root <submit-tree> \
  --aggregate-summary <dir>/summary__…rr95…c1c2.json --aggregate-summary <dir>/summary__…rr50…c1c2.json \
  --aggregate-summary <dir>/summary__…rr5…c1c2.json \
  --expected-spec <dir>/spec__…rr95…c1c2.json 990e3a6f… --expected-spec <dir>/spec__…rr50…c1c2.json b582d20c… \
  --expected-spec <dir>/spec__…rr5…c1c2.json d13c3844… --aggregate-output-dir <dir>
```

(`<dir>` = `output/env/pegasus/floor-pair/t2288-f1`、`…` は `env-pegasus__protocol-silo__threads-48__workload-` 等の省略で実引数は省略
していない。sha256 は 64 hex を渡した。)

- rc=0、stderr 空。出力 `output/env/pegasus/floor-pair/t2288-f1/b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json`、
  sha256 `4896a1fd1735667c62a6ce8200d3f70faf9bc0d08e0afe7c6970e61f69d7dbdf`。file 名は D2138 項 8 の予測名と一致した。
- 中身: `schema p3-b4-authoritative-floor/v2`、`floor_exact [436449544102615, 4503599627370496]` (= 0.09691126658997518、
  `source_float_hex 0x1.8cf2d409e2d70p-4`)、`source_summary` = rr50 の summary (sha256 `fab94a54…`、`status generated`、`loaded_head` = H)、
  `aggregation.expected_specs` は 3 組 (発行器が relpath 順に並べ替えて記録)、`identity_derivation` は campaign 6 件・workload 3 件、
  `artifact_identity` は env_tag `pegasus`・protocol `silo`・threads 48。`non_guarantees` を持つ (下記「主張しないこと」)。

## 採用裁定 (D1641 決定 2) の材料

- **何を採るか:** 上の集約 1 本。採用すると §5 固定表 (`docs/phase3-b4-reflux-ablation-preregistration.md`) の
  「floor (対象動作点で再実測した between-run floor) の artifact パスと hash」欄 (現在 `未記入`) に、発行器の書式
  `artifact_path=<repo 相対>; sha256=<64 hex>` で
  `artifact_path=output/env/pegasus/floor-pair/t2288-f1/b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json; sha256=4896a1fd1735667c62a6ce8200d3f70faf9bc0d08e0afe7c6970e61f69d7dbdf`
  を書くことになる (記入は D1641 決定 1 の §5 記入担当者の手番で、D として記録する)。読み取り関数
  (`resolve_preregistered_authoritative_floor`) は同じ表の「実行責任者・開始時刻」欄も検査するが、現在の値 `実行責任者 = thawk105、
  開始時刻 = 未記入` はその述語の例外形 (`実行責任者 = <名前>、開始時刻 = 未記入`) として通る (述語の読解で、実行はしていない)。
- **採用を支える事実:** D1641 決定 3 の受理条件 (n、2 窓 × 24 h 以上の分離、欠測 ≤ 5%、上限 < 1、競合なし) をすべて満たした
  (上の証拠確認)。集約器の機械検査 (期待 spec 列との閉包一致、窓ちょうど 2) は発行が rc=0 で通った。
- **採用前に読むべき性質 (値の比較・解釈はしない):** 統計関数は凍結された「標本最大値」で、集約はさらに 3 workload の最大を取るため、
  床値は 372 差分のうち 1 標本 (rr50 w2) で決まっている。3 workload の summary 上限は 0.0370 / 0.0969 / 0.0388 で、集約は保守側の最大を
  取る設計 (D1641 決定 3「保守側の最大を取る対象集合: 凍結したセル集合 × 2 時間窓の全部」) のとおりである。統計関数・対象集合を
  結果を見た後で変えることは事前登録に反するので、材料として並べるだけに留める。
- **不採用の場合:** D1641 決定 3 の不採用条件 (欠測 > 5%、上限 ≥ 1) には当たっていない。不採用とするなら、それ以外の理由を D に
  書く必要がある。

## 段 6 相当の read-only レビュー 1 本 (逐語は `verbatim/s6-review.md`、prompt は `verbatim/s6-review-prompt.md`)

実装面ゼロの軽量版で段 2・3・5 は省き、DW-C00 の「一次資料から事実を再抽出する docs」の条項に従って突合レビューを 1 本だけ
投じた (codex `review`、read-only、06:58Z〜07:04Z)。レビューは 3 表の全 cell、6 窓の行数・件数・rep rc・throughput、分離時間、
窓別最大値、`floor_exact`、成果物 10 本の bytes 一致 (投入元と wave worktree)、commit の親と file 数、fragment の文法を検算し、
**GO (must-fix 0)** を出した。親の裁定:

| # | 所見 | 裁定 | 反映 |
|---|---|---|---|
| 1 | 「D2138 の表から切り出してその順で渡した」は、argv を保存していないので一次資料だけでは独立に確かめられない | real・should・採用 | 「集約発行」節を「集約が記録した expected_specs が表と全桁一致」までに狭め、argv 未保存を明記。fragment も同様 |
| 2 | 「答え」の強調記号が閉じていない | real・nit・採用 | 内側の強調を外した |

- `verbatim/s6-review.md` は codex 出力 (3,077 byte、sha256 `fe2b890be5fc1b887b0edcf00fe0501c4b03011072310994b78ae1637ec235ce`) に末尾改行
  1 byte だけを補ったもの (可視文字は不変、末尾の LF を 1 つ除けば原文に戻る)。
- 記録前の検出語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc=1 だった。hit は holdout rr80 / rr20 の
  各 3 件で、いずれも既存の `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の `journal.jsonl` /
  `manifest.json` / `result.json` (2026-09-17 の commit `cc82edc8c` から本 wave の基点 main にある)。本 wave が足した file は hit に含まれない。
  既存物なので本 wave では扱わない。

## 主張しないこと

- 採用裁定・§5 記入・D の記録は行っていない (依頼どおり材料を返すまで)。
- 集約の `non_guarantees` のとおり、凍結が結果を見る前に行われたこと、測定が人間の認可後に行われたこと、標本の統計的独立性、
  binary64 の中間丸めの影響、残存標本での被覆確率は証明しない。本 wave の証拠確認も、上記の記録 file を読んだ結果であって、
  計算ノードの時計の安定・node 間の差・SIGTERM の配送 (F1012) は検証していない。
- 「同一 binary 対の差」の値そのものを性能差として解釈していない。

## 後続への申し送り

1. 採用裁定 (D1641 決定 2) と §5 floor 欄の記入は後続の手番。材料は上の節。
2. submit-tree (`…/dev-wave-t2288-floor-pair-w1/submit-tree`) は HEAD が `f315186c8` に進み、未追跡 file は無い (binary は ignored で残る)。
   3 段が終わったので lock を外して撤去してよい状態だが、本 wave では撤去していない (lock 理由の文字列は「finalize まで」のまま)。
   撤去する場合は `docs/pegasus-runbook.md` と cleanup の手順 (land 調整役への `CLEANUP-READY`) に従う。
3. 証拠 dir は `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair/` に w1 の 6 本と本 wave の 12 本 (w2 dry 3・実 3、finalize dry 3・実 3)。
   削除しない。

## 生証拠

- submitter / job body / scheduler: `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair/<nonce>/` (nonce は上の表)。
- 起動 meta: w1 job dir の `submit-<wl>-w2[-dry].{meta,rc,stdout,stderr}`、本 wave の job dir の `finalize-<wl>-{dry,real}.{meta,rc,stdout,stderr}`、
  `approval.log`、`observations/qstat-f-{35164,35235,35275}-initial.txt`、`watch.log`、`aggregate.{meta,stdout,stderr}`。
- 成果物 (tracked): `output/env/pegasus/floor-pair/t2288-f1/` の `window__…-c{1,2}.jsonl` 6 本、`summary__…-c1c2.json` 3 本、
  `b4-floor-aggregate__….json` 1 本。
- 証拠確認の出力: 本 dir `evidence/evidence-check.json`。
