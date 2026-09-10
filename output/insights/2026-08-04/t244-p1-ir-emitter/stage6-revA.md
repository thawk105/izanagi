結論は **NO-GO**。静的レビューのみで、pytest・plain runner・変異は再実行していない。段 4 の是正 1〜7 のうち、2・6・7 は現物に入り、3 は段 7 記録前なので未確認。1・4・5 には実効性の穴が残る。

## 所見 1 — 是正 1: 現在の 32 点比較は実比較だが、golden 純粋性防壁は迂回できる

判定: **real（must-fix）**。ただし「現物が既に同じソースを二度読んでいる」という攻撃は **refuted**。

根拠:

- `EXPECTED_CASES` は現物では 32 行の直接 literal であり、production import・実行時 Call はない。[reflux_ir_expected_goldens.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/reflux_ir_expected_goldens.py:24)
- `_golden_rows()` は RHS を `ast.literal_eval` し、32 行を要求する。[test_reflux_ir.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:51) [test_reflux_ir.py:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:69)
- production 対 golden は明示的に `range(32)` を回して byte 比較する。例外の握り潰しや 0 回ループではない。[test_reflux_ir.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:179)
- `ast.Call` の見逃しという限定攻撃は refuted。module 全体を `ast.walk()` して Call を拒否している。[test_reflux_ir.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:142) [test_reflux_ir.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:158)
- しかし許可 AST の閉集合にはしていない。`FunctionDef` / `Lambda` / `Assign` / `Subscript` / `Attribute` は module 全体では拒否されない。さらに production module は golden より先に import 済みである。[test_reflux_ir.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:20) [test_reflux_ir.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:24)
- したがって golden が `sys.modules` 経由で `campaign.reflux_ir.emit_predicate` を、自身の literal 表を返す Call 無しの関数へ import-time 代入しても、import 名検査・Call 検査・production 側の文字列 consumer scanをすべて通過できる。[test_reflux_ir.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:145) [test_reflux_ir.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:160)
- また独立 golden の `EXPECTED_REASON_ORDER` は定義されるだけで、テストは `EXPECTED_CASES` しか import していない。[reflux_ir_expected_goldens.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/reflux_ir_expected_goldens.py:16) [test_reflux_ir.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:24)

成果物影響: 放置すると将来 golden の import-time 副作用で新 emitter 本体を検査せず「32/32 監査済み」と台帳化でき、cap-lift と certified 選択が偽の emitter 監査を参照する。現行成果物値は未配線なので不変。

scope: **内**。

## 所見 2 — 是正 2: forged exact IR と二重 import の指定ケースは実際に閉じている

判定: **refuted**。

根拠:

- constructor と sink は exact `int`、`0..31` を共通再検証する。[reflux_ir.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:55) [reflux_ir.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:82) [reflux_ir.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:86)
- テストは `object.__new__` と `object.__setattr__` で exact 型を実際に forge し、`-1`、`32`、`bool`、`int` subclass を両 sink に渡す。[test_reflux_ir.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:91) [test_reflux_ir.py:259](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:259)
- 二重 import は metaclass が二つの実在 module identity を認識する。[reflux_ir.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:61)
- テストも両型が別物であることを確認して両方の値を構成し、相手側の両 sink に渡している。[test_reflux_ir.py:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:270)

成果物影響: 指定された forged `-1/32` が正規 mask へ alias する経路と、通常の二重 import 値が拒否される経路は現物では塞がれている。現行 certified 値は不変。

scope: **内**。

## 所見 3 — 是正 3: 「P1 充足」と記録しないことはまだ検査不能

判定: **未確認**。

根拠:

- 段 4 は成果物名と「P1 未充足・production 到達性ゼロ」の台帳文言を固定している。[s4-ruling.md:73](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s4-ruling.md:73)
- 対象 3 ファイルの docstring は standalone IR/emitter/test-local golden の範囲に留まり、P1 充足を主張していない。[reflux_ir.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:2) [test_reflux_ir.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:2)
- ただし worklog・decision fragment・材料レポートはまだレビュー対象に存在しない。

成果物影響: 段 7 で P1 充足と書けば、production 到達性ゼロなのに cap-lift 台帳だけが前進する。

scope: **対象 3 ファイル外。wave の段 7 記録としては内**。

## 所見 4 — 是正 4: parser 本体は正しいが、正規化受理の防壁が恒真に近い

判定: **real（must-fix）**。

根拠:

- 現実装の受理集合は厳密に「exact `str`、長さ 5、全字 ASCII `0|1`」であり、32 文字列だけである。[reflux_ir.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:96)
- 正例 32 点、長さ 4/6、末尾 `'2'`、全角、`bool`、plain `int`、`str` subclass は実際に検査される。[test_reflux_ir.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:194) [test_reflux_ir.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:208)
- しかし空白例は `" 0000"`、`"0000 "`、`"0000\n"`で、strip 後も長さ 4 のままである。[test_reflux_ir.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:216)
- exact `str` にだけ `strip()` を適用する変異なら、`" 00000"` や `"00000 "`を新たに受理する一方、現 negative 集合は全部拒否のままになる。事前登録 V8 は `isinstance` も同時に導入するため `StrSubclass("00000")` の型正規化でも失敗し得て、whitespace 受理を単一理由で証明しない。[mutation-spec.json:125](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/mutation-spec.json:125)
- 未列挙クラスは whitespace-wrapped canonical、引用符付き canonical (`"\"00000\""`)、混在 Unicode digit、`int` subclass、`None`、float、tuple/set/bytearray 等。後半の多くは現実装では既存の非 `str`/不正文字分岐と同値だが、先頭二つは正規化・封筒除去変異の独立クラスである。

成果物影響: 正規化変異が侵入すると同じ mask に複数 wire が生まれ、将来の source digest・variant ID・proof binding が非正準表記で分岐する。現行 certified 値は未配線なので不変。

scope: **内**。

## 所見 5 — 是正 5: 固定 message は実装済みだが、「開示 0 bit」は成立しない

判定: **real（must-fix）**。

根拠:

- 通常の値拒否は一つの `RefluxIRError` と固定 `"invalid reflux IR"` に集約されている。[reflux_ir.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:21) [reflux_ir.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:47)
- しかし `_capture_rejection()` が見るのは exact type、`vars(exc)`、`str(exc)`だけである。`args`、`repr`、`__traceback__`、`__cause__`、`__context__`、`__suppress_context__` は未検査。[test_reflux_ir.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:81)
- 同じ `encode_wire` でも non-IR は `_mask_from_ir()` の型拒否を通り、forged 範囲外 mask は別の `_validate_mask()` 経路を通るため、traceback の frame/line が異なる。[reflux_ir.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:86) [reflux_ir.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:93)
- `object.__new__(TriggerGateIR)` だけで `mask` を設定しない exact forged 値では、`ir.mask` の `AttributeError` を捕捉中に `_reject()` を呼ぶため、公開例外の `__context__` に元の失敗が残る。[reflux_ir.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:89) テスト helper は常に `mask` を設定するためこの経路を構成しない。[test_reflux_ir.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:91)
- IR subclass は `isinstance` で受理されるので、`mask` access が入力由来の `ValueError` 等を送出すれば、その本文も `__context__` から漏らせる。
- 二重 import では `RefluxIRError` も各 module で別クラスとして定義されるが、統一検査は `IR` 側だけで、`ORCH_IR` の拒否型を比較していない。[test_reflux_ir.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:240)
- 直接の `__cause__` は通常 `None`、通常例の `repr` は固定 message 由来なので、そこから既に漏れているという攻撃は refuted。ただし検査はどちらも pin していない。

成果物影響: 将来 journal/report が traceback・context・module 型 identity を保存すると拒否理由が分類可能になり、材料レポートと台帳の開示 0-bit 契約が破れる。二重 import 側例外を catch できず処理結果が変わる可能性もある。

scope: **leaf と新テストは内。既存 journal/report 多面開示の是正は段 4 裁定どおり外**。

## 所見 6 — 是正 6: 最小 schema identity は置かれている

判定: **refuted**。

根拠:

- `SCHEMA_ID = "izanagi-trigger-gate-ir/v1"` が公開 API に含まれる。[reflux_ir.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:10) [reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:19)
- テストも `str` かつ `/v1` を要求する。[test_reflux_ir.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:97)
- digest pin や P3 ledger 結合は入っておらず、段 4 の限定に一致する。

成果物影響: 将来 origin ledger が参照できる versioned identity は存在するが、現行 certified 選択・材料レポート・台帳値は変わらない。

scope: **内**。

## 所見 7 — 是正 7: freeze 6 record と campaign 9 点の過大表現は是正済み

判定: **refuted**。

根拠:

- freeze test は docstring で「6 records だが 3 distinct masks、6 anchors ではない」と明記し、件数 6 と集合 `{4,8,31}` を別々に検査する。[test_reflux_ir.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:311)
- record loop の前に `len(records) == 6` があり、0 回ループではない。[test_reflux_ir.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:320)
- campaign は 9 entry の literal mappingを持ち、テスト名・docstringとも「historical artifact only」で独立 oracle と名乗らない。[test_reflux_ir.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:38) [test_reflux_ir.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:329)
- 親提示の `axis_trigger_gating.py` / `s8a_trigger_sweep.py` 0 byte 変更とも矛盾しない。

成果物影響: freeze を独立 anchor 6 個、campaign を独立 anchor 9 個として水増しする経路は対象テストの文言から除かれている。

scope: **内**。

## 所見 8 — 現物の主要ループが 0 回・例外握り潰しという攻撃

判定: **refuted**。

根拠:

- golden、legacy differential、wire codec はそれぞれ明示的に `range(32)` を回す。[test_reflux_ir.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:179) [test_reflux_ir.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:186) [test_reflux_ir.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:194)
- golden の mask 欠落・重複は参照時の失敗または集合検査で落ち、predicate/wire の重複も明示的に落ちる。[test_reflux_ir.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:169)
- plain runner は AssertionError とその他 Exception をともに `failed += 1` へ送る。[test_reflux_ir.py:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:345)

成果物影響: 現物の「32 点」「6 record」「9 entry」は空ループ由来の偽合格ではない。ただし上記 3 must-fix の検出力までは 18 passed から一般化できない。

scope: **内**。

## nit

- plain runner は `tests` が空でも 0 を返すため、将来 discovery 名が全消失した場合は fail-open になる。[test_reflux_ir.py:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:345) 現物では test 関数が存在するため今回の 0 回攻撃とは別。
- `SCHEMA_ID` の検査は `/v1` suffix のみで、完全な identity literal は pin しない。[test_reflux_ir.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:106)
- `test_all_32_...independent_golden...` の「独立」はテスト単体で証明されず、親提示の所有分離・実装前 hash 凍結という工程証拠に依存する。現物と提示証拠は整合している。

## 総括

**NO-GO**。must-fix は **3 件**。

最重要は、golden module の AST 防壁が Call と直接 production import だけを禁じ、Call 無しの import-time monkeypatch を許す点である。これにより新 emitter 本体を読まずに「独立 golden と 32/32 一致」を成立させられ、段 4 の最重要是正を再び恒真監査へ戻せる。