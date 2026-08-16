# 再適用 + 合成監査 報告

## 1. 再適用した wave 側変更の一覧

- admission-aware wrapper と cell ごとの admission 解決を、main 版の補助関数群の後ろへ配置した。[s8b_floor_campaign.py:3702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:3702)
- `_Runner` に admission mapping を必須化し、実走開始前に全 cell の集合一致と receipt を検査するよう再適用した。[s8b_floor_campaign.py:3772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:3772) [s8b_floor_campaign.py:4131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:4131)
- public production entrypoint で全 callable seam を拒否し、pilot の不可逆承認を private core 側で必須化した。[s8b_floor_campaign.py:4633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:4633) [s8b_floor_campaign.py:4697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:4697)
- admission の取得を、main が追加した FetchContent build、manifest、portable artifact 検査の後、`runner.run()` の直前へ移植した。[s8b_floor_campaign.py:5013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5013) [s8b_floor_campaign.py:5209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5209) [s8b_floor_campaign.py:5221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5221)
- 外部 4 引数 callback を wrapper で包み、callback の直前に attempt ticket を durable 消費するようにした。既定 closure は観測許可を `measure_point` へ渡す。[s8b_floor_campaign.py:5240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5240)
- CLI の pilot 承認フラグと、main からの転送を再適用した。[s8b_floor_campaign.py:5668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5668) [s8b_floor_campaign.py:5810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5810)
- 対応テストを main 版 fixture へ統合した。合成 fixture の holdout 名は `rr79` / `rr23` のまま維持した。[test_s8b_floor_campaign.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_floor_campaign.py:80)

## 2. 合成監査 — 両側変更が共存できている根拠

- main 側の変更は FetchContent dependency の事前 build と receipt 生成である。build、store projection、manifest、portable artifact 検査が完了してから admission を発行するため、測定しない preflight の成功後という wave 側の順序保証を維持している。[s8b_floor_campaign.py:5013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5013) [s8b_floor_campaign.py:5045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5045) [s8b_floor_campaign.py:5221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5221)
- admission の全 cell exact 検査は `_Runner.run()` 冒頭にあり、host/process 検査や session 実走より先に行われる。[s8b_floor_campaign.py:4131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:4131)
- callback 呼び出し規約は外部 4 引数のまま保ち、内部だけ admission-aware な引数へ拡張した。main 側の caller 変更との衝突はない。[s8b_floor_campaign.py:3990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:3990)
- public production caller である `main()` は新しい不可逆承認フラグを明示的に転送している。[s8b_floor_campaign.py:5829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:5829)
- ledger 発行後に journal が存在しない resume の拒否と、admission 前に測定 preflight が呼ばれないことをテストへ統合した。[test_s8b_floor_campaign.py:3804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_floor_campaign.py:3804) [test_s8b_floor_campaign.py:3874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_floor_campaign.py:3874)

共存不能な変更は確認されなかった。

## 3. 新規 spawn site の実体と分類

`campaign/buildcache.py` の新規 site は、次の Git 情報を取得するだけの process 起動だった。

- `git -C <source_dir> rev-parse --show-toplevel`
- `git -C <source_dir> rev-parse --verify HEAD`

これは FetchContent dependency receipt を repository root と commit に結び付ける処理であり、argv に CCBench executable や `ycsb` workload を組み立てる経路がない。[buildcache.py:759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/buildcache.py:759)

したがって「ccbench でない process 起動」へ分類し、根拠を exact inventory のコメントに記録した。[test_ccbench_spawn_sites.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_ccbench_spawn_sites.py:70)

## 4. 検出力を落としていない根拠

recursive inventory、exact 集合比較、CCBench measurement site の bounded 判定には変更を加えていない。追加したのは関数完全修飾名が一致する一つの非 CCBench process site と、その argv 根拠だけである。

既存期待値の反転、緩和、skip、削除は行っていない。

## 5. 実走したテスト / 実走できなかったもの

以下の nodeid を `tools/run_tests.py --force-dispatch ... -q` で実行要求した。

- spawn inventory の2テスト
- public callable seam 拒否
- pilot 不可逆承認
- admission 順序
- real claim、ledger、ticket
- journal 不在 resume 拒否
- default measurement forwarding
- `_Runner` admission mapping exact 検査

しかし `qstat -Q preflight rc=1` により runner が `rc=16` で停止し、テスト本体は実走されなかった。force-dispatch なしの再試行も headroom 判定後に同じ dispatch 障害となった。

したがって状態は「実装済み・未実走」であり、テスト緑は主張しない。補助確認として、編集した3ファイルの AST parse と NFC・結合文字検査は成功した。

## 6. 落とした変更があればその一覧と理由

無し。

## 総括

wave 側の holdout admission 契約を main 版の FetchContent build 経路上へ再適用した。  
admission は全非測定 preflight 後、runner 実走直前に取得される。  
main 側との API・順序上の非互換は確認されなかった。  
新規 spawn site は根拠付きで非 CCBench process 起動へ分類した。  
docs 編集、commit、Git サブコマンド実行は行っていない。  
テストは dispatch 基盤障害のため未実走である。