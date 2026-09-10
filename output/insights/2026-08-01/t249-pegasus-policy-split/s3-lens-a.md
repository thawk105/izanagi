静的監査のみ実施した。HEAD は base `7b24f81`、worktree は clean。pytest は実行しておらず、緑とは主張しない。

### 1. T-249 本体を実装せず、構造衝突が残る

- 深刻度 / 判定: **Major / real**
- 場所: [s1-brief.md:33](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s1-brief.md:33)、[s2-plan.md:148](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:148)、[policy.json:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/policy.json:22)
- 攻撃入力: この wave 後に calibration / floor / T-141 用 key を共有 `policy.json` へ追加する。registry は policy の編集を禁止せず、全 consumer も共有 file を読み続けるため、現状と同じ T-139 hash drift が再発する。brief:34 の「所在と読み手の付け替え」と brief:39-41 の「付け替えない」は自己矛盾している。
- 成果物影響: T-139 の `binding.policy.sha256` が現行 bytes と不一致になり、certified evidence の再検証が拒否される。
- 最小 fix: actual split と consumer 付替えまで行うか、この wave を「T-249 前処理」と改称して T-249 を未完了のまま残す。D96 は禁止ではなく、新 D と境界テストを要求する手続である。

### 2. path-only registry は「run を支配した設定」の索引にならない

- 深刻度 / 判定: **Major / real**
- 場所: [s2-plan.md:71](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:71)、[silo_ladder_rung1.json:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:41)、[contract.py:497](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/qualification/contract.py:497)
- 攻撃入力: consumer を持たない tracked file `orchestrator/qualification/t999_reservation_policy_v1.json` を registry に登録する。予定 test の実在・tracked・集合一致はすべて満たすが、その file がどの run も支配していないことを検出できない。逆に T-139 の artifact は共有 policy だけを指すのに、flat registry は T-126 policy も併記する。
- 成果物影響: 将来のレポートが dead policy や別タスクの policy を「その run を支配した設定」と列挙できる一方、certified binding 自体は別の意味を示す。
- 最小 fix: registry を「所在 inventory」に限定して支配設定の再導出を主張しないか、task/role/producer と artifact field の対応を持たせて consumer・artifact と交差検査する。SHA は複写しない。

### 3. 完全性 scan は false negative と過剰拒否を同時に作る

- 深刻度 / 判定: **Major / real**
- 場所: [s2-plan.md:120](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:120)
- 攻撃入力: `tools/pegasus/t999_policy_v1.json`、または `orchestrator/qualification/t999_reservation.json` を新 consumer から読む。予定 regex の対象外なので未登録でも沈黙する。反対に、非 Pegasus 用 `orchestrator/campaign/t300_retry_policy_v1.json` は名前だけで Pegasus registry への登録を強制される。
- 成果物影響: 前者は支配設定のレポートから実 policy を欠落させ、後者は無関係な構成を新たに拒否して開発受理集合を縮小する。
- 最小 fix: Pegasus policy 専用 directory を設けて全 file を閉集合 scanするか、広い候補 scan＋明示分類を使う。D112 にはこの受理集合変更と正負両境界を明記する。

### 4. registry 自身の tracked 性を検査していない

- 深刻度 / 判定: **Major / real**
- 場所: [s2-plan.md:124](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:124)、[s2-plan.md:137](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:137)
- 攻撃入力: `policy_registry_v1.json` を working tree に置くが index から外す。予定 test は registry の各 `policy_paths` だけを `git ls-files` へ渡すため、registry 本体が untracked でも静的に素通りする。
- 成果物影響: 部分 commit では test/docs だけが入り、唯一の所在索引が clean checkout に存在しない状態を作れる。
- 最小 fix: registry 本体にも `git ls-files --error-unmatch` を実行し、「registry 本体を untracked」にする変異を事前登録する。

### 5. file 単位の凍結 pin 閉包に 3 件の直接 pin が漏れている

- 深刻度 / 判定: **Major / real（現 wave の no-touch で非発火、実分割時は scope 外へ返す）**
- 場所: 直接固定値は次の tracked 4 file。
  - [silo_ladder_rung1.json:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:43)
  - [submit-receipt.json:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/submit-receipt.json:9)
  - [campaign-identity-receipt.json:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/campaign-identity-receipt.json:21)
  - [campaign-root-receipt.json:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/campaign-root-receipt.json:30)
- 攻撃入力: 実分割時に主 evidence の binding だけを再解釈・再発行する。raw manifest は submit/campaign receipt の bytes をさらに固定しており、[test_silo_ladder_rung1_evidence.py:1305](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1305) が submit binding と主 binding を照合する。台帳入口は [patches/ledger.json:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/patches/ledger.json:35)。
- 成果物影響: raw receipt・manifest・主 evidence の policy digest が分裂し、T-139 proof chain と材料レポートが閉じなくなる。
- 最小 fix: 「campaign は1件」でも direct pin file は4件と brief に記録し、実分割の裁定には raw manifest と ledger pointer を含む全閉包を渡す。現計画の `output/env/pegasus/**` no-touch は維持する。

補足として、T-139 の producer/validator は `submit_silo_ladder_rung1.sh:284-305,370-381,489-496` と `silo_ladder_rung1.py:2394-2424,3496-3516,4538-4562`。T-126 側は `contract.py:38-65`、`t126_driver.py:344-359,398-422,800-843`、`identity.py:130-160`、`submission.py:161-173`、`t126_qualification.sh:675-682`、`collector.py:1510-1518` が動的な identity trust chain であり、固定 SHA の committed receipt ではない。

### 6. registry-only 変更が T-126 の受理集合を変える、という疑いは反証された

- 深刻度 / 判定: **Major（成立時） / refuted**
- 場所: [contract.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/qualification/contract.py:38)、[contract.py:450](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/qualification/contract.py:450)、[t126_driver.py:384](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/qualification/t126_driver.py:384)
- 攻撃入力: 計画どおり registry/test/docs だけを commit する。registry は `REQUIRED_CODE_IDENTITY_PATHS` に入らず、`code_identity` の exact key set も変わらないため、series artifact の受理集合は変わらない。
- 成果物影響: `superproject_commit` / `superproject_tree` は preimage に含まれるため新規 run の `qualification_series_id` 値は通常どおり変わるが、受理する field/key 集合は不変である。
- 最小 fix: registry-only には D96 は不要。「identity 値不変」とは記録しない。将来 `policy.json` を required set から外す実付替えでは D96 を適用する。

### 7. T-126 reservation policy の byte 不変 guard が計画から落ちている

- 深刻度 / 判定: **Minor / real**
- 場所: [s1-brief.md:53](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s1-brief.md:53)、[s2-plan.md:152](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:152)、[s2-plan.md:159](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:159)
- 攻撃入力: `t126_reservation_policy_v1.json` を空白だけ整形して commit する。予定 protected diff は共有 policy と `output/env` しか対象にせず、既存 policy test は JSON 値を検査するため、この byte drift 専用の固定 SHA gate はない。
- 成果物影響: production 値は同じでも `code_identity` digest と以後の `qualification_series_id` が変わり、brief の byte 不変条件に反する。
- 最小 fix: reservation policy も base `7b24f81` との `git diff --exit-code` と既知 SHA 検査へ追加する。

### 8. request `876519` の「ちょうど2 node」は変異族にも全走にも一般化できない

- 深刻度 / 判定: **Major / real**
- 場所: [s1-brief.md:13](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s1-brief.md:13)、[request.json:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/output/pegasus-dispatch/601a9bee1050138d2cd48c98efc966a3/request.json:2)、[test_pegasus_floor_tools.py:313](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_floor_tools.py:313)、[test_silo_ladder_rung1_driver.py:2229](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_silo_ladder_rung1_driver.py:2229)
- 攻撃入力: `silo_ladder_rung1.walltime` を変更すれば PBS directive test も追加で赤になり、`floor_walltime(_s)` 変更なら floor の2 nodeも反応する。key 削除・file 移動ではさらに多数が手前で失敗する。request 自体も全走ではなく、5 test file・394 node の選択実行だった。
- 成果物影響: 変異 attribution と受入レポートの failure 数を誤記し、追加赤を「無関係」と誤裁定する可能性がある。
- 最小 fix: 「指定5 fileに対する top-level 無害key追加では2/394」と限定する。族一般化が必要なら key削除・値変更・整形・移動を独立変異として実測する。

### 9. 共有 `policy.json` を間接的に書き換える既存経路は確認できない

- 深刻度 / 判定: **Major（成立時） / refuted**
- 場所: [s2-plan.md:159](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:159)、[test_t126_pegasus_tools.py:790](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_t126_pegasus_tools.py:790)、[test_t126_pegasus_tools.py:2809](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_t126_pegasus_tools.py:2809)
- 攻撃入力: generator、JSON formatter、fixture test、CRLF 化を想定して全参照を追った。既存 test の書込みは `tmp_path` 内の複製だけで、production は reader のみ。active Git hook・path attribute・repo formatterもなく、手動整形や行末変更は既知 SHA と base diffで検出される。
- 成果物影響: 計画どおり最終 SHA/base diffを実施する限り、T-139 binding や raw receipt の値は変わらない。
- 最小 fix: 現行 guard を維持し、可能なら commit 後にも同じ SHA/base diffを再実行する。

## 総括

- must-fix: registry-only wave を T-249 完了扱いせず、実分割を行うか前処理として未完了を残す。
- must-fix: flat path list を「run の支配設定索引」と呼ばない。consumer/artifact 対応を検査する。
- must-fix: regex scan の false negative・非 Pegasus 過剰拒否を解消する。
- must-fix: registry 本体の tracked 性と、その変異を追加する。
- D112 には新 gate が変える開発受理集合と正負境界を明記する。
- scope 外 real: T-139 は1 campaignでも直接 SHA pin は4 tracked fileあり、raw manifest/ledgerまで閉包する。
- scope 外 real: actual T-126 付替えで identity key setを変えるなら D96 手続が必要。
- 親 brief への異議: request `876519` は5 file・1変異だけで、全走・変異族の「2 nodeだけ」を証明しない。
- 共有 policy の bytes と現在の frozen binding 意味論は、registry-only 案では機械的に不変。
- pytest は未実行。以上は read-only の静的所見である。