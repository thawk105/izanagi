静的検査のみ実施し、pytest・probe は実走していない。

### A-1 P1 source edit は「発行」を未 commit の「有効化」へ変える

**攻撃対象:** [stage1-brief.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage1-brief.md:21) の P1、[stage2v3-plan.md:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:56) / R1-A。

**なぜ壊れるか:** `GenerationEntry` は明示的に「data であって権限ではない」([env_contract.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:172))。現 issuer は CLI 指定から候補を作り、その候補自身の serial/hash を expected head として検証して record だけを publish する ([issue_env_contract_activation.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:167), [同:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:195))。ここで同じ候補から source head も書き換えると、候補 producer が自分の値を trust root に昇格させる。runtime は Git commit/review を見ず、working tree 上の record と定数の一致だけを見る ([env_contract.py:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:519))。したがって plan 自身が S3 で認めるとおり、dirty tree でも fresh process は n+1 を受理する ([stage2v3-plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:30))。

**実害経路:** issuer 成功直後、commit・review 前の worktree から campaign writer を起動すると、新契約で `authorize()` が成功し certified/WAL 成果物を書ける。leaf の schema gate は保たれるが、activation の受理集合が「別途 review された head」から「issuer が選べる任意の登録済み successor」へ広がる。これは control-plane の fail-open。R1-A は選択肢から落とすべきである。

**確度:** high

### A-2 推奨 D の `trusted-main` は呼出し点で成立していない

**攻撃対象:** [stage2v3-plan.md:61–69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:61)、[同:146–155](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:146)。

**なぜ壊れるか:** plan は「candidate 側 checker を実行しない」とするが、接続先に指定した `tools/dev_wave_land.py` は自分自身の `__file__` から code root を取る ([dev_wave_land.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/dev_wave_land.py:27))。現 runbook も相対 path の `python3 tools/dev_wave_land.py` しか固定していない ([pegasus-runbook.md:762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/docs/pegasus-runbook.md:762))。通常は wave checkout の helper が checker を呼ぶため、candidate が caller 自体を削除・変更できる。`LandRequest` に helper/checker の trusted-main blob identity も checker 導入 commit もない ([dev_wave_land.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/dev_wave_land.py:77))。helper 自身も非協調 writer に対する sandbox ではないと宣言している ([同:2–7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/dev_wave_land.py:2))。

**実害経路:** split record/head historyを含む candidate が、candidate 版 land helper で検査呼出しを外せば fast-forward される。成果物上は「land 可能な Git 履歴」の受理集合が再び広がる。main checkout に land 済みの helper を re-exec するか、caller と checker の双方を `tested_main` blob に束縛する必要がある。また「checker 導入 commit 以降」は実在 field ではないため、`tested_main` に checker blob が存在すること等へ定義し直す必要がある。

**確度:** high

### A-3 新 record は tracked ではなく untracked であり、index/stash 状態が欠落している

**攻撃対象:** [stage1-brief.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage1-brief.md:16) の「どちらも git tracked」、plan の S1〜S4 ([stage2v3-plan.md:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:23))。

**なぜ壊れるか:** Git は directory を追跡しない。issuer は次 serial の新しい filename を create-only で生成するため、生成直後の record は untracked である ([issue_env_contract_activation.py:203–213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:203))。静的確認でも現 index にある activation record は `00000001.json` だけだった。このため次の未掲載状態が成立する。

- `git commit -a` / `git add -u` は tracked な head edit だけを commit し、新 record を落とす。
- default `git stash` は head edit を退避するが untracked record を残し、S2 を作る。
- `git stash -u` は整合した record/head を repo 共通 stash に入れ、別 worktreeへ coherent dirty S3 を復元できる。
- head だけ staged、record だけ staged、両方 staged、どちらも unstaged は、runtime には同じ working-tree bytes として見える。

land 時の完全 clean 検査 ([dev_wave_land.py:713–727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/dev_wave_land.py:713), [同:785–787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/dev_wave_land.py:785)) は最終的には止めるが、それ以前の runtime 起動を止めない。

**実害経路:** head-only commit が untracked record に覆われた working treeではテストも fresh writer も n+1 を受理できる。その後 record を別 commit にすると clean tipでも split historyになる。さらに `stash -u` から別の official rootへ dirty activation を移せる。handoff/runbook に exact `git add` 対象、index/HEAD tree照合、stash禁止、writer起動前の完全 clean検査が必要。

**確度:** high

### A-4 推奨 co-commit gate は一 commit 二 record を受理し、未配備世代を ever-active にする

**攻撃対象:** [stage2v3-plan.md:63–69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:63)、予定テスト [同:157–164](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:157)。

**なぜ壊れるか:** 提案条件は「record 集合が変わる commit で head tuple も変わる」「terminal tuple が一致する」だけで、追加 record 数を 1 に固定していない。loader は三 record の forward chain を意図的に受理する ([test_env_contract_activation.py:607–614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/tests/test_env_contract_activation.py:607))。[T-627] は各 edge を検査するだけで ([env_contract_activation.py:274–329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:274))、head pin は terminal record としか照合しない ([同:406–416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:406))。しかも chain 中の全 contract hash が `ever_active` に入る ([同:384–405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:384))。

**実害経路:** 一 commit で n+1 と n+2 を追加して head=n+2 にすると、記述された D gate と T-627 を通る。n+1 の contract は独立した committed headとして一度も配備・smokeされていないのに、`resolve_by_contract_sha256()` は ever-active として historical artifact を受理する ([env_contract.py:690–703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:690))。各 activation commit は「追加 record exactly 1、head serial exactly +1」を要求すべきである。単一 record 内で複数 env を同時 +1 する既存許可とは分ける必要がある。

**確度:** high

### A-5 R0-A の maintenance domain は列挙も fence もできない

**攻撃対象:** P2 手順 [stage2v3-plan.md:80–91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:80)、gate台帳 [同:135–137](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:135)、R0-A [同:181–188](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:181)。

**なぜ壊れるか:** plan が worktree registry の根拠に挙げる `_repository_root()` は現在 import した一 root と sentinel を確認するだけで、worktree を列挙しない ([env_contract.py:465–483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:465))。generic dispatch request は `repo_root` しか持たず source commit がない ([dispatch_compute.py:1374–1380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/pegasus/dispatch_compute.py:1374))。既存 certified-writer preflight も `floor|t126` の二 modeだけ ([certified_writer_preflight.py:136–176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/certified_writer_preflight.py:136)) で、多数の直接 campaign writer / fork / resume を表す roster ではない。人手の submit freeze と `qstat` snapshot の間にも fencing token がない。

**実害経路:** queue 照合後に別 wrapperが submitする、未列挙 worktreeの writerが継続する、generic dispatchが更新後に旧/新どちらの root bytesを使う、といった経路が残る。旧 process/job が durable output を作る受理集合は変わらない。plan 自身が「global proofではない」と認めているため、R0-Aを保証と呼ばず、列挙した launcher/pathだけの checklistへ縮めるか、別 waveへ返すべきである。

**確度:** high

### A-6 [T-627] により「据置 env だけ識別不能」は実際に起こる

**攻撃対象:** brief erratum 2 [stage1-brief.md:25–27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage1-brief.md:25)、未訂正の成果物影響 [同:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage1-brief.md:41)、plan P2-C。

**なぜ壊れるか:** row単位の「同一 generation・別 hash」は、pair が変われば exactly +1 を要求するため起きない ([env_contract_activation.py:274–291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:274))。一方、別 env が進み対象 env が据置の global activation-state 変更は明示的に許可される ([同:293–297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:293)、[D245:11390–11399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/docs/decisions.md:11390))。並行 [T-657] はまさに Linux g1据置・Pegasus g1→g2である ([s1-brief.md:16–19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s1-brief.md:16))。

`authorize()` は global serial/state hashを保持する ([env_contract.py:659–665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:659)) が、guard は照合後に contract objectだけを返し ([execution_guard.py:70–104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/execution_guard.py:70))、durable receipt は `contract_sha256` しか書かない ([同:204–222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/execution_guard.py:204))。`evidence_contract_sha256` は別文書の hashなので、activation identification に使える経路は最初から存在しない。

**実害経路:** Linux g1成果物は serial 1 前後と serial 2 後で同じ contract hashになり、execution receiptだけでは旧/new activation lineageを区別できない。契約値自体が同じなので単独数値の破損までは示せないが、旧 process drain や cross-env 合成の証明には使えない。brief:41 の「receipt の serial」は明白に誤りであり削除必須。

**確度:** high

### A-7 probe は fresh production 経路を測っておらず、serial 2 後は再現不能

**攻撃対象:** brief の実測一般化 [stage1-brief.md:13–17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage1-brief.md:13)、[probe_split_window.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py:1)。

**なぜ壊れるか:** probe は一 process内で production stateを先に cacheし ([probe:14–21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py:14))、その後 `_load_authority_snapshot()` ではなく leaf `load_activation_state()` へ expected値を直接注入する ([同:43–64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py:43))。source edit、`_repository_root()`、calibration、fork reset、production cacheを通らないので、「fresh process」の実測ではない。

さらに rows を常に Linux g1/Pegasus g2へ固定している ([同:23–30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py:23))。T-657後に再走すると serial 3は全 env据置 no-opとなり、Bは head受理まで到達せず拒否される。`UNEXPECTED` 分岐も文字列を printするだけで非0終了しない ([同:52–67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py:52))。

**実害経路:** この probe が裏付けるのは「leaf validator が record2/head1 と record1/head2 を拒否し、record2/expected2を受理した」範囲だけである。「live経路に fail-openなし」「cache/fork/deploy windowも同じ」は裁定根拠にできない。親の実測表現を縮め、将来 successorが実在してから production fresh-process probeを別途行う必要がある。

**確度:** high

### A-8 issuer の二つの repository root が束縛されていない

**攻撃対象:** plan S5 の root説明 [stage2v3-plan.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage2v3-plan.md:33)、crash残骸棚卸し。

**なぜ壊れるか:** issuer の `repo_root` は tool自身の `__file__` から得る一方 ([issue_env_contract_activation.py:159–165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:159))、実際の書込み先は importされた `contract._repository_root()` から得る ([同:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:203))。両者の exact 一致 assert がない。`campaign.env_contract` が別 checkoutから既に import済み、または `sys.path` 上で先に解決されていれば別 rootになりうる。

publish後の handoffで `issued.relative_to(repo_root)` を評価する ([同:143–151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:143))。別 rootならここで uncaught `ValueError`となるが、publish処理は既に正常終了しているため recordは回収されない。

**実害経路:** 意図しない worktreeに record-only残骸を作り、意図した worktreeでは何も発行されず、toolは出力前に crashする。誤配備先は fresh load拒否または、そこに対応 headがあればdirty activationを受理する。通常のfresh CLIでは起こりにくいが、保守 toolの反復利用前に両 rootの identityを fail-closed照合すべきである。

**確度:** medium

### A-9 fork 後を「旧 cache 続走」と一括する brief 表現は不正確

**攻撃対象:** [stage1-brief.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage1-brief.md:17)。plan の S3-fork は概ね正しい。

**なぜ壊れるか:** fork child は authority snapshotを消す ([env_contract.py:551–560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:551))。したがって親の旧 snapshotをそのまま続走せず、継承した旧 module定数でdirectoryを再読する。deploy後なら新record/旧定数で fail-closed、deploy前に再load済みなら旧stateをcacheして続走、という二状態になる。

**実害経路:** 誤った certified artifact受理は書けない。fork timingにより childが停止する可用性差と、runbook上「forkは再起動でない」という説明精度だけの問題。

**確度:** high — **nit**

## 総括

現 plan は **NO-GO**。runtime leaf の exact serial/state-hash pinそのものには fail-openを見つけていないが、その外側の activation authority・Git履歴・deployment domain が閉じていない。

**must-fix**

- A-1: issuer に source headを自己更新させず、発行と activation approvalを分離する。
- A-2: checkerだけでなく callerも trusted-mainへ束縛し、適用開始入力を実在値で定義する。
- A-3: 新 recordが untrackedである前提で index・partial staging・stash状態を表とrunbookへ追加する。
- A-4: activation commitごとに追加 record exactly 1、head serial exactly +1を要求する。
- A-5: R0-Aを実在する launcher/path閉集合へ縮めるか、機械的 roster/fenceを別設計へ返す。
- A-6: brief:41を訂正し、据置 envの activation lineageは durable receiptで識別不能と明記する。
- A-7: probeの裁定根拠を leaf validationへ限定し、production fresh-process実測と呼ばない。
- A-8: tool rootとimport module rootをpublish前にexact照合する。

**nit**

- A-9: fork childの時系列説明を精密化する。runtime受理集合への実害は確認できない。