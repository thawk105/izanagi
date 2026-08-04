---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t407-ruleops-binary-blob
seq: 1
title: [T-407] ruleops inventory の非 UTF-8 停止を読み飛ばし + 件数へ replaced (コード + docs、branch worktree-wave-t407-ruleops-binary-blob)
---

## 本文

- 裁定は {{D:ruleops-inventory-skip-non-utf8}}。実装 commit と docs commit は本エントリの
  branch 上にある
- **段 1 の brief が wave 途中で覆った。** 起動時の main には T-407 の裁定が無く、親は
  「binary として一覧に載せる」案を提示してユーザー承認も得た。段 3 完了後に main を取り込んだ
  ところ、並行セッションが land した既存裁定「(a) 読み飛ばす」を発見し、停止してユーザー再裁定を
  仰いだ。結果「読み飛ばす + 件数を根に出す」で確定し、**旧案前提の段 2 プランと段 3 レビュー
  2 本を破棄して両段を再実行した**。対象非依存の実測事実だけを brief へ継承した
- **敵対検証 4 本 (段 3 の 2 レンズ、段 6 のレビュー 2 本) がいずれも NO-GO を出した。**
  production 実装への署名違反指摘は 0 件で、**4 本すべてがテストの検出力不足**を突いた。
  段 6 の 2 本が独立に見つけた未登録の誤実装は、(i) 非 UTF-8 target を持つ symlink を
  件数へ混入させる、(ii) size 上限超過の valid UTF-8 を黙って落とす、(iii) `.raw` 以外の NUL を
  落とす、(iv) marker を常に空にする、の 4 種。いずれも当初のテストを緑のまま通過した。
  fix でこの 4 契約を固定し、所見は全件 closed
- **段 3 で親の実測 2 件が訂正された。** (i) 走査母集団 1,659 件は insight 族だけで、
  direct test 124 件を足した全 scope は 1,783 件 / 44,994,296 bytes だった (結論の
  「非 UTF-8 は 4 件」は全 scope 走査でも維持)。(ii) 起票予定 ID として親が置いた T-409 / T-410 は
  既に使用済みで、レンズが衝突を検出した。採番は land の lock へ委ねた
- **ユーザー裁定により変異 matrix を後続タスクへ繰り延べた。** 本赤が他タスクを止めているため
  緊急に閉じる方針で、段 4 で事前登録した 12 件 (M01〜M12) の実走と段 6 の焦点再レビューは
  行っていない。spec は `output/insights/2026-08-04_t407-ruleops-inventory/mutation-spec.json` に
  凍結した。段 6 のレビュー 2 本は「M01〜M12 は静的には全件 KILLED」と判定しているが、
  **これは実走結果ではない**
- **この実装が保証しないこと。** (i) `skipped_non_utf8` はどの対象が落ちたかを示さない。
  `--kind test` が正のとき `items` を「直下 test を全数確認した」根拠にできない。
  (ii) 非 UTF-8 でも pytest が収集・実行しうる test file は存在する (PEP 263 の coding cookie)。
  一覧から消えても実行はされる。(iii) 受入全走の緑は並行干渉に対する頑健性を示さない (下記の
  D63 違反が未修正のため)
- 工数: codex 子 8 本 (plan 2 / 敵対レンズ 4 / 実装 1 / fix 1)。段 2・3 は再裁定により各 1 回やり直した
- **段 8 の自己改善候補 2 件も `docs/dev-wave/**` の合計 byte 予算が塞いだ** (25,200 に対し
  現在 25,196、残り 4 bytes)。(150) と同型の**3 例目**である。候補は (i) 段 1 brief の前に
  local main を取り込む義務を `DW-S01` へ足す (本 wave で並行セッションの裁定を段 3 完了後に
  発見し、codex 子 3 本分の成果を破棄して段 2・3 をやり直した。`DW-O23` は land 直前の話で
  段 1 を縛らず、`DW-S01` の「承認済み裁定の前提を実測する」も裁定が現在の main に在るかの
  確認までは含意しない)、(ii) `DW-O20` の startup gate が worktree 新規作成時に submodule 未初期化で
  必ず赤になるのに、NG message は「親セッションで submodule を初期化する」と出る
  (背景 job の worktree では自分で初期化するのが正しい。message は `tools/check_wave_startup.py` 側)。
  予算の解決経路は [T-328] の裁定 (c) で **[T-313] 先行**と決まっているため、本 wave では
  実装せず候補として記録する

## 次の一手差分

### 完了

- [T-407] `ruleops.py inventory` は decode 不能な blob を読み飛ばし、件数を根の
  `skipped_non_utf8` へ出すようにした。schema は v2。運用正本 `docs/ruleops.md` も更新した。
  remaining: none
  base: 5f4718f6ae27e082338e04699dce17c7db2f8a0ce0fed50cf14ea21c4f3eaeaf

### 新規

- {{T:ruleops-inventory-mutation-matrix}} **P2・新規**: [T-407] で事前登録した変異 12 件
  (M01〜M12) を実走する。ユーザー裁定により緊急パッチを優先して繰り延べたもの。
  spec は `output/insights/2026-08-04_t407-ruleops-inventory/mutation-spec.json` に凍結済みで、
  runner は `python3 tools/run_tests.py orchestrator/tests/test_ruleops.py -q -rf -n 0`。
  段 6 の焦点再レビューも未実施
- {{T:ruleops-realrepo-xdist-group}} **P2・新規**: `test_ruleops.py` の real-checkout test が
  D63 の競合閉包契約に反している。decorator で `xdist_group(name="real_repo")` を直接付けており、
  canonical 名 `real-repo` と別 group になるため、実 submodule を patch する writer との排他が
  効いていない。収集監査 meta-test も非 canonical node の positional arg しか見ず kwargs 形を
  見逃す。同 test は D63 決定 (4) の `--untracked-files=all` 共有 helper も使っていない
- {{T:ruleops-git-stderr-strict}} **P2・新規**: `ruleops.py` は許可 rc の Git stderr を
  strict decode せず捨てる。非ゼロ rc の分岐でしか検査しないため、rc=0 や `grep` の rc=1 では
  任意 bytes が素通りする
- {{T:ruleops-test-candidate-decode}} **P3・新規**: `validate_candidate_ledger` が direct test
  candidate の target 本文を decode しない。insight candidate は decode するため非対称で、
  `inspect` が拒否する target を `check` が構造上受理しうる
