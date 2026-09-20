---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-wave-startup-cost
seq: 2
---

## {{D:no-submodule-reference-alternates}}. wave 起動の submodule 再帰初期化を `--reference` / alternates で短縮する局所修正は採用しない

**決定:** `tools/dev_wave_submodule_init.py` (`tools/dev_waves/git_state.py` の `submodule update --init --recursive --no-fetch`、URL は主 checkout の module store の絶対 path) に `--reference` / alternates を足す変更は行わない。wave 起動の固定費の本体は superproject (tracked 31,699 file、872 MB) の checkout を伴う `git worktree add` であり、submodule 初期化は直接計測で 3 処理 (EnterWorktree 85 秒 / submodule 7.46 秒 / 開始 gate 6.70 秒) の 7.5% にとどまる。依頼の実装条件「submodule 初期化が固定費の大半」は観測した条件 (同一 Lustre、主 store と同 inode の hardlink 共有、login node の混雑帯) で不成立 (一次資料は `output/insights/2026-09-21/wave-startup-cost/`)。

**理由:**
- 主 store の pack は worktree の module に hardlink で複製済み (同 inode) で、object の転送は既に無い。git 2.34 の `clone.c` は URL が local path なら `--shared` でない限り `copy_or_link_directory()` で hardlink 複製を行い、`--reference` は `objects/info/alternates` に 1 行を足すだけなので、現行 argv への追加で省ける処理を示せない (正の短縮量は未実証)。
- alternates を導入すると参照先 (主 store) の寿命に依存する: 主 store の gc / prune が借り手にしか要らない object を消す、主 checkout / store の撤去で alternates 先が消える、`tools/dev_wave_cleanup.py` の nlink 検査 (F1026 / T-2777) は object 名形の regular file だけ nlink > 1 を許すので `objects/info/*` の hardlink 共有は rc 20 になる。得られる短縮が示せない変更にこの依存を足さない。
- worktree の登録・lock・開始 gate の受理条件・submodule の pin 一致検査は変えない (依頼の不変条件)。

**却下した選択肢:**
- `--reference <主 store>` の追加 — 上記のとおり省ける処理が無い。
- `--shared` (alternates のみで object を複製しない clone) — hardlink 複製の省略分は object 36 file 程度で、3 段の clone process 起動と 1,440 file の checkout は残る上、参照先の寿命依存が生じる。
- superproject の sparse-checkout で `output/insights` (24,420 file = 77%) を外す — 実在 file を変える設計変更で本 wave の scope 外。件数比 77% は時間比ではない。

次の局所候補 (git 既存機構 `checkout.workers` の local config 1 行、木の本数を減らす運用) は採用効果が未実測 (予備診断 1 系列のみ) なので既成事実にせず、insight §7 の裁定パッケージとしてユーザー裁定と別 wave の実測に委ねる。
