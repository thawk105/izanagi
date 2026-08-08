# insight — [T-316] 意味 gate 設計択一の裁定パッケージ (2026-08-09)

dev-wave `worktree-dev-wave-t316-semantic-gate` の一次資料。**実装差分ゼロ**の設計裁定パッケージ。

## 何を返したか
`tools=[]` + JSON schema が止められない 2 脅威 (α: hole 内 1 行 C++ 注入、β: auditor の
`diff_digest` echo による fail-open) に対し、3 案 (i) 全軸 AST/DSL・(ii) build/run sandbox・
(iii) 両方 を実測付きで比較し、ユーザー裁定へ返した。

## 構成
- `package.md` — 裁定パッケージ本体 (R1〜R5 + 総括)。**ユーザーが読む正本。**
  - R1: 推奨 = 非対称 (iii) の定義 (全軸 sandbox + backoff/trigger 限定 DSL + sort raw 維持 +
    auditor deny-only)。
  - R2: 【要ユーザー裁定】sort の reward hack を意味 gate は塞がない (typed IR / 独立 oracle / 台帳明示)。
  - R3: 実装 wave の前提条件 (段 3 が real と裁定した blocker/must-fix)。
  - R4: 順序 ([T-664] → [T-184] → 計算ノード計測 → 実装)。
  - R5: やってはいけないこと + refuted 3 件。
- `verbatim/` — 逐語。
  - `s1-brief.md` — 段 1 親 brief。
  - `s2-plan.md` — 段 2 プラン (read-only codex sol、effort=max)。
  - `s3-lensA-sol.md` / `s3-lensB-luna.md` — 段 3 敵対 2 レンズ (いずれも NO-GO、全所見 real)。
  - `*-prompt.txt` — 各段のプロンプト。

## 親が実ファイルで裏取りした load-bearing 主張
- D136 実在 = cache/replay/選択 identity への admission 束縛済み (D127 決定(5) の class-cross hole を閉鎖)。
- `materializer_admission.py` docstring = shell/calibrator/任意 binary path を意図的に admission 外に残す。
- `s5_permutation_coverage.py` `_build_broken` = buildcache 非経由の直接 build。
- `calibrator/runner.py:440-450` = 非 certify mode で injected runner を下流に渡さない
  (policy ≠ 実行封じ込めの証明)。

## 台帳
worklog fragment = `docs/spool/worklog/2026-08-09-dev-wave-t316-semantic-gate-1.md` ([T-316] を
更新、land 時に fold)。新規 D/F は起こさない (裁定はユーザーへ返す設計で、決定は未確定)。
