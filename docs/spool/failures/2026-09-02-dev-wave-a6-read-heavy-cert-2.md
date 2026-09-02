---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-a6-read-heavy-cert
seq: 2
---

## 新規

### {{F:qstat-reqname-truncation-inert-guard}}. 投入器の重複検出が導入時から一度も発火していなかった [恒真ゲート] [表示値の切り詰め]

- 事象: `tools/pegasus/submit_paper_story_a2_certification.sh` の
  「同じ certification request が既に見えていたら preregister 前に止まる」検査が、
  A-2 導入時から一度も発火していなかった。実装は `qstat` の出力に対する job 名の部分一致
  (`*paper-a2-cert*`) だった。
- 根本原因: `qstat` の `ReqName` 欄は **8 文字で切り詰めて表示される** (実測: 実際の request 名
  `izdw-b51bb380a6` が `izdw-b51` と表示される)。したがって 13 文字の job 名との部分一致は
  永久に偽である。表示用に整形された列を機械判定の入力にしていた。
- 恒久対応: inventory を引数なし `qstat -f` へ変え、`    Request Name = <job 名>` の
  **完全な行一致**だけを同 study の重複として拒否する。`qstat -f` は全 request について
  切り詰めない完全名を出す (実測)。過剰拒否の正例 (別 study の request、無関係な request、
  接頭辞衝突 `paper-a6-cert-x`) と負例 (同 study の request) を対で登録した。
- 再発検知: 変異 M6 (exact 行照合を無効化すると赤) と、上記の正例 3 件・負例 1 件。
  修正前は死んだ gate だったため、修正前の M6 は KILLED を主張できない。

### {{F:a2-cert-online-fetchcontent}}. certification 経路の build が計算ノードの環境契約に従っていない [環境契約違反] [恒真でない前提]

- 事象: A-6 の正式投入 (request 967525.nqsv) が Elapse 20 秒で driver_rc=2 終了した。
  条件 gate が `BACKOFF_FIXED:supply-effectuation:configure-failed` ほかで cell-0 を拒否した。
- 根本原因: 条件 gate の cmake configure が CCBench の
  `cmake/ThirdParty.cmake` の `FetchContent_Populate(masstree)` を実行し、これは
  `https://github.com/...` からの git clone を必要とする。**計算ノードは直結の外部 network 不可**で
  DNS が解決できない (実測: `git ls-remote` が rc=128、`Could not resolve host: github.com`)。
  同じ configure はログインノードでは成功する。`docs/pegasus-runbook.md` は 2026-08-01 の実測として
  この事実と「依存ソースはログインノードで pinned staging し `FETCHCONTENT_SOURCE_DIR_*` で渡す
  運用を維持する」を既に定めているが、**A-2 / A-6 の certification 経路は job body も条件 gate も
  この契約に従っていない**。
- 波及: 条件 gate は A-2 の実走 (2026-08-28、commit `639c1dba`) より後に driver 全体へ義務化された
  ものであり、A-2 が当時通ったことは同じ経路が今日通ることを意味しない。永続 cache
  `/work/1/SFC/tanab/izanagi-thirdparty-cache` と供給 helper
  `tools/pegasus/fetch_third_party.py` は既に存在し、`mocc_trace_pilot` と `silo_ladder_rung1` は
  使っている。certification 経路は `run_campaign` 経由でビルドするが、`run_campaign` は
  FetchContent の source dir を受け取る引数を持たない (`buildcache` 側には既にある)。
- 恒久対応: **未実施。** 共有 measurement pipeline (`run_campaign` → `pipeline.evaluate` →
  `buildcache`) への横断的な引数追加になり、全 driver の測定ビルドの configure argv を変えるため、
  ユーザー裁定へ返した。規律 2 により gate を緩めて通すことはしない。
- 再発検知: A-6 attempt `a6-20260902a` の `certification.json` が `indeterminate` として保存され、
  reason に driver rc が残っている。
