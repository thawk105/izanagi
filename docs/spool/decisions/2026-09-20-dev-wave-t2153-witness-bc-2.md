---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2153-witness-bc
seq: 2
---

## {{D:witness-ifdef-and-multisite}}. `#ifdef` 形の witness は対照を未定義にし、非一意 directive は宣言した全箇所を観測する — 代表選択はせず、主張は DefineSpec patch の逐語箇所に限る

**決定:** D1490 の compile-time 枝選択 witness に 2 つの型を足す。(1) 登録簿の directive が `#ifdef <MACRO>` で始まる
macro は、要求腕を `-D<MACRO>=1`、対照腕を**未定義 (`-D` なし)** で観測し、request には `default_value=None` を要求する
(`-D=0` を対照にする経路は作らない)。supply arm の対照 compile argv に同 macro が残れば `supply-value-mismatch` で拒否する。
この不在検査は `#ifdef` 登録 macro に限り、他 macro の `default=None` 要求 (`BACKOFF_NOINLINE` 1/None、stock 対照) の
判定は変えない。(2) 同一逐語の directive が所有 TU に複数ある macro は、`_CONDITIONAL_BRANCH_SITE_COUNTS` に箇所数 N を
宣言し、**N 箇所すべて**に marker を入れて要求 (N,N) / 対照 (0,N) を要求する。実測箇所数 ≠ N は N=1 なら従来の
`compile-time-branch-start-not-unique`、N>1 なら `compile-time-branch-site-count-mismatch` で拒否する。green record の
再検証も N と未定義対照に追随する。登録簿へ `IZANAGI_BREAK_TRIGGER_MISATTR` (`#ifdef`、N=1)、`IZANAGI_SILO_LADDER_RUNG1`
(N=2)、`BACKOFF_TRIGGER_GATING` (N=12) を足し (枝選択 18 → 21、対応集合 19 → 22)、`s8a_trigger_coverage` の
`_require_condition_gate` を factory 配線して MISATTR の request を default None にする。`BACKOFF_REQUESTED_US`
(transaction.cc 2 + backoff.hh 2) は 1 macro に複数 file の箇所群を宣言する機構が要るため登録しない (残件)。
`s1_verify_extime_calibration` は TRIGGER_GATING を要求し admission を JSON へ載せるが、capture が genome の configure と
offline 供給を渡さないため配線しない (配線と供給を同じ変更単位で扱う、D2161 理由 4 と同じ)。

**主張の範囲:** N 箇所 witness が確立するのは「所有 TU において、DefineSpec が宣言する patch の逐語 N 箇所すべてで、その
define の値 (または定義の有無) が枝の選択を決めている」ことまで。重ね当て patch が足す条件 (例: 計装 patch の
`#if BACKOFF_TRIGGER_GATING && TRACE`) と `#ifndef` の供給番兵は対象外で、動的到達性・枝本文・誤帰属の発火は主張しない。
`declare_define_runtime_meaning` が None を返す request は従来どおり unestablished admit であり、family 拒否ではない。

**理由:**

- positive control `IZANAGI_BREAK_TRIGGER_MISATTR` は `#ifdef` なので、要求 1 / 既定 0 では両腕とも定義済みで前処理が同一になり、
  現行 gate では **supply arm が `preprocess-bytes-identical` で赤** = `s8a_trigger_coverage` の misattr 腕は preflight で
  `RuntimeError` になる (本 wave の login 実測、production CLI、main 947fd160a)。実 build の対は「定義する / しない」なので
  request の default も未定義が正しい。
- 複数箇所のうち 1 箇所を代表にすると、他の箇所の欠落・不活性を witness が見逃す (D2161 (2) が退けた過大主張)。全箇所に
  marker を入れ両腕の completion を N で要求すれば、箇所の欠落 (site-count)、外側条件で不活性な箇所 (completed < N)、既定腕
  だけ選ばれる箇所 (selected ≠ 0) がすべて red になり fail-closed が保たれる。
- 既存 18 entry の 2-tuple・順序・N=1 の reason/detail 逐語・record の key 集合を変えないことで、既存 macro の witness と
  receipt は変更前後で同一 (SORT / REPORT の実 TU record を leaf 単位で比較し、一時 path 由来の揮発以外は一致)。
- 不在検査を全 domain の `default=None` へ広げると `BACKOFF_NOINLINE` 1/None や SORT 1/None の supply 判定が変わる
  (CMake 既定の `-D<M>=0` が対照に残るため) ので、`#ifdef` 登録 macro に限る。

**却下した選択肢:**

- **`-D<MACRO>=0` を `#ifdef` の対照にする** — 定義済みなので識別しない (実測で supply 赤)。
- **N 箇所のうち 1 箇所を代表にする** — D2161 (2) の過大主張。
- **所有 TU 内の未宣言な条件指令 (重ね当て patch の複合枝) を走査して red にする** — `#ifndef` 番兵の免除規則を要し本題を超える。
  主張範囲を DefineSpec patch の逐語箇所に限って記録することで対応し、機構は足さない (裁定パッケージ候補として残す)。
- **REQUESTED_US を所有 TU の 2 箇所だけで登録する** — header の 2 箇所が未観測の部分登録。
- **登録簿の tuple を 3 要素にして N を持つ** — 2-tuple を unpack する consumer test 3 件を壊す。別 mapping で持つ。
- **新しい dataclass / receipt field を足す** — 既定値でも canonical JSON へ出力され既存 record の bytes が変わる。
