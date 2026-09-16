単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate

## 必読事項の射影

次の絶対パスだけを読む。**この節が列挙した file を読めなければ即停止する** (停止規則の射程は
この射影 file に限る。ここに無い path の不在は停止理由にしない)。

- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/brief-t559.md — 親 brief。**これも検査対象である**
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/artifacts/t559-preclock-publish-gate/stage2-plan.md — 段 2 plan。**検査対象**
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-T559-entry250.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-T559-entry944.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D191.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D218.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D155.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-F108.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/cli.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/schema_v2.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/report.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/campaign/env_contract.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/campaign/execution_guard.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/tests/test_calibrator_certify.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/tools/pegasus/certify_calibration.sh

## 役割

**レンズ B = 整合と実効性。** 親 brief と段 2 plan を守らない。
「書いてあることと、実際に効く層が食い違っている」箇所を探す。

## 攻撃してほしい点

1. **効く層が全部 scope に入っているか。** [T-559] の逐語は「外側の post probe は publish より
   後に走り、publish を取り消さない」と書く。plan は CLI 内部にだけ gate を足し、外側
   `tools/pegasus/certify_calibration.sh` の `attestation-post.json` 経路 (`:961` 付近) を
   触らない。この状態で裁定「publish 前照合を課す」は**満たされるのか、名乗りだけになるのか**。
   外側 probe は gate 後も評価されないまま残る。これを「実装した」と書いてよいか。
   **書いてよくないなら、成果物にどう書けば正確かを 1 文で示せ。**
   scope を広げる提案ではなく、**名乗りの正確さ**の問題として答えよ。
2. **凍結 bytes と pin の波及。** plan は「合格時の published bytes を変えない」と主張する。
   `_assemble_v2` (`cli.py:752` 付近) と `schema_v2.py` の exact keys 検証を読み、
   この主張が成り立つ条件を列挙せよ。`orchestrator/campaign/env_contract.py` が束縛する
   登録済み較正 2 件、および事前登録文書の sha256 pin に波及しないと言い切れるか。
   **plan が提案する staging sidecar (`effective-clock-post-comparison.json`) は
   published bytes の外にあるか。** attempt staging を読む consumer はいるか。実在の file:line で答えよ。
3. **D191・D218・D155 との整合。** 新 gate は D191 決定 2 (「benchmark 後の既存 gate は削除しない」)、
   決定 3 (publish 直前の policy 同一性検査)、決定 5 (early 拒否成果物の自己完結) と衝突しないか。
   D218 が「完全形は実装しない」と定めた範囲に、plan の sidecar が食い込んでいないか。
   D155 決定 (4) が再裁定へ返した observer effect の是正を、plan が事実上先取りしていないか。
   **逐語を引いて判定せよ。逐語より強い断定をしない。**
4. **plan の file:line の正確さ。** plan が挙げた行番号 (`cli.py:1006`, `:1017`, `:1044`, `:1079`,
   `:81`, `test_calibrator_certify.py:40`, `:253`, `:1153`, `:1570`) を実ファイルで 1 つずつ照合し、
   ずれているものを列挙せよ。plan は親 brief の行番号を「ずれている」と訂正したが、
   **plan 自身の行番号も同じ検算にかけよ**。
5. **テストの帰属。** plan の負例テストは、実装を変えずに緑になってしまわないか
   (既に落ちる別の理由があるか)。plan が挙げた 6 つの変異対策のうち、
   **「その変異を入れても緑のまま残る」ものはどれか**。とくに
   「canonical 関数を実関数へ委譲する spy」は、機構の実体を名指しせず性質だけを見ていないか。
6. **既存テストへの波及。** plan は `cli.py:81` 付近の early 未評価一覧に 1 項目足すと言う。
   この定数を読む test・consumer を `grep` 相当で洗い出し、1 項目追加で壊れる既存期待値を
   file:line で列挙せよ。plan が挙げた `test_calibrator_certify.py:40` 以外にもあるか。
7. **親 brief の不変条件 2** (「通る attempt の published bytes を変えない」) は、
   本当に守るべき不変条件か、それとも過剰な自己制約か。守った場合に失われる監査可能性はあるか。

## 禁止

- file の作成・編集・削除、commit、git の状態変更。
- scope を広げる実装提案。必要と判断したら **裁定パッケージ候補**として
  「scope 外だが real」と明記して返す。
- 仮想リスク向けの防壁の新設提案。

## 実行環境

sandbox は read-only で書込可能 tmp が無い。**pytest を実走しなくてよい。静的検査でよい。**
走らせていないものを「緑」と書かない。予算が尽きそうなら途中までの結論を出力形式どおり書いて終わる。

## 出力形式

H2 見出しだけを使う。所見ごとに「real / 疑わしい」「scope 内 / scope 外」「根拠の file:line」を書く。
最後に必ず次の節を置く。

## 総括

- 最も重い所見を 3 件まで、各 2 行以内。
- plan をこのまま実装してよいか (yes / 条件付き / no) と、その条件。
