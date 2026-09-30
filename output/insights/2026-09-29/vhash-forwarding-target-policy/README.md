# 前進先の選び方を比べ、最良設定の Cicada の上で C と E を測り直した (VHash 論文 md_21、2026-09-29〜30)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-vhash-forwarding-target-policy`、起点 local main `8fe87f852` (開始 gate fresh rc 0、2026-09-29 21:5x JST)、CCBench submodule = pin C `68106660` (動かしていない)。
job dir `/work/1/SFC/tanab/tmp/vhash-forwarding-target-policy-2026-09-29/` (段 1 brief・段 2 plan・段 3 相談 2 本・段 4 裁定・段 6 裁定 1〜5・Codex の prompt と報告・計算ノードの raw・変異の記録)。
依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_21.txt` と `common.txt` (job dir `inputs/` に逐語)。対象 item は worklog の [T-2910]・[T-2894]・[T-2903]。

**この文書の性能・GC の値は、正しさ検査 (§5) で巡回 0 を確かめた方策の、計器入り build の診断値である。判定の上限は indeterminate で、certified・serializable とは書かない。throughput は計器なし build の値だけを使い、差は判定しない (記述値)。**
**比較の土台は md_11 の観測最良の Cicada 設定である。その設定の正しさ検査 (md_20) は本 wave の記録時点で local main に着地していない。最良設定の正しさについて言えるのは、md_14 §5 と本 wave §5 の検査が最良 genome の trace build で巡回 0 だった範囲だけである。**

## 1. 依頼と結論

依頼 (md_21): md_14 の構成 E は「今」の時刻へ前進し、zipf 0.9 では前進の 99.7% 以上が失敗して効果が無かった。md_6 の構成 C は長い tx で成功率が落ちた。前進先の選び方 (今・最小・既読の可視区間に収まる最大・1 tx 1 回) を比べ、md_11 の最良設定の Cicada の上で stock・C・F・E を同時刻に測り直す。

結論:

1. **E の前進先を「既読の可視区間に収まる最大の時刻」(E-max) にすると、「今」(E-now) では効かなかった中程度の偏りでも回収境界が進んだ。** 待機 10 ms・skew 0.6 で、E-max の回収境界の遅れの平均は E-hb (flag だけ) 比 −9.5 ms (19.5 → 10.0 ms、GC 10 µs、rep 中央値)、論理生存版数 −13.4 万版、版の保持時間の中央値 16.4 → 8.2 ms。E-now は同じ条件で 17.4 ms とほぼ効かない。MinRts を決めた thread が長い tx だった割合は E-hb 0.88 → E-max 0.13 (§4.2)。
2. **skew 0 では E-max は E-now よりさらに効く。** 遅れ 19.5 (E-hb) → 9.6 (E-now) → 6.0 ms (E-max)、生存版数 132.3 万 → 117.1 万 → 111.3 万 (GC 10 µs)。
3. **skew 0.9 では E-max でも効果は小さい。** 遅れ −1.0 ms (20.4 → 19.4 ms)。E-max の要求の約 75% が `no_room` (既読の可視区間の上端が自分の旧時刻・公開済みの時刻以下) で、これは「既読のどれかが自分の時刻より下の時刻で上書きされ、validation での abort がすでに決まっている tx」に当たる (§4.3)。前進先の選び方ではこの tx を救えない。
4. **C では「最大」(C-max) は既読不一致を減らさず、「届くところまで進む」(C-partial) が長い thread の成功率を上げた。** many_ops・skew 0.6 で長い thread の成功率 (発火を分母) は C-min 0.050 → C-max 0.048 → C-partial 0.320 (GC 10 µs)。段 1 の仮説 P3 (C-max の成功集合は既読について C-min と同じ) と合う。ただし長い tx の完了率はどの腕でも 0.0003 以下で、成功率の向上は完了に結び付いていない (§4.4)。
5. **T-2903 (最良設定での stock・C・F):** C-min の throughput は stock 比 0.97〜1.04 で差は見えない。F (abort と再実行) は skew 0.9 で stock 比 0.21〜0.49 と大きく落ち、skew 0.6 では 0.98〜1.00 (§4.5)。md_6 (CMake 既定の Cicada) の「C / F と stock の差は検出できない」は、最良設定の上では F について成り立たない。
6. **正しさ: 巡回 0。** 最良 genome の trace build で E-max (高競合 tuple 50・zipf 0.9、低競合 tuple 10,000・skew 0)・C-max・C-partial の 6 cell すべてで判定器の巡回 0、integrity の数値項目 0、trace の C 行 = commit 数、保持版の変化 0。検査専用の壊し (既読不一致を無視して前進する E-now) は 2 cell とも到達 (前進の強制成功 5,449・5,993 回) し、保持版検査が待機中の既読版の変化 1,484・1,649 件を検出した (判定器の巡回は 0) (§5)。

![E 腕の回収境界の遅れと生存版数](figures/target-policy-gc.png)

図の読み方: 上段 = 回収境界の遅れの平均 (leader が 10 µs ごとに取る等間隔標本、ms)、下段 = 論理生存版数の平均 (百万)。横軸の目盛は「待機 ms / skew / GC 間隔 µs」、色 = 腕 (E-hb・E-now・E-max・E-max-once)。小さい点が各 rep、菱形が rep 中央値、縦線は小標本 95% CI (n=3)。計器入り build の診断値。

![E 腕の前進の成功率 (要求を分母)](figures/target-policy-success.png)

図の読み方: 縦軸 = 成功 / 要求 (%)。要求 = 待機の安全点で GC 間隔が経過し自分の GC flag が 0 だった回数。E-hb は前進を試さないので系列が無い。E-max の要求には「一度成功した後、上端が動かないので `no_room` になる要求」も入るので、この比は「tx のうち何割が前進できたか」ではない (§4.3)。

![E 腕の失敗理由 (要求を分母)](figures/target-policy-reasons.png)

図の読み方: 失敗理由ごとの panel。縦軸 = その理由の回数 / 要求 (%)。E-now の失敗はほぼすべて既読不一致、E-max は既読不一致 0 で `no_room` と書き込み制約、E-max-once は 2 回目以降の要求が `once skipped`。

## 2. 何を作ったか (仕様)

`patches/cicada-forwarding-variant.patch` (md_6、C) → `patches/cicada-forwarding-gc.patch` (md_14、E) の上に重ねる `patches/cicada-forwarding-target.patch` と、検査専用の壊し `patches/cicada-forwarding-target-broken-ignore-mismatch.patch`。md_6・md_14 の patch は、記録がその hash に束縛されているので変えていない (D2295 の却下理由と同じ)。変更は `cc/cicada/transaction.cc` だけで、**新しい `#if` を足していない** (既存の `CICADA_FWD_ENABLE`・`CICADA_FWD_COUNT`・`CICADA_GC_SAFEPOINT`・`CICADA_GC_COUNT` の内側。directive 行の数は gc 適用後と同じ、条件 gate の登録簿は不変)。macro・flag・登録は `patches/README.md` の節が正本。

**確認・確定・公開の行は変えていない。** 変えたのは目標時刻の計算、`once` の抑止、計数だけで、確認 (事前確認 → 既読版の rts を t′ へ CAS-max → seq_cst fence → 版列を観測し直して可視を確認)・確定・公開 (成功時だけ ThreadWtsArray := t′、ThreadRtsArray := max(旧, t′−1)) は md_14 と同じ行が走る。

| flag (既定 = 現行) | 値 | 目標時刻 |
|---|---|---|
| `--cicada_gc_target` | `now` (既定、md_14) | 自 thread の clock から作る厳密に新しい時刻 (= cap) |
| | `max` | 上端 U が無ければ cap、あれば min(cap, below(U))。旧 ts・公開済みの時刻以下なら `no_room` (試行に数えない) |
| `--cicada_gc_once` | `false` (既定) / `true` | true なら 1 tx で目標計算に入るのは最初の要求だけ。以後は `once_skipped` を数え、GC flag だけ立てる (E-hb と同じ) |
| `--cicada_fwd_target` | `min` (既定、md_6) | 先頭 K 版の最古の committed 版の直後の自 thread 形式の時刻 L |
| | `max` | max(L, min(cap, below(U))) |
| | `partial` | t = min(cap, below(U)) が現在の ts より大なら t (L 未満でも採る = 目標に届かない部分前進、成功すれば `short_success`)、そうでなければ L |
| `--cicada_fwd_once` | `false` (既定) / `true` | true なら 1 tx で目標計算に入るのは最初の発火だけ |

- **上端 U:** read set の各既読版について `ldAcqLatest()` から版列を辿り、既読版に到達するまでに見た非 aborted の版 (committed・pending・deleted) のうち最後 (= 既読版の直上) の wts の最小。直上が無い key は上端なし。既読版に到達できなければ `read_mismatch` として失敗させる。
- **below(U):** U−1 以下で下位 8 bit が自 thread 番号の最大の時刻。候補 ((U−1) & ~255) | thid が U 以上なら 256 下げ、下げられなければ失敗。
- **cap:** 現行 E-now の式そのもの (`max(rdtscp, localClock_ + clockBoost_, max(旧 ts, 公開済み) >> 8)` から作る自 thread 形式の時刻)。上端が無ければ E-max ≡ E-now。
- **計数:** 既定 flag では `CICADA_FWD_V1`・`CICADA_GC_V1` を現行と byte 同形で出す。既定以外では `*_V2` を出す (V1 の全 field + `target`・`once`、thread 別に `no_room`・`once_skipped`・`uncapped`、C は加えて `short_success`)。会計恒等式は E: 要求 = overflow + no_room + once_skipped + 試行、C: 発火 = f_aborts + no_target + no_room + once_skipped + 試行、試行 = 成功 + 各失敗。
- **壊し:** E の事前確認と再観測の 2 箇所の既読不一致の判定を ok とみなす (単一の意味の変更、段 6 裁定 4)。壊し build では GC 行を常に V2 で出し、既読不一致を無視して成功した数を `forced_success` として数える。検査専用で計測には使わない。
- **driver:** `orchestrator/campaign/vhash_forwarding_prototype.py` の `target-run --workload … [--wait-us 1000|10000] [--skew 0|0.6|0.9] [--smoke]` / `target-aggregate --raw …`。既存の `run`・`gc-run`・`aggregate`・`gc-aggregate` の受理・拒否は変えていない。patch stack は variant → gc → target、genome は md_11 の観測最良。
- **作図:** `make_figures.py` (この dir)。`PYTHONPATH=<repo> python3 make_figures.py <aggregate.json> <raw…> --output <stem>` で PNG / PDF / provenance を出す。raw から再集計して aggregate と一致しなければ止まる。

md_10 のモデル・md_13 の論証との関係: E-max は md_10 のモデルの候補集合 (より新しい確定版の next_free) にも入らない時刻を選ぶ (md_14 の E-now と同じく、モデルの結論は直接は及ばない)。E-max が確認手順に新しい依存を足さないことは静的に確かめたが、確認の後に既読版と t′ の間へ pending 版が入る列を writer 側の再確認が捕まえるかは、E-now と同じく条件 W* (D2292 で未認定) に依存する。

## 3. 経緯 — 設計の訂正と実機でだけ出た不具合

### 3.1 段 2〜4 (設計)
- 段 3 相談 B: 依頼の「1 tx 1 回」を plan は「成功後は試さない」と定義していた → 「1 tx で目標計算に入るのは 1 回」に直した。E-max に「今」の上限が抜けていた → cap を現行 E-now の目標そのものにした。成功率の分母を要求 (C は発火) に固定した。T-2903 を閉じるため F を many_ops・normal に足した。
- 段 3 相談 A: E-max の安全は「確認手順が同じ」だけでは言えず W* 条件付き (→ §2 末尾)。上端を辿る走査が回収・再利用に遭うという指摘は、md_14 §3.3 の不変条件 (ThreadRtsArray を tx 開始時の MinWts−1 か、成功時の t′−1 に保つ。どちらも既読版の直上の版の wts 未満) で、回収の切れ目は既読版以下にしかなれず、既存の再観測も同じ鎖を辿るので新しい露出ではない、と静的論証で退けた (実行時の証明ではない、§7)。

### 3.2 段 6 (レビュー・smoke・検査)
| 回 | 何で見つけたか | 内容 | 直し方 |
|---|---|---|---|
| 1 | レビュー A | E-hb は要求を数えるが試行しないので、E の会計恒等式を全腕に当てると集計が必ず失敗する | 恒等式を mode=e の腕だけに当てる |
| 2 | レビュー A | `below(U)` が U ≤ 256 を一律に拒否 | 候補 < U の確認に直す |
| 3 | 焦点走 1 (1200 passed・3 failed) | target patch の文脈行に `#if CICADA_GC_SAFEPOINT`・`#if CICADA_FWD_COUNT` が入り、spawn site テストの define 一覧で 2 macro が「CCBench に元からある」側へ落ちた | `test_ccbench_spawn_sites.py` の重ね patch 用の表に 2 項目を登録 (md_14 の先例 6b72c649f と同じ足跡、期待件数は不変。md_21 の所有外の file) |
| 4 | smoke 1 (36295・36296) | 7 build は通ったが最初の run で `CICADA_LONGTX_V1` の top-level key の期待 ({threads}) が実物 ({schema, threads}) と違った | 実物に合わせ、実 stdout の行を写した回帰テスト |
| 5 | 焦点再レビュー | SAFEPOINT の無い build (stock・C・F の計器あり) の GC 行の mode は `"none"` なのに driver は `"off"` を要求 | build の macro 集合と腕の flag から期待を導く |
| 6 | 検査 1 (36358) | 壊しを E-max で走らせる段 4 の設計では、E-max が可視区間の内側に目標を取るので確認で既読不一致が起きず、壊しに到達しない (forced_success 0、E-max の確認での read_mismatch 0.0) | 壊しは E-now で走らせ、壊し build では GC 行を常に V2 で出す |
| 7 | 図の目視 | many_ops の図に凡例が無い、throughput の図で C 系と E 系の色が重なる | 作図の修正 (段 6 裁定 5) |

4 と 5 は同じ型で、C++ の出力行を新しく読む driver を推測の fixture で検査したため、1 巡に 1 件ずつしか出なかった。

## 4. 本計測

### 4.1 条件

| 項目 | 値 |
|---|---|
| 機材 | Pegasus 計算ノード (gen_S)。1 job = 1 条件群、7 job を 7 台で同時刻に (request 36392〜36398、各 Elapse 217〜431 s) |
| commit | `63719ffaa` (target-run の経路は記録時の HEAD と同じ。以後の fix は壊しの解析・壊し patch・作図だけ) |
| Cicada 設定 | md_11 の観測最良 `BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0` |
| 共通 | 48 thread、1M 件、rratio 50、max_ope 10、extime 3 s、clocks_per_us 2100、GC 間隔 {10, 1000} µs、長い thread 4 本 (normal は 0) |
| wait_after_reads | 10 read + 1 write の後に待機。待機 10 ms × skew {0, 0.6, 0.9}、待機 1 ms × skew 0.9。腕 = stock・C-min・E-hb・E-now・E-max・E-max-once。E 腕の待機は 100 µs の slice |
| many_ops | 1,000 操作・read 90%。skew {0.6, 0.9}。腕 = stock・C-min・C-max・C-partial・C-partial-once・F |
| normal | skew 0.9。腕 = stock・C-min・C-partial・F |
| 反復 | 性能 = 計器なし build 3 rep、計数 = 計器 build 3 rep (normal は 1 rep)。rep ごとに腕順を巡回。各 run の前に単独性確認 (競合 0) |

raw (repo 外、job dir `jobs/meas-*/`) と集計: `data/target-aggregate-compact.json` (集計から rep ごとの長い tx の thread 別行を除いたもの。元の sha256 は同 JSON の `compaction`)。

### 4.2 E の主比較 (待機 10 ms、rep 中央値)

| skew / GC µs | 遅れの平均 ms (stock / E-hb / E-now / E-max / E-max-once) | 生存版数の平均 千 (E-hb / E-now / E-max) | 保持時間の中央値の上限 ms (E-hb / E-now / E-max) | 長い tx が MinRts を決めた割合 (E-hb / E-now / E-max) | 成功 / 要求 (E-now / E-max / E-max-once) |
|---|---|---|---|---|---|
| 0 / 10 | 19.65 / 19.51 / 9.64 / **5.96** / 8.18 | 1,323 / 1,171 / **1,113** | 16.4 / 8.2 / **4.1** | 0.95 / 0.24 / **0.01** | 0.434 / 0.456 / 0.028 |
| 0 / 1000 | 19.97 / 19.67 / 11.39 / **7.07** / 8.26 | 1,321 / 1,205 / **1,128** | 16.4 / 8.2 / **4.1** | 0.90 / 0.31 / **0.02** | 0.489 / 0.592 / 0.149 |
| 0.6 / 10 | 19.73 / 19.47 / 17.40 / **10.02** / 9.36 | 1,330 / 1,295 / **1,195** | 16.4 / 16.4 / **8.2** | 0.88 / 0.62 / **0.13** | 0.145 / 0.167 / 0.038 |
| 0.6 / 1000 | 18.60 / 19.54 / 18.39 / **12.58** / 10.59 | 1,332 / 1,309 / **1,202** | 16.4 / 16.4 / **8.2** | 0.88 / 0.63 / **0.17** | 0.154 / 0.302 / 0.159 |
| 0.9 / 10 | 24.10 / 20.38 / 20.44 / 19.35 / 20.06 | 1,314 / 1,317 / 1,295 | 16.4 / 16.4 / 16.4 | 0.99 / 1.00 / 0.94 | 0.002 / 0.024 / 0.007 |
| 0.9 / 1000 | 23.92 / 20.99 / 20.74 / 19.74 / 19.91 | 1,318 / 1,312 / 1,305 | 16.4 / 16.4 / 16.4 | 0.98 / 0.99 / 0.97 | 0.003 / 0.010 / 0.026 |

rep ごとの差の中央値 (E-max − E-hb): 遅れ skew 0 / 10 で −13.5 ms、0.6 / 10 で −9.5 ms、0.9 / 10 で −0.8 ms。生存版数 −21.1 万・−13.4 万・−1.6 万。推定 bytes (版数 × (sizeof(Version) + 値 4 B)) −27.8 MB・−17.7 MB・−2.1 MB。保持時間は 2 のべきの bin の上限なので、8.2 → 4.1 ms は「中央値が 1 bin 下がった」と読む。
待機 1 ms・skew 0.9 では 5 腕とも遅れ 2.3〜2.9 ms・生存版数 104.6 万〜105.6 万で、差は見えない (待機が GC 間隔の数倍しかなく、そもそも長い tx が境界を長く止めない)。

### 4.3 E-max の `no_room` と成功率の読み方
- E-max の要求の 40〜78% が `no_room`、確認での既読不一致は 0 (全条件)。`no_room` は 2 種類が混ざる: (a) 一度成功した後の要求 (上端が動かないので前進の余地が無い)、(b) 成功前から上端が旧時刻以下 = 既読のどれかが自分の時刻より下の時刻で上書きされている tx (validation での abort が決まっている)。計数はこの 2 つを分けていない。E-max-once で (a) が消え、待機 10 ms・skew 0.9 でも `no_room` が 3〜7% に下がるので、この条件の E-max の `no_room` の大半は (a) と推定する (未検証)。待機 1 ms・GC 1000 µs では E-max-once でも `no_room` が 72% で、(b) が多い。
- 待機 10 ms・skew 0.9 で E-max の成功 / 要求が 0.009〜0.024 と低いのは、成功前の失敗の大半が書き込み制約 (19〜21%) と (b) であるため。E-max-once の成功 / 要求 (0.007〜0.026) は「最初の要求で前進できた割合」に近く、skew 0.9 では 1〜3% の tx しか前進できていない。
- **成功回数・成功率は前進先の選び方の比較の指標であって GC 改善の指標ではない。** GC 改善は §4.2 の遅れ・生存版数で読む。

### 4.4 C の方策 (many_ops、rep 中央値)

| skew / GC µs | 長い thread の成功 / 発火 (C-min / C-max / C-partial / C-partial-once) | 通常 thread の成功 / 発火 (同) | partial の部分前進 (short_success) | 長い tx の完了率 (stock / C-min / C-partial / F) |
|---|---|---|---|---|
| 0.6 / 10 | 0.050 / 0.048 / **0.320** / 0.207 | 0.850 / 0.874 / 0.966 / 0.970 | 7,797 | 0.00008 / 0.00022 / 0.00018 / 0.00002 |
| 0.6 / 1000 | 0.056 / 0.053 / **0.230** / 0.236 | 0.841 / 0.861 / 0.967 / 0.981 | 6,172 | 0.00003 / 0.00007 / 0.00010 / 0.00002 |
| 0.9 / 10 | 0.009 / 0.012 / **0.048** / 0.049 | 0.320 / 0.345 / 0.366 / 0.362 | 27,245 | 0 / 0 / 0.00002 / 0 |
| 0.9 / 1000 | 0.013 / 0.015 / **0.040** / 0.043 | 0.327 / 0.349 / 0.366 / 0.374 | 24,490 | 0 / 0 / 0.00003 / 0 |

![many_ops の C 方策: 長い thread と通常 thread の成功率、長い tx の完了率](figures/target-policy-many-ops.png)

図の読み方: 上段 = 長い thread の成功 / 発火 (%)、中段 = 通常 thread の成功 / 発火 (%)、下段 = 長い tx の完了率 (%、stock・C 各方策・F)。横軸 = skew / GC 間隔。点・菱形・縦線は §1 の図と同じ。

![many_ops の C 方策の失敗理由 (発火を分母)](figures/target-policy-c-reasons.png)

図の読み方: 失敗理由ごとの panel。縦軸 = その理由の回数 / 発火 (%)。C-min と C-max は既読不一致が 90% 前後 (skew 0.6) で同じ、C-partial は既読不一致が 30% 台へ下がる代わりに書き込み制約が 30〜43% に増える。

- C-max は C-min と成功率がほぼ同じ (P3 の予想どおり)。変わるのは成功時の前進幅 (C-max − C-min の中央値 +145,120 clock ≈ +69 µs、skew 0.6 / 10) と、書き込み制約がわずかに減ること。
- C-partial は長い thread の成功率を skew 0.6 で 4〜6 倍、skew 0.9 で 3〜5 倍にした。成功の一部は目標に届かない部分前進 (short_success)。
- **長い tx の完了率はどの腕でも 0.03% 以下で、3 秒の間にほぼ commit しない (md_6 と同じ)。** 前進の成功が増えても、1,000 操作の tx が最後の validation を通るところまでは届いていない。

### 4.5 throughput (計器なし build、3 rep 中央値、stock 比) と T-2903

| cell | stock (kTPS) | C-min | C-max | C-partial | F |
|---|---|---|---|---|---|
| many_ops 0.6 / 10 | 4,244 | 0.988 | 0.988 | 0.985 | 0.981 |
| many_ops 0.6 / 1000 | 4,216 | 0.991 | 0.991 | 0.993 | 0.999 |
| many_ops 0.9 / 10 | 3,593 | 1.017 | 1.025 | 0.688 | 0.212 |
| many_ops 0.9 / 1000 | 3,304 | 1.008 | 1.016 | 0.996 | 0.380 |
| normal 0.9 / 10 | 3,656 | 1.033 | — | 1.024 | 0.301 |
| normal 0.9 / 1000 | 3,341 | 1.043 | — | 1.024 | 0.493 |

wait_after_reads の 8 cell では E 系・C-min とも stock 比 0.972〜1.040。

![throughput の stock 比 (記述値)](figures/target-policy-throughput.png)

図の読み方: 縦軸 = throughput / stock (同じ cell・同じ job の計器なし build の rep 中央値に対する比)。横軸 = cell。**記述値であり、差を判定しない。** n=3 の区間は広く、many_ops 0.9 / 10 の C-partial (0.688) は rep の値が 0.26〜1.0 に散る。

- **T-2903 の結論:** md_6 は CMake 既定の Cicada (rr50 で最良より約 4.5 倍遅い) の上で「C / F と stock の throughput の差は検出できない」とした。最良設定の上では C-min について同じ (stock 比 0.97〜1.04) だが、**F は skew 0.9 で stock の 0.21〜0.49 倍に落ちた**。最良設定は BACK_OFF=0 で abort 後にすぐ再実行するので、F が発火のたびに abort と再実行を繰り返す費用がそのまま throughput に出ると推定する (未検証)。F は「再実行の費用を示す対照」として読む (md_6 §5.3 と同じ)。
- md_14 §4.5 と同じく、実行コードが同じ腕の間でも 0.97〜1.04 の揺れがある。

## 5. 正しさ検査 (md_3 の trace と判定器、md_17 の拡張、D2279)

repo 外起動器 (md_14 の起動器の派生、job dir `verify/launch_cicada_run_target.py`、検査 2 回目で使った bytes は `jobs/verify2/launch_cicada_run_target.used.py`、sha256 `b72ff100…`) で、trace patch → variant → gc → target (→ 壊し) の TRACE=1 build を最良 genome で走らせた。job 36408.nqsv (Elapse 221 s、木 `69d5d5310`)。8 thread・長い thread 2 本・extime 1 s。結果 = `data/verify-result-compact.json`。

| build | cell | 巡回 | 判定 | C 行 = commit | integrity の数値項目 | 保持版の変化 | 読んだ版の食い違い | 到達 (前進の成功) |
|---|---|---|---|---|---|---|---|---|
| E-max | tuple 50・zipf 0.9・待機 10 ms・GC 10 / 100 | 0 / 0 | indeterminate | 一致 | すべて 0 | 0 / 0 | 0 / 0 | E 5 / 15 (要求 5,540 / 5,346)、C 2,637 / 2,612 |
| E-max | tuple 10,000・skew 0・同 | 0 / 0 | indeterminate | 一致 | すべて 0 | 0 / 0 | 0 / 0 | E 513 / 452 (要求 9,722 / 8,892) |
| C-max | many_ops 型・tuple 50・zipf 0.9・GC 10 | 0 | indeterminate | 一致 | すべて 0 | 0 | 0 | C 3,675 (発火 272,481) |
| C-partial | 同 | 0 | indeterminate | 一致 | すべて 0 | 0 | 0 | C 5,887 (発火 275,641) |
| 壊し (E-now・既読不一致を無視) | tuple 50・zipf 0.9・待機 10 ms・GC 10 / 100 | 0 / 0 | indeterminate | 一致 | すべて 0 | **1,484 / 1,649** | 0 / 0 | 強制成功 5,449 / 5,993 |

- integrity の数値項目 = orphan_reads・version_dups・dup_txids・genesis_commits・missing_txids・write_version_mismatch・malformed_keys・framing_violations・lock_coverage_violations・write_intent_violations・permutation_violations。`integrity.clean` は Cicada に証拠面が無いので構造上 false (md_3 §3)。起動器はこれを失敗と数えるので job の rc は 1 になる (巡回・数値項目の異常ではない)。
- **言えること:** 実測した YCSB と待機型・操作数型の長い tx の履歴で、E-max・C-max・C-partial の前進の成功を含む状態でも判定器は巡回を検出せず、待機中の既読版は変わらなかった。壊しは到達し、回収の危険 (待機中の既読版の変化) を保持版検査が捉えた。
- **言えないこと:** serializable・certified (上限 indeterminate)。壊しを判定器は検出しなかった (巡回 0): 既読不一致を無視して公開しても、最後の stock validation が既読の食い違いで abort させるので、履歴には巡回が残らないと推定する (未検証)。回収の危険は判定器の対象外で、保持版検査は待機の前後の照合だけを見る (§7)。
- 検査 1 回目 (36358、木 `a91f0260a`) は、C の 2 cell が旧木の driver の mode の誤り (§3.2 の 5) で要約なし、壊しは E-max で走らせたため到達 0 (§3.2 の 6)。E-max の 4 cell は巡回 0・保持版の変化 0 だった。

## 6. 変異 (login では殺せない C++ の論理は §3.2・§5 の実機観測で扱う)

独立 clone (D1009) を commit `69d5d5310` (driver・テストは記録時の HEAD と同じ) に固定し、束ね経路 (D842、`dispatch_compute.py --task mutation`) で走らせた。
事前登録は段 4 (MT1〜MT8) と段 6 裁定 1〜4 の fix の前 (MT9〜MT16)。対象テスト = `orchestrator/tests/test_vhash_forwarding_prototype.py`・`orchestrator/tests/test_ccbench_spawn_sites.py`。

| 段 | request | 結果 |
|---|---|---|
| probe (全件 SURVIVED 期待で観測 node を集める) | 36422 (2,222 s) | baseline PASSED。MT1・MT3〜MT16 の 15 件はすべて登録したテストが赤 (MISMATCH = 殺された)、MT2 は SURVIVED |
| final (狙い直した MT2 だけ、driver のテスト 1 file) | 36593 (119 s) | baseline PASSED、KILLED 1 (`test_target_count_throughput_ineligible`) |

変異: MT1 (patch stack から target を外す)、MT2 (計器ありの throughput を性能集計に入れる)、MT3 (計数行の重複を受ける)、MT4 (腕順の回転を止める)、MT5 (欠けた job を受ける)、MT6 (V2 の欠けた key を受ける)、MT7 (成功率の分母を試行にする)、MT8 (E-max の flag を now にする)、MT9 (E の会計恒等式を E-hb にも当てる)、MT10 (V2 の schema 1 を受ける)、MT11 (GC 行の mode を照合しない)、MT12 (`policy_exercised` を常に真にする)、MT13 (重ね patch 用の表から gc patch の項目を外す)、MT14 (LONGTX 行の key の期待を誤りへ戻す)、MT15 (SAFEPOINT なしの mode 期待を `"off"` に戻す)、MT16 (壊しの解析で V1 行を受ける)。
- **MT2 の erratum (DW-M02):** 登録した置換 (集計のラベル検査を外す) は、性能集計への混入を防いでいる build 種による振り分けと重なる冗長な検査を外すだけで、登録した性質を起こさず SURVIVED した。振り分け側へ狙い直し (count の枝で性能集計にも append)、final で KILLED。初回の結果は消さずに残した (job dir `mutation/erratum-mt2.md`)。
- **final を全件で取り直さなかった:** probe の Elapse が 2,222 s で、全件の final を足すと本 wave の計算が合計 2 node 時間を超える見込みだった (common.txt 3)。MT1・MT3〜MT16 の kill の証拠は初回の dispatch probe の観測 node (各変異で登録したテストが赤) で、final の完全一致照合 (DW-M08) は MT2 だけで行った。
- 記録: job dir `mutation/` (spec・results・期待 node)。

## 7. 確かめたこと / 確かめていないこと

確かめたこと (実測):
- 既定 flag で目標・出力行が md_14 と同じになること: 全 macro 未定義での前処理の一致 (gc 適用後と target 適用後)、`#if` 系 directive 行の数の一致、既定腕 (stock・C-min・F・E-hb・E-now) の V1 行が既存の解析を通ること (smoke 2・本計測の全 run)。
- 正しさ検査 (§5)、本計測 (§4)、焦点走 (7 file、最終 commit `69d5d5310` で 1,219 passed・2 skipped)。

確かめていないこと・限界:
- **serializability** (上限 indeterminate)。E-max の安全は E-now と同じく W* (確認の後に既読版と t′ の間へ置かれた pending を writer 側が待機解除後に再確認すること) に依存する。弱メモリは md_14 §7 と同じ (x86 の lock 付き CAS の順序保証に依存)。
- **上端の走査の物理的な安全は静的論証だけ** (§3.1)。保持版検査は待機の前後の wts・status の照合で、走査中の pointer、待機の後から commit までの窓、同じ wts での再利用は見ない。
- **最良設定 (md_11) の正しさ検査 (md_20) は未着地。** 本 wave の検査は最良 genome の trace build での巡回 0 まで。
- E-max の `no_room` の 2 種類 (成功後 / 成功前) を計数で分けていない (§4.3)。tx 単位の「前進できた tx の割合」は測っていない。
- C の成功率の向上は長い tx の完了に結び付いていない (§4.4)。完了までの距離 (最後の validation の失敗理由) は測っていない。
- 1 run 3 秒・3 rep。長時間の定常・他の thread 数・レコード数・長い thread 数・待機長 (1 ms / 10 ms 以外) は測っていない。skew は {0, 0.6, 0.9} の 3 点。md_11 の最良 genome は skew 0.9 で較正したもので、skew 0・0.6 の最良は確かめていない。
- 論理生存版数は物理メモリ量ではない (REUSE_VERSION=1 の pool は縮まない)。保持時間は切り離した版だけの分布で、bin の上限。時間は timestamp 空間 (clock boost を含む)。
- throughput の差 (§4.5 の揺れの内側、または n=3 で区間が広い)。

## 8. 次の版 (docs/paper-story-vhash/ 2 版目) へ

- **U0 の実物の証拠の範囲が広がった:** 前進先を「既読の可視区間に収まる最大」にすると、skew 0.6 でも回収境界の遅れが約半分 (19.5 → 10.0 ms)、MinRts を長い tx が決める割合が 0.88 → 0.13 になる。skew 0 では遅れ 19.5 → 6.0 ms。図 `figures/target-policy-gc.png`。
- **限界:** skew 0.9 では選び方を変えても効果は小さい。既読が自分の時刻より下で上書きされた tx (abort が決まっている tx) は前進できない。そうした tx を安全点で早く abort させて境界を解放する方策は未検討 (次の研究課題の候補)。
- **C の結論:** 最小前進と最大前進は既読不一致について同じ成功集合を持ち、部分前進だけが長い tx の成功率を上げる。ただし完了率は上がらない。
- **比較相手:** 最良設定の上では F (abort と再実行) が skew 0.9 で stock の 0.21〜0.49 倍に落ちる。
- 図: `figures/target-policy-gc.png`・`-success.png`・`-reasons.png`・`-many-ops.png`・`-c-reasons.png`・`-throughput.png` (生成器 `make_figures.py`、provenance 同名 `.provenance.json`)。

## 9. 計算資源

| 用途 | job (request / Elapse) |
|---|---|
| smoke | 36295 / 90 s、36296 / 91 s、36378 / 112 s、36379 / 110 s、36380 / 103 s |
| 正しさ検査 | 36358 / 195 s、36408 / 221 s |
| 本計測 | 36392 / 217 s、36393 / 428 s、36394 / 427 s、36395 / 431 s、36396 / 428 s、36397 / 427 s、36398 / 409 s |
| 焦点走 | 36266 / 79 s、36310 / 132 s、36407 / 132 s |
| provenance 監査 | 36264 / 14 s |
| 変異 | 36422 / 2,222 s、36593 / 119 s |

合計 6,387 s (約 1.77 node 時間、受入の全走を除く)。2 node 時間未満。
