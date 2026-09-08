---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2397-a1-pilot-attempt3
seq: 2
---

## 再発

### F580

- **再発: 2026-09-09** — (2) と同一症状の 3 例目。A-1 pilot attempt-0003 で 3 job とも
  `v3 BACKOFF_FIXED condition gate rejected measurement: supply-effectuation:configure-failed`
  により 40 秒前後で停止した (request `986702` / `986703` / `986704`)。今回止まったのは job body の
  build ではなく、**条件関門が別に走らせる configure** である。job body 自身は同じ job の中で
  gflags / glog の staging を完了しており、欠けていたのは関門への供給だけだった。
  probe job `986707.nqsv` が取った detail は逐語で
  `Could NOT find gflags (missing: gflags_LIBRARY_FILE gflags_INCLUDE_DIR)` /
  `cmake/Findgflags.cmake:9` / `CMakeLists.txt:33 (find_package)`。
  A-1 の呼び出しは `capture_define_inputs` へ configure 引数を 1 つも渡していない
  (`captured.configure_args` が `()` であることを同 probe が印字した)。同じ関門に届く他の
  production 経路 (`backoff_sweep.py:107`、`screening_driver.py:189-196`) は渡している。
  本 F の再発検知が求める「同種の既存経路を 1 本名指しして、そこが行っていて自分が行っていない
  手順を列挙する」を、関門の呼び出し側にも適用していれば投入前に見えていた。
  一次資料は `output/insights/2026-09-09_t2397-a1-pilot-attempt-0003/README.md` §6.1、
  裁定は {{T:a1-gate-build-context}} 待ち。
