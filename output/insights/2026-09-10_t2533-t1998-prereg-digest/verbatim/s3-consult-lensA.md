## 前提と読んだ資料

指定された追加射影を含む次の全資料を読めた。読めなかった path はない。

- `s1-brief.md`
- `s2-plan.md`
- `verbatim/D1874.md`
- `verbatim/D1790.md`
- `verbatim/D1244.md`
- `verbatim/D1267.md`
- `verbatim/D1525.md`
- `artifacts/probe-source-digest.json`
- `artifacts/probe-env-contract.json`
- `artifacts/AUTHORITATIVE-VALUES.md`

指定 worktree では consumer 全文と、`buildcache.py`、`backoff_sweep.py`、`source_digest.py`、`loop.py`、producer job body、submitter、patch、既存テスト、T-1998 handoff/insight、B-10 loader の関連範囲を読んだ。親側 checkout は読んでいない。pytest、build、benchmark、qsub は実行しておらず、緑とは報告しない。

## 所見

1. **重大度: must-fix** — target の `source_bytes_sha256=6454d9f3…` は正式 producer が測定する source の digest ではない。probe は target を `tracked_clean=true` / `src_token=stock` と記録している (`artifacts/probe-source-digest.json:21-27`)。しかし正式経路は `silo-backoff-fixed.patch` を適用してから campaign を走らせ (`orchestrator/campaign/backoff_sweep.py:410-411,462-473`)、target では patch の fixed 分岐が stock の `Backoff_.load` を別式へ置換する (`patches/silo-backoff-fixed.patch:60-73`)。WAL の source evidence はその適用中 source から計算される (`orchestrator/campaign/loop.py:627-630`)。`6454…` は repo の B-10 provenance でも `BACKOFF_FIXED=-1,BACK_OFF=1` の inert/adaptive digest として記録されている (`output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json:557-559`)。planned positive test は同じ literal を fixture の artifact と prereg の両側へ置くため、この誤りを検出しない (`orchestrator/tests/test_t1998_stock_inline_pair.py:116-121,399-405`)。  
**影響:** 正式 fixed-5 artifact は `source-identity-unbound` (`orchestrator/campaign/t1998_stock_inline_pair.py:521-533`) で拒否され、T-1998 の適格値を 1 本も得られない。

2. **重大度: must-fix** — patch 適用下で再計算しても、login node の同名 `g++` から compute node の digest は一般化できない。compute でだけ `("gcc","g++")` が選ばれる (`orchestrator/campaign/buildcache.py:1838-1842`) 一方、source digest は builtin と preprocessor 出力を残し、実装自身が「cxx/環境に依存する」と明記する (`orchestrator/campaign/source_digest.py:1646-1659`)。probe JSON は executable identity/toolchain manifest を持たない。具体的反例は、login と compute の `/usr/bin/g++` に同じ `--version` 文字列を返す別 build を配置し、一方だけが inspected source で使われる macro（例: `RWLOCK`）を predefined にすること。同じ `"g++"` 選択でも正規化 source bytes は変わる。  
**影響:** compute 上で内部整合した artifact でも、事前登録した login digest と違えば `source-identity-unbound` で拒否される。

3. **重大度: must-fix** — D1790 の成果物側定数への割当が逐語と異なる。D1790 が要求するのは「成果物が記録しているべき事前登録 sha」と「現行解析文書 sha」の二つ (`verbatim/D1790.md:3-5`) だが、plan は前者を job body sha に置換している (`s2-plan.md:96-105,301-303`)。`reservation.binding.script_sha256` は実際にも job body の digest である (`tools/pegasus/a5_second_boot_backoff_sweep.sh:414-426`; consumer `:915-919`)。reservation と result の schema には preregistration sha が存在しない (`a5_second_boot_backoff_sweep.sh:424-440,761-785`)。scalar 一値比較である点は正しいが、pin する対象が違う。  
**影響:** 同じ job body を使った別 preregistration cohort を成果物側 pin で区別できず、D1790 が禁止する測定時点版の曖昧化が残る。

4. **重大度: must-fix** — `repository_commit` は固定値にならない。plan の条件は「引数が HEAD の祖先」「指定 commit の文書 blob が現行 bytes と同じ」だけ (`s2-plan.md:117-124`) なので、文書を変更しない後続 commit はすべて `prereg_commit` 候補になる。consumer は caller が選んだ値を result/reservation と比較するだけである (`orchestrator/campaign/t1998_stock_inline_pair.py:823-851`)。文書に自身の commit/hash を書かず、文書 hash をコード定数に置く点は F36 に抵触しないが、その回避策から「期待 commit は一意」という D1874 の束縛は導けない。  
**影響:** 受理される repository commit が事前登録時の一値ではなく、「同じ文書 blob を持つ祖先 commit」の集合へ広がる。

5. **重大度: must-fix** — loader は正式 consumer 経路に不可避化されない。dataclass は整形式しか検査せず (`orchestrator/campaign/t1998_stock_inline_pair.py:131-181`)、consumer は直接構築した object を引き続き受け取る (`:707-714`)。plan も署名を変えず「loader を明示的に呼んだ側だけ」とする (`s2-plan.md:228-234`) うえ、最終 CLI/caller が scope にないと認める (`:314`)。submitter も preregistration を読まず、現在の HEAD と job body hashだけを qsub へ渡す (`tools/pegasus/submit_t1998_balanced_stock_inline.sh:82-92,172-180`)。したがって結果を見た後に artifact から repository/gitlink/env/source 値を写して object を作る経路が残る。  
**影響:** canonical 文書を通さない post-hoc identity でも consumer が受理でき、prospective 束縛を成果物から証明できない。

6. **重大度: should-fix** — 文書で固定するとする field の相当数は consumer の意味的比較へ届かない。特に `env_tag`、`job_body_path`、arm 順序、推定規則は既存 dataclass に格納されず、whole-document SHA 以外には影響しない (`s2-plan.md:63-89,147-158`; `t1998_stock_inline_pair.py:131-181`)。workload、sample 数、ratio 等は consumer の独立した module 定数・計算が効いているだけで、文書値を期待値として比較していない。  
**影響:** 文書値と実装定数が食い違っても、文書 SHA 定数を同時更新すれば artifact の受理集合・算出値は変わらず、事前登録 field は保証として恒真化する。

7. **重大度: nit** — loader の変異テストに帰属不能なものがある。`test_load_preregistration_rejects_worktree_blob_drift` は blob 比較を削っても後段の whole-file SHA が同じ drift を拒否する (`s2-plan.md:121-123,281-285`)。`nonancestor` は非祖先 commit に同一文書 blob を持たせない限り blob 取得が先に赤になる。`current_document_sha_drift` も worktree と選択 commit の blob を一致させない限り blob gate が先に赤になる。また ancestor 正例は、文書と同じ値を module に手書きして返す変異を観測できない (`:275-285`)。  
**影響:** artifact の値は変わらないが、blob/ancestry/hash 各 gate の変異証拠が実際より強く報告される。

8. **重大度: nit** — plan の job body digest literal 2 箇所は壊れている (`s2-plan.md:74,100`)。直後の訂正 (`:92-94,107-109`) と値の正本 (`AUTHORITATIVE-VALUES.md:3-18`) は正しい。  
**影響:** 壊れた方を実装へ転記すると正例が拒否されるが、正本どおりなら成果物への影響はない。

既存拒否の削除・緩和そのものは plan に見つからない。fixture literal の交換、loader 追加、job body scalar pin は受理集合を狭める差分である。問題は、新しい束縛が一意・不可避になっていない点にある。

prospective 性について、exact pair 自体は 2026-08-28 時点で no-backoff / fixed-5 と確定しており (`docs/handoff/2026-08-28-t1998-balanced-stock-inline-precheck.md:57-64`)、2026-09-07 生値から選んだ証拠はない。job body/gitlink/env digest に outcome からの逆算も観測しなかった。破れは上記の caller-controlled identity と複数 commit 受理である。

## 親 brief の誤り

- target source digest は formal producer と異なる source 状態から取得されている。`tracked_clean=true` を formal patch-applied target へ一般化したのが最大の誤り。
- 「同じ GNU 11.4.0」から compute digest の一致は証明できない。brief 自身も header closure 未証明と認めるが (`s1-brief.md:60-67`)、問題は header だけでなく compiler/preprocessor identity である。
- P1-3 の ancestry/blob 方式は F36 を避けるが、期待 repository commit を一値に固定しない (`s1-brief.md:93-96`)。
- P1-4 は D1790 の preregistration sha を job body sha に読み替えている (`s1-brief.md:97-99`)。
- 「artifacts に生の JSON」は provenance 全体の所在として不正確。source JSON、environment JSON、repo の job body bytes、Git tree に分散している (`s1-brief.md:47-58`)。
- A-5 は未充足のまま、旧 digest の live preregistration は存在しない、exact pair は生値取得前に既知、という訂正には誤りを見つけなかった。

## 恒真・冗長と判定したもの

事前登録 field と発火先の対応は次のとおり。

| field | consumer の発火先 |
|---|---|
| `schema_version` | proposed loader の文書 parse のみ。artifact rejection code なし |
| `repository_commit_binding` | proposed loader の文書 parse のみ。artifact rejection code なし |
| `repository_commit` | `repository-identity-mismatch` (`t1998_stock_inline_pair.py:823-851`)。ただし期待値は caller 注入 |
| `env_tag` | 固定値 `pegasus` との比較なし。WAL 内部の相互一致だけ (`:499-504`) |
| `ccbench_gitlink_commit` | `gitlink-identity-mismatch` (`:832-860,894-901`) |
| `environment_contract_sha256` | `environment-identity-mismatch` (`:507-513,903-908`) |
| `job_body_path` | 発火なし |
| `launcher_script_sha256` | `launcher-script-identity-mismatch` (`:915-919`)。plan の scalar pin も同 code 想定 |
| baseline/target `canonical_genome` | `preregistered-pair-mismatch` (`:468-474`) |
| baseline/target `source_bytes_sha256` | `source-identity-unbound` (`:521-533`) |
| `workload` | `result-contract-mismatch` だが、文書値でなく module 定数との比較 (`:728-737`) |
| `target_fixed_us` | 同上 |
| `producer_point_count` | `pair-cardinality` だが、module 定数との比較 (`:945-949`) |
| `samples_per_arm` | `pair-value-mismatch` だが、module 定数との比較 (`:598-607`) |
| arm 順序 | 発火なし。record を genome で分類する |
| median 規則 | `pair-value-mismatch` (`:598-615,637-645`)。文書値は未使用 |
| `ratio` / `improvement_percent` | `pair-value-mismatch` (`:1061-1075`)。文書式は未使用 |
| unstable 規則 | rejection なし。`inconclusive` への分岐 (`:1095-1104`) |
| off-grid 規則 | 文書値による発火なし。pair 外を推定量へ入れない処理はコード固定 |

既存 consumer の単独発火不能な冗長 gate は、`_one_record` の receipt cardinality (`:444-453`)、COMMIT environment digest (`:505-513`)、receipt id (`:681-688`)、admitted view と同じ bytes の lock/WAL SHA (`:790-799`)、WAL gitlink (`:879-901`)、全体/arm cardinality (`:942-959`)、abort・stage 欠損 (`:1008-1023`)。既存 insight も同じ一覧を変異証拠から除外している (`output/insights/2026-09-08_t1998-stock-inline-parts/README.md:98-104`)。

plan の新テストでは、worktree blob drift は whole-file SHA と重複して単独変異を殺さない。nonancestor と current-document-SHA drift は、同一 blob/bytes を保つ fixture でなければ ancestry/hash の単独証拠にならない。ancestor 正例の「module 手書き値を殺す」という主張も、手書き値が文書と同じなら成立しない。

## 裁定パッケージ候補

- **D1790 と producer schema scope の衝突:** 現成果物には測定時点 preregistration sha がない。scope 外の producer schema/job body/launcher を変更するか、D1790 の逐語を変更するかの裁定が必要。job body sha への黙示的読み替えでは閉じない。
- **正式経路への loader 不可避化:** production caller/CLI と submitter は今回 scope 外だが、ここを閉じない限り canonical preregistration を通った正式分析経路が存在しない。どの entry point を正式経路とするか裁定対象。
- **一意な measurement commit と F36 の両立:** ancestry + 同一 blob では複数 commit を受理する。文書自身の commit を埋めずに、どの既存 commit を測定対象の一値とするか、着地順序を含めて裁定が要る。

## 総括

target source digest は formal patch-applied source の値ではなく、このままでは正式 artifact が拒否される。  
login の同名 `g++` から compute digest の一致も導けない。  
D1790 の成果物側 preregistration sha は job body sha に置換され、producer schema に存在しない。  
`repository_commit` は一値でなく同一文書 blob を持つ祖先集合を受理する。  
loader は任意呼出しで、直接構築 identity による post-hoc 受理経路が残る。  
既存拒否を緩める差分はないが、事前登録の新しい束縛は全層で成立していない。