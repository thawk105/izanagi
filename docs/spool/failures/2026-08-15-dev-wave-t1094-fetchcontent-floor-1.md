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
