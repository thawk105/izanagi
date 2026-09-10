# V-8 の「実行費用 33 倍」を現行コードで測り直した — 33 倍は run の本数比であって費用比ではなく、実測は約 1.0 倍だった

- wave: `worktree-dev-wave-t2261-v8-cost` ([T-2261])
- 起点 local main: `c7ed56589`。記録前に main `7013ea81f` を ff で取り込んだ
- 実装面の差分 0 (docs と insight のみ)。変異 matrix 免除。段 2 plan 1 本、段 3 敵対相談 2 本
- **新規の測定投入をしていない。** 既存の B-10 正式走の成果物と、実行中の走行を read-only で読んだ
- **V-8 の択一は選んでいない。** D1561 が材料を持って裁定すると定めており、本書は材料である

---

## 1. 一行で

`docs/phase3-8c-wiring-design.md` §5.3 の「実行費用を 33 倍にする」は、**campaign run の本数比
(33 対 1) をそのまま実行費用の比と呼んだ数字**である。費用は run の本数ではなく、run ごとの
固定費と行ごとの費用の和で決まる。現行コードで両方を測ると、**倍率は 1.0 倍前後**だった。

倍率がちょうど 33 になるのは、**比較相手が物理行を 1 本しか実行しないとき**だけである。
そのとき `33(F+R) / (F+R) = 33` になる。物理行を 32 本または 33 本実行する相手に対しては、
`R` がいくつでも 33 倍にはならない。

---

## 2. 測った値

一次資料は次の 3 つ。いずれも既存の成果物である。

- 公式出力 root: `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output`
- 各 campaign の WAL: `<root>/campaigns/<campaign_id>/runs/wal.jsonl`
- 投入証拠 root: `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions`

### 2.1 run の前置費 — 23〜38 秒。ただし分離できていない

job の開始時刻から、その run の最初の `build_start` WAL 事象までの実時間。

| campaign | workload | job 開始 (JST) | 最初の WAL (JST) | 差 |
|---|---|---|---|---:|
| `068fd2cd` | write-heavy | 09-01 01:26:36 | 09-01 01:26:59 | 23 s |
| `15e75b3f` | balanced | 09-01 05:02:11 | 09-01 05:02:39 | 28 s |
| `ed8a676b` | read-heavy | 09-02 01:07:49 | 09-02 01:08:17 | 28 s |
| `e3de15eb` | write-heavy | 09-01 21:16:42 | 09-01 21:17:20 | 38 s |
| **`143a3f74`** | **balanced** | **09-03 20:30:05** | **09-03 20:30:38** | **33 s** |

最後の 1 行が現行コードでの観測である。job `974207.nqsv` の submit receipt が
`source_commit = c7ed565892cd4aba52d7fa47a7d1da17b117c005` を記録しており、本 wave の起点
local main と同一である。job 開始時刻は `qstat -f 974207.nqsv` の `Started Request Time`。

**この 33 秒を「run ごとの固定費」として 33 回掛けてはならない。** 区間には job script の
prologue (PBS envelope 検査、repo / Python / policy 解決、submit receipt 照合、`qstat`、
reservation 環境構築、依存の build)、Python の起動と import、そして `run_campaign()` の
前置費が混ざっている。33 run を 1 job・1 process で回すなら、前半は 1 回しか払わない。
**区間内の計時が無いので、この 33 秒を job 共通費 `J` と run 固定費 `F` へ分ける手段は無い。**

5 観測は同一母集団でもない。3 種の source commit、3 種の job-script SHA、複数の workload と
node が混ざっている。中央値 28 秒は「この混合標本の中心」、38 秒は「観測最大」にすぎず、
どちらも `F` の点推定でも上限でもない。

### 2.2 1 行の費用 — 現行コードで 908.908 秒と 374.728 秒

campaign `143a3f74` (現行コード、balanced) の `build_start` から `commit` までの実測。

| variant | 行全体 |
|---|---:|
| `84319b1127a6` | **908.908 s** |
| `602b4ce9c788` | **374.728 s** |

**同じ campaign の中で 2.4 倍違う。** 行の費用は 1 つの値ではない。1 変種の値を 32 mask 共通の
`R` として使う根拠は無い。

### 2.3 直列性検査の並列化の効果 — 同一 variant・同一 commit 数で 1.84 倍

同じ variant `84319b1127a6`、同じ balanced workload、同じ 6 パス構成 (legacy 1 + performance 5)。
**各パスの commit 数が 1〜4% しか違わない**ので、所要差は検査対象量の差ではない。

| パス | 並列化前 `15e75b3f` (08-31) | commits | 現行コード `143a3f74` (09-03) | commits |
|---|---:|---:|---:|---:|
| build | 50 s | — | 51 s | — |
| legacy | 28 s | 629,914 | 17 s | 639,048 |
| performance 1 | 321 s | 3,914,759 | 173 s | 4,083,126 |
| performance 2 | 314 s | 4,050,041 | 163 s | 4,110,736 |
| performance 3 | 314 s | 4,074,556 | 167 s | 4,150,200 |
| performance 4 | 330 s | 4,053,699 | 171 s | 4,123,584 |
| performance 5 | 316 s | 4,073,441 | 166 s | 4,096,412 |
| **行全体** | **1672.789 s** | | **908.908 s** | |

performance 1 パスの平均は 319.0 秒 → 168.0 秒。1 commit あたり 79.2 マイクロ秒 →
40.9 マイクロ秒。**build の所要は変わっていない。**

**この 1.84 倍は end-to-end の混合区間の比であって、検査器単体の値ではない。**
T-2191 が測った検査器単体の 2.2 倍とは別の量であり、2.2 を行全体へ掛けて得たものでもない。

**因果は確定していない。**
- node が違う (`bnode003` → `bnode015`)。ただしこの cluster のノード間の相対差は 1〜2% 台で
  (`docs/pegasus-node-variance-protocol.md` の第 1/第 2 世代差 1.774%、within-node CV 1.2479%、
  材料閾値 0.6%)、1.84 倍を説明する大きさではない。**ただしその protocol が測ったのは
  throughput であって検査器の実時間ではない。**
- `orchestrator/verifier/parse.py:794` は worker の起動に失敗すると**無言で直列へ落ちる**。
  WAL は worker 数を記録しないので、live 走行で並列枝が実際に発火したかを直接示す証拠は無い。
- 並列化 commit (`d719c1e35`、`da45b6b2b`、`76b824f94`) が `c7ed565…` の祖先であることと、
  job script が投入前に HEAD・clean・script SHA の三者一致を検査することは確認した。
  **「現行 commit に gate された走行」までは言えるが、「並列枝が発火した」は未証明である。**

### 2.4 行間の費用 — 2〜3 秒

`143a3f74` で `commit` から次の `build_start` まで 3 秒。`15e75b3f` と `e3de15eb` では 2〜2.3 秒。
これは 1 campaign run の中で行を繋ぐ費用であり、run を割る (a) では払わない。

---

## 3. 費用の構造 — 何が run ごとで、何が行ごとか

### 3.1 `run_campaign()` の中

**run ごとに 1 回:** 引数・protocol shape の事前検査 (`loop.py:270-375`)、verify mode の解決と
build policy の identity 束縛 (`loop.py:372-377`, `149-158`)、writer authorization と
environment contract 照合 (`loop.py:161-178`)、Pegasus の calibration artifact 読込・
live attestation・receipt 生成 (`loop.py:179-193`)、campaign identity の再計算
(`loop.py:194-196`)、reservation の env 読込と job/boot/deadline 検査 (`loop.py:198-207`)、
claim root 検査と campaign claim の作成・fsync (`loop.py:208-229`)、perf preflight
(`loop.py:387-393`)、layout 生成 (`loop.py:394`)、campaign lock (`loop.py:396-404`)、
campaign.lock 照合と WAL の tail repair・復旧走査 (`loop.py:405-455`)。

**行ごとに 1 回:** compiler 選択と source evidence の解決 (`loop.py:466-486`)、
`variant_id` と `done` lookup (`loop.py:522-529`)、trace build と perf build の 2 本
(`pipeline.py:1197-1263`)、各 correctness repetition の一時 directory・trace binary 実行・
標準出力の解析・C 行の数え直し (`pipeline.py:1365-1470`)、直列性検査と verify_done WAL
(`pipeline.py:1471-1517`)、commit receipt と commit WAL (`pipeline.py:1714-1773`)。

**run 固定費でも行費用でもないもの:** Python の起動と module import は `run_campaign()` の外に
あり、33 回の呼出しを同一 process で行えば 1 回しか払わない。

**条件付き:** `settle()` は「run あたり必ず 1 回」ではない。`do_bench=False` または verify 前に
abort すれば 0 回、bench に到達すれば初回 1 回、高 CV で再測定すれば既定 3 round で最大 3 回
(`loop.py:463`, `624-629`; `pipeline.py:765-792`; `calibrator/stability.py:58-90`;
1 回の上限は `calibrator/runner.py:271-290` の 20 秒)。perf preflight は `do_bench=True` の
ときだけで、2 候補を順に probe し各 timeout 10 秒なので静的最悪は約 30 秒
(`calibrator/perf_preflight.py:100-176`)。**B-10 の shape campaign は `do_bench=False` で
`bench_done` を 1 件も出さないため、この 2 項の実費は上の実測に含まれていない。**

### 3.2 8c topology の側

| 操作 | 成功時の回数 | 単位 |
|---|---:|---|
| fresh origin、origin capability、create-only run plan | 1 | origin / batch |
| `BatchReserved` / `BatchCommitted` / `BatchResultsPrepared` / `BatchSealed` / `OriginSealed` | 各 1 | batch / origin |
| campaign authorization・reservation 検査・claim・layout・WAL 復旧 | (a) は 33、(b) は 1 | campaign run |
| 物理 attempt と terminal WAL / provenance | (a) は 33、(b) は 32 | 物理行 |
| `result-evidence/v1` record | 33 | non-tombstone member |
| formal consumer とその receipt | 1 (33 record をまとめて検査) | sealed batch / origin |

**「1 query ordinal = 1 campaign run」にしても ledger の batch lifecycle は 33 回にならない。**
reserve / commit / seal は batch 単位で各 1 回のままである
(`docs/phase3-8c-wiring-design.md` §5.1、§4.1)。33 回になるのは campaign 側の
authorization / claim / layout と、物理 attempt と result-evidence だけである。

### 3.3 build cache は 33 行を安くしない

cache key は genome・CCBench commit・trace の有無・`src_token` (preprocess 後の内容 hash)・
compiler・build-admission receipt の内容キーで、campaign identity を含まない
(`buildcache.py:624-642`)。したがって cache は campaign run を跨いで効く。

**しかし 32 mask は source bytes が異なるので `src_token` が異なり、hit しない。**
さらに正式 S8b の materialization は一意 worktree の絶対 `source_root` を admission preimage に
含めるため、**実装自身が「正式経路では cache hit は起きない」と明記している**
(`buildcache.py:2312-2318`)。現行コードの走行でも最初の 2 行はいずれも `cached: false` で、
2 行目の build に 50 秒かかっている。

**33 回の build は (a) でも (b) でも同じだけ必要である。**

---

## 4. (b) は 33 行を物理実行しない — 32 行である

`variant_id` は genome と `src_token` だけで決まり、query ordinal・replicate ordinal・
trigger nonce を含まない (`pipeline.py:121-127`)。8c topology では source base と
`m == m_s` の validation 行が同じ wire を持つので `src_token` が一致し、
`query_ordinal = 1 + m_s` の行が `loop.py:522-529` で skip される
(**「2 行目」とは限らない。`m_s = 0` のときだけ 2 行目である**)。

§5.3 の意味上の記述は現行実装と一致する。**ただし同節が引く行番号 `loop.py:242-246` は古く、
現行位置は `522-529` である。**

さらに §3.4 の対応表は `duplicate skip` を「record を発行しない → 当該行以降を tombstoned」に
写している。**したがって (b) では origin が aborted になり、33 行の成果物を作れない。**
これは費用ではなく正しさ側の理由であり、本測定はこの判断を動かさない。**厳密には (b) は
「同じ成果物あたりの費用」の比較対象になっていない。**

---

## 5. 倍率

`J` = job / process の共通費、`F` = run ごとの固定費、`R` = 1 行の費用、
`D` = skip された行が skip までに払う費用、`g` = 行間費用。

    (a)  = J + 33 x (F + R)
    (b)  = J + F + 32R + D + 31g       (§11 の literal な (b)。duplicate skip で 32 物理行)
    (b*) = J + F + 33R + 32g           (33 行すべてを物理実行できると仮定した反実仮想)

実測から固定できるのは `J + F = 33 秒` (未分離) と `g = 3 秒` である。`J` と `F` の分け方が
決まらないので、**両端点で値を出す。**

| R (現行コードの実測) | (a)/(b) | (a)/(b*) |
|---|---|---|
| 908.908 秒 | 1.028 〜 1.064 | 0.997 〜 1.032 |
| 374.728 秒 | 1.023 〜 1.110 | 0.992 〜 1.077 |

`(a)/(b*)` が 1 を下回る端点があるのは、(a) が行間費用 `g` を払わないからである。

### 5.1 いつ大きくなるか

- **33 秒がすべて job / process の共通費なら (`F = 0`)、`R` がいくつでも `(a)/(b)` は
  `33/32 = 1.031` を超えない。** 分子も分母も同じ 33 回 (32 回) の物理行を含み、
  差が行 1 本分に収まるからである。
- **33 秒がすべて run ごとの固定費なら (`F = 33`)**、倍率は `R` について単調減少し、
  `R` が大きいほど `1.031` へ収束する。`R = 908.9` 秒で 1.064、`R = 374.7` 秒で 1.110。
  観測値から組める最小の行 (build 50 + legacy 8 + S2 1 パス 63 = 121 秒) でも **1.27** である。
- **`(a)/(b) = 33` はこの模型では `R = 0` にしても到達しない。** `R = 0` でも 8.6 である。
  **倍率が 33 になるのは、比較相手が物理行を 1 本しか実行しないときだけ**であり、
  それは §5.3 自身が「per-query の物理実行保証が破れる」として退けた形である。

**これらは B-10 の実測から組んだ scenario 値であって、(a) と (b) を実際に走らせた値ではない。**
形式 P6 の 33 行 producer は存在せず、事前登録の extime / reps も未記入である。

### 5.2 費用の種類は 4 つあり、上の倍率はそのうち 1 つである

| 種類 | 本 wave が出した値 |
|---|---|
| 計算ノードの占有時間 | 上の 1.02〜1.11 倍 (B-10 由来の scenario) |
| 待ち行列込みの実時間 | **未測定。** 33 run を 1 job で回せるかに依存する (§6) |
| 投入する job の本数 | **未確定。** §6 の衝突が解けるまで決まらない |
| 人手の投入・監視・回収 | **未測定** |

---

## 6. 測定より重い発見 — (a) は現行コードで実行形が成立していない

**33 個の campaign run を作る形は、現行の 2 つの契約と正面から衝突する。**

- `campaign_identity = str(ident.campaign_id(bound_cfg))` は `CampaignConfig` だけから決まり、
  **`genomes` を含まない** (`loop.py:194`、`ident.py:196-235`、`model.py:67-84`)。
  同じ cfg で genome だけ変えて 33 回呼んでも、campaign identity は 33 回とも同じである。
- `acquire_claim` は identity を key に `O_EXCL` で claim file を作り、**release API を
  意図的に持たず、crash 後も残す** (`campaign_claim.py:74-79`、`383-434`)。
  **したがって 2 回目の `run_campaign()` は「既に所有されている」で拒否される。**
- cfg を変えて 33 個の identity にすると、今度は `OriginBindingCapability/v1` が
  **`campaign_id` を 1 つしか持たない**ことと衝突する
  (`docs/phase3-8c-wiring-design.md` §6.2)。formal consumer は 33 record すべてが
  capability と `campaign` 一致であることを要求する (同 §4.1 条件 3)。

**claim を通すには 33 個の別 identity が要り、consumer を通すには 33 record が同じ
`campaign_id` を持つ必要がある。** 現行コードのままでは (a) を実行できない。

generic な reservation 自体は 33 run の連続実行を妨げない。binding は job ID・host・boot ID・
deadline を保持するだけで消費済み状態を持たず、同じ job 内で再検査できる
(`reservation.py:26-55`、`223-275`)。`run_campaign()` が要求する残時間は各呼出し 1 秒だけである
(`loop.py:198-207`)。**したがって「scheduler へ 33 回投入する必要がある」わけではない。**
止めているのは claim と capability の identity 設計である。

**解消案は本 wave では設計しない。** V-8 の裁定と 8c 結線の実装 wave の仕事である。

---

## 7. 本書が主張しないこと

- **V-8 の択一を選んでいない。** D1561 が材料を持って裁定すると定めている。
- **新しい測定を起こしていない。** 既存の B-10 成果物と実行中の走行を読んだだけである。
  `settle()` を login node で計時してもいない (load average の regime が計算ノードと違う)。
- **`run_campaign()` の per-run 固定費を分離していない。** 既存 WAL は最初の `build_start` より
  前を記録しない。分離には計測配線が要り、それは実装面なので本 wave の scope 外である。
- **未算入の終端費用がある。** `commit` の WAL 時刻は append の前に採られ、実際の write と
  file / directory の fsync はその後である (`wal.py:1410`、`1165`)。`return` は
  `with ExitStack()` の中なので、復帰前に campaign lock の unlock / close が走る
  (`loop.py:396`、`652`; `lock.py:84`)。job 側にも `job-result.json` 作成と scratch 削除がある。
- **形式 P6 の `R` を測っていない。** 33 行 producer が存在せず (`§5.3` 末尾)、
  事前登録の extime / reps が未記入である (`docs/phase3-8c-preregistration.md` の数値欄)。
  上の `R` は B-10 の実測と `legacy+S2` の既定パラメータから組んだ帯である。
- **並列枝の実発火を証明していない** (§2.3)。
- **`docs/phase3-8c-wiring-design.md` §11 の表を書き換えていない。** 絶対規律 7 に従い、
  同 file の末尾へ追記で訂正した。§11 の (a) 欄は「実行費用が 33 倍」のままである。
- 33 run が 1 job で回せることは**コードの読取りで判定した。実走で確かめていない。**

---

## 8. 一次資料

- `docs/decisions.md` の D1561 — 本作業を起票した裁定
- `docs/phase3-8c-wiring-design.md` §5.3 (33 倍の出所)、§11 (V-8)、§4.1、§6.2
- `output/insights/2026-09-02_b10-trace-truncation/README.md` の「所要の内訳と、並列化への入力」
  — 1 反復所要が混合区間であること
- `output/insights/2026-09-02_t2191-verifier-parallel/README.md` — 検査器単体の費用と 2.2 倍
- `output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md` — 「23 分」の帰属訂正
- `docs/pegasus-node-variance-protocol.md` — ノード間の相対差の実測
- 本 dir の `verbatim/` — 段 1 brief、段 2 plan、段 3 の 2 レンズ、段 4 裁定、親の実測
