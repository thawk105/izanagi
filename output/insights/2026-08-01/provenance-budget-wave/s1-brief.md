# 段 1 brief — docs/ai-provenance.md の予算逼迫を意味保存縮約で解消する

- wave: `dev-wave-provenance-budget` / branch `worktree-dev-wave-provenance-budget` / base `18d7fc3`
- site: PEGASUS_LOGIN (pegasus02)。login では静的検査と子の実行だけ。pytest と provenance 履歴監査は
  `tools/run_tests.py` / `check_ai_provenance.py` の sanctioned dispatch で計算ノードへ送る

## scope

- S1: `docs/ai-provenance.md` (実測 8,942 bytes / 予算 9,000、headroom 58 = 0.6%) を**意味保存縮約**し、
  **7,200 bytes 以下** (headroom 1,800 = 20% 以上) にする。編集面はこの 1 ファイルだけ (docs-only)。
- S2: 旧→新の**義務対応表**を insight へ凍結し、削除ゼロを機械的でなく逐語で追跡可能にする。
- scope 外 (裁定パッケージへ送る): 予算値の変更、doc 分割 (= 予算 schema 変更)、再肥大を止める
  ratchet 検査の新設、`check_docs` / `check_ai_provenance` の実装変更。

## 確定済みユーザー裁定・上位規律

- 予算値の引き上げは通常の自己改善に含めない (`docs/skill-self-improvement.md` §入口の編集条件、
  memory の T-127 裁定)。よって縮約のみで解決する。
- D105 却下案 (f): 「provenance から製品の優劣を断定するな」の解釈上の歯止めは**削らない**。
- D98 決定 4: 予算は `PROVENANCE_LIMITS` 独立 registry、9,000 exact 受理 / 9,001 拒否。

## 不変条件 (破ったら停止)

1. exactly-once メタテストが束縛する 3 逐語を各 1 回だけ保存する — CAB 配置文、Codex author 必須文、
   waiver trailer 形式。現状各 1 件を実測済み。
2. 義務の削除ゼロ。必須 trailer 形式、`AI-Agent: none` の排他、`scope` 必須条件、Codex author 契約と
   waiver 運用、CAB 連続配置、forward correction の成立条件 (「自身の通常 green」を含む)、記録単位、
   session URL 禁止、優劣断定の歯止めをすべて保存する。
3. 予算値・checker・test を変えない。green の定義は現行 `check_docs` / 現行 test のまま。
4. docs 間の行番号参照を作らない (LIVING_DOCS の `LINE_REF_STRICT`)。

## 前提の実測結果 (段 1 前提実測)

- `check_docs.py` は現状 green。凍結 manifest / trust root による bytes pin は皆無 (`grep --include=*.py` で
  test fixture・予算 registry・LIVING_DOCS 登録のみ) → `DW-O09`/`DW-O10` は不発火。
- checker の epoch 検出は `git log -S <needle> --reverse` の**最初の**出現 (実測: Codex author = `8c6d3f3`
  2026-07-29、CAB = `9b26b3b` 同日) なので、現行本文の縮約では epoch は動かない **(P4、段 3 の攻撃対象)**。
- `6b64d21` の target SHA は checker 側定数で、docs からは読まれない。

## provisional 裁定 (親の暫定判断であり攻撃対象)

- (P1) 縮約対象は散文の重複・冗長な言い換え・例示の多重化だけで、義務文は 1 つも消さない。
- (P2) forward correction 節 (819 bytes) は D101 が正本なので、公表契約に要る成立条件だけ残して縮約できる。
- (P3) 目標 7,200 bytes は義務保存のまま到達可能 (削減必要量 1,742 bytes = 現行の 19.5%)。
- (P5) docs-only のため D95/D105 の Codex author 契約は対象外で、親が本文を編集してよい。

## 成果物影響 (`DW-G05`)

放置すると、次に provenance 規約へ義務を 1 行足す変更 (58 bytes 超) が `check_docs` 赤で入らず、
「未審査の予算引き上げ」か「義務の削除」のどちらかへ圧力がかかる。provenance は台帳の AI 帰属欄と
`check_ai_provenance` 監査の正本なので、どちらに倒れても台帳の帰属記録が検証不能側へ動く。

## 成果物の形・分割方針

- 成果物: 縮約後の `docs/ai-provenance.md` 1 ファイル、義務対応表 insight、worklog エントリ。
- 単一ファイルの docs-only なので実装並列はしない。子は read-only codex のみ:
  段 2 planner 1 本、段 3 敵対 2 本 (A = 義務保存・正しさ防壁、B = 機械束縛と checker epoch・lint 構造)、
  段 6 レビュー 2 本。段 5 の本文編集は親が行う。
- 受入: 計算ノードで `run_tests.py` 全走 + `check_docs` + `check_ai_provenance` + `git diff --check`。
  変異 matrix は「3 逐語を 1 つずつ落とすと exactly-once メタテストが赤になるか」の positive control を
  統合 commit 後に `DW-O19` で本走する。
