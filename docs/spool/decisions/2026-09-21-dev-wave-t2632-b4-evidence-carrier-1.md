---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-t2632-b4-evidence-carrier
seq: 1
---

## {{D:b4-base-provenance-carrier}}. B-4 の対応証拠の carrier は base driver の iteration keyed side channel とし、参照点の定義は docstring と記録で確定する。中断時の保証は「公開できない iteration を checkpoint に確定しない」だけにする

**決定:** D2194 項 3 の実装形として次を採る。

1. **carrier:** `orchestrator/campaign/p3_s4_loop.py` が `<campaign root>/reports/p3_s4_loop_provenance.json` に iteration ごとの entry
   (`iteration` / `variant` / `build_attempt_id` / `initial_proposal_sha256` / `wal_refs` / `outcome` の 6 field ちょうど) を、評価と whiteboard 射影の後・
   `save_loop_state` の前に書く。file の意味 (path・iteration key の上書き merge) は trigger driver の `_append_provenance_entry` 系、書き込みの堅さ
   (排他 tmp・fsync・atomic 公開・directory fsync) は `_write_source_preimage_artifact` 系に合わせる。base に source preimage artifact は足さない。
   stock 対照と入口停止は iteration を消費しないので書かない。dry-pass・duplicate・duplicate-skip・rejected は書く。
2. **束縛:** `initial_proposal_sha256` は `load_proposal_file` が読んで検証した document の `canonical_b4_proposal_sha256`。canonical 化できない
   proposal は mode を問わず null で走行を続ける (canonical hash を既に要求するのは B-4 bootstrap の registry 束縛だけで、他の経路で止めると受理集合が縮む)。
   `wal_refs` は当該 variant かつ当該 `build_attempt_id` の WAL record 全体の `agent_outputs.canonical_sha256`。certified / duplicate / rejected で
   attempt を特定できないときは記録不能として停止する (証拠不足を別 attempt で救済しない)。
3. **評価前の検証:** layout が決まった直後、B-4 認可の検査・消費と評価より前に既存 report を読み検証する。破損は元 bytes を退避して停止し、
   1 回限りの B-4 認可を消費しない。
4. **保証の限界:** 保証は「provenance を公開できない iteration は checkpoint に確定しない」だけとし、中断後の経路別帰結 (非 B-4 certified は
   duplicate になり得る / 検疫 reject は新 attempt で entry が上書きされ旧 attempt は WAL にだけ残る / WAL 履歴のある B-4 は再実行を拒否し
   公開済み entry が残る) を docstring に書く。「回復可能」「対応を失わない」とは主張しない。
5. **参照点の定義 (事前登録 §5.1.1 の解釈の確定):** 祖先 = 同一 campaign 内の時間順 (precursor の iteration より前の最後の whiteboard `success` に
   対応する certified attempt を本 carrier で引く)。`reference_snapshot_hash` / `reference_receipt_hash` = その attempt の WAL `commit` / `bench_done`
   record 全体の `agent_outputs.canonical_bytes` の sha256。祖先なし・同着・record 非一意・`PerfConfig` / `env_tag` の一致を確認できないときは不適格で、
   別基準へ切り替えない。`reps` と `ycsb_max_ope` は run_cmd で確認できない不足として残す。定義は `_wal_attempt_provenance` の docstring と
   本決定に置き、resolver・新 object・`reference` 欄は作らない。凍結された事前登録本文は編集しない。
6. **caller:** `p3_b4_prerun_caller` は lock を `campaign_lock.decode_campaign_lock_bytes` で読み `decoded.identity.get("trial")` を使う。受理は
   有効な v2 へ広がり、旧 `json.loads` が受理していた不正な v1 (duplicate key・非有限値・reserved field) は拒否へ移る。独自の救済分岐は足さない。

**理由:**

- 先例 2 つが動いており、凍結型 (D1846) と leak 防壁 (D39 決定 3) に触れない (D2194 項 3 の理由どおり)。whiteboard の 5 field と planner / coder /
  critic の入力 bytes が report の有無・内容で変わらないことを test で固定した。
- 評価前の検証は、B-4 continuation の receipt を消費した後に破損で止まると、その 1 回限りの認可を失うため (段 3 相談 A)。
- 保証の限定は、段 3 相談 A と段 6 レビュー A が、検疫 reject の再実行・B-4 の再実行拒否・bootstrap の WAL 不在で「回復可能」が成り立たない経路を
  示したため。
- hash 失敗の null 化は、段 6 レビュー A が非 B-4 / B-5 slot の過剰拒否 (rc=3 sidecar を経由しない停止) を示したため。

**却下した選択肢:**

- 同 iteration の差分がある再書込みを拒否する (source preimage 型) — 中断後の正当な再評価 (certified → duplicate) を塞ぐ。
- entry を append-only の列にする — 対応は失わないが trigger 同型から外れ、D2194 項 3 の「iteration ごと」の形を変える。本 wave では採らず、
  上書きで失われ得る対応は WAL に残ることを docstring に書いた。
- side channel に `reference` 欄を持たせる — D2194 項 3 (1) の field 列挙に無く、定義 (項 3 (2)) は既存 field から引ける (段 3 相談 B)。
- base の provenance を admission が検査する — 依頼と D2194 の「gate を足さない」の外 (scope 外、起票しない)。
- B-4 mode だけ hash 失敗で停止する — B-4 continuation は canonical hash を要求しておらず、受理集合が縮む。

**変異:** commit 群 (変異を commit として焼いて contract loader の drift を避ける自作 harness、段 6 裁定 §5 で走行前に登録) S1・S2・S10〜S15 の
8 件、注入群 S3〜S9 と E1 (等価対照)、caller の C1〜C5 (結果は insight §6)。

**研究状態への影響:** 新規 base campaign から赤 precursor が出たとき、proposal・attempt・参照点候補を harness の記録で辿れるようになる。
適格行・certified 判定・台帳の値は本決定では変わらない (caller の不足報告は候補 1 件につき 12 件のまま)。B-4 本走・床値は未投入。
