| 項目 | 判定 | file:line 根拠 |
|---|---|---|
| L-1 | **closed** | COMPETITOR の生成条件は `unexplained >= 3 && rate > 6.7` のみ。[probe:2258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2258)、[probe:2269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2269)。実 duration は CPU 境界時刻差から算出・保存される。[probe:2674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2674)、[probe:2285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2285)。旧 arm 絶対閾値は消え、空 subwindow は INVALID。[probe:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:875) |
| L-2 | **partial** | 非 singleton affinity は全量が `self_unattributable_total` へ入り、その量は `unexplained` から控除される。[probe:2225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2225)、[probe:2258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2258)。しかし「全区間 pin」は両端 affinity の一致だけで推定され、後から検出した reader migration を再判定へ反映しない。[probe:2207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2207)、[probe:2679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2679)、[probe:2691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2691) |
| L-3 | **closed** | `alpha` は A1 巡回から作った値で、`alpha_with_rotation` と同じ内容。旧値は `alpha_without_rotation` のみ。[probe:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:422)、[probe:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:451)、[probe:465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:465) |

### S6R3-01

- ID: **S6R3-01**
- 主張: L-2 は未閉鎖。equal-singleton affinity の両端だけを「全区間 pin」とみなし、窓内で検出した reader migration すら per-CPU self 帰属の veto に使わない。
- file:line: [probe:2215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2215)、[probe:2222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2222)、[probe:2679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2679)、[probe:2700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2700)、[test:1059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:1059)、[test:1127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:1127)
- 失敗シナリオ: self が両境界では affinity `{c0}`、窓内だけ c1 へ移って3 tick消費し `{c0}` へ戻る。全 self delta は c0 へ誤帰属され、c1 の3 tickが `unexplained` に残る。0.4秒なら7.5 tick/sとなり偽 COMPETITOR。後段の `observed_reader_migration=True` は判定を戻さない。
- 成果物影響: 正常な self 移動を競合と誤断して後続 arm を止め、A2/A3および2×3表を欠落させる。
- 強度: **強・静的反例**
- must-fix か backlog か: **must-fix**
- 最小の是正案: 判定前に readings を解析し、reader migration／singleton pinとの矛盾が一件でもあれば当該 self 全量を unattributable にする。全 self process は明示的な全窓 pin 証拠がない限り同様に扱う。equal-singleton endpoints・窓内移動・率超過を一理由にした fixture を追加する。

現 fixture は過剰決定している。`test_same_endpoint_unpinned_self...` は両端 affinity が `[0,1]` なので、途中移動を無視しても「非 singleton」だけで緑になる。[test:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:1064)。また境界順序 fixture は migration を記録する一方、3 tick / 1秒という率不足で UNRESOLVED になるため、migration veto の欠落を殺さない。[test:1131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:1131)、[test:1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:1165)。

### S6R3-02

- ID: **S6R3-02**
- 主張: `migration_detected` / `migrated_self_processes` は migration ではなく「singleton affinity でなかった self」を記録している。
- file:line: [probe:2225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2225)、[probe:2287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2287)、[probe:2700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2700)、[test:1083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:1083)
- 失敗シナリオ: A0/A4/A3 の reader が48 CPU affinityのまま同一CPUに留まっても、self deltaが正なら `migration_detected=True` になり、両 endpoint が同一CPUの recordまで `migrated_self_processes` に入る。
- 成果物影響: A4を含む生成果物が「移動あり」を偽記録し、親の因果レポートが誤った migration 根拠を採用し得る。
- 強度: **強・静的確定**
- must-fix か backlog か: **must-fix**
- 最小の是正案: 当該 alias を削除または `self_unattributable_*` に改名し、migration は独立した `observed_reader_migration` だけで表す。

445読み、anchor/cooldown、境界サンプル位置、submission/final hash束縛、観測対象 process の argv/env 非保存、pinned self のCPU別 clampには破壊を認めない。S6R2-04、S6R2-05、巡回αの空 should-reject は受容済み backlog として判定理由から除外した。静的レビューのみで、pytest・self-testは実行していない。

## 総括

- (a) **NO-GO**。
- (b1) L-2 は両端 affinity 推定のままで、窓内 migration を検出しても self 帰属を撤回しない。
- (b2) `migration_detected` が「非 singleton」を migration と偽記録し、A4/因果レポートを汚す。
- (c) 実機で最初に発火しそうなのは、短窓48回を持つ `A1_pin_sweep:competing_process_detected`（任意窓で3 tick超・6.7 tick/s超）。
- (d) 親は equal-singleton return-migration の単一理由 fixture と、migration検出後の再帰属を確認すること。
- (d) 併せて84 subwindowの実 duration、self控除、最大率、全445読み、巡回α9群/余り3、hash最終束縛を確認すること。