## 所見

1.  
   - **対象 (file:line):** `s2-plan.md:31-35,42-50`、`verbatim-decisions.md:128-153`
   - **何が問題か:** `"not-acquired"` の採用が D1528 越境だという疑いは成立しない。D1527 は非保持走行の値を本裁定内で定めるよう要求し、D1528 が延期したのは inode・xattr・sidecar 等、取得あり世代の導出方式である。
   - **裁定にどう効くか:** D1527/D1528 と整合する。成果物影響は、参照 signed-v6 の受理値域が SHA-256 だけから `SHA-256 | "not-acquired"` へ広がり、非保持 receipt の signed bytes が定義されること。
   - **性質 (real / refuted):** refuted
   - **推奨する扱い:** `"not-acquired"` は維持し、「取得あり世代の導出方式は未採用」と明記する。

2.  
   - **対象 (file:line):** `s2-plan.md:32,34`、`acceptance_receipt_signature.py:127-129,185,202-217`
   - **何が問題か:** 予約定数と serialized 値を `SHA-256 | marker` として検査する変更は、非保持値を既存 slot に載せるために必要であり、念のための gate ではない。
   - **裁定にどう効くか:** D1527 に直接必要で、field 集合を変えないため D1528/D1443 とも衝突しない。certified 選択・材料レポート・試行台帳には影響せず、reference signed-v6 の受理集合と非保持 receipt bytes だけが変わる。
   - **性質 (real / refuted):** refuted
   - **推奨する扱い:** `LEASE_NOT_ACQUIRED` と serialized union の検査だけを本題の最小実装として残す。

3.  
   - **対象 (file:line):** `s2-plan.md:32-33`、`brief.md:40-43`
   - **何が問題か:** 必須 `lease_acquired: bool`、真の `bool` 型検査、`(lease_acquired, lease_generation)` の矛盾拒否は、既に構文的に排他的な serialized 値へ第二の discriminator を重ねる新設 gate である。D1527 は別引数を要求していない。
   - **裁定にどう効くか:** D1499 の既定値回避は、既存の必須 `lease_generation` に marker を明示指定させるだけで満たせる。追加引数は旧 acquired call を新規拒否する一方、signed bytes・受理 receipt 集合・研究成果物の値を変えない。
   - **性質 (real / refuted):** real
   - **推奨する扱い:** P2 の必須状態引数と tuple helper を棄却し、既存 `lease_generation: str` に disjoint union を直接渡す。

4.  
   - **対象 (file:line):** `s2-plan.md:35`、`acceptance_receipt_signature.py:326-364`
   - **何が問題か:** verifier の `expected_lease_acquired` も不要である。現行の exact `payload["lease_generation"] == expected_lease_generation` は、marker と SHA-256 が非交差なら取得有無を既に区別する。
   - **裁定にどう効くか:** D1450 の異なる値への再送拒否は既存比較で維持できる。追加 bool は verifier API の受理 call を狭めるだけで、最終 receipt/context の受理集合、certified 結果、台帳値を変えない。
   - **性質 (real / refuted):** real
   - **推奨する扱い:** expected 側も serialized marker または SHA-256 を直接受け、既存の完全一致を維持する。

5.  
   - **対象 (file:line):** `s2-plan.md:36`、`acceptance_issuer_reference.py:2-41`
   - **何が問題か:** issuer の claims 表を取得あり・非保持に分け、どちらも live lease から独立に導出・検査しないと書く変更には問題がない。
   - **裁定にどう効くか:** D1527 の意味論を reference 境界へ反映し、D1443/D1499 が禁じる不可避な lease gate の主張を避けている。成果物の値は変えず、参照文書の保証範囲だけを正す。
   - **性質 (real / refuted):** refuted
   - **推奨する扱い:** この文書変更は残す。ただし「自己申告を検査した」と読める表現は避ける。

6.  
   - **対象 (file:line):** `s2-plan.md:37-38`、`acceptance_issuer_reference.py:436-464,513-528`
   - **何が問題か:** issuer API の marker 受理は必要だが、必須 bool と pair の早期検証は projection の同じ検査と重複する。projection/自己検証への状態転送も、追加 bool を採った場合だけ生じる機械的変更である。
   - **裁定にどう効くか:** marker を通す最小変更は reference issuer の受理集合を増やす。一方、重複検査と転送行には独立した成果物・受理集合への効果がなく nit、新しい例外層にもなる。
   - **性質 (real / refuted):** real
   - **推奨する扱い:** 現行 `lease_generation` の検査を serialized union へ広げるだけにし、pair gate と追加状態転送は入れない。

7.  
   - **対象 (file:line):** `s2-plan.md:39`、`acceptance_issuer_reference.py:550-579`、`verbatim-decisions.md:100-126`
   - **何が問題か:** required mutually-exclusive group と `--lease-not-acquired` は D1527 に必要ではない。既存の required `--lease-generation` へ `"not-acquired"` を明示指定すれば、欠落時の既定値は生じない。
   - **裁定にどう効くか:** D1499 との衝突は元々回避可能であり、group は reference CLI に別 spelling と conflict gate を追加する scope 膨張である。production 成果物は変わらず、reference CLI の入力受理集合だけが変わる。
   - **性質 (real / refuted):** real
   - **推奨する扱い:** group を棄却し、既存の required option 一つを維持する。

8.  
   - **対象 (file:line):** `brief.md:23-26,46`、`acceptance_issuer_reference.py:4-6,67-87,513-528,564-579`、`test_external_acceptance_signing.py:31-32`
   - **何が問題か:** repo 内の実呼出しは issuer 内部と当該テストだけで、waiter/lander への production 配線はない。ただし「この 2 file を import するのは test だけ」は字義どおりには誤りで、issuer が signature module を import している。また P4 は repo-wired lander には正しいが、module 自身が想定する repository-external operational copy まで不変とは言えない。
   - **裁定にどう効くか:** 新しい marker 受理形はテストと直接起動された reference CLI には到達可能だが、production acceptance、certified 選択、材料レポート、試行台帳には到達不能である。外部配置の有無は未測定。
   - **性質 (real / refuted):** real
   - **推奨する扱い:** 「repo 内の外部 caller は test のみ」「repo-wired production land の受理集合は不変」と限定し、production gate が実在するとは扱わない。

9.  
   - **対象 (file:line):** `s2-plan.md:58-72`、`test_external_acceptance_signing.py:214-232,284-340`
   - **何が問題か:** テスト案には冗長なものがある。既存 acquired の2正例は新機構を空にしても緑、acquired+marker 負例は bool 判定を無視しても旧 SHA 検査で赤になる。二つの交差 context 負例は既存 exact-equality/replay test と同じ分岐で、expected bool の整合検査を通らない。parser の missing/conflicting 負例も、変更が空でも現行 required/unknown-option 拒否により `SystemExit(2)` になり得る。
   - **裁定にどう効くか:** 実効なのは nonholding の署名正例、`False + SHA` 拒否、予約外文字列拒否、parser の nonholding 正例。ただし bool/CLI gate 自体を棄却すれば前二者以外の追加群も不要になる。新例外文言の exact assert は受理集合を変えない診断 pin なので nit。
   - **性質 (real / refuted):** real
   - **推奨する扱い:** 冗長 test を新 gate の証拠に数えない。marker の受理・署名対象包含・予約外拒否と acquired canonical bytes 不変に絞る。

10.  
   - **対象 (file:line):** `brief.md:21-46`、`README.md:94-128,203-219`、`dev_wave_wait.py:448-454,2895-2911,3906-4004`
   - **何が問題か:** P1 の非交差性、現行 SHA-only 値域、`unclaimed` の実在、非保持時に live 再確認を飛ばす構造は確認できる。P2 の「明示 bool が必要」は確認事実ではなく不要な設計選択。P3 の自己申告・exact equality という限定は正しい。全 branch/worktree の重複 0 と pin 閉包 0 は、指定資料に逐語出力がなく再現可能性までは確認できない。
   - **裁定にどう効くか:** probe 基準 commit と現行 commit の対象コードに差分はなく、非保持経路の一般化は妥当。ただし P2/P4 と全 worktree 閉包は、測れた repo 内 surface を越えて表現している。
   - **性質 (real / refuted):** real
   - **推奨する扱い:** P1/P3 と producer 実体は採用し、P2 は serialized union に縮め、P4 と閉包主張は観測範囲を明記する。

11.  
   - **対象 (file:line):** `s2-plan.md:31,35,82-86`、`verbatim-decisions.md:67-78,128-160`、`acceptance_receipt_signature.py:357-364`
   - **何が問題か:** plan は取得ごとの値を caller が再利用しないという契約にはするが、別取得で同じ64桁値を渡すことは拒否できない。したがって D1450 の実効保証は未完成である。ただし plan は導出・一意性強制を D1528 後の不確実性として明記しており、現 wave で達成したとは主張していない。
   - **裁定にどう効くか:** D1450 との整合は規範上・条件付きであり、実効再送防止ではない。現変更による certified 成果物や production 受理集合への影響はない。
   - **性質 (real / refuted):** refuted
   - **推奨する扱い:** blocker にはしないが、完了報告では「粒度契約と非保持値を確定、別取得一意性は D1528 後」と限定する。

## brief と plan が正しかった点

- 現行実装は `lease_generation` と expected 値の双方を64桁小文字 SHA-256 に限定し、caller 値を署名と自己検証へそのまま渡している。
- `"not-acquired"` は SHA-256 構文と交差せず、既存 `lease_generation` field のまま署名対象にできる。
- marker の採用は D1527 が要求する非保持値の確定であり、D1528 が延期した取得あり世代の導出方式選択ではない。
- marker は自己申告にすぎず、live lease 検査通過を意味しないという縮退は D1443/D1499 と整合する。
- production waiter/lander から signed-v6 issuer/verifier への repo 内配線は存在しない。
- acquired receipt の canonical length/hash、root field 集合、既存 replay 期待値を変更する必要はない。
- 非保持 producer の `unclaimed` と保持時だけの再確認分岐は現行コードに実在する。
- plan は pytest 未実走を正しく明記しており、既存期待値を書き換える提案も含んでいない。

## 総括

- 最も重い所見は、serialized marker だけで足りるところへ必須 bool、pair helper、verifier 状態引数、CLI mutually-exclusive group を重ねている scope 膨張である。
- `"not-acquired"` 自体は D1528 越境ではなく、D1527 を満たす本題の選択である。
- production 呼び手は repo 内に存在せず、新受理形が変えるのは reference API/CLI とテストの受理集合だけである。
- 親は実装後、marker の signed bytes、予約外拒否、acquired canonical bytes/hash 不変を実測すべきである。
- D1450 の別取得再送拒否は導出方式未採用のため依然として条件付きであり、完了扱いしてはならない。
- pytest は実行しておらず、本所見は静的検査のみである。