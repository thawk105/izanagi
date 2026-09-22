静的検査の結論は **plan 修正後に実装へ進める。must-fix は1件**です。指定必読資料はすべて読めました。書込み・configure・build・実測は行っていません。

以下、`J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3`、`CC` は指定 worktree の `external/ccbench` です。「検査を通る」という指摘は、まだ存在しない probe の実測結果ではなく、plan の受理条件に対する静的な反例です。

1. **must-fix — `trace.hh` の追加位置が既存関数の内部を指している。**

   根拠: [s2-plan.md:76](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/out/s2-plan.md:76)、`CC/include/trace.hh:117–124`。

   「元120行の直前」は `emit_lock_violation()` の閉じ括弧の直前である。空行は121行、namespace 終端は122行。指定どおり新 helper の関数定義を置くと、既存関数内に関数を定義することになり TRACE=1 がコンパイル不能になる。`#line 120` は構文上の位置を直さない。

   **修正:** 元120行の閉じ括弧を保持し、元121行の前へ追加して `#line 121` で元の空行へ復元する、または元122行の前へ追加して `#line 122` で namespace 終端へ復元する。

   **成果物への影響:** TRACE=0 の比較が一致しても、silo・si・mocc および追加 include を持つ全 TPC-C TU の TRACE=1 が失敗し、trace/witness の受入へ進めない。

2. **should — 共有 header の TRACE=1 互換性を、silo の2 target だけでは確認できない。**

   根拠: `J/out/s2-plan.md:193–212,284–286`、`CC/cmake/ProtocolHelpers.cmake:34–62`。

   12 source path／21 compile entry の列挙は一次資料と一致する。ただし、その全件比較は TRACE=0 であり、新 API・TLS・追加 include は消える。TRACE=1 の build は `tpcc_silo.exe`／`ycsb_silo.exe` だけなので、他8 protocol の `tpcc_*.cc` と si/mocc の `transaction.cc` における名前衝突・include 順序依存・警告は検査されない。

   所見1を直した案について、これらに固有のコンパイル失敗は静的には発見できなかった。これは具体的な破損の断定ではなく、検証範囲の不足である。計算 job 内で、変更 header の TRACE=1 consumer に少なくとも実 flags による構文・警告検査を追加するとよい。protocol 本体の変更は不要。

   **成果物への影響:** silo の内部受入が緑でも、共有 header を利用する他 protocol の TRACE=1 互換性は未検証のまま残る。

3. **should — 構造 probe は、範囲内の誤った取引種別・表番号を受理する。**

   根拠: `J/out/s2-plan.md:320–331,416–430`、`CC/include/tpcc/tpcc_query.hh:19–25`、`CC/include/tpcc/tpcc_tables.hh:16–28`。

   反例は、全 C の `tx_type` を `1↔2` に入れ替えること。両種別は残り、frame・件数・witness・OrderLine 復号条件も変わらない。別の反例は、R/W の表5と表6を両方とも5へ写すこと。表番号の範囲、token 数、C/E、witness、表8の検査は維持される。「表5と表6に同じ key がある正常 fixture を受理する」試験だけでは、この誤実装を拒否できない。

   plan の setter と `get_storage(storage_)` 自体は正しく、この誤りが必ず入るという指摘ではない。新機能の意味を確認するには、既知の NewOrder／Payment 操作と期待する表・種別を照合する job-local の試験が必要である。例えば NewOrder の同一 key に対する表5・6の INSERT 対、Payment の History INSERT と種別2との対応を確認し、上の変異を負例にする。

   **成果物への影響:** 誤った取引種別、または別表を統合した trace が `structure+witness pass` になり、後続 verifier の帰属や依存辺を誤らせうる。

4. **should — 終了境界の計数修正に、決定的な回帰検査がない。**

   根拠: `J/out/s2-plan.md:533–539`、`J/verbatim/tpcc-design-README.md:254`、`CC/include/tpcc.hh:102–112`。

   旧 quit 判定へ戻した実装でも、1秒走の終了が成功 commit と counter 加算の間に重ならなければ完全一致する。trace の末尾削除という負例は「照合器が不一致を拒否する」証拠であり、「producer が必ず成功 commit を数える」証拠にはならない。plan 自身もこの限界を認めている。

   設計 §6.1 の「commit 成功直後に quit を立てる」制御を scratch の試験に戻し、候補では一致、旧順序では不一致を確認するのが直接的である。repo への gate 追加は不要。

   **成果物への影響:** 正常走が緑でも、最終 commit の計数漏れを再導入した候補を非決定的に見逃す。

5. **should — 生 trace の削除が、今回の新 parser と並走 verifier による再検証を不可能にする。**

   根拠: `J/out/s2-plan.md:310–312`、`J/s1-brief.md:19,31`。

   SHA-256・C/E 数・少数 frame は、削除した入力を再構成できない。probe に所見3のような不足が後から見つかっても、同じ実行を修正版 probe／単位4の verifier へ渡せない。再走は異なる並行履歴であり、削除した走の再検証にはならない。

   少なくとも最終 review と単位4への受渡しが済むまでは、上限を設けた今回の小さい trace を圧縮して保持することを推奨する。digest と実行資材の保存はその代替ではない。

   **成果物への影響:** 当日の受入結果は残るが、その結果を生入力から再監査できず、後日の検査修正に対する証拠が失われる。

6. **nit — P1 の採用理由に、現状の事実から導けない一般化がある。**

   根拠: `J/s1-brief.md:22`、`J/out/s2-plan.md:154`、`CC/cmake/ProtocolHelpers.cmake:32–43,64–65`。

   現行の transaction TU に workload 別 define がないことは正しい。しかし「workload 別 define を足すと perf build の flag も変わる」は必然ではない。TRACE=1 の target にだけ付ける設計は可能である。今回 CMake を変更せず TLS を採る理由としては十分だが、compile 時の識別が原理的に不可能という説明にはしない方がよい。

   **成果物への影響:** 現案の trace／witness は変わらないが、P1 を唯一可能な方式として固定する根拠が過大になる。

7. **nit — P7 の正当化は「別 worktree だから」ではなく、明示された作業範囲と F546 に置くべき。**

   根拠: `J/s1-brief.md:27`、`J/verbatim/D41-excerpt.md:14–20`、`J/verbatim/D296.md:10–13`、`J/verbatim/F546.md:11–15`、`J/request.md:2–4`。

   D41 の拒否理由は hook の編集面制限の迂回であり、元の作業ツリーを直接変更したかどうかだけではない。したがって「本経路は作業ツリーを変えない」は単独では反論にならない。

   一方、今回は依頼が両 header の実装を明示し、F546 が disposable clone と親による適用を規定している。plan は拒否時に停止する条件も置いている。この組合せに対して、現時点で迂回と断定する攻撃は成立しなかった。説明の根拠を修正すればよく、追加承認を求める理由にはならない。

   **成果物への影響:** bytes 上の影響はないが、別 path を一般的な hook 回避根拠にする誤読を防げる。

## 総括

- **must-fix 一覧:** 所見1。`trace.hh` の挿入位置を元関数の外へ訂正する。

- **P1:** 賛成。外部 linkage の inline accessor 内 TLS は TU 間共有の意図に合い、begin 後の setter と失敗・成功時の clear で持越しを防げる。compile 時識別についての説明は所見6のとおり限定する。
- **P2:** 内部候補の限定的な証拠として条件付き賛成。実 header の `-E -P -dD` と include 活性比較は、D297 の header 単体比較の穴を避ける。ただし D297 pass の代替承認にはならない。D297 は genome／overlay を列挙するが、plan は選定 build flags の比較であり、保証範囲が同一ではない。逆アセンブル一致も任意のデータ領域・全構成の同一性証明ではない。
- **P3:** 賛成。C1 は未完成 producer、受入対象は C2 と明示されているため、C1 の旧 TPC-C trace を完成品と誤認する経路は plan 上では閉じている。
- **P4:** 条件付き賛成。構造検査と現行 YCSB 認定の分離は適切。ただし所見2〜5の検証・保存上の限界を残したまま、producer の意味や全 consumer の互換性まで実証済みとしない。
- **P5:** 親 brief のままには反対、plan の限定修正に賛成。runtime の line 0 観測と、初期ロードとの静的対比を区別する。「si を走らせない」と「段1では到達しない」も区別する。
- **P6:** 賛成。pin と候補で前提 patch 列を揃える比較が必要。適用成功と「17本」の網羅性は本検査では独立実証していない。
- **P7:** 条件付き賛成。明示依頼・F546・D16を根拠とし、拒否後の経路変更はしない。D296 の既存 helper 維持と一取引一 C の条件も守れる。

- **攻撃不成立 — TRACE=0／`__LINE__`:** 所見1以外では、指定位置どおり元行を残す限り、`tpcc.hh` の復元値27・56・94・104・109・110・111、および silo の635・658・679・700に off-by-one は見つからなかった。既存 ERR の88・106・690は両 TRACE 値で元の論理行を維持する。追加 include は TRACE=0 では非活性で、`#pragma once` による先行抑止経路も見つからなかった。追加の未使用変数・関数による具体的な警告経路も未発見。
- **攻撃不成立 — witness:** silo の成功経路は `commit():706` → `writePhase()` → true → counter 加算となる。app abort・validation 失敗・begin 前 quit・leader 経路から C と counter の片側だけへ到達する新経路は見つからない。TRACE=0 の quit 判定と計数順序も維持される。完全一致条件に許容幅はない。
- **攻撃不成立 — frame／状態:** C の排他的分岐、同じローカル種別値による R/W/X 選択、全 X 後の E は整合する。retry は query 再生成後に setter を通るため、前取引の種別が付く経路は未発見。context が0になる故障なら v2 が出て TPC-C probe が拒否する。現行 verifier も v3 を受理せず、TPC-C 認定を誤って緑にする経路はない。
- **攻撃不成立 — 表識別:** read／insert／delete／update はそれぞれ `transaction.cc:277,109,137,547` で渡された `Storage s` を要素へ保存する。`get_storage` は整数 cast であり、NewOrder=5／Order=6、Warehouse=0／Item=9を実際に分離する。
- **攻撃不成立 — YCSB／P:** 既存 v2 の出力式・helper を保持する案から、YCSB の bytes 形式変更は導けなかった。P は採番前の validation で出るため txid を付けない扱いが正しい。P/X を正常対照の失敗とする点も適切。
- **攻撃不成立 — 負例の基本設計:** frame 欠落、重複 C、nR/nW 不一致、固定 stdout witness に対する取引削除は、記載された条件なら拒否される。実装前なので、自己試験が実際にその拒否分岐を通ることまでは確認していない。
- **裁定パッケージ候補:** 将来の pin 前進における header 変更と D297 の扱い。今回は拒否を記録して未解決条件として残し、checker・verifier・si/mocc の変更へ scope を広げない。