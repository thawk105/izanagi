---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t1062-acceptance-scheduler
seq: 2
---

## {{D:effective-scheduler-attestation}}. 受入の実効 scheduler を観測して receipt へ束縛し land で照合する

**決定:** 受入全走の controller は、実際に使われた xdist scheduler object を観測して受入 log の
marker 1 行として出す。待ち手はその marker と log の SHA-256 を**同一の単一 read** から得て
acceptance receipt (schema `dev-wave-acceptance-receipt/v3`) の `effective_scheduler` へ格納し、
`tools/dev_wave_land.py` が閉集合として照合する。D390 の `--dist` 拒否は argv 層で残す。

観測と記録は次の 6 点を満たす。

1. 値源は `pytest_runtestloop` の wrapper post-yield で固定した
   `config.pluginmanager.get_plugin("dsession")` の `.sched` の**実型**とする。
   `pytest_xdist_make_scheduler` の hookwrapper の戻り値を値源にしてはならない。
2. 判定は exact 型で行う。`type(sched) is LoadGroupScheduling` のみ `loadgroup`、
   `dsession` plugin 不在は `serial`、それ以外・参照不能・例外は `unknown`。
   派生クラスは scheduling を上書きできるため `isinstance` にしない。
3. marker は `pytest_unconfigure` wrapper の中で、**failure digest の直前**に controller だけが
   1 行出す。`pytest_sessionfinish` では digest より前になり Pegasus dispatch の relay tail から
   押し出されうる。digest より後にすると、digest の END 行が stdout の末尾であることを要求する
   既存 e2e 契約を壊す。digest が出るのは失敗がある走行だけで、その走行は relay の失敗側
   (末尾 64 KiB) に載り、digest の予算上限 48 KiB を足しても marker は tail に収まる。
4. 待ち手は単一 `O_NOFOLLOW` open の streaming で hash と marker を同時に得る。
   `st_dev` / `st_ino` / `st_size` / `st_mtime_ns` の前後照合に加え、
   読み切り byte 数 == `st_size` を必須とする。
5. 抽出は bare 形と relay の `| ` 前置形の**両方**を受け、両形を合わせて exact-one を要求する。
   欠落・parse 不能・複数行・field 逸脱・閉集合外は rc=70 で receipt を発行しない。
   scanner は log 長に対して線形時間・定数追加メモリで走る。
6. receipt は `unknown` も**記録**し、拒否は land が行う。land の受理集合は
   `loadgroup` と `serial` だけとする。schema は待ち手と land を同一 commit で v3 へ上げ、
   v2 の互換受理と警告 fallback を作らない。

**理由:**
- plugin は `pytest_xdist_make_scheduler` で scheduler を差し替えられるため、既に必須の契約
  (受入形状 = loadgroup 排他) は argv 検査では閉じない。D390 の却下理由に挙がっていた
  「実効 scheduler を conftest で検査する」を、独立裁定を得て実装したものである。
- 1 の理由は pluggy の wrapper 意味論である。後から登録された外側 wrapper は、conftest の
  wrapper が post-yield で値を見た**後**に戻り値を差し替えられる。DSession が実際に保持した
  object を見るしかない。
- 3 の理由は dispatch の relay が成功時 4 KiB / 失敗時 64 KiB の tail しか返さないことと、
  conftest 自身が失敗要約を最大 48 KiB 出すことの両方である。前後どちらへ置いても
  失われない位置は digest の直前だけであり、これは実受入で 1 度踏んで確定した。
- 4 の理由は、hash 後に別 open で marker を読むと「log A の hash と log B の scheduler」を
  1 つの receipt へ載せられるためである。land は raw log を受け取らないので検出できない。
- 6 で `serial` を受理するのは、`python3 tools/run_tests.py -n0` が現行 `_is_acceptance_run` の
  受理形だからである。`loadgroup` のみ受理にすると、いま受理されている受入形を拒否することに
  なり、裁定が禁じた受理集合の縮小になる。`serial` は `numprocesses` の読み値ではなく
  `dsession` plugin 不在の観測で決めるため、推測ではない。

**保証しないこと:** 閉じるのは*非共謀 plugin による差し替えの検出*である。scheduler を
差し替える plugin は同一 process 内で marker 自体も偽造できる。発行者認証には plugin autoload の
隔離か pytest 外の観測路が要り、受入 env と受理集合の裁定を伴うため別裁定とする。

**却下した選択肢:**
- hookwrapper の戻り値を attest にする — 後登録の外側 wrapper に差し替えられる。
- `dsession.sched` を marker 出力時点で読む — 読むまでの間に再代入・unregister されうる。
- marker を `pytest_sessionfinish` で出す — failure digest より前になり relay tail から落ちる。
- marker を failure digest より後に出す — digest の END 行が stdout 末尾であることを要求する
  既存 e2e 契約を壊す。既存契約の側を緩めない。
- land が `loadgroup` のみ受理する — 現行受理形の `-n0` を拒否し受理集合を狭める。
- receipt へ `unknown` を記録せず待ち手で落とす — 裁定文の「receipt へ記録し land で照合」に
  反し、何が観測されたかの診断も残らない。
- v2 receipt を互換受理する — 必須 field の欠落が黙って通る。

## {{D:full-suite-plugin-option-split}}. plugin / ini 上書き option を full-suite 認定から外す

**決定:** `tools/run_tests.py` は `-p` / `-o` / `--override-ini` を
`_FULL_SUITE_DISQUALIFY_VALUE_OPTIONS` へ分離し、`_is_full_suite` から外す。
`_VALUE_OPTIONS` には残して値消費と positional 判定を不変に保つ。
`_is_acceptance_run` は 1 文字も変えない。

**理由:**
- この 3 綴りは `_is_acceptance_run` が既に同一に拒否しているのに、`_is_full_suite` は通していた。
  結果として、受入形ではない走行が task-run 上 `full` (`tests-full` / `pytest-orchestrator-full`)
  として記録されていた。ユーザー裁定は `-p` を名指ししたが、3 綴りは同一 predicate の同一穴で
  あり、1 つだけ直すと閉集合の中に非対称が残る。
- `_VALUE_OPTIONS` に残す理由は、外すと option の値が positional target として数えられ、
  `_test_operation` の key が別の壊れ方をするためである。
- 影響半径を実測した。`output/task-runs` の全記録に該当 3 綴りを含む走行は 0 件
  (full 分類の記録は 6 件)。peak ledger の cold start と集計の世代境界はいずれも実データが無い。

**却下した選択肢:**
- `-p` だけ直す — 2 predicate の非対称が残る。ユーザーが望めばこの形へ縮められる。
- `_suite_identity` だけ直して `_test_operation` を据え置く — 同じ predicate を共有する
  2 consumer の間に新しい不整合を作る。
