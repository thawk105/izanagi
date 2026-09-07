## 所見

1. **[must-fix候補 / schema・D1699] 厳密に固定した受理 schema が、既裁定で不適合になった旧 `v2` である。**  
   プランは `floor-pair-summary/v2` だけを受け、現行 `finalize_floor()` との integration test を要求する一方、driver は変更しない（[s2-plan.md:15](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/artifacts/b4-floor-issue-wire/s2-plan.md:15)、[s2-plan.md:138](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/artifacts/b4-floor-issue-wire/s2-plan.md:138)）。現行 driver は「二つの candidate session と一つの reference session」から D を作り（[floor_pair_driver.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/floor_pair_driver.py:4)）、実際に三つの独立 session を計画する（[floor_pair_driver.py:1257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/floor_pair_driver.py:1257)）。D1699 はこの形を明示的に退け、candidate と reference を同じ低水準 session で測り、D の式を再凍結せよとしている（[rulings-verbatim.md:218](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/rulings-verbatim.md:218)）。  
   v3 の外部申告を根拠にしなくても、現物と D1699 だけで v2 の意味は権威化不可と判定できる。  
   **影響:** authority の `floor_exact` が旧 D の値になり、受理集合は「正しい将来版を拒否し、既知不適合の v2 を受理する」集合になる。

2. **[must-fix候補 / P1-c・D1377] `adoption-record` は権威束縛ではなく、名前を変えた caller 自己申告である。**  
   CLI caller が `--summary` と `--adoption-record` を選び（[s2-plan.md:19](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/artifacts/b4-floor-issue-wire/s2-plan.md:19)）、採用記録は `decision_id` が `D<正整数>` であることと、caller が書いた summary path/hash しか要求しない（[s2-plan.md:31](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/artifacts/b4-floor-issue-wire/s2-plan.md:31)）。その D が当該 summary の採用裁定かを検証する固定位置・producer・decision 内容との束縛がない。D1641 が要求するのは「採用裁定を D として記録する」ことであり（[rulings-verbatim.md:107](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/rulings-verbatim.md:107)）、D らしい文字列ではない。これは自由記述の出所を添えても正当性は増えないとした D1377 の却下理由と同型である（[rulings-verbatim.md:21](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/rulings-verbatim.md:21)）。  
   さらに `artifact_identity.protocol` 等は summary の実 field ではない。現行 summary の top-level は [floor_pair_driver.py:2688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/floor_pair_driver.py:2688) の集合だけで、`protocol` は spec に加えても unknown key として拒否される（[test_floor_pair_driver.py:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/tests/test_floor_pair_driver.py:592)）。したがって filename identity も adoption-record 作成者の申告である。  
   **影響:** caller は複数の v2 summary から値を選び、無関係な D 番号と任意 identity を添えて authority の値・path・参照を決められる。

3. **[must-fix候補 / D1530・D1592] 「同じ wave」には見えるが「同じ変更単位」は保証されず、実 producer も接続されない。**  
   D1592 は発行前提と production 配線を「実 producer の接続と同じ変更単位」で閉じるとしている（[rulings-verbatim.md:94](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/rulings-verbatim.md:94)）。しかしプランは A=standalone issuer、B=report 配線という二単位に分け（[s2-plan.md:144](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/artifacts/b4-floor-issue-wire/s2-plan.md:144)）、`floor_pair_driver.py` は変更しない。integration test は producer 接続の代わりにならず、A 単独では未接続 interface、B 単独では A の未着地 API への依存になる。  
   **影響:** 分割 landing が可能なままだと、発行だけ／配線だけの中間状態が repository の受理面に残り、D1530 が禁じた古びる未接続 interface を再現する。

4. **[must-fix候補 / P1-a・D1383] `nextafter(+∞)` は型変換ではなく floor 値の変更であり、裁定されていない。**  
   `candidate_floor.as_integer_ratio()` は binary64 の値を一切変えず evaluator が受ける整数 tuple にできる。契約もその tuple を受理する（[p3_b4_analysis_contract.py:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/campaign/p3_b4_analysis_contract.py:233)）。それにもかかわらずプランは必ず一つ上の float へ動かす（[s2-plan.md:69](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/artifacts/b4-floor-issue-wire/s2-plan.md:69)）。現行 producer は `0.0` も正規に生成する（[test_floor_pair_driver.py:2024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/orchestrator/tests/test_floor_pair_driver.py:2024)）ため、その場合さえ最小正 subnormal へ変更される。親 brief の「型の断絶」は実在するが、「切上げが必要」という P1-a は成り立たない。  
   **影響:** evaluator の tie 境界が採用された `candidate_floor` と異なり、1 未満の正規な最大値の一部は発行拒否へ変わる。AI が未裁定の別値を既成事実化する。

5. **[must-fix候補 / P1-b・解決規則] resolver の exact grammar は §5 に実在しない。**  
   プランが要求する `artifact_path=<...>; sha256=<...>` は新規のコード側規則である（[s2-plan.md:101](/home/SFC/tanab/.claude/jobs/bc895de9/tmp/b4-floor-issue-wire/artifacts/b4-floor-issue-wire/s2-plan.md:101)）。現物の floor 行は逐語で  
   `|floor (対象動作点で再実測した between-run floor) の artifact パスと hash|未記入|`  
   である（[phase3-b4-reflux-ablation-preregistration.md:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/docs/phase3-b4-reflux-ablation-preregistration.md:162)）。§11 も「path と hash」としか定めず、採用 D は commit message に置く案である（[phase3-b4-reflux-ablation-preregistration.md:927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-issue-wire/docs/phase3-b4-reflux-ablation-preregistration.md:927)）。  
   **影響:** 後続担当が別の合理的表記で正しく記入しても拒否され、逆に plan 作者が選んだ未裁定構文が de facto の受理契約になる。

## scope 外だが real

- D1695 の n=62 と D1699 の同一低水準 session/D 再定義へ producer を適合させ、意味が変わる版に新しい schema identity を与える作業。これは本 wave 外でも、authority 発行の前提である。v3 という名称自体は別 session 由来なので未確定として扱う。
- §5 の実記入、採用 D を伴う commit、残り 9 欄と §6 の充足。現在は sentinel のため、本 wave の resolver を実装しても正規 report は引き続き常に absent branch である。
- D1696 が人手責任に残した 9 項目、特に 5 要素名、sample/window、finalize hash の確認。新 validator の追加は却下済みなので、これを must-fix の実装拡張とはしない。ただし report が「機械検査済み」と誤表示してはならない。
- [T-2289] closure receipt の production 接続は明示どおり別件のまま残る。

## 反証できなかった点

- schema 判定そのものは exact `floor-pair-summary/v2` の閉集合であり、v2/v3 を名前を無視して横断受理する緩さはない。意味の異なる v3 は fail-closed で拒否できる。ただし受理対象を旧 v2 にした点は上記所見 1。
- material report 側は固定の repository 内 preregistration pathだけを読み、public API/CLI に floor や artifact path を追加しない案である。この層単独では caller の floor 注入口は増えない。
- A/B の列挙上の編集 file は重ならない。衝突は textual ではなく、D1530/D1592 が要求する atomicity と A→B の API 依存である。
- closure tuple は変更せず、[T-2289] を実質的に同梱する記述も見つからなかった。
- プランには具体的な既定 floor や tracked sample authority artifact は書かれていない。明示的に synthetic な一時 fixture だけなら、それ自体は D1383 違反とは断定できない。
- floor が present でも report 全体を evidence-only、§5 not in effect、4分類未実効のまま保つ限定は §11.3 と整合する。

## 総括

- must-fix候補は、既知不適合な v2 semantics の権威化を止めること。
- adoption-record を caller 作成 JSONではなく、実在する採用 D へ束縛すること。
- issuer と production 配線を分割 landing 不可の同一変更単位にすること。
- `nextafter` による未裁定の値変更をやめ、採用値を exact に保存すること。
- §5 の non-sentinel grammar を裁定なしにコード側で既成事実化しないこと。
- 検査は静的にのみ行い、pytest は実行していない。