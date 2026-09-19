---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2629-legacy-compiler-reach
seq: 2
---

## {{D:legacy-build-compiler-asymmetry-closed-as-limit}}. 旧 build 分岐の compiler 非対称は修正せず、到達条件・呼び手範囲・保証境界を明記して閉じる

**決定:** `pipeline._prepare_evaluation_core` の旧 build 分岐 (`env_contract` 無し → `buildcache.build()` を cc/cxx 無しで
呼び、既定 `g++-13` を使う) と事前 source evidence (`compilers_for_current_site()` が選ぶ compiler) の非対称は**修正しない**。
D2044 項 24 の「限界として閉じる」形を採り、到達条件・確認した呼び手の範囲・既存の拒否の実測・保証境界を insight
`output/insights/2026-09-20/t2629-legacy-compiler-reach/README.md` に記録する。checker・build・gate の受理集合は変えない。

**理由:**

- 非対称は「(A) `env_contract is None` ∧ (B) 実 site が Pegasus 計算ノード」の積でだけ成立する。(B) 以外の site では
  `compilers_for_current_site()` が既定を返し、旧分岐でも evidence と build の compiler が一致する。
- certified 入口 3 API (`loop.run_campaign` / `pipeline.evaluate` / `pipeline._prepare_evaluation`) の呼び出し 28 箇所
  (中継 3 + 外側 25) のうち、pegasus 契約で `env_contract` を省く呼び手は 0。省く 12 呼び手は全て `linux-baremetal`
  で、計算ノードでは `execution_guard.require_certified_writer_authorization` が evidence・build より前に拒否する
  (計算ノード `bnode020` で実測: `CertifiedWriterAuthorizationError`)。pipeline を経ない legacy `buildcache.build()` の
  直接呼び手 (7 file・8 呼び出し箇所) は evidence 側と build 側が同じ compiler (対称)。
- 到達したとしても fails-closed。`g++-13` 不在は `bnode009` (2026-09-14) と `bnode020` (2026-09-20) で観測した。`bnode020` で
  旧分岐の `buildcache.build()` を cc/cxx 無しで直接呼び、cmake configure が `CMAKE_CXX_COMPILER: g++-13 … was not found
  in the PATH` で失敗する `RuntimeError` を実測した。pipeline 経由ならこれが `build-error` abort へ変換されること、および
  cache-hit 側では先行検査を通過後に既定 compiler による evidence 再計算が同じ compiler 不在の `RuntimeError` で止まることは
  静的確認であり、実走していない。
- 発生記録: worklog / failures に無く、repo 内の campaign WAL 30 本 (全て `linux-baremetal`、`build-error` abort 12 件) の
  記録された error 本文にも compiler 不在型の診断は発見しなかった (本文なしの 2 件は判定できない)。

**保証境界 (本決定が主張しないこと):**

- `_recheck_source_evidence` の拒否は「build compiler で再計算した source evidence が事前 evidence と異なれば拒否」であって
  「compiler 差を全て拒否」ではない。同じ evidence を返す 2 compiler は通る (source identity の意味では正しい)。
- 旧分岐 (v1) には toolchain 束縛が無い。`g++-13` が解決可能になった機体で、同一 identity・異なる toolchain の binary が
  v1 経路で作られうることは観測も否定もしていない (D293 の領域)。
- `g++-13` 不在は観測した node・日時・PATH の事実であり、全 node・将来へは一般化しない。解決可能になっても現行呼び手への
  認可拒否は変わらないが、仮想的な旧分岐到達後の「不在による拒否」は消える。
- 呼び手の閉包は静的 (AST + 現物読解) であり、動的呼び出しの不可能性は証明しない。

**却下した選択肢:**

- **旧分岐へ site compiler を渡して対称化する** — `g++-13` 固定は D293 が「現に効いている fail-closed 障壁」と位置づけたもので、
  床値 campaign では calibration 由来の toolchain 束縛検査と同じ commit でしか入れられない。加えて本 wave で必要性
  (到達する呼び手) を確認できない。
- **事前 evidence を旧分岐では既定 compiler にして対称化する** — 失敗段階が build から evidence へ移り、WAL の abort reason が
  `build-error` (非 retryable) から `identity-error` (retryable) へ変わる。再試行・集計の分類を変える変更であり
  「成果物不変」ではない。必要性も未確認。
- **計算ノードでの旧分岐を明示拒否する新 gate** — 依頼が scope 外と明示。compiler の有無に依存しない拒否になるが、
  到達する呼び手が無い現状では発火経路が無い。
