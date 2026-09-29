| 前回所見 | 判定 | 根拠 |
|---|---|---|
| B-1 再生成手順 | **partial** | wrapper の `draw` と必須引数、参照 path、wrapper・生成器・入力の SHA-256 は一致する。ただし掲載コマンドの出力先はそのまま実行できない。 |
| B-2 caption の符号差 | **partial** | [figures/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/figures/README.md:8) の説明は一次資料と合う。R2 の効果は rr5 `+65.4129%`・rr50 `+12.8953%`、原 fig6 も `+63.5485%`・`+14.4213%`。末尾の文は[原 fig6 の README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/docs/paper-story/figures/README.md:608)にもある。ただし注記は画像自体にはなく、PNG・PDF 単体で読む際の誤読は残る。 |
| B-3 受入実測 | **partial（open）** | [§9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/README.md:181) は受入後に記録すると明記しており、未実施を実測済みとは主張していない。 |

| ID | 重大度 | 場所 | 問題 | 根拠 | 直し方 |
|---|---|---|---|---|---|
| F-1 | should-fix | [figures/README.md:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/figures/README.md:25) | `--out-prefix <出力 dir>/...` は実行可能な shell 引数ではない。 | `<`・`>` がリダイレクトとして解釈され、wrapper に必要な絶対 path が渡らない。 | 例示中で `OUT="$(mktemp -d)"` を定義し、`--out-prefix "$OUT/fig6_r2_a2_certification"` とする。 |

**NO-GO**（静的検査。再生成の実走はしていない。）

## 総括

差分の注記に事実の誤りは見つからなかった。再生成コマンドを実行可能な形に直し、画像単体での caption の誤読を解消する必要がある。