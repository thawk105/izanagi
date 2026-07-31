判定は **NO-GO** です。親実測の 150 passed、POS/NEG snapshot 成功、禁止 commit 到達不能、歴史 control の正しい向きは前提として採用しました。fix 報告の自己申告は根拠にしていません。

## 全17件の再判定

追加条件の RF-1〜RF-8 は review A の Must-fix 1〜8 として併記します。

| 所見 | 判定 | fix後の静的根拠 |
|---|---|---|
| Review A MF-1 / RF-1 — NEG allowlist | `closed` | NEG は訂正版6件で、`fix1.md` を含みません。[impl:111](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:111) prompt参照集合との完全一致も検査します。[impl:1440](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1440) |
| Review A MF-2 / RF-2 — replay verifier | `closed` | `verify` は raw launch/events/done/prompt/output/oracle/rollout を必須読込し、snapshot、`collect_run()`、`score_run()` を再実行して保存JSONとの canonical byte 一致を取ります。[impl:3815](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3815) [impl:3870](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3870) [impl:3877](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3877) [impl:3891](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3891) |
| Review A MF-3 / RF-3 — stale/extra session | `closed` | session timestampをlaunch envelopeへ拘束し、`id == session_id == thread_id`、さらに `(path,inode,id,session_id,timestamp)` 行集合の完全一致を要求します。[impl:2485](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2485) [impl:3105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3105) [impl:3979](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3979) |
| Review A MF-4 / RF-4 — retry上限 | `closed` | 1〜3以外をlaunch前拒否し、supervisor ledger、全launch集合、連続generation、親runを照合します。[impl:2002](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2002) [impl:3565](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3565) [impl:3684](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3684) ただし非対称technical-invalidのpair retryは別途N-3。 |
| Review A MF-5 / RF-5 — primary verdict join | `partial` | packet→run→slot、二読者、output SHA、judgmentの逐件joinは実装済みです。[impl:3277](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3277) [impl:3360](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3360) ただし凍結前unblindが可能です（N-1）。 |
| Review A MF-6 / RF-6 — scorer | `partial` | 歴史control、否定R-1、tilde fence、500-byte境界は固定されています。[test:1497](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1497) [test:1517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1517) [test:1528](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1528) なお別形の曖昧決定が残ります（N-5）。 |
| Review A MF-7 / RF-7 — golden独立性 | `closed` | route B は独立parser/byte decoderを持ち、route比較をproduction entrypointが必ず通り、source rollout SHAも検査します。[impl:425](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:425) [impl:536](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:536) [impl:559](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:559) |
| Review A MF-8 / RF-8 — turn graph/classification | `closed` | context/start/completeのturn ID join、event順・timestamp、zero token、ledger fragment、構造化treatment開始判定があります。[impl:2614](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2614) [impl:2680](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2680) [impl:2709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2709) [impl:2753](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2753) |
| Review B MF-1 — arm treatment同一性 | `partial` | config/auth/CLI/bwrap/env/argv/snapshot/promptを正規化identityへ束縛し、case内濃度1を検査します。[impl:1578](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1578) [impl:3994](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3994) ただしagentからlaunch receiptが読めます（N-2）。 |
| Review B MF-2 — Git object閉包 | `closed` | ref/remote/reflog/packed-refs/replace/alternates/grafts/pseudo-ref/unreachable objectを検査し、禁止object・focus履歴も明示拒否します。[impl:1053](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1053) [impl:1127](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1127) fix4の未初期化submoduleも直接store経路は閉じています。後述のN-7/N-8は現snapshotへの影響未立証のbacklogです。 |
| Review B MF-3 — NEG snapshot | `closed` | Review A MF-1と同じく訂正版6件へ一致しています。[impl:111](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:111) |
| Review B MF-4 — raw replay/freeze | `closed` | receipt/scoreの申告値を採用せずraw artifactから再生成します。`sessions-root`も必須です。[impl:4012](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4012) |
| Review B MF-5 — label-masked adjudication | `partial` | 二読者とfreeze→revealの公開操作順は存在します。[impl:4192](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4192) [impl:4232](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4232) しかし秘密map自体は先に平文生成・返却されます。 |
| Review B MF-6 — slot/attempt/失敗分類 | `partial` | 全attemptはsupervisor ledgerとmanifestの集合一致を取り、resource ledgerへ全行入り、final technical-invalidなら品質出力を全てnullにします。[impl:3587](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3587) [impl:3503](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3503) [impl:3517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3517) ただしpair retryに実行不能ケースがあります。 |
| Review B MF-7 — 同時実行干渉 | `closed` | crossover blockはmanifest上隣接し、supervisorはfor-loopで逐次起動、実monotonic時刻でもoverlap・逆順・過大gapを拒否します。[impl:3175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3175) [impl:2105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2105) [impl:3660](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3660) |
| Review B MF-8 — 全域decision function | `partial` | completeness→POS→NEG→reliability→resourceの出力面は存在しますが、POSとNEGを交差した採用可否が誤っています。[impl:3469](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3469) |
| Review B MF-9 — T-181指標 | `partial` | primary、新規finding、全attempt resource、logical turn、reliability、decisionはaggregateから出ます。[impl:3549](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3549) ただしlogical turnはvalid runで構造的に1となり、decisionもMF-8の誤りを含みます。 |

合計は **closed 10 / partial 7 / regressed 0** です。

## 残存finding

### N-1 — 凍結前unblindが平文mapとSHA照合で可能

- severity: **CRITICAL / must-fix**
- real/refuted: **real**
- 根拠: `make_packets()` は verdict 前に `packet_id→run_id` を平文で書き、呼出元へ秘密ファイルpathを返します。[impl:4088](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4088) [impl:4100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4100) [impl:4111](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4111) 実際、テスト自身がfreeze前にそのファイルを読みます。[test:580](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:580) またpacket stateのoutput SHAを既知のrun output SHAと突合するだけでも復元できます。[impl:4084](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4084)
- 成果物影響: launcher兼親裁定者がarmを知ってから verdict を書けるため、primary `k/3`、偽finding、新規finding、T-184採用可否のlabel-masked保証が成立しません。
- 最小fix: mapping custodianを別OS権限・別processへ分離し、両読者の署名済みverdict freezeまで親へmap/path/keyを渡さない。評価者向けpacket stateからoutput SHAも除き、公開後にだけ別artifactでjoinする。

### N-2 — agent自身からarm・slot・attemptが読める

- severity: **HIGH / must-fix**
- real/refuted: **real**
- 根拠: bwrapはattempt directory全体をbindし、その中へprompt送信前に`launch.json`を書きます。[impl:1743](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1743) [impl:1864](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1864) [impl:1917](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1917) 同ファイルにはarm、slot、attempt、親run、block順が平文で入ります。path検査はliteral `max/high` しか直接検出しません。[impl:1394](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1394)
- 成果物影響: 出力差をreasoning effortだけに帰属できず、agentがlabel/order/再試行状態に反応した差が混ざります。
- 最小fix: launch receiptとledgerをsandbox外へ置き、agentには専用CODEX_HOME、stdin、stdout先だけをbindする。slot/block/attemptをagent可視path・fileから除去する。

### N-3 — 片側だけtechnical-invalidになったpairを正規にretryできない

- severity: **HIGH / must-fix**
- real/refuted: **real**
- 根拠: 仕様上はpair全体を再実行しますが、verifierはretry前の各slotが個別に`technical-invalid`であることを要求します。[impl:3967](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3967) [impl:3972](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3972) 一方のrunがvalidなら、そのmateは`failure_class=None`なので、両側をretryしてもmanifestが失格になります。既存testは「片側だけを再実行すること」の拒否だけです。[test:1321](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1321)
- 成果物影響: 1件の非対称technical failureで、許可されたretryを消化しても`experiment_complete`へ到達できず、10 run全体が実行後に使用不能になります。
- 最小fix: pair memberの一方がtechnical-invalidなら、mateを構造化`pair-invalidated`として品質分母から外し、両方の次generationを許可する。資源は両attemptとも残す正例testを追加する。

### N-4 — NEG finding発生時にPOS安全条件を無視してarmをeligibleにする

- severity: **CRITICAL / must-fix**
- real/refuted: **real**
- 根拠: NEG finding branchの`adoption_eligibility`はPOSの`k`を参照せず、「NEGで除外されなかったか」だけです。[impl:3483](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3483) 例えばmaxにNEG false findingがあり、highがPOS 2/3でもhighを`True`にします。またmax≤2/high=3の「benchmark不安定」でもhighをeligibleにします。[impl:3475](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3475) [impl:3498](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3498)
- 成果物影響: 事前登録zero-miss条件を満たさないhighをT-184採用候補にでき、routing判断が逆転します。
- 最小fix: POS eligibilityを先に全4分岐で確定し、NEG除外を論理ANDする。POS四分岐×NEG両arm findingの直積testを追加する。

### N-5 — 強調記号を挟む曖昧decisionがvalidになる

- severity: **HIGH / must-fix**
- real/refuted: **real**
- 根拠: decision語抽出とdisclaimer検査が別regexで、disclaimerはMarkdown強調を正規化しません。[impl:2915](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2915) [impl:2920](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2920) 500 bytes超の総括を「`**GO** との判断は保留する。`」で始めると、GO一意として受理され、現在の`未裁定|未決定|判断保留`にも一致しません。
- 成果物影響: 本来post-treatment failureである未裁定出力がvalid扱いとなり、reliabilityとonline max escalation候補を過小計上します。
- 最小fix: inline emphasisを除去した正規形で、凍結した一文decision grammarを検査する。上記反例を独立fixtureにする。

### N-6 — logical turnはvalid runで構造的に1

- severity: **MEDIUM**
- real/refuted: **real**
- 根拠: turn IDが変わる複数contextをinvalid化し、task start/completeも各1件へ固定した後、unique ID数をturn数にしています。[impl:2520](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2520) [impl:2657](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2657) [impl:2720](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2720)
- 成果物影響: T-181成果物にはturn列が出ますが、valid arm間のturn効率差を測れません。T-184で「turn削減」を根拠にできません。
- 最小fix: 複数turnを許すprotocolならturnごとにcontext/start/terminal graphを検査して数える。単一turn固定が仕様なら、値が構造定数であると明記し、比較指標から外して`model_calls`を用いる。

### N-7 — standalone `verify-snapshot` の非Gitメタデータ閉包

- severity: **LOW / backlog**
- real/refuted: 構造上は **real**、現POS/NEG成果物への影響は親のfresh build・凍結SHA実測により **未立証**
- 根拠: filesystem allowlistは非directoryだけを数え、root `.git` 配下を全面除外します。[impl:980](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:980) `.git`の任意ファイルはmetadataへ記録されるだけで、standalone specとの固定比較はありません。[impl:1102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1102)
- 成果物影響: 現実走についてなし。汚染がschedule freeze前に混入した場合だけ、`.git/answer.txt`や空directory名をpacket入力から読めます。
- 最小fix: deterministic builder由来の`.git` metadata/全directory allowlistを外部pinし、余剰entryを拒否する。

### N-8 — 未初期化submoduleのnetwork取得面

- severity: **LOW / backlog**
- real/refuted: egress面は **real**、歴史answer到達は **未立証**
- 根拠: 未初期化submoduleはworktree・marker・admin store不在を要求するので、直接local store漏洩は閉じています。[impl:812](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:812) [impl:845](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:845) gitlink/stateもPOS/NEGで一致必須です。[impl:3197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3197) ただしbwrapはPIDを分離してもnetworkを分離せず、実`.gitmodules`は公開URLを持ちます。[.gitmodules:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/.gitmodules:3) [nested .gitmodules:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/external/ccbench/.gitmodules:3)
- 成果物影響: 現在のURL先からT-181歴史回答へ到達する証拠はなく、現成果物影響なし。したがってmust-fixには数えません。
- 最小fix: inference APIだけを許すegress proxyか、agent tool subprocessのnetwork拒否をattestする。

## Git object閉包の経路別結論

- `packed-refs`、reflog、replace、grafts、alternates/http-alternatesは削除・非空拒否ともあります。[impl:667](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:667) [impl:1070](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1070)
- `.git/objects/info` の外部object経路はalternates/http-alternates拒否と`fsck --unreachable`で閉じています。commit-graph等はblob本文源ではありませんが、N-7のメタデータallowlist hardening余地があります。
- 初期化済みsubmoduleは再帰的にclosure検査されます。[impl:855](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:855) 未初期化submoduleはgitlink SHAだけで無条件受理しているわけではなく、worktree空、`.git` markerなし、期待admin storeなしが必要です。
- `--reference`で使えるhost repoは、`/home` maskとcanonical bwrap argvによりsandboxから見えません。[impl:1687](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1687)
- snapshot外の継承`GIT_*`はallowlist生成時に全除去されます。[impl:1500](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1500) agentが後から設定しても参照可能なhost object storeはmountされていません。
- `/proc`はfresh PID namespaceです。host processのenviron/cmdline/fd経路は閉じていますが、自分自身のargvやlaunch fileからarmを知る経路はN-2として残ります。

## M1〜M12検出力

全変異に対応nodeが実在し、対応欠落はありません。

| 変異 | 期待node |
|---|---|
| M1 | [test:730](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:730) |
| M2 | [test:739](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:739) |
| M3 | mode、HEAD、extra/missing、focus方向を独立固定。[test:758](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:758) [test:770](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:770) [test:780](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:780) |
| M4 | [test:1351](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1351) |
| M5 | 実extra session行のbehavioral負例があります。[test:1166](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1166) |
| M6 | [test:1639](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1639) |
| M7 | [test:1359](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1359) |
| M8 | [test:1376](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1376) |
| M9 | [test:1430](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1430) |
| M10 | 実focus SHAと向きを固定。[test:1497](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1497) |
| M11 | [test:1528](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1528) |
| M12 | [test:1538](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1538) |

歴史 control はfocus1/focus2双方を独立SHAで固定し、`NO-GO/true`、`GO/false`を直接期待しているため、採点器の向きに回帰はありません。実rollout goldenもfull rollout SHAとliteral token行の双方を照合しており、source SHA pinは実効です。[test:1124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1124) 一方、fake end-to-end fixtureはproductionのcollector/scorerから期待receiptを作る共通故障点を持ちます。[test:537](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:537) 今回のN-3〜N-5が残った理由でもあり、150 passedだけではこれらを閉じません。

## 総括

**NO-GO。closed 10件、partial 7件、regressed 0件です。この実装のまま10 runの実走へ進んではいけません。** 親実測により、旧33→27 test時の主要な検出力低下は回復し、M1〜M12の期待nodeは全件存在します。歴史focus1はNO-GOかつR-1候補true、focus2はGOかつfalseの向きをSHA固定された実ファイルで維持しており、禁止commit、通常ref、focus履歴、初期化済みsubmodule object store、fix4で受理された未初期化submoduleの直接local store経路にも回帰は認めません。raw replayも現在は実際にsnapshot、collect-run、score-runを再実行し、保存receipt/scoreの自己申告値だけで通る旧受理集合は閉じています。

それでも実走を止める具体的理由が残ります。第一に、packet生成時点で平文mapping secretとoutput SHAが親へ渡るため、verdict凍結前のunblindを機械的に防げません。第二に、agent自身がbindされたlaunch.jsonからarm、slot、attempt、block順を読め、effort以外のtreatment差が出力へ混入します。第三に、片側だけtechnical-invalidとなったpairを仕様どおり両側retryすると、validだったmateの親attemptがtechnical-invalidでないという理由で最終verifyが失敗します。第四に、NEG false finding分岐がPOS zero-miss条件を無視してhighを採用可能にでき、事前登録した決定関数と逆のT-184判断を出せます。さらに曖昧GOをvalidとする書式経路と、valid runで恒常的に1となるlogical turn指標も残ります。これらは「テスト未実走」ではなく、fix後コードに残る静的な受理集合・裁定関数の問題です。少なくともN-1〜N-5を修正し、非対称pair retry正例、POS四分岐×NEG除外の直積、強調付き曖昧decision、sandboxからlaunch metadataが不可視であることを固定してから、段6 focused reviewへ戻す必要があります。