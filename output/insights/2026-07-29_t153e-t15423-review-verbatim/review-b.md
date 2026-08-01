結論は **NO-GO** です。指定7ファイルと `author.md` を全文確認しました。編集・pytest・mutation 実走はしておらず、author の緑報告も検証済み事実として採用していません。

### Findings

1. **severity: high / real — `--no-divider` が既存 AI-Agent/Codex-author 受理集合まで変更**

   - file:line: [tools/check_ai_provenance.py:92](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:92)、[tools/check_ai_provenance.py:117](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:117)、[tools/check_ai_provenance.py:256](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:256)、[brief.md:9](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/brief.md:9)
   - `--no-divider` の parser を CAB だけでなく既存 AI-Agent と Codex-author 判定にも共有しています。CAB がない message でも、`---` 後の AI-Agent を新たに認識したり、divider 前の従来 trailer を失ったりします。現行規約の確認例は通常の Git trailer 解釈です。
   - 放置時の影響: CAB 以外の provenance 受理集合まで拡大・縮小し、divider 後の Codex author 行で実装 commit が受理され得ます。予算検査への影響はありません。
   - 最小fix: AI-Agent/Codex-author は旧 divider 意味論を保つ parser、CAB 配置だけを `--no-divider` parser に分離する。AI 意味論も変えるなら brief の不変条件を覆す明示裁定と CAB 無し・実装 path の両方向境界テストが必要です。

2. **severity: high / real — M1 は CAB 単一理由 kill にならない**

   - file:line: [test_check_ai_provenance.py:142](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:142)、[test_check_ai_provenance.py:215](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:215)、[adjudication-plan-v2.md:42](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/adjudication-plan-v2.md:42)
   - accepted divider case は `base` を `cab` より先に assert します。`--no-divider` を外すと AI-Agent が消え、CAB assertion に到達する前に既存 base gate で赤になります。逆方向の rejected case も最初の赤は AI-Agent です。
   - 放置時の影響: mutation 台帳上は M1 kill でも、CAB divider 検出力は証明されません。CAB gate が壊れた受理集合を段6が誤って承認できます。
   - 最小fix: parser 分離後、AI-Agent 結果を固定した CAB-only helper/CLI fixture で、CAB finding だけが変化する node を登録する。

3. **severity: high / real — M2 ambient config fixture は非単一理由かつ cwd 配線欠落を見逃す**

   - file:line: [test_check_ai_provenance.py:261](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:261)、[test_check_ai_provenance.py:278](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:278)、[test_check_ai_provenance.py:288](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:288)、[test_check_ai_provenance.py:304](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:304)
   - `GIT_CONFIG_PARAMETERS="malformed"` のため env 隔離を外した赤は alias 相殺ではなく Git parser error になり得ます。これは false acceptance ではなく fail-closed です。
   - 一方、`cwd=TRAILER_PARSE_CWD` だけを削除すると、テストは `tmp_path` へ `chdir` していないため、一時 repo に置いた alias configへ到達しません。末尾の定数 assert は、その定数が subprocess の `cwd` に使われたことを証明しない恒真寄りの pin です。
   - 放置時の影響: ambient alias が body CAB と alias trailer を相殺して分断 message を受理する回帰が、mutation 済みとして誤承認され得ます。
   - 最小fix: `monkeypatch.chdir(tmp_path)` を入れ、alias 相殺 fixture から malformed env を外す。cwd 隔離、global/system、`GIT_CONFIG_COUNT` を別 fixture・別変異 anchor に分け、期待結果を例外ではなく `cab == []` または CLI rc=0 に固定する。

4. **severity: high / real — policy needle のテストが本体定数を自己追認する F9**

   - file:line: [tools/check_ai_provenance.py:26](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:26)、[test_check_ai_provenance.py:61](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:61)、[test_check_ai_provenance.py:440](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:440)
   - synthetic policy はすべて `provenance.CO_AUTHORED_BY_POLICY_NEEDLE` を本文へ差し込みます。本体定数が実 policy 文言から drift しても、テスト側も同じ誤文字列を導入して全履歴テストが通ります。
   - 放置時の影響: 実 docs の policy 導入後も ancestry gate が永久に不発となり、履歴経路だけ split CAB commit を受理します。
   - 最小fix: テスト側に独立 literal を置いて production 定数と一致を assertし、synthetic policy は独立 literalから作る。親 docs land 後は実 `docs/ai-provenance.md` に exact 1件あることも固定する。

5. **severity: medium / real — policy 導入 commit 自身の負境界がない**

   - file:line: [test_check_ai_provenance.py:61](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:61)、[test_check_ai_provenance.py:387](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:387)
   - epoch commit は常に正常な `CODEX_AUTHOR` で、違反は次 commit にしか置かれていません。policy 検索を `commit^` から始める off-by-one 変異は全現行テストを生存できます。
   - 放置時の影響: policy と checker を導入する統合 commit 自身だけ CAB 分断を受理し、同一commit closure が一件広くなります。
   - 最小fix: policy needle を追加する commit 自身を `SPLIT_CAB_NONE` にし、その commit 単独 range が rc=1 になる境界 nodeを追加する。

6. **severity: medium / real — plan v2 が約束した fence 拒否にテストがない**

   - file:line: [adjudication-plan-v2.md:13](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/adjudication-plan-v2.md:13)、[test_check_ai_provenance.py:149](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:149)
   - 現実装の raw regex は fence 内も数えるため現在の挙動自体は正しいものの、rejected matrix は indent だけで fence を固定していません。
   - 放置時の影響: 将来 Markdown-aware scanner が fence 内候補を除外すると、policy が拒否するとした曖昧 attribution を履歴/message-fileが受理します。
   - 最小fix: backtick/tilde fence 内の列頭 CAB 候補を各1件、CAB finding 単独の負例として追加する。

7. **severity: nit/backlog / real — 診断文字列 pin は kill と別枠にすべき**

   - file:line: [test_check_ai_provenance.py:226](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:226)、[test_check_ai_provenance.py:400](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:400)
   - exact finding 文言だけの変更でも赤になります。これは有用な diagnostic sensitivity pin ですが、受理集合 kill ではありません。
   - 放置時の影響: checker受理集合・予算には直接影響なし。ただし mutation 台帳が単なる文言赤を kill と数えると証拠を過大評価します。
   - 最小fix: テスト削除は不要。mutation 記録で rc/空非空の変化と診断だけの変化を分離する。

### Refuted / 静的に充足

| 疑義 | 判定 | file:line | 放置影響 / 最小fix |
|---|---|---|---|
| M3 boolean/set | refuted | [test_check_ai_provenance.py:110](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:110)、[同:189](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:189) | exact duplicate 正例と body+final 同値負例が相補的。追加fixなし。 |
| M4 `none` early return | refuted | [tools/check_ai_provenance.py:157](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:157)、[test:167](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:167) | base は正常で CAB finding だけが必要。単一理由。 |
| M5 常時適用 | refuted。ただし finding 4/5 は別 | [test_check_ai_provenance.py:404](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:404) | legacy commit 単独 range が rc=0 の正例。常時適用変異は単独で死ぬ。 |
| M6 三CLI経路 | refuted | [default:387](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:387)、[range:404](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:404)、[message-file:542](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:542) | 各負例は CAB 以外が正常で、配線除去時に rc=0 へ変わる。 |
| M7、9000/9001 | refuted | [test_check_docs.py:427](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_docs.py:427)、[同:438](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_docs.py:438) | 9000 は `>=` 型過剰拒否、9001 は `all_limits` unwire をそれぞれ検出。9001 は診断だけでなく rc が1→0になる。 |
| registry全consumer / dispatch非拡張 | refuted | [tools/check_docs.py:231](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:231)、[同:1466](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:1466)、[test:417](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_docs.py:417) | 現構造の production budget consumer は `all_limits` 一箇所。governed test集合にも追加され、dispatch allowlist は未拡張。 |
| 既存件数・plain-runner | refuted（実走は未確認） | [docs runner:3041](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_docs.py:3041)、[provenance runner:577](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:577)、[meta-test:60](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_plain_runner_coverage.py:60) | 静的には provenance 40 nodes、docs 126 nodes と算術一致し、patch に既存test削除なし。author の「passed/赤0」は本レビューでは採用していない。 |

## 総括

**NO-GO。** must-fix は、(1) CAB parser の `--no-divider` を既存 AI-Agent/Codex-author 意味論から分離するか、受理集合拡張を明示再裁定すること、(2) M1 を CAB finding 単独の kill にすること、(3) M2 を valid ambient config・実到達 cwd・単一 alias 相殺へ分割すること、(4) policy needle を独立 literal で pin し導入 commit 自身の負境界を追加すること、(5) plan v2 が宣言した fence 拒否を固定することです。

静的 mutation 期待表（未実走）:

| 変異 | 期待 node / 受理集合変化 | 静的判定 |
|---|---|---|
| M1 `--no-divider` 除去 | divider 正例の拒否、逆向き負例の受理 | **無効**。両 node とも CAB より先に AI-Agent base assert が赤。 |
| M2 config隔離除去 | alias が raw=1/parsed=1 を作り split CAB を誤受理 | **無効**。env除去は malformed parser error、cwd除去はtmp config非到達で生存可能。 |
| M3 boolean/set化 | `body-and-final-same-value` を誤受理、または exact duplicate を過剰拒否 | **有効**。相補fixtureがありCAB単独。 |
| M4 none早期returnでCAB破棄 | `cab-then-blank-then-ai` を誤受理 | **有効**。base正常、CABだけが消える。 |
| M5 ancestryを常時適用 | pre-policy commitを過剰拒否 | **有効**。legacy単独rangeがrc=0正例。ただしneedle driftとepoch off-by-oneは別途生存。 |
| M6 各CLI配線除去 | default/range/message-fileの対応負例がrc=1→0 | **有効**。三経路に独立nodeあり。 |
| M7 registry unwire | 9001 bytesを誤受理 | **有効**。9001 nodeがrc=1→0、9000正例が過剰拒否を監視。 |
| 過剰拒否controls | CAB無し、mixed-case/colon-space、duplicate、CAB+none、bullet/quote、9000 | 概ね有効。ただし divider control はM1のAI maskあり、fence拒否controlは欠落。 |

したがって M3〜M7 と予算全層配線、dispatch非拡張、件数保存は静的に支持できますが、M1/M2とpolicy activation oracleが段6の単一理由・F9要件を満たしません。ここを閉じる前に mutation matrix を「全kill」と記録すると、実際より広い CAB 機械受理集合を承認することになります。