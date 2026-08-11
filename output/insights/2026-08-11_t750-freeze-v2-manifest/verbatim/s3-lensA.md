判定は **NO-GO**。提案どおり実装すると、自己整合した artifact を「人間承認済み」と誤認し、公式 consumer が未承認 manifest を受理できる。

## 所見

### 1. BLOCKER — Git record による「人間承認」が恒真化する

根拠: P1 は非 merge commit と逐語 `AI-Agent: none` を承認根拠にする一方、それが暗号学的証明でないことを認めている（[s2b-plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md:9)、[s2b-plan.md:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md:242)）。実装側も commit message を検査するだけである（[s8b_ratified_freeze.py:525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_ratified_freeze.py:525)、[s8b_ratified_freeze.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_ratified_freeze.py:537)）。これは、artifact の存在を認可証明にしてはならないという D86(8) に正面から反する（[decisions.md:3773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/docs/decisions.md:3773)、[decisions.md:3797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/docs/decisions.md:3797)）。

成果物への影響: 同一主体が spec・budget・approval commit を作れば、caller 選択の `n`、seed、block schedule、除外理由、予算が「人間承認済み」となり、certified winner と ledger 上限が変わる。

直し方: approval JSON/Git trailer は監査記録に限定する。発効には、人間だけが保持する鍵・権限による署名または AI から到達不能な明示 activation capability を要求する。この trust root の追加裁定までは `no-approved-spec` のまま止める。

### 2. BLOCKER — A-9 は manifest CLI にしかなく、公式 driver/report が迂回できる

根拠: exact configuration 検査は明示的に CLI 専用で、generic `build_manifest` には入れない（[s2b-plan.md:307](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md:307)、[s2b-plan.md:321](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md:321)）。現 manifest schema には spec/approval 参照がなく（[s8b_oracle_manifest.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_manifest.py:34)）、generic builder は holdout の部分集合だけを検査し（[s8b_oracle_manifest.py:693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_manifest.py:693)、[s8b_oracle_manifest.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_manifest.py:729)）、schedule hash は document 自身から再計算するだけである（[s8b_oracle_manifest.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_manifest.py:749)、[s8b_oracle_manifest.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_manifest.py:858)）。公式 report もこの generic verifier を使う（[s8b_oracle_report.py:1747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_report.py:1747)）。

成果物への影響: 全 holdout × 任意の1 configuration、`n=1` の自己整合 manifest を通すと、report はそれだけを expected cells にし（[s8b_oracle_report.py:1713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_report.py:1713)）、judge は唯一の eligible configuration を `unique-best` にする（[s8b_oracle_judge.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_judge.py:232)）。

直し方: official manifest schema に approved spec と approval の path/hash を構造化して含め、`verify_manifest` で active freeze の holdout/configuration 集合、全 schedule parameter、spec hash を再検証する。driver/report/judge へ authority-bound な sealed typeを伝播させ、generic builder 由来 manifest は公式実走不能にする。この変更は現 scope 外の consumer 層を含む裁定が必要。

### 3. BLOCKER — budget approval が ratified proof chain から消える

根拠: plan が保証するのは producer 内の「入力 budget と approval record の一致」だけであり、ゼロ・巨大有限値も許す（[s2b-plan.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md:11)、[s2b-plan.md:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md:81)、[s2b-plan.md:141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md:141)）。v2 schema・transition・semantic verifier には budget approval の構造化された参照や equality edge がない（[s8b_ratified_freeze.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_ratified_freeze.py:96)、[s8b_ratified_freeze.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_ratified_freeze.py:128)、[s8b_ratified_freeze.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_ratified_freeze.py:146)、[s8b_ratified_freeze.py:930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_ratified_freeze.py:930)）。`refreeze_note` 内の path/hash 文字列は verifier が意味検証しない。

成果物への影響: producer を経由しない自己整合 g1 にゼロ予算を入れれば実走・選択を停止でき、巨大値なら探索上限を事実上撤去し、ledger の limit/consumption と得られる観測集合が変わる。

直し方: v2 に構造化した `budget_authorization` を追加し、transition、ratified verifier、proof adjacency で trusted approval bytes と exact 束縛する。ただし完全性の束縛だけでは所見1の認可欠陥は直らないため、同じ外部 trust root が必要。

### 4. BLOCKER — 同一 generator module の編集と v1 受理集合不変は両立しない

根拠: M-1 は T-080 receipt 経路の CLI 成功を module 編集一般へ拡張している（[s1-brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s1-brief.md:41)）。しかし v1 `verify_document` は generator の現 worktree SHA を直接照合する（[s8b_holdout_freeze.py:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_holdout_freeze.py:648)、[s8b_holdout_freeze.py:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_holdout_freeze.py:716)）。T-080 例外は canonical path の専用 CLI helper に限られる（[s8b_holdout_freeze.py:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_holdout_freeze.py:833)、[s8b_holdout_freeze.py:878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_holdout_freeze.py:878)）。既存関数本体や `TOP_LEVEL_KEYS` を変えなくても、同じファイルへ新 producer を追加すれば SHA は変わる。

成果物への影響: 編集前の現行 generator SHA を持つ正当な v1 document が direct `verify()` / `verify_document()` で拒否へ変わり、その consumer では freeze gate が赤となって manifest・report・ledger が生成されない。

直し方: v1 generator file を一切編集せず新 module を v2 producer identity として認めるか、direct API まで含む migration semantics に変更する必要がある。どちらも T750 の producer identity または「v1受理集合不変」の裁定変更を要する。

### 5. MAJOR — 新 writer は堅いが、旧 writer から canonical namespace に到達できる

根拠: 提案された `SafeA` を raw string のまま実装すれば、絶対 path、`..`、大小文字差、末尾 slash、既存 symlink/hardlink leaf、親 symlink、検査後差替えは exact literal・held dirfd・`O_NOFOLLOW|O_EXCL` で閉じる（[s2b-plan.md:153](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md:153)）。しかし既存 `generate(output_path=...)` は任意 path の親を作って通常の `open("x")` を行い（[s8b_holdout_freeze.py:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_holdout_freeze.py:577)）、generic manifest writer も任意 parent に temporary hardlink を作る（[s8b_oracle_manifest.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_manifest.py:772)）。plan 自身もこの到達可能性を残す（[s2b-plan.md:454](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md:454)）。

成果物への影響: canonical namespace に新規ファイルを置くと `namespace-dirty` となり、active freeze が解決不能になって certified selection・report・ledger がすべて欠落する。

直し方: canonical namespace deny を全 writer/API の共通最外層へ置く。旧 API の受理集合を狭めるため、v1 不変条件を「document 判定」に限定する裁定、または canonical namespace を OS 権限で writer から隔離する必要がある。

## 境界確認

- `reps` / `extime` は現 run-contract validator で固定され、`oracle_shared is True` も検査されるため、単独の迂回は見つからない。`allowed_excluded_reasons` は該当 cell を `unknown` にするため、直接 `unique-best` を作る面ではない（[s8b_oracle_judge.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest/orchestrator/campaign/s8b_oracle_judge.py:96)）。

- v2 candidate の key 集合と transition は既存 verifier と整合しており、「作れるが構造上発効不能」という矛盾は見つからない。問題は逆で、spec/budget authority edge がない自己整合 candidate でも proof chain を通り得る。

- M-2/M-3/M-4/M-6 は実装と一致した。M-5 の三検査が現 repo にないことも性質検索で確認したが、「新 CLI に純増すれば全層が閉じる」という一般化は成立しない。M-7 は新 producer 単体についてのみ真であり、旧 writer を含む namespace 全体については偽である。

## 総括

- **NO-GO**。
- Git artifact は人間認可の証明にならず、D86(8) 違反である。
- spec/budget の authority は manifest・ratified proof chain・consumer 層へ伝播していない。
- A-9 は generic manifest 経路で迂回でき、縮小 schedule が `unique-best` を作れる。
- 実装前に trust root、official manifest schema、consumer scope、v1互換境界の再裁定が必要である。