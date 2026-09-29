---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-acceptance-critical-path
seq: 1
---

## {{D:acceptance-template-no-dontwritebytecode}}. 受入門番の共有雛形は PYTHONDONTWRITEBYTECODE を立てない。受入 shard の割付と所要台帳は変えない

**決定:**

1. 受入門番の共有雛形 `/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/run-acceptance-gated.sh` から `export PYTHONDONTWRITEBYTECODE=1` を外した (repo 外、sha256 `b30be0fb…` → `25d25685…`、差分は export 1 行の削除と理由のコメント 1 行)。受入自身の login collection (`tools/run_tests.py` の `_collect_login_universe`) が、post-claim merge 後の検査対象の木に bytecode cache を書く。門番の閾値・周期・再投入は変えない。
2. 受入 shard の割付 (`tools/acceptance_shards.py`) と所要台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) は変えない。
3. 明示的な温め (投入前に login で pytest の collect-only を直接起動する) は採らない。

**理由:**

- 9/26 以降の受入 shard の collection (pre) の倍増 (温 65〜80 秒 / 冷 125〜140 秒の二峰) は、雛形の export が launcher → run_tests.py → login collection と計算ノード worker に継承され、投入元 worktree の `orchestrator/tests/__pycache__` を誰も書かないことで説明できる。9/26〜29 の 124 走で、dispatch の request env にこの値がある 73 走は冷 67、無い 51 走は冷 2。
- 同時刻対照 2 対 (同 commit の fresh 木、事前登録) では、H (値なし) の pre が 6/6 shard で 24.7〜28.6 秒短かった。事前登録の判定は、待ち行列が短く H の全 shard が login collection 完了前に始まったため「判定不能」で、全効果 (約 65 秒) は同時刻対照では測っていない。変更は pre を縮める方向にしか働かず、受入の受理集合・受領証・清浄性の指紋 (`git status` 由来、`__pycache__/` は .gitignore 済み) を変えない (段 3 相談・段 6 review とも反証なし)。
- 割付: 現行台帳の `allocate` は実走と 3 shard 完全一致し、台帳を実測中央値・`--refresh` 再生成・5 走中央値の合成に替えても、予測した shard 間最大の makespan は 153.7 秒で差 0 (shard-1 / 2 は単独の長い test 1 本が律速)。
- 明示の温めは AGENTS.md の「pytest・build を自分で直接起動しない。必ず tools/run_tests.py を通す」に反し、login の `run_tests.py --collect-only` は計算ノードへ dispatch されて login の cache を温めない。

**却下した選択肢:**

- `tools/run_tests.py` の login collection で env を外す恒久策 — run_tests.py の blob 差は D987 により in-flight の全 wave の再受入を招く。初回受入でも shard 開始前に cache をそろえる設計択一として次の一手に残す。
- 所要台帳の再生成 — 効果 0 秒 (上記)。land のたびに台帳が競合する既知の循環 (memory) も負う。
- 事前登録の判定を結果を見た後に緩めて「支持」と書く — 規律 3 の後付け禁止と同じ向き。観測値として並記するに留める。
