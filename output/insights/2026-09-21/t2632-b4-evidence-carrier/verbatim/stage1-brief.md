# [T-2632] 段 1 brief (2026-09-21 17:45 JST 確定 = file mtime、起点 local main `5f48a298a`、branch `worktree-dev-wave-t2632-b4-evidence-carrier`)

**研究前進:** B-4 (critic 還流 ablation) の適格行は、赤 precursor の proposal・走行・参照点を harness 記録で結べないため 0 行しか作れない
(一次資料 `output/insights/2026-09-20/t2632-b4-evidence-provenance/README.md` §7、D2100 の 12 field)。本 wave は base driver にその記録を足し、
caller が現行形式の campaign を読めるようにする。完了判定 = 新規 base campaign の各 iteration が harness 書きの 1 行を残し、v2 lock の campaign が
caller の「不足報告 + 空 batch 到達」に乗る。土台であり、B-4 本走・床値 w2 は投入しない。

**確定済みユーザー裁定:** D2194 項 3 (1)〜(4) (控え = rulings-inbox 2026-09-21 項 3)。D2120 項 5 (2) (bootstrap 集合は定義しない)。D39 決定 3・D1846 (whiteboard 5 field)。

**scope:** (1) side channel、(2) 参照点の定義の確定、(3) 順序 (本 wave の land をもって新規 base campaign 起動前を満たす)、(4) caller の codec 経由化。これ以外 (gate・台帳・一般化・admission 検査・sort / trigger への展開) は scope 外。

**不変条件:** whiteboard 5 field と planner 射影 (`project_whiteboard` / `whiteboard_for_planner`) は不変。規律 2 (anomaly は即 reject) は不変。
新 object・新 producer は作らない (D2194 項 3 (2)(i))。凍結された事前登録本文は編集しない (§5 の projection hash 欄は `未記入` を実測、陳腐化する値なし)。
caller は codec が受理する形だけを読む (v1 / v2 の独自救済分岐を足さない)。

**変更面 (実アンカー、main `5f48a298a`):**

| file | anchor | 変更 |
|---|---|---|
| `orchestrator/campaign/p3_s4_loop.py` | `drive_iteration` の `out = _run_one_iteration_resolved(...)` 直後、`save_loop_state(layout, state)` の直前 | entry を書く |
| 同 | `main()` の `--run-iteration` 経路、`load_proposal_file(...)` の直後 | 読んだ document の canonical hash を `drive_iteration` へ渡す |
| 同 | 新規 helper (先例 = `p3_s4_loop_trigger_gating._provenance_path` / `_load_provenance` / `_write_provenance` / `_append_provenance_entry` / `_wal_attempt_provenance`) | `reports/p3_s4_loop_provenance.json` の atomic merge 書き |
| `orchestrator/campaign/p3_b4_prerun_caller.py` | `collect_scheduled_batch` の `lock = json.loads(...)` / `lock.get("trial")` | `campaign_lock.decode_campaign_lock_bytes` → `decoded.identity["trial"]` |
| `orchestrator/tests/test_p3_s4_loop.py`・`test_p3_b4_prerun_caller.py` | 新 test、`_campaign` fixture を v2 (`campaign_lock_test_support.build_v2_campaign_lock`) へ | test |

**割れうる前提 (親の provisional 裁定・段 3 の攻撃対象):**
- (P1) 参照点の定義 (2) は記録 (insight・decisions fragment) と side channel の docstring で確定し、resolver は作らない。
- (P2) 書き手は base driver だけ (DW-G03)。sort / trigger へは展開しない。
- (P3) entry は B-4 mode 以外の走行でも書く。`initial_proposal_sha256` は `canonical_b4_proposal_sha256(document)` を使う (receipt key を除いた canonical JSON)。
- (P4) 書けない・壊れているときは fail-closed (先例どおり `.corrupt.<epoch>` へ退避して停止、`save_loop_state` は進めない)。
- (P5) stock 対照 (`--stock-control`、pair mode の後段) と入口停止 (`stopped-before`) は entry を書かない (iteration を消費しない)。dry-pass・duplicate・duplicate-skip・rejected は書く。
- (P6) `wal_refs` = 当該 variant の WAL record のうち当該 `build_attempt_id` に属するものの `wal:<agent_outputs.canonical_sha256>`。duplicate は再利用した既存 attempt を指す。
- (P7) 依頼文は先例を `_write_source_preimage_artifact` と名指すが、同関数の出力は `source-bindings/<proposal raw sha256>.preimage` で、
  D2194 項 3 が指す `reports/<driver>_provenance.json` の先例は `_provenance_path` / `_append_provenance_entry` 系である (F31: 裁定優先)。
  親の読み = file の意味 (path・field・iteration key の merge) は `_append_provenance_entry` 系、書き込みの堅さ (fsync・atomic 公開・冪等) は
  `_write_source_preimage_artifact` 系に合わせる。base に source preimage artifact は足さない (field 一覧に無い)。

**実測済みの事実:** 実物 v2 lock (B-5 試走 10 件、例 `p3-s4-loop-s4-autonomous-6fc5d263`) は top-level に `trial` を持たず、identity 内 `trial = "p3-s4-loop"`
(jq 実測)。`reports/` は既存 campaign で空。`p3_s4_loop.py` は contract loader closure (85 path) と B-4 projection closure に入る →
未 commit の注入で 114 node が内容と無関係に落ちる ([T-2795] insight §5)。変異は drift node 除外の注入群 + 独立 clone の commit 群で組む。

**成果物の形:** 実装 2 file + test 2 file、変異 matrix (事前登録 → probe → final)、insight (brief・相談・裁定・変異・受入の逐語)、worklog / decisions fragment。

**分割 (段 5):** 子 A = side channel (`p3_s4_loop.py` + `test_p3_s4_loop.py`)、子 B = caller (`p3_b4_prerun_caller.py` + `test_p3_b4_prerun_caller.py`)。file が交わらないので並列。

**受入・実測環境:** Pegasus login (読み取り・self-run) + 計算ノード dispatch (焦点走・変異・受入、`tools/dev_wave_wait.py acceptance --lease-optional`)。
