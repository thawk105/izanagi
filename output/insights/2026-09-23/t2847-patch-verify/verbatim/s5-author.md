## 作成した file

[t2847_launch/launch_patch_verify.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847pv-launcher/t2847_launch/launch_patch_verify.py) のみ新規作成しました。commit はしていません。repo root は必須の `--repo-root` から取得します。

## 差し替えの到達性 (file:line)

以下の driver 名は `orchestrator/campaign/` 配下です。

| 対象 | 到達先 |
|---|---|
| s2.PIN | `s2_verify_calibration.py:135,308` の既存 pin 照合 |
| compiler 定数 | s2 `:106,111,314`、s3 `:93,96,102,211`、s5 `:90,93,99,244` |
| stock build | s3 `:258`、s5 `:293`。`buildcache.py:3413` の定義時既定値を明示 cc/cxx/cache_root で補完 |
| source evidence | s3 `:257`、s5 `:292`。`source_digest.py:2418` の既定 cxx を明示指定 |
| 出力先 | from-import のローカル束縛を置換。s3 `:46,318`、s5 `:43,359`、t152 `:37,932` |
| ENV_TAG | s3 `:247,318`、s5 `:282,359` |
| t152 環境設定 | `t152_write_intent_coverage.py:827,833,836,837` |

`buildcache.py:3647` の内部 evidence 再照合にも明示 cxx が渡ります。対象経路の到達漏れは静的確認ではありません。s2 main の stock/performance 経路は呼びません。

## verifier 出力の保存箇所 (file:line)

subprocess 呼出しは次の4箇所です。

- s2 `s2_verify_calibration.py:206`
- s3 `s3_lock_coverage.py:169`
- s5 `s5_permutation_coverage.py:199`
- t152 `t152_write_intent_coverage.py:533`

起動器 `:56` の recorder が `<out-dir>/verifier/0001.json` 以降へ argv・rc・stdout 全文・stderr を保存し、元の CompletedProcess を返します。保存失敗は meta と stderr に記録します。verifier 以外は引数を変えず委譲します。

## 実行前提の確認

起動器 `:217` 以降に Python、CMake、policy/compiler 照合、s2 の補助実行体確認を実装しました。不成立は build 前に rc=2 と `preflight.json` へ記録します。

依存 helper は実シグネチャに合わせて `:258,259` で呼びます。CMake ファイルには指定された3つの依存 source path のみを書きます。終了時の meta 保存は `:297` の finally です。

## 実走した検査と未実走

- `python3 -m py_compile`：rc=0
- `--help`：rc=0
- 3つの path 引数それぞれの相対 path 拒否：すべて rc=2

build・driver・verifier・性能測定は実行していません。**実装済み・未実走**です。

## 波及

所有外の変更はありません。git status は `?? t2847_launch/` のみです。

- caller：既存コードから起動器への参照なし。
- 共有 fixture：変更なし。
- consumer test：`test_s5_permutation_coverage.py:10`、`test_t152_write_intent_coverage.py:21` は既存 driver を直接 import。変更不要。
- 既存 JSON consumer：`test_campaign.py:11438` の出力参照は維持。今回の出力は別 out-dir です。

## 未確認点

計算ノードでの依存準備、全 configure 経路への環境供給、実 verdict、保存失敗経路は未実走です。t152 の固定 `host_role="login-node"` は維持し、起動器 meta に hostname と注記を残します。

## 総括

指定の1 fileを作成しました。親による repo 外への退避と計算ノードでの実走に進める状態です。