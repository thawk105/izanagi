# 段 6 fix 裁定 — 敵対レビュー 2 本の所見処理

裁定時刻 2026-08-16 15:35 JST。統合 snapshot = `s5-snapshot.patch` (54,700 bytes)。

## 裁定表

| 出所 | 所見 | 判定 | 処理 |
|---|---|---|---|
| A-1 / B-1 | hold 書込み失敗 (inode 作成前) を層 2 が独立に塞げず、非 timeout 経路で source が復元される | **real** | **must-fix 1** |
| A-2 | `qsub_result_unknown` が非永続。discovery 中の再 signal / SIGKILL で hold 到達前に終了しうる | **real** | **must-fix 2 (順序入替のみ)** + 残余は scope 外として明記 |
| A-3 | `_apply_mutation` の `finally` が本体例外を握り潰し、停止 ledger から故障原因が消える | **real** | **must-fix 3** |
| B-5 | orphan-stop が通常 ledger を `--out` で上書きし、案内される `--resume` が schema mismatch で必ず rc=2 になる | **real** | **must-fix 4** |
| A-5 / B-2 / B-3 | 新設テストが配線を証明せず、事前登録 P1 が 5 detector を 1 変異にまとめている | **real** | **must-fix 5** |
| A-7 / B-4 | 既知の赤は別 output root への隔離で直す (期待値緩和ではない) | **real** | **must-fix 6** |
| A-4 | 署名の return 網羅性 | **refuted** | 単純署名を維持 |
| A-6 / B-6 / B-8 | F47・通常完走・local・非 timeout PARSE_ERROR の受理集合、consumer schema/rc、repo scan | **refuted** | 変更しない |
| A-8 | 既存 hold の lstat / symlink / 部分書込み検査 | **refuted** | 維持。ただし判定不能の注入テストを must-fix 5 で足す |
| B-7 | fan-out 上位 report が hold 理由と request ID を出さない | **real** | **nit / backlog**。成果物の値は変わらず復旧時間だけ延びる (DW-G05 を書けないので must-fix にしない)。`tools/mutation_fanout.py` は本 wave の所有外 |
| B-9 | runbook 更新が必要 | **real** | 段 7 で親が書く (節割りは B-9 の一覧に従う) |
| B-10 | false positive の頻度と停止範囲 | **refuted** | 署名は緩めない。発生条件を段 7 へ記録する |

## must-fix (実装子へ渡す)

### must-fix 1 — hold 書込み失敗を層 2 が独立に検出する

- `tools/mutation_harness.py` の `_read_dispatch_stdout` は既に receipt JSON を読んでいる。
  そこから **`qdel.job_may_remain`** と **`qdel.hold_error`** を権威ある値として result へ載せる。
- `_dispatch_orphan_stop` の孤児条件へ次を追加する。
  「dispatch mode の attempt で、receipt 由来の `job_may_remain is True`、
   または `hold_error` が非 None」→ 孤児条件。
  このとき hold file が無ければ harness 自身が create-only で立てる (既存 timeout 経路と同じ)。
- 統合テストを追加する: dispatcher の hold 書込みを失敗させ、harness が
  **復元せず・次の変異へ進まず・停止記録を書いて rc=2** で終わることを、
  helper 直呼びでなく production 経路で固定する。

### must-fix 2 — qsub 結果未観測経路で hold を先に立てる

- `_dispatch_impl` の例外経路 `qsub_result_unknown` 分岐で、**`_latch_orphan_hold` を
  `_discover_request_id` より前に呼ぶ**。request ID は補助情報として、判明したら receipt へ追記する。
  (hold record 自身の `request_id` が `None` になるのは許容する。)
- **残余として明記する (scope 外)。** `qsub_result_unknown` は依然メモリ上の状態なので、
  SIGKILL や discovery 中の再 signal では hold 到達前に終了しうる。qsub 前の永続 claim は
  解決 (削除) 経路を新設することになり、その経路の欠陥が全 dispatch を恒久停止させる危険があるため
  本 wave では実装しない。**「この窓を閉じた」と主張してはならない。**

### must-fix 3 — 元例外を保存する

- `_apply_mutation` は `except BaseException as exc` で元例外を保持し、
  `OrphanHoldStop` の構造化 field (`origin_error_type` / `origin_error_message`) へ保存して
  `raise stop from exc` とする。
- `finally` 内の検証 (`_assert_only_expected_dirt` / `_assert_head` / 変異 bytes 再読) が失敗した場合も、
  元例外を置換せず併記する。
- 停止記録に上記 field を含める。

### must-fix 4 — 停止記録を通常 ledger と別 file にする

- orphan-stop 記録は `--out` を上書きせず、**`<out>.orphan-stop.json` (別 path)** へ書く。
  `--out` の通常 ledger v4 はその時点の内容 (collection / baseline / 完了済み mutation) をそのまま残す。
- したがって `partial_ledger` の埋め込みは不要になる。停止記録は
  `ledger_path` で通常 ledger を指すだけにする。
- `tools/mutation_worktree.py` が hold 保全時に表示する案内は、
  **復旧順序を先に出し、`--resume` は hold を解除した後にだけ有効**であると明示する。
  resume loader の契約は変更しない。

### must-fix 5 — 検出力を配線ごと証明する

次を追加する。既存テストの期待値は 1 行も変えない。

- **配線テスト**: `claim_cleanup_once` の `finally` から latch 呼出しを削除すると赤になるテスト
  (helper 直呼びではなく `_dispatch_impl` を通す)。
- **判定不能の注入**: 4 consumer (`dispatch_compute` / `mutation_harness` / `mutation_worktree` /
  `check_acceptance_reds`) の `lstat` が `OSError` を返す場合に hold 成立側へ倒れることを、
  それぞれ 1 本ずつ固定する (通常 file と不在だけでなく)。
- **`_cleanup_dispatch_artifacts` の gate** を消すと赤になるテスト (現状 M9 は `_cleanup_probe` のみ)。
- assert 対象は診断文字列ではなく「変異 bytes 保持」「次 runner 呼出し 0 回」「container 存在」
  「非終端 stop 記録の存在」「scheduler command 0 本」にする。

### must-fix 6 — 既知の赤を fixture 隔離で直す

- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_nonzero_qstat_run_stdout_does_not_restart_deadline`
  の 2 回の `_dispatch` へ**別々の output root** を与える。**assert は 1 行も変えない。**
- 同一 root 複数 dispatch の他 2 件
  (`test_m6_qstat_success_without_request_skips_qdel_and_create_only_latches`、
   `test_f47_latch_precedes_orphan_hold_and_hold_remains_independent`) は
  「2 回目が止まること自体が目的」なので**変更しない**。

## 変異事前登録の改訂 (DW-M01 / DW-M08)

段 4 の M1〜M9 は維持し、次を追加・分割する。

| id | 変異 | 期待 |
|---|---|---|
| M10 | `claim_cleanup_once` の `finally` から `_latch_orphan_hold` 呼出しを削除 | KILLED |
| M11 | consumer の `lstat` `OSError` を「不在」扱いへ倒す (4 面のうち dispatch 側 1 面) | KILLED |
| M12 | dispatcher の hold 書込み失敗を harness が無視するよう戻す (must-fix 1 の削除) | KILLED |
| P1a | `_orphan_hold_required` を常時成立へ | KILLED (過剰拒否) |
| P1b | dispatch の `_orphan_hold_present` を常時成立へ | KILLED (過剰拒否) |
| P1c | harness の `_path_present_fail_closed` を常時成立へ | KILLED (過剰拒否) |
| P1d | worktree の hold 検出を常時成立へ | KILLED (過剰拒否) |
| P1e | acceptance の hold 検出を常時成立へ | KILLED (過剰拒否) |

段 4 の P1 (単一変異) は**取り消す** — 5 つの独立 detector を 1 変異にまとめており単一理由性を満たさない (B-3)。

**期待 node は fix 後の最終 commit で `--junitxml` から完全集合を再導出する** (DW-M07 / DW-M08 / F33)。
B-3 の静的見積り (M1=11 件、M2=2 件、M4=2 件、M7=5 件など) は目安であり、
再導出した完全集合だけを spec へ書く。

## 変更しない (明示)

- 署名 `job_may_remain is True` は緩めない。
- F47 ラッチ、通常完走、local runner mode、非 timeout `PARSE_ERROR` の受理集合。
- 通常 ledger v4 / wrapper receipt v1 / dispatch receipt v2 の schema。
- `tools/mutation_fanout.py` (所有外)。
