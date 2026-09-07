## 所見

1. **real — 変異は焦点実行では狙った decode 失敗を作るが、コード上は seam より広い。**

   `_validate_read_purpose()` は変異後も先に実行され、旧 exact-24 lock は通常 decoder の exact-62 検査で直ちに拒否されるため、焦点の赤が後段処理との褹果になることはない (`artifact_admission.py:987-996`, `campaign_lock.py:327-339`)。一方、この helper は `_inspect_campaign()` だけでなく epoch-only 経路からも呼ばれる (`artifact_admission.py:1143-1146,1307-1308`)。また現行 exact-62 lock では返却型が変わり、commit blob、activation、WAL contract の型別検査も変わる (`artifact_admission.py:1009-1022,1156-1188,1371-1379`)。したがって「全入力について decoder 以外は不変」は誤りである。

   より忠実な対照は、焦点 call site `artifact_admission.py:1307` だけを `_decode_campaign_lock(lock_raw)` に戻す形である。これは D1653 直前の同 call site (`da44dc7b1^:orchestrator/campaign/artifact_admission.py:1141`) と一致する。D1653 前全体の再現ではないが、旧 lock はそこで失敗するので焦点因果には十分である。

   **反証条件:** helper に別 caller がなく、返却型による後段分岐もない版を示せれば、広すぎるという所見は反証される。

2. **refuted — 提示された `10 passed` が skip による空振り、という疑いは成立しない。ただし使用 root の所在地は未確定である。**

   file には test がちょうど10個あり、実 root を読む test は `test_throughput_ci_is_wal_t95_and_abort_has_no_ci_in_canonical_data` である (`test_plot_b10_extended_backoff.py:149,194,235,265,284,300,316,354,369,393`)。この test は不足時に明示的に skip し、通過時には `load_measurements()` を呼ぶ (`test_plot_b10_extended_backoff.py:60-71,194-198`)。よって「10 passed、skip 0」と関数数10の組み合わせは、この node が実行されて通過したことを含意する。さらに loader は admission 前に22入力すべての固定 SHA-256 を検査する (`plot_b10_extended_backoff.py:235-241,747-755`)。

   未確定なのは `IZANAGI_B10_MEASUREMENT_ROOT` による所在地の差し替えである (`test_plot_b10_extended_backoff.py:21-24`)。最小追加観測は、実行時の同環境変数と解決後 `MEASUREMENT_ROOT` の記録で足りる。証拠を直接的にするなら対象 node の `PASSED` 行も残す。

   **反証条件:** collection の差し替えや deselection により対象 node が未収集だったことを示す report があれば、この結論は反証される。

3. **real — 赤を旧 grammar に帰属させるには、最上位 message だけでは不足する。**

   必要な失敗署名は、外側が `ArtifactAdmissionError`、明示的な cause が `CampaignLockCodecError`、外側 message が通常 decoder 由来の `campaign.lock codec validation failed`、内因が `authority.contract_loader_blob_sha256s の exact key 集合が不正` であること (`artifact_admission.py:965-973`, `campaign_lock.py:333-339`)。加えて次を記録すべきである。

   - one-line 以外がない実行直前 diff と対象 HEAD。
   - 解決後 root、最初に失敗した lock の path と固定 SHA-256。
   - その lock の key tuple が pre-T733 tuple と完全一致すること。24個という数だけでは足りない。
   - 同じ baseline と変異走行が同じ node、環境、入力 digest を使ったこと。

   SHA-256 drift は admission より先に `B10FigureError` になるため、上記 chain が出れば入力 drift との識別力は高い (`plot_b10_extended_backoff.py:235-241,747-755`)。ただし workload は write-heavy から逐次処理されるので、最初の赤だけでは残り2 lock の通常 decoder 拒否を実走したことにはならない (`plot_b10_extended_backoff.py:75-103,754-755`)。

   **反証条件:** exact diff と pinned digest が同一なのに、別のコード位置から同じ例外 chain が生成された traceback が示されれば、署名による帰属は崩れる。

4. **real — 「旧 grammar が受入全走の失敗原因である」は時点と範囲なしでは言い過ぎである。**

   焦点 file の対が証明するのは、このHEAD、このpinned B10入力、このnodeにおける decoder 依存であり、現在の受入全走に他の赤がないことではない。2026-09-05 の全走で当該 node が唯一の赤だったことは別の一次記録である (`verbatim-worklog-1279.md:27-31,51-52`)。両者を結合するなら「2026-09-05 の観測された唯一の赤」まで限定できる。

   逐語案は次の1文である。

   「HEAD 542bfadb86b14625a99cca1bdef3583ea09a95ca の焦点 test では、同一の SHA-256 pinned B10 入力に対して現行 `HISTORICAL_RAW` decoder ありの baseline は通過し、その入口を通常 decoder に戻した対照は `authority.contract_loader_blob_sha256s` の現行 exact key 集合検査で失敗した。」

   **反証条件:** 同じHEADで受入全走を実行し、この失敗だけが赤で同じ chain を持つことを示せば、現在時制の全走主張まで引き上げられる。

5. **refuted — この負の対照を実行したこと自体が規律2違反、とは言えない。**

   規律2が禁じるのは、異常を通す方向へ正しさゲートを緩め、性能や fitness のために採用する変異である (`CLAUDE.md:67-71`)。今回の焦点入力では historical 受理枝を除去し、通常 decoder に拒否させるため、decode の受理集合は縮む。反証用 test だけに使い、正しい測定や certified 判定として採用せず即時復元する限り、禁止線は越えない。

   ただし変異箇所は正しさゲートそのもので、現行 exact-62 の historical 入力では後段検査も変わりうるため、焦点外の実行へ使ってよいとは言えない。また変異走行は過去の全走そのものではなく現在行った counterfactual として別記録にする必要がある (`CLAUDE.md:97-105`)。

   **反証条件:** 変異状態を通常測定、認証、性能評価へ使った、異常を新たに受理した、または復元せず残した事実があれば、規律2違反の判断へ変わる。

6. **real — (c)(d) だけから「旧 grammar の lock は13件」とは書けない。**

   旧 grammar は cardinality 24 ではなく exact ordered tuple である (`verbatim-D1653.md:24-25`; `campaign_lock.py:391-397`)。親の観測で完全な集合一致を確認したのは balanced だけで、他のB10 2件とA-2 10件は「keyが24個」という候補分類に留まる。balanced の sorted diff も wire orderとlock全体のcanonical性までは証明しない (`campaign_lock.py:392-404,596-604`)。同様に62個だけでも現行 grammar の証明にはならない (`campaign_lock.py:333-339`)。

   書ける上限は「指定したB10 rootとA-2 rootで24-key候補を13 path観測した」である。「旧 grammar 13件」とするには、各lockをstrict historical decoderで検証し、記録 grammarがpre-T733 tupleであることを13件すべてについて確認する必要がある。件数も「file path数」「unique SHA-256数」のどちらかを明記すべきである。

   全体数を主張するなら、検索範囲を絶対path、時刻、symlink方針、読めなかったdirectoryまで固定し、その範囲内の全 `campaign.lock` を同じstrict分類で走査する必要がある。別rootの不存在は、列挙した検索領域を越えては主張できない。

   **反証条件:** 13件全てのstrict decode結果と、宣言したartifact保管領域を漏れなく走査した記録が提示されれば、この過大計数の所見は反証される。

## 総括

焦点対は、最初のB10 lockについて必要な例外 chain、pinned digest、pre-T733 exact tupleを記録すれば、通常 decoder のgrammar拒否が赤の直接原因だと示せる。baselineの `10 passed / skip 0` は空振りではない。

一方、`if False` は共有helper全体を変えるため対照として広く、全走の現在的主張や旧lock総数13件までは証明しない。主張は焦点nodeへ限定し、13件は全候補のstrict分類が済むまでcardinality観測として扱うべきである。本回答ではテストを再実行していない。