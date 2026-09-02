# [T-1777] A-1 交互配置の coordinator は着地済みだった — 依頼の前提を実測で覆した

- `authority: insight` — 可変状態の正本ではない。現在地の正本は worklog の「次の一手」。
- `default_effect: no-state-change`
- wave = `worktree-dev-wave-t1777-interleaved-impl`、基準 commit `08a17b3b3` (着手直前の local main)
- 本 wave は**実装面の差分を持たない**。依頼された coordinator が既に在ったからである (§2、§3)。
- **ただし「純増ゼロ」ではない。** 敵対検証が、依頼の scope 外に 2 件の real な残件を出した
  (§6.1 の pilot 事前登録未凍結、§6.2 の中断 recovery の射程)。裁定パッケージは §7。

---

## 1. 依頼と、依頼が置いた前提

依頼は次のように述べていた。

> [T-1777] A-1 の対の配置を交互配置へ改める実装を入れる。境界の棚卸しと配置の確定は完了済みで、
> 一次資料は `output/insights/2026-08-29_t1777-interleaved-pairing`。**残るのは実装で**、閉包 4 member と
> driver に「単一 campaign の 5-rep ブロック交互 + AB/BA 均衡」の coordinator を入れる。

この「残るのは実装」は、T-1777 の次の一手 (1) をそのまま引いたものである
(`docs/archive/worklog-phase3-0829-1091.md:259-266`)。当該項は 1091 で書かれて以来、
1138 / 1139 / 1140 / 1141 / 1142 / 1143 と carry stub で持ち越されている。

## 2. 実測 — 前提は着手時点で既に成立していない

**次の一手 (1) が列挙する実装は、着手直前の local main `08a17b3b3` にすべて着地している。**
着地させたのは T-2074 の wave であり、同 wave は estimand の揃え直し (D1262) と
均衡配置 (D1295) を同じ変更単位で実装していた。

main の祖先である実装 commit は 3 本である。

| commit | 題 |
|---|---|
| `ed61448f6` | feat(a1): D1262 の arm 対と **D1295 の均衡配置**で A-1 の新 study 機構を作る |
| `73c6473fa` | fix(a1): 段 6 の敵対レビューが出した配線欠落と受理集合の穴を閉じる |
| `a1f91bdbe` | fix(a1): 並行 fix が生んだ合成不整合 3 件を単一 author で突き合わせて閉じる |

worklog 1142 (T-2074) の本文はこの均衡配置の着地を明示していない。次の一手の T-1777 も
更新されていない。**着地とその記録がずれたまま carry され続けたのが、本依頼が
「残るのは実装」と置いた原因である。**

## 3. D1295 の 7 項目とコードの対応

判定は「着地 = 発火するコードがあり、受理集合を実際に変える」とする。file:line は
基準 commit `08a17b3b3` のもの。

| D1295 | 内容 | 対応するコード | 判定 |
|---|---|---|---|
| 1 | 両 arm の build と verify を bench より前に完了する | `loop.py:512-525` が両 arm を `_prepare_evaluation` で準備し、`loop.py:576-584` が 2 本揃わなければ workload ごと reject する。`pipeline.py:1634` が `_PreparedEvaluation` を返す | 着地 |
| 2 | `bench_lock()` を全ブロックにわたり 1 回だけ保持する | `pipeline.py:1953` の `with bench_lock():` が `1974-2087` の group ループ全体を包む。ブロックごとの再取得は無い | 着地 |
| 3 | 10 対を 1 組とし、組の中に `A^5 B^5` と `B^5 A^5` を 1 つずつ置く。組内の先後を凍結 seed で決める | `pipeline.py:620-623` が bit に応じて `A^5 B^10 A^5` / `B^5 A^10 B^5` (= `A^5B^5` と `B^5A^5` の対) を作る。bit は `pipeline.py:610-617` の SHA-256 下位 1 bit | 着地 |
| 4 | contrast は物理順によらず役割で決める | `paper_story_a1_paired.py:1178-1190` が arm へ `minuend` / `subtrahend` を束縛し、`3093` が artifact の arm role から独立に再計算する。**contrast の中身は D1262 により `static10 − adaptive` から `variant − baseline` (fixed backoff − no-backoff) へ差し替わっている。** 「物理順に依らない」という D1295 の要求は保たれ、対の中身だけが後発の決定で更新された | 着地 (D1262 で更新) |
| 5 | 推定対象を「5-rep 均衡スケジュール下での差」に限定し、事前登録の本文に書く | policy の `pairing.estimand` に `arithmetic mean of paired differences under the balanced five-rep schedule` がある。**pilot policy の `preregistration` は `{path: null, sha256: null}` で未凍結**であり、`paper_story_a1_paired.py:1472-1483` が submit / measure を必ず拒否する | 部分。限定文言を含む事前登録が未起草で、pilot study を起動できない (§6.1) |
| 6 | `bench_max_rounds = 1`、CV 再測なし、静定と競合検査は残す | `loop.py:271-282` と `pipeline.py:1930-1931` が `1` 以外を拒否。`pipeline.py:1955` の `settle()`、`1982` の `competing_bench_pids()` が残っている | 着地 |
| 7 | 対ごとの同期追記台帳を置かない。全ブロック完了後に完了記録と受領証を出し、途中中断と片側 commit は invalid に閉じる | `pipeline.py:2158-2196` — ブロックループ内に WAL / file 書き込みが無く、受領証の後にのみ両 arm の `bench_done` を出す。collector 側の invalid 化は `paper_story_a1_paired.py:3549-3562,3763-3803`。中断は `wal.py:1896-1983` の recovery と `loop.py:381-399` の再評価拒否 | 部分。台帳非設置と完走後発行は着地。**実走中断の terminal-invalid recovery は `build_done` 前の窓でしか発火しない** (§6.2) |

## 4. D1297 の変更対象の着地状況

| 対象 | 着地状況 |
|---|---|
| `orchestrator/campaign/ident.py` | `36-51` に配置名と新 study ID 2 本の exact identity、`76-80,493,524` に balanced5 専用 recovery の呼出し |
| `orchestrator/campaign/wal.py` | `97-116,144-150` に同じ 2 条件の独立再要求。terminal invalid recovery の入口は `2015`、実体は `1896-1983` (射程は §6.2) |
| `orchestrator/campaign/loop.py` | `253-282` の opt-in 契約、`424,474-590` の coordinator |
| `orchestrator/campaign/pipeline.py` | `463-465,532-563,596-640,1904-2210` |
| driver profile | `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json` (frozen、`POLICY_SHA256` 束縛あり) |
| driver スケジュール | `paper_story_a1_paired.py:1527-1600` (`_balanced_schedule_plan` / 受領証検査) |
| collector | `paper_story_a1_paired.py:4227,5103,5375` (受領証の snapshot と突き合わせ) |
| 投入 selector | `paper_story_a1_paired.py:745-755,6112` (`--study-id` から policy identity を解く) |
| job script | `tools/pegasus/paper_story_a1_paired.sh:26-60` (v3 pilot / sized の分岐と非認証 source 集合の差し替え) |

## 5. では何が残っているか

次の一手 (1) の**実装**は閉じている。残るのは計測と凍結だが、**(1) と (2) の間に、
手順が割り当てていなかった段が 1 つある** (§6.1 で判明。敵対検証の成果である)。

- **(1.5、未記載だった段) pilot の事前登録を起草して凍結する。** `v3-pilot.json` の
  `preregistration` は `{path: null, sha256: null}` のままで、
  `paper_story_a1_paired.py:1472-1483` が submit も measure も必ず拒否する。
  **これを終えるまで (2) は 1 歩も進まない。**
- (2) その機構で pilot を 60 対/workload 測る — 機構と選択経路は通っている
  (`--study-id paper-story-a1-20260901-balanced5-pilot-v1`)。durable base
  `dev-wave-jobs/dev-wave-paper-story-a1-balanced5-pilot-20260901/measurement` は未作成で、
  `output/insights/2026-09-01_paper-story-a1-balanced5-pilot` も存在しない。**pilot は未走である。**
- (3) pilot から対 SD とブロック実効 sigma を出し、独立 seed の simulation で反復数を認証する。
- (4) 別 study の policy と事前登録を凍結する — `paper_story_a1_paired.v3-sized.json` は
  未作成で、`_policy_identity` は sized の `POLICY_SHA256` を `None` のまま持つ
  (`paper_story_a1_paired.py:753`)。§3 の項目 5 が要求する estimand の限定文言は、ここで書く。
- (5) 本走を投入する。

## 6. 敵対検証と段 4 の裁定

段 3 相当の独立レンズ 1 本 (read-only codex、`reasoning=xhigh`) に、親の判定そのものを検査させた。
全文は `verbatim/s3-consult.md`。**親の「実装面の純増はゼロ」は支持されなかった。**
親は所見を次のように裁定する。

### 6.1 real — pilot の事前登録が未凍結で、pilot study を起動できない (本 wave の scope 外)

`paper_story_a1_paired.v3-pilot.json` の `preregistration` は `{path: null, sha256: null}` である。
`paper_story_a1_paired.py:1472-1483` の `_require_policy_ready_for_execution` は v3 policy で
この束縛が無ければ `PaperStoryError("...not frozen by the parent")` を投げ、submit も measure も
必ず拒否する。**これは事故ではなく意図された未完成である** —
`orchestrator/tests/test_paper_story_a1_paired.py:1386-1390` が「pilot は親が凍結するまで拒否される」
ことを正例として固定している。

親の裁定: **real。ただし本 wave では実装しない。** 理由は 3 つある。

1. 事前登録の本文は研究上の約束であって機械的な配線ではない。D1296 は pilot の反復数・係数・
   再標本化手順を、D1295 項目 5 は「5-rep 均衡スケジュール下での差」という限定文言を、
   事前登録の本文に書くことを要求する。これを AI が独断で起草して凍結するべきではない。
2. 凍結成果物を新規発行し `POLICY_SHA256` を差し替える作業である。`DW-O09` / `DW-O10` の
   pin 閉包の棚卸しは**段 1 brief より前**が読了期限であり、本 wave は既にその期限を過ぎている。
   取り込むなら段 1 からやり直しになる。
3. 依頼が本 wave の scope を「本題の実装だけ」と明示している。

**T-1777 の手順 (1)〜(5) はこの作業を割り当てていない。** (4) は pilot と sizing の後に作る
「別 study」の policy と事前登録である。したがってこれは **(1) と (2) の間の未記載の段**であり、
次の一手の本文へ明示的に足す (§5 と worklog fragment で反映した)。

### 6.2 real — 中断の terminal-invalid recovery は build_done 前の窓でしか発火しない (本 wave の scope 外)

`wal.py:1896-1913` は、active attempt の開始後に `build_done` / `verify_done` / `bench_done` の
いずれかがあると、`InterruptedAttemptRecoveryError` を投げて `wal.py:1962-1983` の
terminal-invalid abort 生成へ到達しない。正例テスト
(`test_a1_non_certifying_marker.py:347-367`) の fixture も `build_start` しか記録しないため、
bench 中断・片側 commit の状態は被覆されていない。

親の裁定: **real。ただし correctness の穴ではなく、本 wave では実装しない。**

- **不正な結果が admit される経路にはならない。** 例外は fail-closed であり、さらに
  `loop.py:381-392` が「中断された WAL repair 後の再評価」を、`loop.py:392-399` が
  「recovered incomplete attempt」を、balanced schedule に限って独立に拒否する。
  規律 2 は破れていない。失われるのは「invalid であった」という WAL 上の耐久記録の形だけである。
- 一方で D1295 項目 7 の文言「途中中断と片側 commit は invalid に閉じる」に対しては、
  実装が狭い。**設計意図との差として real と数える。**
- 直すには recovery 層の受理集合を変えることになり、専用の変異事前登録を要する。
  pilot の起動には不要 (中断しない限り発火しない) なので、独立の項目としてユーザーへ返す。

### 6.3 不明 → 親が裁定する — D1295 項目 4 の contrast は D1262 が更新した

子は「D1295 は `static10 − adaptive` を要求するが v3 は `variant − baseline` である。
決定間の優先関係なしには確定できない」として不明とした。**親は D1262 を正本と裁定する。**

- D1262 (2026-08-29) は A-1 の凍結 contrast を論文採用値の estimand へ揃え直す決定であり、
  D1295 (同日) より後段の estimand 裁定である。T-2074 の wave が実装したのはこの D1262 である。
- D1295 項目 4 が守ろうとした不変条件は「contrast を**物理順によらず**決める」ことであり、
  それは `paper_story_a1_paired.py:1178-1190` の役割束縛と `3093` の独立再計算で保たれている。
- **両決定は食い違っていない。** 対の中身が後発の決定で更新され、順序独立性はそのまま残った。
  この読みを記録しておかないと、次の wave が「コード欠陥」として再提起する。

### 6.4 親 brief の誤り (子の指摘を採用する)

段 1 brief は `wal.py:1834,2004,2015` を挙げて「中断を terminal invalid へ閉じる経路まで
入っている」と書いたが、これらは marker 検査・誤用拒否・wrapper であって recovery の実体ではない。
実体は `wal.py:1896-1983` であり、§6.2 のとおり射程が狭い。**brief のこの記述は誤りである。**
brief は pilot profile を「着地済み」と数えたが、実行到達性を検査していなかった (§6.1)。
`verbatim/s1-brief.md` は訂正せずそのまま残し、本節を正とする。

### 6.5 refuted — 生存しなかった懸念

子が独立に照合して refuted としたもの (親の判定と一致する)。

- 両 arm の build/verify 前置きは宣言でなく実行経路に入っている (`loop.py:512-525,563-589`)。
- 単一 lock と 5-rep 実行は実際に発火し、block loop 内に WAL / 受領証の書込みが無い
  (`pipeline.py:1953-2088`)。
- 各 10 対組の AB/BA 配置は実装済み (`pipeline.py:596-630,1973-1980`)。
- collector は片側 commit や不完全な arm を valid として受理しない
  (`paper_story_a1_paired.py:3549-3562,3763-3803`)。
- D1297 の変更対象は、file も分岐も丸ごと欠落してはいない。
- `paper_story_a1_paired.v3-sized.json` の不存在は (1) の欠落ではなく (4) の未了である。

### 6.6 段 4 の結論

**coordinator の実装 (依頼の本題) は着地済みであり、本 wave の実装面の純増はゼロである。**
`4→7→8→9` を採る。§6.1 と §6.2 は real だが本 wave の scope 外であり、
実装せず裁定パッケージとしてユーザーへ返す (§8)。

## 7. ユーザーへ返す裁定パッケージ

**本節は、本 wave の land 競合中に着地した 2026-09-01 のユーザー裁定 3 件
(D1383 / D1388 / D1391) を読んだうえで書き直したものである。** 段 4 の裁定はこれらより前に
行われたので、`DW-S04` の「段 4 直前に裁定 inbox を再走査し、wave 開始後の更新を取り込む」に
従って主題で照合し、推奨を改めた。所見そのもの (§6.1、§6.2 が real であること) は変わらない。

### 7.1 pilot の事前登録 — 工程を分けて進める (§6.1)

当初 親は「事前登録は研究上の約束なので丸ごとユーザーへ返す」と書いた。**この推奨を改める。**

D1383 (B-4 事前登録の床値欄) と D1391 (承認 record) は、同じ形の問題に対して同じ工程分割を
確定している。**AI は準備・手続き案・測定計画を人間承認の直前まで用意し、発効 (凍結・発行・
pointer の有効化) だけを人間の手番として残す。** D1383 は「AI が既成事実として値を埋めることは
しない」とも明記する。

したがって A-1 pilot の事前登録も、丸ごと止めるのではなく次のように割るのが既裁定と整合する。

- **AI が用意してよい部分:** D1296 が定める本文 (60 対/workload、対 SD `s_pair` とブロック実効
  sigma `effective_sigma_95` の両欄、判定式 `df = n−1` / `k` / `h` / `B`、3 条件と成功率 80%、
  再標本化と独立 seed の確認手順)、D1295 項目 5 の限定文言 (「5-rep 均衡スケジュール下での差」を
  残留効果の無い定常状態の直接効果と同一視しない)、および `v3-pilot.json` の
  `preregistration` 欄へ path と sha256 を差し込む手続きの案。
- **人間の手番として残す部分:** その事前登録を**発効させること** — 凍結の確定と、
  `POLICY_SHA256` を含む pin 閉包の更新を「これで走らせる」と決める行為。

**親の推奨: これを次に置く。** pilot が動かない限り (2)〜(5) が 1 歩も進まない。
凍結成果物の新規発行を伴うので、`DW-O08`/`DW-O09`/`DW-O10` を**段 1 brief より前に**読む
別 wave として起こす必要がある (本 wave はその読了期限を過ぎている)。

**紛らわしい別 study との取り違えに注意する。** 同じ 2026-09-01 に
`output/insights/2026-09-01_t1875-pair-pilot-prereg-ruling/` が着地し、
「**対計画用 pilot の事前登録は発行せず裁定へ返す**」と結論している。**これは本節の pilot では
ない。** T-1875 の対象は D1268 / D1066 が定める **8c の対計画用 pilot** で、arm の outcome は
`G=2` の最終世代の生成 variant である。本節の対象は A-1 の balanced5 pilot
(`paper-story-a1-20260901-balanced5-pilot-v1`) で、arm は fixed backoff と no-backoff の
2 本に固定されている。T-1875 が A-1 の `v3-pilot` policy に言及するのは、`delta_min` の
独立な根拠を探す過程で「既存資料はどれも相対値だった」例の 1 つとして引いたためである。

とはいえ T-1875 は本節にとって有用な先例である。**事前登録の本文を独立に根拠づけられない
まま発行してはならない**という判断を、同じ日に別 study で実行している。7.1 の工程分割
(AI が用意し、発効はユーザー) はこの先例と同じ向きにある。

### 7.2 中断 recovery の射程 — D1388 の下で、まず「やるべきか」を問う (§6.2)

D1388 は enforcement source closure の束縛について、**「live resume の互換のために緩めない。
実害が再走に要する時間だけなら、受理集合を広げる代償に見合わない」**と裁定した。
§6.2 の所見はこの判断基準と同じ形の問題である。

- 現行の挙動 (例外で止まる) の実害は、中断した pilot を**測り直す時間だけ**である。
- 提案する変更は recovery 層の受理集合を変える。**方向は「緩める」ではない**
  (例外も terminal-invalid abort も、どちらも campaign を進めない) が、
  受理集合に触れる以上、D1388 と同じ天秤にかかる。

**親の推奨を改める: まず「D1295 項目 7 の文言に合わせて直す価値があるか」をユーザーが決める。**
実装を先に決め打ちしない。直すと決めた場合だけ、受理集合の変更として変異事前登録を伴う
独立 wave にする。いずれにせよ pilot の起動を妨げないので、7.1 より後でよい。
本 wave は worklog の次の一手へ新規項として起票するに留める
(採番は land の fold が行うので、この insight には番号を書かない)。

## 7. 一次資料

- `output/insights/2026-08-29_t1777-interleaved-pairing/README.md` — 配置の確定と境界の棚卸し
- `docs/decisions.md` の D1295 / D1296 / D1297
- `docs/archive/worklog-phase3-0829-1091.md:259-266` — T-1777 の次の一手 (1)〜(5) の逐語
- `verbatim/s3-consult.md` — 本 wave の敵対検証全文
