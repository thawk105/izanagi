# [T-1777] A-1 の対の作り方 — 交互配置の設計判定 (実装は行わない)

- `authority: insight` — 可変状態の正本ではない。判定の正本は同 wave の decisions fragment。
- `default_effect: no-state-change`
- wave = `worktree-dev-wave-t1777-interleaved-pairing`、基準 commit `d03855e92`
- 本 wave は**実装面の差分を持たない**。段 4 で「実装しない」と裁定した (根拠は §4)。

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
`loop.py` / `pipeline.py` が必要になるのは **rep 単位の完全交互を採る場合だけ**であり、
driver 層のブロック配置なら不要である。

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

**3 workload すべてで、対応づけた差の SD が独立近似より 25〜33% 大きい。**
`Var(B−A) = Var(A) + Var(B) − 2Cov(A,B)` の共分散項が負だからである。
すなわち現行の位置対応は分散を減らすどころか増やしており、
凍結事前登録の反復数 (balanced 205) はこの膨らんだ SD を基に決まっている。

**限界を明記する。** 各系列は n=5 である。n=5 の相関推定の標準誤差は非常に大きく、
3 workload とも負という一致も、相関が真に 0 なら 8 分の 1 の確率で起こる。
**この表は「対応づけが分散を減らしている証拠は無い」ことを示すが、
「時間隔の交絡が効いている」ことを同定しない。** 逆順走が無いため、
時間ドリフト・偶然・arm 固有挙動を分離できない。

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

### 4.3 推奨する配置 (次 wave 以降の実装対象候補)

**ブロック単位の交互配置に、対内順序の均衡を組み合わせる。**
1 workload を K 本の campaign に割り、各 campaign を `reps = N/K` で走らせ、
campaign ごとに先頭 arm を反転する。balanced (N=205) で 5-rep block なら
同番号間の間隔は約 16.8 秒となり、現行の約 41 分の 1 になる。

配置案の比較 (balanced、実測 3.36 秒/rep を使用。3.36 は事前登録 README §2 の実測値)。

| 配置 | 同番号間の間隔 | `measure_point` 呼出し | 順序・残留効果 |
|---|---:|---:|---|
| 現行 (arm 一括) | 約 689 秒以上 | 2 | 長時間ドリフトと arm 順が完全交絡 |
| 固定 AB 完全交互 | 約 3.36 秒 | 410 | static10 が常に 2 番目で完全交絡 |
| 5-rep block + AB/BA 均衡 | 約 16.8 秒 | 82 | 間隔を約 41 分の 1 にし、順序を均衡できる |
| rep 単位 ABBA | 約 3.36 秒 | 410 | 線形順序効果を相殺、同 arm 連続が残る |

**現行の「約 615 秒」は nominal 値である。** `205 × 3` は ccbench へ渡す指定時間の総和にすぎない。
同じ事前登録が実測 3.36 秒/rep を記録しているので `205 × 3.36 = 688.8 秒` が実測換算であり、
実際の対間隔は arm B の build と verify の分だけさらに長い。

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
- `pairing_correlation.txt` — §3 の再計算の生出力 (親が実走。定義は §3 に逐語で書いた)
