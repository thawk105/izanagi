# 逐語の可逆最小正規化 (DW-S07、`git diff --check` 抵触の解消。可視文字は不変)

| file | 正規化 | 原文 sha256 / bytes | 正規化後 sha256 / bytes | 復元法 |
|---|---|---|---|---|
| `focus-1.log` | 行末の空白 (`[ \t]*$`) を除去 (9 行) | `ee18c5742ecd5a6f8094ad0a4266d4f17d83926d833d96f3a94186a76ec13dfd` / 22434 | `15cf5975a7d5ba8f6c41f1ca5575b0e01f3c242657eae85a93a5b7dd9a347d9a` / 22409 | 原本 = job dir `focus/focus-1.log` (未加工)。差は該当行末の半角 space / 末尾の改行 |

job dir = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/`。他の逐語 file は無加工。
