# 2026-07-13 提案ラウンド束 (S-2/C4/C5) — 実走の引き継ぎ (次セッション向け)

**状態: 実走準備完了・中断 (ユーザー指示で次セッションへ)。gate 残 2 点から再開する。**
経緯の worklog 正本 = 07-13 (4)(5) エントリ。設計正本 = `output/insights/2026-07-13_s6-round-execution-design.md` (v2)。

## 再開手順 (このまま上から)

1. **gate 残 2 点をユーザーに確認:**
   - **master seed** — ユーザーが整数 1 つを独立確定 (`! echo $RANDOM$RANDOM` を案内済み)。
     **準備者 (Claude) が候補を提示・試算することは禁止** (v2 §3.2、帰無分布 cherry-pick 対策)
   - **実走開始承認** — 見積もり **$18〜46** (cache 命中率依存。射影 18k tokens/呼 × 60 +
     採点 60〜120 件)。性能計測ゼロ・計測窓不使用
2. 凍結コミット: 契約追記は適用済み (391fda4)。採点プロンプト 2 ファイルは敵対チェック
   反映済み (39b8733) — 凍結の実体は freeze が生成する hash 台帳
3. `python3 orchestrator/campaign/s6_proposal_rounds.py freeze --master-seed <s>` →
   `output/s6-rounds/frozen/` 生成 (ペイロード 60・C4 抽出列・実行順・採点定型部・hash 台帳)。
   **生成物を即コミット (提案生成前 = freeze-before-observation)**
4. `... verify` (鮮度 3 述語 + 凍結物 hash + アーム間単一差分。fail = 実走しない)
5. `... run --neutral-cwd /home/tanab/tmp/s6-rounds-cwd` (60 スロット、再開冪等 —
   途中死しても再実行で続きから)
6. `... anonymize` → `... score --neutral-cwd ...` (採点カウンタ 120 機械執行) → `... tally`
7. **採点 reason の人間監査** (全 c*_reason を通読 — 集計後・報告前の明示の段、v2 §9)
8. worklog エントリ + この handoff の吸収・削除

## 主要ファイル

- 設計 v2: `output/insights/2026-07-13_s6-round-execution-design.md` (§3 機械手続き / §5 採点 /
  §9 gate と手順)
- レビュー台帳: 同 `-review.json` (v1 全文込み) / 採点器チェック: `..._s6-scoring-prompt-check.json`
- driver: `orchestrator/campaign/s6_proposal_rounds.py` (構文チェック済み・未実走)
- 採点プロンプト: `orchestrator/campaign/s6_scoring_prompt_system.txt` + `_user_template.txt`
- 契約追記適用済み: `.claude/agents/axis-proposer.md` (391fda4、実走完了まで変更凍結)

## 注意 (次セッションの Claude へ)

- 実走前に必ず `verify` を通す (fails-closed — 1 述語でも不成立なら人間判断)
- claude -p の呼び出しフラグ (`--system-prompt` / `--output-format json` /
  `--exclude-dynamic-system-prompt-sections` / `--disallowedTools`) は canary 07-13 (1) の
  遮断構成 — 本走前に preflight (保有ツール NONE の実測) を 1 本流すこと (canary の前例)。
  effort 指定が headless で効かない場合は §7 変更点台帳への追記を忘れない
- 60 ラウンドの実走中は心拍規律 (約 1 分周期の日本語進捗) + スロット単位の中間 provenance
