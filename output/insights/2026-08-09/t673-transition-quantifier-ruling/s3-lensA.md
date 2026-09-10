静的監査のみを行った。`pytest`、mutation harness、bench は実走しておらず、現 turn の緑判定はない。過去 ledger を使う箇所は「既往実測」と明記する。

## 所見

### 1. `4be7a362` から `2c0a418f` の対象差分疑い — [refuted]

[s2-plan.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:3) の HEAD 表記は古いが、指定された主要 4 ファイルを `git diff 4be7a362..2c0a418f` で照合すると差分は空だった。blob ID も両 commit で一致した。

- production: `2d4adf9c...`
- existing test: `fdffbb344...`
- mutation harness: `efe54a15a...`
- worktree wrapper: `5a5ed49d...`

したがって、以下の静的推論を merge 前コード由来として棄却する理由はない。

覆す一手: 上記 4 path のいずれかで non-empty diff または異なる blob ID を示す。

### 2. G 系の事前登録 `expected_nodes=[D4]` は誤り — [real]

プランの登録は [s2-plan.md:109-124](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:109)。しかし G loop を切ると、[env_contract_activation.py:274-300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract_activation.py:274) で `changed` 自体が prefix に縮み、P2/P3/P4 の偽 witness も消える。

4-node focal scope 内の静的 failure 集合は次になる。

| mutant | plan | 静的 failure 集合 |
|---|---|---|
| G-N1 | `{D4}` | `{D4,P2,P3,P4}` |
| G-N2 | `{D4}` | `{D4,P3,P4}` |
| G-N3 | `{D4}` | `{D4,P4}` |
| G-N4/N8/N63/N64 | `∅` | `∅` |

根拠は D4 の末尾 downgrade [test_env_contract_activation.py:571-586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:571) と、偽 predicate がそれぞれ第 2/3/4 env に置かれた [同:921-990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:921)。

したがって frontier の数値だけは `≤3 / ≥4` のままでも、harness は失敗集合の exact equality を要求するため [mutation_harness.py:1177-1193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_harness.py:1177)、G-N1〜3 を `KILLED` ではなく `MISMATCH` と判定するはずである。collection 検査は期待 node の存在しか確認せず、期待集合の完全性は検査しない [同:945-986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_harness.py:945)。

「多すぎる expected node」は focal scope では見つからず、「少なすぎる」が G 全 3 件にある。

覆す一手: 同じ 4-node runner で G-N1〜3 の `failed_nodes` が各 `{D4}` だけになる記録を得る。

### 3. P-N1 が focal で 3 件ちょうどかという疑い — [refuted]

4-node runnerに限ればプランどおりである。

- P-N1: `{P2,P3,P4}`
- P-N2: `{P3,P4}`
- P-N3: `{P4}`
- P-N4 以上: `∅`

D4 は P loop 到達前の exactly +1 検査で拒否されるため影響しない。[env_contract_activation.py:285-300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract_activation.py:285)

覆す一手: focal の P-N1 で D4 が失敗する、または P2/P3/P4 のいずれかが失敗しない記録を示す。

### 4. P-N1 の既存 suite 検出力は 3 件ではなく 10 件 — [real]

既往の T-627 ledger は、現在と同一の production/test blob に対する同じ `changed[:1]` 変異を記録している [mutation-ledger-v3.json:209-246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/output/insights/2026-08-08_t627-noop-binding/mutation-ledger-v3.json:209)。失敗集合は 10 node [同:223-233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/output/insights/2026-08-08_t627-noop-binding/mutation-ledger-v3.json:223)。

さらに由来文書の「semantic 3 / diagnostic 7」分類 [worklog-phase3-0808-318.md:34-38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/docs/archive/worklog-phase3-0808-318.md:34) も誤っている。

- mutant が拒否を受理へ変える semantic failure は、P2/P3/P4 に加え、後段の non-bool と例外 [test_env_contract_activation.py:1053-1082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:1053) の計 5 件。
- 受否は維持し call 列だけ変えるものは、first-failure 3 件、reused-hash、call-once [同:775-800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:775)、[同:993-1103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:993) の計 5 件。

したがって [s2-plan.md:132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:132) の「4 node なら semantic kill に絞れる」は、semantic failure を 2 件落としている。

覆す一手: 同一 blob の full-file P-N1 再測定で、後段 non-bool／例外 node が失敗せず受理も変わらないことを示す。

### 5. focal scope は A の幅を過小評価し、B/C の「純増」を過大表示しうる — [real]

G-N1 は、先頭 env が据置で末尾だけ変更されると `changed` が空になり、[env_contract_activation.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract_activation.py:293) の no-op 拒否へ誤って入る。現実の serial-2 fixture は `linux-baremetal` 据置、`pegasus` 更新である [test_env_contract_activation.py:178-195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:178)。従って production loader 正例 [同:1467-1474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:1467) や issuer 成功経路 [同:1959-2018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:1959) も、focal 外の semantic detector になり得る。2/3-env matrix [同:690-772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:690) にも suffix-only change／invalid suffix が含まれる。

一方、候補 option の command は candidate 2 node だけ [s2-plan.md:355-367](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:355)。これは「既存 suite＋候補」を測っておらず、A と B/C の node 数・semantic breadth を直接比較できない。

ただし既存 fixture の最大 M=4 なので、full-file にしても `N≥4` を殺すとは静的に言えない。歪むのは主に検出の幅と純増件数であり、A の境界値そのものではない。

段 4 では両方必要である。

1. full-file 共通 scopeで「実際の既存 CI」と「既存＋候補」の union／marginal を測る。
2. focal scope は原因帰属専用に残し、`raw rc/failed_nodes` と expectation 一致を別指標にする。

覆す一手: full-file matrixで A の追加 failure がゼロかつ、候補単独と既存＋候補の marginal 結果が全 mutant で一致することを示す。

### 6. core hash は「同じ置換文字列」を示すだけで、同じ実験ではない — [real]

[s2-plan.md:152-155](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:152) の hash は `(id, category, replacements, hang_risk)` だけで、次を含まない。

- 置換前 production blob
- candidate test blob
- runner argv／collection
- Python・pytest・Hypothesis identity
- `expected_nodes`

異なる disposable commit で旧文字列が一度だけ一致しても、周辺 production が違えば同一 mutant とは言えない。また option ごとに `expected_nodes` を変えると、同じ `rc/failed_nodes` でも harness status が変わる。`MISMATCH` を `KILLED` と読み替えないだけでは足りず、`detected-but-mismatched` と「事前登録一致」を別軸で報告すべきである。

覆す一手: manifest に base target blob、実適用 diff hash、runner/test blobs、環境 identity を含め、それらが option 間で一致することを示す。

### 7. `test_campaign.py:4452` の直接 `[:N]` kill 疑い — [refuted]

既存 test は iterator が exact `ast.Name("passes")` の loop を `next()` で取る [test_campaign.py:4452-4475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_campaign.py:4452)。実 loop は [pipeline.py:981](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/pipeline.py:981)。

この行を直接 `passes[:N]` にすると iterator は `ast.Subscript` になり候補が消えるため、未捕捉の `StopIteration` が node を失敗させる。N の値には依存しない。この狭い主張は静的に成立する。

覆す一手: その一行だけを `passes[:N]` にした状態で当該 node が rc=0 になる記録を示す。

### 8. 上の先例を本件の correctness gate へ一般化すること — [real]

同 test は「一致 loop が一つだけ」を検査しない。例えば actual loop を `passes[:N]` にし、その前へ inert な `if False: for ... in passes:` を置けば、`next()` は decoy を選び得る。source 順序 assertionだけが成立し、実 gate の truncation を見ない。

従ってこの先例が示すのは「単一の直接 slice を syntax で拒否できる」ことだけであり、非恒真性・semantic robustness・転用コストではない。

覆す一手: exactly-one cardinality、decoy loop、decorator、先行 prefix 化を含む negative-control matrix を同じ checker がすべて拒否することを示す。

### 9. 「150 test 中 36 が `import ast`」を採用可能性の根拠にすること — [real]

`test_*.py` に限定した静的 count は 150 中 36 で再現した。例として [test_campaign.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_campaign.py:12) がある。

しかし import 頻度は、対象 mutant の検出、偽陽性率、refactor 負担、恒真化耐性のどれも測らない。単に AST が既知の stdlib 依存だと示すだけで、C 採用の証拠にはならない。

覆す一手: 36 件を分類し、同種 correctness invariant の保守実績や neutral-refactor false-positive 率との相関を示す。

### 10. 「dispatch が tracked 限定コピーなので commit が必要」 — [refuted]

dispatch は repository archive を作らない。

- `run_tests.py` は既存の repo 外 path を絶対化する [run_tests.py:267-323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/run_tests.py:267)、[同:1674-1676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/run_tests.py:1674)。
- dispatcher は `repo_root` と argv を request に書くだけ [dispatch_compute.py:1371-1390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/pegasus/dispatch_compute.py:1371)。
- compute node は共有 pathへ `chdir` し、同じ argv を live checkout 上の runnerへ渡す [同:567-592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/pegasus/dispatch_compute.py:567)。

したがって共有 filesystem から見える repo 外 probe は、非変異コスト測定なら絶対 path のまま dispatch できる。

覆す一手: compute node で job directory が不可視、または dispatcher が tracked archive へ置換しているコード経路を示す。

### 11. 現 mutation harness で候補を変異測定するには tracked commit が必要 — [real]

必要性の原因は dispatch ではなく、harness の test-target gateである。[mutation_harness.py:543-582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_harness.py:543) は target が checkout 内かつ `HEAD:path` に存在することを要求する。

従って repo 外 probe の通常 timing は commit 不要だが、現 harness で ledger を作るには disposable tracked file または harness 自体の変更が必要である。

覆す一手: 現 harness が repo 外 absolute test target を preflight 通過させる記録を示す。

### 12. 「1 mutant 27〜37秒」を本 wave へ転用すること — [real]

brief の主張は [s1-brief.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s1-brief.md:28)。しかし T-627 ledger の同じ P-N1 mutant は `42.29s` [mutation-ledger-v3.json:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/output/insights/2026-08-08_t627-noop-binding/mutation-ledger-v3.json:209) であり、他にも約 42.2 秒が複数ある。runner は 2 file・214 node scopeだった [同:948-958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/output/insights/2026-08-08_t627-noop-binding/mutation-ledger-v3.json:948)。

本 wave の 4-node／2-node runnerとは test量も spec も違い、dispatch 起動時間の比率も変わる。過去値は予算の桁感にしか使えず、option 間 cost の実測値にはならない。単発 `duration_s` も約 26.9〜42.3 秒へ散っており、反復なしでは runner cost と queue/bring-up noise を分離できない。

覆す一手: 同一 runner scope・同一環境で各 option を複数回、順序を交互化して測り、27〜37秒帯に安定して収まることを示す。

### 13. C1/C2 の target 解決が非恒真か — [unknown]

候補ファイルはまだ存在しないため実装を検査できない。[s2-plan.md:412-415](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:412) は exactly-one を要求しているが、実装保証ではない。

- bare `next(generator)` または `assert len(matches)==1` なら、関数 rename は空集合で失敗し、静かには通らない。
- `next(generator, None)`、条件付き assertion、`all([])` を使えば rename で恒真化し得る。
- decorator は AST 上の `FunctionDef` を消さないため空集合にはならないが、runtime binding を別 callable に差し替えても C1 が旧 body を見て通る条件を作れる。
- C2 が import 後の decorated callable を見る場合は、対象 instruction の空集合処理次第で失敗にも恒真にもなる。

覆す一手: 実装後、target/loop の cardinality を明示 assertしていることを静的に確認し、rename・削除・decorator control がすべて node failureになる記録を得る。

### 14. C1/C2 が通っても量化縮退を殺していない条件がある — [real]

直接 `[:N]` 以外には既知の逃げ道がある。

- C1: `changed[:] = changed[:N]` または `del changed[N:]` の後で元の `for ... in changed:` を保つ。単純な `ast.Name(Store)` 再束縛検査では `ast.Subscript(Store/Del)` を落とす。
- C1: inert decoy loop に expected body pattern を置き、実 loop を truncation する。
- C1: decorator が runtime gate を置換しても、source body は不変。
- C2: `changed = changed[:N]` を前行へ置けば loop 自体は依然 `LOAD_FAST → GET_ITER`。プラン自身もこの偽陰性を認める [s2-plan.md:442-449](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:442)。
- C2: line 275/300 固定抽出が空集合になったとき `all([])` 型実装なら恒真化する。

よって C が閉じられるのは、実証した「直接 literal slice family」だけである。[s2-plan.md:287](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:287) の但し書きを落として「残穴が消えた」とは言えない。

覆す一手: 上記等価 truncation 全てを拒否し、同時に rename・`tuple(changed)` 等の neutral refactor を受理する checker を示す。

### 15. 測定 commit／worktree が本番・land 集合を汚す経路 — [real]

具体経路が複数ある。

- plan の A commandは共有 wave worktreeを `--repo` にし、実走時は `--plan-only` を `--detached` に替える [s2-plan.md:335-370](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:335)。harness は production fileを実際に書き換える [mutation_harness.py:1277-1286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_harness.py:1277)。wrapper が「推奨」のままなら、並行 wave が変異中 bytes を読む。
- `mutation_worktree.py --commit` は commit を作らず、任意の指定 commit を解決するだけ [mutation_worktree.py:240-276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_worktree.py:240)。その commit に production／既存 test／spool fragment が混入しても、wrapper は選択 commit と clean tree であることしか検証しない [同:533-550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_worktree.py:533)。
- measurement commit の子孫へ docs commit を積み、その branch/rangeを landすれば probe も入る。land path allowlist／baseとの差分制約は wrapper にない。
- container 名は scratch rootごとに固定 [同:33-34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_worktree.py:33) だが lock は `--out` ごと [同:185-213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_worktree.py:185)。別 out の `--resume --plan-only` が同 commit の clean containerを採用し、harness lock失敗後も `plan_only` 条件で teardownし得る [同:446-459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_worktree.py:446)、[同:913-915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_worktree.py:913)。
- shared snapshot は primary と source worktreeの porcelain/submoduleだけ [同:339-381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_worktree.py:339)。sibling wave、job directory、spool ownership、commit ancestryは監視しない。

段 4 では、option ごとの一意 scratch root、wrapper 必須化、`base..measurement` の path allowlist、measurement commitとland branchの非祖先化が必要である。

覆す一手: repository-global container ownership、base blob allowlist、land ancestry検査が機械的に実装済みであることを示す。

### 16. 「gate として効く全層」は candidate scope から落ちている — [real]

実 consumer は二つある。

- production loader: [env_contract.py:519-532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract.py:519)
- issuer の publish 前 gate: [issue_env_contract_activation.py:179-213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/issue_env_contract_activation.py:179)

一方 B candidate は `_validate` helper [test_env_contract_activation.py:157-170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:157) を直接使い、C は leaf source/bytecodeを見る。既存 wiring pins は loader [同:1544-1564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:1544) と issuer [同:2021-2114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:2021) にあるが、candidate-only mutation commandから外れているうえ、最大 2 env の production registryでは `N≥4` を発火させない。

裁定パッケージには未実装の追加候補として、次を別 cost 行で返すべきである。

- loader経由で tail-only不正遷移を与え、cache clear後の `current_activation_state()` が fail-closedになる integration pin。
- issuer経由で tail callback failureを与え、`_write_create_only` が呼ばれないことを確認する integration pin。
- M>N の合成 registryを使い、leaf detectorと二つの wiring detectorを別々に記録する。

覆す一手: candidate ledger が両 consumer 経路を実際に通り、tail mutantで loader拒否と publish非実行の双方を観測していることを示す。

### 17. 親 brief の P1〜P4

- **P1 — [unknown]** 「有限の通常 tuple fixtureなら穴を最大 M の先へ移すだけ」は論理的だが、B/C の分類が未裁定。slice時だけ失敗する tuple subclassを private gateへ渡す runtime sentinelなら、AST/bytecodeなしで全 literal N を検出できる。形の pinなので C3 と呼ぶこともでき、分類次第で P1/P2 は循環論法になる。参照: [s1-brief.md:52-56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s1-brief.md:52)。覆す一手: Bを exact production tuple上の extensional fixtureだけ、と先に定義する。
- **P2 — [real]** 「残穴を実際に閉じる」は過大。C1/C2も直接 literal familyしか閉じず、先行 prefix化等を残す [s2-plan.md:427-430](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/s2-plan.md:427)。覆す一手: 結論を「登録した直接 `[:N]` family」に限定する。
- **P3 — [real]** strict linear／M64無視可能は未成立。test helperは envを sortし [test_env_contract_activation.py:130-145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:130)、production decodeも sort比較する [env_contract_activation.py:215-229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract_activation.py:215)。覆す一手: raw値と O(M), O(M log M) fitで M64のCI増分が測定誤差内だと示す。
- **P4 — [real]** 「初の第三者 test dependency」は偽。pytest は既存 import [test_env_contract_activation.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:23)、xdist は既に自動導入経路を持つ [run_tests.py:253-264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/run_tests.py:253)。成立し得るのは「初の tracked 依存宣言機構」。覆す一手: 用語を後者へ限定する。

## 総括

1. 最重: G-N1〜3 の `expected_nodes` は全件過少で、現 spec のままなら 3 件とも `MISMATCH` になる。  
2. 最重: focal scope は P-N1 の既存 semantic detectorを 5件中2件落とし、G-N1 の loader／issuer false-rejectも隠す。  
3. 最重: disposable commit・固定 container・out単位 lockには、並行 wave／spool／land混入を防ぐ機械境界がない。  
- 段4裁定: G expected集合を修正してから進むか、現 spec を破棄すること。  
- 段4裁定: full-file union/marginal と focal attribution の両測定を必須にすること。  
- 段4裁定: `raw detection` と exact expectation一致を別指標にすること。  
- 段4裁定: Cの保証を direct literal familyへ限定し、C3 runtime sentinelも比較対象にすること。  
- 段4裁定: loader＋issuer integration add-onと、measurement commit隔離条件を裁定パッケージへ載せること。