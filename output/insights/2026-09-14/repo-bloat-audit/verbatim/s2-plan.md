## 総括

削除条件をすべて満たすと確定した対象は **0 件・0 bytes**。削除・編集・commit・テスト実行はしていない。  
同値な assertion のテストを **1 組**、外部から basename が言及されない docs を **2 件・18,327 bytes**確認したが、削除条件は閉じていない。  
**P1-a は保留**。調べた記録には証拠価値があるが、output 全体について「概ね偽」とする網羅的根拠は得ていない。  
**P1-b の「概ね真」は支持しない**。行数増加と不要性は別であり、同一本体でも入力が異なる例を確認した。  
**P1-c は親の実測を採用**。**P1-d とは整合する**が、削除可能数の上限を証明した結果ではない。

以下の repo 内相対パスはすべて `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-repo-bloat-cleanup/` 配下。参照数は、特記しない限り tracked 内容の固定文字列検索による一致行数である。

## A. テスト削除候補

**採用候補なし。** 調査した拾い上げ例と除外理由を示す。

### A1 死んだ pin

| nodeid / file:line | 現物で確認した事実 | 判定 |
|---|---|---|
| `orchestrator/tests/test_related_work_search.py::test_tier_enforcement_remains_outside_registration_executor_scope` — 同 file:1581 | assertion は `not hasattr(search, "validate_tier_analysis")`。symbol 文字列の repo 内出現は、この assertion と同 file:1979 の 2 行だけ | **単独削除候補から外した。** API の再導入で赤になるので、不在を検査していること自体は inert の証明にならない。重複関係は A2 |
| `orchestrator/tests/test_codex_role_runtime.py::test_runtime_commit_prerequisites_are_available` — 同 file:710 | :719–728 は前提物の有無と `IZANAGI_REQUIRE_CODEX_RUNTIME` により return／fail／skip を分岐 | **外した。** 常時 skip ではない。`docs/decisions.md:2330` の D60 が opt-in 発火を規定し、:2340 が単純削除を明示的に却下。受入番人でもある |

A1 として削除可能と確定した件数は 0。環境不足による skip を死んだ pin と数えていない。

### A2 完全重複

| nodeid / file:line | 同値性の根拠 | 判定 |
|---|---|---|
| `orchestrator/tests/test_related_work_search.py::test_postprocessing_tier_api_remains_outside_executor_scope` — 同 file:1978 ↔ `orchestrator/tests/test_related_work_search.py::test_tier_enforcement_remains_outside_registration_executor_scope` — 同 file:1581 | 両方とも引数・decorator なし。同じ :19 の import を使い、本体は同じ `assert not hasattr(search, "validate_tier_analysis")` だけ。検査述語を P とすれば P∧P=P。後者を残せば API 再導入の検出は残る | **本体の同値性は確認、削除採用は保留。** 両 nodeid にそれぞれ 14 一致行があり、brief の参照ゼロ条件を満たさない。これらがすべて非拘束の履歴参照であることまでは閉じていない |
| `orchestrator/tests/test_buildcache_v2.py::test_masstree_source_root_nonempty_empty_like_source_does_not_fallback[space]` — 同 file:691 ↔ `orchestrator/tests/test_buildcache_v2.py::test_masstree_source_root_nonempty_invalid_source_does_not_fallback[relative]` — 同 file:1026 | 本体 AST は一致するが、:686–689 は空白・tab・quoted-empty、:1021–1024 は相対 path・NUL を入力する | **外した。入力が違う。** 片方の削除で対応する不正入力の被覆を失う |

最初の組の参照先は次のとおり。

- `orchestrator/tests/acceptance_duration_ledger.json:2602`、`:2646`
- 各テスト定義
- `output/insights/2026-09-02/t1881-axis3-mutation/` の `mutprobe-ledger.json`、`mutreal-ledger.json`、`mutreal2-ledger.json`
- `output/insights/2026-09-10/t2028-axis3-live-preflight/mutation/` の `mutation-ledger-final-tip.json`、`mutation-ledger.json`、`probe-ledger.json`

**履歴への名前の出現を、現役 pin と断定したわけではない。** 参照ゼロという今回の条件と、pin 閉包の未確認を区別して保留した。

件数について、docstring を除いた関数本体 AST の一致は 23 群を抽出した。ただし decorator・入力・import 先を無視した拾い上げ数であり、完全重複数ではない。現物で同値と確認したのは上記 1 組。

### A3 恒真

| nodeid / file:line | 調べた根拠 | 判定 |
|---|---|---|
| `orchestrator/tests/test_guided.py::test_online_digest_leakage_assert` — 同 file:90 | `docs/decisions.md:528` の D26 は、実 caller 経路の述語が集合包含により恒真と説明している | **外した。テスト自体は恒真ではない。** 同 file:155–162 は committed 2 件に `iterations=1` を渡して例外を要求し、2 の場合も検査する。例外を出さない変異なら :158 で赤になる。D26 :538–539 も配線 sanity として温存を指定 |

AST を解析できた範囲で、テスト関数内の literal `assert True` は検出しなかった。検索で現れた `assert True` 文字列には、別テスト用に生成する fixture コードが含まれる。一般的な恒真式の全数判定はしていない。

### A4 撤回済み機構

削除可能と確定したものは 0。

D60 の休眠機構は撤回ではなく、再開時の検査を残す決定だった。D26 も独立防壁という説明を撤回した一方、sanity の温存を明記している。いずれも A4 から外した。

anomaly・serializability・verifier・freeze・provenance・受入 gate のテストは削除候補に採用していない。

## B. 記録削除候補

**採用候補なし。** path 参照ゼロまで確認できた調査対象も、次の理由で採らない。

| 型 / path | bytes | 完全 path 参照数 | 検索した key と結果 | 判定 |
|---|---:|---:|---|---|
| B1/B3 `output/env/pegasus/debug/debug_early.sh` | 604 | 0 | `debug_early` は 1 行。`output/env/pegasus/debug/debug_early.sh.e867864:4` が実行 request 名を記録 | **保留。** :6–18 は実行ログを生成する script。外部台帳による「使い捨て・撤回済み」の裏付けを取得できていない |
| B2 `output/env/pegasus/calibration/job-staging/0:867863.nqsv/hostname-f.stdout` | 9 | 0 | `0:867863.nqsv` は 19 行・6 files。`hostname-f.stdout` は 8 行・7 files | **外した。** 実機観測記録であり、証拠価値ゼロではない |
| B2 `output/env/pegasus/calibration/job-staging/0:867863.nqsv/hostname.stdout` | 9 | 0 | 同じ job ID の検索で台帳と観測記録へ到達 | **外した。** 上と同じ実測 job の記録。両 path が無拘束であることも未証明 |

hostname の組は両方とも本文が `bnode003\n`、git blob が `403068fdd844c220638e072e6c65f0cf133da2a8` で一致する。

key 検索の主要な到達先は次のとおり。

- `docs/decisions.md:17844`：D430 がこの calibration/job-staging 族を、実機 `PBS_JOBID` の根拠として扱う。
- `docs/archive/worklog-phase3-0816-572.md:9`：同じ実機 ID の記録。
- 当該 job の `allocation-unavailable.json:4`、`failure.json:3`
- `output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measure/phase-20260904-223623-rep1.jsonl` と `phase-20260904-223914-rep2.jsonl`
- `hostname-f.stdout` は別 job の `final-receipt.json:299`、bundle manifest、`tools/pegasus/certify_calibration.sh:258` 等にも現れる。ただし、**別 job の receipt をこの 2 files の pin と取り違えていない。**

この組は「job-staging 内にも同一 blob がある」という事実を示す。親の「他所に同一 blob ゼロ」が **job-staging 外との比較**を意味するなら、その主張への反証ではない。

`debug` 族全体の一括削除も不可。`output/insights/2026-08-03_t293-perf-site/brief.md:24` と `s6-review-B.md:92` は旧 perf 記録を証拠として参照している。

## C. docs 候補

### handoff

README 以外の tracked file は次の 1 件、8,424 bytes。

`docs/handoff/2026-08-28-t1998-balanced-stock-inline-precheck.md`

- :3 は「中断」。
- `docs/archive/worklog-phase3-0908-1333.md:12–18` は、その「未完の作業」が裁定前の古い記述であると明示している。
- 一方、`output/insights/2026-09-08_t1998-stock-inline-parts/README.md:9` は段 4 裁定を参照し、`output/insights/2026-09-10_t2533-t1998-prereg-digest/verbatim/s3-consult-lensA.md:46` も exact pair の根拠として参照する。
- basename 検索は 5 行、完全 repo 相対 path は 4 行。

**現役の作業状態としては陳腐化しているが、参照先としては生きている。単純削除から外した。**

なお `output/insights/2026-08-29/rescue-unlanded-fragments/README.md:72–85` の「破棄」は追加内容を持つ別 worktree 版の話であり、:85 は main の precheck 版を変更しなかったと明記する。現存版の削除済み証明には使えない。

### spool

tracked file は以下の 5 件だけ。

- `docs/spool/FOLDED.md`
- `docs/spool/README.md`
- `docs/spool/decisions/README.md`
- `docs/spool/failures/README.md`
- `docs/spool/worklog/README.md`

**fold 済み fragment の残骸は 0 件。**

`FOLDED.md` は 1,149,738 bytes。`tools/spool_fold.py:35` が receipt path を束縛し、`:1204–1209` が必須入力として扱い、`:1703` 以降が内容を検査する。単なるログではないため削除から外した。

### archive

1,206 件のうち、README 以外の **1,205 件すべて**について、basename が `docs/archive/README.md` に掲載されていることを確認した。

- worklog 族は 1,200 件。`tools/spool_fold.py:1431–1445` が `worklog-*.md` を glob で読み、base-digest 用入力にする。
- `tools/check_docs.py:6810–6824` は索引と実在物を双方向に検査する。
- 残る監査・phase 資料も索引参照があり、参照ゼロ条件を満たさない。

**個別 path の検索結果によらず、worklog 族には実行コードの consumer がある。**

### 孤児 Markdown

tracked テキストから Markdown basename を抽出し、対象自身以外の file に出現しない `docs/**/*.md` は次の 2 件だった。

| path | bytes | 外部 basename 言及 | key 検索で確認した関係 |
|---|---:|---:|---|
| `docs/related-work/notes/note_decentmem_decentralized_memory_for_mas.md` | 9,077 | 0 | `2605.22721`。`docs/archive/worklog-phase3-0827-1027.md:34` が分類結果を記録し、`docs/related-work/claim-survey/2026-08-27-axis1-adjudication-3.md:311` が同論文の根拠を扱う |
| `docs/related-work/notes/note_memevolve_meta_evolution_of_agent_memory.md` | 9,250 | 0 | `2512.18746`。同 worklog:31 に分類結果。同 adjudication:544 は「ノート」の引用訂正を記録する |

両論文は `docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md:536–537` の登録前に読んだ資料にも含まれる。

**文字列上の孤児は実在する。しかし研究記録としての関係があり、内容の完全重複・証拠価値ゼロは証明していないため削除は保留。** key の一致だけで、この note path の hash pin が存在すると断定してもいない。

## D. 実行手順

今回の確定計画は次のとおり。

- **削除 path の完全列挙：空集合**
- **削除する test nodeid：空集合**
- **同じ commit で修正する consumer：なし**
- **削除後の焦点走 nodeid：空集合**
- 編集・削除 commit は作らない。

A2 の保留案件を親が継続調査する場合、変更境界は明確である。

| 項目 | 対象 |
|---|---|
| 重複部分 | `orchestrator/tests/test_related_work_search.py:1978–1979`。関数定義と本体で 124 bytes |
| 残す同値検査 | 同 file:1581–1582 |
| 参照整理を判断する箇所 | `orchestrator/tests/acceptance_duration_ledger.json:2602`、上記の過去変異試験記録 |
| 参照関係から直接引ける焦点走 | `orchestrator/tests/test_related_work_search.py::test_tier_enforcement_remains_outside_registration_executor_scope` |

これは**削除採用済みの手順ではない**。とくに所要台帳の残存行を「削除すると必ず赤になる consumer」とは確認していない。`orchestrator/tests/conftest.py:1502–1539` の台帳 validator は台帳内部の件数整合を確認するため、行だけを消す操作も無条件には提案しない。

## E. 削れないと確定した集合と理由

今回の条件で削除から外せると確定した範囲は次のとおり。

| 集合 | 理由 |
|---|---|
| archive の worklog 1,200 件 | fold の glob 入力。参照ゼロ・成果物不変条件を満たさない |
| `docs/spool/FOLDED.md` | 必須 receipt 入力であり、replay 検査用の耐久記録 |
| 残存 handoff 1 件の単純削除 | 後続資料が段 4 裁定を参照している |
| calibration の hostname 2 files | 同一 bytes でも実機観測の記録。D430 の根拠となる記録族に属する |
| A1 の runtime 番人 | D60 が削除を却下し、opt-in 発火を維持 |
| A2 の buildcache 例 | 本体一致でも入力集合が異なる |
| A3 の guided 例 | D26 の恒真性は実 caller の性質。テスト自身は不整合入力を与え、sanity の消失を検出する |

**output 全体、全 test、全孤児 docs を「削れないと確定」とはしていない。**

## F. 読めなかった file / 確かめられなかったこと

射影された必読 2 files は両方読めた。

調査中に指定して不在だった repo 内 path：

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-repo-bloat-cleanup/tools/pytest_duration_shard.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-repo-bloat-cleanup/docs/related-work/catalog.yml`

未確認事項：

- output 全件についての `FROZEN_MANIFEST`、generator source hash、key→canonical path、role／xdist group pin の完全閉包。
- A2 の同値テストを削除した際の、全 collection hook・履歴記録 consumer への影響。
- 孤児 note 2 件と adjudication 本文の、全内容の包含・重複関係。
- 全テストの意味論的な重複・恒真性。AST 一致の拾い上げはその証明ではない。
- pytest、変異試験、docs checker の実行結果。**今回は静的調査のみで、緑の報告はない。**