# 段 4 裁定 — dev-wave token-hygiene (2026-08-06)

段 3 敵対レンズ 1 本 (gpt-5.6-sol / reasoning=max / read-only、rc=0、`check_codex_output.py` OK)
は **NO-GO** を返し must-fix 6 件を出した。**親は 6 件すべてを real と裁定し、brief v1 を破棄する。**

## 所見の裁定

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| 1 | 母集団と時間窓が未定義 (単一 encoded cwd の subtotal、mtime 窓、20 応答未満を除外) | **real** | 採用。台帳が母集団を明示定義し報告に併記する |
| 2 | metric の混同 (model call と tool call、文字数比と token 比、raw token と費用) | **real** | 採用。台帳で分離し、費用と名乗らない |
| 3 | codex 部が既存 `codex_worker_ledger.py` と二重管理になる | **real** | 採用。**codex 側は実装しない** |
| 4 | P2 (段 2 の high 化) は交絡した観察値に基づく | **real** | 採用。**実装せず** T-184 / `codex_reasoning_ab.py` の paired・blind・非劣性評価へ送る |
| 5 | 固定換算率を `CLAUDE.md` へ入れると stale 化し無理な bundling を誘発する | **real** | 採用。**CLAUDE.md は変更しない** |
| 6 | 段 6 reviewer 1 本は契約違反、aggregate 予算の削除先が未特定 | **real** | 採用。レビューは 2 本。**workers.md も変更しない** |

追加で親が独立に確認した事実 (レンズと一致):

- `tools/codex_worker_ledger.py` (stage 別 read-only 台帳) と `tools/codex_reasoning_ab.py`
  (effort の A/B 装置、primary endpoint は arm を隠した親の意味裁定) が既に存在する。D100 が
  「token は observable proxy であり hard cap ではない」と既に裁定している。
- `grep -rln "claude/projects" tools/ orchestrator/ docs/` は archive の 1 件だけ。
  **claude 側は完全に未計装である。**
- dev-wave 4 文書の aggregate 予算は 25,200 bytes に対し現状 25,187 bytes = **余地 13 bytes**。
  削除先を特定せずに追記できない。

## 親の裁定 (P1〜P3 の帰結)

- **P1 (max→high の一律引き下げをしない) は維持する。** レンズは「臆病な現状維持ではなく規律 2 に
  沿う fail-closed 判断」として defect ではないと判定した。
- **P2 (段 2 起草だけ high) は撤回する。** 観察値は stage と交絡しており、因果を主張できない。
  既存の A/B 装置が所有する問いである。
- **P3 (軽量版にしない) は維持し、段 6 レビューを契約どおり 2 本にする。**

## 確定 scope (これだけを実装する)

**`tools/claude_session_ledger.py` + `orchestrator/tests/test_claude_session_ledger.py` の新設のみ。**

claude 側セッションの read-only 台帳。`codex_worker_ledger.py` の姿勢 (観測値だけを公開し、
推測値を観測値と名乗らない) を踏襲する。

**scope 外** (実装しない): codex 側の集計、`docs/dev-wave/workers.md` の変更、`CLAUDE.md` の変更、
effort 既定の変更、過去 transcript の圧縮、削減施策そのもの。

## 不変条件 (緩めない)

1. **検出力を下げる変更をしない。** 段 3・段 6 の effort・本数・レンズ多様性に触れない。
   「トークンが減った」を品質低下の言い訳にしない。
2. **read-only。** transcript を書き換えず、書込先を引数に取らない。
3. **観測値と推測値を分ける。** model call を tool call と呼ばない。文字数比を token 比と呼ばない。
   raw token を費用・課金・枠消費と呼ばない (サブスク運用のため実費ではない)。
4. **母集団を黙って決めない。** 走査した root・cwd/originator filter・時間窓の判定根拠
   (event timestamp か mtime 退避か)・読めなかった件数を必ず報告に出す。
5. **login ノードで暴走しない。** 読み取り上限を持ち、既定で共有 process を巻き込まない。

## 成果物影響 (DW-G05)

certified 選択・材料レポート・試行台帳・proof chain の値と参照は一切変わらない。
実装しない場合、消費の 3 分の 2 を占める claude 側は観測手段を持たないままとなり、
effort・往復・文脈のどれを削っても効果を before/after で検証できない。

## 変異事前登録 (DW-M01、実装前に固定)

| ID | 変異 | 期待 kill node |
|---|---|---|
| M1 | requestId dedupe を外し record 単位で数える | 応答数・トークンが 2 倍になる fixture テスト |
| M2 | 同 requestId の**最初**の record の usage を採る (最終でなく) | 出力過小計上の fixture テスト |
| M3 | `cache_read_input_tokens` を入力から落とす | 入力合計の fixture テスト |
| M4 | `cache_creation_input_tokens` を落とす | 同上 |
| M5 | `input_tokens` を落とす | 同上 |
| M6 | `model="<synthetic>"` の usage 全ゼロ error request を応答数へ数える | 除外の fixture テスト |
| M7 | `subagents/*.jsonl` を走査対象から外す | sidechain 別計上の fixture テスト |
| M8 | sidechain を親と合算して 1 つの数字にする | 分離報告の fixture テスト |
| M9 | 時間窓を event timestamp でなく mtime だけで決める | 窓判定根拠の報告テスト |
| M10 | 読めなかったファイル件数を報告から落とす (黙って 0 件) | 報告テスト |
| M11 | 読み取り上限を無視して全件走査する | 上限テスト |
| M12 | 母集団 (走査 root・filter) を報告から落とす | 報告テスト |

## 並列分割方針

実装面は 1 所有単位 (`tools/claude_session_ledger.py` とそのテスト) で分割しない。
段 6 の敵対レビュー 2 本だけ並列にする。
