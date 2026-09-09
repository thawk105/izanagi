---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2449-s4loop-gate-evidence
seq: 1
title: [T-2449] 段 4 loop の condition gate supply arm は現行 main で既に通ると実測で確定し、止めていたのが gflags でなく masstree の offline 供給だったことを帰属した — あわせて次に拒否されたとき失敗本文が残る配線を入れた (コード + テスト + insight、branch worktree-dev-wave-t2449-s4loop-gate-evidence、変異 9/9 KILLED・期待 node 完全一致)
---

## 本文

- **依頼は「再現して証拠を採る」だったが、現行 main では再現しない。** 姉妹 wave
  `dev-wave-t2182-k2-eval-run` の attempt-0001 (job `988516.nqsv`、2026-09-09 22:59-23:00 JST、
  Elapse 55S) が `driver_rc=0` で gate を越え、`[campaign] evaluate` を経て
  `abort: trace-parse-error` で終わっている。その submit-tree の `p3_s4_loop.py` と
  `condition_meaning_gate.py` は本 wave の base (local main `7f17e1c63`) と sha256 が一致するので、
  「別の版で通った」ではなく「この版で通った」である。他 session の成果物なので現物を読んで確認し、
  その wave の撤去に備えて insight へ写した。
- **帰属は gflags ではなく masstree だった。** 止まっていた job の commit では gate 自身の cmake
  configure に `configure_args=()` が渡っており、`-DFETCHCONTENT_BASE_DIR` /
  `-DFETCHCONTENT_SOURCE_DIR_*` が無かった。計算ノードには外部ネットワークが無いので gate 専用
  build root に masstree source も生成済み `config.h` も無く、owner TU (`cc/silo/transaction.cc`) の
  `-E` が `masstree_wrapper.hh` 経由の header を解決できなかった。`gflags/gflags.h` と
  `glog/logging.h` も同じ owner TU の include 連鎖に入っているが、env の `CMAKE_PREFIX_PATH` が
  export 済みで解決できていた。gate へ offline 引数を渡す seam は 2026-09-09 02:36 JST の commit で
  入っており、止まった job の木には無い。
- **この帰属はコードと成果物からの帰属であって、捕まえた stderr ではない。** 当時の preprocess
  stderr は isolate worktree (`/scr`) と共に消えており復元できない。旧 commit の再走は既に
  置き換わった producer を測ることになるので別命題である (絶対規律 7)。
- **計算ノードへ新規投入しなかった。** 本 wave の変更は gate が拒否したときだけ発火する診断で、
  green 走行では 1 行も通らない。同じ答えのために混雑した queue へ 1 本足すのは絶対規律 4 に反し、
  `DW-G01` の最安の生死確認は姉妹 wave が済ませている。投入したのは焦点走・変異走・受入全走だけ。
- **段 2 のプランが依頼の成果物を自ら落としていた。** 過去実走の凍結 evidence を「現行 producer の
  red record bytes を縛る consumer」と読み、argv 採取を採用不能と判断していた。親が生きた consumer
  0 件を実測して反証し、段 3 の 2 レンズも独立に同じ結論へ達したので採用へ戻した。
  失敗台帳 {{F:frozen-record-read-as-live-contract}}。
- **段 6 のレビュー 2 本が独立に同じ欠陥へ収束した。** 証拠 file の最終 digest 名を内容完成前に
  `open("xb")` で公開しており、途中 kill・容量不足・close 失敗で壊れた file が最終名で固定化され、
  同じ record の再試行が `FileExistsError` で修復不能になる。一時名 + `os.replace` + 親 dir fsync へ直した。
- **レビューの是正案を 1 件 refuted にした。** `except Exception` を `except BaseException` へ変える案は
  採らない。`KeyboardInterrupt` / `SystemExit` / `GeneratorExit` の伝播は正しい挙動で、「拒否すべき
  variant を受理する」方向の破れではない (何も受理されない)。`SystemExit` を `RuntimeError` へ
  変換する方が誤りである。`MemoryError` は `Exception` なので既存の境界で捕捉済み。
- 設計判断は {{D:condition-gate-rejection-evidence}}。
- **焦点走 1 回目を infra 失敗で 1 巡失った。** D612 の opt-in 上書きを投入 script に書き忘れ、
  `queue-wait-timeout` で `child_started=false` の rc=16 になった。差分に帰属しない。
  上書きを入れた 2 回目は rc=0 / 534 passed。同型は記憶に既にあり、今回も焦点走 script で再発した。
- **受入台帳は更新していない。** 新 test は既存 2 file への追加で新規 test file が無く、台帳は
  未登録 nodeid を unknown 扱いにする fail-soft の scheduling hint である。登録には JUnit 実走を
  もう 1 巡 dispatch する必要があり、得られるのが scheduling の精度だけなので見送った。
- **変異は DW-M08 の diagnostic sensitivity pin として記録した。** 本 wave の変更は gate の受理集合を
  1 bit も変えないので、kill は「拒否すべき入力を受理しなくなった」ことではなく「失敗本文が失われる
  実装を検査が捕らえる」ことを示す。

## 次の一手差分

### 完了

- [T-2449] 段 4 loop の supply arm 停止は現行 main で再現しないことを計算ノードの一次資料で確定し、
  masstree の offline 供給欠落へ帰属した。次に拒否されたとき失敗本文 (argv・rc・stderr・arm record・
  admission) が job 終了後も残る配線を入れ、修正方向は裁定パッケージで返した。
  remaining: none
  base: 95b5fef7063f61f30be70ed26f95c3380a25cf34a2ff73eaa2bd96a519a7d4c2

### 新規

- {{T:s4-loop-trace-parse-error}} **P1・新規**: 段 4 loop の evaluate が
  `abort: trace-parse-error` で止まる件を帰属して直す。gate を越えた先の関門で、
  計算ノードでの試行台帳は依然 0 行である。job `988516.nqsv` の
  `[eval 8a84a7b00103] built trace=cf94503330a15b40 perf=3f1db7e3a3cd5f39` の直後に出ている。
- {{T:run-process-empty-stderr-rule}} **P2・新規・ユーザー裁定待ち**:
  `condition_meaning_gate._run_process` の「rc=0 でも stderr が非空なら失敗」規則は configure に
  対して脆く、CMake が新しい警告を 1 行出すだけで gate が `configure-failed` になる。規律 2 を
  緩めずに扱う方向 (configure に限った警告 allowlist / 別 reason code / 現状維持) の裁定が要る。
- {{T:s4-loop-evidence-root-reexport}} **P2・新規・ユーザー裁定待ち**:
  `tools/pegasus/p3_s4_loop_pegasus.sh` が canonical 化した `evidence_root` を元の環境変数名へ
  再 export していないため、相対 path が渡ると shell と driver が別 directory を指しうる。
  job body の変更は D1773 / D1801 の契約テストに触れるため裁定が要る。
