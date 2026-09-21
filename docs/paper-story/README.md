# docs/paper-story/ — 論文ストーリーの横断合成

論文で「何を新規性として主張し、どういうストーリーで語るか」の横断合成を集約するディレクトリ。
`docs/roadmap-history/` や `docs/related-work/` と同じく、**凍結スナップショットを時点ごとに束ねる**構成。

## このディレクトリの位置づけ

- 各スナップショットは**特定時点の凍結物**（新規計測ゼロ・その時点の正典からの導出）。**書いた後は更新しない。**
  内容を更新したいときは上書きせず、新しい日付のスナップショットを追加する。
  ただし**新しい日付の版は、その日付時点の正典全体からの導出でなければならない。**
  一項目だけを直した差分改訂を新しい日付の版として置くと、更新しなかった項目の stale が
  「その日付時点でそう主張した」という新しい嘘に変わる。一項目の決着を届けたいだけなら、
  版を足さずに本 README の「最新スナップショット以後に確定したこと」で指す。
- **図 (`figures/`) も同じ凍結物である。** 複数の版が同じ path を共有するので、誤りが見つかっても
  上書きしない。後継図は別 filename で、再現可能な生成器を伴うときだけ作る。
- 日付なしの入口はこの `README.md`（ポインタは腐らない・スナップショットは腐る、の原則）。
- **正典（矛盾があればこちらが勝つ）:** `docs/roadmap.md` §8（ポジショニング）・`docs/decisions.md`（設計判断）・
  `docs/worklog.md`（時系列）・`docs/phase3.md` + `docs/phase3-main-experiment.md`（Phase 3 完了定義・事前登録）。
  本ディレクトリの文書はそれらの導出物。

## 版の履歴

| 日付 | ファイル | 時点 | headline |
|---|---|---|---|
| 2026-07-03 | `2026-07-03.md` | Phase 2 完了・Phase 3 kickoff 進行中 | 否定的結果 + 空間外合成（P2-4/P2-5） |
| 2026-07-10 | `2026-07-10.md` | Phase 3 段 5 完了（sort 軸 iteration 1 が実 LLM で E2E certified） | 同上（Phase 3 進捗を反映、図つき） |
| 2026-08-23 | `2026-08-23.md` | 縮小主張 S' が headline 不成立で確定（2026-07-16）した後。8b descriptor・層3 事実層 v2・8c bounded MVP・床値 protocol まで機構は進行、新 protocol による床値の実測は未取得 | 同上（第 3 幕を「機構は深化し性能主張は後退した」として再記述。未取得証拠の一覧を A/B/C の 3 群で付す） |
| 2026-08-26 | `2026-08-26.md` | A-3（P2-4 利得値）決着・後継図 fig2b 成立・A-1 探索走と反復数事前登録の凍結・A-2 driver とコスト実測・床値 pilot の 12 セル完走・8c 正式系列の閂の再特徴づけ（D930）の後 | 同上（科学的主張は前版から動かず、「あと何が要るか」の地図だけが変わった、として §6 と §8 を全面再導出。§9 の分類に「限定付きで取れた観測」を追加） |
| 2026-09-02 | `2026-09-02.md` | A-2 が正式 protocol を outer `reject` で完走した後。論文採用値の別 boot 再取得（D1100）・A-1 の estimand 揃え直し（D1262）・床値 official が起動不能であることの確定（D1396）・完了証明層の C10 開放・B-10 拡張格子と balanced profile・MoCC G2 再現率・軸 1 本検索の実行まで | **性能主張の側に、現行環境で正式に測って負けた点が 1 つ生まれた。** 第 2 幕の否定的結果と肯定的結果の対比を主軸に据える結論は前版から不変。§9 の要約を 3 文から 4 文へ拡張 |
| 2026-09-05 | `2026-09-05.md` | 説明可能性 (軸 3) の核を D1598 で 3 点へ書き直し、A-2 結果節 (`results/` 系列) と図 5 が凍結された翌日に、その走行の adopted cell が採用静的 backoff を build していなかったこと (F707 再発。D1645 で取り直しまで論文素材から外す) が確定した後。A-1 pilot 事前登録の発効・A-5 の Pegasus 不充足 (D1525)・A-6 の `indeterminate`・床値の量の確定 (D1639 / D1641)・人間手番の AI 委任 (D1638) と予算承認・鍵配置の実施 (1278)・B-10 balanced 完走と read-heavy 試し打ち成功・調整済み adaptive の正しさ認証・2 本目の論文系列の新設 (D1637) まで | **差別化の核は「対象がトランザクション CC・action vocabulary そのものの拡張・正しさゲートを毎反復」の 3 点で書く。忠実性・proof chain・試行 provenance は補助。** 前版が「現行環境で正式に測って負けた 1 点」と数えた A-2 は、採用構成についての判定ではなかった。採用構成を現行環境の正式 protocol で測った判定は無い。第 2 幕主軸の結論は不変。§9 の第 4 文を書き換え |
| 2026-09-14 | `2026-09-14.md` | 採用構成を現行環境の正式 protocol で測った判定が 3 workload とも出た後。A-2 の取り直し attempt が `observed-positive` (2026-09-07)・A-6 が完走して `reject` (2026-09-08)・balanced の stock-inline 対が `accepted` (2026-09-14)・A-1 の pilot 完走と反復数の確定 (n=30) と本走認可の据え置き (D1986 項5)・走行間ばらつきの下限が 3 workload 揃ったこと・official 床値 campaign の史上初の実投入 (未 land)・B-10 待ち方 grid の閉鎖 (D1678)・静的 tail 本走 driver の着地 (本走未投入)・文献調査 2 軸の停止 (D1760 / D1931)・mocc への証明面計装 (T-2294)・D1936 と D1986 の一括裁定まで | **前版が「採用構成を現行環境の正式 protocol で測った判定は 1 件も無い」と書いた空白が埋まった。** A-2 protocol (write-heavy と balanced の連言) は `observed-positive`、A-6 protocol (read-heavy) は `reject`、balanced の別の事前登録の対比較は `accepted` で、**符号は旧環境と 3 workload とも一致した — ただし再現判定ではない。** 但し書き 2 (性能 workload そのものでの採用静的 backoff の certification) は限定 4 つ付きで外れた。第 2 幕主軸の結論と S' 不成立は不変。B-1 (既知軸最良の超越) も不成立のまま |
| 2026-09-17 | `2026-09-17.md` | official 床値 campaign が初めて計測段を越えて完走し floor 案の実値が出た (2026-09-16、両 holdout とも配線下限 0.03 × stock 中央値、未発効)・B-10 静的 backoff 右 tail の本走が完走して集団判定が出た (2026-09-15、`not-observed-in-any-workload`)・B-7 の 3 走行材料がそろったが要件充足へは昇格しない (D2044 項3)・rr5 の accepted 較正で silo 3 workload セルが揃い非 silo 4 対の within-run floor が用途限定で登録された (D2083)・B-4 の材料 (記述統計追補 D2016、binary record と配置 D2069、`perf_config` の 3 項目と 3 cell と較正選別規則 D2088〜D2090) が増えたが A-5 の値待ちで実施不可のまま・D1640 の追補 (D2049)・fig7・identity 走査境界の到達実測 (T-2630、修正は裁定待ち)・K2 ループの 1 巡 (T-2588、既評価値の再提案)・A-1 認可据え置きの再確認 (D2044 項8)・D2044 (39 項) の一括裁定・8c manifest schema の `n` (D2071 / D2072)・ライセンス D1992 まで (local main `fa24e6ea8` から導出) | **前版が「未取得・未投入」と書いた 2 つの測定 (official 床値、右 tail 本走) が完走したが、どちらも肯定的 headline 主張を増やしていない。** 床値は配線下限で決まった未発効の案、右 tail は「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」という記述的な結末。正しさの identity 層に上限が 1 つ実測で加わり、exact claim の限定は D1993 の 4 つ + 1 つ。第 2 幕主軸の結論・S' 不成立・B-1 不成立は不変。前版を 3 か所で訂正した (執筆時点で偽だったもの) |
| 2026-09-19 | `2026-09-19.md` | A-1 balanced5 sized 本走の attempt-0001 が D2120 項 3 の 1 attempt 認可で投入され 3 workload とも完走した後 (2026-09-18、登録済み解析は 3 本とも `resolved-above-floor`、符号 +/+/−、非認証 lane のまま。単独稿と fig9)・stock mocc の G2 signal の 非 certifying 観測 3 件 (T-2774 witness off でだけ再現 2/40・3/40・2/40、T-2779 通常 5/120・診断 0/120・backoff 2/120、T-2780 discriminator の finalization 到達。D2148 項 13 = 上流報告まで)・Silo 固定スコープの解除 (D2114) と mocc 第 2 例の準備 (機械実証の設計 D2134 と wave 1 D2147、pin 前進の承認 D2150 項 1 = 未実施)・official 床値の g1 床としての採用裁定 (D2120 項 2) と g1 候補の実体化 (保存 branch) と chain land の不成立 (entry 1640) と A-3 整合 (D2154。chain 未取り込み・未発効)・B-4 spec 3 本の凍結 (D2138) と窓 job の資材 (D2145) と `PerfConfig` の出所 (D2146。実測未開始)・identity 層の上限の修正 (T-2731、D2108。残る限界は明記)・K2 2 巡目 (T-2746、事後承認 D2148 項 2) と機序仮説層 v3 の初適用 (D2143) と critic 診断の型付き入力経路 (T-2783、D2155。3 巡目未実走)・fig8 の成立・A-6 と T-1998 の単独稿・軸 1 の再開と限定付き閉鎖 (D2095 / D2120 項 14 / D2150 項 4)・一括裁定 4 回 (D2104 / D2120 / D2150 / D2148) まで (local main `a99425b66` から導出) | **前版が「本走未投入・認可据え置き」と書いた A-1 が非認証 lane の attempt-0001 として完走したが、「A-1 の値がある」とは書けず、肯定的 headline 主張は増えていない。** mocc は観測 3 件が出たが根因未同定・非 certifying で「第 2 成功例」ではない。床値は採用が裁定されたが未発効、B-10 は図が成立しても閉じていない。exact claim の限定は D1993 の 4 つ + identity の 1 つ (範囲は修正後に狭まった)。第 2 幕主軸の結論・S' 不成立・B-1 不成立は不変。前版の執筆時点の誤りは 0 件 |
| 2026-09-20 | `2026-09-20.md` | 採用静的 backoff の候補 2 genome (fixed 5 / fixed 10 µs) の検証相が Pegasus で完走し、両候補とも判定集合 30 verify (本走 24 + 校正完走 6) で `serializable`・certified・anomaly 0 (2026-09-19〜20、S-1 (iv 付属) の規則の準用、D2160、単独稿)・同一候補 fixed 5 µs を 3 workload で同時期に測る descriptive な attempt `b7f5-20260919a` が結果前固定の規則で read-heavy だけ床値超の退行 (−11.3787%、D2162、B-7 の材料稿、要件充足は判定しない)・B-10 静的右 tail の第 2 cohort (独立再現) が cohort 1 と同じ `not-observed-in-any-workload` (合成しない、D2157、単独稿)・A-1 sized の attempt-0002 が1 attempt 認可されたが既存 submit 経路の gate で qsub 前に拒否 (測定値なし、D2156、投入経路は [T-2792] 裁定待ち)・B-4 床値 w1 が凍結 spec 3 本で実投入され 3 job 完走 (集約・採用は未)・K2 3 巡目が critic 診断入りで実走 (縮小走行、同 job stock 対照は未達、[T-2795] 裁定待ち)・mocc 機械実証 wave 2 (D2159、30 check all_pass、n=1 弁別) と軽量 witness 4 arm (on 0/60・0/60、off 1/60・1/60) (探索・pin 前進は未解禁)・B-5 生成器対照の事前登録 v1 (D2158、未発効、[T-2797] 裁定待ち)・chain land 2 度目の不成立 (B-10 freeze-tree byte pin)・A-2 `nodes=5` の policy 実装・軸 1 の後継凍結記録 (78 leaf)・受入 pairing A/B 3 対 ([T-2766] 裁定待ち) まで (local main `b7f970dfa` から導出) | **前版が「未判定」「未投入」「未実走」と書いた項目のうち 6 つが動いたが、肯定的 headline 主張は増えていない。** 検証相は正しさ側の追加検証であって S-1 の充足でも B-8 の取得でもなく、性能値を含まず既存 certified 記録を昇格も降格もしない。同一候補の 3 workload 測定は B-7 の要件充足を判定しない材料。第 2 cohort は「再現されたので飽和しない」とは書かず B-10 は閉じていない。A-1 は「認可されたが gate で止まった」までで「A-1 の値がある」とは書けない。mocc は観測 4 件・非 certifying で「第 2 成功例」ではない。床値 official は未発効。第 2 幕主軸の結論・S' 不成立・B-1 不成立は不変。前版を 1 か所で訂正した (§3 項目 3 の見出し「仮説層は未実装」は D2143 (2026-09-18) 以後は偽で、前版の執筆時点で既に偽だった。段 6 レビューが検出) |
| 2026-09-20 (第 2 版) | `2026-09-20b.md` | 凍結 v2 g1 が発効した後 — chain / X2 / G が main に着地し (D2166、entry 1716)、承認 A と active pointer X を AI が作って発効 (13:2x のユーザー裁定、D2180、entry 1742。批准 loader は成功、full launch validation は既存不整合 2 件で `allowed: false` = [T-2810]、W-4 / W-5 は未、oracle 実走は未達)・B-7 が限定付き (単一 attempt・descriptive・非認証・反復間安定性は未判定) で充足と裁定 (D2174 項 3、fig10)・前版の裁定待ち 4 件が裁定 (第 24 回 D2172 13 項 / 第 25 回 D2174 7 項) され A-1 sized attempt-0002 の rear gate の exact な認可 record (D2178)・K2 同 job stock 対照の pair launcher (D2183)・B-5 の K2 共有部品が着地 (投入・試走は未)・B-8 事前登録 v1 (D2175、未発効)・verifier の容量改善 (D2181、10 s trace が完走、判定は bytes 同一)・単独稿 6 本 (mocc G2 観測条件 / mocc 軽量 witness 4 arm / K2 手動 loop 3 巡 / S-1a 9 対 / B-10 待ち方 grid 正式走 / 旧環境 P2-4 静的 backoff sweep)・図 5 本 (fig8b / fig10 / fig11 / fig12 / fig3b)・claim-evidence 2026-09-20 稿・mocc 追加実験の見送り (D2172 項 7) と上流報告案 ([T-2791]、未送信) まで (local main `fec4a8187`、同日 18:01 JST から導出。同日の 2 版目) | **前版が「裁定待ち」「未発効」「材料はそろった」と書いた項目が裁定と工程で動いたが、新しい測定は 1 件も無く、肯定的 headline 主張は増えていない。** g1 の発効は、配線下限で決まった床を持つ世代が AI 委任の A / X で active になったことであり (「AI が自己承認した世代」、論文での呼称は D2180 の対象外)、oracle 実走の前提は未達。B-7 の充足は報告要件についてで、候補の採用・認証・性能主張ではない。A-1 / K2 / B-5 は投入を可能にする機構が着地しただけで投入は 1 job も無い。第 2 幕主軸の結論・S' 不成立・B-1 不成立は不変。前版を 1 か所で訂正した (「『非列挙』の定義の置き直しは未裁定」は D1441 (2026-09-02) で裁定済みで、2026-09-05 版以降の 5 版で執筆時点で偽だった。前版自身が §8 B-5 で D1441 を引いており版内で矛盾していた) |
| 2026-09-21 | `2026-09-21.md` | A-1 balanced5 sized 本走の attempt-0002 (D2172 項 2 の 1 attempt 認可の独立再現) が exact な認可 record 経由で投入され 3 workload とも完走 (2026-09-20、[T-2792]、entry 1755、3 本とも `resolved-above-floor`、符号 +/+/− = attempt-0001 と同じ、`variance_plan_breach` は write-heavy / read-heavy で true、非認証 lane のまま、単独稿、図は無い)・ccbench pin が候補 `e9e477ca` へ前進 (2026-09-20、[T-2304]、D2184、entry 1747。mocc の R/W trace hook は pin に入ったが X/P 計装は patch のまま、旧系列は固定 checkout から)・第 26 回 /rulings D2186 (全 10 項、entry 1751) が B-8 の対象 = 案 A・定義・試走を段階認可し [T-2807] が発効前試走を完走して発効束を揃え発効 commit + 本走認可の 1 行再提示 (D2190、entry 1766、発効・校正・本走は未)・K2 同 job stock 対照の pair が初投入され不成立 ([T-2795]、D2187、entry 1754。候補 10 は certified、stock は one-shot claim leaf で停止、再投入なし、4 巡目未投入)・K2 3 巡の campaign 原本が cleanup 事故で消失 (F1034、entry 1759) し下流影響を [T-2815] が対応表で実測 (entry 1764。値・判定・稿・図は不変)・[T-1871] 追補 1 が着地し B-1 の実装残件なし (entry 1752)・B-4 の対応証拠は現存資料では 3 辺とも閉じないと確定 ([T-2632]、entry 1753)・B-10 待ち方 grid の forest 図 fig13 (entry 1763)・意味 witness 22 / 23 (D2189)・受入 pairing 既定 on (D2188)・closure 63 → 85 (D2193)・provenance の受領証 (D2192) と land の timeout 契約 (D2191)・本体論文の日本語草稿 4 本 (方法・結果考察・序論・関連研究) まで (local main `285477c00`、2026-09-21 00:21 JST から導出) | **前版が「投入は未」と書いた 3 件のうち A-1 attempt-0002 は投入され完走し (非認証 lane の descriptive 出力、新しい単独稿はこの 1 本)、K2 pair は投入され不成立 (候補 10 の追加評価は certified だが昇格させない)、B-5 試走は基準 HEAD では未。肯定的 headline 主張は増えていない。** 「A-1 の値がある」「再現した」とは書けない (2 attempt から何も計算しない)。pin 前進は工程で mocc の certified 系列・探索の解禁を含まない。B-8 は試走までで「取得した」「発効した」とは書けない。K2 は「対照が取れた」とは書けない。原本消失は値・判定を変えず「再検算できる強さ」だけを変える。第 2 幕主軸の結論・S' 不成立・B-1 不成立は不変。前版の執筆時点の誤りは 0 件 (段 6 レビュー 2 本も見つけなかった。0 件の証明ではない) |
| 2026-09-21 (第 2 版) | `2026-09-21b.md` | 第 27 回一括裁定 (D2194、entry 1771) が B-8 事前登録 v1 の発効と校正・本走の投入を承認し、K2 4 巡目の射影入力 (round 3 の派生物)・B-4 の耐久 carrier と参照点定義・enforcement source closure の次段 (発行器先行)・凍結 v2 g1 の未発効候補文書の削除・A-1 の 2 attempt の並記と L-A1S-4 の書き換えを裁定した後 (いずれも基準 HEAD では未実施)・B-5 生成器対照の上限付き試走 (β) が完走 (2026-09-20〜21、[T-2797]、D2198 / D2199、entry 1779。3 arm の score 4,002,540〜4,045,006 tps は floor 3.0% の内側、n = 1 系列 / arm の `not-applicable-pilot`、主標本外、本走は未認可)・凍結 v2 g1 の launch validator が official 成果物の現物形へ整合され historical reverify が段階 8 に到達 ([T-2810]、D2196、entry 1776。live は policy 照合で拒否、P3 は `allowed: false`)・本体論文 (日本語) の結果・考察草稿の 2026-09-21 版と要旨・結論草稿 (entry 1772)・運用側の着地 (変異の login self-run D2195、`/cleanup-branches` への F1034 の命令 [T-2814]、受入律速の分解診断 [T-2817]、Codex 子 branch の `-D` 経路 D2197 と F1036) まで (local main `5efd69367`、2026-09-21 05:25 JST から導出) | **A-1 の 2 attempt を「同一配置の反復で分類と符号が一致した観察」として §8 A-1 に並記し (6 cell とも `resolved-above-floor`、符号 + / + / − が一致、`variance_plan_breach` は attempt-0002 の write-heavy / read-heavy で true)、attempt-0001 稿の限定 L-A1S-4 を「2 attempt の観察に基づく限定」として読む書き方へ改めた (D2194 項 6)。解除ではなく、プールした推定量・差・比・再現判定は作らず、図も作らない。** 肯定的 headline 主張は増えていない。「A-1 の値がある」「再現した」「安定している」とは書けない。**裁定・承認は実施ではない** — B-8 の発効 commit・校正・本走、K2 4 巡目、B-4 の carrier、closure の次段、g1 候補文書の削除はいずれも未実施で判定は無い。B-5 の試走は主標本外で優劣を言わない。g1 の validator の整合は P3 の受理ではない。第 2 幕主軸の結論・S' 不成立・B-1 不成立は不変。前版の執筆時点の誤りは 0 件 (段 6 レビューも見つけなかった。0 件の証明ではない) |

**最新 = `2026-09-21b.md`。** 図は `figures/` に、2026-07-10 版の作成時に気づいた示唆は
`notes-2026-07-10.md` に分離。`figures/fig3_arc_status.png` は 2026-07-10 版（Phase 3 段 5 時点）の
現況図であり、2026-08-23 版以降の第 3 幕の記述とは一致しない（各版 §0 に明記）。

**この節は最新版の訂正だけを載せる。** 旧版が自分の前版をどこで訂正したかは、その旧版自身の
冒頭が持つ（凍結物なので、訂正の一覧も版と一緒に凍結されている）。

**2026-09-21b 版 (同日の第 2 版) が前版 (2026-09-21 版) を訂正した箇所は 0 件である (段 6 の敵対レビューも前版の執筆時点の誤りを見つけなかった)。**
前版の入口 (この README) が積んでいた stale 注記 2 件 (第 27 回 /rulings D2194、本体論文の日本語結果・考察草稿の 2026-09-21 版と要旨・結論草稿)
は、いずれも前版の導出起点 `285477c00` (2026-09-21 00:21 JST) より後に着地した事実で、前版の記述は執筆時点では真であり「当時は真で、
後続の前進が古くした」型である。2026-09-21b 版は 2 件を本文の該当節へ取り込み (下の移管先)、この節の注記から外した。前版の記述で古く
なった他の箇所 (B-5 の試走、g1 の launch validation の段階、[T-2810] の着地) も同じ型で、本文で現在地へ更新した。**0 件は誤りが無いことの証明
ではない** (下の「積んでいる項目の数は…」を参照)。前版 (2026-09-21 版) は自分の前版 (2026-09-20b 版) を訂正した箇所を 0 件と判定し、
2026-09-20b 版は自分の前版 (2026-09-20 版) を 1 件 (「非列挙」の定義の置き直しは未裁定、4 か所、2026-09-05 版以降の 5 版で執筆時点で偽) と
判定した (どちらの判定も各版の凍結物として残す)。2026-09-20 版が 2026-09-19 版を訂正した 1 件 (§3 項目 3 の見出し「仮説層は未実装」) と、
2026-09-17 版が 2026-09-14 版を訂正した 3 か所 (層3 screening の対象範囲、official 初投入日 2026-09-09、D1341 未 land の誤認) は、各旧版自身の
冒頭が持つ。

B-2 の `delta_min` について 2026-09-14 版が「受理集合を広げる向き」と書いた箇所は、引き続き誤りとは断定しない。
D2049 が定めるとおり、逆対応の逐語適用は片側の境界を過小に、他方を過大にするので、両 holdout を合わせた
受理集合が単純に広がるとは言えない。2026-09-17 版・2026-09-19 版・2026-09-20 版・2026-09-20b 版・2026-09-21 版・2026-09-21b 版は「片側についての説明」として限定して書く。

## 最新スナップショット以後に確定したこと（stale 注記）

スナップショットは凍結物なので腐る。ここは腐らない入口として、最新版の記述が既に古くなった箇所を
指す。**矛盾があればここが指す一次資料が勝つ。**

**現在この節に積んでいる項目は 2 件である (下の「積んでいる項目」)。** 2026-09-21b 版 (同日の第 2 版) は 2026-09-21 05:25 JST の local main
(`5efd69367`、worklog entry 1779 までの fold を含む) から導出している。前版 (2026-09-21 版) に対して積んでいた
2 項目は、いずれも 2026-09-21b 版が本文へ取り込んだのでここから外した。移管先は次のとおりである。

1. **第 27 回 /rulings (2026-09-21、D2194、全 14 項、entry 1771) が B-8 事前登録 v1 の発効と本走の投入を承認し、K2 4 巡目の入力元・B-4 の
   耐久 carrier と参照点定義・enforcement source closure の次段・凍結 v2 g1 の未発効候補文書の削除・A-1 の 2 attempt の並記と L-A1S-4 の
   書き換えを裁定した** → 2026-09-21b 版の冒頭 (第 1・第 2)、§0 の前進 1 と 2、§1、§2 第 1 幕・第 3 幕 (b) / (c) / (d) / (e) / (f) / (g)、
   §3 の導入と項目 2・4・5、§4 の図の注記、§5 の運用素材と設計判断、§6 の「言えること」「言えないこと」、§7 (更新 9 項と追加 7 項)、
   §8 の冒頭・A-1・A-4・B-2・B-3・B-4・B-5・B-6・B-8・C-1・C-4、§9、§10 の段 1 (P4 / P5 / P7)。**「裁定された」を「実施した」と書かない** —
   発効 commit・校正・本走、4 巡目、carrier の実装、closure の次段、候補文書の削除はいずれも基準 HEAD で未実施である。A-1 の並記は
   「同一配置の反復で分類と符号が一致した観察」として書き、L-A1S-4 は「2 attempt の観察に基づく限定」として読む (解除ではない)。
2. **本体論文 (日本語) の結果・考察草稿が 2026-09-21 版へ更新され、要旨・結論の草稿が新規起草された (2026-09-21、entry 1772、台帳 ID 未起票)**
   → 同版の §0 の前進 5、§5 の執筆材料 (注記)、claim-evidence 2026-09-21 稿の C43。**いずれも執筆者向けの草稿で、版の数値・状態語の出所に
   しない。採用時点は `285477c00` で、第 27 回 D2194 と B-5 の試走を反映していない。**

**積んでいる項目 (2026-09-21b 版の起点 `5efd69367` より後に着地したもの。着地順):**

1. **運用側の診断・収容が 5 件着地した (2026-09-21、entry 1780〜1781・1783〜1785)** — 変異 probe の login self-run 手順の被覆 (D2195 の後段)、
   計算ノード job の END → 待ち手の回収遅延の実測、受入全走を 2 回以上投入した wave の原因分類、焦点走の本数と wall の集計、T-2803 着地後の
   全史 provenance 監査の再利用可能性の事後診断。**いずれも運用素材で、2026-09-21b 版 §2 (e) / §5 の素材が増えるだけであり、論文の主張・判定・
   状態語は動かさない。**
2. **第 28 回 /rulings (2026-09-21、D2200、entry 1782、全 12 項) が B-5 生成器対照の本走を段階認可した (項 1)。** 2026-09-21b 版の §2 (b)・§6・
   §8 B-5・§9 と claim-evidence 2026-09-21 稿の C33 / C38 / L55 が「本走は未認可」と書くのは執筆時点 (起点 `5efd69367`) の事実である。
   D2200 項 1 は択 (a') 段階認可で、**発効束を完成させる AI 手番の範囲** ([T-2830] の job body の node-local lock と job ごとの submit-tree、
   Tier0 の実装、LLM arm の親運用の設計、事前登録 §12 の全項目、全 arm 同一の job walltime) を定め、**倍率・発効 commit・校正と本走の投入は
   完成した束と共に 1 行で再提示してユーザーが承認する**とした (B-8 の D2186 項 1 → D2194 項 1 と同型)。**段階認可は本走の認可ではない。**
   同項は試走で判明した 6 事項の扱い (perf 欠測の受容、rep 1 の warm-up 確認、endpoint 選択、方向契約、Tier0 は実装する、job ごとの
   submit-tree) も定めた。**同項の理由欄は、insight §8.2 の「LLM arm の親手番 1,080 巡」を 3 倍過大と独立に訂正している** (親の handshake は
   LLM arm だけが呼ぶので 36 系列 × 10 巡 = 360 巡 ≈ 60〜78 h。拒否なしの見積りで、A = 30 まで使えば最大 1,080 機会になりうる)。
   **2026-09-21b 版 §8 B-5 と §10 は、この 3 倍過大を段 6 レビューの指摘として独立に訂正しており、数は D2200 と一致する。** 同回の他の項
   (到達不能台帳 248 件の扱い、変異 final の batching と受入門番の据え置き、見送り 3 項の維持、[T-2821] の bundle 保全、push 承認、mocc 上流
   報告の継続) は版の状態語を動かさない。
**積んでいる項目の数は「最新版に誤りが有る」ことも「無い」ことも保証しない。** 移管した 2 件も積んでいる 2 件もいずれも「当時は真で後続が古くした」型であり、
執筆時点の誤りではない。2026-09-21b 版は前版の執筆時点の誤りを 0 件と判定し、前版も自分の前版について 0 件と判定したが、2026-09-20b 版が自分の
前版に執筆時点で既に偽だった記述を 1 件 (5 版連続)、2026-09-17 版が 3 件 (同版の冒頭) 見つけた型の誤りは、最新版にもありうる。
**次に正典が動いたら、その項目をここへ積む。** 2026-09-21b 版の起点より後に着地する見込みの項目 (D2194 項 1 の B-8 発効 commit・校正・本走、
同項 5 の g1 候補文書の削除、同項 2 の K2 pair 修復と 4 巡目、同項 3 の B-4 carrier、同項 4 の closure の次段、B-5 本走の認可、[T-2812] の
pin 系列整合、第 28 回 /rulings など) は、着地した時点でここへ積む。
**項目が積まれること自体は、新しい日付の版を作る要求にはならない** (D1858)。

**恒久の erratum は別の場所にある。**
`figures/fig2_backoff_mechanism.png` の baseline 誤 label（横破線に `stock adaptive backoff` と
書いてあるが、その値は無 backoff）と後継図 `figures/fig2b_backoff_sweep_3workload` への
乗り換え指示は、腐らない入口として `figures/README.md` が持つ。**旧図と、旧図を載せた
2026-07-10 版・2026-08-23 版のキャプションは凍結物なので訂正しない。**
**論文で P2-4 の図を使うときは後継図を使い、旧図を使わない。**

`figures/fig5_a2_certification_reject` の測定条件 erratum も同じく `figures/README.md` の fig5 節が持つ
(2026-09-07、D1645)。図が実際に比較したのは採用静的 backoff ではなく `BACK_OFF` の有効/無効であり、
**論文の A-2 の結論にも図にも使わない。** 図と provenance の bytes、キャプション正文は
凍結物なので訂正しない。
**取り直した attempt は 2026-09-07 に取れた (`t2364-20260907b`、outer `observed-positive`) が、
この制限は解除されない** — 下の追補が定めるとおり期限なしである。**新 attempt の図は
`fig6_a2_certification_observed_positive` であり、`fig5` の後継図ではない。**

**旧 fig5 の用途制限への追補 (2026-09-11、D1936項21・T-2521)。** 上記の D1645 に由来する
「取り直しまで」「正しい identity で取り直した attempt」という期限は、当該旧図には適用しない。
**採用静的 backoff に関する A-2 の結論・図として使えない制限は期限なしである。** 新 attempt の取得は、
旧図が比較した `BACK_OFF` の有効/無効を変えない。旧図の利用範囲は訂正済みの当時の測定対象と判定に
限る。詳細は `figures/README.md` の「追補 — 旧 fig5 の用途制限に期限を設けない」を正本とする。
旧画像・provenance JSON・統計・凍結稿・キャプション正文は保持する。

## 読み方

- 論文執筆・ポジショニング検討のときに読む。日常セッションのブートには不要（ブートコスト規律 D35）。
- 各版の §（過大主張チェックリスト）は執筆フェーズで消し込み式に運用してよい唯一の例外。
- **旧 Phase 3 主実験（phase3.md 後続段 6）は 2026-07-16 に完了し、縮小主張 S' は不成立で
  確定した。** 「主実験が成立すれば headline がそちらへ移る」という以前の見通しは、
  そのままでは使えない（正本 = `output/reports/s_prime_final_report.md`、
  および最新版の §2 第 3 幕 (a) と §6）。新しい headline 候補が実際に成立したときは、
  その時点で新しい日付のスナップショットを追加する。

## claim-evidence 系列（`claim-evidence/` サブディレクトリ）

**版とは別系列の、執筆者向けの作業表を置く場所。** 版が「その時点で何を語るか」を書くのに対し、
こちらは「主張 1 件ごとに、何を書けて、何がそれを弱めているか」を並べる。
版と混ぜないために **filename ではなくディレクトリで分ける。**

| 日付 | ファイル | 内容 |
|---|---|---|
| 2026-08-26 | `claim-evidence/2026-08-26.md` | claim-evidence matrix（科学的主張 / 運用・方法論の証拠 / 文献 guardrail の 3 表）、限定レジストリ `L01`〜`L28`、limitations 節の日本語統制稿 |
| 2026-09-21 | `claim-evidence/2026-09-21.md` | 2026-09-21b 版の §3 / §6 / §7 / §8 / §9 全体から作り直した 3 表 (前稿の行 `C1`〜`C37` を継承し `C38`〜`C43` を追加 — B-5 の上限付き試走、B-8 の段階認可と承認、第 27 回一括裁定、運用側の着地、図の着地、日本語草稿)、限定レジストリ `L01`〜`L53` を継承し `L54`〜`L64` を追加 (A-1 の 2 attempt の並記と L-A1S-4、B-5 の試走、裁定 ≠ 実施、g1 と validator、B-7 の限定付き充足、pin 前進の射程ほか)、読み違い防止を 8 条から 9 条へ (G9 = 裁定・承認を実施と読まない)、limitations 統制稿の更新、前稿との対応表 (§7)。**継承した `L36` (attempt-0002 は未投入) と `L48` (起点) は、後続の着地に合わせて本文を書き換えた (ID と趣旨は不変)** |
| 2026-09-20 | `claim-evidence/2026-09-20.md` | 2026-09-19 版の §3 / §6 / §7 / §8 / §9 全体から作り直した 3 表 (行 `C1`〜`C37`、現行環境の A-2 / A-6 / T-1998 / A-1 attempt-0001 / B-10 cohort 1・2 / official 床値案 / 採用候補の検証相 / B-7 fixed5 / mocc 観測 4 件を追加)、限定レジストリ `L01`〜`L28` を継承し `L29`〜`L53` を追加、limitations 節の統制稿の更新、前稿との対応表 (§7)。未着地の図・裁定待ち 3 件 (T-2792 / T-2795 / T-2797) は完成扱いしない |

**T-1998 単独稿の読解上の追補 (2026-09-18、回収時の独立監査):**
`2026-09-18-t1998-balanced-stock-inline-accepted.md` §0.1 の「投入は 1 回だけ」「2 本目の試行は存在しない」は、
指定 receipt と 2026-09-13 / 09-15 の wave 記録から確認した 1 試行を指す。他の投入の不存在を網羅的に
保証するものではない。事前登録 §7 は投入回数の規則であり、不存在の証拠ではない。凍結稿・測定値・consumer 判定は保持する。

**この系列の規則。**

- **append-only。書いた後は更新しない。** 版と同じ凍結物である。
- **新しい日付を足すときは、入力 5 節（最新版の §3 / §6 / §7 / §8 / §9）全体から作り直す。**
  一項目だけを直した差分改訂を新しい日付として置かない（版と同じ理由 — 更新しなかった項目の
  stale が「その日付時点でそう主張した」という新しい嘘に変わる）。
- **「版の履歴」表には登録しない。** これは版ではない。どちらが全面再導出された版かは
  ディレクトリで判別する。
- **数値・日付・判定の出所は一次資料だけとする。** 版の記述を数値の出所にしない。
- 版と同じく `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外である。

**C14a の所在調査の追記 (2026-09-18、[T-1878])。** 2026-08-26 稿は変更せず、今回の探索結果をここに記録する。claim-evidence matrix の
新稿ではない (一項目だけを直した新しい日付の稿は規則 2 が禁じる)。矛盾があれば下で指す一次資料が勝つ。

- **C14a の `[権威 bytes]` は 2026-09-18 時点でも未特定 — 探索した範囲での未特定であり、全体での不在の断定ではない。**
  2026-08-26 稿の C14a 行 (mocc trace-hook TRACE=1 pilot、PBS `934607.nqsv`、outer `2efe6282`) が `[権威 bytes]` を「未特定」と書いた件を、
  pilot の insight 5 群が名指す job dir 9 件、`/work/1/SFC/tanab/izanagi-job-evidence/` 配下、`tools/pegasus/mocc_trace_pilot.sh` の出力先に
  限って探索した結果、raw `verifier.json` もその sha256 も特定できなかった。当時の script の出力先は投入 worktree
  (`dev-wave-t755-mocc-trace-execution`) 配下の `output/env/pegasus/mocc-trace/job-staging/$PBS_JOBID/` (request 934607 の実表記は
  `934607.nqsv` か `0:934607.nqsv`) で、同 worktree は現在存在しない。探索時点の全 ref から辿れる履歴に同 path を触る commit は無く、
  evidence dir と名指し job dir (50 MiB 以下の全 file の本文と path 名) にも raw も退避物も特定できなかった。当時の receipt 生成処理は
  `verifier.json` を名前で指すだけで sha256 を束縛していなかった。消失の経緯と過去の保存履歴は確定していない。insight に埋め込まれた
  JSON block は raw の逐語ではない (当時の verifier `--json` が出す `trace_dir` など 3 key を欠く) ので、その sha256 を `[権威 bytes]` の
  代わりに書くこともできない。一次資料 = `output/insights/2026-09-18/t1878-mocc-trace-pilot-raw-artifact/README.md` (探索範囲・方法・
  結果と、探索していない範囲)。**変わらないこと:** C14a の判定値 (`serializable` / `certified` 真 / anomaly 0) と `[導出索引]` は
  2026-08-26 稿のままで、C14a を引くときは「raw artifact 未特定 (insight 転記のみ)」の限定を外さない。2026-08-26 の pair wave の
  TRACE=1 leg (`0:949961.nqsv` / `0:949963.nqsv`) には raw と sha256 があるが、別 request の観測であり C14a の行に流用しない。

## results 系列（`results/` サブディレクトリ）

**版とも claim-evidence とも別の、結果 1 件ごとの結果節の材料を置く場所。** 版が「その時点で何を語るか」、
claim-evidence が「主張ごとに何を書けて何が弱めているか」を書くのに対し、こちらは
**完走した 1 つの protocol / campaign の結果を、論文の結果節・表・図・限定の形へ落とした統制稿**を置く
（一次資料に束縛した執筆者向け統制稿。D12 が定める機械射影の材料レポートではなく、投稿本文でもない）。
版と混ぜないために **ディレクトリで分ける** (D1013 と同じ理由)。

| 日付 | ファイル | 対象 | protocol status |
|---|---|---|---|
| 2026-09-04 | `results/2026-09-04-a2-certification-reject.md` | A-2 正式 certification (attempt `t2022-20260828c`、write-heavy / balanced の exact 4 cell、図 5、限定 11 件) | outer `reject`。correctness は別の trace-enabled run で 4 cell とも certified (性能の判定ではない)。**測定条件の記述に誤りがあり、2026-09-07 の稿が改めた (下記)。執筆材料には使わない** |
| 2026-09-07 | `results/2026-09-07-a2-certification-reject.md` | 同じ attempt `t2022-20260828c` を一次資料全体から作り直した改訂稿。**測ったのは採用静的 backoff ではなく CCBench 内蔵 backoff の有効/無効** (`BACK_OFF=1` 対 `0`) である。限定 15 件 (D1645、F707 の再発) | outer `reject` は不変。**同じ attempt の執筆材料にはこの稿を使う。**2026-09-04 の稿は append-only の履歴として残る |
| 2026-09-07 | `results/2026-09-07-a2-certification-observed-positive.md` | D1644 の pin + patch 束縛 `src_token` で identity を計算する driver で取り直した**別の attempt** `t2364-20260907b` (write-heavy / balanced の exact 4 cell、図 6、限定 6 件)。上の 2 行とは測っている条件が違い、前後比較として読んではならない (絶対規律 7) | outer `observed-positive`。correctness は別の trace-enabled run で 4 cell とも certified (性能の判定ではない)。**この attempt の執筆材料にはこの稿を使う** |
| 2026-09-09 | `results/2026-09-09-a2-certification-observed-positive-en.md` | 直上の 2026-09-07 observed-positive 稿の**英語稿**。同じ attempt `t2364-20260907b` について、事実命題を足さず一次資料へ再照合して英語で書き直したもの ([T-2329]) | outer `observed-positive` (直上の稿と同一)。日本語稿を改めるものではなく、どちらも凍結物として残る |
| 2026-09-14 | `results/2026-09-14-b7-all-workload-regression.md` | 見送り台帳の項目 B-7 (全 workload の退行込み報告) の材料。現行環境・正式 protocol で判定の出ている 3 workload の 6 cell を、**2 つの attempt に分かれた記録のまま横断で併記する** (`t2364-20260907b` の rr5 / rr50 と `a6-20260908b` の rr95、生標本 6 cell、限定 11 件)。単位は失敗条件 (e) が報告を求める「全 workload」の集合。**2 attempt を統括する単一の正式実験は存在しない** | 単一の outer status を持たない。所属 attempt の status をそのまま併記する (rr5 / rr50 は `observed-positive`、rr95 は `reject`)。**B-7 の充足も床値超の退行も判定せず、D1645 の解除は 2026-09-14 版の判定を引き写すだけである** |
| 2026-09-16 | `results/2026-09-16-b7-three-run-materials.md` | 同じく見送り台帳の項目 B-7 の材料。**直上の 2026-09-14 稿が対象外とした [T-1998] の balanced stock-inline 対を加え、3 走行・4 対比較・8 arm を一次資料から作り直して併記する** (`t2364-20260907b` の rr5 / rr50、`a6-20260908b` の rr95、別事前登録 v1 の balanced 対、生標本 8 arm、限定 20 件)。**直上の稿を改めるものではない** — 同稿は 2 attempt・6 cell の材料として有効なまま残る。3 走行を 1 file に収めたのは編集判断であり、系列の規則がそれを要求しているわけではない | 単一の outer status を持たない。所属する走行の出力をそのまま併記する (rr5 / rr50 は A-2 outer の `observed-positive`、rr95 は A-6 outer の `reject`、[T-1998] は consumer の `accepted`。producer 側の `complete` とは別)。**D1993 項 6 に従い 3 走行をプールせず、B-7 の充足も床値超の退行も判定しない。A-1 が定める横断実験の代わりにもしない** |
| 2026-09-16 | `results/2026-09-16-b10-static-tail-not-observed.md` | 見送り台帳の項目 B-10 (機序説明の帯域外への拡張) のうち、静的 backoff 右 tail の本走 1 cohort (group `b10-backoff-grid-20260915T061814Z-545445`、`run_kind` `t2500-tail-formal`、事前登録 `docs/b10-backoff-static-tail-preregistration.md` の commit `cad6f46d8` に束縛、3 workload × 8 点 = 24 cell、性能 120 rep・正しさ 120 記録、生標本 24 cell、限定 15 件)。**言い方は事前登録 §4.5 の固定表現に限る** — 「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」。「飽和しない」「飽和点が存在しない」とは書かない。図は無い (`fig2c` は別 cohort)。**この cohort の執筆材料にはこの稿を使う** | 集団 `verdict` は `not-observed-in-any-workload` (3 workload とも `not-observed`、18 区間すべて `declining`、局所平坦区間 0、`failures` 空)。correctness は trace-enabled の別走行で 120 記録とも certified・anomaly 0 (性能の判定ではない)。**`performance_certified: false` のままで、性能値を採用根拠にしない。機序・9999 マイクロ秒より右・他 cohort との関係は書かない** |
| 2026-09-18 | `results/2026-09-18-a6-certification-reject.md` | A-6 read-heavy 正式 certification (attempt `a6-20260908b`、request `982234.nqsv`、2026-09-08、rr95 の exact 2 cell = stock `BACK_OFF=0` 対 採用静的 backoff 2 µs、生標本 2 cell、限定 12 件、図は稿の執筆時点では無く 2026-09-20 に図 11 `figures/fig11_a6_certification_reject` を追加 — 稿 bytes は不変、下の追補)。**1 attempt の一次資料全体 (権威 bytes・raw manifest・WAL・受領証・裁定) から作った単独稿**で、同じ rr95 の値を併記する横断稿 (2026-09-14 / 2026-09-16 の B-7 稿) を出所にしない ([T-2611])。B-10 read-heavy 本走 3 block との同符号・同程度は近接条件の別実行による履歴的照合であって再現ではなく、反復 attempt は行わない ([T-2430])。実行基盤測定の −4.876% は attempt に数えない (D1870)。限定は D1993 項 3 の (i)〜(iv) に identity 層の (v) ([T-2630]、D2108) を加えた 5 つを含む | outer `reject` (効果 −5.7841%、`a4_noise_floor_status` は `open`、有意差判定なし)。correctness は別の trace-enabled 走行で 2 cell とも certified (性能の判定ではない)。**性能の `reject` は正しさ証拠の欠落ではない (D1993 項 2)。この attempt の執筆材料にはこの稿を使う** |
| 2026-09-18 | `results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` | A-1 balanced5 sized 本走 attempt-0001 (study `paper-story-a1-20260901-balanced5-sized-v1`、job `4939` / `4940` / `4941`、2026-09-18、source `d2ebef7a4`、3 workload × 30 対 × 2 arm = 生標本 180、限定 20 件、図 9)。**1 attempt の一次資料全体 (公開 leaf の result.json / receipt.json / .complete.json、campaign WAL 3 本、事前登録、policy v3、裁定) から作った単独稿**で、stale 注記・記録 insight・版を数値の出所にしない ([T-2611] / [T-2674] の型)。登録済み解析の descriptive 出力 (対差平均 ± h と床 ±B の分類) を書き写す。**A-1 の充足・formal 化・再投入・再認可は判定しない** (認可はユーザー手番、D2044 項 8)。図 9 は本稿を `caption_source` として束縛するので、稿は provenance の sha256 を持たない (F36、正本は `figures/README.md` の fig9 節) | 単一の outer status を持たない非認証 lane (`formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only`)。登録済み解析の分類は 3 workload とも `resolved-above-floor` (対差平均の符号 write-heavy 正 / balanced 正 / read-heavy 負、`variance_plan_breach` false ×3)。correctness は別の trace-enabled verify で 6 arm とも certified・anomaly 0 (性能の判定ではない)。**headline 値・workload 横断の結論・C1 の再現判定にせず、単一 attempt を反復間の安定性へ一般化しない。この attempt の執筆材料にはこの稿を使う** |
| 2026-09-18 | `results/2026-09-18-t1998-balanced-stock-inline-accepted.md` | [T-1998] balanced の stock-inline 対 (無 backoff 対 静的 fixed 5 µs) の**単独稿**。事前登録 `docs/t1998-balanced-stock-inline-preregistration.md` v1 の下の 1 試行 (job `995755.nqsv`、測定 2026-09-13、認証 2026-09-14、着地後 main での再解析 2026-09-15) を、2026-09-16 の横断稿から引き継がず一次資料 (権威 bytes・campaign lock と WAL・事前登録・裁定) から作り直した ([T-2674]、D2120 項 15 の型)。生標本 2 arm、限定 20 件。成果物に無い情報・束縛の範囲・本稿で未照合の対応は §4 に区別して明記。図は無い | consumer の **`accepted`** (reason `preregistered-balanced-stock-inline-pair`、ratio 1.1122537536191646、improvement_percent 11.225375361916456)。producer 側の `complete` とは別の出力。**各 arm 5 標本の median 比であって A-1 の対差平均ではなく、A-2 / A-6 とプールせず (D1993 項 6)、B-7 の要件充足でもない (D2044 項 3)。有意差判定でも区間推定でもない。** correctness は campaign WAL の `verify_done` で 2 arm とも `serializable` / `certified` / anomaly 0 (legacy 条件 1 回ずつ。性能の判定ではない) |
| 2026-09-19 | `results/2026-09-19-b10-static-tail-cohort2.md` | 見送り台帳の項目 B-10 (機序説明の帯域外への拡張) の静的 backoff 右 tail について、**主結果 (2026-09-16 稿の cohort 1) に対する独立再現 = 第 2 cohort** (group `b10-backoff-grid-20260919T131526Z-2235286`、`run_kind` `t2500-tail-formal`、job `10752` / `10753` / `10754`、2026-09-19、事前登録の 2026-09-19 追記込み commit `8737cacb4` に束縛、3 workload × 8 点 = 24 cell、性能 120 rep・正しさ 120 記録、生標本 24 cell、限定 16 件)。地位は結果を見る前に事前登録追記 (D2050 の充足、ユーザー決定 2026-09-19) で固定: cohort 1 の verdict を主として保持し、第 2 cohort の verdict は再現欄 (同稿 §2.6) に併記、**合成しない**。投入時に失敗した attempt 1 (依存 source 不在、測定なし) を §1.5 に開示。file 名は結果前に中立名で固定。**2026-09-16 稿を改めるものではない**。図は無い (fig8 は cohort 1 の図。再現欄の追加は生成器の改変を要し別 wave) | 集団 `verdict` は `not-observed-in-any-workload` (3 workload とも `not-observed`、18 区間すべて `declining`、局所平坦区間 0、`failures` 空)。cohort 1 と同じ verdict だが、**言い方は事前登録 §4.5 の固定表現に限り「再現されたので飽和しない」とは書かない**。correctness は trace-enabled の別走行で 120 記録とも certified・anomaly 0 (性能の判定ではない)。**`performance_certified: false` のままで、性能値を採用根拠にしない。2 cohort の統合 verdict・プール推定・またぐ有意水準は作らない** |
| 2026-09-19 | `results/2026-09-19-b7-fixed5-three-workload-regression.md` | 見送り台帳の項目 B-7 の材料。**同一候補 (静的 backoff fixed 5 µs = T-1998 事前登録の採用 arm と同じ genome・同じ source bytes digest) を 3 workload で同一 attempt・同時期に測り、各 workload の同 campaign 内 stock 対照との対差を D1639 の between-run 床値と比べた単独稿** (study `paper-story-b7-fixed5-regression`、attempt `b7f5-20260919a`、request `10807` / `10808` / `10809`、2026-09-19、source `c18a80967`、6 cell × 5 標本、限定 14 件、図 10)。A-2 / A-6 と同じ certification 経路を descriptive に使った別 study instance で、既存 2 policy は不変。図 10 は本稿を `caption_source` として束縛するので、稿は provenance の sha256 を持たない (F36、正本は `figures/README.md` の fig10 節)。既存材料 (2026-09-16 稿、workload 別採用値 10 / 5 / 2 µs) とは表を分けて併記し、プールしない。**判定規則 (対差 < −床値 で退行、床値 = JSON 全桁) は結果を見る前に固定** (ユーザー裁定 2026-09-19) | 機構の outer status は `reject` (3 workload の論理積、read-heavy の負の効果の帰結)、`a4_noise_floor_status` は `open`。稿の床値判定: write-heavy +67.8968% / balanced +12.6717% は退行なし、**read-heavy −11.3787% は床値 (−0.2228%) 超の退行**。correctness は別の trace-enabled 走行で 6 cell とも certified・anomaly 0 (性能の判定ではない)。**B-7 の要件充足は判定しない (D2044 項 3)。certification の昇格でも有意差判定でもない。この attempt の執筆材料にはこの稿を使う。** 追補 (2026-09-20、D2174 項 3): 稿の外で B-7 は**単一 attempt・descriptive・非認証・反復間安定性は未判定**の限定付きで充足と裁定され、D2044 項 3 の「要件充足へ昇格させない」はこの限定付き充足で supersede された (上の stale 注記)。稿本文は凍結のまま |
| 2026-09-20 | `results/2026-09-20-verify-phase-adopted-backoff.md` | 採用候補 2 genome — fixed 5 µs (T-1998 v1 target = A-2 rr50 採用値) と fixed 10 µs (A-2 rr5 採用値) — の**検証相** (trace-enabled build、write-heavy / balanced / read-heavy 各 8 独立反復、extime 3 s、計 48 verify + 校正 18 記録 (実走 16)、Pegasus gen_S、2026-09-19〜20)。S-1 事前登録 (iv 付属) の充足ではなく、2026-09-19 のユーザー裁定で対象を変え同節の反復数・校正規則・判定規則を**準用**した追加検証。identity は現行 patch の source digest に束縛 (fixed-5 は T-1998 v1 と bytes 一致、fixed-10 は A-2 と同 genome だが source bytes は `91a5bfca3` 分だけ異なる)。限定 9 件。図は無い。**この検証相の執筆材料にはこの稿を使う** | 候補ごとに runner の機械判定 **`pass`** (判定集合 30 verify = 本走 24 + 校正完走 6、全件 `serializable`・certified・anomaly 0。校正 10 s の未完走 2 件は verdict を持たず開示のみ)。操作的事実であって 1−εⁿ の確率主張ではなく、性能値を含まない (規律 1)。A-2 / T-1998 / A-6 の certified 記録の昇格・降格はしない (規律 7) |
| 2026-09-20 | `results/2026-09-20-mocc-g2-observation-conditions.md` | stock mocc の G2 signal の**観測条件の分離** ([T-2779]、runner v5 `t2779_probe.py` の非 certifying 観測 1 試行 = 段 4 裁定で結果を見る前に固定した単一の観測 protocol の完走、witness off に固定した 3 arm = 通常 X/P 計装 / 診断 patch / `BACK_OFF=1` × 4 block (request `5894` / `5895` / `5897` / `5898`、2026-09-18) × 30 round = 各 arm 120 走、固定 cell 3 s・48 thread・10,000 record・rratio 50・zipf 0.9、producer = hook branch 先端 `e9e477ca` + X/P 計装 patch (D1686)、TRACE=1 観測専用、限定 18 件、図は無い)。**1 試行の一次資料全体 (job dir の 4 block `result.json`・360 走の run / verifier JSON・G2 7 走の trace-manifest と生 trace 336 file・段 4 裁定 = 事前登録・dispatch の NQSV 要約、insight の `summary.json`) から作った単独稿**で、横断稿・版を数値の出所にしない ([T-2611] / [T-2674] の型)。限定を先頭に置く: 非 certifying・TRACE=1 観測専用・pin 前進なし (D2150 項 1 は承認済み未実施、D2159 は認可しない)・頻度差から `BACK_OFF=1` の抑制効果や正しさを結論しない・G2 signal の再現を根因確定としない (D2148 項 13 = [T-2791] の限定)。witness 軽量化の静的設計とその後の実走は本稿の対象外 | 単一の outer status を持たない非 certifying 観測。runner の機械集計 (`summary.json`) は **通常 5/120 (CP 95% [1.3665%, 9.4559%])・診断 0/120 ([0%, 3.0273%])・`BACK_OFF=1` 2/120 ([0.2025%, 5.8909%])**、介入側が低下する方向の片側 Fisher (未調整) は診断 0.0299507441 / backoff 0.2230864755。事前登録の言い方は前者「固定条件で 2 変更を束ねた介入と検出率低下が整合する」まで、後者「この標本・条件では低下を検出できない」まで。family 全体の有意性・G2 不在・根因同定は主張しない。7 件の signal は全件 G2・長さ 2・両辺 rw、生 trace 保全済み、discriminator は全走 `not-run` (witness off)。certified 昇格・pin 前進・変異探索・規律 2 の即 reject 契約は不変 |
| 2026-09-20 | `results/2026-09-20-mocc-witlight-four-arm.md` | stock mocc の軽量 witness (hook commit W `5b02546f`、branch `izanagi-t1943-mocc-g2-witlight`、`e9e477ca` の子、GitHub 未 push) を実装した wave の**本走 4 arm (witness on / off × BACK_OFF 0 / 1) × 各 60 走** (4 block = request `10827` / `10828` / `10835` / `10837`、2026-09-19 22:35〜23:02 JST、pin `e9e477ca` + [X/P、測定 patch] の TRACE=1 観測専用 build、smoke 4 走は分母外、限定 11 件、図は無い)。**1 wave の一次資料全体 (job dir の走ごとの JSON・集計・会計・事前登録・検査 log・hook commit の git object、記録 insight の逐語) から作った単独稿** ([T-2611] / [T-2674] の型) で、README 追補 (entry 1696)・worklog・版を数値の出所にしない。書くのは「この診断で何を識別できたか」(同稿 §2.8): 4 arm の完全収載、on 0/60 ×2、off 1/60 ×2 (G2・長さ 2・両辺 rw)、discriminator 未発火 (問い (ii) は識別対象 0 件で未到達)、W の TRACE=0 preprocess identity、smoke 正例の witness 文法、曝露量 on/off 0.864 / 0.845。検出力 0.105 は off 率 0.0417 ([T-2779] 通常 arm) 対 0 の完全抑制・片側 α=.05・K=60 の条件付き計算で上限として明記 (「80%」は率 0.119 の条件付き計算)。smoke 合格集合は結果前固定。mocc の稿はこれが最初 | 単一の protocol status を持たない**非 certifying の観測記録**。主比較 (BACK_OFF=0) も副比較 (BACK_OFF=1) も on 0/60 対 off 1/60、片側 Fisher 未調整 **p=0.500**、discriminator 発火 0 件。**p=0.500 と on 側 0 件を同等性・効果なし・G2 不在の証明にしない。TRACE=1 観測専用 (合成 source の TRACE=0 identity は未担保)。certified 昇格・pin 前進・変異探索は認可されていない (ユーザー決定 2026-09-19)。commit 数の比は曝露量であって性能主張ではない (規律 1)。[T-1892] / [T-2774] / [T-2779] と合算しない (規律 7)。個別 verifier の `certified=true` 238 件は認証ではない** |
| 2026-09-20 | `results/2026-09-20-k2-manual-loop-three-rounds.md` | 見送り台帳の項目 B-6 (リーク制御を完備した状態での実走) の材料。**K2 手動 loop の 3 巡 = 提案 → 評価 1 本 → critic を 3 回** (2026-09-16 [T-2588] / 09-18 [T-2746] / 09-19 縮小走行、campaign ID `409e13f8` は 3 巡とも同一だが別 submit-tree・別 WAL、評価 job `1216` / `4954` / `10761.nqsv`、提案値 20 / 25 / 10、計 3 評価 + preflight 拒否 1 投入) を、各巡の proposal JSON・role 逐語・campaign WAL・受領証・材料レポート・裁定 (D2044 項 9 / D2120 項 1 / D2148 項 2・3 / D2155 / ユーザー決定 2026-09-19) から作った**単独稿**で、数値・機械判定・入力内容に記録 README・版・stale 注記を出所にせず、実行者の手続きは「記録による」と区別する ([T-2611] / [T-2674] の型)。**性能の結果節ではなく方法論 (往復と診断の還流) の実施例**: 成立したのは実測の還流 2 回 (巡 1 → 2、巡 2 → 3) と D2155 の `k2_critic_diagnosis` (critic-2 逐語の exact 6 field) による診断の還流 1 回 (critic-2 → 巡 3。planner-4 / coder-4 の両入力に届き coder-4 が候補 10 を提案) までで、巡 3 の実測・critic-3 を次の提案へ戻す実走は含まない。巡 2 は診断が型付き入力に無く coder が既知値 20 (critic の候補 10 と不一致) を出した記録。限定 21 件。台帳 ID 未起票 (2026-09-20 時点)。図 12 (データフローの説明図、値なし。稿を `caption_source` として束縛するので、稿は provenance の sha256 を持たない — F36、正本は `figures/README.md` の fig12 節) | 認証 protocol ではなく単一の outer status を持たない。各巡の評価は harness の terminal `outcome=certified` (verify `serializable` / anomaly 0、legacy 条件 1 回) で停止判定 `continue`、材料レポートは `certifying_input=false`。**同 job stock 対照はどの巡にも無く ([T-2795] 裁定待ち)、3 走の値 (719,324.5 / 687,508.5 / 815,983 tps) は非同時刻で改善・退行の証拠にしない。診断は「届いた」「参照したと申告した」まで書き「効いた」は書かない (planner 入力は診断 key 以外同一、coder 入力は診断 + `planner_direction` の差だけだが、各条件 1 回の別起動で統制比較ではない)。知識の因果効果は主張せず、legacy critic のため B-4 ablation には非適格。規律 6 は coder 4 出力が `instruction_like_content_detected=false`、planner / critic は散文で「指示めいた文字列なし」と自己申告 (形式は role ごとに違う)**。追補 (2026-09-20、[T-2795] pair 試行): 同 job pair launcher (D2183) の初投入 `13339.nqsv` で候補 10 の再評価は certified (811,956 tps、別 policy epoch の新 campaign) だが stock は one-shot claim leaf に認可前で拒否され pair 不成立 (STOCK 性未確認)。stock 対照未達の限定は不変 (上の stale 注記)。稿本文は凍結のまま |
| 2026-09-20 | `results/2026-09-20-s1a-nine-pair-direct-comparison.md` | 縮小主張 S' の性能次元 S-1a (合成軸 = 系側 gate 構成 `g_rl` / `g_rt` が、2026-07-12 に凍結した既知軸最良 3 種 `p2_2_flag_opt`・`backoff_fixed_best`・`sort_best` を判定境界 +3% を超えて上回るか) の**直接比較 9 対 (3 対 × 3 workload、n = 8 / cell = block1 4 + block2 4、certified 標本のみ) の単独稿**。S-1 登録追試の 1 本走 (develop / floor / block1 / block2 の正典 4 campaign、2026-07-16 JST、旧環境 `linux-baremetal`・CCBench `d706650`・`perf stat` 下) の一次資料全体 (凍結 report `s1_direct_comparison/report.json` sha256 `491ad38d…`、fig4 provenance、S-1 計測 freeze、4 campaign の WAL と lock、時間台帳、develop v1 の WAL、事前登録、S' 最終報告、確定文言、worklog 2026-07-16) から作り、版・図 README・stale 注記を数値の出所にしない ([T-2611] / [T-2674] の型)。**「本稿が判定しないこと」を先頭に置き**、実施回数 (凍結資料に記録された本走は 1 回、第 2 の本走は資料から特定していない) と主張範囲 (9 対の family 判定のみ、成立した 3 対を単独の主張にしない) を分け、「既知軸最良を超えなかった」を「合成が無価値」と読まず (既知軸集合は凍結有限集合 = 合成未探索の下界)、develop 相 v1 の build-error 3 cell (`backoff_fixed_best`) と retry 6 件 (計 120.65 秒) を時間台帳と v1 の WAL から開示する。prospective power 未保証 (事前登録 層 1 (iii)) と校正費用の台帳上の位置が未特定であることを限定に置く。限定 19 件。図は fig4 (失敗報告図、同じ凍結 report と 4 campaign から。図の作り直しは無い)。台帳 ID 未起票 (2026-09-20 時点) | 事前登録の family 判定 **不成立** (family p = 1.0。report の `reference_alpha` 0.0125 の参考判定と、2026-07-16 人間承認の Holm 族 4 判定表の非有意)。9 対の内訳: 対 `sort_best` は 3 workload とも +55.5%〜+98.4% で gate (1) 通過 (`p_perm` = 1/4,900)、対 `p2_2_flag_opt` は −9.3%〜−55.1%、対 `backoff_fixed_best` は −36.0%〜−51.9% で gate (1) 不通過。gate (2) (block 間の方向一致) は 9 対とも通過し、負けた 6 対は 8 対 8 標本が完全分離 (確率優越 0.0)。correctness は trace-enabled 別 build の検査で 324 verify とも serializable・certified・anomaly 0 (性能の判定ではない。事前登録 (iv 付属) の検証相の記録は一次資料に無い)。**結果既知の事前登録付き追試の出力であって新しい否定的発見ではなく (HARKing 境界、D12)、S-1b の成立は S-1a を救わず、適格率次元の発見再現性が未実証であり S-1b の成立もこの限界を解消しないことを併記する (確定文言・S' 最終報告の原文の逐語引用は稿 §0・§3.2)。現行環境の A-2 / A-6 / T-1998 / B-7 / A-1 / B-10 / 検証相とは環境・pin・genome・identity が違い、`backoff_fixed_best` の値 (5 / 10 / 2 µs) が A-2 / A-6 の採用値と同じでも同じ測定ではない (規律 7)。`stock_common` は登録比較ではない。この 1 本走の執筆材料にはこの稿を使う** |
| 2026-09-20 | `results/2026-09-20-b10-waiting-grid-formal.md` | 見送り台帳の項目 B-10 (機序説明の帯域外への拡張) のうち、**待ち方 grid** (事前登録 `docs/b10-backoff-shape-preregistration.md` の発効版 v4 = commit `77b33e37d`、blob `ea910de32…`、登録した `constant` 対 `symmetric-modulo`、μ = 2 / 5 / 10 / 25 / 50 / 100 µs、48 スレッド Silo / YCSB 3 workload) の report phase (request `978195.nqsv`、2026-09-05、解析コード `2a338449b`) が 3 campaign × 45 cell = 135 cell (write-heavy `e3de15eb` / `965564.nqsv`、balanced `143a3f74` / `974207.nqsv`、read-heavy `acf840c8` / `977647.nqsv`、別 job・別日・別 driver 版、旧 2 系列は D1588 / D1636 の限定受理) を exact に集約した 1 つの判定の**単独稿**。1 判定の一次資料全体 (report .md と provenance JSON、3 campaign の record・lock・WAL、4 件の受領証と job 結果、発効版 blob、裁定) から作り、版・insight を数値の出所にしない ([T-2611] / [T-2674] の型)。生標本 135 cell、対差 54、限定 19 件。**「本稿が判定しないこと」を先頭に置く**: 事前登録 §9 の 9 項目はいずれも閉じず、うち 5 項目は D1678 (2026-09-07) が見送りと裁定 (再訪 = 査読で要求されたとき)、制約 3 つ (D1092 / D1094 / D1097) を限定に入れ、待ち量についての主張は指示値の平均に限定し機序は述べず、静的右 tail の 2 cohort (2026-09-16 / 09-19 稿) と合成しない。図は無い。台帳 ID 未起票 (2026-09-20 時点)。**この判定の執筆材料にはこの稿を使う** | 3 族すべて Holm で **`different`** (write-heavy raw p 0.02556610107421875 = 6702 / 2^18、balanced Holm p 0.0005340576171875、read-heavy Holm p 2.288818359375e-05、α 0.05、18 対 / 族、全 2^18 列挙の exact 符号反転)。方向は 3 族とも `symmetric-modulo` が高い側。36 cell の効果量はすべて `estimable` で、等価域 ±3.0% の内側 32 / 境界を跨ぐ 4 / 外側 0 / 判定不能 0。点推定が負なのは write-heavy μ 5 の 1 cell (−0.97%、区間は 0 を含む)。性能 cell 135 / 135、検証 slot 270 / 270 (不完全 0)、135 cell すべて `correctness_certified` (trace 有効ビルドの別走行。性能の判定ではない)。**`official_certification` は `false` のままで、性能値を採用根拠にしない。B-10 という項目の閉鎖でも、`binary` / ladder / 用量反応 / 直交切り分けの一般化でもない** |
| 2026-09-20 | `results/2026-09-20-p24-static-backoff-sweep-linux-baremetal.md` | 論文ストーリー §8 の exact claim (性能) の出所である**旧 `linux-baremetal` 環境の P2-4 静的 backoff sweep 3 campaign** (trial `p2-backoff`、write-heavy `493813a7` / balanced `484c663e` / read-heavy `610004b9` = fig2b の provenance が入力として指す 3 本、各 8 genome (無 backoff 対照・既定 adaptive・静的 2 / 5 / 10 / 25 / 50 / 100 µs) × 5 反復、CCBench `6656e93`、trace-disabled の Release build、`perf stat` 下、8 genome の binary hash は 3 campaign で同一、測定 2026-06-22 (write-heavy / balanced) と 06-28 (read-heavy)、限定 15 件、図は無い) の**単独稿**。1 campaign 群の一次資料全体 (`campaign.lock`・WAL・`.dat`・材料レポート・fig2b の provenance JSON・同環境の較正記録・裁定) から作り、論文値と測定数値 (median・反復・条件・時刻・当時の判定) の出所に A-3 一本化 insight (`authority: none` の導出索引)・figures README・版・claim-evidence を使わない ([T-2611] / [T-2674] の型。混同防止の参考値 = 別分母の利得・profile との差・既定 adaptive の 3 定数・D20 の観測者効果は A-3 insight・figures README・D20 からの引用と明記し、再計算していない範囲を §5.4 に置く)。3 campaign × 8 genome の生標本と当時の `verify_done` (verifier epoch E0) を完全収載。fig2b は同じ 3 campaign の図だが点推定は標本平均 (+38.1 / +11.4 / −6.9%) で論文値の出所ではなく、稿は図の provenance の SHA-256 を持つ (稿を `caption_source` にする図は無い)。台帳 ID 未起票 (2026-09-20 時点) | 採否 protocol ではなく、事前登録も単一の outer status も持たない記述的結果。**同一 sweep 内の無 backoff 対照 (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) との各 5 反復 median の比で write-heavy fixed 10 µs +38.3% / balanced fixed 5 µs +11.3% / read-heavy fixed 2 µs −6.6%** (未丸め 38.328803879% / 11.268232226% / −6.642987663%、A-3 insight と一致)。有意差判定でも区間推定でもない。**但し書き 1 (D496 以前の記述的結果で A-1 の配置・推定対象ではない) と但し書き 3 (別 boot 未取得、D1100 / D1525) は本稿でも外れない。3 値の正しさは機序論証による外挿で、A-2 / A-6 の certification は遡らない (D1993 項 4。WAL の `verify_done` 24 件が `serializable` / `certified` / anomaly 0 なのは当時の判定器の記録)。現行環境の 3 走行 (A-2 / A-6 / T-1998) とプールしない (D1993 項 6)。+38.5% (`BACKOFF_NOINLINE=1`・`perf record` 下・3 反復の機序診断 profile) は D20 により headline に使わず、+38.3% との差を丸め違いとも別 regime の実証とも言わない。sweep 自身の 24 走も `perf stat` 下で、絶対 tps は headline の出所にしない。分母は無 backoff 対照 1 本で、既定 adaptive (+147.4%) や別分母の値と混ぜない** |
| 2026-09-20 | `results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` | A-1 balanced5 sized 本走 **attempt-0002** (同じ study `paper-story-a1-20260901-balanced5-sized-v1`、job `13220` / `13221` / `13222`、2026-09-20 18:11 JST 投入、source `fec4a8187`、3 workload × 30 対 × 2 arm = 生標本 180、固有の限定 13 件を記載し attempt-0001 稿の限定 20 件は稿 §3 に明記した読み替えの下で参照する、図は無い)。D2172 項 2 (2026-09-20) が「同一配置 (同 seed・同物理順) の反復」を研究目的として **1 attempt 限定で認可した独立の観測 attempt** で、durable base の exact な認可 record (D2178、追補 `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md`) を gate の入力にして投入した (再走ではない)。**1 attempt の一次資料全体 (公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` の result.json / receipt.json / .complete.json、campaign WAL 3 本、schedule receipt 3 本、事前登録、policy v3、追補、認可 record、裁定) から作った単独稿**で、stale 注記・記録 insight・版を数値の出所にしない ([T-2611] / [T-2674] の型)。root seed・group_bits・block の物理順は attempt-0001 と 3 workload とも一致 (schedule receipt で照合)、束縛 9 file のうち driver 1 本だけが認可 record の生成・照合、submit / materialize への接続、CLI 分岐の 143 行追加・3 行削除で異なる。§2.7 に attempt-0001 稿の値を**並記**するが、2 attempt をプールした推定量・差・比・合成区間・再現判定は作らない (D1993 項 6)。**A-1 の充足・formal 化・L-A1S-4 (反復間の安定性) の解除・3 本目の認可は判定しない** (認可はユーザー手番、D2044 項 8) | 単一の outer status を持たない非認証 lane (`formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only`)。登録済み解析の分類は 3 workload とも `resolved-above-floor` (対差平均 write-heavy +1,538,451.47 / balanced +548,138.23 / read-heavy −560,565.60 tps、符号 + / + / − は attempt-0001 と同じ)。**`variance_plan_breach` は write-heavy と read-heavy で true** (標本 sd が計画 sigma の 1.21 / 1.08 倍。balanced は 0.87 で false)、分類は変わらない。correctness は別の trace-enabled verify で 6 arm とも certified・anomaly 0 (性能の判定ではない)。bench 相の順序 (balanced → read-heavy → write-heavy) と node (bnode035 / 039 / 040) は attempt-0001 と異なる。**headline 値・workload 横断の結論・C1 の再現判定にせず、2 attempt の並記を「再現した」「安定している」と読まない。この attempt の執筆材料にはこの稿を使う** |

**この系列の規則。**

- **append-only。書いた後は更新しない。** 版と同じ凍結物である。誤りが見つかったら新しい日付の file を足し、旧 file は残す。
- **1 file = 1 結果 (1 protocol または 1 campaign 群の完走)。** 新しい日付を足すときは、その結果の一次資料全体
  (権威 bytes・raw manifest・WAL・裁定) から作り直す。一項目だけを直した差分改訂を新しい日付として置かない。
- **「版の履歴」表には登録しない。** これは版ではない。
- **数値・日付・判定の出所は一次資料だけとする。** 版や claim-evidence の記述を数値の出所にしない。
  図を伴うときは `figures/` の凍結物と provenance JSON を指し、図の値と表の値は同じ生値から同じ計算で出す。
- **protocol status (`reject` 等) は protocol の出力として書き、研究としての成功・失敗・新規性の宣告へ拡張しない** (D12)。
  性能・別走行の正しさ・旧系列との関係の段を 1 文へ畳まない (最新版 §7 の区別の規律)。
- この系列の文書は**執筆者向けの統制稿**であり、D12 が定める機械射影の材料レポートではない。数値は図の provenance JSON から転記し、
  転記元の SHA-256 を文書に書く。散文は執筆者の判断を含む。
  ただし `results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` は、図9が本稿を `caption_source` として束縛するため、
  数値と転記元の SHA-256 を公開 leaf の `result.json` から得る個別の扱いとする。自己参照を避けて図の provenance の SHA-256 は
  `figures/README.md` の fig9 節に置き、図と稿の値の対応は `test_plot_a1_sized_paired.py` で検査する (F36)。
- 版と同じく `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外である。

**A-6 単独稿の限定 11 への追補 (2026-09-20、fig11 wave):** `results/2026-09-18-a6-certification-reject.md` §4 限定 11 の
「図は無い。A-6 の 2 cell を描いた凍結図は `figures/` に存在しない」は執筆時点 (2026-09-18) の事実である。2026-09-20 に、同じ権威 bytes
(`certification.json` SHA-256 `3a9505b0…`、`raw-manifest.json` SHA-256 `8d179535…`) と durable authority から fig6 と同じ生成器
(`tools/plotting/plot_a2_certification.py`) で `figures/fig11_a6_certification_reject` (PNG / PDF / provenance JSON) を作った。
provenance は同稿を `caption_source` として SHA-256 `34a96842…` で束縛するので、**稿の bytes・表・限定 1〜12 は変えない**
(凍結物であり、この束縛のため以後も変えられない)。図の値と稿 §2.1 の表の値は同じ生値から同じ計算で出る。図が言えることの範囲・
caption・proof chain の正本は `figures/README.md` の fig11 節。性能の `reject` と別走行の正しさ `certified` は図でも別の段のままである (D1993 項 2)。

**B-10 待ち方 grid 単独稿の「図は無い」への追補 (2026-09-21、story 2026-09-21 wave、D2194 項 7):** 上の表の
`results/2026-09-20-b10-waiting-grid-formal.md` の行と同稿 §3 限定 11 の「図は無い」は起草時点 (2026-09-20) の事実である。2026-09-20 に、
同じ一次資料 (report の provenance JSON `b10_backoff_shape_provenance.json` SHA-256 `a4390603…` と report .md SHA-256 `e237d17d…`、
外部の受領証 `93a1cd74…` と job 結果 `d5d4a0ee…`) から生成器 `tools/plotting/plot_b10_waiting_grid_forest.py` で
`figures/fig13_b10_waiting_grid_forest` (PNG / PDF / provenance JSON) を作った (fig13 wave、entry 1763、branch `worktree-dev-wave-fig13-b10-waiting-grid`、起点 `482f19b88`)。
provenance は同稿を `caption_source` として SHA-256 で束縛するので、**稿の bytes・表・限定は変えない** (凍結物であり、この束縛のため
以後も変えられない)。図は report の判定を読み、生成器は 135 record から同じ式で再計算して一致を要求するだけで判定を作らない。図が言えることの
範囲・caption・proof chain の正本は `figures/README.md` の fig13 節。**区間が等価域の内側にあることは等価性の成立ではなく、cell ごとの有意差は
判定せず、静的右 tail の 2 cohort (fig8 / fig8b) と合成・比較せず、`official_certification` は `false` のままである。** 後継図は作らない
(D2194 項 7)。

## 運用ルール（check_docs.py との関係）

- 本ディレクトリの文書は追記型の凍結記録なので `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外。
- 他文書からは**ファイル名（basename）で参照**する（行番号参照は禁止・節名参照にする、check_docs.py 準拠）。
