### 所見 1 — BLOCKER: 71 件の「非比例」裁定は一次資料と矛盾する

- 主張: A06 21件／A09 10件／A10 40件を「4部分木が30日間不変」として却下した根拠は成立しない。
- 根拠 file:line: [adjudication.md](/home/SFC/tanab/.claude/jobs/bc06a389/tmp/dev-wave-t1222/adjudication.md:33) は `tools/task_runs` を30日前0件、現在7件と記録しながら、同:35-38で「4部分木は1 fileも増えていない」と結論している。実際、A09は [test_dev_waves_checker.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/orchestrator/tests/test_dev_waves_checker.py:60)、A10は [test_dev_waves_integration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/orchestrator/tests/test_dev_waves_integration.py:160) から `tools/task_runs` をcopytreeする。`git ls-tree -r -l` の再計算でも0 file / 0 Bから7 file / 138,785 Bへ増えている。A06の三部分木も合計486,395 Bから490,292 Bへ増え、copytree量はfile数だけでなくbytesにも比例する（fixtureは [test_codex_agents.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/orchestrator/tests/test_codex_agents.py:37)）。さらにA06の正例はfixture外の実ROOTを直接検査し、`.codex/agents/*.toml`も列挙する（同:159-161、[check_codex_agents.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/tools/check_codex_agents.py:323)）。
- これが真なら何が壊れるか: `not_proportional_bounded_input=71` が虚偽になり、D335対象を「非比例」として棚卸しから永久に外す。特にA06正例とA09正常系は独立経路があり得るため、実装済み3件だけで登録集合が確定したとも言えない。
- 提案: 段4へ戻し、71件をまず `growth-real` に再分類したうえでD451をnode別に再裁定する。negative/tamper群は最後の検出nodeなので非保留、A06正例とA09正常系は登録可否を再検査する。A10は比例性とは別にguard binding不可を維持する。

### 所見 2 — BLOCKER: provenance 2件は固定歴史だけを入力にしていない

- 主張: 「固定SHAの祖先集合なので今後増えない」はnode全体の呼出し閉包を見ていない。
- 根拠 file:line: 2 nodeは確かに固定SHAを渡す（[test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/orchestrator/tests/test_check_ai_provenance.py:2546)、同:2646）。しかし `_audit_history()` は毎回 `_scope_policy_commit()` と `_implementation_policy_commit()` を呼ぶ（[check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/tools/check_ai_provenance.py:1552)）。両者は固定SHAではなく現在のREPOで `git log ... -- docs/ai-provenance.md` を走査する（同:1122-1136）。裁定は `_build_ancestry` だけを根拠にしている（[adjudication.md](/home/SFC/tanab/.claude/jobs/bc06a389/tmp/dev-wave-t1222/adjudication.md:58)）。
- これが真なら何が壊れるか: `not_proportional_fixed_history=2` と「3.78秒は今後増えない」が過大主張になる。tip側の履歴成長項が受入に残る。
- 提案: 2件を `growth-real` に戻し、known-violation正例とregistry空変異を分けてD451を再判定する。「固定なのは選択commitとその祖先閉包だけで、policy epoch探索はtip依存」と記録する。

### 所見 3 — must-fix: A05の検出は回収されるが、land/waveだけを根拠にするのは不完全

- 主張: 3 nodeが担う正常系は、成功したno-arg `check_docs.py` 実行なら実質回収される。ただし全経路で常に回収されるわけではない。
- 根拠 file:line: 3 nodeはいずれもno-arg checkerのrc=0を確認し、1件はadmission findingゼロも確認する（[test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/orchestrator/tests/test_check_docs.py:7284)、同:7464、同:9435）。admission driftはproduction findingsへ入り、findingがあればrc=1になる（[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/tools/check_docs.py:5212)、同:5433）。一方landはnoopなら検査前にreturnし（[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/tools/dev_wave_land.py:2337)）、実行時も `--expect-active-transaction` 付きである（同:2211）。wave checkerはnoncompletedなら不要扱い、passive failureならskipする（[checker.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/tools/dev_waves/checker.py:643)）。ただし通常のクラス2/3完了には別途no-arg `check_docs.py` 実行義務がある（[CLAUDE.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/CLAUDE.md:155)、[AGENTS.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/AGENTS.md:26)）。
- これが真なら何が壊れるか: noncompleted/passive failureでは検出が後送りになるが、そのwave自体は成功成果物としてlandできない。noopは通常のclass 3 worklog fragment運用では例外的。landを通らない通常のAI作業は直接完了検査で回収されるが、人間の手作業や規律違反には機械防壁がない。発生率の実測資料はなく、頻度の定量断言はできない。
- 提案: 登録自体は維持可能だが、根拠を「land/wave」だけでなく「クラス2/3直接完了検査＋成功wave checker＋non-noop land」と書き、各非発火条件も併記する。

### 所見 4 — must-fix: collateral noteは発火条件を正直に表していない

- 主張: 現在の「trigger point regresses from acceptance to land」は単純化しすぎで、事実とも一致しない。
- 根拠 file:line: 実装文言は [growth_test_holds.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/orchestrator/tests/growth_test_holds.py:88)。裁定自身はnoop/noncompletedを認識している（[adjudication.md](/home/SFC/tanab/.claude/jobs/bc06a389/tmp/dev-wave-t1222/adjudication.md:53）が、diffのnoteにはnoop、noncompleted、passive failure、直接完了検査、landの引数差がない。
- これが真なら何が壊れるか: inventory利用者は「必ずlandで同値検査される」と誤読する。実際には成功経路と失敗経路で回収時点が異なる。
- 提案: noteを「pytest内の3回は消える。no-arg checkerはclass 2/3完了およびcompleted/passive-green waveで残る。landはnon-noop時のみactive-transaction modeで実行」に改める。

### 所見 5 — must-fix: D335のユーザー提示義務はcollateral_noteとinsight保存だけでは尽きない

- 主張: 機械可読記録は揃っているが、「ユーザーへ提示」は別義務である。
- 根拠 file:line: D335は正しさゲートの保留をユーザーへ提示すると明記する（[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/docs/decisions.md:14957)）。inventoryはnode、release condition、correctness flag、collateralを出力できる（[hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/tools/hold_inventory.py:208)）が、自動的にユーザーへ表示されるわけではない。実装差分にはinsightもまだない。
- これが真なら何が壊れるか: 3正しさゲートが既定skipになった事実を、ユーザーが最終報告を読むだけでは認識できない。
- 提案: 段7/最終報告で3 node、失う正例、代替実行と非発火条件、解除token、素のPython実行がfile-wideで拒否される変更を明示する。insightは証拠リンクとして添える。

### 所見 6 — must-fix: 既知の取りこぼし数とs8cの文言が曖昧

- 主張: 「最低8件」は真ではあるが、既に把握済みのtop-level node数を不必要に小さく見せる。
- 根拠 file:line: 既知漏れはA06の7、A10 socketの1（[adjudication.md](/home/SFC/tanab/.claude/jobs/bc06a389/tmp/dev-wave-t1222/adjudication.md:44)）、s8c negative-controlの1（同:47）、provenanceの2（同:63-64）で少なくとも11 node。s8cも共有fixture consumer 3件（[test_s8c_preregistration_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/orchestrator/tests/test_s8c_preregistration_invariant.py:118)）とは別に、`check_docs.main()` negative-controlが1件ある（同:257）。
- これが真なら何が壊れるか: 「s8cの3 nodeをD451で見送り」だけでは4件目が記録から消え、母集合の既知欠落数も過少になる。
- 提案: 「既知漏れは少なくとも11 top-level node。s8c共有fixture consumer 3件とs8c negative-control 1件を別々にD451見送り」と書く。

### 所見 7 — must-fix: 受入wall短縮は主張できない

- 主張: critical path未測定なので「wallが縮む」は書けない。
- 根拠 file:line: 3 nodeは各5.33秒という単発値しかない（[adjudication.md](/home/SFC/tanab/.claude/jobs/bc06a389/tmp/dev-wave-t1222/adjudication.md:75)）。受入はxdist/loadgroupで並列化される（[run_tests.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/tools/run_tests.py:380)）うえ、独立の完了時 `check_docs.py` は残る。
- これが真なら何が壊れるか: 3×5.33秒を受入wall短縮量として扱うと、並列workerの余裕と外側の直列checkerを無視した偽の性能成果になる。
- 提案: 「観測条件下で約16秒分のsubprocess elapsed総和をpytest選択集合から除いた。受入critical pathとnet wall差は未測定で、wall短縮は未確認」と書く。

### 所見 8 — nit: completeness実装は安全だが、裁定見出しは過大に読める

- 主張: 現diffは`registered-layers-only`を壊していない。ただし「母集合の棚卸し」「すべて棚卸し」は限定文から離れると完全性主張に見える。
- 根拠 file:line: inventory正本は明示的に `registered-layers-only`（[hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/tools/hold_inventory.py:35)）で、禁止文言テストもある（[test_hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-hold-sweep/orchestrator/tests/test_hold_inventory.py:766)）。裁定の限定定型は安全（[adjudication.md](/home/SFC/tanab/.claude/jobs/bc06a389/tmp/dev-wave-t1222/adjudication.md:117)）だが、同:1と同:96は単独引用に弱い。
- これが真なら何が壊れるか: 登録2層のsnapshotと、未閉包の候補探索を「全hold層の完全inventory」と誤認される。
- 提案: 「宣言した探索primitive内の既知候補」「既知の非登録理由」と呼び、限定文を件数・表の直前にも置く。

## 総括

- BLOCKER: copytree 4部分木不変という裁定は、`tools/task_runs` の0→7件と正面から矛盾する。
- BLOCKER: provenance 2件は現在HEADのpolicy履歴を走査し、「固定歴史だけ」は誤り。
- BLOCKER: 段4へ戻し、71件とprovenance 2件を比例対象としてD451をnode別に再裁定すべき。
- must-fix: A05登録は維持可能だが、代替経路・非発火条件・直接完了検査を正確に記録する。
- must-fix: D335のユーザー提示は最終報告で明示的に行い、insight保存だけで済ませない。
- must-fix: 既知漏れは最低8ではなく、現証拠上少なくとも11 top-level nodeと書く。
- must-fix: wall短縮は未確認。主張できるのは約16秒のsubprocess elapsed総和除去まで。
- nit: inventory実装のcompletenessは安全だが、「すべて棚卸し」の文言は限定する。
- pytest・Web検索は実行しておらず、緑は主張しない。