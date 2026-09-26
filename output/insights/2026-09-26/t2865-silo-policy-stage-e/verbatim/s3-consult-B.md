## 所見

1. **must-fix — 共有検疫の新引数が段階 C/D の呼び出しを壊す。** plan は policy marker で compiler と scratch を必須にする一方、`silo_policy_coverage.prepare_policy` は引数なしで `quarantine` を呼び、変更対象からも外している（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-policy-stage-e/codex/s2-plan.md:5)、[silo_policy_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/silo_policy_coverage.py:287)）。**影響:** C/D の既存診断が正常な方策も停止し、受理集合が縮む。**代案:** `prepare_policy` の呼び出しを同じ所有単位で更新し、既存の正例・負例と receipt を固定する。二重 compile を残すなら、その費用も見積りに入れる。

2. **must-fix — proposal JSON の閉包が値と重複 key まで届いていない。** plan の完全 schema は `axis`、`implementation`、`confidence`、`prior_critic_reverse` の型・値域を述べるが、`projection_guard` の現行関数は key 集合だけを検査する。兄弟 loader の `json.loads` は重複 key を拒否しない（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-policy-stage-e/codex/s2-plan.md:28)、[projection_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/projection_guard.py:291)、[p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_sort.py:459)）。例えば `{"axis":"wrong","axis":"silo-function-policy"}` は通常の JSON 読込後には違反を観測できない。**影響:** 不正 proposal が受理され、候補と auditor の帰属が曖昧になる。**代案:** 生 bytes の重複 key 拒否を入口に置き、両形の全 scalar を exact 型・値域で検査する。欠落、未知 key、型違反、壊れた JSON を別々に試す。

3. **must-fix — `prior_critic_reverse` は自己申告を排除する配線が未定義。** plan は proposal の任意 key としながら「親が与える」と記すだけで、既存の兄弟 loader はその key を JSON から取り、停止カウンタへ直接渡す（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-policy-stage-e/codex/s2-plan.md:28)、[p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_sort.py:516)、[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop.py:2910)）。連続する `false` は reverse 枯渇を常にリセットできる。**影響:** iteration の停止値と系列台帳が coder 側の値で変わる。**代案:** proposal からこの key を除き、親が検証済み critic receipt から別引数として渡す。receipt がなければ reverse 判定に算入しない。

4. **must-fix — firewall の path と履歴の出所を受理条件に固定していない。** `make_policy_coder_input` は任意の `projection_path` と `history_path` を受ける設計で、固定 path・campaign ID・WAL 対応をどこで拒否するかが未定義（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-policy-stage-e/codex/s2-plan.md:26)、[同](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-policy-stage-e/codex/s2-plan.md:71)）。また実 projection の `scope` は自由文であり、`binary` だけの型検査では自由文経由の混入を証明できない（[projection.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/output/env/pegasus/calibration/silo_function_policy_recon/projection.json)）。**影響:** 禁止資料や他系列の内容が coder 入力に入り、レポートの探索条件が変わる。**代案:** production 入口で許可 path を固定し、projection の exact key・`binary` の exact bool・`scope` の str を検査する。履歴は campaign と WAL の識別子で照合し、justification を射影前に排除する。自由文の内容保証は主張しない。

5. **should — 変異 M-E1〜E4 の帰属は現行案のままでは成立しない。** C/D 経路には `quarantine` の後に独立した `check_policy_body` があるため、前者の grammar/TU を無効化しても後者が同じ本文を拒否する（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-policy-stage-e/codex/s2-plan.md:77)、[silo_policy_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/silo_policy_coverage.py:287)）。M-E4 は診断 subtype だけの変更で、DW-M03 の kill ではない。**影響:** gate が効かなくても「変異を殺した」という台帳値になり得る。**代案:** E driver の単独経路で受理集合が変わる fixture を使い、M-E4 は diagnostic sensitivity pin に分離する。実装後に各変異の mask と期待失敗 node の完全集合を再登録する（[mutation.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/docs/dev-wave/mutation.md:8)）。

6. **should — live job の実行経路は未確定。** plan 自身が既存 job body は旧 driver 固定で、worktree をそのまま渡せないと認める（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-policy-stage-e/codex/s2-plan.md:94)）。既存の許可経路は compute host、hydrate 済み root、receipt、reservation、固定 argv を要求する（[tools/pegasus/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/tools/pegasus/README.md:335)）。**影響:** P8 の live 確認は投入不能、または異なる条件の job になり、Elapse を見積り単価へ使えない。**代案:** 新 driver 用 job body と契約 test、admission registry の扱いを live 前に確定する。見積りには単独 TU、trace/perf の最大 2 build、legacy 1 rep、性能 verify 5 rep、bench 5 rep、依存物準備を含める。rep 数の記述自体は実コードと一致する（[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/pipeline.py:195)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/pipeline.py:2039)）。

7. **should — IR codec の一意な往復と例外試験を明文化する必要がある。** plan は閉じた node を列挙するが、`next_state` の `null` と省略、空配列、数値の bool 混同、未知 `kind`、文字列入口の重複 key をそれぞれどう正準化・拒否するかを test に割り当てていない（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-policy-stage-e/codex/s2-plan.md:20)、[silo_policy_ir.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/silo_policy_ir.py:172)）。**影響:** 同じ IR の JSON 表現が割れ、履歴や提案の参照が不安定になる。**代案:** 各 node と hook に exact key 集合を定め、`serialize(parse(x))` の正準形と `parse(serialize(ir)) == ir` を全 node 種で固定する。identity を描画後 C++ の `source_digest` とする方針は維持できる。

## brief と plan の前提の判定

| 前提 | 判定 | 理由 |
|---|---|---|
| P1 | **要修正** | 追加位置は妥当だが、compiler/scratch 必須化と既存 `prepare_policy` 呼び出しが衝突する。 |
| P2 | **要修正** | 空 whiteboard なら収束しない点は real。reverse 入力の信頼境界と履歴の出所照合が未完成。 |
| P3 | **要修正** | IR 型・renderer は実在する。一意な codec と全負例の契約は追加が必要。 |
| P4 | **要修正** | planner と value を外す判断は real。proposal の重複 key・scalar 型・reverse 出所を閉じる必要がある。 |
| P5 | **要修正** | projection の実 key は合う。任意 path と履歴の出所、自由文 `scope` の保証範囲を修正する。 |
| P6 | **real** | legacy＋性能 verify、1M/48/skew 0.9/3 秒/5 rep の設定は実コードと合う。 |
| P7 | **要修正** | 14→16、sha pin、forbidden 語、adapter の追随は必要。既存 test の「22 拒否」は「27 拒否」へ変わる理由と正例を併記し、緑化だけの変更を禁じる。 |
| P8 | **要修正** | 手書き 2 形は配線確認になる。auditor 実 spawn と計算投入には承認済み role と許可 job 経路が要る。 |

## 再発しうる失敗の型

[恒真ゲート]、[テスト代表性]、[変異帰属] は、後段の再拒否を単独変異の kill と読む F28・F126・F948 型に当たる（[failures.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/docs/failures.md:1154)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/docs/failures.md:6137)）。[consumer 取り残し] と [pin 閉包漏れ] は `prepare_policy` と spawn site の行番号 pin に当たる F954 型（[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/docs/failures.md:26403)）。[ドリフト] と [誤前提] は proposal・role・job 契約の説明と実効配線の差に当たる。既存 test の期待値だけを反転して緑にする F27 型にも注意が要る。

## scope 外の層 (裁定パッケージ候補)

自由文 `scope` や候補本文からの意味的な情報リークの完全判定、候補ごとの公平性計測・sanitizer・TRACE 計数、非 LLM IR arm と比較 harness は本 E 段の保証に含めない。必要になれば、それぞれ受理権威・観測方法・費用を明示した別裁定にする。段階 F の実 LLM 系列も別 session のままとする。

## 総括

**推奨: adopt_with_conditions。** 実装前の must-fix は、(1) `prepare_policy` を含む全 policy-marker 呼び出しの引数整合、(2) proposal JSON の重複 key と値型の fail-closed、(3) reverse 判定を検証済み critic 出所へ束縛、(4) projection・履歴の固定 path と系列出所の検査。静的レビューのみ実施し、build・pytest・live 計測は行っていない。