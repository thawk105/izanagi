# 段 5 author 共通契約 ([T-2847] mocc-run)

正本: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/s4-ruling.md (段 4 裁定。R1 scope・R2 patch と発火診断・R3 cell・R4 期待と分類・R5 job・R8 所有)。
設計: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md、相談所見: codex/s3-consult-a.md・codex/s3-consult-b.md (裁定で採否済み。裁定と食い違えば裁定が正)。
どれか読めなければ即停止し、その旨だけを書いて終われ。

## 権限と境界

- 編集してよいのは、prompt が名指した所有 path だけ。docs (`*.md`) は編集しない。commit しない (起動器が終端で commit する)。
- `external/ccbench` (submodule、pin C `68106660`) の作業木・index を変更しない。複写して編集するときは unit worktree 直下の scratch (`.t2847-scratch/`、終了前に削除) を使う。
- 壊し patch を baseline に混ぜない (規律 2)。verifier・driver・condition gate の判定を変える編集はしない。tracked の driver (`orchestrator/campaign/s3_mocc_*.py`)、policy (`tools/pegasus/mocc_trace_v1_policy.json`)、既存 patch、calibration JSON は変えない。
- build はしない (login node の build は hook が拒否する。親が計算ノードで build する)。

## 検査と報告 (DW-S05-C)

- 緑には実走したコマンド・nodeid・範囲を併記。実走できなかったものは「実装済み・未実走」と書く。子の実走は親の全走を代替しない。
- fixture への現行 hash の差し込み等、テストを甘くして緑にしない。機構の正例・負例は実体を名指しし依存先を stub しない。
- 期待値へ揮発 payload を焼き込まない。
- 報告に所有外 caller・共有 fixture・consumer test への波及を静的に列挙する。
- 指示外の受理集合変更をしない。scope 前に現行の受理・拒否挙動を明記する。
- 最後に見出し「## 総括」を置く。
