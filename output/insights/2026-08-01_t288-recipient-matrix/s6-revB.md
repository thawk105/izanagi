pytest・変異実走は行っていない。以下は差分・呼出経路・assert の静的追跡結果である。read-only を維持し、編集・commit はしていない。

## M01〜M15 静的判定

| 変異 | 判定 | 実際の失敗点 |
|---|---|---|
| M01 | KILL | `0.079` のままになり [test:215](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:215) の `7.9` と不一致。 |
| M02 | KILL | `0.79` となり同じく `test:215` で失敗。 |
| M03 | KILL | `0.124` となり [test:216](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:216) の `12.4` と不一致。ただし M11 と注入位置が競合する。 |
| M04 | KILL | bool guard を外すと `True → 1.0` となり [test:177](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:177)・[test:185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:185) で失敗。 |
| M05 | KILL | `nan` が通り [test:179](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:179)・`test:185` で失敗。 |
| M06 | KILL／登録不備 | `abort_rate` 側なら [test:236](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:236)、LLC 側なら [test:237](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:237) で失敗。ただし対象となる `None` が複数あり、一意の変異ではない。 |
| M07 | KILL | key 集合が [test:142](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:142) で失敗し、critic 側も [test:369](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:369) で失敗。 |
| M08 | KILL | abort が `0.124` になり [test:149](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:149) の辞書比較で失敗。 |
| M09 | KILL | planner が内部 key になり [test:350](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:350)、monkeypatch E2E は [test:435](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:435) で失敗。 |
| M10 | KILL | coder baseline の key が [test:362](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:362)、値が [test:437](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:437) で失敗。 |
| M11 | KILL／登録不備 | helper 変異なら M03 と同じ [prod:551](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:551)。caller 上書き変異なら [test:436](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:436) が失敗するが、これは別の注入位置である。 |
| M12 | KILL | `abort_rate_pct` key が critic に入り `test:369` で失敗。 |
| M13 | KILL | literal v2 を固定した [test:342](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:342) で失敗。実装定数との恒真比較ではない。 |
| M14 | KILL | planner `current_perf` の abort が `0.0` となり [test:378](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:378) で失敗。 |
| M15 | KILL／DW-M01 違反 | guarded 変異なら [test:217](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:217) で失敗。ただし単純な `llc_miss_rate * 100.0` は未観測 `None` で先に `TypeError` となり、別理由でも赤くなる。 |

named M01〜M15 の exact 解釈では生存は 0 件。ただし、以下の登録外 changed-line 変異が生存するため、「殺せない行なし」は成立しない。

## 所見

### RB-01 / blocker

世代 1 で唯一有限値を受ける critic の「値と単位」が未試験である。E2E の `_fake_drive` は metrics を一切返さず、critic assert は key 集合と全 `None` しか観測していない。

根拠: 裁定は critic を唯一の live 経路と明記している [s4-adjudication.md:9](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s4-adjudication.md:9)。`_fake_drive` は metrics 無し [test:46](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:46)、critic assert は [test:369](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:369) と [test:384](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:384) のみ。配線テストも planner/coder だけを検査している [test:435](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:435)。

生存変異:

```python
"metrics": {
    **current_metrics,
    "llc_miss_rate": (
        None
        if current_metrics["llc_miss_rate"] is None
        else current_metrics["llc_miss_rate"] * 100.0
    ),
},
```

なぜ生存するか: 全 E2E で critic の LLC 値は `None` のため、key 集合も全 `None` assert も変化しない。直接 helper test は [prod:991](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:991) の critic 配線を通らない。

成果物影響: live critic が ratio `0.124` ではなく percent `12.4` を受け、世代 1 の帰属・推奨を誤る。

### RB-02 / blocker

`contention_level` の caller 配線値が未固定である。monkeypatch は引数を記録するが、assert は metrics の key 集合しか見ていない。

根拠: 実配線は [prod:846](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:846)。spy は値を記録する [test:404](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:404) が、検査は [test:427](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:427) の metric key 集合までで `calls[0][1]` を見ない。通常 E2E も leading の key だけで値を検査しない [test:357](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:357)。

生存変異:

```python
contention_level="wrong",
```

なぜ生存するか: 通常 E2E は `"contention_level"` の存在だけを確認し、monkeypatch E2E の stub は引数値に関係なく `expected_leading` を返す。

成果物影響: planner が workload descriptor と異なる競合度を受け、workload-conditioned 提案が別条件に基づく。

### RB-03 / blocker

境界 `1.0` が未被覆であり、有限値契約を破る changed-line 変異が生存する。指定された境界のうち、被覆済みは `-0.001`、`1.5`、`0.0`、`10**400`、文字列数値で、未被覆は `1.0`、`Decimal`、numpy scalar である。

根拠: accepted 値は [test:187](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:187)、invalid 値は [test:175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:175)。契約実装は [prod:505](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:505)–[prod:512](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:512)。

生存変異:

```python
return metric if math.isfinite(metric) and metric != 1.0 else None
```

なぜ生存するか: 追加テストに正確な `1.0` はなく、他の literal もこの分岐を踏まない。`Decimal` / numpy scalar の受理・拒否も oracle が存在しない。

成果物影響: 100% abort/LLC ratio や IPC `1.0` が「未観測」へ偽装され、critic payload の証拠が消える。

### RB-04 / blocker

「report に `metrics` が無い」は dry-pass 世代だけでしか固定されておらず、同じ生成物同士の比較も独立 oracle になっていない。live outcome にだけ `generation_record["metrics"]` を復活させる変異が生存する。

根拠: absence assert は [test:313](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:313)、唯一の drive outcome は `"dry-pass"` [test:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:47)。`on_disk == report` は同じ `report` を書いて返す [prod:785](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:785)–[prod:786](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:786) もの同士の比較 [test:322](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:322) である。

生存変異:

```python
current_metrics = _metric_projection(outcome)
if outcome["outcome"] != "dry-pass":
    generation_record["metrics"] = dict(current_metrics)
```

なぜ生存するか: 全完走 E2E が dry-pass なので条件が一度も成立せず、disk/in-memory 比較も同じ誤った report を比較するだけである。

成果物影響: live report v1 に未 versioned の `metrics` が再導入され、固定済み report schema と consumer を破る。

### RB-05 / blocker

M03/M11 は同じ conversion 行を奪い合い、M06 は複数の `None`、M15 は guarded/unguarded で赤理由が変わる。したがって M01〜M15 表は 15 個の一意・単一理由変異ではなく、`DW-M01` の事前登録条件を満たさない。

根拠: 一意性・単一理由要件は [s4-adjudication.md:79](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s4-adjudication.md:79)。M03 と M11 は [s4-adjudication.md:86](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s4-adjudication.md:86)・[s4-adjudication.md:94](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s4-adjudication.md:94) だが、実装上の LLC percent 式は [prod:551](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:551) の一つだけ。M15 の単純変異は初期 `None` [prod:828](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:828) に対して `TypeError` を起こし、未観測保存テスト [test:224](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:224) でも別理由で落ちる。

成果物影響: 「15/15 kill」という検出力証拠が再現不能で、cache-miss 単位と `None` 保存の回帰を誤った kill node に帰属する。

### RB-06 / must-fix

module docstring は planner の絶対 throughput を追記した一方、coder は依然「勝ち筋値を見ずに合成」と断言しており、実際の `baseline` 配線と矛盾する。裁定が要求した module docstring 是正は未完了である。

根拠: 矛盾する記述は [p3_s4_loop.py:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_s4_loop.py:7)–[p3_s4_loop.py:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_s4_loop.py:10)、実配線は [prod:886](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:886)。裁定は coder への absolute throughput 明記まで要求している [s4-adjudication.md:58](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s4-adjudication.md:58)。

成果物影響: 監査者が coder の性能値遮断を誤認し、recipient matrix の信頼境界を過大評価する。

## 総括

**NO-GO**

- blocker: **5 件**
- 生存変異: **4 件**（M01〜M15 の exact 変異は 0 件、登録外 changed-line 変異が 4 件）
- M01〜M15 表: exact 置換は殺せるが、M03/M11・M06・M15 が一意性／単一理由性を破っており、15 個の有効な `DW-M01` 証拠ではない
- pytest: 未実行。親提示の基準線 109 passed を変異結果として流用していない