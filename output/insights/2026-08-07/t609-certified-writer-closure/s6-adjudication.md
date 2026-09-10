# 段 6 所見の裁定 (親) — fix 指示の正本

段 6 レンズ C (must-fix 6) / レンズ D (must-fix 4) と、親が実測した回帰 1 件を裁定する。
逐語は `s6-lensC.md` / `s6-lensD.md`。ここには裁定と fix 指示だけを書く。

| # | 出所 | 裁定 | 処置 | 担当 |
|---|---|---|---|---|
| R1 | 親実測 | real | preflight bootstrap の interpreter ループが既存 operational ループと**同一文字列**を先に出現させ、既存順序テストが別行を拾う。bootstrap 側の文字列を別形へ変える (例: ループ変数を `preflight_py_name` にする)。**既存テストは変えない** | B' |
| R2 | C-1 | real | `env_tag` / `clocks_per_us` に exact 型検査 (`type(x) is str` / `type(x) is int`) を追加。equality を偽装する object と `1800.0` を負例に足す | A' |
| R3 | C-2 | real | build selector が非 None なら比較の**前に** `type(env_contract) is ExecutionEnvironmentContract` を要求。custom-equality subclass を負例に足す | A' |
| R4 | C-3 | real | `prepare_screening_campaign()` に認可を必須化し、`layout.ensure()` と WAL repair より**前**に集中述語を呼ぶ。production caller も配線 | A' |
| R5 | C-4 / D-1 | real | **source-commit 束縛が adapter 1 ファイルしか効いていない。** `admit()` を呼ぶ直前に、`sys.modules` のうち repo root 配下の全 module について、その file bytes が receipt の `source_commit` の同 path blob と一致することを検査し、不一致・blob 不在なら exit 3/4 で拒否する。B 側 module を fail-open に書き換えても A の job が拒否される負例テストを足す | A' |
| R6 | C-5 | real | M2 の fixture が過剰決定。runtime 3 値は登録値と同一のまま `calibration_ref` か `isolation_policy` だけを変えた exact dataclass に差し替え、registry 同値検査だけを消すと受理される形にする | A' |
| R7 | C-6 / D-5 | real | P-2 正例が実 admission を一度も通っていない。current registry・正しい protocol/calibration・receipt/ledger/qsub binding を持つ実 fixture で `admit("floor")` と `admit("t126")` を直接通す正例を足し、同じ fixture を wrapper 境界正例にも使う | A'(CLI 正例) / B'(wrapper 正例) |
| R8 | C-7 | real (should-fix) | `numactl is None` の単独 branch は直後の exact list/tuple 検査に覆われ過剰決定。両者を 1 つの shape gate に統合し、変異 M4 は「shape gate 全体を旧 falsy-collapse へ置換」と定義し直す (`DW-M03`) | A' |
| R9 | D-2 | **real / 但し gate は変えない** | floor は既存設計で「現 HEAD == receipt commit」を要求する。したがって floor では source-commit 束縛と現 worktree 束縛が一致し、A→B drift は既存 gate が (最初の書込みの後で) 拒否する。**この既存 gate を receipt 基準へ変えるのは受入集合の変更であり scope 外。** fix は「A/B drift を誤拒否しない」という**主張の方を撤回**し、B のテストが floor について drift 耐性を主張しないよう直すこと。T126 は receipt commit から source stage を作るため R5 の束縛が実効する | B' |
| R10 | D-3 | real | T126 の request 検査が共有 policy の `floor_walltime_s` を参照している。mode 別にし、T126 では commit 由来の T126 固有 policy の walltime を使う。共有 policy からは project/queue/nodes だけ取る。floor と T126 の walltime を意図的に違えた正例を足す | A' |
| R11 | D-4 | real | `test_trigger_gate_binding.py:401,419` が `Signature.bind()` に認可を渡していない。**期待値ではなく入力**に `authorization_contract=object()` を足す (signature binding だけを見るテストなので型は問わない) | A' |

## 全 fix 共通の制約

- 段 5 実装子契約 (`DW-S05-A` / `DW-S05-B` / `DW-S05-C`) を全文継承する。
- **既存テストの期待値を変更してはならない。** 反転・緩和・skip・削除を禁じる。
  赤なら実装側が誤りとする。期待値が誤りだと判断したら実装を変えず報告して止まる。
- 受理集合を、この表に書かれていない方向へ拡大・縮小しない。
- docs を編集しない。commit しない。
- 所有パスは A' と B' で素集合を保つ。

## 変異台帳の更新 (`DW-M07`)

- M2 は R6 で再照準する。旧 fixture での結果は erratum として残す。
- M4 は R8 で「shape gate 全体の置換」へ定義し直す。単独 branch の kill は証拠から外す。
- M1 の exact 型部分は単一理由 kill になっていないとレンズ C が指摘した。
  R2/R3 で型検査が独立の負例を持つため、M1 は「必須引数の欠落と明示 None」に限定する。
- R5 の新負例を M8 として追加登録する
  (source commit と異なる domain module bytes を拒否する。単一理由: 他層に同じ検査がない)。
