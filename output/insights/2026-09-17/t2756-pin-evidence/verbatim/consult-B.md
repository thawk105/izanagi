## 総括

- **must-fix 6件、nit 2件**。静的検査のみ。書込み・pytest・checker実走なし。
- 134件を照合し、欠落・重複なし。主分類は A12 / B12 / C31 / D1 / E35 / F31 / G12。
- **確定的な分類ラベルの誤りは0件**。ただし分類後の帰結に補足が必要。
- 閉包外の補助表へ追加すべきファイルは**最低13件**。一部はplanが既に存在を指摘している。
- P4は「過去判定の保持」に賛成、「A〜C・Fだけ」に反対。D・Gと再実測義務が抜ける。
- P5は参照追加に賛成。文面を修正し、spoolの見送り追記を使う。
- decisions fragmentは不要。較正の流用許可など新判断は、本waveで確定しない。

## 1. 閉包の完全性

### M1：134件は文字列検索の集合であり、再承認材料の依存閉包ではない

**所見:** planはこの限界を認識しているが、本文・提示文にはなお「pin束縛134 file」が残る。除外資料と間接consumerを別表で具体化しないと、134件を全影響範囲と誤読できる。
**根拠:** `parent-brief.md` scope 3、`s2-plan.md` §3・骨格13行対応、D2114理由節。
**区分:** 整合・実効性。**must-fix。**
**推奨是正:** 元TSVは不変で保存し、次の**最低13ファイル**を「文字列集合外の判断根拠・間接依存」として別表に加える。

| ファイル | 必要な理由 |
|---|---|
| `docs/decisions.md` | D1936項1のpin固定、D2083の用途限定、D2114の再承認範囲を逐語で確認する正本 |
| `output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json` | 過去系列のpin付き証拠 |
| `output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json` | 骨格が名指した凍結証拠 |
| `output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json` | 同種の別系列証拠 |
| `output/insights/2026-09-07_t2364-paper-story-a2-certification/artifact-manifest.json` | `raw-manifest.json`等をSHA-256で束縛 |
| 同ディレクトリの `completion-receipt.json` | raw manifestのpath/hashと取得完了を束縛 |
| `orchestrator/campaign/ident.py` | `identity_preimage`不一致を拒否する機構 |
| `orchestrator/campaign/source_digest.py` | source evidenceのcommit束縛 |
| `orchestrator/campaign/paper_story_a2_certification.py` | evidence・identity・pinの照合 |
| `orchestrator/campaign/env_contract.py` | 較正のpath/hashと契約世代の束縛 |
| `orchestrator/campaign/calibration_verify.py` | 較正bytesのhash・schema・契約値の検査 |
| `orchestrator/campaign/s8b_floor_campaign.py` | pinを含む凍結protocolの解決・生成 |
| `orchestrator/tests/test_s8b_approved.py` | `:38`で実gitlinkを読み、`:59`以降で承認定数との一致を検査 |

これは完全な追加閉包の確定件数ではなく、**今回確認した最低数**である。gitlink `external/ccbench` 自体は通常ファイル数と別に1 entryとして記載する。

指定された別表現の探索結果：

- **`v1.1.0-126`：見つからない。** tracked filesへの`git grep`で該当なし。
- **tree OID：見つかった。** 旧pinのtreeは `d230aac7969f8091078ee0fe93d20fea99e196e2`。このliteralは既存#118の`receipt.json`にあり、今回の探索では追加ファイルなし。
- **campaign.lockのidentity_preimage：見つかった。** #49〜51に既存。生成済みcampaign全体の列挙にはならない。
- **SHA-256による間接束縛：見つかった。** 上表のartifact manifest。
- **gitlinkを読むtest：見つかった。** 上表の`test_s8b_approved.py`。134件外。

Eへ落とすべき単なる言及は、planで既に概ね処理されている。#47の時間台帳、#91等のcheckoutログ、#122〜125の既知違反説明はEでよい。一方、古い取得証拠であるという理由だけでCをEへ落とすと、hash束縛の役割を失う。

### M2：骨格の「full SHA」が実物と一致しない

**所見:** 指名された凍結raw manifestの`current_pin`は**7桁の`511c953`**であり、full SHAではない。
**根拠:** `output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json:1`、`insight-cross-protocol-s4-s6.md` §5。
**区分:** 正しさ境界。**must-fix。**
**推奨是正:** 「短縮pin＋manifest内のファイルhashによる束縛」と記す。短縮値からfull OIDを補完せず、完全長の対応は別のgitlink/source evidenceで示す。D2114の趣旨は維持できるが、波及表の各fieldの型までfull SHAへ一括化しない。

## 2. 分類の正しさ（全数）

134行のpath対応とpin出現箇所を照合した。**主分類の訂正は不要**。特に指定箇所の判定は以下のとおり。

| 対象 | 判定・根拠 |
|---|---|
| #32 `buildcache.py:1059` | **E維持**。pinは観測条件を記すdocstringであり、pin不一致を拒否するGではない。ただし`:1062`の「更新時は生成物の形を再実測」は独立した移行作業として残す |
| #33 `p3_s4_loop.py:112` | **A維持**。D1936による独立full OID。`CURRENT_PIN`への自動追随ではない |
| #45 `silo_ladder_rung1.py` | **A維持**。専用driverの固定値 |
| #46 `silo_ladder_rung1_contract.py:543` | **G維持**。ledgerの`base_commit`を照合 |
| #121 `patches/ledger.json:10` | **B維持**。旧基底とability-probe限定を登録する契約 |
| #126 `mocc_trace_v1_policy.json:20–21` | **B維持**。旧→候補の比較端点であり、現行pinの別名ではない |
| #110〜115 `registered/*.json` | **C維持**。acquisitionを含む取得証拠。登録済みという語だけではBにならない |
| #122〜125 `known_violations/*.json` | **E維持**。pinは過去commitの説明。新pinの承認・拒否条件ではない |
| #47 `acceptance_duration_ledger.json:10208` | **E維持**。旧pinを含むtest nodeidの時間記録 |
| #12〜16 figure provenance | **E維持**。過去図の条件・入力同一性。新図を作る場合は別成果物 |

### N1：patchの適用性と登録上の適格性を明記する

**所見:** #45・46・120・121の帰結は正しいが、「新基底の適用性確認」だけでは、patchが当たれば利用可能と読める。
**根拠:** `patches/ledger.json:10–18`、`silo_ladder_rung1_contract.py:543`、親briefの候補差分1ファイル。
**区分:** 整合・実効性。**nit。**
**推奨是正:** 「候補差分はMOCCのみなのでSilo patchの機械的適用が維持される可能性はあるが、未実測。適用成功とbase_commit契約の充足は別。新基底へ移すなら新登録と専用consumerの整合確認が必要」と補う。

### N2：mocc policyはpin前進だけではbase==newにならない

**所見:** base==newになるのは、旧baseを新pinへ機械置換した場合である。policyを保持すれば旧→候補の比較は保持される。
**根拠:** `tools/pegasus/mocc_trace_v1_policy.json:20–21`。
**区分:** 整合・実効性。**nit。**
**推奨是正:** #126に「旧比較を保持。新しい比較命題には別policy。baseの追随置換で比較を自己比較へ変えない」を追記する。planのB分類と非追随方針には賛成する。

## 3. 規律7の適用

### M3：P4の結論はD・GとE内の再実測義務を落としている

**所見:** 過去のcertified判定を保持する点は正しい。しかし「新系列だけがA〜C・Fの更新を要する」は必要作業の列挙として不正確。
**根拠:** `CLAUDE.md`規律7、D2114理由節の「登録・identity・凍結の更新」、`s8b_floor_campaign.py:834,1067,1296`、`buildcache.py:1062`。
**区分:** 正しさ境界。**must-fix。**
**推奨是正:** P4を次へ置換する。

> pin前進だけを理由に旧pin・旧identityで得た測定事実と当時の判定を無効化しない。新pinで継続する系列は、登録・identity・凍結・consumer・対応するテストの契約を整合させ、明示された再実測を行う。旧証拠の保持は、新pinへの保証の移転を意味しない。

規律7は逐語で「**事前登録の充足・凍結・環境契約・較正・correctness gate**」を残している。D297合格を理由にこれらを省略する帰結は、規律2とも整合しない。

### M4：較正・floorを「保持」だけで閉じない

**所見:** planは「較正が全部無効とは結論できない」と正しく留保するが、新pinに対して何が未決なのかが不足する。
**根拠:** `env_contract.py:454–485`、`calibration_verify.py`の`load_verified_calibration`、D2083項1〜3・6、規律7。
**区分:** 正しさ境界。**must-fix。**
**推奨是正:** 次の境界表を追加する。

| 層 | 判定 | 根拠・限界 |
|---|---|---|
| 既存較正record | **保持** | acquisitionの旧headを含むbytesを保持。pin前進だけでは取得事実を取り消さない |
| 環境契約の較正参照 | **保持／変更時は新登録** | path/hash、schema、env_tag、clock等を束縛。現行CCBench pinとの直接一致検査ではない |
| 新pinで取得した較正値という主張 | **再取得＋必要な新登録** | 旧recordのheadだけを張り替えて作れない |
| 新pin系列で旧較正を利用できるか | **ユーザー裁定へ返す候補** | hash検査通過だけでは適用範囲の拡張を証明しない。一方、pin差だけで一律再取得も導けない |
| 既存凍結floor protocol | **保持** | 旧pinを含む凍結bytes・pathを変更しない |
| 新pin系列のfloor protocol | **新登録／新しい版の凍結** | 解決キーにpinを含む。旧protocolを新pinの契約として流用しない。protocol生成と床値の実測は別 |
| D2083のwithin-run floor登録 | **保持** | 指定4対の既取得recordに限る文書上の用途限定登録 |
| 新pinでのwithin-run floor観測を追加する場合 | **再取得＋新登録** | 旧4対の値を新pinでの観測に読み替えない |
| 過去記録の誤りが判明した場合 | **erratum** | pin差だけではerratum不要。訂正は追記で行う |

裁定候補の文面：

> 新pinで開始する各系列について、旧較正recordを既存の適用範囲内で利用するか、新pinで再取得して登録するかを、対象protocol・workload・用途を名指しして裁定する。D297合格のみを流用根拠とせず、旧recordとD2083の用途限定登録は保持する。

D2083は`registered/`をreportが自動走査しないことも明記する。6件のrecordを列挙しただけで「環境契約へ登録済み」「reportに利用可能」としてはならない。

## 4. 見送り台帳への提示形（P5）

### M5：追記文から無限定の134件と可変状態の断定を除く

**所見:** 親案の「再承認は未提示」は同日の他waveによる提示後に古くなる。plan案の「pin束縛134 file」は検索集合を依存閉包へ格上げする。
**根拠:** `parent-brief.md` P5、`s2-plan.md` §4、`phase3-T167-row.md`、`docs/spool/worklog/README.md:71–79`。
**区分:** 整合・実効性。**must-fix。**
**推奨是正:** spoolの`### 見送り追記`に次の1物理行を置く。

> - [T-167] 【2026-09-17 追記: [T-2756] の候補 commit・直接区間検査の結果と保証限界・pin 更新の波及資料を `output/insights/2026-09-17/t2756-pin-evidence/README.md` に記録。本追記は判断材料の参照追加である】

静的確認結果：

- 承認・前進可能・合格を理由にした許可を含まない。`状態:`も含まない。
- 現pin literalを含まず、`check_docs.py:6781`付近のliving docs検査に抵触する要素はない。
- `phase3.md`は確認したbyte予算表の対象ではない。command等のbyte上限と混同しない。
- `状態:`検出はhandoff向けであり、この追記を状態遷移として検査するものではない。
- t2757／t2760が実際に同じ行を変更中とは未確認。ただしspoolなら既存本文を上書きせず直列追記できる。意味の重複・矛盾はfoldだけでは解消しないため、land時に最新行を読む。

**insightだけに書く代案の得失（2文）:** insightだけなら同じ台帳行への並行変更を避けられる。反面、親briefの完了条件である「見送り台帳からの参照」を満たさないため、現scopeではspool追記を選ぶ。

## 5. 成果物の骨格

**所見:** planの節順は妥当。非判断事項を冒頭に置き、材料1→2→3、残る論点、証拠索引へ進む構成は判断材料として読める。
**根拠:** `s2-plan.md` §4。
**区分:** 整合・実効性。**指摘なし。**
**推奨是正:** 材料3は「新pin系列で必要な作業の短い一覧→層別表→134行の詳細→集合外の依存」の順にする。134行を最初に読ませない。

verbatim一覧には、既存案に加えて次を含める。

- 閉包取得の正確なargv・除外pathspec・集計方法・日時・HEAD。
- M1の追加依存一覧と根拠。
- 親brief自体と、今回採用した訂正の記録。
- D1936項1、D2083、D2114等の必要な逐語抜粋。出典と取得時点を付す。

**decisions fragmentは不要。** 分類・観測・既裁定の適用範囲を資料化する範囲だからである。旧較正の新用途への流用やD986残余の受容を新たに決める場合は、この結論の対象外であり、資料整備に紛れ込ませない。

## 6. 親の実測値の一般化

### M6：134／79の再現条件が成果物として固定されていない

**所見:** TSVは134行、`full40 > 0`は79行で再計数できた。ただしplanは閉包取得条件を置くと宣言するだけで、正確な除外式・4形の数え方を固定していない。
**根拠:** `pin-closure.tsv`、`s2-plan.md` §4、親brief「模擬／実の差」。照会したHEADは`38353207f719acb0871cfe3d9bbe3a02490282bb`。
**区分:** 整合・実効性。**must-fix。**
**推奨是正:** 次の条件を数値と同じ場所に記す。

> 2026-09-17、superproject HEAD `38353207f719acb0871cfe3d9bbe3a02490282bb`を基準として取得した、指定除外範囲外のtracked working-treeファイルに対する文字列検索集合は134件。そのうち完全40桁値を含むファイルは79件。これは依存閉包や更新対象件数ではない。

加えて、以下を保存する。

- 台帳3本・archive・spool・insightsの**実際の除外pathspec**。
- HEAD対象検索かworking-tree検索か。後者なら未commit差分の有無。
- full40／describe／hex8／hex7の包含重複をどう処理したか。
- 検索・集計スクリプトの逐語。特にtest中の9桁・10桁の異常値も`git grep 511c953`には当たるため、「4形だけを検索した134件」と単純化しない。
- main進行後は旧TSVを上書きせず、必要なら別時点の集合として再取得する。

## 訂正版の分類表（差分だけ）

**該当なし。** 134ファイルの主分類A〜Gは維持する。訂正対象は、閉包外の補助表、束縛表現の精度、分類から導く移行作業と裁定境界である。
