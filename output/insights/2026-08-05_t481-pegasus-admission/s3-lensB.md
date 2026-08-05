判定は **NO-GO**。必読資料と `tools/pegasus/` 直下の全ファイルを静的に確認した。pytest・実測は走らせておらず、緑は主張しない。

## real 所見

### R1 — real / critical: `collect_receipt.py` の cap 方針が入力全体を閉じていない

- 根拠: (P1') は「入力サイズの hard cap + cap 下の実測」を要求する一方、(P2') は会計 summary だけを修正対象としている。[brief-addendum.md:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/brief-addendum.md:48)  
  実装には、JSON 全読込 [collect_receipt.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py:33)、`rglob()` の全件 sort/list 化を2回行う manifest [collect_receipt.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py:76)、stderr 全読込 [collect_receipt.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py:147)、それら全体を同時保持する payload [collect_receipt.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py:153) が残る。
- 具体例: stderr を100行に切っても、1 GiB の `job-result.json`、または100万ファイルの attempt tree でメモリは無上限に増える。保持行数だけ cap して `read_text()` を残す実装も無効。
- 修正案: stderr・3 JSON・manifest file 数・path 総 bytes・個別 path 長・receipt 推定 bytes の全てに hard cap を置く。`stat` 後、materialize 前に拒否し、manifest は件数上限内でだけ sort する。各 cap の境界値と `cap+1` のテストを追加し、その最大 fixture で §7.0 実測する。
- 成果物影響: 未修正で `login-ok` にすると collector が OOM/失敗し、`final-receipt.json` が作られず、その calibration は certified 選択の参照集合に入れない。

### R2 — real / high: 新規 entry の登録・実測・昇格 lifecycle が閉じていない

- 根拠: 追記は「測定には allowlist 登録が必要、登録には測定が必要」という循環を明示している [brief-addendum.md:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/brief-addendum.md:31)。しかしプランの表は `login-ok` / `compute-only` の二値だけで [s2-plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:52)、meta-test は行を1件足せば通る [s2-plan.md:180](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:180)。測定 receipt や cap の存在は検査しない。
- 具体例: 開発者が `submit_t500.sh` と README の login 手順を追加した場合、行が無ければ利用時に機械拒否される。根拠なしで `login-ok` 行と期待値を足せば tests は通り得る。つまり「毎回1件 sanctioned 化」は、表形式になっただけで残る。
- 修正案: registry を `unknown` / `local-ok` / `dispatch-required` の三値にし、初回登録は必ず `unknown`。`local-ok` 昇格には cap 契約と測定 evidence ID を必須化する。測定は hook 外の人間端末または専用 qsub 手順で行うと明記する。exact-path 登録自体は D103 上必要であり、「個別審査をなくす」ではなく「未審査の silent land をなくす」と主張を狭める。
- 成果物影響: 未修正では、新 collector の receipt 参照が拒否で欠落するか、逆に未測定 entry が login 受理集合へ入り成果物生成中に資源超過する。

### R3 — real / high: 「悉皆」meta-test が直下限定で、nested entry を閉じない

- 根拠: meta-test は `tools/pegasus/` **直下**だけを列挙する [s2-plan.md:186](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:186)。一方 runtime は nested path も未分類として拒否する設計 [s2-plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:74)。既に `tools/pegasus/probes/` には Python・shell・PBS entry が存在する。
- 具体例: probe 担当者が `tools/pegasus/probes/collect_t500.py` を login collector として追加しても、直下集合は変わらないので meta-test は赤にならない。後で Claude Bash が README の手順を踏んだ時点で初めて拒否される。
- 修正案: repo から実行可能な `.py` / `.sh` / `.pbs` と executable regular file を再帰列挙して registry と一致させる。nested を一律 compute-only とするなら、現在分も明示登録し、nested login entry を禁止する契約を機械検査する。
- 成果物影響: 未修正では nested collector の final receipt が作れず、レポートが参照する env contract 集合からその attempt が欠落する。

### R4 — real / high: (P4) の hook-side 正本は分類根拠の正本になれず、二重管理を残す

`guard_bash.py` は Claude Bash adapter にすぎず、資源分類・一次 gate・運用手順の所有者ではない。[hooks/README.md:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/README.md:78)

| ドリフト経路 | 現行/提案検査 |
|---|---|
| 直下実体 ↔ hook 分類 key | 提案 meta-test が停止。ただし直下・tests 実行時のみ |
| `login-ok` key ↔ `_SANCTIONED_PATHS` | 派生集合と提案 meta-testが停止 |
| hook class ↔ runbook の `local-ok/unknown`・実測・pin | **停止しない** |
| hook class ↔ README の「login node で実行」 | **停止しない** |
| runbook task 表 ↔ `dispatch_compute.py:TASKS` の `{task: child_script}` | `check_docs.py` が停止 [check_docs.py:2228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/check_docs.py:2228) |
| `TASKS` の env allowlist・site gate ↔ docs/hook | **停止しない**。checker が抽出するのは `child_script` だけ [check_docs.py:2179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/check_docs.py:2179) |
| runbook の測定値 ↔ 現行 cap・入力・pin | **停止しない**。runbook 自身も inventory 同期しか保証しない [pegasus-runbook.md:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/docs/pegasus-runbook.md:389) |

- 具体例: hook 行を `login-ok` に変え、behavior test も同時変更すれば、runbook に測定がなくても land できる。逆に README に login 手順を追加して hook を更新し忘れても止まらない。
- 修正案: Pegasus 側に単一の machine-readable admission registry を置き、`path`、三値 class、理由種別、primary gate、cap 契約、measurement evidence ID を持たせる。hook はそこから exact `local-ok` path を投影する。README/runbook は値を再掲せず registry/evidence を参照する。`TASKS` は自動 dispatch enum という別概念なので正本を維持し、既存 `check_docs` 同期を残す。
- 成果物影響: 未修正では class drift により、正当な collector receipt が欠落するか、未測定 entry が login で走って wrong-site/不完全成果物を生成する。

### R5 — real / high: (P1') を厳密適用すると既存 sanctioned paths も失格するが、裁定がない

- 根拠: 現在の sanctioned は dispatcher、fetch、3 submitter [guard_bash.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:174)。しかし dispatcher は scheduler 出力を `capture_output=True` で全文保持してから64 KiBへ切る [dispatch_compute.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/dispatch_compute.py:339)。fetch も全 git stdout/stderr を保持し [fetch_third_party.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/fetch_third_party.py:147)、任意 `--repo-root` を受ける [fetch_third_party.py:672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/fetch_third_party.py:672)。実測でも alternate root が ALLOW [probe_baseline.json:111](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/probe_baseline.json:111)。さらに `submit_silo_ladder_rung1.sh` は runbook 上すでに `unknown` [pegasus-runbook.md:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/docs/pegasus-runbook.md:393) なのに sanctioned。
- 具体例: P1' を global invariant とすれば、fetch の既存実測値だけでは足りず、現在 ALLOW の5 entryを denyへ落とす必要がある。
- 修正案: P1' を「新規昇格だけ」に適用するのか「全 login-ok」に適用するのか明示裁定する。global なら cap/実測を追加するか ALLOW→DENYを受理する。prospective なら `legacy-admitted` を隠さず記録し、P1'を満たす `local-ok` と同一視しない。
- 成果物影響: global denyなら dispatch receipt、certification/floor/silo submit receipt、third-party staging が作れない。grandfatherなら入力次第で login 資源上限を超える受理集合が残る。

### R6 — real / high: (P2') は現状では妥当な段階導入ではなく、成果物主張と衝突する中途半端な scope

- 根拠: 追記は本 wave の cap を `collect_receipt.py` に限定し、他 entry は `unknown`/denyとする [brief-addendum.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/brief-addendum.md:50)。ところが段2プランは `collect_receipt`、`collect_t126`、`submit_t126` の3件を ALLOWへ反転すると残している [s2-plan.md:194](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:194)。実装対象一覧にも collector cap が入っていない [s2-plan.md:277](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:277)。brief は T126 receipt 経路が開くことを成果物影響としている [brief.md:70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/brief.md:70)。
- 具体例: 追記に従えば T126 submitter/collector は denyのままなので、T126 final/failure receipt は Claude Bash 面から閉じられない。プランに従えば無上限 collectorを許可する。
- 判定: **現在は (a) 中途半端で族を閉じない**。ただし「calibration collectorだけを安全化し、T126は明示的後続」と成果物主張を狭めれば、(b) 妥当な段階導入へ変えられる。
- 修正案: 段2プランを追記後の内容で再発行し、ALLOW変化を安全化・実測済み `collect_receipt` だけに限定する。T126成果物を本 wave の完了条件から外して個別 follow-up を作る。T126まで含めるなら、scope拡張の裁定を得て両 entryの全入力 capと実測を追加する。
- scope過多: `make_acquisition_receipt.py` は全 entry 表へ載せること自体は必要だが、欠陥例や新規 allow対象に数えるべきではない。compute job 内 helperである [certify_calibration.sh:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/certify_calibration.sh:633)。
- 成果物影響: 未修正では T126 qualification report の final receipt 参照が欠落するか、無上限 collectorを経由した不安定な受理集合になる。

### R7 — real / medium: P3 の役割二分と二値 path class は実装の意味を表せない

直下18実行体の実態は次の4群だった。

| 群 | entry |
|---|---|
| login-side 手順 | `collect_receipt.py`, `collect_t126_qualification.py`, `fetch_third_party.py`, `submit_{certify,floor,silo_ladder_rung1,t126_qualification}.sh` |
| mixed/self-gated | `dispatch_compute.py` |
| compute job body | `certify_calibration.sh`, `floor_campaign.sh`, `floor_scoping.sh`, `silo_ladder_rung1.sh`, `smoke_probe.sh`, `t126_qualification.sh`, `t141_region_profile.sh` |
| compute-only helper/semantic | `exec_calibrate.py`, `make_acquisition_receipt.py`, `run_probe.py` |

- 根拠: dispatcher は同一 path の通常 modeで qsubし、生成 jobから同じ pathを `--job-run` で再起動する [dispatch_compute.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/dispatch_compute.py:434)。`--job-run` 側だけ hostname gateを持つ [dispatch_compute.py:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/dispatch_compute.py:547)。既存テスト helper は常に `bnode114` を注入しており、login拒否を直接 pinしていない [test_pegasus_dispatch_compute.py:2475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_pegasus_dispatch_compute.py:2475)。`run_probe.py` は軽量でも計算ノード環境の観測そのもの [run_probe.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/run_probe.py:3)。
- 具体例: `dispatch_compute.py` を単に `login-ok` と記録したまま `_job_run` hostname gateが削除されても、分類meta-testは通る。`run_probe.py` をメモリ実測だけでlocalに倒すと、軽量だが意味の違うlogin profileを生成する。
- 修正案: class名を「役割」ではなく login admission に限定し、別フィールドで `resource_state`、`semantic_site`、`primary_gate`、`reason` を保持する。`--job-run` を login hostnameで呼び、子を起動せず rc=16になるbehavior testを追加する。
- 成果物影響: gate退行時は `result.json.hostname` が bnode でなく `pegasus0N` となり、`child_rc` がwrong-site test/provenance結果を表す。`run_probe` 誤分類なら allocation profile参照がlogin観測へ変わる。

### R8 — real / medium: DW-G03 の「3例」は独立していない

- 根拠: brief は4つのDENYから「3例目・DW-G03充足」を宣言する [brief.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/brief.md:16)。しかし `submit_t126` と `collect_t126` は同じT126 producer/consumer鎖であり、`make_acquisition_receipt.py` は正しくdenyされるcompute helper [s2-plan.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:7)。`collect_receipt.py` も現規範ではdenyが正しい [brief-addendum.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/brief-addendum.md:18)。
- 具体例: T126 submitterとcollectorを2 reproductionとして数えるのは同一workflowの前後段を言い換えただけ。`make_acquisition` は再現ですらない。
- 修正案: familyを「文書化されたlogin workflowとadmission/resource registryの不整合」と定義し、独立例を calibration鎖とT126鎖の2 workflowとして示す。T126を本waveで閉じないなら、DW-G03充足ではなく「registry mechanismの段階導入」と記録する。T483の`-m` parser familyは別に数える。
- 成果物影響: 未修正では wave report/台帳がT481を族完了と記録する一方、T126 final receipt参照は実際には欠落したままになる。

## gate の効く層

| 層 | 実効性 |
|---|---|
| Claude の直接 Bash literal | 効く。LOGIN/SUSPECT時だけ `decide()` の重量判定へ入る [guard_bash.py:947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:947) |
| Codex 子/subprocess | 効かない。hook未配線 [AGENTS.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/AGENTS.md:18) |
| script file 越し | 効かない。`bash script.sh` は明示的にALLOW [test_hooks.py:786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:786) |
| ユーザー端末 / cron / IDE | 効かない [decisions.md:4599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/docs/decisions.md:4599) |
| CI | meta-testを実行した時だけrepository driftを検出。runtime admissionではない |
| entry自身のsite gate | entryごと。dispatcher等にはあるが全Pegasus entry共通ではない |

brief と既存runbookは「第二防壁」「全経路保証なし」と明記しているため、恒真保証そのものは主張していない。ただし段2プランにもこの表を入れ、meta-testの「新規entryを足すと赤」を「直下・suite実行時」に限定すべきである。これはR3以外は文言上の nit。

## 既存 pin の検査

テストを甘くする変更は不要であり、次を保持すべきである。

- [test_hooks.py:915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:915) の `certify_calibration.sh` / `run_probe.py` は、「sanctioned siblingではない」から「明示 classified compute-only」へ意味が変わるが、期待bitはDENYのまま。汎用table testへ吸収して削除しない。
- [test_hooks.py:977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:977) の `exec_calibrate.py` は anti-glob / arbitrary-exec controlとして独立維持する。分類key一致だけではruntimeがclassを無視する変異を殺せない。
- プランの全compute entry behavior test [s2-plan.md:159](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:159) を追加すること自体は強化方向であり、既存pinを残す限り real finding はない。

## 総括

- **real 所見: 8件**
- 最重要3件:

  1. **R1:** 会計summaryだけのcapでは `collect_receipt.py` は入力有界にならず、安全な`login-ok`へ昇格できない。
  2. **R2:** `unknown → evidence付き local-ok` のlifecycleがなく、制度化したように見えて個別sanctionとbootstrap循環が残る。
  3. **R4:** hookを分類正本にすると、runbook実測・README手順・一次gateとのドリフトが機械停止されず、二重管理を移設するだけになる。