結論は **NO-GO** です。パッチと worktree の `git diff` は SHA-256 が一致しましたが、blocker 候補が 2 件あります。以下は pytest 未実施の静的レビューです。

## 所見

### 1. truncated tail repair が guard より先に走り、正しさ signal を消して回復できる

- **severity:** blocker 候補
- **根拠:** [`ident.ensure_resumable_wal`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/ident.py:185) は identity → [`repair_truncated_tail`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:526) → recovery の順です。repair は receipt を作ってから `ftruncate` し、その後に初めて [`signal-after-start` guard](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1207) が走ります。
- **攻撃シナリオ:**
  1. `build_start(v,A,R,h) → build_done(v,A,h)` を正常追記。
  2. verifier が RED を返し、[`verify_done` emit](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:877) が完全な JSON 本体まで書いたが、末尾 LF の直前で write/EIO/crash。WAL tail は「完全な `verify_done` JSON、ただし LF 無し」になる。
  3. resume で tail repair がその signal 全体を削除する。
  4. recovery は `verify_done` を見つけられず `abort(A, recovery-...)` を追記。
  5. retry attempt B が GREEN となり `commit(B)`。
- **成果物影響:** 差分前なら A が active のまま B の `build_start` が入り、topology が二重 start を拒否しました。差分後は A が recovery-abort で閉じられ、[`artifact_admission`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:640) が B の commit を含む campaign を受理できます。既に得られた RED signal が台帳から消え、同じ variant が certified 選択へ到達し得ます。
  
  さらに、newline 終端済み `verify_done` の後ろに無関係な torn bytes があるだけでも、repair が WAL と receipt を変更した後に guard が例外を出します。この場合も正本の「一 byte も書かない」を満たしません。
- **提案:** active attempt と truncated tail が併存するときは自動 repair/recovery せず、同じ WAL lock 内で raw tail を含めて事前判定し、書き込み前に停止してください。少なくとも「LF だけ欠けた `verify_done`/`bench_done`」と「valid signal + torn garbage」の二列をテストに追加すべきです。

### 2. 生存 evaluator の遅延 signal は topology が拒否せず、裁定の安全性説明が成立しない

- **severity:** blocker 候補
- **根拠:** recovery の `LOCK_EX` は scan から append の間だけです（[`wal.py:1159`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1159)）。一方、topology validator は `build_done`/`commit` と `abort` だけを attempt に束縛し、`verify_done`/`bench_done` は素通しします（[`wal.py:976`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:976)）。これは「peer の後続 record は loud に拒否される」という [`s4-ruling.md:27`](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s4-ruling.md:27) の根拠を崩します。
- **攻撃シナリオ:**
  1. P1: `build_start(v,A,R,h) → build_done(v,A,h)`、その後 verifier 実行中。
  2. P2: resume し、まだ signal が無いため `recovery-abort(A,h)` を追記。
  3. P1: RED の `verify_done(v,{certified:false, anomalies:1,...})` を追記し、自己の abort を書く前に kill。
  4. P3: active attempt は無い。`last_terminal` は recovery-abort のままなので [`retryable_abort`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/model.py:161) が真。
  5. B を再評価し、GREEN の `verify_done` と `commit(B)` を追記。
  
  最終列は `start A → build_done A → recovery-abort A → RED verify_done A → start B → build_done B → GREEN verify_done B → commit B`。現 validator はこれを受理します。
- **成果物影響:** artifact admission は RED signal と attempt の関係を検査しません。Layer3 の reject 判定も「variant に commit が無いこと」だけです（[`layer3_report.py:477`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/layer3_report.py:477)）。したがって同一 variant の既知 RED 後に certified commit が成立します。また critic の verify signal は variant 単位の先勝ちなので、A の signal が B に誤帰属します。
- **提案:** s4 の推奨どおり campaign-wide owner lease を導入するか、`verify_done`/`bench_done` に attempt ID と receipt SHA を束縛し、inactive/aborted attempt の signal を validator と全 consumer で拒否してください。少なくとも「resume は旧 evaluator 終了後」という未強制の運用前提だけでは、偽 certified が無いとは言えません。

### 3. recovery payload の exactness は生成時しか保証されず、受理側は余剰 key を通す

- **severity:** must-fix
- **根拠:** [`_recovery_abort_record`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1090) 自体は exact です。しかし [`_validate_attempt_topology` の abort 分岐](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1009) は attempt ID と receipt SHA しか見ず、key 集合を検査しません。artifact admission もこの validator の直呼びだけです。
- **攻撃シナリオ:** 正規の receiptful `build_start(v,A,R,h)` の後に、公開 writer または raw WAL で次を追記します。
  ```json
  {
    "reason": "recovery-abort-incomplete-attempt",
    "build_attempt_id": "A",
    "build_admission_receipt_sha256": "h",
    "build_admission": {"forged": "body"},
    "fitness_tps": 999999999,
    "verify": {"verdict": "G2", "anomalies": [{"forged": true}]}
  }
  ```
  topology と artifact admission はこれを受理し、reason により retryable にもなります。
- **成果物影響:** 受理集合に s4 が禁止した recovery payload が残ります。特に [`critic.load_rejections`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/critic/digest.py:232) は余剰 `verify` を本物の正しさ signal として次手へ渡すため、critic 入力、Layer3 の abort view、WAL SHA・参照が変わります。
- **提案:** `reason == INCOMPLETE_ATTEMPT_RECOVERY_REASON` の全 abort に対し、元 attempt が receiptless/receiptful のどちらかに応じた exact key 集合を共有 validator で強制してください。生成結果だけでなく、raw WAL → replay → artifact admission を通す負例が必要です。

### 4. recovery API 自体は post-policy campaign を要求していない

- **severity:** must-fix
- **根拠:** [`recover_interrupted_attempts`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1140) は `admission_policy` の型しか確認しません。`campaign.lock` は読みますが、欠落や `search_config.build_admission` 不在を拒否しません。production wrapper の [`ensure_campaign_identity`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/ident.py:214) は防ぎますが、公開 recovery API の直接呼び出しでは迂回できます。
- **攻撃シナリオ:** lock 無し、または pre-policy lock の WAL に receiptless `build_start(v,A,{"build_attempt_id":"A"})` を置き、current policy を渡して recovery を直接呼ぶ。trigger validation と topology validation は通り、abort が追記されます。
- **成果物影響:** identity/ownership 未照合の台帳 bytes と WAL SHA を変更できます。歴史的 snapshot と一致していた pre-policy campaign なら、その後の admission は snapshot/hash 不一致となり、既存参照が失効します。偽 certified には直結しませんが、exact な回復対象集合を越えた破壊的変更です。
- **提案:** recovery 内でも lock の `search_config.build_admission == admission_policy.as_preimage()` を必須化するか、identity 検証済み capability を受け取る private helper にしてください。lock 無し・legacy lock の byte-stable 負例を追加すべきです。

### 5. MU-7 は事前 topology 検査の byte 防壁を単一理由で pin していない

- **severity:** nit
- **根拠:** [`test_recovery_invalid_topology_and_multiple_active_are_byte_stable`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:932) は例外 condition と byte 不変を見ますが、事前検査を迂回しても [`prospective` 再検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1244) が同じ既存違反を append 前に拒否します。
- **攻撃シナリオ:** 事前 validator を非検証 projection に置換し、prospective validator は残す。bytes は変わらず、テストは主に condition 名の差で赤になります。
- **成果物影響:** production の受理集合は変わらず、現状は二重防御です。影響は変異主張の精度だけです。
- **提案:** s4 の F28 に従い MU-7 を取り下げるか、「既存違反 WAL に append が到達する」実効 gate へ再照準してください。

## 5 条件の到達性

以下では `R` は canonical receipt、`h` はその SHA、全 record は newline 終端済みとします。

| 条件 | 発火する具体的 record 列 | 実際に見る field |
|---|---|---|
| signal 後 | `build_start(v,A,R,h) → build_done(v,A,h) → verify_done(v,{verdict:...})`。`bench_done` でも同じ | start より後、`later.variant == v` かつ `later.stage ∈ {"verify_done","bench_done"}`。payload、attempt ID、env、ts は見ない |
| trigger | machine lock (`axis=silo-backoff-trigger-gating`, `generator=reason-subset-v1`, exact `space`) + active start。または `trigger_binding(A,B) → build_start(A,{trigger_gate_binding_commitment:c(B)})` | machine は lock の exact fields、proposal は start payload の commitment key。値は先行する binding validator が照合 |
| 上限 | 同じ variant で `start A0→recovery-abort A0` を3回、その後 `start A3` | `variant`、`stage=="abort"`、`payload.reason` の3項目を全履歴で数え、`>=3` |
| 既存 topology 違反 | `build_start(v,A,R,h) → build_done(v,A,sha="f"*64)` | 既存 `_validate_attempt_topology` の receipt SHA 不一致 |
| 複数 active | `build_start(v,A) → build_start(v,B)` | `_active_attempt_candidates` が同一 `variant` の EOF-active ID 数を数え、2件で拒否 |

5 条件とも恒真ではありません。in-scope の実 emitter は bench を [`pipeline.py:452`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:452)、verify を [`pipeline.py:877`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:877) の stage 名で出しており、別 stage 名の漏れは見つかりませんでした。guided の schema-free pseudo-WAL と S8b oracle は s4 の明示的 scope 外です。

## 攻撃したが破れなかった箇所

- **direct recovery の byte 不変:** 上記所見1の上位 tail-repair 経路を除けば、5 guard、既存 topology、prospective topology の例外はすべて最初の `os.write` より前です。通常の active WAL で lock が欠落していれば identity gate が lock 作成前に拒否するため、lock 作成も走りません。
- **原子性:** `LOCK_EX` は `wal.py:1159` で取得され、scan、両検査、`_append_records_locked`、fd close まで同一区間です。append helper は `wal.append` を再呼び出さず直接 `os.write` するため、同一 process の二重 flock はありません。二重 recovery は直列化されています。ただし owner/evaluator 排他は所見2のとおりありません。
- **生成される payload:** helper から生成される receiptless/receiptful payload は exact で、SHA は `attempt.receipt_sha256 is not None` の場合だけ伝播し、variant/env は元 start を再利用しています。破れたのは受理側です。
- **5 entry point:** s6、s8a、p3 backoff、sort、trigger-gating の全5箇所に配線されています。p3 3系統はいずれも state load、`check_stop`、checkpoint、provenance より前です。
- **変更禁止箇所:** パッチには `pipeline.py` と `artifact_admission.py` の hunk がなく、`wal._validate_attempt_topology` と `wal.replay` の既存行にも変更はありません。`wal.replay` の trigger orphan tombstone 書き込みも従来どおり残っています。
- **schema 判別:** 4 key のいずれかが任意 record にあれば strict validator に入り、全く無ければ append せず no-op です。
- **規律2/3:** verifier gate、start emit、正しさ signal の生成位置自体は緩められていません。ただし所見1・2は既得 RED の消失/誤帰属、所見3は偽 signal の注入を許すため、差分全体としては規律2/3を守ったとは判定できません。

## 新たに増えた受理

意図どおり増えたのは、post-policy・非 trigger・signal 前・上限未満・variant ごと active 1件の列です。receiptless/receiptful、および複数 variant 各1件を一括して閉じた後の retry/commit が受理されます。recovery reason の追加により、その abort は permanent skip ではなく再評価対象になります。

意図外または正本の説明を越える受理は次の4つです。

- truncated tail に隠れた verify/bench signal を削除した後の回復。
- recovery と生存 evaluator の間に遅延 signal が入る列。
- recovery reason を持つ余剰-key abort。
- post-policy lock を持たない WAL に対する recovery API の直接適用。

pytest は実行しておらず、テストの緑は主張しません。

## 総括

- blocker 候補は **2件**あります。
- tail repair が guard より先に signal を消し、以前は拒否された campaign を certified 可能にします。
- owner lease 不在時の遅延 signal は topology が loud に拒否せず、s4 の安全性説明を反証します。
- exact payload と post-policy 限定にも must-fix が各1件あります。
- direct recovery の5 guard、同一 `LOCK_EX` 区間、生成 payload、5入口配線自体は静的に確認できました。
- pytest は未実施です。
- 判定は **NO-GO** です。