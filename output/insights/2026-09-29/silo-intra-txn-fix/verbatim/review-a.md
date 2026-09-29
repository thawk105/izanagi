## 所見

- **R01｜must-fix｜[run_ci_then_judge.sh:17](/work/1/SFC/tanab/tmp/silo-intra-txn-fix-2026-09-29/wave/author1-out/scripts/run_ci_then_judge.sh:17)**
  直接起動する `run_judge_v2.sh` の退避物は mode `644`。放置すると CI 後の D297 が実行されず、4 比較の結果が得られない。**推奨:** 判定 script に実行権限を付けてから job に渡す。

- **R02｜must-fix｜[launch_gate_liveness_v2.py:40](/work/1/SFC/tanab/tmp/silo-intra-txn-fix-2026-09-29/wave/author1-out/scripts/launch_gate_liveness_v2.py:40)**
  対照 F に D2b (i) と (ii) の**各々**で違反 ≥1 を要求している。R5 の期待は両者の**合計** ≥1。放置すると裁定を満たす対照走行も rc=4 になり、trace の読みが変わる。**推奨:** 対照の違反条件を `i.count + ii.count >= 1` にする。

- **R03｜must-fix｜[format-ci.sh:23](/work/1/SFC/tanab/tmp/silo-intra-txn-fix-2026-09-29/wave/format-ci.sh:23)、[inv-run.sh:36](/work/1/SFC/tanab/tmp/silo-intra-txn-fix-2026-09-29/wave/inv-run.sh:36)**
  両 script とも検査の直後に `echo` するため、検査が失敗しても最終 `*.done` は rc=0 になり得る。放置すると CI 緑や棚卸し完了の記録が誤る。**推奨:** 採取した各検査 rc から最終 rc を決める。

- **R04｜should｜[format-ci.sh:17](/work/1/SFC/tanab/tmp/silo-intra-txn-fix-2026-09-29/wave/format-ci.sh:17)**
  既存の `$J/fcheck` を再利用し、checkout 後の porcelain 件数を表示するだけで clean を要求しない。放置すると R7 の「各 clean checkout の全対象 file」という CI 証拠にならない場合がある。**推奨:** 各検査前に checkout の clean 状態を必須条件にする。

- **R05｜should｜[inventory_silo_patches.py:43](/work/1/SFC/tanab/tmp/silo-intra-txn-fix-2026-09-29/wave/author1-out/scripts/inventory_silo_patches.py:43)**
  trigger 系の前提出典が driver の patch 名定数の行だけで、実際の重ね順を示す行ではない。放置すると棚卸し表の前提の根拠を読者が追認できない。**推奨:** 表の出典を実際の適用順を示す driver または README の箇所へ差し替える。

## 確認して問題なかった点

修正 file と `clone-diff.patch` は修正案と同じ意味の 2 hunk で、`#line` は不変。commit message の実測件数と未修正範囲も一次資料に合う。計装の Q、V、RMW 刻印は指定位置にあり、追加の取引処理は `#if TRACE` 内。`check_instr_v2.py` の除去比較は恒真ではない。

起動器の pin・clean・単独性・空き容量・compute site、bundle 親子と変更 path、判定器の checkout 指定、trace 保存は残っている。D297 の二組の引数と照合、CI build の親照合、棚卸しの 44 本列挙・素の `git apply`・前提土台との inert 比較も静的には整合する。計算 job と親の棚卸しの実走結果は、今回の判定には含めていない。

## 総括

**NO-GO**。R01〜R03 を直し、計算 job と親の棚卸しを実走してから結果を採用する。