### A1 B の登録前の窓と、論文に書く文が一致しない

重大度: **must-fix**
根拠: `plan2.md:17,30,194-196`、`s1-brief.md:5,31`、`cicada-certified-evidence-design/README.md:60,159`。
放置すると: 版を選んでから read set に登録するまでに回収・再利用された読みも、「生存中の tx が読んだ版を全 tx で照合した」という一次資料の文では検査済みに見える。
推奨対処: 登録前の窓を閉じる設計と正例を加えるか、主張を「read set 登録後から tx 終了まで」に明確に狭める。後者では依頼の元の文言を達成したと扱わない。

### A2 世代番号の読み方だけでは並行する変更との順序が未確定

重大度: **must-fix**
根拠: `plan2.md:28-30`。
放置すると: 世代増分、wts の書換え、切離し・返却の順序次第で、異なる版の wts を安定した世代と組にして偽の緑にするか、有効な読みを偽の違反にする。plan 自身が線形化点を実装時へ残している。
推奨対処: 各変更 site と登録・終了照合の順序を先に仕様化し、並行して変更した場合の許容結果を列挙する。`Version::set()` が世代を戻さないことだけでなく、再利用時の wts 更新を挟む観測も検証する。

### A3 U の「公開記録」は公開 store より前に作られる

重大度: **must-fix**
根拠: `plan2.md:40-46`、`instr-cicada-trace.patch:69-96`、`cicada-forwarding-variant.patch:215-220`、`cicada-forwarding-gc.patch:402-408`。
放置すると: 記録後に committed store を飛ばす壊れ方では、公開していない版と W 行が一致し、U が偽の緑になる。W 行自身も write set と tx wts から作られるため、独立した公開観測にはならない。
推奨対処: store の実行後に status を確認して公開記録を確定し、設置記録・公開記録・実際に emit した W 行の三者を照合する。forwarding が未設置版の wts を更新するので、設置時と公開時の wts を混同しない。

### A4 read API 照合には発火を示す正例がない

重大度: **must-fix**
根拠: `plan2.md:50-58,128,130-136,172-177`、`cicada-certified-evidence-design/README.md:64-71`。
放置すると: `api_checked>0` は一部の呼び出しを数えたことしか示さず、forwarding が変える read 経路の登録漏れや、登録漏れと余分な登録の相殺を拒否できる証拠にならない。旧壊し三本の目的は巡回検出である。
推奨対処: 外部 read の登録漏れ、余分な登録、再読または own-write の誤対応を少なくとも対象分岐ごとに発火させ、呼び出し単位の key・body・要素対応に帰属させる。追加の壊しが所有範囲を超えるなら、未検証面として裁定へ戻す。

### A5 stock の壊し B は、待機と下限変更だけでは回収事象に帰属しない

重大度: **must-fix**
根拠: `plan2.md:94-104,168,174-175`、`s1-brief.md:17,28-29`、`ruling-D2295.md:10-17`、`cicada-forwarding-gc.patch:480-492`。
放置すると: `reached/changed/committed>0` でも leader の境界更新、該当版の切離し、持ち主 thread の pool 返却・再利用が起きず、B の正例が未発火のままになる。逆に同じ版の違反だけでは、下限変更が原因だったと一意には言えない。
推奨対処: 生死確認で、壊した tx の既読版について境界更新→切離し→返却または再利用→B 違反の事象列を記録し、default と inline BEST を別々に成立確認する。到達しなければ plan 記載どおり site を再設計してから本走に進む。

### A6 TRACE=0 比較に E-max の実際の patch 列がない

重大度: **must-fix**
根拠: `plan2.md:114-120,124-128`、`s1-brief.md:19`、`launch_gcfix_run.py:447-478`。
放置すると: stock の `pin C` 対 `pin C + instr + M` が一致しても、E-max で使う `instr → variant → gc → target → M` に M を足した TRACE=0 命令列が同一とは言えず、その構成の性能値を結び付ける一次資料の根拠が欠ける。
推奨対処: 四 target・二 genome の比較に加え、E-max の同一 forwarding patch 列について **M なし対 M あり**を同じ compile command で比較する。

### A7 全 tx 照合の入力契約が総件数の正値に留まる

重大度: **should**
根拠: `plan2.md:64-71,156-181`、`s1-brief.md:32`。
放置すると: 一部の tx だけを照合しても `b_checked/u_published/api_checked>0` と違反 0 で合格でき、台帳には「全 tx」と残る。新設 field の到達性 probe は必要だが、被覆率の証明にはならない。
推奨対処: read-only、書く tx、abort の各母集団を入口側で独立に数え、照合済み件数と突き合わせる。各 cell で到達可能な要求値を生死確認してから合否述語を固定する。

## 総括

現行 plan はそのまま採用できない。B の並行時の順序と登録前の窓、U の公開後観測、read API の正例、壊し B の実際の回収列を先に確定する必要がある。TRACE=0 は E-max の実際の patch 列でも比較する。`plan2.md` は abort 照合、inline の返却・再取得、未実在 field の生死確認を明記しており、これらの方向は維持できる。静的検査では起動器の新設 field や壊しの到達は実証できないため、合否と一次資料の文は実走結果まで確定させない。判定器・campaign の実装を M の成果として記帳しない。