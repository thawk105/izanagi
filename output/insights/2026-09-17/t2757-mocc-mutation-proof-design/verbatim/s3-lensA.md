## 判定と参照

**修正して採用。** 最大の問題は、plan が F-b を read/update に限定しても、validation による torn read 検出の論証が成立していないことです。また、update 負例の発火を候補全体の経路被覆へ拡張すること、登録検出を実行経路の閉包とみなすことはできません。

指定資料はすべて読取可能でした。静的検査のみで、変更・build・実走はしていません。以下では [現物]( /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/mocc-transaction-e9e477ca.cc) を M、[段2 plan](/home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/s2-plan.md) を plan と略記します。

## 1. F-b の「未完了なら lock、完了済みなら版」は観測時点が異なる

- **対象:** brief F-b／plan:25–36。
- **severity:** **must-fix**
- **主張:** 全 read-set を検査することは確認できる。しかし、版と counter の別々の読取によって、torn read が必ず検出されるとは言えない。plan:33 の局所論証にも穴がある。
- **根拠:** M:1008–1039 は、途中で abort しない限り全要素を走査し、温度による検査免除はない。ただし版を M:1010–1013、counter を M:1024 で別々に読む。

次の静的な反例候補を、このコード上の順序だけでは排除できません。

1. cold reader が旧版を取得し、counter が非 writer であることを確認する（M:320–339）。
2. writer が正常に施錠し、payload を更新する。reader の body 読取がその途中に重なる（M:346–348、1169–1170）。
3. writer の publish 前なので、reader の再読版と validation の版がともに旧版となる（M:350–352、1010–1013）。
4. **validation の版比較後、counter 読取前**に writer が publish・unlock する（M:1195–1196、1207）。
5. reader は解放済み counter を読み、版比較・writer 検査の両方を通る。

writer の X/P は正常でも、この順序は排除されません。hot の単一 load から read lock を単純に抜いた場合も、同じ観測の隙間があります。

これは **stock で torn read を実走確認したという報告ではありません**。body のコピー実装・サイズ・メモリモデルを含む確定には追加確認が必要です。しかし、「必ず捕まる」の証明としては既に不十分です。

一方、正常な hot/RLL 経路は読取前に lock を取得します（M:280–313）。canonical restore は後続操作で既存 lock を解放し得ます（M:834–857）。validation の write-set 昇順施錠（M:990–1001）、upgrade／再取得（M:770–788、834–888）について、**温度述語の変更だけで別個の直列性違反を起こす確定反例は今回得ていません**。それを上記の検出保証へ読み替えることもできません。

- **是正案:** F-b の還元主張と plan:33 の二分論証を削除する。「既存防壁の保存・発火範囲を検査する設計」とし、この観測順序を正しさ上の未解決事項として残す。DELETE の absent 非対称（M:341–344 対 356–364）も、plan が既に記した静的反例候補の扱いを維持する。D2114 の「成立可否を判定する」を、成功前提へ強めない。

## 2. hot-update 負例は条件付きで三 reason を出すが、再取得方法を固定すべき

- **対象:** brief F-b／plan:74–92。
- **severity:** **should**
- **主張:** U が本当に「read-set 空・UPDATE 一回」なら、t1 の設計は成立する。stock まで必ず赤になる負例ではない。ただし「pending の lock を再取得」の API が曖昧。
- **根拠:** D1686 の counter 意味に従えば、成功した writer lock を早期解放して counter は `-1 → 0`。CLL の writer 記録が残るので M:993 の `lock()` は M:744–746 で戻る。したがって既存計装の以下三点で counter 不一致になる。

| 検査点 | t1/U の期待 reason |
|---|---|
| writePhase 入口 | `not-locked-at-entry` |
| payload 前 | `lock-lost-before-write` |
| publish 前 | `lock-lost-before-publish` |

その後、**RWLOCK の `w_lock()`** で `0 → -1` に戻せば、最後の `unlockCLL()` が `-1 → 0` にする。ここで `TxExecutor::lock()` を使うと stale CLL により再取得を省略し、末尾 unlock が `0 → 1` を作り得る。

U では後続の別 tuple への lock がないため、plan が認識した canonical restore による二重解放を避けられる。t4 は他 worker の lock を counter だけで区別できず、reason ごとの発火保証はない（D1686）。stock/U 対照を要求する点は妥当。

- **是正案:** commit／abort 回復の両方を `pending->rwlock_.w_lock()` 相当と明記する。U の実呼出列と pending の初期化・消去を実装時の成立条件にする。timeout は失敗として扱い、完走未確認を「balanced 実証済み」と書かない。

## 3. update 負例の発火だけでは型4を全面的に閉じない

- **対象:** brief F-a・F-b／plan:64、70、92、147–150。
- **severity:** **must-fix**
- **主張:** 負例方式は update の分岐実行と X の歯を示せる。一方、read の hot 経路、RLL 再試行、将来候補自身の verify 中の到達は証明しない。
- **根拠:** plan:92 はこの限定を正しく記す。しかし機械要件の「hot 証拠」がこの一件だけなら、read 側の helper 呼出が実質不発でも緑になる。M:280 の RLL 分岐は温度述語自体を迂回する。閾値を無視する候補も契約内にあり得る（plan:64）。

| 方法 | 証明できる範囲／空振りとなる形 |
|---|---|
| hot 負例の発火 | 同一述語の true 枝内だけで故障注入し、既存 X が出れば、その負例の update 到達証拠になる。別判定や直接 X emit では成立しない |
| 計数行 | 実分岐の観測点で数え、run・候補 identity に束縛すれば当該 run の証拠になる。helper 呼出回数だけでは hot 側選択や lock 成功を示さない |
| flag 値 | 入力条件の記録。関数未呼出、引数すり替え、threshold 無視、RLL 迂回を排除できず、単独では実行証拠にならない |

- **是正案:** gate の保証名を「stock 等価述語における hot-update 負例の到達・検出」と固定する。read/update の両経路被覆を要求するなら read 側の独立 witness を設計する。候補ごとの型4は別途扱い、今回の較正成功を全候補へ継承しない。四 site 全被覆を今回必須とする、という裁定の追加は不要。

## 4. P2 は登録時の発火を示すが、登録を通らない経路を閉じていない

- **対象:** brief P2／plan:213–237。
- **severity:** **must-fix**
- **主張:** 前件なしでは空真、template／軸登録後は proof 必須、という形は妥当。ただし検出対象への登録が実行の必須条件になっている証拠がない。
- **根拠:** plan の鍵は `patches/*.patch` と登録済み軸 module。別名でも同ディレクトリ内の patch 内容を構造的に調べれば発火するため、**単なる basename 変更は必ずしも迂回ではない**。しかし次は未規定。

  - 別配置・埋込み template を driver が使用する。
  - marker 導入済み checkout を driver 直書き PIN で取得する。
  - 軸 module を使わず、driver が source／marker 定数を直接持つ。

既存 driver に literal PIN・SOURCE_REL が実在する（Driver:42–43、648–675）。これは正当な診断経路であり禁止対象ではないが、「全 driver が軸登録を必ず通る」という前提にはできない。DQ:18–23 も admission 全体の閉包を主張していない。

- **是正案:** 新しい mocc mutation consumer が、実際に使う source・template・PIN と proof の束縛をどこで必須検査するかを設計に加える。別名 template、軸 module なしの直接指定、marker 導入済み別 PIN による対照を置き、**拒否または同じ proof 要求へ到達すること**を確認する。既存 NON_ADMISSIBLE 診断経路との区別も明記する。一般的な新台帳の新設までは要求しない。

なお、brief の「mocc は EBS 所属なので同じ鍵では恒真」は不正確。plan:217 の訂正どおり、常時 true なのは前件です。

## 5. 契約違反 A/B を D38 点5の lockskip 検出と同一視できない

- **対象:** brief P4／plan:159、189–211。
- **severity:** **must-fix**
- **主張:** `FLAGS_clocks_per_us` 読取 A は有効な契約違反対照。しかしこれだけで D38 決定4点5の実証をそのまま再現したとは言えない。
- **根拠:** D38:48–55 は点5を「fresh auditor が lockskip diff を独立検出」と記す。Silo n=1:18–23 は無保護書込みの機序を独立に読み解いた記録。対して plan の A は直列性違反を意味しないと明記されており、その限定は正しい。

また、「正しさ違反型 A は必ず marker 外侵食になる」という前提も成立しない。DQ が保証するのは物理行の封じ込め（DQ:10–23、490–526）。**hole 内の式から可視 global／関数を介して副作用を起こす契約違反**は、marker 外の差分を必要としない。許可された純粋比較の集合と、実際に投入できる C++ テキストを混同してはいけない。

- **是正案:** A/B を「D48 型の読取契約弁別 n=1」と記録する。D38 点5相当については、既存 mocc lockskip diff の独立静的監査を別対照として残すか、この置換の妥当性を明示的な判断事項にする。hole 内副作用型を使う場合は、コンパイル成立と実機械 gate の拒否位置を先に確定する。

  marker 外 lockskip／validation 改変は、実 template・実 working diff に対して `outside-region` を確認する。これは DQ の positive control であり、auditor の独立検出には算入しない。機械 reject に auditor pass を与えても拒否が維持されることは AG:205–206 に対応する。

## 6. I を追加しない判断は支持するが、Silo 対称性だけを根拠にしない

- **対象:** brief F-c・P3／plan:239–243。
- **severity:** **should**
- **主張:** 今回の gate に I を追加必須とする固有根拠は得られなかった。ただし「Silo より強くなる」は十分な正しさ論拠ではない。
- **根拠:** 純粋な値渡し述語は write-set を直接変更しない。update では早期 lock の後に write-set 登録があり（M:459–477）、失敗は abort 側へ流れる。construct_RLL の温度述語は read-set 側で、write-set 全要素の登録は独立している（M:905–913、970–972）。

一方、P は sort 前後の size／pointer multiset しか見ない（D1686）。例えば M:477 の登録を落とす改変は P の観測開始前であり、P で捕まるとは言えない。

- **是正案:** I を今回要求しない根拠を「許可された述語の作用範囲と固定骨格」に置く。write-set 登録行の侵食を実 template の DQ 対照へ含める。I absent と write-intent 未実証を維持し、D1603 の pin 手続きを省略する根拠にはしない。

## 7. 既存実測と、今回初めて要求する保証を分離する

- **対象:** brief「既存被覆」・F-a・F-d／plan の既存14 check 再利用。
- **severity:** **should**
- **主張:** 過去の成功は資材・条件に束縛された実測であり、hot 被覆や新 template の保証ではない。
- **根拠:**
  - 要約 JSON:26–44、86–153 には abort 数・hot 到達数がない。「1 thread は abort 0」は、この射影だけでは再検証できない。
  - threshold 21 でも RLL による施錠は残る（M:280–295、473、905–913、970）。
  - 旧 `stock_high_xp_silent` は certified／cycle を条件にしていない（Driver:533–538）。
  - 19/19 KILLED には patch SHA 不一致による consumer 拒否も含まれる（T-2294 README §4）。すべてを独立した意味検出力と数えられない。
  - e9e477ca 単体は X/P/I absent、計装後も I absent（ProofTest:410–426）。

- **是正案:** F-a の abort 0 は親の追加観測として出典を区別する。「全 cold」を「温度述語 false」に直す。旧14 check は歴史的結果として保存し、新 template／hot 条件の意味証明に転用しない。F-d の隔離 checkout による診断実走と certified 探索の分離は、plan の修正を採用する。

## 8. 非解禁の文言は十分明確で、維持すべき

- **対象:** brief「不変条件」／plan:247–249、314。
- **severity:** **nit**
- **主張:** 設計完了を探索解禁と読ませる直接の文は見当たらない。
- **根拠:** plan は設計完了だけでなく **proof 完了も mutation 探索の認可ではない**と書き、D579、D2114、pin 手続き、producer の proof surface を区別している。
- **是正案:** この非解禁文を insight と decisions fragment の両方へ維持する。「機械 gate 通過」は必要な証拠の充足として記し、単独の認可条件としない。

## 総括

**must-fix は次の4点です。**

1. F-b と plan:33 の torn read 検出論証を撤回し、版／counter の観測間隙を未解決事項として明記する。
2. hot-update 負例の証拠範囲と、read 経路・候補ごとの型4を分離する。
3. P2 を実 mutation consumer へ接続し、登録外 template／直接指定 PIN の対照を設計する。
4. 契約違反 A/B と D38 点5の正しさ違反検出を区別し、DQ 拒否を auditor の実証に算入しない。

**plan の採否：修正して採用。** 温度述語案は実証対象の候補として残せます。ただし、read/update 限定だけで正しさ論拠が完成したとは扱えません。設計完了・実証成功・探索認可の分離は維持してください。
