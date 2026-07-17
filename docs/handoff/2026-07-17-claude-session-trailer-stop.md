# Claude-Session trailer の停止 + 履歴除去手順の提示
- 目的: commit message への Claude-Session URL 記録を止め (設定 + 規約)、既存履歴からの除去スクリプトを提示する (実行はユーザー承認後)
- 状態: 作業中
- 最終更新: 2026-07-17
- 基準コミット: 223bd83 (クリーン)

## 完了した中間成果
- 調査完了: セッション URL はアクセス制御された不透明 ID (公式 docs 確認済み)。repo は private (GitHub API 404)。影響コミット 50/460、最古 b6f7f64 (2026-07-13)。タグなし・署名なし・check_ai_provenance.py は SHA 固定なし (POLICY_PATH 導入 commit を動的検出)
- 全ローカルブランチが origin/main と同期または ancestor — 未 push 独自コミットなし (書き換えの好機)

## 未完の作業と次の一手
1. [完] 設定 2 件 (project + user) に `attribution.sessionUrl: false` — jq 検証済み
2. [完] `docs/ai-provenance.md` へ規約追記 — check_docs.py 違反なし
3. [完] `tools/strip_claude_session_trailers.sh` 作成 + 合成 repo で実地テスト成功
   (2 ブランチ・途中行 trailer・改行なし末尾 trailer、全て正しく除去、他 trailer 無傷)
4. [完] opus 敵対レビュー: 5 主張成立・real 4 件 (rebase 復活 / 未 push 盲点 / branch protection /
   PR 本文・refs/pull 残存) → 全て反映。preflight 追加 (負テストで発火確認済み)
5. [完] 追加依頼 (ユーザー): AI-Agent scope フィールド導入 — 規約 + checker (同 role 複数行で必須、
   -S 内容検出の epoch で遡及なし)。message-file 7 ケース + 全履歴監査 121 件 + check_docs 全て緑
6. [残] commit 2 本 (privacy / scope 分離) → worklog 吸収 → handoff 削除

## 落とし穴・気づき
- このセッション以降の commit には Claude-Session を付けない (ユーザー裁定 2026-07-17)
- 履歴書き換えの実行・force-push は絶対にしない — 手順提示のみ。push はユーザー (Pegasus 運用と同じ)
- 書き換え後は他マシンの clone (Pegasus 等) も fetch + reset が必要になる旨を手順に含める
