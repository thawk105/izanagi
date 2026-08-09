# 段 4 裁定 — [T-682] provenance 既知違反登録 + probe .md 移行

親 (Claude) が段 2 プランと段 3 の 2 レンズ (A=正しさ境界 sol / B=実効性 luna) を裁定した。
両レンズとも NO-GO。所見 16 件 (A 6 / B 10) を real/refuted・採否・scope で裁定する。

## 1. 所見の裁定

| ID | 判定 | 採否 | 根拠 |
|---|---|---|---|
| A-01 | real | **採用 (強化)** | 抑止が `SHA + kind` だけで、元 finding 本文を見ない。裁定文自身が懸念する「将来の本物の形式違反も同じ経路で登録できる」経路が、note 必須では塞がらない |
| A-02 | real | **部分採用** | `note` 非空・`ruling` 非空は名目だけ。zero-width / 制御文字が通る。構造化 note の強制は過剰なので、A-01 の値 pin で機械的裏付けを与え、note は制御文字を拒否する |
| A-03 | real | **scope 外** | land 関門は `tools/dev_wave_land.py`。並行 wave t139 の所有。本 wave は触らない |
| A-04 | real | **採用 (受入 oracle として)** | 実装差分ではなく、段 6/7 の受入条件の定義を変える |
| A-05 | real | **nit → backlog** | subject を診断へ無加工で流すのは**既存挙動**であり本 wave が導入しない。`DW-G05` の成果物影響を 1 行で書けない |
| A-06 | real | **不採用 (無処置)** | probe 逐語内の指示形は insights の記録データ。fenced block 内であり consumer なし |
| B-01 | real | **採用** | 受理集合不変テストが定数比較と有限例だけでは、`AGENT_VALUE` へ optional token を足す変異を殺せない |
| B-02 | real | **採用** | stale テストの spec に note が無いと、note 必須検査で先に落ち `_ledger_policy_is_visible` へ到達しない |
| B-03 | real | **採用** | synthetic mock だけでは production 分類経路の接続漏れを検出しない |
| B-04 | real | **採用 (分類の是正)** | `:1371`=総台帳長、`:1925/:1939/:1943`=選択 commit の control (30 件へ更新)、`:3517/:3546/:3586`=dispatch 戻り値 (無関係)。親の初期走査の偽陽性を確定 |
| B-05 | real | **scope 外 → 裁定パッケージ候補** | `check_docs` が `output/insights/*.md` を再帰走査しないのは**既存の死角**で、既存 verbatim/*.md すべてに等しく当たる。新 gate 新設は本 wave の scope 外 (`DW-O13` / `DW-G04`)。**「check_docs が検査する」と主張しない**ことだけを義務にする |
| B-06 | real | **採用 (文言限定のみ)** | 移行は「履歴 artifact の実装面是正」であって probe に証拠能力を与えない。.md 本文にその限定を書く |
| B-07 | real | **採用** | 22 note がほぼ同一文では裁定の緩和条件を満たさない。A-01 の値 pin + commit 固有事実で補う |
| B-08 | real | **採用 (親の検証手順)** | 所有境界は実 diff で照合する。凍結境界の主張は「この manifest にない」と限定する |
| B-09 | real | **採用 (A-04 と同じ)** | 「23 件登録 → rc=0」は条件付きにしか成立しない |
| B-10 | real | **採用 (現状維持)** | literal 固定は保守負担だが正しい。緩めない |

## 2. plan v2 (段 5 実装子への確定指示)

### 2.1 production (`tools/check_ai_provenance.py`)

1. `:132-134` に `MALFORMED_AI_AGENT = "malformed-ai-agent"` を足し、
   `_LEDGER_FINDING_KINDS` へ加え、`_NOTE_REQUIRED_FINDING_KINDS = frozenset({MALFORMED_AI_AGENT})`
   を新設する。
2. `KnownViolationSpec` へ **`expected_finding_value: str = ""` を追加**する (A-01)。
   意味は「その commit で観測された不正 `AI-Agent` trailer の値そのもの」。
3. `_known_violation_registry()` の検証を追加する。既存検査の順序と診断文言は変えない。
   - `expected_finding_value` の型検査 (str)。
   - `MALFORMED_AI_AGENT` の entry は `expected_finding_value` **非空必須**、
     他 kind は**空必須** (二義化防止)。
   - `_NOTE_REQUIRED_FINDING_KINDS` の entry は `not note.strip()` なら RuntimeError。
   - 必須 note と `expected_finding_value` に**制御文字・zero-width (U+200B〜U+200D, U+FEFF) を
     禁止**する (A-02)。
   - 挿入位置は既存の note 改行検査 (`:241-245`) の後、`registry[...] = spec` の直前。
4. `_normal_commit_audit()` (`:963-971`) の kind 付与を private helper へ出す。
   判定は**完全な `label` を含む固定 prefix** `f"{label}: AI-Agent の形式違反: "`。
   単なる substring 判定にしない (P1、B-01 の変異対象)。
5. `_known_violation_audit()` (`:1027` 付近) の照合に **値一致を足す** (A-01)。
   `spec.expected_finding_value` が非空なら、finding 本文が
   `f"{label}: AI-Agent の形式違反: {spec.expected_finding_value!r} — "` で始まることを要求する。
   空なら従来どおり `SHA + kind` のみ (既存 7 件は不変)。
6. `_ledger_policy_is_visible()` (`:1049` 付近) の常時可視分岐へ `MALFORMED_AI_AGENT` を加える。
7. ruling 定数 2 本を新設する。**worklog 番号を使わない** (P4)。
   - `_T139_MALFORMED_RULING = "2026-08-09 dev-wave-jobs/rulings-inbox/2026-08-09-t139-r4-probe-provenance-format-violation.md"`
   - `_T659_PROBE_RULING = "2026-08-09 dev-wave-jobs/rulings-inbox/2026-08-09-t659-provenance-and-f37-rulings.md"`
8. `KNOWN_PROVENANCE_VIOLATIONS` の**既存 7 件を一切変えず**、末尾へ 23 件を
   `violations-23.tsv` の順で足す。22 件は `MALFORMED_AI_AGENT` +
   `expected_finding_value="product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"`、
   `2c1929533a6f641b513f4f7990fe06e6cdb383b1` は `MISSING_CODEX_AUTHOR` +
   `expected_finding_value=""`。

**note の書式** (B-07)。22 件は次の 3 要素を 1 行で持つ。
(i) 内容は正確で綴りだけの誤りである理由 = 「実装面は Codex `role=author` が書き親が統合した」、
(ii) 不適合フィールド = `model` の角括弧と `role=orchestrator` の 2 点、
(iii) **その commit 固有の事実** = `git show --name-only` で観測した実 path 種別
(merge commit は combined path の有無まで書く)。
22 件すべてで trailer literal が同一である事実も各行に明記する
(値そのものは `expected_finding_value` が機械的に持つ)。
`2c192953` にも説明 note を付けるが、`MISSING_CODEX_AUTHOR` は note 必須集合へ入れない。

### 2.2 テスト (`orchestrator/tests/test_check_ai_provenance.py`)

**既存の期待値を反転・緩和・skip・削除してはならない。**

更新:
- `:1323` `..._is_exactly_seven_literal_entries` → 30 件の literal 完全一致へ。
  SHA・kind・ruling・note・`expected_finding_value`・順序まで固定。production/TSV から
  動的生成しない。`_LEDGER_FINDING_KINDS` と `_NOTE_REQUIRED_FINDING_KINDS` の exact pin を追加。
- `:1385` `..._matches_real_commit_findings` → 入力を 30 SHA へ拡張し、
  `(SHA, kind)` の exact 列を 30 件へ更新。
- `:1925` 系 empty-registry control → 30 件へ拡張。空 registry で exact 30 finding
  (内訳: trailer なし 6 / Codex author なし 2 / 形式違反 22) を固定。

新設:
- `note` 必須の正負対 (`""` と `" \t"` が rc=2、非空単一行は通る、旧 kind + 空 note は通る)。
- 制御文字・zero-width を含む note / value の拒否 (A-02)。
- `expected_finding_value` の正負対 (A-01)。
  **同じ SHA・同じ kind で値だけ違う finding は抑止されない**ことを固定する。
  malformed entry の値が空、非 malformed entry の値が非空はいずれも rc=2。
- full-label anchored 分類 (subject に `: AI-Agent の形式違反: ` を埋め込む。
  duplicate / `none` 混在 / reserved product / `model=none` は `ledger_kind is None`)。
- 登録済み malformed の抑止を **実 `_normal_commit_audit()` 経由**で固定する (B-03)。
- 未登録 malformed が rc=1 のまま。**少なくとも 1 例は production registry を差し替えず、
  30 件集合外の SHA を使う** (B-03)。
- malformed の stale rc=2。**spec に非空 note と非空 value を持たせる** (B-02)。
- 受理集合不変 (B-01)。`ROLES` / `IDENT` の literal 比較に加え、
  **reject matrix** を `AGENT_VALUE.fullmatch()` と `validate_message()` の両方で固定する。
  matrix には少なくとも: 末尾に未知 token を足した形 (`; extra=x`)、フィールド順序違い、
  未知フィールド名、`model=claude-opus-5[1m]`、`role=orchestrator`、大文字始まり identifier
  を含める。正例として `product=claude; model=claude-opus-5-1m; reasoning=high; role=manager`
  と全 5 role を含める。

### 2.3 probe 移行

- `output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py` を削除し、
  同 directory へ `probe_split_window.md` を作る。
- 先例 `output/insights/2026-08-08_t664-docs-budget/verbatim/firing-evidence-script.md` の構成
  (H1 / 説明 / repo 外控えの path / ```python fenced block) に倣う。
- 本文に書くこと: 元 repo path、元 `.py` bytes の sha256
  `0128696a79035139ffaba3732cd3b20400eb231fb3124af98496665d70da455d` (**`.md` 全体や fence 内の
  digest ではなく元 `.py` bytes の digest**と明記)、repo 外の byte 同一控え
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py`、
  および **B-06 の限定** —「本移行は履歴 artifact の実装面是正であり、probe に証拠能力を
  与えるものではない。probe は既存テストより弱く、[T-659] の裁定で証拠から外されている」。
- fenced block へ元 `.py` を shebang から終端まで逐語転記する。
- **`verbatim/README.md` を新設しない** (存在しない。作らない)。

### 2.4 所有と権限

段 5 実装子が触ってよいのは次の 4 path だけ。

- `tools/check_ai_provenance.py`
- `orchestrator/tests/test_check_ai_provenance.py`
- `output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py` (削除)
- `output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.md` (新設)

親が担う: `README.md:29,39` と `package.md:38` の path 表記、worklog/insights/spool、
commit、受入全走、変異走行。実装子は docs 編集と commit をしない。
`docs/worklog.md:2049` と `docs/archive/` の probe 言及は凍結記録なので**誰も触らない**。
`tools/dev_wave_land.py` と `docs/dev-wave/` は**本 wave の誰も触らない** (A-03、peer 所有)。

## 3. 変異事前登録 (DW-M01)

実装後に anchor 逐語を確定して `mutation-spec.json` を発行する (`DW-M07`)。
位置・単一理由・期待 node は本節で先に確定する。各変異は「その 1 行を無効化したとき
赤くなる理由が 1 つに絞れる」ことを実装後に確認し、絞れなければ登録せず実効 gate へ再照準する。

| ID | 位置 | 無効化する防壁 | 期待赤の単一理由 |
|---|---|---|---|
| M1 | `_known_violation_registry()` の note 必須検査を削除 | 追加 kind の note 必須 | 空 note の malformed entry が registry を通る |
| M2 | kind 分類 helper の anchored prefix を bare substring (`"AI-Agent の形式違反" in finding`) へ | full-label anchoring | subject 注入 finding が誤って malformed kind を貰う |
| M3 | `_ledger_policy_is_visible()` から `MALFORMED_AI_AGENT` を除去 | stale の可視性 | malformed の stale が `expected-finding-missing` でなく不正 kind 扱いになる |
| M4 | `_known_violation_audit()` の `expected_finding_value` 一致条件を削除 | 値 pin (A-01) | 同 SHA・同 kind で値の違う finding が抑止される |
| M5 | `AGENT_VALUE` の末尾へ `(?:; extra={IDENT})?` を追加 | 受理集合の不変 | 未知 token 付き trailer が受理され形式違反にならない |
| M6 | `_known_violation_registry()` の zero-width / 制御文字拒否を削除 | note/value の名目化防止 (A-02) | zero-width だけの note が通る |

`hang_risk` は全件 false。想定所要は harness 6 変異 × 受入部分集合。
`DW-M08` に従い `-rf` を指定し、赤 node を毎回記録する。
本 wave は production を変えるため「テスト強化だけの wave」ではなく、新旧両走は登録しない。

## 4. 受入 oracle (A-04 / B-09)

「23 件登録 → rc=0」は**無条件には成立しない**。受入は次の条件付き命題として測る。

- 統合 commit 後に `python3 tools/check_ai_provenance.py` を**パイプへ通さず**単独 rc で実行し、
  **rc=0 / 新規違反 0 / known-violations=30 / stale 0** を実測する。
- 本 wave 自身の commit も監査対象に入る。実装面 path (`tools/`、`orchestrator/tests/`、
  probe `.py` の削除) を含む commit は `product=codex; ...; role=author` を必ず持つ。
- 受入全走 (`tools/run_tests.py` の受入形) を背景で 1 回通す。
- 実測前に worklog へ結果欄を作らない。

## 5. ユーザーへ返す項目 (実装しない)

- **B-05**: `tools/check_docs.py` が `output/insights/**/*.md` を再帰走査しない死角。
  既存の全 verbatim package に等しく当たる既存問題で、新 gate 新設は本 wave の scope 外。
  段 7 で insights へ記録し、裁定パッケージ候補として返す。
- **A-03**: land 関門 (`tools/dev_wave_land.py`) は並行 wave t139 の所有。
  本 wave の land 後に peer が有効化する順序で合意済み。
- **A-05**: 診断へ subject を無加工で流す既存挙動。backlog。
