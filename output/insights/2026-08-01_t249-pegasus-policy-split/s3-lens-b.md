静的監査のみ実施した。HEAD は `7b24f81`、worktree は clean、ホストは `pegasus02`。pytest は実行しておらず、緑とは主張しない。

### 1. P1 と P2 は矛盾し、ユーザー裁定を実装しない

- 深刻度・自己判定: **Critical / real**
- 場所: [s1-brief.md:33-41](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s1-brief.md:33)、[s2-plan.md:193-197](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:193)、[decisions.md:4938-4940](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/docs/decisions.md:4938)
- 攻撃入力: P1 は「読み手の付け替え」を再編の実体と定義する一方、P2 は全 live consumer の付け替えを除外する。現に calibration は [certify_calibration.sh:33-35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/certify_calibration.sh:33)、floor は [floor_campaign.sh:35-38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/floor_campaign.sh:35)、T-126 は [submission.py:161-167](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/qualification/submission.py:161)、T-141 は [t141_region_profile.sh:377-400](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/t141_region_profile.sh:377) から旧 file を読む。次のタスクが `policy.json` に 1 key 足しても、新 registry node は内容を読まないため失敗せず、既存 hash node だけが赤になる。事故経路はそのままである。
- 成果物影響: [silo_ladder_rung1.json:41-43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:41) の `binding.policy.sha256` が現行 bytes と一致せず、T-139 committed evidence が受理集合から外れ、certified 根拠参照を再導出できなくなる。
- 最小 fix: この wave を「registry 前提整備」と改称して T-249 を未完のまま残すか、実再編まで scope に戻す。`policy.json` の bytes を変えない実再編は可能である。旧 file を **T-139 専用の legacy frozen snapshot** と明記して T-139 consumer だけ残し、calibration・floor・T-126・T-141 は同値の task file へ付け替える。新 file は各 producer の receipt/identity に束縛する。T-126 identity set から旧 path を外す処理だけは D96 パッケージへ分離できるが、consumer の付け替え自体まで除外する理由にはならない。

### 2. pytest node は五つの層のうち acceptance 時にしか発火しない

- 深刻度・自己判定: **Major / real**
- 場所: [s2-plan.md:112-133](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:112)、[run_tests.py:290-308](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/run_tests.py:290)、[hooks/README.md:15-24](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/hooks/README.md:15)

| 層 | 発火 | 沈黙 |
|---|---|---|
| 人間の file 作成 | full suite または新 node を明示実行した時 | 作成・stage・個別の無関係 test 実行時 |
| AI 実装子 | 親が段 7 で full suite を実行した時 | 作成時。Codex hook は未配線 |
| shell reader | なし | 全 consumer が path を直書き |
| Python reader | なし | `submission.py`、driver、collector 等は registry を読まない |
| 他 worktree/session | registry land 後に取り込み、そこで test を実行した時 | 古い base 上の作業中と別 worktree 内では常時 |

- 攻撃入力: 別 worktree で新 task policy と consumer を作り、registry/test を取り込まないまま作業する。現在の node はその worktree を観測せず、shell/Python も registry を参照しない。統合時にも full suite を省けば沈黙する。
- 成果物影響: 未登録 file が run を支配すると、レポート・台帳から「支配した設定」への registry 参照が欠落する。特に T-126 final receipt は [t126_final_receipt_schema.json:17-48](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/qualification/t126_final_receipt_schema.json:17) のとおり直接の policy path を持たない。
- 最小 fix: 少なくとも local-main land/CI の必須 checker として発火させる。shell/Python 層まで解決済みと称するなら、registry resolver 経由にするか、全 live consumer の参照先を検査する。リアルタイムな他 worktree 強制まで行わないなら、明示的な scope 外裁定パッケージにする。

### 3. 命名規約を外した file は「完全性検査」を素通りする

- 深刻度・自己判定: **Major / real**
- 場所: [s2-plan.md:120-131](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:120)、[failures.md:104-116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/docs/failures.md:104)
- 攻撃入力: `tools/pegasus/t300_profile_policy_v1.json`、`orchestrator/qualification/policies/t300_reservation_policy_v1.json`、または `t300_pegasus_settings.json` を作り、新 consumer から読む。提案 scan は `orchestrator/<owner>/t<数字>_<purpose>_policy_v<正整数>.json` だけなので、registry 未登録のまま exact-set assert を通る。
- 成果物影響: T-300 の結果が certified 候補や材料レポートへ入っても、設定参照は唯一索引から辿れず、レポートの設定列挙と実 run の支配入力が乖離する。
- 最小 fix: 新規 policy を専用 directory 一箇所へ閉じ、名前ではなく directory 内の全 regular file を exact 列挙する。さらに実効性まで必要なら、consumer が registry resolver 以外から policy path を得られない構造にする。既存 T-126 path と frozen T-139 path は legacy 例外として明示する。

### 4. 純増検出力の帰属は過大・過小の両方がある

- 深刻度・自己判定: **Minor / real**
- 場所: [s1-brief.md:47-49](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s1-brief.md:47)、[s2-plan.md:122-144](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:122)、[test_t126_pegasus_tools.py:1209-1272](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_t126_pegasus_tools.py:1209)
- 攻撃入力:
  - 現行 T-126 path の削除は既存 reservation-policy 読取で既に赤になる。
  - 現行二 path の untracked 化は、両方が `REQUIRED_CODE_IDENTITY_PATHS` に含まれ、既存 `git ls-files` parametrized node が既に捕まえる。
  - 一方、`policy.json` を同一 bytes の外部 file への symlink に置換すると、既存二 hash node はリンク先 bytes を読んで一致し得る。提案 node の `is_symlink()` はここに純増検出力を持つが、P4 は列挙していない。
- 成果物影響: mutation 台帳で current-path の存在/tracked kill を新規検出として数えると純増数が水増しされる。逆に同一 bytes symlink を落とすと、certified binding の hash を保ったまま参照先を可変にできる。
- 最小 fix: 変異帰属を「既存が先に kill」「新 node のみ kill」に分け、same-bytes symlink を事前登録する。現行 path の存在/tracked assert は防御の重複として残してよいが、純増には数えない。

### 5. 「既存二 node が policy.json の byte drift を取り逃す」は反証された

- 深刻度・自己判定: **Minor / refuted**
- 場所: [test_silo_ladder_rung1_evidence.py:1195-1206](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1195)、[test_t126_pegasus_tools.py:1237-1248](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_t126_pegasus_tools.py:1237)
- 攻撃入力: 空白変更、nested key 変更、接頭辞のない key 追加、削除、整形変更。
- 成果物影響: いずれも `read_bytes()` の SHA-256 が変わり既存 node が拒否するため、受理集合は拡大しない。
- 最小 fix: なし。死角は literal な byte drift ではなく、symlink・consumer 取り残し・registry discovery の層に限定して記録する。

### 6. JSON registry は dead file を正規 policy として受理できる

- 深刻度・自己判定: **Minor / real（nit）**
- 場所: [s2-plan.md:71-105](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:71)、[s2-plan.md:120-142](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s2-plan.md:120)、[core.md:57-60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/docs/dev-wave/core.md:57)
- 攻撃入力: `orchestrator/qualification/t999_reservation_policy_v1.json` を tracked にして registry に登録するが、consumer・artifact binding・計測 ID は一つも作らない。予定 assert はすべて通り、dead copy を正規 policy と認定する。
- 成果物影響: この入力単独では certified 選択・レポート・台帳を変えないため **must-fix ではなく nit**。ただし registry の件数や「完全性」報告は水増しされる。
- 最小 fix: runtime consumer を持たない単なる所在目録なら、README の一節・表でも現在の二 path は辿れる。JSON を採るなら entry に owner/role/artifact locator を持たせ、少なくとも consumer または producer-backed identity との対応を検査する。なお registry 全体が空振りという攻撃は refuted で、T-139 には実 artifact pathがあり、T-126 には [submission.py:161-173](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/qualification/submission.py:161) の producer がある。

### 7. request 876519 は全走ではなく、scope 決定の根拠へ一般化できない

- 深刻度・自己判定: **Major / real**
- 場所: [receipt.json:50-66](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/output/pegasus-dispatch/601a9bee1050138d2cd48c98efc966a3/receipt.json:50)、[receipt.json:68-89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/output/pegasus-dispatch/601a9bee1050138d2cd48c98efc966a3/receipt.json:68)、[s1-brief.md:13-18](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s1-brief.md:13)
- 攻撃入力: request 876519 を「受入全走」として worklog/insight に記録する。receipt の argv は五つの test file だけで、結果はその集合内の `2 failed, 392 passed` である。
- 成果物影響: acceptance 記録の suite kind・受理 node 数・「赤はちょうど二つ」という値が誤り、未走 node を検査済みとして扱う。
- 最小 fix: 「five-file targeted run で 2 failed / 392 passed」と限定する。この実測が支持するのは「この一つの top-level key 追加を少なくとも二 node が検出した」までであり、全走の失敗総数、consumer 付替えの安全性、registry の検出力、shell/Python の実効性は射程外と明記する。全走は段 7 で別 request ID を取得する。

## 総括

- must-fix: P1/P2 の矛盾を解き、実再編まで行うか「registry 前提整備」として T-249 を未完に戻す。
- must-fix: 命名規約外を黙って見逃す scan を「完全性 gate」として land しない。
- must-fix: request 876519 を受入全走の実測と記録しない。
- scope 外へ返す real 所見: 非 T-139 consumer の付替え、各 task artifact への新 policy binding、T-126 identity set の整理。
- scope 外へ返す real 所見: 他 worktree・人間経路を覆う local-main land/CI gate。pytest 単独に全層防御を主張しない。
- 親 brief への異議: bytes 不変は実再編と両立する。旧 file を T-139 frozen snapshot として残せば証拠を変更せず衝突を消せる。
- nit: path-only JSON は dead file も受理するため、docs 索引より強いと主張するには consumer/artifact 対応検査が必要。