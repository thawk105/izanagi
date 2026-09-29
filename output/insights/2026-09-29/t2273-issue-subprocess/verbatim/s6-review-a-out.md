## 所見

- **must-fix — [s8b_holdout_freeze.py:574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:574)**: `MappingProxyType` は背後の dict を変更できるのに、内容確認を省いて共通 literal の結果を再利用する。例えば `{"p": "x"}` の proxy と memo で `(?:ab=z)` を走査後、背後を `"ab=v"` に変えて `(?:ab=v)` を走査すると、新 cache は「ab 不在」を再利用する。旧実装では第2式が hit するため、**受理集合と report bytes が変わる**。D512 の内容変化拒否にも反する。
- **should-fix — [s8b_holdout_freeze.py:598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:598)**: `str` subclass の `find` が `-1` を返す場合、実体が `"ab=cd"` で式が `(?:ab=cd)` でも、旧経路の `in` と regex は hit、新経路は不一致になる。通常の file decode は exact `str` だが、`_scan_one` の受理集合と report bytes は変わる。
- **should-fix — [s8b_holdout_freeze.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:21)**: `sre_parse` は Python 3.11 から非推奨で、[Python 3.15 では削除される](https://docs.python.org/3.15/whatsnew/3.15.html)。3.11 以降の警告をエラーにする環境や 3.15 では module import 自体が失敗し、検索 report を生成できない。3.9/3.10 の通常 import にはこの差はない。

## 変異と番人

M1〜M3 の単軸 fixture は右端、JSON の左端、重複出現を個別に踏む。M4 は窓付き search の記録、M5 は異なる literal の第2走、M6 は共通判定回数で検出する構成になっており、実装子の「各1理由で赤」という申告と静的には整合する。ただし実走結果そのものは検証していない。既存の prefilter・memo 番人も候補数と独立 reference を保持している。共通 literal が `None` なら軸 literal は導出されず、全文 search に戻る。変更2 file に具体値まで連続した軸 key literal は見当たらない。

## 判定

**修正後 GO**。少なくとも memo の内容変化による新たな偽陰性を解消し、再検査が必要。

## 総括

窓式自体には、受理文法と exact `str` の範囲で反例を見つけなかった。
memo の proxy 経由の内容変化には新たな report 差がある。
このレビューは静的検査のみで、test は実走していない。