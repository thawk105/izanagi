## 段 4 裁定 (親、2026-09-20 21:12 JST、段 2・3 は軽量版で省略)

- 裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査: T-2501 / D1879 / exploration campaign に関わる wave 開始後の更新なし。phase3.md・next-tasks.md にも T-2501 の更新なし。
- 実装する (docs のみ)。実装面の差分ゼロ → 変異 matrix 免除 (DW-S04)。受入全走は免除しない (記録 commit 後の tip で 1 走)。
  実 repo を読むテスト: `python3 tools/check_docs.py` (login 実行は runbook §7.0 の暫定例外) を段 7 前に実走。
- (P1) 採用: glossary §4 (campaign 項目の直後) に 1 項目。機体固有値を書かず、対応の詳細は runbook §7.9 へ委ねる。
- (P2) 採用: runbook `### 7.9` 新設、§8 の該当項目に「(語の定義は §7.9)」の 1 句。
- (P3) 採用: 対応表の実例に A-1 対測定 (`paper_story_a1_paired.py:97` `DECLARED_USE_CLASS = "exploration"`、job script が `IZANAGI_EXPLORATION_OUTPUT_ROOT` を export) を「語 A の値は語 B (標本の帰属) を含意しない」の例として載せる。A-1 の標本が正式か否かは本節で判定しない。
- 追加で気づいた事実 (brief 後): `layout.py` の `ExplorationCampaignLayout` docstring 自身が「探索専用 layout」と書く — code 中の「探索」は語 A。runbook の節にこれを明記する。
- scope 外 real 所見: なし。
- 段 5 は親が起草、段 6 は read-only codex review 1 本 (lens: 一次資料との事実照合 + 規律 2・受理集合に触れる文の混入検査)。
