# 段 3 敵対検証 — レンズ A

判定は **NO-GO**。静的検査のみで、pytest は実行していない。

## 所見

### 1. [重大度: blocker] [種別: real] 「受理集合は縮むだけ」という不変条件が自己矛盾している

親 brief は「shim を張れない入力だけを新たに拒否し、緩めない」と定めているが、プランの positive control は明示的に「現行は赤、修正後は緑」を要求している。[s1-brief.md:50](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:50)、[s2-plan.md:126](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:126)

受理集合を request の最終 rc と定義すれば、次の両方向が発生する。

| 具体的入力 | 変更前 | 変更後 | 方向 |
|---|---|---|---|
| 選定 `python3.10` は 3.10、同じ dir の `python3` は 3.9、子が 3.10 構文を使う | 子失敗 | 成功 | **成功集合の拡大** |
| 選定 dir に `python3` がなく、後続 PATH にもない | ENOENT 等で失敗 | shim 経由で成功 | **拡大** |
| `--task provenance`、ただし submission FS が noexec・書込不能 | 現行は `sys.executable` 直起動で成功可能 | shim gate で rc=16 | 縮小 |
| 子が sibling `python3` 固有の package に依存 | 成功可能 | 選定 interpreter へ束縛され失敗可能 | 縮小 |
| crash 後に shim dir だけ残った同一 submission の再実行 | 少なくとも子起動までは進む | 子起動前に rc=16 | 縮小 |

「許可する interpreter identity の集合」なら縮小だけ、と説明できる。しかし「request の成功集合」や「テスト受理集合」なら非単調である。段 4 で軸を定義し直さない限り、brief の停止条件を満たせない。

### 2. [重大度: blocker] [種別: real] PATH shim は「束縛」ではなく、最初の子環境に対する上書き可能な既定値でしかない

プランが保証するのは `_job_run()` が渡す PATH の先頭だけである。[s2-plan.md:62](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:62)、現行の配線点は [dispatch_compute.py:485](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:485)。

実際の対象 test helper は inherited PATH のさらに前へ fake bin を追加している。[test_t126_pegasus_tools.py:2929](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/tests/test_t126_pegasus_tools.py:2929) その fake bin に `python3` があれば shim は直ちに迂回される。同様に以下は束縛されない。

- 子が PATH を置換・前置する場合
- `/usr/bin/python3` の絶対指定
- `python3.10` や `python`
- PATH を再構築した後の `/usr/bin/env python3`

従って「孫プロセス全部」「今後どのテストでも塞ぐ」は偽。保証を「渡した PATH を競合する `python3` より前に置き、PATH を保持する descendant を束縛する」へ狭めるか、consumer 側の明示 interpreter 化との択一を再裁定すべきである。

### 3. [重大度: must-fix] [種別: real] 二層版数 gate の片側削除が検出されない

probe 層はソース逐語 test で単独に pin されている。[test_pegasus_dispatch_compute.py:1475](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/tests/test_pegasus_dispatch_compute.py:1475)

一方、`_job_run()` の版数拒否は [dispatch_compute.py:462](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:462) にあるが、既存 M5 は両層を同時に削除した場合だけ赤になる設計である。[test_pegasus_dispatch_compute.py:875](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/tests/test_pegasus_dispatch_compute.py:875)

プランは M5 を維持するだけで、`_job_run` gate 単独削除の sensitivity pin・変異を登録していない。[s2-plan.md:144](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:144) 「二層を弱めない」という不変条件に対して穴である。3.9 を直接 `_job_run()` に入れ、probe を経由せず子未起動を確認する構造 test が必要。

### 4. [重大度: must-fix] [種別: real] fail-closed 経路自体は live だが、identity test の注入位置が未確定

計画どおり helper 前に `stage="interpreter-shim"` を置けば、現行例外処理は `"child"` 以外の stage を保持する。[dispatch_compute.py:499](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:499) 親も `"child"` 以外を bootstrap failure として rc=16 に畳む。[dispatch_compute.py:1328](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:1328) 「print が raise より前」の同型や後段上書きは、この配置案には見つからなかった。

ただし mismatch test が `_verify_interpreter_shim()` 自体を `raise` に mock すると、実際の canonical 比較を削除しても test は緑になる。別 executable を返す identity subprocess の出力を注入し、比較コードそのものを通す必要がある。[s2-plan.md:129](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:129)

### 5. [重大度: must-fix] [種別: real] symlink・TOCTOU・権限境界が未解決

- wrapper は raw `sys.executable` を毎回 exec し、canonical path は一回の検査にしか使わない。[s2-plan.md:41](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:41)、[s2-plan.md:73](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:73) venv の raw path が symlink なら、検査後の target 差替えを以後の裸 `python3` が追従する。
- identity probe と実 child 起動の間、さらに child 実行中の各 `python3` lookup まで TOCTOU 窓が残る。差替え後の失敗は `stage="child"` の通常テスト失敗になり、shim infra failure として識別されない。
- shim dir は 0700 のまま PATH 先頭へ入る。[s2-plan.md:43](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:43) owner process は `git` 等を追加できるため、「Python 以外の tool 解決を変えない」は作成直後だけ成立する。特に provenance task は裸の `git` を多数起動する。[check_ai_provenance.py:196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/check_ai_provenance.py:196)
- `_read_json_object()` は symlink を拒否すると見せるが、CLI は先に request path を `.resolve()` するため symlink 性が消える。[dispatch_compute.py:413](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:413)、[dispatch_compute.py:1510](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:1510) さらに `is_symlink()` と `open()` の間も競合可能である。

[種別: speculative] 現 checkout の `output/pegasus-dispatch` は 0755、submission は 0700 で、別 UID の書換えは現時点では観測しなかった。ただし root の owner/mode/symlink は検査されず、作成処理は `root.mkdir(exist_ok=True)` と child の 0700 だけである。[dispatch_compute.py:991](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:991) root が第三者 writable なら、親 directory の rename 権限により 0700 child 全体を差し替えられる。少なくとも threat model、root 検査、作成後 dir の非 writable 化を裁定すべきである。

### 6. [重大度: must-fix] [種別: real] 親の非再現主張は bnode002 一台にしか成立しない

`876518` は nodes=1、結果 host=bnode002、launcher=`/usr/bin/python3.10`。[focused receipt:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/output/pegasus-dispatch/8534b20625ae5d72bb4119945ad99a2b/receipt.json:57)、[focused receipt:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/output/pegasus-dispatch/8534b20625ae5d72bb4119945ad99a2b/receipt.json:67)

`876520` も nodes=1、host=bnode002、4709 passed / 19 skipped。[full receipt:53](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/output/pegasus-dispatch/06b1f519670e4d26d8ceb4928f8e464c/receipt.json:53)、[full receipt:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/output/pegasus-dispatch/06b1f519670e4d26d8ceb4928f8e464c/receipt.json:63)、[full receipt:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/output/pegasus-dispatch/06b1f519670e4d26d8ceb4928f8e464c/receipt.json:81)

したがって brief の「現ノード群で再現しない」は過大表現である。[s1-brief.md:13](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:13) 同 brief は後段で「ノード群全体へ一般化しない」と自ら訂正しているため、冒頭を「bnode002 の二走では非再現」に直すべきである。[s1-brief.md:32](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:32)

また receipt の `result.interpreter` は launcher の記録であり、問題の sibling `dirname(sys.executable)/python3` の path/version は記録していない。全走緑は症状非再現の行動証拠だが、裸 `python3` の実体証拠ではない。

### 7. [重大度: must-fix] [種別: real] P1 は実質正しいが、親 brief の現物証拠は閉じていない

親が示した [dispatch_compute.py:491](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:491) は「directory しか前置しない」ことを証明する。しかし bare consumer までの file:line chain は brief にない。

実際の reachable chain は存在する。

- `_job_run()` が child_env で `run_tests.py` を起動する。[dispatch_compute.py:494](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:494)
- focused test が submitter を subprocess 起動する。[test_t126_pegasus_tools.py:3144](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/tests/test_t126_pegasus_tools.py:3144)
- helper は inherited PATH を保持する。[test_t126_pegasus_tools.py:2929](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/tests/test_t126_pegasus_tools.py:2929)
- submitter は裸の `python3` を起動する。[submit_t126_qualification.sh:350](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/submit_t126_qualification.sh:350)
- 一般 consumer も固定 argv に裸の `python3` を持つ。[task_run_check.py:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/task_run_check.py:16)

P1 の結論は採れるが、この chain を段 4 正本へ追加し、「将来どのテストでも」ではなく現在の継承条件を明記すべきである。

## P2〜P5 への反証結果

- [重大度: nit] [種別: real] **P2 は repo 管理下の `_job_script` に限れば反証できなかった。** probe は `"$resolved"`、job-run は `"$selected"` を直接実行し、裸の Python はない。[dispatch_compute.py:389](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:389) PBS site prologue/epilogue の source は repo にないため、それらまで「不要」と一般化してはならない。
- [重大度: must-fix] [種別: real] **P3 の canonical symlink 棄却は妥当だが、wrapper 案も未裁定。** venv prefix 保存には有利だが、raw target の再束縛と `/bin/sh`・noexec 依存を新たに受理条件へ加える。[s2-plan.md:79](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:79)
- [重大度: nit] [種別: real] **P4 の反証は成立しなかった。** 正しさ防壁または受理集合を変える場合は軽量版にしない契約そのものである。[core.md:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/docs/dev-wave/core.md:11)
- [重大度: nit] [種別: real] **P5 の中心機序は正しい。** 実 interpreter のコピーを本当に subprocess launcher とし、同一 dir の旧 `python3` を実 lookup させれば、fix 全巻戻しで赤になる。ただし helper mock で代用せず、launcher の `sys.executable` と fake 実行記録を残すこと。これは PATH を子が上書きする場合までは証明しない。

## scope 全層検査

### [重大度: must-fix] [種別: real] プランの件数表は reachability 証明になっていない

- `tests` task: inherited PATH を保持する descendant には効く。明示 PATH 上書きには効かない。
- `provenance` task: child 自体は `sys.executable` で起動され、現行 checker に裸の Python consumer はない。[dispatch_compute.py:68](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:68) 無条件 shim は benefit なしに作成・noexec・TOCTOU failure を追加する。tests task 限定か uniform invariant かを裁定すべきである。
- `tools/task_run_check.py`: dispatch descendant として起動された場合だけ covered。通常の dev-wave check として直接起動する場合は covered ではない。
- `t126_qualification.sh`、`floor_campaign.sh`、`silo_ladder_rung1.sh`: それぞれ自前候補列・3.10 gate・`$PY` 直接実行を持つため、dispatch shim に統合すべきではない。[t126_qualification.sh:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/t126_qualification.sh:15)、[floor_campaign.sh:161](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/floor_campaign.sh:161)
- `#!/usr/bin/env python3` の 50 件: direct executable 起動かつ PATH 非上書きの場合だけ covered。単純件数では scope 証明にならない。

### scope 外の裁定パッケージ候補

- [重大度: must-fix] [種別: real] **certification 系:** `certify_calibration.sh` は計算ノードで裸の `python3` を繰り返し使い、自前版数 gate がない。[certify_calibration.sh:55](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/certify_calibration.sh:55)、[certify_calibration.sh:715](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/certify_calibration.sh:715) `submit_certify.sh` の qsub は shim PATH を束縛しない。[submit_certify.sh:170](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/submit_certify.sh:170) T-248 へ無断で入れず、別 wave 候補にする。
- [重大度: must-fix] [種別: real] **T-141:** `t141_region_profile.sh` は `python3` の存在だけを検査し、version は検査しない。[t141_region_profile.sh:357](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/t141_region_profile.sh:357)
- [重大度: nit] [種別: real] **smoke probe:** 裸の system `python3` を使うが、環境観測 job なので shim 化すると観測対象を変える。[smoke_probe.sh:111](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/smoke_probe.sh:111) 意図を明記して scope 外維持が妥当。
- [重大度: must-fix] [種別: real] **qualification toolchain 候補:** `submission.py` は `python3` を先に採り、version floor を検査せず version を記録するだけである。[submission.py:73](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/qualification/submission.py:73)、[submission.py:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/qualification/submission.py:107) 現在は login-side 実行だが、F46 family の別候補として裁定対象にすべきである。

## 変異事前登録の帰属

### [重大度: must-fix] [種別: real]

| 変異 | 攻撃結果 |
|---|---|
| child PATH から shim を削除 | positive control に加え、共有 `_job_run_with_mocked_child` の PATH assert を使う3 nodeも赤になる計画で、期待赤1件という帰属にならない。[s2-plan.md:137](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:137) |
| wrapper→symlink | raw `sys.executable` を比較する全 parameter が赤になり得る。期待 node を `[isolated]` 1件へ固定する根拠がない。 |
| 作成例外を fallback | 注入を `_write_text_x` へ置けば単一理由性は成立する。helper 全体を mock してはならない。 |
| identity 不一致を警告化 | identity subprocess の返値を注入すれば成立。verify helper 自体の例外 mock は恒真 test になる。 |
| `mkdir(exist_ok=True)`＋既存 wrapper 再利用 | **二編集の複合変異**。`exist_ok=True` 単独では leaf の O_EXCL が拒否し、test が緑のままになり得る。分割が必要。 |
| shim stage の親保存 test | 既存の任意非-child stage 拒否 test が既にある。[test_pegasus_dispatch_compute.py:917](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/tests/test_pegasus_dispatch_compute.py:917) 新規 test が殺す固有変異が未登録。 |

未登録の必須候補は、`_job_run` 版数 gate 単独削除、`shutil.which` leaf 検査削除、helper 呼出し削除、作成後 PATH directory への別 command 混入、identity probe 後の target 差替えである。`fsync` を要件として残すなら、その削除を検出する test もない。単一理由性契約は [mutation.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/docs/dev-wave/mutation.md:5) に反する。

## 総括

**NO-GO。** 現プランのまま段 5 へ進めない。  
最大の懸念 1: 受理集合の軸が未定義で、「縮小のみ」と意図した成功回復が矛盾する。  
最大の懸念 2: PATH shim は descendant の PATH 上書き・絶対指定を防げず、「全孫束縛」は成立しない。  
最大の懸念 3: `_job_run` 版数 gate の単独削除と filesystem TOCTOU が検出・裁定されていない。  
段 4 で保証範囲、provenance への適用、脅威モデル、変異の単一理由性を確定してから再計画すべきである。  
pytest は実行しておらず、緑の主張はしていない。