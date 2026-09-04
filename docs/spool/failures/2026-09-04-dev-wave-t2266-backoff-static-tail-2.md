---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-04
wave: dev-wave-t2266-backoff-static-tail
seq: 2
---

## 新規

### {{F:insight-claims-unmeasured-without-checking-offrepo-artifacts}}. 材料文書が「1 点も測っていない」と書いたが、その測定は執筆時点で既に存在していた [検証漏れ] [一次資料未確認]

- 事象: `output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md` §5 が
  「b > 100 µs の静的 `T(b)` は 1 点も測っていない」と書き、§7 がそれを次の作業の根拠にした。
  この記述を正本として [T-2266] が起票され、依頼として投げられた。
  **実際には B-10 拡張格子が 2026-08-26 に b = 0〜900 µs の有効 28 点を 3 workload 分すべて
  完走させており、依頼が挙げた 6 点のうち 4 点は依頼どおりの条件で既に測られていた**
  (job 951689 / 951690 / 951691)。
- 根本原因: **成果物が repo 外 (`/work/1/SFC/tanab/b10-backoff-grid-runs5/`) にあり、
  repo 内の grep では見つからない。** 一方で同じ bytes は
  `docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json` が図 2c の入力として
  束縛しており、repo 内から辿る経路は存在した。執筆者は「未測定」を、
  自分が参照した材料の範囲で判断し、既存成果物の全数確認を行わなかった。
- 恒久対応: `docs/dev-wave/core.md` の `DW-S01` が既に
  「依頼・対象 vector の既存被覆を性質で decisions / archive worklog まで検索し、純増だけ書く」
  を求めている。本件はこの義務が **repo 外の測定成果物にも及ぶ**ことを示す実例である。
  measurement 系の「未測定」主張は、`docs/paper-story/figures/*.provenance.json` の
  `root_at_generation` が指す repo 外 root を列挙して反証を試みてから書く。
- 再発検知: 「未測定」「1 点も測っていない」と書く段で、
  対象量を出力する producer (`orchestrator/campaign/*.py`) を名指しし、
  その成果物 root を実際に `ls` した記録を残す。記録の無い未測定主張を根拠に起票しない。

### {{F:dispatch-queue-wait-timeout-read-as-test-red}}. 焦点走の rc=16 を test の赤と読みかけた [誤帰属] [infra]

- 事象: fix 後の焦点走が rc=16 で戻った。log 末尾は
  `Pegasus dispatch infrastructure failure: queue-wait-timeout` /
  `IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,...}` で、
  **子は 1 度も起動しておらず test は 1 件も走っていない。**
  他 wave の job が 5 本 queue に並ぶ混雑下だった。
- 根本原因: 既定の queue 待ち上限 (900 秒) が、実際の混雑 (数十分〜時間オーダー) に足りない。
  D612 が opt-in 上書きを用意しているが、既定のまま投げると infra 失敗が test 結果の位置に現れる。
- 恒久対応: `docs/decisions.md` D612 の
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE` / `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE`
  を混雑時に明示して投げる (本 wave では 3600 / 600 で通った)。
  併せて `IZANAGI_DISPATCH_OUTCOME_V1` の `child_started` を rc の解釈より先に読む。
- 再発検知: 非 0 rc を赤と分類する前に、log 末尾の `IZANAGI_DISPATCH_OUTCOME_V1` 行を読み、
  `child_started` が false なら infra として扱い、赤の内訳へ数えない。
  失敗後は `output/pegasus-dispatch/orphan-hold.json` と
  `output/pegasus-dispatch/orphan-holds/<request>.json` の 2 file を、
  `qstat -f <request>` で job の不在を確認してから撤去する。
