## 段 1 brief (親)

**研究前進 (土台):** 共有 login node で重量走行 (pytest 等) を止める hook の穴を閉じる。実害の実測 =
2026-09-09 に 172 秒の pytest 走行が profiler 越しで 1 回素通り (load 17/96、実害なし)。研究の実測を
直接止めてはいないが、runbook の共有環境作法に反する走行を機械が見逃す状態。最小差分 = 既存 parser の
抽出結果へ既存の重量判定を再帰適用 (新判定軸なし)。ユーザーが command 引数で明示指示 (DW-C00: 引数優先)。

**scope (本題のみ):** `hooks/guard_bash.py::_heavy_segment_violation` で、python head + `-m <executor>`
の内側実行対象を既存 parser の option 表で取り出し、同じ head の合成 segment
(`[head, "-m", <inner module>, *rest]` または `[head, <inner script>, *rest]`) へ
`_heavy_segment_violation(…, depth+1)` を再帰適用する。テストは `orchestrator/tests/test_hooks.py`、
docs は `hooks/README.md` の「Pegasus の重い処理層」段落に 1〜2 文。**scope 外:** wrapper module の
列挙追加、allowlist 反転、防護対象の拡大、追加 gate、shell 状態模型、subprocess 内側。

**着手前の実測 (現行 main 38353207f、`decide(cmd, root, site="PEGASUS_LOGIN")`):**
- DENY: `python3 -m pytest -q` (interpreter の baseline 重量対象)
- ALLOW (素通し): `-m cProfile -m pytest`、`-mcProfile -mpytest`、`-m profile -m pytest`、
  `-m coverage run -m pytest`、`-m pdb -m pytest`、`-m trace --trace --module pytest`、
  `-m runpy pytest`、`-m cProfile -m cProfile -m pytest`、`-m cProfile -m cmake --build build`
- ALLOW (修正後も維持すべき正例): `-m cProfile -m pytest --collect-only` / `--help`、
  `-m cProfile tools/run_tests.py` (sanctioned)、`python3 tools/run_tests.py`
- 素通しの機序: `_script_executor_targets` が `-m pytest` を `_executor_module_target` で repo 内 path へ
  写像できず `()` を返し、`_python_pytest_args` は最初の `-m` (cProfile) しか見ない。

**確定済みユーザー裁定:** D1891 (再帰適用・列挙追加禁止・allowlist 反転禁止)、D427 (hooks/ は有効化前
commit `d92800f49` = 施錠 commit `84e5e0b00` の親を base にした第 2 worktree で Codex author が書き、親が
統合 commit → wave branch へ merge)、D428 (wave 前後の同一 corpus で deny→allow 反転 0 件)、D1719 (第 2
worktree の 3 点: 全文射影 + sha256 検算 / guard_write は本 wave では触らないので施錠は起きない /
merge 競合は実装側を採り blob 一致を検算)、D95 (実装面は Codex author)。

**不変条件:** 規律 2 を緩めない。既存拒否 (`-m pytest` 直接、executor 越しの admission 拒否、出力先の
admission 上書き拒否) を正例維持。非実行形 (`--collect-only`/`--help`/`trace --report`/`cProfile --help`)
の ALLOW を維持。反転検査 deny→allow 0 件。site 非拒否 (compute/OTHER) の受理 bit 不変。

**割れうる前提 (親の provisional 裁定・攻撃対象):**
- (P1) 再帰の挿入位置: shell command-string 再帰 (`depth < 2` block) の直後、`_is_sanctioned` 早期許可より
  **前** (sanctioned な executor target が内側の pytest を隠さないよう、shell と同じ理由)。
- (P2) 再帰対象は「単一 program を実行する executor」= cProfile / profile / pdb / trace / runpy /
  coverage run。multi-target (pydoc / doctest / unittest) は内側 program を実行しないので対象外。
- (P3) 抽出は `_script_executor_targets` の option 消費規則を共有し、`mapped or token` へ落とす前の
  生の (kind ∈ {module, script}, value, rest) を返す姉妹関数へ分離する。repo 外 module (`pytest`) でも
  内側 invocation を構成できることが要件 (現行は `()` に落ちる)。既存 `_script_executor_targets` の
  返り値は変えない (admission 判定の受理集合を動かさない)。
- (P4) 深さ上限: 内側 args は厳密に短くなるので停止は保証される。shell 再帰の `depth < 2` を流用すると
  2 重 wrapper (`-m cProfile -m cProfile -m pytest`) が届かない可能性 → author は上限を明示し、
  review が攻める。
- (P5) 軽量判定: D428 が「防壁の受理集合を変える wave」と明記するので段 6 の敵対レビュー 2 本は省かない。
  段 2・3 は D1891 が plan + 別系統相談を経て設計を確定済みなので省く。

**成果物:** コード (guard_bash.py) + テスト (test_hooks.py、正例・負例) + docs (hooks/README.md) +
D428 反転検査 corpus と結果 (job dir) + 変異 matrix (計算ノード) + insight README
(`output/insights/2026-09-17/t2498-executor-heavy-recurse/`)。

**分割方針 (D427 の所有分離):** author A = guard_bash.py を第 2 worktree (base d92800f49) で編集
(現行 main 全文の射影 + 変更、親が sha256 検算)。author B = test_hooks.py を wave worktree で編集。
両者は並列。親: 統合 commit (第 2 worktree) → wave branch へ merge (競合は実装側、blob 一致検算) →
焦点走 → 反転検査 → 段 6 review 2 本 → fix (必要なら第 2 worktree の統合 commit から fix branch) →
変異 matrix → 受入 → land。

**変異事前登録 (草案、段 4 で確定):** M0 等価 (comment のみ) SURVIVED。M1 再帰呼び出しの恒偽化 →
内側 pytest 素通し → KILLED。M2 内側 invocation の module 形を落とす (script だけ) → KILLED。
M3 coverage run 経路を落とす → KILLED。M4 内側で `_pytest_nonexecuting` を無視 → `--collect-only`
正例が赤 → KILLED。M5 再帰位置を `_is_sanctioned` 早期許可の後へ移す (P1 の対照。sanctioned target を
持つ executor 形が無ければ等価 = SURVIVED 対照として登録)。

**既存被覆の検索 (純増だけ):** F121 は executor 越しの admission 迂回 (Pegasus path) を閉じたが、内側
program の重量分類は含まない。T-518 (cwd/symlink/env -S/nesting/launcher) は別 vector。D1891 以降に
本件を止める・上書きする裁定なし (decisions を D1891 以降で走査)。

