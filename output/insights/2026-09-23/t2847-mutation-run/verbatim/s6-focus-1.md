## 対応表

| 前巡の所見 | 判定 | 修正後の根拠 |
|---|---|---|
| A01 V18/V35 の宣言順 | **closed（静的）** | 両 patch とも `transaction.hh` の include 後に `Tidword` を使う helper があり、`Tidword` はグローバル名前空間で宣言される。[V18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/patches/broken-silo-no-write-tid-max.patch:9)、[V35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/patches/broken-silo-no-read-tid-max.patch:9)、[tuple.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/include/tuple.hh:12)。build 成功自体は未確認。 |
| A02 V20 の版巻き戻り | **partial** | `tid` を 29 bit 最大値から `2^28` に変え、直後の `tid++` による巻き戻りは解消した。一方、公開値を毎回同じ値にする問題が残る。[V20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/patches/broken-silo-published-version-mismatch.patch:45)。 |
| A03 V21 の証人あり検査が例外を投げる経路 | **closed（静的）** | 元の例外を保存し、trace が残る間に証人なし検査を試し、元の例外を再送出する。両検査の欄も保存する。[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/launch_mutation_run.py:247)、[結果保存](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/launch_mutation_run.py:383)。 |
| A04 / B03 test 改名 | **closed** | 旧 nodeid `exact_38` に戻し、本文の期待値 57 は維持した。[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_condition_meaning_gate.py:3706)。 |
| B01 重複する 14 件照合表 | **closed** | 個別表を削除し、在庫と登録の集合一致・patch 束縛の既存検査を残した。[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_ccbench_spawn_sites.py:2904)。 |
| B02 stock 失敗後の変異実行 | **closed** | 同 workload の stock 前提が満たされなければ、帰属不能・skip を記録して build/run を飛ばす。stock 不成立なら最終 rc も 1 となる。[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/launch_mutation_run.py:353)。 |
| 焦点走: screening driver の `KeyError` | **closed（静的）** | 14 macro をすべて既定値 0 で追加した。[screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/screening_driver.py:93)。 |
| 焦点走: condition meaning gate の件数 | **closed（静的）** | 既存 24 cache route ＋既存 19 flags route ＋新規 14 flags route ＝ flags 33、総数 57。[登録表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/condition_meaning_gate.py:261)、[期待値](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_condition_meaning_gate.py:3582)。 |
| 焦点走: spawn sites の赤 2 件 | **closed（静的）** | 分類は登録 macro と sink の直積。総数 43→57 のうち、s1 は covered 4 のままなので unreachable 39→53、s8b は covered 43→57。certify sink は deferred 14 のままなので unreachable 29→43。[分類ロジック](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_ccbench_spawn_sites.py:2828)、[期待値](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_ccbench_spawn_sites.py:3563)。 |

件数固定の変更はすべて登録 14 件による増分と一致する。fix 差分に、登録と無関係な期待値の緩和・skip・削除は見当たらない。

## 新しい所見

- **F01・must-fix・[V20:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/patches/broken-silo-published-version-mismatch.patch:48)** — `epoch=UINT32_MAX, tid=2^28` を全 UPDATE で再利用する。最初の公開値を読んだ同 key の次の更新では、[TID 生成](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:567)がその値の `tid+1` を C/W に出すが、tuple には再び元の固定値を公開する。29 bit の巻き戻りは当面起きず、通常の C/W が固定値そのものに到達する経路も見当たらない。ただし公開版の重複が orphan 以外の版異常として混ざる。**修正案:** 公開値を更新ごとに一意にし、後続の TID 生成と衝突しない根拠を示す。**成果物影響:** V20 の I や他 counter を、狙った孤児版だけに帰属できない。

## 未確認点

テスト・build・実走は指示どおり行っていない。V18/V35 の有効 macro build、焦点走 4 件の実際の緑化、V21 の両 verifier の argv・rc・結果、V20 の発火と anomaly counter は親の実測が必要。

## 総括

**NO-GO。** 件数と起動器の修正は静的には整合するが、V20 の固定公開版の再利用が事前登録した単一機構の帰属を損なう。