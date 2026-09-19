# 段 4 裁定 — [T-2035] (2026-09-19 22:02 JST、親)

consult (codex luna、medium、read-only、rc=0、`check_codex_output.py` OK) の所見 8 件を裁定し、plan v2 を確定する。
段 4 直前の裁定 inbox 再走査: main は着手時 `a99425b66` → `657e1e5a7` (T-2489 の land + fold) へ前進。編集面
(`docs/related-work/claim-survey/`、`docs/paper-story-backoff/`) との交差なし、未 fold fragment 0、decisions に軸 1 の新規言及なし。
worktree を `--ff-only` で `657e1e5a7` に揃えた。[T-2035] の base digest は不変 (`a20b1575…`)。

| 所見 | 判定 | 採否 | 処置 |
|---|---|---|---|
| A-1 軸の帰属から材料の用途は退けられない | **real / must-fix** | 採用 | (P1) を撤回。軸 1 が主論文の軸であることは事実だが、`paper-story-backoff/README.md` は一次資料の共有を認め、`2026-09-10.md` §8 が禁じるのは「B5 の完了に数えること」だけで参考材料としての参照は禁じていない。ユーザー引数の用途指定 (2 本目論文の関連研究の材料) と scope 外 (主論文の関連研究) をそのまま守る。**`docs/paper-story/README.md` には触れない。** 凍結記録は claim-survey (共有物) に置き、backoff README から「関連研究の参考材料」として指す。B5 の成熟度 (`RW0`) と保留 (D1936 項 16) は変えない |
| A-2 1676 の反映手番は 18b で消費済み | real / should | 採用 | 新記録は「裁定の初反映」ではなく「18b の追補 (取得済み leaf 一覧 + 2 本目論文への導線)」と書く。1660 の fold 衝突回避の経緯は entry 1660 本文 (「台帳の扱い」) と commit `03829a867` の message から引ける — 記録には要点だけ |
| A-3 materials-index より execution 型が明快 | real / should | 採用 | file 名を `2026-09-19-axis1-search-execution.md` にし、冒頭で「request 0 件・取得なし・検査器再走なし・新裁定なし。18b の追補」と宣言する |
| A-4 分類 78 行は一致、E/F は最終診断で区別不能 | real / should | 採用 | `Q3` / `Q6` の母集合は `SPRE1991` + `SY1991`〜`SY2026` (各 37) と書く。`complete` 8 のうち `Q2` は期待 pass `[1]` (1 走で完走する枝) なので「独立 2 走完了」と一括しない。E/F の 7 leaf は検査器の最終コードが同値 (`leaf_page_evidence_missing` + `resume_action=None`) で、区別は窓 4 記録 (drift) と窓 3・5・6 記録 (条件 5) の逐語から採ると明記 |
| B-1 主論文 README の追記は削り、backoff README の短い導線に | real / should | 採用 (A-1 に含む) | backoff README「`docs/paper-story/` との関係」節に 1 段落 (所在・2 裁定・77 = 61 + 16・`RW1`・B5 に数えない) を足す。stale 注記節には足さない (B5 の記述は古くなっていない) |
| B-2 入力 commit の不足、転記値の身元 | **real / must-fix** | 採用 | §0 に導出元 commit (`657e1e5a7`、本 wave の base) と入力 path (window6 `bundle-check.json` / `leaf-states.txt`、18 / 18b、窓 3・4・5・6 の逐語) を列挙し、bundle manifest SHA は「18b 記載値の転記、本記録では現物未照合 (bundle 非接触)」、`Q6-SY2026` の 21,040 件・106 頁・1060 credit は「件数 probe が返した申告総数からの換算であって取得実績ではない」と書く |
| B-3 「被覆」は網羅性と誤読される | real / should | 採用 | 見出しを「登録 leaf の枝別内訳」にし、「候補判定・文献の網羅性を表す数ではない」を同じ場所に置く。「未検出」「調査済み」の語を使わない |
| B-4 gate・検査・台帳の新設なし | refuted / nit | — | 変更なし (実装面差分ゼロを維持) |

## plan v2 (変更 file 4 本、すべて docs)

1. 新規 `docs/related-work/claim-survey/2026-09-19-axis1-search-execution.md` — 18b の追補。§0 身元 (導出元 commit・入力 path・転記値の出所)、
   §1 起動 0、§2 78 leaf の全列挙表 (区分 A〜G、検査器の状態列)、§3 登録 leaf の枝別内訳 (網羅性でない旨を併記)、§4 限定 (18 §3 / 18b §3 の逐語引き継ぎ)、
   §5 未走 query `Q6-SY2026` の明記 (D2150 項 4、換算値の身元)、§6 2 本目論文での使い方 (参考材料、B5 に数えない、`RW1` の表現規律)、
   §7 次に残るもの (18b §5 を指す)、§8 凍結物への注記の限界、§9 母集合の外。
2. `docs/related-work/claim-survey/README.md` — 一覧に 1 行。
3. `docs/paper-story-backoff/README.md` — 「`docs/paper-story/` との関係」節に「参考材料として共有するもの (軸 1)」1 段落。
4. `docs/spool/worklog/2026-09-19-dev-wave-t2035-axis1-materials-record-1.md` — [T-2035] 完了 (base `a20b1575…`)。
   + insight `output/insights/2026-09-19/t2035-axis1-materials-record/` (README + verbatim: brief / plan / consult / adjudication / review)。

## scope 外 real 所見の扱い (DW-S04)

主論文の入口 `docs/paper-story/README.md` と最新版 `2026-09-17.md` §8 C-4 の「3 窓ぶん・9/8 打ち切り・この版でも動いていない」は
窓 5・6 / D2120 項 14 / D2150 項 4 を含まず古い。これは本 wave の scope 外 (ユーザー引数「主論文の関連研究」) なので実装せず、
新しい T も起票せず、insight README に所在を記録する。研究前進の欠陥ではなく入口の stale なので裁定パッケージにもしない。

## 変異 matrix

実装面 (D95 決定 2) の差分ゼロ → 免除。受入は免除しない (段 6 後に `tools/run_tests.py` の docs 焦点走 + `check_docs.py`、
段 7 記録前に実 repo を読むテストを実走)。

## 不変条件 (段 1 から不変)

軸 1 は `未完走`・`RW1`、世界の不在を 1 文も作らない、材料に数える leaf は 61 で不変、既存凍結物は 1 byte も変えない、request 0、
bundle 非接触、実装面差分ゼロ。
