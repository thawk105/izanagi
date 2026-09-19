## 変更面

**新 policy と closed set の追加で、3 workload・6 cell の全件完走経路を利用できる。submitter は273行目だけでなく、receipt を構築する365行目も変更が必要。**

行番号は現在の checkout 基準。以下の略号を用いる。

- `M` = `orchestrator/campaign/paper_story_a2_certification.py`
- `S` = `tools/pegasus/submit_paper_story_a2_certification.sh`
- `J` = `tools/pegasus/paper_story_a2_certification.sh`
- `T` = `orchestrator/tests/test_paper_story_a2_certification.py`
- `JT` = `orchestrator/tests/test_paper_story_a2_job_contract.py`

| file:line | author の変更 |
|---|---|
| `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json:1`〔新規〕 | 下記 JSON を追加。A-2/A-6 JSON は編集しない。 |
| `M:74` | `B7_FIXED5_POLICY_PATH = POLICY_PATH.with_name("paper_story_b7_fixed5_regression.v2.json")` を追加。 |
| `M:358–370` | `canonical_paths` に新定数を追加。比較方法は維持。359行目の説明の `two` は `three` に更新。 |
| `M:373–381` | 名前表に `"paper-story-b7-fixed5-regression": "paper-b7-fixed5"` を追加。 |
| `M:384–390` | `IZANAGI_A2_POLICY_PATH` を追加する条件を A-6／B7-fixed5 の明示的な集合にする。A-2 と未知 study の扱いは維持。 |
| `M:564–571` | `policy_shapes` に `"paper-story-b7-fixed5-regression": (3, 6)` を追加。 |
| `S:273–275` | shell の study 条件に `paper-story-b7-fixed5-regression` を追加。 |
| `S:365–366` | 埋込み Python の receipt 環境再構成にも同じ study を追加。片方だけでは submission 検証に失敗する。 |
| `T:1045`, `T:1462`, `T:1945–2049`, `T:2519`, `T:4823` | fixture・receipt helper・policy／CLI／全件 materialize テストを追加・拡張。詳細は tests 節。 |
| `JT:31`, `JT:432–729`, `JT:1107`, `JT:1284` | 新 study fixture と harness 選択、重複検出、3 request の投入契約テストを追加・拡張。 |

`J`、admission registry、A-2/A-6 policy、partial 処理は変更不要。

## 新 policy 案

`orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` 全文：

```json
{
  "schema_version": "paper-story-a2-certification-policy/v2",
  "study": "paper-story-b7-fixed5-regression",
  "historical_reference": {
    "ccbench_commit": "6656e93",
    "role": "originating historical campaign only; never a current comparison value"
  },
  "durable_measurement_base": "/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919",
  "tracked_destination": "output/insights/2026-09-19_t1998-b7-fixed5-three-workload",
  "performance_common": {
    "records": 1000000,
    "threads": 48,
    "skew": "0.9",
    "rmw": "0",
    "max_ope": "10",
    "extime": 3,
    "reps": 5,
    "base": "L-W0",
    "wal": 0,
    "ccbench_protocol": "silo"
  },
  "legacy_correctness": {
    "ycsb_tuple_num": "200",
    "thread_num": "4",
    "ycsb_zipf_skew": "0.9",
    "ycsb_rratio": "50",
    "ycsb_rmw": "true",
    "ycsb_max_ope": "5",
    "extime": "1"
  },
  "workloads": [
    {
      "id": "rr5",
      "label": "write-heavy",
      "rratio": "5",
      "adopted_backoff_us": 5
    },
    {
      "id": "rr50",
      "label": "balanced",
      "rratio": "50",
      "adopted_backoff_us": 5
    },
    {
      "id": "rr95",
      "label": "read-heavy",
      "rratio": "95",
      "adopted_backoff_us": 5
    }
  ],
  "controlled_define_base": {
    "CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION": "1",
    "CCBENCH_NO_WAIT_OF_TICTOC": "0",
    "CCBENCH_WAL": "0",
    "CCBENCH_BACKOFF_NOINLINE": "0",
    "CCBENCH_TRACE": "0"
  },
  "trace0_cmake_argv": {
    "configure": {
      "source_option": "-S",
      "build_directory_option": "-B",
      "fixed_arguments": [
        "-DCMAKE_BUILD_TYPE=Release",
        "-DENABLE_SANITIZER=OFF"
      ],
      "toolchain_arguments": [
        {
          "role": "cc",
          "prefix": "-DCMAKE_C_COMPILER="
        },
        {
          "role": "cxx",
          "prefix": "-DCMAKE_CXX_COMPILER="
        }
      ],
      "dependency_prefix_argument": "-DCMAKE_PREFIX_PATH=",
      "fetchcontent_path_argument_prefixes": [
        "-DFETCHCONTENT_BASE_DIR=",
        "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
        "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
        "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST="
      ],
      "controlled_define_argument": "-D"
    },
    "build": {
      "subcommand": "--build",
      "target_option": "--target",
      "target_prefix": "ycsb_",
      "target_suffix": ".exe",
      "jobs_option": "-j"
    }
  },
  "cells": [
    {
      "id": "rr5-stock",
      "workload": "rr5",
      "role": "stock",
      "genome": {
        "BACK_OFF": 0,
        "BACKOFF_FIXED": -1
      }
    },
    {
      "id": "rr5-fixed5",
      "workload": "rr5",
      "role": "adopted",
      "genome": {
        "BACK_OFF": 1,
        "BACKOFF_FIXED": 5
      }
    },
    {
      "id": "rr50-stock",
      "workload": "rr50",
      "role": "stock",
      "genome": {
        "BACK_OFF": 0,
        "BACKOFF_FIXED": -1
      }
    },
    {
      "id": "rr50-fixed5",
      "workload": "rr50",
      "role": "adopted",
      "genome": {
        "BACK_OFF": 1,
        "BACKOFF_FIXED": 5
      }
    },
    {
      "id": "rr95-stock",
      "workload": "rr95",
      "role": "stock",
      "genome": {
        "BACK_OFF": 0,
        "BACKOFF_FIXED": -1
      }
    },
    {
      "id": "rr95-fixed5",
      "workload": "rr95",
      "role": "adopted",
      "genome": {
        "BACK_OFF": 1,
        "BACKOFF_FIXED": 5
      }
    }
  ],
  "certification_composition": {
    "campaign_unit": "one independently environment-contracted campaign per workload",
    "outer_certification": "logical conjunction in policy workload order"
  },
  "scheduler": {
    "project": "SFC",
    "queue": "gen_S",
    "nodes": 5,
    "walltime": "12:00:00",
    "job_body": "tools/pegasus/paper_story_a2_certification.sh"
  }
}
```

`load_policy` を通る静的根拠は次のとおり。

| 検証 | 根拠 |
|---|---|
| exact key 集合 | 現行の名前は `_POLICY_KEYS` ではなく `_TOP_LEVEL_KEYS`（`M:114–119`）。上案はその13 key と一致。`_exact_keys`（`M:307–315`）が欠落・余分な key を拒否する。 |
| 子 object の key | performance／workload／cell／genome／CMake／controlled define の集合は `M:125–163`。historical は `M:431`、scheduler は `M:448`、legacy は `M:476–481`。上案はいずれも一致。 |
| schema・composition・historical | `M:423–439`。schema と composition は A-2 同値、historical commit は形式適合し、role に指定句を含む。 |
| durable／tracked path | `M:440–447`。durable は絶対・lexical canonical、tracked は `..` を含まない相対 path。ここでは存在確認や `output/insights` prefix の強制はしない。 |
| scheduler | `M:448–460`。nodes は正の exact int、walltime は指定形式、job body は bounded relative path。 |
| 共通設定・CMake 文法 | `M:462–562`。A-2 と同値なので既存検証を満たす。FetchContent prefix は4種類、toolchain role は `cc`／`cxx`。 |
| workload identity | `M:572–587`。3件・重複しない非空 ID、非空 label、文字列 rratio、正の exact int の adopted 値。**ID・label・rratio の意味的対応そのものを固定する検証ではない**ため、その対応は新 policy 正例テストで固定する。 |
| cell shape・role pair | `M:589–608`, `M:637–641`。6件・ID 重複なし、各 workload に stock／adopted 各1件。 |
| adopted 値との整合 | **検査あり**。`M:609–616` が stock の `{0,-1}` と adopted の `{1, workload.adopted_backoff_us}` を完全一致で検査。上案では3対とも `{1,5}`。 |
| hash | `M:643–648`。生 bytes と protocol preimage を別々に SHA-256 化。新 study は固有の protocol hash を持つ。 |

## 経路確認

**全3 workload の driver が成功し、必要な証拠がそろえば、既存処理の変更なしで `finish-group → collect → materialize` が通る。** 性能上の勝利は完走の条件ではない。

| 経路・関連箇所 | 3 workload での挙動 |
|---|---|
| `M:936–938`, `M:959–989` | policy 順 `rr5, rr50, rr95` で preregistration と workload 別 directory を作る。 |
| `M:828–851`, `M:3721–3733` | exact 2 cell 制約は**workload ごと**。上案の stock→adopted 順で満たす。 |
| `M:1531`, `M:1561–1589` | submission は policy と同じ3 job を要求。scheduler、job 名、環境 key／policy path の完全一致を検査する。 |
| `M:2226–2329` | `finish_group` が全 workload の terminal／compute／reservation 証拠を検証。`M:2302` の成功数＝policy workload 数で full manifest を作る。 |
| `M:3883–4059` | workload ごとに2 raw cell と campaign closure を検証。全体では **18 manifest members、9 campaign members**（`6×3`, `3×3`）となる。 |
| `M:1854–1918`, `M:2168–2204` | full completion は3件を受理し、full acquisition を構成する。partial schema に入らない。 |
| `M:4295–4463` | manifest loader も policy 件数依存。`M:4330–4332` は `6 raw + 3 condition receipts + 9 campaign members = 18` を要求。 |
| `M:5042–5058`, `M:5000–5038` | CLI collect が acquisition を検証し、full report を導出して materialize する。 |
| `M:2735–2741`, `M:2972–2998` | 全6 cell を分類し、3 workload 分の request ID／effect を扱う。effect は `M:2930–2937` の `adopted / stock - 1`。 |
| `M:4710–4804` | report identity／request 集合を policy と照合し、acquisition 再読込みから full report を再導出して一致を要求。3 workload 固定拒否はない。 |
| `M:4808–4852` | authority・attempt 選択・fresh destination を検証し、3 workload の condition receipt を出力する。 |

全体検索で確認した、変更不要の前提・注意点：

- **partial 境界**：writer の `M:2305–2309` と consumer の `M:1930–1933` は exact two-workload のまま維持する。`_partial_workload_authority`（`M:3030`）、`_canonical_partial_report`（`M:3115`）、partial manifest producer／loader（`M:4077`, `M:4112`）へ guard を追加しない。
- **workload 内の2 cell 制約**：`M:831`, `M:1369`, `M:2958`, `M:3721`, `M:3892`, `M:3932`, `M:4431`, `M:4458`。全体を2 workload に限定する制約ではない。
- **protocol preimage**：`M:344–355` は study・workloads・cells を含む。scheduler・durable／tracked path は含まない。変更不要。
- **A-2 名の残存**：schema 定数（`M:49–72`）、preregistration／artifact schema（`M:974`, `M:1161`, `M:4856`）、campaign `spec_slug`（`M:3259`, `M:3733`）は維持。campaign の study binding と workload 別保存先は別途存在する。
- **policy path の残存**：`M:393` の default は A-2 のまま。`M:3684` の `POLICY_PATH.parents[2]` は repo root の取得であり、新 policy を妨げない。選択入口は `M:5163–5166`。
- **test token**：`M:189`, `M:2830` はテスト専用の WAL 再構成 bypass。production collect（`M:5023–5027`）は渡さない。新全件経路テストにも渡さない。
- **materialize の追加前提**：`M:1196–1240`, `M:1290–1332` の durable census／同 cohort の sibling 成果物検査がある。新しい専用 durable base を使い、余分なファイルや衝突する attempt を置かない。
- **説明文の件数**：`M:5173` の CLI help にも `two canonical` が残る。実行上の障害はない。厳密な「列挙外関数は触らない」に従い、本 plan の必須変更には含めない。

submitter／job body の経路：

- `S:68–105` で canonical policy から job 名・nodes・walltime・workloads を取得する。`S:244–255` の重複検出は取得した job 名との完全一致なので、追加変更不要。
- `S:266–330` は3 workload を順に qsub し、各 request の visibility を確認する。計算完了は待たない。「同時投入」はこの fan-out であり、3回の qsub の原子的同時実行ではない。
- `S:343–409` の receipt 生成も policy 順。study 固有の環境条件は **273行目と365行目の両方**を変更する。
- `finish-group` は `S:117–138` で選択 policy の preregistration を読み、同じ `POLICY_ARGS` を module に渡す。投入時と同じ `--policy` を指定すれば追加変更不要。
- `J:103–130` は環境変数から canonical policy を選択し、workload membership を検証する。`J:151–159` は nodes−1 の sibling を要求し、`J:358–376` は選択 policy を preflight／run に渡す。**job body は無変更**。
- job body の PBS defaults（`J:2–6`）と scratch 名（`J:340–341`）は残す。submitter が scheduler 引数を明示し、scratch は request ID ごとに分離される。

## tests

`git show 60605bec3 -- orchestrator/tests/` を参照した。同 commit と同形に、専用 fixture、policy 正負例、CLI 選択、全件 materialize、submitter 契約を追加する。

**既存テストが追加だけで赤になる箇所**：確認した2ファイルには「shipped policy の総数＝2」「全 job 名集合＝A-2/A-6」を直接 assert するテストはない。`T:1945` の3 workload A-6拒否、未知 study 拒否、既存 A-2/A-6 の shape・job 名・SHA pin はそのまま成立させる。既存 param ID の変更も不要。

一方、新 study のケースを追加するには、次の helper の二択を直す必要がある。

| file:line | 最小変更 |
|---|---|
| `T:1045`, `JT:31` | `_b7_fixed5_policy(tmp_path)` を追加。新 canonical JSON を読み、durable base だけ tmp 配下に差し替えてロードする。 |
| `T:1462–1463` | receipt helper の policy-path 環境条件に新 study を追加。 |
| `JT:442–444` | 新 fixture を作り、study→fixture の明示的3択にする。未知 study を暗黙に A-2 にしない。 |
| `JT:615–630`, `JT:677–678` | wrapper の fixture 環境変数と canonical path→loaded fixture に B7 を追加。実 durable base へ流れないようにする。 |
| `JT:706–707`, `JT:723–724` | submit と finish の両方に新 policy の `--policy` を渡す。 |
| `JT:551`, `JT:575` | rr95→`945413.nqsv` の対応は既にある。変更不要。 |

追加する正例・負例：

1. **policy literal 正例**（`T:2005` の隣）
   - shape `(3,6)`、順序 `rr5,rr50,rr95`、label／rratio、全 adopted 値5、6 cell の ID／role／genome を assert。
   - scheduler と2 destination を assert。
   - brief が同値を求める6項目を A-2 と比較する。
   - job 名 `paper-b7-fixed5`、環境集合 `_QSUB_ENV_KEYS | {"IZANAGI_A2_POLICY_PATH"}` を assert。
   - 現行 `_QSUB_ENV_KEYS` は **8 key**（`M:167–176`）。新 study は9 key。先例 commit の「7 key」を転記しない。

2. **closed set／CLI 正例**（`T:4823`）
   - 既存 default A-2／明示 A-6 に、新 study の明示選択を追加。
   - 新 policy の repo 相対 path と当該 checkout の絶対 path の両方を確認する。
   - param 化するなら `a2-default`, `a6-explicit`, `b7-fixed5-explicit` など一意な ID を使う。

3. **policy 負例**（`T:1945–1990` 付近）
   - 新 JSON の `cells[1].genome.BACKOFF_FIXED` だけを `10` に変更し、`adopted cell does not match workload policy` を期待する。
   - top-level に未知 key を1個追加し、`policy keys mismatch` を期待する。
   - workload または cell の不足を `study shape` で拒否する。
   - `T:1979` を A-6／B7 の param にし、有効 bytes を tmp の非 canonical path へコピーしても `_load_selected_policy` と `_exact_qsub_command` が拒否することを維持する。
   - `load_policy(tmp_path)` 自体は fixture 用にも許される。**canonical path 拒否は CLI 選択境界のテスト**とする。

4. **全件 finish→collect→materialize**（`T:2519–2547` と同形）
   - 新 fixture で preregister、receipt bundle、`finish_group`、acquisition 検証、`collect_results`、`_canonical_full_report` 一致、`materialize` を実行。
   - `_test_token` は使わない。
   - 6 cell・3 effects・18 raw manifest members・full schema chain・`COMPLETE.json` を assert。
   - 全 arm 正常の fixture と、`adopted_gain < 1` の fixture を param 化すると、退行を含んでも6 cell が materialize され、outer status が `reject` になる経路を確認できる。

5. **partial 不変**（`T:2501` と同形）
   - B7 に偽の partial completion を与え、exact two-workload 拒否を確認。
   - B7 の1成功／2成功では `finish_group` が partial schema を作らず、full completion の manifest が `null` になることを確認する。

6. **submitter の3 request 正例**（`JT:1284–1323` と同形）
   - `study="b7-fixed5"`、visibility failure 無効で実行。
   - jobs は3件、request ID は `945411/945412/945413.nqsv`、全 job の `-b 5`／12時間／`paper-b7-fixed5`／新 policy 環境を assert。
   - driver log の preregister、3回の exact-qsub／diagnostics／request 記録、record-submission、finish-group に同じ `--policy` が付くことを確認。
   - 既存 harness の finish 呼出しは戻り値を検査していない（`JT:721–729`）。これは**policy 伝播のテスト**であり、完走証明は上記4で行う。

7. **study ごとの重複検出**（`JT:1107–1122`）
   - B7 の同名 request→拒否、A-2/A-6 名→通過、`paper-b7-fixed5-x`→通過を追加。
   - A-2/A-6 側から B7 名を見ても通過する例を追加する。既存ケースは残す。

A-2/A-6 の不変条件は、既存 pin を更新せずに検査する。

| policy | bytes SHA-256 | protocol SHA-256 | 既存 pin |
|---|---|---|---|
| A-2 | `cacfdd5dd5f5841ed300310f73fcf36c0684b401c15cf88a83e9405fe86e5e3b` | `d99f08bcc50c605d24d443d387a2c3144c16b9e670c9b9e247227c5db1be7f9c` | `T:1864–1877` |
| A-6 | `682e0f4ed980b74d509426d8f074f51f5b8062a1ca7cf82cd8dbbaae93c4446a` | `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc` | `T:2046–2049` |

親は author 後、基準 commit から両 JSON の差分が空であることと、この pin テストを確認する。対象2テストファイルは `tools/run_tests.py` 経由で実行する。本段では pytest・実装・書込みを行っておらず、テスト実測は未確認。

## 親の投入前提

| 項目 | 確認事項 |
|---|---|
| durable base | 手動の事前作成は不要。`preregister_attempt → create_attempt_root` が `mkdir(parents=True, exist_ok=True)` する（`M:921–929`, `M:964`）。親ディレクトリへの権限・容量・symlink 不在を確認する。attempt root の再使用は拒否。 |
| durable census | 専用 base に無関係なファイル・symlink・不正な attempt を置かない。同 cohort の sibling 成果物による materialize 拒否もある（`M:1196`, `M:1290`）。現在の実在状態は未確認。 |
| tracked destination | **leaf を事前作成しない**。空 directory でも materialize が拒否する（`M:4813–4819`）。preregister 時点では拒否しないため、投入前に親が不在を確認する。 |
| attempt ID | `[A-Za-z0-9][A-Za-z0-9._-]{0,79}`（`M:86`, `M:922`, `S:63`）。`b7f5-20260919a` は適合する。 |
| policy path | repo 相対 `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` または**実行中 module と同じ checkout**の canonical 絶対 path が通る（`M:358–370`）。submit-tree から元 worktree の絶対 path を渡さない。 |
| 選択の継続 | submit、finish-group、collect すべてで新 `--policy` を指定。module CLI の `--policy` は subcommand より前に置く。省略すると A-2 になる。 |
| submit-tree | 実装 commit の detached checkout と CCBench submodule pin `511c953` を用意。tracked clean を維持する（`S:165–170`, `S:212–233`）。 |
| hydrate | brief 指定の `<tree>/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` を staging root にする。直下の `masstree`, `mimalloc`, `googletest` が実 directory であることを確認（`S:200–208`）。job body は node scratch の `*-src` へコピーする（`J:340–355`）。 |
| nodes=5 | `exact_qsub` は非空文字列 argv と先頭 `qsub` のみを検査し、`-b 5` を拒否しない（`M:2208–2213`）。**nodes の policy 一致検査は submission receipt 側**（`M:1565`）。job body は head＋4 sibling を検証する（`J:151–159`）。 |
| queue・同時期性 | gen_S の状態、quota、3 request 各5 nodes の割当可能性を投入時に確認。実開始時刻の同時性・待ち時間は未確認。既存 fan-out は各 qsub 後に visibility を確認してから次を投入する。 |
| collect 先 | `--repo-root` と新 `tracked_destination` の組合せを明示し、対象 leaf が fresh であることを確認する。 |
| 床値判定 | 結果を見る前に rr5=`0.009536033056996148`、rr50=`0.00725042525457718`、rr95=`0.0022283754708938273` を原 JSON と照合して固定。判定は稿で `effect_w < -floor_w`。コードへ gate を追加しない。 |
| 結果の扱い | 正常に測れて退行した場合も全 workload を報告する。outer `reject` と driver failure は別で、`driver_rc` は `reject` に0を返す（`M:3182–3187`）。欠落時の3-workload partial 対応は追加しない。 |

未確認事項は、新 study の実測完走、投入時の directory／queue 状態、3 request の開始時刻差、workload 間の実 source／binary digest 一致。静的な経路適合から、これらの成立までは主張しない。

## 裁定パッケージ候補

実行を成立させるために必要な scope 外変更は**なし**。

説明文だけ、`M:5173` の CLI help に「two canonical」が残る。厳密な編集範囲を維持するなら据え置ける。直す場合も `two`→`three` の文言修正だけであり、受理条件は変更しない。

## 総括

- 新 policy、module の5箇所、submitter の**2条件**、対応テストで実装できる。
- 全3 workload・6 cell の full finish／collect／materialize は既存経路で扱える。
- A-2/A-6 bytes・protocol pin、job body、partial 境界は維持する。
- 床値判定と投入・回収・稿は親の担当とする。
- 本回答は静的確認による plan。テスト・測定は未実施。