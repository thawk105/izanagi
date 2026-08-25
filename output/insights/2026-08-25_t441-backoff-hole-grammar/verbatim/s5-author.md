Tier 1 の実装は完了しました。編集は許可された 4 ファイルだけで、Tier 2、docs、output、凍結 9 file、commit/index には触れていません。

変更内容:

- [backoff_hole_grammar.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py:1)
  - T1-1〜T1-7 の有限字句 grammar、固定 rule ID、固定 reason、資源上限を実装。
  - 式本体は opaque とし、Tier 2 の call、算術、三項、comma などは閉じていません。
- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py:200)
  - backoff marker のみへ配線。
  - type/raw-size preflight を path read、materialization、帰属 regex より前へ配置。
  - cap 内では `HOLE_ESCAPE`、`HOST_EFFECT`、`AttributionMismatch` を新 grammar より優先。
- [diff_quarantine.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/diff_quarantine.py:41)
  - `DiffRejectSubtype.BACKOFF_GRAMMAR` を追加。
- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/tests/test_p3_s4_loop.py:241)
  - 指定された effect scanner テストは名前と検査内容を保ち、marker だけ sort 軸へ移動。
  - 複数行、空行、tab 行、indent 除去、exact bytes の被覆はすべて維持。
  - Tier 1、優先順位、上限、非反射、marker 非影響、consumer closure を追加。

変更前は 32 形中 25 形を `quarantine()` が受理し、既存拒否 7 形だけが `HOLE_ESCAPE` / `HOST_EFFECT` でした。変更後も cap 内のこの 7 形の理由は保存されます。

検査結果:

- `py_compile`: rc=0
- `git diff --check`: rc=0
- `check_codex_agents.py`: rc=0
- `check_docs.py`: rc=0、既存 handoff 2 件の警告のみ
- pytest: 正規 runner を3回起動しましたが、すべて `qstat -Q preflight rc=1`、`child_started=false`、rc=16。実走 nodeid は0件です。runner が dispatch receipt を `output/pegasus-dispatch/` に自動生成しましたが、手動の output 編集はしていません。
- mutation harness: 未実走。未commit変更を固定 `HEAD` として扱えず、この段では commit禁止のためです。
- DW-M04: m01〜m14 の各 exact replacement anchor はすべて出現数1。一意でない対象はありません。

注意点として、T1-1の空拒否はT1-2の宣言必須に論理的に包含されます。そのため、t441.m03で空検査だけを外しても受理集合は広がらず、拒否 rule IDが変わるだけです。裁定表の「受理集合 KILLED」という期待は、実際の述語構造では単独には成立しません。

## 総括

- 実装した規則と実走 nodeid:
  - T1-1 空実装拒否。
  - T1-2 exact `double now_backoff`、参照禁止、単一宣言子、宣言数1。
  - T1-3 再宣言と代入・増減による再束縛拒否。
  - T1-4 jump、label、分岐、loop、try/catch の拒否。
  - T1-5 `static` / `thread_local` 拒否。
  - T1-6 有限・無損失整数 1..1000。
  - T1-7 type/raw-size preflight。
  - pytest実走 nodeid: なし、0件。全指定対象が runner infrastructure で開始前停止。
- 未実走・未解決:
  - `test_p3_s4_loop.py` 全体、import invariant、certified-writer caller inventory、collection meta-test。
  - mutation harness baselineとm01〜m14本走。
  - t441.m03の「受理集合変化」期待はT1-2による包含のため成立しない。
  - Tier 2、grammar identity/WAL/cache束縛、macro parityは未実装。
- 独自判断:
  - 上限を4096 code point、4096 UTF-8 byte、1024 token、nesting 64に固定。
  - loader互換のため数学的整数の `20.0` はvalueとして許可。ただし文字列、bool、小数、非有限値は拒否。
  - straight-lineを明確化するため、列挙されたjumpに加えて条件分岐、loop、try/catchもT1-4へ含めた。
  - Tier 2不実装を優先し、`001`、suffix、`1..0`、user-defined literalはTier 1 grammarでは落とさず既存帰属またはbuildへ残した。`value=100`の`1e2`だけは既存帰属regexで拒否されることを固定。
  - value gateはcap内の既存 `AttributionMismatch` の後、`int()` の前に配置。
  - consumer closureはproduction `render_hole` 呼出し集合が非空かつ `p3_s4_loop.quarantine` 1点であることとして固定。
- 波及の静的列挙:
  - `quarantine()` production callerは8 module、15 call site。直接backoff markerは `run_one_iteration` の2箇所だけ。
  - sort 3箇所、trigger 3箇所、各sweep、preview、direct comparisonはexact marker guardにより不変。
  - `record_diff_reject`、`load_diff_rejections`、`render_rejections` は新 subtypeをgenericな固定診断として消費。
  - 共有fixtureは `_TEMPLATE`、backoff/trigger/sort一時template helper。effect scanner fixtureの軸だけを移動。
  - 新nodeidは acceptance duration ledger未登録ですが、現行consumerは未知durationをfail-softに扱います。