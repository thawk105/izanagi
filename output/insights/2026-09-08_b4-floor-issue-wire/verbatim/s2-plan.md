## プラン

1. 権威 floor 成果物の schema と発行経路

新設: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_floor_artifact_issuer.py`

想定する行構成と責務:

- 新設 `:1-70`: B-4 専用の定数、型、例外。
  - `B4_FLOOR_ARTIFACT_SCHEMA_VERSION = "p3-b4-authoritative-floor/v1"`
  - `B4_FLOOR_ADOPTION_SCHEMA_VERSION = "p3-b4-floor-adoption/v1"`
  - `GENERATOR_IDENTITY = "orchestrator/campaign/p3_b4_floor_artifact_issuer.py"`
  - `ROUNDING_ID = "nextafter-positive-infinity-binary64/v1"`
- 新設 `:71-175`: duplicate key、非有限値、非 canonical JSON、symlink、repo 外 path を拒否する共通 loader。
- 新設 `:176-270`: `floor-pair-summary/v2` と採用記録の B-4 専用検証。
- 新設 `:271-315`: float から exact ratio への変換。
- 新設 `:316-405`: authority JSON の構築、canonical serialization、create-only 発行。
- 新設 `:406-500`: authority artifact の loader と事前登録 §5 resolver。
- 新設 `:501-550`: CLI。入力は `--repo-root`、`--summary`、`--adoption-record` だけとし、`--floor`、floor の既定値、caller 指定の出力 filename は作らない。

issuer が要求する入力は次の二つだけにする。

- `floor-pair-summary/v2`:
  - exact schema/format
  - `status == "generated"`
  - `candidate_floor` が exact Python `float`、有限、`0 <= value < 1`
  - `upper == candidate_floor`
  - `spec_relpath` / `spec_sha256` / `loaded_head` / `plan_sha256`
  - `window_artifacts`、`campaigns[].campaign_id`、derivation を含む現行 top-level field set
  - raw summary bytes の SHA-256
- create-only で事前作成された `p3-b4-floor-adoption/v1`:
  - `decision_id = D<正整数>`
  - `adopted_summary = {path, sha256}`
  - `artifact_directory`
  - `artifact_identity = {env_tag, protocol, threads, workload_identifier, campaign_identifier}`
  - floor 値そのものは持たせない。

authority JSON は少なくとも次を持つ。

- schema と generator identity
- `floor_exact = [numerator, denominator]`
- source float の `float.hex()` と `as_integer_ratio()`
- 丸め algorithm、方向、precision、丸め後 ratio
- summary の path、raw SHA-256、schema/status、spec/head/plan/campaign binding
- 採用記録の path、raw SHA-256、`decision_id`
- 5 要素の `artifact_identity`

filename は caller に渡させず、採用記録の directory と identity から次の形で組み立てる。

`b4-floor__env-<env_tag>__protocol-<protocol>__threads-<threads>__workload-<workload_identifier>__campaign-<campaign_identifier>.json`

`env_tag` 等は安全な canonical ID、`threads` は正整数だけを許す。複数 workload/campaign をまとめる場合の identifier の正しさは D1696 どおり採用記録作成者の人手責任とし、issuer が spec との意味的一致 validator を新設しない。

canonical bytes を同一 directory の一時 regular fileへ書いて fsync し、hard-link の create-only publish、directory fsync、temporary unlink の順で発行する。既存 target は変更しない。内容 SHA-256 は canonical bytes から計算し、`B4AuthoritativeFloorWrite` と CLI の canonical result に `artifact_path` / `artifact_sha256` として返す。後続 §5 記入はこの二値を転記する。

新設 test: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`

- 新設 `:1-110`: summary/adoption fixture。
- 新設 `:111-180`: 実 `floor_pair_driver.finalize_floor()` が出した summary を issuer が受け取れる integration test。
- 新設 `:181-250`: exact ratio、1 ULP 切上げ、0 近傍、1 への切上げ拒否。
- 新設 `:251-350`: schema/status/hash/adoption 欠落、改変、unknown key の拒否。
- 新設 `:351-430`: filename 5 要素、content hash、create-only collision、symlink 拒否。
- 新設 `:431-500`: §5 sentinel、正常 pin、hash 不一致、missing artifact、重複 floor 行の resolver test。

2. exact 変換

新 issuer `:271-315` でだけ変換する。規則は次とする。

1. strict JSON loader が得た `candidate_floor` を exact binary64 float として検証する。
2. `source_ratio = candidate_floor.as_integer_ratio()` を記録する。
3. `rounded = math.nextafter(candidate_floor, math.inf)` とする。
4. `rounded.as_integer_ratio()` を既約な `[numerator, denominator]` として authority artifact に置く。
5. `rounded >= 1` なら clamp や切下げをせず、`floor_rounding_out_of_domain` で発行しない。

precision は「入力 binary64 における直上 1 ULP」、丸め方向は正の無限大側である。decimal 桁数を恣意的に決めず、source/rounded の hex と exact ratio を残すため loader が変換を再計算できる。

この向きが規律 2 に沿う理由は、凍結 evaluator が `gain_difference <= floor` を tie にするからである。floor を直上へ動かせば、元の floor で tie だった block は必ず tie のままで、追加で一部の境界 block が tie になるだけである。非 tie と方向性の証拠を増やさず、成立・不成立の主張を強めない。逆に `nextafter(candidate_floor, -inf)` のように小さくすると、`rounded_floor < D <= candidate_floor` の block が tie から勝敗へ変わり、非 tie 数と片側検定の信号を増やして、いずれかの方向の主張を本来より通しやすくしうる。

3. §5 からの解決と report 配線

[p3_b4_material_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_material_report.py:1) を次の位置で変更する。

- 現行 `:1-7`: 「常に `floor=None`」という docstring を、§5 sentinel 時は従来経路、pin があるときだけ authority を読む説明へ更新。
- 現行 `:30-45`: 新 issuer module の `B4AuthoritativeFloor`、typed error、resolver を import。
- 現行 `:107-115`: `B4MaterialReportInputs` に `authoritative_floor: B4AuthoritativeFloor | None` を追加。
- 現行 `:201-257`: `_load_and_evaluate()` が repository 内の固定 preregistration pathを resolver に渡す。§5 が sentinel なら従来どおり `None`、正常 pin なら `Fraction` を現行 `evaluate_b4_artifacts()` の `floor` 引数へ渡す。public 関数の引数は増やさない。
- 現行 `:814-919`: 現在の `_build_report_value()` を absent 用 legacy composer として保持する。新しい present-only helper がその戻り値の既存 fieldだけを次のように射影する。
  - `analysis.floor_argument = [numerator, denominator]`
  - `floor.availability = "present"`
  - `floor.source = {artifact_path, artifact_sha256, schema_version, generator_identity, decision_id}`
  - `floor.value = [numerator, denominator]`
  - `report_scope.floor_availability = "present"`
  - `expected_analysis_* = "not_fixed_by_floor_presence"`
  - `kind = "evidence-only"`、`preregistration_section_5 = "not_in_effect"`、4 分類 operationalized は `False` のまま
  - present branchだけ `authoritative_floor_artifact` を `not_guaranteed` から除き、checked に加える。
- 現行 `:922-953`: present branch の floor/source/hash/analysis argument が resolver 結果と exact 一致する独立 assertion を追加。
- 現行 `:973-1068`: 既存 `_render_markdown()` は absent 用として保持。present-only renderer は旧 bytes の `- floor: unavailable` 1 行だけを exact ratio と artifact path/hash の行へ置換する。
- 現行 `:1071-1097` と `:1392-1424`: authority の有無で legacy/present composer・renderer を選ぶ。
- 現行 `:1427-1447`: CLI surface は変更しない。`--floor`、`--floor-artifact`、その既定値を追加しない。

resolver が読む preregistration は module 位置から一意に決まる repository root の
`docs/phase3-b4-reflux-ablation-preregistration.md` だけとする。floor 行の値は次の exact grammar とする。

`artifact_path=<canonical repo-relative path>; sha256=<64 lowercase hex>`

挙動は以下で固定する。

- exact sentinel `未記入`: authority 不在。report は従来 bytes/verdict 経路。
- sentinel のまま別場所に artifact が存在: 探索せず不在。
- non-sentinel の malformed 値、missing file、hash 不一致、schema/conversion 不一致: fail closed。`None` へ読み替えない。
- caller が artifact path や floor を指定する経路は作らない。

4. 不在時の非退行 test

既存 test が守っている範囲は次のとおり。

- [test_p3_b4_material_report.py:635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/tests/test_p3_b4_material_report.py:635): floor public 引数の不在、floor/report_scope の exact object、`floor_argument is None`、`protocol_violation`、理由 `floor_domain_error`。
- [同:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/tests/test_p3_b4_material_report.py:184): assembly rejection 時の exact analysis projection。
- [同:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/tests/test_p3_b4_material_report.py:419): 402 行の完全射影と canonical JSON bytes。
- [同:1006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/tests/test_p3_b4_material_report.py:1006): CLI 再実行が既存 JSON/Markdown bytes を変えないこと。

ただし、現状は「変更前の report 全 bytes」と比較する test がない。現行 `:635-660` 直後へ次を追加する。

- `test_absent_authority_is_byte_identical_to_legacy_composer`: sentinel resolver の public build結果を、変更せず残した `_build_report_value()`、`_render_markdown()`、`_canonical_json_bytes()` から独立に組んだ legacy bytes と JSON/Markdown の両方で exact 比較する。verdict と invalid reason も再確認する。
- `test_resolved_authority_passes_exact_fraction_without_public_floor_surface`: evaluator wrapper が受けた値の型と ratio、report の floor/analysis projection を検査する。
- `test_non_sentinel_authority_failure_does_not_fall_back_to_absence`: missing/tampered authority は report error になり、evidence-only absent reportを発行しない。

同 test module は file 全体が xdist group なので、[test_real_repo_serialization.py:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/tests/test_real_repo_serialization.py:282) の `_P3_B4_MATERIAL_REPORT_NODES_GOLDEN` に上の node id を追加する。

5. 触らない面

以下は変更しない。

- [p3_b4_analysis_path.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_analysis_path.py:67) の `_SOURCE_CLOSURE_PATHS`
- [p3_b4_analysis_prereg_consumer.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:98) の `_CLOSURE_PATHS`
- `p3_b4_analysis_contract.py` 全体
- preregistration doc 全体
- `floor_pair_driver.py` 全体
- [p3_b4_material_report.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_material_report.py:48) の既存 `SCHEMA_VERSION`
- [同:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_material_report.py:49) の既存 `GENERATOR_IDENTITY`

新 issuer は分析 5 module の外に置き、両 closure tuple へ追加しない。report v1 は既に floor availability/source/value を持つため、field set を増やさず present variantを使う。仮に v1 の型制約が別途見つかった場合の代案は「present branchだけ別 schema 定数、absent branchは現行 v1 bytesを維持」であり、既存 `SCHEMA_VERSION` の一括 bump は採らない。

6. 段 5 の二単位

A — issuer:

- 新設 `orchestrator/campaign/p3_b4_floor_artifact_issuer.py`
- 新設 `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`

責務は summary/adoption の検証、1 ULP 切上げ exact 化、5 要素名の構築、create-only 発行、artifact loader、§5 resolver まで。

B — 配線と report 射影:

- `orchestrator/campaign/p3_b4_material_report.py`
- `orchestrator/tests/test_p3_b4_material_report.py`
- `orchestrator/tests/test_real_repo_serialization.py`

B は A が公開する `resolve_preregistered_authoritative_floor()` と immutable result typeだけを利用する。A/B の編集 file は重ならない。`floor_pair_driver.py`、事前登録 doc、分析 closure はどちらも編集しない。

## 根拠

- 現 producer は [floor_pair_driver.py:2688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/floor_pair_driver.py:2688) で `floor-pair-summary/v2` を作り、`:2696-2698` に status/upper/candidate_floor、`:2699-2704` に window/campaign/derivation を持つ。`:2713-2721` は summary を exclusive-create し raw bytes の SHA-256 を返す。
- `candidate_floor` の型は [同:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/floor_pair_driver.py:325) で float、設定箇所は [同:2683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/floor_pair_driver.py:2683)。
- 凍結契約は [p3_b4_analysis_contract.py:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_analysis_contract.py:233) で float/Decimal を拒否し、int/Fraction/int ratio だけを受ける。`:323-325` は不在または値域外を `floor_domain_error` にする。
- tie 判定は [同:525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_analysis_contract.py:525) の `gain_difference <= exact_floor` なので、floor の増加が保守側になる。
- 現 report は [p3_b4_material_report.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_material_report.py:242) で明示的に `floor=None` を渡し、`:829-874` で不在を report に射影している。
- 事前登録は [phase3-b4-reflux-ablation-preregistration.md:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/docs/phase3-b4-reflux-ablation-preregistration.md:438) で floor を「§5 の凍結 artifact から読み、引数で渡す」と定め、`:491-494` で境界を tie に含める。
- §5 の現物は [同:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/docs/phase3-b4-reflux-ablation-preregistration.md:162) が sentinel。§11 は [同:895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/docs/phase3-b4-reflux-ablation-preregistration.md:895) で、docを読む接続がまだ無いことを明記している。
- D1641 は [rulings-verbatim.md:122](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/rulings-verbatim.md:122) で create-only JSON、名前の5要素、§5への content SHA-256 転記を確定している。
- D1696 は [同:191](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/rulings-verbatim.md:191) で成果物名を含む9項目の validator 拡張を却下している。そのため identity は採用記録へ束ねるが、specとの意味的一致を新 validator にしない。
- §11.3 は [preregistration:1047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/docs/phase3-b4-reflux-ablation-preregistration.md:1047) で report 接続を別実装とし、`:1049-1053` で floor 行だけでは本書も4分類も発効しないと限定している。

## 危険と限界

- 1 ULP 切上げが保証するのは「summary に記録された binary64 float より小さくしない」ことだけである。raw throughput を実数または exact rational で再計算した真の上限を覆う証明ではない。
- source float が `1` の直前なら切上げ結果は `1` となり、issuer は発行を拒否する。clamp はしない。
- 採用記録の `env_tag`、protocol、threads、workload/campaign identifier が実 spec と意味的に一致するかは D1696 どおり人手責任である。issuer は canonical shapeと束縛だけを検査する。
- §5 の exact cell grammar と後続の §5 記入 wave が一致しなければ resolver は fail closed する。doc は本 wave で編集しないため、この interface を後続担当へ明示する必要がある。
- authority issuer 自体は意図的に分析 source closure の外であり、5 module closure receiptは issuer sourceを証明しない。§5 の artifact hashとgenerator identityが別の束縛になる。
- report は floor を利用できても certification や preregistration 全体の発効を主張しない。
- `_load_and_evaluate` の AST callsiteを参照する [test_p3_b4_producer_auth_experiment.py:791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:791) があるため、evaluator callを別関数へ移したり複数回呼んだりしない。
- read-only 条件に従い、編集・pytest 実測は行っていない。

## 総括

採用案は「実 summary + 採用記録 → binary64 直上 1 ULP の exact ratio → create-only authority JSON」である。  
report は §5 の固定行からだけ解決し、sentinel 時は現在の legacy composer/rendererをそのまま通す。  
欠損した pin を不在へ読み替えず、caller の floor/artifact 自己申告口も作らない。  
分析契約、closure tuple、事前登録 doc、driver、既存 report schema/generator identity は非改変。  
A=issuer、B=report配線で編集 file は完全に分離できる。