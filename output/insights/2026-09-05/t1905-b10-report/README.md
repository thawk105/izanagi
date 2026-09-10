# [T-1905] B-10 正式走の report phase — 135 セルの集約と 3 族 Holm 判定、[T-2311] erratum の適用 — wave 記録

判定は driver `orchestrator/campaign/b10_backoff_shape_sweep.py` の `judge()` の出力をそのまま写す。
本 wave は driver・投入 script・test を 1 byte も変えていない (実装面の差分 0)。判定の正本は
repo 内に収めた report 成果物であり、本書はその読み方と一次資料の所在を記録する。

## 0. 何をしたか

- read-heavy 本走 977647.nqsv (job-result driver_rc=0、45 record) の完走を現物で確認した後、
  同じ driver bytes (sha256 `b15c35480f50e73a440be0a734e7247f9ca56f17df58d86a4cdb1752fb214dd9`) の固定 checkout
  (`dev-wave-jobs/dev-wave-t1905-b10-trial-cell/submit-tree`、detached `2a338449bb2798b729c5bc2f9bfe76463a7fe347`)
  から `tools/pegasus/submit_b10_backoff_shape.sh --prereg-commit 77b33e37d… --phase report` を 1 回だけ投入した
  (**978195.nqsv**、nonce `23409962b76be959bb523a0cd5a31bc1`)。投入 13:14 JST、完了 13:20 JST (2026-09-05)、driver_rc=0。
- report は write-heavy 旧系列 `e3de15eb`・balanced 旧系列 `143a3f74`・read-heavy 現行 formal `acf840c8` の
  3 campaign × 45 cell = 135 cell を exact に集約し、3 族 Holm 判定と 36 cell の効果量・95% 信頼区間を出した。
- report 完了で D1627 (a) の条件が成立したので、[T-2311] の erratum を `docs/b10-backoff-shape-preregistration.md`
  末尾へ `## 10.` として当て、canonical machine spec block が 1 個のまま・`as_dict()` / `spec_sha256` 不変を実走で確かめた (§3)。

## 1. 一次資料

| 何 | 所在 |
| --- | --- |
| report 成果物 (repo 内、bytes は固定 checkout の出力と sha256 一致) | `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json` (sha256 `a4390603f20fbc8fdb74c482a17ae880f292e340e79846c31f5d923d71789fca`)、同 dir の `b10_backoff_shape_report_978195.nqsv-23409962b76b.md` (sha256 `e237d17db4f02818ea27049165fa90da4c19adea1bc8bca9b165b73b77e8e768`) |
| report 投入の受領証と job 結果 | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/23409962b76be959bb523a0cd5a31bc1/` (`submit-receipt.json`、`job-attempts/978195.nqsv/job-result.json` driver_rc=0、driver.stderr 0 byte) |
| read-heavy 本走の現物 | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/4537eb096a8ded8119e0bc92944f3171/` (977647.nqsv、job-result driver_rc=0、driver.stdout 末尾「done: 15 committed / 0 aborted / 0 skipped (of 15)」) |
| read-heavy 45 record | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-read-heavy-formal-acf840c8/runs/b10-backoff-shape-blocks/` (45 file、全件 correctness_certified・missing=false・execution_host=bnode088) |
| write-heavy / balanced の record と受理条件 | `output/insights/2026-08-31_t1905-b10-formal-run/`、`output/insights/2026-09-05_t1905-b10-trial-cell/README.md` §0・§1 |
| 事前登録 (発効版) | commit `77b33e37d2d63b1f83d10652792c3c93eba9fe8f` の `docs/b10-backoff-shape-preregistration.md` (blob `ea910de32df83c1bb320cbe62344dc5fb3b94684`) |
| erratum 適用前後の spec digest | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1905-b10-report/spec-before.json`、`spec-after.json` |

## 2. 判定 (report の逐語、解釈を足さない)

束縛 (report 冒頭と provenance JSON `preregistration` の field):

- 発効版 commit `77b33e37d2d63b1f83d10652792c3c93eba9fe8f`、binding `24d80d9a35122de1d6ecd8a7d0244c439434452e94418fa35d34a48169b9f483`
- patch SHA `36cd974c56c6f103d894a53048ac734d9859def266c05898d3794d2c48470832`、式 SHA `5b3d8deefed35d05597891592d7af442c96b2fa094cdebc8376b2e9bc9cd7662`、
  spec SHA `9c59411476018d510c8fc5d57f203920ccd3b216e6c5f341ce6b97e45041a7c2`
- 解析コード `2a338449bb2798b729c5bc2f9bfe76463a7fe347` / `b15c35480f50e73a440be0a734e7247f9ca56f17df58d86a4cdb1752fb214dd9`
- official certification: `false` (driver の固定値。formal driver 経路について「登録前に性能を見ていない」という限定主張だけを行う)
- 性能 cell の完全性 135 / 135、検証 slot の完全性 270 / 270 / 不完全 0 (3 campaign とも verify_done 90、legacy 15 + performance 75、WAL 切断なし)
- 曝露 (backoff 呼び出し ≥ 10,000 回/cell): 登録 126 cell は全件 met。indeterminate の 9 行は各 block の
  no-backoff 参照点 (`point=none`、呼び出し 0 回) で、判定の族には入らない。判定不能 cell・判定不能族は 0

3 族 Holm (対 = 18、両側 exact 符号反転 permutation、α = 0.05、効果 = symmetric-modulo の中央値 throughput / constant の中央値 throughput − 1):

| 族 | outcome | raw p | Holm p |
| --- | --- | ---: | ---: |
| write-heavy / symmetric-modulo | different | 0.025566101 | 0.025566101 |
| balanced / symmetric-modulo | different | 0.00026702881 | 0.00053405762 |
| read-heavy / symmetric-modulo | different | 7.6293945e-06 | 2.2888184e-05 |

read-heavy の raw p = 2 / 2^18 は 18 対すべてが同符号のときの下限である。

cell 効果 (symmetric-modulo、constant 比、95% paired-block 区間、等価域 ±3.0% との関係。値は report の `Cell effects` 節を % に直したもの):

| workload | μ 2 | μ 5 | μ 10 | μ 25 | μ 50 | μ 100 |
| --- | --- | --- | --- | --- | --- | --- |
| write-heavy | +0.74 [−3.29, +4.78] 境界を跨ぐ | −0.97 [−2.10, +0.15] 内側 | +0.39 [−1.18, +1.96] 内側 | +1.28 [−0.75, +3.31] 境界を跨ぐ | +1.15 [+0.02, +2.28] 内側 | +1.14 [+0.91, +1.38] 内側 |
| balanced | +0.47 [−2.14, +3.08] 境界を跨ぐ | +0.12 [−0.67, +0.92] 内側 | +0.95 [+0.23, +1.66] 内側 | +1.37 [−1.41, +4.15] 境界を跨ぐ | +0.71 [+0.18, +1.25] 内側 | +0.76 [−0.20, +1.73] 内側 |
| read-heavy | +0.65 [+0.04, +1.25] 内側 | +0.55 [−0.36, +1.46] 内側 | +0.20 [−0.10, +0.50] 内側 | +0.71 [+0.20, +1.21] 内側 | +0.39 [+0.10, +0.69] 内側 | +0.43 [+0.11, +0.75] 内側 |

constant の 18 cell は自分自身との対なので効果 0、区間 [0, 0] (report にそのまま並ぶ)。
36 cell の status はすべて `estimable`。等価域の外側に出た区間は 0 cell、境界を跨ぐ区間は 4 cell
(write-heavy μ 2・μ 25、balanced μ 2・μ 25)、残り 32 cell は内側。

退行込みの全 workload 報告: 点推定が負なのは write-heavy μ 5 の 1 cell (−0.97%、区間は 0 を含む)。
それ以外の 17 cell は正。どの workload でも等価域の外へ出た cell は無い。

事前登録 §3 の「書ける主張」の範囲での要約: 48 thread Silo / YCSB の 3 workload、μ = 2〜100 µs の登録 grid で、
`constant` と `symmetric-modulo` の 2 実装の間の throughput の差は、事前登録した手続きで 3 族とも検出された
(方向は 3 族とも symmetric-modulo が高い側)。効果量は全 cell で ±3.0% の等価域の内側か境界上にあり、
外側に出た cell は無い。これはこの 1 contrast についての主張であり、待ち方の効果一般・ばらつきの用量反応・
`binary` を含む ladder については何も言わない (§3「書けない主張」、§9)。

外部 floor 由来の参考幅 (検出力の保証ではない): write-heavy 1.9% (CV 0.67%、linux-baremetal)、
balanced 3% (CV 1.07%、linux-baremetal)、read-heavy 0.62% (CV 0.22%、pegasus)。

物理残差の 3 区分: 開示した 18 cell の probe は事前登録 §4.1、登録した 12 cell とその値は §5 と
provenance JSON の `physical_residual_values`、v4 の束縛は同 JSON の `preregistration` field。
本 wave は物理残差を測り直していない。

3 workload の実行は別 job・別 node・別日である (write-heavy 2026-08-31 系列、host 未記録 `not-recorded-legacy-v2`、
balanced 974207.nqsv bnode015、read-heavy 977647.nqsv bnode088)。判定は workload 内の block 対だけで
組まれており、workload 間の絶対値は比べない。

## 3. erratum の適用と検査

- 適用先: `docs/b10-backoff-shape-preregistration.md` の末尾 (`## 9.` の最終行の後) に `## 10. Erratum (2026-09-04) — §7 の perf 不在記述`。
  本文は `output/insights/2026-09-04_f241-perf-attribution/README.md`「未適用の訂正」節のとおり。§7 の本文行は書き換えていない。
  `IZANAGI-B10-SPEC` の marker 文字列は本文に書いていない。
- 検査 (driver の `parse_preregistration` を追記前後の作業木 bytes に直接当てた):
  追記前 35,820 bytes → 追記後 37,204 bytes。BEGIN / END marker はどちらも 1 / 1。
  `spec_sha256` は両方 `9c59411476018d510c8fc5d57f203920ccd3b216e6c5f341ce6b97e45041a7c2` (report と campaign record の値に一致)。
  `as_dict()` の JSON は byte 一致 (差分は本書が記録用に付けた `prereg_bytes` の 1 行だけ)。
- 帰結: 発効版 commit `77b33e37d` を指す `run_formal` は、追記後の作業木では `prereg-blob` で止まる (bytes 完全一致を要求するため)。
  これは D1627 が「全 phase 完了後に当てる」とした理由そのものであり、残り phase は無い。
  今後 B-10 の新しい phase を走らせるには、新しい登録 commit を指す必要がある。

## 4. 主張しないこと

- `binary` を測った、3 水準を比較した、`binary` の除外が事前登録された判断だった。
- 本結果で A-2 の逆転や過抑制域の機序を説明した。
- 待ち方と待ち量の直交切り分けを一般に閉じた。
- 検出力の範囲内で検出した。参考幅は検出力の保証ではない。
- 3 workload 間で絶対 throughput を比較した。
- official certification。report の `official_certification` は `false` である。

## 5. wave の形

実装面の差分 0 (docs + report 成果物の収容のみ) の軽量版。codex 子は起動していない。段 2・3・5・6 は省略、
変異 matrix は無し。受入全走は land の要件として 1 回投入する (結果は worklog)。
