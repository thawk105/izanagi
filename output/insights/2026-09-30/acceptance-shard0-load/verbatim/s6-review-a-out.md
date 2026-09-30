## 所見

1. **must — join 超過時に構築中の木を削除できる。** `conftest.py:2614–2623` は生存 thread を検出して例外を投げた後も、`finally` で controller の `bases.close()` を呼ぶ。worker がすべて退出済みなら `test_s8b_oracle_driver.py:932–944` が session 木を削除する。例えば builder を 900 秒止め、最後の worker を先に終了させると、builder が保持する key flock と無関係にその足元の木が消える。再開した builder は書込みに失敗し、非 daemon thread が生き続ければ session の終了上限としても機能しない。**修正:** 生存 thread がある間は lifetime lock と写しを撤去しない終了手順を設ける。生存 thread がない通常例では、従来どおり join、error 回収、close、写しの cleanup の順で通す。

2. **must — thread 起動失敗時には 900 秒上限が適用されない。** `conftest.py:2595–2606` では 1 本目が起動して 2 本目の `start()` が失敗すると、1 本目を無期限に `join()` する。1 本目が builder 内で停止すれば configure_node 自体が戻らず、controller lock も解放されない。**修正:** 起動途中の失敗にも有限の終了手順を適用し、生存 thread の木を消さずに起動例外を報告する。1 本目が正常終了した後に 2 本目の起動が失敗する例では、lock を閉じて元の起動例外を返す。

3. **should — T6 は危険な cleanup を許したまま緑になる。** `test_s8b_oracle_driver.py:1373–1390` は builder を止めて timeout 例外だけを検査し、その後 thread を解放する。現在の実装では、その間に `close()` が木を消しても T6 は通り得る。**修正:** timeout 時点で session 木と lifetime lock が保持され、解放後に安全に撤去されることまで検査する。正常終了済み thread の例では即座に close できることも通す。

4. **should — T1 は controller から worker への公開を直接検査しない。** `test_s8b_oracle_driver.py:1283–1288` は consumer に controller と**同じ** `bases` object を注入する。worker が `_t080_join_shared_bases()` から同じ session path に参加して hit する経路は、この test 単体では未検査である。**修正:** 別 process の worker 相当参加者から 2 key を `get()` し、追加 build がないことを数える。controller 内の同一 object から hit する現行の正例も維持する。

5. **should — M3・M5・M6 の「期待 node だけが単一理由で赤」は未成立。** M3 は「thread 内へ移す」か「参加を外す」かで変異が未確定で、T1 の job 参照や T4 の close 検査も壊し得る（`conftest.py:2571–2574`、`test_s8b_oracle_driver.py:1276–1288, 1333–1337`）。M5 を単に分岐外へ移すと、非選択走では可視 job が無く `conftest.py:2572` の参照失敗で赤になり、不要な構築を検出した証拠にはならない。M6 は既存の `test_t080_shared_base_returns_independent_repos_and_documents` も赤にする（`test_s8b_oracle_driver.py:1433–1450`）。**修正:** M3 は controller の lifetime 参加だけを外す具体的な差分に固定し、M5 は可視 job を用意した非選択例で起動を観測するよう登録し直す。M6 は T7 と既存 copy 独立性 test の両方を期待 node に登録する。M1→T1、M2→T2、M4→T4 は静的には直接性がある。

6. **should — 写しの失敗後に worker が観測する結果は終了順で変わる。** prewarm は `result.json` の失敗・180 秒超過を error にする（`conftest.py:2576–2593`）。一方、worker の複製関数は写しの directory が消えると実 repo 複製へ進む（`test_s8b_oracle_driver.py:1015–1033`）。finish で写しが撤去された後に consumer が動ける異常終了順では、同じ失敗から worker 側の別経路が生じる。**修正:** producer または consumer が生きている間は写しを保持し、失敗を観測できるようにする。写し成功後に全利用者が終わった通常例では、最後に directory を撤去する。

## 反証できず

- 2 controller thread と worker が同じ key を `get()` する通常経路では、key flock が build と `complete.json` 公開を直列化する。marker 不在の残骸は次の取得者が削除して再構築する（`test_s8b_oracle_driver.py:946–973`）。
- 通常終了で controller が最後でない場合も、残る worker の `workers.lock` が木を保持し、最後の退出者が撤去する（同 `:925–944`）。
- `_T080_PREWARM_RUN_ID` は thread 内で設定し、`get()` の例外時にも解除する（`conftest.py:2587–2593`）。worker の run_id 解決は、thread local が未設定なら従来の環境変数へ進む（`test_s8b_oracle_driver.py:1015`）。
- `_early_memo_selected` が偽なら起動行へ到達せず、`workerinput` に新しい key も追加しない（`conftest.py:2373–2390, 2711–2744`）。既存 test の assert・期待値・nodeid・parametrize の変更も提示差分にはない。
- T2、T3、T4、T5、T7 の主張には対応する検査がある。ただし全 test・変異は未実走であり、実際の赤 node 集合は確定していない。

## 総括

**NO-GO。** join 超過と thread 起動失敗に、上限・木の寿命を破る具体的経路がある。
T6 はその危険を検出せず、M3・M5・M6 の事前登録は単一理由性を満たさない。