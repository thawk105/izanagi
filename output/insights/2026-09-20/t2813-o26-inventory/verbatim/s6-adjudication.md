# 段 6 裁定 — レビュー所見の real / refuted (2026-09-20 21:38 JST)

レビュー: `codex/s6-review.md` (read-only、gpt-6-astra、3 レンズを 1 本、GO、must-fix 0 / nit 1)。`check_codex_output.py` rc=0。

| # | 所見 | 判定 | 採否 | 処置 |
|---|---|---|---|---|
| 1 | (C) 4 群の追加は T-2292 全体の解消ではない — 起点 entry 1238 が挙げた「process 起動一覧」(`test_ccbench_spawn_sites.py`) と「subprocess guard」(`test_check_subprocess_bytecode_guard.py`) は 4 群に含まれない | **real** (両 file の実在と 4 群非包含を `git ls-files` と本文で確認) | scope 外 (裁定 D2186 項 5 は「この 1 句だけ、他の gate・検査を足さない」) | 実装しない。記録: T-2292 の「契約側更新をセットで行う」義務は本 wave で閉じる。残る型 (process 起動一覧 / subprocess guard) は insight §7 に裁定パッケージ候補として置き、worklog に「言わないこと」で明記。新規 T は起票しない (D2186 項 5 の 4 群を広げるのは再裁定) |
| 反証 | 段 4 §2 の削減表の「すべて根拠説明」は粗い — 「受入前」「production を grep」「も含める」は義務文の短縮 | **real** (分類の粗さ。義務は保持されている点は一致) | 採用 | 段 4 §2 の表は書き換えず、本裁定で訂正: 削減は (i) 根拠説明の削除 4 件 (「名前の推測でなく」「初回実測でも…この拡張を欠く焦点走は」「全走緑は file 単独緑を含意しない」「並行投入は orphan hold で rc=16 になる」) と (ii) 義務文の短縮 5 件 (「変更した」→「変更」×3、「受入全走前」→「受入前」、「production 全体を」→「production を」、「焦点走に含める」→「含める」、「焦点走対象」→「焦点走」) の 2 種。(ii) は義務の条件・対象を変えない |

- 確認済み (レビューが独立に検算): 3 者 998 bytes 一致・NFC・末尾 LF 1・attack 文字列 1 行内 1 回、M8 削除後 939 bytes で exact 不一致だけが立つ、DW-C00 の rc=16 参照は成立、
  旧断片への実行可能な依存なし、上限 1000 / exact 登録集合 / 他 pin 節 / L1・L1.5 不変、候補 1 件目の混入なし。
- fix 子: 不要 (must-fix 0)。焦点再レビュー: 不要 (fix なし)。
- 変異 matrix: probe 起動 21:35 JST (`mutation-probe.*`、独立 clone `mutation-source` = c805a53a7、dispatch)。final は probe の観測 node で `make_mutation_spec.py final`。
  docs 変異 M4' は実 repo 正例 3 test が growth hold (docs_bytes 軸) で skip されるため pytest では殺せない → 親が DW-O19 で `python3 tools/check_docs.py` 直叩きの手動 probe とし、
  harness 外の変異として記録する (受入前、統合 commit 後、`--porcelain` 空確認 → 1 文字変異 → 赤確認 → `git checkout --` 復元 → bytes を HEAD と照合)。
- 焦点走 focus-1 起動 21:37 JST (request 13595.nqsv、19 file = 変更 test 1 + consumer 14 + inventory 4 群 (新 DW-O26 の dogfood)、`focus/focus-1.log`)。
