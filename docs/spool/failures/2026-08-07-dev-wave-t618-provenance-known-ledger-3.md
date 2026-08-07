---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t618-provenance-known-ledger
seq: 3
---

## 再発

### F155

- **再発: 2026-08-07** ([T-618] wave)。**変異 harness を通さない素の targeted 走行でも同じ rc=16 が
  出た。** `python3 tools/run_tests.py orchestrator/tests/test_check_ai_provenance.py` (追加 flag なし、
  harness 非関与) が `bounded scope の memory.max / memory.oom.group を走行中に attest できない` で
  止まった。対象 238 test は計算ノードで 8 秒台に終わる規模で、`_SCOPE_ATTEST_SECONDS = 1.0` の
  race に入る。**本 F の (b) が harness 固有ではなく「login ノードで短時間に終わる走行」一般の
  条件であることが判明した。** `--force-dispatch` を足して計算ノードへ回すと同じ走行が
  rc=0 / 238 passed になり、実装差分は 1 byte も汚さずに止まっていた。
- **恒久対応の射程を広げる。** 本 F の既定 recipe (`--force-dispatch`) は変異本走だけでなく、
  **login ノードから投げる短時間の targeted 走行**にも適用する。受入全走は所要が長く race に入らない
  ため既定形 (追加 flag なし) のままとする — 受入形へ余計な flag を足すと事前検査が黙って
  発火しなくなる (F153) ので、この 2 つを混同しない。
