### F324 の「違反件数と母集合」が出力 schema に存在しない

severity: blocker  
判定: real  
根拠: F324 は「満たさない件数」を必須とし、ゼロなら母集合の併記を要求する [docs/failures.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/failures.md:9541)。しかし plan が構造化するのは path 数、Python 数、parse 数、非 Python 数、除外数であり、契約適合・違反・未判定の各件数や入力欄はない [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:114)。renderer の欠落防止も canonical path にしか掛からず、変更識別子、call 候補、違反判定の欠落を殺す negative control がない [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:118)。  
成果物影響: author が母集合も違反件数も書かずに「静的 call 候補なし」で監査を閉じ、F324 型の契約違反が certified 選択コードへ入る。

### `complete=true` と意味的 call 不完全が両立し、動的 Python を探索不要と誤読できる

severity: major  
判定: real  
根拠: plan は `semantic_calls_complete=false` を固定する一方、parse と手動面が閉じれば rc=0 の「完全な射影」とし、一般名の `complete` が真なら「他にない」を生成可能にする [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:57)、[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:114)、[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:124)。推測を含む過小報告条件は、代入 alias、`getattr`、`globals`、動的 import、文字列組立 dispatch、decorator registry、factory 経由の `__init__`・`__call__`、pytest fixture 引数・`usefixtures`・hook 名解決、method・nested function、同名 overload、merge 結果だけで新設された識別子である。import alias、末尾名候補、非 call 参照の出力は一部を可視化するが閉包にはならない。F481 の pytest hook は実例で、hook は名前規約で pytest から呼ばれる [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/orchestrator/tests/conftest.py:1704)。  
成果物影響: 静的 call 数ゼロが動的 consumer ゼロに読み替えられ、F481 型の stale 検査無効化が監査レポートから落ちる。

### Markdown 生成コードと submodule 内部差分は必須手動監査へ閉じていない

severity: major  
判定: real  
根拠: C/C++、shell、JSON、CMake、patch/diff は `manual_review_required` と rc=1 にするが、YAML など他の非 Python 実装面は明記されず、Markdown/RST は `classifier_excluded_changed_paths` に載せるだけで手動監査へ昇格しない [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:108)。正規分類器は `.github/`、`.codex/`、`external/` 配下の Markdown/RST 以外を広く実装面とする [check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/tools/check_ai_provenance.py:67)。また `external/ccbench` は実物では mode 160000、OID `511c9538e4e8efa54b45cda62e72389ed3b706ec` の gitlinkであり、superproject の tree 走査は内部の C++・script・生成設定を列挙しない。plan には旧新 OID、submodule 内 diff 母集合、取得不能時の fail-closed 条件がない。実物定義は [.gitmodules](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/.gitmodules:1)。  
成果物影響: 生成コードを含む文書、workflow YAML、または ccbench pin 内の変更が除外 path・gitlink 1 行へ畳まれ、監査子が実装差を読まずに受理しうる。

### F324 の探索上界は repo 全 Python であり `_message_file_paths` 上界化の懸念は反証される

severity: nit  
判定: refuted  
根拠: call 母集合は結果 snapshot の全実装面 `.py` blobで、`canonical_preflight_paths` ではない [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:91)。F324 の実入力は base `22c13a04…`、wave `49e22d2b…`、main `330f67d0…`、merge `5ed5a106…`。wave 側の top-level `require_admitted_campaign` 契約変更が識別子母集合へ入り、全 snapshot 走査は非競合 test 2 file の call を候補化する。実物監査が修正した箇所は [merge-audit.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/output/insights/2026-08-15_t817-verifier-epoch/verbatim/merge-audit.md:16)。F481 も両親が変更した `conftest.py` 自体は side-overlap に入るが、pytest の動的呼出しは前所見の限界に残る。  
成果物影響: F324 型の path 上界による欠落は生じないが、意味解決と報告強制の欠落は残る。

### F324 実物を使う回帰がなく、上界を再び狭めても計画中のテストが通りうる

severity: major  
判定: real  
根拠: 実 repo 回帰に選ばれたのは t1726 の重複 path 1 本だけで、F324 の識別子抽出、非重複 2 test file、65 call 集計を期待値に固定しない [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:153)。一般名の `test_changed_identifier_calls_scan_the_whole_python_population` はあるが、historical F324 の module re-export、terminal-name 候補、非重複 path を同時には固定しない [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:146)。  
成果物影響: 実装者が call scan を canonical path 集合へ狭める退行を入れても回帰が緑になり、F324 の 2 call がレポートから消える。

### D697・D554・D770 の異なる集合を運用文の 1 語へ畳んでいる

severity: blocker  
判定: real  
根拠: D697 決定 8 は「両親が同じ実装面 file を変更」で合成監査、D554 は postclaim merge の「結果が両親双方と食い違う実装面 path」で Codex author 昇格、D770 は combined diff 非空時だけ 2 commit 分割であり、集合が異なる [D697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/decisions.md:27509)、[D554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/decisions.md:22590)、[D770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/decisions.md:29736)。plan 内部は `side_overlap_implementation_paths` と `canonical_preflight_paths` を分けるが、DW-O17 の置換文は「実装面path差」としか書かず、どの集合が監査・author・分割を発火させるか消している [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-merge-audit-necessity/s2-plan.md:187)。D894 は checker と provenance 文書を変更しない限り受理集合変更なしで、この点の懸念は refuted。  
成果物影響: canonical 集合を D697 の発火条件に使えば F481 型監査が減り、side-overlap を D554・D770 に使えば不要な author 要求と 2 commit 分割が増える。

### 8 件すべてを合成監査固有の検出と数える根拠はない

severity: major  
判定: real  
根拠: 0817-621 は Git が実際に競合を出しており、合成監査は解消内容の assert union を確認したもので、無監査なら無音通過する型ではない [worklog-phase3-0817-621.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/archive/worklog-phase3-0817-621.md:21)。0818-656 は F393 の既存凍結不変テストが組み直し前に 2 件赤を出したため、evidence の「テスト緑」と矛盾する [docs/failures.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/failures.md:11273)。0823-859 も既存 collection 検査が `UsageError` を出す型で、監査が先に見つけたものの次の関連走行では赤になる [worklog-phase3-0823-859.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/archive/worklog-phase3-0823-859.md:109)。したがって監査固有の下界は 8 ではなく最大 5 件だが、F481 は受入全走でも緑なので撤廃を支持しない。  
成果物影響: 必要性レポートの「固有検出率 5 割超」は最大 5/13〜15 へ下がるが、監査維持という選択自体は変わらない。

### 既存 streaming scan の未登録運用は新 tool の分類義務を免除しない

severity: nit  
判定: refuted  
根拠: 既存 scan の約 60 MB 実測は負荷懸念を弱めるが、`tools/README.md` は新規 script 追加時の再分類を明示的に要求する [tools/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/tools/README.md:22)。未登録 script が machine gate の外で緑になる事実は、prompt 規律を撤回する根拠ではない [tools/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/tools/README.md:31)。  
成果物影響: certified 選択・台帳値は変わらず、分類完了まで tool の実行可能性だけが未確定である。

## 総括

blocker は 2 件あります。最大の懸念は、F324 が要求する「違反件数と母集合」を schema と renderer が強制せず、同時に D697・D554・D770 の別々の path 集合を運用文で曖昧化していることです。

F324 の実入力自体は repo-wide Python 上界により拾えます。しかし、その事実を固定する実物回帰、動的 Python の未解決欄、全非 Python 面の必須手動監査、submodule 内部差分が揃うまでは、検出力を保全した高速化とは判定できません。静的検査のみで、テストは実行していません。