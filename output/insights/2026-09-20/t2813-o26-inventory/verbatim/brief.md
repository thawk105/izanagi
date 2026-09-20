# 段 1 brief — [T-2813] DW-O26 に inventory test 4 群の常時収載 1 句を足す (2026-09-20 21:04 JST)

- **研究前進 (土台):** 止めている研究 = dev-wave の受入往復。T-2795 で焦点走 15 file が緑のまま受入で repo 全体の inventory pin 2 件が赤
  (受入 1 往復 + fix 3 巡、一次資料 `output/insights/2026-09-20/t2795-pair-launcher/README.md` §6〜§7)。最小差分 = DW-O26 へ 1 句 + exact pin の追随。
  完了判定 = 新本文で `check_docs` 緑・`test_check_docs.py` 緑・受入 child-green・land。
- **確定済みユーザー裁定:** D2186 項 5 (採用、文言・4 群・予算処理の委任)、D782 / D961 (予算超過は削減 → 独立 3 例 → 最小増分を AI が閉じ、上限を上げた場合だけ報告)、
  D95 (実装面は Codex author)、T-2292 (DW-O26 の契約側 = exact pin をセットで更新)。
- **scope:** (1) `docs/dev-wave/operations.md` DW-O26 節に裁定の 1 句を足す。(2) `tools/check_docs.py` `DEV_WAVE_DW_O26_SECTION_LITERAL` と
  `orchestrator/tests/test_check_docs.py` `_SYNTHETIC_DW_O26_SECTION` (+ bytes assert 979) を新本文へ追随 (Codex author)。(3) 単節予算 1000 bytes
  (実測 979/1000、新句 331 bytes) は D782 手順 1 段目 = 既存記述の削減で閉じる。上限は上げない。
- **scope 外:** 候補 1 件目 (provenance 監査 dispatch の直列化 1 句、同 README §7)、guard 類への便乗、仮想リスク向け gate・検査・台帳・一般化、
  失敗台帳の逐語引用 (`docs/failures.md` の DW-O26 引用 3 箇所は歴史記録、不変)、L1 / L1.5 予算 (DW-O26 は L2、条件 18 のみ)。
- **不変条件:** 規律 2 を緩めない。DW-O26 の既存 6 義務 (参照関係で引く / private symbol を symbol 名で grep / 同一 worktree の dispatch 全種直列 /
  変更 test file の単独走 / 新規 test file のメタテスト収載 / 並行 wave の相乗り) を 1 つも落とさない。落とすのは根拠説明 (「名前の推測でなく」「初回実測でも」
  「全走緑は file 単独緑を含意しない」「並行投入は orphan hold で rc=16 になる」= DW-C00 が同文を保持) だけ。`o26_contract_weakened` の attack 文字列
  「静的レビューが見落とした破れを」は保持。F242 参照は保持。裁定の 4 群名は逐語、`orchestrator/tests/` prefix と「repo 全体の」は bytes 次第で省く。
- **条件 dispatch の判定 (段 1 前):** DW-O08 非成立 (freeze 族に触らない、submodule 初期化済み rc=0)。DW-O09: pin 閉包を実測 — DW-O26 本文の写しは
  operations.md / check_docs.py literal / test_check_docs.py fixture の 3 箇所、`launch_authority.py` は DW-O01・S05-A・S06-A/C のみ対象で DW-O26 は非対象、
  file 全体 bytes の pin は無し (dev-wave.md 9_519 / next-tasks.md 27_060 は別 file)。凍結成果物の bytes は変わらない → 非成立。DW-O10 非成立。
  DW-O13 非成立 (既存 exact 述語の literal 置換で受理形は 1 → 1、増えない。gate 新設なし)。
- **(P1) 親の provisional 裁定・攻撃対象:** 新本文 (段 4 で bytes 確定、≤ 1000)。攻撃点 = 削減が義務を落としていないか、裁定文言からのずれが意味を変えないか、
  fixture の attack 文字列・bytes assert・`DEV_WAVE_EXACT_VISIBLE_SECTIONS` の整合。
- **模擬 / 実の差:** bytes は python で実測。check_docs・pytest は Pegasus 計算ノードで実走 (login では焦点走 fallback 拒否 rc=16)。
- **前提の実測:** 4 群の受入所要 (台帳 `acceptance_duration_ledger.json`) = test_campaign 152 s / official_perf_closure 37 s / p3_exploration_namespace 39 s /
  p3_b4_wiring_probe 110 s (直列合計 338 s、shard 並列で短縮) — 裁定の「軽い」は成立。独立 3 例 (D782 2 段目が要る場合の根拠) = F42 再発 2026-09-07 /
  entry 1238 (T-2292 起点、4 件中 3 件) / T-2795 §6 (2026-09-20)。
- **成果物の形:** 統合 commit 1〜2 (親 docs commit → Codex author 実装 commit → 親統合)、insight `output/insights/2026-09-20/t2813-o26-inventory/README.md`、
  worklog fragment (`docs/spool/`)、handoff は job dir。
- **変更面 (実アンカー):** `docs/dev-wave/operations.md` L185〜194 / `tools/check_docs.py` L618〜628 / `orchestrator/tests/test_check_docs.py` L178〜188、L9486、
  (L7149 は attack 文字列保持なら不変)。
- **分割方針 (軽量版):** 段 2・3 省略 (設計択一なし、正しさ防壁でない、受理集合は置換で不増)。段 5 = Codex author 1 本 (check_docs.py + test_check_docs.py)。
  段 6 = read-only レビュー 1 本 (義務の欠落・pin 整合) + 変異 matrix (pin 変異 3 種、事前登録は段 4) + 焦点走 (test_check_docs.py 単独 + consumer) + 受入。
- **受入・実測環境:** Pegasus 計算ノード (`tools/dev_wave_wait.py acceptance`)、runbook = `docs/pegasus-runbook.md`。
