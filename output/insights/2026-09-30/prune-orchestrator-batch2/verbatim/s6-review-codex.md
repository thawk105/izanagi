## 所見

| # | 重大度 | 対象 file:行または節 | 内容 | 根拠 (file:line) | 修正案 |
|---|---|---|---|---|---|
| 1 | must-fix | insight README:12,23,64／fragment:7,13 | `backoff_nonmonotonicity_analysis.py` の**過去の再利用**を「現役の拘束的 consumer」として扱っている。提示された probe と hash hit は歴史記録であり、現在の実在を要求する根拠にはならない。ただし D2179 の「一回限り」条件は後続作業で再利用した事実により不成立なので、「残す」結論は維持できる。 | `verbatim-D1989.md` の「歴史的言及」、`verbatim-D2179.md` 条件 1、T-2583 README:380、T-2635 README:202 | D1989 上は歴史的言及、D2179 上は一回限り不成立、と分けて記す。「9 群すべてが現役の拘束を持つ」という総括も直す。 |
| 2 | must-fix | insight README:25 | `docs/orchestrator-design.md` §材料レポートは一般的な出力規約と `orchestrator/reports/` を述べており、`backoff_sweep_report.py` を D12 の射影器として名指ししていない。引用だけではこの module の拘束を立証できない。一方、共有 test は同 module を import し、`report_workload` 等を検査しているため、削除 0 の判断には別の根拠がある。 | `docs/orchestrator-design.md:117-128`、`orchestrator/tests/test_backoff_consumers.py:21,108-152` | D12 文書からの直接拘束という主張を弱め、共有 test の具体的な照合と削除単位への影響を根拠にする。 |
| 3 | nit | insight README:35,43,45 | 「消すと残る test のどこにも無くなる検査」という表題の下で、共有 test *file* の検査も「失われる」と書く。module だけを消せば共有 test は残って import に失敗するため、仮定する削除単位が曖昧。 | `orchestrator/tests/test_backoff_consumers.py:21`、`orchestrator/tests/test_s8b_oracle_artifacts.py:19-25` | 共有 test を丸ごと削除する仮定と、module だけを削除して test が壊れる場合を分けて書く。 |
| 4 | nit | fragment:7,13-16 | worklog の題と本文が insight の候補別判定を詳しく再掲している。worklog は協議・異常・工数と一次資料への索引を中心にする書式。H2 と frontmatter の構造自体は適合している。 | `docs/worklog.md:3-5,21-31`、`docs/spool/worklog/README.md:5,17-23` | 判定の詳細を insight への参照に縮め、裁定・段構成・セッション異常・工数を残す。 |

## 判定

**NO-GO** — 削除 0 は支持できるが、D1989 の分類と D12 を根拠とする記述を訂正してから記録すべき。

## 総括

指定された数値は現物と一致した。11 file・6,223 行、test 4,139 行、fixture 48 file、台帳の 222 node・788.8 worker 秒と全体比 4.9% を確認した。hash hit 台帳も 9 行で一致した。  
9 群の中に、この静的検査で削除可能と確定した群はない。主な問題は「残す」結論ではなく、その根拠の分類と強さである。  
fragment の構造違反や README の placeholder は見つからなかった。テストは実走していない。