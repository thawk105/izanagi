## test の網羅と単一理由性

静的レビューのみ。pytest・変異実行・ファイル変更は行っていない。以下、A/F/R は `orchestrator/campaign/p3_b4_{admission_record,floor_artifact_issuer,material_report}.py`、AT/FT/RT は対応する `orchestrator/tests/test_*.py` を指す。

裁定 §2-4 の新規 test は 12 関数・14 node 存在する。下表の node はすべて `FT::` 接頭辞。

| 項目 | node 名 | 単一理由性 |
|---|---|---|
| 1 | `test_resolver_real_preregistration_is_absent` | 実文書の正例 |
| 2 | `test_resolver_ignores_pin_outside_section5` | §5 外の追加行だけ |
| 3 | `test_resolver_rejects_missing_floor_despite_outside_pin` | **行数と label 集合の二重不正** |
| 4 | `test_resolver_rejects_unrecorded_owner_before_loading_pin` | 責任者値だけ。pin/sentinel 両方を検査 |
| 5 | `test_resolver_rejects_missing_owner_row` | **行数と label 集合の二重不正** |
| 6 | `test_resolver_ignores_blocked_section5_decoys[fence]` / `[comment]` | 各 block 内の decoy 正例 |
| 7 | `test_preregistration_floor_label_matches_admission_label` | 独立 literal と集合所属 |
| 8 | `test_resolver_preserves_raw_floor_pin` | padded pin、全角 path、grammar 不正を順次検査 |
| 9 | `test_resolver_keeps_exact_floor_label[padded]` / `[fullwidth]` | strip 前 exact label だけ |
| 10 | `test_resolver_rejects_unknown_label_at_fixed_row_count` | 行数を維持した label 集合不一致だけ |
| 11 | `test_resolver_preserves_encoding_error` | 不正 UTF-8 と BOM 正例を順次検査 |
| 12 | `test_resolver_rejects_nfkc_only_absent_sentinel` | raw sentinel 不一致だけ |

**所見**：行削除の新規 2 test と既存の重複行 test は、個別の構造検査への帰属が過剰決定である。
**分類**：real
**重さ**：nit
**根拠**：FT:848 の `replace(row + b"\n", b"")`、FT:873 の責任者行削除は 9 データ行・11 非空行と label 欠落を同時に作る；FT:784 の label 置換も重複と別 label 欠落を同時に作る。
**影響**：これらだけでは、行数・集合・重複の各検査を単独で除去した退行を識別できない。
**推奨**：上記 3 test を個別検査の独立証拠から外す。M3 は項目 10 を用いる。項目 3/5 は M1 の旧全文走査への退行検出としては残してよい。

loader 未呼出の観測は FT:819 の `unexpected_load` が呼出を記録して `AssertionError` を送出する**差し替え**であり、実 loader への委譲 wrapper ではない。裁定が許した未呼出観測の範囲にある。pin は FT:800–805 で実 issuer から生成され、項目 8 は実 loader を通る。

## fixture の再利用

**所見**：material report 側は、指定された `_section5_document` の直接 import ではなく floor test の wrapper を経由している。
**分類**：real
**重さ**：nit
**根拠**：FT:189 は `from orchestrator.tests.test_p3_b4_admission_record import _section5_document`、RT:137・1001・1110 は `from orchestrator.tests.test_p3_b4_floor_artifact_issuer import _preregistration`。
**影響**：nit。依存段数は増えるが、生成表は同じで、FT:193 が責任者既定値を `実行責任者 = fixture-owner、開始時刻 = 未記入` に置換する。
**推奨**：機能修正は不要。直接 import の表記統一を実施済みとは記録せず、実際の委譲関係を残す。

**所見**：実文書と同じ未記入状態の回帰は absent 側だけで、他欄未記入のまま有効 pin を受理する正例はない。
**分類**：real
**重さ**：nit
**根拠**：FT:826 は実文書に対する `is None`；文書:158–166 に値が `未記入` の 6 欄がある。一方 FT:191 の builder は floor・責任者以外を既定の記入済み値にする。
**影響**：有効 pin のときだけ他欄の sentinel を過剰拒否する退行は、この新規正例群では識別できない。
**推奨**：補強するなら項目 8 内に、実文書相当の他欄を未記入にした有効 pin 正例を足す。裁定必須の項目 1 と M11 の無条件過剰拒否検出は既存の実文書 test が担う。

## material report test の golden

静的 AST 照合では RT は既存の **32 関数・50 node** のまま。新規 test 関数はなく、`test_real_repo_serialization.py:362` の golden との関数名集合差分は空。

全 collection を比較する入口は同 file:1591 の `test_real_repo_group_collection_exactly_matches_canonical_nodes`、比較本体は :1340 の `assert actual_by_group == ...`。

変更は RT:137・1001・1110 の完全表書込みに限定される。m7 の `path_error`（:1136）、aggregate の Fraction/path/hash、m9、non-guarantees、固定 bytes golden の期待値変更はない。追加指摘なし。実 collection の成功は未確認。

## admission test の追加

**所見**：追加 test は raw/normalized 値を区別するが、label が strip 前であることは区別しない。
**分類**：real
**重さ**：nit
**根拠**：AT:1177 は値に `"  Ａ  "` を与え、:1179–1181 で `"A"`・`"Ａ"`・元 label を検査するが、入力 label 自体には空白も全角化もない。
**影響**：この test 単独では `verbatim_labels[label] = raw_label` への誤変更を検出できない。ただし floor label については FT の `[padded]` が補完する。
**推奨**：同 test の入力 label を padded spelling に置換し、辞書 key は normalized、保存 label は padded spelling と assert する。

`git diff 1042a1bc9 -- orchestrator/tests/test_p3_b4_admission_record.py` の削除行は **0**。追加は上記 1 関数・10 行で、既存期待値は変更されていない。

## 自走 harness

FT:1681 は `pytest.main(["-q", str(Path(__file__).resolve())])` で file 全体を収集するため、新規 test を除外する固定一覧はない。新規 parametrize ID は `fence`、`comment`、`padded`、`fullwidth` の ASCII のみ。追加指摘なし。

## consumer の波及

`_floor_cell` の唯一の caller は F:1523 の `raw_cell = _floor_cell(raw)`。入力 bytes への更新済みで、戻り値は変更前後とも `str`。

公開 resolver の呼出箇所は R:216、RT:1006・1062、FT:688・695・701・727・772・791・810・829・1506。完全表 wrapper または実文書へ接続されている。`orchestrator/`・`tools/`・`hooks/` の Python 検索で追加 caller は見つからなかった。

F:80 の label literal、:83 の sentinel、:88 の regex は不変。追加の取り残し指摘なし。

既知所見：F:74 の絶対 sibling import は規約違反（real、修正予定）；焦点走は未実測。予定どおり相対 import にして既存 import 群へ移す。

## 自己申告の検算

静的な件数は FT **51 関数・93 node**、AT **30 関数・30 node**、RT **32 関数・50 node** で、自己申告の合計 **173** と一致する。追加 nodeid の綴りも現物と一致する。ただし、実走成功そのものは自己申告を超えて検証していない。

`focus-baseline.log:23` の **230 passed** は変更前の別範囲の記録であり、173 と直接比較して欠落数とは扱えない。

既存期待値の変更は申告した 3 関数に収まる。m05/m06 の `v2 → v999` 入力補正も報告に明記されている。受理集合の自己申告は裁定 §3 と整合し、差分に報告外の実装変更は見つからなかった。

## 変異 matrix の anchor

以下は現物に各 **1 回**存在する逐語候補。複数行は `\n` で表す。これは anchor の静的確認であり、実行可能 patch・killer 集合の確認ではない。

| ID | file:line | old 逐語候補 |
|---|---|---|
| M0 | A:27 | `Complete admission Section 5 validation checks the fixed raw table shape, nonempty source cells,` |
| M1 | F:1476 | `def _floor_cell(raw: bytes) -> str:` |
| M2 | F:1496 | `        _assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel(\n            owner_label, values[owner_label]\n        )` |
| M3 | A:658 | `    if set(values) != set(_SECTION5_LABELS):\n        raise B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)` |
| M4 | A:650 | `        raw_label, raw_value = (cell.strip() for cell in cells)` |
| M5 | A:656 | `        raw_values[label] = raw_value` |
| M6 | A:615 | `    fenced_lines, html_commented_lines = _markdown_block_context(lines)` |
| M7 | A:615 | `    fenced_lines, html_commented_lines = _markdown_block_context(lines)` |
| M8 | F:1526 | `    match = _FLOOR_PIN_RE.fullmatch(raw_cell)` |
| M9 | F:1489 | `    if verbatim_labels[PREREGISTRATION_FLOOR_LABEL] != PREREGISTRATION_FLOOR_LABEL:\n        _fail(\n            "preregistration_floor_row_error",\n            "§5 floor row label は既存の exact 表記でなければならない",\n        )` |
| M10 | F:1524 | `    if raw_cell == PREREGISTRATION_ABSENT_SENTINEL:` |
| M11 | F:1496 | M2 と同じ呼出ブロック |

置換の注意点：

- M0 は元行を残し docstring 内へ説明行を追加する。
- M1 は関数先頭へ bytes decode・旧 prefix 探索・件数検査・セル返却を挿入して旧経路へ戻せる。型エラーによる kill を避ける。
- M2 は `try` を空にしないよう呼出ブロックを `pass` にする。
- M6/M7 は A:615 の代入直後に、それぞれ fence/comment mask だけを全 False にする置換なら、境界探索と区間検査を一箇所で変更できる。
- M8 は fullmatch の入力だけを NFKC 化すると、後続の `match.group()` から loader への path/hash もその系列になる。sentinel 比較まで変更しない。
- M10 は比較式だけ NFKC 化する。
- M11 は M2 の呼出ブロックを全 `values.items()` への述語適用へ置換する。

**所見**：author が挙げた M6/M7 の位置をそのまま個別置換すると、single-site ではなくなる。
**分類**：real
**重さ**：nit
**根拠**：`s5-author.md` の matrix は M6 に `A:619・626・632`、M7 に `A:620・627・633` を挙げる；`if not fenced_lines[index]` 等の短い old は複数存在する。
**影響**：単一 occurrence の置換では片側の境界や区間検査が残り、意図した変異と killer 帰属がずれる。
**推奨**：上表の A:615 を使って single-site 化する。上表の候補には不存在・非一意の anchor はない。probe 前に具体的 patch を固定する。

## 裁定パッケージ候補

なし。新 gate・台帳・一般化の追加は提案しない。

## 総括

must-fix **0 件（本レンズの新規指摘）／GO**。既知の絶対 sibling import 修正は別途必要。

新規 test の欠落、golden 不一致、consumer の取り残し、未申告の期待値変更は確認されなかった。修正・記録上の注意は、過剰決定 fixture の証拠帰属、strip 前 label の test 入力、M6/M7 の single-site 化。GO は静的レビューの判定であり、焦点走・変異走の成功を意味しない。
