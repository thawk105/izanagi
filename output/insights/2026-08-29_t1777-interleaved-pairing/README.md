# [T-1777] A-1 の対の作り方 — 交互配置の設計判定 (実装は行わない)

- `authority: insight` — 可変状態の正本ではない。判定の正本は同 wave の decisions fragment。
- `default_effect: no-state-change`
- wave = `worktree-dev-wave-t1777-interleaved-pairing`、基準 commit `d03855e92`
  (段 9 の land 競合後に local main `17bfcda68` を取り込み済み)
- 本 wave は**実装面の差分を持たない**。段 4 で「配置は決めるが、本 wave では実装しない」と
  裁定した (根拠は §4)。配置の択一はユーザー指示により本 wave で確定させた (§4.3)。

---

## 1. 依頼と、依頼が置いた前提

依頼は「A-1 の対の作り方を交互配置へ改める。実装は `orchestrator/campaign/loop.py` か
`pipeline.py` を要求し、どちらも批准の境界に触れるので、着手前に触れる境界を洗い出して
記録すること」であった。凍結物の bytes を変えないこと、配置変更の前後を同じ campaign へ
混ぜないこと、本 wave では測定投入を行わないことが条件として付いた。

T-1777 の原文 (`docs/archive/worklog-phase3-0826-971.md:827-831`) は着手条件として
「批准の執行設計が着地した後に着手する」を置いていた。

## 2. 触れる境界の棚卸し (依頼が求めた記録)

### 2.1 着手条件は解消済み

D1139 (2026-08-27、ユーザー裁定) が enforcement source closure の批准突き合わせによる拒否を
廃止した。live の閉包は exact 24 path であり、批准集合との照合呼出しは現行経路に無い
(`orchestrator/campaign/contract_loader_binding.py:348-383`、
`orchestrator/campaign/artifact_admission.py:66-69`)。

**ただし撤去されたのは批准照合だけである。** 記録した commit blob と disk bytes の
自己整合検査は残り、不一致は `IdentityMismatch (contract-loader-drift)` で拒否される。
未 commit の編集がある作業木では campaign を初期化できない。これは F357 の偽赤の正体でもある。

### 2.2 閉包 member

`orchestrator/campaign/campaign_lock.py:49-74` の `CONTRACT_LOADER_RELATIVE_PATHS` は exact 24 path。
`loop.py` (行 53) と `pipeline.py` (行 54) はどちらもその member である。
`ident.py` (行 56) と `wal.py` (行 55) も member である。

閉包 member を編集すると次が機械的に起きる。

- commit 前の焦点走で `contract-loader-drift` の偽赤 (F357)。
- 変異 matrix に、変異の意味と無関係な共通核 (F358。2026-08-20 に `pipeline.py` / `loop.py` で実測)。
  判定は共通核 (`failed_nodes` の交差) を引いた delta で行う。ERROR 経路は `failed_nodes` 抽出から
  漏れるので、delta 不一致の原因は実 stdout で切り分ける。

### 2.3 bytes の pin

`loop.py` / `pipeline.py` の bytes を固定値として pin する台帳・test・trust root は **0 件**である。
ただしこれを「bytes が pin されない」と読んではならない。両 path は A-1 の
`NON_CERTIFYING_SOURCE_RELATIVE_PATHS` (`paper_story_a1_paired.py:125-131`) に入り、
**投入ごとに** git blob OID と working SHA-256 が submission intent へ記録され、後段で厳密に
再照合される (`paper_story_a1_paired.py:1715-1754,3682-3705`)。
凍結された固定 digest 定数が無いだけである。

凍結 policy `paper_story_a1_paired.v2.json` の bytes を pin する閉包は次のとおり
(path 検索 + 識別子検索の両方で引いた)。

- `orchestrator/campaign/paper_story_a1_paired.py:76,114,136` (`POLICY_PATH` / `POLICY_RELATIVE_PATH` / `POLICY_SHA256`)
- `orchestrator/tests/test_paper_story_a1_job_contract.py:49,241,1087`
- `orchestrator/tests/test_paper_story_a1_headline.py:1240`
- `orchestrator/tests/test_paper_story_a1_paired.py:818`
- `docs/paper-story/2026-08-26.md`、`docs/paper-story/claim-evidence/2026-08-26.md`

本 wave はこれらを 1 byte も変えていない。

### 2.4 依頼の前提「実装は loop.py か pipeline.py を要求する」は不正確である

**どの配置案を採っても、実際に必ず要求されるのは `ident.py` と `wal.py` である。**
A-1 の非認証 lane の入口は、study ID と配置名を literal で二重に固定している。

- `orchestrator/campaign/ident.py:36-54` — `_A1_NON_CERTIFYING_STUDY_ID` と
  `pairing_design == "arm-grouped-positional-v1"` の exact 一致を要求する。
- `orchestrator/campaign/wal.py:100-116` — 同じ 2 条件を独立に再び要求する。

したがって新しい study ID または新しい配置名を使う実行は、この 2 か所を直さない限り
build 前に拒否される。両方とも閉包 member である。
**`loop.py` / `pipeline.py` も、採用した配置 (§4.3) では必要である。** 当初これを
「rep 単位の完全交互を採る場合だけ」と書いたが、段 4 の相談で反証されたので訂正する。
両 arm の build/verify を bench より前に済ませる形は、現行の逐次 `evaluate()`
(`loop.py:383-474`) と arm 単位の `_run_bench()` (`pipeline.py:512-621`) の分割を要求する。

なお「1 workload を K 本の campaign に割れば driver だけで済む」という当初の見立ても
**誤りである。** `orchestrator/campaign/trial_registry.py:3889-3896` は A-1 の
`campaign_ids` を workload と同数の **exact unique triple** に固定しており、K 本化は
非閉包の registry と collector の変更まで要求する。

加えて、投入経路と job script も旧 study ID に固定されている
(`paper_story_a1_paired.py:1080-1112,4530-4538`、`tools/pegasus/paper_story_a1_paired.sh:13-17,42`)。

### 2.5 混在防止は既存構造で成立している

配置は `campaign_config()` が `search_config["pairing_design"]` へ入れ
(`paper_story_a1_paired.py:801-822`)、`search_config` 全体が campaign identity の key である
(`campaign_lock.py:19-21`、`ident.py:169-208`)。配置名を変えれば campaign は別物になる。
**新しい混在防止 gate を足す理由は無い。**

## 3. 実測 — 現行の対応づけは分散を減らしていない

一次資料 `output/insights/2026-08-24_paper-story-a1-paired/result.json` の raw TPS から、
位置対応差の標本 SD と、独立標本を仮定した近似 SD、および位置を揃えた arm 間の相関を
親が独立に再計算した。

**計算の定義 (再現に必要な全て)。** 各 workload について、`result.json` 中の 2 本の `tps` 配列
(各 n=5、arm ごとに 1 本) を位置順に `a`, `b` とする。

- 対応差 `d_i = b_i − a_i`、その標本 SD は `sqrt(sum((d_i − mean(d))^2) / (n − 1))`
- 独立近似 SD は `sqrt(sa^2 + sb^2)` (`sa`, `sb` は各 arm の標本 SD、分母 `n − 1`)
- 相関は `cov(a, b) / (sa * sb)`、`cov` の分母も `n − 1`

いずれも標準の標本統計であり、arm のどちらを `a` に取るかで相関と SD 比は変わらない。
再計算に使った使い捨てスクリプトは repo へ入れていない (D95 決定 2 の実装面に当たるため)。

| workload | 対応差 SD | 独立近似 SD | 位置対応の arm 間相関 | 対応差 / 独立近似 |
|---|---:|---:|---:|---:|
| write-heavy | 43,649.1 | 34,940.4 | −0.591 | 1.249 |
| balanced | 66,139.4 | 53,029.6 | −0.563 | 1.247 |
| read-heavy | 25,453.5 | 19,185.8 | −0.765 | 1.327 |

**この 15 対では、3 workload とも対応づけた差の SD が独立近似より 25〜33% 大きい。**
標本上は `Var(B−A) = Var(A) + Var(B) − 2Cov(A,B)` の共分散項が負である。
凍結事前登録の反復数 (balanced 205) は、この標本 SD を基に決まっている。

**再計算値が凍結事前登録の入力そのものであることの確認。** 上の対応差 SD に自由度 4 の
片側 95% 上側係数 `sqrt(4 / chi2_0.05,4) = 2.372356` を掛けると 103,551.1 / 156,906.2 /
60,384.8 となり、凍結 policy の `planned_sigma_tps` (103551.0849 / 156906.1857 /
60384.6868) と一致する。本節の再計算は v2 が実際に使った値を独立な経路で再現している。

**言えることの上限 — 当初の記述を訂正する。** 各系列は n=5 である。無相関検定
(`t = r*sqrt(n-2)/sqrt(1-r^2)`、df=3) と Fisher-z の概算 95% 区間は次のとおりで、
**3 workload とも 0 を含み有意でない。**

| workload | r | 概算 95% 区間 | 両側 p |
|---|---:|---:|---:|
| write-heavy | −0.591 | [−0.968, 0.609] | 0.294 |
| balanced | −0.563 | [−0.966, 0.634] | 0.323 |
| read-heavy | −0.765 | [−0.983, 0.361] | 0.132 |

したがって言えるのは **「この 15 対では分散削減を観測しておらず、有益な正の共分散を示す
証拠も無い」**までである。「母集団で真に分散を増やす」「原因は時間隔である」は言えない。
当初書いた「真の相関 0 なら 3 符号一致は 8 分の 1」は、3 workload の符号推定が独立という
追加仮定を要する。同一 job が workload を順に処理する現行経路
(`paper_story_a1_paired.py:3562-3565`) ではその独立性が示されていないので**取り下げる**。
逆順走が無いため、時間ドリフト・偶然・arm 固有挙動も分離できない。

**見返りの大きさ (仮定付きの見積り)。** SD が両 arm で等しいとすると
対応差の分散は `2s^2(1−rho)` である。rho が −0.6 から +0.5 へ動けば対応差 SD は約 0.56 倍になり、
反復数は SD の 2 乗に比例するので約 3.2 分の 1 (balanced 205 → 約 64) になる。
これは仮定に基づく見積りであって実測ではない。

## 4. 段 4 の裁定 — 本 wave では実装しない

### 4.1 却下したもの: rep 単位の固定 AB 完全交互

親が段 1 brief で暫定裁定した「単一 campaign 内の rep 単位交互 bench」を **撤回する。**

1. **新しい完全交絡へ置き換わる。** `adaptive → static10` の固定順で完全交互にすると、
   static10 が常に対の 2 番目になる。差には arm 効果に加えて、直前 arm の残留効果・
   周波数・熱・対内順序効果が常に同じ向きで乗る。時間隔の交絡を、順序の交絡へ移すだけである。
2. **消そうとしている交絡が効いている証拠が無い** (§3)。
   `DW-G01` は「新しい探索軸・大型機構の本格実装前に最安の生死確認を行う。
   確認前の専用機構の構築は brief で却下する」と定める。本件はこれに該当する。
3. **実装面が大きい。** 敵対検査は、この案に対して閉包 member 4 file (`loop.py` /
   `pipeline.py` / `wal.py` / `ident.py`)、新しい耐久台帳と専用 recovery、
   trace/perf binary の新しい分離検査、投入経路と job script の分岐を要求すると指摘した。
   配置が未確定のままこれを作るのは、作るものを間違える risk が高い。

### 4.2 却下したもの: reps=1 の campaign を反復数だけ並べる案

campaign ごとに genome ごとの `evaluate()` が走り、legacy verify が 1 回ずつ入る
(`loop.py:383-474`、`pipeline.py:128-135,1338-1347`)。balanced を 205 本の fresh identity に
割ると verify は 2 回から 410 回になる。verifier capability は PID・variant・operation へ
束縛され一度消費すると再利用できないので (`verifier/core.py:168-258`、
`commit_receipt.py:309-332`)、証明書の使い回しでは避けられない。

**ただし「費用が 205 倍になる」は誤りである。** 敵対検査の指摘により訂正する。
verify 成功時の nominal extime は 1 秒 (`pipeline.py:128-135`) なので、
balanced の単純合計は約 1,379.6 秒に対し約 1,787.6 秒、**約 30% 増**である。
build も 205 倍にはならず、cache hit が大半を占める (`buildcache.py:2438-2494`)。
campaign 初期化・cache 検証・preflight の費用は未実測である。

### 4.3 採用する配置 (ユーザー指示により本 wave で決定した)

ユーザーは「裁定は codex と相談して決めて」と指示した。段 4 の相談を追加で 1 本回し、
親の推奨を独立に評価させたうえで次を**採用**する。相談の全文は
`verbatim/s4-ruling-consult.md`。

**単一 campaign の 5-rep ブロック交互 + 局所 AB/BA 均衡、単一 bench ロック。**

1. 1 workload = 1 campaign のまま、**両 arm の build と verify を bench より前に完了**する。
2. その後、`bench_lock()` を**全ブロックにわたり 1 回だけ保持**し、
   5 rep ずつの arm ブロックを交替させる。
3. 10 対を 1 組とし、組の中で `A^5 B^5` と `B^5 A^5` を 1 つずつ置く。
   組内の先後だけを凍結 seed で決める。
4. contrast は物理順によらず常に `static10 − adaptive` とする。
5. 推定対象は **「5-rep 均衡スケジュール下での差」**であり、
   残留効果の無い定常状態の直接効果と同一視しない。この限定を事前登録に書く。
6. `bench_max_rounds = 1`。CV 再測は使わない。静定と競合検査は残す。
7. 対ごとの同期追記台帳 (journal) は**置かない**。全ブロック完了後に arm ごとの
   `bench_done` とスケジュール受領証を出し、途中中断と片側 commit は invalid に閉じる。
   台帳 I/O 自体が観測者効果になるのを避けるためである。

balanced での同番号間の間隔は約 16.8 秒 (`5 × 3.36`) となり、現行の約 41 分の 1 になる。
write-heavy は約 242 秒から、read-heavy は約 94 秒から、いずれも約 17 秒になる。

配置案の比較 (balanced、実測 3.36 秒/rep を使用。3.36 は事前登録 README §2 の実測値)。

| 配置 | 同番号間の間隔 | 主な新しい交絡 | 判定 |
|---|---:|---|---|
| 現行 (arm 一括) | 約 689 秒以上 | 長時間ドリフトと arm 順が完全交絡 | 却下 |
| 固定 AB 完全交互 | 約 3.36 秒 | static10 が常に 2 番目で完全交絡 | 却下 |
| **単一 campaign・5-rep ブロック + AB/BA 均衡** | **約 16.8 秒** | **ブロック内位置との交互作用** | **採用** |
| rep 単位 ABBA | 約 3.36 秒 | arm 間遷移が 5 倍、周期 4 と環境変動の交絡 | 却下 |
| 均衡無作為 | 約 3.36 秒 | seed 固定は再現性のみ。実現した時間偏りは残る | 却下 |
| K 本 campaign へ分割 | 約 16.8 秒 | campaign 境界・静定・検証を 62 回持ち込む | 却下 |

**K 本 campaign 案を却下した理由 (親の当初案の撤回)。** 親は「driver だけで済むので閉包を
触らない」と考えたが誤りだった。`trial_registry.py:3889-3896` が A-1 の `campaign_ids` を
workload と同数の exact unique triple に固定しており、K 本化は registry と collector の
変更を要求する。加えて旧 n のままなら 62 ブロック = 124 verify・248 build API 呼出しになり、
campaign 境界・静定・ロック解放が 62 回対の間に挟まる。採用案なら verify は現行同様
workload あたり 2 回 (合計 6 回)、build API は 12 回のままである。

**実装が及ぶ範囲 (採用案)。** 閉包 member は 4 つとも要る —
`ident.py:36-54` と `wal.py:102-125` に新しい `(study_id, pairing_design)` を追加、
`loop.py:327-383` に両 arm を先に準備する coordinator、
`pipeline.py:512-621,1027-1086,1502-1561` に build/verify と bench の分割とブロック実行器。
非閉包側は driver の profile・スケジュール・collector・投入 selector と job script である。

**現行の「約 615 秒」は nominal 値である。** `205 × 3` は ccbench へ渡す指定時間の総和にすぎない。
同じ事前登録が実測 3.36 秒/rep を記録しているので `205 × 3.36 = 688.8 秒` が実測換算であり、
実際の対間隔は arm B の build と verify の分だけさらに長い。

### 4.3.1 pilot を挟むか — 挟む。ただし使い捨ての pilot 実装は作らない

pilot と本実装の実装面はほぼ完全に重なる (閉包 4 file、driver 実行核、投入経路のすべてが共通で、
異なるのは study ID・policy と事前登録の hash・反復数・k・sigma・出力先といった profile 値だけ)。
したがって**本番用の機構を先に 1 度だけ作り、その同じ機構で pilot を走らせる。**
pilot の価値はコードの試作ではなく、新配置での共分散・ブロック相関・残留効果を実測して
反復数を決めることにある。これは §4.4 が要求するので省けない。

簡易版 (K 本 campaign) の pilot を sizing に使ってはならない。build/verify とロック解放が
対の間に入るため、本番 coordinator とは異なる共分散を測ってしまう。

### 4.3.2 反復数の決め方

各 workload について、同じ機構で **60 対**を 1 度測る (5 対/ブロック × 12 ブロック、
A 先行 6 ブロック・B 先行 6 ブロック、10 対ごとに一方ずつ、組内順は凍結 seed)。
TPS・物理順・ブロック番号・ブロック内位置・開始終了時刻を記録する。

- 対 SD: `s_pair = sqrt(sum((d_i − mean(d))^2) / 59)`、
  `planned_sigma_tps = s_pair × sqrt(59 / chi2_0.05,59)` (係数は約 1.181)。
  v2 が同じ方式であることは §3 の照合で確認済みである (n=5 の係数 2.372356)。
- ブロック内相関も計画へ入れる。12 個の 5 対ブロック平均の標本 SD を `s_block` として
  `effective_sigma_95 = sqrt(5) × s_block × sqrt(11 / chi2_0.05,11)` (後半は約 1.551)。
  sizing には `max(planned_sigma_tps, effective_sigma_95)` を使い、
  policy では対 SD 用と平均分散用を別 field にして意味を混ぜない。
- n の探索は 10 の倍数に限る (5-rep ブロックの AB/BA を exact に均衡させるため)。
  判定式は現行どおり `df = n−1`、`k = t_0.975,n−1`、`h = k*s/sqrt(n)`、
  `B = 0.03 × 当該走の adaptive 平均`。
  条件は既存 sizing 器と同じ 3 つ (`tools/size_paper_story_a1_headline.py:61-63`) —
  真の差 0 で floor 内、真の差 ±6% (floor の 2 倍) で floor 超えかつ符号一致 — を
  それぞれ成功率 80% 以上とする。pilot のブロックを順序別に再標本化して探索し、
  独立 seed で再計算して確認する。pilot の観測値は最終推定へ混ぜない。

### 4.4 統計式の可搬性

各 block について `d_i = static10_i − adaptive_i` を 1 つ作る限り、算術平均と
分母 `n−1` の標本分散は配置に依存しない。現実装もその算術しか行わない
(`paper_story_a1_paired.py:1769-1827`)。`df = n−1` と `k` も n を固定する限り同じである。

**しかし `planned_sigma_tps` と到達確率は流用できない。** 現行の計画 sigma は
arm 一括配置の探索走の位置差 SD から導かれており (事前登録 README §2)、
配置を変えれば共分散項が変わる。新配置の反復数は、新配置の pilot から取り直す必要がある。

## 5. 敵対検査で生存した主張

- enforcement source closure が exact 24 path であること、`loop.py` / `pipeline.py` が
  その member であることは、両レンズの独立照合で生存した。
- 凍結 v2 policy と事前登録の bytes、`POLICY_SHA256`、`PREREGISTRATION_SHA256` の 4 値が
  現物と一致することは静的照合で生存した。
- 配置名を変えれば campaign identity が分かれることは生存した。新しい gate は不要である。
- 「D1139 により着手条件は解消した」は生存した (ただし §2.1 の限定付き)。
- verify 回数 410 という数え方は生存した (205 個の fresh identity を作る条件付き)。
- 現行経路で trace build が性能計測へ混入する経路は見つからなかった。cache key が `trace` を
  含み、perf build は trace symbol 不在を検査し、A-1 collector も現在の binary digest を
  再検査する (`buildcache.py:618-636,2992-3014`、`paper_story_a1_paired.py:2016-2043,2112-2147`)。

## 6. 一次資料

- `verbatim/s1-brief.md` — 段 1 の親 brief 全文 (§2.1 / §2.3 の言い方は §2 の本文で訂正済み)
- `verbatim/s2-plan.md` — 段 2 の起草プラン全文
- `verbatim/s3-lensA.md` — 段 3 レンズ A (正しさ防壁・実行記録・同一性) 全文
- `verbatim/s3-lensB.md` — 段 3 レンズ B (測定設計・交絡・費用・scope) 全文
- `verbatim/s4-ruling-consult.md` — 段 4 の裁定相談全文 (配置の択一・pilot・反復数)
- `pairing_correlation.txt` — §3 の再計算の生出力 (親が実走。定義は §3 に逐語で書いた)
