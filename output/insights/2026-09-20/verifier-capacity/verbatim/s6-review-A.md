## 所見

1. **観点6 — 大規模入力の同一性確認が未完了。重み: should（最終受入前には必須）**  
   **場所:** [compare-summary.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-capacity/run/compare-summary.md:7)。  
   **具体入力・影響:** rh6 は旧版が完走していますが、新版は `new-failed`、結果・終了コードなしです。`identical=False` は判定差の反例ではなく比較未成立を示します。この記録から「完走済み入力すべての同一性確認済み」とは判断できません。指定要約には12 verdict全件の比較も揃っていません。  
   **修正案:** D-9 の最終実測で rh6 の失敗原因を記録して比較を完了し、12 verdict の JSON hash・全 field 一致を一覧化してください。段6後の予定作業なので、実装レビューの blocker とはしません。

静的点検では、実装に対する **must-fix は見つかりませんでした**。各観点の根拠は以下です。

- **辺集合:** `dsg.py:50` の範囲内変換は辞書式順序を保存します。範囲外 epoch は全版の前／後、負 tid は当該 epoch の先頭、過大 tid は次 epoch の先頭を境界にするため、tuple の strict successor と一致します。`lo == hi` は writer 不在・後続なしになります。`dsg.py:238` は genesis でも実 writer を優先し、不在の非genesis readだけを occurrence ごとに数えます。wr→rw、ww隣接対、共通 `add` の自己辺除外も旧経路と一致し、trace反例は構成できませんでした。
- **producer・診断:** `dsg.py:391` の鍵採番、`:447` の安定整列、`:464` の元入力再走査で、鍵初出順・版昇順・最初のwriter・重複note順を保存しています。同txid同版の二重writeは加算されません。`:380` の事前検査はwriteを持つwinnerだけを対象にし、退避前にintegrityを変更しません。bias変換の上端は `2**63-1` で、`:45` の逆変換も成立します。
- **worker入力:** `dsg.py:218` 以下のpacked分岐では親の鍵・版・producer要素を読みません。生成するdict・整数はworker側のものです。`test_verifier.py:3104` の代役はMapping操作と鍵参照を禁止し、read／ww双方の実機構とrun順を固定しています。
- **fallback・終端:** `dsg.py:595`、`parse.py:670` は失敗時にSIGKILL後shutdownし、逐次再計算前に部分結果・Future・executor参照を解放します。全task／全fileを再計算し、PID集合は採用outcomeから構成します。ImportError・OSError等の退避も同型です。`test_verifier.py:3203` のSIGTERM無視、pipe容量超過、`:3277` の子process timeoutとprocess groupのSIGKILLは、旧停滞を検出する具体的な構成です。
- **消費者・説明:** 差分は指定3ファイルのみで、既存testの変更は追加以外ありません。`core.py:186` の鍵数、receiptの親PID束縛、closure対象を維持しています。`campaign_lock.py:59`／`:61` の既存対象のbytes変更によるdriftはauthor説明どおりです。反実仮想の「実走で検出した」という履歴自体は再検証していませんが、挙げられた変異を検出するassertionは実体にあります。

## 段 3 A の所見の閉じ方

- **A-1 — closed:** `dsg.py:376` の無副作用事前検査と`:464` のtxn単位診断再生で、退避の二重計上とwriteなしgenesisを処理。
- **A-2 — partial:** `test_verifier.py:3070` で別fileのlast-wins後の辺・stats・integrityを固定。同file版の同等なliteral追加はありませんが、winner選択実装は不変。
- **A-3 — closed:** `test_verifier.py:2878` で隣接tuple・root順・SCC・integrityを比較し、fixtureでは`VerifyResult`全fieldも比較。大規模全件の完了は所見1の留保。
- **A-4 — closed:** `dsg.py:624` のset再生と探索処理を維持し、既存witness順の期待値も変更なし。
- **A-5 — closed:** CSR／破壊的source再利用は採用外。`dsg.py:187` のtask完全性検査と全件再計算を維持。
- **A-6 — closed:** D-5によりfreeze不採用。GC状態変更を導入していません。
- **A-7 — closed:** 裁定§6でcampaign lock driftとT126旧記録の扱いを明記。診断PIDを認証に流用していません。
- **A-8 — partial:** 裁定§1・§1bに対照と帰属の限界を記録。配列参照への変更は確認できますが、page単位のCoW帰属まで証明する資料ではありません。
- **A-9 — partial:** D-1・D-9・§4(c)で対象・閾値・schemaを固定。rh6を含む最終比較の完了が残ります。
- **A-10 — closed:** 裁定§7・§9で固定入力の容量改善に限定し、B-8達成や長時間一般の保証を主張していません。

## 総括

**GO — 実装レビューとして。** 辺・診断・探索順の変更やfail-open化の具体的反例は見つかりませんでした。  
最大の留保はrh6の比較未成立と、最終12 verdict比較の未完了です。  
容量改善の最終受入はD-9の実測完了後に判断してください。  
指定資料の静的点検のみ実施し、書込み・pytest・変異実走は行っていません。