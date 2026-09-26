## 所見

以下の `s1-brief.md`、`out/s2-plan.md`、`evidence/`、`verbatim/` は指定された job dir 内、checker・probe・insight は指定された worktree または単位 11 job dir 内の path を指す。今回は静的審査であり、合格や費用の実測は行っていない。

1. **must-fix／成立 — genome 文脈の保証範囲が曖昧。** plan は genome ごとに configure しながら、その genome の protocol の entry だけを「production 文脈」として採る。一方、実測では `CCBENCH_KEY_SORT` など一つの option が他 protocol の argv も変えた。従って、ある configure で生じた他 protocol の実効文脈は比較されない。根拠: `out/s2-plan.md:28-30,58`、`evidence/genome-configure-measure.md:9-15`。**放置時の成果物影響:** CCBench 全体の genome 文脈を覆うように読める certified の名乗りに対し、実際の受理集合は protocol ごとに抜粋した文脈だけになる。**代替案:** v2 で「どの configure のどの entry を選ぶか」を保証名と結果に明記する。全構成を主張するなら交差して変わる argv も比較対象に入れる。研究上の最小形なら stock の全 consumer と silo・mocc の必要文脈に限定し、他 protocol の genome 網羅を主張しない。

2. **should／成立 — 64 genome 一律の本走は、研究前進に対する最小形として過大。** TPC-C 段 1 の対象は silo・mocc で、mocc 空間の `KEY_SORT` は YCSB の live site に限ると定義されている。実測でも三つの configure の source entry 集合は同じで、argv の変化は target ごとに偏る。64 文脈 × 二 compiler × 旧新の configure を初手の必須範囲とする根拠はまだない。根拠: `out/s2-plan.md:30,85`、`evidence/genome-configure-measure.md:9-16`、`orchestrator/campaign/genome.py:123-140`。**代替案:** まず stock の全 consumer と silo・mocc の対象 argv を固定し、実効 argv が同一の文脈は比較を共有する。追加文脈が保証に必要かは、生成された argv と header 依存の差で決める。費用は「数 node 時間」を上限として提示せず、configure・生成 header・前処理を分けた計算実測後に示す。

3. **should／成立 — P7 の変異案には再演と既存拒否の確認が混じる。** H-line は単位 11 で実 CCBench の 9 TPC-C entry に対して検出済み。CMake 変更の拒否、`.cc` include 行不一致、比較件数不一致にも既存 checker の試験がある。新しい header consumer 規則の欠陥を識別する変異としては、間接 consumer、TRACE=0 値変更、条件付き include、consumer 0 件、予定集合からの比較脱落が中心になる。根拠: `s1-brief.md:18`、`out/s2-plan.md:70-83`、`output/insights/2026-09-26/t2854-unit11-combined/README.md:28-34`、`orchestrator/tests/test_check_trace0_preprocess_identity.py:370-381,623-687,733-743`。**代替案:** 既存拒否は回帰試験を維持し、新規変異は新しい受理分岐が誤って緑にする形だけに絞る。H-line は新分岐を通す代表負例として一度使えば足りる。

4. **should／成立 — 実装委任の問いに任意の実装形が入り過ぎている。** v3 schema、複数の新 CLI 引数、header 別依存関係の詳細記録、全組合せの fixture は、保証に必要な「選定集合・実行集合・比較結果を区別できること」の実現方法であって、規則そのものではない。report の意味を変えるなら版を上げる判断は妥当だが、承認事項で field 名や引数構成まで固定する必要はない。根拠: `out/s2-plan.md:12-14,40,70,91-92`、`tools/check_trace0_preprocess_identity.py:47,708-743`。**代替案:** 承認対象は受理条件、保証名、比較対象の選定、費用の測り方に限る。report は旧 `files` の意味を保ち、新分岐の証拠と予定・実行集合が判別できる形を実装時に選ぶ。

5. **should／成立 — 「全 TU 前処理には build が必要」は実測から言い過ぎ。** login で `config.h` 不在により `-E` が失敗した事実は、選ばれた走行に生成物が必要なことを示す。すべての consumer、すべての genome configure で独立した build 段が要ることまでは示さない。根拠: `s1-brief.md:23-27`、`out/s2-plan.md:42`。**代替案:** 計算 job で、選定 entry の前処理に必要な生成物を用意する、と記述する。生成物の共有と再利用の可否は本走の計時で決める。

6. **nit／成立 — 裁定の提示は二段階・二問で足りる。** D2249 は審査結果を見て規則承認と実装委任を裁定すると定めるが、両者を別々の問いにすることまでは要求していない。現在の三問案は、まだ無い pass と pin 波及確認を要する第 3 問を同じ提示に並べ、決める時点を見えにくくする。根拠: `verbatim/D2249.md:46-55`、`out/s2-plan.md:87-93`、`s1-brief.md:19`。**代替案:** 今は「提示した範囲・費用条件で規則を承認し、その実装を委任するか」を一問にする。C2′ pin 前進は pass と波及結果が揃った後の別問とし、その予定を成果物に記す。規則だけ承認して実装を留保したい回答も受けられる書き方にする。

7. **should／不成立 — compile database の全 entry を完全比較する方が単純で強い、という攻撃。** 全 entry を**母集合として走査**することは必要だが、変更 header に依存しない entry まで二種の完全前処理を比較しても、この header 差分の保証は増えない。第三者 TU や環境差による失敗と費用は増える。依存を旧新・TRACE 両値で列挙し、その和集合の consumer を比較する境界は合理的。根拠: `out/s2-plan.md:18-24`、`evidence/consumers-c2p.txt:1-24`。**代替案:** 全 entry の依存走査と、選ばれた consumer の完全比較を維持する。stock で直接 include 検索と 21 件一致した事実を、一般的な列挙方法の根拠には使わない。

8. **should／不成立 — probe をそのまま checker として使えば足りる、という攻撃。** `entries()` は直接 include の正規表現と固定 21 件に依存し、`preprocess()` も 21 件を前提とする。一方、compile argv の出力 option 除去、実 entry の鍵、stream 比較、計算 job の枠組みは十分に再利用できる。既存 checker には commit 間の diff 拒否と独立した test があり、probe の一走結果だけではその受理契約を置き換えられない。根拠: `probe/run_probe.py:317-375,377-421,553-583`、`tools/check_trace0_preprocess_identity.py:131-224,651-725`。**代替案:** probe の部品と job 手順を実装の出発点にし、consumer 選定と固定 21 件だけを規則に合わせて替える。

9. **should／不成立 — GCC 二版、consumer 非零、予定・実行集合の照合は削れる、という攻撃。** D297 は複数 compiler と比較 0 件の拒否を要求し、D2150 では GCC 11.4／12.3 を受容した。新分岐でも header ごとの consumer 非零と、列挙した比較の実行確認を欠くと、対象を落として緑にできる。根拠: `verbatim/D297.md:20-23`、`verbatim/D2150.md:26-32`、`out/s2-plan.md:22,38-40`。**代替案:** 二版と非零・予定集合照合を維持する。件数に加えて集合を照合すれば、詳細な件数 field の数は実装上整理できる。

10. **should／不成立 — 段 2 の header 変更には規則が効かない、という攻撃。** `tpcc_initializer.hh` は `tpcc.hh` から include され、TPC-C の silo・mocc source は `tpcc.hh` を読む。変更 header を依存出力で選ぶ規則なら、段 2 でこの header が M 差分になった場合も、該当 consumer が受理集合に入る。ただし合格は段 2 の実差分と文脈で再確認が必要。根拠: `external/ccbench/include/tpcc.hh:19`、`external/ccbench/cc/silo/tpcc_silo.cc:16`、`external/ccbench/cc/mocc/tpcc_mocc.cc:13`、`out/s2-plan.md:18`、`verbatim/D2249.md:50-55`。**代替案:** 「段 2 にも適用可能」と記し、「段 2 も合格する」とは記さない。

## 総括

- **成立した攻撃:** genome 文脈の名乗りと選定 entry のずれ、64 文脈一律の費用、再演変異、実装形まで含む委任案、build 必要範囲の一般化、三問を同時に並べる提示。
- **不成立の攻撃:** 全 entry 完全比較への置換、probe の無修正採用、GCC 二版・非零・予定集合照合の削除、段 2 の header が規則の対象外という疑義。
- **削れる部分:** H-line 等の変異再演、既存拒否の新規変異化、全 64 genome を初手の必須本走とする案、schema field・CLI 引数の裁定レベルでの固定。
- **規則案 v2:** M・mode 不変の header を対象に、選定 configure の全 compile entry から旧新・TRACE 両値の依存を取り、変更 header の consumer 和集合を作る。header ごとの非零と予定・実行集合の一致を要求し、選んだ実 argv の TRACE=0 完全展開・include 活性を GCC 二版で比較する。`.cc` の既存拒否は併用する。保証名には**選定した configure・entry に限る**ことを含め、D780 の「trace 完全除去の必要条件の一つ」を維持する。
- **承認事項案への修正:** 今は規則案 v2 の範囲と実装委任を一問で諮り、選定文脈と暫定費用を明示する。C2′ pin 前進は実装後の C→C2′ pass、実費、pin 波及を示してから別に諮る。成果物には未実測の GCC 12.3・genome 文脈、選定外の entry、費用の上限未確定を残る穴として記す。