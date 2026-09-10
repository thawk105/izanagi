# 段 1 brief — [T-403] gate が見送った孤児 job の後始末を fail-closed にする

wave: dev-wave-t403-orphan-job-hold / branch: worktree-dev-wave-t403-orphan-job-hold
base main: 2f7eeb22 / 実測環境: Pegasus login (受入は `tools/run_tests.py`、変異本走は dispatch)

## 確定済みユーザー裁定

- fail-closed 側へ倒す。孤児が生きている間は「次回投入」と「source 復元」を止める。
- **本 wave では qdel を 1 度も実行しない。** 実装にも新たな qdel 呼び出しを足さない
  (自分の job を qdel すると F47 ラッチが武装し、worktree の dispatch が全面停止してユーザー手番になる)。
  実装するのは「止める」判定と記録までとする。
- Codex author = D95 (実装面は Codex `role=author` の実装子が書く。親は直接編集しない)。

## 実測で確かめた前段の事実 (brief 前提)

- `tools/pegasus/dispatch_compute.py` の D142 gate は、見送り時に `qdel.job_may_remain=True` と
  `qdel.gate.reason` を receipt へ書く。この field の**非テスト consumer は
  `_print_qdel_remaining_warning` (:1252-1271) 1 個だけで、stderr へ 1 行印字するだけ**である
  (`grep -rn "job_may_remain" --include=*.py` の全件を実測。他は同 module 内の書き手とテスト)。
- `_dispatch_impl` 冒頭 (:1350-1354) の投入前ラッチは `submission-disabled.json` (F47 型) だけを見る。
  孤児の有無は見ない。
- `tools/mutation_harness.py` `_apply_mutation` の `finally` (:1602-1604) は、runner の rc・
  timeout・孤児の有無に関わらず `_restore_targets` を呼ぶ。
- `tools/mutation_worktree.py` `_should_teardown` (:932) は `child_rc in {0,1} and terminal` だけで
  container の `rmtree` を許す。孤児の有無は見ない。
- 「計算ノード上の job が生きたまま login 側が source を復元する / 次を投入する / checkout を消す」
  という**性質**を止める機構は repo 内に 0 件。最も近い `mutation_fanout._append_orphan_evidence_claims`
  は走行後の evidence dir の帳尻合わせであり、生存 job を止めない。F47 ラッチは
  (a) qstat permission (b) request 不可視 (c) compute marker 不在 の 3 原因でしか立たない。

## 実 receipt 135 件の実測 (2026-08-16 14:10 JST、`izanagi/output/pegasus-dispatch` +
`/work/1/SFC/tanab/dev-wave-jobs/*/pegasus-dispatch-evidence`)

| 件数 | `qdel.attempted` | `qdel.job_may_remain` | `gate.reason` | `gate.request_present` | `outcome.kind` |
|---|---|---|---|---|---|
| 124 | false | **欠落** | 欠落 | 欠落 | child |
| 8 | false | **欠落** | 欠落 | 欠落 | infra |
| 2 | true | false | fresh-cancellable-snapshot | true | infra |
| 1 | false | **true** | state-not-cancellable | true | infra |

読み取れること。

- 正常完了 (124 件) では `qdel` は receipt 初期値 `{"attempted": false}` のままで、
  `job_may_remain` も `gate` も**存在しない**。判定式は field 欠落を「孤児なし」に写像しなければならない。
- 唯一の孤児事例が main checkout の untracked 成果物として残っている
  (`output/pegasus-dispatch/` は `.gitignore:26` で無視され、`git ls-files` は 0 件):
  `/work/1/SFC/tanab/izanagi/output/pegasus-dispatch/c35f548903e1d3b5a165908e006e76f2/receipt.json`。
  `outcome.reason="_SignalAbort: signal 15"`、`gate.scheduler_state="RUN"`、
  `gate.reason="state-not-cancellable"`、`job_may_remain=true`、`request_id="907709.nqsv"`。
  親が SIGTERM された後も job が RUN のまま残った F333 型そのものである。
- **したがって hold の判定は「過去 receipt の走査」であってはならない。** 走査型にすると、この
  既存 receipt が永久に dispatch を封じる。`output/pegasus-dispatch/` は checkout ごとに別物だが、
  `tools/mutation_worktree.py` の `_rehydrate_dispatch_evidence` (:616) が scratch container へ
  過去 evidence を持ち込む経路があるため、worktree を分けても隔離されない。
  hold は当該 dispatch 呼び出しがその場で立てる create-only file だけを権威とする。

## 因果の要 (親が実測)

job script は `cd "$REPO"` してから dispatcher を exec する
(`tools/pegasus/dispatch_compute.py:502-509`、`REPO` は login 側が渡す `repo_root`)。
`repo_root` は変異 worktree の checkout であり、共有 filesystem 上にある。
**したがって計算ノードの job は login 側 worktree の source をその場で読む。** 孤児が生きている間に
login 側が復元・再変異・削除を行えば、孤児が実行する source は台帳の記録と食い違う。
この因果が崩れると wave の前提そのものが崩れるので、段 3 レンズ A に再検証させる。

## scope (この wave で実装する)

1. **dispatch 側 hold の発行**: gate 見送り・qdel 失敗で「孤児が生きうる」と判定したとき、
   create-only の hold record を `output/pegasus-dispatch/` へ書く。qdel は呼ばない。
2. **次回投入の遮断**: `_dispatch_impl` の投入前検査へ hold を足し、qsub を 1 度も起動せず INFRA_RC を返す。
3. **source 復元の遮断**: `mutation_harness` が dispatch 試行のたびに hold を検査し、
   立っていれば `_restore_targets` を行わず、次の変異へ進まず、構造化 reason を台帳へ書いて fail-closed 終了する。
4. **worktree 廃棄の遮断**: `_should_teardown` が hold 成立時に False を返し、container を保全する。

## scope 外

- qdel の実行、F47 ラッチの受理集合・回復手順の変更、hold の自動解除、`qstat` の再問い合わせ。
- [T-404] (request ID discovery の候補確定条件)、[T-405] (receipt schema 版管理)、[T-406] (receipt 永続化の atomicity)。

## 攻撃対象の provisional 裁定

- **(P1) 孤児判定の署名。** `qdel.job_may_remain is True` **かつ** 不在・終端の実証がないこと、で hold を立てる。
  不在・終端の実証とは `qdel.gate.request_present is False` (qstat rc=0 で対象不在) または
  `qdel.gate.reason == "terminal-history-conflict"` (監視ループが END を観測済み) のいずれか。
  `request-id-unavailable` は「不明」であって「不在」ではないので hold を立てる側に倒す。
- **(P2) hold を F47 ラッチに相乗りさせない。** 別 file (`orphan-hold.json` 相当) を create-only で立てる。
  原因も回復手順も異なり、相乗りは既存 F47 テストの受理集合を変える。回復はユーザーが `qstat` で
  不在を確認して file を消す手番とし、自動解除経路は作らない。
- **(P3) 復元しない方が安全である。** 孤児が読むのは worktree 上の source なので、復元すると
  「変異入りと記録された試行が、実際には原本を実行した」食い違いが起きる。変異を残したまま止め、
  hold record と台帳に復旧手順 (孤児の終了確認 → `git checkout --`) を書く。
- **(P4) 判定入力は既存 receipt field だけ**とし、新しい scheduler state 語彙を作らない (D142 の双方向一致)。

## 不変条件

- 新たな destructive command (`qdel`・`rmtree`・`qsub`) を孤児成立時に 1 つも起動しない。
- 既存 F47 ラッチの発火条件・payload・回復文言を変えない。
- hold record は create-only。既存 hold を上書き・削除しない。
- gate の禁止は署名で書き、通る正例 (hold 不成立で従来どおり復元・投入・teardown する経路) を必ず添える。
- 実装子はコードとテストだけを編集し、docs 編集と commit をしない。

## 成果物影響 (DW-G05)

実装しないと、変異台帳 `ledger.json` の `mutations[].status` (KILLED/SURVIVED/MISMATCH) と
`failed_nodes` が、孤児 job が復元後 source または次変異 source を実行した結果を当該変異の結果として
記録しうる。B-057 事前登録の裏取り (DW-M02/DW-M08) が根拠を失い、受入・land の「変異 matrix 全 KILLED」
という受理判断そのものが誤りになる。

## 検出力 (純増)

新規テストが増やす検出力は次の 4 点に限る (既存被覆ゼロ)。
(a) gate 見送り receipt から hold が立つこと・不在実証時は立たないこと、
(b) hold 存在下で `_dispatch_impl` が `qsub` を 1 度も起動せず INFRA_RC を返すこと、
(c) hold 存在下で `_apply_mutation` が復元せず次の変異へ進まないこと、
(d) hold 存在下で `_should_teardown` が False を返すこと。

## 分割方針

編集面は `tools/pegasus/dispatch_compute.py` → `tools/mutation_harness.py` →
`tools/mutation_worktree.py` の一方向依存 (後段が hold record の形式を読む) なので、
段 5 は Codex `role=author` 1 単位の直列とし、所有 path を上記 3 file + 対応 test に限定する。
