---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-artifact-dir
seq: 1
title: dev-wave launcher の起動前 fail-closed バグ (dry-run のディレクトリ生成漏れ) を直した (コード + テスト、branch worktree-dev-wave-artifact-dir、変異 matrix = baseline PASSED・1/1 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー裁定は 2026-08-13 rulings 第12回 #14 の **(a)** (控え =
  `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-rulings12-17rulings.md` 項14、詳細 =
  同 inbox `2026-08-13-t1048-dev-wave-codex-artifact-dir.md`)。`dev_wave_codex.py` 側で job-id
  ディレクトリまで作る側を採用し、launcher の fail-closed 実在検査はそのまま残した。
- **過去の未 land patch は再利用しなかった。**
  `dev-wave-jobs/2026-08-13_t1048-trigger-freeze-epilogue/0001-docs-t1048-8-dev-wave-artifact.patch`
  の中身は worklog spool fragment へ backlog 項目 1 件を足すだけの docs-only patch であり、
  コード修正そのものではなかった。その本文は既に worklog archive entry (542) へ着地済みで、
  `docs/phase3.md` の見送り台帳にも該当項目は存在しない (grep 0 件) ため、T 番号の起票・解決
  いずれも本 wave の scope に含めなかった。
- **段5 実装子の diff (`main()` の directory 作成呼び出しを dry-run 早期 return より前へ移動) は
  正しかったが、親の実走で回帰を検出した。** 反転後の dry-run テストで
  `python3 tools/run_tests.py orchestrator/tests/test_dev_wave_codex.py -v` が 7 failed / 10 passed。
  原因は共有 test helper `_invoke()` が `--artifact-root` の親ディレクトリを事前に作っておらず、
  dry-run 修正で初めて有効になった「`--artifact-root` は投入前に作る」契約 (非 dry-run 経路では
  元から真、`DW-O01` に既記載) を満たせなかったこと。段6 fix で `_invoke()` に
  `(root / "artifacts").mkdir(exist_ok=True)` を 1 行足し、既存 assert は一切変更せず全 17 test
  green にした。実装子はいずれも Pegasus dispatch preflight failure (rc=16) でテスト未実走を
  正しく申告しており (`closed` 主張なし)、親の実走がこの回帰を捕捉した形。
- 子の工数: author 1 本 (luna/max、35 model calls)、fix 1 本 (luna/max)。いずれも accepted、
  親の再実走でのみ検出できた回帰だった。

## 次の一手差分
