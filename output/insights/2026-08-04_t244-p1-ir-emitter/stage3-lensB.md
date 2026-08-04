判定は **NO-GO（現 brief / plan のままでは不可）**。指定 8 ファイルはすべて読取済み。静的レビューのみで、テストは実行していない。

## 所見

### 1. BLOCKER — D121 P1 の形式充足値は変わらない

判定: `real / scope 内（成功条件・記録）`  
production wiring の実装: `scope 外`

D121 P1 は「候補表現が固定 5-bit IR に閉じる」かつ「その正準 emitter が全 32 mask で監査済み」の連言である。[D121 P1](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/docs/decisions.md:5842)

しかし plan は、現行 `implementation: str`、`parse_coder()`、`load_proposal_file()`、直接 dataclass 構築をすべて残し、production から `reflux_ir` を参照しないことまで検査する。[stage2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage2-plan.md:201) したがって候補受理集合は引き続き任意の一行 C++ であり、追加する emitter は「production で使われる emitter」ではない。

brief の「P1 だけを実装する」と「P1 を満たしたと名乗らない」は自己矛盾している。[brief:5](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s1-brief.md:5) [brief:55](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s1-brief.md:55)

また「実装しなければ cap-lift が FAIL」は真だが、**実装しても同じく FAIL**である。P1 の候補閉包がなく、他の無条件義務も残るため、これは本 wave の限界効果を示していない。

価値が完全にゼロという攻撃は `refuted`。新テストが全 32 点で既存 sweep emitter と独立 literal を結べば、開発時の回帰検出力と将来 wiring 用の部品は増える。ただし価値は「監査済み standalone candidate」であり、実効 gate ではない。

成果物影響: 実装の有無で certified 選択、材料レポート、台帳値、D114 上限 1 は変わらず、D121 P1 は `FAIL / production_reachable=false` のまま記録しなければならない。

### 2. BLOCKER — 検査が効く層は test/development 層まで

判定: `real / scope 内・外混在`

| 層 | 本 wave が効くか | scope |
|---|---|---|
| `TriggerGateIR`、wire codec、standalone emitter | 明示 import した caller にだけ効く | 内 |
| test-local 32 literal、旧 emitter 差分、freeze/provenance 照合 | CI・素の runner で効く | 内 |
| 既存 `s8a_trigger_sweep.predicate_for` の drift | 新テスト実行時に赤くできる | 内 |
| coder role の JSON 出力契約・`GATING_SPEC` | 効かない。依然 `implementation` | 外 |
| `parse_coder()` / `load_proposal_file()` / dataclass 直生成 | 効かない | 外 |
| preview、DiffQuarantine、syntax gate、auditor | 効かない | 外 |
| hole materialization、build、C++ runtime | 効かない | 外 |
| exact-mask cut、禁止集合、query 消費 | 効かない | 外 |
| 拒否ログ・digest・whiteboard・journal・critic 投影 | 効かない | 外 |
| origin manifest の IR schema / emitter SHA 束縛 | 効かない | P3 との統合外 |
| cap-lift gate、formal consumer、proof chain | 効かない | 外 |
| production 受理集合 | 変わらない | 内の不変条件 |

scope 外の行を本 wave の成果に含めてはならない。真に P1 を満たすには、全入口を wire に閉じ、trusted emitter の出力だけを materialize する別 wave と D96 手続が必要になる。

成果物影響: 本 wave が変更できるのは source/test と「standalone 監査済み」という記録だけで、実 proposal・variant・certification・report の値は一切変わらない。

### 3. 正準 wire 自体の表記 side channel

#### 3-a. 空白・順序・同義表現が wire 内に残る、は反証される

判定: `refuted / scope 内`

長さ 5、ASCII `0|1`、位置 0 を LSB と固定すれば受理文字列は正確に 32 個で、各 mask の表現は 1 個である。[plan:72](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage2-plan.md:72) emitter も mask から決定的なら、述語の長さ・enum 列は mask の関数であり、同じ mask に対する追加選択 bit はない。

ただし emitted diff や SHA を untrusted role が見れば mask 本体の 5 bit は復元できる。これは P2 の観測面閉包であり、本 wave は解かない。

成果物影響: wire/emitter の表記自由度だけは 0 bit にできるが、production や generator 可視面の開示量は変わらない。

#### 3-b. brief の「JSON は全拒否」は実現不能

判定: `real / scope 内`

JSON decode 後の `"10010"` は通常の Python `str` と区別不能である。plan 自身はこの誤りを正しく認めている。[plan:66](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage2-plan.md:66) brief の表現を残すと、実装不能な由来判定を acceptance criterion にしてしまう。

成果物影響: 記録は「非 `str`、container、quoted/enveloped raw text、非正準文字列を拒否」に縮める必要があり、transport 由来拒否を名乗ってはならない。

### 4. BLOCKER — 拒否が「開示なし」になっていない

#### 4-a. 新 leaf の API 自体が拒否を分類する

判定: `real / scope 内`

plan は型不正を `TypeError`、値・範囲不正を `ValueError` と分ける。[plan:34](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage2-plan.md:34) エラーメッセージも固定・秘匿されていない。これだけで reject 条件下に少なくとも二分類が生まれ、将来既存 `_invoke()` に接続すれば例外型と全文が journal へ出る。

必要なのは、少なくとも untrusted 境界で全 invalid input が同一の型・同一の固定 payload・入力本文なしになる検査である。内部診断を保持するなら recipient projection で不可視であることが別途必要になる。

成果物影響: 現在の production 値は不変だが、このままでは leaf を「開示なしの拒否に利用可能」と監査済み扱いできない。

#### 4-b. 現行 production は拒否理由を多面開示している

判定: `real / scope 外（裁定パッケージ候補）`

現行経路には次がある。

- gate は subtype、reason、禁止識別子、violations 件数を digest・log・戻り値へ載せる。[gate:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/p3_s4_loop_trigger_gating.py:358)
- preview は `subtype`、`reason`、`forbidden_identifiers` を返す。[trial:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/p3_autonomous_workload_trial.py:560)
- role parse 失敗は例外型と文言を attempt journal に保存する。[trial:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/p3_autonomous_workload_trial.py:788)
- `rejected` は whiteboard・provenance に残り、critic は rejection digest を受け取る。[trial:1482](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/p3_autonomous_workload_trial.py:1482)

さらに T-409 plan は六種類の `reason_code` を新設し、preview/report へ残す。[T409 plan:29](/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:29) 式本文を消しても拒否 class の開示は残る。

成果物影響: 開示を閉じる場合は journal/report/preview/digest/critic/whiteboard の field・参照 schema が変わる。受理集合を変えずとも、既存 report と投影契約の別 wave が必要である。

### 5. MAJOR — bit schema・enum・module identity の drift 防壁が不足

判定: `real / scope 内（一部は統合 scope 外）`

plan の guard が見るのは `GATEABLE_REASONS` の名前と順序だけである。C++ enum 名は leaf と既存 `_CPP_ENUM` に重複し、T-409 の `trigger_gate_language.py` がさらに 8 enum member の第三 authorityを作る。

| drift | 何が赤くなるか | 赤くならないもの |
|---|---|---|
| `GATEABLE_REASONS` だけ変更 | leaf import 時 `RuntimeError`、新テスト | production は leaf を import しないので稼働継続 |
| 旧 `_CPP_ENUM` だけ変更 | 全 32 differential test | 現行構造テストは誤った既存 enum への置換を見逃し得る |
| leaf の enum/format だけ変更 | literal 32 と differential | — |
| wire encode の bit 方向だけ変更 | wire literal/round-trip | — |
| axis・leaf・golden・旧 emitter を協調更新 | historical anchor が当たる mask は赤 | schema version のない過去 wire の再解釈は検出不能 |
| C++ 骨格側だけ意味変更 | P1 テスト単体では赤にならない | 将来 compile/runtime で破綻 |
| `campaign.reflux_ir` と `orchestrator.campaign.reflux_ir` の二重 import | planned test なし | exact type 判定が同値 IR を拒否 |

最後の点は実在する import 形である。現 repo は package 実行と直接実行の両方を支え、型 identity を揃えるため特別処理も持つ。[trial:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/p3_autonomous_workload_trial.py:32) `type(ir) is TriggerGateIR` は別 module identity の同じ source から作った値を拒否する。

加えて public API に schema version、bit-definition manifest、schema digest がない。D121 と T-410 の確定契約は origin が IR schema と emitter に束縛されることを要求するため、P3 との結合点が欠けている。

成果物影響: このままでは origin ledger が正しい IR/emitter 参照を保存できず、過去 wire の意味と caller の受理が import path や将来の協調編集で drift する。

### 6. 並行 wave の衝突

| wave | 判定・scope | 衝突 |
|---|---|---|
| T-409 allowlist | `real / 実装は scope 外、調整は scope 内` | `s8a_trigger_sweep.py`、`test_s8a_trigger_sweep.py`、production gate、autonomous parser を変更予定。本 wave が read-only oracle/baseline とする面そのもの。さらに T-409 は 2^7 Boolean 方策と多数の表記を受理し、P1 の 32 正準形と両立しない |
| T-244 P3 ledger | direct path collision は `refuted`、統合欠落は `real / scope 外` | `reflux_origin_ledger.py` / `test_reflux_origin_ledger.py` と名称は別。ただし P1 は schema/hash を公開せず、P3 は P1 を計算しないため、両 leaf が緑でも origin→IR→emitter の鎖は存在しない |
| T-410 sort witness | direct code/test collisionは `refuted` | 現在の段 4 裁定は「この wave では実装しない」。[T410 ruling:3](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s4-ruling.md:3) したがって現時点の衝突は docs fold と意味上の origin binding だけ |
| docs | `real / scope 内の land 調整` | 全 wave が worklog/decisions/phase status を触る。spool は textual race を緩和するが、P1/P3 を互いに見ず「充足」と記録する semantic race は防がない |

特に T-409 は、freeze が source hash を pin している `s8a_trigger_sweep.py` を編集予定である。[T409 plan:150](/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:150) [known freeze](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/output/s1-freeze/known_axes_freeze.json:51) そのまま land すれば既存 proof-chain verifier が赤くなるか、編集を避ければ T-409 の materialization consumer 閉包が欠ける。

成果物影響: land 順を固定せず進めると、P1 differential oracle の基準、freeze source hash、production の受理文法、D121 status 記録が互いに異なる snapshot を指す。

### 7. production 受理集合の暗黙変更

判定: `refuted / scope 内`

現 plan は新規 3 ファイルだけを追加し、既存 production からの参照をゼロにする。`campaign/__init__.py` に自動 import もない。この差分単独では既存の受理・拒否挙動は変わらず、D96 手続の対象ではない。

ただし所見 1 を安易な wiring で直すと、自由な一行 C++ から 32 wire への縮小になるため直ちに D96 対象となる。T-409 が行う Boolean allowlist 化も別の受理集合変更であり、P1 wave の「不変」と混同してはならない。

成果物影響: 本 wave 単独では受理集合と既存期待値は不変。将来 wiring 時は新 D・境界テスト・consumer 閉包を同一変更単位にする必要がある。

### 8. 既存テストとの差分は実在するが、純増説明に誤りがある

#### 8-a. 既存被覆を「8 点」と数えるのは誤り

判定: `real / scope 内`

既存テストは `W.candidates(EFF3)` を反復し、これは 8 subset に `ident_all` を加えた **9 predicate** である。[existing test:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_s8a_trigger_sweep.py:92) `ident_all` により 5 enum 名も一度は通る。

また `s1_expected_goldens.py` は既に 3 distinct mask の predicate literal を持つ。[goldens:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/s1_expected_goldens.py:168)

成果物影響: 監査報告は「既存構造 9 出力、既存 literal 3 mask、全 32 literal/differential は未被覆」と訂正すべきで、独立 anchor 数を水増ししてはならない。

#### 8-b. 新テスト全体が重複、という攻撃は反証される

判定: `refuted / scope 内`

純増があるのは次である。

- IR 値型と非正準 wire の拒否
- 32 wire の全単射・round-trip
- 全 32 byte literal
- 旧 emitter との全 32 differential
- historical artifact と新 emitter の接続
- golden の runtime self-reference 防止

一方、次は検出力を重ねて数えてはならない。

- `test_axis_reason_order_matches_wire_schema` は import-time guard とほぼ同じ変異で赤くなる。
- freeze の「6 record / 3 mask」という件数自体は既存 golden が既に固定している。新規性は新 emitter への接続だけ。
- golden の import 禁止 AST は既存 `test_goldens_helper_is_independent_of_production` と同じ検査型だが、新ファイルを対象にするため検出力ゼロではない。

成果物影響: テスト数ではなく、未被覆 vector を「wire/parser、32 literal、32 differential、artifact→emitter 接続」の四つとして台帳化すべきである。

### 9. 親実測 A〜H の一般化

判定: `real / scope 内`

実測値自体は親測定として採用し、再実測していない。攻撃対象は推論である。

| 項目 | 許される結論 | 許されない一般化 |
|---|---|---|
| A | 現 axis bytes は pin と一致 | bit semantics や新 leaf の正しさ |
| B | 別時点・別 source の emitter がある | 独立 oracle である |
| C | 3 distinct mask の freeze anchor | 32 mask 全体の artifact 実証 |
| D | 偏った 9 mask の campaign 記録 | 残り 23 点、特に bit 1/4 singleton の実走 |
| E | 出力文字列が injective | bit→reason 対応・C++意味の正しさ |
| F | blacklist を通る | C++ 文法、副作用なし、`kUnset` 必在 |
| G | stub の存在とその文字列が repo scan/freeze 3 tests を壊さなかった | final leaf の import、golden/test 追加、plain runner、全 suite への無影響 |
| H | compute dispatch 経路が実在 | 本 wave のテストが緑 |

特に G の freeze tests は新 source 内容をほぼ観測せず、stub は import-time guard も exact-type API も test discovery も持たない。stage2 plan が最終 snapshot で repo-scan/freeze/plain-runner を再走するとした点は正しいが、G 自体を最終証拠へ昇格してはならない。

成果物影響: final snapshot の受入が完了するまで「既存検査に触らない」を記録できず、G の 3 passed を本成果物の緑として転記してはならない。

## nit

- `test_axis_reason_order_matches_wire_schema` は import guard と検出変異が同じで、主な価値は診断名だけ。
- P3 の durable origin ledger と区別するため、test-local golden を文書で単に「ledger」と呼ぶのは避けた方がよい。
- `predicate_for` は「既存別実装」であって「独立 oracle」ではない。plan は概ねこの区別をしている。

## 総括

**NO-GO。**

最大の 3 件は次である。

1. **production 到達性がゼロで、D121 P1・cap・certified 成果物の形式値は実装前後で同じ。**
2. **拒否が開示なしでない。新 API の例外分類に加え、現行/T-409 経路は reason・subtype・例外文言・digest を公開する。**
3. **IR schema/hash の結合点がなく、T-409 の別文法・旧 `_CPP_ENUM`・P3 origin ledger と authority が分裂する。**

GO にするには、wiring を本 wave に追加する必要はない。その代わり段 4 で、成果を「P1 component-only、P1 は FAIL」と明記し、opaque rejection 契約、versioned bit schema/emitter binding、dual-import 型 identity 検査を plan v2 に入れ、T-409 との land 順・freeze 処理・最終全 suite を固定する必要がある。