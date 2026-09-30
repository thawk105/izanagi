---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: dev-wave-md20-lock-order-loop
seq: 1
---

## 新規

### {{F:author-stop-rule-hits-untestable-sandbox}}. 実装子 prompt の「失敗したら止まれ」が子の既知の試験不能 (rc=16) にも掛かり、段 5 の実装子 2 本が同時に途中停止した [手順漏れ]

- 事象: md_20 wave ([T-2888]・[T-2946]) の段 5 で、並列の実装子 2 本 (判定器・pipeline 側と driver・関門側) が、実装の途中で `tools/run_tests.py` を試し、
  子の sandbox から計算ノードの状態確認 (`qstat -Q`) ができずに rc=16 になった時点で、prompt の「失敗したら推測で進めず、その時点の事実を書いて止まれ」に従って停止した
  (投入 2026-09-30 22:52、停止 23:05 前後。production 追加 105 行・447 行の途中、試験は 0 件)。継続子に「試験は走らせず未実走で完成させる」と明記して出し直し、2 本とも完了した。
- 根本原因: 子が `tools/run_tests.py` も `python -m pytest` も走らせられないことは既知 (/rulings 第 30 回項 8: 子に自走の実走を指示しない、報告は「実装済み・未実走」、赤の実測は親の焦点走) だが、
  親の prompt は「自走できるものは走らせる」「失敗したら止まれ」を並べて書き、試験の不能がその停止規則に当たらないことを書かなかった。`DW-S05-C` の「実走不能なら『実装済み・未実走』と書く」と
  停止規則の優先関係は、どこにも書かれていない。
- 恒久対応: memory `codex-child-discipline` の節「sandbox-children-use-self-run-harness-not-pytest」(子は run_tests.py・pytest を走らせられない、prompt に書く) を段 5 の prompt を書く前に引く。
  実装子・fix 子の prompt に「試験は走らせず、直し終えて『実装済み・未実走』と報告せよ。試験を走らせられないことを理由に止まらない」の 1 文を入れる (本 wave の継続子・fix 子 4 本はこの 1 文で全件完了した)。
- 再発検知: 実装子の報告が「test 起動が失敗したため停止」「実装途中」を含み、`.done` の rc が 0 のもの。受理検査 (`check_codex_output.py`) は通るので、親が報告の総括を読んで判定する。
