結論は **NO-GO**。必読資料はすべて読めた。`git diff` 上、実コード差分はなく docs-only であることも確認した。以下の成果物影響は、主に D116 を実装根拠として D114 の上限を解除した場合を指す。

静的検査のみであり、pytest・build・`check_docs.py` は実行していない。

## 所見 1 — 1 件の red を atom 全域へ一般化しており、no-good cut ではない

**重大度: BLOCKER**

**根拠:**

- 設計本文は singleton relaxation の 1 候補が red だったことしか証明しないと認める（`README.md:97-107`）。
- それにもかかわらず atom `r` を `C` に追加し、以後すべての候補へ `E=P∨C` を適用する（`README.md:97,118,130-140`、`docs/decisions.md:5482-5484,5500-5503`）。
- 1 個の失敗 mask `p` に対する正確な no-good は `p` だけを除く clause である。`r=true` を全候補へ要求すると、他の 4 bit が異なる `r=false` の mask まで一括して除外する。無拘束時なら 32 点中 16 点を除外する。
- 本文自身が「他 atom との相互作用や因果単調性は証明されていない」（`README.md:105-106,279`）と認めているため、この一般化を支える根拠がない。
- A8 の「因果と名乗らない」は直ったが、B3 の「atom 全域を禁止できない」は直っていない。名称変更を実質修正として扱っている。

**成果物影響:** certify 可能な `r=false` mask が verifier 前に消え、certified best、tie 集合、材料レポートの候補母集団と棄却台帳が変わる。

## 所見 2 — P1〜P10 は「すべて機械検査可能」ではなく、cap-lift とも結線されていない

**重大度: BLOCKER**

**根拠:** `README.md:330-348` と `docs/decisions.md:5517-5523` は全 10 件を機械検査可能な必須条件とするが、実際の検査可能性は次のとおり。

| P | 実際に書けるか | 欠陥 |
|---|---|---|
| P1 | 部分的 | 自由文字列拒否は書ける。しかし「emitter 出力が mask ごとに固定」は emitter を自己参照すれば恒真になる。独立した 32-entry literal golden と mask→意味の外部 oracle が必要 |
| P2 | 定義後なら可能 | 比較対象 payload を実装側が選べば恒真になる。provider 応答、report、journal、call/stop topology、時刻等を含む観測面の閉集合が未定義 |
| P3 | 現状は不可 | authority、外部 anchor、CAS 状態機械、各 crash prefix の正規回復状態が未裁定。ローカル ledger 全削除は外部錨なしには観測不能 |
| P4 | 書けるが恒真化可能 | batch サイズ 1 なら常に満たせる。batch cardinality、全候補の事前 commit、結果を batch seal まで保留する契約がない |
| P5 | 3 要件中 1 件だけ | 検査欄は注入 run の下流拒否だけ。role 間 session 共有と未予約 token の replay/missing を検査しない |
| P6 | 条件文なので恒真 | 「no-good を超える主張をするなら」であり、超えない現在は真または N/A。atom の独立再導出規則も未定義 |
| P7 | 部分的 | proof 無し拒否だけなら全 campaign を拒否する実装でも通る。issuer、proof schema、valid/tamper/replay/wrong-origin の正例・負例、consumer 閉集合がない |
| P8 | 現状は不可 | 「全経路」は集合が閉じておらず、runbook は prose。reflux on/off の hidden constraint 適用意味も未定義 |
| P9 | 定義後なら可能 | direction/magnitude/result の enum、exact type、iteration 整合の意味が未規定。任意の「汚染 fixture」を自己採択できる |
| P10 | 機械検査ではない | ユーザー裁定は人間 gate。署名済み ruling receipt と定数・authority identity の pin を定義して初めて機械照合できる |

特に P6 が条件付きである以上、「10 件すべて必須」「現時点で満たされているものはゼロ」（`README.md:348`、`docs/decisions.md:5523`）は論理的に成立しない。P6 は真または非適用であり、10 個の Boolean predicate 自体がまだ存在しない。

コードには `MAX_APPROVED_GENERATIONS = 1` と `_validate_generation_budget()` しかなく（`p3_autonomous_workload_trial.py:90-92,184-193`）、`reflux-control`、origin proof、P1〜P10 を cap 変更へ束縛する guard は存在しない。`model.WAL_STAGES` にも `reflux-control` はない（`model.py:20-32`）。

**成果物影響:** 将来、定数と既存境界テストだけを変更して多世代を開放でき、origin proof・非干渉・予約台帳なしの `COMMIT` が certified 集合と正式材料へ入る。

## 所見 3 — 軸 (iii) の必須化はユーザー裁定の逸脱であり、技術的にも不足している

**重大度: BLOCKER**

**根拠:**

- ユーザー裁定は「軸 (i) 主軸 + (iv) 併用」「(iii) は (i) の補強として後置可」である（`brief.md:14-18`）。
- 段 4 は「禁止されていないから必須化と両立する」と解釈した（`s4-adjudication.md:49-50`、`docs/decisions.md:5488-5492`）。しかし「後で置いてよい」は「多世代開放の必須 gate に変更してよい」という承認ではない。安全上推奨することはできても、新しい裁定としてユーザーへ返すべきだった。
- 必須化の根拠も自己矛盾する。D116 は raw/effective 差が membership を示すとする一方（`docs/decisions.md:5489-5491`）、直後に effective mask を generator へ開示しないとする（`:5494-5496`）。二値 accept/reject だけでは、未拘束 mask が偶然通った場合と constraint により閉包された場合を一意に区別できない。
- P4 の検査は「結果取得後の batch 変更拒否」だけ（`README.md:340`）。同文書の不採用案 C には本来必要な「immutable freeze」「batch seal まで結果非公開」が書かれている（`:292`）のに、必須条件へ移されていない。batch=1 の逐次実行で適応 oracle はそのまま残る。

**成果物影響:** 未承認の条件が cap-lift の受理条件になる一方、batch=1 実装なら条件を満たした体裁で適応探索が通り、origin ごとの候補列・certified 選択・予約台帳が変わる。

## 所見 4 — §2 の「現行実測」は候補空間と whiteboard alphabet を事実以上に閉じている

**重大度: BLOCKER**

**根拠:** コード照合結果は以下。

| 主張 | 判定 | コード根拠 |
|---|---|---|
| recipient matrix | 概ね正しい | planner `:816-825`、coder `:843-860`、auditor `:897-905`、critic `:957-967` |
| `current_metrics` が次世代へ流れる | 正しい | 初期化 `:795-802`、更新 `:953`、planner/coder への送信 `:818-824,858` |
| `prior_reverse` が制御へ効く | 正しい | `p3_s4_loop.py:673-683` |
| whiteboard `result` は 3 状態、最大 `log2(3)` | **機械契約として偽** | `project_whiteboard(..., result: str)` は任意文字列を受ける（`p3_s4_loop.py:258-270`）。`state_from_dict()` も result/direction/magnitude の enum・exact type・iteration 整合を検査しない（`:371-404`） |
| `delta_pct≡None` | 正しい | 射影 `:273-286`、load `:394-398` |
| syntax gate は禁止識別子 blacklist | 正しい | `check_syntax_contract(implementation: str) -> List[str]`（`p3_s4_loop_trigger_gating.py:105-115`） |
| 現行の意味ある候補空間は 32 点 | **偽** | `GATEABLE_REASONS` はコメント上も「偵察の列挙空間」（`axis_trigger_gating.py:45-51`）。production coder parser は任意の非空物理 1 行 C++ を受理する（`p3_autonomous_workload_trial.py:261-284`） |
| `kUnset` は常に true | **prompt/comment 契約のみ** | `axis_trigger_gating.py:53-56`。blacklist はこの意味を強制しない |
| `GATEABLE_REASONS` の中身 | 正しい | `lock-conflict`, `update-absent`, `readvali-tid`, `readvali-locked`, `node-vali`（`:50-51`） |
| campaign preimage | 正しい | `canonical_preimage(cfg: CampaignConfig) -> str` は spec/commit/tag/config/trial を含む（`ident.py:76-91`） |
| WAL 呼出形・last-wins | 正しい | `wal.log(...)->WalRecord`（`wal.py:499-506`）、`records_by_stage()` last-wins（`:586-601`） |

算術自体は `2^5=32`、`log2(3)=1.585`、`log2(5)=2.322`、`log2(6)=2.585`、`log2(9)=3.170`、`1+5+10=16=4 bit` で正しい。しかし「現在の受理 alphabet がその有限集合に閉じる」という前提が偽である。自由 C++→固定 5-bit は正準化ではなく、明白な受理集合変更である。

**成果物影響:** 現行 parser が受理できる 32 点外の候補と任意 result 値が bit 会計から消え、移行時の certified 候補集合、whiteboard、disclosure 値、材料レポートの母集団が誤る。

## 所見 5 — 「固定・解いた・supersede」が未実装／未裁定という本文と衝突する

**重大度: BLOCKER**

**根拠:**

- 制限文自体は存在する。`README.md:8-13` と `docs/decisions.md:5512-5515` は draft、未裁定 5 件、実装ゼロ、cap=1 を明記する。
- しかし D106 追記は同じ段落で「設計択一は D116 が解いた」と「未裁定の択一が 5 件」を併記する（`docs/decisions.md:4876-4880`）。
- D114、phase、runbook も「設計択一／設計軸と前提条件を確定」とする（`docs/decisions.md:5317-5319,5375-5378`、`docs/phase3.md:471-476`、runbook `:100-115,175-176`）。予算、authority、cap binding、formal consumer、診断 run が未裁定なら、確定したのはユーザー承認済みの (i)+(iv) までである。
- D116 見出しの「前提条件 10 件を機械検査可能な形で固定」（`docs/decisions.md:5475`）は所見 2 により偽。
- §8 択一 1 は「(iii) を必須化してから値を再導出するか」と問うが、§3.6/D116 は既に必須化済み（`README.md:166-173,354`）。P7 は必須条件なのに formal consumer gate を入れるか未裁定（`:343,357`）。診断 run は規則として断定済みなのに未裁定（`:225-226,358`）。
- `README.md:364` と D116 `:5526` の「cross-generation 還流は 3 入口で機械拒否」も射程過大。三入口が拒否するのは `generations > 1` という引数であり、注入 `drive` が callable 内で反復する経路や driver 直接反復は D114 自身が保証外としている（`docs/decisions.md:5379-5383`、`p3_autonomous_workload_trial.py:1002-1004,932-949`）。

D116 `:5536-5537` の「現時点の production 挙動・受理集合は不変」は docs-only の現在地については正しい。問題は、権威文書が未解決設計を将来の cap-lift 前提として「解いた」と状態遷移させる点である。

**成果物影響:** 後続実装者が D116 を完成済み仕様として扱い、未裁定の authority・consumer gate・cap binding を省略したまま多世代成果物を正式受理する。

## 所見 6 — ablation は supersede されておらず、on/off の意味も未定義

**重大度: MAJOR**

**根拠:**

- `docs/phase3-main-experiment.md:48-50` は「8c 自律ループでは D116 がこの還流形を supersede する」と書く。
- 実コードでは `make_critic_digest(reflux=)` が現在も on/off を実装し（`p3_s4_loop.py:236-253`）、trigger driver もそれを消費する。hidden constraint 機構は存在しない。
- P8 は「reflux on/off ablation が壊れない」としか書かず（`README.md:344`）、hidden constraint を off armでも適用するかを定義しない。
- 常時適用なら off armが constraint で汚染される。offで無効なら on/offで候補受理集合・origin state・query budgetが別物になる。どちらも単なる regression 検査では決まらない。

**成果物影響:** arm label と実際の操作が一致せず、on/off の certified 集合、効果量、材料レポートの比較参照が無効になる。

## 所見 7 — `reflux-origin` preimage が D116 と設計本文で異なる

**重大度: MAJOR**

**根拠:**

- 設計本文は role bundle、recipient projection schema、stock certification、structural-zero evidence、records/threadsまで origin に含める（`README.md:159-164`）。
- 権威 decision の D116 は series ID、spec、commit、axis、descriptor SHA、verifier/environment、IR/emitter、budgetだけを列挙する（`docs/decisions.md:5505-5510`）。
- `role bundle / recipient projection schema` は P2 の非干渉意味を変え、structural-zero evidence は 5-bit universe の正当性を変える。省略可能な補助 metadata ではない。

**成果物影響:** どちらを正本に実装するかで同一 origin と判定される run が変わり、異なる role projection・要因 universe の query counter、constraint、WAL refs が混載される。

## 所見 8 — 段 4 の「17 件すべて反映」は算術から誤りで、B8 が落ちている

**重大度: MAJOR**

**根拠:**

- レンズ A は BLOCKER 5 + MAJOR 4、レンズ B は BLOCKER 6 + MAJOR 3。合計は **BLOCKER 11 + MAJOR 7 = 18 件**。
- 段 4 は「BLOCKER 11、MAJOR 6」「所見 17 件」と記す（`s4-adjudication.md:5-6,55`）。重複排除の対応台帳はない。
- `README.md:317-328` の反映表には B8「実シグネチャと実装地図が不足」が存在しない。
- B8 の懸念は現存する。`layer3_report.py` は独自の固定 `STAGES` を持ち（`:38-40`）、未知 stage を拒否する（`:99-100`）。`model.WAL_STAGES` に将来 `reflux-control` を足すだけでは formal material report が壊れる。

各所見を個別に追うと次の判定になる。

| 所見 | 判定 | 理由 |
|---|---|---|
| A1 | partial | auditor から effective diff/SHAを外す設計は入ったが、P2 の観測面が閉じていない |
| A2 | partial | session共有をP5へ書いたが、検査は注入 run だけ |
| A3 | partial | (iii) を追加したが、singleton batch と結果早期公開を防がない |
| A4 | partial | 回復経路と上位 origin は書いたが authority・重複発行・rollback は未決 |
| A5 | closed | `current_metrics`、理由条件付き bit、blacklist の三点は本文で訂正された |
| A6 | regressed | 検査不在から、恒真化可能なリストを「全件機械検査可能」と呼ぶ状態へ悪化 |
| A7 | closed | 構文集合・固定 origin 内だけという射程を明記 |
| A8 | closed | 因果帰属／failure reason を名乗らない限定は明記 |
| A9 | partial | 原子性・crash 問題を未解決として記載しただけ |
| B1 | partial | auditor面は狭めたが shared provider/session と同一UID面が未閉包 |
| B2 | partial | origin単位を導入したが、authority・cell重複発行・予算値が未決 |
| B3 | regressed | 名称だけ no-good に変え、atom全域の過剰拒否は維持 |
| B4 | partial | P7に置いただけで proof schema・consumer集合・実装判断が未決 |
| B5 | partial | P3と未解決節に移しただけで状態機械はない |
| B6 | partial | draft/cap=1は維持したが「設計択一を解いた」とし、cap guardも未結線 |
| B7 | partial | 多くの実測を訂正したが、候補32点・whiteboard値域・runbook metricsがなお誤り |
| B8 | regressed | §6から完全に脱落し、`layer3_report.py` 等の実装地図も補われていない |
| B9 | regressed | P8の一行だけでon/off意味を定義せず、main-experimentには偽の supersede を追加 |

したがって反映状況は **closed 3 / partial 11 / regressed 4** であり、「17件を折り込んだ」は成立しない。特に A6、B4、B9 は表に参照を書いただけで本文契約が閉じていない。

**成果物影響:** `layer3_report.py` など未列挙 consumer が `reflux-control` を拒否または origin proof なしで受理し、材料レポートの stage 集合・source refs・正式受理集合が実装者ごとに変わる。

## 所見 9 — runbook が同じ現行挙動について設計本文・コードと異なる説明をする

**重大度: MAJOR**

**根拠:**

- runbook は「次世代 planner/coder が受けるのは abstract whiteboard まで」とする（`docs/phase3-s8c-autonomous-trial-runbook.md:168-170`）が、実際には前結果から更新した `current_metrics` も planner/coderへ渡る（`p3_autonomous_workload_trial.py:796-825,843-860,951-953`）。設計本文はこれを第 2 チャネルとして正しく書く（`README.md:61-64`）。
- runbook は `--run-root` を変えても同一 campaign state と断定する（`:148-153`）。これは build 側には当てはまるが、no-build は `run_root/campaigns/<id>` を使うため別 run-rootで新品になる（`p3_autonomous_workload_trial.py:779-783`、`README.md:151-154`）。
- critic bool は planner/coder payloadへ渡るのではなく driver の停止カウンタへ畳まれる。runbook の表現では recipient と制御面が混同される。

**成果物影響:** runbook 利用者が run-root 変更で state/budget を意図せず再生成し、metrics 適応を disclosure 台帳へ計上しないため、proposal provenanceと正式 report の探索量が実態からずれる。

## 総括

**(a) 判定: NO-GO**

**(b) BLOCKER: 5 件**

1. 1件の失敗 maskから atom全域を除外しており、certified候補を根拠なく消す。
2. P1〜P10は機械 predicateとして閉じず、cap-lift guardにも結線されていない。
3. 軸(iii)の必須化はユーザー裁定を越え、しかもbatch=1で恒真化できる。
4. 現行候補空間32点・whiteboard 3状態という事実認定がコードに反する。
5. 「設計択一を解いた／前提条件を確定」が、未裁定5件・実装ゼロ・保証外経路と矛盾する。

**(c) 最小の修正**

1. D116と各docsの「解いた・確定・supersede」を「draftで提案中」に戻し、D114の上限1を維持する。
2. atom-wide必須化をやめ、失敗した正確なmaskだけを除くno-good clauseにする。全域禁止を望むなら相互作用を含む独立な単調性証明を要求する。
3. 軸(iii)の必須化を新しいユーザー裁定へ戻し、採る場合はbatch cardinality、全候補事前commit、batch sealまでの結果非公開をP4へ入れる。
4. 予算値・authority・formal consumer・診断runを裁定後、P1〜P10を独立golden、正負proof、crash-state oracleへ書き直し、cap変更をその検査へ機械束縛する。
5. §2、runbook、main-experiment、origin preimageをコード事実に合わせ、B8を含む全18件の1対1台帳と `layer3_report.py` を含むconsumer実装地図を作る。