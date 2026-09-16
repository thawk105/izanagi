必読7ファイルを読み、静的に追跡した。変更・pytest実走はしていない。以下の行番号は変更前のコードを指す。

## 所見 A-1: certified への迂回受理経路は確認できない

**主張:** プランどおりの変更であれば、exact-62 の v2 wire が certified 用入口から歴史 decoder に到達する経路はない。

**根拠 (file:line):**

- `artifact_admission.py:1518` → `_require_admitted_campaign:1472` → `_inspect_campaign:1222` → `_decode_campaign_lock_for_purpose:987`。目的を exact enum として検査し、`HISTORICAL_RAW` 以外は通常 decoder に渡す。
- `require_campaign_verifier_epoch:1126` も同じ目的別 decoder を通る。`classify_campaign:1448` は certified を明示する。
- 通常 decoder は `campaign_lock.py:526` → `_validate_authority:328` で現行63集合を要求するため、62は epoch 構築前に拒否される。
- overlay の早期 return (`artifact_admission.py:1292`) は拒否 decision。`require_admitted_campaign:1482` で止まり、certified view の抜け道にはならない。
- 歴史 epoch を内部 gate に直接渡しても `:1111` で拒否。view 構築にも `:426` の exact 通常型要求がある。

**real と思う理由 / refuted されうる条件:** 「certified に歴史 decoder の追加が波及する」という攻撃仮説は反証された。例外時の歴史 fallback、目的判定の緩和、通常 validator の変更が実装差分に入れば再成立する。

**成果物影響 1 行:** 計画された変更によって exact-62 が certified 選択へ加わる経路はない。

## 所見 A-2: encode・resume も通常 decoder の拒否を回避できない

**主張:** 歴史専用型の追加だけでは、exact-62 の再発行・再開は許可されない。

**根拠 (file:line):** `campaign_lock.py:696` の `encode_campaign_lock_v2` は生成した text を通常 decoder で自己検証する。resume は `loop.py:554` → `ident.ensure_resumable_wal:472` → `ensure_campaign_identity:538` → `verify_against_lock:350` → 通常 decoder (`:363`)。この照合は WAL repair より前。A-1 分岐も専用 non-certifying schema を要求し、exact-62 v2 の代替入口にならない。

**real と思う理由 / refuted されうる条件:** 迂回仮説は反証された。歴史 authority を通常 authority や mapping に包み直しても、62 map のままなら encoder の自己検証で拒否される。

**成果物影響 1 行:** 歴史閲覧対応によって62閉包の新規認証 lock や再開 WAL が生成される経路は増えない。

## 所見 A-3: 既存否定テストとの衝突はあるが、検出力の喪失ではない

**主張:** 現行63から worker を落とす入力は exact-62 と一致する。ただし該当テストは通常 decoder の拒否を検査しており、差し替える必要はない。プランはこれを見落としていない。

**根拠 (file:line):**

- `test_campaign_lock_codec.py:278` は63の各 path を削除し、通常 decoder の exact-key エラーを要求する。
- 同 `:182` の歴史未知 grammar は23、25、別集合24。`:202` は24の順序交換。
- `test_artifact_admission.py:1815` も同じ合成で、codec 段の拒否を要求する。
- `s2-plan.md` §5は worker 削除との衝突を明記し、新62 superset に worker ではなく未知 path を使う。

**real と思う理由 / refuted されうる条件:** 既存テストの恒真化という仮説は反証された。ただし新テストで「62＋worker」を未知と呼べば誤りになる。それは既知63である。

**成果物影響 1 行:** 既存の通常 decoder 拒否検査を残すことで、certified 受理集合の拡大を検出し続けられる。

## 所見 A-4: 二重検査は成立するが、wire 順序の独立再検査ではない

**主張:** decoder と authority の両方に exact grammar 検査が残る。ただし authority は再構成後の宣言順を検査するため、元 wire の順序違反を独立に再検出する層ではない。

**根拠 (file:line):** `campaign_lock.py:393` は sorted wire tuple を比較し、`:399` で宣言順 map に再構成する。`HistoricalCampaignLockAuthority.__post_init__:211` は宣言 tuple の whitelist と map 順序を検査する。プランはこの形を62にも追加する。元 wire の順序には、さらに decoder の outer canonical 検査 (`:604`) がある。

同数別集合62、subset61、未知 path を足すsuperset63は新62分岐に一致せず、24 validator でも拒否される。順序違い62も同様。既知63へ一致するsupersetは、既知 grammar として受理される。

**real と思う理由 / refuted されうる条件:** 受理集合の穴は確認できない。「authority も元 wire 順序を守る」という説明なら過大だが、プランは wire 順序と宣言順を区別している。追加 gate は不要。

**成果物影響 1 行:** 未知集合・非canonical順序の入力から歴史材料レポートが生成される経路は計画上増えない。

## 所見 A-5: epoch の通常型への誤分類が最も危険だが、プランは必要箇所を押さえている

**主張:** `E1` 表示自体は歴史 epoch でも正しい。危険なのは通常 `CampaignVerifierEpoch` として返すことである。ただし分類分岐だけを落としても、通常型に対する63 map 検査が残れば拒否になる。

**根拠 (file:line):**

- `artifact_admission.py:1051` は epoch 算出前に committed blob 検証を呼ぶ。
- プラン (`s2-plan.md:55`) は62を明示 path 版へ接続する。`contract_loader_binding.py:577` は渡された全 path を照合し、`_iter_blobs:437` は欠落 path を拒否する。
- `binding_from_authority:597` 側は `:81` の現行63固定検査で62を拒否する。誤ってこちらへ流しても照合省略による成功にはならない。
- 歴史型判定は `artifact_admission.py:1067`、mapとの対応検査は `:275`。プラン (`s2-plan.md:53`) は scope の組、型、記録 map の対応を変更対象に含める。
- certified gate の `artifact_admission.py:1118` は現在閉包の**可用性**を確認するだけで、記録閉包との一致を再検査しない。

**real と思う理由 / refuted されうる条件:** 通常型にも62 mapを許す変更まで加われば、誤分類された内部 epoch は型 gate を抜け得る。ただし公開 certified 入口では通常 decoder が別途止める。プランは通常型の63限定を維持し、62専用歴史型と全62件のdigest否定テストを指定しているため、現段階の欠陥とは認定しない。

**成果物影響 1 行:** 誤分類を許すと材料の現行適合表示と内部 certified gate が壊れるが、計画された型・map対応検査で防がれる。

## 所見 A-6: 親の実測は「3本の全面的な読取り成功」を証明していない

**主張:** 実測から言えるのは、測定時の指定射程に限られる。「並行編集なし」の無限定な結論は過大である。

**根拠 (file:line):**

- **同一 grammar:** `measured-facts.md:18` 以降は3本の62 key列の一致を報告している。digest値、記録commit、activation、WAL、全面的なadmission成功の一致は示していない。sorted wire から宣言順も復元できない。宣言順は別証拠が必要であり、今回 `git show 2a9ba783f^:...` をAST比較して、親の62行と完全一致、記載SHA-256との一致を確認した。
- **並行編集なし:** 同 `:126` は114 branchの指定2ファイル、`:129` は指定worktree群の同2ファイルを測った結果。テスト、他ファイル、列挙外checkout、測定後の編集には及ばない。`main...branch` 自体も未commit編集の検査ではない。
- **T-2125非発火:** 同 `:118` は3本のpolicy正規化hashと測定時policyの一致。`artifact_admission.py:1365` の比較条件については根拠になるが、現在はそれ以前のdecoderで拒否されるため、全経路の成功実測ではない。将来policyやWAL側receiptの適合まで保証しない。

**real と思う理由 / refuted されうる条件:** 射程の限定は必要。ただしプランは実装後の実3本確認を親に残しており、既に全面成功したとは扱っていない。並行編集の文言だけなら正しさへの直接影響を示せないため nit。

**成果物影響 1 行:** 実3本の歴史admission成功を未確認のまま報告すると、実際には生成不能な材料レポートを「読取り復旧済み」と誤記する。

## 所見 A-7: 「対象3本」は decoder の個体限定ではない

**主張:** grammar収載後の歴史decoderは、同じexact-62 grammarを持つ他の適格入力も受理する。「この3本だけ受理する」という説明なら誤りである。

**根拠 (file:line):** `s1-brief.md` のscopeは3本に限定する一方、`s2-plan.md:40` の分岐はpath tupleだけを識別し、個体のpath・lock hashを照合しない。これは `ruling-D1653.md` のgrammar収載方針と整合し、同裁定は個体hash allowlistを却下している。

**real と思う理由 / refuted されうる条件:** 受理集合の説明上の注意であり、実装欠陥ではない。対象3本を調査・確認範囲と読めば矛盾しない。個体限定gate、台帳、互換frameworkを追加する必要はなく、その追加はscope外。計画された検査はgrammar・digest・型境界に直結している。

**成果物影響 1 行:** 歴史閲覧の受理集合はexact-62 grammar単位で広がるが、certified選択と台帳membershipは広がらない。

## 総括

最も危険なのは A-5 の通常 epoch 型への誤分類。プランはその防止箇所を押さえている。  
正しさゲートを緩める具体的な欠陥は、静的追跡では確認できなかった。  
**プランは採用可。** 親の実測は A-6 の射程に限定して記述すること。  
実装後の差分・テスト・実3本の読取り結果は未検証であり、本所見は実装承認ではない。