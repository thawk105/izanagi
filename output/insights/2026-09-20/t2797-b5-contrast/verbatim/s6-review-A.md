# 検査範囲と結論

**NO-GO。静的読解で成立する must-fix は3件です。** 前処理拒否の系列早期終了、verify 環境故障の候補失敗への誤分類、job 全体打切り時の B・物理 attempt 過少集計が残ります。

全検査は **未実走・静的読解**です。pytest、変異、実機 build・bench・handshake は実行していません。親・author の緑の報告を、今回の独立実証には数えていません。

以下の略号を使います。

- **B**：[b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/b5_generator_contrast.py)
- **R**：[b5_generator_contrast_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/b5_generator_contrast_report.py)
- **L**：[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/p3_s4_loop.py)
- **P**：[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/pipeline.py)
- **TB／TR／TL**：それぞれ対応する `orchestrator/tests/test_*.py`。

# 1. 帰属不一致の A-only 拒否が、系列全体の欠測終了になる

**対象：B:721、B:762、L:2148。判定：real。格：must-fix。**
**成果物影響：不正候補1件で次の提案機会が失われ、本来継続できる系列の endpoint・score が欠測になる。**

具体例は、LLM の coder proposal が `value=20`、`implementation="double now_backoff = 30;"` の場合です。

1. B:723 の schema 検査と B:731 の値域検査では、value と literal の不一致を検査しません。
2. L:2787 まで進み、`slot-start.json` ができます。
3. L:2148 の `_check_attribution_before_quarantine` → L:1739 の `AttributionMismatch` で停止します。`record_diff_reject`、`pipeline-submitted` のいずれにも到達しません。
4. B:347 の未投入分岐には拒否 WAL がなく、`unclassified-missing` のままです。
5. B:762 が系列を終了します。

A=1、B=0という消費量自体は適切ですが、候補起因の帰属不一致を分類不能として系列終了にする点が、裁定の「帰属整合・前処理不通過は A のみ、その後継続」という契約に合いません。

また、LLM だけ B:735 の実 loader 検査を省いています。L:2525 の K2 semantic 検査等が layout 前に拒否すると、今度は `slot-start` 不在から `pre-start-failure` に分類され、同じ拒否候補を機械故障として追加2回実行します。**sidecar 不在は、候補処理前の障害の証明ではありません。**

**代案：B:721／L:3430／L:2148。** 既存の受理基準を変えず、loader・帰属検査の候補起因拒否を構造化して系列 driver へ返し、`proposal-rejected`、A-only、次の opportunity とする。実 loader と帰属検査を通す負例を追加する。

# 2. verify の環境故障が候補起因失敗になり、fallback に化ける

**対象：B:55、B:375、P:2410。判定：real。格：must-fix。**
**成果物影響：回復可能な環境故障で同候補の retry が失われ、故障が続くと機械欠測が stock fallback の数値 score に変わる。**

`MACHINE_FAILURE_ABORT_REASONS` は bench 側2種だけです。P:2410 の `verify-probe-error`、P:2417 の `verify-competing-tenant` は B:378 で `outcome="aborted", failure_class="candidate"` になります。

たとえば stock-start 成功後、探索の各 full-scale verify で probe の入出力障害が発生すると、現実装は同 slot を retry せず次候補へ進みます。10件とも同様なら、品質欠測も certified 候補もないため、B:769 は `pending-block-stock` を設定します。正常な block stock があれば R:354 が数値 score を与えます。

これは §3.3 の候補と独立な入出力障害、および「機械故障の欠測を stock で置き換えない」と矛盾します。**裁定 §2.2 自身がこの狭い集合を指定しており、実装だけの逸脱ではありません。**

ただし、競合検知の全ケースが §3.3 の限定列挙に自動的に入るとまでは言えません。そこは bench 側を含めて分類根拠の裁定が必要です。少なくとも環境故障を候補起因と断定して fallback 可能にする現状は不適切です。

**代案：B:55／B:370。** verify・bench の対応する環境 reason を揃え、証拠付き機械故障は同 slot retry、原因を確定できないものは欠測にする。retry 上限到達後に fallback が生じないことを検査する。

# 3. job 全体の打切りでは、durable sidecar が B 集計へ接続されない

**対象：B:499、B:578、B:603、R:166、R:313。判定：real。格：must-fix。**
**成果物影響：投入済みの最終評価が報告上 B 未消費となり、その物理 attempt と費用も集計から落ちる。**

通常の子 process 終了後なら、B:590 が sidecar を読んで B を加算します。しかし、台帳の `pipeline-submitted` イベントは B:616、すなわち **runner が返った後**にしか書かれません。

次の状態で scheduler が job 全体を打ち切るケースが成立します。

- `proposal-opportunity(a=1,b=0)` は台帳にある。
- 子 CLI は `pipeline-submitted.json` を durable に公開済み。
- build／verify 中であり、系列 driver は `subprocess.run` 待機中。
- job 全体が終了し、driver も戻れない。

R:166 は header/events のみを読み、sidecar を取り込みません。R:328 はイベントの `max(b)` を B とし、R:313 はイベントに載った `slot_key` だけを物理 attempt と数えます。そのため、この例は **B=0、探索 attempt=0** と報告されます。

未完走を欠測に倒す処理はありますが、§3.3 の投入後 walltime の B 消費と、物理試行全件記録を満たしません。`TimeoutExpired` を投げる TB:617 の fake は、親 driver 自身も終了する経路を検査していません。

**代案：B:578／R:166。** 起動前に attempt の座標を durable に記録し、終了後集計で sidecar を照合して未完了 attempt の投入有無を反映する。元イベントは改変せず、欠測と B 消費を両立させる。再実行・claim 削除の仕組みは不要です。

# 4. critic 診断の「両方欠落」は、2回目以降も通る

**対象：B:443、B:451、TB:565。判定：real。格：should。**
**成果物影響：critic 診断を省いた planner／coder 入力が継承検査を通り、登録した K2 loop と異なる候補列になり得る。**

現物が検査するのは、両入力の key 有無の一致、診断がある場合の内容一致・6 field・境界文字列、初回の key 禁止です。2回目以降も、両入力から診断を省けば通ります。TB:565 の10評価 handshake 正例も、全評価で診断を省いています。

したがって「有無の左右一致を検査する」は正しい一方、「直前 critic の診断が次の両役割へ継承されたことを検査する」は成立しません。診断の正本との照合もありません。

**代案：B:443／B:626。** 診断生成済みの場合の期待値を親の保存材料に束縛し、両側欠落・同じ別診断への置換を拒否する。診断を生成できなかった場合の表現は親裁定で固定する。実送達の証明まで要求するものではありません。

# 5. LLM 待機時間の集計から拒否・timeout が落ちる

**対象：B:639、B:649、B:655、R:315。判定：real。格：should。**
**成果物影響：A-only 拒否や45分 timeout に使った待機費用が、LLM 手番時間の分布・最大値に入らない。**

`proposal_wait_wall_s` は proposal 成功時だけ返されます。さらに consumer は `evaluation-result` の provenance だけを集計します。

したがって、`.rejected.json`、継承不一致、timeout、proposal 後の schema 拒否等の待機時間は落ちます。A2 報告もこの不足を認めていますが、費用試走の成果としては未充足です。

**代案：B:626／R:315。** handshake の全終了枝で経過時間と終了種別を保存し、opportunity 単位で重複なく集計する。timeout の打切り時間を正常応答時間と区別する。

# 6. report は正常 bench 証拠と異なる fitness を採用できる

**対象：R:239、R:358、TR:292。判定：real。格：should。**
**成果物影響：台帳内の `fitness_tps` と bench median が食い違っても、異なる score・endpoint CV を報告できる。**

R の検査は bench payload 自身の品質を確認しますが、イベントの `fitness_tps == bench_payload["median_tps"]` を検査しません。

TR の `test_fresh_median_not_search_max_and_slow_endpoint_not_replaced` は、score-session の fitness だけを `[10,40,50,60,100]` に変更し、bench payload を変更せず `invalid == []` を期待しています。この不整合はテスト自身に存在します。

通常の B producer は B:397 で照合するため、正常経路で直ちに発生するとは判断しません。ただし、consumer の台帳整合検査の主張には穴があります。

**代案：R:239／TR:292。** イベント fitness と bench median の一致も検査し、正例 fixture は両方を整合させる。不一致を独立した負例にする。

# 7. seam・既定経路・machine admission の主な疑いは反証

**対象：L:1917、L:1962、L:2049、L:2234、L:2822、L:3265。判定：refuted。格：—。**
**成果物影響：指定の B-5 option がない既定経路について、新 kwargs・identity・成功復元の変更は確認できない。**

`a1.patch` と現物から確認した範囲は次のとおりです。

- `bench_max_rounds=3` は B-5 mode の条件付き追加。
- `drive_iteration` からの新 kwargs も条件付き辞書展開。
- `b5_slot` の identity 追加は option 指定時だけ。
- opt-in guard の例外には machine flag が必要。その flag は `--run-iteration` と `--b5-slot` を要求し、coder authority・K2 option と排他。
- machine context に coder authority は渡らず、resolver は STOCK evidence で `None`。
- receipt の input digest は proposal raw-byte SHA と evidence の genome SHA に束縛される。
- 候補の B-5 skip は L:2251 で `_resolve_duplicate` より前に拒否され、CLI は rc=1。
- stock skip も既存どおり成功復元せず、B の分類器が `outcome=skipped` を duplicate として扱う。

`slot-start` は layout 確定後、`pipeline-submitted` は campaign 呼出し前です。`.publishing` が異常終了で残れば、同 directory の再公開は `mkdir` で拒否されます。retry は別 attempt directory なので、この残骸自体は retry を妨げません。

**代案：変更不要。** L:10375／L:10411 相当の TL テストを維持する。ただし所見3の job 全体終了は別途扱う必要があります。

# 8. 物理 attempt identity、stock 成立、通常 WAL 順序は整合する

**対象：B:153、B:350、B:382、B:555、`ident.py:201`、`loop.py:222`、`campaign_claim.py:421`。判定：refuted。格：—。**
**成果物影響：通常経路では retry ごとの claim 分離、fresh session、stock の出所制約が維持される。**

slot key は `attempt-0/1/2` を含み、`search_config` 全体が canonical preimage に入ります。campaign ID と claim 名、protocol digest が attempt ごとに分かれ、旧 claim を削除しません。

B:352 の campaign ID 末尾照合は、`ident.cfg_hash` の SHA-256 先頭8桁と整合します。lock の preimage SHA、slot、genome、variant、WAL 全 record の build attempt も照合しています。

`_stock_established` は certified、品質正常、STOCK token、stock genome の variant、有限正 fitness を要求します。不成立なら探索前に `stock-unestablished` です。random／sweep の生成関数には stock 値・台帳を渡していません。

WAL の厳密列も今回の argv と合います。`--verify-performance` は legacy 1回と performance 5回を実行するため、成功時は **10 record** です。5 record の K2 pair 観測を、この B-5 構成の期待列に代入する根拠はありません。P:2180 の各 repetition の即時 return と P:2436 の pass 失敗時 return により、anomaly 後の bench 到達も認められません。

**代案：変更不要。** 実機の10 record・tag 順の確認は未実走として残す。

# 9. 通常の A/B、handshake、endpoint・score の基本規則は整合する

**対象：B:347、B:603、B:626、B:750、B:767。判定：refuted。格：—。**
**成果物影響：通常完了する対象経路では、予算返却・探索値の score 流用・score anomaly 後の次点選択は起きない。**

- diff-quarantine は `build_start → abort` を書きますが、submission sidecar がないため B:347 が先に A-only と判定します。
- 投入後 build failure・anomaly・bench abort は B を消費します。
- retry は同 proposal、同論理 slot、attempt+1、追加最大2回。`submitted_once` により論理 B は重複加算されません。
- 品質欠測は B を返さず endpoint から除外します。
- `.rejected.json` は A を消費して次へ進み、45分無応答は retry なしの `proposal-wait-timeout` です。
- whiteboard は件数だけでなく順序・値・全 field を比較します。current_perf／baseline は直近の正常 certified、なければ stock-start。abort rate は100倍です。
- request に leading indicators 全体はありませんが、親は台帳の bench payload を読めます。`slot-<b>.json` に campaign root、digest path、bench payload はあります。
- endpoint は `(-fitness,value,b)`、固定イベント公開後に5 fresh score session。
- score anomaly は次点に戻らず fallback、score 品質欠測は欠測。
- endpoint がなく探索品質欠測がある場合の `score=None` は、欠測を stock で埋めない読みとして整合します。

**代案：基本処理は維持。** 所見1〜3の例外経路を同じ規則へ接続する。

# 10. `indeterminate` を一律に機械故障とする根拠はない

**対象：P:657、B:370。判定：refuted〔一律 retry 必須という疑い〕。格：—。**
**成果物影響：判定不能 verdict だけを理由に無料 retry しない現挙動は、§3.3 の限定列挙を広げない。**

P は verifier の非 certified verdict を abort reason にします。`indeterminate` は「認証できなかった」ことを示しますが、それだけでは通信障害・node 喪失・候補と独立な供給／入出力障害を証明しません。

投入後の非認証として B を消費し、bench・endpoint を許さない点は適切です。故障原因が別途証明される場合は所見2の分類対象になりますが、verdict 名だけで機械故障集合へ追加するのは支持しません。

**代案：B:370。** verdict と故障原因を分けて扱い、証拠なしの retry は追加しない。

# 11. 生成器・統計関数・変異テストの静的検算

**対象：B:75、B:110、B:128、R:42、R:57、R:79、R:123、TB／TR／TL。判定：refuted〔主要計算の不一致・期待値の恒真性〕／kill 実走は根拠不足。格：—。**
**成果物影響：読解した計算は登録した候補分布・主要な統計判定を維持する。ただし本レビューは kill 実績を独立認定しない。**

重みは Decimal、`2**128`、ROUND_FLOOR、100／130桁全要素一致。random は指定 preimage、unsigned big-endian、`U<L`、`bisect_right`。sweep は指定28点の hash 順です。

統計は inclusive tail、族6固定・p=1穴埋め、標本分母の4 CV 最大、fallback 対数≥2で副解析、厳密な `CV>2f`、判定順1〜8を実装しています。pilot は登録判定前に戻り、横断 anomaly は workload/value 集合を先に作って既存 endpoint を失格にします。

変異対応の静的検算結果は次のとおりです。

| ID | 現物の検査と限界 |
|---|---|
| M0 | コメント追加は等価。生存実績は author 報告のみ。 |
| M1 | TB:25 の m₁、ln2 数値、表 SHA は固定定数。実装から期待値を生成していない。atanh による由来そのものはコメント上の主張。 |
| M2 | TB:45 は実 hashlib と固定 residue の小表 vector。独立だが、登録1000重みを使う end-to-end vector ではない。 |
| M3 | TB:55 は実 digest を M にして U=L を構成。hash stub はなく、境界を直接踏む。 |
| M4 | 固定28点から別途 hash 順を計算。数値順への変異を検出できる。 |
| M5〜M9 | 単独品質条件、投入後 abort、tie、探索1000対score30、whiteboard 順序交換という異なる期待値がある。 |
| M10〜M12 | 実 main／identity／context を通す。M12 は campaign 境界で **marker を読み、その後に例外**を投げる。依存境界の fake はあるが、検査対象を stub してはいない。 |
| M13／M14 | 実 shell の呼出し数、および空値拒否位置を検査。単なる最終 rc 一致ではない。 |
| M15 | 仮想時計で2700秒、retry 0を検査。job 全体終了の検査ではない。 |
| M16／M17 | TR の固定族6と pilot JSON 検査。13/4096・79/4096も明示定数。 |
| M18 | 固定60・4 job・53 sessionを検査。cap61変異は定数と整合ガードの2箇所変更であり、その形を報告に明記すべき。 |
| M19 | fake runner は duplicate を供給するだけで、分類・B=0・系列終了は実処理。TL:10411 は別途、実 CLI が復元へ進まないことを検査。 |

**代案：TB:45。** 登録重み表を使う固定候補 vector を補えば接続証拠が強くなる。変異実走の成否と上表の静的評価は区別して報告する。

# 12. 品質欠測の系列単位への波及は、親裁定が必要

**対象：R:350、R:358、事前登録 §7.4(2)。判定：根拠不足〔逐語解釈〕。格：—。**
**成果物影響：探索中の品質欠測を系列欠測と数えるかで、比較が優越／同等まで進むか、判定不能で止まるかが変わる。**

探索評価に品質欠測が1件あっても、別の正常 endpoint と5正常 score session が得られれば、R:358 が成立し `missing=None` になります。イベント全体の品質欠測検査はその後の `else` にしかありません。

裁定・B producer の「当該 session を endpoint から外して探索継続」には合います。一方、§7.4(2) の「12系列のいずれかが機械故障・品質欠測」を、探索 session の欠測も含めて読むなら一致しません。§5.3・§6との関係を含め、本レビューだけでどちらかへ確定しません。

**代案：R:358。** 「探索品質欠測は当該 session の資格のみ失う」のか「比較の第2段も発火する」のかを親裁定で明記し、その対照例を consumer test に置く。

# 13. session 算術と verify 区間名は適切。時間見積りは外挿

**対象：brief のβ節、裁定 §1・§2.2、B:265。判定：refuted〔53の算術・隣接差の誤り〕。格：—。**
**成果物影響：53は論理 session 上限として正しく、WAL計時を純 verifier 秒と誤認しなければ費用集計の意味は維持される。**

`3×(stock-start 1＋探索10＋score 5)＋block-stock 5=53≤60` は正しいです。retry と品質 round は物理回数で、53に加算する新論理 slot ではありません。

B:279 は `build_done → legacy verify_done → performance verify_done…` の隣接差を取り、名称も「trace+verifier+周辺処理 区間」です。

brief は12〜14分を「見積り」とし、後続裁定は「外挿」、8h／3hを暫定値として明記しています。ただし brief の「verifier費用の5/6」は回数比からは導けません。legacy と full-scale の所要は同一ではありません。

**代案：brief の当該記述。** 「6回中5回が performance verify」と書き、時間比は試走後の実測から記載する。この文言単独の問題は **real／nit** で、現時点の実装値への影響は示せません。

## 総括

**must-fix**

1. **前処理拒否で系列を終了させない。** 帰属不一致は A-only 継続、layout 前の候補拒否を機械 retry にしない — **B:721、B:762、L:2148**。
2. **verify 環境故障を候補失敗・fallback にしない。** 裁定の reason 集合も修正対象 — **B:55、B:375、P:2410**。
3. **job 全体打切り後の投入済み B・物理 attempt を集計する。** durable sidecar を報告へ接続 — **B:578、B:616、R:313、R:328**。

**should**

- **4：** critic 診断の両側欠落と正本不一致を区別する — **B:443**。
- **5：** 拒否・timeout を含む全 handshake 待機費用を残す — **B:626、R:315**。
- **6：** report で fitness と bench median の一致を検査する — **R:239、R:358**。

**判定：NO-GO。**

親裁定が必要なのは、verify／bench の環境 reason と §3.3 の対応、診断欠測時の入力契約、探索品質欠測の §7.4(2) への波及です。実機 build・bench・共有 FS handshake、変異 kill の独立再実走は未確認です。