## 発火可能性の検査

1. **[real] report CLI は入口として実在するが、成功入力は今日存在しない。**  
   `p3_b4_material_report.py:1594-1614` に正式 CLI があり、`publication_root` をロードして report を書く。一方、`output/**/{prerun-issuer-receipt.json,analysis-manifest.json,scheduled-attempt-registry.jsonl,report.complete}` は全て 0 件だった。  
   **影響:** 現在の正式 report、certified 選択、参照先は全て未生成のまま。

2. **[refuted] plan L3 の「publication が無いので launcher が止まる」は、実測上の最初の停止点ではない。**  
   launcher は `prepare_launch()` で admission record を検証してから driver を呼ぶ (`p3_b4_launcher.py:551-580`)。3 admission record は不在で、親実測も `record is unavailable` で停止している (`stage1-addendum.md:67-71`)。publication はその後に driver argv へ渡る (`p3_b4_launcher.py:581-588`)。  
   **影響:** 停止台帳で最初の拒否理由を publication 不在とすると、実際の発火順と再開条件が誤る。

3. **[real] publication issuer は API として実在するが、production 発行経路は存在しない。**  
   issuer は caller-supplied `B4ScheduledAttemptInput` を要求し (`p3_b4_prerun_issuer.py:709-738`)、201 eligible 未満を拒否する (`:796-805`)。検索では production caller は 0 件で、`B4ScheduledAttemptInput` の非定義出現は prereg consumer の synthetic behavior probe (`p3_b4_analysis_prereg_consumer.py:757-785`) と tests だけだった。  
   **影響:** publication・manifest・schedule receipt・planned result path は一件も確定せず、下流の launcher/report は成功発火できない。

4. **[refuted] plan の「M13 は正しい。反例 path はない」は追補と食い違う。**  
   `output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/s4_rejections_digest.txt` に赤 entry が3件ある。`loop_state.json` が無いため eligible ではないが、「赤 precursor 0」の反例ではある (`stage1-addendum.md:73-83`)。  
   **影響:** precursor 台帳値は「0」ではなく「最大3、eligible 0」となる。受理集合 0/201 は変わらない。

5. **[real] B-4 production 成果物と marker campaign は今日も 0 件。**  
   `output/` の固定6名を再検索し、上記3 publication artifact、`report.complete`、`b4_launch_context.json`、`raw-record-rejections.jsonl` は全て 0 件。`output/campaigns/` の30 `campaign.lock` に `b4_reflux_ablation` hit はなかった。  
   **影響:** production report、planned result、certified-selection の値を更新できる実 artifact は存在しない。

## 依頼 4 項目の着地状況

1. **「不変な結果 artifact の writer」— [refuted: create-only writer はあるが、不変ではない]**  
   `_publish_exact()` は同一 path の異 bytes を拒否し、同一 bytes は idempotent success にする (`p3_b4_raw_record_producer.py:527-590`)。しかし通常の mode `0600` file であり、削除後は別 bytes を再発行できる。producer 自身も後日の再開を排除しない (`:62-70`)。issuer も coordinated rewrite・external rename を非保証としている (`p3_b4_prerun_issuer.py:53-64`)。  
   rejection ledger は append 前に未終端 tail を truncate し (`p3_b4_raw_record_producer.py:657-733`)、complete suffix の削除・truncate は report が明示的に検出不能としている (`p3_b4_material_report.py:66-80`)。  
   **影響:** 過去の成功・拒否を巻き戻した後の再生成で、report の在否・拒否率・verdict が変わり得る。

2. **「§7.1 の全件 report generator」— [refuted: material report generator はあるが、§7.1 全件規則は未達]**  
   generator が完全行を作る対象は manifest の各 block × 2 arm に限られる (`p3_b4_material_report.py:331-355`)。registry にある manifest 非選択 attempt は `not_selected` の ID/path/status だけであり (`:790-798`)、§7.1 が各行に要求する arm、campaign id、各 hash、WAL、停止理由、予算、verdict、anomaly class、性能有無を持たない (`phase3-b4-reflux-ablation-preregistration.md:690-700`)。  
   選択行についても `model_hash`、`budget_consumption`、`anomaly_class` は明示的に absent (`p3_b4_material_report.py:412-432, 604-630`)。さらに生成物自身が `section_7_1_four_classifications_operationalized: false` と宣言する (`:872-882, 1055-1063`)。これは T-2049 の「4分類を実効化したとは主張しない」「model hash と予算消費は存在しない」と一致する (`2026-09-01_t2049-b4-material-report/README.md:41-50,190-204`)。  
   **影響:** この report を「§7.1 全件 report」と認定すると、非選択 attempt と欠落 field が certified 判断・全件台帳から落ちる。

3. **「正式起動口」— [refuted: per-arm driver 起動口はあるが、分析 chain 全体の起動口ではない]**  
   bootstrap は選択した1 arm の driver を呼ぶだけ (`p3_b4_launcher.py:561-589`)。continuation は on/off critic receipt を作るが、実行する driver は選択した1 armだけ (`:591-642`)。201 block × 2 arm の完走、`publish_b4_attempt_result(s)`、material report の呼出しはいずれも launcher に無い。  
   覆う区間は  
   `admission検証 → context/sidecar → 単一armのdriver main`  
   まで。  
   覆わない区間は  
   `予定表生成 → publication発行`、`全block/arm投入`、`driver終端 → raw writer`、`raw → report`、`report → certified selection`。  
   **影響:** launcher が成功しても planned result artifact・report・certified 選択は自動では1 bitも更新されない。

4. **「certified-selection connection」— [real: 未着地]**  
   T-2139 の無条件再開条件は、安定した `report.complete`、report 後の正規 caller、耐久判定先と sink 参照の3件 (`2026-09-01_t2139-b4-certified-selection-connection/README.md:106-114`)。いずれも現在 0。順方向を含める場合は floor と approval authority も必要。  
   **影響:** material report が将来生成されても、certified 選択・その台帳・参照は変化しない。

したがって、親 M2 の「4項目中3項目着地」は**依頼の形に照らすと refuted**。厳密には「部分実装2件、区間限定の起動口1件、未実装1件」である。

## 取り残された層

必要な層と、停止確認に使う観測は次のとおり。

1. **[real] 事前登録・admission 層**  
   §5 sentinel、3 admission record、floor、環境・予算を確認する。現在は §5 に `未記入` を含む7行 (`docs/...preregistration.md:154-167`)、admission record 0件、T-2288 では rr5/rr95 accepted calibration 0件。  
   **影響:** formal launcher は campaign 副作用前に拒否される。

2. **[real] authoritative precursor → scheduled input producer 層**  
   production caller と実際に生成された typed registry 行数を測る。現在は authoritative producer 0、正式 registry 0。  
   **影響:** 母集合・参照・initial proposal hash が確定せず、publication 受理集合は空。

3. **[real] publication 発行・権威選択層**  
   固定3 artifact と production issuer caller、権威 root の pin を測る。全て不在で、別 root 再発行も非保証 (`p3_b4_prerun_issuer.py:53-64`)。  
   **影響:** launcher/report がどの母集合を参照すべきか一意に定まらない。

4. **[real] 全 block・全 arm 実行調停層**  
   402 arm 実行の schedule 遵守と、全 attempt の終端を測る。現 launcher は単一 arm 起動のみ。  
   **影響:** §7.1 の無条件完走集合を形成できない。

5. **[real] driver 終端 → raw writer 接続層**  
   planned result path、producer caller、rejection ledger を測る。いずれも production 0。  
   **影響:** campaign が走っても分析入力へ到達せず、report は missing/rejected 観測しか出せない。

6. **[real] report 発行・安定所在層**  
   `report.complete` と束縛された2 file、正規 report caller を測る。全て 0。  
   **影響:** T-2139 の再開条件1・2が成立しない。

7. **[real] certified-selection 層**  
   耐久判断 artifact と sink 参照を測る。T-2139 により不在確定。  
   **影響:** certified selection とその参照集合は更新されない。

層2、3、4、5、6の所有者・正規 caller は現在の4項目 scopeだけでは閉じていない。実装済みと数えず、下の裁定候補へ返すべきである。

## 停止地点の構造化への所見

1. **[refuted] L1→L5 を一本の直列 chain とする切り方は実測順と一致しない。**  
   formal launcher の観測順では admission が publication より先 (`p3_b4_launcher.py:551-588`)。一方、artifact 生成依存では precursor producer → issuer publication が先である。二つの軸を混ぜている。  
   **影響:** 「次に何を満たせばどこまで進むか」の台帳順が誤り、publication を作っても launcher が同じ admission 点で止まる。

2. **[refuted] L2 の `design_not_feasible で停止した` は実測ではなく静的予測。**  
   issuer production callerも正式 input batchもなく、実際の issuer rejection receipt は存在しない。確定しているのは「201未満なら拒否するコード」 (`p3_b4_prerun_issuer.py:796-805`) と、正式 bundle 0件だけ。  
   **影響:** 計測台帳に未実行の拒否を実測値として記録することになる。`state=not-instantiated` と `expected rejection=design_not_feasible` を分ける必要がある。

3. **[refuted] L3 は launcher と raw writer を一層にまとめているが、両者の接続は存在しない。**  
   launcher の終端は driver return (`p3_b4_launcher.py:580-589,635-642`)。writer の入口は独立 API (`p3_b4_raw_record_producer.py:2057-2115`) で production caller 0。  
   **影響:** publication/launch を解けば raw artifact まで進むという誤った再開見積りになる。

4. **[refuted] L4 の名称「§7.1 report」は T-2049 の到達点より強い。**  
   T-2049 と現コードの双方が4分類未実効・field 欠落・closed-world 非保証を明記する。  
   **影響:** 不完全な material report を certified-selection の十分な入力として扱う危険が生じる。

5. **[real] L5 の停止自体は妥当。**  
   `report.complete`、report後 caller、耐久判断先が全て不在で、T-2139 の3条件と一致する。条件4は順方向を含める場合だけ。  
   **影響:** 現在の certified 選択・sink 参照は変化しない。

推奨する構造は、直列 L1〜L5 ではなく、少なくとも「規範/admission」「母集合/publication」「実行」「収集」「report」「certified selection」の6層で、各層を `observed stop` / `not instantiated` / `static expected rejection` に分ける形である。

## P1 を倒す反例 (あれば)

**[refuted: P1 の「したがって実装 diff 0」という結論は倒せる。ただし「今日 formal run が成功発火しない」は real]**

具体的な1単位は、`require_b4_proposal_registry_binding()` に **manifest membership** を追加すること (`orchestrator/campaign/p3_s4_loop.py:478-507`)。

現状は publication をロードした後、registry の一致行だけを選ぶ (`:442-475,492-502`)。issuer は eligible 行が201を超えれば先頭201行だけを manifest に採る (`p3_b4_prerun_issuer.py:796-806`、事前登録 `:382-388`)。したがって「registry にはいるが manifest にはいない attempt」は正規に構成可能で、launcher は受理する一方、raw writer は `_manifest_row()` で後から拒否する (`p3_b4_raw_record_producer.py:945-954`)。これは T-2101 が明記した実在穴でもある (`2026-09-09_t2101-proposal-binding/README.md:29-30,175-179`)。

この述語は恒真ではなく、既存の正規 producer/consumer 間で受理集合が実際に不一致である。依頼の「正式起動口」に直接属し、仮想攻撃向けの一般 gate ではない。T-2101 が受理した「実走前に実在述語を閉じる」型と同形である。

**影響:** bootstrap の受理集合から manifest 外 attempt が除かれ、実行済み campaign が§7.1 report の行集合外へ落ちる経路を閉じる。

よって、P1 の文字どおりの「今日発火する formal 実行はない」は維持されるが、そこから導いた「実装面の純増はない／diff 0」は維持できない。

## 裁定パッケージ候補

1. **publication authority**  
   どの root・発行者・一回性を権威とするか。別 root 再発行を許す現状を正式仕様とするか、一意の publication を選ぶか。  
   **影響:** launcher/report が参照する母集合と certified 対象が変わる。

2. **正式起動口の終端範囲**  
   現状の「単一 arm driver 起動」までを正式入口と認めるか、「全201 block×2 arm→raw writer→report」までを要求するか。  
   **影響:** 3項目目を着地済みと数えるか、未完とするかが変わる。

3. **結果 artifact の不変性定義**  
   cooperative create-only で十分か、削除・rename・別 root 再発行後も歴史を保持する必要があるか。  
   **影響:** report の在否・拒否率・verdict を耐久証拠として扱える範囲が変わる。

4. **T-2288 floor の集約規則**  
   rr5/rr95 accepted calibration の取得後、workload別3成果物を§5が受ける1 pinへどう集約するか。T-2288 が D1383 の裁定事項として返している。  
   **影響:** §7.1 の4分類と T-2139 順方向条件が発効可能になる。

5. **T-2139 の持ち主と保存先**  
   report後 caller、耐久判断先、sink参照の所有者を決める。3条件が揃うまでは再開しない。  
   **影響:** material report が certified selection を実際に変更できるかが決まる。

## 総括

plan は production artifact 0、admission/floor 未充足、certified-selection 未接続という大勢では正しい。しかし、以下は must-fix である。

- M13 を「赤 precursor 最大3、eligible 0」へ訂正する。
- 実測最初の停止点を admission record 不在とする。
- issuer の `design_not_feasible` を実測停止ではなく静的予測として記録する。
- launcher と raw writer を別層に分ける。
- material report を「§7.1 全件 report」と呼ばない。
- 4項目中3項目着地という集計を撤回する。
- P1 の diff 0 結論を再裁定し、manifest membership の実装1単位を段5候補に残す。

read-only 静的検査のみで、pytest・formal B-4 実走・性能測定は行っていない。