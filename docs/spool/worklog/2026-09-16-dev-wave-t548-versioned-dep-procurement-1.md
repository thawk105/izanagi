---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t548-versioned-dep-procurement
seq: 1
title: [T-548] gflags / glog を url + pin の共通調達経路へ移し、機体固有の絶対 path を repo から消した (コード + docs、branch worktree-dev-wave-t548-versioned-dep-procurement、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- **裁定の実体は 2026-08-16 /rulings 全件 第 3 回 索引 19 (択 (b)) で、「[T-585] と同じ面なので
  同一 wave で閉じる」まで含む。** 段 2 plan は「1 consumer だけ結線 + opt-in 入口」を推したが、
  段 3 の 2 レンズが独立に、それが D1737 の却下 (同じ依存を 2 経路で pin) に当たり裁定の
  「同一 wave」にも反すると結論したので不採用にし、consumer 21 本 (job body 15・Python 5・data 1)
  の全付け替えへ scope を広げた。設計は {{D:gflags-glog-versioned-procurement}}。
- **段 1 brief の誤り 3 件を段 3 が突いた。** 調達ツールの命令は 3 でなく 4、段 4 loop には依存 build が
  既にある (D1737 着地済み)、**[T-2625] は既に成立している** (job 999363)。通したのは親の一回限りの
  env 回避で、それは裁定が択 (c) として却下した形そのもの — 研究前進の理由はこちらが正しい。
- **実装子は 6 回 fail-closed で停止し、6 回とも親の欠陥を指した。** 内訳と追補は insight の表。
  親の失敗型は {{F:stage1-consumer-enumeration-stale-by-stage5}}、
  {{F:ownership-split-by-filename-misses-fixture-coupling}}、および **F736 の再発 2 回**
  (許可を列挙で与えて漏らした)、**F370 の再発 4 形** (本数 pin・行番号 pin・凍結 evidence の binding・凍結 prereg の
  job script sha が pin 閉包に出ない)。
- **凍結値はすべて親が算出した** (D200)。policy の現行 golden は変更前 bytes に 2 行の置換だけを
  適用して実装前に算出し、実装後の実測と一致した。silo 凍結 evidence の `pbs_job` / `submitter` は
  歴史値 + 現行 pin へ移し、凍結成果物は 1 byte も変えていない。
- **段 6 レビュー: must-fix 4 件はすべて本 wave の回帰か本 wave で消えた検査だった** (silo が
  gflags / glog を運ばない、T-126 submit が一時展開先を root と誤認、mocc の自己 hydrate が
  gflags 段より後、cache root の fail-closed 検査が乗り物ごと消えた)。テストは緑のまま、実 job を
  投げると依存段で必ず止まる断線 3 件を、レビュー B (実効性) が静的に見つけた。
- **レビュー A の must-fix (使用直前の `_verify_source` 相当) は不採用。** 変更前から同じ挙動で
  本 wave の弱体化ではなく、段 4 で採った R5 は出所の所見が「回帰ではない」と書いていたものを
  親が scope 判定せずに採った誤り。{{D:no-use-time-verify-source-gate}} に限界として明記。
- **棄却した所見:** レビュー A の P-2 候補 (metadata 4 case の削除) — 同レビュー自身が
  「代替なく検出力が消えた」を不成立と判定。レビュー B §8 (既存の orchestrator import が F88 に該当) —
  本 wave 由来でなく調達経路の本題でもない。
- **main の取り込み 2 回** (134 commit → `d97c423bd`、72 commit → `e667c8c13`)。2 回目は両親が
  同じ台帳テストを別 entry で書き換えており、Codex author が merge 後の現物で行番号 pin 10・
  起動本数 pin 143・合成 pin 32 を全件照合 (編集 0) してから commit した (先例 `1b0fe1b4c`)。
  midflight gate が MERGE_HEAD のある木を拒否するため、別の作業場で検証してから wave 側で
  merge をやり直した。
- **非帰属赤:** `test_p3_s4_loop.py` の自走 harness 単体走 (TypeError 112・guard 6) は fix 前の
  wave tip でも同じで、受入 harness の fixture 注入が無い構造。
- **受入 attempt 1 (tip `4b73b5a95`、claimed main `702b3c26f`) は 24,222 passed / 23 error / 1 failed で
  rc=1。** 24 件すべて wave が触れていない file (`test_t1259_qsub_env_delivery_probe.py` 18、
  `test_s8c_preregistration_predicates.py` 5、`test_s8b_oracle_n_pilot.py` 1) の **setup での
  `subprocess.TimeoutExpired`** で、command は `git archive` / `git -C <wave 木> ls-files`。
  同時受入 3 本。git 単体は 0.04 s (親が実測)、多数 worker の同時 git で timeout する既知の型
  (F の型は memory `login-node-load-times-out-20s-subprocess-tests`)。同 3 file の単独再走
  (login、loadgroup) も 51 error / 1 failed で command はすべて `git -C <wave 木> ls-files`。
  **本 wave に帰属しない。** load 下降局面 (20 < 22 < 27)・同時受入 2 本で attempt 2 を投入。
- **受入 attempt 2 (claimed main `e419fb733`、待ち手の post-claim merge `a792c92f8`) は
  24,243 passed / 3 failed で rc=1。** timeout 型は消えた。3 件の内訳: (a)(b)
  `test_codex_worker_launch.py` の 2 node — 計算ノード bnode042・1 分 load 43.77 での launcher
  timeout (`receipt_status=missing`)、wave 非接触、**非帰属**。(c)
  `test_s8b_oracle_n_pilot.py::test_r33_protocol_document_loads_from_repository` — attempt 1 でも
  赤だった**決定的な赤で、本 wave に帰属する**。凍結 prereg `protocol-r33.json` が
  `oracle_n_pilot.sh` の変更前 sha を記録し、test が現行 bytes と live 比較していた。
  段 6 追補 4 で D1790 の 2 定数へ (F5)。同時に、wave の変更 file 40 本の変更前 sha256 を
  repo 全体で逆引きし、live 比較で壊れる箇所がこの 1 つだけであることを確かめた。
- **工数 (Codex 子 19 本、全件 accepted):** author 8 本 4,983 s、fix 5 本 2,372 s、
  consult 2 本、review 2 本、plan 1 本、focus 1 本。計 8,938 s、451 model call。
  実装子の停止 6 回はすべて成果物ゼロで戻り、親が追補を書いて再投入した。
- 変異は probe 走 (全件 SURVIVED 期待で観測 node を集める) → 本走 (KILLED + 完全集合) の 2 段。
  M2 (pin 形式) と M7 (使用直前検証) は赤理由が 1 つに絞れず取り下げ。M10 の裁定文の記述は
  「env へ戻す」だったが実際の登録は「job の列挙から `build_dependency_rows` を除く」で、
  焦点再レビューが記述の不整合を指摘した (spec は正しい形)。M5 は契約テストの 52 node が同じ
  job body を読む過剰決定、M10 の 2 node のうち凍結 evidence の sha pin は任意の byte 変更で
  赤になる冗長 gate。

## 次の一手差分

### 完了

- [T-548] gflags / glog を url + 40 hex pin の共通調達経路へ移し、旧 locator を読む consumer
  21 本をすべて hydrate 済み staging root 配下の解決へ付け替えた。`verify-deps` は廃止。
  凍結成果物は不変で、golden と evidence binding は歴史値 + 現行 pin へ移した。
  remaining: none
  base: 3c0c9202db3a1e8e07d64a41ae5f8d3df34fcf9883edecc66ad05c1f036968e5
- [T-585] 依存 source の所在を機体固有の絶対 path で repo に書く結合を除去した
  (`gflags_source_path` / `glog_source_path` は policy から消え、読み手は 0)。
  remaining: none
  base: ad83c9147de56a926fbd005e90bb1713a2f7c76d99bd91c09cfc16782cbecfbc

### 新規

- {{T:job-body-inline-python-orchestrator-import-f88}} **P3・新規**: job body の inline python に
  既存の orchestrator import が残る (`certify_calibration.sh:227`、`mocc_trace_pilot.sh:1496`、
  `t141_region_profile.sh:1104`)。計算ノードの既定 python3 では import できない (F88)。
  本 wave 由来ではない。python 3.10 の選択を import より前へ動かすか、inline を json だけにする。
- {{T:dev-wave-pin-closure-count-line-evidence-forms}} **P2・新規**: `DW-O09` の pin 閉包に、
  編集する file を本数・行番号・sha256 で固定するメタテストを引く手順を足す
  (本 wave で 3 回、実装後の実走で初めて出た。F370 の再発)。候補は
  「編集 module / data file 名で `orchestrator/tests/` を逆引きし、hit の中身で pin の形を読む」。
- {{T:dev-wave-reenumerate-consumers-at-stage5}} **P2・新規**: 段 5 投入直前 (midflight gate の直後) に
  段 1 の consumer 列挙を採り直す手順を `DW-S05-A` へ足す。
  {{F:stage1-consumer-enumeration-stale-by-stage5}}。
