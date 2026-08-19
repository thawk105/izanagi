結論を先に言うと、row 18 の grammar と command byte 予算は成立します。ただし、現在の `tools/check_docs.py` を変更しない docs-only 変更としては成立しません。

## 1. `dev-wave.md` の pin と短縮候補

`tools/check_docs.py` が command 本文を検査する箇所は次のとおりです。

- 予算・存在・最大行長: `tools/check_docs.py:183-187`, `:4610-4636`, `:4700-4750`
- frontmatter key、`disable-model-invocation`、`$ARGUMENTS` 件数: `:548-564`, `:4798-4866`
- `## 入力と開始` の可視本文 exact pin: 定数 `:394-403`、登録 `:460-468`、検査 `:4868-4878`、実装 `:1304-1327`
- command 内の `gpt-*` 禁止: regex `:281-346`、検査 `:4344-4355`
- 9 段状態機械の段 6/9 waiter 行 exact pin: 定数 `:298-342`、検査 `:4421-4535`、command 適用箇所 `:4477-4497`
- 段 dispatch / 条件 dispatch の header、row、参照集合、trigger: 定数 `:640-748`、grammar `:2334-2409`、pair 展開 `:2447-2484`、表検査 `:3885-4023`, `:5147-5244`
- D2/D4/Codex-first の regex 構造 pin: 定義 `:750-770`、検査 `:5245-5259`
- 共通 land 経路外の command 禁止: regex `:578-588`、検査 `:5260-5268`

`DEV_WAVE_DW_O25_SECTION_LITERAL` や `DEV_WAVE_DW_C01_SECTION_LITERAL`（`tools/check_docs.py:441-469`）は operations/core 側の pin、`CODEX_DEV_WAVE_*`（`:471-489`）は Skill 側の検査であり、command 本文の短縮を直接拘束しません。

機械的に pin されていない短縮候補はあります。いずれも表、exact section、regex の必須アンカーを変更しません。

` .claude/commands/dev-wave.md:7`（9 bytes削減）

```text
あなたは izanagi の開発 wave の manager である。これは開発作業のループであり、
```

```text
あなたは izanagi の開発 wave の manager である。これは開発ループであり、
```

`.claude/commands/dev-wave.md:85`（4 bytes削減）

```text
段 6 時点で成立している全条件の `DW-Oxx` も、fix 操作の直前に読む。
```

```text
段 6 時点で成立している全条件の `DW-Oxx`をfix 操作の直前に読む。
```

`.claude/commands/dev-wave.md:118`（2 bytes削減）

```text
同じ物語を入口や reference へ再掲しない。
```

```text
同じ物語を入口・referenceへ再掲しない。
```

最小の 2 bytes 削減でも row 18 拡張分を吸収できます。`## 入力と開始`（10-17）、table 本文、waiter の exact 行、D2/D4/Codex の必須アンカーは短縮対象外です。

## 2. row 18 の複数節 grammar

対象セルは次の形です。

```text
`docs/dev-wave/operations.md`: `DW-O18`, `DW-O07`
```

これは grammar 上正しいです。

- `_DISPATCH_REFERENCE_CELL_RE` は同一 path の section list を `, ` で許可します（`tools/check_docs.py:2358-2365`）。
- `_dispatch_reference_cell_errors` は raw path と backtick path の一致、および cell 全体の fullmatch を検査します（`:2371-2409`）。
- `_dispatch_pairs_from_line` は path 後の各 section を同じ path に束縛します（`:2447-2484`）。`〜` の場合だけ range 展開し、comma 区切りは個別 section として追加します。

既存の同一 grammar は、段 5/6 の operations cell（`.claude/commands/dev-wave.md:72,77`）、および mutation の range+comma（`:76`）です。

追加 bytes は `, ` 2 bytes + `` `DW-O07` `` 8 bytes = 10 bytes です。現在の row は 96 bytes、拡張後は 106 bytesです。

ただし現在の contract は `DW-O18` だけです。`CONDITION_DISPATCH_CONTRACT` は通常 row を 1 section に自動生成しています（`tools/check_docs.py:711-714`）。したがって grammar は正しくても、checker では `DW-O07` が extra として落ちます。

## 3. `DW-O07` の挿入順序

`operation_positions` が機械的に順序検査するのは `DW-O23` と `DW-O25` だけです（`tools/check_docs.py:4880-4900`）。したがって一般的な O 番号の昇順検査はありません。

人間向けの自然な挿入位置は、既存の `DW-O06` と `DW-O08` の間、すなわち現在の `docs/dev-wave/operations.md:49` の `DW-O08` の直前です。`DW-O23` が `DW-O25` より前に残ることだけは必要です（現状 `:147` と `:159`）。

しかし現在は `_OPERATION_NUMBERS` から 7 が除外されています（`tools/check_docs.py:566-569`）。そのため `DW-O07` をどこに置いても、次の検査に抵触します。

- operations registry に O07 がない: `:590-608`
- 未登録 H2 として orphan 扱い: `:4902-4921`
- dispatch typed-edge 閉包不一致: `:5223-5237`
- 条件 18 contract 不一致: `:5183-5207`

## 4. 結論

バイト予算だけなら Yes です。必要量は `+10 bytes`、捻出候補は `-2 / -4 / -9 bytes` あります。

ただし、`DW-O07` の registry と row 18 の複数参照 contract が未登録なので、コード変更なしの docs-only wave としては No です。実施するなら、checker 側の O07 registry・condition contract・dispatch 閉包を裁定のうえ更新するか、既存登録済みの別 L2 ID を使う選択肢があります。

## 総括

1. 短縮可能箇所はあり、最小 `-2 bytes` で足ります。
2. row 18 の複数節セルは grammar 上正しく、追加は `+10 bytes` です。
3. O07 の置き場所は O06/O08 間が自然ですが、現在の registry ではどこに置いても orphan になります。
4. byte 予算は可能、現行 checker のままの docs-only 実施は不可能です。