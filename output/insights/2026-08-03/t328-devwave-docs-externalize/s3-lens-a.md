判定は **NO-GO**。必須 7 ファイルはすべて読了した。本レビューは静的検査のみで、`pytest` と checker は実行していない。

### A-1 — real / critical: 新族は総量上限の改名による引き上げであり、全経路の読量も増える

根拠:

- ユーザー裁定は総量上限を上げない: `s1-brief.md:15-19`
- 提案後の全 reference は 25,198 → 26,946 bytes、横断 ceiling は 27,200: `s2-plan.md:82-99,390-399`
- D110 は family 合計を 9,000 のまま維持し、分割 overhead を非義務重複の削減で吸収した: `docs/decisions.md:5125-5128,5154-5160`
- dispatcher は節単位で同じ条件節を読み続ける: `.claude/commands/dev-wave.md:56-105`

成り立ち得る反論は、「新族が別の consumer に属し、旧条件では読まれず、横断総量も 25,200 のままなら既存予算の引き上げではない」である。しかし本案では、移動節は以前から同じ dev-wave の条件 dispatch で読まれており、`DW-M06` は段 6 で常時読まれる。さらに横断上限を 27,200 に増やすため、この反論の前提がすべて崩れる。

比較対象を「command 全文 1 回、stage/condition ごとの指定節、段 8 の自己改善文書全文」に限定して再計数した。AGENTS・CLAUDE・worklog 等の両案共通分、新ファイルの前置き 285 bytes、子自身の再読は除外しているため下限である。

- 通常実装: 条件 01/02/03/05/13/15/16/17/18/19/23
- docs-only: 段 5/6 を飛ばし、条件 01/02/03/05/13/17/18/23
- 凍結成果物: 通常実装に 08/09/10 を追加
- Codex 起動数は、段 2 が 1、段 3 が 2、実装子が 2、段 6 reviewer が 2 の最小値を使用。fix は未算入

| 経路 | 一意な節 payload | stage/condition 再読を含む下限 |
|---|---:|---:|
| 通常実装 | 36,561 → 38,228（+1,667） | 63,519 → 68,470（+4,951） |
| docs-only | 28,922 → 30,229（+1,307） | 39,650 → 42,185（+2,535） |
| 凍結成果物 | 37,940 → 39,607（+1,667） | 67,656 → 72,607（+4,951） |

`DW-O01` を読む追加の subprocess 1 件ごとに、提案後の増分はさらに 307 bytes増える。条件 20 が成立すれば、その読了回数ごとに 154 bytes増える。

低頻度判定も成立しない。`DW-O09` は docs-only でも成立すると逐語で定義され、実事故 F78 も同じ誤判定を記録している: `docs/dev-wave/operations.md:46-57`, `docs/failures.md:1657-1677`。プラン自身も `rare` を撤回している: `s2-plan.md:11-18`。

**失敗シナリオ:** primary 24,191 + risk 2,755 = 26,946 bytes を checker が受理する。旧来の「dev-wave 規範総量 ≤ 25,200」なら拒否される入力であり、通常・docs-only・凍結の全経路で context 読量も増える。

**影響:** 受理集合が最大 25,200 から 27,200 へ拡大し、reference 総量と全 wave 経路の読量が増える。

### A-2 — real / high: 新予算値の引き上げを「独立審査済み」に束縛する機械証拠がない

根拠:

- 自己改善契約は予算引き上げを独立審査へ送る: `docs/skill-self-improvement.md:48-51,57-60`
- 現行テストは数値を literal assert するだけ: `orchestrator/tests/test_check_docs.py:956-973`
- 提案テストも新しい数値 2,900 / 27,200 を literal pin するだけ: `s2-plan.md:229-241`
- checker は現在コード中に書かれた cap を超えた場合だけ拒否し、cap 変更の authority は検査しない: `tools/check_docs.py:2685-2691`

文言上は新族 cap も「予算値」に含まれる。しかし機械保証はない。

**失敗シナリオ:** 将来の自己改善 wave が risk ceiling を 3,200、横断 ceiling を 27,500 に変更し、同じ commit で pin テストの期待値も更新する。checker・テストはともに通り、ユーザー裁定や D 節の存在を要求する分岐はない。

**影響:** 台帳に独立裁定がないまま受理集合だけが拡大し、予算規律が prompt 規律へ退行する。

### A-3 — real / critical: 条件 dispatch の発火条件と列所有を checker が検査しない

根拠:

- generic parser は行全体から path/ID を抽出する: `tools/check_docs.py:1691-1725,2320-2364`
- `_DispatchTables` は条件文・列数・token 漏出を保持しない: `tools/check_docs.py:1638-1644`
- 実際の検査は pair と row count と allowlist だけ: `tools/check_docs.py:3014-3055`
- provenance 側には、発火条件・3 列・第 2 列 token・第 3 列 path を拒否する実装が既にある: `tools/check_docs.py:1761-1837,2873-2940`
- プランは弱い generic 構造をそのまま使う: `s2-plan.md:195-205`

**該当する構造クラス:** 期待される risk `(path, ID)` が第 2 列にあり、第 3 列が空または規範参照でない行。あるいは第 3 列を維持したまま第 2 列の発火条件だけを成立不能な文へ変更した行。どちらも `tools/check_docs.py:2352-2362` と `3034-3055` を通過する。

**失敗シナリオ:** 条件 09 の発火条件を成立不能に変更しても、行中に期待 pair が残るため checker は受理する。入口上は `DW-O09` が発火せず、凍結 bytes の列挙が消える。

**影響:** dispatch reference が到達不能になっても受理集合は変わらず、規範節が実運用から消える。

### A-4 — real / critical: sibling への間接委譲は現行・提案後のどの閉包分岐にも入らない

根拠:

- 現行の物理閉包は exact `docs/dev-wave/` root だけ: `tools/check_docs.py:2590-2611`
- 提案閉包も exact `docs/dev-wave-risks/` root だけ: `s2-plan.md:166-184`
- checker 自身が leaf から別 living doc への間接委譲を検査しないと明記する: `tools/check_docs.py:7-10,2320-2324`
- 一般 path lint は参照先の実在しか見ない: `tools/check_docs.py:3259-3267`

**該当する構造クラス:** `docs/dev-wave-risks.md`、`docs/dev-wave-risk-notes/**`、`docs/dev-wave-risks-extra/**` のような sibling path に規範 detail を置き、登録済み risk H2 からそこへ委譲する形。これは現行 `2590-2611` にも、提案 `s2-plan.md:170-183` にも該当しない。

**失敗シナリオ:** `guards.md` の `DW-O09` を短い外部参照へ置換し、実手順を sibling 文書へ移す。登録 leaf、予算、H2、dispatch pair はすべて残るため checker は受理し、sibling 本文は family 予算外になる。

**影響:** 規範 detail が reference 閉包と予算から逃げ、参照だけが登録 leaf に残る。

この穴は単純な path closure では塞げない。「規範委譲」と「証拠参照」を型付き記法で区別するか、命題 2 を「直接 dispatch と物理実体だけを閉じる」へ弱める裁定が必要である。

### A-5 — real / high: 登録ファイルの先頭 preamble は予算内だが dispatch 外に置ける

根拠:

- 現行 H2 検査は `^##` から得た ID だけを見る: `tools/check_docs.py:2769-2787`
- 提案も同じ H2 helper 化だけである: `s2-plan.md:186-203`
- 前置きは固定すると書くが、恒久 checker/test pin は計画されていない: `s2-plan.md:53-61,101`

**該当する構造クラス:** `guards.md` / `hang.md` の H1 と最初の必須 H2 の間に置かれた規範 prose。物理 member、byte 予算、必須 H2、孤児 H2、三面一致のどれにも違反しない。

**失敗シナリオ:** 全条件に適用すべき停止義務を最初の H2 より前へ置く。checker は受理するが、入口が exact section を読む際にはその義務へ到達しない。

**影響:** reference 総量には数えられる一方、dispatch 到達可能な規範集合から義務が欠落する。

### A-6 — real / high: 節 ID の全族一意性を拒否する production 分岐がない

根拠:

- H2 multiplicity はファイルごとに検査するだけ: `tools/check_docs.py:2769-2787`
- 提案 pair closure の key は `(path, ID)` である: `s2-plan.md:197-203`
- 提案テストは期待 path map を pin する予定だが、checker の global `ID → owner exactly one` 分岐ではない: `s2-plan.md:257-263`
- path を持たない `DW-O08/O09/O10` の rollback regex も残る: `tools/check_docs.py:486-493`

**該当する構造クラス:** 同じ `DW-O09` を旧 `operations.md` と新 `guards.md` の両 registry に登録し、両 pair を dispatch contract に含める形。budget/section/dispatch の path 三面と pair 閉包は自己整合できる。

**失敗シナリオ:** 移設時に旧 H2 を残し、primary registry と stage contractにも残す。各ファイルでは count=1、各 `(path, ID)` も登録済みなので standalone checker は受理する。

**影響:** ID 単独参照の所有者が二重化し、reference identity と dispatch 解釈が不定になる。

### A-7 — real / high: 既知の consumer 3 面が実装 scope から落ちている

根拠:

- Codex Skill は worker の参照先を `workers.md` と `operations.md` に固定する: `.agents/skills/dev-wave/SKILL.md:29-35`
- checker/test もその old 2 path を literal pin する: `tools/check_docs.py:263-270`, `orchestrator/tests/test_check_docs.py:3943-3963`
- 自己改善 routing は `docs/dev-wave/` の既存 leaf だけへ送る: `docs/skill-self-improvement.md:22-33`
- docs 地図も旧 4 本だけを family として列挙する: `docs/README.md:28-31`
- プランの docs 所有範囲は command・既存 4・新 2 referenceだけで、これらを含まない: `s2-plan.md:505-515`

`LIVING_DOCS` への追加も三面一致には含まれない。プランは追加を指示するが、budget/section/dispatch と `LIVING_DOCS` の集合一致はない: `s2-plan.md:107-127,195-203`。

**失敗シナリオ:** 計画どおりの所有範囲だけを編集する。Codex worker は旧 2 path だけを渡され、hang/freeze 条件の新 leaf を受け取らない。段 8 の自己改善は risk 手順を旧 primary へ戻す。既存 Skill literal test はむしろ旧形のまま通る。

**影響:** alternate entry・自己改善・docs 索引から新 reference が欠落し、参照到達性と将来の配置先が分裂する。

### A-8 — real / medium: gate は呼ばれるが、最終 land 境界からは迂回できる

根拠:

- checker main は guard を呼ぶ: `tools/check_docs.py:3167-3172`
- standard Codex Skill は手動実行を要求する: `.agents/skills/dev-wave/SKILL.md:41-45`
- supervisor は docs-check を exact 1 回要求し実行する: `tools/dev_waves/cli.py:187-194`, `tools/dev_waves/checker.py:643-700`
- ただし Codex Skill は real supervisor を実行面にしない: `.agents/skills/dev-wave/SKILL.md:38-39`
- full pytest は `test_real_repo_clean` 経由で checker を呼ぶが、targeted test は呼ばない: `orchestrator/tests/test_check_docs.py:5259-5266`, `tools/run_tests.py:911-1004`
- land request に test/check receipt はない: `tools/dev_wave_land.py:77-83`
- land helper は spool fold 時だけ checker を呼び、fold=noop なら ff 後そのまま返る: `tools/dev_wave_land.py:1363-1384,1916-1932`
- hooks/CI からの呼出しは見つからない。`.claude/settings.json:8-45` は別用途の PreToolUse hooksだけである。

**失敗シナリオ:** standalone `check_docs` と full suiteを省き、targeted testsだけを「tested」として no-spool waveを land helperへ渡す。新族 closure違反を含む tipでも ff-only land が成立する。

**影響:** local main の受理集合が checker の拒否集合より広くなり、台帳には「landed」だけが残り得る。

これは現 waveへ無断追加せず、裁定パッケージ候補にすべきである。択一は「land は外部 receipt を信頼する非安全境界と明記する」か、「isolated pre-land checkまたは検証 receiptを LandRequestへ束縛する」。

### A-9 — real / medium: `[T-264](a)` の stale 判定は義務を削っている

根拠:

- 元の義務は、実装子 prompt に最初から「テスト実走は親」と書くこと: `docs/archive/worklog-phase3-0801-89.md:48-53`
- 実測理由は workspace-write 子が計算ノード dispatch不能だったこと: `docs/archive/worklog-phase3-0801-100.md:96-99`
- 現在の `DW-O05` は read-only Codex の条件であり、非実走を緑にしない結果規律だけである: `.claude/commands/dev-wave.md:88-89`, `docs/dev-wave/operations.md:31-34`
- brief はこれを「概ね充足」として候補から外す: `s1-brief.md:58-60`

**失敗シナリオ:** workspace-write 実装子へテスト実走を要求する promptを渡す。条件 05 は成立しないため `DW-O05` も渡らず、子は Pegasus dispatchを試して失敗する。親が後で全走しても、この空振り防止義務は回復しない。

**影響:** `[T-264](a)` が台帳上だけ stale 扱いになり、implementation-child reference の予防義務が欠落する。

一方 `[T-328](a)` は `DW-O17` に逐語で存在するため、この側の stale 攻撃は refuted: `docs/dev-wave/operations.md:93-100`。

### A-10 — real / medium: 親 brief の P3 恒久 tool はユーザー裁定と規律 5 を越える

根拠:

- brief は恒久 tool を provisional 採用する: `s1-brief.md:99-101`
- 規律 5 は必要な component だけを段階導入する: `CLAUDE.md:83-86`
- 恒久案は新 tool・test・実行場所契約を増やし、自動 dispatchには D105 supersedeまで必要: `s2-plan.md:402-438`
- 一回限り実測で閉じる案が別にある: `s2-plan.md:440-463`

**失敗シナリオ:** P3を採用して tracked toolを作るが、計算ノード dispatchを scope外に残す。login nodeからは対象 `/tmp` を測れず、恒久 interfaceだけ増えて T-282 の実測は閉じない。

**影響:** 受理集合と保守対象を増やす一方、T-282 は台帳に残り、ユーザーの「測って済ませる」が履行されない。

プランの一回限り実測案を段 4 で確定しない限り、この赤は残る。

物理 closure のうち、次の攻撃はプランどおり実装されれば refuted となる。

- 新 root symlink: `s2-plan.md:172-175`
- 登録 member symlink・親 component symlink: `s2-plan.md:175-178`, `tools/check_docs.py:567-613`
- subdirectory symlink・直下/入れ子の未登録 file・非 Markdown実体: `s2-plan.md:175-177`
- 登録 member 不在: `s2-plan.md:176-178`

空の通常 directory は `rglob` の実体集合から落ちるが、そこに規範 detail は置けないため現時点では nit。

role 名 key の hidden byte pin も、指定された `AGENTS.md`、`tools/check_codex_agents.py`、`tools/dev_waves.py`、`tools/dev_wave_land.py`、hooks からは見つからなかった。`role=author` の hit は provenance判定であり、dev-wave文書のbytes pinではない: `tools/check_ai_provenance.py:407-415,570-587`。ただし brief が `DW-Oxx` を「role 名 key」と呼んでいるのはカテゴリ誤りであり nit。既知の Skill consumer取り残しは A-7 の real である。

DW-G05 の campaign 数値については、certified選択・材料レポート・全試行台帳へ直接書く経路は見つからなかった。現在の直接影響は docs受理集合とland可否であり、この攻撃は refuted。将来の運用失敗という二次効果を、現在のcampaign数値変化と偽ってはならない。

## 総括

最も重い 3 件は次のとおり。

1. **A-1:** 新族は実質的な総量上限引き上げで、通常・docs-only・凍結の全経路で読量が増える。
2. **A-3:** 条件表の発火条件と列所有を検査せず、到達不能な dispatch を受理できる。
3. **A-4:** sibling living docへの間接委譲が明示的既知限界であり、「規範 detail の逃がしを機械拒否する」という命題 2 は成立しない。

現プランは **NO-GO**。ユーザーが「増える経路が 1 つでもあれば敗北」と定義した条件に対し、3 経路すべてが増えている。

段 4 で必ず裁定すべき択一はこれである。

- **択 A:** 「上限を上げない」を維持し、primary + risk の横断 hard ceiling を **25,200 bytes** に置く。分割前置きと A1〜A11 は、D110 同様に非義務重複の削減または候補の削減で全量吸収する。
- **択 B:** 既裁定を正式に開き直し、27,200 を **2,000 bytes の予算引き上げ**としてユーザーへ再裁定を求める。「既存定数名を据え置いたので引き上げではない」という第三の扱いは認めない。

現ユーザー裁定のまま進められるのは択 A だけである。