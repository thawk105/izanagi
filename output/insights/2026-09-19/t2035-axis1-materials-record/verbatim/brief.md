# 段 1 brief — [T-2035] 軸 1 OpenAlex 窓 5・6 の取得結果を論文の関連研究の材料として記録し T-2035 を閉じる (docs のみ)

作成 2026-09-19 21:53 JST。base = local main `a99425b66` (fresh worktree `dev-wave-t2035-axis1-materials-record`)。

## 研究前進 (1 行)

主論文 (`docs/paper-story/`) の C-4「体系的な先行研究調査」について、軸 1 の材料の現在地 (77 leaf 分・限定付き・`RW1`・
`Q6-SY2026` 未走) を leaf ID 単位で凍結し、論文の入口 (`docs/paper-story/README.md` の stale 注記) から引けるようにする。
完了判定 = 記録 1 本が land し、[T-2035] が worklog で完了になる。取得の再実行・request 追加は 0 件。

## 引数の前提のうち、実測で覆ったもの (段 4 で再裁定)

- **(P1) 置き場。** 引数は「2 本目論文 `docs/paper-story-backoff/` の関連研究の材料へ記録」と言うが、軸 1 (`AX1-20260902-E1`) は
  **主論文の主張軸**である (`docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md` §1「軸 1 = `docs/paper-story/2026-08-26.md`
  の §3 の 1『対象の空白』」、`docs/related-work/README.md` §7.7 冒頭「`docs/paper-story/` §8 の C-4 のための規則」)。
  2 本目論文の関連研究軸は **B5** (別登録 `2026-09-05-backoff-axis-registration.md`、`RW0`) で、最新版 `docs/paper-story-backoff/2026-09-10.md`
  §8 は「後続の一般的な CC 合成文献調査を本軸の完了に数えず」と明記し、主論文最新版 `docs/paper-story/2026-09-17.md` §8 C-4 も
  「2 本目の論文の軸 B5 は D1936 項16 で保留 … 本体論文の軸 1〜5 の状態は動かさない」と両者を分けている。
  さらに `docs/paper-story-backoff/README.md` は「一項目だけを直した差分改訂を新しい日付の版として置くな」「一項目の決着は README の
  stale 注記で指す」と定めるが、その stale 注記は「最新版の記述が古くなった箇所」用で、B5 の行は軸 1 で古くなっていない。
  → 親の provisional 裁定: **置き場は主論文側**。(i) 凍結記録 `docs/related-work/claim-survey/2026-09-19-axis1-materials-index.md`
  (request 0 件、D1208 の後継物の型) + 同 `README.md` の一覧行、(ii) `docs/paper-story/README.md` の stale 注記 4 件目 (最新版 2026-09-17 の
  C-4「3 窓ぶん取得・9/8 打ち切り・この版でも動いていない」が窓 5・6 / D2120 項 14 / D2150 項 4 を含まず古い)。
  引数の「scope 外 = 主論文の関連研究」は「軸 1 = 2 本目論文」という誤前提の上の文なので、(ii) は関連研究の本文執筆ではなく所在の
  pointer に限る形で scope に入れる。`docs/paper-story-backoff/` には触れない。
- **(P2) T-2035 の残件。** worklog の carry 本文 (archive entry 1676、rulings wave の fold) は「D1208 に従い後継の実行記録へ今回の確定を
  反映する」と言うが、それは entry 1660 (`2026-09-18b-axis1-search-execution.md`、commit `d56c5a7d3`、main 包含) で消費済み。1660 は
  未 land の裁定 wave fragment との fold 衝突を避けて [T-2035] に触れず暗黙 carry したため、1676 の文が stale になった。
  → 本 wave の記録 1 本で引数の成果条件 (leaf 一覧・限定・未走 query) を満たし、**[T-2035] を完了で閉じる**。
- **(P3) 何が新規か。** 18 / 18b 記録は限定・未走 query・区分の件数 (61 / 16 / 1) と、`complete` 8・落ちた 16・未走 1 の leaf 名は持つが、
  **停止 53 leaf の ID 一覧は凍結 docs に無い** (一次資料 `output/insights/2026-09-17/t2035-axis1-openalex-window6/leaf-states.txt` と
  `bundle-check.json` の `status.leaf_diagnostics` にだけある。18b が offline 再走で byte 一致を確認済み)。新規 = 78 leaf の ID × 区分 × 検査器の
  `reason_code` / `resume_action` / checkpoint 有無の全列挙表と、枝ごとの被覆 (どの年 shard が材料にあるか)。

## scope

- **入れる:** (a) 凍結記録 1 本 (上記 (i))、(b) claim-survey README の一覧行 1 行、(c) paper-story README の stale 注記 1 件 + 件数行の更新、
  (d) worklog fragment ([T-2035] 完了)。数値・leaf ID はすべて repo 内の凍結逐語 (window5 / window6 insight、18 / 18b 記録) から採る。
- **入れない:** 取得の再実行・request・件数 probe (0 件)、repo 外 bundle への接触、取得器・検査器・catalog・完走述語の変更、per-leaf の
  取得日・頁数の 6 窓横断再構成 (一次資料が 6 窓の insight に散り checkpoint run ID は repo 外。18 記録 §3 が引き方を持つのでそれを指す)、
  候補判定 (`検出` / `近傍` / `除外` / `要裁定`) の 1 件でも行うこと、不在の文を作ること (`RW1`)、`docs/paper-story-backoff/` の編集、
  主論文の関連研究本文の執筆、新しい日付の paper-story 版、gate・検査・台帳の新設、実装面の差分。

## 不変条件

- 軸 1 は `未完走`・`RW1` のまま。世界の不在を 1 文も作らない。材料に数える leaf を 61 から増やさない・減らさない。
- 既存凍結物 (窓 1〜6 記録、18 / 18b、catalog、bundle mirror) は 1 byte も変えない (D1208)。
- 規律 2 / 3 / 6 / 7 に触れる面は無い (docs のみ)。

## 成果物影響 (DW-G05)

放置時: 論文執筆者が主論文の入口から C-4 の現在地を引くと「3 窓・9/8 打ち切り」で止まり、窓 5・6 の取得と 77 leaf 限定・
`Q6-SY2026` 未走の確定を見落とす → 関連研究の限定文の根拠 (どの枝・年が材料にあるか) を誤る。certified 選択・材料レポート・台帳の値・
受理集合は変わらない (docs のみ)。

## 分割・子

軽量版。実装面ゼロ → 段 5 は親が docs を起草、変異 matrix は免除 (実装面差分ゼロ)。段 3 = codex consult 1 本 (レンズ 2 つを prompt 内で分ける:
A 前提・置き場の択一 / B 過剰・削除と再抽出の正確さ)。段 6 = codex read-only レビュー 1 本 (一次資料からの再抽出の照合)。
受入環境 = login node の `tools/run_tests.py` 焦点走 (docs 検査) + `python3 tools/check_docs.py`。
