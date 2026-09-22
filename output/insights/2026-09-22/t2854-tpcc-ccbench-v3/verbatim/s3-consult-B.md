判定は **修正後に進行可**。完了判定 (a)〜(c) の骨格は妥当ですが、変異検査の免除理由と、計数修正の境界経路の検証は直す必要があります。削減対象は、将来の pin 前進に属する patch 全件検査と、既知の D297 拒否を再実行する手順です。

指定資料はすべて読みました。現物の CCBench HEAD は `e9e477ca1b55348ab4530de0b1cf663ce4555290`。静的検査のみで、書込み・build・投入・実走はしていません。

以下の参照では、`J` は指定 job directory、`W` は指定 worktree、`CC` は `W/external/ccbench`、`V` は `J/verbatim`、`driver` は `W/orchestrator/campaign/s3_mocc_lock_coverage.py` を表します。

1. **must-fix — P4 の変異免除は、superproject と wave 全体を取り違えている。**
   **根拠:** `J/s1-brief.md:25`、`J/out/s2-plan.md:525`、`W/docs/dev-wave/core.md:97`、`V/D95.md:15`。
   DW-S04 の免除条件は「実装面の差分ゼロの wave」であり、superproject の tracked 差分だけではない。今回の主成果は CCBench の C++ 差分で、job-local probe も D95 が名指す実装面である。資材を job directory に置くことは免除根拠にならない。
   **修正:** producer の変更に対応する小さい変異 matrix を登録する。全候補をフル rebuild する必要はなく、前処理比較で殺せる変異と、境界制御を伴う計数変異に絞れる。実施する変異は `mutation.md:18`・`:30` の kill／harness 契約に従う。
   **成果物への影響:** 現案では「壊した trace を parser が拒否した」を「壊した producer を受入が拒否した」の代わりにして、内部受入の検出力を過大報告する。

2. **must-fix — commit 成功直後の quit 経路を、既定の確認から外している。**
   **根拠:** `CC/include/tpcc.hh:102`・`:110`、`J/out/s2-plan.md:296`・`:533`・`:539`、`V/tpcc-design-README.md:254`。
   2 thread・1秒走は、この境界を踏む保証も観測証拠も持たない。旧計数のままでも、終了時に該当する成功 commit がなければ witness は一致する。thread 数や extime を増やしても決定的にはならない。plan 自身がこの限界を認めながら、設計にある境界試験を除外している。
   **修正:** scratch 診断で成功 commit の直後、問題の quit 判定より前に quit を立てる。実際の workload 経路で、候補は C 数＝counter、旧計数に戻した変異は不一致になることを確認する。診断用変更は候補 commit に混ぜない。
   **成果物への影響:** 必須の計数修正を欠いた候補が、偶然の通常走の一致だけで内部受入を通る。

3. **should — v3 構造検査は必要だが、正しい表・取引種別の証明には足りない。**
   **根拠:** `J/out/s2-plan.md:320`・`:324`・`:331`・`:430`、`V/tpcc-design-README.md:49`・`:72`。
   範囲内の表番号や取引種別を取り違えても、token・件数・witness は通る。例えば tx_type の 1 と 2 を交換する誤実装は、両方が正の件数という条件を満たす。表5・6を使う手書き fixture の受理も、実 emitter が正しく表番号を運んだ証拠ではない。
   **修正:** NewOrder／Payment の実 frame から少数の内容対応を確認する。例えば NewOrder の同一注文 key が NewOrder 表と Order 表の別識別子で出ること、取引種別が実際の操作群と対応すること。既存の標本採取に相乗りでき、DSG を作る必要はない。
   **成果物への影響:** 形式は正しいが表・取引種別が誤った trace を、後続 verifier の入力として引き渡しうる。

4. **nit・攻撃不成立 — 完了判定 (a)〜(c) 自体を削る根拠はない。**
   **根拠:** `J/s1-brief.md:6`、`V/D295.md:10`、`V/D297.md:28`、`J/out/s2-plan.md:7`。
   (a) は producer の出力契約と完全性、(b) は共通の silo emitter を変更することによる YCSB 回帰、(c) は規律1をそれぞれ扱う。nm／strings だけでは無名の計装漏れを閉じず、binary 比較だけでは他 consumer を覆わない。
   親 probe の結果名は plan のとおり **`structure+witness pass`** に限る。直列化可能性、insert の存在意味論、表付き依存辺の正しさは単位4・5待ちである。
   **成果物への影響:** 現案の限定表現を維持すれば誤認定は増えない。TPC-C の `certified` と呼ぶ変更には反対する。

5. **nit・一部削減可 — 9 protocol の consumer 確認は妥当。21 entry の重複実行は縮められる。**
   **根拠:** `J/out/s2-plan.md:195`・`:210`・`:237`、`CC/cmake/ProtocolHelpers.cmake:32`・`:41`。
   `tpcc.hh` は実際に9 protocol が読むため、silo だけの前処理比較へ縮める攻撃は成立しない。一方、同じ transaction source の4 workload 分は、前処理に効く argv・cwd・入力・依存が同一と確認できれば、代表1回の比較へまとめられる。全21 entry から代表への対応は残す。
   **削ると失うもの:** 同じ前処理の反復だけ。同等性未確認の source-path 単独 dedup は不可。
   **成果物への影響:** 同等性を確認した削減なら受入集合は変わらないため、最適化は nit。

6. **nit — D297 の「拒否を実走して記録」は完了条件から外せる。**
   **根拠:** `J/out/s2-plan.md:250`、`W/tools/check_trace0_preprocess_identity.py:195`、`V/D297.md:7`。
   現 checker は `.hh` 差分を明示的に拒否する。今回の header 変更に対する拒否は一次コードで確定でき、既知の rc=1 を再取得しても producer の品質は上がらない。静的根拠と「D297 pass 未取得」を記せば足りる。
   **削ると失うもの:** CLI が予想どおり拒否したという実走記録。TRACE=0 同一性の証拠は失わない。
   **成果物への影響:** なし。したがって blocker にしない。

7. **nit — P6 の17本全件・前提列付き apply 検査は、今回から外せる。**
   **根拠:** `J/s1-brief.md:10`・`:28`、`J/out/s2-plan.md:519`、`W/docs/dev-wave/core.md:82`。
   今回は pin を進めず、旧 pin 上の patch 利用も変わらない。全17本の互換性は単位11の材料であり、今回の producer 内部受入に直接必要ではない。今回の変異／control に実際に使う patch だけ候補に適用確認すればよい。
   **削ると失うもの:** 将来の適用衝突の早期発見。既存 patch の実行意味の互換性は、apply 成功だけでは元々証明できない。
   **成果物への影響:** 今回の正常候補・既存 pin の認定結果には影響を示せないため nit。

8. **should — P5 は plan の訂正を採用し、部分観測と再現完了を区別する。**
   **根拠:** `J/s1-brief.md:26`、`J/out/s2-plan.md:399`・`:403`、`V/D2219.md:99`、`CC/include/tpcc/tpcc_initializer.hh:279`、`CC/include/tpcc/tpcc_tx_neworder.hh:314`。
   runtime の OrderLine key 復号は既存 trace に相乗りでき、D2219 項7の明示要求にも対応するため、過剰として削る攻撃は成立しない。ただし実証するのは runtime の0始まりだけ。初期ロードとの差は静的対比、隣注文を scan する問題は未再現である。
   brief の「他は段1では到達しない」は誤り。si の read→update 問題は Payment にも関係し、今回は si を走らせないから対象外である。
   **成果物への影響:** brief のままだと、未検証の所見を到達不能として報告し、D2219 の再現結果を誤って閉じる。

9. **nit — 2 commit 分割は必須ではなく、1 commit がより単純。bundle は維持してよい。**
   **根拠:** `J/out/s2-plan.md:446`・`:449`・`:461`、`V/tpcc-design-README.md:278`、`V/D16.md:8`。
   設計の「実装単位」は commit 数の指定ではない。C1 単独は v3 producer として受入されないので、3 file を1 commit にまとめても最終 tree と確認命題は同じ。親関係の検査・message・fix 後の管理が減る。
   bundle は使い捨て作業面から候補を保全する具体的な役割がある。主 checkout への非 force fetch は内部受入には不要だが、後続統合・人間の push 用に ref を置く安価な操作であり、強く削る理由はない。
   **削ると失うもの:** 2 commit を1本にすると単位別 cherry-pick の便利さ、fetch を延期すると主 checkout からの即時利用。
   **成果物への影響:** 最終 tree・証拠が同じなら認定結果は不変で nit。

10. **nit・攻撃不成立 — build の主要失敗点は plan が既に押さえている。**
    **根拠:** `J/out/s2-plan.md:273`・`:279`・`:281`・`:285`、`driver:147`・`:190`・`:224`、`CC/cmake/CompileOptions.cmake:30`。
    環境の暗黙継承を避け、hydrate、gflags/glog の固定 source、static/PIC、toolchain digest、`-Werror` を扱っており、「依存準備が丸ごと欠けている」という攻撃は成立しない。
    実装時の注意は、`_resolve_toolchain` が PATH 上の gcc/g++ を選ぶ点。期待 compiler が PATH に無ければ digest 不一致で止まる。また `_load_policy` と `_common_configure_args` は mocc の target／`STOCK_G` を含み、そのまま再利用できない。
    **成果物への影響:** 誤った再利用は build 失敗または意図しない macro 構成を作るが、plan は既に流用禁止を明記しており、現時点で新しい欠落とは数えない。

11. **should — trace の上限と `/scr` 全体の容量見積りを分ける。**
    **根拠:** `J/out/s2-plan.md:280`・`:284`・`:310`、`driver:194`・`:225`。
    2 worker × 512 MiB × 2 run＝2 GiB は、現在の「worker ごとに1 file」という emitter を前提にした trace 上限として妥当。ただし `/scr` には source、hydrate、依存 build/install、CCBench の3 build 木も置く。RLIMIT_FSIZE は directory 全体の quota ではない。
    **修正:** probe 起動時と trace 開始前に空き容量を確認し、trace 上限とは別に build 類の実使用量を記録する。容量不足は今回の専用 directory 内で停止し、共有領域へ自動退避しない。汎用 quota 機構は不要。
    **成果物への影響:** trace だけの2 GiBを必要容量と誤認すると、build／trace が ENOSPC で未完了となり、再投入が増える。

12. **nit・攻撃不成立 — YCSB の proof surface は plan の指定で足りる。**
    **根拠:** `J/out/s2-plan.md:354`、`W/orchestrator/verifier/cli.py:48`・`:70`、`W/orchestrator/verifier/model.py:238`・`:290`。
    `--expected-commits`、`--protocol silo`、実際に build した候補を指す `--ccbench-root`、個別 `certified=true` の確認は必要で、plan は既に要求している。pin の source を渡す代案は不可。
    ただし proof surface は source 内の emitter 呼出しの存在検査で、到達性や発火の証明ではない。正常走の X=0 から v3 X emitter の健全性まで主張しない。
    **成果物への影響:** plan を守れば参照取り違えは防げる。v3 X の実発火確認が必要なら、所見1の限定した control として扱う。

13. **nit — 既存関数の再利用を具体化すれば、新 probe の量は減らせる。**
    **根拠:** `driver:101`・`:147`・`:224`・`:343`・`:387`・`:439`。
    再利用候補は `_run_checked`、`_resolve_toolchain`、`_prepare_dependencies`、`_normalize_objdump`／`_trace0_record`。新規部分は silo の2 target 構築、stdout 保持、v3 の局所構造検査、候補参照の束縛に絞れる。既存 `_run_trace` は stdout を返さず、`_verify` は mocc 固定かつ witness 無しなので、そのまま使わない。
    login では読取り、patch 適用確認、資材の構文確認、環境が揃う場合の前処理比較まで。C++ build・リンク・境界診断実行・benchmark は依頼どおり compute で行う。configure に try-compile がある点は plan の注意を維持する。
    **成果物への影響:** 同じ証拠を出す局所再利用なら受入集合は不変。汎用 driver 化や新 gate は不要。

14. **should — node 時間の算術は整合するが、上限保証ではない。**
    **根拠:** `J/s1-brief.md:37`、`J/out/s2-plan.md:263`・`:436`、`V/D2219.md:29`、`driver:336`。
    0.5時間×2投入＋0.25時間×2受入＝1.5 node時間なので算術上は正しい。ただし3 build 木は2 target ずつで、依存構築・前処理・検証も含む。0.3〜0.5時間の実測根拠は提示されておらず、30分 walltime の上端と予算上端が一致している。所見1・2の追加費用も再積算が要る。
    **2時間に届く経路:** 30分 job を3回＋受入2回でちょうど2時間、30分 job を2回＋受入4回でも2時間。ここへ達する見込みの投入前に確認する。
    最初は1 job にまとめて依存構築を共有するのが安い。分割は失敗した検証だけ再実行しやすい反面、scratch が引き継げなければ hydrate/build を繰り返す。失敗までの log・中間結果を保存し、再利用できる trace／binary がある場合だけ再投入範囲を縮める。専用 resume 基盤は足さない。
    **成果物への影響:** 「≤1.5」を固定扱いすると、再試行・変異を計上せずユーザーの確認ラインを越える。

15. **nit — 親の一次資料に基づく主張は2件成立、P1の説明だけ過度に一般化している。**
    **根拠:** `J/s1-brief.md:22`、`CC/cmake/ProtocolHelpers.cmake:41`・`:65`、`W/tools/check_trace0_preprocess_identity.py:195`、`J/out/s2-plan.md:493`。
    現 CMake は workload 別の compiler define を供給していない。この限定では P1 は正しい。ただし「compile 時には区別不能」「define を足せば必ず perf flag が変わる」は一般論として誤りで、TRACE=1 の target にだけ define を足す設計は可能。それでも今回は CMake 変更と取引種別 context の二重管理が増えるので、TLS 案より安いとは言えない。
    D297 の `.hh` 拒否、対象 patch が silo の17本であることは現コード／patch header と一致した。列挙の正しさと、17本の apply 検査を今行う必要性は別問題である。
    **成果物への影響:** P1の説明を限定しても最終実装は変わらず nit。D297拒否・17本列挙への事実攻撃は不成立。

16. **nit・攻撃不成立 — `#line` と P7 の適用経路に、より安い同等案は見つからない。**
    **根拠:** `CC/include/tpcc.hh:88`、`CC/cc/silo/transaction.cc:690`、`J/out/s2-plan.md:85`・`:483`、`V/F546.md:11`。
    行数を合わせる空行削除や巨大な1行化でも論理行を保存できるが、読みやすさと将来の編集を悪化させる。差分比較側で `__LINE__` を消す代案は同等ではない。局所的な `#line` 復元を支持する。
    F546 の disposable clone と親の適用、拒否された地点で停止する P7 も妥当。D296 は旧 v2 の変更契約であり、今回明示された v3 helper 実装を禁止する一般規則とは読めない。ただし1 txn に C が1本という条件は維持する。
    **成果物への影響:** 提案経路に未修正の具体的欠陥を示せず、攻撃不成立。

**裁定パッケージ候補（今回の実装外）:** header 変更を含む候補を単位11でどう受け入れるか。D297 の現契約では拒否される一方、今回の局所 consumer 比較はその契約変更を意味しない。単位11で比較方式・保証範囲を提示する。今回 checker を拡張したり、独自比較の成功を D297 pass と扱ったりしない。

## 総括

- **must-fix:** ① superproject 差分だけを根拠にした変異免除を撤回する。② commit 成功直後に quit を立てる境界試験と旧計数変異を、限定した診断として組み込む。
- **削るべき項目:** D297 の既知拒否の実走を完了条件にすること、未使用 patch 17本の全件・前提列付き互換検査。2 commit は1本へ簡素化可。consumer 比較は、同等性を示せる重複実行だけ削れる。
- **足すべき項目:** 小さい producer 変異 matrix、計数境界の決定的確認、実 frame の表／取引種別対応の確認、build 類を含む `/scr` 容量確認、追加診断を含む投入前の再見積り。
- **P1:** 賛成。現 build 定義に限定して根拠を書き直す。
- **P2:** 条件付き賛成。consumer／binary 比較と保証範囲の限定を維持し、拒否再実走は必須から外す。
- **P3:** 2 commit 必須には反対。1 commit で同等。
- **P4:** (a)〜(c) と既存受入は賛成。変異免除と計数境界試験の除外には反対。
- **P5:** plan の限定修正に賛成。runtime の部分観測を残し、未検証を到達不能と書かない。
- **P6:** 全17本を今回の必須条件にすることには反対。使用する control の patch だけ確認する。
- **P7:** 賛成。F546 の経路と拒否時停止を維持する。
- **攻撃が成立しなかった項目:** (a)〜(c) の骨格、9 protocol の consumer を覆う必要性、D297 の header 拒否という事実、patch 17本の列挙、P5の安価な runtime 復号、plan の依存構築方針、候補 source を指す YCSB proof surface、局所 `#line` 復元、bundle による候補保全。