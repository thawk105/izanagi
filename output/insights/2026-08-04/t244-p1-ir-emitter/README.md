# [T-244] D121 P1 の機械部品 — 固定 5-bit IR と正準 emitter (2026-08-04)

**authority:** 本 dir が本 wave の逐語・実測の正本である。設計本文の正本は
`output/insights/2026-08-01_t244-reflux-design/README.md` と
`output/insights/2026-08-03_t244-p6-contract/README.md`、決定の正本は D121 である。

## 1. この wave が作ったもの / 作っていないもの

**作った:** D121 決定 (7) の前提条件 P1 が要求する**機械部品**。新規 leaf
`orchestrator/campaign/reflux_ir.py` (固定 5-bit IR の値型・正準 wire codec・正準 C++ emitter)、
独立 golden 台帳 `orchestrator/tests/reflux_ir_expected_goldens.py`、
テスト `orchestrator/tests/test_reflux_ir.py`。

**作っていない (名乗ってはいけないこと):**

- **P1 は充足していない。** P1 は「候補表現が固定 5-bit IR に閉じる」かつ「正準 emitter が
  全 32 mask で監査済み」の連言である。本 wave は production へ wiring しないため、
  候補の受理集合は従来どおり任意の 1 行 C++ のままであり、**production 到達性はゼロ**である。
- **cap-lift は依然 FAIL である。** D114 の `MAX_APPROVED_GENERATIONS = 1` は変えていない。
  P2 / P3 / P5 / P7 / P9 / P10 も本 wave では 1 件も充足しない。
- 規律 3 の還流、軸 (i)、failure reason constraint のいずれも実現していない。
- side channel が無いとは言えない。表記由来の追加 bit が 0 なだけで、membership oracle・
  transport・P2 の非干渉は未解決である。
- JSON 由来の入力を拒否するとは言えない (decode 後の `str` は通常の `str` と区別できない)。

## 2. 中心的な発見 — 「独立 golden」は一本の系譜だった

段 2 のプランは独立 golden を四層 (凍結 bytes 3 点 / campaign 記録 9 点 / literal 32 点 /
既存実装との差分 32 点) で構成する案だった。**段 3 の敵対レンズ 2 本が独立に**、これらが
実は一本の系譜であることを指摘し、親が実測で裏取りした。

```
旧 predicate_for (s8a_trigger_sweep.py:215、2026-07-11)
  └─ campaign provenance (_write_provenance が candidates() の出力を implementation へ格納)
       └─ known_axes / measurement freeze (_trigger_entries が provenance を複写)
            └─ s1_expected_goldens.py (freeze から転記)
```

したがって **campaign 9 点と freeze 3 点は独立な期待値ではない**。「歴史的 materialization の
記録」であって、独立 anchor として点数に加算してはならない。この構成のまま単一の実装子が
golden と emitter を同時に書けば、監査は恒真になっていた。

## 3. 是正 — 独立性を「順序」で担保した

段 4 で実装子を**所有分離した 2 体・直列**に変えた。

1. **子 G** が `reflux_ir_expected_goldens.py` **だけ**を書く。旧 emitter・campaign provenance・
   freeze・既存 golden・(未作成の) leaf を**読むことを禁止**し、親が段 4 で宣言した規範仕様と
   骨格 patch `patches/silo-backoff-trigger-gating-variant.patch` だけから 32 行を導出させた。
2. **親が hash を凍結。** 子 E を起動する**前に** sha256
   `641f89ca02b8b0b3e85ff679fc7c0656058e9570fc558356e2c36ff35cee1f9f` (8918 bytes) を記録した。
3. **子 E** が leaf とテストを書く。golden の中身と `predicate_for` の実装本文を読むことを禁止。

**規範仕様の順序規則は親が段 4 で宣言したものである** (軸 docstring の要因定義順に由来)。
旧実装との一致は差分結果であって恒真ではない。

## 4. 親が実測した監査結果

| 検査 | 結果 |
|---|---|
| golden の mask 被覆 | 0..31 を過不足なく 32 点、wire・predicate とも一意 |
| golden の wire | 全点で LSB-first 表現と一致 |
| **golden vs 旧 `predicate_for`** | **32/32 byte 一致** (独立起草どうしの差分結果) |
| **golden vs 凍結 freeze** | `known_axes_freeze.json` の `gate_predicate` **6 record**、
相異 mask は **3 点 `{4, 8, 31}`** |
| campaign provenance | 指定 provenance の非 stock **9 named entry**、相異 mask `{0,1,4,5,8,9,12,13,31}`。
**歴史的 artifact との一致であって独立 oracle ではない** |
| golden の hash | 子 E・fix 子の作業後も凍結時と**不変** |
| 新テスト (fix 前) | 計算ノードで 18 passed (request `884332.nqsv`) |
| 対象走行 (fix 後) | 58 passed (request 収集は `s6-postfix.log`) |
| **全走 (fix 後)** | **5447 passed / 1 failed / 19 skipped** (request `884462.nqsv`) |
| provenance 監査 | 963 件、違反なし (request `884676.nqsv`) |

**唯一の赤は本 wave の差分に帰属しない。** `test_ruleops.py::test_real_checkout_independent_
maximum_package_and_runner_preflight@real_repo` は `tools/ruleops.py inventory` が
`output/insights/2026-08-03_t361-t362-cluster-probes/.../home-read-write.probe.raw` を
非 UTF-8 blob として rc=2 で拒否するために落ちる。**本 wave の 3 ファイルが存在しない
ユーザーの元 checkout でも同一の rc・同一の blob で再現する**ことを親が実測した。
この件は並行 wave `wave-t407-ruleops-binary-blob` が所有する。

## 5. 段 6 の敵対レビューが見つけたもの (2 本とも NO-GO)

| # | 所見 | 対応 |
|---|---|---|
| F1 | golden 純粋性の AST 防壁が迂回できる (許可 AST が閉集合でなく、Call 無しの import 時差し替えが通る) | closed — 許可ノードの閉集合へ |
| F2 | 「正規化すると正準になる」負例が無く、**事前登録した変異 V8 (`strip()` 追加) を単一理由で殺せない** | closed — 空白・引用符で包まれた正準文字列を追加 |
| F3 | 拒否の `__context__` に元例外が残る。`args`/`repr`/`__cause__`/`__context__` が未検査 | closed — `from None` 化 + 両 import 経路で全項目を検査 |
| F4 | `TriggerGateIR` subclass の `mask` property が `RuntimeError` を投げると統一拒否面を迂回 | closed — `except Exception` へ統一 |
| F5 | 骨格 patch が executable authority に束縛されておらず、patch だけの drift を検出しない | closed — テストが patch を読んで token を検算 |
| F6 | plain runner が `skiputil.Skip` を捕捉せず `skipped` が常に 0 | closed — Skip を別計数 |
| F7 | `SCHEMA_ID` が `endswith("/v1")` だけで `"unrelated/v1"` を通す | closed — exact pin |

## 6. 検出力の正直な会計 (水増ししない)

- **独立な証拠系譜は 2 系譜だけ**である: ① 別所有・実装前 hash 固定の literal golden 32 点、
  ② 旧 `predicate_for` との全 32 点差分。freeze 6 record と campaign 9 mask は旧実装から
  materialize された歴史 artifact なので、**独立 oracle の純増は 0** である。
- 32 は**入力点数**であって vector 数ではない。「32+32+6+9」や「テスト 18 本」を
  検出力として数えてはならない。
- 静的な fault-class vector は **11 本** (emitter exact bytes / wire bit order / parser 非正準受理 /
  mask exact scalar domain / sink 再検証 / dual import / rejection disclosure / golden 内容破損 /
  golden 実行時依存 / 正準 32 点の過剰拒否防止 / axis order drift)。
  fix で patch authority・subclass 拒否・Skip 契約・SCHEMA_ID の 4 面が加わった。

## 7. 独立性の限界 (正直に書く)

- 子 G は禁止 6 対象を不読と報告している。
- 子 E は、consumer 検索時の `rg` で除外 glob が効かず golden を走査した可能性を自己申告した。
  **親が実測したところ、その rg パターン (`reflux_ir_expected_goldens|reflux_ir`) に一致する行は
  golden ファイルに 0 行存在しない**ため、golden の内容が出力されることはありえない。
- それでも「emitter 子は golden に一切接触していない」「完全 blind」とは名乗らない。
  主張するのは**順序保証**である — golden は emitter 実装前に凍結され、その hash は
  実装後も不変だった。恒真化 (emitter から golden を生成する) は構造的に起きていない。

## 8. 逐語

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief と前提実測 A〜H |
| `stage2-plan.md` | 段 2 プラン (codex, read-only, reasoning=max) |
| `stage3-lensA.md` / `stage3-lensB.md` | 段 3 敵対相談 2 レンズ (両者 NO-GO) |
| `s4-ruling.md` | 段 4 裁定・プラン v2・変異事前登録 |
| `stage5-golden.md` | 子 G (golden 起草) の報告 |
| `stage5-leaf.md` | 子 E (leaf + テスト) の報告 |
| `stage6-revA.md` / `stage6-revB.md` | 段 6 敵対レビュー 2 本 (両者 NO-GO) |
| `stage6-fix.md` | fix 子の報告と F1〜F7 の closed 表 |
| `mutation-ledger.json` | 変異 matrix の台帳 (別 commit) |
