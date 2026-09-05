# 段 4 裁定 — plan v2 と変異事前登録

## 1. 所見の裁定 (real / refuted、採否、scope)

| # | 出所 | 所見 | 裁定 | 採否 |
|---|---|---|---|---|
| A-1 | lens A | 置換が「root と同じ bytes が現れた」だけで発火し、その bytes が置き場所由来である保証が無い。意味差を緑に通す反例が 2 つ示された | **real** | **採用 (must-fix)** — 置換許可を閉包束縛へ絞る |
| A-2 | lens A | brief (P1-1) の「前処理出力に行番号の目印が残る」前提は誤り。実装は `-E -P` を使う (`condition_meaning_gate.py:1990`) | **real** | 採用 — 行単位比較は維持し、根拠を差し替える |
| A-3 | lens A | (P1-4) は弱い。コメント内や未展開の `__FILE__` でも非空になる | **real** | 採用 — 必要条件として残すが、単独では保護と数えない (A-1 の修正が本体) |
| A-4 | lens A | brief の因果 (「debug.hh が原因」) が裏取り不足 | **real** | 採用 — 親が実測で補完 (下記 2 節) |
| A-5 | lens A | 変異の穴。とくに「差分区間を丸ごと置換する誤実装」を落とす負例が無い | **real** | 採用 — 負例を 4 件登録 |
| B-1 | lens B | `SequenceMatcher` は実 CCBench 規模で最悪 `O(N^2)`。予測不能 | **real** | **採用 (must-fix)** — 線形の対応行 1 対 1 比較へ置換 |
| B-2 | lens B | A-2 の inert arm は 6 本。`BACKOFF_NOINLINE=0` も同じ分岐を通る | **real** | 採用 — 正例を 2 macro で parameterize |
| B-3 | lens B | evidence の root 対が実 configure の `-S` へ束縛されていない | **real** | 採用 — 1 行の束縛検査を足す (新設 gate ではなく、同 file の既存 record 契約との整合) |
| B-4 | lens B | T316 probe が旧 reason を exact 要求するため、S6 は go にならない | **real** | **scope 外 → 裁定パッケージ**。現状も go ではないので後退は無い (下記 5 節) |
| B-5 | lens B | brief の「consumer 3 件」は不正確。旧 reason の exact 期待は 7 箇所 4 file | **real** | 採用 — 記録を訂正。挙動が変わる既存テストは 0 件 |
| B-6 | lens B | 変更は `stock_comparison` を使う全 driver へ届く | **real** | 採用 — D1523 の意図どおり。影響 driver を記録に残す |
| B-7 | lens B | 「構造的に常時赤」は現構成の実測命題であり、gate 一般の不変条件ではない | **real** | 採用 — 記録の言い方を直す |
| — | 親 | build root を置換対象に含めるか (brief P1-3) | — | **反転して不採用**。下記 3 節 |

## 2. 親が実測で補完した因果 (A-4 への対応)

- `external/ccbench/cc/silo/transaction.cc:106` と `:690` で `ERR` が実際に展開される。
- `ERR` は `external/ccbench/include/debug.hh:54-64` の `NNN` を経由して `__FILE__` を出す。
- `cc/silo/transaction.cc` → `cc/silo/include/transaction.hh` → `include/fileio.hh` /
  `include/string.hh` → `include/debug.hh` で閉包に入る。
- preprocess は `-E -P` (`condition_meaning_gate.py:1990`) なので行番号の目印は出ない。
  出力へ絶対 path が入る経路は `__FILE__` の実展開である。
- したがって「A-2 の inert 比較は現構成で必ず赤」は成立する。ただしこれは**現構成についての
  実測命題**であり、compile argv の source 表記が相対なら成立しない (B-7)。

## 3. build root を置換対象から外す (brief P1-3 の反転)

- 置き場所由来と認めるには「その path が実際に閉包の file を指す」ことを要求する。build root 側で
  それが起きるのは、build tree に生成された header が `__FILE__` を展開する場合だけである。
- **その発火条件を満たす既存 artifact path も計測 ID も名指しできない** (DW-G04)。
  到達不能な述語は採用しない (DW-O13)。
- よって inert 分岐の置換対象は **source root 対だけ**とする。build root の差は残差として赤になる。
  これは現行より狭く、規律 2 の向きに倒れている。
- 副次効果として、置換対応が 1 組だけになり「対応が競合したときの順序」という未検査分岐が消える。

## 4. plan v2 (実装の確定形)

### 4.1 判定順序 (`evaluate_define_supply_effectuation`)

compiler identity 検査と comparable argv 検査は現行のまま先行させる。その後:

1. `if not stock_identity:` の中に、現行の `preprocess-root-dependent-builtin` 判定、
   dependency closure equality、bytes difference 判定を**順序も理由コードも変えずに**入れる。
   非 inert 経路の受理集合は 1 bit も変えない。
2. inert 分岐:
   - `requested.preprocessed_bytes == control.preprocessed_bytes` なら
     **現行のまま** `stock-inert-preprocess-identical` (green)。evidence も現行のまま。
     この枝を分類経路へ回してはならない (consumer 7 箇所が旧 reason を exact 一致で読む)。
   - 一致しなければ分類器を呼ぶ。
   - 分類が「置き場所由来のみ」を返したときだけ
     `stock-inert-preprocess-root-location-only` (green)。
   - それ以外 (残差あり、置換ゼロ、builtin 空、分類不能) はすべて
     **現行のまま** `stock-inert-mismatch` (red)。

### 4.2 分類器 `_classify_stock_inert_root_location_difference`

inert 専用の private helper。一般化した path 正規化 utility にしない。

入力: requested / control の元 `bytes`、requested / control の source root (bytes)、
requested の dependency closure identity 集合、両側の `root_dependent_builtin_paths`。

手順:

1. どちらかの root bytes が `b"\n"` または `b"\r"` を含むなら **分類不能 → 赤**。
2. `requested.split(b"\n")` と `control.split(b"\n")` で行に割る
   (`b"\n".join(...)` が元 bytes を厳密に復元する分け方)。
3. `itertools.zip_longest(req_lines, ctl_lines, fillvalue=None)` で対応づける。
   どちらかが `None` の対は**残差**とする (行数差はここで赤になる。別の長さ検査を置かない)。
4. 元 bytes が同じ対は通過させ、**加工しない**。
5. 異なる対だけ、requested 側の行を左から 1 回だけ走査して書き換える。
   位置 `i` で `requested_root + b"/"` が一致したとき、その直後から
   path 文字集合 `[0-9A-Za-z._+-/]` が続く最大の bytes を候補 `rel_bytes` とし、
   `rel_bytes` を字句正規化する (`/` で割り、空と `.` を捨て、`..` で 1 つ戻す。
   root の外へ出るなら不採用)。正規化結果 `rel` について
   `f"source/{rel}"` が **requested の dependency closure identity 集合に実在する**ときだけ、
   `requested_root` を `control_root` へ写し、入力 cursor を `requested_root` の長さだけ進める。
   実在しなければ 1 byte だけ写して次へ進む。**出力 buffer を再走査しない。**
   置換は requested 側だけに行い、control 側と出力全体には触れない。
6. 書き換えた requested 行が control 行と **byte 単位で完全一致**しなければ残差とする。
7. 「残差ゼロ」かつ「置換回数 ≥ 1」かつ
   「requested と control の `root_dependent_builtin_paths` の和集合が非空」の
   3 つがそろったときだけ、置き場所由来のみと判定する。

### 4.3 reason code / comparison / evidence

- 新 green reason: `stock-inert-preprocess-root-location-only`
- 新 comparison: `stock-inert-root-location-only`
- `status_contract` へ `("stock-inert-root-location-only", False)` を足す。
  既存 2 契約は変えない。
- 新 reason のときだけ required key に次の 4 つを足す。他 2 reason の key 集合は変えない。
  - `root_diff_line_count`: exact `int`、1 以上 (`bool` は拒否)
  - `root_diff_replacement_count`: exact `int`、1 以上 (`bool` は拒否)
  - `root_diff_source_roots`: exact `tuple[str, str]`、両者は非空かつ相異なる
  - `root_diff_has_residual`: exact `bool`、新 green では必ず `False`
- **束縛検査 (B-3)**: `root_diff_source_roots[0]` は `requested_configure_argv[2]` と、
  `[1]` は `control_configure_argv[2]` と完全一致すること
  (`condition_meaning_gate.py:1582-1583` により argv[1] は `-S`、argv[2] が source root)。
- red 側の record にも同じ 4 field を載せてよい (green schema 検査は red を通さない)。
  ただし載せるなら値は実測どおりにする。

### 4.4 gate の禁止 (署名) と通る正例

**禁止**: `evaluate_define_supply_effectuation` の inert 分岐が、
requested と control の前処理 bytes が異なるのに `terminal_status="green"` を返すのは、
差の全体が「requested の dependency closure に実在する file を指す `<requested_root>/<rel>` 形の
path を `<control_root>/<rel>` へ写す」ことだけで説明でき、かつ書き換え後に 1 byte の残差も
残らない場合に限る。

**通る正例**: patch 済み木と stock 木が同一内容で、差が `__FILE__` の展開により
`<requested_root>/cc/silo/transaction.cc` と `<control_root>/cc/silo/transaction.cc` の
2 つの絶対 path だけである前処理出力の対。

## 5. scope 外として裁定パッケージへ返す項目

- **B-4 (T316 probe)**: `tools/pegasus/probes/t316_sandbox_backend_probe.py:367-374` は
  `stock-inert-preprocess-identical` を exact 一致で要求するため、実 CCBench では
  新 reason を受け取って `S6_CONDITION_GATE_UNPROVEN` になる。
  **現状も同じ判定 (現在は supply が赤で admission されない) なので後退ではない。**
  選択肢: (A) T316 側の validator に新旧 2 契約を明示許可する、
  (B) T316 は raw bytes 一致専用として据え置く。lens B の推奨は A。
  受理集合の変更にあたるため本 wave では実装しない。

## 6. 変異事前登録 (DW-M01、実装前)

各変異は単一理由性を実装後に確認する。確認できないものは登録しない。

| # | 変異 | 期待 | kill する node |
|---|---|---|---|
| M1 | 置換許可の述語 (`<root>/<rel>` かつ `source/<rel>` が閉包に実在) を無条件許可へ | KILLED | `test_inert_root_shaped_literal_outside_closure_is_red` |
| M2 | 残差判定を常に `False` へ | KILLED | `test_inert_semantic_difference_on_root_line_is_red` |
| M3 | `root_dependent_builtin_paths` 非空の要求を削除 | KILLED | `test_inert_root_difference_without_code_owned_file_builtin_is_red` |
| M4 | 置換を control 側の行へ適用する (方向反転) | KILLED | `test_inert_root_location_only_difference_is_green` |
| M5 | 元 bytes 完全一致の枝を分類経路へ回す | KILLED | `test_backoff_fixed_minus_one_stock_preprocess_identity_is_green` |
| M6 | `root_diff_source_roots` と configure argv の `-S` の束縛検査を削除 | KILLED | `test_inert_root_location_evidence_binds_configure_source_roots` |

登録しなかった候補と理由:

- 「置換回数 > 0 の要求を削除」— 元 bytes 不一致なら置換 0 で必ず残差が出るため、
  残差判定と冗長。単一理由性が立たない (F820)。
- 「行数一致の要求を削除」— `zip_longest` で残差へ畳んだので独立の述語が存在しない。
- 「build root 対応の削除」— 3 節により build root 対応を実装しないので変異対象が無い。

## 7. 成果物影響 (DW-G05)

放置した場合: A-2 の 6 本の inert arm がすべて赤のまま留まり、certified な選択結果・
材料レポート・試行台帳が 1 件も作られない。[T-2211] (A-5 の別 boot 再取得) も順序待ちのまま動かない。

誤って緩めた場合: 意味の異なる個体が certified selection へ入り、材料レポートと試行台帳が
その green record を参照する。A-1 の修正はこれを塞ぐためのものである。
