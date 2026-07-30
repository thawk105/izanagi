指定資料はすべて読了しました。書き込み、pytest、live inference は実行していません。現行 plan のまま段5へ進む判定は **NO-GO** です。

## 1. snapshot oracle は「歴史 focus1」と異なる状態を正解にする

- severity: **CRITICAL / must-fix**
- 判定: **real**
- 根拠:
  - brief は `9b26b3b` から fix2 を逆適用すれば focus1 状態になると断定していますが、plan 自身が HEAD・dirty 状態の差を認めています。[brief:19](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:19) [plan:42](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:42)
  - それでも plan は detached HEAD を正解にしています。[plan:77](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:77) 歴史 session は branch `codex/dev-wave-t153e-t15423` でした。[rollout:1](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl:1)
  - さらに plan は untracked closure を `review-a.md`、`review-b.md`、`fix1.md` の3件に限定します。[plan:52](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:52) [plan:91](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:91) しかし実ログでは focus1 が同じ artifact directory を検索し、`adjudication-plan-v2.md`、consult、plan、各 log・patch など多数を列挙し、実際に `adjudication-plan-v2.md` を読んでいます。[rollout:139](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl:139) [rollout:143](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl:143)

具体的な誤 snapshot 合格例は二つあります。

1. plan どおりの detached HEAD、untracked 3件だけの snapshot は全 assert を通ります。しかし歴史 focus1 の branch と可視 artifact 集合が違います。oracle が誤差を検出しないのではなく、誤差を正解として要求しています。
2. 既に dirty な `tools/check_ai_provenance.py` の mode を `0644→0755` に変えても、content SHA、dirty path、numstat、regular/non-symlink、逆パッチ round-trip は変わりません。提案された全検査を通しつつ Git/file 状態が異なります。

9入力については、content SHA は機械的には **9/9** を拘束します。ただし歴史状態に対する独立 oracle は現状 **7/9** です。4件は `9b26b3b` の未変更 blob、3件は `08a7e5f2` の artifact blobで独立に固定できます。逆適用対象の次の2件は、期待 SHA の由来が同じ逆再構成なら自己追認です。

- `tools/check_ai_provenance.py`
- `orchestrator/tests/test_check_ai_provenance.py`

- 成果物影響: R-1 の `k/3`、新規 finding、歴史 max 出力を scorer oracle に使えるかが変わります。この状態で得た insight は「歴史 focus1 の再現」ではなく別入力の実験であり、T-184 の採用根拠にはできません。
- 最小是正:
  - [plan:42](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:42) で、歴史状態の完全再現を撤回して「意図的に閉じた9ファイル positive-case」と再定義するか、branch・mode・実際に観測された untracked closure まで再構成してください。後者は結果漏洩を再導入するため、前者を推奨します。
  - planned `tools/codex_reasoning_ab.py:321` で全9件の `st_mode`、HEAD symbolic state、許可 untracked 集合を pin。
  - 逆適用対象2件は、同じ patch engine の round-trip ではなく、歴史 rollout の全文出力から別経路で作った golden bytes と逐件照合してください。

## 2. thread ID 同定は改善だが、fresh run の受理集合を固定していない

- severity: **CRITICAL / must-fix**
- 判定: **real**。cwd 部分一致を採用しない点だけは refuted。
- 根拠:
  - full `thread.started.thread_id` と session meta の完全一致は、T-179 の cwd 部分一致より強いです。[plan:141](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:141)
  - ただし locator は `session_meta.payload.id` を正本にする一方、再利用する ledger は `payload.session_id` を読みます。[plan:146](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:146) [ledger:253](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:253) 実ログには両 field があり同値ですが、二義化した入力を拒否する assert がありません。[rollout:1](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl:1)

6 run を並列投入した場合、次が黙って混入できます。

1. 既存 `events.jsonl` と `.done` が残った run directory を再利用し、過去 thread ID を採用する。
2. launch が1本失敗しても、同じ snapshot path・prompt・commit・effort の過去 session で穴を埋める。
3. pilot/retry/別 wave が同じ job path を再利用し、cwd・commit・prompt検査も通る。
4. filename suffix で候補を減らすと、同じ meta ID を持つ renamed copy を走査せず、「一意」と誤判定する。
5. 7本目の retry/session が存在しても、予定された6個の events file が埋まれば余剰 session を無視する。
6. run directory 一式の取り違えで、session・output・receipt が別 schedule slotへ帰属する。

`scheduled_n=3`、`valid_n=3`、session ID 6個が一意でも、これは「fresh な今回の6 process」だとは証明しません。[plan:149](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:149) [plan:226](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:226)

また brief の pilot→残り投入と plan の逐次交互実行が未裁定のままです。[brief:61](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:61) [plan:274](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:274) 全6本並列でも verifier は拒否しないため、wall-clock の競合条件まで受理集合外です。

- 成果物影響: output、token、wall-clock、R-1 verdict が別 run・別 armへ帰属し、arm別合計や T-184 の採用判断が反転し得ます。
- 最小是正:
  - [plan:141](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:141) に、run 前に凍結する `run_id→arm→argv hash→events/output/done path` schedule manifest を追加。
  - run directory は非存在から作り、events・done は regular/non-symlink、開始時 size=0、fresh inode、launch 時間 envelope 内であることを要求。
  - planned `tools/codex_reasoning_ab.py:501` で `id == session_id == thread.started.thread_id` を逐件 assert。
  - filename suffix は一意性検査の候補削減に使わず、root 全体から meta ID の0/1/複数を数える。
  - 予定6 run ID集合と、launch envelope 中に生成された対象 session ID集合を set equality で照合する。

## 3. receipt adapter が T-179 の fail-open を再び握りつぶせる

- severity: **CRITICAL / must-fix**
- 判定: **real**
- 根拠:
  - 現 ledger は最終 cumulative の型異常と top-level 非 object を issue 化します。[ledger:235](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:235) [ledger:240](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:240) [ledger:309](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:309)
  - しかし plan は `_stream_rollout()` の returned `issues` を全件 per-run failure にする、と明記していません。[plan:124](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:124) [plan:228](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:228)
  - `token_count.info` が `null`／非 object なら ledger は issue を出さず黙って飛ばします。[ledger:304](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:304) 全 token event がこの形、または token event 自体が0件なら `model_calls=0, cli_reported=0` が正常 receipt になれます。
  - `reasoning_output_tokens` 欠落は0になります。[ledger:175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:175) 既存テストも legacy 形として strict rc=0 を固定しています。[ledger test:377](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_worker_ledger.py:377)
  - ledger の strict は `outcome=incomplete` 自体を failure にしません。既存テストは task_complete 欠落でも strict rc=0 を期待します。[ledger test:465](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_worker_ledger.py:465)

複数 `turn_context` は一律拒否できません。実在 focus2 は同じ `turn_id` に同一 `(model,max)` の context が2件あり、その間に compaction があります。[focus2 rollout:8](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T16-19-59-019facbe-9584-7642-aa30-37f1c77e6c5f.jsonl:8) [focus2 rollout:147](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T16-19-59-019facbe-9584-7642-aa30-37f1c77e6c5f.jsonl:147) [focus2 rollout:149](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T16-19-59-019facbe-9584-7642-aa30-37f1c77e6c5f.jsonl:149) 必要なのは context 行数1ではなく、distinct turn ID 1件と context 値集合1件です。

「effort 不明を max にする」という既定値は plan には明記されていないため、その具体的主張は refuted です。ただし context 0件を明示拒否していないので、実装時に requested effort で補完すれば同じ fail-open になります。

- 成果物影響: 実消費が0または直前の累積値に化け、missing effort を正しい arm と誤認します。token比、model_calls、valid_n、T-184 の cost/quality 判断が変わります。
- 最小是正:
  - planned `tools/codex_reasoning_ab.py:501` で ledger issue の全 category を failure reason に流し、この実験では1件でも RC≠0。
  - `token_count` 1件以上、valid cumulative 1件以上、最終 token event の schema valid、`model_calls>0` を要求。
  - pinned CLI versionでは `reasoning_output_tokens` 必須、`0 <= cached_input_tokens <= input_tokens`、`total_tokens == input_tokens + output_tokens` を要求。
  - `turn_context` は1件以上、全件同じ turn ID・cwd・model・effort。欠落を requested 値や `max` で補完しない。
  - task_started/task_complete 各1件、同じ turn ID、順序・timestamp・duration整合を要求。`turn_aborted` は task_complete が後にあっても無効。`thread_rolled_back` の扱いも段4で明示裁定する。
  - T-179 の実在3経路を、新 adapter を通す独立回帰として再登録する。既存 ledger test の緑で代替しない。

## 4. scorer は既知の真陽性 focus1 を miss にする

- severity: **CRITICAL / must-fix**
- 判定: **real**
- 根拠:
  - plan は R-1 真陽性に literal `check_cab` を必須とします。[plan:200](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:200)
  - ground truth の歴史 focus1 R-1 block には `check_cab` がありません。`validate_message()`、canonical CAB parser、`_has_co_authored_by_policy`、`_parsed_trailers` で正しく因果を説明しています。[focus1.md:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/output/insights/2026-07-29_t153e-t15423-review-verbatim/focus1.md:17) [focus1.md:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/output/insights/2026-07-29_t153e-t15423-review-verbatim/focus1.md:25)
  - 見出しも `### R-1` ではなく `### 残存finding R-1 — ...` です。plan の厳密 block grammar次第で二重に落ちます。[focus1.md:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/output/insights/2026-07-29_t153e-t15423-review-verbatim/focus1.md:17)
  - `real/refuted: real` の正しい行は文字列 `refuted` を含みます。[focus1.md:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/output/insights/2026-07-29_t153e-t15423-review-verbatim/focus1.md:21) 「block内に refuted が無い」という token-level negative guardなら既知正例を落とします。逆に `R-1 is not real` は literal `real` を含むため、単純 regex では偽陽性です。
  - frozen prompt は table header、`数字+件`、`### R-N` grammarを要求していません。異なる表形式・日本語見出し・箇条書きで正しく検出しても、有効 run の miss として数える経路があります。

summary fragmentも残っています。既存 checker が測る500 bytesは成果物全体であり、総括節ではありません。[checker:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/check_codex_output.py:100) 長い本文と完全な表の後に、

`## 総括` + `NO-GO。残must-fixは1件。`

だけを置けば、plan の GO/count 条件は満たす一方、prompt の「総括を500 bytes以上」に違反します。また fence 除去は backtick のみで、tilde fenceを除きません。[checker:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/check_codex_output.py:16) [checker:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/check_codex_output.py:37) `~~~markdown` 内の偽総括・偽R-1も拾えます。

- 成果物影響: 歴史 max の既知真陽性が miss になり、`k/3` が少なくとも1件変わります。armごとの書式傾向が違えば片側だけ miss/invalid になり、T-184 の採用方向が反転します。
- 最小是正:
  - [plan:198](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:198) の regex 真偽を primary metric にしない。機械層は candidate extraction、最終 `r1_detected` は effort/tokenを伏せた人手裁定にする。
  - 歴史 [focus1.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/output/insights/2026-07-29_t153e-t15423-review-verbatim/focus1.md:17) を必須 positive-control にし、これを miss にする scorer は実装前に失格。
  - `R-1 is refuted`、`R-1は起きない`、`R-1は起きないという反論は成立しない`、正しい別表現を独立 fixture にする。
  - planned `tools/codex_reasoning_ab.py:661` で CommonMark の backtick/tilde fence、見出し節境界、summary節自体の UTF-8 byte数500以上を検査する。
  - 全IDや見出し形式を machine validity に使うなら、frozen prompt が実際に要求した形式だけに限定し、未指定形式を品質 miss にしない。

## 5. F54 型の element-wise join が未設計

- severity: **HIGH / must-fix**
- 判定: **real**
- 根拠: F54 は総和・session数・model_calls・worklog gateが全て不変でも、188,905 tokens の stage帰属が誤った実在 near-missです。[F54:987](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/docs/failures.md:987)
- 本 wave の同型箇所:
  - session receipt、output score、人手 verdict を別々に並べ、同じ indexで zipする。
  - run filename順と session timestamp順が異なり、各集合は6件・3/armのまま。
  - 全 receipt が同じ snapshot hashを持つが、その hash自体が誤った snapshotを表す。
  - CLI versionが全6件同じだが、事前登録した `0.146.0` ではない。plan は「全run同一」しか要求していません。[plan:151](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:151)
  - blinded human verdict の unblind mapが別 outputへ結合され、global hit数は不変でも arm別 hit数が入れ替わる。
  - score rowを別 runの token/wall receiptへ結合し、arm別合計が偶然同じでも quality/token相関が誤る。

- 成果物影響: global token、global R-1 hit、各arm n=3は変わらないまま、run別逐語・new finding・quality/costの帰属が変わります。T-184 が参照する arm別率・中央値・rangeが誤ります。
- 最小是正:
  - [plan:153](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:153) の per-run recordを、独立 scheduleの `run_id` を主キーとする一枚の表にする。
  - 各行に `scheduled_effort`, `argv_sha`, `thread_id`, `session_id`, `turn_id`, `rollout_sha`, `output_sha`, `score_input_sha`, `blind_id`, `verdict_sha` を束縛する。
  - aggregate前に scheduleとの逐件 set equality と、output bytes↔rollout final message↔score input SHAの同一性を検査。
  - 2行を交換して総数・合計を保つ mutationを登録し、aggregateではなく逐件 oracleが殺すことを確認する。

## 6. 親の予定コマンドは受入形ではなく、CIも存在確認できない

- severity: **HIGH / must-fix for all-layer claim**
- 判定: **real**
- 根拠:
  - plan の予定は個別3 test fileへの targeted pytestです。[plan:251](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:251)
  - `tools/run_tests.py` の受入形は positional targetが既定 `orchestrator/tests` 全体である場合だけです。[run_tests.py:367](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/run_tests.py:367) [run_tests.py:391](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/run_tests.py:391) 個別3ファイルでは deletion、RuleOps、submodule の acceptance preflightが発火しません。
  - 新 test file は `orchestrator/tests` 配下なので、既定全走には自動収集されます。[run_tests.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/run_tests.py:41) runner本体へ特別な分岐を追加する必要はありません。
  - repository 内には標準的な `.github/workflows` 等の CI定義が見つかりませんでした。外部CIの存在はこの資料から証明できません。

- 成果物影響: 親の一回限りの実走だけが gateになり、将来 parser/receipt/scorer が壊れても受入全走・CI・再現時に発火しない可能性があります。凍結 insight が検査不能な記録へ退化し、T-184 の proof chainが消えます。
- 最小是正:
  - targeted pytest後、repo rootから `IZANAGI_TEST_TRIGGER=final python3 tools/run_tests.py` を別に全走し、checkoutを記録。
  - `tools/run_tests.py` 自体は変更せず、新 testを既定 collectionに残す。
  - live inferenceは受入全走へ入れない。CI/全走で検査できるのは、snapshot manifest、source hash、strict JSONL schema、schedule cardinality、receipt/output/hash join、Markdown scorer、RC precedence、凍結済み6 run artifactの replayです。
  - `codex_reasoning_ab.py verify --manifest <tracked manifest>` のような pure verifierを作り、最終 artifact commit後の testがそれを実行する。
  - CI workflow新設、mount namespace隔離、live service routingは本 wave実装済みと偽らず、段4の裁定パッケージへ送る。

## 7. 合成 fixture は実ログと構造が違い、自己追認になり得る

- severity: **HIGH / must-fix**
- 判定: **real**
- 根拠:
  - 現 helper の `session_meta` は `session_id` だけで `id` を作りません。[ledger test:66](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_worker_ledger.py:66)
  - `turn_context` を task_startedなしで生成し、task_completeにも `turn_id`、`duration_ms` がありません。[ledger test:90](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_worker_ledger.py:90) [ledger test:172](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_worker_ledger.py:172)
  - 実 focus1 は session_meta、task_started、world_state、turn_context、user_message、28 token event、10 agent message、task_completeという形です。[rollout:1](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl:1) [rollout:167](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl:167)

「テストが通っても正しさの根拠にならない」箇所は次です。

- 同じ逆 patch engineで逆適用と再適用を行う round-trip。
- 再構成結果から期待 SHA を採取して fixtureへ貼る hash test。
- parserが受けやすい synthetic Markdownだけで scorerを検査すること。
- 6件・3/armだけを確認し、session/output/verdictの joinを交換する変異を持たない aggregate test。
- canonical JSONを同じ実装で二度出して一致を見る byte determinism。
- 既存 ledger testが緑でも、新 adapterが `issues` をRCへ伝播することは証明しない。

- 成果物影響: schema drift、既知R-1 miss、stale session、0-token receipt、F54 joinを見逃したまま検査数だけが増え、誤った T-184判断へ「テスト済み」の外観を与えます。
- 最小是正:
  - planned `test_codex_reasoning_ab.py:1` で CLI stdout events と session rolloutを別 fixture型にする。
  - 実 focus1の relevant event sliceを、source rollout SHA付きの tracked goldenとして使う。期待値は T-179 の独立数値 `28 / 320,640 / 806,942ms / max` を literalで照合する。
  - 歴史 focus1.mdを scorer positive-control、focus2.mdを non-regressed controlにする。
  - mode変更、`id/session_id`不一致、all-info-null、最終 cumulative null、非 object、context後の effort変更、stale `.done`、余剰第7 session、tilde fence、短い総括、row swapを負例に追加。
  - fixture/hashを更新すれば緑になる構造を避け、Git blob・歴史 transcript・独立 scheduleの少なくとも二系統で期待値を固定する。

## 8. snapshot外参照監査は結果漏洩を閉じない

- severity: **HIGH / must-fix for T-184 use、または明示的 scope-down**
- 判定: **real、plan自身も未解決と認識**
- 根拠:
  - plan は transcript の snapshot外参照監査を receipt項目にします。[plan:166](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:166)
  - しかし実 turn_context の read-only sandbox は snapshot限定ではなく filesystem rootを読めます。[rollout:8](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl:8)
  - 実際の focus1は prompt外 artifactを探索・読取しました。相対path、glob、Pythonで組み立てたpath、Gitのcommon dir、symlink経由の読取を、command文字列の絶対path検索だけで完全検出できません。
  - plan も mount namespace/containerが無ければ強い主張を避けるべきと認めています。[plan:291](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:291)
  - 逐次交互実行では後続 run が先行 run outputを読めます。6本並列でも、完了時刻がずれれば同じです。

- 成果物影響: R-1 は promptで名指し済みなので盲目発見率ではありませんが、新規 finding数、引用、結論強度が歴史回答や先行arm出力で増えます。T-184 が reasoning効果ではなく漏洩差を採用する危険があります。
- 最小是正:
  - runtime隔離を本 scopeに入れるなら、runごとに snapshotと必要runtimeだけを見せる mount namespace/containerを使用。
  - 入れないなら裁定パッケージとして明記し、insightを「root-readable host上の named-hypothesis確認実験」に縮退。新規 finding率と既定policy変更の根拠には使わない。
  - transcript auditは「明白な外部参照の検出」であって、非参照の証明ではないと出力schemaに記録する。

## 総括

**NO-GO。現行 plan のまま実装へ進めません。** 致命的な fail-open は、第一に、歴史 focus1 と異なる detached HEAD・3件だけの untracked closureを oracle自身が正解にしていること、第二に、fresh launcher receiptがなく過去・別wave・retry sessionで6枠を埋められること、第三に、ledgerの issue伝播・token/context存在条件が未規定で0-tokenまたはeffort不明を有効化できること、第四に、既知の真陽性 focus1が持たない literal `check_cab` をR-1必須語にしていることです。特に scorer は現に ground truthを missへ変えるため、実装詳細以前に受理集合が壊れています。

must-fix は8群です。snapshotを「歴史再現」から明示的な9ファイル限定 positive-caseへ再定義し、2件の逆適用対象へ独立 goldenを置くこと、schedule manifestとfresh process envelopeを発行すること、`id=session_id=thread_id` と run単位の全hash joinを逐件照合すること、ledger issue・0 token・context欠落・abortを必ず非0にすること、歴史 focus1を scorer positive-controlにすること、総括節500 bytesとtilde fenceを検査すること、凍結 artifact replayを受入全走へ載せること、そして filesystem隔離を実装するか T-184への射程を明示的に縮めることが必要です。新 testは `orchestrator/tests` 配下なので `tools/run_tests.py` の既定全走には自然に結線できますが、plan記載の個別pytestだけは受入形ではなく、repository内CIも確認できません。live inferenceを受入全走へ入れる提案や、DW-O01の既定 reasoning値を書き換える提案はしていません。これらを段4 plan v2で閉じ、row-swap・stale-session・known-positive scorerの独立変異を事前登録できた後にのみ、条件付きGOへ再評価できます。