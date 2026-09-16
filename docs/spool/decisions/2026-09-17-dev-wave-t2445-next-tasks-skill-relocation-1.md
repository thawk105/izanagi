---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2445-next-tasks-skill-relocation
seq: 1
---

## {{D:next-tasks-codex-adapter}}. next-tasks Codex adapter は薄い委譲 + Codex overlay とし、Codex 起動時は事実も選定判断も起動主体が持ち、Claude の見解は独立検査として使う

**決定 (1): 移設の形は薄い adapter。** `.agents/skills/next-tasks/SKILL.md` は既存 3 skill (dev-wave /
rulings / cleanup-branches) と同型に、`.claude/commands/next-tasks.md` を共通 dispatcher として全文読んで
実行する委譲だけを持つ。repo 外 `~/.agents/skills/next-tasks/SKILL.md` (13,255 bytes、2026-09-10 版) の
手順・逸話は逐語複製しない。byte 予算は既存 3 skill と同じ扱いで `tools/check_docs.py` の個別 guard に
登録する (現物 5,458 bytes に rulings と同じ比率の余白を掛けた 5,460、`agents/openai.yaml` は 300)。

**決定 (2): D2051 の Codex 起動時の対応付け。** D2051 は Claude が `/next-tasks` を起動し codex へ相談する
形を前提に、事実 = claude の実測、選定判断 = codex の権威と配分した。Codex が `$next-tasks` を起動して
Claude へ相談する形では、裁定状態・機構実在・着地・稼働重複・系統 blocker・ユーザー手番の**事実**は
repo を実測できる起動主体 (Codex) が実測して権威を持ち、**選定判断**も Codex が権威を持つ (D2051 と
同じ側)。Claude の見解は、母集合から落ちた候補・着手不能リスク・前提事実の反証の独立検査として使う。
Claude が挙げた候補と「未確認」と書いた候補は実測せずに外さず、実測結果をまとめて 2 巡目 (全候補
まとめて 1 回、新事実の提示と再評価の依頼に限る) へ返し、返答を採否へ反映してから出力する。3 巡目へ
進めず、2 巡目の失敗で初回の判断を無効にせず、件数合わせで除外候補を復活させない。出所の明記・投げ文・
最終出力の文責は起動主体が負う。これは本 adapter の設計判断であり D2051 の再掲ではない。

**決定 (3): 旧 Codex 版だけにあった出力の義務は Codex overlay として保つ。** 投げ文への自己改善終端条件
(候補なしも明記)、CC 自動合成の候補を入れない理由の明記、既存 patch・OID・handoff をユーザーに転送・
再実行させず束ねること、補助 artifact を必須作業へ昇格させず検証済み単独行だけ示すこと、半角番号
(丸付き数字禁止) の 5 件を adapter の 1 節に置く。Claude 側の command は拡張しない。

**決定 (4): 契約側の終端。** `docs/skill-self-improvement.md` の `### next-tasks` は、昇格と起動手順は
rulings と同じ、既存手順の誤りは入口の編集条件に従って command の該当節を是正、道具は runbook の道具
置き場へ足す、`docs/` へ及ぶ変更は既成事実にせず裁定パッケージ、とする。command の絶対 path は
`<tools>` (所在は `docs/pegasus-runbook.md` §7.2) へ間接化する。

**理由:**

- 既存 3 skill は共通 dispatcher への委譲であり、既存置き場への合流 (D2104 項 37) は同型が最も安い。
  権威の指示文を 2 つ持つと D2051 のような改訂が片側に届かない (実測: 旧 Codex 版は D2051 決定 5 が
  上書きした「相談は 1 往復で終える」をまだ含んでいた)。
- D2051 の理由は「repo を実測できる側が事実を持ち、賢い側が判断を持つ」であり、Codex 起動時は両方が
  起動主体に重なる。相談先の Claude は read-only・15 分・裏取り 3 件の制約下で動くため事実の権威に
  なれない (plan 段の「事実は Claude」案を段 3 レンズ B が反証)。
- 旧版だけの義務 5 件は D2051 が廃止しておらず、移設で黙って落とす根拠がない (段 3 レンズ B)。旧版の
  「独立に評価する」は Codex → Claude の向きで、D2051 が問題にした Claude → Codex の押し切りとは別物。
- 道具の追加まで裁定待ちにすると 2026-08-17 のユーザー指示 (足りなければ同 directory へ足して次回から
  使う) を実行できなくなる (段 3 レンズ B)。

**却下した選択肢:**

- 旧 Codex 版 13,255 bytes の逐語複製 — 二重権威、予算不整合、D2051 前の規定の混入。
- plan の「事実は Claude、選定判断は Codex」 — 相談先を事実の権威にすると 2 巡目の主体が二通りに読め、
  Claude の実測を経ずに出力できる。
- Claude 側 command へ旧版の義務 5 件を足す — 候補生成ロジックの拡張は本 wave の scope 外。
- 契約文書の上限 6,000 の引き上げ — 重複・接続句の縮約で 5,997 bytes に収まり、D782 の上限引き上げは
  発火しない。
