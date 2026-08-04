静的検査の結果、設計案は現状のままでは **NO-GO** である。特に loader の負例が schema に遮蔽される点と、取得時 gate の位置依存変異が生存する点は、F97/F108/F109 と同型の恒真ゲートを残す。

pytest は実行していない。以下はすべてコード読取りによる判定である。

## 所見

### [所見 A-1] Critical — loader / issuer の policy 一致検査は、`100.0` を負例にすると手前の schema 拒否に遮蔽される

具体的な失敗シナリオ:

- 設計どおり schema 上限を `<100.0` にした後、`load_verified_calibration()` に追加する policy equality を削除する。
- SHA を再計算した `tolerance_pct=100.0` artifact を loader test に渡しても、schema が先に拒否するためテストは成功する。loader equality は一度も発火しない。
- issuer test でも `EffectiveClockProfile(tolerance_pct=100.0)` 自体を構築できず、`_recorded_verdict()` に到達しない。
- したがって設計案の「well-formed な `100` artifact」という記述は、新 schema と両立しない。

具体的変異:

- `orchestrator/campaign/env_attestation.py:674-692` に新設予定の policy equality を全削除。
- 設計上の loader test は依然 schema 例外を観測して緑。
- issuer 側も `orchestrator/campaign/env_attestation.py:576-592` の equality を削除しても、負例生成が schema で止まれば赤にならない。

根拠:

- `orchestrator/calibrator/schema_v2.py:235-239`
- `orchestrator/campaign/env_attestation.py:674-692`
- `orchestrator/campaign/env_attestation.py:576-592`
- `/work/1/SFC/tanab/dev-wave-jobs/t452-clock-tolerance-authority/out/s2-plan.md:84,98,100,106,179-184`

塞ぎ方の提案:

schema-valid だが非 policy の値、例えば `5.0` または `99.0` を loader・issuer・consumer 共通の負例にする。中央値 `100`、observed `[104]` とすれば、policy check を消した実装だけが通る。

**成果物影響:** equality が実際には無効でも ±5% 等の artifact が current calibration としてロードされ、certified 選択の受理集合と report/ledger の verdict が広がる。

### [所見 A-2] Critical — 取得時 gate の負例が末尾外れ値だけなので、別 index を捨てる変異が生存する

具体的な失敗シナリオ:

現在の負例は `[2101.0] * 47 + [3079.456]` で、外れ値は index 47 に固定されている。次の変異を入れても、この負例は引き続き不合格になるため全テストが緑のままである。

```python
# orchestrator/calibrator/cli.py:390
{"samples_mhz": effective_clock.get("samples_mhz")[1:]}
```

しかし candidate が `[3079.456] + [2101.0] * 47` なら、唯一の外れ値が捨てられて publish される。F108 では帯外位置が多数の index に分散しており、末尾固定は代表性を持たない。

根拠:

- `orchestrator/calibrator/cli.py:381-391`
- `orchestrator/calibrator/cli.py:608-615`
- `orchestrator/tests/test_calibrator_certify.py:531-577`
- とくに外れ値配置 `orchestrator/tests/test_calibrator_certify.py:533-537`
- 実位置の分散 `docs/failures.md:2353-2363`

塞ぎ方の提案:

48 全 index それぞれに単独外れ値を置く parameterized negative control を作り、全ケースで reason・非publishを確認する。少なくとも first/middle/last の3位置は必須。

**成果物影響:** 特定コア位置の帯外標本を持つ較正が accepted/published となり、certified 結果が自己不整合な参照を指す。

### [所見 A-3] High — observed 専用型だけでは、receipt と歴史 raw JSON から observed tolerance が判定へ混入する穴を閉じない

具体的な失敗シナリオ:

現行 issuer は observed tolerance を receipt から除いており、現時点の計算自体は expected tolerance のみを使っている。しかし receipt validator は nested observed mapping の key 集合を制約していない。

次の変異は、提案された unauthorized-100 vector を含むテストが observed tolerance を持たないため生存する。

```python
# orchestrator/campaign/execution_guard.py:195 相当
allowed_delta = (
    abs(expected_median)
    * float(observed.get("tolerance_pct", EFFECTIVE_CLOCK_TOLERANCE_PCT))
    / 100.0
)
```

その後、expected tolerance `2.0`、observed samples `[150.0]`、observed tolerance `100.0` の forged receipt を渡すと、`validate_receipt_v2()` は追加 nested key を許し、変異 consumer は通す。

歴史 raw evidence にも同型がある。`silo_ladder_rung1.py:3407` を expected から actual tolerance へ置換しても、fixture は actual profile を calibration から複製して両値を同じ `2.0` にしているため赤くならない。実 probe の旧 raw profile は `100.0` を持つ。

根拠:

- observed tolerance を除外する現行コード `orchestrator/campaign/env_attestation.py:545-547`
- consumer の現行取得元 `orchestrator/campaign/execution_guard.py:182-199`
- nested shape を閉じない validator `orchestrator/campaign/execution_guard.py:264-277`
- raw consumer `orchestrator/campaign/silo_ladder_rung1.py:1962-1965,3401-3415`
- tolerance を同値にする fixture `orchestrator/tests/test_silo_ladder_rung1_driver.py:1167-1169`
- probe serializer `tools/pegasus/run_probe.py:24-32,63-70`

塞ぎ方の提案:

receipt の effective-clock observed を exact `{"samples_mhz"}`、expected を exact `{"samples_mhz","tolerance_pct"}` として検証する。加えて observed に `100.0` を注入した hostile receipt/raw fixture が必ず拒否されるテストを置く。

**成果物影響:** forged receipt や歴史 raw bundle の observed `100` が受理帯を `[0,2×median]` へ広げ、材料レポートと試行台帳に偽の pass を残す。

### [所見 A-4] High — policy golden は値しか固定せず、各 consumer が正本を参照していることを証明しない

具体的な失敗シナリオ:

次の変異群は現 policy が `2.0` の間、提案テストをすべて通る。

- `orchestrator/calibrator/cli.py:551`: policy 定数の代わりに literal `2.0` を代入。
- `orchestrator/campaign/env_attestation.py:581`: `expected tolerance == 2.0` を直接検査。
- `orchestrator/campaign/execution_guard.py:189-195`: literal `2.0` を equality と delta に使う。
- loader にも `artifact.tolerance_pct == 2.0` を直接記述。

policy module 自身は正しく `2.0` なので AST/golden は緑、artifact test も literal `2.0` を期待するため緑である。つまり単一 policy 定数は存在するが、権威として load-bearing ではない。

根拠:

- policy test の設計範囲 `/work/1/SFC/tanab/dev-wave-jobs/t452-clock-tolerance-authority/out/s2-plan.md:11-17,92,105`
- producer の現挿入点 `orchestrator/calibrator/cli.py:549-551`
- issuer `orchestrator/campaign/env_attestation.py:576-592`
- consumer `orchestrator/campaign/execution_guard.py:182-199`

塞ぎ方の提案:

各層が module-qualified な同一識別子を参照することを AST で固定し、テスト中だけ policy を schema-valid な `3.0` に差し替えて producer・loader・issuer・consumer が一斉に追従する metamorphic test を置く。

**成果物影響:** 将来の policy 裁定変更時に層ごとに 2%/新値が分裂し、certified 結果・材料レポート・台帳で同じ trial の verdict が一致しなくなる。

### [所見 A-5] High — U-2 後の registry 不変条件には「self-pass 計算が実際に呼ばれた」負の control がない

具体的な失敗シナリオ:

U-2 後に既知例外を空へ反転した状態で、次の変異を入れる。

```python
# orchestrator/tests/test_env_contract.py:456
passes = True
```

`checked_required == 1`、`self_failures == set()`、artifact tolerance `==2.0` はすべて満たされる。現在の提案は空 loop は殺すが、非空 loop 内の constant-pass は殺さない。

この状態で policy `2.0` だが自己不整合な artifact を git 追加または attempt から複製し、registry の path+SHA を更新すると、loader は self-pass を検査しないため campaign まで到達できる。

根拠:

- 現 registry loop `orchestrator/tests/test_env_contract.py:436-463`
- loader は self-pass を行わない `orchestrator/campaign/env_attestation.py:674-692`
- loader self-pass を置かない裁定 `docs/decisions.md:7733-7738`
- 設計案の新 assertion `/work/1/SFC/tanab/dev-wave-jobs/t452-clock-tolerance-authority/out/s2-plan.md:99,107`

塞ぎ方の提案:

registry 検査を入力可能な production/helper 関数にし、SHAを整合させた schema-valid・policy一致・self-fail artifact を明示的に拒否する negative control を置く。

**成果物影響:** 自分自身を通さない登録参照が復活し、certified 選択を全面停止させるか、実 observed が中央値付近なら不正な参照のまま通過する。

### [所見 A-6] High — tolerance 値は守れても、CLI producer を通った artifact であることは証明できない

具体的な失敗シナリオ:

次の経路はいずれも policy `2.0` かつ self-pass な JSON を合成すれば、現在の設計では受理できる。

- git 直接追加
- rejected/accepted attempt からの複製
- 旧 worktree からの持ち込み
- registry pin だけの更新
- CLI 以外の producer
- fixture からの `CalibrationV2` / `VerifiedCalibration` 合成

loader が見るのは repo 内 path、SHA、schema、env_tag、clocks と予定される policy equality であり、acquisition receipt は job script SHA を持つが、policy module/source commit/publish receipt を束縛しない。また registry の canonical path test は `calibration/` 以下を要求するだけで `registered/` や content-addressed filename を要求しない。

根拠:

- loader `orchestrator/campaign/env_attestation.py:643-692`
- acquisition receipt fields `orchestrator/calibrator/schema_v2.py:393-416`
- canonical path の実範囲 `orchestrator/tests/test_env_contract.py:339-371`
- `VerifiedCalibration` の直接構築面 `orchestrator/campaign/env_attestation.py:69-97`
- CLI publish の実体 `orchestrator/calibrator/cli.py:629-653`

塞ぎ方の提案:

本設計の保証を「current admission における tolerance 値の固定」までと明記する。CLI provenance まで保証するなら、`registered/` の content-addressed path と producer/publish receipt の束縛を別の必須防壁として設計する。

**成果物影響:** tolerance は2%でも expected samples/median を人為的に選んだ artifact を登録でき、certified 受理集合と report/ledger の参照元を変更できる。

### [所見 A-7] Medium — schema の `100` 一点テストは `<100` という境界を固定しない

具体的な失敗シナリオ:

実装予定の条件を次のように変異する。

```python
# orchestrator/calibrator/schema_v2.py:238 相当
if tolerance == 100.0:
    _fail(...)
```

`2.0` positive control と `100.0` negative control はどちらも通るが、`100.001` や `1000.0` が schema-valid になる。現在の schema test にも上限超過ケースはない。

根拠:

- 現上限 `orchestrator/calibrator/schema_v2.py:235-239`
- 現 schema 負例集合 `orchestrator/tests/test_schema_v2.py:170-203`
- 提案テスト `/work/1/SFC/tanab/dev-wave-jobs/t452-clock-tolerance-authority/out/s2-plan.md:95,177-178`

塞ぎ方の提案:

`99.999...` を受理し、`100.0` と `100.0 + ε`、十分大きな有限値を拒否する境界テストを置く。

**成果物影響:** 他層が一度欠けると、schema-valid artifact の受理集合が100%超へ広がり、report/ledger が異常な tolerance を正規値として保持する。

### [所見 A-8] Medium — 入力面不在テストは文字列検索と `100` 拒否だけなので、別名・分割表記の option が生存する

具体的な失敗シナリオ:

CLI option を次のように戻す。

```python
# orchestrator/calibrator/cli.py:131 相当
p.add_argument("--effective-clock-" + "tolerance-pct", type=float)
```

値 `2.0` だけ受理するようにすれば、source に完全な flag 文字列はなく、`100` 指定も従来どおり拒否される。提案された source search と legacy-100 test は両方緑だが、U-2案Aの「option 完全撤去」は成立しない。別名 `--clock-window` や別名環境変数も同型である。

根拠:

- 現 parser `orchestrator/calibrator/cli.py:131-132`
- 現 shell surface `tools/pegasus/submit_certify.sh:7-42,177-178`
- job script surface `tools/pegasus/certify_calibration.sh:154-164,718-731`
- 提案テスト `/work/1/SFC/tanab/dev-wave-jobs/t452-clock-tolerance-authority/out/s2-plan.md:93-94,175-176,189-190`

塞ぎ方の提案:

parser action の `dest` 集合を検査し、旧 flag に `2.0` と `100.0` の双方を渡して attempt 前拒否を確認する。shell は任意追加引数・hostile env を実行テストで拒否させる。

**成果物影響:** 台帳に操作者指定値が入力であるかのような trial が残り、他の防壁が退行した際にはその入力面から受理集合を広げられる。

## 迂回経路の実効範囲

| 経路 | 設計後に守れる範囲 | 残る範囲 |
|---|---|---|
| 正規 CLI publish | 固定2%、self-pass、content-addressed publish | A-2の位置依存変異 |
| git直接追加・attempt複製・旧worktree | loader/registryが非2%とself-failを拒否する想定 | policy一致・self-passな合成 artifact の由来は証明しない |
| pinだけ更新 | SHAにより選んだbytesへ束縛 | production loaderはregistered path/content-addressed名を要求しない |
| CLI以外のproducer | 非2%はloader/issuer/consumerで拒否する想定 | policy一致artifactは受理可能 |
| fixture合成・`VerifiedCalibration` 直接構築 | issuer/consumerの重複検査が残れば非2%を拒否 | loaderを通った事実そのものは型で証明しない |
| monkeypatch | 通常production経路の保証対象外 | policy・loader・issuer・consumerを同時patchすればPython内防壁は迂回可能 |
| forged receipt/raw evidence | expected値との再照合あり | observed nested shapeがclosedでなくA-3が残る |

## `tolerance=100` の検算

`orchestrator/campaign/execution_guard.py:194-199` は、expected median を `m` として

```text
allowed_delta = |m| × 100 / 100 = |m|
|x - m| <= |m|
```

を計算する。schema-valid expected samples は正なので `m > 0`、したがって純述語の帯は厳密に `[0, 2m]` である。型付き observed profile は正値しか許さないため、schema 経由では実質 `(0, 2m]` になる。

literal な恒真ではない。`m=100` に対する `200.001` は落ち、既存 golden もそれを固定している `orchestrator/tests/test_execution_guard.py:461-470`。一方、登録 artifact は `m=2101.0`、上限 `4202.0` で、`3080.935` は帯内であるため100%では自己比較を通る `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440-1493`。設計案の「literal ではないが実質恒真」という記述は演算と一致する。

## 総括

**NO-GO。** 方針そのもの—単一2% policy、observed型分離、各 trust boundary の再検査—は妥当だが、提案された反証テストでは防壁が load-bearing になっていない。

実装前の必須修正は次のとおり。

- loader・issuer・consumer の負例を schema-valid な非policy値 `5.0`/`99.0` に変更する。
- 取得時 self gate を全48 index の単独外れ値で反証する。
- policy 正本への参照を、値一致ではなく wiring/metamorphic test で固定する。
- receipt と歴史 raw evidence の observed effective-clock shape を閉じ、observed tolerance 注入を拒否する。
- registry invariant に schema-valid・policy一致・self-fail の負例を与える。
- schema の100超境界と、CLI/shell input surface の意味的不存在を検査する。
- artifact provenance は tolerance authority の保証外であることを明記するか、別防壁として束縛する。