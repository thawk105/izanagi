# 段3 敵対検証 — レンズB

### 1. [重大度: blocker] [real] P1 は既存裁定を事後的に別問題へ読み替えている

ユーザー裁定は抽象的な将来リスクではなく、「孫プロセスの `python3` が計算ノード既定へ戻る件」を事実として提示して得たものだった。[worklog.md:1195](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/docs/worklog.md:1195) ところが親自身が、単発と全走の双方で症状が再現せず、PATH 前置が問題の観測時点より前から存在したと確認している。[s1-brief.md:13](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:13) [s1-brief.md:25](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:25)

したがって P1 の「裁定対象は症状でなく構造的な穴だった」は、裁定後の目的差し替えである。[s1-brief.md:67](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:67) 前提となった事実が消えた以上、ユーザーへ再裁定を返すべきであり、親が裁定の射程を拡張して実装を続けてはならない。

[speculative] shim が追加で殺す具体的構成は作れる。例えば PATH 先頭に「要件を満たす `~/bin/python3.10` だけがあり、同じ dir に `python3` がない」、その後ろに Intel Python 3.9 の `python3` がある構成である。現行は前者を選定しても裸の `python3` が後者へ落ちる。だが、その構成が Pegasus で観測された証拠はない。「古いノード画像」も仮説に留まる。[s1-brief.md:34](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:34)

**代案:** T-248 はいったん「未観測の設計リスク」に戻し、次から再裁定を求める。

1. 実装せず設計メモだけ残す。
2. 実際の裸 `python3` に既存 probe を再実行して、違えば rc=16 にする最小 assert。
3. 異種ノードまたは PATH 構成で不一致を実測できた場合だけ full shim を実装する。

### 2. [重大度: must-fix] [real] 親測定は現行緑を証明するが、shim の必要性も過去の赤の原因も証明しない

親報告の `876518` は「bnode002 のその一走で対象 node が通った」こと、`876520` は「同じ bnode002 の全走で現在の suite が通った」ことを証明する。[s1-brief.md:13](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:13) これは現在の実害主張を強く反証する。

一方、次は証明しない。

- `result.interpreter` は `_job_run` 自身の `sys.executable` を記録するだけで、後続 shell が解決した裸の `python3` ではない。[dispatch_compute.py:459](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:459) [dispatch_compute.py:512](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:512)
- bnode002 以外の現在のノード構成、将来の PATH、ユーザー導入 interpreter は証明しない。
- closure wave の赤が何だったか、なぜ再現しないかは証明しない。
- wrapper、共有 FS の実行可否、PATH shadowing の安全性は証明しない。

**代案:** 測定結果は「現行 main tip・bnode002 では非再現」とだけ記録し、fleet 一般化や原因認定に使わない。

### 3. [重大度: must-fix] [real] P2 の狭い判断は正しいが、被覆主張は誇大である

`_job_script` は probe と dispatcher を `$resolved` / `$selected` で直接起動しており、ここに裸の `python3` はない。[dispatch_compute.py:389](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:389) [dispatch_compute.py:407](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:407) よって「bash 側には shim 不要」という P2 の狭い結論は成立する。

しかし `_job_run` の PATH shim が保証するのは、正確には「その PATH を継承し、後で優先要素を追加・上書きしないプロセスが裸の `python3` を解決するとき」だけである。

実際、対象となった `_run_submit` は pytest から継承した PATH のさらに前へ `fake_bin` を置く。[test_t126_pegasus_tools.py:2924](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/tests/test_t126_pegasus_tools.py:2924) 現 fixture はそこに `python3` を作らないため現在は shim までフォールスルーするが、fake bin に `python3` が加われば即座に shadow される。[test_t126_pegasus_tools.py:2827](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/orchestrator/tests/test_t126_pegasus_tools.py:2827) その先の submitter は裸の `python3` を多数起動する。[submit_t126_qualification.sh:162](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/submit_t126_qualification.sh:162) [submit_t126_qualification.sh:286](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/submit_t126_qualification.sh:286)

- 曾孫であること自体は反例ではない。PATH は深さに関係なく通常継承される。
- `env -i`、PATH の置換、先頭への別 `python3` 追加は反例になる。
- `#!/usr/bin/env python3` も PATH を保持している間だけ被覆される。
- プランが数えた shebang 50 件は「実行候補」の数であって、実 consumer edge の証明ではない。[s2-plan.md:15](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:15)

**代案:** 保証を「継承 PATH 上の裸名」に縮める。全 descendant の束縛を謳うなら、PATH shadow、環境 scrub、env shebang の境界テストを追加する。

### 4. [重大度: must-fix] [real] P3 の symlink は棄却済みだが、wrapper 案は新しい再入 poison を作る

親 P3 の canonical symlink は、venv 外の shim path を `sys.executable` として見せて `sys.prefix` / site 解決を変えうるため、段2プラン自身が棄却している。[s1-brief.md:71](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:71) [s2-plan.md:79](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:79) 透明 wrapper のほうが `-I` / `-S` / `-E` の argv 意味論を保ちやすい。この修正自体は妥当である。

だが、wrapper dir を child 起動前に永続作成し、再入時は無条件拒否する設計は回帰である。[s2-plan.md:39](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:39) [s2-plan.md:90](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:90) 現行は child 終了後にだけ `result.json` を create-only で書くため、result 作成前にプロセスが死ねば同じ submission script を再実行できる。[dispatch_compute.py:493](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:493) [dispatch_compute.py:515](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:515) 新設 shim は child 前に残るので、同じ crash/requeue を恒久 rc=16 に変える。

さらに、生成 wrapper を直接 exec するため、従来なかった「共有 submission FS が exec 可能」という要件も増える。プラン自身がこの依存を認めている。[s2-plan.md:88](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:88)

回帰面の判定は次のとおり。

- `sys.executable`、`-I` / `-S`: wrapper 案と意味論比較テストで相当程度対処済み。
- `TMPDIR` / `/dev/shm`: shim は submission dir 配下なので直接依存ではない。
- xdist: pytest controller は `sys.executable` で起動されるため直接の変更ではない。[run_tests.py:290](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/run_tests.py:290) [run_tests.py:995](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/run_tests.py:995)
- `shutil.which("python3")` や外部 plugin/hook の PATH 観測は確実に変わるが、現行 repo 内の具体的破損 consumer はプランが示していないため [speculative]。

**代案:** full shim を選ぶ場合でも、既存 wrapper の bytes・mode・現在の selected identity が完全一致すれば再利用し、不一致だけ fail-closed にする。あるいは child 生存期間だけ保持する node-local dir に置く。

### 5. [重大度: must-fix] [real] P4 は P1 を前提にした循環、P5 は人工的な変異 control にすぎない

P4 の「正しさ防壁だから軽量化しない」は、そもそもその防壁を新設すべきだという P1 が成立して初めて意味を持つ。非再現・再裁定案件である以上、重い wave 手続は実装理由にならない。dev-wave 自身も段4で「実装しない」と裁定すれば段5・6を飛ばせる。[dev-wave.md:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/.claude/commands/dev-wave.md:47)

P5 の conflicting sibling test は、現行コードを確実に赤くできるよい変異 control ではある。しかし、それは「その人工構成なら shim が効く」ことしか示さず、Pegasus にその構成が存在する証拠にはならない。[s2-plan.md:124](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:124) また、PATH を後から組み替える `_run_submit`、env scrub、env shebang、実 xdist worker の被覆も証明しない。

新概念は専用 dir、shell wrapper、fsync、identity probe、新 stage、再入契約、少なくとも6テストである。[s2-plan.md:101](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:101) [s2-plan.md:126](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s2-plan.md:126) 未観測リスクに対する正味コストとして重すぎる。

**代案:** `_job_run` が最終 child PATH を組んだ直後、裸の `python3` で既存 `interpreter_probe.py` を一度実行し、失敗なら既存 `stage="interpreter"` / rc=16 にする。解決済み interpreter の dir を PATH に置く案は既に実装済みである。[dispatch_compute.py:491](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/tools/pegasus/dispatch_compute.py:491)

### 6. [重大度: must-fix] [real] F46 と runbook は「実体同一性 shim」ではなく実行環境での assert を要求している

runbook は「版付き名で解決するか、実行前に版数を検査して fail-closed」と定める。[pegasus-runbook.md:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/docs/pegasus-runbook.md:157) F46 の恒久対応も候補列＋版数 gate であり、一般則は「実行環境側で assert として束縛する」である。[failures.md:909](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/docs/failures.md:909)

shim は継承 PATH の既定値を強化するが、後続 consumer が PATH を変えた後の実行環境では assert にならない。従って「F46 family を閉じる」というプラン側の主張は過大で、docs 側が正しい。最小の実効策は、実際に裸名を解決する環境で既存 probe を発火させることである。

また、full shim を採るなら「環境事実は変わらないから docs は scope 外」では不足する。[s1-brief.md:43](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:43) 新しい PATH 保証、新しい `interpreter-shim` stage、被覆限界は運用契約なので runbook §4/§7へ記載すべきである。

### 7. [重大度: blocker] [real] closure wave の赤の原因究明は、この T-248 から切り離せない

一次資料は同じ文書内で、全走 `874775` を rc=0 と記録しながら、別の request ID・node・生ログを示さず dispatch 経路の 3.9 fallback を断定している。[s6-ruling-package.md:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/output/insights/2026-07-31_t126-f32-closure-wave/s6-ruling-package.md:54) [s6-ruling-package.md:131](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim/output/insights/2026-07-31_t126-f32-closure-wave/s6-ruling-package.md:131) しかも現行 PATH 前置はその観測時点より前から存在した。[s1-brief.md:25](/home/SFC/tanab/.claude/jobs/135e0913/tmp/wave-t248/s1-brief.md:25)

原因究明を別 ID にすること自体は可能だが、先に次を行う必要がある。

- 元の因果記述を「原因不明・再現不能・3.9 帰属は撤回」に訂正する。
- 「偽赤だった」と断定せず、request ID・node・source tree・生ログが欠落した観測として残す。
- T-248 をその赤の修正から切り離し、純粋な予防的 hardening として再裁定する。

これをしないと、将来の T-126・dispatcher 保守者は、テスト回帰、scheduler、worktree差、PATH、xdist のどれを疑うべきか判断できず、誤った incident history を再利用することになる。

## 総括

- **NO-GO**。
- 現プランのまま shim を実装せず、変更された前提をユーザー裁定へ返すべきである。
- shim が追加で救う構成は技術的には作れるが、Pegasus での実在証拠はない。
- 第一代案は、実際の裸 `python3` に既存 probe を発火させる最小 fail-closed assert。
- full shim を選び直すなら、再入 poison、共有 FS exec 要件、PATH shadowing、docs を先に修正する。
- closure wave の赤は「偽赤」ではなく「原因不明・追跡不能」と記録する。
- 本検証は静的検査のみで、pytest は実行していない。