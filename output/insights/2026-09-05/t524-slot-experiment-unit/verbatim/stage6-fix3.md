## 赤 13 件の原因

親の R2 診断は production defect として正しかったです。

- `test_p5_six_complete_terminal_reports_pass_acceptance` は、outer receipt の `prereg_commit` と row の `prereg_content_commit` を誤照合し、genesis も誤った commit で探索していました。
- 残る 12 件は同型です。fixture が既存 genesis の slot 配列を順序込みで比較し、`on/off/swapped` 順と `slot_id` 順の差で verifier 到達前に失敗していました。key 構成や値ではなく順序だけの差です。
- 対象は v5 正例、M3/M3b/M4、manifest/content binding 負例、第二 root 負例、P1/P2、v4 readability、cross-binding 2 件です。

## 直した内容

- [s8c_acceptance_receipt.py:73](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix3/orchestrator/campaign/s8c_acceptance_receipt.py:73): v5 receipt に既存名の `prereg_content_commit` と `prereg_effective_commit` を必須追加。
- [s8c_acceptance_receipt.py:814](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix3/orchestrator/campaign/s8c_acceptance_receipt.py:814): 両 commit を strict parse。
- [s8c_acceptance_receipt.py:1583](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix3/orchestrator/campaign/s8c_acceptance_receipt.py:1583): attempt row の同名 field と双方を exact 照合。
- [s8c_acceptance_receipt.py:1602](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix3/orchestrator/campaign/s8c_acceptance_receipt.py:1602): genesis 探索先を `prereg_content_commit` へ修正。
- [trial_registry.py:6342](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix3/orchestrator/campaign/trial_registry.py:6342): issuer が検証済み content/effective binding を receipt へ搬送。
- [test_s8c_acceptance_receipt_v2.py:324](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix3/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:324): slot 配列を `slot_id` で正規化して exact 比較。期待値を観測値へ置換していません。
- [test_s8c_acceptance_receipt_v2.py:1099](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix3/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1099): content/effective commit の各不一致を独立に拒否する負例を整備。
- [test_trial_registry.py:1711](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix3/orchestrator/tests/test_trial_registry.py:1711): 統合正例で三種の commit が別物であることを確認。
- [test_reflux_originless_compatibility.py:901](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix3/orchestrator/tests/test_reflux_originless_compatibility.py:901): v5 追加 field を互換 projection で検査して消費。

## R1〜R5 の意図が維持されていること

- R1: v1〜v4 は読取可能なままですが、下流 capability は引き続き current v5 のみです。
- R2: manifest hash、content commit、effective commit、P 時点 genesis-only を厳密検査します。
- R3: `rev-list --all` と全 tree path の第二 root 検査は変更していません。
- R4: `attempt_registry_prefix_bytes` の揮発分類を維持しています。
- R5: projection 再照合と M3b の単独変異 killer を維持しています。

## 実走したテスト

**実装済み・未実走**です。

指定コマンドと焦点 nodeid の絞り込み走を `tools/run_tests.py` 経由で計 3 回試みましたが、すべて Pegasus の `qstat -Q` preflight が `rc=16` となりました。`child_started=false` のため、実際に開始された nodeid や合否結果はありません。

静的確認は以下を通過しています。

- 変更 5 ファイルの AST parse: 成功
- `git diff --check`: 成功

## 受理・拒否挙動の変化

受理集合は広がっていません。正規 v5 receipt が誤った commit 種別比較で拒否される不具合を除去しつつ、v5 は新しい二 field を必須とし、row との content/effective exact 一致を追加したため、境界は厳しくなる向きです。

slot 順序の修正はテスト fixture 内だけで、全 key と値の exact 一致は維持しています。旧 schema、第二 root、後付け genesis、projection 不一致、terminal 欠落などの拒否は緩めていません。

## 親の裁定が要る点

なし。

## 総括

R2 の commit 種別取り違えと、焦点走に現れた slot 順序依存を修正しました。  
変更は production 2 ファイルと関連テスト 3 ファイルだけです。  
docs、規律ファイル、固定 g1〜g13、拒否分岐は変更していません。  
commit と push は実行していません。  
テストは Pegasus infrastructure failure のため未実走です。