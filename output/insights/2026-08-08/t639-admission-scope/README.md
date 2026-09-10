# [T-639] admission 縮小版の制度化 — 一次資料

2026-08-08 の dev-wave (branch `worktree-dev-wave-t639-admission-scope`) の逐語。
台帳の要約は worklog、設計判断は decisions、失敗は failures を正本とし、ここは**逐語の置き場**である。

## 何をしたか

admission registry (`tools/pegasus/admission_registry.json`) の適用 path を `tools/pegasus/` 配下から
**repo 内の exact 登録 path** へ広げた。ユーザー裁定 (2026-08-08、「未分類はログインで走らせない
既定だけ機械化する縮小版」) の履行であり、**全 tool の分類完備は目指していない**。

受理集合が単調に縮むことを、非 `tools/pegasus/` entry を deny class (`unknown` /
`dispatch-required`) に限る 3 層強制で保証した。実例として
`tools/claude_session_ledger.py` (F160 の当該 tool) を `unknown` で 1 件登録した。

**強制面は Claude Code の Bash tool が実行 target と認識した綴りに限られる。**
cwd 相対・`python3 -c`・未解析 launcher・Codex 子・ユーザー端末・cron・subprocess の内側は
本 gate の外であり、塞いでいない (F121 / [T-518] の既知残穴)。

## ファイル

| file | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief。前提実測 5 件 (実編集 → `git checkout --` 復元) |
| `s2-plan.md` | 段 2 codex プラン (file:line 粒度) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談。A = 受理集合と fail-closed、B = 裁定射程と docs 投影 |
| `s4-ruling.md` | 段 4 裁定。所見の real/refuted・plan v2・変異事前登録 10 本 |
| `s5-impl.md` | 段 5 実装子の報告 |
| `s6-lensC.md` / `s6-lensD.md` | 段 6 敵対レビュー。C = 受理集合・恒真ゲート、D = 承認範囲・巻き添え |
| `s6-fix.md` / `s6-fix2.md` | 段 6 fix 2 巡の報告 |
| `mutation-spec-v1.json` / `mutation-ledger-v1.json` | 変異 v1 (**erratum**。7/10 MISMATCH、生存 0) |
| `mutation-spec-v2.json` / `mutation-ledger-v2.json` | 変異 v2 (**10/10 KILLED**、生存 0、baseline 緑) |

## 敵対検証が止めたもの (land 前)

1. **許可の逆流 (段 3 レンズ A、blocker)。** 段 2 プランは非 `tools/pegasus/` の `local-ok` を
   将来許すと書いていた。壊れた・敵対的な registry が `pytest` / `cmake` に `local-ok` を与えると、
   `_is_sanctioned()` の早期許可が既存の重量コマンド拒否を反転できる。
   → 非 `tools/pegasus/` は deny class のみへ限定。副産物として既存防壁 3 本が逐語のまま緑で残った。
2. **整合的破損での素通り (段 6 レンズ C、blocker)。** 管轄外 `local-ok` を lookup が `None` に
   落とすだけでは、registry と sanctioned が**同時に**汚染された状態で admission loop を素通りする。
   → deny sentinel へ強化し、二重汚染の end-to-end テストを追加。
3. **内部例外時の fail-open (段 6 レンズ C / D、blocker)。** `main()` の raw-mention 検出が
   手書き regex で、`tools//…` のような正規化で同じ path になる綴りを取りこぼす。
   fallback 集合が増えても追随漏れが赤にならない。
   → 検出器を fallback 集合から生成し、綴り matrix を集合駆動で固定。
4. **docs の矛盾 (段 6 レンズ C / D、must-fix)。** runbook が「未登録はすべて拒否」と書いた直後に
   「非 `tools/pegasus/` の未登録は素通り」と述べ、hooks README は site gate を持たない tool にも
   「一次強制は各 entry point 自身」と書いていた。→ 親が両方を書き直した。

## 変異検査

- **v2 = 10/10 KILLED、SURVIVED 0、baseline 緑** (`repo_head` = 統合 commit)。
- **M9 が正例** — fallback 判定を `tools/` prefix へ広げると
  `test_bash_unregistered_non_pegasus_path_remains_allowed` が赤になる。
  受理集合を縮小する wave の過剰拒否検出義務 (`DW-M01`) を満たす。
- **M7 は diagnostic sensitivity pin** (`DW-M08`)。sanctioned 差し引きを消しても
  admission 判定が sanctioned 早期許可より先に拒否するため受理集合は変わらない。kill として数えない。
- **v1 は erratum として残す。** 事前登録の `expected_nodes` を単一 node にしたため
  10 本中 7 本が `MISMATCH` になった (生存は 0)。経緯は failures 台帳。

## 変異 matrix の外で実測したもの

- **registry key と実ファイルの結線** (`DW-O19`): key を実在しない canonical path
  (`tools/claude_session_ledger_absent.py`) へ一時変異させ、
  `test_bash_non_pegasus_registry_keys_exist_as_regular_files` (FileNotFoundError) と
  `test_bash_non_pegasus_fallback_set_matches_registry_projection` の 2 本が赤くなることを確認して
  復元した。復元後の tree は clean。

## 受入

**最終 = 7296 passed / 20 skipped / 赤ゼロ (rc=0)。** land 対象 tip で、並行 wave の受入 lease を
取得して実測した。

4 回投入した経緯 (いずれも実装差分に帰属する赤ではない)。

1. PBS の 30 分 elapse 上限で進捗 99% 地点 SIGKILL (rc=16、テストの赤 0)。
2. 7238 passed / **2 failed** / 20 skipped (1477 秒)。赤 2 件はいずれも `git cat-file timeout`。
   2 node の単独再走は 2 passed (85.06 秒) で再現せず、admission の差分は当該コードへ到達しない
   (`DW-O18` により非帰属)。F57 族へ再発記録。
3. main 2 回目取り込み後の tip で 7240 passed / 20 skipped / 赤ゼロ (1237 秒)。
4. main 3 回目取り込み後の land 対象 tip で 7296 passed / 20 skipped / 赤ゼロ。
   件数の増加は取り込んだ並行 wave のテスト追加分である。
