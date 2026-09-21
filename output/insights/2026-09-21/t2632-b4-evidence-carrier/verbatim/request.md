# 依頼の逐語 (/dev-wave の引数、2026-09-21 08:20 JST ごろ受領)

[T-2632] (D2120 項 5、D2194 項 3、控え /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full27-verdicts.md 項
  3、Codex author) B-4 の対応証拠 4 項を実装する。一次資料 output/insights/2026-09-20/t2632-b4-evidence-provenance/README.md §7。(1) base
  driver (orchestrator/campaign/p3_s4_loop.py、silo-backoff-magnitude) に trigger driver
  (p3_s4_loop_trigger_gating._write_source_preimage_artifact) と同型の harness 書き side channel (reports/<driver>_provenance.json: iteration /
  variant / build_attempt_id / canonical_b4_proposal_sha256 / wal_refs / outcome。whiteboard 5 field と D39 決定 3 は不変)、(2) 参照点 = 祖先
  certified attempt の WAL commit / bench_done record の canonical sha256 (agent_outputs.canonical_bytes)、祖先 = 同一 campaign
  内の時間順、PerfConfig は全 field 一致を出所名指しで確認 (reps / ycsb_max_ope は不足として残す)、(3) carrier と定義は新規 base campaign
  の起動前、(4) orchestrator/campaign/p3_b4_prerun_caller.py の trial 読取りを既存 codec campaign_lock.decode_campaign_lock 経由へ (test の
  lock fixture も v2 形へ)。変異 matrix 込み。bootstrap 集合は非空入力が出るまで定義しない。着手条件 = [T-2795] と [T-2830] が main に land
  済み (同 p3_s4_loop.py を編集する)。land 前なら段 1 で待ち、その land を含む local main から fresh worktree を作り直す。B-4 本走・床値 w2
  (2026-09-29 以降) は投入しない。規律 2 を緩めない。本題だけ。gate・台帳・一般化の追加は scope 外。
