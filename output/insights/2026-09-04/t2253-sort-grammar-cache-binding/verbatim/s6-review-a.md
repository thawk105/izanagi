## 観点 1 の所見

- **real / nit — 相互排他の順序は C2 どおりだが、到達不能ではない。** [`source_digest.py:2222`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/source_digest.py:2222) は「相互排他 → stock → sort → backoff」の順である。両引数は [`loop.py:256`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/loop.py:256) から [`loop.py:479`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/loop.py:479)、または [`pipeline.py:1829`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/pipeline.py:1829) から [`pipeline.py:1092`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/pipeline.py:1092) を経て到達できる。ただし既存 producer は backoff が [`p3_s4_loop.py:1529`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop.py:1529) で backoff のみ、sort が [`p3_s4_loop_sort.py:412`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop_sort.py:412) で sort のみを渡す。さらに旧 API には sort 引数自体がなかったため、既存の受理済み呼出しを奪う変更ではない。
  放置影響: 新 API を直接使って両方を指定した stock 入力は `"stock"` にならず停止するが、登録済み producer の certified 選択・レポート値には影響しない。

- **refuted — binder の検査・bytes に相違はない。** [`source_digest.py:2198`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/source_digest.py:2198) は exact `str`、非空、ASCII、NUL なしを検査し、preimage は `b"sort-src-token/v1\0contract=" + id.encode("ascii") + b"\0source=" + raw_digest.encode("ascii")` と C2 に一致する。

- **refuted — backoff 防壁は弱化していない。** `p3_s4_loop.py` は基準から差分なし。`loop.py:337-351` の入口 gate、`source_digest.py:2177-2195` の binder、buildcache の v2 hit/fresh と legacy hit/fresh にある `backoff_grammar_version` の転送行は不変である。

- **refuted — 既定経路の成果物 bytes は変わらない。** `source_options`、`evaluate_options`、`common`、`build_options` はすべて非 `None` の場合だけ新キーを追加する。production で新引数を渡す箇所は sort loop だけであり、列挙された backoff、trigger、S1、S6、screening、S8b 系 caller は無変更かつ既定 `None` である。したがって raw/stock token、variant、admission receipt、legacy key、v2 digest は従来式のままである。

- **real / nit — downstream 呼出し形が逐語的にすべて同一、とはいえない。** `evaluate` は [`pipeline.py:1883`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/pipeline.py:1883) で明示 `None` も core へ渡し、`resolve_evidence` も [`source_digest.py:2358`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/source_digest.py:2358) で内部 helper へ渡す。四出口も `_recheck_source_evidence(..., sort_oracle_contract_id=None)` という呼出し形になる。C2 指定内であり、結果 bytes は不変である。
  放置影響: strict な test double や wrapper の kwargs 観測は変わりうるが、production の certified 値・台帳参照は変わらない。

- **real / must-fix 1 — module-level oracle import は不要な import-time 防壁拡張である。** [`p3_s4_loop_sort.py:68`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop_sort.py:68) の import により、単なる driver import が [`sort_swo_oracle.py:3089`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/sort_swo_oracle.py:3089) の初期化と `inspect.getsource` を必須にする。これは `test_p3_s4_loop.py:48`、trigger test、`s6_sort_sweep.py:64`、さらに全 driver を先に読む `p3_b4_launcher.py:29-31` に波及する。`test_pytest_collection_config.py:1099-1102` 自体は source text を読むだけなので直接は壊れない。現行 source loader で driver・S6・B4 launcher の import smoke は成功したが、pytest collection は実走していない。契約検査時の fail-closed を維持したまま、helper 内の関数内 import へ戻すべきである。
  放置影響: `inspect.getsource` が失敗する実行面では、sort を選ばない B4 base/trigger や関連 test collection まで開始前に停止し、レポート・台帳が生成されない。

## 観点 2 の所見

- **refuted — producer gate の位置関係は写し元に忠実である。** sort は B-4 `require_b4_production_context`、`BuildRunContext` 検査、`_require_sort_oracle_contract`、`ident.bind_admission_policy` の順 (`p3_s4_loop_sort.py:370-390`)。backoff の B-4、context 検査、grammar gate (`p3_s4_loop.py:1435-1451`) と同じ位置関係である。

- **refuted — `drive_iteration` / `main` への追加 gate は不要である。** 実評価は `drive_iteration` の `run_one_iteration` 呼出し (`p3_s4_loop_sort.py:593`) と main の同呼出し (`:790`) に収束する。入口停止や preview は build/cache 成果物を作らない。写し元も外側入口で grammar gate を重複させていない。

- **real / must-fix 1 と同一 — 局所性から外れたのは module-level import だけである。** これは上記と同じ一件で、別件として数えない。

- **refuted — その他の scope 外実装は混入していない。** `p3_s4_loop.py`、`resolve()`、`src_token()`、WAL、diffq、他 producer、`cache_key()`、`_v2_identity()`、`default_cfg()` は変更されていない。差分は許可された source 5 ファイルと sort test だけである。

## 実装子報告への指摘

- **real / nit — 「受理集合の不変」は適用範囲を限定すべきである。** valid な既存 producer と verify/oracle/diff/auditor の候補判定は不変だが、両 binding を指定した stock API 入力と、module import を受理できる環境集合は変わる。
  放置影響: 前者は開始時停止、後者は一部 tool・collection の開始前停止となる。

- **real / nit — 「既存 caller の呼出し形は変わらない」は入口 caller に限れば正しい。** 編集した内部 seam では明示 `None` kwargs が増えるため、全 downstream への一般化は過剰である。
  放置影響: strict double の受理集合だけが変わり、production の cache/WAL bytes は変わらない。

- **refuted — backoff 経路、campaign identity、四出口、既定 bytes を維持したという実装報告には、上記限定を除いて実コードとの齟齬はない。** campaign ID の read-only probe も `p3-s5-sort-loop-s5-sort-autonomous-6f6a8cf1` のままだった。

- **refuted — 実装子は pytest を緑と主張していない。** 本レビューでも pytest・collection は実走しておらず、campaign module の import smoke だけを確認した。

## 総括

- must-fix は 1 件。
- 最重要は `p3_s4_loop_sort.py` の module-level oracle import で、helper 内 import へ戻す必要がある。
- それ以外の契約伝播、exact preimage、既定 bytes、backoff 防壁は C2 と一致する。
- 判定は **NO-GO**。must-fix 解消後は GO 相当。
- pytest は未実走であり、緑とは判定していない。