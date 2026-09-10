# [T-1357] DENY_TABLE の識別子削除を意味的 probe で検知する

2026-08-19/20、dev-wave `dev-wave-t1357-deny-table-shrink-guard`、基準 main = `050b06488f`。
実装 commit = `22d68576`。逐語・成果物は `verbatim/` を参照。

## 1. ratified 裁定と本 wave の scope 選定

[T-1357] は 2026-08-18 `/rulings` 全件第8回で「設計する」と裁定された
(`docs/archive/worklog-phase3-0819-671.md:555`)。ratified 文言は「禁止集合が縮んでいないことを
意味で守る検査を設計する。変異 M6 が SURVIVED ですり抜けを実証しており、正しさの門を緩める方向の
穴である」で、対象ファイルを名指ししていない。

起票本文 (`docs/archive/worklog-phase3-0818-651.md:595`) の真の動機は
`.claude/agents/coder-v4-autonomous-sort.md` の closed-region 契約 (5 bullet) を守る role adapter
pin (SOURCE_FILE_SHA256 等) が bytes の同一性しか証明しないことだった。この pin/契約テキスト側の
問題は**本 wave では実装していない**。本 `/dev-wave` 起動引数が `coder_effect_gate.py` の
`DENY_TABLE` へ明示的に scope を narrow したため、段3 敵対相談レンズB がこの選定の妥当性を検算し
(real、ratified 文言は対象を縛っていないため矛盾しない)、「完了報告は DENY_TABLE の局所成果に
限定し、role-contract pin/M6 全体の解決とは報告しない」ことを条件に採用した。

**動機記述の stale 訂正:** `/dev-wave` 起動引数が引用した
「`orchestrator/tests/test_coder_effect_gate.py:151` が bounded loop 通過を明示的に固定している」は
2026-08-15 時点の事実で、2026-08-18 commit `dc87fff7` (main 済み、[T-396] 裁定 B の実装) が
該当テスト (`test_ordinary_for_range_for_and_data_dependent_loops_pass`) を削除済み。現 line151 は
別テスト (`test_explicit_unconditional_loop_headers_are_rejected`) の一部で、bounded loop 自体の
拒否可否は変更していない。本 wave の実際の動機は
(a) `output/insights/2026-08-15_t396-hole-allowlist-refuted/README.md` §7 の DENY_TABLE 欠落項目表、
(b) 2026-08-18 wave651 の一般教訓「pin は bytes 同一性しか証明しない」
(`docs/archive/worklog-phase3-0818-651.md:36-40`) で再構成した (段3 レンズA/B・段6 レンズ1が
`git show dc87fff7` で独立に再検算し確認)。

## 2. 実測: 修正前の実際の穴

`DENY_TABLE` は 5 category・96 identifier。既存 `test_each_deny_table_category_has_a_mutation_killing_probe`
は category ごとに 1 identifier (代表 probe) だけを非自己参照 golden probe で守っており、残り約90
identifier は個別削除されても無検知だった。

## 3. 設計 (段2 codex plan → 段4 親裁定で確定した plan v2)

`orchestrator/campaign/coder_effect_gate.py` は不変。`orchestrator/tests/test_coder_effect_gate.py`
へ以下を追加した。

1. `_FROZEN_DENY_IDENTIFIERS: dict[str, frozenset[str]]` — category 別・全96 identifier の独立
   literal (`DENY_TABLE` から動的導出しない)。
2. `test_frozen_deny_identifier_still_triggers_its_category` — 全96 identifier を
   `scan_host_effects(f"{identifier}();")` で実際に走らせ、期待 category の finding が出ることを
   assert する意味的 probe (96 parametrized cases)。構造比較 (identifier が消えれば finding が
   出ない) と、scanner 実装破壊の両方を検知する。
3. `test_frozen_deny_identifiers_total_is_96` — frozen literal 自身の内部整合 sanity check
   (`DENY_TABLE` は参照しない)。
4. `test_frozen_deny_identifiers_is_a_literal_not_derived_from_deny_table` — frozen literal の
   代入を AST で静的検査する meta-test。**単一代入の強制** (`_FROZEN_DENY_IDENTIFIERS` への
   `Assign`/`AnnAssign` がちょうど1件) と、**RHS ノード形状の allowlist** (`Name` は
   `"frozenset"` のみ許可、`Attribute`・comprehension は一律禁止、`Constant` は文字列のみ、
   `Call` は `frozenset(...)` 直呼びのみ) で、denylist 方式より強い自己参照防止を行う。

比較則は `current ⊇ frozen` (superset、識別子の削除だけを検知し追加は許容) を採用した —
ratified 文言「縮んでいない」の直訳であり、段3 レンズB が推奨した。既存
`test_each_deny_table_category_has_a_mutation_killing_probe` は scanner の category↔rule_id
対応という別の性質を守るため併存させた。

production と frozen literal を**同一 commit で協調して縮める編集** (真の M6 が実証した pin と
同型の攻撃) は、段4 裁定により本 wave の scope 外の**既知残存**として明記した (理由: (a) 引数が
引用する直接動機は単一箇所の局所編集であり採用した設計で閉じる、(b) 真の M6 対象である
role-contract pin は scope 外のまま、(c) 部分的な暗号的 pin を DENY_TABLE 側にだけ導入しても
真のリスクは閉じず絶対規律5 に反する)。テスト本体にもこの既知残存をコメントで明記した。

## 4. 段3 敵対相談・段6 敵対レビューの所見

- **レンズA (段3、reward hack耐性)**: plan の自己参照防止記述は意図としては正しいが実装拘束が
  弱いと指摘し、AST guard の具体的コード形状を提案。全96件の意味的 probe への設計変更
  (構造比較だけでなく scanner 実動作を検証) を提案。`tools/mutation_harness.py` が実際に
  複数ファイル同時変異 (`replacements` 複数指定) を過去 wave (t396.m6) で実行した実績を
  独立に発見し、「production+frozen literal 協調改変は harness の技術的射程内であり、
  安易に scope 外と決めつけてはならない」と警告 (段4 裁定はこれを受けて既知残存として
  明記する扱いにした — 閉じないことを選んだが、無視はしていない)。
- **レンズB (段3、scope境界)**: (P1)(P2) の事実認定を検算し正しいと確認。D96 は必須要件では
  ないと判定。consumer (`p3_s4_loop.py`、`digest.py`) の網羅性を確認し見落としなしと判定。
  T-1356 (並行 wave、`.claude/agents/auditor.md` 側) との対象ファイル重複なしを確認。
- **段6 レンズ1 (正確性・退行)**: 実装済み AST guard に2つの回避経路を発見
  (i) `next()` で最初の代入だけを見て後続の再代入 (dangerous Assign) を見逃す、
  (ii) denylist 方式のため `_SOURCE = DENY_TABLE` のような別名参照が素通りする。
  **must-fix** として fix stage へ投げ、denylist を allowlist (許可された Name は
  `"frozenset"` のみ) へ設計変更し、単一代入の強制を追加して解消した。
- **段6 レンズ2 (reward hack耐性の最終監査)**: M1〜M5 は意味的 probe で確実に KILLED になることを
  コードから trace で確認。M6 (協調改変) は**総数96 sanity check のおかげで、identifier 2箇所だけの
  中途半端な協調改変はむしろ検知される**ことを発見 (3点 (production・frozen literal・総数96→95)
  すべてを揃えたときだけ段4裁定どおり SURVIVED になる、という M6 の正確な境界を明確化)。
- **段6 焦点再レビュー (fix統合後)**: fix が2つの回避経路を実際に閉じたこと、既存155件への
  非破壊性、段4裁定の境界線が実装に正しく反映されていることを確認し、変異matrixへ進めてよいと
  結論した。

## 5. 変異 matrix 実測

`tools/mutation_harness.py --runner-mode dispatch --detached`、`repo_head=22d68576`、
spec = `mutation-spec.json` (`verbatim/` 収録、sha256=`8b9dcbb8a718d904307f0dafc6eb557a9361e739da281d7c0e4fe7c92606e79d`)。
baseline: 155 passed (2.71s)。

| ID | 対象 | 削除 | 予測 | 実測 | 一致 |
|---|---|---|---|---|---|
| t1357.m1 | process-shell | `fork` (production のみ) | KILLED | KILLED (1 node) | ✓ |
| t1357.m2 | file-stdio | `fopen` (production のみ) | KILLED | KILLED (1 node) | ✓ |
| t1357.m3 | network | `socket` (production のみ) | KILLED | KILLED (1 node) | ✓ |
| t1357.m4 | sleep-block-thread | `pthread_create` (production のみ) | KILLED | KILLED (1 node) | ✓ |
| t1357.m5 | escape-hatch | `syscall` (production のみ) | KILLED | KILLED (1 node) | ✓ |
| t1357.m6 | 協調改変 (既知残存) | `fork` を production・frozen literal・総数96→95 の3箇所 | SURVIVED | SURVIVED (0 node) | ✓ |

**全6件が事前登録どおり一致。** M1〜M5 はいずれも登録した1 nodeだけが失敗し、他への波及なし
(帰属が正確)。M6 は予測どおり0 failureで、段4裁定の既知残存境界が実装と正確に一致することを
実証した。

**DW-M08 新旧比較 (テスト強化だけの wave の義務):** `git show 050b0648:.../test_coder_effect_gate.py`
の**変更前 (旧) テスト本体**を一時的に作業ツリーへ書き戻し、M1〜M5 の production 変異
(fork/fopen/socket/pthread_create/syscall の5件同時削除) を適用して実走したところ、
**57 passed / 0 failed** — 旧テスト群はこれら5件のいずれの削除も検知しなかった
(SURVIVED を実測確認)。実行後 `git checkout --` で両ファイルを commit `22d68576` の状態へ
復元し、`git status --porcelain` が空であることを確認した。新テストは同じ変異を個別に KILLED
にする (§5 表) ため、新テストだけが持つ純増検出力が実測で示された。

## 6. 残る scope (実装しなかったこと)

- 真の M6 対象である role-contract pin (`.claude/agents/coder-v4-autonomous-sort.md` の
  closed-region 契約と SOURCE_FILE_SHA256 等の byte pin) は未着手。「禁止集合が縮んでいないことを
  意味で守る」という ratified 裁定の完全な解決ではなく、DENY_TABLE 側の局所成果である。
- production と frozen literal を同一 commit で協調して縮める編集は、意図的な既知残存として
  scope 外にした (§3 末尾、変異 t1357.m6 で実測確認済み)。

## 7. 環境と実測

計測 (性能) は行っていない。テスト実測はすべて `tools/run_tests.py --force-dispatch` 経由で
Pegasus 計算ノードへ dispatch した。焦点走は fix 前後で2回 (155 passed each)。受入全走の結果は
worklog エントリへ記載する。
