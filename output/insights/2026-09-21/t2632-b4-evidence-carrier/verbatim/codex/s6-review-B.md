## 1. 過剰

- **refuted／修正不要**：`.corrupt.*` による停止は「本体が無い場合」だけで、修復済み report があれば退避ファイルが残っていても読める（[p3_s4_loop.py:1561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:1561)）；削除すると破損退避後の再試行で空 report を新設でき、過去 iteration と参照 attempt の対応を失う。
- **refuted／修正不要**：schema／axis 検査は既存 report の誤形式・取り違え検出、directory fsync は公開の永続化、hash 引数検査は評価前の不正値拒否に限定される（同ファイル `:1527`、`:1599`、`:2968`）；維持しても適格行・台帳・certified 判定は増えず、削除すると誤 report の受理、公開の耐障害性低下、評価後の書込み拒否をそれぞれ招く。
- **refuted／修正不要**：module docstring の追加は参照点定義への案内だけ（同ファイル `:36`）；削除しても記録内容は変わらないが、定義の発見性だけが下がる。

## 2. scope 外の混入

- **refuted／修正不要［権限逸脱］**：差分は指定された実装・テスト計 4 ファイルに限定され、admission、reference 欄、sort／trigger 展開、新台帳・回復 gate の追加はない（[a.patch:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/a.patch:1)、[b.patch:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/b.patch:1)）；既存の適格性・certified 判定を report に移譲していない。
- **refuted／修正不要**：caller は checkpoint と codec 経由の lock だけを読み、side channel は読まない（[p3_b4_prerun_caller.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_b4_prerun_caller.py:65)）；赤候補あたり不足 12 件という結果と、非空適格 batch を構成しない境界は維持される。

## 3. test の過剰と重複

- **refuted／修正不要**：裁定で不採用の pair 通しテスト・caller の重複 v2 テストは再導入されていない；stock は実 stock 関数、caller は既存テストの v2 化と v1 回帰で検査する（[test_p3_s4_loop.py:7448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py:7448)、[test_p3_b4_prerun_caller.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_prerun_caller.py:95)）；機構全体を stub した緑を carrier の証拠にする追加はない。
- **real／nit**：省略時 hash=null の単独テスト（`test_p3_s4_loop.py:7478`）は、同じ `drive_iteration` の既定値を entry 全体で比較する `:7350`、`:7474` と重複する；既存 assertion に統合しても成果物の性質は欠けず、放置時の影響は小さな実行コストだけ。
- **refuted／修正不要（時間超過の断定）**：binding は module 内で再利用され、焦点走は 167.68 秒（[focus-f1.log:528](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f1.log:528)）；ただし対象別 duration と受入全走の結果がなく、全体 5 分以内や追加分の寄与は未確認。

## 4. 削除・非接触

- **refuted／修正不要**：既存 assertion の削除・緩和はなく、loader stub 3 箇所は capture 契約への追従だけ（`test_p3_s4_loop.py:6566`、`:6624`、`:11044`）；凍結事前登録、whiteboard 型、sort／trigger driver、`campaign_lock.py`、共有 fixture への変更も両 patch になく、既存の判定条件は維持される。
- **real／must-fix［consumer 取り残し］**：既存 launcher positive の評価 stub は `build_attempt_id` と対応する start record を供給せず、新 carrier が拒否する（[focus-f1.log:376](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f1.log:376)、同 `:509`）；当該 fixture に同一 attempt の start／commit を記録する局所修正が必要で、放置すると launcher→base main→checkpoint の既存回帰検証が失われる。production の attempt 検査を緩める理由にはならない。

## 5. 説明の正確さ

- **refuted／修正不要**：P4 は checkpoint 未確定の保証に限定し、reject 再実行の上書き・B-4 再実行拒否も記載している（[p3_s4_loop.py:1613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:1613)）；対応の永続保持や回復可能性を過大に保証していない。
- **refuted／修正不要**：参照点は同一 campaign の先行 success、record 全体の canonical hash、PerfConfig／env_tag の照合と不足項目を定義している（同 `:1632`）；caller の説明も入力範囲に限定されており（`p3_b4_prerun_caller.py:3`、`:57`）、carrier を適格行・certified の証明とする説明は見当たらない。

## 6. 焦点走の結果

- **real／must-fix［手順漏れ］**：破損テスト 8 件は既存 `reports` に対する `mkdir()` で止まる（[test_p3_s4_loop.py:7385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py:7385)）；重複作成の削除または `exist_ok=True` で局所修正でき、放置すると評価前停止・認可未消費・再試行停止が未検証のまま残る。
- **real／must-fix［手順漏れ］**：attempt 選択と全 record 保持の 2 件は未定義 `STAGE_VERIFY_DONE` で停止する（同 `:7246`、`:7281`）；既存 module 定数の参照などで修正でき、放置すると参照 attempt の取り違えと WAL hash 列の欠落を検出できない。
- **real／must-fix［防壁の射程誤認］**：入力隔離テストは WAL 未作成の campaign を admission に渡し、出力比較前に停止する（同 `:7491`、[focus-f1.log:139](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f1.log:139)）；有効な admitted fixture を準備する局所修正が必要で、放置すると side channel が planner／coder／critic 入力を変えないという動的証拠が得られない。
- **refuted／修正不要（過剰実装が失敗原因という主張）**：ログは **12 failed・4689 passed・15 skipped、errors=0**；失敗は上記 11 件と項目 4 の 1 件で、過剰機能より fixture の不備・追従漏れで説明できる。skip の個別理由は提示ログに無く、今回の変更との因果は判定できない。

## 総括

**NO-GO。** 主因は 4 種のテスト準備・追従不備で、局所修正後の親による再走が必要です。新しい gate・台帳・admission 検査の追加は不要です。

本レビューは静的検査と提示ログの読解のみで、テストは実行していません。