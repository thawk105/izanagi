---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t316-r2-oracle
seq: 3
---

## 新規

### {{F:immutable-projection-breaks-exact-type-checks}}. admitted view の不変射影が読み手の厳密型検査を黙って全滅させた [恒真ゲート] [consumer 取り残し]

- 事象: 新設 gate の構造化理由 (公理名・反例対・receipt) が critic へ**一切届いていなかった**。
  reject の件数と subtype は出るため、静的レビュー 3 本 (敵対 2 + 焦点 1) と実装子・fix 子 2 巡が
  いずれも見落とした。検出したのは統合テスト 1 本だけで、その赤も
  `assert {} == {...}` としか出ないため原因は自明でなかった。
- 根本原因: `artifact_admission._deep_immutable` が admitted campaign view を作るときに
  入れ子 `dict` を `MappingProxyType` へ、`list` を `tuple` へ射影する。一方 critic 側の新規 validator は
  `type(value) is not dict` / `type(pairs) is not list` の**厳密型一致**で書かれており、
  射影後の値をすべて「不正」と判定して `{}` に潰していた。**fail-closed に見えて実際は
  診断が消えるだけ**なので、規律 3 が禁じる「謳うだけで働かない片肺」になっていた。
- 恒久対応: 受理する具体型を**明示列挙**する (`dict` と `MappingProxyType`、`list` と `tuple`)。
  `isinstance(x, Mapping)` へ丸ごと緩めない (str や任意実装まで通るため)。キー集合・長さ上限・
  値域・hash 検証は一切緩めない。
- 再発検知: **WAL → admitted 不変射影 → loader → renderer を実際に通す**回帰テスト。
  素の `dict` を loader へ直接渡すテストでは、この欠陥は永久に捕まらない。

### {{F:adversary-blocked-when-asked-for-bypass-artifacts}}. 敵対 prompt が「回避できるコードを書け」と求めて上流分類器に遮断された [子の空振り]

- 事象: 段 3 の敵対レンズ 1 本が最終出力生成の直前で
  `This content was flagged for possible cybersecurity risk` を返し、`rc=1` / 成果物 0 bytes で終了した。
  model call は 6 回消費済み、wall 229 秒。レンズ 1 本分の検証が丸ごと失われた。
- 根本原因: prompt 冒頭に**防御目的は明記していた**が、本文で
  「見逃せる comparator を具体的な C++ 式で 1 つ以上書け」「候補が fd に書ける経路を検討せよ」と
  **攻撃成果物そのものの作成**を求めていた。防御目的の宣言だけでは分類器を通らない。
- 恒久対応: 攻撃成果物を要求せず、**テスト設計として**求める
  (「目撃できない違反族を分類し、テストの負例として登録すべき代表形を挙げよ」)。
  検証の深さは落とさずに、成果物の性格を「回避コード」から「被覆の穴と負例候補」へ移す。
- 再発検知: 再投入は**新しい artifact 名**で行い、`rc=1` は receipt の
  `attempt output` と `validator_rc` を読んでから原因を分類する。

### {{F:merge-submodule-gitlink-blocks-land}}. merge が submodule gitlink を古い側で確定させ、是正 commit が provenance で land を止めた [手順漏れ] [監査ログ汚染]

- 事象: local main 取り込みの merge 後、受入全走で s1/s8b/real-repo 系が 30 件級で赤になった
  (「ccbench worktree HEAD が `pin.CURRENT_PIN` を prefix に持たない」)。自分の差分が到達しない
  ファイル群なので原因が見えにくい。是正のため gitlink を main 側 pin へ進める単独 commit を作ったが、
  `check_ai_provenance` が `external/` を実装面 prefix として扱うため
  **「実装面に Codex `role=author` がない」で新規違反**になり、`DW-O25` の全史 provenance 関門
  (rc=29) で land が止まった。
- 根本原因: merge 競合解決の `git add -A` は、**submodule の未解決 gitlink を作業ツリー側
  (= 古い pin) で確定させる**。main だけが gitlink を進めていても、この一手で main の変更が消える。
  そのうえ後追いの単独是正 commit は「誰も書いていない実装面変更」になり、**真の trailer を
  書く手段が無い** (Codex 著者行は虚偽、`AI-Agent: none` も虚偽、waiver は人間の批准が要る)。
- 恒久対応: `DW-O17` に「commit 前に `git ls-tree main <sub>` と突き合わせ **merge commit の中で**
  main 側 pin へ揃える」を追加した。後追い commit にしない。
- 再発検知: 受入全走で pin 不一致型の赤が出たら、まず gitlink と `pin.CURRENT_PIN` を突き合わせる。
- 補足 (監査ログの質): 本件は **監査ログを汚す型の失敗**である。回避すると
  「waiver / known-violation で通した」記録が残り、監査を工数分析やプロセス改善に使うときの
  信号対雑音比を下げる。手順で発生させないことが対処であり、例外機構の常用ではない。

## 再発

### F102

- **再発: 2026-08-12** — 敵対子が最終出力生成の段で上流分類器に遮断された
  ({{F:adversary-blocked-when-asked-for-bypass-artifacts}} に詳細)。既存の恒久対応
  「防御目的を明記する」だけでは不足で、**攻撃成果物の作成を求めないこと**まで射程を広げる必要がある。
