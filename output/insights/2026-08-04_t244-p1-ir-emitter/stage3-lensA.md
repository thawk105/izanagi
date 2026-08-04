# 判定

**NO-GO**。評価対象は `stage2-plan.md` の sha256 `67ec561e…`。コード変更・テスト実行・再実測はしていない。

## 所見

### 1. 「独立 golden」の四層は、実際には同一系譜を含む

- 判定: **real / scope 内**
- 成果物影響: 未是正なら「全32 mask監査済み」を台帳へ載せられず、P1 は未充足、cap-lift は FAIL のまま。certified 選択・正式レポート値は不変。

証拠の系譜は次である。

| 時点 | 成果物 | 実際の由来 |
|---|---|---|
| 2026-07-10 `31fde1f9` | 軸定数 | `GATEABLE_REASONS` を導入 |
| 2026-07-11 `8c97b6ab` | 旧 emitter | `predicate_for()` を実装 |
| 2026-07-11 `68b55f25` | campaign provenance | `_write_provenance()` が `candidates()`、すなわち旧 emitter の出力を `implementation` に再格納 |
| 2026-07-15 以降 | freeze | `_trigger_entries()` が provenance の `implementation` を直接コピー |
| 2026-07-23 `d50f714` / `69825792` | `s1_expected_goldens.py` | commit 本文どおり canonical freeze から生成スクリプトで転記 |
| 本 wave 予定 | 新 golden + 新 emitter | [brief が同じ実装子による単一所有](</work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s1-brief.md:86)を指定 |

つまり、

```text
旧 predicate_for
  └─ campaign provenance
       └─ known_axes / measurement freeze
            └─ s1_expected_goldens
```

であり、campaign 9点と freeze 3点は旧 emitter と共通祖先を持つ。実 campaign 6ファイルの非 stock entry は静的にはすべて `outcome=certified` だったため、歴史的 materialization 証拠としては有用だが、独立な期待 bytes ではない。[provenance producer](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/s8a_trigger_sweep.py:492>)、[freeze producer](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/s1_known_axes_freeze.py:471>)

計画自身も「過去の転記元は AST では証明できない」と認めているが、なお32行表を「基礎 oracle」と数えている。[stage2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage2-plan.md:134>) 同じ実装子が emitter・golden・比較 adapter を同時に書くなら、「先に手書きした」は最終 patch から監査不能である。

GO 条件は、golden を emitter author の編集所有から分離し、emitter 実装前に hash を凍結し、転記元を旧 emitter/campaign ではなく規範仕様として記録すること。旧 emitter 比較の mask→reason adapter も新 leaf の private mapping を使ってはならない。

### 2. `frozen=True` は32状態の閉包を保証しない

- 判定: **real / scope 内**
- 成果物影響: 未是正なら将来の受理集合に32値外の exact `TriggerGateIR` が入り、mask 32→mask 0、mask -1→mask 31 のような bytes alias が生じ、fitness 帰属を汚染し得る。現行 production は未配線なので今の certified 値は不変。

計画は emitter が exact `TriggerGateIR` の「32値だけ」を受けるとする一方、sink 側は exact-type guard だけで、mask invariant の再検証を予定していない。[API表](</work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage2-plan.md:34>) [実装予定](</work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage2-plan.md:89>)

Python の frozen dataclass は unforgeable value ではない。`object.__new__()` や `object.__setattr__()` で exact 型のまま `mask=-1/32` を作れる。予定される bit 0〜4 走査なら、それらは正規 mask の出力へ alias する。

`emit_wire()` と `emit_predicate()` の利用時にも exact int/range を再検証し、正常 constructor を通っていない exact 型の負例を追加する必要がある。現計画の「non-IR input 拒否」はこの負例になっていない。

### 3. 親 brief は P1 実装を名乗る文と、名乗らない文が矛盾する

- 判定: **real / scope 内**
- 成果物影響: 未是正なら worklog/decisions fragment が P1 を誤って充足扱いし、将来の cap-lift 裁定が偽前提を参照する。正式レポート・受理集合・certified 選択は変更してはならない。

brief の表題と scope は「D121 P1」「P1だけを実装する」と書く一方、同じ brief は「P1を満たしたと名乗らない」と書く。[scope](</work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s1-brief.md:5>) [自己限定](</work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s1-brief.md:55>)

D121 P1 は「候補表現が production で固定5-bit IRに閉じる」と「emitter監査」の連言である。本 wave は wiring せず、現行入口は任意 C++ `implementation: str` のままなので、P1 全体は偽である。[設計 §2.4](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/output/insights/2026-08-01_t244-reflux-design/README.md:95>) [D121](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/docs/decisions.md:5854>)

段2プランの過大表現禁止は正しい。段4では brief と記録文言を「P1用 leaf 部品／静的 emitter 一致検査」に固定し、P1 status は未充足のままにする必要がある。

### 4. fitness 帰属を守る end-to-end 防壁は未実装

- 判定: **real / scope 外 — 裁定パッケージ候補**
- 成果物影響: 現行 proposal 受理集合、build variant、WAL、材料レポート、proof chain、certified 選択はすべて不変。P1 と cap-lift は FAIL のまま。

本 wave が守るのは未使用 leaf の局所写像だけである。将来の D96 wiring wave では少なくとも次を一体で閉じる必要がある。

- 自由な `implementation` field の拒否
- wire→mask→predicate の唯一経路化
- raw mask、schema/emitter SHA、実際の source digest、variant ID の束縛
- WAL/provenance/report での同じ binding の要求
- binding 欠落 artifact の certified proof chain からの拒否
- 旧自由文字列経路・別 emitter 経路が残っていない負例

現プランはこれらを実装したふりにはしておらず、その限定自体は正しい。したがって本所見を今 wave の実装拡張要求にしてはならない。

### 5. brief の「JSON全拒否」は実現不能

- 判定: **real / scope 内**
- 成果物影響: raw parser の32文字列受理集合は変わらないが、台帳に「JSON由来も拒否」とは記録できない。

JSON decode 後の `"10100"` と通常の Python `str` は区別不能である。段2プランは正しくこれを指摘している。[stage2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage2-plan.md:46>) 段4では「raw parser に渡った container・引用符付き text・非正準値を拒否」へ限定するか、transport provenance を別 scope へ送る必要がある。

### 6. 凍結 bytes へ触る経路

- 判定: **refuted / scope 内**
- 成果物影響: 両 freeze JSON、axis/s8a、既存 campaign artifact の bytes・参照・正式成果物は不変。

編集所有は新規3ファイルだけで、既存ファイルは0 byte変更と明記されている。[stage2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/stage2-plan.md:158>) import・読み取り・差分比較は凍結 bytes を変更しない。`measurement_freeze.json` が個別列挙されていなくても「既存ファイル変更ゼロ」に包含される。

静的 hash は次だった。

- 現行 `axis_trigger_gating.py` = `47507d9b…c04c`、両 freeze 記録と一致。
- 現行 `s8a_trigger_sweep.py` = `8911dd24…857`、freeze の歴史記録 `3e94735a…a1` とは不一致。ただし `predicate_for()` 本体は git blame 上、2026-07-11 の初版から不変。

したがって「現行 s8a 全ファイルが freeze hash と一致」とは言えないが、本 wave に凍結抵触経路があるとの攻撃は refuted である。

## 親実測 A〜H の攻撃結果

| 項目 | 判定 | scope | 攻撃結果 | 成果物影響 |
|---|---|---|---|---|
| A | refuted | 内 | no-touch 結論は妥当。ただし現行 s8a 全体は歴史 pin と同一ではない | freeze bytes 不変 |
| B | real | 内 | 2026-07-11 から別実装なのは事実だが、時間的独立≠意味 oracle。軸仕様を共有 | 「独立意味証明」を監査文から除く |
| C | real | 内 | 6 record/3 mask は旧 emitter→provenance→freeze の下流 snapshot | 独立 anchor 数に加算不可 |
| D | real | 内 | 9 mask は旧 emitter が書いた provenance。歴史的 certified 記録だが独立期待値ではない | 「記録一致」まで。独立監査とは書かない |
| E | refuted | 内 | 32/32相異は必要条件のみ、とプラン自身が限定 | 台帳値変更なし |
| F | refuted | 内 | blacklist 検査でありcompile/副作用なしを証明しない、と限定済み | 意味安全の主張なし |
| G | refuted | 内 | stub 3 passed を最終 leaf の保証へ一般化していない | 最終実測前は緑を記録しない |
| H | refuted | 内 | dispatch 経路の実在だけと限定済み | 新テスト結果には算入しない |

## 成果物が効く層／効かない層

| 層 | 本 wave の検査が効く | 効かない |
|---|---|---|
| bit/wire schema | 正常構築された mask 0..31、LSB-first 32 wire | transport origin、forged exact IR |
| parser | raw `[01]{5}` と列挙した拒否クラス | JSON decode 前の provenance |
| predicate emitter | 32出力の静的 byte 一致、順序・空白・`;` | C++意味、production到達、23 maskの実 build |
| golden | runtime production import/Call の排除 | 誰が何から転記したか、同一作者の共通誤り |
| campaign/freeze | 歴史 bytesとの一致、9/3 mask被覆 | 旧 emitter から独立した期待値 |
| syntax gate | 現行 blacklistに引っ掛からないこと | 一般C++文法、副作用なし、auditor verdict |
| proposal ingestion | なし | 任意 `implementation: str` を引き続き受理 |
| quarantine/materialize | なし | mask→実 source bytes の唯一経路化 |
| build/variant identity | なし | raw maskとsource digest/variantのbinding |
| verifier/fitness | なし | 提案maskへのfitness帰属保証 |
| WAL/report/proof chain | なし | IR/schema/emitter proof要求、cap-lift結線 |
| freeze | 既存 bytesを変更しない scope gate | 新 leaf の正しさ証明ではない |

## nit

- `test_all_32_predicates_match_current_execution_gate_surface` は実態が blacklist 照合なので名前が強すぎる。
- `__all__` は star-import の公開集合であり、Python module の属性アクセスを閉じる防壁ではない。
- brief の「emit→parse→mask」は predicate emitter と wire emitter を混同しやすく、「emit_wire→parse_wire」に限定すべき。

## 総括

**NO-GO**

最大の3件は次である。

1. 旧 emitter・campaign・freeze・既存 golden が一本の系譜であり、新 golden も同じ実装子が書くため、「独立 golden」が監査可能になっていない。
2. frozen dataclass の exact-type guard だけでは32状態へ閉じず、forged exact IR が正規 mask bytesへ alias する。
3. brief の「P1を実装する」と「P1を満たしたと名乗らない」が矛盾し、未配線なのに台帳だけ充足へ進む経路が残る。