# 段 1 brief — fig3 の後継図 fig3b_arc_status_2026-09-20 (wave dev-wave-fig3b-arc-status)

基準 HEAD: local main `b7f970dfa507558f7fb669a5ab38958d6c76b57c` (2026-09-20 07:19 JST、fresh worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig3b-arc-status`、branch `worktree-dev-wave-fig3b-arc-status`)。

## 研究前進 (1 行)

論文ストーリーの図 3 (3 幕構成の現況図) は 2026-07-10 版時点の模式図で第 3 幕と不一致 (各版 §0・入口 README が明記)。
本 wave は **2026-09-19 版** (main 上の最新版。09-20 版は稼働中 wave `dev-wave-paper-story-2026-09-20` で未 land) の
第 1〜3 幕と §8 A/B 群の**状態**だけを描いた後継図 1 枚と再現可能な生成器を着地させる。完了判定 = 生成器が実 JSON で rc=0
で png/pdf/provenance の 3 成果物を出し、`figures/README.md` に節が載り、受入全走が緑で land。

## scope

- 新規 `tools/plotting/plot_arc_status.py` (最小の生成器、matplotlib/numpy のみ、§9 の fail-closed layout check、§6 provenance)。
- 新規 状態 JSON をスクリプト脇に置く (例 `tools/plotting/arc_status_2026-09-20.json`)。**tools/ 配下の非 Markdown は D95 決定 2 で
  実装面** → JSON も Codex author が書く (内容の状態表は親が brief で渡す)。
- 出力 `docs/paper-story/figures/fig3b_arc_status_2026-09-20.{png,pdf,provenance.json}` (親が login node で生成、計測機の外)。
- `docs/paper-story/figures/README.md`: 図の一覧に 1 行 + 新節 (何を示す図か / 既存図との関係 / 入力 / 再現 / 作図規約への適合 /
  キャプション正文 / proof chain)。`tools/plotting/README.md` に command 例の節 (FIGURE_CONVENTIONS 末尾の手順 4)。
- **scope 外:** 汎用作図 framework、新 gate、台帳の追加、旧 fig3 の上書き・改変、`docs/paper-story/README.md` (入口、hot file) の編集、
  09-19 版本文の変更 (凍結物)、着地 bytes の pin test (「gate」に当たる)。

## 確定済みユーザー裁定 (引数)

- 凍結図は上書きせず、後継図は別 filename + 再現可能な生成器を伴うときだけ (figures/README 冒頭規則)。
- 値は書かず状態 (取得済み / 非認証 / 裁定待ち / 未取得) だけを示す。内容は 09-19 版の第 1〜3 幕 + §8 A/B 群。
- Codex author (D95) が生成器を書く。FIGURE_CONVENTIONS に従い計測機の外で生成。規律 2 を緩めない。
- 設計 (図の要素・生成器の形) は段 2 の plan で確定し、ストーリー 09-20 版と整合させる (草稿は現時点で時点語の置換のみ、
  状態語の差分なし。段 4・段 7 で再確認する)。

## 不変条件

- 規律 2 / 3 / 7: 図は判定を作らず、09-19 版 §8 の【状態】から読んだ状態を写すだけ。生成器は判定を再計算しない。
  A-2 の observed-positive 等の判定は当時の identity 層の下のものとして「取得済み」に置く (規律 7)。
- 図に数値 (%, tps, µs, p 値, 反復数, 日付以外の量) を出さない。ID (A-1, S-1a, D2114, fig8) は値ではない。
- 既存図 fig1〜fig9 の bytes は 1 byte も変えない。
- 生成器は matplotlib/numpy のみ、layout check は保存前・fail-closed (§9)。provenance に入力 JSON と 09-19 版本文の path+SHA-256、
  生成器・出力の SHA-256、描いた項目と状態の一覧、caption、argv を記録 (§6)。
- FIGURE_CONVENTIONS §1 (入力は WAL/dat) は数値図の規約であり、本図は値を持たない模式図 — 位置づけを README 節に明記する
  (fig4 節が凍結 report を権威とする限定例外を書いた前例と同型)。

## 成果物の形 (親の provisional 設計 = 攻撃対象)

- **(P1) 図の構成:** 上段 = 3 幕の箱 (旧 fig3 と同じ横並び、Act 1 / Act 2 = 完了、Act 3 = 進行中) で各箱に 2〜5 行の要点を状態マーカー付きで置く。
  下段 = §8 の証拠項目を A 群 (A-1, A-2, A-3, A-5, A-6) と B 群 (B-1〜B-10, A-4) の 2 行のセル格子にし、各セルを状態で塗り分け、
  短い英語ラベル (項目 ID + 5 語以内の名前) を付ける。凡例は 4 状態 (色 + マーカー形で白黒でも判別)。脚注に
  「states read from paper-story 2026-09-19 §8; no values drawn」。C 群は描かない (依頼が A/B 群と限定)。
- **(P2) 言語:** 図中は英語 (旧 fig3・fig4〜fig9 と同じ、font は DejaVu Sans でCJK 依存を避ける)。README 節と JSON の `note` は日本語可。
- **(P3) 状態語の許容範囲:** 4 状態は色/マーカーで示し、セル文字列には §8 の【状態】が持つ判定語 (not met / observed-positive /
  reject / accepted / not-observed) を短い副ラベルとして置いてよいが、数値は置かない。判定語は「値」ではなく状態語の一部と扱う。
- **(P4) test:** FIGURE_CONVENTIONS §10 の最小 1 本 `orchestrator/tests/test_plot_arc_status.py` (実 JSON = 実寸 fixture で本物の Figure を
  layout check に通す、不正 state / 重複 ID / 数値混入の拒否、provenance の形)。着地 bytes の pin test は作らない (gate = scope 外)。
  所要は数秒以内。
- **(P5) 入口 `docs/paper-story/README.md` には触れない** (hot file、受入 owned-path 衝突の実測あり。fig3 注記は今も真)。
- **(P6) 状態の写像 (JSON の内容、§8 の【状態】から):**

| 項目 | 状態 | 副ラベル (値なし) | 出所 |
|---|---|---|---|
| Act 1 (Phase 1) | 取得済み | trustworthy evaluator first — complete | §2 第 1 幕 |
| Act 2 (Phase 2) | 取得済み | hypothesis falsified (P2-5) / value relocated (P2-4) — complete | §2 第 2 幕 |
| Act 3 (Phase 3) | 進行中 (箱の色は中立) | S' not met (a); Silo-only scope lifted (b, D2114); mechanism deep (c); adopted config: 3 formal runs (f); A-1 descriptive attempt (f) | §2 第 3 幕, §0 |
| A-1 | 非認証 | attempt-0001 descriptive (non-certifying lane); re-authorization = human turn | §8 A-1 |
| A-2 | 取得済み | observed-positive (write-heavy/balanced), limitations (i)–(v) | §8 A-2 |
| A-3 | 取得済み | settled rule (not evidence) | §8 A-3 |
| A-5 | 未取得 | 0 attempts measured; Pegasus does not satisfy (D1525) | §8 A-5 |
| A-6 | 取得済み | reject (read-heavy) | §8 A-6 |
| A-4 (B 群) | 裁定待ち | official floor measured (not in effect); chain not landed; A/X = human turn | §8 A-4 |
| B-1 | 取得済み | not met (S-1a) | §8 B-1 |
| B-2 | 未取得 | not run; blockage is layered | §8 B-2 |
| B-3 | 未取得 | not completed; authority absent (D1829) | §8 B-3 |
| B-4 | 未取得 | not run; specs frozen, no eligible precursor | §8 B-4 |
| B-5 | 未取得 | not obtained | §8 B-5 |
| B-6 | 未取得 | not reached; K2 round 2 closed, leak control incomplete | §8 B-6 |
| B-7 | 非認証 | materials complete; not promoted to requirement (D2044 §3) | §8 B-7 |
| B-8 | 未取得 | not obtained | §8 B-8 |
| B-9 | 非認証 | (a) done, (b) stopped by ruling, (c) v3 applied once (non-certifying) | §8 B-9 |
| B-10 | 非認証 | grid judged; right-tail cohort judged, fig8; performance not certified; not closed | §8 B-10 |

  4 状態の定義 (JSON と凡例に置く): 取得済み = 正式 protocol の判定または完了が出ている (判定の向きを問わない);
  非認証 = 測定・材料はあるが認証・昇格・発効していない; 裁定待ち = 次の一歩がユーザー裁定または人間手番;
  未取得 = 実測・実走がまだ無い (構造的閉塞を含む)。A-1 (非認証 + 再認可は人間手番) と A-4 (値あり + 人間手番) の主状態は
  この定義で決めた — 割れうる。
- DW-G05: 放置時の成果物への影響 = 論文の現況図が第 3 幕と不一致のまま (certified 選択・レポート・台帳の値は変わらない)。
  本図は判定・受理集合・値を変えない。

## 変更面 (実アンカー表)

| path | 種別 | 誰が | 備考 |
|---|---|---|---|
| `tools/plotting/plot_arc_status.py` | 新規・実装面 | Codex author | 雛形: `plot_a1_sized_paired.py` の `check_figure_layout` / `build_provenance` / `_publish_outputs` の分離 |
| `tools/plotting/arc_status_2026-09-20.json` (名前は段 2 で確定) | 新規・実装面 | Codex author | 状態表 (P6) を機械可読に |
| `orchestrator/tests/test_plot_arc_status.py` | 新規・実装面 | Codex author | (P4) |
| `docs/paper-story/figures/fig3b_arc_status_2026-09-20.{png,pdf,provenance.json}` | 新規・生成物 | 親 (login で生成) | 凍結物になる |
| `docs/paper-story/figures/README.md` | 追記 (一覧 1 行 + 新節) | 親 | 既存節は変えない |
| `tools/plotting/README.md` | 追記 (新節) | 親 | command 例 |
| `output/insights/2026-09-20/fig3b-arc-status/README.md` | 新規 | 親 | 逐語・変異台帳・裁定 |
| `docs/spool/` fragment (worklog) | 新規 | 親 | 段 7 |

## 並列分割方針・段構成

軽量版ではなく、設計択一が割れる (P1〜P6) ため: 段 2 plan 1 本 (read-only codex) → 段 3 consult 1 本 (2 レンズ: 「規律 2/7 と
値の混入」「§8 の状態語の誤写・09-20 版との不整合」) → 段 4 裁定 (変異事前登録を含む) → 段 5 Codex author 1 本 (script + JSON + test)
→ 親が login で実走して 3 成果物を生成 → 段 6 read-only review 1 本 (一次資料からの事実再抽出型の docs を含むため DW-C00 の
必須 1 本) + fix 子 → 変異 matrix → 受入全走 → 段 7〜9。

## 受入・実測環境

- 受入は `tools/dev_wave_wait.py acceptance --lease-optional` (所在 = worklog 末尾の作法、機体固有は `docs/pegasus-runbook.md`)。
- 作図の実走は login node (計測機の外、fig9 節と同じ)。matplotlib 3.10.9 / numpy 2.2.6 / Python 3.10.12 を実測。

## 模擬 / 実の差

- 本 wave に模擬はない。状態表 (P6) は 09-19 版 §8 の実文から親が読み、JSON に写した後の照合は段 6 review の read-only 子が
  一次資料 (09-19 版) と突き合わせる。09-20 草稿 (別 wave の未 land 木、データ扱い) は状態語の差分が出た時だけ README 節に注記する。
