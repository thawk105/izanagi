---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1901-env-coincidence-reaudit
seq: 3
---

## 新規

### {{F:overcorrected-h-bias}}. 偏りの是正が逆方向へ振れ、正しい分類を誤りへ書き換えた [テスト代表性]

- 事象: 前 wave の敵対レビューが「H の誤分類」として 4 件を記録したが、うち 2 件
  (`test_check_ai_provenance.py:6359`、`test_run_tests_preflight.py:2049`) は訂正自体が誤りだった。
  正しい class は T ではなく H である。`assert ev.wait(1)` の `1` は mock の `side_effect` 内の
  test-local `Event` に渡るだけで production の締切・猶予・poll へ到達せず、T の定義を満たさない。
  記録が台帳へ入り、後続 wave が「確認済みの正解」として control に使うところだった。
- 根本原因: 「H へ寄る系統的な偏り」を是正しようとして、**非 H 側の主張を同じ強さで疑わなかった。**
  「wait の戻り値が assert されている」という構文的特徴だけで非 H と断定し、その数値が
  production へ到達するかを確かめていない。偏りの是正は、疑う向きを反転させるだけでは達成できない。
- 恒久対応: {{D:f-materiality}} が T に「production への値伝播」を、H に「性質を担う別 assertion の
  file:line 名指し」を必須化する。どちらのクラスも積極的な立証を要求するので、
  片方向へ倒すだけでは通らない。
- 再発検知: {{D:classification-blind-decoy}} の盲検 decoy 再分類。疑わしいクラスの行だけを
  reviewer へ渡すと誤りが相関するため、同数の別クラス行を混ぜて class を隠す。
  実測では H 主張の 93% が独立に再現し、非 H 側は 64% だった。一致率の差が偏りの所在を示す。

### {{F:parent-dirtied-tree-during-mutation}}. 親が変異走行中に成果物を worktree へ書き、harness を 2 度止めた [手順漏れ]

- 事象: 変異 matrix の本走を投入した直後、親が待機時間を使って分類 JSON を worktree へ書いた。
  harness は runner 実行前の untracked 検出で中止した (rc=2、変異 0 件)。成果物を commit して
  再投入したが、前回の `--attempt-out` を消していなかったため 2 度目も中止した。
  3 回目で 6/6 KILLED を得た。
- 根本原因: `DW-M05` は「変異中は親の編集と worktree へ書きうる子の起動を止める」と定めるが、
  **これは tool が検証不能な親の自己申告義務**である。親は「待機中は独立な作業を進めよ」という
  一般則に従って手を動かし、その作業が worktree への書き込みだと気づかなかった。
  再投入時の残存 artifact も、`.done` と `.pid` だけを消して `--attempt-out` を見落とした。
- 恒久対応: `DW-M05` の自己申告義務は変わらない。運用上は**変異投入の直前に、待機中に行う作業を
  「repo 外への書き込みだけ」と宣言してから投入する**。再投入では `.done` / `.pid` /
  `--out` / `--attempt-out` の 4 つをまとめて退避する。
- 再発検知: harness 自身の fail-closed 検査 (untracked 検出と fresh `--attempt-out` 検査) が
  両方とも正しく発火した。**この失敗は防壁が働いた記録であり、防壁の破れではない。**
  記録する理由は、親が同じ待機時間の使い方を繰り返さないためである。

### {{F:probe-node-extractor-faked-a-survivor}}. 親の node 抽出の取りこぼしを SURVIVED と読み違えた [恒真ゲート]

- 事象: 変異の期待赤 node を確定するための予備測定で、`MUT-T1901-BOOL-AS-NUMBER` が
  `SURVIVED reds=0` と出た。しかし同じ走行の要約行は `failed=1` を報告しており矛盾していた。
  生出力を見ると `FAILED ...::test_bool_literals_are_not_numeric_bounds` は実在した。
  親の抽出器が拾えていなかっただけで、等価変異ではない。抽出を失敗 digest の `nodeid` 欄も
  見る形へ直したら KILLED になり、本走でも KILLED / 期待 node 完全一致だった。
- 根本原因: 抽出器が `FAILED ` 行の 1 経路しか見ていなかった。runner の出力形式は行前置や
  digest 形式を持ち、単一経路の抽出は取りこぼす。
- 恒久対応: 抽出は複数経路 (`FAILED ` 行と失敗 digest の `nodeid=` 欄) を突き合わせる。
  **rc が非 0 なのに抽出 0 件なら fail-closed で止める** (`DW-M08` が F71 として既に定める規律)。
  今回は rc と件数の矛盾が出力に残っていたので気づけた。
- 再発検知: 予備測定の各行で「rc != 0 かつ抽出 0 件」を検出したら停止する。
  `DW-M02` の「SURVIVED は mutated 内容の diff で注入実在を確認するまで equivalent としない」も
  同じ罠を塞ぐ。今回は注入実在の確認へ進む前に矛盾に気づいた。
