## pin 閉包

| 対象 | 実物の pin | 必要な扱い | 段 2 との差 |
|---|---|---|---|
| submitter の公開契約 | usage、既定値、3 値 gate、exact error (`tools/pegasus/submit_certify.sh:8,18,40-42`) | usage、gate、error を 5 値化。既定 rr50 は不変 | 列挙済み |
| submitter の静的 test | usage exact、既定 rr50、20/50/80 literal、export、receipt (`orchestrator/tests/test_pegasus_calibration_workload.py:35-62`) | 5/95 を加え、両 shell から抽出した集合を exact 5 要素で固定。既定 pin は残す | 概ね列挙済み。ただし既定 rr50 の不変 pin は明示不足 |
| job body の gate | 3 値、exact error、変数束縛 (`tools/pegasus/certify_calibration.sh:154-161`) | 値と error だけ更新。位置は維持 | 値は列挙済み。移動案は後述のとおり不要 |
| job body の伝播 | receipt 再照合、workload argv、job-result (`orchestrator/tests/test_pegasus_calibration_workload.py:65-82`) | 現状は許可集合自体を pin していないため、段 2 の exact 集合検査追加は妥当 | 列挙済み |
| rr50 既定経路 | shell fixture と calibrate argv の完全一致 (`orchestrator/tests/test_pegasus_calibration_workload.py:171-195,318-345`) | 変更不可 | 段 2 の pin 閉包から欠落 |
| 旧 95 負例 | rc=2、exact error、attempts 不在 (`orchestrator/tests/test_pegasus_calibration_workload.py:429-446`) | 95 を正例へ移し、未登録値の parameterized 負例へ置換 | 列挙済み |
| dry-run fixture | no-arg の receipt、export、qsub argv が rr50 exact (`orchestrator/tests/test_pegasus_calibration_workload.py:467-590`) | rratio 引数を追加しても no-arg rr50 の既存 pin を残す | helper 変更は列挙済みだが既存 rr50 pin の全箇所は未列挙 |
| docs と docs test | 20/80 例を test が pin (`orchestrator/tests/test_pegasus_calibration_workload.py:639-647`)。README は旧 whitelist と workload 名も断定 (`tools/pegasus/README.md:125-140,157-170`) | 5/95 例追加だけでなく、`20 / 50 / 80` と `rr{20|50|80}` も 5 値へ更新 | 段 2 は例追加だけを書き、README:132,169 の旧閉集合を名指ししていない |
| runtime 全体 hash | submitter が job script 全 bytes の SHA-256 を receipt に入れ、job が PBS_O_WORKDIR 側の script と再照合 (`tools/pegasus/submit_certify.sh:101,143-181,232-262`; `tools/pegasus/certify_calibration.sh:188-228`) | submit tree、qsub script、PBS_O_WORKDIR の script bytes を一致させる | pin 閉包表から欠落。別 submit-tree 運用では重要 |
| admission pin | submitter は local-ok、job body は dispatch-required (`tools/pegasus/admission_registry.json:34-38,334-338`)。登録簿全 entry × 4 field が literal golden (`orchestrator/tests/test_hooks.py:3032-3546,3947-3987`) | registry を触らなければ変更不要 | 段 2 の閉包から欠落。ただし現差分では赤を生まない |
| path spelling pin | submitter の `./`、二重 slash、末尾 slash、絶対 path、`bash` 経由を許可 (`orchestrator/tests/test_hooks.py:3591-3596,4284-4299`) | 変更不要 | 未列挙 |
| runbook | ratio/usage の pin はない。path/class 投影だけ (`docs/pegasus-runbook.md:495-574`) | ratio 拡張による更新不要 | 段 2 の判断が正しい |

射影内には、shell や README の固定 SHA、固定行番号を使う test はありません。行番号は brief／plan の説明アンカーだけです。固定 hash は上表の実行時 job-script binding、登録簿は canonical bytes と literal golden です。

[1] README の変更範囲は例追加だけでは閉じない / `tools/pegasus/README.md:132,169` に旧 3 値集合が残り、`同:17,137-140` も rr80/rr20 専用の記述である / 5/95 の例だけ足すと sanctioned argv と説明上の fixed whitelist が矛盾する。少なくとも 132 と 169 は must-fix、17 と 137-140 も同じ節で整合させるべき / 自己判定 (real)

[2] 95 負例の差替えは検出力を落とさない / 現 test は 95 という 1 点の拒否と副作用不在しか検査していない (`orchestrator/tests/test_pegasus_calibration_workload.py:429-446`)。段 2 は両 gate の exact 5 要素集合と複数の未登録値を検査する (`s2-plan-out.md:29-32,58-62`) / 95 を正例へ移し、0・51・100・空白付き値などへ負例を広げれば、不正な集合拡張への検出力はむしろ上がる。既存 rr50 pin を残すことが条件 / 自己判定 (refuted)

[3] job body gate を副作用前へ移す必要はなく、移動は順序意味論を壊す / 現順序は PBS identity、create-only TMPDIR、repo staging、failure writer、policy、nonce、ratio である (`tools/pegasus/certify_calibration.sh:15-45,47-113,150-161`) / line 15 直後へ移すと invalid ratio が structured `failure.json` を残せず、policy 欠落や unsafe nonce と同時に不正な場合の失敗優先順位も変わる。今回の sanctioned submitter は invalid ratio を qsub 前に拒否するため実利がない / 自己判定 (refuted)

[4] 同じ submit tree の 2 job は runbook 上「独立」ではない / 両 job は同じ `external/ccbench` を base にして、その共通 gitdirへ `git worktree add/remove` する (`tools/pegasus/certify_calibration.sh:535-545,899-902`)。runbook は作業木・lock・read/write 集合を共有する job の並走を禁止する (`docs/pegasus-runbook.md:1344-1377`) / rr5 と rr95 を同じ wave treeから並行投入すると、CCBench worktree 管理 metadata の writer を共有する。並行を維持するなら submodule の `--absolute-git-dir` が異なる submit tree が必要。そうしないなら同じ wave treeで直列が正しい / 自己判定 (real)

[5] `/scr` worktree path と cleanup target の直接衝突はない / TMPDIR は PBS_JOBID ごとで、BUILD_SOURCE はその配下、remove もその exact pathだけを対象にする (`tools/pegasus/certify_calibration.sh:27-31,541-545,899-902`) / 異なる job IDなら一方の cleanup が他方の `/scr/.../ccbench-source` を直接 remove する経路はない。段 2 の「cleanup 干渉」は具体的 path 衝突としては過大。ただし共通 gitdir metadata の共有は [4] のとおり残る / 自己判定 (refuted)

[6] 別 submit-tree での並行投入は wave-local 成果物契約と両立しない / submitter の `--repo-root` は source identity、policy、receipt root を選ぶが、qsub の作業 directory は変更しない (`tools/pegasus/submit_certify.sh:30,56-110,189-195`)。job body は `PBS_O_WORKDIR` を REPO_ROOT として、その直下へ attempts/job-staging を置く (`tools/pegasus/certify_calibration.sh:33-45`) / 各 submit-treeへ `cd` して投入すれば accepted record は各 tree の `output/.../registered` へ着地し、この wave の registered には現れない。逆に wave cwdから別 treeを `--repo-root` にすると receipt が別 treeへ書かれ、jobは wave側で receiptを待って失敗する。現実的な解は wave treeから 2 jobを直列投入すること / 自己判定 (real)

[7] 段 2 の投入 command は cwd 前提が欠けている / `qsub` 前に `cd "$REPO_ROOT"` がなく、job側の `REPO_ROOT=$(cd "$PBS_O_WORKDIR"...)` は command substitution 内だけである (`tools/pegasus/submit_certify.sh:195`; `tools/pegasus/certify_calibration.sh:33`) / 絶対 pathの submitterと `--repo-root` を指定しても、呼出し cwdが dev-wave-jobsや別 checkoutなら PBS_O_WORKDIR はそこになる。policy欠落、receipt不在、または別 repoへの publishになる。投入手順は明示的に `cd <この wave worktree> && tools/pegasus/submit_certify.sh ...` とする必要がある / 自己判定 (real)

[8] preflight の rc 成功だけでは queue 使用可能性を満たさない / submitter は 4 commandを全捕獲するが、判定するのは各 rcだけである (`tools/pegasus/submit_certify.sh:119-187`)。runbook は queue が DIS/INA なら投入しないと定める (`docs/pegasus-runbook.md:343-352`) / `qstat -Q` が rc=0でも対象 queueが停止していれば、段 2 の「4 captureが成功」を満たしながら実走しない。新 gateは scope外でよく、親が保存された qstat本文または queue_state を投入直前に確認すれば足りる / 自己判定 (real)

[9] scheduler出力、create-only staging、現行 request ID形式は投入を止めない / 現 worktreeの git common dirは `/work/1/SFC/tanab/izanagi/.git` なので出力先は repo外の `/work/1/SFC/tanab/izanagi-job-evidence/calibration-certify` となり、submitterが `mkdir -p` する (`tools/pegasus/submit_certify.sh:98-117,193-195`)。parserは runbookの `Request <ID> submitted` 形式に一致する (`同:215-229`; `docs/pegasus-runbook.md:114-117`) / 現行形式なら request IDは取得できる。形式 drift時だけ、qsub成功後に receiptが作れず、jobが60秒後に失敗するため raw `qsub.stdout` から回収が必要 / 自己判定 (refuted)

[10] capability predicateを 5/95へ広げる必要性は示されない / job bodyは選択 ratioをそのまま workloadへ渡し、calibrator rcだけで成功を判定する (`tools/pegasus/certify_calibration.sh:843-897`)。親 brief自身が、当該 predicateの集合外である rr50に accepted recordが2件あるとする (`brief.md:4-10`) / capability不発が certification admissionや accepted条件なら既存 rr50 acceptedと両立しない。したがって変更不要という方向は整合する / 自己判定 (refuted)

[11] ただし CLI capability と publish の独立検証は射影不足 / 依頼が実物確認を要求する `orchestrator/calibrator/cli.py:913,1025`、`sweep.py`、`report.py`、`schema_v2.py` は必読射影に含まれていない。確認できるのは段 2 の引用 (`s2-plan-out.md:35-39,65`) と wrapper側だけ / ratio別 capabilityが publish metadataへ影響する変更や、相対 publish rootの決定方法があっても、この consultは実物から否定できない。親はこれを「独立に確認済み」と数えてはならない / 自己判定 (real)

[12] F660の実効ブロックは起きないが、親の「main側登録簿」という説明は誤り / この checkoutの registryは submitterを local-ok、job bodyを dispatch-requiredとする (`tools/pegasus/admission_registry.json:34-38,334-338`)。testは current `_REPO` から guardとloaderを読み (`orchestrator/tests/test_hooks.py:27-65`)、dot・絶対path等を同じ entryへ正規化する (`同:3591-3596`)。Codex trustも hooks.jsonの絶対path単位である (`hooks/README.md:35-67`) / 既存 submitter bytesだけの変更は path/class admissionを変えず、qsub経由は通る。一方 registry fieldを変更すれば literal goldenが赤になる。さらに local-okは `legacy-admitted (未実測)` であり、安全実測済みという一般化は不可 (`docs/pegasus-runbook.md:456-494,558`) / 自己判定 (real)

[13] 親 briefには A4以外にも実アンカーと成果物契約の誤りがある / A1は gateを42-45行とするが実体は40-43行 (`brief.md:27`; `tools/pegasus/submit_certify.sh:40-43`)。A4は docs runbookではなく tools README (`brief.md:30`; `orchestrator/tests/test_pegasus_calibration_workload.py:22,639-647`)。briefは JSONとmd双方を registered配下とするが、wrapperにはmdを移す処理もregistered実在の後検査もない (`brief.md:46`; `tools/pegasus/certify_calibration.sh:868-903`) / 古いアンカーを実装者が使うと誤ファイルを編集する。mdまで completion条件にすると、JSONだけを自動登録する既存経路では永遠に完了しない。後者の最終確認には [11] の CLI射影追加が必要 / 自己判定 (real)

静的確認では、現在の wave treeは top-level `output` 除外の submitter述語で clean、CCBench HEADは superproject gitlinkと一致し、submodule gitdirはこの worktree専用です。pytestや実投入は実行していません。

## 総括

最重は、別 submit-tree並行化が accepted recordをこの waveの registeredへ着地させない点である。  
次に、`--repo-root` は PBS_O_WORKDIRを変えないため、投入前の明示的な `cd` が必須である。  
実機取得はこの wave treeから rr95、rr5を直列投入するのが、現行コードで成果物契約まで閉じる手順である。  
READMEの旧 whitelist断定も例追加と同時に全箇所更新する必要がある。