静的レビューのみ。pytest は実行しておらず、緑は主張しない。

## C-01 — 案 E は既存テストの実行可能な断言を弱める

- **判定: real**
- **重大度: Blocker**

当該テストが現在断言している性質は次のとおり。

1. 実 index を変更せず、HEAD と index/worktree 差分を含む同一候補 commit を作る（[test:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:76)、[test:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:118)）。
2. その候補に対する production 既定経路の `validate_condition_freeze_at` が、最初の一回で例外なく完了する（[test:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:124)）。これは明示 `assert` ではないが、未捕捉例外を許さない実行可能な断言である。各 Git invocation に production の 15 秒上限が掛かる（[production:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:87)、[production:880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:880)）。
3. 旧 legacy namespace がない（[test:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:133)）。
4. generation が 1 から tip まで連続し、validator の tip と一致する（[test:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:135)）。
5. tip record の protected hash、§5/§6/normative/evidence hash、および g1 の `supersedes=None` が一致する（[test:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:143)）。

案 E でも 3〜5 は成功した一試行について残る。しかし 2 は

```text
最初の production-default invocation が成功
```

から

```text
有限回のうち少なくとも一度成功
```

へ変わる。明示 `assert` の文字列を残しても、テストの受理集合は広がる。brief v2 の「同一 assert を保つ」「assert を緩和しない」はこの制御フロー変異を捕捉しない（[brief v2:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief-v2.md:47)、[brief v2:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief-v2.md:60)）。

- **成果物影響:** fresh/contended な production 発効判定は `freeze_reason_code="git-timeout"`・`condition_freeze_valid=False` のままでも、受入全走だけが failed→passed になり得る。凍結 bytes は変わらない。

## C-02 — direct validator 内での reason 変換漏れはない

- **判定: refuted**
- **重大度: なし。ただし実装条件つき**

production 内の写像は以下が全経路である。

| 経路 | `git-timeout` の扱い |
|---|---|
| `_git` | `TimeoutExpired` を唯一ここで `PreregistrationError("git-timeout")` にする（[production:880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:880)） |
| `_git_text`、各 batch helper、`validate_condition_freeze_at`、`prepare_revision` | reason を変えず伝播（[production:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:909)、[production:1310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1310)、[production:1686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1686)） |
| `condition_freeze_valid_at` | 全 `PreregistrationError` を `False` に消す（[production:1429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1429)） |
| `_activation_report_at` の source 先読み | 全 reason を捨てる。その後 validator が成功すれば `freeze_reason_code="valid"` のまま findings が空になる（[production:1537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1537)） |
| `_activation_report_at` の validator | `freeze_reason_code="git-timeout"`、validationなしへ写す（[production:1544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1544)） |
| `effective_at` | 上記 report から `None`（[production:1614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1614)） |
| `require_effective_preregistration` | report が非発効なら新しい `preregistration-not-effective` へ写す（[production:1769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1769)） |
| evaluator 呼出し | evaluator 内の例外なら predicate reason `evaluator-exception` へ写す（[production:1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1515)） |
| CLI | report 化された timeout は `NOT_EFFECTIVE`/rc=1、伝播した例外は outer catch で rc=2（[production:1799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1799)） |

対象テストは wrapper ではなく validator を直接呼ぶため、ここでは reason は保存される。安全な判別は `str(exc)`、substring、`exc.args` ではなく、機械契約である

```python
except prereg.PreregistrationError as exc:
    if exc.reason != "git-timeout":
        raise
```

だけである（reason field は [production:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:104)）。`str()` は detail があれば `[reason] detail` へ変わり、substring は `git-failed` の detail に含まれる文字まで誤受理する。

- **成果物影響:** exact `.reason` 判定なら、reason 変換漏れによって非-timeout reject が受入される経路はない。案 E 自体による first-attempt 検出力低下は C-01/C-04 のまま残る。

## C-03 — 限定は効くが、F57 の資源競合「族」には届かない

- **判定: real**
- **重大度: High**

負荷劣化は必ず `TimeoutExpired` になるとは限らない。Git が OOM・外部 SIGKILL・spawn/temporary-file 失敗を受ければ `CalledProcessError`/`OSError` から `git-failed` になる（[production:902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:902)）。pytest worker/PBS 自体が kill されれば例外 filter にすら到達しない。F57 には suite 全体の PBS SIGKILL も既載である（[failures:1439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1439)）。

したがって E が吸収するのは今回観測した一点の署名だけで、「全走負荷下の Git 呼出しを族として扱う」という T-553 の要求ではない（[archive:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/archive/worklog-phase3-0806-248.md:360)）。

- **成果物影響:** 次の資源劣化が `git-failed` または worker kill なら、production は引き続き拒否し、受入全走も赤のまま。凍結 bytes は不変。

## C-04 — Q3 の「恒常劣化との分界線」は成立しない

- **判定: real**
- **重大度: Blocker**

再試行は同じ commit に対し validator 全体を直後に再実行する。最初の `cat-file --batch-check` が pack/index/tree のページを読みながら 15 秒で kill されても、OS page cache・共有 filesystem cache は次 process に残る。Git の process-local cache は消えるが、永続する OS cache だけで二回目が構造的に速くなる経路は成立する。

したがって次の恒常状態を E は見落とす。

```text
独立した cold invocation は毎回 15 秒超
直後の warm invocation だけ 15 秒未満
```

これは履歴成長・object layout による真の cold-path 劣化だが、E では timeout→success となり緑になる。「全試行が timeout なら赤」は実装結果の言い換えにすぎず、原因が一過性か恒常劣化かを識別する機械的分界線ではない（[brief v2:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief-v2.md:51)）。

今回の六回を cache warming が説明すると断定はしない。しかし Q3 の保証を反証するには、この到達可能な二世界が同じ timeout→success 列を生成するだけで十分である。

- **成果物影響:** cold production 発効判定は `git-timeout` のままでも、warm retry により受入だけ緑になる。凍結 bytes は不変。

## C-05 — 「負荷依存」は整合するが、「一過性 false reject」は未立証

- **判定: real**
- **重大度: Blocker**

観測は以下で一貫している。

- T-522: 48-worker 全走だけで timeout、単独再走は成功（[failures:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1387)）。
- T-459: 同じ target、単独再走成功（[failures:1405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1405)）。
- T-639: target と独立 ruleops node が同時に Git timeout（[failures:1426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1426)）。
- T-656/T-664: 親 Codex 子なしでも同じ target が再発（[failures:1464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1464)、[failures:1510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1510)）。
- 今回も同一 `_batch_oids` の 15 秒 timeout（[baseline:124](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/acceptance-baseline.txt:124)）。

これは負荷との相関を強く支持する。しかし F57 自身が原因分離を未閉鎖としている（[failures:1489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1489)）。単独再走は負荷・cache・時刻が同時に変わるため、共有資源競合と cold-path の構造的余裕不足を分離しない。また production は wall-clock 超過を正式な fail-closed 条件にしており、「semantic 内容は正しい」という意味以外では false reject とも言えない。

件数説明にも誤りがある。v1 は六件の列挙から T-459 を落とし、別 node の T-648 ruleops を代入している（[brief v1:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief.md:31)）。正しくは target の既載五件＋今回で六件、T-648 は族の追加一件である。v2 の「約20%」の分母約30走も、指定資料からは検証できない。

- **成果物影響:** benign transient と誤分類すると、production の繰返し fail-closed を残したまま受入の赤だけを消す。発効値と凍結 bytes は変わらない。

## C-06 — session fixture は再構築されず、案 E は fixture hardening ではない

- **判定: real**
- **重大度: High**

`repository_candidate_commit` は session scope で一度だけ構築される（[test:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:118)）。再試行は fixture を再実行せず、同じ commit OID・同じ object store・温まった cache を読む。

同じ candidate を保つ点は semantic 比較には正しい。しかし試行独立性はなく、C-04 を強める。さらに E が触るのは fixture の生成処理ではなく test body の production validator 呼出し（[test:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:131)）なので、brief v2 の「fixture を hardenする」は名称からして不正確である。T-327 の 180 秒は実際に候補構築用 `_git_text` に掛かっている（[test:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:43)、[test:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:89)）。

後続二テストも同じ candidate を使う（[test:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:190)、[test:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:206)）。直接の repository state 汚染はないが、cache warming と実行時間は波及する。特に `test_candidate_is_not_effective...` は `freeze_reason_code`/`condition_freeze_valid` を断言せず、timeout でも validation 成功でも `effective=False` なら通る。

- **成果物影響:** 同一 candidate の論理値と凍結 bytes は不変だが、先行 retry の cache によって後続 production-default call と受入結果が緑側へ偏り得る。

## C-07 — 再試行より先に採るべき検出力保存案がある

- **判定: real**
- **重大度: High**

最小の具体案は、実 repo の重い Git reader を同じ xdist group に統合することである。

現在は別名の三群になっている。

- s8c candidate: `"s8c-preregistration-candidate"`（[test:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:29)）
- ruleops real checkout: `"real_repo"`（[test_ruleops:2032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_ruleops.py:2032)）
- 中央正本: `"real-repo"`（[conftest:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/conftest.py:122)）

T-639 では前二者が同時 timeout しており、別 group のため scheduler が並走を許したことと整合する。candidate 三 nodeと ruleops nodeを `REAL_REPO_SERIAL_NODES` に入れて同じ `"real-repo"` groupへ寄せ、独立 golden も更新する（[conftest:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/conftest.py:125)、[golden:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_real_repo_serialization.py:35)）。これなら candidate の session共有、production-default 一発呼出し、全 assert を保ったまま、実測済みの Git×Git overlap を除ける。

ただし loadgroup は全 suite に対する排他ではない。これでなお再発するなら、`run_tests.py` の現在の単一 invocation（[run_tests.py:1859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/tools/run_tests.py:1859)）を、収集集合の和を機械照合する「並列通常群＋単独 real-repo-heavy 群」の二相受入へ設計し直すべきである。15秒負荷耐性も必要な性質なら、偶発的な全走競合へ相乗りさせず、別の固定負荷・first-attempt gateとして明示する。

- **成果物影響:** semantic/15秒一発検査を残したまま既知の競合を減らせる。production 発効値・凍結 bytes は不変で、受入だけを再試行によらず安定化できる。

## C-08 — brief v2 の安全主張は一部が恒真・循環している

- **判定: real**
- **重大度: Blocker**

| 項目 | 判定 | 攻撃結果 |
|---|---|---|
| Q1 | 一部 refuted | exact reason 限定は可能だが、「同一 assert」は制御フローによる量化変更を隠す |
| Q2 | real | 根治でないとの自己認識は正しいが、安全性の根拠にはならない |
| Q3 | refuted・循環 | 「全試行 timeout を恒常劣化と呼ぶ」だけ。timeout→success から原因を機械識別できない |
| Q4 | realだが非防壁 | 有限定数は無限 retry を防ぐだけで、first-attempt 検出力を戻さない |
| Q5 | real | T-553 を閉じないという自己認識は正しい。したがって「すべて直した」終端にはできない |
| 不変条件1 | real | production diff zero は静的に検査できる |
| 不変条件2 | 恒真化 | 明示 assert を一字も変えず、例外を retry loop で吸収できる |
| 不変条件3 | refuted・循環 | 「恒常的 timeout」の独立 oracle がなく、実装結果そのものを条件名にしている |
| 不変条件4 | realだが無関係 | author ownership は provenance を守るが、テスト弱体化を防がない |

production 差分ゼロにより DW-O09/O10 の producer write pathへ直接到達しない点は成立する（[brief v2:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief-v2.md:37)）。しかしこれは凍結 bytes の不変だけを守り、受入ゲートの意味不変を守らない。

- **成果物影響:** これらを安全証明として採用すると、凍結 bytes は同じまま、production 非発効と受入緑が同居する。

## 総括

(i) **案 E は規律 2 違反である。**

- production-default の一発成功という既存の実行可能な断言を、有限回中一成功へ緩める。
- session共有 commitとOS cacheにより Q3 の「恒常劣化との分界線」は成立しない。
- production が `git-timeout` で非発効のままでも、受入だけを緑にできる。

(ii) **NO-GO。案 E を段 5 へ渡してはならない。**

(iii) 親が代わりに採るべき行動:

1. 今回を F57 の target 六回目として記録し、T-459/T-648を取り違えた件数説明を訂正する。
2. [test:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py:131) の一発 production-default callを維持する。
3. まず s8c candidate・ruleops・中央 real-repo readerを同一 xdist groupへ統合し、既知の同時Git競合を除く。
4. なお再発するなら、原因計装と単独の受入相を設計する。必要なら15秒耐性を固定負荷の独立 gateにする。
5. production timeout政策を変えるなら案Cのユーザー裁定へ戻す。裁定までは案Dとして未解決停止する。