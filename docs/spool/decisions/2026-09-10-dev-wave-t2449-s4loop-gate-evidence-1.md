---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-10
wave: dev-wave-t2449-s4loop-gate-evidence
seq: 1
---

## {{D:condition-gate-rejection-evidence}}. 段 4 loop の condition gate は拒否時に arm record と admission を evidence root へ原子的に保存する

**決定:** `orchestrator/campaign/p3_s4_loop.py` の `_require_condition_gate` は、
`require_condition_gate_family` の admission が拒否を返したときにだけ、supply / meaning の
arm record と admission の canonical JSON を環境変数 `IZANAGI_S4_EVIDENCE_ROOT` が指す
directory へ保存する。file 名は arm 名と内容 digest (`record_digest` / `admission_digest`) から
作る。書き込みは同じ directory 内の一時名へ行い、`fsync` してから `os.replace` で公開し、
親 directory も `fsync` する。同じ digest の再試行は冪等な上書きとして正常系に扱う。
環境変数が未設定または空なら保存を省略する。

保存に関わるどの失敗も、元の gate 拒否を置き換えてはならない。拒否本文は保存を試みる前に
確定させ、保存側の例外は `Exception` 境界で捕らえて拒否本文へ追記するだけとする。
`BaseException` は捕捉しない — `KeyboardInterrupt` / `SystemExit` / `GeneratorExit` の伝播は
正しい挙動であり、これらは「拒否すべき variant を受理する」方向の破れではない。

あわせて `orchestrator/campaign/condition_meaning_gate.py` の `_run_process` は、失敗を送出する
全経路の detail に、実行しようとした argv を載せる。500 byte を超える argv は切り詰め、
切り詰め時は切り詰め前 argv 全体の sha256 を印に含める。整形関数は決して例外を送出せず、
整形できないときは固定の代替文字列を返す。

**gate の受理集合・reason code 語彙・admission 判定・rc・green 経路の bytes は変えない。**

**理由:**

- 計算ノードの job が supply arm の `preprocess-failed` で止まったとき、失敗本文 (rc・stderr) は
  red arm record の `evidence.detail` に載っていたが、driver が reason code 2 個だけの
  `RuntimeError` を上げて record ごと捨てたため、job 終了とともに失われた。gate 専用の
  isolate worktree は `/scr` にあり job 終了で消える。
- 保存先を driver 側に置くのは、job body が既に `IZANAGI_S4_EVIDENCE_ROOT` を必須入力として検査・
  解決しており、その値が repository の外にあることを operator 契約が要求しているためである。
  gate module 自身に file 書き出しの責務を持たせない。
- file 名を内容 digest にすると、同じ evidence root への再試行で前回の証拠を壊さない。
  一時名 + `os.replace` + 親 directory の `fsync` にするのは、scheduler の強制 kill と
  同一 digest の並行 writer に対して、壊れた file が最終名で固定化されるのを防ぐためである
  (段 6 の敵対レビュー 2 本が独立に同じ欠陥へ収束した)。
- argv を detail に載せるのは、reason code だけでは「どの command が落ちたか」が復元できないため
  である。切り詰め時に全文 sha256 を添えるのは、先頭 500 byte と総 byte 数が同じで末尾だけ異なる
  2 command が同じ detail・同じ red record digest・同じ保存 file 名に潰れうるためである。

**却下した選択肢:**

- **argv を載せない** — 過去実走の凍結 evidence
  (`output/insights/2026-09-07_t2228-driver-gate-liveness/`) が red arm record の canonical JSON を
  whole-file sha256 で束縛していることを理由に、段 2 のプランは argv 追記を採用不能と判断した。
  **これは反証された。** その manifest を参照する生きた consumer は repo 内に 0 件であり、当の
  manifest 自身が過去実走の provenance 記録だと明記している。絶対規律 7 のとおり、記録された測定は
  現行コードとの差だけでは無効にならず、逆に過去実走の記録は現行 producer を拘束する生きた契約でも
  ない。producer を変えても凍結 bytes は 1 bit も動かない。
- **`except BaseException` にする** — 上記のとおり誤り。`SystemExit` を `RuntimeError` へ変換する方が悪い。
- **兄弟 driver へ同じ形を横展開する** — 同型の「record を作って捨てる」は `p3_kickoff.py`、
  `p3_s4_loop_sort.py`、`backoff_sweep.py` 等にもあるが、`DW-G03` (族一般化には独立 2 例) により
  本 wave では一般化しない。
