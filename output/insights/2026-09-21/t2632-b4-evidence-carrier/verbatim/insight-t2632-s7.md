## 7. 裁定パッケージ (ユーザーへ返す。本 wave では何も実装しない)

**既裁定で閉じる (返さない):** 少数の赤の扱いは記述報告まで (D1986 項 4)。母集合を作るための追加基盤は採らない (D1936 項 8)。
`bootstrap_member` を batch 所属で真にしない (D2100)。bootstrap 集合は非空入力が出るまで定義しない (D2120 項 5 (2))。§5 の 2 欄の
順序 (D1483)。

**返す:**

1. **辺 A の耐久 carrier。** 択一 —
   - (α) **base driver に、trigger driver と同型の harness 書き side channel を足す** (`reports/<driver>_provenance.json`、iteration ごと、
     `save_loop_state` より前)。持たせる最小 field = `iteration`、`variant` (certified / fail は `pipeline.variant_id`、reject は `diffq-*`)、
     `build_attempt_id`、`initial_proposal_sha256` (= `canonical_b4_proposal_sha256(document)`、harness が読んだ bytes から計算)、
     `wal_refs` (その attempt の record の canonical hash)、`outcome`。**whiteboard の 5 field は不変で、D39 決定 3 に触れない**
     (planner へ射影する `project_whiteboard` は side channel を読まない)。重複解決 (`_resolve_duplicate`) と dry-pass も行を残す
     (§7.1 の全件報告と整合)。
   - (β) D39 決定 3 を改訂し、`WhiteboardEntry` に不透明な `variant` / `proposal_sha256` を足す。planner 射影から除けば structural
     inference の経路は増えないが、凍結された型 (D1846、5 field) と、その型を読む consumer が動く (`p3_b4_prerun_caller` 自身は
     `{iteration, result}` の部分集合検査なので壊れないが、`project_whiteboard` の射影規則は D39 決定 3 の改訂として書き直しになる)。
   - (γ) opt-in journal (`--agent-inputs`) を B-4 marker 走行で必須化し、live envelope に canonical hash と variant を足す。live 経路は
     評価前に書くため variant を持てず、2 record transaction でない (docstring) ので、単独では (α) の代替にならない。

   - (δ) trigger 系列の先例 (§2.2: bounded supervisor の `proposals/` 保存 + `autonomous_trial_completeness` の照合、trigger driver の
     source-preimage) を base driver へ移植する。proposal document の保存と raw hash の束縛は既にある形だが、supervisor は trigger 軸専用
     (「generic evolution daemon ではない」と自ら限定) で運用記録の位置付け、source-preimage は proposal JSON でなく materialized source の
     preimage、いずれも B-4 の canonical identity を持たない。移植するなら (α) の field を足すことになり、(α) と独立の択ではない。

   **推奨: (α)。** 理由 — 既存の先例 2 つ (trigger driver の provenance side channel = harness 書き、trigger 系列 supervisor の proposal 保存 +
   completeness 照合) が動いており、凍結型と leak 防壁に触れず、赤 precursor (`diffq-*`) も同じ形で残せる。**不足は carrier の発明ではなく、
   base への接続と B-4 canonical identity (`canonical_b4_proposal_sha256`) の束縛の追加である。** 実装は Codex author の別 wave (実装面)。
   D2100 の「走査 framework・sidecar 入力・ID 規約・耐久 carrier・resolver は作らない」は呼び手の責務の限定であり、driver 側 carrier の
   新設を禁じてはいない — ただし D1936 項 8 との線引き (母集合を**作る**基盤ではなく、出た precursor を**結ぶ**記録) を裁定文に書く。
2. **辺 B の定義。** 3 点とも事前登録 §5.1.1 の**解釈の確定**であり、複数の読みがあることを隠さず択一で返す。値の凍結は §5 の順序 (D1483) に従う。
   - (i) `reference_snapshot_hash` / `reference_receipt_hash` の実体 — 推奨: snapshot = 祖先 certified attempt の WAL `commit` record、
     receipt = 同 `bench_done` record とし、hash は record の canonical JSON の sha256 (64 hex)。**canonicalization は 1 つを名指す** —
     推奨は `agent_outputs.canonical_bytes` (`allow_nan=False`、非有限値を拒否)。`layer3_report._canonical_bytes` は現物で同じ bytes を
     出すが `allow_nan` を指定しないので、定義には採らない (§4.1)。新 object・新 producer を作らない。
   - (ii) 祖先関係 — **未確定で、少なくとも 3 つの読みがある**: ① 同一 campaign 内の時間順 (precursor の iteration より前の whiteboard 行の
     うち最後の `success` に対応する attempt を、裁定 1 の side channel の `iteration` → `variant` で引く)、② proposal が派生した入力
     snapshot の系譜 (planner / coder が読んだ whiteboard・digest の版から遡る)、③ campaign をまたぐ明示的な parent 系譜 (現行に
     記録は無い)。推奨は ①。ただし ① でも、祖先が無い・同着の複数候補・`PerfConfig` / `env_tag` 不一致は §5.1.1 どおり不適格
     (`design_not_feasible` / protocol violation) とし、別基準へ切り替えない。重複提案は新しい評価を作らないので、行順と評価の系譜が
     同一でないことを ① の定義文に書く。
   - (iii) `PerfConfig` / `env_tag` の一致 — **承認された `PerfConfig` の全 field (records / threads / workload の全 key (`ycsb_max_ope` を
     含む) / extime / reps) と `env_tag` の一致を、出所を名指して確認する。** `bench_done.run_cmd` と record の `env_tag` で確認できるのは
     threads・records・extime・workload 3 key・env_tag までで、`reps` と `ycsb_max_ope` は run_cmd から確認できないため、不足として残し
     部分一致を全体一致と呼ばない (D2150 項 2 の 3 種の出所と同じ区別)。
3. **順序。** 裁定 1・2 は §5 の 2 欄 (D1483) と独立に決められるが、carrier の実装と定義の発効は、B-4 の供給源となる新規 base campaign
   (前 wave の順序 (3)) の**起動前**に要る。起動後に足すと、その campaign の precursor は辺 A を欠いたまま残る (遡及で埋めない — 規律 7)。
4. **D2100 呼び手の lock 読取りの局所修正 (§2.3)。** `p3_b4_prerun_caller` が top-level `trial` を読む点を、既存 codec
   (`campaign_lock.decode_campaign_lock`) 経由の `trial` 読取りへ直すか。推奨: 直す (D2120 の「防壁は既存契約の欠陥だけを局所修正」
   と同型。受理形を v1 / v2 の両方に広げるのではなく、codec が受理する形だけにする)。放置すると、現行形式で走った新規 base campaign は
   赤 precursor が出ても D2100 の「不足報告 + 空 batch 到達」に乗らない。実装は Codex author の別 wave、test の lock fixture も v2 形へ。
