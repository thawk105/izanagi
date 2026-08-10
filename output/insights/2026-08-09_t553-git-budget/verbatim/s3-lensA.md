結論は **NO-GO**。Critical 0、Major 5、Minor 1。serializability の内容検査を直接飛ばす経路は見つからなかったが、RATE/CAP の決め方、stdin 迂回口、未実測の無 stdin 経路、成果物影響の記述が未閉である。

## 数値判定

48-worker 下の実所要を `U` 秒、`R=7,002` とすると、観測を包む最小係数は

```text
RATE_min = max(0, (U - 15) / 7002)
```

一方、プランは `RATE=U/7002` を採るため、同じ R では必ず

```text
B(7002) = 15 + U
```

となる。したがって `U/R` は循環ではなく、`(U-15)/R` より常に `15/7002 = 0.002142245 s/request` 大きい、実質 **15 秒の加算余裕**である。独立した倍率 safety factor はないが、その不在だけを欠陥とは判定しない。

| 仮の uncensored `U` | 最小 RATE | プラン RATE | `B(7002)` | CAP |
|---:|---:|---:|---:|---:|
| 20 秒 | 0.000714082 | 0.002856327 | 35 秒 | 157.816 秒 |
| 30 秒 | 0.002142245 | 0.004284490 | 45 秒 | 229.225 秒 |

ただし既存の負荷下観測は 15 秒で打ち切られた `git-timeout` なので、分かるのは `U>15` だけである。40.48 秒はテスト群全体の単独再走時間であり、1 回の `_git` の `U` には使えない。contended な uncensored `U` はまだ存在しない。

## 所見

### A-01 — Major: 1 本の RATE へ batch-check と byte 支配 batch を畳むと、CAP が安全境界にならない

プランは少数 R・最大 64 MiB に近い `--batch` も `max U/R` へ入れるとしている。[s2-plan.md:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/s2-plan.md:39) [s2-plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/s2-plan.md:52)

合法な 16 MiB blob 4 本、`R=4` の cell が仮に `U=1秒` なら `RATE=0.25`、CAP は `15+50,000×0.25=12,515秒`、約3時間28分になる。これは有限ではあるが、50,000-request の絶対防壁として過大である。逆に byte cell を測らなければ、将来の合法な大 blob 入力を過小予算にする。

さらに現在の probe は実 repo の OID を重複排除するだけで、近上限 fixture を生成しない。[probe_git_batch_budget.py:199](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py:199) [probe_git_batch_budget.py:704](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py:704) smoke では4 OID・小 payload のみで、contended 本測定も未実走である。現 probe のままではプラン自身の必須 cell を満たせない。

**成果物影響:** 未修正なら、低 byte の RATE では合法入力が再び `freeze_reason_code="git-timeout"` となり gN・report・trial ledger が生成されず、高 byte の RATE では無関係な50,000行入力まで数時間の予算を得る。

### A-02 — Major: stdin 行数は command に束縛されず、実在する予算増幅経路がある

`MAX_GIT_INPUT_BYTES=16 MiB` は `MAX_BATCH_REQUESTS=50,000` を代替しない。

- SHA-1 OID 1行を41 bytesとすると、50,000行は2,050,000 bytesにすぎず、16 MiBには409,200行入る。
- SHA-256 OIDでも258,111行入る。
- `b"x\n"*50_000` は100,000 bytesだけで CAP に到達する。

全 caller の結果は次のとおり。

| 経路 | `MAX_BATCH_REQUESTS` の実効 bound |
|---|---|
| `_batch_oids():1113` | `len(commits)×len(paths)` を行1105で直接検査する |
| `_assert_rulings_exist():1289` | `_batch_oids` を必ず通る。production の checks も最大 g2..g1024 の1,023件 |
| `_batch_blob_bytes():1137,1160` | 自身には検査なし。ただし現2 callerは `_batch_oids` の結果の部分集合なので最大50,000 |
| `read_blob_at():944` | `_batch_oids` を通らない |
| `_git` / `_git_text` の直接利用 | byte limitだけで、行数の意味的 boundなし |

特に公開名の `read_blob_at(repo, commit, path)` は `path` の LF を拒否せず、`resolved:path\n...` をそのまま batch-check へ渡す。[s8c_preregistration.py:938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:938) 複数の有効な `HEAD:path` 行を埋め込めば予算を CAP まで増やせるうえ、返却 parser は先頭3 tokenだけを検査し、後続 headerを拒否しない。[s8c_preregistration.py:944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:944)

現 production の activation 経路は固定 pathなので直ちに悪用されないが、「timeout引数が無いから迂回口も無い」という条件①の実質は成立していない。予算を exact command family／意味的要求へ束縛する検査が必要である。

**成果物影響:** 未修正なら、直接・将来 callerが無関係な stdin を添えて最大予算を獲得し、通常なら早く `git-timeout` になる読取が activation/report/ledger 生成まで進む、または受入全走を長時間占有する。

### A-03 — Major: P1 は無条件では採れない。history-log の測定は本 wave の land 条件である

`_history_namespace_paths()` は全履歴に対する `git log --name-only` を無 stdin・15秒で実行する。[s8c_preregistration.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1088) 過去6回の timeout が batch にあったことは、この手前の command が次のボトルネックにならない証拠ではない。

段2の「同じ48並列条件で測り、15秒超なら段4を停止」は正しい最低線である。[s2-plan.md:105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/s2-plan.md:105) probeにも exact commandは入っているが、本測定結果はまだ無い。[probe_git_batch_budget.py:641](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py:641)

裁定は次のとおり。

- history-log の contended 測定は本 wave scope内の必須 precondition。
- 15秒超または cap近傍なら、cat-fileだけ直して landせず、同じ waveでscope再裁定する。
- 十分な余裕を実測できた場合のみ、production変更を15秒据え置きに限定してよい。

**成果物影響:** 未実測のまま据え置くと、赤が `_batch_oids` から `_history_namespace_paths` へ移り、validation・gN生成・report・trial ledgerはいずれも引き続き欠落する。

### A-04 — Major: RATE の根拠を永続成果物へ束縛する層が未設計

briefは「probeと実測値の記録」を成果物に含めるが、記録先・raw結果hash・RATEへの導出参照がない。[s1-brief.md:90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/s1-brief.md:90) 計画中の定数テストは RATE/CAP literalを複製するだけで、同じ転記誤りを検出できない。[s2-plan.md:122](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/s2-plan.md:122)

少なくとも `repo_head`、host/PBS、R/S、concurrency、repeat、全 workerの uncensored 最大値、上向き丸め、結果JSONのsha256から production定数までを1本の durable referenceへ結ぶ必要がある。job directoryだけでは後日消失し得る。

**成果物影響:** 未実装なら、誤転記・別HEAD・失敗除外から作られた RATEでも単体テストが通り、`B(R)` と CAP、ひいては report／ledgerへ到達する実行集合が根拠なく変わる。

### A-05 — Major: briefの「report・台帳値は不変」は誤り

production module bytesが変わるため、新commitを評価する activation reportでは `core_module_blob_sha256` と report digest が変わる。[s8c_preregistration.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1533) [s8c_preregistration.py:1745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1745)

その digest は launch admission、lifecycle、acceptance receiptへ入る。[trial_registry.py:1244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/trial_registry.py:1244) [trial_registry.py:1572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/trial_registry.py:1572) [trial_registry.py:2412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/trial_registry.py:2412)

また旧 prereg commitを新しいlive moduleから再評価すると、core bytes不一致により predicatesがERROR、`effective=False`になり得る。[s8c_preregistration.py:1559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1559) これは下流コードを本 waveで変更せよという所見ではなく、裁定パッケージへ記録すべき影響である。現 wiring は `certifying=False` なので、certified選択値そのものは現在生成されない。

**成果物影響:** 未記録なら、「値不変」とされた activation digest・launch report・lifecycle行・acceptance receipt bytesが実際には変わり、旧 prereg参照は `effective` から外れ得る。

### A-06 — Minor: `R=7,002` は HEADには正しいが、赤い invariant の実値ではない

`git rev-list --count HEAD=2334` と3 pathsから HEAD評価は7,002要求で正しい。しかし invariant fixtureは `commit-tree ... -p HEAD` で候補commitを1つ追加する。[test_s8c_preregistration_invariant.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_invariant.py:76) したがって現 failing chainは2,335 commits×3 paths＝**7,005要求**である。将来g2なら現時点換算で2,335×4＝9,340要求となる。

helperは実 stdinを数えるのでproduction式自体は追随するが、`current-r-7002` というテスト名・probe cell・briefの「赤の実要求数」は訂正すべきである。

**成果物影響:** 未修正なら invariantで実際に使われる予算は記録値より `3×RATE` 大きく、測定・テスト参照が実行対象と一致しない。

## 条件①〜⑤

| 条件 | 静的判定 | 根拠 |
|---|---|---|
| ① caller timeout引数なし | **部分／実質未充足** | signatureは維持するが、command非束縛stdinと `read_blob_at` のLF経路で予算を増幅できる |
| ② 1 invocation・deadline 1つ | **充足** | `_git` のsubprocessは1回のまま。chunkなし |
| ③ 50,000点でcap | **字面上充足** | `min` は有限。ただしRATE混在によりcapが数時間化し得る |
| ④ contended実測 | **未充足** | compute本測定なし。現probeは近64 MiB fixtureも作らない |
| ⑤ invariantが同じ式を通る | **充足** | test行131 → `validate_condition_freeze_at`行1310 → `_batch_oids`行1326 → `_git`行1113。blob側も行1327→1137/1160→`_git`。180秒定数は候補commit作成用だけ |

## 親実測の再確認

| 主張 | 再確認 |
|---|---|
| (i) HEAD=2334 commits | 再現した。ただし failing candidateは+1 commitで7,005要求 |
| (ii) freeze pathはg1のみ | `git log` と `git ls-tree` の双方でg1 1本のみを再現。g2発行時の4 pathsは式が実stdinから自動的に1.33倍へ追随する |
| (iii) provenance rc=0 | 実行したが、read-only環境で `output/pegasus-dispatch` を作れず **rc=16**。これは監査結果ではなくdispatch setup failureであり、rc=0は独立再現していない。worklogには過去rc=0記録があるが、最終commit後の再走が必要 |
| (iv) s8c bytes pinなし | 再現した。`FROZEN_MANIFEST` は23 keyでs8cなし。g1 raw SHA-256=`a8fe5246…3419`、`protected_sha256=853e6c44…286e` はg1自身以外にexact pinなし。ただし下流digest不変までは導けない |

## scope判定

本 wave内で閉じるべき層は、計測結果とRATEのdurable binding、RATE/CAP定数、stdinからのruntime量抽出、command/caller束縛、subprocess timeout、reason code保存、core境界テスト、実repo invariant、history-logのland preconditionである。

scope外だがrealな裁定パッケージ候補は、旧 prereg commitのcore-identity失効、activation digestからlaunch/lifecycle/receiptへのbytes伝播、現在は非certifyingであることの明記、および current history-logが通っても10,000 commitまでの将来予算化を別途扱うか、である。これらを理由に下流コードを本 waveで変更してはならない。

pytestは実行しておらず、緑は主張しない。書き込み・commitも行っていない。

## 総括

- **NO-GO**。Critical 0、Major 5、Minor 1。
- `U/R` は循環でなく同一Rへ15秒の加算余裕を持つ。
- ただしuncensoredな48-worker `U` はまだ無く、RATEは確定不能。
- 現probeは必須の少数R・近64 MiB cellを生成できない。
- stdinはcommandに束縛されず、`read_blob_at` のLFでCAPを得られる。
- history-log測定は同waveのland条件で、超過時はscope再裁定が必要。
- g2の4 pathsは式へ自動反映されるが、赤いcandidateの現Rは7,005。
- report・lifecycle・receipt値は不変ではなく、裁定パッケージへの記録が必要。