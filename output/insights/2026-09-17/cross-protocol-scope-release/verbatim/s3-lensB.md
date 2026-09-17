## 総括

- 所見 **10件：real 7件／refuted 3件**。静的検査のみ。書込み・pytest・受入実走なし。
- **P2は(b)**：新pinで継続する系列には登録・凍結・identityの更新が必要。**(c)ではない**。旧pinで取得した certified 判定は保持する。
- D297合格だけでは、SHA束縛を内容ハッシュへ置換できない。
- 準備Tは **5本ともgitlink前進なしで完了可能**。ただしTicToc hookは編集面の認可が別途必要で、無条件に着手できる5本ではない。
- mocc hook branchはローカルremote-tracking refに実在し、D1373の3証拠も確認できた。測定成功は未証明。
- **docs-onlyは可**。ただし、解除を「確定済みユーザー裁定」とするのは過剰。裁定案と準備成果物を具体化するwaveとする。
- D1603材料(1)(3)の候補・波及表は本waveに含める。TicTocのBASELINES追加を同梱する必要はない。

## 1. P2 — pin前進は主経路を実際に壊すか

### 所見1【real】SHAそのものへの束縛があり、D297合格では解除されない

**所見 →** 新pinへ移したcheckoutでは、旧登録に従うA-1実行・consumerや既存campaignの再開が拒否されうる。単に「siloの前処理出力が同一」と説明して通せる実装ではない。

**根拠 →** `rg`と現物読取で確認した主な束縛は以下。

| 層 | file:line | 束縛・影響 |
|---|---|---|
| gitlink／現行定数 | `external/ccbench` のHEAD gitlink、`orchestrator/campaign/pin.py:28` | full SHA=`511c9538e4e8efa54b45cda62e72389ed3b706ec`、定数は短縮形 |
| 承認済み定数 | `orchestrator/campaign/s8b_approved.py:67` | `CCBENCH_FULL_SHA`へfull SHAを固定 |
| A-1登録 | `orchestrator/campaign/paper_story_a1_paired.v3-sized.json:17`、`paper_story_a1_paired.v3-pilot.json:17` | `canonical_pin`へfull SHA |
| A-1 source契約 | `orchestrator/campaign/paper_story_a1_source.v2.json:4` | `canonical_head`へfull SHA |
| A-1実行・consumer | `orchestrator/campaign/paper_story_a1_paired.py:2390`、`:2400`、`:2409` | policyの固定OIDと、実checkoutのHEADを比較。`artifact-consumer`も対象 |
| A-2 | `orchestrator/campaign/paper_story_a2_certification.py:1352`、`:3310`、`:3693` | evidence、campaign identity、`pin.CURRENT_PIN`を照合 |
| campaign identity | `orchestrator/campaign/ident.py:214`、`:379` | `ccbench_commit`をpreimageに含め、保存preimageとの不一致を拒否 |
| lockの実例 | `orchestrator/tests/fixtures/b10_backoff_shape_locks/balanced.campaign.lock:1` | `identity_preimage`内に`"ccbench_commit":"511c953"`。これはfixtureとして確認 |
| 凍結floor | `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json:1` | `ccbench_pin`にfull SHA |
| 凍結evidence manifest | `output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json:1` | `current_pin`、lock・WAL等のhashを保持 |
| 性能事前登録 | `docs/backoff-policy-performance-preregistration.md:129`、`docs/backoff-counterfactual-preregistration.md:140`、`docs/dynamic-backoff-preregistration.md:82` | full SHA＋patch stack |

一方、次は同一視できない。

- `docs/phase3-main-experiment.md`には当該SHAの直接固定は見つからない。ただし`:335`でfreezeに`CCBENCH_COMMIT`を含め、起動時照合を要求する。
- `orchestrator/preregistration/`には当該SHA literalは見つからない。登録blobを扱う機構と、個々の実験のSHA固定を分ける。
- `orchestrator/campaign/env_contract.py:251`、`:261`は較正recordのpath/hashを固定する。**CCBench SHAの直接固定ではない**。新pinだから全環境契約を必ず更新する、とは導けない。
- H1/H2関連driverは`orchestrator/campaign/p3_autonomous_workload_trial.py:828`等でbaseのcommitを継承する。H1/H2事前登録をA-1と同じfull SHA literal固定と断定する証拠はない。

**影響 →** 新旧系列を同じlockでresumeする案や、A-1登録を据え置いてcheckoutだけ進める案は成立しない。A-1には再解析時のcheckout制約も残る。

**是正案 →** **(b)を系列別に適用**する。「新pin採用時にA-1の新登録／追補・新identity・必要な再凍結を行う。旧系列は旧checkoutで保持する」と記す。D297は限定macro contextの観測者効果検査であり、identity schema変更の承認ではない（`docs/decisions.md:13747`）。

### 所見2【refuted】「pin前進により過去のcertified判定が遡及失効する」は支持されない

**所見 →** 過去の判定の有効性と、現在checkoutでそのconsumerを動かせることは別である。

**根拠 →** `orchestrator/campaign/pin.py:11`は歴史的driverのliteral pin保持を要求し、`:16`は一律張替えを禁じる。`ident.py:379`の拒否は異なるconfigでの再開拒否であり、過去判定の取消しではない。

**影響 →** 「主経路が壊れる」を遡及無効化と解釈すると、規律7に反して再測定範囲を膨らませる。

**是正案 →** 結論は「**旧成果物は保持。新pinへの実行移行には費用がある**」。内容同一性は移行判断の材料に使い、旧evidenceのSHAを書き換える根拠にしない。

## 2. D1373関門の位置

### 所見3【refuted】moccにもBASELINES変更が必要、という見方は誤り

**所見 →** moccは適切なhook commitへのpin前進で、当該text-level関門を通る構造である。TicTocにはbaseline追加とhook移植の両方が要る。

**根拠 →**

- `between_run_floor.py:60`の鍵は`silo`と`mocc`。TicTocは`:285`で引数拒否。
- `:125`でCMakeのSOURCESを読み、`:131`以降で**同一file**のinclude・TRACE guard・hook呼出しを照合。`:304`がbuild前の関門。
- ローカルに`refs/remotes/origin/izanagi-t1943-mocc-g2-readfrom-witness`が存在し、OIDは`e9e477ca1b55348ab4530de0b1cf663ce4555290`。
- 同OIDの`cc/mocc/CMakeLists.txt:2`は`transaction.cc`をSOURCESに列挙。同`transaction.cc:13`に`#if TRACE`、`:15`に`trace.hh` include、`:1135`に`izanagi_trace::next_txid()`がある。
- 同OID→現pinのancestor検査はrc=1。現pinとのdiffは`cc/mocc/transaction.cc`のみ、141行追加だった。

**影響 →** mocc開通に不要なdriver汎用化を追加すると費用を増やす。一方、TicTocをBASELINESへ足すだけでは測定は開通しない。

**是正案 →** moccは候補固定・D1603材料・再承認へ進む。TicTocはhookとbaselineの二条件を維持する。**branchのネットワーク到達性、D297合格、verifier通過、測定成功は今回確認していない**。関門は変更しない。

## 3. pin非依存の準備T鎖の実効性

### 所見4【refuted】D297材料(2)に両commitの実バイナリbuildは必須ではない

**所見 →** 「両方をbuildするので必ず計算ノード」という前提は誤り。

**根拠 →** `tools/check_trace0_preprocess_identity.py:528`は両commitを`git show`で読み、`:583`で前処理結果を比較する。呼出先`source_digest.py:1663`は`-E -P -nostdinc`。リンクやベンチではない。D297も保証を翻訳単位全体の同一性とは呼ばない（`docs/decisions.md:13747`）。

**影響 →** 材料整備を不要に計算ノード待ちへ回す可能性がある。

**是正案 →** 前処理検査と実build／性能測定を分離する。前処理検査は非計測であり、login node実行を一律禁止する理由はない。ただし複数compiler・context数・メモリ量を確認して実行場所を決める。後続の実build／テストは指定runner、性能測定は計算ノードを使う。

### 所見5【real】5本はgitlink非依存だが、認可非依存ではない

**所見 →** planの「5本、pin前進不要」は狭義には成立する。これを「5本とも今すぐ無条件に実装・完了できる」と読むのは誤り。

**根拠 →** plan §4の完了条件と、D16（`docs/decisions.md:248`）、D579（`:23370`）を照合した結果：

| T | gitlink前進なしの完了 | 条件・修正 |
|---|---|---|
| pin材料3点 | 可 | 候補OID、検査結果、波及表。検査失敗の記録を「前進可能」と扱わない |
| TicToc hook | 条件付きで可 | **TicTocの正式編集面認可が必要**。別checkout／branch内で実装・commit・control検証する |
| TicToc baseline | 可 | 完了は選択・出力契約・hook不在時拒否まで。floor取得を含めない |
| mocc機械実証設計 | 可 | 設計の完了。変異探索解禁・実証済みとはしない |
| 近年CC候補選定 | 可 | 調査成果物で完了。CCBenchへの追加実装とは分ける |

D16はtrace-hookのbranch格納を要求するが、**submodule内のlocal commitを一律に人間専用とはしていない**。`pin.py:20`の境界はpushである。D579のmocc限定認可をTicTocへ流用することはできない。

**影響 →** 編集面契約を整理しないままTicTocを「即着手可能」と起票すると、次waveが認可待ちで止まる。逆にlocal commitとgitlink前進を混同すると、準備自体が不可能に見える。

**是正案 →** 5本中TicToc hookは「編集面認可依存」を明記する。既存の完了条件なら**pin前進要への再分類は0本**。完了条件に「pinned producerでの正式floor取得」を加える場合は、その部分をpin前進要の別Tにする。

mocc設計だけでも、hole位置、auditor入力、X/P/I、hot/cold lock、陽性・陰性control、期待拒否を後続実装者が使える形まで固定すれば独立waveになる。ただしチェックリストの再掲だけなら、実証waveのplan段へ統合する方が安い。

### 所見6【real】TicTocを同じ候補へ積むと、D297 checker適合も残件になる

**所見 →** hook移植完了からD297材料の合格へ直結するとは限らない。

**根拠 →** `check_trace0_preprocess_identity.py:678`は`SILO_SPACE`を列挙し、`:547`はinclude行変更を検査する。新規includeの特例は`:545`の**moccのtrace.hh 1行限定**。追加・削除等の拒否も`:186`以降にある。

**影響 →** TicToc hookで同種のincludeを追加した候補は、既存checkerが保証できず拒否する可能性がある。「同じ候補へ載せて検査し直す」だけでは準備完了見込みが不足する。

**是正案 →** 初回候補はmocc単独を基本とし、TicTocは別候補とする。TicToc材料Tには「既存checkerの保証範囲との適合確認」を含める。拒否を迂回する提案にはしない。

## 4. D2104項13を同日に覆す記録の書き方

### 所見7【real】直接発話は優先するが、今回の逐語は具体的な解除案の承認までは含まない

**所見 →** 「疑問形だから何もできない」は過小解釈。一方、「当面終了・B群化・A→Bをユーザーが確定した」も過大解釈である。

**根拠 →**

- 射影`user-utterances.md:2`〜`:4`は解除検討と論文価値への懸念、近年手法追加への関心を示す。
- 射影`D2104-head-and-item13.md:3`は推奨に対する一括承認を記録し、`:18`はpin再承認を別途要求する。
- 同項には「主経路完了まで」という期限も、材料整備の禁止もない。

**影響 →** AIが提案した優先順位を直接発話の逐語内容として保存すると、未承認の研究スコープが確定事項になる。

**是正案 →** 現段階のfragmentは、次の区別を明記する。

> **位置づけ：裁定案・準備方針。** D2104はAIが起草した説明・推奨39項へのユーザーの「推奨通りで」という一括承認である。後続の直接発話3件を一次資料として保存し、Silo固定の見直しを検討する。直接指示と旧推奨が衝突する範囲では直接指示を優先する。
> 今回の発話から、pin前進の再承認、A→Bの厳密な順序、C-1のB群化まで承認されたとは解釈しない。これらは親の提案として示す。D2104項13の実測保留とpin再承認は維持し、D1603材料3点を再提示資料として整備する。

最小形は**裁定案の提示＋準備成果物の完成**でよい。「暫定ユーザー裁定」と記録して取消し条件を付ける方法は、承認主体の曖昧さを解消しない。後続で解除が明示された際に、その発話を引用し、変更対象を7月27日改訂(1)に限定して確定記録へ進める。

## 5. docs変更の検査面

### 所見8【real】T-167は文中へのfold追記で読み順が壊れている

**所見 →** 不自然さは実在する。ただし元の本文が欠落したとは確認できない。

**根拠 →** `docs/phase3.md:2595`の「分類不能8件の」と、`:2596`の「帰属を確定」の間に9月17日の追記が入っている。`docs/spool/worklog/README.md`の「見送り追記」規則は、先頭物理行の行末への挿入を要求する。

**影響 →** plan H7どおり同じ位置へ追記すると、文中の割込みがさらに増える。`:2599`の旧再訪条件との優先関係も読み取りにくい。

**是正案 →** 既存bytesを勝手に再構成せず、追記文を「【2026-09-17追記：……】」として明確に区切る。旧再訪条件を置換する場合は対象を明記する。`spool_fold.py --dry-run --show-diff`で**描画後の段落全体**を読む。恒久的な挿入位置修正は別のfold修正として扱う。

### 所見9【real】planの検査表は概ね正しいが、意味の正しさとfold後参照の寿命を保証しない

**所見 →** exact pin検査を通しても、解除の認可・状態語の意味・T-167の文章破損は保証されない。

**根拠 →**

| 対象 | 実際の検査 |
|---|---|
| phase3 | `check_docs.py:142`でliving docs。`:6721`行番号参照、`:6738`現行pin literal、`:6744`D実在、`:6752`path実在 |
| T台帳 | `:2556`台帳境界、`:2862`以降の保存則、`:2896`以降の先頭ID・重複等 |
| spool | `:1259`からschema検査。base整合には別途fold dry-runが必要 |
| paper-story README | `:125`の対象外族。C-1の意味や件数を自動照合する検査は見つからない |
| handoff | `:6585`の書式・状態語はwarning。`:6856`の状態行不在はfinding。`:6857`の稼働中48時間超はwarning |

**影響 →** 「check_docs緑＝解除の正当性まで検証済み」と誤読しうる。またplanの「実在するdecisions fragmentを参照」は、foldでfragmentが削除されるため恒久参照にならない。

**是正案 →**

- living docsは安定したphase節を参照し、消えるfragmentへのpathを恒久参照にしない。
- READMEの「確定したこと」へ未確定案を置かない。
- 状態は「準備」「未実測」「pin未承認」「変異探索未解禁」を個別に目視確認する。
- handoffの古さを本変更の阻害エラーと混同しない。
- exact prose pinの更新は不要と判断するが、親の受入結果で確定する。

## 6. 段4裁定案とdocs-onlyの可否

### 所見10【real】docs-onlyは妥当だが、「裁定の付替えだけ」で終えると既知材料を次waveへ送ることになる

**所見 →** 本waveへTicToc実装を入れる必要はない。一方、既に取得できる候補OID・波及表まで将来Tへ丸投げする必要もない。

**根拠 →** D1603は候補・同一性結果・波及範囲を要求する。候補と波及範囲は本相談で具体化できた。`between_run_floor.py:285`、`:304`から、TicToc baseline単独追加では測定開通しない。

**影響 →** baseline実装を混ぜれば受入・コードレビュー対象が増える。材料(1)(3)を残さなければ、次waveが今回と同じ探索を繰り返す。

**是正案 →** P1〜P4は次のとおり。

| 裁定 | 判定 | 修正文 |
|---|---|---|
| P1 | **修正して採用** | 「moccのcertified比較・合成基盤への実装投資を先行する。近年CCの候補調査は独立して進め、その要求を共通基盤設計へ反映する。B全体をAの汎用化完了まで禁止しない。」 |
| P2 | **却下** | 「D297合格はSHA束縛の置換を認めない。旧成果物を保持し、新pin系列の登録・identity・凍結への波及を明示して再承認を求める。」 |
| P3 | **修正して採用** | 「第2protocolは適用範囲の証拠を増やす。stock比較だけなら評価経路の拡張、mocc変異の独立実証と合成実績まで得て初めて合成対象の拡張を主張する。10protocol選択・descriptorの因果・LLM固有価値は主張しない。」 |
| P4 | **修正して採用** | 「phase内の準備着手条件を対象にし、b2本格投資の全面前倒しを含めない。協議合意済みの変更ならセレモニー不要だが、提案を合意済みとは扱わない。」 |

P4の根拠は`docs/roadmap-history/README.md:25`〜`:27`。なお、planの`docs/roadmap.md:478`参照は現checkoutではPhase 3.5のpopulation行を指しており、Eの根拠行として再使用しない。

**本waveの推奨範囲は、docs-onlyを維持し、裁定案・候補full OID・SHA束縛／移行表・5本の正確な完了条件を完成させること。** D297実走とTicToc実装は別waveでよい。受入全走はdocs-onlyでも既定どおり必要だが、今回確認していない所要時間の差を理由に実装同梱を正当化しない。
