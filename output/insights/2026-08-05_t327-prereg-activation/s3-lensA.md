必須4ファイルはすべて全文読取できた。追加の静的照合のみ行い、ファイル変更・pytest・実走は行っていない。結論は **NO-GO** である。

### 1. P2 は「条件が揃った commit」ではなく、未充足の過去 commit を発効版にできる

**主張:** `git log -1 -- <文書>` は文書の最終変更しか示さず、12条件が成立した時点を示さない。現在の C08 は、未充足だった測定を後続実装によって遡及 green にできる。

**根拠:** [brief.md:29](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:29)、[s2-plan.md:18](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:18)、[s2-plan.md:128](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:128)、[phase3-8c-preregistration.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:24)。

**具体的な攻撃手順:**

1. `A`: §5 と文書を最後に変更するが、C06/C09/C12 などは未充足。
2. `M`: manifest の `prereg_commit=A` で測定し、結果を見る。`A` は `M` の祖先。
3. `Z`: 結果後に不足 consumer・wrapper・predicate を実装する。文書は触らない。
4. `effective(Z)=true`、かつ `activation_commit(Z)=A`。C08 の完全一致と ancestry は通るが、測定時 `effective(M)` は false だった。

また `A→M→P` で、`P` が §2 の誤字修正だけでも P2 は `P` へ移り、正当な旧 manifest が赤になる。結果後に manifest を `P` へ付け替えると、今度は後付け再 binding を誘発する。

**重大度:** blocker

**成果物影響:** 条件未充足時の trial が正式受理集合へ入り、その trial の variant が certified 選択となり、材料レポートの `prereg_commit` が実際には未発効だった `A` を指す。

**提案修正:** P2 を棄却し、manifest が pin する commit `C` について `effective_at(C)` を履歴 blobだけから再計算して true を要求する。さらに launch 時の `C` と activation report hash を run-start に焼き、acceptance でも同じ `C` を再検証する。

---

### 2. activation predicate と実走後 evidence が循環しており、恒真化か発効不能の二択になる

**主張:** §6 は実走前ゲートなのに、C06〜C10 は実走中・実走後にしか生まれない evidence を要求する。実 artifact を要求すれば永久に発効せず、コードや schema の存在で代用すれば恒真になる。

**根拠:** [phase3-8c-preregistration.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:79)、[phase3-8c-preregistration.md:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:93)、[s2-plan.md:119](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:119)、[brief.md:10](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:10)。

**具体的な反例:**

|述語|対象機構なしでも green にできる反例／発効不能性|
|---|---|
|C01|probe 入力のときだけ 1m/48 を返し、実 launcher では 100k/4 を使う。helper 名と返値だけでは sink を証明しない。|
|C02|arm 名と全 ID は injective にするが、on/off/swapped の descriptor payload をすべて on と同じにする。|
|C03|正しい形の未使用 registry を置く。T-325 は未登録 ID の探索実走を許すため、全実走捕捉にはならない。|
|C04|crash 全体停止 helper を追加するが、実 launcher は従来経路を呼ぶ。`code path` の存在だけなら green。|
|C05|完全な schedule artifact を生成するが、launcher は読まず独自順序で走る。plan は production consumer を要求していない。|
|C06|未使用の budget consumer を置けば存在検査は通る。実 bench 秒精算を要求するなら最初の実走前には evidence がなく赤。|
|C07|judge CLI と空の6セル表 generator を置けば通りうる。実結果表を要求するなら発効前には生成不能。|
|C08|一致する文字列と ancestry は作れるが、run-start/report は実走後にしか存在しない。|
|C09|未使用 CLI を「formal acceptance」と命名できる。実 build report を要求するなら事前判定できない。|
|C10|相互整合する mutable artifact 一式を再生成すれば green。外部 anchor がない。|
|C11|「走るな」という裁定の存在だけで SATISFIED 候補になっている。|
|C12|wrapper が存在しても直接 API で迂回できる。live allocation を証拠にすれば同じ `H` でも実行場所により真偽が変わる。|

したがって、名前・artifact 存在型は C02/C03/C05/C08/C11、CLI・code-path 存在型は C01/C04/C06/C07/C09/C12、自己整合だけで通る型は C10 である。予定された一変異ずつの negative control は、probe 特別扱い・dead path・テスト同時改変を捕捉しない。[s2-plan.md:254](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:254)

**重大度:** blocker

**成果物影響:** 前者では正式受理集合が永久に空になり、後者では arm・schedule・budget consumer が実在しない trial が入り、試行台帳と certified 選択の集合が拡大する。

**提案修正:** 三段階に分ける。

1. commitだけで決まる静的 prereg readiness。
2. manifest・schedule・allocation・clean checkout を束縛する launch admission。
3. bench 精算・result table・Layer 3・cross-binding を検査する post-run acceptance。

各 predicate は authoritative launcher/acceptance に対する end-to-end 変異で検証する。

---

### 3. §5 の値と、§4・§7・8b 参照先が freeze 対象外である

**主張:** ledger が pin するのは §5 の「欄名」と §6 の文だけで、閾値・floor・seed・検定選択・manifest 内容などの値を pin しない。停止規則や全件報告規則、normative な 8b の版も保護外である。

**根拠:** [brief.md:12](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:12)、[s2-plan.md:75](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:75)、[s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:93)、[phase3-8c-preregistration.md:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:52)、[phase3-8c-preregistration.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:69)、[phase3-8c-preregistration.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:79)。

**具体的な攻撃手順:**

1. `A` で floor/閾値 `T1` を記入して実走し、結果 `x` を見る。
2. `C` で同じ欄名の値だけを `T2=f(x)` に変える。保護 hash は不変なので gN は不要。
3. §4 の早期停止規則、または §7 の全件報告範囲も有利に変更する。これらも hash 外。
4. 新 manifest と report を `C` に再 binding し、旧出力を一貫した proof chain に載せ直す。

**重大度:** blocker

**成果物影響:** floor・判定閾値・検定有無・停止規則が結果適合的に変わり、成功条件を満たす variant、6セル判定表、材料レポートの結論が変わる。

**提案修正:** trial ごとに、§5 の全 typed value、normative な §§1/3/4/5/6/7、使用する 8b active generation/approval hash、evidence contract、manifest 内容を一つの canonical prereg bundle として pre-run pin する。

---

### 4. 「記録付きの条件緩和」を ledger が正当な改訂として受理する

**主張:** chain は無記録変更を検出するだけで、記録された変更がゲート緩和かを拒否しない。`revision_reason` と次の gN を置けば、結果後の条件緩和が正規の履歴になる。

**根拠:** [s2-plan.md:88](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:88)、[s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:93)、[s2-plan.md:248](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:248)、[worklog-phase3-0802-113-116.md:666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/archive/worklog-phase3-0802-113-116.md:666)、[phase3-8b-descriptor-design.md:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8b-descriptor-design.md:255)、[CLAUDE.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/CLAUDE.md:67)。

**具体的な攻撃手順:** 結果後に C09 を「Layer 3 が acceptance で必須」から「Layer 3 CLI が存在」に変更し、evidence contract と g2 を同じ commit に追加する。`supersedes_sha256`、連番、reason、履歴はすべて正しいため chain は green になる。

**重大度:** blocker

**成果物影響:** Layer 3 を通らない trial が正式受理集合へ入り、材料レポートの source-ref と trial registry の受理集合が拡大する。

**提案修正:** 自動発効と改訂 authority を分離する。実走ごとの承認コマンドは不要でも、8c 条件・証拠契約の改訂は既存 ruling による人間承認を必須にする。自然言語の「受理集合が狭まった」ことは機械判定できないため、gN の存在だけを authorization にしない。

---

### 5. predicate 実装と normative dependency が pin されていない

**主張:** gN は evidence contract の hash を持つが、それを解釈する Python checker の bytes/hash を持たない。8b のどの版を評価したかも activation に固定されない。

**根拠:** [s2-plan.md:75](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:75)、[s2-plan.md:151](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:151)、[s2-plan.md:304](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:304)、[phase3-8c-preregistration.md:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:50)。

**具体的な攻撃手順:** `s8c_preregistration_evidence.py` の C07 を「floor path が存在すれば SATISFIED」に変更し、contract JSON は触らない。テストも同時変更する。保護 hash と chain は不変のため green になる。別経路では、結果後の新しい 8b 再凍結版を current HEAD から読み、旧8c runを新基準で再解釈できる。

**重大度:** blocker

**成果物影響:** 実 floor consumer・judge がない trialが成功判定へ入り、certified variant と材料レポートの判定値が変わる。

**提案修正:** activation bundle に evaluator の reproducible source/executable hash、schema、全 normative dependency blob、8b active generation/receipt を含める。acceptance は current checker ではなく、measurement に pin された evaluator/versionで再計算する。

---

### 6. tracked g1 は自己署名であり、任意 checkout と履歴再構成を区別できない

**主張:** 「任意 checkout」を受け付ける一方で、g1 の root hashを checkout 外に持たない。正常な系列と、結果後に作った別 branch・再構成履歴は同じ検査結果になる。

**根拠:** [brief.md:10](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:10)、[s2-plan.md:92](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:92)、[s2-plan.md:99](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:99)、[decisions.md:5499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/decisions.md:5499)、[decisions.md:5511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/decisions.md:5511)。

**具体的な攻撃手順:**

- 実時間順: `A(draft)` → Git 外で結果 `X` を観測 → `B(§5=f(X)+g1)` → `M(manifest/registry)` → `R(Xを正式成果物として収録)`。
- 公開される commit 列は `A→B→M→R` だけで、`B` が `R` より前という ancestry は成立する。
- さらに pre-g1 commit から別 branch を切り、弱い条件・独自 g1・独自 checker を一貫して作っても、trusted base の pin がないため「任意 checkout」の validator は区別できない。

**重大度:** blocker

**成果物影響:** 全6セルが後付け prereg として受理され得るため、certified 選択・材料レポート・試行台帳の事前登録参照がすべて空証明になる。

**提案修正:** g1/activation receipt を保護された remote ref、署名付き tag、CI transparency log等へ pre-run 公開する。履歴 rewrite を threat model 外にするなら、その限定を成果物の主張へ明記し、第三者向け「事前登録済み」は主張しない。

---

### 7. C10 は mutable 入力一式の同時改変を止めない

**主張:** 多数の hash を相互照合しても、すべての入力を同時に再生成できれば完全な自己整合系になる。事前登録文書自身が認めた情報理論的限界に対する新しい anchor が plan にない。

**根拠:** [phase3-8c-preregistration.md:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:156)、[phase3-8c-preregistration.md:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:172)、[s2-plan.md:130](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:130)。

**具体的な攻撃手順:** 不利な attempt を journal/report から除去し、対応する provider envelope、proposal、WAL、Layer 3 report、全参照 hash を同時に再生成する。最初に commit する前なら Git に旧 bytes は存在せず、C10 は残った集合の完全な整合しか確認できない。

**重大度:** blocker

**成果物影響:** 試行台帳の attempt universe が縮み、6セル結果表の性能値・中央値・admission decisionと、それから選ばれる certified variant が変わる。

**提案修正:** 各 launch/run-start/attempt の hash rootを生成時に外部 append-only ledgerへ送る。post-run acceptance は事前 manifest と外部 event rootの完全な基数・順序一致を要求する。

---

### 8. P6 により activation judge は production correctness signal にならない

**主張:** CLIとテストだけの judge は formal launcherを止めない。これは「正しさシグナルを後付けにしない」という絶対規律3に正面から反する。

**根拠:** [brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:23)、[brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:41)、[s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:28)、[s2-plan.md:307](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:307)、[CLAUDE.md:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/CLAUDE.md:73)。

**具体的な攻撃手順:** T-325 の manifest/ancestry gateへ、まだ `effective=false` の draft commitを渡して launchする。T-325 は T-327 judgeを呼ばないため、manifest・registry・reportの各 `prereg_commit` は焼かれる。その後 T-327 CLIを手で回さない、または結果後に条件を green にする。

現 checkoutにも、prereg sealを要求しない公開 `run_trial()` と任意 `--run-root` がある。[p3_autonomous_workload_trial.py:1530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/p3_autonomous_workload_trial.py:1530)、[同:1752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/p3_autonomous_workload_trial.py:1752)

**重大度:** blocker

**成果物影響:** trial registryに未発効文書を指す6 trialが入り、terminal/Layer 3 reportの `prereg_commit` 参照が偽になる。

**提案修正:** formal launch・直接API・acceptanceすべてが sealed activation resultを必須引数として要求する変更を同一land単位にする。衝突回避が必要なら、結線完了まで正式8c入口をfail-closedで無効化し、T-327を「完了」としない。

---

### 9. `measurement_head` は実行した bytes を証明しない

**主張:** T-325 は HEADの40桁 hashを得るが、orchestrator worktreeのcleanlinessや実行中 bytesを束縛しない。dirty codeまたは別checkoutの実走が、clean commitを `measurement_head` として名乗れる。

**根拠:** [trial_registry.py:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/trial_registry.py:582)、[trial_registry.py:693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/trial_registry.py:693)、[p3_autonomous_workload_trial.py:1734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/p3_autonomous_workload_trial.py:1734)、[s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:28)。

**具体的な攻撃手順:** HEAD=`H` のまま `p3_autonomous_workload_trial.py`、role定義、evidence codeのいずれかを未commit変更し、そのworktreeからプロセスを起動する。manifest/registryは `H` の blobと一致するため gateは通るが、実行されるPython bytesは `H` と異なり、reportには `measurement_head=H` が残る。

**重大度:** blocker

**成果物影響:** 100k/4、弱いgate、別armなどで得た性能値が1m/48・正規gateの `H` に帰属し、certified 選択と材料レポートのcheckout参照が偽になる。

**提案修正:** clean worktree確認だけでなく、commitからmaterializeした immutable execution tree/containerを使う。run-startとpublish直前にorchestrator・role・config・CCBench bundleのhashを照合する。

---

### 10. T-325 の「未登録 ID は探索実走可」が holdout の事前観測路になる

**主張:** T-325 は登録済みIDだけをmanifest-less launchから拒否し、未登録IDは明示的に許可する。briefが同一entrypointを前提とする以上、C01でH1/H2を追加した瞬間に事前観測路となる。

**根拠:** [trial_registry.py:1020](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/trial_registry.py:1020)、[p3_autonomous_workload_trial.py:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/p3_autonomous_workload_trial.py:622)、[phase3-8c-preregistration.md:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:158)、[s2-plan.md:210](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:210)。

**具体的な攻撃手順:** C01 land後、manifestなし・未登録の `trial_id=peek-h1` と別 `--run-root` でH1を走らせる。結果を見て§5のfloor・seed・検定有無・停止条件を決め、その後に別の登録済み6 IDで正式系列を走らせる。registryは `peek-h1` を知らないため全形式検査が通る。

**重大度:** blocker

**成果物影響:** hidden pilotが試行台帳から消え、その結果に合わせた§5とvariantが正式6セルだけの結果としてcertified選択・材料レポートへ入る。

**提案修正:** H1/H2のconfig identityに対する全入口 embargoを設け、trial ID・run-root・CLI/APIに関係なくactivation sealを必須にする。holdoutへの未登録アクセスは外部ledgerへ記録し、そのprereg generationを恒久失効させる。

---

### 11. C11 は禁止裁定の存在を「充足」と取り違えている

**主張:** ユーザー裁定は「budget=1では走らせない」だが、planはその禁止文の存在をC11のSATISFIED候補としている。裁定済みと裁定遵守は別である。

**根拠:** [s2-plan.md:6](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:6)、[s2-plan.md:131](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:131)、[worklog-phase3-0803-122.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/archive/worklog-phase3-0803-122.md:8)、[phase3-8c-preregistration.md:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:118)。

**具体的な攻撃手順:** `MAX_APPROVED_GENERATIONS=1` を維持したまま、裁定blob hashだけでC11をSATISFIEDにする。他11条件を形式上greenにすれば、禁止されているone-shot系列が自動発効する。

**重大度:** blocker

**成果物影響:** 一回の生成応答の差が「generation/searchによるワークロード特化合成」としてcertified選択・材料レポートに昇格する。

**提案修正:** C11をcompliance predicateにする。複数世代、critic還流、標本設計、cap-lift receiptがすべて実装・pin済みで、manifestのgeneration budgetが裁定に適合するときだけSATISFIEDとする。

---

### 12. P3 の未既知性scan実測は一般化しすぎている

**主張:** 「文書本文を複製すると全file scanを汚染する」は実測から導けない。現文書はcanonical三軸綴りを意図的に持たず、そのbytesを複製しても同じ理由でconjunction hitにならない。

**根拠:** [brief.md:34](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:34)、[phase3-8c-preregistration.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:15)、[s8b_holdout_freeze.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_holdout_freeze.py:94)、[同:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_holdout_freeze.py:179)、[同:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_holdout_freeze.py:257)、[同:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_holdout_freeze.py:297)。

**具体的な反例:** scannerは通常tracked file・非ignoreのuntracked fileを列挙するが、symlink/gitlink、NUL含有・非UTF-8、defaultの`s8b-freeze`を除外し、同一fileで三軸すべてが一致した場合だけhitとする。現文書には`ycsb_...`綴りが0件なので、本文複製一般が42 hitを生むわけではない。

現checkoutについては、文書pathのPython hit 0、現在のSHA-256/Git blob IDのtracked hit 0、既存23件manifestに不在、という狭いDW-O09は確認できた。[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/tests/test_frozen_artifacts.py:38)

**重大度:** should

**提案修正:** P3の理由を「compactなcanonical contract」に限定し、候補artifactそのものをrepo scanで実測する。hash pinと本文複製のどちらも独立anchorなしではtrust rootにならない点を分けて記述する。

---

### 13. brief と plan が参照する T-325 snapshot は既に stale である

**主張:** briefは「2 commit」、planはtip `de6e1b` を前提にするが、レビュー時点のbranchは `2dce300` で、T-325固有4 commitとmain mergeを含む。述語契約を古いAPIへ固定してはならない。

**根拠:** [brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:23)、[s2-plan.md:11](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:11)、[s2-plan.md:230](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:230)。

**具体的な反例:** `git rev-parse worktree-dev-wave-t325-trial-registry` は `2dce300...`。旧tip以後に `58d1444`、`f60f077`、mergeがある。旧shapeに合わせたC02/C03/C08/C09 probeは、新consumerを見落とすか、存在しないfieldを理由に永久赤になりうる。

**重大度:** should

**提案修正:** T-325 land後のexact commitをpinして、公開入口・直接API・acceptance・exploratory bypass・arm bindingを再line-upしてからevidence contractとg1を確定する。

## 総括

- **判定: NO-GO**
- **blocker: 11件**
- 最大の破綻は、P2が「条件充足commit」でなく「文書最終変更commit」を発効版にする点である。
- 親が最初に裁定すべきは、P1/P2を維持するか、pre-run自動activation receiptを導入するかである。
- 推奨は、静的 readiness・launch admission・post-run acceptanceの三分割と、pin済みsnapshot `C` の履歴再評価。
- 条件改訂は自動発効とは分離し、人間rulingまたは独立authorityを必須にする。
- P6のlauncher結線を後続へ送ったままT-327を完了扱いしてはならない。
- g1発行前に§5値・normative本文・8b版・checker bytes・外部anchorの所有関係を確定する必要がある。