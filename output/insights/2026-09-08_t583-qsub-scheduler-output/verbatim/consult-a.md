## 所見 1: プランは D1291 をなお三機構ぶん超過する

根拠 (`brief.md:12-15,75-79,90-96`; `plan.md:21-75,97-99,202-211`): D1291 は「投入時の引数 1 箇所」だけを変更し、仮想リスク向け gate を足さない裁定である。各要素の判定は次のとおり。

| 要素 | 判定 |
|---|---|
| `qsub_cmd` への `-o <file> -e <file>` | 裁定内 |
| 公開 CLI `--scheduler-output-root` | 裁定外。プランが削った点への攻撃は失敗 |
| repo/common-repo containment 判定 | 裁定外 |
| `realpath -m/-e`、`mkdir -p -m 0700` による provision | 裁定外 |
| common-dir、絶対性、containment、provision 用の新規 error message | 裁定外 |

影響: プランは公開 CLI の追加こそ退けたが、投入前の受理集合、dry-run の副作用、preflight へ到達する条件を新しい gate と directory 作成で変更する。「他の挙動は変えない」と両立しない。

推奨 (削る): containment、provision、新規 error message、repo 内候補を rc=2 で拒否するテストを削る。最小負例は既存 `--repo-root` と `--dry-run` で表示された qsub argv を解析し、`-o/-e` が存在し、絶対 file path で、repo 配下でないことを否定形で検査すれば足りる。親が実在確認した既存 `izanagi-job-evidence` 直下へ nonce 付き leaf を向ければ、新しい subdirectory の provision も不要である。

## 所見 2: 親 brief の「qsub の cwd = repo root」は code から導けない

根拠 (`brief.md:19-21`; `addendum.md:7-18`; `tools/pegasus/submit_certify.sh:175-210`): `submit_certify.sh` は qsub 実行前に `cd "$REPO_ROOT"` していない。したがって submit directory は呼出し側の cwd であり、repo root になるのは運用時にそこで起動した場合だけである。addendum の `job-staging/.../*.o<ID>` は、同じ節が「手で移していた」と説明するため、元の生成場所の証拠でもない。対照的に B10 は `cd "$REPO_ROOT"` を明記している (`submit_b10_backoff_shape.sh:245-247`)。

影響: brief は個別の実運用を script の一般的性質へ誤って一般化している。D1291 の修正自体は cwd 非依存の `-o/-e` によって有効だが、brief の原因説明はそのまま正本化できない。

推奨 (削る): cwd を固定する追加変更や gate は足さない。「実測した呼出しでは repo root だった」に前提を狭める。

## 所見 3: `submit_floor.sh` は scheduler 出力を repo 外へ置く precedent ではない

根拠 (`brief.md:26-44`; `plan.md:77,95,235-239`; `submit_b10_backoff_shape.sh:108-171,228-247`; `submit_floor.sh:99-135,227-258,287-333,562-565,639-666`): B10 は submission record 全体を repo 外の durable root に作り、その中へ scheduler stdout/stderr を置く。一方 floor は untracked `output/` を明示的に許す clean 判定を持ち、scheduler 出力も repo 内 `output/.../submissions/<nonce>/` に置く。floor の common-dir 由来 repo 外 root は job evidence 用であって、scheduler stdout/stderr 用ではない。

影響: brief の「3 箇所で同一 precedent」は path 導出式についてだけ成立し、scheduler 出力の配置 precedent としては B10 だけである。`floor_campaign.sh` は射影対象に無いため、その 3 件目も本相談では検証不能である。floor 側を採ると dirty gate は `output/` 除外により通り得るが、D1291 と runbook §8 の repo 外要件が破れる。

推奨 (採用): 配置の選択は B10 側。ただし B10 の durable-root CLI、provision、symlink gate まで移植する根拠にはしない。

## 所見 4: common-dir の二つ上という導出は submodule で repo 外を保証しない

根拠 (`plan.md:26-45,77-79,151-180`; `submit_certify.sh:12-14,24-34`): 現 worktreeでの実測は、top-level が `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t583-qsub-oe`、common dir が `/work/1/SFC/tanab/izanagi/.git` であり、計画式は `/work/1/SFC/tanab/izanagi-job-evidence/calibration-certify` を指す。この配置への攻撃は失敗した。

一方、経路別には次になる。

- cwd が submodule 内でも `--repo-root` が無ければ、cwd は参照せず script の所在から同じ top-level repo を使う。
- 通常の standalone `--repo-root /x/repo` は common dir `/x/repo/.git` から `/x/izanagi-job-evidence/...` を指す。
- plan の separate-git-dir fixture は `/x/repo/.git-store/.git` から `/x/repo/izanagi-job-evidence/...` を導き、追加 gate が拒否する。
- submodule の common dir は通常 `/super/.git/modules/<name>` で `/.git` 終端ではない。`GIT_COMMON_REPO=${GIT_COMMON_DIR%/.git}` は何も除かず、二つ上から作る出力先は superproject の `.git` または `.git/modules` 内になる。submodule worktree と module dirだけを比較する plan の判定を通過し得る。

影響: brief の「Git common dir 起点なら worktree で安全」は現配置では正しいが、submodule まで一般化すると誤りである。「絶対かつ repo 外」の不変条件を plan は一般には守れない。

推奨 (不採用): 本 wave で submodule 一般対応や追加 gate を設計しない。対応範囲を現在の top-level checkout/linked worktree に限定し、一般的な安全導出だという主張を削る。submodule 対応が必要なら別裁定である。

## 所見 5: flat な共有 root には別 wave の leaf と同一 path になる経路がある

根拠 (`brief.md:84-89`; `plan.md:83-95,204-209`; `submit_certify.sh:90-104`; `submit_b10_backoff_shape.sh:165-171,232-234`): linked worktree は同じ common dir から同じ `calibration-certify` root を導く。plan はその直下に nonce 名の二 leaf を置くが、共有 root 側で create-only reservation を行わない。既存 `SUBMISSION_DIR` の create-only は各 worktree の `output/` 内であり、共有 scheduler root を予約しない。B10 は逆に repo 外の nonce directory 自体を create-only で確保している。

影響: 二つの wave が同じ nonce を生成した場合、または同名 leaf が既に存在する場合、同一 scheduler path を指す。128-bit nonce により偶発確率は低いが、brief の「NONCE で衝突しない」は絶対的な不変条件ではない。

推奨 (不採用): この wave で予約機構や新 gate は足さない。上書き不能という主張だけを削り、残余として扱う。

## 所見 6: 不変条件の大半は保てるが、逐語検査と repo 外保証の主張が過大である

根拠 (`brief.md:63-73`; `plan.md:190-200`; `submit_certify.sh:5-10,36-39,84-88,115-128,130-176,181-195,213-242`; `test_pegasus_calibration_workload.py:27-38`):

| 不変条件 | 検査結果 |
|---|---|
| `usage()` の逐語行 | plan が行 5-10 を編集しないため実装上は保てる。ただし既存 test は substring だけを検査し、空白を逐語固定していない。brief の説明は誤り |
| `':(exclude)output'` | 対象外にしており保てる。攻撃は失敗 |
| RRATIO 3 値、export | 対象外にしており保てる。攻撃は失敗 |
| receipt schema/field | Python payload を変更せず scheduler path も追加しないため保てる。攻撃は失敗 |
| preflight 4 capture の順序 | 4 command の順序と qsub 前停止は保てる。ただし新 provision failure は preflight 自体へ到達させず、以前に無い副作用と早期終了を作る |
| `-o/-e` が file path | nonce 付き leaf なので保てる。攻撃は失敗 |
| 絶対かつ repo 外 | 現 worktreeでは成立するが、submodule common-dir では不成立 |
| `--dry-run` が qsub を実行しない | 分岐を変更しないので静的には成立する。攻撃は失敗 |
| gate を緩めない | 緩めてはいないが、新 gate の追加自体が scope 外 |

影響: plan の「全不変条件を保全」は、top-level repo という未記載前提を置いた場合だけ成立する。また既存 test の検出力を「逐語」と過大評価している。

推奨 (削る): root gate と provision を削り、既存ブロックを編集しないこと自体で usage、dirty gate、receipt、preflight を保つ。substring test を逐語保証の証拠として報告しない。

## 所見 7: 計画した dry-run test は qsub 非実行を実証していない

根拠 (`plan.md:103-110,130-138,224-233`; `test_pegasus_tools.py:1564-1595`): plan は scheduler leaf が作られないことから qsub 非実行も主張するが、何もしない qsub stub が実行されても同じ観測になる。既存 test も `qsub command:` と receipt を見るだけで、qsub invocation marker を置いていない。

影響: code の既存分岐から非実行性は静的に読めるが、提案 test がその性質を動的に証明するという説明は成立しない。

推奨 (削る): 本 wave の新テストは `-o/-e` argv の負例検査に限定し、「qsub 非実行も新たに実証した」という主張を外す。dry-run 分岐は変更しない。

## 所見 8: 既存 consumer は赤くならず、plan は duration ledger を取り落としている

根拠 (`brief.md:45-55`; `plan.md:213-222`; `test_pegasus_calibration_workload.py:10-12,27-38,58-67,139-156`; `test_pegasus_tools.py:124-131,176-184,692-700,1564-1619`; `pegasus-runbook.md:455-486,484-486,542-550,649-653`): 直接 consumer は次である。

- `test_submitter_exposes_only_the_calibration_whitelist`
- `test_calibration_shell_scripts_parse`
- `test_submitter_rejects_an_unregistered_ratio_before_side_effects`
- `test_shell_syntax[submit_certify.sh]`
- `test_certify_calibration_policy_check_rejects_symlinks[submit_certify.sh]`
- `test_certify_keeps_default_modules_and_uses_system_toolchain`
- `test_submit_dry_run_does_not_resolve_cluster_commands`

計画どおり既存文字列、schema、引数受理集合を変えなければ、これらに赤くなるものはない。admission registry の `submit_certify.sh = local-ok / legacy-admitted` も path/class/evidence consumer であって script bytes の pin ではないため、`test_hooks.py`、`test_check_docs.py`、`tools/check_docs.py` も今回の内容変更だけでは赤くならない。

影響: 「既存 consumer が赤くなる」という前提は成立しない。plan が明示していない consumer は `orchestrator/tests/acceptance_duration_ledger.json` だが、node id を変更しないためこれも赤くならない。brief の全列挙主張は、射影外の registry/test 本文までは本相談で独立検証できない。

推奨 (採用): 焦点対象は二 test fileで足りる。ただし通常完了検査としての `tools/check_docs.py` と、非赤 consumer である duration ledger を inventory から落とさない。

## 所見 9: 新しい機体固有 absolute path は repo へ持ち込まれない

根拠 (`plan.md:26-39,103-109,130-136`; `brief.md:56-59`; `pegasus-runbook.md:1585-1595`): prefix は実行時の Git common dir から導出し、test も fixture の実 path から期待値を計算する。plan は runbook を編集せず、shared script/testへ `/work/1/SFC/tanab/...` を固定する案もない。固定されるのは相対 suffix `izanagi-job-evidence/calibration-certify` だけである。

影響: この攻撃は失敗した。brief/addendum にある機体固有 path は repo 外の調査資料であり、共有 script/test/docsへの導入ではない。

推奨 (採用): 実行時導出を維持する。ただし submodule にも安全という一般化は採用しない。

## 総括

最重は、plan が containment、provision、新規 error contract を残し、D1291 の「qsub 引数 1 箇所」を超えている点である。  
次に common-dir 導出は submodule で superproject の `.git` 内を指し得るため、一般的な repo 外保証ではない。  
親 brief は qsub cwd と floor precedent を実際の code より広く一般化している。  
採用形は `-o/-e` とその argv 負例だけに縮め、gate、CLI、provision、一般化を削るべきである。