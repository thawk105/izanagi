# 独立再命名 canary — 実行記録と人間裁定台帳 (D52 着手順 1)

- **日付:** 2026-07-13
- **位置づけ:** D52 の trigger-gating headline (S-1) 昇格の形式要件。計測ゼロ。
- **正本:** `docs/phase3-main-experiment.md` 2026-07-12 追記 / `output/insights/2026-07-12_s6-headline-system-level-reframe-draft.md` §3
- **一次資料 (全文・hash):** `output/insights/2026-07-13_s6-canary-rename-provenance.json` + 匿名化 patch 実体 `output/insights/2026-07-13_s6-canary-anonymized.patch`

## 手続きの実装 (§3 (i)〜(iii) の充足)

1. **匿名化 (機械的):** `orchestrator/campaign/s6_canary_rename.py` — 骨格導入識別子の
   rename (14 対) + 追加行のコメント全除去 (EVOLVE-BLOCK マーカー行含む、人為選別なし) +
   説明スロット (CACHE STRING docstring / #error メッセージ) の空化。等価性は preprocess 同値
   (cpp -fpreprocessed -P、pinned stock に両 patch を適用して比較) で機械検証 = **PASS**。
   検証は開発中に実バグ (hunk ヘッダ再計算漏れによる同型コンテキスト 2 箇所の入れ違い適用) を
   fails-closed で検出しており、恒真でない。
2. **再命名者 (fresh・ツールなし相当):** agent 定義のセッション開始時登録制約のため
   `claude -p` headless 新プロセスで実現 — 全ツール disallow (事前 preflight で保有ツール
   NONE を実測確認)・動的システムプロンプト節の除去・リポジトリ外の中立 cwd。入力 =
   匿名化 patch 全文 + 偵察の生死二値 1 ビットのみ (D48 条件 7 と同一粒度)。model = opus
   (axis-proposer 前例と同格)。
3. **一致判定 (第三コンテキスト・fails-closed):** 同じ遮断機構の別 fresh プロセス。両命名の
   由来を伏せ提示順は乱数化 (今回 A,B = 元,再命名)。曖昧は不一致に倒す規則を明示。

## 結果

| 項目 | 値 |
|---|---|
| 元命名 | silo-backoff-trigger-gating |
| 再命名 (中立命名) | **abort-cause-gated-backoff** |
| 構造 3 項の判定 | **match = true** (3 項全対応) |
| canary 発火 | **なし** (発火 = 不一致時のみ) |

再命名者は匿名構造のみから「thread_local の abort 要因 8 カテゴリ記録 (begin() で sentinel
リセット) / 記録された要因に応じた backoff 発火可否の分岐 / Backoff::backoff(FLAGS_clocks_per_us)
呼出の gate」の 3 項を再導出し、「現状 flag_x は常時 true だが構造上ここが可変点」まで指摘した
(全文は provenance JSON)。判定者の曖昧点は action_site の位置表現差 (abort() 末尾 vs リトライ
経路) のみで、呼出対象の完全一致により同一と判断。

## 限界 (§3 の自認の再掲 — 変更なし)

匿名化しても骨格構造自体が意味を運ぶため一致はほぼ確実 (circular)。**一致を「写経なし」の
肯定的証拠として報告に使わない。** 写経検査は provenance 三点セット + B レビュー転写検査が担う。
本工程は不一致時のみ発火する canary である。準備者 (メインセッション) は元命名・シート・提案を
読んだ上で匿名化と元側 3 項の構成を行った (射影者の記憶汚染と同型の自認 — provenance が代償)。

## 人間裁定 (最終裁定者 = 人間、D47 決定 5 の充足)

- **status: 追認 (2026-07-13、ユーザー裁定)**
- 裁定対象: 一致判定の追認可否 → **追認**。構造 3 項の対応表と唯一の曖昧点 (action_site の
  位置表現差 — 匿名化 patch では hunk 範囲外の関数名が不可視なための必然的な差、gate される
  呼出 `Backoff::backoff(FLAGS_clocks_per_us)` は完全一致) の解消理由を提示の上で追認を得た
- 帰結: S-1 昇格の形式要件のうち canary は充足。命名 provenance 完全記録は本記録が担う。
  一致を肯定的証拠に使わない扱い (§限界) は不変
