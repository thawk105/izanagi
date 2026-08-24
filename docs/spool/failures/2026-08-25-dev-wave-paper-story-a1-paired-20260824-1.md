---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-paper-story-a1-paired-20260824
seq: 1
---

## 新規

### {{F:nqsv-assumed-as-pbspro}}. 計測経路の 5 gate が PBS Pro を仮定し NQSV で恒真に偽だった [ドリフト] [恒真ゲート]

- 事象: A-1 の計測投入が実機で 5 段階に分かれて拒否された。敵対レビュー 2 巡と焦点再レビューを
  通過した実装が、実際の scheduler では正当な走行を 1 件も受理しなかった。
  (1) job が受け取る `PBS_JOBID` は `0:944076.nqsv` で、qsub 標準出力から得る request ID と
  文字列が一致しない。(2) `PBS_O_QUEUE` は NQSV が job へ渡さないため、必須検査が必ず発火する。
  (3) job の stdout は pipe、stderr は NQSV の spool path であり、どちらも qsub の `-o` / `-e` で
  指定した path ではない。(4) qsub の標準出力は request ID 単体ではなく
  `Request <id> submitted to queue: <q>.` である。(5) `qstat` の状態欄は `QUE` や `RUN` の
  3 文字で、1 文字の大文字を要求する検査は決して一致しない。
- 根本原因: codex 実装子は sandbox から scheduler socket へ到達できないため、この層を動的に
  確かめられない。静的レビューは形式の妥当性しか見ないので、「この site が実際に何を返すか」は
  原理的に検出できない。結果として PBS Pro の一般的挙動を仮定した実装が、レビューを通過した。
  (2) と (5) は**存在しない値を必須にする恒真に偽の gate**であり、正しさの証拠を 1 つも
  生まないまま正当な走行だけを落とす。
- 恒久対応: {{D:probe-scheduler-before-measurement}} に従い、長時間計測の投入前に数秒の probe job で
  `PBS_JOBID` / `PBS_O_HOST` / `PBS_O_WORKDIR` / `PBS_O_QUEUE` / FD 実体 / `nproc` を実測する。
  正規化と解析の正本は `tools/pegasus/dispatch_compute.py` の `_normalize_request_id` と
  `_REQUEST_RE` とし、新しい scheduler 解釈を発明しない。job が原理的に観測できないもの
  (配送後の `-o` / `-e` file) は job でなく親が終端後に hash して cross-bind する。
  存在しない値は落として「落とした」と成果物へ明記し、空値や 0 で埋めて観測したと記録しない。
- 再発検知: 計測経路を持つ wave が段 1 brief で probe 実測を必須にする。scheduler 由来の値へ
  形式検査を書くときは、その形式をこの site が実際に出すことを実測で示すまで closed にしない。

### {{F:env-capability-assumed-present}}. 実装が要求した環境機能 3 件がこの site に無かった [ドリフト] [恒真ゲート]

- 事象: scheduler 語彙の是正後も、計測は 3 回に分かれて止まった。(1) job body が
  `IZANAGI_RESERVATION_*` の 8 変数を 1 つも export しておらず campaign が起動しなかった。
  (2) CCBench の build が `Could NOT find gflags` で失敗し、job は 63 秒で終わって bench が
  1 度も走らなかった。(3) 全証拠検査を通過した後、publish が `renameat2` の
  `RENAME_NOREPLACE` で `EINVAL` を返した。publish 先は Lustre であり、この flag を実装しない。
- 根本原因: (1) と (2) は段 4 裁定が「compute-only とし依存 staging を検査してから開始する」と
  決めていたのに実装が持たなかったもので、**段 2 と段 3 で読めたはずの見落とし**である。
  正本 (`tools/pegasus/certify_calibration.sh`) は同じ job 種別で reservation の組み立てと
  gflags / glog の pin 付き static build/install を実際に行っている。(3) は scheduler ではなく
  filesystem の能力仮定であり、前記 F と同型だが層が違う。
- 恒久対応: 既存の同種 job body を正本として読み、そこが実際に行っている手順との差分を段 2 の
  プラン段階で照合する。環境能力を要求する実装は、その能力がこの site に在ることを実測で
  示してから closed にする。`RENAME_NOREPLACE` の代替は filesystem 名による事前分岐にせず、
  実際に `EINVAL` を観測したときだけ落ちる形にする (名前分岐は別環境で静かに緩む)。
  代替経路で保証できない範囲は恒真な保証で覆わず成果物へ構造化して残す。
- 再発検知: 計測 wave の段 1 brief で、同種の既存 job body を 1 本名指しして「そこが行っていて
  自分が行っていない手順」を列挙する。0 件と書くならその根拠を示す。

### {{F:mutation-found-vacuous-guarantees}}. 敵対レビュー 2 巡を通過した実装に発火しない保証が 2 件残っていた [恒真ゲート] [テスト代表性]

- 事象: 段 6 の変異 matrix 第 1 巡 (22 件) で SURVIVED が 6 件出た。うち 2 件は実欠落だった。
  3 workload の `ycsb_rratio` を全て `50` に書き換えても焦点テストは緑のままで、どの workload が
  どの rratio を持つかを検証するテストが存在しなかった。campaign ID の相異は workload 名だけで
  保たれるため、ID の distinctness 検査では捕まらない。もう 1 件は raw document の top-level
  `complete` 再計算の照合を丸ごと無効化しても緑で、この照合は一度も走っていなかった。
- 根本原因: どちらも「謳うだけで発火しない保証」である。敵対レビュー 2 巡はこれを検出できなかった。
  レビューは実装の意図と構造を読むので、意図どおりに書かれているが**その経路をテストが
  一度も通っていない**ことは見えにくい。
- 恒久対応: 変異 matrix を所見ゼロの裏取りとしてだけでなく、レビュー通過後の必須検査として扱う。
  残る SURVIVED は mask か等価変異か実欠落かを個別に裁定し、mask は両層同時変異で裏取りする。
  本 wave では第 1 巡の生存 6 件を実欠落 2 / 照準ミス 1 / 相互 mask 2 / 前段 mask 1 に分類し、
  実欠落を塞ぎ、相互 mask を 1 entry 2 replacement の同時変異へ組み替え、本走で 23 件全件を
  事前登録した exact node 集合と完全一致で KILLED にした。
- 再発検知: 変異の生存を「等価だから問題ない」で閉じない。実効 gate へ再照準し、初回結果を
  erratum として残したうえで再走する。
