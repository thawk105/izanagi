# 段 1 brief — [T-316] R-1 (b) copy-out 厳格化 + (c) 併置、[T-840] 機械隔離

## scope (確定済みユーザー裁定)

裁定 = rulings-inbox `2026-08-12-coarse-provenance-45rulings.md` 34–35 行、確定済み。
- **A ([T-316] R-1 (b)):** build 出力 copy-out の厳格化 = 2026-08-09 裁定パッケージ R3-6 の must-fix。
- **B ([T-840]):** `quarantine()` を通らない coder-derived build 経路の成果物を
  「非認証成果物」として**機械隔離**する (同 wave 指定)。
- **C ([T-316] R-1 (c)):** 既 land の lexical 効果 gate (`coder_effect_gate.py`) を
  defense-in-depth として**併置**する。新規実装なし。A との関係を docstring/docs へ明示する。
- **不採用:** (a) source の DSL/IR 化。R1 が sort について明示却下済み。

## 段 1 実測 (承認済み裁定の前提。実測日 2026-08-12、base `a70a5acd`)

- **R3-6 の前提は現行コードで成立する。** `orchestrator/campaign/buildcache.py`:
  v2 は `staging_binary` を `os.path.isfile` (symlink を追う) で検査し、
  `os.rename(staging, bdir)` で **staging ディレクトリを丸ごと** publish する (809–851 行)。
  legacy も `os.path.exists` → `os.rename(staging, bdir)` (963–992 行)。
  許可ファイルの絞り込みも `O_NOFOLLOW` も symlink 拒否も無い。`full_sha256` も通常 open。
- **published cache dir の consumer は限定的**: `binary_relpath` の binary、
  `completion.json` (v2)、`admission.json` (legacy)。`_recheck_source_evidence` /
  `_assert_trace_diff` は bdir を**破棄先としてのみ**使い、中身を読まない (1006–1054 行)。
- **B の隔離先候補が既存**: `materializer_admission.py` は閉じたレジストリ +
  `CLOSED_PYTHON_MATERIALIZER_SITES` の AST site 閉包を持つ。`s5_permutation_coverage` は
  既に `NON_ADMISSIBLE`。未閉鎖は `p3_s4_red.py` / 手動 patch + `--allow-coder-derived-build` /
  直接 `buildcache` caller / shell materializer・任意 binary path。
- **`DW-O09` は不成立**: `FROZEN_MANIFEST` (`test_frozen_artifacts.py`) の 23 key は
  すべて `output/` 配下の成果物で、本 wave が触る orchestrator source を pin しない。
  よって `DW-O10` も適用外。段 7 の新規 insights 追加は既存 pin の bytes を変えない。
- **`DW-O08` 実行済み**: worktree で `git submodule update --init` rc=0。

## 不変条件 (緩めない)

- 規律 2: 本 wave は**受理集合を縮める方向のみ**。既存の正例 (正常な build) が落ちる変更は
  過剰拒否として扱い、通る正例を必ず添える (`DW-S04`)。
- 規律 1: trace/perf ビルド分離、`_assert_no_trace_symbols` / `_assert_trace_diff` の
  発火点と順序を変えない。
- T-841 (cache/WAL/COMMIT/freeze への gate receipt 束縛) は **scope 外**。裁定が
  「R3-3/R3-9 後」と明記している。B を receipt 束縛として実装しない。
- 「host-security boundary を得た」「certified が安全になった」とは主張しない。
- `materializer_admission` の第 2 レジストリを作らない (R3-8 の型)。

## provisional 裁定 (親の暫定判断。段 3 の攻撃対象)

- **(P1)** copy-out の実施点は v2 publish と legacy publish の 2 箇所で閉じる。
  staging から cache namespace へ出す第 3 の経路は無い。
- **(P2)** 許可集合は {`binary_relpath`, `completion.json`} (v2) /
  {binary, `admission.json`} (legacy) で足りる。cmake build tree (CMakeCache.txt・object) を
  publish しないことによる incremental rebuild の喪失は費用であって正しさの後退ではない。
- **(P3)** B は「coder-derived build entry point の閉じたレジストリ + AST 閉包検査」で実装する。
  artifact への receipt 束縛ではない。shell materializer / 任意 binary path は
  registry 上で**非認証と明示**するに留め、Python inventory 外の閉包は主張しない。
- **(P4)** A/B とも unit・integration で実測可能で、計算ノードでの実 build 走行は不要。

## 成果物影響 (`DW-G05`、1 行ずつ)

- **A 未実装**: untrusted build が staging に置いた symlink がそのまま cache dir に publish され、
  certified 選択が指す binary path が host 上の任意ファイルを指しうる (proof chain の binary 同一性が偽になる)。
- **B 未実装**: `quarantine()` を通らない経路で作った binary が certified 選択・proof chain に
  区別なく入りうる (台帳上「非認証」と読めない)。
- **C 未実装**: A が閉じない残余 (lexical に検出できる shell/IO/無退出 loop) が build 段まで到達する。

## 成果物の形

コード = `orchestrator/campaign/buildcache.py` の publish 経路、B の registry/閉包検査 (新 module 可)、
`orchestrator/tests/` の正負制御。docs = decisions fragment 1 件、worklog fragment 1 件、
insights パッケージ 1 件。**変異 matrix は事前登録し、A の symlink 拒否と B の閉包検査を
それぞれ殺す変異を最低 1 件ずつ含める** (`DW-M01`)。

## 分割方針

段 5 は所有分離で 2 実装子: 実装子 A = buildcache publish (A + C の docstring)、
実装子 B = 機械隔離 registry + 閉包検査。テストは各自の所有面に閉じる。

## 環境

受入全走 = Pegasus 計算ノード (dispatch recipe、`--force-dispatch` 必須)。
変異走行も同 recipe。所在の正本は worklog、機体固有は `docs/pegasus-runbook.md`。
