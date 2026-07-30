判定は **NO-GO**。must-fix は **8件**です。指定資料はすべて全文読了しました。read-only の静的検分だけで、pytest・runner・mutation は実行しておらず、author 報告の緑も独立確認済みとは扱っていません。

### Must-fix 1 — NEG snapshot の正解集合そのものが正本と違う

- severity: **CRITICAL**
- real/refuted: **real**
- 反例: 正本では NEG の untracked は `brief.md / adjudication-plan-v2.md / review-a.md / review-b.md / focus1.md / fix2.md` の6件で、`fix1.md` は禁止です。[正本:80](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/adjudication-plan-v2.md:80)  
  実装は `review-a / review-b / fix1 / fix2 / focus1` の5件を正解にしています。[実装:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:93) [実装:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:116)  
  `build-snapshot --case NEG` はこの誤集合を自ら作り、`verify_snapshot()` の全 assert を通します。しかし歴史 NEG prompt が要求する2文書を読めず、実runは即停止し得ます。author もこの不整合を報告済みです。[author:31](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/author.md:31)
- 成果物影響: NEG の `valid_n`、偽陽性 occurrence、arm failure 数が benchmark 欠損で変わり、常時 NO-GO arm を排除できません。T-184 の採用判断は無効です。
- 最小fix: [実装:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:93)-[119](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:119) で共通 hash から `fix1.md` を外し、case別 hash/allowlist に分離して正本の6件へ一致させる。実 prompt が参照する全 path の存在と、余剰 path 不在を literal test にする。

### Must-fix 2 — `verify` は replay verifier ではなく、自己申告 receipt/score を信じる

- severity: **CRITICAL**
- real/refuted: **real**
- 反例: `verify_manifest()` は `frozen=true` を見た後、raw rollout・events・done・prompt・snapshot を再検証せず、手書き JSON を集計するだけです。[実装:1461](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1461) [実装:1598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1598)  
  実際の「replay」test fixture は `valid`、`primary_rc`、`thread_id`、`turn_id`、`effective_effort`、`model`、`cli_version`、`rollout_sha256` を持たない receipt と、手書き `r1_candidate` を受理させています。[test:622](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:622) [test:780](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:780)
- 具体的に、出力を `## 総括\nGO` の短片にしてその SHA だけ score JSON に貼り、`valid=true` と書けば通ります。receipt から ledger issue を削除しても再計算されません。schedule の `prompt_sha256` と `snapshot_manifest_sha256` は欠落を許すため、各runが別 prompt/snapshotでも通ります。[実装:1497](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1497)
- 成果物影響: token、model_calls、`valid_n`、R-1候補数、GO/NO-GO を任意値にでき、受理集合全体が fail-open です。凍結 artifact は T-184 の proof chain になりません。
- 最小fix: [実装:1461](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1461) で厳密 schema を要求し、manifest に raw events/done/rollout/prompt/output/snapshot oracle を必須化する。`verify` は `collect_run()` と `score_run()` を再実行し、保存 receipt/score と canonical byte equality を取る。

### Must-fix 3 — stale session と余剰 session が枠を埋められる

- severity: **CRITICAL**
- real/refuted: 三者一致そのものは **refuted（実装済み）**、freshness/set equality 保証は **real**
- `id == session_id == thread_id` は実際に assert されています。[実装:980](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:980)
- 反例: 過去の `events.jsonl` と `.done` を残し、今回 envelope 内で `touch` する。実 inode を引数に渡し、実際の旧sizeとは無関係に `--events-initial-size 0 --done-initial-size 0` と申告する。旧rolloutの cwd/commit/prompt が同じなら、rollout timestamp は envelope と比較されないため `collect_run` を通ります。[実装:808](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:808) [実装:941](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:941)
- schedule/session の set equality は `--sessions-root` 指定時だけです。[実装:1545](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1545) 通常の `verify` testは省略して緑を期待しています。また scan は `set[str]` なので、既存IDを持つ余剰7本目を複製すれば件数が潰れます。[実装:1381](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1381)
- 成果物影響: 過去wave・retry・別armの逐語、token、判定が今回runへ帰属し、arm別数値とT-184判断が反転します。
- 最小fix: `sessions_root` を verify の必須引数にし、session ID集合ではなく `(path,inode,id,session_id,timestamp)` の一意な行集合を検査する。session/task timestampを各run envelopeへ束縛し、初期sizeの後付けCLI申告を信用しない launch receipt に置換する。

### Must-fix 4 — 再実行上限は数値欄に過ぎず、実際には効かない

- severity: **HIGH**
- real/refuted: **real**
- 反例: 100回失敗して101回目だけ成功させ、最後の10行だけを manifest に入れて全行 `attempt=1` とする。`1 <= attempt <= 3` と10行 cardinalityしか見ないため通ります。[実装:1432](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1432) 逆に全行 `attempt=3` でも、attempt 1/2 の実在を要求しません。
- 成果物影響: 失敗attemptのtoken・wall-clock・arm failureが消え、成功するまで回した結果を zero-miss にできます。T-184 のcost/quality判断が選択バイアスで変わります。
- 最小fix: 不変な logical slot ID と attempt ledger を分け、`1→2→3` の連続性、各失敗pairとの親子関係、全attempt artifact保存、4回目不存在を検査する。最終10行だけではなく全attemptを verifier の受理面に含める。

### Must-fix 5 — primary の盲検 verdict join が存在しない

- severity: **CRITICAL**
- real/refuted: machine receipt/scoreの基本run_id照合は **refuted（存在）**、人手primary joinは **real**
- receipt/score/output は run_id と SHA で逐件照合され、単純なファイル2行入れ替えは拒否できます。[実装:1475](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1475)
- しかし `blind_id`、`verdict_sha`、`r1_detected` は一切なく、出力は常に `primary_endpoint: not_scored` です。[実装:1586](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1586) testもこれを成功条件にしています。[test:788](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:788)
- 反例: max/high の盲検 verdict 2行を外部表で交換しても verifier の入力に存在しないため、総hit不変のままarm別primaryが逆転します。手書きscore内の `r1_candidate` 2値だけを交換しても、run_id/input SHAを残せば通ります。
- 成果物影響: 仕様上のprimary endpointが凍結成果物に存在せず、T-184は採用判断を行えません。
- 最小fix: manifest各行へ `blind_id→score_input_sha→verdict_sha→r1_detected→adjudicator` を必須追加し、unblind mapとのbijectionとrun_id逐件joinを検査する。row-swap mutationはarm文字列ではなく、この verdict 2行を交換する。

### Must-fix 6 — scorer は否定・曖昧決定・CommonMark境界を誤受理する

- severity: **HIGH**
- real/refuted: **real**
- 歴史control自体は通ります。focus1は総括1213 bytes、NO-GO、R-1候補=true、focus2は649 bytes、GO、候補=falseとなる構造で、actual file testもあります。[test:557](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:557) よって「歴史controlを取り違える」は refuted です。
- 否定反例: `R-1` 節に「pre-policyではcanonical CAB parserは実行されない。rc=0がrc=2になることはない。このNO-GO/must-fix説はrefuted」と書くと、4語彙条件が全部trueになり `r1_candidate=true` です。[実装:1303](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1303)
- 正しい別表現反例: R番号を使わず「規則導入以前にも正式なCAB readerが走り、例外時に従来成功を内部エラー終了へ変えるためrelease blocker」と書くと、仕様の三命題を満たしても候補=falseです。
- 曖昧決定反例: 500 bytes超の総括を `GO / NO-GO は未裁定` で始めると、先頭の `GO` だけを採用して valid になります。[実装:1276](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1276)
- 通常の `~~~markdown` と500 bytes未満総括は正しく拒否します。ただし tilde fence のinfo stringにbacktickを含む有効CommonMark、例えば `~~~ lang\`x` は opening regexに一致せず、内部の偽 `## 総括` が可視になります。[実装:1214](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1214)
- 成果物影響: `r1_candidate_n`、GO/NO-GO、arm failure/valid_nが変わり、書式傾向の違いだけでT-184の採用方向が変わります。
- 最小fix: lexical candidateをprimary相当へ使わず、否定scopeを扱う凍結codebookへ限定する。決定語の全出現を検査して一意性を要求し、CommonMark準拠parserか完全なfence grammarを使う。上記3反例を独立fixtureに追加する。

### Must-fix 7 — golden の2経路は同じpatch engineの単一故障点で、M2をtestが殺さない

- severity: **HIGH**
- real/refuted: 異なるpatch sourceを比較している点は **refuted**、engine/test独立性は **real**
- runtimeには `(integrated − fix2)` と `(base + author + fix1)` の比較がありますが、両方とも `_apply_patch_set()` を使用します。[実装:398](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:398) 例えば untouched 部分にbare CR/Unicode separatorがある入力では、共通の `splitlines()`→LF join が両経路を同じ誤bytesへ正規化できます。[実装:351](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:351)
- さらに test は両routeを同じproduction engineで作るだけです。[test:361](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:361) `derive_independent_golden()` のroute B比較を削除するM2でも、このtestはその関数を呼ばないため赤くなりません。
- 成果物影響: 誤った2ファイルbytesが正解hashになればR-1の実在・finding数が変わり、T-184の品質評価対象自体が別物になります。
- 最小fix: 一方を実Git `apply`/`apply -R`、他方を別decoderで導出し、actual pinned rolloutsから得た最終bytesと独立literal SHAを照合する。route B削除mutationをproduction entrypoint経由で殺すtestを追加する。

### Must-fix 8 — turn graph不一致とpost-treatment分類漏れ

- severity: **HIGH**
- real/refuted: **real**
- 反例1: `turn_context.turn_id=A`、`task_started.turn_id=B`、`task_complete.turn_id=B` とし、model/effort/cwd、token、outputを正常にする。context内部は単一、start/complete同士も一致するため通ります。contextとtaskのjoinがありません。[実装:1005](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1005) [実装:1077](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1077)
- 反例2: valid token/output/task_completeはあるが `task_started` 行だけ欠落すると、理由は `task_started count is 0`。文字列ベース分類にpost markerがないため technical-invalidとなり、推論後の失敗が品質分母から消えます。[実装:877](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:877)
- 反例3: token usage全fieldを0にしたobjectを1件置くと、token eventあり・schema valid・model_calls=1としてreceiptが通り、実消費0に見えます。
- 成果物影響: effort/token/outputが別turnへ結合され、arm failureとcostが過小計上されます。T-184のcost/quality判定が変わります。
- 最小fix: context/start/completeの同一turn_id、行順・timestamp・envelopeを逐件assertする。failure classは理由文字列でなく、task/token/agent eventを見たかという構造化stateから決める。非空prompt/outputのrunでは正のtoken消費を要求する。

### テストの自己追認・実rolloutとの乖離

- `_snapshot_fixture()` は書いたbytesから期待hashを採取するため、canonical POS/NEGを検査していません。[test:316](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:316)
- patch 2経路testは同じ `_apply_patch_set()` を二度使用しています。
- prompt testは合成messageからSHA・size・置換数を採取してproduction定数をmonkeypatchしています。[test:444](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:444)
- 「focus1 real slice」はtoken列だけがliteralで、session_meta/task/context/outputは合成です。source rollout SHAはfixture bytesと照合していません。[test:115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:115)
- `_aggregate_fixture()` がproducerを通さずreceipt/scoreを手書きし、その欠落schemaを `verify` の正例にしています。これは最も強い自己追認です。
- stale fileをtouchする経路、token event 0件、all-zero usage、abort、context/task turn不一致、retry上限、corrected NEG allowlist、blind verdict row-swapがありません。
- actual `focus1.md`/`focus2.md` controlだけは独立正例・負例として有効です。

### Scope・no-touch・commit

`git status` は次の2 untracked fileだけでした。

- `tools/codex_reasoning_ab.py`
- `orchestrator/tests/test_codex_reasoning_ab.py`

tracked差分、staged差分、docs編集、所有外変更はありません。HEADは `7be05ef7e3487dd62b553c672627845a444e1ff9` のままで実装commitもありません。author子がcommitしない契約には合致し、no-touch違反は **refuted** です。

なお author の `git diff --check: rc=0` は untracked 2ファイルを検査しないため、成果物影響のない **nit/backlog** とします。[author:25](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/author.md:25)

## 総括

**NO-GO。must-fix は8件です。** 最優先は、正本と異なるNEG snapshotをoracle自身が正解として作る点、凍結`verify`がraw rolloutを再生せず手書きreceipt/scoreを信用する点、stale session・余剰session・無制限retryを今回runとして受理できる点です。この3系統だけで、負対照の偽陽性数、arm別valid_n、token・wall-clock、R-1候補数を任意または過度に楽観的な値へ変えられます。さらに、仕様上primaryである盲検人手verdictはmanifestにもjoinにも存在せず、現在の成果物は明示的に`not_scored`です。したがってT-184はこの実装結果からreasoning routingを採用できません。

局所的には、ID三者一致、ledger issue伝播、token event 0件、全info null、最終cumulative null、非object行、context 0件、effort変化、abort、短い総括、通常のtilde fence、歴史focus1/focus2の向きは静的に成立しています。しかし最終`verify`がそれらを再計算しないため、個別gateが正しくても凍結成果物の受理集合には届いていません。NEG allowlistを正本へ合わせ、raw artifact replay、必須session集合検査、attempt全履歴、blind verdictのrun_id join、否定・曖昧決定を扱うscorer、独立patch engine、turn graphに基づく失敗分類を実装し、それぞれの反例をmutationで殺すまでは段7へ進めない判定です。