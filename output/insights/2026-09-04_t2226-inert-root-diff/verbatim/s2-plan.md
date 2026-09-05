## 変更計画

- `orchestrator/campaign/condition_meaning_gate.py:28-45`
  - `difflib` を追加する。
  - 公開 API や `__all__` (`4009-4027`) は変更しない。

- `orchestrator/campaign/condition_meaning_gate.py:2248`、`_preprocess_evidence` の直後かつ `_collect_supply_preprocess_pair` の直前
  - inert 専用の private helper `_classify_stock_inert_preprocess_difference` を追加する。
  - 入力は requested/control の元 `bytes`、source root 対応、build root 対応。
  - 戻り値は差分区間数、実際に使った root 対応、残差の有無とする。一般化した path 正規化 utility にはしない。

- `orchestrator/campaign/condition_meaning_gate.py:2391-2462`、`evaluate_define_supply_effectuation`
  - `2391-2408` の evidence 作成、compiler identity、comparable argv 検査は従来どおり先行させる。
  - 現在の root builtin 判定 `2409-2433` を分岐後へ移し、非 inert 分岐だけで実行する。
  - 変更後の判定順序は次のとおり。

    1. `2396-2402` 相当: compiler path/version drift は赤。
    2. `2403-2408` 相当: comparable argv drift は赤。
    3. 非 inert の場合:
       - 現在の `2409-2433` 相当の `preprocess-root-dependent-builtin` 判定。
       - 現在の `2435-2440` dependency closure equality。
       - 現在の `2441-2451` bytes difference 判定。
       - 順序、reason code、受理集合は変えない。
    4. inert の場合:
       - requested/control の元 `preprocessed_bytes` が完全一致なら、現在の `2458-2462` と同じ `stock-inert-preprocess-identical` green。root 分類には入らない。
       - 不一致かつ `root_dependent_builtin_paths` の和集合が空なら、分類不能として `stock-inert-mismatch` red。
       - 非空なら helper で行差分を分類し、分類 evidence を `evidence` に追加する。
       - 差分区間の全てが root 対応だけで完全一致し、実際の置換が1件以上なら、新 reason `stock-inert-preprocess-root-location-only` green。
       - 残差、insert/delete、曖昧な root 対応、置換ゼロのいずれかがあれば現在の `stock-inert-mismatch` red。

## 差分判定の設計

- 粒度は行単位とする。元 bytes に対して `splitlines(keepends=True)` を使い、改行 bytes と最終未終端行を保持する。`difflib.SequenceMatcher(..., autojunk=False)` の非 `equal` opcode を1差分区間として数える。
- `equal` 区間は元 bytes が既に完全一致しているので加工しない。各非一致区間についてのみ、requested 側の行列を結合した局所 bytes に置換を適用し、control 側の同区間の未加工 bytes と完全一致を要求する。
- 置換候補は次の一方向だけとする。

  - `requested source_root -> control source_root`
  - `requested build_root -> control build_root`

- requested 側 token の byte 長が長い順、同長なら kind の固定順で照合する。置換は元 requested 区間を左から一度だけ走査し、最長 token が一致した位置だけを出力 buffer に写し替える。置換後の control path を再走査しない。このため、control root が requested source root の子でも二重置換しない。
- control 側への置換、逆方向置換、両出力全体の正規化は行わない。
- `replace` opcode は置換後 requested 区間と元 control 区間を byte-for-byte 比較する。`insert` と `delete` は空でない側が残るため赤になる。
- どれか1区間でも完全一致しなければ `root_diff_has_residual=True` とする。1 byte の残差も許容しない。
- 元 bytes を加工しない保証は次の構造で持たせる。

  - `_PreprocessResult` は frozen dataclass (`628-646`) で、`preprocessed_bytes` 自体も immutable な `bytes`。
  - raw 完全一致判定と digest は分類前の元 bytes から行う。
  - helper は `splitlines` の結果から差分区間用の新しい bytes/output buffer だけを作る。
  - `_PreprocessResult.preprocessed_bytes`、requested/control digest、control bytes は書き換えない。
  - 新 green の `status_contract` は requested/control digest の不一致を必須にし、比較前に畳んだ実装を許さない。

## reason code と evidence schema

- 新 green reason code:
  - `stock-inert-preprocess-root-location-only`
- 対応する comparison:
  - `stock-inert-root-location-only`

- inert の raw 不一致を分類した record に次の3 fieldを追加する。greenだけでなく残差のある red recordにも残す。

  - `root_diff_interval_count`
    - exact `int`、1以上。`bool` は拒否する。
  - `root_diff_replacements`
    - exact `tuple`。
    - 各 row は exact 3-item `tuple[str, str, str]` の `(kind, requested_root, control_root)`。
    - `kind` は `"source"` または `"build"`、各 kind は重複不可、root は非空かつ相互に異なる。
    - 実際に差分区間内で使われた対応だけを、最長 requested-root bytes 優先の決定的順序で記録する。
  - `root_diff_has_residual`
    - exact `bool`。
    - 新 green では必ず `False`。負例の red では `True`。

- `orchestrator/campaign/condition_meaning_gate.py:3302-3323`
  - 現在の共通 `required` 25 field は維持する。
  - reason が新 reason のときだけ、上記3 fieldを `required` に加えてから、現在どおり missing/unexpected を exact 検査する。
  - 既存2 green reason の evidence key 集合は変えない。既存 record の canonical digest も不要に変えない。

- `orchestrator/campaign/condition_meaning_gate.py:3393-3398` の直後
  - 新 reason の場合に限り、3 field の exact type、値域、row shape、kind の一意性、順序を検査する。
  - requested/control の `root_dependent_builtin_paths` が両方空なら拒否する。
  - `root_diff_replacements` が空、または `root_diff_has_residual is not False` なら green evidence として拒否する。

- `orchestrator/campaign/condition_meaning_gate.py:3399-3412`
  - `status_contract` に次を追加する。
    - `stock-inert-preprocess-root-location-only -> ("stock-inert-root-location-only", False)`
  - 既存の以下2契約は変更しない。
    - `requested-default-preprocess-different -> ("requested-default-difference", False)`
    - `stock-inert-preprocess-identical -> ("stock-inert-identity", True)`

## 正例と負例

- `orchestrator/tests/test_condition_meaning_gate.py:142-153`
  - `_copied_fixture` の直後に inert root-diff 用 helper を追加する。
  - `_copied_fixture(tmp_path)` で `_SUPPLIED` 全体を `tmp_path/ccbench` へ copy する。静的 fixture は変更しない。
  - copied tree の次の両 header に、同一内容の行を追記する。

    - requested: `include/backoff.hh`
    - control: `stock/include/backoff.hh`
    - 追記内容: `static constexpr const char *condition_gate_backoff_file = __FILE__;`

  - これにより両方の dependency closure が code-owned `__FILE__` を記録し、意味は同じだが前処理 bytes には異なる source root が出る。

- `orchestrator/tests/test_condition_meaning_gate.py:598`、既存 `test_backoff_fixed_minus_one_stock_preprocess_identity_is_green` の直後
  - 正例 `test_inert_file_builtin_root_difference_is_green` を追加する。
  - copied fixture を `capture_define_inputs(root, stock_root=root/"stock")` へ渡し、`_request(-1, default=None, stock=True)` を評価する。
  - 次を検査する。

    - `green / stock-inert-preprocess-root-location-only`
    - comparison が `stock-inert-root-location-only`
    - requested/control digest は不一致
    - `root_diff_interval_count` は exact `int` で1以上
    - source root 対応が `root_diff_replacements` に存在
    - `root_diff_has_residual is False`
    - `_validate_arm_record_integrity` が通る

- 正例が本当に新機構を通ることは、production 変更前にこのテストだけを親が登録して実行し、現行 `condition_meaning_gate.py:2425-2433` により実値が `red / preprocess-root-dependent-builtin` となって新しい green 期待が失敗することを確認する。今回の read-only 段では実走せず、静的には `2062-2063` の検出と `2420-2427` の source-root needle がその赤経路を保証している。

- 正例の直後に負例 `test_inert_file_builtin_does_not_hide_nonroot_residual` を追加する。
  - 同じ copied fixtureと `__FILE__` 追記を使う。
  - control の `stock/include/backoff.hh` だけで
    `Backoff_.load(std::memory_order_acquire);`
    を
    `Backoff_.load(std::memory_order_acquire) + 1;`
    へ exact 1回置換する。
  - 意味差の行と直後の `__FILE__` 行を同一の連続差分面に置く。単に「差分区間に root があった」だけで区間全体を許す誤実装なら green になるため、次の期待で確実に落とせる。

    - `red / stock-inert-mismatch`
    - requested/control digest は不一致
    - source root 置換は実際に記録される
    - `root_diff_has_residual is True`

- 同じ挿入箇所に schema 負例を追加する。
  - 正例 record の evidence をコピーし、`root_diff_interval_count=True`、replacement を `list` 化、不正 kind、`root_diff_has_residual=0/True`、field 欠落を個別に作る。
  - `_public_arm_record` (`88-117`) で再構成し、`_validate_arm_record_integrity(..., require_issuer=False)` が `admission-contract-invalid` にすることを確認する。

- 既存の `test_backoff_fixed_minus_one_requires_stock_preprocess_identity` (`1265-1283`) は変更しない。root builtin が無い状態の意味差が引き続き `stock-inert-mismatch` になる回帰被覆として残す。

## 影響範囲

- `orchestrator/campaign/paper_story_a2_certification.py:606-612,657-672`
  - コード変更なし。
  - A-2 inert cell は新 reason の supply green を受け取る。`require_condition_gate_family` は status のみを見るため、そのまま admission green になる。

- `orchestrator/campaign/condition_meaning_gate.py:3707-3769`
  - 変更なし。特に `3743` の supply 判定は `terminal_status == "green"` のままで、新 reason の whitelist は追加しない。

- `tools/pegasus/probes/t316_sandbox_backend_probe.py:346-374`
  - 変更なし。`370-371` は引き続き raw bytes 完全一致の旧 reason/comparison だけを要求する。
  - 実 CCBench が新 reason になる場合、T316 固有の追加契約はそれを許可しない。T316 の受理拡張は本 brief の範囲外。

- `orchestrator/tests/test_t316_sandbox_probe.py:138-182`
  - 変更なし。使用 fixture には `__FILE__` がなく raw bytes が一致するので、`163-164` の既存期待は維持される。

- `orchestrator/tests/test_backoff_sweep.py:146-170`
  - 変更なし。同じく既存 fixture は raw bytes 一致で、`160-164` の期待は維持される。

- `orchestrator/tests/test_condition_meaning_gate.py:585-698`
  - 既存4件の inert green 期待は変更しない。いずれも `__FILE__` を追加しないため旧 reason のまま。
  - 新規正例、負例、schema 負例だけを追加する。

- `orchestrator/tests/test_condition_meaning_gate.py:1265-1283`
  - 既存 mismatch テストは変更せず、引き続き赤。

- 非 inert の全 consumer とテスト
  - reason code、判定順、受理・拒否は変えない。
  - `preprocess-root-dependent-builtin` を非 inert に残す。

- `orchestrator/tests/condition_gate_test_support.py` と `orchestrator/tests/fixtures/condition_meaning_gate/`
  - 編集しない。新 fixture は各テストの `tmp_path` 内だけで作る。

- `external/ccbench`
  - 編集しない。

## (P1) への回答

- (P1-1): 賛成。行単位 opcode とし、置換後に区間全体の byte 完全一致を要求するため、行より細かい残差も許可されない。
- (P1-2): 賛成。requested 側だけの一方向置換とし、最長一致、一回走査、置換結果の非再走査で親子 root の二重置換を防ぐ。
- (P1-3): 賛成。source root と同じ規則で requested/control build root も候補に含める。ただし evidence には実際に使った対応だけを記録する。
- (P1-4): 賛成。root-dependent builtin path が空なら location-only green にしない。さらに実際の root 置換がゼロの場合も赤にする。
- (P1-5): 賛成。新 reason `stock-inert-preprocess-root-location-only` を使い、旧 reason は digest equality 専用のまま維持する。
- (P1-6): 賛成。`preprocess-root-dependent-builtin` は非 inert 分岐へ移すだけで、同分岐内の順序と判定を維持する。
- 6項目とも採用するため、却下項目に対する代案はない。

## 総括

変更対象は `condition_meaning_gate.py` と `test_condition_meaning_gate.py` の2ファイルだけに限定する。元 bytes の直接比較を先に行い、不一致区間の requested bytes だけへ一方向 root 置換を適用し、各区間の完全一致を必須にする。新 green は digest 不一致、root-dependent builtin の存在、実置換、残差なしを exact evidence schema で束縛する。

この段ではコード編集も pytest 実走も行っていない。正例の現行赤は静的に確認済みで、test-first の赤確認と変更後の実測は親段で行う。