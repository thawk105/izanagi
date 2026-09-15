## 総括

rr95：**射影内の artifact だけでは凍結不可**。accepted 較正は 1 件あるが、採用する binary・portable build record と全項目確定済みの PerfConfig を確認できない。  
rr50：**同じく凍結不可**。accepted 較正は 3 件あるが、較正の存在だけでは残りの必須入力を充足しない。  
rr5：**登録済み較正からは凍結不可**。全 4 file 中、対応する較正は 0 件であり、他 workload の流用は D15 と binder が禁じる。  
較正を待たずに確定・準備できる欄はある。ただし、必須欄を欠いた JSON は今回の定義の「凍結」にならない。rr95／rr50 を rr5 と同時に凍結するコード上の要求はない。  
**repo 全体の receipt・spec・binary「0 件」は本射影では独立確認できないため、親の断定を検証済み事実としては採用しない。** HEAD は `0600887d92538b3f34d894f9674d202d0a29a578` と確認した。

## spec 必須欄の充足表

以下の略号は、指定された絶対パスを指す。

- **F**：[floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/floor_pair_driver.py)
- **B**：[s8b_binary_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/s8b_binary_admission.py)
- **I**：[p3_b4_floor_artifact_issuer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/p3_b4_floor_artifact_issuer.py)
- **T**：[test_floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/tests/test_floor_pair_driver.py)
- **P**：[事前登録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/docs/phase3-b4-reflux-ablation-preregistration.md)
- **D**：[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/docs/decisions.md)

共通型規則：object は記載した **exact key 集合**。整数は bool を含まない exact int、文字列は非空。ID は `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`、SHA は lowercase hex 64 桁。相対 path は canonical repository-relative で、絶対 path・dot・親参照を拒否する。JSON の重複 key・非有限値も拒否する（F:90、F:364、F:403、F:426、F:439、F:453、F:460）。

**較正の現物。** 次の 4 file を全件 JSON として読み、SHA-256 を計算し、HEAD blob との byte 一致を確認した。全件 `quality.status="accepted"`、`env_tag="pegasus"`、`clocks_per_us=2100`、`threads=48`、`saturation.records=1000000`、skew=`"0.9"`、rmw=`"0"`。

| 略号・絶対パス | rr・根拠行 | 実測 SHA-256 |
|---|---|---|
| **C95**：[calibration-5c836a22eff9ab40.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/env/pegasus/calibration/registered/calibration-5c836a22eff9ab40.json:1572) | `"95"`。quality:1604、records:1617、threads/workload:1690 | `5c836a22eff9ab40cabb23cb597cd0b3c232979696c5784b6b3d358b92c789cc` |
| **C50a**：[calibration-449d0ad22f13e366.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/env/pegasus/calibration/registered/calibration-449d0ad22f13e366.json:1571) | `"50"`。quality:1603、records:1616、threads/workload:1689 | `449d0ad22f13e3665ae8eb890c58a2fba25f7a5c95b0b039ce944f473e790008` |
| **C50b**：[calibration-753f535a8d024727.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1568) | `"50"`。quality:1599、records:1612、threads/workload:1685 | `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49` |
| **C50c**：[calibration-94a4b79fa31bba3c.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1568) | `"50"`。quality:1599、records:1612、threads/workload:1685 | `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` |

表の「未確定」は、射影内に採用値・実入力を確認できないという意味である。新たな測定が必要だと一律には意味しない。

| 欄 (file:line) | 要求 | rr95 | rr50 | rr5 | 較正依存か |
|---|---|---|---|---|---|
| top-level（F:1243） | exact `{schema, provenance, environment, artifacts, cells, pairs, windows, randomization, statistics, failure_policy, outputs}` | 全欄必要 | 同左 | 同左 | 混在 |
| `schema`（F:56、F:1251） | string、exact `"floor-pair-spec/v3"` | 確定 | 確定 | 確定 | いいえ |
| `provenance`（F:660） | exact `{calibration, source_commit}` | 下記 | 下記 | 下記 | 混在 |
| `provenance.calibration`（F:647、F:1131、F:1154） | exact `{path, sha256, attestation_mode}`。path・SHA は実在する tracked 較正へ束縛。mode は `"required"`／`"none"`。ただし `calibration=None` は拒否。accepted、正整数の saturation.records が必要 | C95 の path・SHA を供給可能。mode は required を用いる対象。完全 admission 再検証は未実施 | C50a/b/c から採用する **1 件**を選ぶ。完全 admission 再検証は未実施 | 対応する登録済み artifact がない | **はい** |
| `provenance.source_commit`（F:666、F:1285） | lowercase hex 40 桁、loaded HEAD と異なる真の祖先 commit | 現 HEAD は将来の子 commit で凍結する際の候補。現 HEAD 自身を読み込む場合には使えない | 同左 | 同左 | いいえ |
| `environment`（F:692） | exact `{site, env_tag, clocks_per_us, numactl_argv, use_perf, timeout_s, extra_env, probe_timeout_s}` | 下記 | 下記 | 下記 | 混在 |
| `.site`（F:701） | `site_policy.OTHER / PEGASUS_LOGIN / PEGASUS_COMPUTE / PEGASUS_SUSPECT` の値。裁定上は Pegasus 計算ノード gen_S | D1641 決定3で確定。wire literal の正本は射影外 | 同左 | 同左 | いいえ |
| `.env_tag`, `.clocks_per_us`（F:723、F:1154、F:1185） | ID・正整数。較正と一致。env_tag は D1641 により resolver から導出 | `"pegasus"`, `2100` は C95 に実在 | 同値が C50a/b/c に実在 | site 方針は確定しても対応較正との一致を未確認 | **束縛ははい** |
| `.numactl_argv`, `.use_perf`, `.timeout_s`, `.extra_env`, `.probe_timeout_s`（F:709、F:721） | argv は非空文字列の list、空 list 可。use_perf は false。両 timeout は正整数。extra_env は非空 string→string の map、空 map 可、`PATH`／`LD_` 接頭辞は禁止 | false は確定。他の採用値は未確定 | 同左 | 同左 | binder 上はいいえ |
| `artifacts[]`（F:739） | 非空 list。各要素 exact `{artifact_id, binary_relpath, binary_sha256, build_receipt, trace}`。artifact_id は一意 ID、trace=false | 構造と false は確定。採用 artifact 未特定 | 同左 | 同左 | いいえ |
| `.binary_relpath`, `.binary_sha256`（F:760、F:1136） | symlink component のない repo 内 regular file。現物 SHA 一致。**binary 自体の tracked 要求はない** | 対象現物未確認 | 同左 | 同左 | いいえ |
| `.build_receipt`（F:639、F:1091、F:1143） | exact `{path, sha256}`。現物・SHA・HEAD blob が一致し、**portable binary record 全体**を B の validator が受理すること。record／subject の binary SHA は spec と一致、trace=false | 対象 record 未確認 | 同左 | 同左 | いいえ |
| `cells[]`（F:798） | 非空 list、各要素 exact `{cell_id, perf_config}`。cell_id は一意 ID | exact セル列は未確定 | 同左 | 同左 | 集合方針はいいえ |
| `.perf_config`（F:775） | exact `{records, threads, workload, extime, reps, ycsb_max_ope}` | 下記 | 下記 | 下記 | 混在 |
| `.records`, `.threads`（F:787、F:1187、F:1193） | 正整数。全 cell が単一較正の saturation.records／threads と一致 | C95：`1000000`, `48` | C50a/b/c：`1000000`, `48` | 較正による採用値なし | **はい** |
| `.workload`（F:93、F:781、F:1191） | exact `{ycsb_zipf_skew, ycsb_rratio, ycsb_rmw}`。全値非空 string。較正の workload dict 全体と exact 一致。parser 自体に数値域検査はない | C95：`{"ycsb_zipf_skew":"0.9","ycsb_rratio":"95","ycsb_rmw":"0"}` | C50a/b/c：同じ skew/rmw、rratio=`"50"` | rratio=`"5"` は依頼の対象だが、完全な署名を支持する登録済み較正なし | **束縛ははい** |
| `.extime`, `.reps`, `.ycsb_max_ope`（F:790、D:51703） | すべて正整数。binder は較正照合しない。D1641 は校正済み PerfConfig の採用、D1696 は照合責任を人手に残す | 4 較正 file に当該 key なし。採用値未確認 | 同左 | 同左 | **規範上ははい、機械照合なし** |
| `pairs[]`（F:818） | 非空 list、各要素 exact `{pair_id, cell_id, reference_artifact_id, sides}`。各 ID は所定型、pair_id 一意、参照先が cells/artifacts に存在 | 構造は確定。具体的な cell・候補・参照の割当未確定 | 同左 | 同左 | 直接にはいいえ |
| `.sides[]`（F:831） | exact 2 要素、各要素 exact `{side_id, candidate_artifact_id}`。side_id 集合は `{candidate_1,candidate_2}`。両側が同一 candidate ID。reference ID は candidate ID と異なる | D1641 の対照対方針で確定。実 artifact の ID 待ち | 同左 | 同左 | いいえ |
| `windows[]`（F:869） | 非空 list、各要素 exact `{window_id, campaign_id, not_before, not_after, sample_count, pair_ids, artifact_relpath}` | 下記 | 下記 | 下記 | いいえ |
| `.window_id`, `.campaign_id`, `.not_before`, `.not_after`（F:884） | 各種 ID は spec 内一意。時刻は UTC `Z`、非空半開区間、窓同士は非重複。裁定上は 2 campaign、24時間以上分離 | 方針は D1641。実日時と ID は未確定 | 同左 | 同左 | いいえ |
| `.sample_count`, `.pair_ids`（F:896） | sample_count は正整数、採用値 **62**（D1695）。pair_ids は非空・重複なしの既存 pair ID 列 | 62 は確定。pair 列はセル／対の確定待ち | 同左 | 同左 | いいえ |
| `.artifact_relpath`（F:914、F:1271） | 相対 path、全 window と summary の出力先が相異。親 directory 実在・symlink なし。出力 leaf の未作成は許される | 正式出力名未確定 | 同左 | 同左 | いいえ |
| `randomization`（F:928） | exact `{algorithm, seed_hex}`。algorithm=`"hmac-sha256-rank/v1"`、seed_hex は64桁 lowercase hex | algorithm は F:60。実 seed 未確定 | 同左 | 同左 | いいえ |
| `statistics`（F:937） | exact `{session_reducer, stratum_upper, closed_strata, final_combiner, reference_measurements_per_pair_sample, difference_formula}` | 下記固定値を供給可能。closed_strata の具体列は未確定 | 同左 | 同左 | いいえ |
| `.closed_strata[]`（F:976、F:1079） | 非空 list、各要素 exact `{window_id,pair_id}`、ID、重複なし。全 planned `(window_id,pair_id)` と集合一致 | 確定した窓と対から導出する | 同左 | 同左 | いいえ |
| `failure_policy`（F:999） | exact `{policy,retry_count,require_all_reps,max_dropped_fraction}`。値は順に `"d1641-drop-and-count-max-5pct/v1"`, `0`, `true`, `"1/20"` | F:64／D1641／D1695で確定 | 同左 | 同左 | いいえ |
| `outputs`（F:1033） | exact `{window_format,summary_format,summary_relpath}`。形式は `"floor-pair-jsonl/v1"` と `"floor-pair-summary-json/v1"`。summary_relpath は前述の出力 path 条件 | 形式は確定。正式出力名未確定 | 同左 | 同左 | いいえ |

`statistics` の残る固定値は F:61–73、F:950–974 により次のとおり。外部測定 artifact を必要としない。

```text
session_reducer = "median/v1"
stratum_upper = "sample_max/v1"
final_combiner = "max_over_closed_strata/v1"
reference_measurements_per_pair_sample = 2
difference_formula =
"D=abs((median(candidate_1)/median(reference_1)-1)-(median(candidate_2)/median(reference_2)-1))"
```

**JSON 外の必須入力もある。** spec 自身は regular file として実在し、呼出引数 `expected_sha256` と一致し、loaded HEAD の tracked blob と byte 一致しなければならない（F:1197、F:1225、F:1230、F:1237）。spec 内へ `spec_sha256` や `loaded_head` を追加する形ではない。

## 凍結できない欄と、欠けている前提

### 1. rr5 の `provenance.calibration` と較正束縛欄

必要なのは **rr5 の対象署名に対応する accepted calibration 1 件**。登録済み directory の実在 4 file は rr95×1、rr50×3なので、ここに rr5 はない。

これにより `calibration.path/sha256`、採用する `records/threads/workload`、env/clocks の一致を閉じられない。producer は D1641 決定3が指定する calibrator だが、**その producer 実装は射影に含まれておらず、file:line は確認できない**。受入側の所在は F:1154、F:1170、F:1181。

- **D15**（D:222、D:241）：単一較正で別 workload を賄う案を却下。
- **D1936 項6・7**（D:58146、D:58156）：stock 較正の方針を維持し、不要な BACKOFF_FIXED 宣言等を整合して取り下げる。patch materialize・receipt 新 shape を増やす案は採らない。
- **D1696**（D:51702）：schema／validator 拡張で解く案は禁止。
- 較正取得自体は D1641 が認可済みであり、**既裁定が取得一般を禁止しているわけではない**。本依頼が scope 外としているため、取得計画は起草しない。

rr95 は C95 が既にあり、「rr95 較正取得待ち」を現在の必須停止理由にはできない。

### 2. `artifacts[].binary_*` と `build_receipt`

必要なのは、採用する候補・参照についての **実 binary と、それに一致する v3 admission receipt を内包した portable binary record**。

個数を分けて数える必要がある。

- parser が要求するのは **各 spec 最低2 artifact ID**。candidate と reference の ID が異なるためである（F:856）。
- **異なる binary file／receipt file が必ず2件必要、3 spec なら必ず6件必要、とはコードから導けない。** path・SHA の相異は要求されず、receipt の共有も扱っている（F:1143）。
- 実際の distinct file 数は採用する候補・参照と共有関係で決まる。それが未特定なので、正確な不足 file 数は確定できない。
- 射影内には採用対象の実 record／binary が示されていない。**repo 全体の実 instance 数は未確認**。

producer は **B:192 `issue_binary_admission_receipt`**。これは receipt 本体を返す関数であり、F が読む portable record 全体の発行・保存までを単独で行う関数ではない。

発行には human-reviewed／S8B_FLOOR admission（B:213、B:219）、source evidence・binding、実 binary の SHA（B:267）、compiler input manifest、sealed snapshot capability（B:247、B:274）が必要。**較正引数はない**ので、この依存は較正取得とは分離できる。

F が読む file のトップは B:46 の exact 集合：

```text
{cell_id, holdout_id, configuration_id, binary, binary_sha256,
 bin_hash_short, binding, configure_argv, build_argv, cached,
 store_path, admission_receipt}
```

`configuration_id=="sort_best"` の場合だけ `sort_swo_oracle` も必要（B:85、B:467）。receipt 本体だけを保存して渡しても通らない（F:1099、B:343）。

既裁定には、この既存 producer を用いた正当な準備を一律禁止するものは確認できない。D1696 が禁じるのは validator 拡張であり、artifact 準備そのものではない。合成 fixture の文字列 binary と自己構成 receipt（T:54、T:164）は実 artifact の代わりにならない。

### 3. `extime/reps/ycsb_max_ope` と exact セル・対の集合

登録済み 4 較正 file に **`extime`・`reps`・`ycsb_max_ope` という key は存在しない**。noise_floor の標本数を floor 測定の reps と同一視する根拠もない。

必要なのは **3 workload 分の完全な PerfConfig の採用根拠**と、各 spec の exact セル／対の列である。これは「必ず追加 JSON 3 file を作る」という要求ではない。既存の根拠から供給できるなら、それを使う。

- **D1641 決定3**（D:50335）：calibrator 出力を採り、AI が委任の下で承認する。
- **D1696**（D:51703）：当該3欄の較正照合、driver／軸、§5セル集合との一致は人手責任として残す。検査がないことは自由な仮値の採用許可ではない。
- P:1201 の「5反復×3秒」は **名目値**であり、P:1203 は PerfConfig 未校正と明記する。これを実値へ転用できない。
- D1641 の「3 workload × §5 の contention セル」は方針だが、指定された §5 から具体的な contention セル列は確認できない。したがって、実セル数や必要 binary 数を推測で固定しない。

不足する根拠の producer 所在は、射影外の calibrator／対象 driver 等を読まずには確定できない。本段では取得作業や新形式の発行を計画しない。

### 4. 日時・seed・命名・実行設定の具体値

必要なのは各 spec の **2窓分の日時・識別子、seed 1値、出力名3個（window×2＋summary×1）**と実行設定の確定である。既存の裁定は関係・型・方針を決めているが、射影内にこの wave 用の具体値はない。

これらを較正取得待ちにする機械上の理由はない。ただし、値を今回勝手に捏造して「既存 artifact で埋まった」とは扱えない。

- **D1641／D1695**：2 campaign、24時間以上分離、n=62、事前無作為化、命名方針を維持する。
- **D1696／D1974**：n=62 と24時間分離を新しい validator へ移さない。集約器の窓ちょうど2検査は既に I:1058 にある。
- 出力 path は **将来生成する出力の指定欄**であり、loader は leaf 未作成を許す（F:529）。入力 artifact の架空 pin と混同して、測定済み window／summary を凍結前に要求してはいけない。

### 5. 集約成果物は凍結の入力ではない

既存 producer は I:1225 `issue_aggregate_authoritative_floor`。期待 spec を F の loader で読み、各 spec の窓数を検査する（I:1054）。

D1936 項7／D1974 と P:281 の集約規則は着地済みである。**3 summary と集約 artifact は測定後の出力であり、その未取得を spec 凍結の不足入力に数えない。** 新しい集約基盤・台帳・manifest は不要で、P:305 が新設を禁じている。

## 親 brief の誤り

[親 brief](/home/SFC/tanab/.claude/jobs/f1ebd45c/tmp/wave-t2288/s1-brief.md:38)について、訂正・限定が必要な点は次のとおり。

1. **P1-a の workload 制約は正しい。** ただし rr5「0件」を独立確認できた母集合は指定の registered directory 全4 file。repo 全域の較正不在へは拡張しない。

2. **P1-b は「較正が揃っている」の意味が広すぎる。** rr95／rr50 の accepted artifact はあるが、完全な PerfConfig が揃ったことにはならない。`extime/reps/ycsb_max_ope` の採用根拠が別に要る。

3. **実測表44行の方法では spec 実 instance「0件」を証明できない。** `git ls-files | grep -i floor.pair` はファイル名による抽出であり、任意の名前で保存された `floor-pair-spec/v3` を除外できない。件数そのものが誤りだとは断定しないが、提示された根拠は不十分。

4. **43行・P1-b の receipt／binary「0件」は本段で未検証。** 射影外 file の内容を読む全域検索は行っていない。receipt 不在から binary 現物不在も導けない。また F:1136 は binary の tracked blob 一致を要求していない。

5. **P1-c は限定して維持する。** 「較正なしの部分 JSON を凍結 spec として commit できない」は正しい。一方、「較正待ちの間に準備できる範囲がない」「rr95／rr50 も rr5 を待たなければならない」は導けない。binary／record 準備、確定済み統計規則、ID・出力名等は較正と分離できる。

実測表の **registered 較正 rr50=3、rr95=1、rr5=0、§5 floor=`未記入`** は現物で一致を確認した。

## 本報告が保証しないこと

- 静的読解と、登録済み4 fileの JSON・SHA・HEAD blob 照合による報告である。
- `load_frozen_spec`、較正 admission verifier、pytest、build、測定は実行していない。accepted の記載を確認したことと、現行 verifier の受理実測は別である。
- 射影外を読んでいないため、repo 全体の receipt・binary・spec の不存在、完全な PerfConfig の根拠の不存在、射影外 producer の所在は保証しない。
- ファイル作成・変更・commit は行っていない。**厳密な全域不足件数まで確定した報告ではなく、その未確認箇所を明示した段2起草である。**