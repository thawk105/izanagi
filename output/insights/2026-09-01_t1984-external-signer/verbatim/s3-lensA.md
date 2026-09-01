## 所見

静的検査のみ。pytest・live hook probe・署名実走はしていない。

1. **refuted / 署名 field の存在だけで通る・receipt が鍵を運ぶ・改竄 field が canonical 対象外、という恒真化は段 2 の設計にはない。** `s2-plan.md:20,23-25,265-289` は、固定外部公開鍵、exact v6 field set、`issuer_signature` 以外の全 root field の canonical 署名、独立 literal の期待値を要求している。署名なし・鍵違い・field 改竄も実在 signed fixture があれば生成可能。  
   **成果物への影響:** 設計どおりなら land の受理集合は現行 v5 の真部分集合になり、certified report・台帳が unsigned receipt を根拠にする経路は増えない。  
   **提案:** 実装レビューでは `issuer_key_id` を receipt 指定 path として使わせず、固定 trust record の ID と等値比較することを確認する。

2. **real / production positive control は人手 issuer が実在するまで作れない。** 現行 launcher は unsigned v5 の27 fieldだけを生成する (`tools/acceptance_launcher.py:477-528`)。段 2 自身も、現物 v5 や test key の後付け署名は D431 control にならず、人手配置後の実 acceptance で signed v6 を取得する必要があると認める (`s2-plan.md:247-265`)。  
   **成果物への影響:** test key だけで緑にすると、production trust root が壊れていても certified acceptance の検査結果が緑になりうる。  
   **提案:** groundwork 段階では D431 を `unmet` と記録し、production signed fixture 取得前に「署名検証実装済・充足」と書かない。

3. **real / 段 2 の「再送」負例は context mismatch だけで、同一 generation 内の exact replay を赤にしない。** `s2-plan.md:153-165,289,311` は別 generation / tip への再送だけを拒否し、same generation・same request の single-use は外部 consume state が必要として未確定にしている。現行 land は lock を `tools/dev_wave_land.py:5564-5565` で解放した後、CLI が lease を release するのは `5661-5700` なので、その窓では同じ receipt の並行再提出も生成可能である。これは brief S3 の「再送は拒否」(`s1-brief.md:38`) を満たさない。  
   **成果物への影響:** main は2回進まなくても、同じ署名を使った複数の `already-landed` 成功・報告・台帳参照を作れる。  
   **提案:** scope 外の consume ledger を直ちに足さず、段 4 の裁定パッケージとして「D906 の再送防止は lease acquisition 間だけか、exact single-use までか」を確定する。後者なら現プランは未完。

4. **real / 古い land consumer による関門迂回が残る。最重要所見。** land は main copy に pin されていない。実行 copy の root は `__file__` 由来 (`tools/dev_wave_land.py:33-44`) で、検査するのは cwd が exact wave worktree であることだけ (`1276-1291`)。その実行 copy 内の verifier が `5074-5081` で receipt を検査し、そのまま `5531-5535` で main を更新する。したがって pre-v6 の land blobを wave側から起動すれば、新署名 verifier 自体を通らない。段 2 の `dev_wave_land.py` 改修 (`s2-plan.md:24-26`) はこの consumer downgrade を閉じていない。  
   **成果物への影響:** main、land 結果、後続 certified report・台帳の受理集合に、旧 v5 land が受理する unsigned receipt が残る。新関門は不可避な関門にならない。  
   **提案:** 本 wave では「署名必須化で閉じた」と書かない。main/external 起点で consumer bytes を固定する activation 境界は scope 拡張になるため、段 4 の裁定パッケージ候補にする。

5. **refuted / issuer を呼びつつ main・tip・runner・checker 等を単純差替えする経路は、段 2 の設計どおりなら残らない。** issuer は main launcher を自選し、live lease、Git object、実行 bytes、log、exact argv を再導出する (`s2-plan.md:19-22,169-185`)。一方、fingerprint・scheduler・checker結果等の自己申告性は残る (`187-211`) が、段 2 はこれを閉じたと主張していない。  
   **成果物への影響:** 独立再導出 field の差替えでは signed acceptance を増やせないが、自己申告 field の意味的正しさは certified report に残る未閉鎖である。  
   **提案:** issuer 通過と判定内容の真正性を同一視せず、既記載の未閉鎖を維持する。

6. **real / brief P4 の bootstrap 死の診断は正しい。** waiter は main に launcher があれば必ず main blobを選ぶ (`tools/dev_wave_wait.py:2558-2596`)。tip waiter がその source を直接起動する (`3783-3812`)。launcher は source を `tested-main` / `tested-tip-bootstrap` に限定し (`tools/acceptance_launcher.py:23-28,161-171`)、生成物は unsigned v5 (`495-528`)。tip の land だけを v6 必須にすれば自己拒否する。  
   **成果物への影響:** 回避なしでは本 wave の main 更新はゼロで、成果物は未着地のままになる。  
   **提案:** launcher 内で署名せず、外部 issuer が旧 main v5 を検査してv6へ包む構成を維持する。

7. **refuted / 段 2 の bootstrap 回避策が関門を弱める、または機能しない、という欠陥はない。ただし人手配置が前提。** issuer が main v5 の生成後に署名し、exit 0 後だけ publish する案 (`s2-plan.md:19-22,51-58`) なら unsigned fallback は不要である。鍵・issuer が無い場合は通すのではなく発行不能になる (`20`)。  
   **成果物への影響:** 人手 bootstrap 済みなら unsigned receipt は受理集合へ入らず、本 wave 自身の signed receipt を発行できる。未配置なら受理集合は空になる。  
   **提案:** human bootstrap と activation を同一の完了条件に混ぜず、未配置中は production 配線を切り替えない。

8. **real / P5「既存 schema 版上げと同じ範囲」は refuted。量は通常経路を使う稼働中 wave 全て、ユーザー前提で少なくとも6本。** v6 fallbackなし (`s2-plan.md:24-25`) なら既存 v5 receipt は全て無効になる。さらに変更後 main を取り込んだ旧 waiter は merge commit を作った後 (`tools/dev_wave_wait.py:3685-3726`)、実行中 waiter bytes と新 tip bytes の不一致で restart を要求する (`2195-2274,3761-3766`)。外部鍵が未配置なら再走しても v6 を発行できない。これは schema 再発行だけでなく、restart・人手 trust root・lease generation 移行を伴う。  
   **成果物への影響:** cooperative な ≥6 wave の着地受理集合は鍵配置まで空になり、旧 receipt を参照する報告・台帳は更新不能になる。ただし所見4の旧 land bypass があるため「どの経路でも1本も land できない」という絶対命題は偽。  
   **提案:** 回復手順は、人手 issuer/key 配置 → 各 wave が main を取り込む → 更新 waiter で再起動 → signed v6 acceptance 再走 → 新 land 実行。旧 receipt の救済 fallback は置かない。

9. **real / `test_dev_wave_land.py` 編集禁止と署名必須化は両立しない、という段 2 の blocker は妥当。ただし直接検証は射影制約上できていない。** 射影された `s2-plan.md:232-241` は unsigned-v5 fixture と多数の `land()` 正例を具体的行番号付きで報告し、現 production `land()` も v5 exact schema を受理する (`tools/dev_wave_land.py:94-130,934-1160`)。対象 test file 自体は今回の許可資料に含まれず、行番号を独立再読してはいない。  
   **成果物への影響:** 必須化だけ行えば全走が赤になり、certification を緑として発行できない。  
   **提案:** optional署名・v5 fallback・test名 bypassは使わず、競合解消後の activation wave でfixtureを更新する。

10. **real / AI が鍵を生成してから hook で将来の書込みを拒否しても D906 を満たさない。** D906 は鍵と発行権限を最初から AI writable 領域外に置く (`rulings-verbatim.md:1-14`)。現 hook は対象 external root を守らず、通常経路では許可する (`hooks/guard_write.py:216-288`; `hooks/guard_bash.py:2231-2238,2528-2529`)。対象を追加しても script・変数展開・MCP・persistent shell等は開く (`hooks/README.md:112-115,297-304,351-364`)。生成時点でAIが秘密を支配した事実は後付けhookでは消えない。  
    **成果物への影響:** AI生成鍵で署名した receipt を genuine external authority と数えると、候補が任意 receipt を発行でき、certified report・台帳の受理集合は署名前と実質同じになる。  
    **提案:** コード・reference issuer は「実装済」と書けるが、外部 authority は人手儀式まで「未実装／未閉鎖」とする。

11. **real / D906 の「検査器 bytes」の意味が未裁定で、段 2 は red checker だけを候補にしている。** `s2-plan.md:120-127,310` は `checker_content_sha256` を `check_acceptance_reds.py` と解釈する一方、land verifier bytesなら field が無いと認めている。  
    **成果物への影響:** 「検査器」が land verifier を指すなら、その改変は署名対象外となり、同じ署名の受理集合を verifier変更で拡張できる。  
    **提案:** 新規一般 gate を足さず、段 4 の裁定パッケージとして語義を確定する。確定前は D906 完了と書かない。

## 択一の推奨

**(b) 本 wave は機構を実装するが必須化はせず、必須化を後続 waveへ送り、間は未閉鎖と明記する。**

ここでいう「必須化しない」は、v6をoptionalにしたりv5 fallbackを新設したりする意味ではない。production の現行 v5経路は変更せず、lease generation、canonical署名 module、reference issuer、固定trust-root loader、4方向検査のうち実装可能な groundworkだけを作る。人手鍵儀式、test fixture競合解消、再送意味の裁定、consumer downgradeの扱いが揃った後続 activation wave で、waiterとlandを一度にv6-onlyへ切り替える。

(a) は人手鍵と既存 test 正例を欠く現在の状態では完了不能。(c) は実装可能な部分まで止め、D1197の実装命令に反する。(b) が実装量を最大化しつつ、規律2違反のfallbackを作らない線である。

## 親 brief への反論

- **P4 の回避理由:** 「issuerへ移せば本 wave tip の署名実装が走る」(`s1-brief.md:70-73`) は因果が誤っている。実際の回避は、repo外の operational issuer が旧 main launcher のv5を後段署名するから成立する。issuer本体はtip copyではない。
- **P5:** 「schema版上げの既存前例と同じ範囲」(`s1-brief.md:74-75`) は支持できない。今回は人手trust root、waiter restart、lease generation、外部process配線が増え、少なくとも6本すべての通常landへ波及する。
- **§6 item 1:** 「鍵生成と設置はAIが起動したprocessで行う」(`s1-brief.md:79`) はD906と両立しない。これは単なる未閉鎖ではなく、外部発行権限の成立条件を満たさない。
- **親実測1の一般化:** 対象の新規 external authority pathが現hookで無防護、という結論は正しい。ただし「repo外絶対pathは1つも防護されない」は厳密には過大で、hooks fileの既存hardlink aliasはrepo外でもinode照合で拒否される (`hooks/guard_write.py:121-130,155-171`; `hooks/guard_bash.py:2246-2303`)。本件のfresh authority pathには影響しない。
- P2とP3は支持する。issuer後段化でも待ち手自己申告fieldは残り、現v5に排他世代が無いこともコードと整合する。

## 総括

最重所見は、署名を検証しない旧 `dev_wave_land.py` を実行でき、新関門全体を迂回できることである。  
段 2 のcanonical署名・固定鍵・署名なし／鍵違い／改竄の負例設計自体は恒真ではない。  
ただし再送負例は別generationへのcontext mismatchに留まり、same-generation exact replayを閉じない。  
bootstrap回避は外部issuerの人手事前配置後なら成立し、unsigned fallbackを必要としない。  
通常経路では稼働中≥6 waveすべてがrestartとsigned acceptance再走を要し、P5はrefuted。  
親は段4で **(b)** を採り、groundworkを最大限実装しつつ、activationまで未閉鎖と明記すべきである。