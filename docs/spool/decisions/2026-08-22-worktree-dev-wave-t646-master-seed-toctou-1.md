---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: worktree-dev-wave-t646-master-seed-toctou
seq: 1
---

## {{D:t646-holdout-freeze-head-binding-scope}}. holdout freeze producer の HEAD blob 束縛は最小差分に留め、共有 helper の硬化は見送る

**決定:** 床値 protocol master_seed TOCTOU carry の fix は `s8b_holdout_freeze.py` の
`_validate_floor_inputs` へ、同ファイル内で既に使われている `_blob_at_head`
(`measurement_closure` 等) と同型の captured HEAD blob 対 working tree bytes の byte-exact
比較を追加するに留める。`s8b_floor_campaign.py` が備える HEAD commit 検証
(`git rev-parse --verify HEAD^{commit}`)・exact `100644` mode 検査 (`git ls-tree`)・git
replace object 衛生化 (`--no-replace-objects`) は、本 wave では `_blob_at_head`/`head` 捕捉
ヘルパーへ移植しない。

**理由:**
- 段3 敵対相談レンズが指摘した3点 (HEAD が commit である保証がない・HEAD tree entry の exact
  mode 未検査・git replace object 未衛生化) は、`_blob_at_head` を共有する既存4箇所
  (`measurement_closure`・`known_axes_freeze`・`generator`・`design_source`) すべてに及ぶ
  既存の弱点であり、本 wave が新たに導入するものではない。
- 攻撃には repo への特権的 git 操作 (replace object 設定・HEAD 参照の非 commit 化) が要り、
  本 carry が想定する脅威モデル (qsub 投入後の working-tree だけの誤編集・事故) より強い前提を
  要求する。
- `DW-G02` (初回 cycle 前の hardening は correctness 判定を実際に変える欠陥だけ blocker) および
  `DW-G03` (族一般化には独立2例) に従い、同一ファイル内の再発ではあるが独立した別 producer での
  再現ではないため一般化の閾値に届かない。
- 2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) とも整合する。

**却下した選択肢:**
- `s8b_floor_campaign.py` の `_head_commit_oid`/`_head_blob_100644`/`_sanitized_floor_git_env`
  相当を `s8b_holdout_freeze.py` へ移植し、既存4箇所すべてを同時に硬化する — scope が本 carry の
  主張から大きく逸脱し、段階導入規律に反する。carry `{{T:holdout-freeze-head-binding-hardening}}`
  へ送った。
