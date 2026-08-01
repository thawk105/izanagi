| 修正前の所見 | 判定 | 修正後の照合結果 |
|---|---|---|
| revA-1: atom 全域を削る偽 no-good cut | **regressed** | README は exact-mask に直ったが、D119 に旧 `E=P∨C` 書換えが残った。さらに exact-mask は構造化された「なぜ」を消費せず、軸 (i) の実体を失った |
| revA-2: P1〜P10 が機械 predicate でなく cap-lift と未結線 | **partial** | 検査可能度の表示は改善。しかし結線は未実装で、P4/P6 の N/A 処理が論理矛盾したまま |
| revA-3: 軸 (iii) の無断必須化 | **partial** | README・D119 決定 (2) では撤回。しかし D119 決定 (7) が P4 を無条件の「全件必須」へ残した |
| revA-4: 32 点・whiteboard 3 状態の誤認 | **closed** | 列挙空間／規約に限定し、機械契約でないことを本文へ反映した |
| revA-5: 「解いた・確定・supersede」と draft の衝突 | **closed** | phase3・runbook・main-experiment は draft／未実装／cap=1 に戻った |
| revA-6: report-only と reflux on/off の両立不能 | **partial** | 未解決として明記・裁定へ返したが、契約自体は未決 |
| revA-7: origin preimage の不一致 | **closed** | README §3.5 を詳細正本、D119 を骨子とする参照関係は明示された |
| revA-8: 件数誤りと B8 脱落 | **partial** | 18 件へ訂正し B8 を復帰。ただし consumer 地図と control event の扱いはなお不完全 |
| revA-9: runbook の metrics／run-root 誤記 | **partial** | run-root は訂正。metrics の偽文は残したまま後段で自己否定している |
| revB-1: D116 採番衝突 | **partial** | D119 への改番は成立したが、D119 本文に旧 `D116` 参照が残る |
| revB-2: cross-generation 全面拒否の過大主張 | **closed** | 3 入口が拒否するのは `generations` 引数だけと限定し、注入・直接反復・race を保証外とした |
| revB-3: report-only と既存 ablation の矛盾 | **partial** | revA-6 と同じ。未解決の可視化まで |
| revB-4: atom 全域を削る偽 no-good cut | **regressed** | revA-1 と同じ。過剰拒否は縮んだが、D119 の旧式残存と軸 (i) 不充足を新たに生んだ |
| revB-5: D51 逐次 provenance の公開面漏れ | **closed** | README §4②・P2 に追加された |
| revB-6: living docs／実行時文字列の staleness | **partial** | docs の状態表現は概ね是正。コード文字列は残存し、一部は report/journal に入る |
| revB-7: 「機械検査可能な 10 件」の虚偽 | **partial** | 虚偽表現は撤回したが、P4/P6 の適用可能性と cap-lift 判定は未定義 |
| revB-8: runbook 3.3 が実行不能 | **partial** | runbook と README P8 は限定したが、D119 P8 はなお「runbook 3 手順」を要求する |
| revB-9: insights authority marker 欠落 | **closed** | `authority: none` / `default_effect: no-state-change` を追加した |
| revB-10: main-experiment の存在しない path | **partial** | 実 path を追記したが、誤った `campaign/p3_s4_loop.py` 自体も残した |
| revB-11: X1〜X7 / I2/I3 対応なし | **closed** | README §10 に全項目の対応表がある |

集計は **closed 7 / partial 11 / regressed 2**。

## 新規所見

### BLOCKER 1 — exact-mask cut は安全な再実行防止だが、軸 (i)／規律 3 の解ではない

設計目的は「構造化された『なぜ』を機械が消費し、候補空間を狭める」ことだが、cut に入る情報は失敗 mask `p` だけで、anomaly は存在確認にしか使われない。本文自身も「規律 3 の『なぜ』を満たしたとは名乗らない」と明記している。[設計本文:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:47) [設計本文:118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:118)

5-bit universe では機械側の受理領域が 32→31 点へ縮むだけで、generator の提案分布は縮まらない。`C` を見せず、拒否時も query を消費するため、同じ `p` の再提案や、5 個すべて残る Hamming 距離 1 の近傍候補を防げない。[設計本文:143](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:143) [設計本文:262](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:262)

したがって exact-mask cut は「既知 red の重複実行防止」としては正しいが、「failure reason を次候補へ効かせる還流」ではない。

**成果物影響:** 多世代を開くと、origin の query を同一・近似候補で使い切り得る一方、材料レポートだけが「規律 3 還流あり」を名乗り、候補列・certified best・探索量の意味が偽になる。

### BLOCKER 2 — D119 が exact-mask reject と旧 `E=P∨C` 書換えを同時に命令する

D119 決定 (3) は machine が `E=P∨C` を build すると命令する一方、直後の決定 (4) は禁止 mask を書き換えず拒否すると命令する。[D119:5687](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5687) [D119:5693](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5693)

README では `C` は mask の集合であり、`P∨C` は型としても成立しない。README は明確に書換えを禁止している。[設計本文:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:153)

これは §6 の closed 表だけ直し、権威本文を直していない例である。

**成果物影響:** 実装者の解釈によって「提案を拒否」または「別 mask を build」が分岐し、fitness の帰属、WAL の variant、certified 選択が変わる。

### BLOCKER 3 — 軸 (iii) は撤回されておらず、P4/P6 により cap-lift 契約も充足不能

D119 決定 (2) は軸 (iii) の必須化を撤回するが、決定 (7) は P1〜P10 を「すべて満たす」とし、P4 に軸 (iii) の batch freeze を無条件で残す。[D119:5679](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5679) [D119:5717](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5717)

README でも「すべて満たす」としつつ、P4 は条件付き、P6 は非適用なら「満たしたと数えない」とする。[設計本文:397](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:397) [設計本文:407](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:407)

この定義では、ユーザーが (iii) を採らない場合は P4、座標 cut を主張しない場合は P6 が非適用のままなので、「全件充足」が成立しない。加えて D119 は未裁定を 5 件、README・phase・runbook は 6 件と数える。[D119:5712](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5712)

**成果物影響:** 実装者が未承認の batch freeze を必須化するか、cap を永久に解除不能にするかで分岐し、多世代の受理集合と正式系列の開始条件が一意に決まらない。

### MAJOR — `reflux-origin` control event が材料レポートで偽の rejected variant になる

設計は固定 variant `"reflux-origin"` と `reflux-control` stage を WAL に書くよう指定する。[設計本文:291](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:291)

現行 `layer3_report.py` は全 WAL record を `variant` で集約し、`commit` の無い全 variant を `commit-event-absent` reject にする。[layer3_report.py:192](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/layer3_report.py:192) [layer3_report.py:395](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/layer3_report.py:395)

したがって stage allowlist だけを拡張すると、control plane が候補 variant として `variants` と `rejects` に混入する。設計には独立した `control_events` 区画や候補集計からの分離規則がない。これは修正前の「未知 stage 拒否」より一段先の、新しい consumer 意味論漏れである。

**成果物影響:** 材料レポートに実在しない棄却候補が増え、候補件数・reject 台帳・source-ref の意味が汚染される。

### MAJOR — D119 と runbook の限定がなお一致しない

D119 は別 run-root を無条件の予算回復経路として列挙するが、実コードと runbook では新品になるのは no-build だけで、build 経路は同一 campaign root である。[D119:5703](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5703) [runbook:154](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3-s8c-autonomous-trial-runbook.md:154)

また README P8 は実行不能な 3.3 を射程外にしたが、D119 P8 はなお「runbook 3 手順」を要求する。[設計本文:411](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:411) [D119:5724](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5724)

**成果物影響:** origin 分割による予算回復の脅威モデルと cap-lift の受入条件が正本ごとに変わり、同じ artifact の正式受理可否が一致しない。

### MAJOR — closed 表だけ直し、本文の誤記を残した箇所が複数ある

- D119 の却下案に改番前の `D116` が残り、現在の D116＝T-295 を誤参照する。[D119:5735](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5735)
- runbook は「planner/coder が受けるのは abstract whiteboard まで」という偽文を残し、11 行後に訂正を追記しただけである。[runbook:175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3-s8c-autonomous-trial-runbook.md:175)
- main-experiment は存在しない `campaign/p3_s4_loop.py` を残し、実 path を括弧内へ足しただけである。[main-experiment:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3-main-experiment.md:43)
- runbook の run-root 訂正箇所には `。****D114` という壊れた emphasis も残る。[runbook:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3-s8c-autonomous-trial-runbook.md:157)

**成果物影響:** decision ID・情報流・実装 path の機械参照が誤った対象へ解決され、proof-chain と実装地図の参照再現性が落ちる。

### MINOR — 「現行受理集合は任意の非空 1 行 C++」は逆方向への過大訂正

任意の非空 1 行を受けるのは coder parser までである。[p3_autonomous_workload_trial.py:261](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:261)

production 経路はその後に diff quarantine、禁止識別子、auditor gate を適用する。[p3_s4_loop_trigger_gating.py:301](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:301)

したがって正確には「parser の受理集合は任意の非空 1 行、production の受理集合はそこから三 gate を通る未閉包集合」である。

**成果物影響:** D96 で比較すべき現行正例・負例集合を parser 境界だけで作ると、移行時の受理集合差分を誤計数する。

## 「コード側は scope 外」の判断

コードをこの docs-only wave で直さない判断自体は妥当である。ただし所見を閉じたことにはならない。

`_validate_generation_budget()` と freshness error は依然 `D106 残余 1 の裁定まで` と出す。[p3_autonomous_workload_trial.py:184](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:184) freshness 側は `supervisor-error` として journal／report に保存される。[p3_autonomous_workload_trial.py:714](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:714)

したがって revB-6 は **partial** のまま、段 7 で具体的な T-ID を付けて起票すべきである。README の「次の一手へ起票」には現時点で ID がなく、起票済みの証拠ではない。cap=1 を維持する現在の docs-only wave の単独 BLOCKER ではないが、多世代開放前には必須修正である。

静的検査のみであり、pytest・build・`check_docs.py` は実行していない。

## 総括

**(a) 判定: NO-GO**

**(b) 残る BLOCKER: 3 件**

1. exact-mask cut は generator の提案分布も構造化された「なぜ」も変えず、軸 (i)／規律 3 を満たさない。
2. D119 が `E=P∨C` 書換えと exact-mask reject を同時に命令する。
3. 軸 (iii) 撤回と P4 無条件必須が衝突し、P4/P6 の N/A により cap-lift 条件も充足不能である。

**(c) 最小の追加修正**

1. D119 の `E=P∨C` を削除し、exact membership reject へ一本化する。
2. exact-mask cut を「重複実行防止の containment」と降格する。軸 (i) を名乗るなら、構造化 anomaly から安全な候補集合 predicate を独立再導出する契約と、重複時の bounded 再提案／novelty 規則を別途設計する。それまでは T-244 本体を未解決、cap=1 のままにする。
3. P4/P6 を明示的な conditional obligation に分離し、N/A を cap-lift の失敗に数えない。未裁定件数を 6 に統一し、D119 P8 を runbook 3.1/3.2 に限定する。
4. `reflux-control` を candidate variant 集計から分離する Layer3 schema・source-ref・正負例を設計する。
5. D116 残存参照、runbook の偽文、main-experiment path を本文から除去し、コード文字列には具体的な次タスク ID を付ける。