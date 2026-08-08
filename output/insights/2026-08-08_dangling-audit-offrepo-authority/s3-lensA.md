静的監査のみであり、pytest は実走していない。

## 所見リスト

1. **[real / blocker] P2 は「一時的な写し」を「永続的な正本」と誤認する**

   [T-574] の一次証拠は、単なる bytes 一致ではなく、land 済み文書が特定の絶対 path を参照していたことだった（[裁定:19](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-07-dangling-audit-alarm-fatigue.md:19)、[裁定:21](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-07-dangling-audit-alarm-fatigue.md:21)）。しかしプランは、その provenance を捨て、根配下の任意の一致物を正本扱いする（[plan:163](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:163)、[plan:214](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:214)）。

   runbook が保証するのは「生きた handoff」「未記録裁定」「各 wave の成果物」の所在だけであり、保持期限・削除禁止・backup・pin はない（[runbook:731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/docs/pegasus-runbook.md:731)、[runbook:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/docs/pegasus-runbook.md:733)）。事故系列は次で成立する。

   `branch 消失 → audit 時だけ jobs 側に写しが存在 → finding 抑止・rc=0 → jobs 掃除で写し削除 → 約2週間後に Git object prune → 両方消滅`

   open後のregular/size確認（[plan:141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:141)）は読取瞬間しか証明せず、直後の unlink を防がない。これは TOCTOU ではなく、保持契約そのものの欠落である。

   **失われる報告:** jobs 側の写しが一瞬存在した `(unreachable commit, path)` は最初の監査で消え、その後 object ごと prune されて二度と報告不能になる。

2. **[real / blocker] basename + bytes は同一成果物の証明にならず、無関係な同値物を masking する**

   反例は、失われた `new_package/__init__.py` が空で、別 wave に無関係な空の `other_package/__init__.py` が一つある場合で十分である。basename・size・hash・bytes のすべてが一致し（[plan:162](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:162)、[plan:172](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:172)）、失われた path が抑止される。空ファイル、1行テンプレート、定型 `README.md`、生成物では同じ反例が成立し、一つの一致物で複数 commit/path を抑止できる。

   さらに Git mode `100644` と `100755` を同列に受理し（[plan:87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:87)）、候補型には mode がない（[plan:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:39)）。したがって、失われた executable script を同 bytes の非 executable file が抑止できる。

   brief の「同名 `README.md` 121件中一致0」はその日の一標本にすぎず（[brief:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/output/insights/2026-08-08_dangling-audit-offrepo-authority/s1-brief.md:27)）、将来の basename/bytes の一意性を証明しない。

   **失われる報告:** 無関係な空 `__init__.py` や非 executable の同名 script により、本来救出すべき新規 path／実行 mode の `(commit,path)` が消える。

3. **[real / blocker] P1/P5 の root 検査は任意入力による自作自演 masking を閉じていない**

   worktree の祖先を拒否する防壁は「推奨」に留まり（[plan:124](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:124)）、テストも採用時だけという条件付きである（[plan:347](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:347)）。このままなら `--offrepo-root /` や repo と jobs を含む共通祖先から repo 内 copy を拾える。

   祖先拒否を必須にしても、任意の `/tmp/...`、sibling worktree、所有者・modeを検証しない root は受理される。また、validation 後に root 自体を symlink へ交換する race は、path を dirfd として固定しない `os.walk` では閉じない。repo 内 untracked file の hardlink を受理 root に置けば、`lstat()` は regular file、`O_NOFOLLOW` も成功するため P5 を迭回できる（[plan:141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:141)、[plan:143](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:143)）。

   leaf symlink、FIFO、device、読取不能 file を抑止しない設計（[plan:180](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:180)）自体は安全側だが、root symlink race と hardlink は別経路である。

   **失われる報告:** repo 内の untracked copyまたはその hardlinkを「repo 外正本」に化けさせると、同 bytes の失われた `(commit,path)` が消える。

4. **[real / blocker] 段1実測と受入 oracle の算術が両立しない**

   brief は現状を24対、抑止後を15対としているため、抑止数は必ず9対である（[brief:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/output/insights/2026-08-08_dangling-audit-offrepo-authority/s1-brief.md:23)、[brief:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/output/insights/2026-08-08_dangling-audit-offrepo-authority/s1-brief.md:27)）。一方、plan は「抑止13対・残存15 path」を同時に必須化している（[plan:376](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:376)）。`24 - 13 = 11` なので不可能である。brief の「probe 1本 + 成果物11本」と `(commit,path)` 単位の関係も未整理である。

   さらに dangling object と jobs 内容は自然 gc・wave進行で変わるため、一点観測の件数を未固定 checkout の恒久 acceptance oracle にできない。20,544 file・2秒という値（[brief:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/output/insights/2026-08-08_dangling-audit-offrepo-authority/s1-brief.md:31)）も将来の安全性や上限を示さない。

   **失われる報告:** 「13対抑止」を満たす方向へ実装・期待値を寄せると、brief が残すはずの15対から少なくとも4対が余分に消える。

5. **[real / must-fix] P3 は stdout では可視だが、実際の gate interface では silent になり得る**

   plan は抑止一覧を出すため文字どおりの silent suppression は避けている。しかし現行公開契約の `rc=0 = 取り残しなし`（[tool:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:7)）と `LIMITATION_NOTICE` を変更せず（[plan:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:48)）、抑止13対でも `要確認 0件・rc=0` にする（[plan:276](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:276)、[plan:277](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:277)）。

   唯一の consumer は `rc0なら削除` としか規定しておらず、抑止節の確認・保存義務がない（[cleanup-branches:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/.claude/commands/cleanup-branches.md:17)）。したがって end-to-end の可視性は証明されていない。

   **失われる報告:** caller が rc だけを消費すると、抑止された全 `(commit,path)` が cleanup の救出判断・§5報告へ渡らない。

6. **[real / must-fix] 新規テスト群は危険な述語を正当化し、主要な false-negative 変異を殺せない**

   positive control は「directory名が違っても basename+bytes が同じなら抑止」を固定するだけで、両者の wave/provenance 関係を要求しない（[plan:307](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:307)）。negative controls は bytes・size・basename の不一致だけである（[plan:323](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:323)）。

   無関係な同名同内容、空ファイル、複数候補を一つの写しで抑止、100755対100644、root symlink交換、hardlink、読取直後のunlinkがない。祖先 root の control も条件付きである。

   **失われる報告:** 上記いずれかの masking を実装しても予定テストでは検出されず、その種類の `(commit,path)` が将来無音で消える。

## scope 外の real 所見

7. **[real / must-fix・scope外] 既存の第三条件は内容が違う未 land revision を意図的に見逃す**

   `live-wave` 側は `"live\n"`、到達不能側は `"unreachable revision\n"` なのに（[test:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_audit_dangling_commits.py:154)、[test:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_audit_dangling_commits.py:157)）、テストは無報告を固定する（[test:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_audit_dangling_commits.py:162)）。このテストは既存仕様の回帰防壁としては意味を保つが、「内容一致を確認して初めて保全済み」という新哲学とは整合しない。

   これは [T-593] の第二警告カテゴリとして plan が明示的に除外している（[plan:394](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:394)）。本 wave の段5へ混ぜてはならない。

   **失われる報告:** テスト例そのものの `orchestrator/in_flight.py` の到達不能 revision が報告されない。

8. **[real / must-fix・scope外] refs の非 snapshot 読取には既存の false-negative race がある**

   現行実装は branch tip の path を集めた後に unreachable commit を列挙する（[tool:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:134)、[tool:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:140)）。その間に branch が削除されると、commit は unreachable として現れる一方、削除済み tip の path が `other_tip_paths` に残って抑止する（[tool:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:147)）。

   refs snapshot 再試行は明示的 scope 外である（[plan:395](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:395)）。本 wave では実装せず、別件として残すべきである。

   **失われる報告:** tip path 収集直後に消えた branch の全該当 `(commit,path)` が、存在しない branch によって抑止される。

fixture 隔離については今回の静的証拠から独立した real 所見を立てない。ack台帳と即時pruneも修正案に含めない。両者は一次裁定で不採用済みである（[裁定:57](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-07-dangling-audit-alarm-fatigue.md:57)）。

## 総括

- blocker は **4件**。
- 最も危険なのは **所見1**。一時的な jobs copy を理由に報告を消し、その copy と Git object が時間差で削除されると、監査が救出機会そのものを消す。
- 段5へは **NO-GO**。少なくとも、永続性・provenanceを伴う抑止条件、P5の迂回不能なroot契約、矛盾しない件数oracleを段4で確定する必要がある。