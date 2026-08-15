---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-t1094-fetchcontent-floor
seq: 1
---

## 新規

### {{F:nqsv-spools-job-script}}. PBS probe が同伴ファイルを `$0` 相対で解決して必ず落ちる [誤前提] [環境]

- 事象: (2026-08-15、`Request 911131.nqsv`) probe が Elapse **4 秒**・exit 3 で落ちた。
  scheduler stderr の全文は 1 行
  `realpath: /var/opt/nec/nqsv/jsv/jobfile/0.911131.10/t1094_floor_probe.py: No such file or directory`。
- 根本原因: **NQSV は job script を spool 領域へコピーしてから計算ノードで実行する。**
  実行時の `$0` は投入時の path ではなく `/var/opt/nec/nqsv/jsv/jobfile/<job>/` 配下になるため、
  `$0` の親 directory に同伴 `.py` を探す形は構造的に成立しない。login node からこの spool path は
  見えない (親が `ls /var/opt/nec/nqsv/jsv/jobfile/` で不在を確認)。
- 恒久対応: probe の `.pbs` は payload の絶対 path を**必須 env** で受け、
  非空・絶対・`realpath -e`・regular file・非 symlink を fail-closed で検査する
  (逐語 = `output/insights/2026-08-15_t1094-fetchcontent-floor/verbatim/probe-pbs.md`)。
  `$0` / wrapper の親 directory / spool path からの導出を持たない。
- 再発検知: PBS job script 内に `${0%/*}` や `dirname "$0"` を使う同伴ファイル解決があること。

### {{F:pinned-clean-blind-to-ignored}}. pinned-clean 検査が ignored 生成物を見ず、汚染された source を clean と宣言する [恒真ゲート]

- 事象: (2026-08-15、計算ノード `bnode030` と login の双方で実測) 共有 third-party cache の
  masstree は `git status --porcelain --untracked-files=all` が **0 行**、HEAD が凍結 policy の pin
  (`b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`) と一致する一方、
  `git ls-files --others --ignored --exclude-standard` が **71 件**を返した。
  内訳に `config.h` (10,448 bytes) と `libkohler_masstree_json.a` (2,466,846 bytes) を含む。
- 根本原因: `orchestrator/campaign/silo_ladder_rung1.py` の `third_party_source_contract` は
  HEAD 一致と `git status --porcelain --untracked-files=all` の空だけを pinned-clean の判定に使う。
  `git status` は **ignored file を列挙しない**ため、上流 `.gitignore` が無視するビルド生成物は
  判定に入らない。CCBench の `external/ccbench/cmake/ThirdParty.cmake:66-77` は
  `./bootstrap.sh; ./configure; make -j; ar cr` を
  `WORKING_DIRECTORY "${masstree_SOURCE_DIR}"` で実行するため、**build が source tree の中へ
  生成物を吐く**。同 wave の probe は clean な source に対しこの target を実行し
  (rc=0 / 10.676 秒)、`config.h` 10,448 bytes と archive 2,466,926 bytes が
  **その build によって生成された**ことを before/after で確定した。
  すなわち cache の 71 件は過去の build の残骸である。
  D152 決定 (4) が警告した失敗モードが実データで成立していた。
- 影響: `config.h` は `.gitignore` 除外で Git 非管理のため、**HEAD pin はその bytes を証明しない**。
  この経路を通った build の third-party identity 主張は成立しない。
  consumer は床値だけでなく Silo ladder correctness/gap job も含む。
- 恒久対応: **未実施。** 本 wave は測定に留め、実装は裁定へ返した
  (材料 = `output/insights/2026-08-15_t1094-fetchcontent-floor/`)。
  検査へ `git ls-files --others --ignored --exclude-standard` を加える案は、
  既存 record schema の `clean` の意味を上書きすると旧凍結 evidence を誤読するため、
  新 field による新旧分離が要る。
- 再発検知: pinned-clean を名乗る検査が `--porcelain` だけを根拠にしていること。

## 再発

### F306

- **再発: 2026-08-15** — **受入全走で出た**。本 wave の受入 3 走目が
  `test_dev_wave_wait.py::test_public_main_failure_restores_handler_without_release` 1 件で
  `attributable-red` (rc=70) になった。**本 wave の差分は docs 7 ファイルのみで、当該 test file に
  1 行も触れていない。** 単独再走を計算ノードで行い rc=0 (`Request 911268.nqsv`、8 秒) を実測して
  非帰属と判定した。同じ tip の 2 走目は緑だったので決定的な赤ではない。
  F306 の既知の再発検知は「変異 baseline の赤 node が族内で移動すること」だが、
  **本件は変異でなく受入全走で、しかも待ち手の非帰属 checker が `attributable` と分類した**。
  族のフレークが受入の帰属判定を誤らせる経路がある。

### F286

- **再発: 2026-08-15** — 3 例目。`docs/handoff/dev-wave-t971-swo-oracle-floor.md` が main へ
  tracked のまま land しており、本 wave の起動時に `check_wave_startup.py --external-handoff` が
  rc=1 になった。F286 自身が定めた再発検知条件 (`git ls-files docs/handoff/` が README.md 以外を
  返す) にそのまま当たっている。先例 `a3168d85` に従い main で直接撤去して解いた
  (所要 約 10 分)。**[T-1038] の恒久修正が入るまで、handoff が 1 本 land するたびに
  以後の背景 wave が 1 本ずつ同じ停止を払う。** dev-wave 入口へ
  「tracked な残置は main で直接撤去してよい」を書く案は `docs/dev-wave/**` の
  byte 予算が尽きているため裁定パッケージへ送った。
