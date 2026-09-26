# 段 5 author 共通契約 ([T-2847] si-v2)

正本: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/s4-ruling.md (段 4 裁定。R1 scope・R2 発火診断・R3 cell・R4 期待と分類・R5 登録・R6 起動器・R8 所有)。
設計: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/codex/s2-plan.md、相談所見: codex/s3-consult-a.md・codex/s3-consult-b.md (裁定で採否済み。裁定と食い違えば裁定が正)。
どれか読めなければ即停止し、その旨だけを書いて終われ。

## 権限と境界

- 絶対に `git add` / `git commit` を実行しない。commit は親が行う (起動器が終端で残差を記録する)。
- 編集してよいのは、prompt が名指した所有 path だけ。docs (`*.md`、`patches/README.md` を含む) は編集しない。
- `external/ccbench` (submodule、pin C `68106660`) の作業木・index を変更しない。複写して編集するときは unit worktree 直下の scratch (`.t2847-scratch/`、終了前に削除) を使う。`git -C external/ccbench apply --check` のような作業木を変えない検査は使ってよい。
- 規律 2: 壊し patch を baseline (V2 対照) に混ぜない。verifier・parser・driver・condition gate の判定 (受理述語・供給経路・判定基準) を変える編集はしない。tracked の driver (`orchestrator/campaign/s3_*.py`)、policy、既存 patch (`patches/instr-si-trace-v2.patch` を含む)、calibration JSON は変えない。
- 共有 header (`external/ccbench/include/trace.hh`・`include/tpcc.hh`) を変える patch を作らない。
- build・benchmark はしない (login node の build は hook が拒否する。親が計算ノードで build する)。pytest も走らせられない (sandbox が socket を拒否する)。

## 検査と報告 (DW-S05-C)

- 緑には実走したコマンド・nodeid・範囲を併記。実走できなかったものは「実装済み・未実走」と書く。子の実走は親の全走を代替しない。pytest を走らせられない場合は、最低限 test module を import して対象 test 関数を直接呼び出し、fixture が成立するか確かめ、さらに対象の検査を除去して期待どおり赤化するかを確かめる (`tmp_path` は `tempfile.mkdtemp()` で代用してよい)。
- テスト新設・改名をしたなら、制約 meta-test を自ら洗い出し走らせる。fixture への現行 hash の差し込み等、テストを甘くして緑にしない。機構の正例・負例は実体を名指しし依存先を stub しない。
- 期待値へ揮発 payload を焼き込まない。既存テストの期待値は、登録件数の追随 (新しい総数) を除いて変えない。
- 報告に所有外 caller・共有 fixture・consumer test への波及を静的に列挙する。
- 指示外の受理集合変更をしない。scope 前に現行の受理・拒否挙動を明記する。
- 最後に見出し「## 総括」を置く。
