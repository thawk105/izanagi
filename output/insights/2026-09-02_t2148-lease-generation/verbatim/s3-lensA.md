## 所見

1. 非保持走行の「世代」が候補集合で定義されていない

   - 対象: `plan.md:3-8,59-69`、`d1449.md:3-5`、`d662.md:3-5`、`tools/dev_wave_wait.py:2895-2910,3795-3800,3907-4004`
   - 何が問題か: 現行 waiter は他 wave の lease が `held` の場合、`unclaimed=True` としつつ、holder には自 wave の digest を合成して受領証へ渡す。非保持時は終了前の lease 再確認も省く。受領証には非保持を示す field がない。計画の候補はすべて「ある lease 取得の世代」を前提とし、この経路で何を書くかを定義していない。live lease を読めば他 wave の世代を自走行へ結び、caller 値や sentinel を使えば自己申告になる。
   - 裁定にどう効くか: D1449/D662 を維持して非保持走行を許すなら、`ownership_state` と、非保持時の generation domain を先に決める必要がある。現状の17候補だけでは最終採用を裁定できない。
   - 実在性: real。非保持経路はコード上の事実であり、候補がその値を定義していないことも計画本文から確認できる。

2. 世代の判定基準が再送防止には弱すぎ、current producer 候補の恒真性が過小評価されている

   - 対象: `plan.md:5-7,14-30`、特に C1-C3、C6-C7、C13。`d1400.md:36-39`、`d906.md:3-10`
   - 何が問題か: 「再取得時には別値になり得る」だけでは足りない。同一 context の再取得で旧値を再利用できないこと、または信頼された主体が十分な確率で再利用不能にすることが必要である。C1-C3 は repository 内の `_create_lease`、C6-C7 と C13 の current-producer variant は同じ書込み主体が値を選べる。旧受領証の世代を新 lease へ再度書けば、署名側と着地側が同じ writable state を読む検査は再び一致する。C6-C7 では sidecar の残置により、再書込みすらせず旧世代が次の lease と組になる。
   - 裁定にどう効くか: C1-C3 と current-writer の C6-C7/C13 は、外部 authority が再利用を拒否する状態を別に持たない限り「移行上不可」だけでなく「再送防止として不可、または恒真」と分類すべきである。C13 は current writer と external writer を別候補に分ける必要がある。
   - 実在性: real な writer 定義から導ける replay 機序。攻撃成立の評価は設計上の推論だが、必要な比較値を同じ主体が選べる点には仮定がない。

3. 署名 probe は同じ値を両辺へ渡す循環で、信頼の根を測らない

   - 対象: `plan.md:347-415`、`tools/acceptance_issuer_reference.py:436-464,513-528`
   - 何が問題か: Command 4 は同じローカル変数 `generation` を issuer の入力と verifier の `expected_lease_generation` の両方へ渡す。これは「渡した値が署名後も同じ」と「別 literal は拒否」を測るだけで、expected 値の独立した出所を証明しない。現行 issuer 自身も同じ caller 値を payload と照合期待値へ渡している。Command 1 の `external-sidecar-placement` と `external-ledger-placement` も probe 自身が書くため、外部主体を測っていない。さらに ledger は lease directory の外へ作る一方、結果収集は `directory.rglob("*")` だけなので、ledger の残置すら出力に現れない。
   - 裁定にどう効くか: C8/C15 の external authority を支持する実測にはならず、C16 の循環を再現する機能試験に留まる。裁定資料では「署名機構の機能確認」と「generation provenance の確認」を明確に分離すべきである。
   - 実在性: real。値のデータフローと収集範囲をコードから直接確認した。

4. shortlist の候補を強制する production consumer が存在せず、正の end-to-end 証拠がない

   - 対象: `plan.md:43-46,519-527,580-581`、`tools/dev_wave_land.py:5628-5650,5689-5722`、`tools/acceptance_issuer_reference.py:4-16`
   - 何が問題か: production lander は signed-v6 verifier を呼ばず、v5 schema を受理する。lease renew が `unavailable` でも `land(request)` を実行し、release の結果も land 結果を上書きしない。reference issuer も production waiter/lander から未接続である。したがって C8/C13/C14/C15 の generation を、issuer が authoritative state から読み、lander が独立に current state と照合する経路がない。
   - 裁定にどう効くか: 現材料でできるのは棄却と shortlist までであり、積極採用はできない。これは `plan.md:581` も認めているため、その限界を裁定パッケージの前提に昇格させる必要がある。
   - 実在性: real。production 呼出し関係から確認できる。

5. D1400 の訂正は helper の fresh path には成立するが、システム全体へ一般化できない

   - 対象: `brief.md:53-64`、`premeasure.md:19-43,71-81`、`d1400.md:43-47`、`tools/wave_land_window.py:383-425,499-579`、`tools/dev_wave_land.py:5628-5650`
   - 何が問題か: 観測とコードは、基準 commit の current reader が fresh extra-field lease を `free` ではなく `unavailable` とすることを十分支持する。ただし実走したのは current commit の claim/release/status だけで、実際に混在し得る過去版 reader、waiter 全体、lander は測っていない。lander は renew 失敗でも進むため、`brief.md:62` の「規律2に触れる破れではない」は helper の出力からは導けない。また「2400秒間 directory 全体が固まる」も不正確で、TTL超過後は別 claimant が回収でき、status は `stale`、owner release は引き続き `unavailable` である。
   - 裁定にどう効くか: D1400項目11の「extra field を free と読む」という exact な機序は訂正してよい。一方、「排他が開く懸念は解消」「正しさゲートへの影響なし」とまでは訂正してはいけない。
   - 実在性: helper の訂正部分は real。旧版全体や system-level safety へ広げられないという境界も、未実走範囲と lander のコードから real に確認できる。

6. 使い捨て directory は production directory と同値ではなく、特に C8/C13/C14/C15 の判定材料が不足する

   - 対象: `brief.md:41-43,78,94-95`、`premeasure.md:3-6`、`plan.md:26-28,139-165,217-281,519-527`、`tools/wave_land_window.py:186-251,275-308`
   - 何が問題か: disposable directory で確認できるのは、open/create が成功した後の current helper の論理である。production との差として、path の symlink 性、所有 uid、mode/ACL、sticky/setgid、read-only/quota、既存 malformed/foreign file、残置 sidecar、同時 claim/renew/release、複数 node の clock、flock/O_EXCL/unlink の filesystem 実装、xattr 対応、mtime 分解能、inode 再利用がある。C14 の command は `getattr(st, "st_birthtime", None)` を記録するだけで、真の birth time を取得できない環境では候補を測れない。
   - 裁定にどう効くか: payload schema の fail-closed 性は disposable dir でも評価できるが、xattr、inode/birth time、保護 sidecar、外部台帳を積極採用する根拠にはならない。production と同じ filesystem・権限・並行条件での証拠が必要である。
   - 実在性: real な未測定差分。各差分が実際に production で発生するかは未確認であり、その点は推測として扱う。

7. 親観測の値は controlled injection であり、production writer の provenance ではない

   - 対象: `premeasure.md:19-27,34-40,45-62`
   - 何が問題か: extra field、古い mtime、sidecar は親 probe が自分で書き、その後同じ作業環境の helper で読んでいる。これは parser compatibility や stale 分岐を測る正当な注入試験だが、「誰が production generation を書くか」「その主体を AI が変更できないか」は測らない。支給された `premeasure.md` に raw command transcript、stdout artifact、変更前後 bytes の hash はなく、実走値の出所は親の記述だけである。
   - 裁定にどう効くか: current helper の分岐はコード読解でも裏付けられるが、external writer や trust root の実在証拠として引用してはいけない。
   - 実在性: 支給材料内では real。別の raw artifact がどこかに存在しない、とは推測しない。

8. consumer closure は計画の「7面」と一致せず、統合テストが1ファイル漏れている

   - 対象: `plan.md:59-69,475-503`、`orchestrator/tests/test_resume_gate_acceptance_boundary.py:281-289,404-428`
   - 何が問題か: 計画の7面は機能面の分類で、repository の import/subprocess 参照閉包ではない。実行時 closure には、helper を合成 repo へ copy し、実 waiter 経由で起動する `test_resume_gate_acceptance_boundary.py` も含まれるが、Command 6 にない。
   - 裁定にどう効くか: 主結論は直ちには変わらないが、「consumer 閉包を測った」「既存 test を閉じた」という主張には使えない。少なくとも同統合テストを対象へ加える必要がある。
   - 実在性: real。repository 全体の文字列参照と実行経路から確認した。

## 親 brief と親の観測への指摘

- `premeasure.md:25-32` の「基準 commit の fresh extra-field lease は `free` ではなく `unavailable`」は、`tools/wave_land_window.py:133-149,244-251,383-384` と一致する。この狭い訂正は裁定根拠として使える。
- `brief.md:56-57` の waiter 停止はコード上は強く予測できるが、親観測では未実走である。production acceptance 全体の観測として扱ってはいけない。
- `brief.md:62-64` の「規律2に触れない」「2400秒間 directory 全体が固まる」は射程過大である。旧 lander は renew 失敗でも land を進め、TTL後の claim/status/release も同一の回復挙動ではない。
- `premeasure.md:57-59` の「claim は `os.listdir` で固定名を見る」は誤りである。claim は `tools/wave_land_window.py:367-381` で固定名を直接 open/create する。`os.listdir` は renew の `:440-446` と status の `:562-568` にある。sidecar が無視されるという結論自体は正しい。
- D1400項目11を訂正するなら、「基準 commit の current helper において、fresh extra-field payload は claim/release/status で fail-closed」という限定を残すべきである。実際の旧版集合と system-level land safety は未証明である。
- 親観測は controlled injection として有用だが、generation writer、外部 authority、production storage の信頼性を測ったものではない。

## consumer 閉包の再列挙

repository 全体の参照から得た実行時 closure は6ファイルである。実装2、直接テスト2、推移的統合テスト2となる。

| 種別 | consumer | 関係 |
|---|---|---|
| production | `tools/dev_wave_wait.py:2722-2733` | helper CLI の claim/release を subprocess 起動 |
| production | `tools/dev_wave_land.py:44,5634-5637,5696-5700` | module import 後に renew/release を直接呼出し |
| direct test | `orchestrator/tests/test_wave_land_window.py:16-22` | `importlib` で helper を直接 load |
| direct test | `orchestrator/tests/test_dev_wave_wait.py:26-50,9038-9052` | helper を直接 loadし、統合ケースでは subprocess 起動 |
| transitive test | `orchestrator/tests/test_dev_wave_land.py:31-37,593-598` | lander を loadし、その import 済み helper API を直接呼出し |
| transitive test | `orchestrator/tests/test_resume_gate_acceptance_boundary.py:281-289,404-428` | helper を合成 repo へ copyし、実 waiter subprocess 経由で起動 |

`orchestrator/tests/README.md:186` は名称参照だけで consumer ではない。`acceptance_receipt_signature.py` と `acceptance_issuer_reference.py` も generation の consumer ではあるが、`wave_land_window.py` を import／起動しないため、この閉包には含めない。

計画の Command 6 は前半3テストモジュールから nodeid を選んでいるが、`test_resume_gate_acceptance_boundary.py` を落としている。なお、本相談ではテストを実走しておらず、いずれも緑とは判定していない。

## 総括

所見は8件で、そのうち裁定の結論を変えうるものは6件、所見1から6である。

この材料から、次は裁定できる。

- 基準 commit の fresh extra-field payload を current helper が `free` と読む、という D1400項目11の機序は誤りである。
- C4/C5/C9/C11/C16/C17、および current writer だけで閉じる C1-C3/C6-C7/C13 は、そのままでは採用できない。
- C8、external-writer 版 C13、C14、C15 は shortlist に留めるべきである。

一方、最終採用の裁定はまだできない。必要なのは、非保持走行を明示する署名済み意味論、再取得ごとに再利用不能な世代 invariant、authority と lease の原子的な結合、issuer と lander が独立に current generation を得る signed-v6 production 経路、実 production storage と混在旧版での並行観測、および raw transcript を伴う positive control である。