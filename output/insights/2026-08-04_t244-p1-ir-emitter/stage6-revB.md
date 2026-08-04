結論は **NO-GO**。静的検査のみを行い、編集・pytest・plain runner の再実行はしていない。親の `18 passed` は receipt の事実としてのみ扱う。

### 1. 骨格 patch が executable authority に結び付いていない

- 判定: **real（must-fix）**
- 根拠: leaf は C++ 識別子を private literal として複製している（[reflux_ir.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:31)）。旧実装にも別の `_CPP_ENUM` がある（[s8a_trigger_sweep.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/s8a_trigger_sweep.py:117)）。一方、規範の骨格 patch は enum を定義している（[silo-backoff-trigger-gating-variant.patch:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/patches/silo-backoff-trigger-gating-variant.patch:56)）が、新テストの入力 path は golden、production、freeze、provenance だけで patch がない（[test_reflux_ir.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:26)）。golden の docstring は patch 由来と主張するだけである（[reflux_ir_expected_goldens.py:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/reflux_ir_expected_goldens.py:5)）。
- drift 行列:

  | 変更 | 静的に検出する箇所 |
  |---|---|
  | `GATEABLE_REASONS` だけ変更 | import guard（[reflux_ir.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:43)）。明示テスト（[test_reflux_ir.py:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:281)）は同じ vector |
  | leaf literal だけ変更 | golden 比較と旧実装比較（[test_reflux_ir.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:179)、[test_reflux_ir.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:186)） |
  | `_CPP_ENUM` だけ変更 | 旧実装差分比較 |
  | 骨格 patch だけ変更 | **新規 3 ファイルの検査は無反応** |
  | leaf・旧実装・golden を同時変更 | 歴史 artifact が旧 bytes のままなら mask 31 等で検出。ただし独立 authority ではない |

- 成果物影響: patch の relevant member・変数名が変わっても監査済みを名乗れてしまい、将来 wiring 時に C++ コンパイル失敗または別対象への述語生成を招く。
- scope: **内**。patch を変更する必要はなく、新テスト側で relevant token を現物から検算できる。

### 2. `TriggerGateIR` subclass が統一拒否面を迂回する

- 判定: **real（must-fix）**
- 根拠: metaclass は最初に通常の `isinstance` を受理するため、任意 subclass が通る（[reflux_ir.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:65)）。sink はその後 `ir.mask` を評価するが（[reflux_ir.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:89)）、捕捉対象は `AttributeError/TypeError/ValueError` だけである（[reflux_ir.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:91)）。`mask` property が `RuntimeError` 等を投げる subclass は固定 `RefluxIRError` を迂回できる。テストしている subclass は mask 値の `int` subclass だけ（[test_reflux_ir.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:116)）で、IR subclass はなく、forged 検査も exact 型に限定される（[test_reflux_ir.py:259](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:259)）。
- 成果物影響: 将来 untrusted 境界へ wiring した際、例外型・メッセージの理由チャネルまたは処理中断が復活し、「公開 rejection は一型一文言」が偽になる。
- scope: **内**。

### 3. plain runner は README の `Skip` 契約を満たしていない

- 判定: **real（must-fix）**
- 根拠: 二重-runner 契約は `FAIL/ERROR/SKIP` の別計数を要求する（[README.md:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/README.md:107)）。`skiputil.Skip` は `Exception` subclass である（[skiputil.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/skiputil.py:14)）。新 `_run()` は `Skip` を捕捉せず generic `Exception` を ERROR/failed に入れ、`skipped` は常に 0 のまま（[test_reflux_ir.py:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:345)、[test_reflux_ir.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:357)）。メタテストは `_run(` という lexical signal しか確認しないため（[test_plain_runner_coverage.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_plain_runner_coverage.py:25)）、この不履行を検出しない。
- 成果物影響: 将来許可された dependency skip が ERROR/rc=1 に化け、plain runner の記録と検出力会計を誤らせる。
- scope: **内**。

### 4. `SCHEMA_ID` の identity が試験されていない

- 判定: **real（should-fix）**
- 根拠: 公開値は `"izanagi-trigger-gate-ir/v1"`（[reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:19)）だが、テストは `endswith("/v1")` だけ（[test_reflux_ir.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:106)）。したがって `"unrelated/v1"` への変更を検出しない。D121 の将来 origin preimage は IR schema を束縛対象とする（[decisions.md:5831](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/docs/decisions.md:5831)）。
- 成果物影響: P3 wiring 後に同一 schema のつもりで origin が分裂・混同する変更を、P1 の公開 API テストが止められない。
- scope: 定数の exact pin は **内**、origin ledger への配線は **外**。

### 5. discovery・fixture・repo scan の直接破壊は見つからない

- 判定: **refuted**
- 根拠: pytest は `orchestrator/tests` を収集する（[pytest.ini:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/pytest.ini:13)）。新 test は 15 個の `test_` 関数と `__main__` harness を持ち（[test_reflux_ir.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:97)、[test_reflux_ir.py:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:364)）、golden は `test_*.py` でない。fixture 引数はなく、conftest の group hook は既存 exact node のみを扱う（[conftest.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/conftest.py:129)）。repo scan は untracked file も列挙するが（[s8b_holdout_freeze.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/s8b_holdout_freeze.py:197)）、同一ファイルで三軸すべてに一致した場合だけ hit とする（[s8b_holdout_freeze.py:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/s8b_holdout_freeze.py:270)）。3 対象にその conjunction はなかった。
- 成果物影響: 現物上、新規 test 15 node が追加される以外に、既知 repo-scan hit 集合や fixture 排他集合は変わらない。
- scope: **内**。

### 6. `18 passed` を repo 全体の非回帰へ一般化できない

- 判定: **未確認**
- 根拠: receipt の対象は `test_reflux_ir.py` と `test_plain_runner_coverage.py` の二つだけ（[receipt.json:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/output/pegasus-dispatch/f655355afa16ad59a4b1389ff93cf785/receipt.json:50)）。記録された 18 items は（[s6-targeted.log:15](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s6-targeted.log:15)）、新 test 15 node とメタテスト 3 node の合計である。メタ 3 個のうち、新ファイルを直接査定するのは全 test file を列挙する一つだけ（[test_plain_runner_coverage.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_plain_runner_coverage.py:60)）。また pytest 実行であり、`python3 test_reflux_ir.py` の plain path はこの receipt の対象ではない。
- 成果物影響: 台帳へ書けるのは「targeted 2 file・18 node」であり、「既存全テスト不変」「二重 runner を双方実測」は書けない。
- scope: **内**。追加実測を要求する所見ではなく、記録射程の限定である。

### 7. S1 freeze・manifest・12/51 closure への書込み経路はない

- 判定: **refuted**
- 根拠: 新テストは `known_axes_freeze.json` を `read_text` するだけ（[test_reflux_ir.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:28)、[test_reflux_ir.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:313)）。`measurement_freeze.json` は読まない。生成・書込み API は別 module に存在するが（[s1_known_axes_freeze.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/s1_known_axes_freeze.py:769)）、3 対象から呼ばれない。既存 `FROZEN_MANIFEST` は S1 の二 JSON を byte hash で pin する（[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_frozen_artifacts.py:38)）ため、将来の JSON byte 不一致は manifest 検査が担当する（[test_frozen_artifacts.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_frozen_artifacts.py:125)）。新テストはそのうち known-axes の gate 6 records だけを意味比較する（[test_reflux_ir.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:311)）。
- `changed 12 / unchanged 51` は repo 全ファイルの監視ではなく、JSON 内の exact 63 source record を migration basis と比較する分類である（[t080_freeze_migration.py:974](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/t080_freeze_migration.py:974)、[t080_freeze_migration.py:995](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/t080_freeze_migration.py:995)）。新規 3 path はその 63 record に含まれないので、追加自体は 12/51 を変えない。
- 成果物影響: freeze bytes、manifest、63-record closure は不変。将来 known-axes の gate bytes がずれれば新テストも検出するが、measurement や無関係 field は manifest 側だけが担当する。
- scope: **内**。

### 8. 現在の production 到達性と受理集合は不変

- 判定: **refuted**
- 根拠: leaf 自身の dual-import 用文字列を除く production consumer の import/call は静的 `rg` で 0 件だった。現存 import はテストの二経路だけ（[test_reflux_ir.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:21)、[test_reflux_ir.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:23)）。`campaign/__init__.py` は docstring のみで自動 import がない（[campaign/__init__.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/__init__.py:1)）。
- ただし新テストが走査しているのは「production が golden を consumer にしていないこと」であり（[test_reflux_ir.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:160)）、将来の production→`reflux_ir` import を機械的に禁止する検査ではない。現在の 0 件は commit-scoped 静的事実として書くべきである。
- 成果物影響: 現在の既存 acceptance/rejection と certified 選択には到達経路がなく、D96 はこの差分では発動しない。将来 consumer が一つでも入れば別途 D96 対象になる（[s4-ruling.md:115](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s4-ruling.md:115)）。
- scope: 現在値の検算は **内**、production wiring は **外**。

### 9. T-409 が先に land しても、計画どおりなら differential 比較は失敗しない

- 判定: **refuted**
- 根拠: T-409 の計画は `s8a_trigger_sweep.py` の書込み前・build 前へ checker を加えるもので（[stage2-plan.md:150](/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:150)）、`predicate_for` の byte 生成を変える計画ではない。現在の差分 oracle はその `predicate_for` の返り値だけを比較する（[test_reflux_ir.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:186)）。
- 静的判定は次のとおり。

  - checker 追加だけなら、本 wave の differential assertion が失敗するとは予測しない。
  - `_CPP_ENUM` または `predicate_for` の bytes が変われば、これは frozen golden に対する**真の byte drift**であり、偽赤ではない。正当な仕様変更でも無調整 land を止める挙動は正しい。
  - allowlist だけが同じ predicate を拒否する変更は、本テストには見えない。これは偽赤でなく**偽陰性**である。T-409 後は全 32 emitter 出力を新 checker に通す統合検査が望ましい。T-409 自身の予定検査は「全生成候補」である（[stage2-plan.md:192](/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:192)）ため、32 mask 全域と同義とは限らない。

- 成果物影響: predicate bytes の drift は安全に止まる一方、language authority だけの drift は将来 materialization 時まで潜伏し得る。
- scope: land 順と post-rebase 統合確認は **内**、T-409 checker 本体の設計変更は **外**。

### 10. 予定台帳は概ね正しいが、限定なしでは過大表現になる

- 判定: **real**
- 根拠と推奨文言:

  - 「D121 P1 の機械部品を実装」は、上記 must-fix を閉じるまでは「**候補機械部品**」へ弱める。閉じた後は「固定 5-bit IR、LSB-first wire codec、predicate emitter の standalone leaf」と具体化できる。`production 到達性ゼロ、P1 未充足` は正しい（[s4-ruling.md:77](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s4-ruling.md:77)）。
  - 「独立起草の golden」は維持できる。golden 子は旧実装・campaign・freeze・leaf を不読と記録している（[stage5-golden.md:5](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage5-golden.md:5)）。ただし leaf 子は、初稿後に除外不良の `rg` が golden を走査した可能性を申告している（[stage5-leaf.md:12](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage5-leaf.md:12)、[stage5-leaf.md:16](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage5-leaf.md:16)）。したがって「golden は別所有・実装前 hash 固定」は言えるが、「emitter 子は golden に一切接触していない」「完全 blind」は言えない。
  - 「freeze の 6 record」は「**`known_axes_freeze.json` の gate predicate 6 records、相異 mask `{4,8,31}` の3種**」まで限定すれば、より強く正確に書ける（[test_reflux_ir.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:320)）。S1 freeze 二 JSON 全体の話には広げない。
  - 「campaign 記録の 9 mask」は「**指定した provenance 1 ファイルの非-stock 9 named entries**」と書くのが安全（[test_reflux_ir.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:29)）。現在値は `{0,1,4,5,8,9,12,13,31}` の9相異 mask（[test_reflux_ir.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:38)）だが、テストは `len == 9` のみで値の相異性を明示 assertion していない（[test_reflux_ir.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:339)）。
  - 「cap-lift は FAIL のまま」は正しい。さらに「D114 の上限 1 を変更せず、P1 の production 到達性も、P2/P3/P5/P7/P9/P10 もこの wave では充足しない」と強く書ける（[decisions.md:5845](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/docs/decisions.md:5845)、[decisions.md:5863](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/docs/decisions.md:5863)）。

- 成果物影響: 限定を落とすと、将来の cap-lift 裁定が「完全 blind・production-ready・複数独立 oracle」という実在しない前提を参照する。
- scope: **内**。

### 11. 検出力を 18、32+32+6+9 と数えるのは水増し

- 判定: **real**
- 根拠: predicate の独立な証拠系譜は、別起草 literal golden と旧 `predicate_for` differential の **2 系譜**だけ（[s4-ruling.md:58](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s4-ruling.md:58)）。freeze 6 と campaign 9 は旧実装から materialize された歴史 artifact なので、独立 oracle の純増は **0**。また 32 は入力点数であって vector 数ではない。
- 段4の V1–V16（[s4-ruling.md:142](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s4-ruling.md:142)）を同じ検出面で束ねると、静的 fault-class vector は **11 本**:

  1. emitter exact bytes（V1–V5）
  2. wire bit order（V6）
  3. parser 非正準受理（V7–V8）
  4. mask exact scalar domain（V9）
  5. sink 再検証（V10）
  6. dual import（V11）
  7. rejection disclosure（V12）
  8. golden 内容破損（V13）
  9. golden 実行時依存・consumer 混入（V14）
  10. 正準 32 点の過剰拒否防止（V15）
  11. axis order drift（V16）

  V1–V5 は異なる変異例だが、検出署名は同じ exact-byte 比較群である。axis import guard とその fake-module test も一つの vector である。実 mutation の kill 実測は提示された `18 passed` からは確認できないため、`KILLED 11` とまでは書けない。

- 成果物影響: 水増しすると「監査済み」の根拠密度を過大評価し、patch authority や T-409 allowlist という未検出方向を隠す。
- scope: **内**。

### nit

- `EXPECTED_REASON_ORDER` は定義されるだけで、テストにも leaf にも消費されない（[reflux_ir_expected_goldens.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/reflux_ir_expected_goldens.py:16)）。変更しても検査結果に影響しないため、authority を装う dead literal である。

## 総括

**NO-GO**。

must-fix は **3件**。

1. 骨格 patch と emitter/golden の relevant C++ token を executable に束縛する。
2. `TriggerGateIR` subclass／異常 attribute 経路でも一型一文言を守る。
3. plain runner で `skiputil.Skip` を SKIP として別計数する。

最重要は **骨格 patch authority の未束縛**。現状は actual C++ skeleton だけが drift しても新規検査がそれを観測せず、「32 mask 監査済み emitter」という将来の proof 前提を偽のまま land できる。