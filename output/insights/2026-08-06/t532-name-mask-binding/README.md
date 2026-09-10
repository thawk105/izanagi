# [T-532] name↔mask 束縛一致検査 — 逐語と変異台帳

wave branch `worktree-dev-wave-t532-name-mask-binding`。
台帳の正本は `docs/worklog.md` の該当エントリ、設計判断は `docs/decisions.md`、
失敗は `docs/failures.md`。本ディレクトリは**その根拠となる逐語**を凍結したものである。

## 何をしたか

凍結文書 `output/s1-freeze/known_axes_freeze.json` の trigger 系 record (3 workload ×
`system_gate` / `ident_all` の 6 件) について、`name` が指す要因部分集合 (mask) と
`gate_predicate` 本文が符号化する mask の一致を、生成層 `_trigger_entries` と本番到達点
`_validate_schema` の双方で検査する。期待名は emitter (`s8a_trigger_sweep.subset_name`) の
正引きで得る。

**現行 official の受理集合は空であり、本検査は現在値を一件も変えない dormant gate である。**
実効化は [T-531] の世代移行で新世代 artifact を発行する時点。

## ファイル

| ファイル | 内容 |
|---|---|
| `brief.md` | 段 1 brief (親)。DW-G05 と既存被覆の記述は段 3 の指摘で `ruling.md` が是正している |
| `plan-out.md` | 段 2 プラン v1 (codex, read-only, reasoning=max) |
| `adv-a-out.md` | 段 3 敵対レンズ A (正しさ境界・単一理由性)。NO-GO |
| `adv-b-out.md` | 段 3 敵対レンズ B (到達層・実効性)。NO-GO |
| `ruling.md` | 段 4 裁定 + プラン v2 + 変異事前登録 + 裁定パッケージ (親)。**brief より優先する正本** |
| `impl-out.md` | 段 5 実装子の完了報告 (codex, workspace-write, reasoning=high) |
| `rev-a-out.md` | 段 6 レビュー A (受理集合・変異検出力)。NO-GO、must-fix 1 件 |
| `rev-b-out.md` | 段 6 レビュー B (統合・波及・回帰)。NO-GO、must-fix 1 件 |
| `fix-out.md` | 段 6 fix 1 巡目の報告 |
| `rerev-out.md` | 段 6 焦点再レビュー。元所見 2 件は closed、新規所見 1 件 |
| `fix2-out.md` | 段 6 fix 2 巡目の報告 (診断経路のみ) |
| `mutation-spec.json` | 変異 spec (最終版)。sha256 = `82792252f49d9fa9384c23b43509998a10aa1456c7f81d58a70aea1a3c55465a` |
| `mutation-ledger-v2.json` | 変異台帳 (最終版)。7/7 KILLED・node 完全一致 |
| `mutation-spec-v1-erratum.json` | 初回 spec (M5 の置換 bytes が登録文と食い違っていた) |
| `mutation-ledger-v1-erratum.json` | 初回台帳 (M5 のみ MISMATCH)。**erratum として保存する。消さない** |

## 変異 matrix の射程 (silent cap にしないための明記)

runner は次のとおりで、**suite 全体ではなく選択式で絞っている**。

```
python3 tools/run_tests.py \
  orchestrator/tests/test_s1_known_axes_freeze.py \
  orchestrator/tests/test_trigger_gate_binding.py \
  -q -rf -k 'trigger_name_mask or coordinated_canonical or missing_trigger_name or
             semantic_membership or mask31 or duplicate_trigger_names or
             consumer_import_defers or mask_for_canonical_predicate'
```

選択式は事前登録した 7 変異の期待 node をすべて含む。harness は `--runner-mode dispatch` で
Pegasus 計算ノードへ投げ、baseline を含む 8 回を走らせた。

## 初回 M5 の erratum

初回走行で M5 が MISMATCH になったのは**親の登録ミス**である。M5 は
「mask 31 の `ident_all` alias 登録を削除する」変異として登録したが、置換後の文字列に
登録行 `index[alias] = all_mask` を残したため、実際に注入されたのは
「alias の型検査と衝突検査だけを削除する」別の変異だった。その結果、
過剰拒否を検出する 3 つの正例は赤にならず、fail-closed 検査を固定する 2 node だけが赤くなった。

**検査側の欠陥ではない。** `old` は実ファイルから逐語抽出して一意性を assert していたが、
`new` は手書きだったところに穴があった。修正版で 7/7 kill・node 完全一致。
初回の spec と台帳は上表のとおり erratum として残す。

## scope 外の real 所見 (裁定パッケージ)

`ruling.md` の末尾 2 件 (RP-1: `assert_s1b_pairing` の生文字列比較、
RP-2: holdout / ratified / replay の迂回) が正本。worklog の「次の一手」へ新規項として起票した。
