# 探索の独立反復の試走 — block 1 の欠測の原因、投入の停止、正しさを弱めずに費用を削る案の実測比較 ([T-2850]、2026-09-26)

- 位置づけ: 実測と試算の記録。規則の正本は事前登録 v1 `docs/search-repetition-trial-preregistration.md` (D2231)・追補 1、発効は同 wave の decisions fragment
  (2026-09-23)。前段の記録は `output/insights/2026-09-23/t2850-trial-effect-bundle/README.md`。
- wave: `worktree-t2850-trial-run` (2026-09-26 に再開、開始時 tip `835c79edc`)。repo の実装差分はゼロ。測定 script は repo 外で Codex author が書いた (fix 1 回)。
- job dir (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-run/` — block 1 の台帳 `cohort-trial/`・`evidence-trial/`、内訳 `estimate/block1-breakdown.json`、
  試算 `estimate/cost_options.py` と `estimate/cost-options-{3.4,12}.json`、測定 `vprobe/` (script `probe_verify_parallel.py` sha256 `2b7828f5…`、v2 `2e029e8b…`、生データ `vprobe/runs/*/probe.json`)。

## 0. 経過

1. 前 session が block 1 の 6 job (21512〜21517、2026-09-23 23:19 投入) の後に消えた。block 2・3 の 12 job は未投入のまま。
2. 2026-09-26 の再開で rc=1 の 3 本の原因を一次資料で確かめた (§1)。
3. 同日、next-tasks の session がユーザーの指示を中継した: 「block 2・3 は投入しない。費用を削る案を実測で比べ、ユーザーの確認を取ってから投入する」。
   同種の B-5 本走 (見積り 680 node 時間) へのユーザーの発言 (逐語、中継のまま):
   「680node時間使うって何？ありえない。5秒5回実験、xをスイープさせて8プロット点でも200秒でグラフ一つ作れるだろ？1時間で18このグラフが作れる。幾つのグラフ作ろうとしてるんだ？」。
   試走の既承認 (write-heavy だけ 42.4〜60.6 node 時間) はこの発言で差し戻されたものとして扱う。**block 2・3 は投入していない。**
4. B-5 の費用削減を比べる wave (`optimize node cost estimation t-2797`) と分担した: 共通部分 (評価 1 回の内訳・検証の並列化の効果・LLM 待ち) はこの wave が測り、単価を送った。

## 1. block 1 の rc=1 の 3 本の原因と扱い

| job | 系列 | 終端 | 原因 (一次資料) |
|---|---|---|---|
| 21515 (bnode034、Elapse 305 s) | random s1 | `stock-unestablished` | 系列開始 stock は certified だが bench の `settled=false` → 品質欠測。bench の前の静定待ち (1 分 load average が 4.0 以下になるまで最大 20 s、`orchestrator/calibrator/runner.py` の `settle`) が時間切れ。load の実値は記録されない |
| 21516 (bnode037、Elapse 300 s) | sweep s1 | `stock-unestablished` | 同上 |
| 21514 (bnode049、Elapse 4,777 s) | llm s1 | `proposal-wait-timeout` (a=2) | 原提案 1 は評価まで完了。原提案 2 の親 session が起動 20 s で `api_error_status 429`「You've hit your weekly limit · resets Sep 26, 6am (Asia/Tokyo)」で終わり (`parents/state-trial-b1/trial-wh-llm-s1/a-2/out.json`)、driver は 2,702.7 s 待って系列を終えた |

- **扱い = 欠測、再投入しない。** 基盤設計 (`output/insights/2026-09-22/t2849-comparison-harness-design/README.md`) §4.6 項 1「stock の正しさか測定が成立しない → 当該比較は判定不能」、
  §5.6 と事前登録 §5「欠測・A の枯渇・fallback は系列の結果として残し、系列を差し替えない」。
- node の同居はなかった: bnode034 は random の終了 (23:27:07) の 30 s 後に evolution が開始した。
- 静定待ちの時間切れは block 1 の stock 12 session 中 5 件 (random・sweep の系列開始 stock、block stock 1・2・5) と、bo の探索 2 件 (v = 1000 µs) で起きた。
  該当 session はすべて bench の周辺 wall が 36.8 s (bench 16.8 s + 待ちの上限 20 s) である。§3.4 の実測では、直列の検証の直後の load は 1.6〜3.0 で 4.0 未満だったので、
  **検証の余熱だけでは説明できず、原因は未確定**である。
- LLM の週次上限: 2026-09-23 23:50 JST ごろ、B-5 本走の LLM 4 系列も同じ 429 で同時に止まった (T-2797 wave の報告)。当時の同時の LLM 親は試走 1 + B-5 4 = 5 本で、
  これに対話・開発の session (2026-09-26 の ListAgents で 10 本) が同じサブスクリプションの枠を共有している。

## 2. 評価 1 回の内訳 (block 1、S1 write-heavy、commit `7ea9aa09d`)

| slot の種類 | 1 session | build | 正しさの検証 | bench | その他 |
|---|---:|---:|---:|---:|---:|
| 候補 (v = 1〜28 µs、23 件) | 474〜520 s | 9 s | 430〜476 s (legacy 11〜16 s + 性能 trace 5 本 × 84〜93 s) | 16.8 s | 約 20 s |
| 候補 (v = 1000 µs) | 215〜220 s | 9 s | 154〜157 s | 16.8 s | — |
| stock | 245〜273 s | 15 s | 202〜213 s (7 s + 5 × 約 40 s) | 16.8 s | 静定待ち 0〜20 s |
| 参照点 `p2_2_flag_opt` | 472〜482 s | 15 s | 434〜442 s | 16.8 s | — |

- 検証が候補の session の約 91 % を占める。bench (3 秒 × 5 回) は 16.8 s。
- 系列 1 本 (stock 1・初期点 2・探索 10・測り直し 5 = 18 session) の job Elapse は bo 8,079 s・evolution 9,023 s、block job (stock 5・参照点 5) は 3,710 s。
  LLM は 1 機会の待ち 255 s (試走、1 件)、smoke では 225〜780 s。待つ間も node を確保している。

## 3. 検証を同じ node で同時に走らせる測定 (vprobe、2026-09-26)

### 3.1 方法

- 測定 script (repo 外、Codex author): 固定 checkout `7ea9aa09d` の上で trace 有効の build を作り、性能構成 (100 万レコード・48 thread・3 s) の trace を直列に 5 本 (または 4 本) 取得して残し、
  (1) 5 本を 1 本ずつ検査、(2) 90 s の load1 の減衰、(3) 同じ 5 本を同時に検査、(4) 90 s の load1 の減衰、を測る。検査は `python -m verifier <trace> --json --quiet --protocol silo
  --ccbench-root … --expected-commits <n>` (`s2_verify_calibration._verifier_run` と同じ argv、判定・閾値・worker 数 (既定 16) は変えない)。直列と同時で verdict・certified・
  取引数・辺数・閉路数が一致するかを記録した。
- pipeline は同じ verifier library を同じ既定で in-process に呼ぶ (`verify_trace_dir_with_capability`)。stock の 1 反復は pipeline 40 s、測定では検査 35 s + trace 取得 3.4 s で合う。
- generic dispatch (gen_S)、各 job の開始時に `_assert_single_tenant` を通過。

### 3.2 結果

| 構成 | node | trace 1 本の取引数 | 直列 5 本 | 同時 | 比 | 判定の一致 | node 記憶量の最大 | job Elapse |
|---|---|---:|---:|---:|---:|---|---:|---:|
| wh stock | bnode094 | 109〜113 万 | 177.8 s (34.7〜36.3 s/本) | 5 本同時 42.8 s | 0.24 | 全件一致 | 15.5 GiB | 458 s |
| wh stock (再現、下の注) | bnode078 | 107〜112 万 | 177.6 s | 5 本同時 42.8 s | 0.24 | 全件一致 | 15.6 GiB | 458 s |
| rh stock | bnode078 | 552〜563 万 | 640.5 s (125.7〜130.5 s/本) | 5 本同時 166.2 s | 0.26 | 全件一致 | 67.8 GiB | 1,059 s |
| wh B0-L-W0 (重い trace の代理) | bnode099 | 235〜238 万 | 396.8 s (78.8〜80.1 s/本) | 5 本同時 95.0 s | 0.24 | 全件一致 | 27.4 GiB | 734 s |

- 全件 `serializable`・certified、OOM 0。同時にしても判定は変わらない (検査そのものは同じ argv で、trace も全本検査する)。
- 注: 2 行目は「固定 8 µs の候補」として投入したが、`-DCCBENCH_BACKOFF_FIXED=8` は CCBench 本体に無く (template patch が供給する)、build は stock と同じだった
  (取引数・検査時間が stock と一致)。F707 と同型の再発で、stock の再現として扱う。同じ理由で rh 8 µs の job は投入前に止め、flag だけで実現できる B0-L-W0
  (T-2847 の容量実測と同じ定義) を重い trace の代理にした。B0-L-W0 の wh の trace は候補 (1 反復 84〜93 s) とほぼ同じ重さである。
- この wave の測定の計算: 4 job の Elapse 計 2,709 s = 0.75 node 時間。B-5 側の依頼で rh B0-L-W0 (4 本・同時 2 本) を同じ木から 1 job 投入した (B-5 側の枠で数える)。

### 3.3 同時検査の直後の load

| 構成 | 直列の直後 load1 → 20 s 後 | 同時の直後 load1 → 20 s 後 | 同時の後に 4.0 以下になるまで |
|---|---|---|---:|
| wh stock | 2.9 → 2.0 | 6.0 → 4.3 | 23 s |
| wh stock (再現) | 3.0 → 2.3 | 4.3 → 3.0 | 3 s |
| rh stock | 2.2 → 1.6 | 11.1 → 8.0 | 61 s |
| wh B0-L-W0 | 1.6 → 1.1 | 7.4 → 5.3 | 39 s |

**同時検査は、今の静定待ち (最大 20 s) では bench の品質欠測を増やす。** 並列化は静定待ちの上限を 60 s 以上へ上げることと組でないと使えない (1 session 最大 +40 s)。

## 4. 費用を削る案の比較 (図 1 枚あたりの node 時間)

「図 1 枚」は事前登録 §5 の主図の単位 = 1 手法の曲線 (3 系列の中央値と帯)。試走 (S1-wh) は 5 枚。block job 3 本は 5 枚で共有する。
試算は `estimate/cost_options.py` (block 1 の job Elapse と slot ごとの内訳に、§3 の比を当てる)。同時化の効果は、性能 trace 1 本のうち並列化しない部分を 3.4 s (trace の取得だけ、楽観) と
12 s (pipeline の 1 反復と測定の検査時間の差、保守) の 2 通りで出した。静定待ちの延長 (+最大 40 s/session) は含めていない (系列 1 本で最大 +0.2 node 時間)。

| 案 | 正しさの検査 | 非 LLM の図 1 枚 | LLM の図 1 枚 | block job (共有) | 試走全体 (5 枚) | 必要な作業 |
|---|---|---:|---:|---:|---:|---|
| 今のまま | 変えない | 7.1 | 9.3〜26.6 | 3.1 | 40.8〜58.2 | なし |
| (a) LLM の待ちを node の外へ | 変えない | 7.1 | 7.1 | 3.1 | 38.7 | harness を評価ごとの job か、待つ間 node を返す形に変える。経過時間は縮まない |
| (b) 検証 5 本を同じ node で同時に | 変えない (全 trace を同じ argv で検査) | 2.6〜3.2 | 4.7〜22.7 | 1.2〜1.5 | 16.3〜37.0 | pipeline の検証の反復を「trace は直列に取得、検査は同時」に変え、静定待ちを 60 s 以上に |
| (a) + (b) | 変えない | 2.6〜3.2 | 2.6〜3.2 | 1.2〜1.5 | 14.2〜17.5 | 上の両方 |
| (c) 規模の縮小 (事前登録の改訂、ユーザー判断) | 変えない | 係数を掛ける | 同左 | — | — | 追補 |

- (c) の係数 (系列 1 本 18 session に対して): 系列数 3 → 2 は 2/3、endpoint の測り直し N_eval 5 → 3 は 16/18、評価数 B 10 → 6 は 14/18。
  試走の目的は本比較の系列数を決める分散の推定 (事前登録 §8) なので、系列数を減らすと分散の推定が粗くなり、B・N_eval を変えると本比較と同じ系列の定義でなくなる (§3.2)。
- 候補の 1 session は 515 s → 180〜221 s (b)。ユーザーの言う「x を 8 点振る図」に当てると、bench だけなら 8 × 17 s ≈ 0.04 node 時間、正しさの検証を含めて今のままだと 8 × 515 s ≈ 1.1 node 時間、
  (b) で 0.4〜0.5 node 時間。試走の図は 8 点ではなく、独立な探索 3 系列 × (stock 1 + 初期点 2 + 探索 10 + 測り直し 5) = 54 session の比較である。
- trace の本数・長さを減らす案は正しさの検査 (規律 2) を弱めるので勧めない。
- (b) と (a) は評価 1 回の経過時間を変える。事前登録 §6.2 の経過時間の比較 (T_c・E_T) は所要の記録から決まるので、**実装を変えた後の系列と block 1 の系列は混ぜられない**
  (§3.1「修正前の系列は修正後の構成の分散の推定に混ぜない」)。(b) を採るなら block 1 は予備走とし、3 block を新しい実装で走らせ直すのが素直である。

## 5. 限定・言わないこと

- 同時化の比は stock・B0-L-W0 の trace で測った。候補 (hole code の backoff) の trace そのものでは測っていない。B0-L-W0 の wh は候補と取引数・検査時間が近い代理である。
- rh の候補 (1 本 約 430 s・40 GiB) は 5 本同時に置くと node の約 115 GiB を超えうる。rh の同時 2 本は B-5 側の依頼で測定中で、この記録の時点で結果は無い。
- 静定待ちの時間切れの原因は未確定 (§1)。
- 試算は write-heavy の block 1 の 2 系列 (bo・evolution) の実測に依存する。LLM の待ちの幅は smoke と試走の 3 件だけから置いた。
