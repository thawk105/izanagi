# 段 2 実装プラン

推奨は、取得時述語を `calibrator/cli.py` の独立 helper として実装し、既存の品質理由を集めた直後、`status` を決める直前に追加評価する形です。これなら publish より確実に前で発火し、失敗時も既存の通常品質 rejection と同じ staging 形を保てます。

本回答は静的検査だけに基づきます。sandbox が read-only のため、テストは実走しておらず緑は主張しません。

## 確認できた制御フロー

- 実行時 consumer 述語は [execution_guard.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:158) にあり、期待列の中央値と期待側 `tolerance_pct` から帯を作り、観測列の全要素を包含するかを `<=` で判定します。
- probe の観測側は [env_attestation.py:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:433) で生成され、比較値では期待側だけが tolerance を持ち、観測側は samples だけです（[env_attestation.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:521)、[env_attestation.py:545](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:545)）。
- certify 経路では dynamic profile を取得後、CLI tolerance を artifact 候補へ設定します（[cli.py:525](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:525)、[cli.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:537)）。
- 品質理由、status、staging artifact は [cli.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:593) から組み立てられます。rejected なら [cli.py:609](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:609) で return し、`registered/` の作成は [cli.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:613)、実 publish rename は [cli.py:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:622) です。
- schema は samples の非空・正・有限、tolerance の正・有限・100 以下を検査しますが、samples 自身の帯内性は検査しません（[schema_v2.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/schema_v2.py:218)）。
- 現登録 artifact は確かに index 40 が `3080.935`、tolerance が `2.0`、quality は accepted です（[calibration-753f535a8d024727.json:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440)、[同:1484](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1484)、[同:1599](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1599)）。

## S1: 実装位置の比較

| 候補 | publish 前の保証 | reason / staging | 評価 |
|---|---|---|---|
| `_acquisition_reasons`（[cli.py:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:380)） | ベンチ前なので保証される | `acquisition-invalid: ...` と個別 reason が重複しやすい。`result is None` のため `rejection.json` だけが残り、profile の帯外値を含む v2 artifact、report、window probes は残らない | 早期停止は利点だが、receipt/acquisition 整合性と profile 自己整合性を混同するため非推奨 |
| `certification_quality_reasons`（[report.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/report.py:87)） | 呼出しが line 593 なので保証される | 通常品質 rejection の形を保てる | 現在は C3-1 の「8 条件」と run-scoped evidence 専用。profile 引数または `CertificationEvidence` の第9フィールドが必要になり、model と単体テストへ不要な波及が出る |
| `_certify_main` の独立 helper を line 593–594 に接続 | false なら reason が非空になり、line 609 で必ず停止するため rename 到達不能 | `quality.status=rejected` の `calibration.json`、`calibration.md`、`window-probes.json` が残る。`candidate.json`、`publish.json`、新規 registered artifact は生じない | 推奨 |
| `_assemble_v2`（[cli.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:423)） | publish 前には発火する | serializer 内で status を覆すか例外化する必要がある。例外なら通常の品質 reason でなく `attempt-fatal` になり、report/window probe 作成前に落ちる | policy と serialization が混ざるため非推奨 |
| schema の `EffectiveClockProfile` / `CalibrationV2` | 全 loader に効く | 現登録 artifact まで即時 schema-invalid になる。`EffectiveClockProfile` に置くと rejected artifact に帯外証拠を保存することすらできない | CLI の将来 publish 集合だけを狭める S1 を越え、scope 外の凍結 artifact を実質失効させるため不可 |

`_static_profile_bytes` は [cli.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:373) で TSC と effective clock を意図的に除外しています。ここへ含める変更は「静的 hardware が cooldown 前後で同じか」という別述語を動的クロック比較に変えてしまい、S1 の自己帯内検査にはならないため触れません。

### 推す接続形

[cli.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:593) の直後、`status` 算出前に次の論理順で置きます。

```python
reasons.extend(certification_quality_reasons(result, evidence))
if not _effective_clock_self_comparison_passes(profile):
    reasons.append("effective-clock-self-comparison-failed")
status = "accepted" if not reasons else "rejected"
```

reason code は `effective-clock-self-comparison-failed` を推します。

- 既存の `within-run-cv-invalid`、`post-attestation-mismatch` と同じ kebab-case。
- receipt 不一致ではないので `acquisition-` を付けない。
- 型不正等も含め「runtime と同じ self comparison が false」という意味を保てる。
- `quality.reasons` は [schema_v2.py:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/schema_v2.py:420) で閉じた enum にはなっていません。また `_certify_main` は既に report 外の acquisition/fatal reason も追加しています。したがって report の8条件へ無理に混ぜず、テストで文字列を直接 pin するのが現行構造との整合です。

## 述語の独立実装

P4 の方針は妥当です。ここは通常の重複排除より common-mode failure の排除を優先すべき境界です。

現状でも次の2実装があります。

- receipt issuer: [env_attestation.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:564) の `_recorded_verdict`
- receipt consumer: [execution_guard.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:158) の `_independent_comparison_passes`

S1 を新設すると、総数としては「独立2実装」ではなく publisher を加えた3実装になります。brief の「独立2」は、今回等価性を pin する publisher と consumer の一対を指すものと解する必要があります。

consumer を共有すると、具体的には次を失います。

- median を mean に変える、`all` を `any` に変える、inclusive 境界を誤る、といった一つの変異が、publish と runtime acceptance の双方を同時に誤らせる。
- producer/consumer の結果比較テストが同じ関数を二度呼ぶ恒真テストになる。
- consumer の docstring が要求する「issuer が書いた verdict を別コードで再計算する」という二者検証が、artifact issuer に対して成立しなくなる。
- `calibrator` から `campaign.execution_guard` への production import が生じ、現在の依存方向も逆転する。

### helper の配置と中身

[cli.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:373) の `_static_profile_bytes` の直後に、次の2段を置くのが最小です。

1. `_effective_clock_comparison_passes(expected, observed)`  
   `execution_guard` を import せず、Mapping、exact list、非空、tolerance の exact numeric type、`statistics.median`、`abs(median) * tolerance / 100`、全要素の inclusive `<=`、例外時 false を独立に記述する。

2. `_effective_clock_self_comparison_passes(profile)`  
   `profile["effective_clock"]` から、production と同じ expected 形 `{samples_mhz, tolerance_pct}` と observed 形 `{samples_mhz}` を組み、1 の helper を呼ぶ。

`statistics` と `collections.abc.Mapping` の import は [cli.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:17) 付近へ追加します。帯計算だけを共通 helper に切り出して consumer と共有することもしません。それでは最も壊れやすい median・abs・tolerance 計算が再び単一障害点になります。

### 等価性の表駆動テスト

[test_execution_guard.py:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:336) の consumer 独立性テストの後へ、引数なしの1テスト内で表を loop する形を推します。同ファイル末尾の pytest 非依存 `_run()` を壊さないため、pytest parametrization は使いません。

各行に明示的な `want` を持たせ、単なる `publisher == consumer` にしないことが重要です。

| ケース | expected | observed | want |
|---|---|---|---|
| 通常 self-pass | samples=`[99,100,101]`, tol=`2` | 同じ列 | true |
| 下限・上限ちょうど | samples=`[100]`, tol=`2` | `[98,102]` | true |
| 境界直外 | 同上 | `[97.999999]` | false |
| 本欠陥の合成形 | samples=`[100,100,150]`, tol=`2` | 同じ列 | false |
| 偶数列の中央値 | samples=`[90,110]`, tol=`10` | `[90,110]` | true |
| expected 非 Mapping | `None` | valid map | false |
| observed 非 Mapping | valid map | `None` | false |
| expected samples が tuple | tuple + valid tol | valid list | false |
| observed samples が tuple | valid map | tuple | false |
| expected 列が空 | `[]` + tol | valid list | false |
| observed 列が空 | valid map | `[]` | false |
| tolerance 欠落 | samples のみ | valid list | false |
| tolerance が bool / str | `True` または `"2"` | valid list | false |
| 非数値 sample | `["bad"]` | `["bad"]` | false |
| tolerance 0、完全一致 | samples=`[100]`, tol=`0` | `[100]` | true（raw comparator の現挙動） |
| tolerance 0、不一致 | 同上 | `[100.001]` | false |
| tolerance 100 の両境界 | samples=`[100]`, tol=`100` | `[0,200]` | true |
| tolerance 100 の直外 | 同上 | `[200.001]` | false |
| tolerance 負値 | samples=`[100]`, tol=`-1` | `[100]` | false |

tolerance 0 や負値は production artifact には到達しません。CLI が [cli.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:471)、schema が [schema_v2.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/schema_v2.py:235) で拒否します。表では、schema validation と比較述語を混同せず consumer の現挙動と等価であることを pin します。

## S2: positive control

### 不変条件テスト

[test_calibrator_certify.py:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:491) 付近へ、既存 `_invoke` を使う別テストを追加します。

1. 合成 `_profile()` で certify を成功させ、`rc == 0` と registered artifact 1件を確認する。
2. publish 済み bytes を `validate_calibration_v2` で読み戻す。
3. typed profile から `expected_comparison_values(...)[effective_clock.samples_mhz]` を取得する。
4. observed は production と同じ `{samples_mhz: [...]}` だけを組む。
5. `execution_guard._independent_comparison_passes(...) is True` を assert する。

このテストだけでは S1 を削除しても、もともと良い fixture なので通ります。したがって [test_calibrator_certify.py:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:481) の通常品質 rejection テストの隣へ、次の load-bearing negative を必ず対で追加します。

- `_profile()["effective_clock"]["samples_mhz"]` を `[2400, 2400, 3000]` に変更。
- CLI tolerance 5% に対し中央値 2400、帯 `[2280,2520]` なので fail。
- `rc != 0`、`quality.status == rejected`、reason に `effective-clock-self-comparison-failed`。
- `calibration.json`、`calibration.md`、`window-probes.json` は存在。
- `candidate.json`、`publish.json`、`rejection.json`、新規 registered artifact は存在しない。

恒真性は次の組合せで防ぎます。

- publisher が constant false → positive certify の `rc == 0` が赤。
- publisher が constant true、S1 接続を削除、`all` を `any` に変更 → outlier rejection が赤。
- consumer が constant false → published synthetic artifact の runtime assert が赤。
- consumer/publisher の境界・中央値計算が片側だけ変化 → explicit `want` 付き等価性表が赤。

### 現登録 artifact の事実 pin

配置は登録 artifact の canonical/hash/semantic 検査に隣接する [test_env_contract.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:423) の直後を推します。

- `ec.lookup("pegasus")` と `ea.load_verified_calibration(...)` を使い、path/hash-bound な現物をロードする。
- expected/observed を production と同じ形で組む。
- `assert not eg._independent_comparison_passes(...)` とする。
- テスト名に `currently` を入れ、コメントで「probe 是正・再登録 wave では assert を正向きへ反転し、名前も恒久不変条件へ変える」と明記する。

候補比較は次のとおりです。

| 書き方 | 評価 |
|---|---|
| `assert not predicate` | 推奨。load/schema/hash 検証が成功した上で predicate が false という現在事実を直接固定する |
| `pytest.mark.xfail(strict=True)` で正向き assert | unrelated な例外でも XFAIL になり得て、実際に predicate=false かが弱くなる |
| index 40、3080.935、帯を全て exact assert | 既存 path/hash pin と重複し、欠陥の細部を必要以上に API 化する |

「欠陥を固定化する」という批判への回答は、規範と移行事実を分離することです。

- 規範は別の合成 positive control、negative gate test、等価性表が保持する。
- この `assert not` は current hash-bound artifact の移行状態だけを固定し、acceptance oracle には使わない。
- probe 是正後に artifact が変われば意図的に赤くなり、同じ commit で path/hash pin と正向き assert へ更新する必要を強制する。
- constant-false で事実 pin を偽装する変異は、合成 pass 行と positive certify が検出する。

## 既存テストへの波及

推奨案では、静的に確認できる既存テストの赤化対象はありません。

- certify fixture は [test_calibrator_certify.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:194) の `[2400,2410,2390]`、CLI tolerance 5% です。中央値 2400、帯 `[2280,2520]` なので全要素が帯内です。
- この fixture を使う既存 success 系は lines 424–436、491–558 ですが、S1 を通ります。
- execution guard の `_required_binding` は [test_execution_guard.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:179) から `_valid_document()` を使い、その effective clock も `[2400,2410,2390]` / 5% です。
- 現登録 Pegasus artifact は帯外ですが、推奨する producer-only gate は既存 artifact の lookup/load へ遡及適用しません。そのため [test_env_contract.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:423) と [同:428](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:428) の既存テストは期待値変更不要です。新しい事実 pin が現在の false を明示します。

したがって「帯外 samples を持つ既存 certify fixture」は、grep した3ファイルには存在しません。実在する帯外 fixture は現在の registered Pegasus artifact です。

一方、非推奨位置を選ぶと次の実赤が予想されます。

- report API に profile を必須追加すると、[test_calibrator_certify.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:87) と [同:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:104) が引数不足になります。Evidence に default-false 第9条件を足す形なら、少なくとも exact reasons を見る line 87 が余分な reason で赤になります。
- schema の accepted 条件に入れると、現登録 artifact をロードする [test_env_contract.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:423) と [同:428](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:428) が、事実 pin へ到達する前に schema/load error になります。

## scope 確認と brief への補正

本プランでは次を変更しません。

- probe と `method="proc-cpuinfo"`（[env_attestation.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:390)）。
- runtime consumer 述語そのもの。
- schema の受理条件。
- Pegasus pin（[env_contract.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_contract.py:186)）。
- `calibration-753f535a8d024727.json` の bytes、登録先、再取得。
- observer effect の是正方式 α/β/γ。

brief の述語説明と現 artifact の数値には、一次資料との矛盾は見つかりませんでした。ただし次の2点は段3へ渡すべき補正です。

- S1 追加後は実装総数が3になるため、「独立2実装」は publisher–consumer の検査対象ペアという限定表現に直すべきです。
- 既存 certify fixture が帯外で赤くなるという前提は成立しません。帯外なのは現 registered artifact であり、推奨する CLI-only S1 は既存 loader へ遡及しません。

## 総括

- 推す実装位置:
  - [cli.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:373) の直後に publisher-side 独立 comparator と self wrapper。
  - [cli.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:593) の直後、status 算出前に `effective-clock-self-comparison-failed` を追加。
  - 例外化せず通常品質 rejection に流し、帯外 profile を含む `calibration.json` 等を staging に保存する。

- 独立実装の結論:
  - P4 を採用する。consumer helper、issuer `_recorded_verdict`、新 publisher helper の production コードは共有しない。
  - 等価性テストは explicit `want` 付き表で publisher と consumer を別々に検査し、単なる相互 equality にしない。

- 段5実装子へ渡す file:line 作業単位:
  - [cli.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:17): `statistics` / `Mapping` import。
  - [cli.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:373): 独立 comparator と self wrapper。`_static_profile_bytes` 自体は変更しない。
  - [cli.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:593): reason の追加と publish 前 rejection 接続。
  - [test_execution_guard.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:23)、[同:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:336): publisher import と引数なし表駆動等価性テスト。
  - [test_calibrator_certify.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:19)、[同:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:481): 帯外 profile の rejection/staging test と、publish 済み合成 artifact の runtime self-pass test。
  - [test_env_contract.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:36)、[同:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:423): consumer import と現登録 artifact の transitional `assert not` fact pin。
  - `report.py`、`schema_v2.py`、`env_attestation.py`、`env_contract.py`、registered artifact は無変更。

- 未解決の設計択一:
  - S1 failure をベンチ前に fail-fast して `rejection.json` だけ残すか、line 593 で通常品質 rejection として帯外 profile を保存するか。後者を推す。
  - reason code の最終綴り。`effective-clock-self-comparison-failed` を推す。
  - 事実 pin を direct `assert not` と strict xfail のどちらにするか。unrelated error を隠さない direct `assert not` を推す。
  - probe 是正方式、pin 更新、再取得・再登録は本 wave の未解決事項ではあるが、段5の実装単位には含めない。