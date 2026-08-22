---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t1447-orphan-hold-races
seq: 2
---

## {{D:orphan-hold-pending-eager-arm}}. dispatch_compute.pyのorphan-hold latchをqsub直前のpending作成+原子的promotionへ再設計する

**決定:** `orphan-hold.json` を qsub 呼出しの直前に `phase: "pending-qsub"` で create-only
書込みし (`_arm_pending_orphan_hold`)、正常終了時に削除 (`_release_pending_orphan_hold`)、
異常終了時に最終形へ原子的に昇格する (`_promote_pending_orphan_hold`、temp file
書込み→fsync→`os.replace`)。hold操作 (create/promote/release) の失敗は専用例外
`_OrphanHoldError` として fail-closed に伝播させ、`_write_json_x` (create-only のみ) が
握り潰していた OSError を全経路で除去する。

**理由:**
- 外部SIGKILL (`check_acceptance_reds.py`の`subprocess.run(timeout=5100)`等) は dispatcher
  プロセス自身のPython例外処理・signalハンドラを一切経由せず即座にプロセスを終了させるため、
  「cleanup完了時にだけholdを作る」設計では原理的に防げない窓が生じる。危険な状態
  (qsub成功=jobがscheduler上に実在) に入る**前**にholdを作っておけば、SIGKILLのタイミングに
  関わらず窓がほぼゼロになる。
- hold書込み失敗を`None`で返し呼び出し元が戻り値を見ない設計は、checker側
  (`_orphan_hold_present`) が「書込み失敗」と「hold不要」を区別できずfail-openになる
  (repro再現で実証)。例外化して伝播させることで、この区別を構造的に強制する。
- qdel rc=0は「scheduler が取消要求を受理した」ことしか意味せず (docstring自身が明記)、
  対象jobの実際の終端は別途qstatで確認しないと分からない。既存のqstat分類helperを
  再利用したpost-qdel確認を追加し、qdelは再発行しない (F47 latch武装回避)。

**却下した選択肢:**
- `_DISPATCH_TIMEOUT_SECONDS`等、呼び出し元のtimeout marginを広げる — scope
  (`tools/pegasus/dispatch_compute.py`単体) を超え、margin は窓を狭めるだけで閉じない。
- SIGKILL自体を捕捉する設計 — OSレベルで不可能。dev_wave_wait.pyの既存コメント
  「SIGKILLとhost停止はunwind不能」と同じ限界を継承する前提とした。
- pending holdを`orphan-hold.json`と別名のマーカーにする案 — checker側
  (`_orphan_hold_present`)の変更が必須になり、scope外のファイルへ波及する。
