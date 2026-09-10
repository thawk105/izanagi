必読資料はすべて読めた。基準 HEAD は `bb824d8b7fff427eb61d09cf3d9354359914c99c`、作業木は clean。pytest・履歴 checker 本走は行わず、静的検査と read-only Git plumbing だけで判定した。

### 1. CAB を単一 epoch に畳むと branch-local policy を表現できない

severity: blocker

発火入力または再現手順:

1. CAB needle を含まない policy file を root `R` に置く。
2. `R` から分岐した branch A/B が、それぞれ独立に CAB needle を `P_A` / `P_B` で追加する。
3. 各 branch の子 `S_A` / `S_B` に `SPLIT_CAB_NONE` 型の配置違反を置き、両 branch を `H` へ merge する。
4. 現行 `cab_policy_mask` は `P_A|P_B` を持ち、`S_A` と `S_B` の双方に CAB 規則を適用する。
5. plan の「全 hit の祖先である一意 root」は 0 件。fail-closed なら rc=2、片方を任意採用すれば他方の明示 range が現行 rc=1 から rc=0 へ緩む。

実 repo でも pickaxe の集合は tip 依存だった。tip `8c8dc5e0a337677e213b4ebabbeff5ea188111ae` では hit 0、`9b26b3bd3acc10df95ef6ef6684a91d2ff3fa2ec` と HEAD では hit 1。tip 非依存なのは「各 commit が hit か」という局所判定だけで、複数 tip に対する集合集約ではない。

file:line: [plan.md:163](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:163)、[check_ai_provenance.py:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:643)、[check_ai_provenance.py:869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:869)、[check_ai_provenance.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:893)、[test_check_ai_provenance.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:862)、[test_check_ai_provenance.py:4660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:4660)

成果物影響: 現行で監査可能な履歴が rc=2 で実行不能になるか、任意 root 選択なら CAB 違反 branch が rc=0 になり commit gate の受理集合が広がる。CAB は単一 `E` ではなく、lineage ごとの seed 集合として残す必要がある。

### 2. `scope=` の最古 hit は policy 導入 commit を一意に表さない

severity: blocker

発火入力または再現手順:

1. commit `A` が `docs/ai-provenance.md` の例示や別節に非規範的な `scope=` を書く。
2. その子 `B` に、同一 role 2 行・scope 無しの message を置く。
3. 後の `P` で初めて scope 規則を導入する。
4. `git log --reverse -S scope=` は `[A,P]` となり、現行 `commits[0]` も plan の「全 hit の root」も `A` を選ぶ。`B` は本来 legacy なのに scope finding 2 件で rc=1 となる。

実 repo にも既に hit は2件ある。

- `2f0245c196f82dddef91a9966e19b78a4b3f62e9` — 実際の導入
- `6d7141dc8a174384f3b9be689d3516a8a3a31bbf` — forward-correction 文書改稿での count 変化

`--reverse` により現在は前者が `commits[0]` になるだけで、needle の意味を検証していない。既存テストは現在のファイルに `"scope="` が1個あることしか固定せず、履歴 hit を固定していない。

file:line: [check_ai_provenance.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:626)、[plan.md:166](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:166)、[test_check_ai_provenance.py:2979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:2979)

成果物影響: policy 導入前の commit を scope 違反として拒否し、commit gate が rc=0 で受けるべき履歴を rc=1 にする。scope finding は D221 台帳に登録できないため、現行機構では救済不能。

### 3. reachability 適用と「非遡及」文書契約は両立せず、0-byte 方針では land できない

severity: blocker

発火入力または再現手順:

- `R` から先に違反 commit `S` を side branch に作り、その後 main に policy commit `P` を置き、最後に `S` を `H` へ merge する。
- plan の `R_E` と plain `P..H` は `S` を検査して rc=1 にする。
- 規範文書は「導入 commit 自身と以後」「導入前は legacy」「導入 commit 以後だけ」と定めている。plan 自身も `S` が真の pre-policy commit かもしれないと認めている。

file:line: [plan.md:91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:91)、[plan.md:185](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:185)、[plan.md:304](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:304)、[ai-provenance.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/ai-provenance.md:6)、[ai-provenance.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/ai-provenance.md:29)、[ai-provenance.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/ai-provenance.md:46)、[audit.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/provenance/audit.md:15)

byte 実測:

- `docs/ai-provenance.md`: 6,287 / 6,300
- `docs/provenance/audit.md`: 1,346 / 1,600
- `docs/provenance/correction.md`: 1,361 / 1,600
- family: 8,994 / 9,000

上限は [test_check_docs.py:2303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_docs.py:2303) と [test_check_docs.py:2436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_docs.py:2436) が固定する。純増できるのは family 6 bytes だけ。

等価縮約の一案は、次の逐語4箇所を統合すること。`\n` は実際の LF 1 byte。

- 104 bytes: `本規約は導入 commit 自身と以後の commit に\n適用し、既存履歴を書き換えない。`
- 77 bytes: `この規則は内容検出した導入 commit 以後へ適用する (F25)。`
- 129 bytes: `導入 commit 以降にのみ適用して遡及せず、\n  checker も内容検出した導入 commit 以後だけ検査する。`
- 38 bytes: `本節を導入する commit 以後、`

計348 bytesを削り、次の180-byte 文へ統合できる。

`既定監査は各規則の内容検出 commit 自身と、その祖先でない HEAD 到達 commit に適用する。導入祖先は legacy とし、履歴を書き換えない。`

この骨格なら net −168 bytes、entry 6,119、family 8,826 になる。ただし PR-A02 と残る「導入 commit より後」も同じ意味へ揃える必要がある。

成果物影響: 文書を変えず実装だけ変えると、規範上 legacy の commit が rc=1 となり DW-O17 の full 監査が merge を停止する。文書への純増は物理的に不可能で、置換設計が必須。

### 4. 51,151 commit で CAB pickaxe が `ARG_MAX` を超え、full 監査が実行不能になる

severity: blocker

発火入力または再現手順:

- base policy を root に置き、既定選択集合を51,151 commitにする。
- `_build_ancestry()` の2本目は全 SHA を positional argv に展開する。
- 40-byte SHA と NUL だけで `51,151 × 41 = 2,097,191 bytes`。この環境の `ARG_MAX` は `2,097,152`。
- 51,151個の引数を渡した read-only probe は `OSError: [Errno 7] Argument list too long` になった。main はこれを捕捉して rc=2 を返す。

file:line: [plan.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:55)、[check_ai_provenance.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:893)、[check_ai_provenance.py:2050](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:2050)、[checker.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/dev_waves/checker.py:328)

計算量・メモリ:

- 現在は選択1,702、祖先閉包2,041。`bits` の tuple と整数本体は347,148 bytes。
- CPython の自己 bit だけでも、100,000件で670,066,720 bytes、400,000件で10,680,266,720 bytes。
- bitset だけで4 GiBを初めて超えるのは253,565件、12 GiBは439,374件、14 GiBは474,599件、16 GiBは507,385件。`rows`・index・Git子プロセスは別なので実際の上限到達は早い。
- 現在の call graph は full audit 1回につき少なくとも9,111 Git subprocess。plain 化の現行増分は0件、4-epoch strict 化は既存 validator のままなら29 subprocess増。将来の通常 non-merge 1件ごとに docs-only で6本、実装面で7本増える。並行生存数は `AUDIT_WORKERS_CAP=32` 以下。
- 現存する性能実測は試作596 commit・32並列の5.23秒だけで、現在の出荷 call graph の所要時間は静的には断定できない。[pegasus-runbook.md:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/pegasus-runbook.md:596)

成果物影響: full 監査が rc=2 になり実行不能。dev-wave supervisor は rc=2も `PROVENANCE_FAILED/nonzero` と記録するため、違反ではなく exec 上限なのに commit gate の受理集合が事実上空になる。argv を stdin 等へ移した後も二乗 bitset と4 GiB local capの受入条件が必要。

### 5. 真の legacy 違反に D221 も correction も使えない

severity: must-fix

発火入力または再現手順:

- policy 前に分岐した共有済み branch に、形式違反・scope 違反・CAB 違反のいずれかを置き、policy 後に merge する。
- reachability strict はその commit を検査する。
- D221 が受けられるのは `missing-ai-agent` と `missing-codex-author` だけ。scope/CAB/形式 finding の `ledger_kind` は `None`。
- forward correction は固定 target で消費済み。

plan はこの欠落を30行目で認識しているが、最終裁定項目と land 順序は `333605d6…` の missing-codex-author しか扱っていない。

file:line: [brief.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/brief.md:68)、[plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:30)、[plan.md:338](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:338)、[check_ai_provenance.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:132)、[correction.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/provenance/correction.md:13)

成果物影響: full 監査は恒久的に rc=1となり、DW-O17 が land を停止する。裁定パッケージには「merge 前 rewrite を義務化する」か「D221 schema／新 attestation を別裁定する」かを明記する必要がある。

### 6. `epoch-lineage-gap` は dev-wave receipt に残らない

severity: must-fix

発火入力または再現手順:

- plan の現行 main 想定どおり26件の gap を stdout に出す実装にする。
- `tools/dev_waves/cli.py` の default provenance check を通す。
- consumer は stdout/stderr を `DEVNULL` に捨て、receipt には pass または汎用 `PROVENANCE_FAILED` だけを残す。

file:line: [plan.md:170](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:170)、[cli.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/dev_waves/cli.py:188)、[checker.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/dev_waves/checker.py:328)、[brief.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/brief.md:17)

成果物影響: rc と gate acceptance は変わらないが、監査 receipt から26件の epoch・SHA・仮想 finding 数が全欠落する。「直接実行時の terminal 公開」に限定するか、T-621 の durable consumer を裁定パッケージとして明示すべき。

### 7. brief M6 の「`_audit_history` は順序非依存」は verdict にしか成立しない

severity: nit

発火入力または再現手順:

- finding を持つ2 commitの入力順を逆転すると、`Executor.map` が保存する順に stderr finding が逆転する。
- 2 commitで例外を起こすと、入力順で先の例外だけが main の rc=2 detailになる。入力を逆にすれば表示 SHA も変わる。

plan はこの点を既に補正し、`--reverse` を残している。

file:line: [brief.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/brief.md:28)、[check_ai_provenance.py:1057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:1057)、[test_check_ai_provenance.py:4558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:4558)、[test_check_ai_provenance.py:4723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:4723)

成果物影響: commit gate の rc/受理集合は同じだが、直接監査ログの finding 順と rc=2 detail が変わる。

## 反証・追認

- `_build_ancestry` の閉包懸念は refuted。`rev-list --parents --stdin` は選択集合そのものではなく正 tip の祖先閉包を返す。HEAD単独は2,041行、`HEAD^1` は2,040行、両方でも2,041行。既定選択1,702件からの閉包も2,041件だった。canonical complete DAG では選択集合変更後も親欠落は生じない。
- plan の default membership テストは恒真ではない。`S` は plain `P..H` に入り、`--ancestry-path P..H` から消えるため、membership の exact assert と期待 rc=1 の双方が静的に不成立になる。pytest は未実行。
- M2 は追認した。`f85e16e2416197adc2c24b1af7784db9bb807b87..HEAD` は ancestry 62、plain 79。
- M7 は追認した。`_commit_range(`、`ancestry-path`、`policy..HEAD`、default-history、`sys.argv` の別検索でも直接 membership test は0件。既存762行は直線履歴だけ。
- `tools/dev_wave_land.py` は [dev_wave_land.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/dev_wave_land.py:1387) の `--message-file` preflight だけなので、今回の history range 変更では壊れない。DW-O17 の correction 契約とも矛盾しない。
- hook 層は refuted。checker は [check_ai_provenance.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:4) で非 hook を明記し、CLI 面も変わらない。追加 hook は不要。

触れていない有効層は、規範文書、T-621 の receipt consumer、Pegasus の規模別 admission/performance acceptance の3つ。前二者は裁定パッケージへ、最後は実装前の機構修正・受入条件へ戻すべきである。

## 総括

blocker あり（4件）。現状の `plan.md` は land してはならない。