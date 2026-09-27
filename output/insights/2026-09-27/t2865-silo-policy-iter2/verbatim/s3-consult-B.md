## 所見

1. **must-fix** — [brief.md:16](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/brief.md:16)、[D2270.md:7](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/verbatim/D2270.md:7)、[runbook:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/phase3-silo-policy-runbook.md:47)。P3 の bootstrap 省略は確定済み手順と食い違う。**放置時の成果物:** B の初回 coder 入力に A の stock 値が記録され、手順どおり測った系列とは言えなくなる。**代案:** 今回は B 専用 stock を測る。省略するなら、stock の source は骨格 patch を使わず、各 iteration の評価には同 job stock が付くことを根拠に、親が手順の例外を明示裁定する。「条件が混ざるから性能比較が歪む」という [plan:48](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/codex/s2-plan.md:48) の理由は強すぎる。再測が変えるのは初回 coder 入力の二値であり、pair の対照値ではない。

2. **should-fix** — [patch:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/patches/silo-function-policy-variant.patch:79)、[段階 F:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md:51)。seed 修正は採るべき。旧骨格で B′ を回しても、実際に使われた `ctx.rand` の jitter が worker 間で同期し、2〜3 iteration の少ない観測から待機方策を誤って避ける可能性がある。**放置時の成果物:** B′ の性能値と critic 診断が同一 seed 条件の影響を受ける。**代案:** 新系列 B の前に骨格だけ直す。Codex author、焦点 test、変異、受入の費用はあるが、新 checkout が必要な時点で条件分離の追加費用は小さい。旧 A と B の性能値は合算しない。

3. **should-fix** — [plan:30](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/codex/s2-plan.md:30)、[template test:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_function_policy_template.py:228)。二本目の新 test は既存の stock token・API・hole・上限検査と重なる。`begin()` の文字列確認だけでは、seed 関数が実経路で効く証拠にもならない。**放置時の成果物:** test が緑でも各 worker の乱数系列が同じままの B を受け入れ得る。**代案:** 実 patch 適用後の関数を使う一つの焦点 test で、異なる `thid`、同一 `thid` の再現、`begin()` 再呼出し後の継続、呼出しの結線を確認する。既存 test はそのまま走らせる。変異は M1〜M3 をこの欠陥への照準として残し、M4 は削る。xorshift の非 0 状態は 0 に遷移しない。M4 が表す危険は初期 seed 自体が 0 になる場合だけで、通常の worker ID に対する到達性を示さない変異は実欠陥の証明にならない。

4. **should-fix** — [plan:50](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/codex/s2-plan.md:50)、[実 digest:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-stage-f/trees/e2e/output/exploration/campaigns/p3-silo-policy-loop-silo-policy-autonomous-877344a7/silo_policy_loop_digest.txt:10)、[runbook:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/phase3-silo-policy-runbook.md:119)。P5 の最小添付は妥当。digest だけでも四見出しは書けるが、候補実装も同 job stock も載らず、設計選択への帰属はほぼ `uncertainty` になる。**放置時の成果物:** 次の coder に渡る診断が、実装に結び付かない方向指定か根拠のない帰属になる。**代案:** B の当該候補実装と当該 pair の stock 結果だけを添え、欠測の LLC/IPC や因果関係は断定させない。§1(g) は critic の入力を digest に限定していないため、これは手順の範囲内。`justification` と他系列の値は渡さない。

5. **nit** — [brief.md:9](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/brief.md:9)、[plan:59](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/codex/s2-plan.md:59)。brief の「最大 4」は約 1125〜1245 秒／回という自身の見積りでは楽観的。**放置時の成果物:** 記録する予定 iteration 数と node 時間が過大になり、投入判断を誤る。**代案:** 2 回を目標、3 回目は開始前の残 walltime で判断する。`record-reject` が先に起点を作る経路も既に [runbook:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/phase3-silo-policy-runbook.md:109) にあるので、同じ説明を増やす必要はない。

6. **nit** — [plan:65](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/codex/s2-plan.md:65)、[runbook:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/phase3-silo-policy-runbook.md:22)。runbook 追記四項のうち、checkout 分離と投入前残予算は既存手順にある。**放置時の成果物:** 成果物の値は変わらないが、重複した運用文が後の改訂で食い違い得る。**代案:** 追記は critic の最小入力・四見出しと、骨格変更時に条件を分ける記録方法に絞る。bootstrap は項 1 の裁定に合わせて既存 §1(0) を扱う。

## plan / brief への代案

B は seed 修正を含む commit の **HEAD から**新 submit checkout を作り、A の campaign dir を共有せずに回す。[plan:54](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/codex/s2-plan.md:54) の時点指定は必要。patch の `begin()` 初回 seed は既存 hunk と `thid_` を使える最小の実用形である。[patch:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/patches/silo-function-policy-variant.patch:130)、[transaction.hh:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/external/ccbench/cc/silo/include/transaction.hh:45)。`next_random()` の lazy seed は worker ID を渡す経路が別途必要になり、TLS address や thread ID hash に替えると実行間の決定性を失うため、より小さくない。

brief の patch hash 監視不在、coverage JSON、campaign identity 内部の詳述は、checkout・HEAD・patch SHA を insight に記録し別 dir で走る限り実走条件を増やさない。[brief.md:10](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/brief.md:10)、[plan:49](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/codex/s2-plan.md:49)。一方、pair job の要求 walltime 値、trace 保全先、検査を含む投入直前の 2 node 時間判定は [plan:57](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/codex/s2-plan.md:57)・[plan:61](/work/SFC/tanab/tmp/dev-wave-t2865-iter2-20260927/codex/s2-plan.md:61) のとおり残す。

## 総括

所見 6 件（must-fix 1、should-fix 3、nit 2）。  
seed は直す。A は予算停止として閉じ、修正後の新 checkout で B を 2 iteration 以上回す。  
親への裁定依頼は P3 のみ必須：確定済み bootstrap 手順を守って再測するか、初回二値の再利用を明示的な例外として認めるか。  
P5 は当該候補実装と同 job stock だけを添える最小案を推奨する。