# 段 1 brief — [T-1505] A-1 balanced5 sized 本走を 1 attempt 投入する (2026-09-18 06:2x JST)

- 研究前進: 論文 headline 証拠 paper-story A-1 の sized 本走 (study `paper-story-a1-20260901-balanced5-sized-v1`、3 workload × 30 対、`formal=false` / `result_authority=sized-preregistered-descriptive-only`) を初めて実機で完走させ、A-1 状態欄 (`docs/paper-story/claim-evidence/2026-08-26.md` A-1 行「実証は 0 件のまま」、`docs/paper-story/2026-09-17.md`) に「sized 本走 1 attempt の outer status」を書ける材料を作る。完了判定 = 3 job が driver rc 0 で終端、`complete` rc 0 で group terminal、`materialize` rc 0 で固定 leaf 生成、各 workload の valid / errors と outer status を insight に記録。落ちた場合 = 落ちた層・失敗受領証・request ID を insight に記録して止める (再投入しない)。
- 確定済みユーザー裁定: D2120 項 3 (択 (a)、2026-09-17)。前提条件「pilot 専用分岐を外す実装が閉じた」は entry 1590 (commit ad83b108b、変異 10/10 KILLED、受入緑) で成立。D2120 以降 (D2121〜D2134) と spool に本件を止める裁定は無い (実測 06:2x JST)。
- scope: 既存 submit 経路 1 attempt の投入・待ち・complete・materialize・insight 化・記録だけ。実装差分ゼロ (実装面 0 byte、変異 matrix 免除、受入全走は免除しない)。gate・検査・台帳・一般化の追加なし。
- 不変条件: 規律 2 (既存 verifier の anomaly → reject をそのまま)。submit-tree は投入後 1 byte も書かない (F936 型)。v1 契約・pilot 公開先 `output/insights/2026-09-01_paper-story-a1-balanced5-pilot/` に書き足さない。事前登録 README (sha 6047eff0…)・policy (a6228bcd…)・source v2 契約 (b50a4edf…)・追補 (6093de24…) は変えない (sha は wave worktree で実測一致)。
- 実測環境: 投入は login node から job dir 下の submit-tree (local main d2ebef7a4 の detached worktree、submodule 再帰初期化、lock)。実行は Pegasus 計算ノード (queue gen_S、1 workload = 1 job = 1 node)。所要見込み = pilot attempt-0004 (60 対) が投入 08:51 → 全終端 09:15 の 24 分、sized は 30 対なので bench 部は概ね半分 + queue 待ち (06:1x JST 時点で cluster QUE 36 / RUN 32)。
- 成果物の形: (1) `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md` (投入 argv・request ID・node・各層の rc・outer status・言わないこと) + 受領証 (submission / completion / group terminal / 各 job-terminal) と materialize 受領証の byte 保持コピー。(2) materialize の固定 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` (policy `materialization_relative_path`、排他作成) を submit-tree から wave worktree へ byte 保持で複製し commit。(3) worklog fragment 1 本。decisions fragment なし (新しい設計判断なし)。A-1 状態欄の本文更新は別 wave (本 wave は材料まで)。
- 並列分割方針: 子ゼロ (docs-only + 親の実測)。設計択一・正しさ防壁・受理集合の変更が無いので段 2・3・6 の子は省く (DW-C00 軽量版)。
- 変更面 (実アンカー): repo 内の編集は `output/insights/2026-09-18/t1505-a1-sized-attempt1/**` (新規)、`output/insights/2026-09-13/paper-story-a1-balanced5-sized/**` (新規、materializer 出力の複製)、`docs/spool/worklog/*.md` (新規 fragment) のみ。

## 親の provisional 裁定 (攻撃対象)

- (P1) attempt 名は `attempt-0001`。sized の attempt 名は契約で pin されず (D2096、追補「attempt 番号は pin しない」)、耐久 base `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement` は未作成 (submit が mkdir する) なので先行 attempt は 0 本。
- (P2) 依存供給は 2 箇所へ hydrate する: (a) submit-tree 既定 staging root `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` (gitignore 済み、job body が gflags / glog を読む既定 root、`tools/pegasus/README.md` §6)、(b) job dir `third-party-hydrated` (`--third-party-source-root`、job body が masstree / mimalloc / googletest を `cp -a` する root、pilot attempt-0004 と同形)。cache は 5 本 pin 一致 (verify rc=0)。pilot 時 (2026-09-11) は helper が 3 本で gflags / glog の供給が別経路だったため、pilot と完全同形ではない — 差は job 冒頭の dependency preflight (HEAD / dirty 検査) が判定する。
- (P3) 段構成は 1 → 4 (実装しない) → 実測 (submit / 待ち / complete / materialize) → 7 → 8 → 9。実測が途中で落ちても段 7 以降は行い、落ちた層を insight に記録する。

## 模擬 / 実の差

- 模擬なし。submit・job・complete・materialize はすべて実機・実 tree。
- 棚卸し: job body の外部 command は cmake / gcc / g++ / qsub のみ (pilot と同じ)。qsub 変数は `_canonical_qsub_contract` / `_v3_group_intent` が組む (`IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT` を含む)。gflags / glog 用の `IZANAGI_THIRDPARTY_SOURCE_ROOT` は qsub に渡さず既定 root を使う。qstat parser は `orchestrator/scheduler_nqsv` 委譲 (pilot で実機通過)。
