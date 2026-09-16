# [T-2723] B-4 floor セルの読取を事前登録 §5 の admission 契約へ接続した

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-t2723-floor-cell-admission`
- 基準 commit: `1042a1bc95057fa03117d504cfa2b0fafaae60d0` (local main、wave 開始時)
- 実装 commit: `8cfcd62f129686655ad94aebba3c03bf9ffee5a8` (Codex `role=author`、6 file、+332/−87)
- 起票: worklog archive 1571 の T-2723 項 (T-2464 の段 3 / 6 が real・scope 外として残した所見)
- 設計判断: 本 wave の decisions fragment (slug `floor-cell-reads-through-section5-admission-parser`、D 番号は land の fold が付ける)
- job dir (prompt・log・patch・probe の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2723-floor-cell-admission/`

## 何をしたか

材料レポート (`orchestrator/campaign/p3_b4_material_report.py`) は事前登録 §5 の floor 行から権威 floor を読み、
凍結評価器へ渡す。現行の読取 (`p3_b4_floor_artifact_issuer._floor_cell`) は文書全体を `|<label>|` の exact prefix
で走査し、§5 の見出し境界・固定表の形状・責任者行を見ていなかった。F423 (文書全体の string search で「本物の
箇所」を決める設計は decoy に欺ける) と同型である。

`p3_b4_admission_record.py` の既存 §5 検査から、固定表の解析を `_parse_section5_fixed_table_source_cells`
(normalized value / strip 済み raw value / strip 前 label の 3 系列を返す) へ、1 セルの受理述語を
`_assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel` へ切り出し、既存関数は両 helper を
呼ぶだけにした (受理集合・例外 message・検査順は不変、段 6 レビュー A が行単位で照合)。floor issuer は共有 parser
で §5 固定表の floor セル 1 つだけを読み、floor label の strip 前 exact 一致と責任者行の述語を通してから、strip 後
raw の `未記入` を absence、それ以外を既存 pin grammar で解く (raw のまま loader へ)。他欄の sentinel と
expectation 行は検査しない。新 error code・validator・gate は無い。

## 受理集合の変化 (段 4 裁定 §3 の列挙契約)

- 拒否→受理 (2 系統): (a) floor 値セルの外周空白の strip (admission と同一)、(b) 真正 §5 の外にある同 prefix 行の存在
  (fence / HTML comment 内を含む) は無視される。
- 受理→拒否: 共有 parser の全条件 (`## 5.`〜`### 5.1` の一意な見出し境界、区間内の fence / comment 無し、12 非空行、
  exact header、各行の両端 `|` と 2 セル、正規化後 label の重複なし・10 label 集合と一致、全 label / 値セルの
  default-ignorable・Cf 拒否)、floor label の strip 前 exact 一致、責任者行の既存 admission 述語 (D2079 の 1 形 +
  一般 sentinel 規則)、path 中の ASCII `|`。
- 不変: sentinel は strip 後 raw の `未記入` だけ (NFKC 異体 `未記⼊` は grammar error のまま)、pin grammar と loader へ
  渡す path / hash は raw、他欄の sentinel と expectation 行は検査しない (現行文書 = 6 欄 `未記入` で None)。

親の brief は当初「縮小 + strip だけ」と書いたが、段 3 レンズ A・B が独立に反証した (外側同 prefix 行の無視は strip と
独立の拒否→受理、縮小は §5 外・責任者欠落だけでなく共有 parser の全条件に及ぶ)。列挙契約へ置き換えた。

## 親の対照 probe (実文書 bytes の最小改変、変更前後の module で同一入力)

`verbatim/parent-probe-counterfactual-before.txt` (HEAD 1042a1bc9 の module を `git archive` で展開) と
`verbatim/parent-probe-counterfactual-after.txt` (実装後)。

| 入力 (実文書 117,781 bytes を改変) | 変更前 | 変更後 |
|---|---|---|
| 無改変 | None | None |
| 文書末尾 (§5 外) に有効 grammar の pin 行を追加 | 拒否 `exact 1 件 … observed=2` | None (無視) |
| 責任者 `thawk105` → `未記入` | **None (受理)** | 拒否 `preregistration_floor_row_error` (§5 実行責任者・開始時刻) |
| §5 の floor 行を削除 (9 行表) + 外側に pin | **`path_error` (外側の pin を読んで loader へ進んだ)** | 拒否 `preregistration_floor_row_error` |
| §5 の floor 行に pin (artifact 不在) | `path_error` | `path_error` (§5 の行が読まれた) |
| `未記⼊` (末尾 U+2F0A) | grammar error | grammar error |
| ` 未記入 ` (外周空白) | grammar error | None (strip) |

太字 2 行が起票の欠陥そのものである。変更前の admission 検査は実文書を「6 欄 `未記入`」で拒否し、変更後も同じ
(`verbatim/parent-probe-before.txt` / `parent-probe-after.txt`)。

## 段 3・段 6 の所見 (逐語は `verbatim/`)

- 段 2 plan (`s2-plan.md`): helper 切り出しの signature と code 片、fixture の完全表化、新規 test 11 件、変異 M0〜M9。
  brief への補正 4 点 (floor label exact の維持、expectation 検査は切り出し外、real-repo 分類 2 file、launcher 回帰)。
- 段 3 レンズ A (`s3-lensA.md`、正しさ境界): real 14 / refuted 4 / plausible 1 (親が本文から数え直した)。最重要は「NFKC 後で sentinel を比べると
  `未記⼊` が拒否→None へ変わる追加緩和」→ 裁定で strip 後 raw 比較に変更、負例 test と変異 M10 を追加。
  F423 型の残存 (両見出しを壊して別所へ canonical §5) は admission parser 自身の既知限界として記録。
- 段 3 レンズ B (`s3-lensB.md`、整合・consumer): real 12 / refuted 5 / plausible 3 (同)。m05/m06 が fixture 破損でも緑になる
  (code 固定へ)、M4 の複合を単一化、real-repo 分類登録の主張は決定 4 で不採用 (先例・writer 不在・scope 外)。
- 段 4 裁定 (`s4-adjudication.md`): 所見ごとの real/refuted・採否、plan v2、列挙契約、変異 M0〜M11 の事前登録。
- 段 5 author (`s5-author.md`): 6 file。自走 FT 93 / AT 30 / RT 50 passed。schema 負例の入力を `v2` (現行 aggregate
  schema として有効) → `v999` へ補正。
- 段 6 レビュー A (`s6-reviewA.md`): must-fix 0 / GO。受理集合は列挙内、NFKC sentinel 反証、述語は同一関数、admission
  不変、error 写像正しい。
- 段 6 レビュー B (`s6-reviewB.md`): must-fix 0 / GO。nit 3 = 行削除 test (3)(5) と duplicate rows は過剰決定 (単独
  検査の証拠から外す)、AT 新 test の label を padded に、他欄 `未記入` + 有効 pin の正例を足す。M6 / M7 の single-site
  anchor は mask 代入行。
- 段 6 fix (`s6-fix.md`): 相対 sibling import へ (親の読解所見 — 走査器 `scan_campaign_relative_imports` は level 0 の
  `orchestrator.campaign.*` を違反とし既知例外は 1 件、該当 test は growth hold で受入では走らない)、AT test の padded
  label、正例 `test_resolver_accepts_valid_pin_with_other_cells_unrecorded`。自走 FT 94 / AT 30 passed。

## 親の実走

| 走 | 対象 | 結果 |
|---|---|---|
| baseline (変更前、計算ノード 2268.nqsv) | floor issuer / admission / material report / closed critic の 4 file | 230 passed、139.5 s |
| 統合後 (段 5、2329.nqsv) | 上 4 + raw record producer + launcher + campaign import invariant | 361 passed、6 skipped (import invariant の growth hold 6 node、解除 env はユーザー明示専用)、140.0 s |
| fix 後 (2362.nqsv) | 6 file (import invariant を除く) | 338 passed、144.7 s |
| provenance full (commit 後) | 導入 commit〜HEAD | 10,809 件、新規違反なし |

## 変異 matrix

container worktree `.codex/worktrees/t2723-mutcontainer` (実装 commit `8cfcd62f1` の使い捨て worktree) で
`tools/mutation_harness.py --runner-mode dispatch --detached`、runner は `python3 tools/run_tests.py` に floor issuer /
admission / material report の 3 test file + `-q -rf --force-dispatch`。D612 の queue-wait / grace 上書き 1800 / 600。
spec と台帳は本 dir の `mutation-spec-probe.json` (sha256 `373c3b3a…`) / `mutation-ledger-probe.json`、
`mutation-spec-final.json` (sha256 `e0b7d255…`) / `mutation-ledger-final.json`。

- probe 走 (全件 SURVIVED 登録、観測 node を集める): baseline PASSED、M0 SURVIVED、M1〜M11 は全部 MISMATCH (= 赤 node を
  観測)。観測 node を本走 spec の `expected_nodes` へそのまま写した。
- 本走: **baseline PASSED (165.5 s)、負例 11 件 (M1〜M11) すべて KILLED で期待 node と観測 node が完全一致
  (matching 12/12)、等価変異 M0 (docstring だけ) は SURVIVED、MISMATCH 0、TIMEOUT 0**。全変異の anchor は 1 箇所
  (anchor_counts = 1)。所要は変異 12 件で 3,221 s (M6 だけ 1,036 s、queue 待ち込み)。

| ID | 変異 (single-site) | KILLED node 数 | 専属 killer / 主な killer |
|---|---|---|---|
| M0 | admission module docstring に 1 行 (等価) | — (SURVIVED) | — |
| M1 | `_floor_cell` を文書全体 prefix 走査の旧挙動へ | 10 | outside-pin / decoy 両種 / missing-floor / missing-owner / unrecorded-owner / unknown-label / padded sentinel / encoding / raw-pin |
| M2 | 責任者行の述語呼び出しを削除 | 1 | `test_resolver_rejects_unrecorded_owner_before_loading_pin` (専属) |
| M3 | label 集合一致検査を削除 | 1 | `test_resolver_rejects_unknown_label_at_fixed_row_count` (専属) |
| M4 | cell の `.strip()` を除去 | 3 | padded sentinel、raw pin、admission の raw/normalized test |
| M5 | `raw_values` に normalized を格納 | 4 | admission `…nfkc_only_ascii_grammar_matches`、raw/normalized test、raw pin、NFKC 異体 sentinel |
| M6 | fence mask を全 False | 4 | decoy[fence] + admission の fence test 3 本 |
| M7 | HTML comment mask を全 False | 3 | decoy[comment] + admission の comment test 2 本 |
| M8 | pin grammar / loader へ NFKC 後の値 | 1 | `test_resolver_preserves_raw_floor_pin` (専属) |
| M9 | floor label の strip 前 exact 一致を削除 | 2 | `test_resolver_keeps_exact_floor_label[padded/fullwidth]` |
| M10 | sentinel 比較を NFKC 後の値に | 1 | `test_resolver_rejects_nfkc_only_absent_sentinel` (専属) |
| M11 | 述語を全 label に掛ける (過剰拒否の正例、DW-M01) | 41 | 実文書 `test_resolver_real_preregistration_is_absent`、他欄未記入 + 有効 pin 正例、材料レポート 33 node (実文書を読む) |

M6 / M7 は既存 admission test も killer になる (専属性は主張しない、段 3 レンズ A の予測どおり)。レビュー B の nit
のとおり、行削除の負例 (3)(5) と duplicate rows は過剰決定なので単独検査の証拠には数えず、M1 の旧挙動検出にだけ使う。

## 残存限界・scope 外 (記録のみ)

- 両見出しを軽微に壊し別所へ canonical §5 を置く F423 型は admission parser の既知限界。
- 他欄が `未記入` のまま有効 pin を置けば floor は present になる (既存仕様)。完了主張は「floor セルの読取を §5 固定表 +
  責任者行述語へ接続した」に限る。
- 実文書 → None の回帰 test は現在の未登録状態の写し。floor 登録 wave で更新する。
- 事前登録文書 §11.3 末尾の「現行の生成器は本書を読まず無条件に floor 不在を渡す (D1377)」は本 wave 以前から陳腐化
  している (生成器は §5 を読む)。文書の追補は同文書の改訂契約に従う別 wave の手番で、本 wave は触らない。
- admission module の bytes 変更で live projection closure hash (base / sort / trigger) は変わる。§5 expectation 行は
  `未記入`、committed admission record は 0 件、変更前 sha256 (3 module) は tracked file に pin 0 件。失効対象なし。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の `.md` / `.txt` は `git diff --check` に触れる行末空白 (Codex 出力の Markdown 二重空白改行と probe 出力の末尾空白) を除いてある。可視文字は不変。原文 bytes は `verbatim/originals.json` (sha256 `d08c4e2d33480bd373f335211dbadaa5f346f13513cd33f9d849a62c62812f89`) に UTF-8 text として収め、各 text をそのまま書き出せば原文 bytes を復元できる。`s5-author.md` と `s6-fix.md` は末尾改行を 1 byte 足しただけ。

| file | 原文 bytes | 原文 sha256 | 行末空白を除いた行数 | 正規化後 bytes |
|---|---|---|---|---|
| `parent-probe-after.txt` | 645 | `0bc99064013de591…` | 1 | 644 |
| `parent-probe-before.txt` | 645 | `0bc99064013de591…` | 1 | 644 |
| `parent-probe-counterfactual-after.txt` | 739 | `75d49059394f7fcc…` | 1 | 738 |
| `parent-probe-counterfactual-before.txt` | 802 | `8470f2e35c4ae046…` | 0 | 802 |
| `s1-brief.md` | 5591 | `eae98d321e0deb14…` | 0 | 5591 |
| `s2-plan.md` | 24930 | `423611c5672fd63a…` | 19 | 24893 |
| `s3-lensA.md` | 15913 | `133ec1c5fc188afc…` | 76 | 15762 |
| `s3-lensB.md` | 17302 | `2879b6264806e326…` | 80 | 17143 |
| `s4-adjudication.md` | 16827 | `75fb24da85a1dcde…` | 0 | 16827 |
| `s5-author.md` | 9297 | `e3a546c3eb48b77d…` | 0 | 9298 |
| `s6-fix.md` | 3921 | `462ee4705a2b36a6…` | 0 | 3922 |
| `s6-reviewA.md` | 11318 | `962c0fc4e7412faa…` | 50 | 11219 |
| `s6-reviewB.md` | 11254 | `f0e495a283173b68…` | 25 | 11205 |
originals.json sha256 d08c4e2d33480bd373f335211dbadaa5f346f13513cd33f9d849a62c62812f89
