結論として、段 2 の **再導入 11 / 削除 0 / hold 5** はそのままでは certify できない。静的検査のみで、pytest は実走していない。

### 1. [real] P4 は誤りだが、プランの `F(t)` も不完全

14 node は共通 fixture を要求し、fixture は POS/NEG の golden 準備後に `_build_snapshot_base(_ROOT, base)` を実行する。[test_codex_reasoning_ab.py:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:506) [test_codex_reasoning_ab.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:518)

プランはこれを `Sdir(t) ∪ Hfixed` としたが、`_build_snapshot_base` は現在の `_ROOT` を `_init_submodules_from_local_source` に渡す。[codex_reasoning_ab.py:2550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:2550) [codex_reasoning_ab.py:2569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:2569) その先では source repo の全 index entry を `_index_stage_entries` で取得し、実体は `git ls-files --stage -z` である。[codex_reasoning_ab.py:847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:847) [codex_reasoning_ab.py:1487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:1487)

したがって14 node の共通閉包は少なくとも `Sdir(t) ∪ tracked-index-at-tip(t) ∪ Hfixed ∪ Tnode`。親の「body が固定だから非比例」は D463 違反であり、プランの「比例」という区分自体は正しいが、比例軸を output artifacts だけに限定した台帳は不正確である。

成果物影響: certified 選択は変わらないが、5 hold の reason/F(t) と台帳の `hold_axis` は tracked-files 軸を欠いたままになる。

### 2. [refuted] `pack-objects --revs` 自体は tip 依存ではない

`BASE_COMMIT` は固定 literal であり、`pack-objects --revs` の stdin も `BASE_COMMIT + "\n"` だけである。[codex_reasoning_ab.py:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:59) [codex_reasoning_ab.py:2557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:2557) さらに既定 node が転送入力を base commit だけと明示検査している。[test_codex_reasoning_ab.py:1634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1634) [test_codex_reasoning_ab.py:1716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1716)

tip 比例項は pack の祖先閉包ではなく、その後の current source index/submodule 検査である。

成果物影響: レポートで pack を比例源とする参照は追加不要。比例軸の参照先は `:2569 → :847 → :1487` に修正する。

### 3. [real] 実 golden を導出する既定 node は既に存在する

fixture は `_prepare_snapshot_case` を実行し、POS では `derive_independent_golden` に入り、route A/B を実際に作って比較する。[test_codex_reasoning_ab.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:518) [codex_reasoning_ab.py:2532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:2532) [codex_reasoning_ab.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:771) [codex_reasoning_ab.py:815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:815)

少なくとも次の既定4 node が fixture を起動する。

- `test_snapshot_submodule_object_store_is_recursive` [test_codex_reasoning_ab.py:2059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:2059)
- `test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid` [test_codex_reasoning_ab.py:4778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:4778)
- `test_git_answer_object_reinjection_is_rejected` [test_codex_reasoning_ab.py:4859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:4859)
- `test_supervisor_launches_pair_and_scrubs_git_environment` [test_codex_reasoning_ab.py:6150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6150)

ただし M2 node は `_compare_golden_routes` が実際に呼ばれたことと literal hash を独立に検査する。[test_codex_reasoning_ab.py:1976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1976) fixture だけでは「比較を route A の return に退化させる」mutation を殺せない。一方 `test_derive_independent_golden_wires_pins` が配線検査だけという判定は正しい。[test_codex_reasoning_ab.py:6037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6037)

成果物影響: レポートの「唯一の実 golden node」は「唯一の route-comparison 呼出し mutation 防壁」に修正するが、M2 の再導入という受理集合は維持する。

### 4. [real] replay の代替防壁は明白に非等価

hold 候補は10 run の実 manifest を replay し、完全性、判定台帳、resource ledger、reader agreement、extra rollout tamper を動的に検査する。[test_codex_reasoning_ab.py:6205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6205)

代替とされた `test_m5_generated_session_rows_require_set_equality` は production source に2文字列があることしか見ない。[test_codex_reasoning_ab.py:9138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:9138) プラン自身も「完全 replay と tamper 実行の代替ではない」と認めている。[s2-plan.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:34) D451 は防壁がゼロになる hold を禁止している。[D451.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/D451.md:3)

成果物影響: replay は hold 受理集合から外して再導入するか、先に分割・最適化する必要があり、現行 11/5 は少なくとも 12/4 に変わる。300秒上限と両立できる実装が無い現状では certify 不可。

### 5. [real] cleaned-snapshot の代替も manifest 防壁として非等価

held node は cache が消えたことに加え、各 repository の `commit_graph` absent manifest が5 fieldの正確な値で記録されることを検査する。[test_codex_reasoning_ab.py:1780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1780)

代替 node は object-info directory が空になることだけを検査し、返却 manifest の schema/value は見ない。[test_codex_reasoning_ab.py:1818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1818) 既定 fixture consumer も `commit_graph` の値を assert していない。[test_codex_reasoning_ab.py:2059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:2059) プランも「逐語 assertion は固有」と認めながら hold を選んでいる。[s2-plan.md:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:37)

成果物影響: absent-manifest contract を正しさ防壁として維持するなら、この node も再導入となり、受理集合は少なくとも 13/3 へ変わる。

### 6. [real] M1 hold は mutation の期待参照と不整合

module 冒頭の現行契約は M1 の expected mutation node を `test_m1_snapshot_head_pin_is_independent` と明記し、親 harness がこの一覧を使うとしている。[test_codex_reasoning_ab.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:4) [test_codex_reasoning_ab.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:21)

代替 node も HEAD mismatch branch を通すが、別 node である。[test_codex_reasoning_ab.py:4060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:4060) D452 の入口も expected node は既定 skip されないことを要求する。[D451.md:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/D451.md:23)

成果物影響: M1 を再導入するか expected-node 正本を代替 node へ変更しなければ、mutation 台帳の期待赤参照が held node のまま残り、certified mutation 受理が成立しない。

### 7. [real] re-evaluation token は運用上の恒真条件

プランが提案する validator は suffix の JSON shape を検査するだけで、`barrier_nodes` の収集・hold 状態や suite 時間を評価しない。[s2-plan.md:100](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:100)

実際の collection hook は registry key の存在だけで常に skip を付ける。[conftest.py:869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:869) 完全 collection 時の検査も「hold 対象 node が消えたか」だけで、token 内の barrier node は読まない。[conftest.py:908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:908) registry 側も reason を検証・出力するだけである。[growth_test_holds.py:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:533) [growth_test_holds.py:697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:697)

したがって barrier が消えても、suite+node が300秒以下になっても何も赤くならない。既定走行の評価主体は存在しないので、指定どおりこれは恒真と断ずる。

成果物影響: 台帳には「再評価条件あり」と表示される一方、受理集合は永久に変化せず、レポートの trigger は実効性のない注釈になる。

### 8. [refuted] D335 違反のテスト削除は計画されていない

D335 は該当テスト本体の削除を却下している。[D335.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/D335.md:3) [D335.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/D335.md:20) プランは削除0件で、編集案も registry 行の除去による再導入と1 test call の変更だけであり、test body の削除はない。[s2-plan.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:5) [s2-plan.md:166](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:166)

成果物影響: 削除件数0と削除受理集合は変更不要。「registry 行削除」を「テスト削除」と記録しないことだけが必要。

### 9. [real] cold/warm の比例一般化は測定されていない

probe は同じ5,482-file corpus に対する cold unpinned 1回と pinned 1回しか記録していない。[probes.txt:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/probes.txt:1) [probes.txt:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/probes.txt:7) 18.99秒と18.05秒は standalone `_find_rollout` probe ではなく、parametrized test 全体の call 時間である。[durations-16-opt-in.txt:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/durations-16-opt-in.txt:5)

したがって異なる corpus size を用いた傾き、反復分散、page-cache 条件、他 job の I/O 競合は測っていない。静的コードの `rglob` は D463 上の output-corpus 入力集合を証明するが、cold/warm 時間が file 数へ比例するという性能曲線までは証明しない。[codex_reasoning_ab.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:462) [codex_reasoning_ab.py:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:483)

また pinned でも `rglob` は残るため、親の「0.036秒になり比例源が消える」は誤りで、プラン自身はこれを訂正している。[s1-brief.md:57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s1-brief.md:57) [s2-plan.md:126](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:126)

成果物影響: レポートの warm 18.5秒は「test call からの推定」に降格し、329.754/18.5から将来予算や成長率を外挿してはならない。D463 区分自体は変わらない。

## 総括

must-fix は重い順に次の3点。

1. replay integration を非等価な文字列検査で代替して hold する裁定を撤回する。最適化・分割なしでは D451 と300秒上限を同時に満たせない。
2. re-evaluation token に既定 evaluator と期待赤 node を設ける。現案は全条件が運用上の恒真である。
3. hold 集合を再監査する。少なくとも cleaned-snapshot は最後の manifest 防壁であり、M1 は mutation の期待参照と不整合。現行 11/0/5 は維持できず、少なくとも 13/0/3、M1 正本を変えないなら 14/0/2 になる。