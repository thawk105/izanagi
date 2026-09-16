## 所見 (番号・real/refuted/判定不能・file:line・成果物影響 1 行)

以下、リポジトリ内の行番号は指定 worktree、`brief.md`・`plan.md`・`sources/` は指定 job ディレクトリを基準とする。静的検査のみ実施した。

1. **real — pin 閉包は3機構では閉じない。**
   `orchestrator/campaign/p3_b4_closed_critic.py:656` は critic 本文を projection closure に含め、`:1658` と `:1679` は receipt 再読時に live 本文・closure と照合する。さらに `p3_b4_raw_record_producer.py:1000`、`:1165`、`:1185`、`:1192` に独立した snapshot 照合がある。`claude_projected_provider.py:159`、`:162` は本文から role hash・実効 prompt を生成する。`brief.md:22` の列挙は不完全。
   **成果物影響:** critic 訂正で新規 receipt の role／prompt／projection hash が変わり、旧本文に束縛された receipt は新版 consumer で拒否され得る。

   **refuted〈指定範囲〉 — 記入済み B-4 pin の陳腐化。**
   指定3ディレクトリへ `grep -rlE` で role hash、critic パス、旧 critic SHA、prompt／closure hash の識別子を検索したがヒットなし。`docs/phase3-b4-reflux-ablation-preregistration.md:166` も未記入。ただし「§5 全体が未記入」は誤りで、`:158–161` には記入済み値がある。repository 外まで含む「receipt 0件」は判定不能。

2. **real — planner の凍結説明を全経路へ一般化している。**
   `plan.md:124–126` は campaign ごとの凍結を無条件に述べる。しかし T-2588 は同じ planner-v4 に本走の実測を戻している（`output/insights/2026-09-16/t2588-k2-loop-roundtrip/README.md:184`、`materials/planner-input-2.json:2`）。凍結の実装根拠 `p3_autonomous_workload_trial.py:2043–2076` は8c経路である。
   **成果物影響:** 新版 planner 本文が K2 の更新済み入力を凍結値として解釈させ、次提案とそのレポートを変え得る。

   **判定不能 — 記録済み K0/K1/K2 の再検証が実際に赤になること。**
   具体的な既存記録から変更対象 role 本文への live 照合連鎖は確認できなかった。B-4 の拒否経路は所見1で確認済みだが、対象 receipt は未発見。規律7による当時の commit での再検証と、新版 consumer での受理は別の保証である。旧記録を修正せず当時の環境で検証する限り、今回の文書変更を過去へ適用する必要はない。

3. **real — D1860 の扱いについて brief の根拠が不足。**
   `sources/D1860.md:3` は「削除せず null」、`:13` は role と runbook の乖離を削除却下の理由とする。実装変更 T-304 自体に裁定を上書きする権威はない。一方、後続の `sources/D2104-item4.md:5–8` は今回の runbook 訂正を明示的に授権している。現在は削除する方が role と整合するため、削除案そのものは妥当。
   **成果物影響:** 根拠を補わないと、裁定記録には「保持」、新版の手動射影には「削除」が併存し、適用すべき入力形の参照が分裂する。

   新たな裁定を要求する必要はないが、D2104による今回以降の限定的な変更と、D1860当時の判断を保持する旨を decisions fragment 等に残すべき。

4. **refuted／real — 入力への追加内容は分けて評価する必要がある。**
   **refuted:** `plan.md:64–67` の verify 規模・build 分離・median 規則は測定手順であり、勝ち筋値・実測利得・最適化機序を追加するものではない。`:28` の適用版にも K0/K1/B-4 や裁定番号は入っていない。

   **real:** `plan.md:56` の「その走行の `PerfConfig` を用いる」は、inline データ内で実行方針を指示する読みが可能。`src/coder-leakproof-context.md:3` は直接入力を明記している。
   **成果物影響:** 指示として採用されれば、coder の提案根拠に評価設定の選択が混入する。実際の設定変更や certified 受理への到達は未実証。

   critic の「独立の帰属根拠として使わない」（`plan.md:92`）も指示文だが、こちらは役割指示本文への適切な訂正であり、未信頼データからの権限昇格とは異なる。恒等式自体も勝ち筋情報ではない。trigger-gating への D410番号・内部関数名の追加（`:138`）は coder に不要で、運用文書へ移す方がよい。

5. **refuted／判定不能 — scope 外とする攻撃は一律には成立しない。**
   - **refuted:** hardware 削除は名指しの Measurement Setup 内（`src/coder-leakproof-context.md:63`）。訂正範囲内。ただし「default_perf に無いから誤り」とは証明できず、汎用設定として断定できないため削除、と説明する。
   - **refuted:** critic-experiment は `sources/worklog-items.md` の T-2717 項で明示され、D2104はT-2717を対象に含む。「裁定の名指し外」という brief の整理が狭すぎる。
   - **refuted:** trigger-gating の「直近実測」（`.claude/agents/coder-v4-autonomous-trigger-gating.md:62`）は coder 凍結表現訂正の直接対象。
   - **判定不能:** base coder を除外して十分か。`.claude/agents/coder-v4-autonomous.md:27` は更新を明言しないが、凍結も説明しない。誤記がないことと、依頼された凍結表現が十分なことは同義ではない。
   - **refuted:** architecture／roadmap の latency 訂正漏れ。`docs/agent-architecture.md:66–72`、`docs/roadmap.md:226–232` に当該 latency 列挙は現存しない。

6. **refuted — schema／manifest／共通テンプレートの変更は必要ない。**
   `spec.py:55–68` の manifest entry に本文は入らず、`:566` はその entry 自体を hash 化する。本文照合は別の `:583–590`。共通テンプレートの hash は展開前文字列を対象とする（`:550–553`）。したがってこれらの pin は不変。

   一方、**semantic digest と展開済み developer instructions は変わる**（`:771`、`:790–799`）。plan はこの点を正しく列挙している。shape parity は入力例を変えない限り維持されるが、open subtree を検査しない（`tools/check_codex_agents.py:169–173`）ため、本文の意味的正しさの証明には使えない。

7. **refuted〈変異設計〉／要限定〈検出力の主張〉 — M1/M2/M0 は概ね単一理由。**
   `plan.md:267–279` の区別は妥当。M1は3 role 個別の検出ではなく「追随 helper 呼出し欠落」一理由。M2は既存の一般的な source pin 検査で、`tools/check_codex_agents.py:44` → `spec.py:587` の import 時拒否。今回の latency／凍結説明の意味を守る検査ではない。M0はコメントのみの等価変更。

   KILLED／SURVIVED はすべて期待値であり、未実測。新規 semantic 防壁の追加は不要。

## brief の provisional 裁定 (P1)〜(P4) への判定

| 裁定 | 判定 |
|---|---|
| P1 | **修正して採用。** ledger・adapter・baseline 追随は必要。ただし第4の receipt／projection 閉包を追加し、「受理集合・挙動不変」の無条件主張を撤回する。 |
| P2 | **採用。** T-2717を通じて射程内。過去のP2-5入力・結果は保持する。 |
| P3 | **採用、理由修正。** Measurement Setup内の汎用的でない断定を除く訂正として扱う。 |
| P4 | **一部採用。** trigger-gating優先は妥当。ただしplannerの凍結説明を8cと該当runbookへ限定し、K2へ一般化しない。base coder除外の説明も補う。 |

## 推奨する plan v2 への修正

- pin 閉包表に B-4 receipt、projection closure、実効 prompt を追加する。成果物検索範囲と「該当値未発見」を記録する。
- 「不変」を schema・検査規則に限定し、本文・prompt・semantic digest・新版で受理される source bytes は変わると明記する。
- planner の冒頭を経路非依存の説明に戻し、凍結は8c／指定runbookの段落で説明する。
- D1860との関係をD2104に基づく限定的な後続訂正として記録する。
- inline文書は「評価側で使用される設定である」等の記述形にする。裁定番号・内部関数の説明は運用側へ置く。
- 焦点走へ `orchestrator/tests/test_p3_b4_raw_record_producer.py` を追加する。M2は一般pin検査による拒否として計数する。

## 総括

**plan v2への修正が必要。主な real は、第4のpin機構の欠落と、8cの凍結規則をK2にも通用する説明へ広げている点。** 記入済みB-4 receiptの実害は指定範囲では確認できなかった。schema改版や新規gateは不要。書込み・pytest・checker実行は行っていない。