# 逐語の可逆最小正規化 (DW-S07、`git diff --check` 抵触の解消。可視文字は不変)

| file | 正規化 | 原文 sha256 / bytes | 正規化後 sha256 / bytes | 復元法 |
|---|---|---|---|---|
| `focus-1.log` | 行末の空白 (`[ \t]*$`) を除去 (9 行) | `ee18c5742ecd5a6f8094ad0a4266d4f17d83926d833d96f3a94186a76ec13dfd` / 22434 | `15cf5975a7d5ba8f6c41f1ca5575b0e01f3c242657eae85a93a5b7dd9a347d9a` / 22409 | 原本 = job dir `focus/focus-1.log` (未加工)。差は該当行末の半角 space / 末尾の改行 |
| `focus-2.log` | 行末の空白 (`[ \t]*$`) を除去 (2 行) | `14dc04ff3ef4a4f2f32f77eba3197655fcbe931dd26b19d36f96709087cfc406` / 8502 | `f846947e1dd4aa2290b5cad373a44d86c0eba2fe0a6840ad53d58635a4247975` / 8500 | 原本 = job dir `focus/focus-2.log` (未加工)。差は該当行末の半角 space |

job dir = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/`。他の逐語 file は無加工。
