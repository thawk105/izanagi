## 総括

**(e) 可・推奨** — 受入・land を閉じたまま裁定／修復待ちとするのが唯一、受理集合も検出力も変えない。wave 全体を終了する必要はなく、D1144 に従って非 land 作業を終え、正当な修復で tip が変わるまで再投入しない。

## 選択肢ごとの判定

### (a) 復元 — 条件付き可、ただし現状は実行不能

exact bytes を権威ある backup から戻せるなら、pin や受理集合を変えないため最も安全である。ただし必要なのは author 1本だけではない。

- 5 session と SHA は凍結値である: `tools/codex_reasoning_ab.py:196-208`。
- POS/NEG は manifest の provenance、author/fix1/fix2 は独立 golden の入力である: `tools/codex_reasoning_ab.py:329-356`, `tools/codex_reasoning_ab.py:925-970`。
- exact SHA は同一性の錨として検査される: `tools/codex_reasoning_ab.py:640-655`, `docs/decisions.md:14399-14401`。
- POS はさらに固定 path から直接読まれる: `orchestrator/tests/test_codex_reasoning_ab.py:145-149`, `orchestrator/tests/test_codex_reasoning_ab.py:8575-8583`, `orchestrator/tests/test_codex_reasoning_ab.py:8611-8617`。

現存 7,169 rollout を5つの期待 SHAすべてで全件 hash 照合したが、**POS/NEG/fix2/author/fix1 は全て0件**だった。backup、Trash、repo output、浅い `/work`、local tmp、git object にも回収可能な一致は見つからなかった。別 host の非共有 local disk には到達できないため絶対的不在までは主張しないが、現在読める回収元からの復元は現実的でない。

復元を可とする条件は、5本すべてについて期待 SHA が一致し、session owner が各1件になり、POS の固定 path も復元されること。

### (b) pin の張り替え — 不可

受理集合を変える。

- session ID/SHA は frozen task manifest の provenance そのもの: `tools/codex_reasoning_ab.py:313-361`。
- public alias も manifest から導出されるため、張り替えは manifest canonical bytes と downstream digest を動かす: `tools/codex_reasoning_ab.py:363-389`。
- author/fix1/fix2 の rollout は二つの独立経路から golden bytes を導く入力であり、別 session への変更は検査対象を変える: `tools/codex_reasoning_ab.py:925-970`。
- literal provenance を固定する回帰もある: `orchestrator/tests/test_codex_reasoning_ab.py:1765-1789`。
- 既裁定も frozen T-181 provenance の書換えを禁じる: `docs/decisions.md:38935-38937`。組込み T-181 manifest を変更せず従来の受理集合を維持する決定もある: `docs/decisions.md:40664-40669`。

したがって本 wave が「現存する似た session」を選ぶ範囲ではない。同一 bytes の別 copy を置くだけなら、それは (b) ではなく (a) である。

### (c) hold 登録 — 不可

本 wave の F fragment を根拠にするのは循環であり、現行実装上も通らない。

- DW-O18 は明示的に「**main既存F**」を要求し、F 不在時は登録せず裁定送りとする: `docs/dev-wave/operations.md:131-135`。
- 現行 validator は `evidence_id` を canonical `docs/failures.md` の実 F に限定する: `orchestrator/tests/flaky_test_holds.py:19-23`, `orchestrator/tests/flaky_test_holds.py:142-150`。
- さらに F 節には登録 node の exact test 関数名と failure signature が必要: `orchestrator/tests/flaky_test_holds.py:151-161`。
- wave の fragment は land 時まで canonical F にならない。この構造的循環は既に F766 に記録済み: `docs/failures.md:19668-19696`。
- 今回の fragment は exact test 関数名を0件しか含まず、しかも「26件すべて同じ fixture setup 本文」と誤記している: `docs/spool/failures/2026-09-01-dev-wave-t1909-probe-closure-3.md:30-41`。

循環を断てる既存条件は次のどちらかだけである。

1. 別の先行 wave が、exact node 名と各 failure signature を持つ F を canonical main へ先に land し、後続 wave がそれを使う。
2. D1160 の placeholder 契約が先に main へ実装される。D1160 自体は循環を認識して placeholder を裁定済みだが、現行 regex は未実装のままである: `docs/decisions.md:38786-38798` と `orchestrator/tests/flaky_test_holds.py:19,142-150`。

自分の赤を自分の未採番 fragment で hold するのは、このどちらでもない。

### (d) skip 条件の是正 — 不可

「未検査である」という表示自体は正直だが、**受入が skip を許す以上、正しさゲートとしては検出力低下であり、受理集合を広げる**。しかも提案どおり fixture だけを変えても26件は skip にならない。

fixture 利用 node は21件である: `orchestrator/tests/test_codex_reasoning_ab.py:787-825`。これを skip にすると、次の回帰検出が消える。

- snapshot/golden closure: `:2133`, `:2448`, `:3119`, `:3147`, `:3159`, `:3169`, `:3196`（3 parameter node）, `:3211`, `:6104`
- schedule・answer reinjection: `:7056`, `:7139`
- supervisor isolation: `:8627`, `:8658`
- end-to-end replay/digest/evidence: `:8796`, `:8855`, `:9254`, `:9375`
- prelaunch failure handling: `:11961`, `:11981`

具体的には、HEAD/mode/symbolic HEAD、extra/missing artifact、再帰 submodule closure、stale commit graph、POS/NEG 初期化差、schedule pairing、answer object reinjection、git環境 scrub、sandbox exclude、manifest交換、snapshot evidence伝播、pre/post検査、pair failure処理などの回帰が acceptance から不可視になる。

さらに fixture を使わない5 node は残る。

- `test_m2_production_golden_requires_both_routes`: `:3128-3143`
- `test_prompt_replacement_count_zero_expected_and_excess` の3 node: `:8575-8608`
- `test_real_rollout_collector_golden_is_source_bound`: `:8611-8624`

したがって fixture の条件だけを広げても、**21 skip・5 failed**となるだけで緑にはならない。5件まで skip するなら、凍結 source SHA と二経路 golden の検査も失い、さらに弱化する。

### (e) 停止 — 可・推奨

受入・land を停止する。DW-O18 は `child-green` だけを受理し、赤の受領証を禁じる: `docs/dev-wave/operations.md:135`。よって receipt 不発行の現状を維持するのが正しい。

D1144 により「wave 全体を終端する」必要はない。非 land 作業を終え、正当な修復または有効な hold によって tip が変わるまで再投入しない: `docs/decisions.md:38374-38394`。これは (e) の gate 停止と両立する。

## 正しさゲートへの影響

推奨 (e) は受理集合・検出力を一切変えない。

- 現在拒否されている tip は拒否されたまま。
- 26 node は除外・skip 化されない。
- T-181 の frozen provenance と manifest digest は不変。
- `child-green` が得られるまで receipt と land は開かない。

代償は進行停止だが、検査不能な状態を緑へ読み替えないための正しい停止である。

## 事実の projection との食い違い

あり。重要度順に以下。

1. **「26件すべて同じ fixture setup error」は誤り。** 実ログは `21 error, 5 failed`。5 failures は fixture 非依存で、うち4 node は固定 POS path の `FileNotFoundError`、1 node は独立 golden 呼出の author 欠落である。`acceptance-child-1.log:3-28`、`orchestrator/tests/test_codex_reasoning_ab.py:3128-3143,8575-8624`。
2. **「fixture を直すと26件 skip」は誤り。** fixture consumers は21 nodeだけで、上記5 nodeは残る。
3. **author 以外4本が健全とは確認できない。** author が最初に失敗するため、その走行は後続素材の exact SHA を証明しない。現存7,169 rolloutの全 hash 照合では、凍結された5 SHAすべて0件だった。
4. consultation 中に共有 worktree の HEAD が `53b02a7de` から `382711c355` へ進んだ。現行 docs は D1144 に従って「wave 全体は停止せず修復待ち」へ更新されているが、受入・land が閉じている点は不変。
5. rollout 母数は新規 session 増加により 7,120 から7,169へ変化した。また author ID の単なる言及は現在153 filesあり、projection の3 filesは時点差である。owner match が0件という核心は変わらない。

## 全件検索の記録

完走した検索のみを0件根拠にした。

- `find /home/SFC/tanab/.codex/sessions -type f -name 'rollout-*.jsonl'`  
  → **7,169 files**
- 上記7,169 filesを `sha256sum` し、`_LEGACY_ROLLOUT_SHA256` の5値と照合  
  → **POS=0, NEG=0, fix2=0, author=0, fix1=0**
- 上記 store で5 session IDを basename検索  
  → **0 files**
- POS の固定 exact path検索  
  → **0 files**
- `rg -uuu -l -F <author-id> /home/SFC/tanab/.codex/sessions`  
  → **153 files**（525 lines、すべて言及。ownerではない）
- `/home/SFC/tanab/.claude/{backups,sessions}`  
  → 母集合 **49 regular files**、author ID filename/content **0**、5 SHA一致 **各0**
- `/home/SFC/tanab/.local/share/Trash`  
  → regular file **0**、一致 **0**
- repository `output/**/*.jsonl`  
  → 母集合 **278 files**、5 SHA一致 **各0**。標準 `rollout-*.jsonl` は **0**
- `/work/1/SFC/tanab` の深さ6まで、author ID basename／POS exact path  
  → **各0**
- `/tmp` と `/var/tmp` のauthor ID basename／POS exact path  
  → **各0**
- `git rev-list --objects --all` のauthor ID／POS rollout basename  
  → **各0**
- `.snapshot` 候補6 path  
  → **存在0**
- backup/trash/session候補ディレクトリ列挙  
  → `/home/SFC/tanab/.claude/backups`, `.claude/sessions`, `.codex/sessions`, `.local/share/Trash` の **4 directories**

`/work` 全深度走査と別 host の非共有 local disk は完走・到達できていないため、そこまで含めた「machine 全体0件」とは主張しない。pytest は実行していない。