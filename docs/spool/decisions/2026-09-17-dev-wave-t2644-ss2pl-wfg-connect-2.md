---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2644-ss2pl-wfg-connect
seq: 2
---

## {{D:ss2pl-wfg-transport-and-mode}}. SS2PL 待ちグラフ計器は標準出力の 1 行 event を一次伝達とし、mode は実 lock mode で出し、検証器の述語は変えない

**決定:** D791 の証拠を採る計器 (`patches/ss2pl-lock-protocol-study.patch` の `wfg.cc`) と runner の検証器
(`tools/pegasus/run_ss2pl_lock_study.py` の `validate_deadlock_evidence`) の接続は次の形にする。

1. 計器は閉路の立った watchdog tick ごとに、検証器の要求形 (`ss2pl-wfg/v2`: `nodes[thread_id, attempt,
   wait_lock_id, request_mode, commit_count, abort_count, held_locks[{lock_id, mode}]]`、
   `edges[waiter_thread_id, holder_thread_id, lock_id, request_mode, holder_mode, compatible:false]`、`tick`)
   の compact 1 行 JSON を標準出力へ出す。書き込みは `cout_mutex` と `flockfile(stdout)` の中で `fwrite` 1 回 +
   `fflush`。durable file には最後に emit した同じ文字列を書く (副次成果物であり、受理条件にも代用証拠にもしない)。
2. `held_locks` は同一 snapshot 内のその worker の保持一覧全件。`holder_holds_lock` のような自己申告 boolean は出さない。
   holder の保持一覧に無い辺は出さない。
3. mode は実 lock mode で出す: `SS2PL_LOCK_IMPL=1 && SS2PL_LOCK_KIND=0` (study lock の排他版) では全箇所 `write`、
   それ以外は既存の read / write。取得 counter の分類は変えない。
4. hang して kill される走行でも build 軸を読めるよう、YCSB main は `chkArg()` 直後に `#if SS2PL_WFG_DIAG` の中で
   `ShowOptParameters()` を呼ぶ。追加はすべて `wfg.cc` か `#if SS2PL_WFG_DIAG` の内側に置く。
5. runner の `_run_phase_trial` は trial ごとの directory に `-ss2pl_wfg_output=` を渡し、生の stdout / stderr と
   durable file を保全して受領証に残す。`validate_deadlock_evidence` / `_extract_snapshots` / `_holder_evidence` /
   `_edge_is_incompatible` / `_admit_output` は変えない。tick の連続性検査は検証器に足さない。
6. 条件 3 (counter 不変) は計器が attempt 開始時に写した値で判定され、attempt 不変と冗長である。この冗長性は
   受領証の説明に明記し、実更新時の同期は行わない。

**理由:**
- 標準出力 event は runner の既存経路 (`_json_events` → `_extract_snapshots`) をそのまま使え、SIGTERM / SIGKILL の後も
  flush 済み行は `communicate()` が回収する。file を一次にすると runner 側の受理経路を作り直すことになる。
- 排他 lock は `writer_` に格納する 1 種の mode しか持たない。read 操作を `read` と出すと検証器の
  `_edge_is_incompatible` が read/read を両立と判定し、実閉路を拒否する。計器側の表現を実 lock mode に合わせれば
  検証器 (規律 2 の権威) を触らずに済む。
- `held_locks` は registry の写しで独立観測源ではないが、辺との照合と非両立の再導出を検証器に残すことで、boolean の
  自己申告より偽りにくい。
- 計算ノード 1 走 (高競合点、48 threads、hard timeout 60 秒) で、この形のまま production 経路が 2 node 閉路を 3 snapshot で
  受理した (`output/insights/2026-09-17/t2644-ss2pl-wfg-connect/README.md`)。

**却下した選択肢:**
- **durable file を一次伝達にする:** runner の受理経路を file 読取りへ作り直す必要があり、hang して kill された走行では
  file の有無が受理条件へ紛れ込む。
- **field 名を検証器側で計器に合わせる:** 検証器は既存 test 3 件の権威であり、`holder_holds_lock` の boolean 枝を残す限り
  自己申告が受理される形が残る。
- **検証器に tick 連続性検査を足す:** 受理形の変更であり、本題の接続の外。phase1 (排他 + wait) では閉路が消えて
  同じ signature で再出現する経路が構成できないことを論証で担保した。
- **counter を実更新時に同期する:** 本題の接続の外。watchdog から非 atomic な counter を無同期に読む設計を招く。
