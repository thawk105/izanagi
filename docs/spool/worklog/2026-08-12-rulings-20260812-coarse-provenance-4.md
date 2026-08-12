---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: rulings-20260812-coarse-provenance
seq: 4
title: check_codex_hooks の 7 ERROR を診断した — hook は実 repo で発火しており誤警報、原因はパス単位の hook trust と使い捨て複製 probe の衝突。対応 wave を起票登録 (docs のみ、branch worktree-rulings-20260812-coarse-provenance)
---

## 本文

- **ユーザー報告と診断 (2026-08-12)。** [T-815] の手番として `python3 tools/check_codex_hooks.py` を
  実行した結果が 7 ERROR (protected file 作成・拒否証拠なし、codex-cli 0.147.0)。診断の実測 3 点:
  (1) **実 repo (信頼済みパス) では hook が発火する** — 本番同形 argv (`codex exec --json --ephemeral
  -s workspace-write`) の probe で `Command blocked by PreToolUse hook: [guard_bash] 拒否` を確認、
  保護ファイルは作られず。(2) **信頼承認は成功している** — `~/.codex/config.toml` の `[hooks.state]` に
  本 repo の `.codex/hooks.json` パスの `trusted_hash` 2 件。(3) **旧版 0.146.0 でも同じ 7 ERROR** —
  version drift 説は棄却。
- **機序**: Codex の hook trust は hooks.json の**絶対パス単位**で永続化される。checker は使い捨て
  複製 (temp) の中で probe するため、そのパスに信頼が無く hook が**黙って外れる**。したがって
  checker は信頼承認後も構造的に rc=0 になれず、[T-815] の完了基準「承認すれば rc=0」は誤りだった。
- **残る実穴**: worktree のパスも信頼されないため、dev-wave の codex 子は hook 無しで走っている
  可能性が高い (未実測 — 稼働中 worktree への書込み probe になるため控えた)。当面の防御は codex
  sandbox (workspace-write) + Claude 親 hook。**修正まで codex-only dev-wave は投入しない** (運用注意)。
- **ユーザー裁定**: 「hook trust 対応 wave を立てて」→「ここで dev-wave やるわけじゃないよ。
  登録するだけね」。本 fragment は起票登録のみを行い、wave の実行はユーザーの投入に委ねる。
  起票資料 = `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-codex-hook-trust-wave.md`。

## 次の一手差分

### 更新

- [T-815] **P1・ユーザー手番は完了 (2026-08-12 実測)、rc=0 基準は {{T:codex-hook-trust}} へ移管**:
  hook 信頼の承認は成功している (`~/.codex/config.toml` に本 repo パスの trusted_hash 2 件、
  実 repo probe で guard_bash の拒否発火を実測)。`check_codex_hooks.py` rc=0 は「使い捨て複製の
  パスに trust が無い」構造的理由で承認後も達成不能と判明し、完了基準としては誤りだった。
  基準の回復は {{T:codex-hook-trust}} の checker 修正後に行う。既裁定 (1)(2)(3) の内容は不変。
  base: 26f9c84f7904eb20df6d73522dbdddb34cece894044109cecb9d413207d07519

### 新規

- {{T:codex-hook-trust}} **P1・新規 (wave 承認済み・起票のみ、実装面 = Codex author、防壁変更 =
  敵対レビュー 2 本)**: Codex の path 単位 hook trust への適応。scope = (1) `tools/check_codex_hooks.py`
  の probe argv に `--dangerously-bypass-hook-trust` を許す — checker は複製直後に hooks bytes を
  自ら検証しており、flag の但し書き「hook source を自前検証済みの自動化向け」を満たす。probe argv と
  出荷 argv の同一性契約 (「診断用にも混入させない」docstring) の supersede を decisions へ記録する。
  (2) `tools/dev_wave_codex.py` の子起動 argv に同 flag + 起動前の hooks 検証 (checker の
  `validate_installation` 再利用) を **fail-closed** で足す — 検証が赤なら起動拒否、flag 無し起動へ
  fallback しない。(3) `hooks/README.md` へ trust 模型 (パス単位・worktree 非継承・ephemeral) を記載。
  (4) 変異の事前登録 — 検証を外して flag だけ足す fail-open 形、および wave 前の形 (flag 無し probe)
  への revert を必ず含める。修正までは codex-only dev-wave を投入しない。
  起票資料と診断逐語 = rulings-inbox `2026-08-12-codex-hook-trust-wave.md`。
