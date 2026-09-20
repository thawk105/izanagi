# 逐語の可逆最小正規化 (DW-S07、`git diff --check` 抵触の解消。可視文字は不変)

| file | 正規化 | 原文 sha256 / bytes | 正規化後 sha256 / bytes | 復元法 |
|---|---|---|---|---|
| `focus-1.log` | 行末の空白 (`[ \t]*$`) を除去 (2 行) | `6bc898118655d9a6376004dcc5e48114ac61091a72adae1068d4f3f415df001d` / 8497 | `45bc68fe37894e6c7e9daf78cbd7481b88beaa3abc747aa75db347a08c874953` / 8495 | 原本 = job dir `focus/focus-1.log` (未加工)。差は各該当行末の半角 space 1 個 |
| `D2186-item5.md` | 末尾の空行を除去 | `f99a00f52afbd36d99ab06ae9bda7e91cae92ba2190d154453e8be1d8b0d0470` / 1696 | `0a18d8ca1b31bbe551aa87b40b9355885a7a5770fa323592a86fd1f266bb81c5` / 1695 | 原本 = `docs/decisions.md` の D2186 「### 項 5 — DW-O26 …」から「### 項 6」直前まで (awk で見出し切り出し)。復元 = 末尾に `\n` を 1 個足す |
| `T-2292-origin.md` | 末尾の空行を除去 | `c25d9aa505e2840f3c6d421997492f23bbc2c4b2e3657a29a7ac05f119e903d7` / 445 | `e9db659d8fd2eccd8fabaa3d2fe45724e5f850969214943ad9cfa29851196ff3` / 444 | 原本 = `docs/archive/worklog-phase3-0903-1238-1239.md` 480〜484 行 (`sed -n 480,484p`)。復元 = 末尾に `\n` を 1 個足す |
| `s6-review.md` | 行末の空白 (`[ \t]*$`) を除去 (8 行、markdown の行末 2 space 改行を含む) | `f6d0fbda87e2585669f587ed36b0fb025c1c88314c059eed45c1e0555881afb6` / 4546 | `e9524031c85a4fe9a03d17155befc269c7e2e85835de0fdbc1e8d7c0e6200e82` / 4530 | 原本 = job dir `codex/s6-review.md` (未加工)。差は該当行末の半角 space |

job dir = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/`。他の逐語 file は無加工。
