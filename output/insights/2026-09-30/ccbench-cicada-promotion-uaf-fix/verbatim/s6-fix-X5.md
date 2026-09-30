## 直したこと (file:line)

- [launch_promo_confirm.py:108](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:108): ci の `--format-evidence` を受け、ログの SHA-256 と files・rc・version の行を結果に記録。ci part 内の format 実行を外しました。CI image build と D297 の判定は維持しています。
- [launch_promo_confirm.py:269](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:269): `failed` 行の thread 接頭辞を除いて種類別に合算。M3 は旧形式の `failed_lines` からも集計できます。
- [README.md:3](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/README.md:3): ci の証跡入力と実行内容を更新しました。

## login で行った検査と結果 (未実走の明記)

- ci `--dry-run`: **rc=0**。証跡 SHA-256 は `cfa32f6131e469944076d825af015e9d50ecfbd6faea0a17b5839fb7608eb075`、要約は両環境とも **213 files・rc=0**、clang-format **14.0.0 / 14.0.6** と記録されました。
- 既存の TPC-C 結果から M3 を再集計: 修理後 **18,306**、fix2 逆適用版 **305,335**。thread 別行と別種の `failed` 行を使った小入力検査も通過しました。
- Python 構文検査、`check_codex_agents.py`、`check_docs.py`、`git diff --check` は rc=0。TPC-C、CI image build、D297 は今回**未実走**です。

## 総括

指定の 2 点を修正し、ci の dry-run を通しました。TPC-C の再走はしていません。