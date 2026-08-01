# 段 1 brief — トークン衛生監査 (claude 子 / codex 子の model・reasoning 経済)

- wave: 2026-08-01 token-hygiene-audit / branch `worktree-dev-wave-token-hygiene`
- 引数: 「claude, codex ともにエージェント呼び出しの際に不必要に高位モデルを呼んだり
  不必要に深い推論でトークンの無駄遣いが起きていないか」

## scope (成果物影響を 1 行ずつ、DW-G05)

- **S1 棚卸し**: 子起動面すべての model / reasoning を実測列挙する。放置しても certified 選択・
  レポート・台帳の値は変わらない → **運用経済のみ。must-fix にはしない (nit/backlog 扱い)**
- **S2 追跡実測**: 2026-07-19 監査で承認された是正が実際に適用済みかを一次資料で照合する。
  成果物影響なし (運用経済のみ)
- **S3 機械防壁の穴**: model/effort/reasoning の指定が機械検査されない経路を同定する。
  うち **reasoning 値の妥当性未検査 (F: `ultra` が rc=0 で通る) は成果物影響あり** —
  model×reasoning 比較台帳 ([T-181]/[T-182]/[T-184]) の `reasoning` field が
  「要求値」でしかなく served identity の attest でないため、台帳の比較主張が無根拠になりうる
- **S4 裁定パッケージ**: policy 変更 (段別 reasoning の引き下げ等) は本 wave では実装せず返す

## scope 外 (実装しない)

- 凍結実験契約の tier 変更 (`s6_proposal_rounds` proposer/scorer、`selector-8b`、`coder-v4` 系)
- `~/.claude/settings.json` の編集 — repo 外かつ AI 編集は classifier 拒否 (2026-07-19 と同じ)
- [T-189] (reasoning 許可リスト検証) の実装、[T-181] の認証再走 — 各々別タスク

## 確定済みユーザー裁定 (前提として使う)

- 2026-07-06 協議決着: メインループ = 日常 `high`、監査・設計の山場のみ `xhigh`。
  子は頻度 × 判断の重さで段差、effort は全 role 明示
- 2026-07-19 裁定 (a): 親既定 `fable[1m]/xhigh` → `opus/high` への引き下げを承認 (手動変更を引き渡し)
- 2026-07-19 裁定 (b): verifier の codex 列を terra/medium へ再ピン (D61)
- 一般原則 (2026-07-18): model と effort/reasoning は難易度に整合。過剰・過小の両方向を避ける

## 不変条件

- 正しさ防壁 (規律 1〜3) を経済最適化で緩めない。D61 の「削除でなく新値で再ピン」を踏襲する
- 受理集合を変えない。凍結成果物の bytes を変えない (`DW-O09` 非成立を確認済み)
- 実装面 (コード・テスト・機械設定) は本 wave では触らない → docs-only。触るなら Codex author 必須 (D95)
- push / remote 操作なし。`~/.claude/settings.json` は読むだけ

## 親の provisional 裁定 (攻撃対象)

- **(P1)** `DW-S02` (段 2 プラン起草) の `reasoning=max` は doctrine (「最難の敵対検証・設計攻撃 =
  max」) の適用範囲外で過剰である。根拠は [T-181] (max は POS +29.4% token / wall 1.52x、
  劣化未観測) だが **replay 未認証 n=6** で policy 根拠にできない → 実装せず裁定へ
- **(P2)** 実測した親既定 `model=opus[1m]` / `effortLevel=xhigh` のうち **effort 側は
  2026-07-19 承認裁定の未適用分**である (model 側は適用済み)。後続の別裁定で xhigh 維持が
  決まっていないかの反証を求める
- **(P3)** Agent tool には `effort` パラメータが構造的に存在せず、ad-hoc claude 子の effort は
  セッション値の無条件継承である。よって「ad-hoc 子は model と effort を毎回明示」という規律は
  Workflow `agent()` でしか満たせない
- **(P4)** named role 13 件の tier は 2026-07-19 監査で triage 済みで、再変更を要する role はない

## 成果物の形

1. `output/insights/2026-08-01_token-hygiene-audit/audit.md` — 全面の実測表 + real/refuted 裁定 +
   裁定パッケージ (逐語・一次資料つき)
2. worklog エントリ 1 件 + 次の一手への起票
3. 段 8 自己改善候補 (`docs/dev-wave/` の穴。予算 headroom は workers.md 563B / core 802B /
   operations 399B / mutation 3B で実測済み)

## 分割方針・受入環境

- 実装面がないため段 5 の実装子は起動しない。`DW-C00` の軽量版に該当する
  (設計択一は本 wave で採用せず裁定へ返す / 正しさ防壁に触らない / 受理集合を変えない)
- ただし前回監査で親の事実誤認 2 件を検出したのは codex 側だけだった実績があるため、
  **独立 codex 1 本で findings の事実性を敵対検証する**。段 3 の「プラン敵対相談」ではない
  (プランが無い) ため `DW-S03` の max 固定は適用せず、事実照合の難易度に合わせ `reasoning=high`
  とする。この選択自体を本 wave の主張の一貫性として worklog に記録する
- 受入: docs-only のため `python3 tools/check_docs.py` と関連テスト。site は Pegasus login
  (`pegasus02`) — 重い全走は `tools/run_tests.py` 経由で計算ノードへ同期 dispatch される
