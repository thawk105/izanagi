判定は **NO-GO**。段 2 plan の `DW-O23` 訂正と raw byte 実測は正しい一方、L1/L2 分類を実 dispatcher の条件性へ束縛できておらず、ユーザー裁定が指した「常時読量」とも一致が証明されていません。以下は静的検査のみで、テスト緑は主張しません。

## Scope 内の重大所見

### A1 — real / blocker: L1 分類が実 dispatch の条件性に束縛されていない

Plan は [`plan.md:37`](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:37) で stage 契約を無条件・条件付きへ手書き分割し、和を既存 `STAGE_DISPATCH_CONTRACT` に戻します。しかし現行 parser は、

- [`tools/check_docs.py:2339`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2339): `stages.setdefault(key, set()).update(pairs)`
- [`tools/check_docs.py:2352`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2352): condition 表でも path/section pair と row count しか保持しない

という実装で、段 dispatch の `成立した条件の` や条件表第 2 列の意味を捨てています。

したがって次が gate 無発火で通ります。

- [`dev-wave.md:66`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:66) の逐語 `成立した条件の ... DW-O01〜...` から `成立した条件の` だけを削る。pair 集合は不変なので既存 stage 照合は通り、実際は全 operations を読むのに L2 のままです。
- [`dev-wave.md:84`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:84) 以下の発火条件を `常に` 等へ変える。`CONDITION_DISPATCH_CONTRACT` は条件文を pin しないため通ります。
- L1 本文を既存 L2 節へ移し、元 L1 節を短い stub にする。到達性検査は「何らかの条件 dispatch に載る」ことしか証明せず、その条件が真に条件付きか、本文が移設可能かを証明しません。

`L1/L2 exact pair` テストでも pair 自体が同じなら検出不能です。段表の条件 marker と条件表第 2 列を exact contract にし、分類 overlap も拒否しない限り、新 gate は実読量 gate ではありません。

### A2 — real / blocker: ユーザー裁定が指した量を P1 がすり替えている

裁定の一次記録は [`worklog archive:896`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/archive/worklog-phase3-0802-106-110.md:896) で、

> docs-only wave の実読 10,515 / 23,990 = 44 パーセント … が「総量は実態の 2 倍以上」を示した

ことを理由に択 (a) を採用しています。ところが brief は [`brief.md:47`](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/brief.md:47) で `常時読量 = DW-C00 の L1` と再定義し、plan は 20,061 bytes を採りました。

`DW-C00` の逐語は [`core.md:8`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/core.md:8) の `L1=段 dispatch の無条件節` ですが、これは「到達した各段内では無条件」という意味です。実装なしなら段 5・6 を飛ばせる [`dev-wave.md:49`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:49) ため、「全 wave が必ず読む集合」と同値ではありません。

結果として、裁定根拠の 10,515 に対し提案 ceiling は 20,200。総量との比も約 2.3 倍から 1.26 倍へ変わります。過去の D110 も [`decisions.md:5149`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/decisions.md:5149) で入口・通常列・全履歴等を別指標としていました。P1 は repo 決定性のある案ではあっても、ユーザー裁定からは導出できません。ここは段 4 で既成事実化せず再裁定が必要です。

### A3 — real: P4/P5 は「予算引上げなし」の実質迂回になりうる

現行コード自身が [`tools/check_docs.py:254`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:254) で、

> 個別 cap は各 reference の「形」を守り

と説明しています。brief の [`brief.md:54`](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/brief.md:54) にある「core/workers/mutation は L1 ceiling に包含」は論理的に誤りです。`core=12,000` でも他ファイルを縮めて L1≤20,200 なら新 gate は通るため、個別 cap は L1 合計に包含されません。

提案値の理論上限は、

`20,200 + 14 × 1,000 = 34,200 bytes`

で、旧 25,200 より 9,000 bytes、35.7% 大きい受理領域です。現行 L2 は 5,137 bytes なので、各節を 1,000 まで膨らませると 8,863 bytes 増やせます。[`plan.md:172`](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:172) はこの 14,000 bytes を認めた直後、[`plan.md:174`](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:174) で `これは予算値の引上げではありません` と断じていますが、受理集合上は明確な拡大です。

また、aggregate だけを撤去して個別 cap を残しても、現行 25,198 から cap 総和 26,750 まで 1,552 bytes の余地が出ます。「operations は 44 bytes だけ」は正しいものの、「実質何も解放しない」は family 全体については refuted です。

### A4 — real as written: allowlist から self doc を落とす

現行 allowlist は [`tools/check_docs.py:393`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:393) の逐語 `{*REFERENCE_LIMITS, *SELF_LIMITS}` です。段 8 は [`dev-wave.md:73`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:73) で `docs/skill-self-improvement.md` を dispatch します。

一方、plan は [`plan.md:124`](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:124) で `allowlistを DEV_WAVE_REFERENCE_FILES から構成` とだけ書いています。文字どおり実装すると self doc が allowlist 外になり、現行 repo 自身が赤になります。`{*DEV_WAVE_REFERENCE_FILES, *SELF_LIMITS}` を明記すべきです。

## 親 brief の独立検算

| 親の主張 | 判定 | 独立検算 |
|---|---|---|
| 4 reference = 25,198 | real | 8,537 + 4,623 + 3,682 + 8,356 |
| 残余 1,063 / 377 / 68 / 44 | real | 各 cap との差と一致 |
| L1=18,938 / L2=6,260 | refuted | `DW-O23` 1,123 bytes の分類漏れ |
| Plan の L1=20,061 / L2=5,137 | real。ただし P1 定義を仮定 | `DW-O23` は段 9 の無条件行 |
| L2 最大 `DW-O09`=935 | real | `DW-O23` は L1 |
| Python consumer は 2 本 | real | `tools/check_docs.py` とその test のみ |
| docs 側に 25,200 の再掲なし | 字義上 refuted | [`decisions.md:6304`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/decisions.md:6304) に D129 の履歴値あり。ただし live pin consumer ではない |
| 計算ノード不要 | refuted | [`brief.md:75`](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/brief.md:75) と、login node の pytest を全面禁止する [`AGENTS.md:31`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/AGENTS.md:31) が衝突。将来の受入は `run_tests.py` dispatch が必要 |

### 全 49 節の raw UTF-8 byte 内訳

数え方は「見出し行・原改行・末尾改行を含み、次の可視 H2 直前まで。全 preamble を L1 に一度加算」です。

| file | preamble | L1 節 `line: ID=bytes` | L2 節 | 計 |
|---|---:|---|---|---:|
| [core.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/core.md:5) | 108 | 5:C00=873; 17:STOP=577; 24:S01=1,620; 42:G01=256; 47:G02=263; 52:G03=256; 57:G04=227; 62:G05=466; 69:S04=1,044; 84:S07=1,253; 99:S08=226; 104:S09=490; 111:CTX=878 | — | 8,537 |
| [workers.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/workers.md:5) | 165 | 5:S02=256; 10:S03=697; 19:S05-A=425; 26:S05-B=313; 32:S05-C=1,056; 45:S06-A=304; 51:S06-B=959; 64:S06-C=448 | — | 4,623 |
| [mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/mutation.md:5) | 109 | 5:M01=536; 12:M02=294; 16:M03=343; 22:M04=407; 29:M05=786; 38:M06=258; 43:M07=209; 48:M08=740 | — | 3,682 |
| [operations.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/operations.md:6) | 263 | 6:O01=673; 14:O02=508; 21:O03=266; 31:O05=209; 74:O13=177; 125:O23=1,123 | 26:O04=200; 36:O06=210; 41:O08=183; 46:O09=935; 59:O10=261; 64:O11=223; 69:O12=195; 78:O14=200; 83:O15=55; 87:O16=367; 93:O17=703; 102:O18=441; 109:O19=675; 118:O20=489 | 8,356 |

集計は L1 節 19,416 + preamble 645 = **20,061**、L2 = **5,137**、L1 35 節 / L2 14 節です。段 dispatch の逐語 [`dev-wave.md:60–75`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:60) に照らし、P1 の形式定義内では `DW-O23` 以外に分類誤りはありません。

### 数え方を変えた場合

| 規則 | L1 | L2 | 20,200 ceiling への影響 |
|---|---:|---:|---|
| Plan の raw 規則 | 20,061 | 5,137 | 139 bytes 余裕 |
| preamble を除外 | 19,416 | 5,137 | 784 bytes 余裕 |
| H2 見出し行を除外、preamble は含む | 18,748 | 4,597 | 1,452 bytes 余裕 |
| 見出し・preamble とも除外 | 18,103 | 4,597 | 2,097 bytes 余裕 |
| 各 file の最終 LF を 1 byte 除外 | 20,057 | 5,137 | 143 bytes 余裕 |
| 各節の末尾 LF を 1 byte除外 | 20,026 | 5,123 | 174 bytes 余裕 |
| 現行内容を LF→CRLF 化 | 20,352 | 5,227 | **152 bytes 超過で赤** |
| 4 file 全てに UTF-8 BOM | 20,073 | 5,137 | 127 bytes 余裕 |

したがって見出し・preamble・原改行を含める定義は結論に効きます。特に意味等価な CRLF 化だけで現行文書が赤になるため、raw byte を採るなら CRLF 拒否またはその受理方針をテストで固定する必要があります。

## 迂回路の判定

| 経路 | 判定 |
|---|---|
| 条件付き行を無条件化、条件文を恒真化 | **real**。A1 のとおり parser が条件性を保持しない |
| L1 本文を既存 L2 へ移す | **real**。本文意味の保存・条件性を検査しない |
| `docs/dev-wave/**` 内へ未登録 file を追加 | refuted。現行閉包の [`check_docs.py:2590`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2590) が余剰実体を拒否 |
| L1 節を同じ L1 内で分割 | refuted。unique raw bytes の合計なので逃げられない |
| L2 節を分割 | 現行 14 節 cap は単純追加を拒否。ただし既存 L2 の統合・再利用で総量を最大 14,000 まで増やせる |
| reference preamble へ移す | refuted。plan どおりなら preamble は L1 加算 |
| `docs/dev-wave/**` 外の living doc へ切り出して leaf から間接委譲 | **real**。[`check_docs.py:2323`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2323) が逐語で「leaf reference 本文から別 living doc への間接委譲は…検査しない」と認めている |
| command / self / Codex Skill へ移す | scope 外ではあるが実読量として real。後述の裁定パッケージ対象 |

## 受理集合の変化

旧 document gate は概略、

`core≤9,600 ∧ workers≤5,000 ∧ mutation≤3,750 ∧ operations≤8,400 ∧ total≤25,200`

です。新案は、

`L1≤20,200 ∧ L2節数≤14 ∧ 各L2節≤1,000`

です。

### 旧赤 → 新緑

- 現行 `DW-O09` +3 bytes: total=25,201、O09=938。旧 aggregate 赤、新案は緑。
- 現行 `DW-O04` +45 bytes: operations=8,401、total=25,243。旧 file+aggregate 赤、新案は緑。
- 現行 mutation の任意 L1 節 +69 bytes: mutation=3,751、L1=20,130。旧 file+aggregate 赤、新案は緑。
- 合成入力で core>9,600 / workers>5,000 / mutation>3,750 / operations>8,400 のどれかを満たしても、他 member を縮めて新三条件を守れば緑。
- L1=20,200、L2 14節×1,000なら total=34,200 まで緑。
- checker 構成について、旧 `cap_sum > 110%` は checker 自身が赤にしましたが、新案には `L1_MAX + count×section_cap` の関係を検査する meta-gate がありません。

### 旧緑 → 新赤

Plan が挙げた L1=20,201、L2単節=1,001、L2 15節に加え、以下が漏れています。

- registry に存在するが stage/condition のどこからも到達しない節。新 `unreachable_l2_pairs` が拒否するが、現行 dev-wave checker には同じ閉包検査がありません。
- fenced fake H2 だけで必須節を満たす入力。現行 raw regex [`check_docs.py:2773`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2773) は受理しうる一方、新 visible scanner は拒否します。
- 逆に、実 H2 + fence/comment 内の同名 fake H2 は旧 checker が重複赤、新案は緑になります。

最後の二つは望ましい parser 修正ですが、受理集合表から脱落しています。

## Fail-closed 性

| 入力 | 静的判定 |
|---|---|
| H2 なし | refuted: 0 bytes 緑にはならない。必須 H2 finding を出して budget 計算を skip |
| 可視 H2 重複 | refuted: count≠1 の構造 finding 後に budget skip |
| fence/comment 内の偽 H2 | 新案は可視 scanner で境界にせず、raw bytes は周辺実節へ算入する設計。ただし fake-only 負例と raw-byte 算入テストが不足 |
| CRLF | 0 にはならず `\r\n` の 2 bytes を数える。ただし現行内容の CRLF 化で ceiling 超過 |
| BOM | `utf-8` 読取では拒否されず、preamble に3 bytes加算。0 にはならないが「BOM を許す」正例が未固定 |
| symlink / FIFO | refuted: [`_safe_read_text():578`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:578) が開かず finding |
| invalid UTF-8 | refuted: [`_safe_read_text():603`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:603) が finding。decoded 不在で budget を飛ばしても全体は赤 |

Plan の構造を忠実に実装する限り、質問に挙がった入力の多くは fail-open ではありません。未固定なのは CRLF/BOM の受理方針と、fake H2 の raw bytes を本当に周辺節へ算入する検出力です。

## テスト置換の検出力

### real な欠落

- 旧 cap-sum の ±境界 [`test_check_docs.py:965`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:965) と [`test_check_docs.py:1279`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:1279) を L2節数テストで代替するのは非同値です。前者は「予算定数同士の構成関係」、後者は「文書中の節数」を検査します。
- 4 file の個別境界テスト [`test_check_docs.py:1385`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:1385) が持つ file-shape 検出力は、L1合計/L2単節テストでは代替されません。
- N22 [`test_check_docs.py:776`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:776) の dev-wave 部分削除により、core・operations・aggregate の adjudicated 値を live finding と結ぶ検出力が消えます。
- A1 の条件 marker 削除、条件文恒真化を拒否するテストがありません。
- fake H2 テストは見出し inventory だけでなく、「fake 部分の bytes を落とす mutant」を殺す境界入力が必要です。
- CRLF、BOM、unconditional/conditional overlap のテストがありません。

### refuted / 条件付きで十分

Plan には L1/L2 の `limit-1 / limit / limit+1`、L2 成長を通す正例、14節 exact 正例があります。新軸の ±1 と正例自体はあります。

ただし `_build_min_repo()` の実値は、現行 fixture 生成規則 [`test_check_docs.py:479`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:479) から計算すると、

- L1 = 1,578 bytes
- L2 = 434 bytes、各節 31 bytes
- L2節数 = 14

です。節数 gate は意味がありますが byte gate は baseline から遠いです。既存 `_pad_to_bytes()` は [`test_check_docs.py:3330`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:3330) のように EOF へ追加し、operations の EOF は L1 の `DW-O23` です。L2 境界には選択節へ raw bytes を挿入する専用 helper と、生成後の L1/L2 実測 assert が不可欠です。

## 変異候補の裁定

`DW-M01` は [`mutation.md:7`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/mutation.md:7) で「手前の同入力拒否なし・赤理由一つ」を要求し、`DW-M03` は診断だけの赤を kill に数えません。

| 候補 | 判定 |
|---|---|
| M1 L1比較無効化 | 成立。ただし L1境界だけでなく `distinguishes_l2_growth_from_l1_growth` も赤になるため、plan の「plus-one testだけ」は refuted。赤理由は同じ L1 gate |
| M2 L2単節比較無効化 | 成立。対象節1,001、他軸正常なら一理由 |
| M3 L2節数比較無効化 | 成立。copied checker の cap=13、現行14節なら count finding 一つ |
| M4 到達性無効化 | 条件付きで成立。新 pair を registry/H2 に同時登録し、copied cap=15 として初めて一理由 |
| **M5 O23 のL1帰属落とし** | **不成立**。O23 が L2へ移ると L2節数が14→15になり count gate が同じ入力を拒否する。acceptance は赤のままで、finding 名だけ変わるため kill に数えられない |
| M6 preamble算入落とし | 成立。ただし L1境界と区別テストの複数 node が同じ一理由で赤になりうるので期待 node を列挙する必要あり |
| M7 fence/comment mask外し | 成立するが「正例を過剰拒否する mutant」の位置付け。duplicate H2 一理由に固定可能 |
| M8 byte→文字数 | 条件付きで成立。fixture が `encoded=1,001` かつ文字数≤1,000 を assert すること。synthetic heading の `—` だけでも差は出るが、暗黙に依存させない |

M5 は名指しで事前登録から外すか、copied checker の count cap を15へ上げて mask を外した専用 fixture に直す必要があります。

## Scope 外の裁定パッケージ候補

これは本 wave へ黙って追加実装すべき内容ではありません。

1. **「常時読量」の全層化**

   - L0 command: 8,907 / cap 9,500
   - self doc: 5,997 / cap 6,000
   - Codex dev-wave Skill: 3,747 / cap 5,500
   - reference L1: 20,061

   Plan は [`plan.md:66`](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:66) で L0/self を対象外と明記しており、隠してはいません。しかし成果物を「実際に効く全層の常時読量 gate」と呼ぶことはできません。択は、(a) 今回は `docs/dev-wave reference L1 gate` と明記する、(b) L0/self/Codex surface を含む複合 gate を別 wave で裁定する、です。

2. **leaf から scope 外 living doc への間接委譲**

   現 checker が明示的に未検査としている経路です。択は、(a) normative indirect delegation を禁止、(b) 閉包 registry へ含めて byte 計測、(c) 意味監査だけに残し gate の既知限界として明記、です。現 wave の二ファイル変更だけで意味を決めてはなりません。

## 総括

- 最重所見1: dispatch parser が条件性を捨てるため、条件 marker 削除・恒真条件化で L1 gate を迂回できる。現 plan は NO-GO。
- 最重所見2: 裁定根拠は docs-only 実読 10,515 だが、plan は別量の L1=20,061 を採用した。ユーザー再裁定なしに同一視できない。
- 最重所見3: 個別 cap 撤去と `20,200 + 14×1,000` は総受理上限を34,200へ広げ、P4 の「包含」と P5 の「引上げでない」は成立しない。