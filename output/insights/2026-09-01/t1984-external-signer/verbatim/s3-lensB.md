## 所見

静的検査のみ。pytest は実行しておらず、緑とは判定しない。

1. **real — 「issuer を通ったこと」は署名からは証明できない。**

   - 該当: `s1-brief.md:80-81`、`parent-findings.md:26-31`、`s2-plan.md:19-25`
   - 署名が証明するのは、設定された公開鍵に対応する秘密鍵が canonical payload を署名し、署名後に改変されていないことまでである。特定の `acceptance_issuer.py` が実行されたこと、reference と operational copy が同一であること、issuer が所定の再導出を行ったこと、内容が意味的に正しいことは証明しない。
   - 成果物への影響: certified 選択やレポートを「外部 issuer の検査済み」と扱うと、鍵保有だけを実行・内容の証明へ格上げしてしまう。
   - 逐語の修正案: 「署名検証が証明するのは、設定済み公開鍵に対応する秘密鍵による payload の承認と、署名後の非改変である。特定の issuer 実装の実行、再導出手順の実施、payload の意味的正しさは証明しない。」

2. **real — brief の「再送を拒否する」は範囲が過大である。**

   - 該当: `s1-brief.md:35-39,80-81`。これに対し `s2-plan.md:153-165,311` は別 wave/main/tip/lease acquisition 間だけと正しく限定している。
   - `lease_generation` による束縛は異なる acquisition への再利用を拒否するが、同一 wave/main/tip/generation/request での再利用を一回限りにはしない。single-use には外部 consume state が必要であり、これは追加実装ではなく裁定候補とすべきである。
   - 成果物への影響: 台帳が「再送防止済み」とだけ書くと、同一 context の receipt 再利用まで拒否されると後続 wave が誤認する。
   - 逐語の修正案: 「署名済み context 束縛により、receipt の別 wave・別 main・別 tip・別 lease acquisition への再利用を拒否する。同一 context 内での single-use は保証せず、外部 consume ledger も本 wave では実装しない。」

3. **refuted — 判定の意味的真正性を未閉鎖として落としている、という疑いは成立しない。**

   - 該当: `s1-brief.md:79-83`、`s2-plan.md:187-211,300-315`。特に `s2-plan.md:199,211` は `non-attributable-only` の意味が checker 系自己申告に依存し、署名しても閉じないと明記している。
   - ただし経路差は明記すべきである。`acceptance_launcher.py:426-474,582-635` では `child-green` は launcher が観測した `child_rc == 0` から導出される一方、`non-attributable-only` は waiter 由来 completion に依存する。
   - 成果物への影響: 一括して「verdict は真正」と書けば非帰属判定を過大評価し、一括して「完全な自己申告」と書けば `child_rc` の launcher 観測まで失う。
   - 逐語の修正案: 「署名は verdict 文字列を改変から守る。`child-green` は issuer が起動した launcher の `child_rc == 0` 観測と構造的に結合するが、テスト選択全体の意味までは証明しない。`non-attributable-only` の意味的正しさは checker completion の自己申告に依存し、未閉鎖である。」

4. **real — D583 の四残余は brief では名指しされるが、段 7 用記録として理由が足りず、plan の最終一覧では trust root と bootstrap 例外が曖昧化している。**

   - 該当: `s1-brief.md:82-83`、`s2-plan.md:302-315`、`rulings-verbatim.md:71-89`
   - 親起動点の迂回は `s2-plan.md:313`、completion 自己申告は `307-310` にある。issuer trust root は同一 uid/hook 限界へ吸収され、PATH・symlink・interpreter・Git・cwd・operational bytes の問題が落ちる。bootstrap は「人手配置未実施」とだけ書かれ、導入・更新時に定常時の保証を使えない理由が残っていない。
   - 成果物への影響: 後続 wave が「人手配置さえ済めば trust root と bootstrap も閉じる」と誤読する。
   - 逐語の修正案: 「D583 の四残余は、(1) 親起動点が issuer を省略できる、(2) issuer の code/key/toolchain を真正とする別 trust root が無い、(3) issuer 導入・更新時は新機構自身でその配置を承認できない bootstrap 例外になる、(4) completion protocol の内容と実行実在は waiter 自己申告のままである、という各理由により未閉鎖である。」

5. **real — 外部 issuer の導入が、operational source identity という新しい未証明面を作る。**

   - 該当: `s2-plan.md:19-20,171-185,302-304`、D583 の F385 指摘 `rulings-verbatim.md:75-79`
   - plan は repo 内 reference と repo 外 operational copy を置くが、その同一性や実行 bytes を land が束縛する field は示していない。issuer 自身に source revision/blob hash を署名させても、それだけでは F385 と同型の自己証明になる。
   - 成果物への影響: レポートが「reviewed issuer が署名した」と記録すると、実際には configured key の署名しか確認していない。
   - 逐語の修正案: 「repo 内 reference と repo 外 operational issuer の bytes 同一性、および operational issuer の実行実在は receipt から独立検証されない。issuer が自身の revision/hash を署名しても自己証明に留まるため、issuer trust root の未閉鎖として残す。」

6. **real — D906 の「検査器」は red checker と読むのが妥当だが、plan の field は executed bytes の証明ではない。**

   - 該当: `acceptance_launcher.py:402-474,512-518`、`dev_wave_land.py:1118-1154`、`s2-plan.md:116-127,187-200,310`
   - 現行 receipt vocabulary で `checker_*` が指すのは `tools/check_acceptance_reds.py` であり、land verifier は receipt の consumer である。したがって「検査器」は red checker と判定できる。ただし提案する `checker_content_sha256` は tested-main の期待 content hash であり、checker がその bytes で実行されたことは証明しない。`child-green` では checker 自体が実行されない。
   - 成果物への影響: D906 の四対象がすべて「実行 bytes として証明済み」と書かれると、署名対象と実行実在を混同する。
   - 逐語の修正案: 「D906 の『検査器』は `tools/check_acceptance_reds.py` と解釈する。署名へ入る `checker_content_sha256` は tested-main 上の期待 content hash であり、実行 bytes の独立証明ではない。land verifier bytes は署名対象に含めない。」

7. **real — plan の「受理追加なし」は raw receipt 集合については文字どおり成立しない。**

   - 該当: `s2-plan.md:15-31`、特に `23-26`
   - 現行 land は exact v5 のみを受理する (`dev_wave_land.py:94-130,775-785,960-1004`)。提案後は新しい v6 bytes を受理し、v5 を拒否するため、raw byte 集合は単純な部分集合ではなく置換になる。ただし証拠意味論で unsigned-v5 を signed-v6 に置き換えることは関門の弱体化ではない。
   - 成果物への影響: 変異台帳へ「受理集合は純粋に縮小」と書くと schema migration の新規受理を隠す。
   - 逐語の修正案: 「raw receipt byte 集合は exact v5 から exact signed-v6 へ置換されるため、集合論上の単純な縮小ではない。正規化した証拠意味論では unsigned receipt を除外し、署名・context 束縛を満たす receipt だけへ狭めるため、正しさゲートの緩和ではない。」

8. **refuted — unsigned-v5 正例の期待値更新は関門弱体化ではない。**

   - 該当: `s2-plan.md:230-241`
   - 既存正例が固定しているのは現行 exact-v5 契約であり、D906 は unsigned receipt の拒否を明示する。署名済み production fixture へ更新することは正当な契約更新であり、skip・xfail・optional fallback・module 名 bypass にする場合だけ弱体化になる。
   - 成果物への影響: fixture 更新を禁止し続けると署名必須化はできず、逆に fallback で緑を維持すると certified 選択が unsigned receipt を受理し続ける。
   - 逐語の修正案: 「既存 unsigned-v5 正例は、署名済み production-v6 fixture を通す正例と unsigned-v5 を拒否する負例へ更新する。この期待値変更は D906 による契約更新であり、旧入力を通す互換 bypass は設けない。」

9. **real — brief の「既存 schema 版上げと同じ影響範囲」という一般化は支持できない。**

   - 該当: `s1-brief.md:74-75`、`s2-plan.md:15-24,230-241,300-315`
   - 必須化で塞がるのは、(a) 全 unsigned-v5 receipt、(b) unsigned-v5 を作る既存正例、(c) generation の無い legacy lease の `acquired` / `held-self`、(d) `held` / legacy `queued` の `unclaimed=True` 発行、(e) issuer/key 未配置時の全発行、(f) 旧 waiter で既に走行中の wave である。過去 receipt の拒否だけではない。
   - 成果物への影響: 稼働中 wave の land と新規 receipt 発行が同時に止まり、計画上の受理集合が想定より大きく空になる。
   - 逐語の修正案: 「影響は過去 v5 receipt の拒否に限らない。legacy lease、`held`/`queued` の非保持走行、旧 waiter の稼働中 wave、issuer/key 未配置期間も停止するため、従来の schema 版上げと同じ範囲とはみなさない。」

10. **real — `held` / `queued` の receipt 廃止は D662 と衝突する過剰拒否であり、段 4 の裁定事項である。**

   - 該当: `s2-plan.md:18`。現行は `dev_wave_wait.py:370-374,2883-2911,3907-4004` で疑似 holder を作り、lease 再確認を省略して receipt を発行する。runbook は `docs/pegasus-runbook.md:1042-1047,1122-1128,1172-1176,1206-1216` で、`held` でも待たず投入し他 wave の land を止めないことを D662 の意図としている。
   - 実 generation を持たない走行に D906 の世代を署名できないため、両裁定は現状のままでは両立しない。「追加拒否だから可」だけでは D662 を上書きできない。
   - 成果物への影響: `held` 走行はテストを完了しても receipt を得られず land 不能となり、D662 が廃止した全体停止が実質的に再発する。
   - 逐語の修正案: 「`held` / legacy `queued` の `unclaimed=True` receipt 廃止は D662 の非待機受入契約を変更する。D906 の実 lease generation 必須化と両立しないため、段 4 で『D662 を改訂して非保持走行を land 不可とする』か『D906 を満たす別の世代意味論を裁定する』かを選ぶ。本 wave 内で暗黙に前者を採らない。」

11. **real — 段 7 に必要な「実装した」と「効いている」の択一別逐語が plan に無い。**

   - 該当: `s2-plan.md:238-241,300-315`
   - 成果物への影響: groundwork だけでも「外部署名主体を実装した」と記録されれば、後続 wave が production enforcement 済みとして receipt を正しさ根拠に使う。
   - 逐語の修正案（groundwork の場合）: 「【機構追加・未強制】署名検証・issuer reference・lease generation の実装部品を追加したが、production land の署名必須化と operational issuer/key の配置は完了していない。これらの部品は現在の着地関門では効いておらず、unsigned-v5 receipt による既存受理を置換していない。D906 の enforcement 完了とは数えず、着地受領証を根拠にした正しさ主張は D1197 に従い未閉鎖である。」
   - 逐語の修正案（必須化の場合）: 「【署名必須化・稼働 wave 影響あり】production land は unsigned-v5、署名不正、context 不一致を拒否する。旧 waiter が発行済みまたは発行中の v5 receipt は land に使えず、更新後の待ち手と配置済み issuer/key による受入再走が必要である。これは署名と context 束縛が効いていることを意味するが、issuer trust root、bootstrap、completion 自己申告、判定の意味的正しさまで閉じたことを意味しない。着地受領証を根拠にした正しさ主張全体は未閉鎖として残す。」

## 未閉鎖の確定版

段 7 では、上記所見 11 の択一別冒頭文に続けて、次をそのまま記録できる。

- 「署名が証明するのは、設定された公開鍵に対応する秘密鍵による canonical payload の承認と署名後の非改変である。特定の issuer 実装の実行、再導出手順の実施、payload の意味的正しさは証明しない。」

- 「鍵と issuer を repo 外へ置くことは OS 上の主体分離ではない。同一 uid の process は鍵の read・issuer の観測や変更を行いうる。hook が抑止するのは信頼済み PreToolUse が観測した一部の直接書込み面だけであり、認証防壁ではない。」

- 「親の起動点は引き続き tip 側 waiter を直接起動する。改変された起動側が issuer 呼出しを省略する可能性は、issuer 単体の設計では閉じない。」

- 「issuer の code/key/toolchain を真正とみなす trust root は別途必要である。PATH、symlink、`python3`、`git`、cwd、repo 内 reference と repo 外 operational copy の bytes 同一性および実行実在は receipt から独立検証されない。」

- 「issuer の初回配置と更新は、新機構自身でその配置を承認できない bootstrap 例外である。定常時の署名検証を、導入・更新期間にも無条件で成立する保証として扱わない。」

- 「completion protocol の `pre_fingerprint`、`post_fingerprint`、`env_projection`、`effective_scheduler`、checker 結果、red/flake nodeid は、内容と供給元の実行実在について waiter の自己申告性を残す。構造的整形式性と署名は、この意味的真正性を閉じない。」

- 「署名対象には main/tip の識別子、`runner_executed_sha256`、red checker の `checker_content_sha256`、`lease_generation`、`verdict` を含める。`checker_content_sha256` は期待 content hash であって実行 bytes の独立証明ではなく、`child-green` では checker は実行されない。land verifier と operational issuer 自身の bytes は署名対象に含まれない。」

- 「`child-green` は issuer が起動した launcher の `child_rc == 0` 観測と構造的に結合するが、実行された test selection・import closure・環境全体の意味的正しさまでは証明しない。`non-attributable-only` の意味的正しさは checker completion の自己申告に依存する。」

- 「署名済み context 束縛は別 wave・別 main・別 tip・別 lease acquisition への再利用を拒否する。同一 context 内の single-use は保証せず、外部 consume ledger は本 wave の scope 外である。」

- 「bounded/dispatch の内側で pathname 実行のまま残る層、および land verifier 自身が候補コードである T-696 の協調境界は、本 wave では閉じない。追加実装は行わず、残余として記録する。」

- 「`held` / legacy `queued` の非保持走行を receipt 発行不能にする変更は D662 と衝突しており、裁定が確定するまで解決済みと数えない。」

- 「本検証は静的検査であり、pytest は実行していない。テスト緑、production signed-v6 receipt の実在、operational issuer/key の配置完了は証明していない。」

## 親 brief への反論

- `parent-findings.md:27` の「receipt は issuer を通らないと作れない」は支持できない。検証できるのは configured key の署名であり、特定 issuer process の通過ではない。

- `parent-findings.md:26-27` の「repo の外の別主体」は支持できない。repo 外 path は別の OS 主体を意味せず、同一 uid のままである。書けるのは「repo 外 path に operational copy/key を配置した」までである。

- `parent-findings.md:33-37` の既存 v5 receipt は、新しい署名述語の D431 positive control 素材にはならない。production signed-v6 receipt を実発行して取得するまでは positive control は unmet である。

- `s1-brief.md:70-73` の「issuer へ起動権を移せば本 wave の bootstrap 死を回避できる」は、事前配置済み operational issuer/key がある場合に限る。本 wave 自身だけでの受入成立へ一般化できない。

- `s1-brief.md:74-75` の「既存 schema 版上げと同じ範囲」は支持できない。今回は過去 receipt に加え、legacy lease、`held` 非保持走行、旧 waiter の稼働 wave、issuer/key 未配置期間まで停止する。

- hook が現在の repo 外 issuer path を防護しないという `parent-findings.md:3-24`、および現行 v5 に generation/replay field が無いという `58-68` は、投影資料とコードから支持できる。

## 総括

最重は、署名を「issuer process を通った」「verdict が正しい」の証明へ格上げしてはならない点である。  
次に重いのは、`held` の receipt 廃止が D662 の非待機受入契約と正面衝突する点で、段 4 の裁定が必要である。  
段 4 は、(1) 人手 bootstrap・既存テスト更新後に必須化するか、(2) groundwork のみにして enforcement を後続へ送るかを選ぶ必要がある。  
必須化を選ぶ場合は、D662 改訂の可否も同時に裁定しなければならない。  
「検査器」は red checker と読むのが妥当だが、その content hash と実行実在は区別して記録する。  
どちらの択一でも「着地受領証を根拠にした正しさが閉じた」とは記録しない。