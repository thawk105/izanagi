# 段 4 裁定 — fig3b_arc_status_2026-09-20 (plan v2 + 変異事前登録)

裁定時刻: 2026-09-20 07:48 JST。基準 HEAD `b7f970dfa` (main 不変を再確認)。裁定 inbox (`dev-wave-jobs/rulings-inbox/`) に本 wave 関連の項目なし。

## 所見の裁定

| 所見 | 判定 | 採否 | 内容 |
|---|---|---|---|
| A-M1 数量検査が脚注の `§8` / `§0` を拒否 | real | 採用 | 構造参照 (節番号・図番号・版日付) は生成器が構造 field から組み立て、自由文検査の対象外にする。自由文 (label / sublabel / 状態定義文 / 脚注の自由部分) だけを検査 |
| A-M2 anchor を項目 ID 形へ | real | 採用 | `source_anchor` は `§8 A-1` / `§0 item 3` / `§0 act 3` の 3 形式。生成器は本文の該当節内で見出し行の**一意な存在**だけを検査 (意味は段 6 review) |
| B-M1 色・マーカーの実 artist 検査 | real | 採用 | test 側に独立の状態→色・マーカー表を持ち、Patch の facecolor と Line2D の marker を照合。中立行はマーカー無しを確認 |
| B-M2 変異の単一理由性 | real | 採用 | 下の事前登録表のとおり層ごとに分け、等価変異は登録しない |
| A-S1 副ラベルの限定補完・定義統一 | real | 採用 | 下の JSON 内容表に反映 (A-1 / A-4 / A-5 / B-4 / B-7 / B-9 / Act 3 A-1 行)。brief の 4 状態定義は plan の定義へ差し替え |
| A-S2 caption を記述範囲に縮める | real | 採用 | consult 案の 2 文へ置換 (「gate は変わらない」型の保証文を書かない) |
| A-S3 09-20 整合は限定・人間手番まで比較、JSON 名を版で | real | 採用 | JSON 名 `tools/plotting/arc_status_story_2026-09-19.json`。README に「状態 enum・副ラベル・限定・人間手番を項目ごとに比較」と書く。JSON は凍結物ではない (再現のため残す方針、規則ではない) と分けて書く |
| B-S1 数量検査は小さい表示契約に | real | 採用 | 自由文: Unicode 数字を全面拒否、ただし **JSON 内で宣言された ID** (証拠項目 id と top-level `reference_ids`) に token 全体一致するものだけ許す。`=`、`%`/`％`、単位語 (`tps` `µs` `μs` `us` `ms` `ns` `sec` `seconds` `percent`)、数詞の固定小集合 (`zero one two three four five six seven eight nine ten eleven twelve twenty thirty hundred thousand million dozen once twice thrice`) を拒否。NFKC は残す。自然言語の数量判定へは広げない |
| B-S2 所有と衝突の分離 | real | 採用 | 兄弟セル同士だけ非交差、親子包含は許す、複数行 Text は全体 bbox、marker は padding 込み bbox、中立横線は高さ条件を課さない、Agg 200 dpi で検査し PDF は親が目視 |
| B-S3 最小性 | real | 採用 | 状態定義文の正本は JSON のみ (code に複製しない)、JSON 異常系は描画せず parametrize、`--states` と既存出力拒否は残す |
| B-S4 所要の予算化 | real | 採用 | 実寸描画は 7 回以内を目標にし、親が実測して worklog に書く。目安 20 秒超なら fix で削る |
| B-N1 checker / lint 適合は未確認 | real (nit) | 記録 | 親が commit 前に `check_ai_provenance.py` と `check_docs.py` を現物で通す |

refuted: なし。scope 外 real 所見: なし。

## plan v2 (段 2 plan からの差分だけ)

1. **file 名:** 生成器 `tools/plotting/plot_arc_status.py`、状態 JSON `tools/plotting/arc_status_story_2026-09-19.json`、test `orchestrator/tests/test_plot_arc_status.py`。出力 prefix `docs/paper-story/figures/fig3b_arc_status_2026-09-20` (親が生成)。
2. **JSON schema (`izanagi-arc-status/v1`):** top-level = `schema`, `story_version` (ISO 日付), `story_path` (`docs/paper-story/<story_version>.md` と一致必須), `figure_created` (ISO 日付、図名の日付), `reference_ids` (自由文で許す ID token の配列、各 `^[A-Za-z]+[0-9]*-?[0-9]+[a-z]?$` に一致し重複不可), `state_definitions` (4 key 固定、値は自由文 = 検査対象), `acts` (3 件), `evidence_groups` (2 件: A, B)。act = `id` (`Act 1`〜`Act 3`), `label`, `progress` (`complete` | `in-progress`), `source_anchor`, `items[]`。item (act 行・証拠項目共通) = `id`, `label`, `state`, `sublabel`, `source_anchor`。証拠項目の `state` は 4 値必須、act 行だけ `null` 可。key 集合は各階層で完全一致 (未知・不足・重複 key 拒否、NaN/Infinity 拒否)。
   4 状態の key: `obtained` / `uncertified` / `awaiting-ruling` / `not-obtained`。表示名は生成器が固定で持つ: `obtained` / `uncertified` / `awaiting ruling / human action` / `not obtained`。
3. **anchor 検査:** `§8 <item-id>` → §8 節 (`## 8.` 見出しから `## 9.` 直前) 内に `- **<item-id>` で始まる行 (直後は空白・`.`・`(` のいずれか) が**ちょうど 1 行**。`§0 item <n>` → §0 節内に `^<n>\. \*\*` の行がちょうど 1 行。`§0 act <n>` → §0 節内に `- **第 <n> 幕` の行がちょうど 1 行。本文は bytes で 1 回読み、同 bytes の SHA-256 を provenance に記録。
4. **自由文検査:** 上表 B-S1 のとおり。構造参照 (脚注の `paper-story 2026-09-19`, `section 0`, `section 8`, `fig3`, `Figure 3b`) は生成器が構造 field (`story_version`, 図番号) から組み立て、検査対象外。脚注の自由部分は JSON `footnote_lines` にせず生成器の固定文 (数字を含まない) にする。
5. **図の要素:** plan のとおり (16×11.5 in、200 dpi、Act 3 箱、A 1×5、B 2×6 (11 セル + 空き 1)、凡例 2×2、脚注 3 行)。色 = obtained `#DCEAF5` 塗り丸、uncertified `#FCE8CF` 中抜き菱形、awaiting-ruling `#EBDFF2` 中抜き三角、not-obtained `#EEEEEE` ×。Act 3 の中立行は短い横線・マーカー無し。単語境界で折返し、収まらなければ保存拒否 (縮小・切捨て禁止)。
6. **layout check:** B-S2 のとおり。全可視 Text を `fig.findobj(Text)` で集め、figure 内包 + 所属領域内包 + 他 Text との交差 ≤ 1 px² + 兄弟セル非交差 + 幅・高さ有限正。
7. **provenance (`izanagi-arc-status-figure-provenance/v1`):** `generated_utc`, `story_version`, `story_path`, `figure_created`, `inputs[]` ({kind: states|story, path, sha256}), `generator` ({path, sha256}), `outputs[]` (png/pdf の path, sha256), `drawn_items[]` ({id, state, label = 実表示文字列}), `state_definitions`, `caption`, `argv`, `versions` ({matplotlib, numpy})。自己 hash なし。
8. **caption (英文、provenance と同一):**
   `Figure 3b. Status of the paper-story arc read from the frozen 2026-09-19 story: act summaries from section 0 and evidence-item states from section 8. Colors and marker shapes distinguish obtained, uncertified, awaiting ruling / human action, and not obtained. Obtained records that a judgment or completion exists, not that a claim is supported: B-1 remains not met and A-6 records reject. A-3 is a settled reporting rule, not new empirical evidence. A-1 remains descriptive and non-certifying; A-4 is adopted by ruling but inactive pending human action. B-7, B-9, and B-10 are neither promoted nor closed by this figure. This figure summarizes recorded statuses; it does not evaluate correctness, certify performance, or authorize further work. A-2 and A-6 retain the judgments made under the identity layer used at the time; later identity fixes do not strengthen them retrospectively. No measurement values are drawn and no judgments are recomputed. Successor to fig3; the original remains frozen.`
   caption の数字 (3b, 2026-09-19, 0, 8, A-1 等) は構造参照と宣言 ID なので自由文検査の対象外 (caption 全体は検査しない。caption は生成器の固定 template + 構造 field)。
9. **CLI:** `python3 tools/plotting/plot_arc_status.py [--repo-root PATH] [--states PATH] OUT_PREFIX`。prefix basename は `^fig[0-9]+[a-z]*_`。既存の 3 出力のいずれかが存在すれば拒否 (上書きしない)。layout check 通過前に出力 dir・一時 file を作らない。失敗時は新規 file を残さない。
10. **test (8 本、実寸描画 ≤ 7 回):** T1 実 JSON 実寸描画 + layout 通過 + 構造数 (3/5/11) + 全 ID の表示、T2 状態→色・マーカー・provenance の一致 (独立表) + 実寸 copy の 1 項目を変えて描画と provenance へ届く、T3 JSON 異常系 parametrize (描画なし: 不正 state、証拠項目の null、重複 ID、未知/不足 key、不正 anchor、非一意 anchor、story_path 不一致、自由文の数量 4 例)、T4 自由文検査の関数単体 (宣言 ID 受理 / `38%` `10 tps` `2 µs` `A=0.58` `three runs` `applied twice` 拒否)、T5 layout: 同一セル内 2 Text を重ねて overlap 拒否 / Text を figure 外へ出して escape 拒否 (別 fixture)、T6 衝突 Figure を `_publish_outputs` へ直接渡し例外 + 出力ゼロ (隠し一時 file も無し)、T7 CLI 正常 (tmp prefix `fig3b_...`) で 3 出力 + magic bytes + provenance の sha256 を独立 hashlib で照合 + schema/caption/argv/versions + 同 prefix 2 回目は rc≠0 で既存 bytes 不変、T8 CLI 不正 prefix `foo_` は rc≠0 で出力ゼロ。`MPLBACKEND=Agg` を test と生成器で固定、Figure は必ず close。
11. **README:** plan のとおり + 09-20 整合手順 (A-S3) + 二重日付の説明 + JSON は凍結物でない旨。`docs/paper-story/README.md` は触れない。
12. **JSON 内容 (author が写す。値・数量は書かない):**

`reference_ids`: `["T-1998", "S-1a", "P2-4", "P2-5", "D2114", "fig3", "fig8"]` (使うものだけ。未使用は入れない — author が実使用で確定)

state_definitions:
- obtained: `A recorded judgment or completion exists; it need not support the claim.`
- uncertified: `Materials exist; the item is not certified, promoted, or closed.`
- awaiting-ruling: `A ruling or human action remains pending before the item can advance.`
- not-obtained: `The required evidence is not yet obtained, including blocked work.`

acts:
- Act 1 `Trustworthy evaluator` progress complete anchor `§0 act 1`; items: `act1-evaluator` / `Build a trustworthy evaluator` / obtained / `complete` / `§0 act 1`
- Act 2 `Falsification and synthesis` complete `§0 act 2`; items: `act2-hypothesis` / `Search hypothesis` / obtained / `falsified` / `§0 act 2`; `act2-value` / `Value beyond the search space` / obtained / `relocated to synthesis` / `§0 act 2`
- Act 3 `Code-level synthesis` in-progress `§0 act 3`; items: `act3-claim` / `S' claim` / obtained / `not met` / `§8 B-1`; `act3-scope` / `Silo-only scope` / null / `lifted; preparation underway` / `§0 item 3`; `act3-mechanism` / `Mechanism work` / null / `advanced; claim remains unmet` / `§0 act 3`; `act3-formal` / `Adopted configuration` / obtained / `A-2 observed-positive; A-6 reject; T-1998 accepted` / `§0 act 3`; `act3-descriptive` / `A-1 descriptive attempt` / uncertified / `completed; non-certifying` / `§0 item 1`

evidence_groups A (`A-series items`):
- A-1 `Paired headline estimand` uncertified `descriptive; non-certifying; fulfilment undetermined; reauthorization requires human action` `§8 A-1`
- A-2 `Write-heavy / balanced certification` obtained `observed-positive; limitations retained` `§8 A-2`
- A-3 `Reporting rule` obtained `settled; rule only; not evidence` `§8 A-3`
- A-5 `Separate-boot reproduction` not-obtained `unfulfilled; Pegasus does not establish separate-boot reproduction` `§8 A-5`
- A-6 `Read-heavy certification` obtained `reject; limitations retained` `§8 A-6`

evidence_groups B (`B-group requirements`):
- A-4 `Official floor` awaiting-ruling `adoption decided; chain not landed; inactive; human action pending` `§8 A-4`
- B-1 `Beyond best known axis` obtained `not met` `§8 B-1`
- B-2 `Descriptor causal evidence` not-obtained `not run; layered blockage` `§8 B-2`
- B-3 `Formal holdout series` not-obtained `not completed; authority absent` `§8 B-3`
- B-4 `Detailed anomaly feedback` not-obtained `not run; descriptive-only; specs frozen; eligible precursor absent` `§8 B-4`
- B-5 `Budget-matched generator comparison` not-obtained `not obtained` `§8 B-5`
- B-6 `Leak-controlled execution` not-obtained `loop exercised; leak control incomplete` `§8 B-6`
- B-7 `All-workload regression reporting` uncertified `materials complete; not promoted to requirement fulfilment` `§8 B-7`
- B-8 `Independent long-run validation` not-obtained `not obtained` `§8 B-8`
- B-9 `Mechanism reporting` uncertified `screening support scoped; deep check stopped by ruling; secondary view applied, non-certifying` `§8 B-9`
- B-10 `Extended mechanism evidence` uncertified `grid and tail judged; performance uncertified; not closed` `§8 B-10`

脚注 (生成器固定、構造参照は field から):
- `Evidence states: paper-story <story_version> section 8; act summaries: section 0. No values drawn.`
- `Obtained does not imply a supported claim. A-3 is a settled rule, not new evidence.`
- `Successor to fig3; the original remains frozen. Statuses are recorded, not evaluated, here.`

## 変異事前登録 (DW-M01、単一理由性)

| # | 位置 (関数) | 変異 | kill する test | 赤理由 (1 つ) と fixture |
|---|---|---|---|---|
| M1 | `load_states` の state 検査述語 | 4 値の membership を恒真にする | T3 (不正 state `bogus`) | 不正 state が受理される。他層 (key 集合・anchor) は正常な fixture |
| M2 | `load_states` の key 集合検査 | 未知 key を無視する (完全一致 → 部分集合) | T3 (item に `extra: 1` を注入) | 未知 key が受理される。key 集合検査は 1 か所だけに実装 (二重にしない) |
| M3 | 自由文検査関数 | 本体を早期 return にする | T4 (`three runs` / `38%` / `A=0.58`) | 数量が受理される。他層はこれらを拒否しない (ID 検査は digit 無しの token を見ない) |
| M4a | `check_figure_layout` の交差面積 | `_intersection` を常に 0 | T5-overlap (同一セル内 2 Text を同座標へ) | 交差が検出されない。escape・兄弟セル条件には掛からない座標 |
| M4b | `check_figure_layout` の内包 | `_contains` を常に True | T5-escape (Text を figure 外へ移動、他 Text と交差しない位置) | 逸脱が検出されない |
| M5 | `build_provenance` の inputs sha256 | 実 hash を別の有効長 64-hex 定数に置換 | T7 (独立 hashlib 照合) | provenance の hash 不一致。digest 形式検査は通る値 |
| M6 | `make_figure` の状態→style 対応 | 全セルを obtained の色・マーカーで描く | T2 (独立表で facecolor / marker 照合) | artist の style 不一致。Text と provenance は正しいまま |
| M7 | `_publish_outputs` | `check_figure_layout` 呼出しを削除 | T6 (衝突 Figure を直接渡す) | 検査なしで出力が公開される。test は事前に check を呼ばない |
| M8 | prefix 検査述語 (`_figure_number` 相当、1 関数) | 常に受理 | T8 (`foo_x`) | 不正 prefix が受理される。main と publisher の両呼出しが同じ述語を使う |

登録 8 件。等価変異が実装後に判明したら除外して台帳に理由を書く。変異は実装後 (段 6) に登録 anchor を実行番号へ確定して走らせる。

## scope の再確認

- 実装面 = 生成器 + JSON + test (Codex author)。docs = 親。生成物 = 親が login で生成。
- 段 6: read-only review 1 本 (一次資料からの状態写しを含む) + 必要なら fix 子。変異 8 件。受入全走。
- 「実装しない」裁定ではないので 5 → 6 → 7 → 8 → 9 の通常遷移。
