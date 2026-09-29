## 対応表

| 所見 | 判定・根拠 | 放置時に成果物がどう変わるか |
|---|---|---|
| G1／F3 | **closed（静的検査）**。[patch:162–175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:162)、[patch:193–246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:193)。選択版を最初に pending と見た場合、待機本体を通ればその直後に、待機前に確定すれば走査後に再観測する。aborted 後に次の版を選ぶ経路も追跡した。確定版の記録でフラグを消すため二重計数せず、`ldAcqNext()` の追加もない。 | この競合による先頭 K 候補と `vlife_selected_upper` の欠落は解消。 |
| G2／F4 | **closed（既読集合について）**。[patch:245–285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:245)。nullptr は登録前に戻り、deleted は判定後に戻る。L・U・`vlife_reads_` は成功して `read_set_` に登録した後だけ更新される。 | 失敗 read が後続 read の既読数・L・U を変える問題は解消。ただし下記の新所見が残る。 |
| G3／F6 | **closed（静的検査）**。[measure:310–347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:310)、[smoke:387–424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:387)。両関数とも N を 1M→2M→4M の順に調べ、`maxrss_kb × 1024 > 4 × l3_bytes` を満たす最小 N、該当なしなら 1M とする。measure は witness、短い走、全 probe の成功と選定値の一致も要求する。 | smoke の自己申告 N だけで正式 measure を始める経路は解消。 |
| F1・F2 | **F1 closed、F2 partial**。[patch:265–287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:265)、[test:146–166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:146)、[driver:440–453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:440)。fix 2 の二枝とも、stock の deleted 判定を `#line 121`、続く位置を `#line 127` に戻す。ファイル名付き `#line` は増えていない。実 binary 比較は結果未着。 | 既定 build の inert 判定は `.text`／`.rodata` の smoke 結果で確定する。 |
| F5・F7・F8・F9・B2・P1 | **closed を維持**。fix 2 は該当する作図・時間 bucket・較正前の単独性確認を変更していない。[変更対象](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:393)、[作図:130–189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:130)。 | 前回 closed とした成果物への新たな退行は差分上認めない。 |

## 新たな所見

- **must-fix:** deleted で失敗する read でも、deleted 判定より前に `deep`・`deep_read_zero`・`candidate`・`candidate_read_zero` を増やす。[patch:247–269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:247)。裁定が失敗 read に許した位置・hop 以外も図 2 の分母・分子へ入り、楽観的候補率を変える。[plot:148–163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:148)
- **nit:** fix 2 の patch 差分には空白行の trailing whitespace が 2 箇所ある。[patch:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:284)、[patch:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:288)。計測値への影響はない。

既存 test の期待値は変更されず、smoke fixture は新しい検証条件に合わせて拡張された。[test:169–231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:169)。条件 ID の受理規則も差分外である。[driver:58–67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:58)。受理集合の変化は G3 の smoke 検証強化に沿う。

## 変異の被覆

| 変異 | 単一理由で殺す test nodeid |
|---|---|
| MUT-1 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_json_line_contract` |
| MUT-2 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_k_boundary_and_condition_subset`（patch 文字列の境界検査） |
| MUT-3 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_patch_default_preprocess_matches_stock` |
| MUT-4 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_k_boundary_and_condition_subset` |
| MUT-5 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_worker_sum_and_readonly_denominator` |
| MUT-6 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_patch_default_preprocess_matches_stock` |
| MUT-7 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_smoke_identity_binds_records` |
| MUT-8 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_smoke_recomputes_calibration_and_requires_success` |

MUT-8 は自己申告 4M に対し probe から再計算した 2M を使う拒否例で殺す。[test:207–223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:207)。この巡では変異を実走していない。

## 総括

**NO-GO。** 残る must-fix は、deleted で失敗した read を候補率の計数から除外すること。修正後も、既定 build の inert 判定には待ち行列中の実 binary smoke 結果が必要。