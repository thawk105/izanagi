---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-known-violation-audit
seq: 1
---

## {{D:campaign-lock-honors-exploration-redirect}}. campaign advisory flock は exploration リダイレクトへ既存 resolver 経由で追従させる (target-side 修正)

**決定:** `orchestrator/campaign/layout.py` の `campaign_lock_dir()`/`campaign_lock_path()`
(campaign 単位 advisory flock、D621 が新設) へ `declared_use_class`/`output_root` を追加し、
`repo_output_root()` の直接呼び出しをやめて、official/exploration の分岐に既に使われている
既存の `resolve_campaign_output_root(declared_use_class, output_root)` を経由させる。
`orchestrator/campaign/loop.py` の `run_campaign()` から既存のローカル変数をそのまま渡す。
`declared_use_class` に既定値は付けない (呼び出し忘れを fail-fast にする)。

**理由:**
- `IZANAGI_EXPLORATION_OUTPUT_ROOT` (`_resolve_exploration_output_root()`) は resolved base が
  **repository 外でなければならない**ことを `_has_git_ancestor()` で明示的に検査・拒否する。
  exploration 経路のあらゆる出力を「どの git repo にも属さない」ものにする設計契約であり、
  D621 導入の advisory flock だけがこの契約から漏れていた。
- `orchestrator/tests/test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean`
  (既存の positive control) が、この漏れにより exploration 実行後に wave の tracked tree へ
  flock ファイルが untracked のまま残ることを検出し、決定的に FAILED していた
  (隔離 worktree で再現確認、shared checkout での並行 land 由来の near-miss ではない)。
- `campaign_layout()`/`exploration_campaign_layout()` は既に `resolve_campaign_output_root()` を
  official/exploration で正しく分岐させて使っており、`campaign_lock_dir`/`campaign_lock_path` だけが
  この既存パターンに乗っていなかった。新しい抽象を作らず既存関数を再利用するだけで閉じる。

**却下した選択肢:**
- test-side 修正 (`test_exploration_external_root_keeps_wave_clean` を、flock ファイルの存在を
  許容するよう緩める) — 上記のとおり exploration リダイレクト自身の設計契約 (repository 外必須)
  と正面から矛盾する側であり、検査を消して緑を買う形に近い。段3 敵対相談2レンズ (sol/luna)
  がいずれも target-side を支持し blocker/major の反対はなかった。
- 明示 `output_root` を渡す official campaign でも flock 配置を変えない (旧 `repo_output_root()`
  直呼びの一部だけ残す) — 明示 root の official は layout 自体が既に明示 root を使っており、
  flock だけ実 repo 側に残すと同じ campaign 内で参照 root が割れる。既定 (`output_root=""`) の
  official 挙動のみ不変とし、明示 root のケースは意図して統一する。

一次資料: command 引数「known violation があれば直す」(一次裁定は 2026-08-17 `/rulings 全件
第4回`、`docs/archive/worklog-phase3-0817-611.md`)。段2 codex plan・段3 敵対相談2レンズ
(blocker/major なし)・段6 敵対レビュー2本 (blocker/major なし) を経て実装。変異事前登録3件
(resolver 呼び出しの revert・`declared_use_class` 固定・`output_root` 握り潰し) は
baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0。
