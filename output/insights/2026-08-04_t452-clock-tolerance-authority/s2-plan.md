# [T-452] `effective_clock.tolerance_pct` policy 権威設計案

結論は、`2.0 %` を env 非依存の単一 policy 定数とし、observed profile から tolerance field 自体を除去する設計を推奨する。CLI、投入 script、環境変数のいずれも値を指定できなくし、producer・loader・issuer・consumer が同じ policy 値を参照しつつ、issuer の比較アルゴリズムは独立実装のまま残す。

本稿は静的読取りだけによる設計案であり、コード・テスト・文書・git は変更していない。pytest も実行していない。

## 1. 権威の所在

### 推奨配置

新規 leaf module `orchestrator/calibrator/effective_clock_policy.py:1` に、次の単一識別子を置く。

```python
EFFECTIVE_CLOCK_TOLERANCE_PCT: Final[float] = 2.0
```

この module は env tag、mapping、setter、fallback、環境変数参照を持たない。`schema_v2.py` が現在 stdlib-only の共有 leaf であることは `orchestrator/calibrator/schema_v2.py:1-8` に明記されているため、schema 自身を policy の正本にせず、独立した小さな leaf とする。

参照者は次の4者である。

- producer: `orchestrator/calibrator/cli.py:549-551`
- loader / issuer: `orchestrator/campaign/env_attestation.py:674-692`
- issuer の独立比較: `orchestrator/campaign/env_attestation.py:576-592`
- canonical consumer: `orchestrator/campaign/execution_guard.py:182-199`

issuer と consumer が共有するのは数値の権威だけであり、比較計算は引き続き別実装とする。これは D155 の独立裏取り契約 `docs/decisions.md:7700-7704` を維持する。

### 単一定数と env_tag 表の比較

| 案 | 書換え可能者と攻撃面 | 評価 |
|---|---|---|
| 独立 module の単一定数 | repository を編集できる者は変更できる。ただし変更面は1識別子に限定され、env 追加担当者が局所的に広げることはできない。`Final` は runtime 防壁ではないため、golden test と consumer 側再検査が必要 | 推奨 |
| `env_contract.REGISTRY` の env_tag ごとの field | `_build_registry()` を編集できる者が、特定 env だけを `100.0` にできる。`MappingProxyType` は import 後の代入を防ぐだけで、source 内の値変更は防がない。現在の構造は `orchestrator/campaign/env_contract.py:163-199` | 不採用 |
| `CalibrationRef` に field を追加 | calibration pin 更新者が policy も同時に書き換えられる。artifact 内の値との二重正本になる。現在の責務は path+sha256 だけである `orchestrator/campaign/env_contract.py:63-79`。field 集合もテストで固定されている `orchestrator/tests/test_env_contract.py:598-601` | 不採用 |

`REGISTRY` に置く利点は `contract_sha256` に直接入ることだが、artifact の SHA が既に `CalibrationRef` を介して contract hash に含まれる `orchestrator/campaign/env_contract.py:145-160`。artifact が policy と一致することを loader で検査すれば、独立 module でも policy は calibration SHA、ひいては contract SHA に間接的に束縛される。

環境固有の測定差は probe/method の問題として扱うべきで、env ごとに許容幅を広げる理由にはしない。別の意味を持つ述語が必要なら、暗黙の table entry ではなく別 policy version として裁定する。

## 2. 固定値と根拠

推奨値は **`2.0 %`** とする。

根拠は smoke 分布への fitting ではなく、述語の意味である。canonical 述語は expected の中央値を中心に observed の全要素を検査する `orchestrator/campaign/execution_guard.py:182-199`。D143 が正とした意味は「`governor=performance` 下で、定格帯から外れたコアが一つもないこと」である `docs/decisions.md:6976-6985`。

`2.0 %` は次の意味境界とする。

- 小さな周波数表示の量子化・制御誤差には有限の余白を与える。
- turbo、別 governor、競合負荷など「定格から外れた状態」は許容しない。
- 現 artifact の `+46.641 %` 標本を通すための値にはしない。現実測では `46.65 %` 以上が必要であり、policy 値による救済は不可能である `/work/1/SFC/tanab/dev-wave-jobs/t452-clock-tolerance-authority/brief.md:29-32`。
- `100.0 %` は literal な恒真ではないが、正の expected median に対して概ね `[0, 2×median]` を受理する実質恒真化である `/work/1/SFC/tanab/dev-wave-jobs/t452-clock-tolerance-authority/brief.md:25-28`。

### 値変更の手続き

値の変更は通常の設定変更として扱わず、次をすべて必要条件とする。

1. ユーザー裁定と decisions 記録に、述語の意味がなぜ変わるのかを書く。
2. smoke 分布から逆算せず、inside-boundary / outside-by-epsilon の手書き反証 vector を提示する。
3. policy golden test の literal を変更する。
4. `attestation_mode="required"` の全較正を新 policy で再取得する。
5. calibration path+SHA、registry、contract SHA、依存 evidence、テスト pin、既知例外を一つの migration closure として更新する。
6. 旧 artifact は履歴として parse 可能に保つが、current loader admission には通さない。

## 3. observed sentinel との衝突

現在は expected と observed が同じ `EffectiveClockProfile` を共有する `orchestrator/calibrator/schema_v2.py:218-239`。probe は「observed は自前の policy を持たない」という意味を `100.0` で代用している `orchestrator/campaign/env_attestation.py:433-440`。一方、receipt の observed 比較値からは tolerance が既に除かれている `orchestrator/campaign/env_attestation.py:545-547`。

### 選択肢比較

| 案 | 既存 artifact bytes | receipt / consumer 影響 | 評価 |
|---|---|---|---|
| 専用 observed 型 | expected calibration の JSON shape は不変なので既存 artifact bytes は変わらない。同一 sample を publish した場合、型分離自体は artifact bytes に影響しない | receipt の observed 値は既に samples だけなので bytes 不変。`probe()`、`compare_profiles()`、`probe_fn` annotation と、full observed profile を直列化する診断 consumer は移行が必要 | 推奨 |
| `Optional[float]` として observed=`None` | 既存 expected artifact bytes は不変 | full observed JSON は `100.0` から `null` へ変わる。outer calibration validation が `None` を拒否しないと、expected にも「policy なし」が流入する | 次点 |
| `100.0` を名前付き sentinel として維持 | bytes はすべて不変 | consumer 変更が最小。ただし schema 上限を狭められず、observed を expected と誤用できる構造が残る | 不採用 |

### 推奨する型分離

- `schema_v2.EffectiveClockProfile` は calibration/expected 専用として残す。
- `orchestrator/campaign/env_attestation.py:390` の `probe()` は、新しい `ObservedEffectiveClockProfile` と `ObservedAttestationProfile` を返す。
- `ObservedEffectiveClockProfile` の field は `samples_mhz`, `method`, `governor` の3つだけとする。
- `compare_profiles()` は expected と observed を別型で要求する。現在は同じ型を要求している `orchestrator/campaign/env_attestation.py:600-615`。
- calibrator は observed dataclass を dict 化した後、policy field を挿入して expected artifact に変換する。現在も probe 値を dict 化してから tolerance を上書きする経路である `orchestrator/calibrator/cli.py:337-342`、`orchestrator/calibrator/cli.py:549-551`。

schema は expected の `100.0` を拒否するよう上限を `<100.0` に狭める。ただし current policy との完全一致は schema の責務にせず、producer・loader・issuer・consumer の trust boundary で検査する。これにより旧 policy artifact を履歴として parse できる一方、current calibration としては受理しない。

## 4. 恒真化を塞ぐ機械

CLI 値域だけの変更では、publish する値を人が選べる構造が残る。以下を組み合わせ、どれか一層の脱落を他層が検出するようにする。

| 機械 | 実装位置と内容 | 壊す変異 | 変異を殺すテスト |
|---|---|---|---|
| policy 正本 | `orchestrator/calibrator/effective_clock_policy.py:1` に単一定数 `2.0`。mapping/setter/env参照なし | `2.0` を `100.0` に変更、または env_tag table にする | 新設 `orchestrator/tests/test_effective_clock_policy.py:1::test_effective_clock_policy_is_single_global_2pct_constant`。literal `2.0` と AST 上の単一定義を検査 |
| 投入面 | `tools/pegasus/submit_certify.sh:7-42,177-178` の引数・環境変数搬送を撤去。job script の検証・CLI転送 `tools/pegasus/certify_calibration.sh:154-164,718-731` も撤去 | submitter に `100` の入力面を戻す | `orchestrator/tests/test_pegasus_tools.py:200::test_certify_has_no_tolerance_input_surface` と、現在の dry-run site `orchestrator/tests/test_pegasus_tools.py:1074-1080` を無引数に改め、source に flag/env 名がないことを検査 |
| CLI 検証 | parser の手入力 option `orchestrator/calibrator/cli.py:131-132` と `(0,100]` 検証 `orchestrator/calibrator/cli.py:485-488` を撤去 | legacy option を再び受け入れる | `orchestrator/tests/test_calibrator_certify.py:384` 付近に `test_cli_rejects_legacy_tolerance_override_before_attempt`。`100` 指定が attempt 作成前に rc=2/SystemExit(2) |
| schema / observed 型 | expected schema は `100.0` を拒否し、observed 型には field 自体を持たせない。現上限は `orchestrator/calibrator/schema_v2.py:235-239` | expected で `100` を再受理、または observed に tolerance field を戻す | `orchestrator/tests/test_schema_v2.py:194` 隣接の `test_expected_clock_rejects_hundred_pct`、`orchestrator/tests/test_env_attestation.py:77::test_probe_returns_tolerance_free_observed_profile` |
| producer 注入 | `orchestrator/calibrator/cli.py:551` は args ではなく policy 定数を代入 | `100.0` literal、env var、引数値を代入 | 現在の任意引数保存 pin `orchestrator/tests/test_calibrator_certify.py:613-636` を `test_cli_artifact_uses_effective_clock_policy` へ置換し、artifact が literal `2.0` であることを検査 |
| 取得時 gate | `_effective_clock_self_comparison_passes()` `orchestrator/calibrator/cli.py:381-391` を policy 注入後の profile に適用し、publish 前 `orchestrator/calibrator/cli.py:608-615` で拒否 | helper を `return True`、外れ値を除外、gate を publish 後へ移動 | 既存 `test_cli_effective_clock_self_failure_is_quality_rejected_before_publish` `orchestrator/tests/test_calibrator_certify.py:531-577` が外れ値、reason、非publishを検査 |
| loader admission | `load_verified_calibration()` が schema validation 後、expected tolerance と policy の完全一致を検査してから `VerifiedCalibration` を返す。挿入点は `orchestrator/campaign/env_attestation.py:674-692` | hash-bound artifact の `100` を current calibration として返す | `orchestrator/tests/test_env_attestation.py:264` 付近に `test_load_verified_calibration_rejects_non_policy_tolerance`。bytes と SHA を整合させた `100` artifact を拒否 |
| registry 不変条件 | required entry 全件について policy 一致と self-pass を要求し、U-2 後は例外集合を空にする。現検査は `orchestrator/tests/test_env_contract.py:436-463` | loop を0回にする、1件を skip、既知例外を残す | `test_registry_effective_clock_policy_and_self_consistency` とし、`checked_required == 1`、`self_failures == set()`、artifact tolerance `==2.0` を別々に assert |
| issuer 独立比較 | `_recorded_verdict()` は expected tolerance が policy と一致しなければ fail、その後も独自に median/band/all を計算する `orchestrator/campaign/env_attestation.py:576-592` | artifact の `100` をそのまま計算に使う、または常に pass | `orchestrator/tests/test_env_attestation.py:249` 付近に `test_compare_profiles_rejects_non_policy_expected_tolerance`。issuer verdict を直接検査 |
| runtime guard | canonical predicate は expected tolerance の policy 一致を検査し、delta は policy 定数から計算する `orchestrator/campaign/execution_guard.py:182-199` | equality check を削除して expected の `100` を使う | `orchestrator/tests/test_execution_guard.py:360-478` の golden vectors に unauthorized-100=False を置く。issuer を constant-pass に変異させても consumer が拒否する既存独立性テスト `orchestrator/tests/test_execution_guard.py:336-357` も併用 |

### 恒真検査になっていないことの自己点検

- policy test は production constant と同じ値から期待値を生成せず、literal `2.0` を独立に持つ。
- negative control は schema-invalid な壊れた JSONだけでなく、SHAまで再計算した well-formed artifact を loader に渡す。
- registry test は required entry の件数を assert し、空 loop を成功させない。
- publish test は helper 単体だけでなく、実際の `registered/` 非生成まで観測する。
- issuer と consumer は別々に呼び、片方を constant-pass にした receipt をもう片方が拒否する。
- `100.0` のテストは「必ず落ちる巨大値」を用いるのではなく、現在なら `[0,2×median]` を通る標本を用い、policy equality が load-bearing であることを示す。

## 5. 移行

### 現在の不整合

登録済み artifact は47個の `2101.0` と1個の `3080.935` を持ち `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440-1493`、それでも quality は accepted である `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1599-1601`。F97 はこの参照自身が predicate を通らないことを記録している `docs/failures.md:2154-2173`。

### 必須順序

1. **[T-419] U-1 probe 実験**  
   F108 の観測者効果を計算ノードで反証・確定する。現時点では probe 自身の走行コアが帯外になると記録されている `docs/failures.md:2351-2372`。
2. **probe 方式のユーザー裁定と実装**  
   本設計は方式を決めない。全要素 predicate を緩めない範囲で、observed を意味のある定格観測にする。
3. **policy authority 実装**  
   型分離、入力面撤去、producer/loader/issuer/consumer の policy 検査を入れる。
4. **[T-419] U-2 較正再取得**  
   新 CLI が policy `2.0` を自動挿入し、self-comparison を通った artifact だけを content-addressed publish する。publish は `orchestrator/calibrator/cli.py:608-638`。
5. **pin closure**  
   新 artifact の登録と全参照更新、既知例外削除を行う。
6. **その後に campaign / certified 選択を再開**  
   移行途中の current calibration では certified campaign を開かない。

### 本設計を先に入れると再取得は塞がるか

**現行 probe のままなら塞がる。U-1 後に predicate を満たす probe が得られれば塞がらない。**

実経路は、probe profile取得 `orchestrator/calibrator/cli.py:525-551` → policy挿入 → benchmark → self gate `orchestrator/calibrator/cli.py:598-610` → accepted の場合だけ publish `orchestrator/calibrator/cli.py:611-638` である。現行 probe の帯外標本に `2.0` を挿入すれば self gate が落ちる。`100.0` で迂回する経路を閉じること自体が本設計の目的である。

一方、現登録 artifact の tolerance は既に `2.0` なので、policy equality の導入だけでは loader を新たに壊さない。壊してはならないのは self-comparison を loader の schema admission に追加すること。この gate を loader に置く案が D155 で却下された理由は `docs/decisions.md:7733-7738` にある。

### pin 閉包

U-2 では最低限、次を一つの閉包として扱う。

- `env_contract.REGISTRY` の path+sha256: `orchestrator/campaign/env_contract.py:180-192`
- lookup golden: `orchestrator/tests/test_env_contract.py:239-251`
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の旧 literal: `orchestrator/tests/test_env_contract.py:58-63`
- Pegasus contract SHA golden: `orchestrator/tests/test_env_contract.py:678-691`
- self-inconsistency 既知例外を空集合へ反転: `orchestrator/tests/test_env_contract.py:436-463`
- silo ladder binding の path+sha256+contract_sha256: `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:10-17`
- その current-registry 結合テスト: `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1219-1230`
- driver の current-binding gate: `orchestrator/campaign/silo_ladder_rung1.py:3519-3527`

ただし、過去の silo ladder evidence の calibration binding を新 artifact へ書き換えると、「その試行が新較正を使用した」という虚偽の履歴になる。推奨は旧 evidence bytes を自己完結した歴史資料として保持し、current eligibility を外したうえで、新 calibration を使用した後続 evidence を別 artifact として作ることである。既存 evidence を current registry と常に一致させるテスト契約は、この区別に合わせて変更する必要がある。

## 6. 反証テストの設計

### Positive controls

- `orchestrator/tests/test_effective_clock_policy.py:1::test_effective_clock_policy_is_single_global_2pct_constant`  
  正本が単一定数 `2.0` である。
- `orchestrator/tests/test_schema_v2.py:194` 隣接 `test_expected_effective_clock_accepts_policy_tolerance`  
  expected schema が `2.0` を受理する。
- `orchestrator/tests/test_calibrator_certify.py:580::test_cli_published_artifact_passes_runtime_effective_clock_self_comparison`  
  publish 済み参照を canonical consumer に自分自身として与えると通る。
- `orchestrator/tests/test_env_contract.py:436::test_registry_effective_clock_policy_and_self_consistency`  
  全 required registry entry が policy と一致し、例外なしで自分の判定を通る。
- `orchestrator/tests/test_env_attestation.py:249` 隣接 `test_compare_profiles_accepts_policy_boundary`  
  issuer 独立実装が ±2% の inclusive boundary を通す。
- `orchestrator/tests/test_execution_guard.py:360::test_effective_clock_canonical_predicate_golden_vectors`  
  canonical consumer も同じ手書き boundary outcome を返す。

### Negative controls

- `orchestrator/tests/test_calibrator_certify.py:384` 隣接 `test_cli_rejects_legacy_tolerance_override_before_attempt`  
  `--effective-clock-tolerance-pct 100` は attempt 作成前に拒否。
- `orchestrator/tests/test_schema_v2.py:194` 隣接 `test_expected_effective_clock_rejects_hundred_pct`  
  expected schema は sentinel 値を拒否。
- `orchestrator/tests/test_env_attestation.py:264` 隣接 `test_load_verified_calibration_rejects_non_policy_tolerance`  
  path と SHA を正しく束縛した `100.0` artifact も current loader が拒否。
- `orchestrator/tests/test_env_attestation.py:249` 隣接 `test_compare_profiles_rejects_non_policy_expected_tolerance`  
  issuer は observed の値にかかわらず unauthorized expected policy を fail。
- `orchestrator/tests/test_execution_guard.py:360` の unauthorized-100 vector  
  `100.0` なら従来通る `[0,2×median]` 内の標本でも consumer は拒否。
- `orchestrator/tests/test_execution_guard.py:336::test_receipt_consumer_is_independent_of_constant_true_issuer_comparator`  
  issuer verdict を forged pass にしても consumer 再計算が拒否。
- `orchestrator/tests/test_calibrator_certify.py:531::test_cli_effective_clock_self_failure_is_quality_rejected_before_publish`  
  policy 帯外標本を持つ candidate は reason を残し、publish されない。
- `orchestrator/tests/test_pegasus_tools.py:200::test_certify_has_no_tolerance_input_surface`  
  submitter、job script、calibrator argv に手入力 surface が存在しない。

## 7. 却下した案

述語の緩和、attestation の除去、issuer の canonical 実装への統合は確定裁定により設計空間外である `/work/1/SFC/tanab/dev-wave-jobs/t452-clock-tolerance-authority/brief.md:18-21,49-50`。

それ以外に、次を却下する。

- **env_tag ごとの tolerance table**  
  env 登録者に受理集合を局所的に広げる権限を与え、同じ predicate の意味が環境ごとに変わる。
- **schema 上限だけを `10` や `20` に狭める**  
  publish 値の手入力権限が残り、なぜその上限かという第二の根拠問題を作る。
- **artifact 内の `tolerance_pct` 自身を権威とする**  
  検査対象が自分の受理幅を宣言する自己署名構造であり、現在の欠陥そのもの。
- **環境変数・shell policy・JSON 設定を正本とする**  
  submitter、scheduler export、job script のいずれかが値を差し替えられる。現在の搬送面は `tools/pegasus/submit_certify.sh:177-178` と `tools/pegasus/certify_calibration.sh:730`。
- **`CalibrationRef` に policy を複製する**  
  artifact、policy module、contract の三重正本となり、どれを正とするかが再び未定になる。
- **runtime guard だけで検査する**  
  unauthorized artifact を accepted として publish・登録でき、材料レポートや pin が既に汚染される。
- **named numeric sentinel `100.0` の維持**  
  consumer が expected/observed を取り違えたときに実質恒真値が再び権威位置へ流入できる。
- **既存 silo evidence の calibration binding だけを新 SHA へ差し替える**  
  過去試行で使っていない較正を使ったように見せ、試行台帳と proof chain の履歴を改変する。

## 8. 未決の設計択一

### U-1 — policy の配置

- 選択肢A: 独立単一定数 module
- 選択肢B: `REGISTRY` の env_tag table
- 有利材料A: 単一レビュー面、env 登録者が局所的に広げられない
- 不利材料A: contract hash への束縛は artifact SHA 経由の間接束縛
- 推奨: **A**

### U-2 — CLI 互換面

- 選択肢A: option を完全撤去
- 選択肢B: option を残し、policy と完全一致する値だけ受理
- 有利材料A: 権威と誤認される入力面が消える
- 不利材料A: submitter、job script、既存テストを同時移行する必要がある
- 推奨: **A**。互換性が必要でも期限付きでBとし、`100` の拒否テストを置く。

### U-3 — observed の表現

- 選択肢A: tolerance field を持たない専用型
- 選択肢B: 共有型で `Optional[float]`
- 選択肢C: numeric sentinel を明示化
- 有利材料A: 「policy を持たない」が構造的事実になる
- 不利材料A: probe/compare/type annotation と full-profile consumer の移行面が広い
- 推奨: **A**

### U-4 — schema と current policy の結合度

- 選択肢A: schema は structural range のみ、exact policy は trust boundary で検査
- 選択肢B: schema 自体が current policy と完全一致を要求
- 有利材料A: 旧 artifact を履歴として parse できる
- 不利材料A: loader/issuer/consumer の重複防壁が必須
- 推奨: **A**。schema は `100.0` を expected として拒否し、完全一致は producer・loader・issuer・consumer が担う。

### U-5 — silo ladder evidence の扱い

- 選択肢A: 旧 evidence を歴史資料として保持し、current eligibility を外して後続 evidence を作る
- 選択肢B: 旧 evidence の binding を新較正へ書き換える
- 有利材料A: 試行台帳の歴史的真実を保持する
- 不利材料A: current registry との常時一致を要求する既存テスト・driver 契約を分離する必要がある
- 推奨: **A**

### U-6 — landing 単位

- 選択肢A: U-1 後、authority 実装を先に landし、current campaign を閉じたままU-2とpin closureを続ける
- 選択肢B: authority実装、U-2 artifact、pin closureを一つの最終 commitへ集約
- 有利材料A: 新 CLI を clean source として計算ノードで使用できる
- 不利材料A: 一時的に旧既知例外が残るため、途中状態で certified campaign を開けない
- 推奨: **A**。2 commitを同じT-419 cycle内で連続させ、間ではcampaignを禁止する。

## 9. 成果物影響

| 主要項目 | 実装しなかった場合の certified 選択・材料レポート・試行台帳への影響 |
|---|---|
| 1. 権威の所在 | certified 選択の受理集合を CLI 操作者が変えられ、材料レポートは手入力値を policy のように参照し、台帳には比較不能な tolerance の trial が混在する。 |
| 2. 固定値と根拠 | 同じ観測でも実行ごとに accepted/rejected が変わり、材料レポートは述語の意味を説明できず、台帳の attestation verdict を横断比較できない。 |
| 3. observed sentinel | sentinel が expected に漏れれば受理集合が実質 `[0,2×median]` へ広がり、逆に上限だけ狭めれば probe 自体が schema reject され、いずれも certified 結果を作れない。 |
| 4. 恒真化防壁 | `100` artifact が self gate と実行時 guardを通り、certified 選択は環境同一性を未証明のまま受理され、report/ledgerには偽の pass receipt が残る。 |
| 5. 移行 | 旧較正が自分の述語を通らないため certified 選択は開始前に停止し、report は旧 SHA/contract を参照し続け、台帳には attestation failure だけが積まれる。 |
| 6. 反証テスト | constant-pass、入力面復活、loop空振りなどの変異が生存し、certified acceptance と report/ledger の proof chain が静かに広がる。 |
| 7. 却下案の封鎖 | env別緩和・自己宣言・runtime-only 検査が復活すると受理集合が広がり、材料レポートと台帳が「なぜ受理されたか」を再計算できなくなる。 |
| 8. 未決択一 | 実装者ごとに module、sentinel、CLI互換、歴史 evidence の扱いが分岐し、同じ calibration SHA を指さない certified 結果・report・ledger が併存する。 |

## 総括

- `orchestrator/calibrator/effective_clock_policy.py:1` の単一定数 `2.0` を唯一の権威とする。
- observed は tolerance field を持たない専用型へ分離し、CLI・shell・環境変数の手入力面を撤去する。
- producer・loader・issuer・consumer は policy 一致を各境界で拒否し、issuer の比較計算は独立実装のまま残す。
- [T-419] U-1 → authority実装 → U-2再取得 → pin閉包・既知例外削除の順とし、旧 evidence は遡及的に再束縛しない。