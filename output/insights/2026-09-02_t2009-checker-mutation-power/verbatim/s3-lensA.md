## 所見 1 — blocker: M5 の分岐が到達不能

所見: M5 に登録された digest は 63 桁で、SHA-256 の `hexdigest()` と一致しないため、意図した hash-overfitting 変異ではなく実質的な等価変異になる。  
根拠: [plan-out.md:231](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2009-checker-mutation-power/plan-out.md:231>) は末尾 `...11a2`、実 fixture の値は末尾 `...11a2a` の 64 桁である [test_verifier.py:1413](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/tests/test_verifier.py:1413>)。  
影響: `SURVIVED` しても閉じた fixture 集合の検出力を測ったことにならず、E1 と同じ「分岐非到達」の結果になる。  
推奨: scope 内 — digest を `1dbb84734cd360e785f25ae241ab2d61ef51a4b2c55e77ea8af2a641ee511a2a` に直し、fixture digest との一致を事前登録してから走らせる。

## 所見 2 — blocker: P1 を殺す既存 node の見落とし

所見: 推奨分母の外に、P1 で赤になる既存 behavioral node が少なくとも 1 件ある。  
根拠: `_mock_pipeline_multipass` は `False` のとき `r1_write_skew` を実 verifier に渡し、結果を `_red_vr()` へ置換しない [test_campaign.py:8029](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/tests/test_campaign.py:8029>) [test_campaign.py:8034](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/tests/test_campaign.py:8034>)。その経路を使う `test_pipeline_extra_correctness_second_pass_red_aborts_with_workload_tag` は赤判定を assert する [test_campaign.py:8125](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/tests/test_campaign.py:8125>)。  
影響: plan の「test_campaign の r1 経路はすべて mask される」という説明 [plan-out.md:396](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2009-checker-mutation-power/plan-out.md:396>) と、P1 の失敗 node 完全集合が誤りになる。M3/M5 の生存方向を直接反転させる見落としではないが、suite-wide の分母主張と DW-M08 を満たさない。  
推奨: scope 内 — 上記 node を selector と P1 の `expected_nodes` に追加する。新しい test は不要。

## 所見 3 — behavioral 分母に純粋な fixture 同一性 node が残る

所見: `test_verifier.py` 全体を選ぶと、contract-loader pin ではないが、verifier 挙動を一切実行しない raw-bytes 同一性 node が 2 件残る。  
根拠: `test_new_real_fixture_bytes_are_exact` [test_verifier.py:1749](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/tests/test_verifier.py:1749>) と `test_real_silo_fixture_bytes_are_exact` [test_verifier.py:1788](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/tests/test_verifier.py:1788>) は fixture bytes の長さ・SHA だけを見る。plan 自身も source 変異では落ちないと認めている [plan-out.md:449](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2009-checker-mutation-power/plan-out.md:449>)。  
影響: KILLED/SURVIVED 自体は歪めないが、「behavioral node だけの分母」という説明は正確でなく、実行 node 数を検出力の分母に使うと汚染する。  
推奨: scope 内 — この 2 node は exact `--deselect` にするか、matrix 上で「inert identity controls」と別層へ明記する。

## 所見 4 — F-new1 は過大一般化だが、同一性 pin 自体は正当

所見: 親 brief の「全変異が数百件の drift 赤を引く」は成立しない。一方、それを理由に同一性検査自体を無意味・禁止と書くのも誤りである。  
根拠: drift は列挙されているだけでは発火せず、`capture_contract_loader_binding()` が live bytes と HEAD blob を比較したときに発火する [contract_loader_binding.py:348](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/campaign/contract_loader_binding.py:348>)。brief は過去の `pipeline.py` 384 件を verifier へ一般化している [brief.md:22](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2009-checker-mutation-power/brief.md:22>)。規律 7 は束縛・完全性の同一性検査を明示的に許す [consult-facts.md:13](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2009-checker-mutation-power/consult-facts.md:13>)。  
影響: behavioral mutation power の証拠からは除外すべきだが、現行成果物と意味互換性を束縛する別目的の検査としては有効であり、両者は矛盾しない。  
推奨: scope 内 — 「同一性検査を除外」ではなく「今回の behavioral estimand から別層化」と記し、実行した exact selector と除外層を併記する。

## 所見 5 — 「規律 7 の穴」と呼べる条件をさらに限定すべき

所見: 生存変異を穴と呼べるのは、分岐が到達可能で非等価、受理集合または fail-closed 挙動を広げ、他層に mask されず、完全な behavioral 分母でも生存した場合だけである。  
根拠: `_classify` は verdict に影響しない [dsg.py:241](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/verifier/dsg.py:241>)、受理判定は SCC 数で決まる [core.py:147](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/verifier/core.py:147>)。DW-M03 も診断赤を kill としない [mutation.md:16](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/docs/dev-wave/mutation.md:16>)。  
影響: M1 は diagnostic sensitivity、E1 は等価対照、修正後 M5 は意図的 overfitting/D387 control であり、事故的退行の穴ではない。現計画では M3 だけが、生存した場合に coverage hole と呼べる候補である。  
推奨: scope 内 — 最終 matrix を「機械結果 / semantic 分類 / 主張可能範囲」に分け、M3 以外を穴数へ加えない。主張は固定 commit・exact selector・事故的退行に限定する。

## 所見 6 — README と実測が食い違う場合の一次資料

所見: 現 commit における検出挙動の一次資料は変異実測であり、README は設計意図・過去の認識・fixture provenance の一次資料として扱うべきである。  
根拠: README は M1/M2 を別 test が担い、M3 は未担保と記す [fixtures/README.md:175](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/orchestrator/tests/fixtures/README.md:175>)。一方 DW-M08 は観測 failure node の完全集合を要求する [mutation.md:55](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2009-checker-mutation-power/docs/dev-wave/mutation.md:55>)。  
影響: 食い違いを README に合わせて丸めると、実測の反証価値を失う。逆に README の由来や当初意図まで「誤り」と消すのも不適切である。  
推奨: scope 内 — 実測を current behavior、README を prior claim として併記し、差を erratum/所見にする。既存期待値は変更しない。

## 所見 7 — 実装 scope は維持可能

所見: plan に新 checker・新 test・新 fixture の実装は含まれておらず、上記 blocker は既存 selector と mutation spec の修正だけで解消できる。  
根拠: brief は tracked source を変えず scratch worktree だけで変異すると定める [brief.md:41](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2009-checker-mutation-power/brief.md:41>)。D799 も第二 checker の保存を退けている [consult-facts.md:44](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2009-checker-mutation-power/consult-facts.md:44>)。  
影響: M3 用の長さ 4 fixture や M5 用 metamorphic test は real な後続候補だが、この wave で追加すれば明確な scope 逸脱になる。  
推奨: 裁定へ — 穴を塞ぐ案は実装せず裁定パッケージに留め、insight も固定 commit と exact 分母を越えて一般化しない。

## 総括

(a) blocker は 2 件: M5 の 63 桁 digest による分岐非到達と、P1 を殺す `test_campaign.py::test_pipeline_extra_correctness_second_pass_red_aborts_with_workload_tag` の見落とし。

(b) 推奨分母は `test_verifier.py` から raw-bytes 2 node を deselectし、t1286 の赤 capability nodeと上記 campaign nodeを加えた集合。contract-loader live-binding node は別層のまま外す。

(c) プランのまま進めてはいけない。上記 2 blocker と分母純化を直せば、追加 checker/test/fixture なしで進行可能。pytest は実行しておらず、本結論は静的検査による。