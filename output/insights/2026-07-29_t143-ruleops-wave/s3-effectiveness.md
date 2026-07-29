## 前提検証

指定8ファイルはすべて可読で、全文を確認した。編集・commit・pytest・`tools/run_tests.py`・checker は実行していない。したがってテスト緑は存在しない。

read-only Git 集計では、HEAD は `eaa2dd2ae806983e186672c94faa738992c77ce4`、SHA-1、non-shallow、replace ref / grafts なしだった。

- test: 97 files / 2,726,974 bytes
- insight: 251 files / 7,860,617 bytes

件数は親 brief と一致するが、byte は不一致。plan の再集計値は正しい。[parent-brief.md:22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:22) [s2-plan.md:8](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:8)

## findings

### B-1 — BLOCKER — committed ledger が自己参照で固定点を持たない

根拠: tracked ledger 自身が候補の `path`、`semantic_queries`、`reviewed_hits` を保持する。[s2-plan.md:51](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:51) [s2-plan.md:62](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:62) 一方、test は HEAD/current history を再検索し、insight は target 以外の全 HEAD blob にある path/basename を拒否する。[s2-plan.md:85](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:85) [s2-plan.md:86](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:86)

ledger を commit すると、insight は ledger 内の自分の path を inbound reference として検出する。test query も ledger 自身を current/history hit に追加し、その commit ID を事前登録できない。ledger 更新がさらに新しい history hit を作る。

放置時の成果物影響: 非空 ledger は未commit時だけ通り、commit後に赤くなるか、更新を繰り返す自己参照状態になる。決定的・再検証可能な候補台帳にならない。

最小修正: current/history/reference scan から、exact な control artifact（ledger 自身と当該候補の typed receipt）を除外する。その除外集合を literal pin し、「候補追加をcommitした後も同じ package が通る」「通常 blob の参照は拒否する」の両 positive control を追加する。

### B-2 — BLOCKER — typed mutation receipt が実験証拠ではなく自己申告 JSON

根拠: receipt は将来 `output/insights/` に作り、`candidate_excluded=true`、rc、`KILLED`、failed node を検査するとだけ定義される。[s2-plan.md:77](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:77) CLI は生成・再実験機能を持たず、`inventory / inspect / check` のみである。[s2-plan.md:89](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:89) 元要件は、省略が受理集合を変えないことを機械的に示すよう求めている。[external-consultation-scope-and-axes.md:162](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-27_external-consultation-scope-and-axes.md:162)

HEAD には候補 test が存在する一方、receipt は「候補除外済み」と主張する。その除外状態の tree、pytest argv、収集集合、mutant bytes のどれにも束縛されていないため、手書きまたは別実験の receipt が構造検査を通せる。

放置時の成果物影響: `check` が受理集合不変の証拠を検査したように見えるが、実際には申告 field の整合しか検査しない。

最小修正: receipt を `base_head`、実験 tree OID、候補 preimage、mutant patch digest、exact argv、collected-node digest、各 node の outcome、復元後 tree に束縛する producer 契約を追加する。それを scope に入れないなら、v1 の成功意味を「receipt の構造整合のみ」へ縮め、test retirement の機械証拠を実装済みと主張しない。

### B-3 — BLOCKER — `derived-report` を候補側が自己申告し、凍結 snapshot を区別できない

根拠: `artifact_class: "derived-report"` は候補 ledger 内だけにある。[s2-plan.md:72](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:72) しかし `output/insights/` は、プロセス監査・ユーザー裁定用の凍結 snapshot も収容し、それらもまさに `authority: none / default_effect: no-state-change` を持つ。[output/README.md:71](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/README.md:71) 実例も自ら「逐語凍結」と宣言し、同じ marker を持つ。[t139-ladder-verbatim/README.md:1](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t139-ladder-verbatim/README.md:1) [t139-ladder-verbatim/README.md:3](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t139-ladder-verbatim/README.md:3)

放置時の成果物影響: 凍結逐語、裁定資料、mutation evidence を候補作成者が `derived-report` と誤分類でき、親 brief の freeze 対象外境界を機械的に守れない。[parent-brief.md:7](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:7)

最小修正: v1 retirement は作成時から target 内部に型を持つ新規 `derived-report` schema だけに限定する。既存の untyped / verbatim / audit / ruling / mutation / receipt artifact は全て inventory-only とし、後付けの候補自己申告で型を昇格させない。

### B-4 — MUST — 空 ledger + standalone check は回収機構として空虚

根拠: 初期 ledger は空である。[s2-plan.md:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:35) RuleOps は runner、checker、hook に結線せず、明示実行だけにする。[s2-plan.md:113](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:113) 現行 runner は `git ls-files --deleted` による未stage削除しか検査せず、stage を促した後は当該 gate が消える。[run_tests.py:453](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:453) [run_tests.py:500](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:500)

放置時の成果物影響: 今 wave 後も通常 workflow の挙動は変わらず、候補作成も回収もゼロ。コード・docs・テストの保守面だけ増える。将来の staged deletion と RuleOps package の対応も検査されない。

最小修正: 削除なしでも、`inspect` から決定的な候補 skeleton を出す導線、production ledger の schema canary、1件の実候補を使う end-to-end dry-run を受入へ入れる。それを行わない場合、成果物名を「RuleOps inventory prototype」に縮める。

### B-5 — MUST — schema・CLI・exit code が author の裁量に残りすぎる

根拠: inventory と候補 schema は field 名のみで、型、enum、順序、サイズ上限、nested exact keys がない。[s2-plan.md:45](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:45) [s2-plan.md:62](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:62) それでも oversize、unknown field、duplicate key をテストするとしており、閾値や正確な外延が未定義である。[s2-plan.md:122](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:122) CLI も default path の基準、stdout/stderr、error JSON、exit code が未定義。[s2-plan.md:89](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:89)

放置時の成果物影響: author が schema と error contract を実装中に発明する。`--repo` 使用時の ledger/inspect path、Git failure と候補不適合、argparse error を automation が区別できない。byte-identical テストも serializer・timestamp・hit順を固定できない。

最小修正: plan v2 に全 nested object の exact key/type/enum/上限、SHA-1/SHA-256規則、timestamp source、sort/JSON encoding、相対path基準、rc表、stdout/stderr契約、traceback禁止境界を書く。

### B-6 — MUST — semantic/history gate が「弱くも死にもなる」

根拠: query は候補作成者が指定する意味語で、完全性の独立 oracle がない。[s2-plan.md:68](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:68) `git log -S` を「履歴 hit の完全列挙」と扱うが、`-S` が返すのは occurrence count が変化した commit であり、全過去 blob の全 occurrence や runtime 発火ではない。[s2-plan.md:31](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:31)

また「発火実績ありは拒否」は、dev-wave L2 節だけの D94 条件を tracked test 全般へ一般化している。[decisions.md:4216](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/decisions.md:4216) 歴史上一度発火したが現在は代替済み、という RuleOps の本命まで永久拒否する。

放置時の成果物影響: 狭い query なら見逃して偽緑、妥当な query なら歴史記録により永久赤になる。自然言語分類を機械証拠と誤認する。

最小修正: `git log -S` の出力を `pickaxe_events` と呼び、runtime firing と分離する。必須 query の導出元を固定し、未レビュー hit だけを自動拒否する。実発火済みは typed supersession evidence とユーザー裁定へ送り、一般的な永久拒否にしない。

### B-7 — MUST — Git history 証明に replace/grafts 防護が欠ける

根拠: plan は shallow repository の拒否だけを明記する。[s2-plan.md:85](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:85) 既存の H-pure 実装は `core.useReplaceRefs=false` を全 Git 呼出しへ付け、replace refs と grafts の存在自体も拒否する。[s8b_ratified_freeze.py:282](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/campaign/s8b_ratified_freeze.py:282) [s8b_ratified_freeze.py:320](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/campaign/s8b_ratified_freeze.py:320)

放置時の成果物影響: root `head` は元 commit OIDのまま、inventory tree・last change・`-S` 履歴だけが local replace/graft で差し替わり得る。`--repo` で任意 repo を扱う CLI の決定性と履歴証拠が崩れる。

最小修正: read-only subcommand allowlist、Git env scrub、`--no-optional-locks` に加え、`core.useReplaceRefs=false`、replace/grafts拒否、timeout、bytes出力のUTF-8境界を file:line planへ明記する。

### B-8 — MUST — AST node 実在は pytest collection・実効性を証明しない

根拠: replacement node は `{nodeid, blob}` とし、AST で実在確認するとだけ定義される。[s2-plan.md:67](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:67) [s2-plan.md:85](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:85) pytest の nodeid は class、parametrize、dynamic collection、skip、`__test__` 等を含み、AST declaration の存在と収集・非skip実行は同値でない。

放置時の成果物影響: dead/skipped replacement を受理するか、動的だが有効な node を過剰拒否する。AST resolver の保守面も無制限に広がる。

最小修正: AST は module-level function / class method の限定 preflight と明記する。receipt 側で exact nodeid の collection、非skip、mutant時の失敗を束縛し、未対応 node shape は明示 reason code で拒否する。

### B-9 — MUST — basename closure が nested insight を過剰拒否する

根拠: target の full path または basename が他 blob にあれば拒否する。[s2-plan.md:86](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:86) 一方、nested insight は明示的な対象である。[s2-plan.md:119](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:119) 実在候補には `README.md` があり、repo 内の無関係な `README.md` 言及が多数ある。[t139-ladder-verbatim/README.md:1](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t139-ladder-verbatim/README.md:1) [docs/README.md:37](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/README.md:37) 静的 `git grep` ではこの basename に他 blob 135件が hit した。

放置時の成果物影響: `README.md`、`result.json` 等の一般 basename を持つ nested report は、実際の参照閉包と無関係に永久不適格になる。

最小修正: repo-relative full path と解決済み相対 Markdown link を主検査にする。basename は repo 全体で一意な場合だけ補助 signal とし、非一意 basename 単独を拒否根拠にしない。

### B-10 — SHOULD — 件数・bytes と「二族」は制度一般化の根拠にならない

根拠: 親の実測は件数とbytesだけである。[parent-brief.md:20](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:20) tests と insights は必要証拠が別物で、insight 内部も5形式、mutation ledger も複数schemaである。[s2-plan.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:15) [s2-plan.md:20](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:20) DW-G03 は同型欠陥が異なる producer/consumer で独立再現した場合の制度一般化を要求する。[core.md:55](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/dev-wave/core.md:55)

放置時の成果物影響: test runtime と insight 発見性という異なる問題を、一つの大型 CLI/schema に早期統合し、回収実績ゼロのまま保守費だけ固定化する。

最小修正: 共通化の主張を HEAD inventory/Git primitive に限定し、retirement validator は二つの provisional adapter と記録する。削除なしの実候補 dry-run を各族1件得るまで、族一般化・ROI・研究的有効性を主張しない。

## positive controls

- **PC-1:** P3 の動的 HEAD inventory は正しい。plan の件数・byte 再集計も静的再測定と一致し、親値を固定値へ転写しない判断は妥当。[s2-plan.md:6](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:6)

- **PC-2:** P1 の read-only 境界は明確で、`delete/move/apply/archive` を持たず、未定義 subcommand の負例も予定されている。[s2-plan.md:24](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:24) [s2-plan.md:126](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:126)

- **PC-3:** worktree `stat()` でなく HEAD tree/blob を使い、dirty worktreeでも同じ HEAD inventory を維持するテスト方針は決定性に有効。[s2-plan.md:81](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:81) [s2-plan.md:120](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:120)

- **PC-4:** `tools/run_tests.py` の変更は、新規 pytest の収集だけなら不要。既定 target は `orchestrator/tests` である。[run_tests.py:42](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:42) pytest-only allowlist 追加も、自走 harness を持たせない選択なら既存契約に合う。[orchestrator/tests/README.md:84](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/README.md:84)

- **PC-5:** `docs/ruleops.md` を `LIVING_DOCS` と `_OWN` に追加する方針は、文書消失と腐る行番号参照を検出する責務に合う。[check_docs.py:26](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_docs.py:26) [check_docs.py:67](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_docs.py:67)

- **PC-6:** proof chain、campaign、正式 report、submodule、既存 heterogeneous mutation schema の移行を v1 に含めない境界は明記されている。[s2-plan.md:158](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:158)

- **PC-7:** plan は pytest 非実走を明記し、緑を捏造していない。[s2-plan.md:144](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:144)

## scope 外の裁定候補

- **C-1: staged/committed deletion と承認 package の機械束縛。** `run_tests.py`、hook、commit差分のいずれで強制するかは P1 を越えるため、別裁定にする。ただし導入しない限り「削除 gate」実装済みとは呼ばない。

- **C-2: mutation receipt producer / isolated experiment runner。** B-2を機械証拠として閉じるなら scope 拡張が必要。見送る場合、v1 は evidence validator ではなく evidence-document schema checker に縮める。

- **C-3: 既存251 insight の型付け・移行・archive/tombstone。** 凍結逐語やmutation証拠を含むため、自動分類や後付け marker は行わず、個別裁定パッケージにする。

- **C-4: test node単位の retirement と pytest価値二層化。** 現 plan はfile単位だけであり、大きなtest file内部の陳腐nodeは回収できない。別タスクとして裁定する。

## 総括

現 plan は **NO-GO**。P1 の read-only 境界と P3 の動的 inventory は支持できるが、非空 ledger の自己参照、未束縛 receipt、凍結 snapshot の型誤認という3 BLOCKERがある。

これらを直さず空 ledger + standalone CLI を実装しても、成果物は「決定的 inventory prototype」であって、T-143 の「回収する運用機構」には達しない。pytest は未実走であり、緑の受入結果はない。