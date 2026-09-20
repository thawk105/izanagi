# 逐語の可逆最小正規化 (DW-S07、`git diff --check` 抵触の解消。可視文字は不変)

| file | 正規化 | 原文 sha256 / bytes | 正規化後 sha256 / bytes | 復元法 |
|---|---|---|---|---|
| `focus-post-fix1.log` | 行末の空白 (`[ \t]*$`) を除去 (14 行) | `0a709ce76cf391a4d4fef0e2860ee2c3b8c0085d3eb0eb72f845f67752bc4917` / 13373 | `671c5e7966858f8cacdf04fab5457b2686fec0907961a618b2c52d4c0d648688` / 13359 | 原本 = job dir `focus/focus-post-fix1.log` (未加工)。差は各該当行末の半角 space 1 個 |
| `focus-post-fix2b.log` | 同上 (2 行) | `47ae92856579fe065ae8e9a238d49e0b3fd71e4e62ca9d12c70933527127bcd6` / 6583 | `c29ae3107091d6c2953becbf20e95a0549534b591a1a1cbd8289a0ffe17f4f18` / 6581 | 原本 = job dir `focus/focus-post-fix2b.log` |
| `design-memo-item6.md` | 末尾の空行 1 行を除去 | `8b4795c5685b6b5241cee5f1b2001e41d78c753c18018bbcca9db5acb52a5fa5` / 2968 | `51bc95e4ef73911abb3b382b1b452c8d7549e05bec78763f333eb5f6ea161e0f` / 2967 | 原本 = `output/insights/2026-09-19/k2-loop-round3/reviews/s2-plan.md` の 193〜223 行 (`sed -n 193,223p`)。復元 = 末尾に `\n` を 1 個足す |

job dir = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-pair-launcher/`。他の逐語 file は無加工。
