## 現行の候補選択挙動

現行の探索集合は次の形です。

- 直下集合 \(D\): [`calibration_dir.glob("*.json")`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:507>)。非再帰なので `calibration/registered/*.json` は含みません。
- pin \(P\): v2 lock の authority hash を [`resolve_by_contract_sha256`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/env_contract.py:881>) で ever-active 世代へ解決し、WAL の `env_tag` と一致すると [`calibration_ref`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:364>) を返します。v1 lock は `(None, None)`、env 不一致は候補なしです。
- 走査集合 \(S=D∪\{P\}\): pin は [`_validated_pin_path`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:393>) で repo 相対、対象 env directory 内、通常 file、SHA 一致を検査された後、[`path_sources`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:515>) へ加わります。直下由来は `True`、pin-only は `False` です。
- within-run 候補は \(S\) のうち `noise_floor` dict を持つ全 path です。[`_floor_protocol_and_basis`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:466>) と records / threads / workload / protocol の一致で選びます。
- between-run 候補は実質 \(D\) のうち `between_run` dict を持つ path です。pin-only path は [`kind == "between_run" and not path_sources[path]`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:549>) で除外されます。pin と直下 path が同一なら、直下由来として扱われます。
- `build_report` が pin を取得して `_calibration_floors` へ渡す接続点は [`layer3_report.py:827–836`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:827>) です。

| `contract_pin.status` | 書込み箇所 | 条件 |
|---|---|---|
| `candidate` | [`layer3_report.py:385–390`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:385>)、直接呼出し時の補完 [`:517–522`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:517>) | authority と campaign の env が一致し、未検証の pin 候補になった |
| `authority-env-tag-mismatch` | [`layer3_report.py:379–384`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:379>) | authority の env と WAL env が不一致 |
| `pin-file-missing` | [`layer3_report.py:523–524`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:523>) | canonical な配置先に file がない |
| `validated` | [`layer3_report.py:525–527`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:525>) | directory・file・SHA 検査を通過し、走査集合へ加わった |

## 宣言の置き場

| 候補 | γ-3 / γ-16 / AST 検査 | import 循環 | 単一出所化 | g1 削除時 |
|---|---|---|---|---|
| [`calibration_verify.py` の module 定数](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/calibration_verify.py:17>) | 契約 field ではないので γ-3、contract hash と無関係です。同 file は [`V2_ENV_NEUTRAL_MODULES`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_env_contract.py:83>) の免除なし対象ですが、追加する full path と SHA は、禁止される env_tag / clocks_per_us / numactl の値そのものではないため現行 AST 検査に抵触しません。primitive `(path, sha256)` だけなので「env-contract 型に依存しない leaf」も維持します。 | `layer3_report → calibration_verify → effective_clock_policy/schema_v2`。確認できる import edge に `layer3_report` への戻りはありません。`calibration_verify` も `env_contract` を import しません。 | `layer3_report.py` と `test_env_contract.py` が同じ定数を直接 import できます。 | g1 が registry から除去される T-419 U-1/U-2 で tuple 1 件を削除します。g2 が active になっただけで g1 が registry に残る間は、historical g1 lock のため削除しません。 |
| [`layer3_report.py` 自身](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:46>) | env contract の γ-3/γ-16 の対象外で、AST 対象一覧にもありません。path/SHA も禁止 literal ではありません。 | 自 module 定数なので循環なしです。 | consumer との局所性は最良ですが、`test_env_contract.py` が大きな report module とその依存閉包を import する逆向き依存になります。 | 定数要素を削除し、env-contract audit が空集合との一致を確認します。 |
| [`env_contract.py` の module 定数](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/env_contract.py:373>) | dataclass field ではなく実際に consumer が使うため γ-3 の直接違反ではなく、hash も変わりません。AST は full path/SHA を検出しません。ただし同 module のより強い方針「env 固有 literal は `_build_registry` 内だけ」[`env_contract.py:38–40`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/env_contract.py:38>) と、Pegasus path をその外へ置くことが文言上衝突します。builder 内から副作用的に公開する案も不自然です。 | `layer3_report` が既に `env_contract` を import しており、新しい循環はありません。 | `ec.KNOWN_...` として最も容易です。 | registry 編集と同じ file で削除できますが、上記 module 方針との摩擦が残ります。 |

推奨は `calibration_verify.py` です。`KNOWN_SELF_INCONSISTENT_CALIBRATIONS: frozenset[tuple[str, str]]` を [`GRANDFATHERED_V1_SHA256` の近傍](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/calibration_verify.py:17>) に置きます。較正の既知性を leaf に集約でき、契約型・registry・hash を変えず、`layer3_report` に effective-clock 再検査を導入しません。

## 変更案

| file:line | 変更内容 | なぜそれが D1537 を満たすか | 変更後に新しく候補から外れる pin / 変わらない経路 |
|---|---|---|---|
| [`calibration_verify.py:17–20`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/calibration_verify.py:17>) | `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` を `(path, sha256)` の `frozenset` として追加。要素は Pegasus g1 `calibration-753f535a8d024727.json` の 1 件だけ。loader や admission からは参照しない。 | 層 3 が実測を再実行せず、既知の exact bytes だけを識別できます。新 gate ではありません。 | 新たな除外対象は Pegasus g1 の exact pair だけ。g2、linux-baremetal、未登録の健全な pair は含めません。 |
| [`layer3_report.py:52–60`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:52>) | `calibration_verify` を import。 | production 宣言を唯一の判定元として消費します。 | `env_contract` の型・registry・activation 解決は不変です。 |
| [`layer3_report.py:500–528`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:500>) | `_validated_pin_path` は必ず従来どおり先に呼ぶ。成功した pin は従来どおり走査集合へ入れつつ、exact pair が宣言内なら `excluded_within_run_pin_path` として記録する。missing は従来の status のまま。 | 自己整合性の再検査なしで除外対象を識別しつつ、SHA 不一致・directory 外・非 file の fail-closed を短絡しません。 | 新規除外は Pegasus g1 の within-run 候補化だけ。`pin-file-missing`、SHA/path/file 拒否、健全な `validated` pin は不変です。 |
| [`layer3_report.py:541–568`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:541>) | kind 判定後、`kind == "within_run"` かつ path が記録済み除外 pin なら `candidates["within_run"]` へ append しない。既存の between-run 条件はそのまま残す。 | g1 bytes は検査・走査されても within-run の比較候補にならず、現行 Pegasus 系列では `no-matching-env-record` のままになります。 | 直下 record の候補形成、`genome-absent-legacy-record`、records / threads / workload / protocol 比較、重複一致拒否は不変。between-run の pin-only 除外も同じ行で不変です。 |
| [`layer3_report.py:595–610`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:595>) | within-run の detail を作るときだけ `contract_pin.status` を `self-inconsistent-awaiting-healthy-generation` に上書きする。path / sha256 キーは保持。between-run detail は `validated` のままにする。schema は編集しない。 | 一致なしの理由を既存 `contract_pin` object 内で明示し、schema キー集合を増やしません。 | 既存4 status の条件・値は不変。between-run の候補経路と status も不変です。 |
| [`layer3_report.py:364–390`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:364>) | `_contract_calibration_pin` は編集しない。 | authority 解決と `candidate` の意味を変えず、bytes 検証前に例外扱いしません。 | v1、env mismatch、unknown/never-active authority の経路は全て不変です。 |
| [`test_env_contract.py:39–67`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_env_contract.py:39>)、[`:856–944`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_env_contract.py:856>) | test-local literal 集合を削除し、`calibration_verify.KNOWN_SELF_INCONSISTENT_CALIBRATIONS` を参照。既存の集合完全一致 assert は維持。 | 宣言と実際の自己比較失敗集合が同じ production 出所へ束縛されます。 | audit の実測方法、g2 drift positive control、policy equality は不変です。 |
| [`env_contract.py:80–185`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/env_contract.py:80>)、[`:248–312`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/env_contract.py:248>) | 変更しない。 | contract field、世代、登録 ref の bytes/hash に影響させません。 | `contract_sha256`、`EXPECTED_GENERATION_HASHES`、activation record は全て不変です。 |

## テスト案

**正例**

| nodeid 案 | setup と assert |
|---|---|
| `orchestrator/tests/test_layer3_report.py::test_registered_healthy_pegasus_g2_pin_remains_selectable` | 実 registry の Pegasus g2 `calibration-94a4b79fa31bba3c.json` とその実 bytes を使います。g2 ref が production 宣言に含まれないことを assert し、tmp の `output/env/pegasus/calibration/registered/` へ bytes をコピーして、実 `_calibration_floors(..., contract_pin=g2.calibration_ref)` を呼びます。`within_run.provenance == "env-record"`、source path/SHA が g2 ref、値が実 record の `noise_floor`、`search_details["within_run"]["contract_pin"]["status"] == "validated"` を assert します。`resolve_by_contract_sha256` は never-active g2 を拒むため、activation は stub せず consumer seam を直接検査します。 |
| `orchestrator/tests/test_env_contract.py::test_registry_effective_clock_self_failures_are_exact_known_exception` | test-local literalを production import に置換したうえで、実 g1/g2 bytes、実 `expected_comparison_values`、実 `effective_clock_comparison_passes` を使い、`self_failures == calibration_verify.KNOWN_SELF_INCONSISTENT_CALIBRATIONS` を維持します。 |
| 既存 `test_linux_v2_keeps_direct_skew_zero_floor_in_addition_to_pin`、`test_floor_kinds_match_independently_and_classification_records_skips` | 無変更で残し、直下和集合と between-run の正例を維持します。`test_legacy_silo_within_floor_without_genome_states_match_basis` も無変更で `genome-absent-legacy-record` を固定します。 |

**負例**

| nodeid 案 | 変更する assert | 何が起きたら赤になるか |
|---|---|---|
| `orchestrator/tests/test_layer3_report.py::test_pegasus_v2_excludes_self_inconsistent_pin_and_registered_glob`（現 [`:3467`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3467>) を改名） | `within_run.value is None`、`provenance == "no-matching-env-record"`、`source is None`、`candidate_files == []`、within-run の pin status が新値、path/SHA が g1 ref。g2 file を同じ `registered/` に置いても glob 候補にならないことも維持。between-run の pin status は `validated` を assert。 | g1 が再び within-run 候補へ append され、CV `0.011705…` が出たら赤になります。 |
| `orchestrator/tests/test_layer3_report.py::test_nested_exploration_root_resolves_then_excludes_self_inconsistent_pin`（現 [`:3672`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3672>) を改名） | nested output root でも `value is None`、新 status、g1 path/SHA を assert。 | suffix 解決後の除外が nested root で抜け、g1 値が採られたら赤になります。 |
| 既存 `orchestrator/tests/test_layer3_report.py::test_contract_pin_sha_mismatch_fails_closed_before_floor_use` [`:3555`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3555>) | 期待値変更なし。改竄した g1 pin が `Layer3ReportError` の SHA 不一致になることを維持。 | 宣言 membership を `_validated_pin_path` より前で短絡し、改竄 pin が例外なしで除外されたら赤になります。 |
| `orchestrator/tests/test_env_contract.py::test_registry_effective_clock_self_failures_are_exact_known_exception` | production 宣言から実 g1 を落とすと [`_registered_clock_self_audit` の未宣言失敗 assert](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_env_contract.py:883>) が失敗し、余分な ref を宣言すると最終集合完全一致 [`:898`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_env_contract.py:898>) が失敗する構造を維持。 | 宣言の不足または過剰が実失敗集合との不一致を起こしてもテストが通れば赤にできていないため不合格です。 |

既存期待値を変えるのは指定された Pegasus g1 採用 2 件だけです。`test_env_contract.py` は literal の所在を import へ変えますが、期待する集合・件数・自己比較結果は変えません。missing、env mismatch、SHA/path/file fail-closed、linux-baremetal、between-run、legacy basis の既存期待値は変更しません。

## 親 brief の誤り

| 対象 | 判定 |
|---|---|
| (P1) [`brief.md:57–64`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:57>) | 方針は正しいです。置き場は `calibration_verify.py` を選ぶと γ-16 の文言上の摩擦も避けられます。 |
| (P2) [`brief.md:65–67`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:65>) | 誤りです。「`_validated_pin_path` を呼ばずに」は、不変条件 [`brief.md:83–84`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:83>) の SHA 不一致・directory 外・非 file の fail-closed 維持と矛盾します。検証を先に完遂し、その後 within-run candidate append だけを止める必要があります。 |
| (P3) [`brief.md:68–69`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:68>) | 誤りなし。exact g1 pin 以外の直下 record 経路は維持します。 |
| (P4) [`brief.md:70–71`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:70>) | 誤りなし。production で effective-clock 比較を呼びません。 |
| (P5) [`brief.md:72–77`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:72>) | 前提は正しいです。ただし合成 JSON/ref より、実 registry の健全な never-active g2 ref と実 bytes を `_calibration_floors` へ直接渡す方が強い正例です。monkeypatch は不要です。 |
| 実測 [`brief.md:20–44`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:20>) | 提示資料との矛盾はありません。なお schema 凍結テスト [`test_layer3_report.py:1516`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:1516>) が直接固定するのは schema version、`runs.items.required`、screening nested shape であり、top-level 全キー集合ではありません。本変更は schema 自体を触らないため影響しません。 |
| 不変条件 [`brief.md:79–85`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:79>) | 誤りなし。ただし上記 P2 をそのまま実装すると fail-closed 不変条件を破ります。 |
| 変更面 [`brief.md:46–53`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:46>) | `_contract_calibration_pin` を編集対象に含める必要はありません。除外は validation 後の `_calibration_floors` に置くべきです。また「linux-baremetal v2 pin 採用テスト」は実際には [`test_linux_v2_keeps_direct_skew_zero_floor_in_addition_to_pin`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3634>) で、pin-only 正例ではありません。健全 g2 の新テストが必要です。 |
| 分割方針 [`brief.md:93–97`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:93>) | 誤りなし。production 2 file、test 2 file の一つの実装単位で閉じます。 |

## 総括

- 宣言は `calibration_verify.py` の immutable な exact `(path, sha256)` 集合へ置きます。
- g1 pin は従来の path/file/SHA 検証後に、within-run 候補化だけを止めます。
- between-run、直下 record、legacy basis、既存 status、schema、契約 hash・世代・activation は維持します。
- 健全 pin の正例には実 Pegasus g2 artifact を使い、activation や依存先を stub しません。
- 本回答は指定資料の静的読解のみで、pytest・probe は実走していません。
- 親は焦点 nodeid、AST 検査、契約 golden、既存7レポートの `noise_floor` 値不変を実測してください。