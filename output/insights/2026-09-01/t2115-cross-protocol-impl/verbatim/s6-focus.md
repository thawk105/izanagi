## 対応表

| 項目 | 判定 | 根拠 |
|---|---|---|
| P-1 | closed | fixture は実際の `calibration/` 配下へ既存 JSON を置き、`FileExistsError` と bytes 保持を直接検査する。[test_between_run_floor.py:191](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:191) writer 側も事前検査と `"x"` 作成を使う。[between_run_floor.py:258](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:258) |
| P-2 | closed | `ccbench_add_protocol(... SOURCES ...)` の列挙 source だけを解決し、CMakeLists 欠落、SOURCES 欠落、非 source、存在しない file は偽へ倒す。[between_run_floor.py:111](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:111) 未列挙 decoy と列挙 source の正負例も機構を直接通る。[test_between_run_floor.py:277](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:277) |
| P-3 | partial | 通常の行・ブロックコメントと単純な literal `#if 0` は除去される。[between_run_floor.py:161](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:161) ただし `#if 0` 除去 regex は入れ子を数えず最初の `#endif` で終了するため、入れ子条件の後ろにある hook が残る。追加負例は単純な配置だけである。[test_between_run_floor.py:324](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:324) |
| P-4 | closed | body を整数化し、重複を拒否した後、`Genome.canonical()` との完全一致を要求する。[genome.py:121](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/genome.py:121) 指定された malformed 5 形は floor と WAL の双方に負例がある。[test_layer3_report.py:2926](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_layer3_report.py:2926) |
| P-5 | closed | JSON と Markdown の内容を両方構築してから作成し、2 file 目の失敗時は作成済み file を逆順に削除する。[between_run_floor.py:258](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:258) Markdown 作成だけを失敗させ、directory が空へ戻ることを検査する。[test_between_run_floor.py:219](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:219) |
| P-6 | closed | canonical な wrong-protocol floor をちょうど 1 件だけ置く負例が追加された。[test_screening_driver.py:250](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_screening_driver.py:250) protocol 比較を外すと `matches` は 1 件となり、後段の一意性検査では拒否されない。[screening_driver.py:150](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/screening_driver.py:150) |

## 所見

### 1. literal `#if 0` の除去が入れ子構造を処理しない

- 主張: P-3 は通常例を閉じたが、dead branch にだけ存在する hook をなお受理できる。
- 根拠: `#if 0` から最初の `#endif` までを非貪欲 regex で除くため、`#if 0` 内に別の `#if ... #endif` があると、外側の dead branch の後半が残る。[between_run_floor.py:161](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:161) 例えば active include・別の `#if TRACE` と、`#if 0 / #if TRACE / #endif / izanagi_trace::emit_abort(...) / #endif` を同一 file に置くと三条件が残る。現在の負例はこの入れ子を含まない。[test_between_run_floor.py:348](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:348)
- 成果物影響 1 行: 実際には hookless な compiled source が admission を通り、根拠のない between-run floor を公開できる。
- 判定: must-fix
- 確信度: 高

### 2. 禁止範囲と commit の独立監査証跡が不足する

- 主張: tracked な全差分は許可された production/test 16 file に限られるが、`output/` の完全不接触と commit の不存在までは射影資料から独立確認できない。
- 根拠: [author-diff.txt:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/author-diff.txt:1) の file boundary には docs、`output/`、submodule、`tools/`、`hooks/` がない。一方、fix 報告自身は `output/pegasus-dispatch/` に receipt 2 件が生成されたと記す。[fix1.md:90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/fix1.md:90) commit 不作成は同報告の自己申告だけである。[fix1.md:99](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/fix1.md:99)
- 成果物影響 1 行: tracked 実装差分への影響はないが、「output 無変更・commit 無し」を本レビューの独立確認済み事実にはできない。
- 判定: nit
- 確信度: 高（監査限界）、中（receipt の現在状態）

追加負例について、現行コード上で別の拒否条件が同時発火する恒真・過剰決定は見つからなかった。P-2/P-3/P-4 の変更はいずれも従来の受理集合を狭めており、fix 自体による拡大も見つからない。P-3 の所見は以前からあった dead-branch 穴の閉じ残しであり、新しい回帰ではない。

## 変異の単一理由性

| 変異 | 判定 | 根拠 |
|---|---|---|
| M1 | 成立 | 単独の wrong-protocol floor は schema、workload、canonical genome、`between_run.cv` を満たす。protocol 比較だけが `matches` への追加を止め、比較除去後は 1 件となるため一意性拒否も発火しない。[test_screening_driver.py:250](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_screening_driver.py:250) |
| M2 | 成立 | Layer 3 の単独 wrong-protocol floor は records、threads、workload が一致する。照合条件から protocol だけを外すと唯一の match となり、screening consumer はこの経路に参加しない。[layer3_report.py:419](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/layer3_report.py:419) |
| M3 | 成立 | current mocc は CLI と `BASELINES` には受理され、trace 述語で build 前に止まる。負例では後段の evidence、build、measure、write を成功 stub にしており、述語を恒真化すると他の拒否層はない。[between_run_floor.py:111](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:111) |
| M4 | 成立 | `space_for("mocc")` は `SPACES` の直接 lookup であり、entry 除去前後に別の受理・拒否層がない。[genome.py:111](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/genome.py:111)、[test_campaign.py:227](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_campaign.py:227) |

## 実装のどこが正しいか

- silo baseline の flags は従来値のままで、`BASELINE` compatibility 名も silo を指す。[between_run_floor.py:58](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:58)
- silo では protocol suffix が空なので既存 stem を維持し、mocc だけ `_mocc` を加える。[between_run_floor.py:250](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:250)
- strict parser は既存 canonical silo genome を引き続き受理する。親の実走済み 4 direct file が赤なしであるため、既存 4 floor JSON の可読性回帰も反証された。
- 3 caller は固定文字列ではなく実 baseline genome の protocol を転送する。[backoff_sweep.py:166](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/backoff_sweep.py:166)、[s6_sort_sweep.py:279](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/s6_sort_sweep.py:279)、[s8a_trigger_sweep.py:379](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/s8a_trigger_sweep.py:379)
- Layer 3 は `(protocol, records, threads, workload)` の 4 field を同一条件で照合する。[layer3_report.py:419](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/layer3_report.py:419)
- genome 欠落の within-run record は silo にだけ帰属し、採用時に `genome-absent-legacy-record` を出す。[layer3_report.py:398](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/layer3_report.py:398)
- 裁定が直さないとした TOCTOU、共通 header include の不受理、焦点走集合の拡張には手を入れていない。
- 私自身は pytest を実走していない。実測については親が提示した 621 passed / 3 skipped と consumer 117 passed を所与にした。

## 総括

P-1、P-2、P-4、P-5、P-6 は closed、P-3 は partial。  
回帰、fix による受理集合の拡大、追加負例の過剰決定は見つからない。  
M1〜M4 の単一理由性はすべて成立する。  
残る must-fix は、入れ子を持つ literal `#if 0` の除去漏れ 1 件。  
tracked 禁止範囲差分はないが、output receipt と commit 状態は射影だけでは独立確定できない。