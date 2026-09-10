# 段 4 裁定 — [T-2449]

入力: 親 brief (`prompts/s1-brief.md`)、段 2 プラン (`artifacts/.../s2-plan.md`)、
段 3 レンズ A / B (`artifacts/.../s3-lensA.md` / `s3-lensB.md`)、および親が段 2〜3 の走行中に
自分で採った実測 (下記 A1〜A4)。

## A. 親が wave 中に採った実測 (段 1 brief を覆すものを含む)

- **A1 (決定的)。段 4 loop の supply arm は、現行 main の計算ノードで既に通る。**
  姉妹 wave `dev-wave-t2182-k2-eval-run` の attempt-0001 (job `988516.nqsv`、2026-09-09
  22:51 投入 / 22:59:16 開始 / 23:00:07 終了、Elapse 55S) が `driver_rc=0` で終わり、
  `job.stderr` に `condition gate rejected` の traceback が無い。`job.stdout` は
  `[campaign] evaluate silo|BACKOFF_FIXED=20,...` へ進み、`[eval 8a84a7b00103] abort:
  trace-parse-error` → `0 committed / 1 aborted / 0 skipped` で終わっている。
  `_require_condition_gate` は `run_campaign` より前に例外を上げる (`p3_s4_loop.py:1826`、
  `:1857`) ので、evaluate 行への到達が gate 通過の証拠である。fixture 値は 983020 と同じ 20。
  一次資料: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2182-k2-eval-run/evidence/attempt-0001/`
  (`compute-result.json` / `job.stdout` / `job.stderr`)。**他 session の成果物なので、
  親は伝聞でなく現物を読んで確認した。**
  **さらに、その走行が使ったコードが本 wave の base と同一 bytes であることを確認した** —
  submit-tree の `orchestrator/campaign/p3_s4_loop.py` は sha256
  `9207514ba04ab51b662a8b48ff063e1b8198867cc2100705d66227a744db14e4`、
  `orchestrator/campaign/condition_meaning_gate.py` は
  `b4f6cabc3538f39b3949610514447b909d747a19b994cbc222e76d43978f8511` で、
  いずれも local main `7f17e1c63` の現物と一致する。
  したがって A1 は「別の版で通った」ではなく「**この版で通った**」である。
- **A2。owner TU の include 連鎖 (静的、CCBench PIN `511c9538`)。**
  `cc/silo/transaction.cc` → `cc/silo/include/common.hh` が
  (i) `gflags/gflags.h` と `glog/logging.h` を直接 include (`common.hh:14-15`)、
  (ii) `../../../include/masstree_wrapper.hh` を include (`common.hh:12`) し、これがさらに
  `<config.h>` `<masstree.hh>` `<kvthread.hh>` 等を include する
  (`include/masstree_wrapper.hh:20-32`)。`config.h` は masstree 事前構築が**生成する**。
- **A3。gate 自身の configure argv は `captured.configure_args` をそのまま含む**
  (`condition_meaning_gate.py:1661-1676`)。983020 の commit `a173f0ab5` では
  `_require_condition_gate(sub, genome)` が無条件で `configure_args=()` だった。
- **A4。凍結 manifest `output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/
  full-file-sha256.json` を参照する生きた consumer は repo 内に 0 件**
  (`git grep -ln "full-file-sha256"` が `*.py` / `*.json` / `docs/*` で 0 件、
  当該 3 test file の 64 桁 hex literal も 0 件)。

## B. 983020 の失敗の帰属 (A1〜A3 からの結論)

**gate の preprocess が落ちた直接の原因は、gate 専用 configure に FetchContent の offline 指定が
渡っていなかったことであり、system gflags の不在ではない。** env の `CMAKE_PREFIX_PATH` は
D1773 (d) により export 済みだったので gflags/glog は `find_package` で解決できた。渡っていなかったのは
`-DFETCHCONTENT_BASE_DIR` と `-DFETCHCONTENT_SOURCE_DIR_*` であり、計算ノードには外部ネットワークが
無いため gate 専用 build root に masstree source も生成済み `config.h` も無く、owner TU の `-E` が
`masstree_wrapper.hh` 経由の header を解決できなかった。`9a32ef5ca` (T-2182、2026-09-09 02:36 JST) が
この引数を gate へ通し、A1 で実際に通ることが確認された。

**この帰属は「コードと成果物からの帰属」であって「捕まえた stderr」ではない。** 983020 の
preprocess stderr は isolate worktree (`/scr`) と共に消えており復元できない。この区別は記録に明記する。

## C. 所見の裁定

### 段 2 プラン

| # | 判定 | 裁定 |
|---|---|---|
| P1b を「hash 束縛あり」として argv 断念 | **refuted** | A4 と規律 7 により反証。過去実走の provenance 記録は現行 producer を拘束しない。argv 追記は採用する |
| driver 側で red 時に record を evidence root へ保存 | real・採用 | 下記 D の修正を入れる |
| 固定 file 名 + `O_EXCL` | real・**不採用** | レンズ A 所見 3 を採る。`record_digest` を含む名前にする |
| 保存対象は arm 2 本のみ | real・**不採用** | レンズ A 所見 4 を採る。admission canonical JSON も同じ attempt へ保存する |
| 既存 2 test file へ追加、新規 file を作らない | real・採用 | 自走 harness と受入台帳の追加負担を避けられる |
| 受入台帳は正本 producer の `--add-only` で作る | real・採用 | 手書き placeholder を作らない |

### 段 3 レンズ A

| # | 判定 | 裁定 |
|---|---|---|
| 1 argv 断念では依頼を完了できない | **real・採用** | `_run_process` の失敗 detail に argv を載せる。red (raise) 経路のみ |
| 2 `p3_s4_loop.py` 編集が B-4 admission を動かす | **real・scope 外 (運用注記)** | 親実測: live hash 検査は起動時に admission record を渡したときだけ発火し (`p3_b4_launcher.py:381-388`)、repo に committed な record は無い (hit は過去 insight の逐語のみ)。closure member を編集する全 wave に共通する帰結であり、直前の `9a32ef5ca` も同じ。errata 不要。**次の B-4 起動が現行 live hash を宣言する**ことだけ記録する |
| 3 固定名 + `O_EXCL` は再試行時に現行証拠を残さない | **real・採用** | file 名に arm と `record_digest` を入れる |
| 4 admission record が依然捨てられる | **real・採用** | admission canonical JSON も保存する |
| 5 `evidence["detail"]` は全 red の共通契約ではない | **real・採用** | detail 不在の reason code では `reason_code` と evidence 全体を落とす。`None` を本文に出さない |
| 6 提案テストが恒真化する | **real・採用** | 正例は実体を名指しする。少なくとも 1 本は fake でない実 process 失敗で argv と stderr が detail に載ることを検査する。変異の帰属は新 nodeid 単独走で分離する |

### 段 3 レンズ B

| # | 判定 | 裁定 |
|---|---|---|
| 1 plan が argv 要件を放棄 | real・採用 | レンズ A 1 と同じ |
| 2 evidence root の永続性を job body は保証しない | **real・採用 (運用側で閉じる)** | 投入時に `<job dir>/evidence/attempt-NNNN` を使う。実装側の追加 gate は作らない (scope 外) |
| 3 driver が見るのは canonical 化前の環境値 | real・**scope 外** | README §7 が絶対 path を要求しており、job body の変更は D1773/D1801 の契約テストに触れる。裁定パッケージへ送る |
| 4 green 後の timeout は gate 通過の証拠にならない | **real だが本 wave では不発火** | A1 が evaluate 行への到達で通過を示しており、walltime kill ではない |
| 5 保存失敗の隔離が `OSError` 限定 | **real・採用** | 保存処理全体を `Exception` 境界に置き、拒否本文を先に確定する |
| 6 投入前提の不足 (single-tenant 検査ほか) | **real だが本 wave では不発火** | 下記 E により計算ノード投入を行わない |
| 7 hook の一般化が未証明 | real・**不発火** | 新規実行体を作らず、計算ノード投入もしないため |

### 親 brief 自身の是正 (レンズ A の指摘を採る)

- 「`merge-base` rc=1 → 失敗は消えている**可能性**」は弱い可能性命題までしか支持されない。
  **A1 の実測がこれを経験的に確定させた**ので、記録では推論でなく A1 を根拠にする。
- 「system gflags/glog がログインノードにも無い → 計算ノード固有ではない」は過剰一般化だった。
  実測できたのは `/usr/include/gflags` 不在と `pkg-config --exists gflags` rc=1 の 2 点だけである。
  記録ではこの 2 点に限定して書き、「compiler から不可視」とは書かない。

## D. プラン v2 (実装子への確定指示)

1. `condition_meaning_gate._run_process`: 失敗を送出する 3 箇所 (timeout / 実行不能 / rc 非 0 /
   rc=0 かつ stderr 非空) の detail に、実行しようとした argv を載せる。**成功経路は 1 bit も変えない。**
   reason code 語彙・受理集合・rc は不変。
2. `p3_s4_loop._require_condition_gate`: `admission.admitted` が偽のときだけ、
   supply / meaning の arm record と admission の canonical JSON を
   `$IZANAGI_S4_EVIDENCE_ROOT` 配下へ保存する。file 名は arm 名 + `record_digest` を含める。
   保存処理全体を `Exception` 境界に入れ、**どんな失敗でも元の拒否が必ず送出される**ようにする。
   環境変数が未設定・空なら保存を省略して従来どおり拒否する。green 経路は無変更。
3. 例外本文には reason code に加え、detail がある arm はその detail を、無い arm は
   `reason_code` と evidence の key 集合を載せる。`None` という文字列を出さない。
4. テスト: 既存 `test_p3_s4_loop.py` と `test_condition_meaning_gate.py` へ追加する。
   少なくとも 1 本は**実 process の失敗**で argv と stderr が detail に入ることを検査する
   (fake で埋めない)。保存の正例・負例 (root 未設定 / 書込失敗 / 再試行時の別 digest) を入れる。
5. 受入台帳は `tools/update_acceptance_duration_ledger.py --add-only` で JUnit 実走から作る。

## E. 計算ノード投入は行わない (規律 4 / DW-G01)

A1 が現行 producer での gate 通過を計算ノード上で既に示している。本 wave の変更は red 経路の
診断だけなので、green 走行では 1 行も発火しない。同じ答えを得るためだけに混雑した queue へ
1 本足すのは「大きすぎるスケール」であり、DW-G01 の「最安の生死確認」は姉妹 wave が既に済ませている。
**投入するのは受入全走の dispatch だけとする。**

## F. 変異事前登録

実装確定後に spec を書く。帰属を分離するため、`p3_s4_loop.py` への変異は
**新 nodeid の単独走**で kill を確認する (B-4 projection hash の連鎖赤と混同しない、レンズ A 6)。
登録する SURVIVED 期待は、実装が確定してから書く。

## G. ユーザー裁定パッケージ (実装しない)

1. **`_run_process` の「rc=0 でも stderr が非空なら失敗」規則 (`:1584-1586`) は configure に対して
   脆い。** CMake が新しい警告を 1 行出すだけで gate が `configure-failed` になる。983020 の
   `job.stderr` には実際に `Manually-specified variables were not used by the project:
   CMAKE_C_COMPILER` が 2 回出ている (別段のもの)。規律 2 を緩めずにこの脆さを扱う方向 (configure に
   限った警告の allowlist / 別 reason code / 現状維持) は裁定が要る。
2. **次の関門は `trace-parse-error`** (A1)。段 4 loop は gate を越えたが evaluate で abort する。
   これは別タスクとして起票すべきである。
3. **同じ「record を作って捨てる」形は兄弟 driver にもある** (`p3_kickoff.py:94`、
   `p3_s4_loop_sort.py:137`、`backoff_sweep.py:213` ほか)。DW-G03 により本 wave では一般化しない。
   独立 2 例が出たら制度化を裁定する。
4. **レンズ B 3**: job body が canonical 化した `evidence_root` を元の環境変数名へ再 export していない。
   相対 path が渡ると shell と driver が別 dir を指しうる。job body の変更は D1773/D1801 の契約テストに
   触れるため裁定が要る。
