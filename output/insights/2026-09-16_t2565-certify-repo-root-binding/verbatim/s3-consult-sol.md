## 束縛の根拠

- **refuted —「投入時 cwd → `PBS_O_WORKDIR` に repo 内の実測根拠がない」**
  
  対応する記録がある。[A-1 attempt-0002 の記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2565-certify-repo-root-binding/output/insights/2026-09-07/a1-pilot-attempt-0002/README.md:70) は、投入元 `submit-tree` を cwd にして投入したと明記する。同ファイル `:140–146` には、実 job `981331.nqsv` の `job-terminal.json` から、`pbs_o_workdir` がその同じ絶対パスだったと記録されている。`docs/archive/worklog-phase3-0907-1317.md:11–16` も対応を記録している。
  
  さらに `output/env/pegasus/smoke/0:867860.nqsv/scratch.stdout:1–2` に実 job ID と `PBS_O_WORKDIR` の生値がある。ただし、この smoke 単体では投入時 cwd との対照までは示せない。

- **real — 親 brief の完了判定と予定する観測の間には差がある。**
  
  `brief.md:6` は「job 側の `PBS_O_WORKDIR` が一致することを実走テストで示す」と要求するが、`:29–32` は実投入を行わない。fake qsub で直接観測できるのは qsub プロセスの cwd までである。段 2 はこの限界を `s2-plan.md:153` で正しく認めている。
  
  **過去の scheduler 経路には実測根拠がある。本修正を通した実 scheduler の観測は未実測**、という区別が正確である。過去実測は、任意の qsub wrapper や全入力への普遍的保証ではない。

## 恒真性の検査

- **refuted — 提案された repo 外 C の負例は、設計どおりなら恒真ゲートではない。**
  
  `s2-plan.md:115,123` は fake qsub 自身の実 cwd を観測し、`R` と一致し `C` と異なることを要求する。現行 `submit_certify.sh:13–14,30` の `cd` はすべてコマンド置換内であり、親 shell の cwd は変わらない。`:223` はそのまま qsub を起動する。
  
  したがって、**`C ≠ R` として submit を `cwd=C` で起動すれば、修正前の観測は C になり、`observed_cwd == R` が赤になる。** `cwd=R` の正例だけでは、この区別はできない。

- **real — 既存 helper の流用だけでは、その負例を成立させられない。**
  
  `orchestrator/tests/test_pegasus_calibration_workload.py:1535` は `--dry-run`、`:1541–1546` は明示的な `cwd` 指定なしである。また別の job fixture は `:458` で `PBS_O_WORKDIR` を期待値から直接設定している。これらをそのまま使って束縛を証明したと扱えば、検証対象を通らない。
  
  段 2 の非 dry-run・実 cwd 観測という設計はこの問題を避けている。ただし新テストは未実装なので、**修正前に赤くなるという判定は静的判定であり、実測済みではない。**

## 親の実測値と一般化

- **real — 親 P2 の「同じ commit・clean なら照合は通る」は、十分条件として過大。段 2 の条件付き説明が正確。**
  
  job の検査は `certify_calibration.sh:240–259` にあり、commit 以外に script hash、request ID、project、queue、nodes、walltime、ratio、protocol、非 dry-run を要求する。receipt 自体も `:208–216` の固定探索先に時間内に現れる必要がある。
  
  特に具体的な反例は **submit script の所在木 S と、`--repo-root` の R が別の場合**である。既定 `JOB_SCRIPT` は `submit_certify.sh:13–15` で S から決まり、`:30` の `--repo-root` では更新されない。R と投入元 C が同じ commit・clean でも、S の script が違えば submit が記録する hash（`:117`）と job が C で採る hash（`certify_calibration.sh:227`）が不一致となり、`:243,258–259` で拒否される。

- **refuted —「同じ commit の別 checkout を既存照合が必ず排除する」**
  
  `certify_calibration.sh:240–257` に checkout パスの同一性検査はない。段 2 `:34–37` の追加条件まで満たせば、別 checkout でもこの照合は通る。

- **real — 親 brief の成果物影響も、断定が強すぎる。**
  
  `brief.md:25–27` の「provenance が偽になる」は、木の不一致だけからは導けない。job は実際にコピーした third-party source を `certify_calibration.sh:598–630` で pinned-pristine 検証し、CCBench の HEAD・clean を `:632–636` で確認する。receipt の `pinned_clean` は `:823–825` の **CCBench の属性**であり、全入力の checkout パス一致を表す field ではない。
  
  「submit が検査した staging と job の staging の同一性を証明できない」は成立するが、「それゆえ既存 receipt の値が偽」は別の立証を要する。

## 規律 2 への影響

- **refuted — 既定・絶対 job script に対する提案の subshell 変更が、既存 gate を直接緩める。**
  
  `s2-plan.md:69–79` は qsub の実行 cwd だけを変更する。receipt 不在時の停止（`certify_calibration.sh:208–216`）、dirty 拒否（`:223–225`）、source 等の照合（`:240–259`）を削除・迂回する変更は含まれていない。receipt を C に置いたまま job が R を使う場合も、R から見えなければ停止する。

- **real — 相対 job script を未処理で通すと、検査対象と投入対象の bytes が分離する。**
  
  存在確認・hash は C 基準（`submit_certify.sh:67,117`）、cwd 変更後の相対 script は R 基準で解決される。この場合、**既存 gate を備えた検査済み script を実際に投入したこと自体が保証されない。** job 内の hash 検査も、自身の実行 bytes ではなく `$TOOLS/certify_calibration.sh` を読む（`certify_calibration.sh:227`）。
  
  これは単純な `cd` 案を全入力対応として採った場合の実在する穴である。段 2 は `:99–103,144` で既に認識し、そのままの全面採用を拒否している。

## 相対 job-script の択一

- **refuted — 現行 qsub 経路と厳密な不変条件を保った、成立する第三案がある。**
  
  `C/j` と `R/j` が異なる場合、同じ相対 argv `j` を cwd=R で通常どおり解決すれば R 側になる。C 側への絶対化は `submit_certify.sh:211` の実 argv を変える。
  
  stdin／FD 経由への変更も、現在の script 引数を差し替えるなら argv 不変に反する。R 側への symlink・コピーは段 2 `:103` が除外しており、既存の異なる R/j を保った全入力対応にもならない。`PBS_O_WORKDIR` の環境上書きで逃げる案についても、scheduler が採用するという repo 内の裏付けを確認していない。
  
  よって、**提示された scope 内で成立する第三案は確認できず、段 2 の制約衝突は反証できなかった。** あらゆる実行機構について数学的に不可能とまで一般化する根拠ではない。

- **refuted —「既定 JOB_SCRIPT の早期絶対化も必ず argv を変える」**
  
  親の指摘どおり、`submit_certify.sh:13` の `pwd -P` により `SCRIPT_DIR` は絶対パスで、`:15` の既定 `JOB_SCRIPT` も既に絶対パスである。**相対値だけを絶対化する処理なら既定 argv は変わらない。**
  
  ただし明示的な相対 `--job-script`（`:32`）の argv は変わるため、親の `brief.md:12–13` と P1 `:21` の衝突は残る。既定値で成立することは全入力で成立する根拠にならない。

## 総括

- **real:** 親 P2 の十分条件と provenance への一般化は過大。根拠は `certify_calibration.sh:227–259,598–636,823–825`。
- **real:** 相対 job script に単純な cwd 変更だけを適用すると、検査した bytes と投入 bytes が分離する。根拠は `submit_certify.sh:67,117,211`、`s2-plan.md:69–73`。
- **refuted:** cwd 束縛に過去の実測根拠がない、負例が必然的に恒真、既定 script でも argv 維持が不可能、という反証は成立しない。
- **real:** fake qsub の成功を本修正の scheduler 実測と呼ぶことはできない。`brief.md:6,29–32` と `s2-plan.md:153` の証明範囲は一致していない。

静的検査のみ。実装・編集・commit・テスト実走は行っていない。