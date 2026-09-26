## 所見対応表

| ID | 判定 | 根拠 |
|---|---|---|
| 親 F1 | closed（静的） | lost update と直列対照の key は `aa` に修正された。[test_verifier.py:4139](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:4139)。同ファイルの検証ラッパーが synthetic Silo の proof source を渡し、試験は proof gate 成立、malformed・framing が 0、直列対照の certified、lost 側の表 1 の ww・rw を要求する。[test_verifier.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:58) [test_verifier.py:4152](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:4152) |
| RA1 / RB1 | closed（静的） | executor の全ケースで使う R/W の key が `aa` になり、certified 正例と witness 不一致だけの診断をそれぞれ assert する。[test_campaign.py:7519](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7519) [test_campaign.py:7557](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7557) |
| RA2 | closed（静的） | v2 対照は有効な key と一致する commit witness を持つ。[test_campaign.py:7523](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7523)。同じ trace_dir を verifier 単独で検証して certified を要求し、executor では v3 要求による拒否を要求する。[test_campaign.py:7560](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7560) |
| RB2 採用部分 | closed | `_run_trace` に、YCSB と TPC-C 段 1 の許可理由、計数修正の前提、verifier 後の v3 要求を記した。[pipeline.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:434)。critic の文言は裁定どおり対象外。[s6-ruling.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/s6-ruling.md:16) |

## 新規所見

なし。`fix1.diff` の production 変更はコメント 3 行で、試験の修正も今回追加した関数内に限られる。[fix1.diff](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/fix1.diff:1)。既存試験の期待値変更は見当たらない。

## 総括

- v2 の単独検証は、executor が trace を書いた後、削除前に同じディレクトリを**読み直す**。executor は後片付けを行わず、verifier の経路も trace を読むため、`standalone.certified` が再利用順序だけで偶然緑になる構造は見当たらない。[pipeline.py:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:508) [core.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:38)
- M2 を旧射影へ戻すと、existence 詳細を要求する executor assertion が赤になる。これは**診断の欠落**の検出であり、受理集合の変化の検出ではない。[test_campaign.py:7573](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7573) [core.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:194)
- M8 で v3 要求を外すと、単独では certified の v2 trace が後続の認定経路へ進むため、拒否 assertion が赤になる構成である。[pipeline.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:642) [test_campaign.py:7560](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7560)
- M11 は ww・rw assertion で赤になり得るが、単一理由性がないため登録から外す判断でよい。[test_verifier.py:4158](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:4158)
- 判定は静的レビューである。executor 試験と変異の実走結果は含めていない。