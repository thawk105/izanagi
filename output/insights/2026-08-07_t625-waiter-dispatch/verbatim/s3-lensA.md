静的検査のみ実施した。pytest / `check_docs` は実走しておらず、緑・赤は主張しない。

## Real 所見

### 1. 条件 24 → `DW-C00` の独立 oracle がない

- 主張: 提案された削除 mutation は行の存在を検査するが、参照先が本当に `DW-C00` かは独立に固定しない。入口と契約をともに `DW-CTX` へ誤配線しても、提案テストは通る構造である。
- 根拠: synthetic 行は契約から生成されるため、checker と fixture が同じ値を共有する。[test_check_docs.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:476) [check_docs.py:3894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3894)。独立 literal pin は operations と特殊 key `15` だけで、core key は固定しない。[test_check_docs.py:4720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4720) [test_check_docs.py:4740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4740)
- 成果物影響: `check_docs` の受理集合に「条件 24 は存在するが `DW-C00` を届けない入口」が残り、待ち手規約が事故直前に参照されず、worklog／試行台帳の欠落経路が残る。
- 深刻度: must-fix

### 2. 発火条件の裁定逐語は一切検査されない

- 主張: 「背景 producer・…通知処理の直前」を「常に」「producer 起動後」などへ変更しても、提案された契約・削除 mutation・real-repo check は通る。
- 根拠: dev-wave parser は条件セルを保持せず、key・参照 pair・parse 済み row 数だけを保持する。[check_docs.py:3179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3179) [check_docs.py:3185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3185)。実際、synthetic fixture の条件セルは裁定文でなく `synthetic` である。[test_check_docs.py:477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:477)。provenance 側は別 parser で条件文を保持・逐語比較している。[check_docs.py:1837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:1837) [check_docs.py:3775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3775)。プラン自身もこの穴を認めて scope 外としている。[s2-plan.md:114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s2-plan.md:114)
- 成果物影響: `check_docs` の受理集合に、条件 24 の参照先だけ正しく発火時点が誤った入口が残る。結果として対象境界で `DW-C00` が読まれない。
- 深刻度: must-fix

### 3. 「key ごとに厳密に 1 行」は parse 可能行にしか成立しない

- 主張: プランの一意性説明は過大である。同じ `| 24 |` を持つ第2行でも、3列未満または backtick 付き path がなければ parser が無視し、row count は1のままになる。
- 根拠: 条件表の行は `len(cells) < 3` または path regex 不一致で無条件に skip される。[check_docs.py:3180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3180) [check_docs.py:3183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3183)。それに対しプランは key ごとに厳密1件と記す。[s2-plan.md:111](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s2-plan.md:111)
- 成果物影響: `check_docs` は、人間には条件 24 が二義的に見える入口を受理できる。競合行の条件・参照を manager が採れば `DW-C00` の到達性が変わる。
- 深刻度: must-fix

### 4. 親 brief の既存条件数が 1 件多い

- 主張: 現在の条件 dispatch は22行であり、「既存23条件」は誤り。追加後が23行である。
- 根拠: 現行表は `01` から始まり [dev-wave.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:84)、`23` で終わる [dev-wave.md:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:105)。プランは正しく22本と数えている。[s2-plan.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s2-plan.md:7)。brief は23条件とする。[s1-brief.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s1-brief.md:34)
- 成果物影響: 実装どおりなら受理集合は変わらないが、総数を使う mutation／記録の期待値を誤らせる。
- 深刻度: nit

### 5. 「case／mutation／needle のどれが欠けても失敗」は case 登録について偽

- 主張: `_COMMAND_GUARD_CASES` への登録だけを落とすと、その case は parametrization されず無言で消える。
- 根拠: pytest の入力集合は `_COMMAND_GUARD_CASES` 自身である。[test_check_docs.py:5142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:5142)。期待件数も同じ集合から生成される。[test_check_docs.py:4703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4703)。プランの「いずれかが欠けると失敗する」という説明とは一致しない。[s2-plan.md:104](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s2-plan.md:104)
- 成果物影響: checker の現在の受理集合は直ちに変わらないが、条件24の回帰検出 case が収集集合から消える。
- 深刻度: nit

## Speculative 所見

なし。上記はすべて静的に構成できる受理経路である。

## 反証・確認済み

- key `24` は正しい。operations 自動生成集合は19件で、O07/O15を除外し、21/22をcore条件用に予約、23をlandに使用している。[check_docs.py:371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:371)。したがって24は `_OPERATION_NUMBERS` ではなく手動 update 側へ入れるべきである。[check_docs.py:497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:497)
- 誤って自動側と手動側の両方へ入れると、手動 `update` が条件 map のO24束縛を黙って上書きする。ただし必須H2・段5/6集合にはO24が残り、独立 operations pin が拒否するため、検査全体を黙って通過はしない。[check_docs.py:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:410) [check_docs.py:440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:440) [test_check_docs.py:4726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4726)
- provenance の同名 heading は別ファイルの別 parser 呼出しで、keys も `correction` 等であるため `24` と衝突しない。[ai-provenance.md:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/docs/ai-provenance.md:86) [check_docs.py:3733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3733) [check_docs.py:3874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3874)
- `_rewrite_matching_lines` の `expected` 省略は安全で、既定値1かつ `matched == expected` assertion がある。0行置換は通らない。[test_check_docs.py:4155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4155)
- byte計算は正しい。現物は8908 B、LFのみ・末尾LFあり、最大137文字。追加行は82文字／126 B、LF込み127 Bなので9035 B、余裕465 B、最大行は137文字のまま。checker もUTF-8再encodeと `splitlines()` で同じ尺度を使う。[check_docs.py:3541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3541)
- 発火条件文字列自体には backtick 付きpath／sectionがなく、`_DISPATCH_TOKEN_RE` に触れない。[check_docs.py:1671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:1671)
- live consumer は入口、`check_docs.py`、そのテストだけ。Skill は入口を共通dispatcherとして参照するだけで key を複製しない。[SKILL.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.agents/skills/dev-wave/SKILL.md:14)。生成 `openai.yaml` はUI metadataのみ、`tools/check_codex_agents.py` はrole-adapter inventory検査で条件集合を読まない。[openai.yaml:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.agents/skills/dev-wave/agents/openai.yaml:1) [check_codex_agents.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_codex_agents.py:2)。consumer取り残しはない。

## 総括

blocker はない。must-fix 3件、nit 2件。  
key `24`、手動契約側、名前空間、予算、leak、consumer判断は採用可能。  
ただし参照先・発火条件・可視key一意性を独立に固定するまで、現プランのままの採用は推奨しない。  
pytest / `check_docs` は未実走。