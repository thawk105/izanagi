---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: dev-wave-t244-p6-contract
seq: 3
---

## 新規

### {{F:placeholder-gate-nonrecursive}}. placeholder gate の対象族が非再帰 glob で、insights の 81% が実効的に無検査だった [恒真ゲート] [誤前提]

- 事象: `tools/check_docs.py` の literal placeholder 検査 (D88、F36 の恒久対応) が
  `directory.glob("*.md")` で対象族を列挙しており、**subdirectory 配下の insights を 1 件も走査
  していなかった**。本 wave の段 7 で実測: top-level は 155 ファイルだが、
  **subdirectory 配下は 652 ファイル / 63 dir** あり、対象族の **81% が gate の外**にある。
  現時点で placeholder の hit は 0 件で実害は出ていない
- 根本原因: 対象族を「ディレクトリ + glob pattern」という**構成に依存する形**で定義し、
  その構成が変わったときに被覆が落ちることを検査していなかった。D88 (2026-07-25) の時点では
  insights は概ね top-level に平置きされており `*.md` で足りていたが、その後 wave ごとの
  subdirectory へ置く運用が広がり、**定義が実体に追随しないまま gate だけが緑を返し続けた**。
  被覆率そのものを検査する仕組みが無いため、劣化が無検出だった
- なぜ危険か: gate は緑を返し続けるが、その緑は「大半のファイルを見ていない緑」である。
  D88 (3) は `-verbatim.md` suffix による除外を「**誰でも作れる全ファイル除外スイッチ**であり
  規律 2 に反する受理集合拡大」として明示的に却下した。**subdirectory はこれと同じ性質の
  除外スイッチ**であり、しかも意図せず既定になっている。insights を wave ごとの
  subdirectory へ置く運用が D88 (2026-07-25) より後に広がったため、対象族の定義が
  実体の構成変化に追随しなかった
- 判別: `find output/insights -mindepth 2 -name "*.md" | wc -l` を
  `ls output/insights/*.md | wc -l` と比べる。前者が大きければ被覆が抜けている
- 恒久対応: **未実装である。** 所有は {{T:placeholder-gate-recursion}} に置いた
  (対象族を再帰列挙へ変える = 受理集合を狭める方向の変更であり D96 手続が要る)。
  本 wave が採った即時の緩和は、自分が追加した subdirectory 配下 6 ファイルを
  同じ 3 リテラルで手 grep し 0 件を確認したことだけであり、これは制度的対応ではない
- 再発検知: 上記 2 コマンドの差分を検査へ落とす。所有 ID で実装する
- 近縁: F36 (placeholder の埋め戻し失敗そのもの)、F34 (repo scan invariant)
- 記録: 本 wave の worklog エントリ、一次資料 = `output/insights/2026-08-03_t244-p6-contract/`

## 再発

### F24

- **再発 (near-miss): 2026-08-04** — 完了判定を中間状態から推測する同型を、`-o` 出力ファイルで
  実測した。段 2 の codex は `-o` の成果物を **00:01 に 31,141 bytes で書き、rc=0 で終了した
  00:08 に 36,694 bytes へ書き換えた**。途中版も末尾が整って見えるため、
  「出力ファイルが存在する / サイズが安定した / 末尾が整っている」で完了判定していれば
  切り詰めたプランを採用していた。**F24 の恒久対応 (`.done` の存在 + exit code だけで判定) が
  そのまま効き、実害はゼロ**であった。本追記は恒久対応の射程が log 本文 grep だけでなく
  **`-o` ファイルの存在・サイズ・末尾形にも及ぶ**ことを明示するためのものである
