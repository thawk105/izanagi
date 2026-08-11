## 所見

### 1. blocker — `--run-root` 指定時には git 配下拒否が働かない

対象: [docs/phase3-s8c-autonomous-trial-runbook.md:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/docs/phase3-s8c-autonomous-trial-runbook.md:253)

> 「一意な `--trial-id` と `--run-root`」  
> 「`IZANAGI_EXPLORATION_OUTPUT_ROOT` は git 配下を拒否し」

この並びは、明示した `--run-root` も環境変数の admission を受けるように読めるが、実装は違う。[p3_autonomous_workload_trial.py:2290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/orchestrator/campaign/p3_autonomous_workload_trial.py:2290) は `--run-root` があればそれを直接採用し、`IZANAGI_EXPLORATION_OUTPUT_ROOT` の検査を呼ばない。環境変数側の git-ancestor 拒否は [layout.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/orchestrator/campaign/layout.py:293) の「明示引数がない経路」だけである。明示 root には worktree-container 拒否しかなく、通常の git repository 配下は通り得る。

最小修文:

> `(2) ... 一意な --trial-id と、相互に異なる resolved run_root。(3) 推奨経路は、repo 外かつ git ancestor を持たない job 専用 base を IZANAGI_EXPLORATION_OUTPUT_ROOT に設定し、--run-root を省略する。--run-root を明示する場合、その path の repo 外・非 git 条件は人手確認であり、環境変数の拒否 gate は適用されない。`

成果物影響: git 配下の探索 artifact が親 directory consumer や tracked/untracked 検査へ混入し、report の参照 path、台帳の成果物集合、受入全走の観測集合を変え得る。

### 2. blocker — 「投入前に request ID」は実行不能

対象:

- [docs/phase3-s8c-autonomous-trial-runbook.md:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/docs/phase3-s8c-autonomous-trial-runbook.md:257)
- [docs/pegasus-runbook.md:1007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/docs/pegasus-runbook.md:1007)

> 「投入前に期待集合 (N・trial_id・workload・run_root・request ID) を書き出す」

scheduler の request ID は投入結果として初めて得られるため、投入前には書けない。逐語どおりでは全条件を満たす fan-out が存在せず、後書きを「事前登録」と呼ぶか、架空 ID を書く運用を誘発する。

最小修文:

> `投入前に N 個の expected slot と trial_id・workload・run_root・submission nonce を固定する。各投入直後、scheduler が返した request ID と receipt を対応する slot へ束縛し、集計開始前に group manifest を完成させる。`

§7.5 の既存逐語も同時に直すべきである。

成果物影響: request と report/receipt の対応を誤ると、group ledger が別 request の rc や hash を参照し、欠落 job を含まない受理集合を作り得る。

### 3. should — 失敗時に存在しない report/hash を要求している

対象: [docs/phase3-s8c-autonomous-trial-runbook.md:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/docs/phase3-s8c-autonomous-trial-runbook.md:258)

> 「完了時に全 N 本の rc・report・journal hash を照合する」

起動失敗や supervisor crash では report、場合によっては journal も存在しない。§7.5 は成果物欠落を正規の失敗分類として保存すると定めており、この逐語とは整合しない。「全 N 本に hash があるまで再投入」と読むと repeat-until-success に寄る。

最小修文:

> `全 N slot の terminal state・rc・report/journal の存在または欠落を照合し、存在する artifact は hash を照合する。欠落を含む group は incomplete のまま保存し、成功分だけを集計しない。`

成果物影響: 欠落 artifact を ledger から消すか再投入結果で置換すると、失敗 report の参照と group の受理集合が変わる。

### 4. should — 失われる保証の説明が実装より強く、`lifecycle-start-once` は対象外

対象: [docs/phase3-s8c-autonomous-trial-runbook.md:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/docs/phase3-s8c-autonomous-trial-runbook.md:261)

> 「割ったときに失われるのは機構ではなく保証である」  
> 「`_check_workload_coverage` の期待集合被覆、共有 wall 予算、… trial 単位の start-once がいずれも 1 process 内へ縮む」

三点不正確である。

- `_check_workload_coverage` は全 workload の実行を要求せず、実 cell が requested list の prefix であり、欠落 suffix が終端事象で説明されることを検査する。
- shared wall は N 個の独立予算へ変わるため、保証だけでなく予算意味論も変わる。
- 許可対象の exploratory 起動は lifecycle ledger を使わない。`lifecycle-start-once` は「process 内へ縮む」のではなく非適用である。registered 側も保証範囲は同一 lifecycle ledger／repository 内で、process-local ではない。
- `CrossRoleSessionTracker` が process-local で、invalid parse の session を report 間の valid `child_id` だけでは代替できない、という説明はコードと一致する。

最小修文:

> `各 process 内の検査は残るが group-level 保証は無い。workload coverage は singleton report ごとの prefix/欠落理由検査に縮み、wall 予算は N 個の独立予算になり、session 相異検査は process 間を覆わない。exploratory 起動には lifecycle-start-once 自体が適用されない。`

成果物影響: exact workload 被覆や一意性が機械保証済みだと誤認すると、欠落・重複 workload や N 倍の wall 予算を持つ report 群が同じ ledger 集合として扱われる。

### 5. should — campaign freshness gate の再走拒否を恒真に書いている

対象: [docs/phase3-s8c-autonomous-trial-runbook.md:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/docs/phase3-s8c-autonomous-trial-runbook.md:267)

> 「同一 trial/config の再走は build 経路の campaign freshness gate で拒否される」

実装の `_assert_fresh_campaign_state` が拒否するのは既存 checkpoint を読めた場合である。同じ §5 の既存記述も、state 生成前の crash と freshness 検査の並行 race は保証対象外と明記している。したがって無条件の再走拒否ではない。

最小修文:

> `既存 checkpoint がある同一 trial/config の build 再走は campaign freshness gate で拒否される。ただし state 生成前の crash と並行 race は覆わないため、新 trial-id/new run-root は機械保証ではなく必須の運用規範である。`

成果物影響: gate を完全な一回性保証と誤認すると、同一 trial/campaign identity の report が複数生成され、台帳上の対応関係と参照集合が曖昧になる。

### 6. should — 未測定を「効かない」と断定している

対象: [docs/pegasus-runbook.md:1066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/docs/pegasus-runbook.md:1066)

> 「本番の律速 (role 呼び + build / verify / bench) には効かない」

fixture + `--no-build` の実測から言えるのは、それらへの利得を測っていないことまでである。とくに許可対象の no-build pilot でも実 role 呼びは並行化されるため、「効かない」は根拠を越えている。

最小修文:

> `本番の律速である role 呼び・build・verify・bench への利得は測っておらず、この比からは主張できない。`

成果物影響: certified 値は直接変わらないが、実 role を使う exploratory pilot の投入判断と、生成される report／台帳集合を不当に減らし得る。

### 7. nit — RP-6 の配置は妥当だが、§7.5 に trial 固有説明を重複させすぎている

対象: [docs/pegasus-runbook.md:1063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/docs/pegasus-runbook.md:1063)

> 「`for workload in selected:` を割る実装はしない — 足りないのは…」  
> 「N 起動自体は今日そのまま動く…」

P1 の「各文書に一つの項を置く」という解釈は妥当で、6 条件を逐語一行へ潰す必要はない。ただし上記の verifier 理由と fixture 実測は §5 と評価 package の重複で、運用規範として必要なのは許可形・build 禁止・§5 へのポインタである。

最小修文: §7.5 は次まで短縮し、検証機構と実測の説明を削る。

> `8c workload fan-out は、8c runbook §5 の全条件を満たす探索 pilot の N 起動だけを許す。本体 loop の分割は実装しない。`

成果物影響: 現時点の値は変わらないが、二重正本が将来ずれると、運用者が異なる条件集合を参照して report を採否する。

## 裁定との整合性

RP-1、RP-2、RP-3、RP-5 は意図どおり明文化されている。RP-4/P2 も、leaf の partial 意味論を変更せず、group では成功 N-1 本だけの集計を禁止しているため妥当である。6-node 配置、build 付き fan-out、成功分のみの集計、N 本と旧 1 trial の同値扱いは、本文上はいずれも明示的に禁止されている。

コード由来のうち、`CrossRoleSessionTracker` の process-local 性、`bench_lock`／`competing_bench_pids` の射程、manifest の exact 6 と hash 束縛、manifest の四 field は確認できた。テスト・ビルドは実行しておらず、緑は主張しない。

## 総括

**blocker 2 件を直すまで、この差分を運用規範としてこのまま採用してはならない。**