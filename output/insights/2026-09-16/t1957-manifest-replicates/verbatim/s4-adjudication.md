# 段 4 裁定 — [T-1957]

## 1. 所見の real / refuted と採否

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | A | 「受理集合は狭まる向き」は生 JSON 集合としては不成立 | real | 採用 (brief の言い方を訂正) |
| 2 | A | 旧版互換受理の負例が「真正 v2 (n 無し)」を覆っていない | real | 採用 (負例を 2 分割、変異は再照準) |
| 3 | A | 欠落補完変異は exact-key 検査に遮蔽される | real | 採用 (変異の編集位置を指定) |
| 4 | A | bool 負例は型検査を弱めても下限で落ちる | real | 採用 (変異登録から外す、test は残す) |
| 5 | A | holdout 間で n が異なる正例は 8b の完全 block 文言と衝突 | real | **採用 — (P1-b) を変更** |
| 6 | A | 登録 n と観測反復集合の exact 一致は未実装のまま残る | real | scope 外 (記録する) |
| 7 | B | 独立 fixture 3 箇所が取り残される | real | **採用 — scope を広げる** |
| 8 | B | plan の file:line にずれ無し | refuted | — |
| 9 | B | 既存 test の削除案は無い | refuted | — |
| 10 | B | key 名 `n` は衝突しない | refuted | 採用 (`n` のまま) |
| 11 | B | 下限変異は 1 cell だけ変えると一致検査に遮蔽される | real | 採用 (全 cell 同値へ訂正) |
| 12 | B | serializer 変異は「省略」と「固定値化」を分けるべき | real | 採用 |

## 2. (P1) の再裁定

- **(P1-a) 実施する。** ただし根拠 (iii) を訂正する。正しい言い方は
  「**既存の受理条件を 1 つも撤去・緩和せず、追加 field への制約だけを増やす**。生 JSON 集合としては
  v2 と v3 で入れ替わり、真部分集合にはならない」。
  D959 の (b)〜(e) は本 wave では 1 つも解除されない — manifest / registry の実体は 0 件のまま、
  §5 は未記入のまま、正式起動の閉塞も動かない。
  **記録上の制約:** 本 wave の成果を「(d) を解除した」「反復束縛が完成した」「§5 を記入できる
  ようになった」と書かない。書けるのは「保存・読込・identity の契約を用意した」までである。
- **(P1-b) 変更する。`n` は 6 trial すべてで同一であることを要求する。**
  8b §10.1 は逐語で「各反復が全 (holdout, 構成) を 1 度ずつ持つ**完全 block** であることを要求する。
  欠測・重複・1 始まりでない連番・**cell 間の反復集合不一致**は判定不能とし」と定める。
  §5 が n を H1 / H2 の 2 欄で持つのは記入の単位であって、両者が異なってよいという許可ではない。
  割れたときは狭い側 (全 cell 同一) へ倒す。
- **(P1-c) 維持する。** manifest / registration とも `/v3` へ上げる。旧版受理分岐も移行処理も作らない。

## 3. plan v2 (実装内容)

`R = orchestrator/campaign/trial_registry.py`

1. `R:55` `MANIFEST_SCHEMA_VERSION = "p3-8c-trial-manifest/v3"`、
   `R:56` `REGISTRATION_SCHEMA_VERSION = "p3-8c-trial-registration/v3"`。
2. `R:117-119` `_TRIAL_KEYS` に `"n"` を追加 (必須。optional にしない)。
3. `R:276-281` `TrialSpec` に `n: int` を追加 (既定値なし)。
4. `R:784` の `generations` 検査の直後に、trial ごとの検査を挿入する。
   - `type(n) is not int` なら `_fail("field", f"{label}[{index}].n must be an integer")`
   - `n < 2` なら `_fail("field", f"{label}[{index}].n must be at least 2")`
5. `R:793` の trial-universe 検査の直後に、cell 間一致検査を挿入する。
   - `len({item.n for item in trials}) != 1` なら
     `_fail("field", f"{label} n differs across cells")`
6. `R:785` の `TrialSpec(...)` へ `n` を渡す。
7. `R:827-834` `_trial_dict` に `"n": trial.n` を追加。
8. `R:1566-1574` `_trial_canonical_tuple` に `trial.n` を追加。docstring も 1 行直す。
9. **fixture 追随 (段 3 レンズ B の取り残し、親が実測で確認済み)。**
   - `orchestrator/tests/test_trial_registry.py` の manifest / registration fixture 一式
   - `orchestrator/tests/test_p3_autonomous_workload_trial.py:7221-7227` と `:10361-10367`
   - `orchestrator/tests/test_reflux_origin_binding.py:65-75` (`_manifest_value`)
   - `test_trial_registry.py:5060-5061` の v2 リテラル置換を v3 へ追随
   - `test_trial_registry.py:6765` の canonical tuple 変異 parametrize に `"n"` を追加
     (replacement は `trial.n + 1`)

## 4. テスト設計

**正例** `test_t1957_six_cell_n_round_trip`: 6 trial すべて `n=3`、`generations=2`。
- P1 `len(manifest.trials) == 6`
- P2 すべての `trial.n == 3` (parser が値を保持する)
- P3 `_trial_dict` 経由の registration JSON の `"n"` がすべて `3` (serializer が値を保持する)
- P4 `registration.trials == manifest.trials`

**負例** `test_t1957_rejects_n[<source>-<case>]`、`source ∈ {manifest, registration}`。
`missing` / `string` / `bool-true` / `bool-false` / `float` / `one` / `zero` / `negative` /
`cell-split` / `holdout-split` / `v2-with-n` / `v2-genuine`。
`one` `zero` `negative` `string` `float` `bool-*` は**全 6 cell を同じ値にする** (1 cell だけ変えると
cell 間一致検査に遮蔽され、どの層で落ちたか決まらない)。
`cell-split` は 1 cell だけ `4`、`holdout-split` は H1 の 3 arm を `2`・H2 の 3 arm を `3` にする。
`v2-with-n` は `schema_version` を `/v2` にして `n` を持つ入力、`v2-genuine` は `/v2` で `n` 無し。
**期待は例外型だけでなくメッセージまで照合する** (型検査を弱めても下限で落ちて緑になるため)。

**版定数** `test_t1957_schema_versions`: 2 定数がリテラル `/v3` と一致する。

## 5. 変異事前登録 (実装前登録)

負例 14 件 + 等価変異 1 件。すべて `orchestrator/tests/test_trial_registry.py::` が接頭辞。

| id | 変異 (編集位置を明示) | 期待赤 node |
|---|---|---|
| M1 | `_exact_keys` 呼出の**直前**に `raw_trial = {**raw_trial, "n": raw_trial.get("n", 2)}` を挿入 | `test_t1957_rejects_n[manifest-missing]`, `[registration-missing]` |
| M2 | 型検査を `not isinstance(n, (int, float))` へ弱化 | `test_t1957_rejects_n[manifest-float]`, `[registration-float]` |
| M3 | 下限を `n < 1` へ弱化 | `test_t1957_rejects_n[manifest-one]`, `[registration-one]` |
| M4 | 下限検査を削除 | `[manifest-zero]`, `[registration-zero]`, `[manifest-negative]`, `[registration-negative]`, `[manifest-one]`, `[registration-one]` |
| M5 | cell 間一致検査を削除 | `[manifest-cell-split]`, `[registration-cell-split]`, `[manifest-holdout-split]`, `[registration-holdout-split]` |
| M6 | cell 間一致を「同一 holdout 内でのみ一致」へ弱化 | `[manifest-holdout-split]`, `[registration-holdout-split]` |
| M7 | `TrialSpec(...)` へ渡す `n` を定数 `2` にする | `test_t1957_six_cell_n_round_trip` (P2) |
| M8 | `_trial_dict` から `"n"` を省略 | `test_t1957_six_cell_n_round_trip` (registration load の exact-key) |
| M9 | `_trial_dict` の `"n"` を定数 `2` にする | `test_t1957_six_cell_n_round_trip` (P3) |
| M10 | `_trial_canonical_tuple` から `trial.n` を除去 | `test_acceptance_rejects_registry_canonical_tuple_mutation[n]` |
| M11 | `MANIFEST_SCHEMA_VERSION` を `/v2` へ戻す | `test_t1957_schema_versions` |
| M12 | `REGISTRATION_SCHEMA_VERSION` を `/v2` へ戻す | `test_t1957_schema_versions` |
| M13 | manifest 版検査を `in {v2, v3}` へ広げる | `test_t1957_rejects_n[manifest-v2-with-n]` |
| M14 | **過剰拒否の正の control。** 下限を `n < 4` へ強化 | `test_t1957_six_cell_n_round_trip` |
| M15 | **等価変異。** `{item.n for item in trials}` を `set(item.n for item in trials)` へ | SURVIVED 期待 |

**登録しないと決めたもの (F28 の再照準)。**
- `bool` を許す型弱化 — `True`/`False` はいずれも下限 2 未満なので拒否層が 2 枚になり、
  単一理由性を満たさない。負例 `bool-true` / `bool-false` は test には残すが変異登録から外す。
- 真正 v2 (`/v2` かつ `n` 無し) を受理させる互換分岐 — 版検査と exact-key 検査の
  2 箇所を同時に変えないと成立せず、単一変異では作れない。負例 `v2-genuine` は test に残す。

## 5b. 変異事前登録の erratum (段 6 レビュー後、本走前)

段 6 のレビュー 2 本を受けて、§5 の登録を次のとおり訂正・追加する。**本走前の訂正である。**

1. **M8 の期待失敗箇所を訂正する。** §5 は「registration load の exact-key」で落ちると書いたが、
   実際は `test_t1957_six_cell_n_round_trip` の `row["trials"]` を読む行が先に `KeyError` を出し、
   loader には到達しない。期待 node は同じだが、**「読込時の必須キー検査を実証した」と
   記録してはならない**。これは serializer 側の欠落を検出する赤である。
   コードは直さない (レビュー B の must-fix はコードの欠陥ではなく登録記述の誤りである)。
2. **M16 を追加する。** 型検査を先頭 cell だけへ限定する退行
   (`if index == 0 and type(n) is not int:`) は、既存 24 ケースをすべて緑のまま通す。
   `{3, 3.0}` は Python の集合で長さ 1 になるため cell 間一致検査も捕まえない。
   段 6 fix で負例 `tail-float` (先頭 cell は整数 3、残り 5 cell は `3.0`) を足し、
   M16 の期待赤 node を `test_t1957_rejects_n[manifest-tail-float]` と
   `[registration-tail-float]` とする。
3. **期待 node 集合は probe 走で確定する。** レビュー B が M2 / M11 / M12 / M13 / M14 について
   「登録した node 以外も赤くなる」と指摘した。`DW-M07` / `DW-M08` に従い、
   全件 SURVIVED 期待の probe 走で観測 node を集めてから本走の期待完全集合を確定する。
4. **新規 test 関数は 3 個である** (§4 の記述は 4 個を示唆していたが、実装は
   `test_t1957_schema_versions` / `test_t1957_six_cell_n_round_trip` / `test_t1957_rejects_n` の 3 個)。
   負例は fix 後 13 case × 2 source = 26 ケース。

## 6. scope 外だが real (裁定パッケージ候補)

1. **登録 `n` と観測反復集合の exact 一致は未実装のまま残る。** `R:3600-3612` は genesis の
   `attempt_index == 0` slot 集合を `replicate_index` を `0` に固定した期待集合と比較する。
   **訂正:** 段 1 brief は「n≥2 の genesis は構造的に受理されない」と書いたが、正確には
   「反復 0 の slot だけを割り当てた genesis はこの局所検査を通る。反復 1 以上の初回 attempt slot を
   含む genesis が拒否される」である。どちらにせよ 8b が要求する全 slot 事前割当は満たせない。
   直すと受理集合が広がるため D959 の下では事前登録の発効が先。
2. **8b §10.1 の「1 始まりでない連番」と実装の 0 始まり `replicate_index` が食い違う。**
   本 wave では触らない。
3. 真正 v2 互換分岐は単一変異で検出できない (上記)。
