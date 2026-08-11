## 1. 編集面の完全な列挙

採る設計は「`Integrity` に optional な witness 情報を保持し、`result_to_dict` では witness がある場合だけ条件付き出力」です。既存 `notes` だけでは期待値・観測値・差を構造化できず、無条件の新 key は凍結証拠を壊すため不採用です。

### verifier

- `orchestrator/verifier/core.py:17`

  signature を次へ変更します。

  ```python
  def verify_trace_dir(
      trace_dir: str,
      max_report: Optional[int] = 20,
      *,
      expected_commits: Optional[int] = None,
  ) -> VerifyResult:
  ```

  keyword-only にして、既存の第2位置引数 `max_report` との取り違えを防ぎます。既定値は `None` です。

- `orchestrator/verifier/core.py:19`–`30`

  `parse_trace_dir()` 後の `len(txns)` を trace 内の観測 committed txn 数とし、witness がある場合だけ以下を設定します。

  ```text
  integrity.expected_commits = expected_commits
  integrity.observed_commits = len(txns)
  ```

  不一致時は `notes` にも `expected / observed / delta` を記録します。差の符号は `observed - expected` と固定します。比較対象は pipeline の生 C 行数ではなく、duplicate 処理後の `len(txns)` です。

- `orchestrator/verifier/model.py:132`–`150`

  `Integrity` に次の2フィールドを追加します。

  ```python
  expected_commits: Optional[int] = None
  observed_commits: Optional[int] = None
  ```

  `clean()` へ次の条件を追加します。

  ```python
  (
      (self.expected_commits is None and self.observed_commits is None)
      or (
          self.expected_commits is not None
          and self.observed_commits == self.expected_commits
      )
  )
  ```

  片方だけ設定された不整合も unclean にします。第三の `delta` フィールドは持たず、二重管理を避けて出力時に導出します。

- `orchestrator/verifier/model.py:201`–`203`

  `VerifyResult.certified` 本体は変更不要です。既に `self.integrity.clean()` を必須にしているため、新条件が自動的に配線されます。ここへ別の commit-count 判定を重複実装しません。

- `orchestrator/verifier/report.py:42`–`75`

  現行辞書をまず同じ key・順序で構築し、その後、witness がある場合だけ次を追加します。

  ```json
  "integrity": {
    "...existing keys...": "...",
    "commit_witness": {
      "expected": 2,
      "observed": 1,
      "delta": -1
    }
  }
  ```

  witness がない場合は `commit_witness` 自体を挿入しません。既存 key の値・順序・`notes` も変えないため、同じ JSON serializer を通した bytes は現行と同一です。

- `orchestrator/verifier/report.py:95`–`115`

  witness がある場合だけ text report に `expected / observed / delta` を表示します。witness なしの text 出力は不変です。

- `orchestrator/verifier/parse.py:197`–`226`

  変更不要です。`max(txid)+1` は内部欠番の検査として残し、末尾欠番だけを外部 witness が補完します。stdout の解釈を trace parser に混ぜません。

### pipeline

- `orchestrator/campaign/pipeline.py:26`付近

  `from ..calibrator.benchparse import parse_bench_stdout` を追加します。依存方向は既存の `campaign → calibrator` と同じで、`benchparse.py` は typing 以外へ依存しないため循環しません。

- `orchestrator/campaign/pipeline.py:218`–`227`

  新しい regex は作りません。`parse_bench_stdout()` で stdout を一度辞書化し、pipeline 内の小さな helper で `commit_counts_` と `batch_commit_counts_` を非負整数へ変換します。欠落・非整数・負数はいずれも `None` です。

  既存 `_ABORT_COUNTS_RE` / `_parse_abort_counts` は `s2_verify_calibration.py:58` からも使われているため、そのまま残します。

- `orchestrator/campaign/pipeline.py:257`–`285`

  `_run_trace` の返り値を次の5-tupleにします。

  ```text
  (
      trace_c_lines,
      returncode,
      abort_counts,
      commit_count_witness,
      batch_commit_count_witness,
  )
  ```

  型は概ね次です。

  ```python
  tuple[int, int, Optional[int], Optional[int], Optional[int]]
  ```

  `proc.stdout` とその run の `trace_dir` を同じ関数内で束ねるため、別 run の witness を誤結合しません。

- `orchestrator/campaign/pipeline.py:853`–`881`

  5-tuple を展開し、既存の `rc != 0`、空 trace、abort count 欠落の拒否後に以下を追加します。

  - main または batch witness の欠落・不正:
    - abort reason: `trace-no-commit-witness`
  - `batch_commit_counts_ != 0`:
    - abort reason: `trace-batch-commits-unattributed`

  両者の WAL payload field は共通して次にします。

  ```json
  "commit_witness": {
    "commit_counts": 123,
    "batch_commit_counts": 0
  }
  ```

  既存 `"commits"` は trace の C 行数として残し、意味を変更しません。

- `orchestrator/campaign/pipeline.py:881`

  必須結線は次です。

  ```python
  vr = verify_trace_dir(tdir, expected_commits=commit_count_witness)
  ```

  pipeline 自身では C 行数との一致を重複判定せず、比較責務は verifier 一箇所にします。

- `orchestrator/campaign/pipeline.py:886`–`903`

  `STAGE_VERIFY_DONE` payload にも同じ `commit_witness` field を追加します。不一致時の abort payload には、`result_to_dict(vr)` 由来の `integrity.commit_witness` が期待・観測・差を保持します。

### batch commit の裁定

`batch_commit_counts_` は加算しません。与えられた構造的同値は silo/YCSB の通常 `tx.commit()` と `commit_counts_` に対するものであり、batch path が C 行を一件ずつ出すことや通常 counter と排他的であることは確認されていません。加算は未証明の対応関係を正しさゲートへ持ち込むため、非ゼロなら帰属不能として fail-closed にします。

### 全 consumer

- `orchestrator/campaign/pipeline.py:853`–`881`
  - 5-tuple 展開、欠落・batch guard、witness keyword の追加。
- `orchestrator/campaign/p3_s4_red.py:103`–`117`
  - fixture の返り値を `(n, 0, 1, n, 0)` に変更。注入 trace 自身の完全な count を witness とします。
- `orchestrator/tests/test_campaign.py:5137`–`5150`
  - `_mock_pipeline` の `fake_trace` を5値化。
  - `verify_trace_dir` の fake は `expected_commits` keyword を受けられる signature にする。
- `orchestrator/tests/test_campaign.py:6077`–`6085`
  - 実 `_run_trace` の展開と期待値を5値化。
- `orchestrator/tests/test_campaign.py:6534`–`6547`
  - 既知リストから漏れていた multipass fixture も5値化。
  - `fake_verify` も witness keyword を受け、必要なら渡された値を記録する。
- `orchestrator/tests/test_campaign.py:5870`、`orchestrator/tests/test_build_site_gate.py:380`
  - 返り値を利用しない直接呼び出し。signature は変えないので変更不要。
- `orchestrator/campaign/s3_lock_coverage.py`、`s5_permutation_coverage.py`、`s8a_trigger_coverage.py`
  - 同名の別関数であり変更不要。

### `verify_trace_dir` の4系統

- `campaign/pipeline.py:881`: witness を必ず渡すよう変更。
- `campaign/silo_ladder_rung1.py:2842`–`2844`: 変更不要。witness なしを維持し、凍結 verifier JSON を変えない。
- `verifier/cli.py:28`–`51`: 変更不要。複数ディレクトリと単一数値の対応が曖昧で、pipeline 修正にも不要なため新 flag を設けない。
- テスト群: 既存呼び出しは原則変更不要。反転テストと新 control だけ明示的に `expected_commits=` を渡す。

実装面は新規ファイルなし、production 5ファイル＋test 2ファイルの計7ファイル、概算150～210編集行です。`external/ccbench`、gitlink、承認定数、凍結成果物には変更がありません。

## 2. 受理集合の before/after

現行 verifier の認証条件を `Old(T)` とすると、

```text
Old(T) =
  nonempty(T)
  ∧ serializable(T)
  ∧ existing_integrity_clean(T)
```

変更後は次です。

```text
New(T, None) = Old(T)

New(T, E) =
  Old(T)
  ∧ unique_committed_txns(T) == E
```

したがって、どの witness 付き入力でも `New(T,E) ⇒ Old(T)` です。witness なしでは完全同値なので、新たに受理される入力はありません。

pipeline 全体では、現行条件へさらに次を conjunction として追加します。

```text
commit_counts_ が非負整数
∧ batch_commit_counts_ が非負整数
∧ batch_commit_counts_ == 0
∧ len(parsed_txns) == commit_counts_
```

新たに拒否されるものは次です。

- 最大 txid 側の committed txn が丸ごと失われ、残存 txid が密連番に見える trace。
- thread trace file 丸ごとの欠落。
- trace C 行数が stdout counter より多い破損。
- main または batch witness 行の欠落・不正値。
- `batch_commit_counts_ != 0` の帰属不能 run。

変わらないものは次です。

- 完全な trace、正しい `commit_counts_`、batch 0。
- cycle、内部 txid gap、duplicate C、version mismatch、malformed key 等による既存拒否。
- nonzero exit、空 trace、abort count 欠落、parse error による手前の拒否。
- FN-2。C 行が残り R/W だけ失われた場合、commit count は一致するので本 wave では検出されません。

規律2に照らした緩和はありません。既存条件を削らず、新条件を積むだけです。

ただし、全 API を対象に「witness なしの fail-open が消えた」とは示せません。互換性要件により、直接 API、CLI、silo-ladder の no-witness 呼び出しでは FN-1 の旧挙動が残ります。構造的に閉じられるのは現在の `pipeline.evaluate` 経路です。この経路は、有限な唯一の production call site `pipeline.py:881` の直前で witness 欠落と batch 非ゼロを拒否し、非 `None` の値を keyword で渡します。

なお mismatch と cycle が同時にある場合、`model.py:194`–`197` の優先順位により verdict は従来どおり `non-serializable` です。`certified=False` は常に成立し、FN-1 のように残存 DSG が acyclic の場合は `indeterminate` になります。

## 3. テスト計画

この read-only 作業では pytest は実行していません。親実装時の計画は以下です。

### verifier controls

- 反転:
  - `orchestrator/tests/test_verifier.py::test_characterization_tail_txid_gap_is_indeterminate_with_commit_witness`
  - 現在の一件だけ残った trace に `expected_commits=2` を渡す。
  - `missing_txids == 0` は残し、旧検査では拾えないことを維持。
  - `serializable is True`、`verdict == "indeterminate"`、`certified is False`、expected=2、observed=1、delta=-1 を要求する。

- positive control:
  - `orchestrator/tests/test_verifier.py::test_commit_count_witness_detects_removed_trace_file`
  - 完全な2-file trace を作り、片方の trace file を削除してから元の witness 2を渡す。
  - mismatch 以外の integrity と DSG は緑にし、欠落注入だけで赤になるよう隔離する。

- negative control:
  - `orchestrator/tests/test_verifier.py::test_commit_count_witness_accepts_complete_trace`
  - 同じ2-file traceを削除せず、witness 2で `certified=True` を要求する。
  - 過剰拒否を直接検出する。

- 構造化結果:
  - `orchestrator/tests/test_verifier.py::test_commit_count_witness_result_is_structured`
  - `integrity.commit_witness == {"expected": 2, "observed": 1, "delta": -1}` を完全一致で固定する。

- no-witness bytes:
  - `orchestrator/tests/test_verifier.py::test_result_to_dict_without_commit_witness_is_byte_identical`
  - 安定した `trace_dir` 名に置換した結果を、現行と同じ JSON options で serialize し、inline の旧 bytes と完全一致させる。
  - integrity key の集合だけでなく値と順序も固定する。
  - 既存 `test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` の recorded-result 完全一致もそのまま通す。

- FN-2:
  - `test_characterization_txn_tail_loss_is_false_green` は期待値を変更しない。
  - コメントだけ「FN-1 は witness で分離、FN-2 は権限外」と更新する。

### pipeline controls

- `test_run_trace_parses_commit_witness_from_stdout`
  - stdout に abort/main/batch の3行を出し、5-tupleの各位置を完全一致で検査する。
  - main と batch のラベル取り違えも検出する。

- `test_pipeline_missing_commit_witness_rejects`
  - rc=0、非空、abortあり、batch=0、完全 trace とし、main witness だけ `None`。
  - reason が `trace-no-commit-witness`、VERIFY_DONE が無く、COMMIT/fitness が無いことを要求する。

- `test_pipeline_missing_batch_commit_witness_rejects`
  - main は正しく、batch だけ `None`。同じ fail-closed reason を要求する。

- `test_pipeline_nonzero_batch_commits_rejects`
  - main witness と trace count は一致させ、batchだけ1にする。
  - reason `trace-batch-commits-unattributed` を要求する。

- `test_pipeline_tail_loss_witness_reaches_verifier`
  - trace C 行数1、stdout main witness2、batch0。
  - pipeline の手前条件はすべて通し、実 verifier により `indeterminate` abort になることを要求する。

- `test_pipeline_matching_commit_witness_commits`
  - 完全 trace、main一致、batch0で従来どおり COMMIT。
  - witness 導入による過剰拒否の pipeline-level negative control。

- `test_pipeline_verify_payload_records_commit_witness`
  - VERIFY_DONE と欠落/batch abort の WAL に、`commit_witness` の完全な値があることを固定する。

### 既存 helper 群

既存 `_tmp_trace` 利用25件は、反転対象以外を `verify_trace_dir(d)` のまま維持します。緑を保つ条件は次の三つです。

- `expected_commits=None` の既定値。
- `Integrity` の両フィールドが `None` なら `clean()` の新条件が恒真。
- `result_to_dict` が witness key を一切追加しない。

既存の赤・ParseError テストも判定を緩めず、そのままです。なお `_tmp_trace` の実定義は `test_verifier.py:195` であり、依頼文にある「20～40行」は `FIX` と `_verify` の範囲だけでした。

## 4. 親 brief の誤り・飛躍

- `brief.md:23`–`24`

  「不一致なら indeterminate」は FN-1 の対象入力には正しいものの、一般には不正確です。現行 `VerifyResult.verdict` は cycle を integrity より先に判定するため、mismatch と cycle が共存すれば `non-serializable` のままです。普遍なのは `certified=False` です。

- `brief.md:50`–`52` の P1

  witness が T marker より「強い」という表現は範囲が広すぎます。whole-txn omission、suffix loss、thread-file lossには強い一方、FN-2、count-preserving corruption、別 run の stdout 誤結合は検出しません。「通常 commit の個数完全性について強い」と限定すべきです。機構自体は、与えられた silo/YCSB 不変条件の下では妥当です。

- `brief.md:53`–`55` の P2

  主方針は妥当ですが、返り値 consumer の影響列挙が不足しています。`test_campaign.py:6534` の multipass fixture も3-tupleを返しており、更新必須です。既知事実に挙げられた `:5145`、`:5870`、`:6067` だけでは取り残します。

- `brief.md:60`–`63`

  「部分 trace が certified」という記述は条件付きです。内部 txid gap、duplicate、残存 cycle等があれば現行でも拒否されます。偽緑になるのは、欠落後の残存 txid が `0..max` に見え、既存 integrity が clean で、残存 DSG が acyclic な場合です。

- `brief.md:80`–`82`

  引用された evidence test が直接証明するのは deserialize 後の辞書完全一致であり、JSON whitespace・key orderまで含む literal byte equalityではありません。今回の上位制約はさらに強いので、専用 byte regression を追加して両方を守るべきです。

- `brief.md:83`–`84`

  「optional 側が fail-open にならない保証」は論理的に成立しません。no-witness 出力を現行同一にする以上、直接 API・CLI・silo-ladder の旧 FN-1 は残ります。pipeline acceptance pathだけが必須化される、と限定する必要があります。

P3の「FN-2を本 waveで実装しない」は、与えられた gitlink・承認定数・権限境界と整合しており、訂正不要です。

## 5. 変異候補

| # | file:line・一行変異 | 落ちるテスト nodeid | 隔離性 |
|---|---|---|---|
| 1 | `verifier/core.py:19`付近: 比較右辺の `expected_commits` を `len(txns)` に置換し、現行 `parse.py:217`–`223` だけを残す | `test_verifier.py::test_characterization_tail_txid_gap_is_indeterminate_with_commit_witness` | wave前の実コードと同型。入力は密連番・acyclic・他 integrity clean なので、この比較以外に拒否層なし。 |
| 2 | `verifier/model.py:144`–`150`: `clean()` から commit-count 一致節を削除 | `test_verifier.py::test_commit_count_witness_detects_removed_trace_file` | direct verifier 入力で他違反なし。赤理由は witness mismatch の無視だけ。 |
| 3 | `verifier/model.py:201`–`203`: `certified` から `self.integrity.clean()` を削除 | `test_verifier.py::test_commit_count_witness_detects_removed_trace_file` | 残存 DSG は acyclic・非空。certified の integrity bypass だけで偽緑になる。 |
| 4 | `verifier/report.py:58`–`75`: `commit_witness` を witnessなしでも無条件挿入 | `test_verifier.py::test_result_to_dict_without_commit_witness_is_byte_identical` | 判定層を通さない直列化テスト。失敗理由は旧 bytes/key shape の破壊だけ。 |
| 5 | `verifier/report.py:58`–`75`: `delta` を `expected - observed` に反転 | `test_verifier.py::test_commit_count_witness_result_is_structured` | verdict は同じで、完全一致 assertion の delta 符号だけが赤になる。 |
| 6 | `campaign/pipeline.py:257`–`285`: `_run_trace` の4番目返り値を stdout witness でなく `n` にする | `test_campaign.py::test_run_trace_parses_commit_witness_from_stdout` | producer 単体テストで、後段拒否は存在しない。独立 witness が trace 自己申告へ退化した一点だけを検出。 |
| 7 | `campaign/pipeline.py:872`付近: `trace-no-commit-witness` guard を `if False` にする | `test_campaign.py::test_pipeline_missing_commit_witness_rejects` | rc=0、非空、abortあり、batch0、完全 trace。guard 後は optional API が旧緑になるため他の拒否層なし。 |
| 8 | `campaign/pipeline.py:880`付近: batch 非ゼロ guard を `if False` にする | `test_campaign.py::test_pipeline_nonzero_batch_commits_rejects` | main witnessをtraceと一致させるので、guardを抜けると verifier は緑。他層による重複拒否なし。 |
| 9 | `campaign/pipeline.py:881`: `expected_commits=commit_count_witness` keyword を削除 | `test_campaign.py::test_pipeline_tail_loss_witness_reaches_verifier` | 手前はすべて正常。no-witness verifierだけが旧偽緑になり、結線欠落に理由を一意化できる。 |
| 10 | `campaign/pipeline.py:257`–`285`: main と batch の返り値順を交換 | `test_campaign.py::test_run_trace_parses_commit_witness_from_stdout` | `_run_trace` 単体の5-tuple完全一致だけで検出し、後段 reason の競合を避ける。 |
| 11 | `verifier/core.py:19`付近: mismatch 条件を `observed != expected` から `observed == expected` に反転 | `test_verifier.py::test_commit_count_witness_accepts_complete_trace` | 正しい完全 trace を赤にする過剰拒否変異。direct verifierで他の拒否層はなく、新条件だけが失敗原因。 |

重複した拒否層に隠れる変異、例えば「batchをmainへ加算するが、後段のcount mismatchでも結局拒否される」形は登録しません。abort reasonだけを狭く assertして見かけ上 kill するのではなく、guardを無効化すると本当に偽緑になる入力へ限定しています。

## 総括

最小で安全な形は、optional witness を `Integrity` に保持し、no-witness の直列化を完全不変にしたうえで、pipelineだけを availability・batch帰属・count一致の三段で必須化する設計です。production pipeline の受理集合は厳密に縮小しますが、互換性上、直接 API・CLI・silo-ladder の no-witness FN-1は残ります。変更は7ファイル・概算150～210行、新規 module・schema version・CCBench変更なしです。