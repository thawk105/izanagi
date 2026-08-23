# [T-986] freeze v2 budget pin 承認パッケージ
- 目的: budget pin の見積り根拠・pilot 実測・不確実性を整備し、数値承認前の承認パッケージを作る
- 状態: 作業中
- 最終更新: 2026-08-24 02:35 JST
- 基準コミット: 768e9fe62e6fecd50280bd95771159947e08c4d8 (worktree: worktree-dev-wave-t986-budget-approval-package)

## 完了した中間成果

- `AGENTS.md` / `CLAUDE.md` / dev-wave dispatcher と開始時必読資料を確認した。
- main、worktree、branch、repo 内外 handoff を照合した。T-1484/T-1505 は別 worktree で
  attempt registry の変異本走中で、編集面は `attempt_registry_core.py` / `trial_registry.py` 系。
- 本 wave は budget 承認資料を中心とし、暫定 pin、official guard 解禁、正式 launch を行わない。
- 専用 worktree を main `768e9fe6` から作成し、`tools/dev_wave_submodule_init.py` で再帰 submodule
  初期化を完了した。通常の `git submodule update --init` は file transport 禁止で失敗したため、
  失敗を初期化済みとは扱わず helper で是正した。
- 段 1 brief を repo 外 job dir の `stage1-brief.md` に確定した。Pegasus の既存 sanctioned pilot
  132 session を一次 result から再集計し、平均 26.7810 秒、最大 26.8686 秒、全 rep rc=0 を確認した。
- `n=8` 条件の provisional 候補は 27 秒/session の切上げで total=2592、holdout ごと=1296 秒。
  ただし現行 reservation envelope が名目 2400/1200 のままになる疑義を段 2/3 の攻撃対象とした。
- 段 2 plan と段 3 敵対 2 レンズを完了。初回 plan は `max_model_calls=1` で output 0 byte のため
  不採用・receipt 保全し、別 job ID の再投入を採用した。3 成果物はいずれも output validator 緑。
- 段 4 裁定は operational 数値承認を保留。2592/1296 は conditional planning candidate、
  2400/1200 は現行名目 reservation としてのみ提示する。追加実装・追加計測は scope 外。
- 関連焦点走は21 passed (17.12s)。先行2走は `/tmp/.git` / `dev-wave-jobs/.git` ancestor による
  既知F457の前段 refusalで、production predicateを変えずGit ancestorの無いbasetempへ分離して緑を得た。

## 未完の作業と次の一手

1. local main 固定SHAを取り込み、記録後検査と受入を完了する。
2. 段 8 自己改善裁定と段 9 land を閉じる。

## 落とし穴・気づき

- T-1484 は `mutation_harness.py --force-dispatch` の 6 変異本走中。計算ノード負荷を重ねない。
- T-1484 は変異本走を完了し、現在は acceptance 中。T-986 は新しい性能計測を起こさないため、
  編集面・性能計測面とも重複しない。acceptance の所有物には触らない。
- budget approval の `BUDGET_APPROVAL_SHA256` は `None` のまま維持し、approval JSON を発行しない。
- 性能値は trace-disabled・計算ノード・環境 tag 付きの実測だけを根拠にする。

## dev-wave 改善候補

1. 段 2 plan の初回 dispatch に `--max-model-calls 1` を指定したところ、1 call 目を射影資料の
   読取に使って `f45_missing_output` (output 0 byte) で停止した。既存 receipt/done を保全し、別 job
   ID・4 calls で再投入して完了した。`DW-O01` は上限を上げてよいとは書くが、projection を読む
   read-only plan/consult で 1 call が実質不足になる実測を持たない。段 8 で既存節への候補 routing を
   裁定する。改善作業は本 wave に追加しない。
