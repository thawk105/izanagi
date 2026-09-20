# 検査範囲と結論

**P9 は修正付きで採用するのが妥当です。現記載のままでは、B の過少計上、機械故障 retry の claim 衝突、分類不能な無応答の無料 retry が残ります。** plan の投入前記録・物理 attempt 分離・証拠付き分類を、subprocess 案にも残す必要があります。

全検査は **未実走・静的読解**です。pytest、build、計測は行っていません。peer job の失敗は親提示の観測であり、本相談の実測ではありません。

以下、`plan` は [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s2-plan.md)、`追補` は [brief-addendum-1.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/brief-addendum-1.md)、`V` は同 job directory の `verbatim/`。コードの略号は `L=orchestrator/campaign/p3_s4_loop.py`、`P=pipeline.py`、`C=loop.py` とします。

# 1. BUILD_START の不在から「未投入」は導けない

**対象:** 追補:33–35。
**判定:** real。**格:** must-fix。
**成果物影響:** 投入済みの打切りを A-only に誤分類し、B 台帳を過少計上して追加評価を許し得る。

§3.1 は「certification pipeline へ投入した時点」で B 消費、§3.3 は投入後の時間切れも B 消費とする。追補はこの境界を `BUILD_START` の有無に置き換えている。

しかし、[L:2165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/p3_s4_loop.py:2165) の `run_campaign` 呼出し後、C:519 の authorization、C:538 の perf preflight、C:545 の lock、C:634 の source evidence 解決を経て初めて build record に至る。この途中で job walltime により kill されれば、**投入済みでも BUILD_START は無い**。WAL の最終 record だけでは投入前／後を一意に復元できない。

なお、通常の admission-error は P:1763 の `_prebuild_abort` が BUILD_START を書く。この既存対策まで欠落しているという指摘は refuted。ただし、強制終了や先行処理の例外との間隙は残る。

**代案:** plan:269 の durable な `pipeline-submitted` を採用する。subprocess 内の L:2165 直前で B-5 sidecar に投入を記録し、親はその記録と WAL を照合する。未完了は成功にせず、投入前後が証明できないケースを A-only に決め打ちしない。

# 2. slot 分離だけでは、同 slot の subprocess retry が成立しない

**対象:** 追補:21–32、plan:316・324。
**判定:** real。**格:** must-fix。
**成果物影響:** retry 可能な機械障害が、残存 claim による連続拒否に変わり、回復可能な系列の score が欠測になる。

追補の peer claim 衝突の説明は実装と一致する。[campaign_claim.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/campaign_claim.py:383) は release・自動削除を持たず、:421 の O_EXCL と :428 の既存ファイル拒否は、前 process が終了していても働く。

別 slot なら、`ident.py:216` の search_config が preimage に入り、C:223 の protocol digest も変わるため、この衝突は回避できる。しかし、**同 slot・同 config の subprocess 再起動は同 claim を再取得する**。これは追加 retry が必要な場面そのものに当たる。

plan:316 の `b5_attempt=0,1,2` はこの問題への適切な対策だが、追補の CLI 契約には継承が明記されていない。「slot ごとに別 identity」で十分とする置換は不可。

**代案:** 論理 slot は固定し、物理 attempt を identity に追加する契約を必須にする。同じ proposal bytes・入力 hash・予定位置を維持し、A/B は増やさない。claim を削除して再利用しない。

また、plan:324 の復元前 skip 拒否も残すこと。L:2177 → L:1878 は過去 COMMIT から whiteboard の success を復元する。既存 WAL に BUILD_START があることだけを今回の fresh 評価の証拠にしてはならない。

# 3. 45 分無応答は、それだけでは機械故障ではない

**対象:** 追補:53–54。
**判定:** real。**格:** must-fix。
**成果物影響:** 既に消費した生成機会を未消費扱いにして再生成でき、A 台帳と候補列が変わる。

V/prereg-s3.md:35–46 は機械故障を限定列挙し、「分類不能な失敗を無料 retry として扱わない」とする。45 分ファイルが現れないという事実だけでは、通信障害、親の未着手、LLM 実行中、生成済み出力の未公開、空出力の未報告を区別できない。

追補は plan:461 の「原因を断定できない場合は分類不能欠測」を落とし、無応答を一律に候補処理前の中断へ分類している。候補評価 subprocess が未起動でも、原提案機会が未消費とは限らない。

**代案:** plan:461 を維持する。機械故障の証拠がある場合だけ同じ操作を追加2回まで retry し、待機延長を新しい生成依頼にしない。生成機会の開始、空出力、schema reject は同じ `a` に記録する。理由不明の無応答は分類不能欠測とする。

# 4. A/B 対応表と品質欠測の基本分類は適合している

**対象:** plan:209–235・269–295。
**判定:** refuted〔品質欠測で予算が返る、または build failure を Tier0 に読み替えるという疑い〕。**格:** —。
**成果物影響:** 指摘した予算返却は plan 上では発生しない。

plan は次を明記している。

- 空出力・schema・値域・帰属・文法・検疫不通過は A-only。
- 投入後の build failure・anomaly・bench abort は A/B 消費。
- 品質欠測は A/B を返さず、endpoint 資格なし。
- `bench-no-throughput`／`bench-cv-undefined` は COMMIT 不在でも欠測分類。
- 分類不能、品質赤、候補 compile failure は無料 retry 不可。

P:1455 の bench payload には `tps`、`unstable`、`settled` が実在し、plan の OR 条件で §5.3 の採用条件を検査できる。P:1441・1450 の COMMIT 前 abort も plan:225 が拾っている。pipeline の歴史的 COMMIT と B-5 の採用資格を分離する方針は適切。

ただし、追補へ切り替える際もこの分類器を継承する必要がある。CLI の rc は品質や certified を表さない。

# 5. Tier0 不在の費用試走は可能だが、§10 の完全充足とは別

**対象:** plan:287、追補:42–43、brief:9–13。
**判定:** real。**格:** should。
**成果物影響:** Tier0 が排除するはずの候補も B を消費するため、本走と同じ受理前処理・予算配分を実証した成果にはならない。

V/prereg-s3.md:22–24 は共通 Tier0 が未成立であることを明記する。plan と追補の `tier0_status="not-implemented"`、現行 build failure を B 消費とする扱いは正しい。condition gate を Tier0 に改名する必要もない。

一方、V/prereg-s10.md:16 の「共通 Tier0」は未成立のまま残る。したがって今回の完了記録では、**実装済み部品と Tier0 未成立を分ける**必要がある。

**代案:** 費用試走の位置づけを維持し、裁定パッケージへ Tier0 の exact 契約を未確定事項として引き継ぐ。本相談から固定スモーク追加を要求するものではない。

# 6. 別 driver と fresh layout は、checkpoint 初期化による停止迂回とは異なる

**対象:** plan:245–267・350、追補:30–32。
**判定:** refuted〔`check_stop` を呼ばないこと自体が §3.4 違反という疑い〕。**格:** —。
**成果物影響:** 系列台帳を維持すれば、収束・逆方向停止による探索機会の減少を防げる。

§3.4 が禁止するのは checkpoint の改変・初期化による迂回であり、同節自身が fresh layout では停止が発火しないと説明している。plan は系列状態を台帳に保持し、評価用 LoopState と区別している。系列 checkpoint を消して継続する設計ではない。

P9 も、fresh slot に既存 checkpoint が無い限り、L:2707–2712 で新規 state に対する入口判定となる。ただし**既存 slot の再利用まで fresh と呼べない**。所見2の対策が必要。

`A<30 and B<10`、原提案前の A 記録、投入時 B 記録、終端理由の検査という plan の形は「運用だけでは不足」に応える。保証するのは障害下での必然的な完走ではなく、正常条件での継続と未完走の検出である。

# 7. stock 成功条件と初回入力は適切。入力検査の範囲を明示する

**対象:** plan:181–203・358–368、追補:51–52。
**判定:** refuted〔rc 0 だけで stock 成立とする疑い〕。**格:** —。
**成果物影響:** 非 STOCK・品質欠測・skip を初期性能として採用する経路は plan が排除している。

plan は certified-stock、当該 attempt の admitted COMMIT、`src_token == STOCK`、stock genome 一致、正常品質・有限正値を要求する。L:1999–2005 と D2183:9–11 に沿っている。stock 不成立時の系列停止・比較判定不能も §6 末尾に整合する。

D2183 の同 campaign は K2 pair の設計であり、B-5 の stock-start／search／score を別 session identity にすることだけで正しさ基準が変わるわけではない。旧 pair の既定 identity は維持すべきである。

**追加所見 — 判定:** real。**格:** should。
**成果物影響:** whiteboard が一致しても、誤った stock 値・出所を `current_perf` に渡せば LLM の候補列が変わる。

plan:366 が exact 比較を明記する中心は whiteboard。L:1299–1301 は `current_perf` を明確に責務外としている。追補の「直近の正常 certified、無ければ stock」という規則を採るなら、`assert_inherited_inputs` で planner の current_perf、coder の baseline、出所開示も台帳から照合する仕様を明記すること。

random／sweep は plan:155・167 の純粋関数に台帳・stock 値を渡さず、系列共通の stock 記録と生成器の入力を分ける形で、性能依存の分岐を防げる。

# 8. whiteboard の比較対象は定義済み。親の介入禁止を機械保証したとは言えない

**対象:** plan:348–368、brief:40。
**判定:** refuted〔件数だけの恒真検査という疑い〕。**格:** —。
**成果物影響:** 評価履歴の脱落・順序交換・他系列混入を検出する設計になっている。

plan:359–366 は、台帳の評価1〜k−1から作る期待値と実 planner/coder 入力を、順序・値・全 field で比較する。A-only reject を評価件数に混ぜず、`delta_pct=None` も維持する。

既存の値域正本は L:1420–1438。

- direction: `increase / decrease / explore_both`
- magnitude: `small / medium / large`
- result: `success / fail / rejected`

plan が参照する L:647 は WhiteboardEntry の位置としてずれており、正しくは L:653、射影は L:1198、値域検査は L:1426。これは **real / nit**。成果物値への直接影響は示せない。

さらに、親が性能を見て追加助言・候補修正・再抽選しないことは、この入力照合では保証できない。**限界の明記欠落は real / should**。役割入力・出力の保存と照合で保証する範囲を示し、「親の未記録の介入や実送達は機械保証しない」と記すべきである。新たな一般的防壁の追加は不要。

# 9. random の写像は適合。床値の確定は受入時の証拠が必要

**対象:** brief:22、plan:131–164。
**判定:** refuted〔modulo bias・累積区間の off-by-one・重複再抽選の疑い〕。**格:** —。
**成果物影響:** 記載どおりなら事前登録の候補分布・列を維持する。

`M=sum(weights)`、`L=(2**256//M)*M`、`U<L` のときだけ採用、`bisect_right(cumulative,U%M)+1` は §4.2 と一致する。累積境界の整数は次の値の区間に属するので `bisect_right` が正しい。

preimage は §4.2 の ASCII・改行なし・先頭ゼロなし・c=0 を参照し、SHA rejection の c 更新と A 更新を分離している。重複・不成績による再抽選禁止も明記済み。

**精度についての判定:** 根拠不足。**格:** should。
100／130桁一致は本段で未検算であり、二精度一致だけを数学的な床の証明とは呼べない。ただし、誤った重みが現に得られる証拠もないため must-fix とはしない。実装受入時には1000要素の一致結果・整数表・hashを残す。厳密な確定根拠を求めるなら、誤差を含む上下界が同じ整数床に入ることを示す。

# 10. sweep の次点補充と B 上限は両立する

**対象:** plan:167–177、追補:48。
**判定:** refuted〔必ず10提出で打ち切るべきという疑い〕。**格:** —。
**成果物影響:** 前処理不通過による B 未消化を補いつつ、評価機会10件を超えない。

`backoff_extended_sweep.py:55–58` は0込み29点で、1..1000との共通部分は指定の28点。hash→v の順序は §4.3 と一致し、`MEASUREMENT_SEEDS` は使わない。

§3 の B/A 規則と §4.3 の「次点」「格子を使い切ったら」を合わせると、**B を消費しない候補起因の前処理不通過について11点目以降で補充する**読みが整合的。投入後の build failure や anomaly は既に B を消費するため、それを理由に10評価を超えて補充してはならない。plan の B 条件はこれを防ぐ。

機械故障は同点・同入力の retry、枯渇は再巡回せず記録、という仕様も適合する。

# 11. endpoint・score・anomaly 波及は plan に閉じる設計がある

**対象:** plan:333–346・382–408。
**判定:** refuted〔最大探索値の score 流用、次点再選択、他 arm の同値失格漏れという疑い〕。**格:** —。
**成果物影響:** 指定の endpoint と独立 score、後発 anomaly による訂正を表現できる。

以下は §6 と一致する。

- certified・品質正常・未失格から、median 降順→v昇順→slot昇順。
- endpoint を永続化してから同じ source の5 fresh session。
- 5 session の median を score とし、探索値を再利用しない。
- 再計測 anomaly は不採用・fallback、次点へ戻らない。
- 品質欠測・機械欠測は score missing。
- 同 workload・block の stock 5 session を fallback に共有。
- consumer が全台帳の `(workload,value)` anomaly 集合を先に作り、他 arm・他系列の既確定結果も訂正する。

search／score／block-stock の identity は plan:307–316 で分離される。実装受入では、同一 session の別名登録を許さず、異なる arm で後から anomaly が出た例を確認する必要がある。これは plan:569 の予定検査に含まれる。

# 12. 正しさの既存接続は維持できる。machine mode は入口 guard も変更対象

**対象:** plan:229–237、追補:25–29。
**判定:** refuted〔performance verify の回数不足、anomaly 後 bench 到達という疑い〕。**格:** —。
**成果物影響:** 既存経路のまま legacy 1回＋performance 5回を通し、不通過を即 reject できる。

C:160 → P:193–222 は perf の exact workload と `reps` を correctness に渡す。P:2185–2188 は各 repetition の不通過で直ちに return、P:2436–2437 は次段へ進ませない。plan は B 消費・bench 不到達・endpoint 不採用を明記している。pipeline.py／loop.py／build_admission.py を変更する必要はない。

**追加所見 — 判定:** real。**格:** should。
**成果物影響:** machine resolver だけ追加しても、random／sweep は入口で拒否され、B=0のまま評価できない。

[L:3145–3151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/p3_s4_loop.py:3145) は stock・no-build 等でない候補に coder authority を必須とする。追補の「coder authority 無し」の machine mode には、この guard の限定例外も必要。

**代案:** machine flag の実装範囲にこの箇所を明記する。`--run-iteration` と正規 machine receipt に限定し、通常候補の opt-in 要求、3 arm 共通の proposal schema・帰属・文法・検疫は維持する。

# 13. 53 session の算術は正しい。115 秒と12〜14分の適用域は限定される

**対象:** brief:35–39・65、plan:489–534、追補:45–47。
**判定:** real。**格:** should。
**成果物影響:** 外挿を B-5 の実測最大値と扱うと、walltime 根拠と未完走リスクの記録が誤る。

115秒・9.7GiBに合う証拠は、[別検証相の表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/output/insights/2026-09-20/verify-phase-adopted-backoff/verbatim/table-B.md:16) にある。fixed-5／fixed-10 の write-heavy、3秒 trace の本走各8反復では verifier wall は約113.5〜118.4秒。balanced・read-heavy より短い。

ただし、[同 README:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/output/insights/2026-09-20/verify-phase-adopted-backoff/README.md:56) の対象は固定値5／10、別 runner・当時の verifier、1M／48 threads の検証相である。B-5 の全1..1000、適応 stock、legacy＋5 verify＋bench の session 所要を測ったものではない。12〜14分は外挿として提示すべきで、実測とは呼べない。brief:65 の「費用の5/6」も回数比であり、legacy と full-scale の費用比ではない。

53の内訳は §11 と対応する。

| 用途 | 試走 |
|---|---:|
| 探索 | 3×10 = 30 |
| 系列開始 stock | 3 |
| endpoint 再計測 | 3×5 = 15 |
| block stock | 5 |
| 合計 | **53 ≤ 60** |

plan:502・572 の固定 schedule、B11／score6／block-stock6拒否は適切。53は上限であり、未採用・anomaly・欠測でも全件実施を強制しない。retry・品質再測は物理回数として別計上する。

追補の計時方針は、依頼逐語の括弧書きに照らして支持する。ただし `build_done→各verify_done` の累積差を各 rep 所要にしてはならない。plan:521–524 の隣接差と workload tag を使い、**trace＋verifier＋周辺処理の区間**と呼ぶ。打切りで終点が無い区間は欠測または打切りとして残す。

# 14. pilot 専用報告は適切だが、P7 の反証対象を正確に書く

**対象:** brief:30・76、plan:410–412・604。
**判定:** real。**格:** nit。
**成果物影響:** 提案された pilot consumer の値は変わらないが、親判断を反証した理由が過剰になる。

brief は「n=1で対不足、記述統計のみ」と書くが、「§7.4 第4段で止まる」とまでは書いていない。plan の反証はその点を補っている。

ただし、登録用判定器へ n=1 を投入して第4段だけを理由にする実装は不適切で、floor 欠測等が先行するという内容は正しい。`purpose="pilot"` と `registered_judgment="not-applicable-pilot"` の分離を支持する。

## 総括

**must-fix**

1. **所見1:** BUILD_START の有無だけで投入前後を決めず、subprocess 内の投入境界を durable に記録する。
2. **所見2:** 同一論理 slot の retry に物理 attempt identity を必須化し、claim 再取得と旧結果復元を防ぐ。
3. **所見3:** 45分無応答を一律に機械故障へ分類せず、証拠付き retry と分類不能欠測を分ける。

| 前提 | 判定 |
|---|---|
| **P1** | **条件付き支持。** 別 slot は分離できる。「構造的に絶対 skip しない」は反証。attempt 分離と fresh 証拠照合を残す。 |
| **P2** | **支持。** 別 driver は checkpoint 改変による迂回ではない。B/A 台帳・継承・終端検査が必要。 |
| **P3** | **支持。** WAL 品質分類で対応可能。COMMIT 前 bench abort と系列欠測も保持する。 |
| **P4** | **条件付き支持。** 同 job handshake は適合。「唯一の形」は反証。timeout 分類を修正する。 |
| **P5** | **条件付き支持。** 既存 job body 拡張は妥当。旧 argv、拒否条件、TJ 契約を維持する。 |
| **P6** | **条件付き支持。** 分布・写像は適合。整数床とhashの確定結果は未検証。 |
| **P7** | **修正版を支持。** pilot は独立した記述経路。登録判定の第4段だけへ短絡させない。 |
| **P8** | **暫定設定として支持。** write-heavy 選択には既知証拠がある。8h／3hの完走保証や実測上限とはしない。 |
| **P9** | **修正付きで plan の新 entrypoint 案より優位。** 既存 coder authority と proposal CLI を使い、§4.1との対応も明瞭。ただし現記載のままでは採用不可。所見1〜3を取り込み、machine guard と skip 拒否を明文化する。 |

親裁定で残すべき事項は、P9に追加する投入記録・物理attempt契約、timeoutの証拠基準、`current_perf`／baseline／出所の照合仕様である。Tier0未実装の費用試走、pilot専用報告、traceを含むverify区間の計時は支持する。本走のTier0 exact契約、発効束、総wall上限、本走認可は引き続き未確定として残す。