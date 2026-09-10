結論は NO-GO です。8-file の disk drift 検査自体は機能しますが、「certified 経路が source-bound」「enforcement 閉包」という名乗りは成立しません。

### A-01 / 8 path は enforcement 閉包ではなく、列挙した disk file 集合にすぎない / real — must-fix

- **根拠:** `pipeline.py` は閉包外の verifier・calibrator・buildcache・build_admission・source_digest 等へ判定を委譲しています。[pipeline.py:30–60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/pipeline.py:30) の `verify_trace_dir` の戻り値が [pipeline.py:885–919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/pipeline.py:885) で正しさを決め、[pipeline.py:1019–1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/pipeline.py:1019) で COMMIT に到達します。`execution_guard.py` も閉包外の `env_attestation` / `site_policy` を import し、site 判定と attestation 比較を委譲しています。[execution_guard.py:28–31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/execution_guard.py:28)、[execution_guard.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/execution_guard.py:141)、[execution_guard.py:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/execution_guard.py:611)。独立した T126 は、まさにこれらを含む大きい code identity 集合を持っています。[qualification/contract.py:38–76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/qualification/contract.py:38)
- **根拠:** D259 は raw reader / report 投影等を延期したまま「proof chain が全経路で完結した」と名乗れないとしています。[decisions.md:11966–11970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/docs/decisions.md:11966)。段2は caller closure 延期だけを supersede する計画です。[stage2-plan.md:41–50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage2-plan.md:41)
- **成果物影響:** verifier・attestation・source helper の変更だけで `certified`、COMMIT、oracle/report の受理値が変わる一方、8-key authority は不変です。
- **最小の修正案（scope 内）:** 「enforcement 閉包」「certified 経路が source-bound」を撤回し、次までに限定してください。

> `require_environment_contract=True` で `ident.ensure_campaign_identity` の source 検査が実際に完了した呼出しについて、検査中に読み取った列挙 8 個の `.py` disk bytes は、その呼出しが authority に採用した `contract_loader_commit` の同 path Git blob と一致した。これは未束縛 bootstrap、Git executable、既ロード Python state を信頼する 8-file drift check であり、in-process/pyc/動的 callable、検査後の変更、admission/report/selection、閉包外 helper の source binding は保証しない。

完全な推移閉包の束縛は scope 外です。

### A-02 / `ensure_campaign_identity` は certified sink の支配点ではない / real — must-fix

- **根拠:** 通常の `loop.run_campaign` は確かに [loop.py:146–150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/loop.py:146) を通ります。しかし `pipeline.evaluate` の引数には identity/source-gate capability がなく、単独で WAL を書けます。[pipeline.py:477–496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/pipeline.py:477)、[pipeline.py:1021–1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/pipeline.py:1021)
- **根拠:** 低層の `wal.append` / `write_lock` / `acquire_lock_atomic` も ident を呼びません。[wal.py:362–375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/wal.py:362)、[wal.py:1554–1596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/wal.py:1554)。実在する別経路として、S8b oracle は独自 lock を直接獲得し [s8b_oracle_driver.py:979–1012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/s8b_oracle_driver.py:979)、`evaluate_fn` を直接呼びます。[s8b_oracle_driver.py:1351–1393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/s8b_oracle_driver.py:1351)。T126 も独立 code-identity 経路から直接呼びます。[t126_driver.py:489–550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/qualification/t126_driver.py:489)
- **根拠:** artifact admission は完成済み bytes を検査するだけで、`ensure_campaign_identity` が実行された証拠を要求しません。[artifact_admission.py:656–670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/artifact_admission.py:656)
- **成果物影響:** clean lock 作成後に drifted code から `pipeline.evaluate` または低層 WAL writer を直接呼んでも、live source gate を通ったか区別できない成果物が残ります。
- **最小の修正案（scope 内）:** 名乗りを「実際に ident を通った呼出し」に限定する。全 certified sink に gate receipt/capability を要求する変更は scope 外です。

### A-03 / 「ensure 成功時点で一致」は TOCTOU により偽 / real — must-fix

- **根拠:** 新規 lock は source capture を [ident.py:465–467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:465) で終えた後、activation・encode を経て [ident.py:484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:484) で初めて lock を書きます。この間の再検査はありません。resume も live 検査後にそのまま return します。[ident.py:449–455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:449)
- **根拠:** no-follow reader が守るのは個々の read 前後だけです。[contract_loader_binding.py:146–225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:146)。これは既知の F130「検査と観測の時点ずれ」と同型です。[failures.md:3338–3349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/docs/failures.md:3338)
- **成果物影響:** capture 後・lock 獲得前の変更により、ensure が成功を返した時点では disk が authority commit と不一致になり得ます。
- **最小の修正案（scope 内）:** 段2案の「成功した時点」を「検査が読み取った bytes」に変更する。成功時点までの強い原子性は scope 外です。

### A-04 / 未束縛の検証器自身が root of trust であり、広い名乗りを成立させない / real — must-fix

- **根拠:** brief は `campaign_lock.py` / `contract_loader_binding.py` を明示的に除外しています。[brief.md:46–53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/brief.md:46)。前者は exact path 集合と codec を決め [campaign_lock.py:27–30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/campaign_lock.py:27)、[campaign_lock.py:153–172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/campaign_lock.py:153)、後者は capture/live/committed の全比較を実装します。[contract_loader_binding.py:320–373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:320)。どちらかを no-op/縮小へ変えれば自己検出されません。
- **根拠:** brief の「F36」参照は、少なくとも `docs/failures.md` の F36とは一致しません。そこは placeholder の空証明問題です。[failures.md:792–813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/docs/failures.md:792)
- **成果物影響:** 未束縛 validator の変更だけで authority の key 集合・blob 比較・admission 受理集合を任意に変えられます。
- **最小の修正案（scope 内）:** 両 module と Git executable を「信頼する未束縛 bootstrap」と新 D に明記し、F36 参照を訂正する。この残穴は accidental drift モデルなら受容可能ですが、「certified 経路 source-bound」には不成立です。独立 launcher からの validator pin は scope 外です。

### A-05 / 計画済みテストは内部 verifier を固定するが、実経路の呼出し辺を固定しない / real — must-fix

- **根拠:** 予定される exact sentinel・live/committed parameterization は [stage2-plan.md:80–103](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage2-plan.md:80) の内部 seam を検査します。現行 fixture は temp repo に inert な file bytes を置き、実際に import 済みの `ident` / `pipeline` は変更せず `_REPO_ROOT` だけ差し替えます。[test_t671_source_binding.py:50–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:50)、[test_t671_source_binding.py:119–140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:119)
- **根拠:** `loop -> ident` 辺を削除しても、この unit test は ident を直接呼ぶため緑です。これは F127 の「helper 本体は検査したが委譲辺が未固定」と同型です。[failures.md:3284–3296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/docs/failures.md:3284)
- **成果物影響:** driver から ident を外す、または bound wrapper から閉包外 helper へ機能を逃がす改変が、追加テストをすべて通しつつ COMMIT 受理集合を広げられます。
- **最小の修正案（scope 内）:** certified driver ごとに「最初の lock/WAL sink より前に ident を1回通る」呼出し辺テストを追加し、T126/S8b等の別系統を明示除外する。各 parameterized 負例は例外理由だけでなく対象 path も assert してください。

### A-06 / 親 brief の「受理集合は縮むだけ」は実装と両立しない / real — must-fix

- **根拠:** brief は「閉包が広がった分だけ縮む」としています。[brief.md:54–55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/brief.md:54)。一方、段2自身が exact-2 map は受理→拒否、exact-8 map は拒否→受理で、wire 集合は部分集合でないと正しく認めています。[stage2-plan.md:111–132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage2-plan.md:111)
- **根拠:** 現 checkout `b0b84837` で 32 lock・v2 0 は独立再確認できました。ただし、これは repository corpus の事実であり、同じ `campaign-lock/v2` schema の一般受理集合や外部 artifact 不在の証明ではありません。
- **成果物影響:** exact-8 v2 は新規受理され、exact-2 v2 は拒否されるため、同じ schema_version の受理言語が双方向に変わります。
- **最小の修正案（scope 内）:** 段4で親 invariant を「現存 repository corpus は不変、v2 wire language は exact-2 から exact-8 へ置換」と明示訂正する。外部 v2 を排除できないなら schema bump は scope 外の追加裁定です。

### N-01 / admission 時の6-file disk drift は一件も拒否されない / real — nit（計画は認識済み）

- **根拠:** live verifier は disk を読みます。[contract_loader_binding.py:336–355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:336)。committed verifier は Git blob/digest だけです。[contract_loader_binding.py:358–373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:358)。admission は後者だけを呼びます。[artifact_admission.py:549–564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/artifact_admission.py:549)。段2もこの限界を明記しています。[stage2-plan.md:46–50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage2-plan.md:46)
- **成果物影響:** admission decision は current 8-file disk drift で変わらず、`validator_sha256` も記録されるだけで既知値と比較されません。
- **最小の修正案（scope 内）:** この正例をテストで固定し、名乗りを admission 時点へ拡張しない。live admission 化は scope 外です。

### N-02 / 「安定した6-file disk driftが ident でも発火しない」は refuted / refuted — nit

- **根拠:** capture/live は定数の全要素を無条件に走査します。[contract_loader_binding.py:325–355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:325)。新規 lock は [ident.py:465–480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:465)、resume は [ident.py:365–373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:365) から到達します。
- **成果物影響:** 信頼済み verifier を実際に通る通常経路では、追加6 pathの静的 disk drift により新規作成/resume の受理集合は意図どおり縮みます。
- **最小の修正案（scope 内）:** per-path test を維持し、対象 path をエラーメッセージでも固定する。

### N-03 / 既存テストの期待値緩和は現プランからは確認できない / refuted — nit

- **根拠:** 段2は exact golden を削らず8 tupleへ更新し、無効になる digest fixture と意味が変わる `[-1]` を明示修正しています。[stage2-plan.md:28–39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage2-plan.md:28)。また誤理由で緑になる既存 test も特定しています。[stage2-plan.md:52–78](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage2-plan.md:52)
- **成果物影響:** 計画どおりなら既存拒否集合を甘くする変更はなく、fixture の偽緑が解消されます。
- **最小の修正案（scope 内）:** 実装時に assert 削除・例外型だけへの緩和・skip 化を禁止し、各負例の対象 path/reason を保持する。

### N-04 / P1 の歴史的 wire 名据え置きは correctness hole ではないが、今が最後の低コスト改名窓 / real — nit

- **根拠:** `contract_loader_*` が8-file enforcement setを表す二義化は brief 自身も反対論拠として認識しています。[brief.md:69–76](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/brief.md:69)。段2も exact rename 面を列挙しています。[stage2-plan.md:134–168](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage2-plan.md:134)
- **成果物影響:** hash 値や現在の受理集合は変わりませんが、最初の v2 artifact 以後は非 loader 6 path を loader key として恒久解釈する負債になります。
- **最小の修正案（scope 内）:** repository-local v2 不在を互換性根拠として採るなら今 exact rename する。P1を維持するなら「歴史名であり loader 集合ではない」を wire contract と新 D の双方に永久注記する。

## 総括

- **NO-GO**
- **must-fix 6件、nit 4件**
- 8-file live disk drift detector 自体は成立する。
- 「enforcement 閉包」「certified 経路が source-bound」「ensure 成功時点で一致」は成立しない。
- 段4で名乗り、停止点の射程、v2受理言語の置換を裁定し直す必要がある。
- read-only 静的検査のみで、ファイル変更・pytest 実行は行っていない。