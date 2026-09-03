## 所見一覧

1. **重大** — `s2-plan.md:42-45` は ledger fd を `O_APPEND|O_CREAT|O_NOFOLLOW` で開くとしており、`O_WRONLY` または `O_RDWR` と作成 mode が欠ける。逐語実装では `p3_b4_raw_record_producer.py:501-509` と異なり書込み不能となり、台帳は残らず材料レポートの復元値も増えない。成功受理集合と certified 選択への直接影響はない。
2. **重大** — `s2-plan.md:40,43-45` の「未終端 tail は無視」後に `O_APPEND` すると、部分行の直後へ次行が連結される。以後 `s2-plan.md:133` の strict loader が恒久的に拒否し、正常な成功 leaf がそろっても assembly と材料レポートが `rejected/not_evaluated` へ変わる。記録失敗が consumer 側の成功可否へ漏れる。
3. **重大** — `s2-plan.md:74,103-105` の「absent path に matching rejection があれば説明済み」は deferred を間接的に rejection 扱いする。`p3_b4_raw_record_producer.py:588-610` で同一候補を一度拒否した後、`:1651-1672` で再試行を deferred にできるため、leaf は absent、ledger には古い rejection が残り、材料レポートだけが非保証を誤って落とす。
4. **重大** — `s2-plan.md:40,50,74,150` には rejection 履歴の完全性を証明する外部 head または gap 記録がない。append 失敗後の同一候補の別 event、または newline 単位の末尾切捨てで欠落を隠せるため、台帳件数と材料レポートの「fully reconstructible」が偽になる。受理集合は不変だが参照される履歴が不完全になる。
5. **要補足** — `s2-plan.md:39,101` は event ID を全 planned 集合で受ける一方、manifest join を必須のように書く。registry は 201 件超を保持でき、manifest は先頭 201 eligible だけを選ぶ (`p3_b4_analysis_ledgers.py:1050-1083`)。manifest 外の scheduled ID は producer が `p3_b4_raw_record_producer.py:613-622` で実際に拒否するため、材料レポートは manifest 不在を明示できないと valid ledger event で失敗または欠落する。
6. **nit** — `s1-brief.md:33-35` の「producer の書出し面は 1 種類」は誤り。`p3_b4_raw_record_producer.py:867-870` は検証ごとに receipt bundle の snapshot 群を一時 directory へ書く。成果物 bytes への直接影響はないが、広い `open/write/fsync` failure 注入では ledger writer に到達したか帰属できない。
7. **nit** — `s2-plan.md:117-136` は新テストを列挙するが、既存の一対一 mutation 台帳 `test_p3_b4_raw_record_producer.py:284-303,807-810` の拡張を定めない。tamper、固定名、append 消失の各変異は複数 node が同時に落ち、どの層が拒否したか一意にならない。成果物値への直接影響はない。

## 受理集合が動く可能性

既存の成功列は `p3_b4_raw_record_producer.py:1739-1758,1841-1878` にあり、`_validated_publication`、`_request`、`_derive_b4_attempt_data`、`_publish_exact` を通る。プランどおり rejection catch 後だけ writer を呼ぶなら、棄却入力から成功へ戻る枝は増えない。

`_publish_exact` の同一 bytes idempotence、異 bytes 拒否 (`:487-499,526-534`)、symlink 拒否 (`:453-478`) も変更対象外である。issuer の新固定名予約は受理集合を広げず、その名前を planned path に使う入力だけを狭める。

ただし assembly に strict ledger load を必須化すると、`s2-plan.md:133` が期待する ledger tamper 拒否により、既存の正常な success leaf 集合まで利用不能になる。これは producer の成功公開集合ではなく、assembly と材料レポートの受理集合を狭める変更である。ledger 検証失敗は raw assembly rejection ではなく、独立した `rejection_history_status=invalid` として運ぶ方が境界を保てる。

発火入力は存在する。実 rejection は `test_p3_b4_raw_record_producer.py:1101-1115`、planned conflict は `_publish_exact:487-499`、deferred は同テスト `:1183-1198`、固定名 descendant は `test_p3_b4_prerun_issuer.py:543-571` で到達している。恒真な検査ではない。

変異帰属を一意化できる候補は、専用 append helper を狙う failure test、`PLANNED_PATH_CONFLICT` の catch だけを狙う記録 test、rejection 後 deferred の非保証維持 test である。反対に loader・assembly・report の tamper test、固定名の発行時・reload 時 test、writer 呼出し削除は複数 node が落ちるため一意でない。

## 記録失敗と公開可否の結合

成功枝から writer を呼ばない設計自体は正しい。記録成功・失敗のどちらからも `_publish_exact` へ戻らないため、同じ呼出しが rejection から success へ反転する経路はない。

実装には少なくとも `O_RDWR|O_APPEND|O_CREAT|O_NOFOLLOW`、mode `0o600`、同一 locked fd 上の先頭からの reload が必要である。`O_WRONLY` では strict reload できず、プラン記載の flag だけでは write できない。

未終端 tail を検出した場合、そのまま append してはならない。最後の newline まで truncate・fsync してから「履歴欠損あり」を耐久記録するか、ledger を回復不能として扱い、以後も historical-rejection 非保証を絶対に落とさない必要がある。

また、append 後の `fsync` 失敗では event が可視だが耐久性不明という状態が生じる。この状態を単なる有効 event として coverage に数えると、後の材料レポートが誤って完全性を主張する。

## deferred と rejection の分離

型と返却経路は現状明確に分離されている。`B4RawRecordRejection` は `p3_b4_raw_record_producer.py:128-133`、`B4RawRecordDeferred` は `:135-141`、deferred の返却は `:1665-1672,1748-1749,1849-1851` である。プランが deferred を ledger writer へ渡さない点は正しい。

問題は consumer の coverage 判定である。到達可能な反例は次のとおりである。

1. valid scheduled ID に caller judgment field を加え、`:588-610` で durable rejection を作る。
2. 同じ候補を campaign lock 保持中に再試行し、`:1651-1672` で deferred を返す。
3. planned leaf は absent のままだが matching rejection は存在する。

この状態で非保証を落とすと、「過去に拒否された」は復元できても「現在 absent なのは rejection のため」は復元できない。`s2-plan.md:132` の test は event count 不変だけでなく、この順序で非保証が残ることまで検査すべきである。

## 名前衝突の閉じ方の検査

この部分は閉じている。`p3_b4_prerun_issuer.py:423-430` の固定 path 群へ新しい direct leaf を追加すれば、`:434-440` が exact path と descendant を拒否する。新 leaf の祖先になれる planned path は publication root 自身だけで、これも `:434` が拒否する。

planned path 同士は `_normalize_planned_results` の一意性 (`:380-385`) と厳密祖先衝突 (`:386-398`) で閉じる。発行時は `:732-740`、reload 時は `:1100-1109` が同じ固定名検査を通るため、receipt 全再束縛でも回避できない。

新しい literal は `_REGISTRY_NAME`、`_MANIFEST_NAME`、`_RECEIPT_NAME`、`_RECEIPT_TEMP_NAME` と異なる。writer が caller path を受けず、検証済み root fd に対する固定 basename だけを開く条件も維持すべきである。

テストは新名前について発行時 exact、発行時 descendant、publication root 自身、reload 時 exact、reload 時 descendant を分けて持てばよい。ただし同一 fixed-list 削除変異で複数 node が落ちるため、mutation の一意帰属とは別問題である。

## 親 brief 自身の誤り

DW-O09 の結論「producer source の pin は 0 件」は正しい。`test_frozen_artifacts.py:41-88` の 23 path に producer はなく、producer 自身の projection closure `p3_b4_raw_record_producer.py:655-684` にも自分は含まれず、`:65` も closure 外と明記する。live code の参照は material report import とテストで、source hash pin は見つからない。

ただし `s1-brief.md:29-31` の grep hit の列挙は不完全で、tracked な過去 insight にも多数の言及がある。いずれも歴史記録であり pin 結論は変わらない。

DW-O10 は誤りである。最終 attempt JSON のほか、`p3_b4_raw_record_producer.py:867-870` が一時 receipt snapshot を書き、`_publish_exact:501-537` も staging file を作る。また `_ensure_real_parent:453-472` は既存 directory が実 directoryかは検査するが、既存 mode が 0o700 かは検査しない。

DW-G04 の migration 不要判断は妥当である。worktree 内に issuer receipt、registry、manifest の実ファイルはなく、campaign code に issuer/producer の production caller もなく、launcher 配線もない。既存 bytes を変換しないことで壊れる repo 内成果物は確認できない。将来、外部に旧 v1 publication が存在するなら、新予約名と同じ planned path だけは reload 受理集合が狭まるが、現時点の実在根拠はない。

## 総括

- 最重所見は、古い rejection の存在だけで deferred 後の absent path を説明済みにし、材料レポートの非保証を誤って落とす点である。
- writer flag 欠落と未終端 tail への追記も、そのままでは ledger を作れない、または恒久破損させる。
- strict ledger failure を raw assembly failureへ昇格すると、記録失敗が後の成功成果物の利用可否へ漏れる。
- 成功公開の受理集合、`_publish_exact`、symlink 拒否、固定名衝突の基本設計には拡大経路を認めない。
- pin 0 件と migration 不要は妥当だが、DW-O10 の書出し面 1 種類は誤りである。
- よってプランは現状のまま採らず、完全性・deferred 順序・tail 回復・fd flags・manifest 外 ID を直してから採るべきである。