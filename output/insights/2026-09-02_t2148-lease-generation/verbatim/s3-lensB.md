## 所見

1. **対象:** `plan.md:3-8`、`d1449.md:3-5`、`d906.md:3-5`。**何が問題か:** 計画は「同じ wave・main でも再取得ごとに別値」を先に判定基準へ置き、未裁定のはずの世代粒度を取得単位に決めている。D906 は署名対象へ世代を含めることを求めるが、その粒度までは決めていない。この前提で C4、C5 を不可とするのは循環している。**裁定にどう効くか:** wave、main、lease directory 単位を比較前に落とし、裁定者の選択肢を狭める。**性質:** real。決定文と計画の直接比較である。

2. **対象:** `plan.md:10-32`。**何が問題か:** 「17 件で網羅」とするが repository 内台帳、wave 単位、main の進み単位、lease directory 単位がない。また C7 の時刻と counter、C8 と C15 の乱数と counter、C13 の current producer と外部主体は、費用と信頼性が異なるのに同じ候補へまとめられている。**裁定にどう効くか:** 追加 4 候補が比較されず、既存候補も候補別費用を出せない。「17×7」の母集団も確定していない。**性質:** real。列挙表と指定された軸の照合結果である。

3. **対象:** `plan.md:61-69,505-529`、`brief.md:62-64`。**何が問題か:** 移行窓を具体化しているのは payload 追加だけで、候補ごとの「影響 wave 数」と「回復時間」がない。少なくとも P 類は共有 directory に来る全旧 waiter、R 類は旧 reader が別の固定 lease を取得する fail-open、S/H/O 類は旧 helper に関して baseline、という異なる費用になる。絶対 wave 数には rollout 時の旧版稼働数も必要である。**裁定にどう効くか:** 停止と排他破壊という質の異なるリスクを比較できない。**性質:** 費用欄の欠落は real。実際の影響 wave 数は未観測であり、現時点では推測不能である。

4. **対象:** `plan.md:19-28,65,215,526-527`。**何が問題か:** 定常費用が候補別に測定されない。sidecar、hardlink 名、companion directory、repository 内外の台帳は残留・掃除主体・次の取得との対応が必要だが、xattr は固定 lease の unlink とともに消える。複数 object を使う候補には「lease 作成後、世代記録前に停止」などの不完全更新窓もある。**裁定にどう効くか:** D4 型の「移行費用 0、定常費用あり」と、xattr や導出値の「掃除不要」を比較できない。**性質:** 残留と測定欠落は real。crash 時の誤対応は設計からの推論で、実測されていない。

5. **対象:** `plan.md:14-30,347-415`。**何が問題か:** 時刻、整数 counter、inode tuple などを、署名 schema が要求する 64 桁の小文字 SHA-256 形式へ変換する規約がない。Command 4 は `"0" * 64` の pass-through だけで、各候補の変換を測らない。**裁定にどう効くか:** 候補が schema を通るか、issuer と lander が同じ bytes を再構成できるかを比較できない。**性質:** real。`acceptance_receipt_signature.py:185,212,351` と計画の入力値の照合結果である。

6. **対象:** `plan.md:59-69,475-503,574-580`。**何が問題か:** 「119 coverage cell」は測定数ではなく、主に等価類へまとめた予測である。acceptance 実走は payload 追加だけ、lander は extra lease field と extra receipt field だけ、issuer は caller-supplied 値だけで、C8、C10、C12-C15 の generation source を consumer まで結んでいない。22 個の既存テストも候補別試験ではない。**裁定にどう効くか:** fail-open、fail-closed、不可視の候補を棄却する材料にはなるが、残った候補から 1 つを採用する材料にはならない。**性質:** real。command と coverage 表の対応から確認できる。

7. **対象:** `plan.md:71-281`。**何が問題か:** probe の観測項目にも穴がある。外部台帳は `directory` の sibling に書く一方、出力は `directory.rglob("*")` だけなので台帳を記録しない。xattr は `setxattr` するだけで値や renew 前後を読まない。C14 は `getattr(st, "st_birthtime", None)` だけで、取得不能時に真の btime を得る代替がない。sidecar 残留後の次回取得も実走しない。**裁定にどう効くか:** C13-C15 の実行可能性と定常費用が、計画どおり実走しても埋まらない。**性質:** real。probe コードが出力する値から判定できる。

8. **対象:** `brief.md:89-91`、`premeasure.md:71-81`、`plan.md:533-535`。**何が問題か:** 1 つ目の P1 は未成立である。親が実走したのは `wave_land_window` の claim/release/status までで、`dev_wave_wait` acceptance と `dev_wave_land` は未実走である。計画自身もこれを認める。**裁定にどう効くか:** helper の `unavailable` から acceptance 全体の終了状態や lander の停止まで一般化できない。Command 3 は payload 候補についてだけ、この穴を部分的に閉じる。**性質:** real。親資料自身に未実走と明記されている。

9. **対象:** `brief.md:53-64`、`plan.md:507-515,537-544`、`tools/wave_land_window.py:152-160,383-425,433-493,499-545`。**何が問題か:** 「2400 秒間固まり、その後回復」という表現は正確でない。stale は最後の mtime 更新から 2400 秒超であり、新実装が renew すれば旧 reader の停止は無期限になり得る。新実装が release すれば即時回復し得る一方、旧実装による invalid payload の release は stale 後も `unavailable` である。また lander は renew の失敗だけでは停止しない。**裁定にどう効くか:** payload 追加の移行費用を固定 2400 秒として比較すると過小評価または過大評価になる。**性質:** code 上の分岐は real。新 writer が renew するかは未決定実装に依存する推論である。

10. **対象:** `plan.md:347-415,524-527,580`。**何が問題か:** 最終候補で必要な「外部主体が live lease identity から世代を取得する」「lander が独立に同じ世代を得る」という経路がない。Command 4 は同じ変数を issuer と verifier の expected 値へ渡す機能試験である。計画自身も C8、C13-C15 は operational evidence 不足、production lander は signed-v6 未接続と認めている。**裁定にどう効くか:** shortlist は作れても、D906 を満たす候補の積極採用は裁定できない。**性質:** real。計画の明記と現行呼出し関係の照合結果である。

## 候補集合への追加

少なくとも次の 4 候補を追加する必要がある。

| ID | 候補 | 64 桁形式への変換 | 移行窓 | 定常費用と弱点 |
|---|---|---|---|---|
| A1 | repository 内台帳へ取得ごとの乱数または counter を記録 | 32 byte 乱数は直接 lowercase hex。counter は domain-separated canonical bytes を SHA-256 | tracked/untracked な worktree file なら旧 waiter の clean-tree preflight を壊す。ignored file や git common dir なら別途実測が必要 | locking、原子更新、prune、複数 worktree の合流が必要。AI 書込み可能なら D906 不可 |
| A2 | wave 単位。`lease_holder` または wave identity から導出 | `sha256("wave-generation\\0" + identity)` | payload 無変更なので旧 lease consumer は baseline、回復待ちなし | 掃除不要。ただし同一 wave の再取得を区別せず、holder の 48 bit 衝突余地も増えない |
| A3 | main の進み単位。`main_sha` から導出 | `sha256("main-generation\\0" + main_sha)` | payload 無変更なので旧 consumer は baseline | 掃除不要。同じ main 上の全 wave・全再取得が同値で、既存 `tested_main` の再符号化になる |
| A4 | lease directory 単位。開いた directory の `st_dev/st_ino` または固定 directory identity から導出 | tuple を固定幅、domain-separated encoding にして SHA-256 | file payload 無変更なら旧 consumer は baseline | directory 再作成・移動・device 変更の意味を決める必要がある。同じ directory 内の再取得は区別しない |

既存候補の形式変換も明記すべきである。C1/C6/C8/C13/C15/C17 の 256 bit 乱数は直接 64 桁 hex、C2/C3/C7/C13/C15 の時刻・counter と C14 の metadata tuple は canonical encoding 後の SHA-256、C5 は hash algorithm と domain separation を固定する。C9-C12 は同じ 64 桁値を file/directory 名へ符号化する。費用は小さい hash 1 回と最大 64 文字の保存だが、hash は時計衝突、counter 永続化、inode 再利用、writer の信頼性を改善しない。

mtime は C14 で明示的に触れられており、追加候補には数えなかった。live mtime は renew ごとに変わるため、取得中に安定する世代としては棄却できる。

## file:line の照合結果

不一致は 4 件ある。

1. `premeasure.md:29-30` は fixed lease 不在の status 分岐を `tools/wave_land_window.py:565-566` とするが、実体は `:567-568`。
2. `premeasure.md:57-59` は claim が `os.listdir` で固定名を見るとするが、claim は `tools/wave_land_window.py:367-381` で固定名を直接 open/create する。`os.listdir` は renew の `:440-446` と status の `:562-568`。
3. `premeasure.md:77-79` の `tools/dev_wave_land.py:5628-5646,5689-5710` は renew/release state の収集範囲であり、「land を続行」と「stderr へ印字」を直接支える行はそれぞれ `:5650` と `:5712-5720`。
4. `plan.md:40` の「status だけが directory listing」は誤り。renew も `tools/wave_land_window.py:440-446` で listing を使う。計画後半の `plan.md:562` は正しいが、前半と矛盾する。

次は実体と一致した。

- `brief.md:16-26` の lease parser、open、claim、signature slot、waiter state の参照。
- `premeasure.md:66,73,80` の renew test、waiter state、signature schema の参照。
- `plan.md:8,14,27,29,38-39,41-46,503,511,513,515,517,535,537,548,568-571` の各参照。なお「production waiter/lander は reference issuer を呼ばない」「既存 test は `issue_signed_receipt` の full path を呼ばない」も検索結果と一致した。
- 親実測の extra field 名は `generation`、追試案は `lease_generation` だが、現行 parser の strict field-set rejection を確認する限り両者は等価である。

## 裁定の形

計画どおり実走した場合、裁定者はまず「取得ごと、wave ごと、main の進みごと、lease directory ごと」のどれを世代と呼ぶかを選び、その後に、payload 追加の旧 waiter fail-closed、fixed filename/directory 置換の fail-open、companion・台帳の移行互換性と残留管理、metadata・既存 field 導出の無状態性と再利用弱点、外部 writer の信頼境界を比較することになる。ただし現計画には粒度 3 種と repository 内台帳、候補別の影響 wave 数・回復時間・掃除費用、64 桁変換規約、sidecar/ledger の crash 整合性、外部 issuer と lander が同じ live lease identity を独立観測する実測がないため、棄却と shortlist まではできても最終採用は選べない。

## 総括

- 所見: 10 件。
- 追加候補: 4 件。
- file:line 不一致: 4 件。
- 1 つ目の P1 は未成立。Command 3 で payload 候補について部分的に追試できる。
- 2 つ目の P1 も未成立。計画は brief より広いが、指定された粒度と repository 内台帳を尽くしていない。
- この材料だけでは最終的な世代意味論を裁定できない。候補の分割、候補別の移行・定常費用、probe の観測穴の修正、外部 authority から signed-v6 lander までの独立した世代照合が必要である。
- 本点検では source/test を静的に読んだだけで、テストおよび probe は実走していない。