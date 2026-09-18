# T-1905 B-10 待ち方 grid — 正式投入 (write-heavy 完走、他 2 workload 未取得)

事前登録 `docs/b10-backoff-shape-preregistration.md` (v4、発効版) に従う正式走の記録である。
**3 workload のうち write-heavy だけが完走した。** read-heavy はユーザー裁定で撤去、
balanced は未投入である。本書は投入と実行の記録であり、結果の解釈と主張は事前登録 §3 と §8 の
制約に従う。

## 発効版の同定と投入前照合

**発効版 prereg commit: `77b33e37d2d63b1f83d10652792c3c93eba9fe8f`**

事前登録本文の blob は `ea910de32df83c1bb320cbe62344dc5fb3b94684` で、この commit で初出し、
着手時の local main 先端まで 1 バイトも変わっていない。v4 を作った直前の 2 commit は本文 bytes が
異なるため発効版ではない。

| commit | 本文 blob | 判定 |
|---|---|---|
| `3673f08b2` (v4 として再設計) | `4d68ab3e6` | 発効版ではない |
| `c0a2689da` (外部床の参照幅を復元) | `b26494bf6` | 発効版ではない |
| `77b33e37d` (D1270 対応を §0 へ明記) | `ea910de32` | **発効版** |

投入前に login node で通した検査 (いずれも read-only)。

- `load_preregistration` — 祖先性、本文 bytes と commit blob の一致、canonical path、
  patch bytes の一致、解析コードの HEAD 束縛。
- `validate_runtime_physical_residual(spec, clocks_per_us=2100)` — 上限が exact 1.0、
  実測表が grid の閉集合と一致、指示平均が環境の `clocks_per_us` と整合、各 `deviation_pct` が
  再計算値と一致、最大絶対偏差が上限未満。**返り値 = 0.5616942857142844** (`constant` / μ=2)。
- `validate_patch_bytes`、`validate_formula_contract`。
- 登録 calibration (`env_tag=pegasus`, `threads=48`, `clocks_per_us=2100`,
  `lower_bound_selected=true`, `cache_floor_warning=false`, `quality.status=accepted`) が
  `load_calibration` の全条件を満たすこと。

## 完走した測定 — write-heavy

campaign `b10-backoff-shape-silo-write-heavy-formal-e3de15eb`、request `965564.nqsv`、
`verify-perf` 相、`driver_rc=0`、所要 3 時間 50 分 (2026-09-02 01:06 終端)。

**45 cell (3 block × 15 点) 全部が `correctness_certified=true` / `missing=false`。**
正しさ検証は 15 変種すべてで anomaly ゼロ、verdict は全件 `serializable`。

block 間で同一の点は同じ値を持つので、点ごとの代表値を示す。

| point | 中央値 throughput | abort 率 | backoff 呼び出し回数 |
|---|---:|---:|---:|
| none | 2,422,011 | 0.7849 | 0 |
| adaptive | 1,354,088 | 0.1221 | 2,830,938 |
| zero-loop | 2,439,674 | 0.7818 | 130,595,054 |
| constant-mu2 | 3,454,217 | 0.6364 | 90,469,377 |
| symmetric-modulo-mu2 | 3,415,244 | 0.6350 | 89,221,334 |
| constant-mu5 | 3,982,673 | 0.4990 | 58,789,077 |
| symmetric-modulo-mu5 | 3,923,154 | 0.5006 | 58,974,695 |
| constant-mu10 | 3,924,247 | 0.3873 | 37,256,513 |
| symmetric-modulo-mu10 | 3,932,174 | 0.3862 | 37,156,234 |
| constant-mu25 | 3,430,191 | 0.2631 | 18,381,750 |
| symmetric-modulo-mu25 | 3,505,891 | 0.2586 | 18,271,151 |
| constant-mu50 | 2,904,761 | 0.1915 | 10,318,030 |
| symmetric-modulo-mu50 | 2,952,224 | 0.1882 | 10,250,505 |
| constant-mu100 | 2,346,648 | 0.1376 | 5,623,103 |
| symmetric-modulo-mu100 | 2,375,988 | 0.1357 | 5,599,704 |

**本書はこの数値から何も結論しない。** 事前登録 §5 の判定手続き (block 内対比較、
符号反転検定、3 族の Holm 補正) は 3 workload の族を前提としており、1 workload だけでは
族が揃わない。判定は残り 2 workload が揃ってから、事前登録した手続きで行う。

レポートと provenance は `reports/write-heavy/` に保全した。

## 未取得

- **read-heavy:** 15 点中 3 点で撤去 (request `965996.nqsv`)。理由は下記。
- **balanced:** 未投入。先行して 6 時間枠で走らせた verify は 15 変種中 14 変種で打ち切られ、
  その WAL は D193 により再開不能になった (下記)。

## 実行で判明した機構の欠陥 (4 件、いずれも実測)

### 1. official 出力 root が未配線で verify が起動しない

D641 は `declared_use_class="official"` の campaign 出力 root を repo 外の明示指定に限り、
未指定なら fail-closed にすると定める。`tools/pegasus/b10_backoff_shape_campaign.sh` は
これを渡していなかった。**probe 相と build 相は `campaign_layout` の手前で終わるため、
この欠落は verify が初回の露見点である。** verify は 20 秒で `driver_rc=1` になった。

env を設定するだけでは足りない。外部 root 配下の claim root は既定の書き込み許可方針
(repo の `output/` だけを承認) が拒否するので、解決済み root を承認する方針を
`run_campaign` へ注入する必要がある。実証済みの型は
`orchestrator/campaign/paper_story_a2_certification.py` にある。

### 2. binary に job 固有 path が入り、認証と測定の SHA が一致しない

事前登録 §7 は「性能測定に使う binary は正しさを認証した attempt の binary の SHA-256 と
完全一致させる」と要求する。ところが job ごとに変わる作業 path が binary の bytes に入るため、
**相を別 job に分けた時点でこの一致は構造的に起こりえない。** perf 相は 45 cell 全部が
「performance binary SHA が correctness-certified BUILD_DONE と不一致」で計測不能に終わった。

path が入る経路は 3 つあり、完走した binary を解剖して全数を確定した。

- `.rodata` の `__FILE__` 由来 8 件 (offset 278607-282271)
- RUNPATH 1 件 (gflags/glog の install prefix)
- buildcache の staging directory (`.staging-<PID>-<hex>`) が `.debug_line_str` に残る

同一 genome・同一 trace 設定の 2 binary は size 701,920 で一致し、差は 149 bytes だけだった。

**path 非依存化は 2 巡実装したが収束しなかった** (差分 149 → 56 → 45,454 bytes)。
この build は `-g -O3` で完全な debug 情報を持ち、byte 再現性の確保が現実的でない。
codex 相談も同じ結論で、**同一 job・同一 checkout で認証と測定を行う `verify-perf` 相**を採った。
write-heavy 45/45 の完走はこの形で得られた。

**cell を別ノードへ分散する設計では、この面が再燃する。**

### 3. 壁時計の固定値が 4 か所に散っている

`#PBS -l elapstim_req`、job script の受領証照合、job script の起動時自己検査、投入器の要求値、
driver の receipt 検査。1 か所でも食い違うと job が起動時の自己検査で落ちる。

### 4. シグナル処理が壊れており、強制終了の理由が毎回失われる

`tools/pegasus/b10_backoff_shape_campaign.sh` の signal handler は

```
local name=$1 number=$2 rc=$((128 + number))
```

と書かれている。`$((128 + number))` は語展開時に評価されるため `number` はまだ未設定で、
`set -u` により `number: unbound variable` で落ちる。**その結果 `write_failure` へ到達せず、
`failure.json` が書かれない。** 実測: request `965996.nqsv` の scheduler.stderr に
`user_script: line 108: number: unbound variable` が出ている。balanced が 6 時間で
打ち切られたときも同じ理由で記録が残らなかった。**本 wave では未修正。**

## 打ち切りからの再開が塞がる 2 つの関門 (実測)

balanced は 6 時間枠で 15 変種中 14 変種まで進んで打ち切られた。再投入は 2 段で塞がれた。

1. **stale claim。** `campaign_claim.acquire_claim` は「claim は crash 後も残す。stale 判定、
   自動削除、release は意図的に存在しない」と定める。所有者の死亡を scheduler の応答で確定させ、
   claim の bytes を `receipts/stale-claim-963545-balanced.json` へ保全してから操作者判断で除去した。
2. **D193 の回復制限。** 「build 完了後の record が 1 つでもある中断 attempt は自動回復しない。
   1 バイトも書かずに停止する」。理由は「回復後に正しさ signal だけが静かに紛れ込む列を
   構成させない」ことであり、正しさゲートそのものなので迂回しない。**この WAL は再開できない。**

## 所要時間の内訳 (実測)

1 反復の所要は取引試行数 (commits + aborts) に対して約 25.6 マイクロ秒/件で、175 秒あたりで
頭打ちになる。**ベンチマーク実体の時間は 1 workload で 4.5 分** (3 秒 × 6 記録 × 15 変種) であり、
残りはトレース書き出しと直列化可能性検査である。反復数 5・extime 3 秒・レコード 100 万・
48 スレッドはいずれも事前登録済みで、§7 が「実行時間を理由に減らさない」と明記している。

**read-heavy は「中止が少ないから速い」という予測が外れた。** 中止は 300 万件と少ないが
commit が 1690 万件あり、検査対象の合計は write-heavy とほぼ同じ約 2000 万件である。

> **但し書き (D1529、2026-09-04)。** 「commit が 1690 万件」「中止 300 万件」「約 2000 万件」の
> 母集団は、read-heavy で commit 数が飽和した 3 変種の本規模 (performance) 反復 (反復数 5・5・3)
> である。3 反復だけの 1 変種は、campaign 記録上 commit (変種の認証確定) に到達しないまま
> 打ち切られた実行 (以下「欠測 attempt」) の `constant-mu2` 変種 `292d58f1dad8` で、5 反復のうち
> 3 反復だけが記録に残る。値を無効にするものではなく、欠測 attempt を除いた母集団での再計算は
> 行っていない。

**CPU/経過 = 1.0 である。** 48 コア確保のうち 47 コアが遊休だった。read-heavy はこの形で
5 時間走って 15 点中 3 点しか終わらず、ユーザー裁定により撤去された。
**次の正式系列は複数ノードへ分散した形で設計し、ユーザー裁定を経てから投入する。**

> **但し書き (D1529)。** 「5 時間走って 15 点中 3 点」の 5 時間は、撤去された request `965996`
> の走行時間を指すが、その計測区間は現記録から確定できない (request 全体の Elapse は 20950 秒 =
> 約 5 時間 49 分)。いずれの区間でも、完了した 3 変種の時間のほかに、欠測 attempt
> (`constant-mu2`) の初期確認 (legacy) 1 反復と本規模 3 反復に使った時間を少なくとも含む。
> 終了直前に次の反復が始まっていたかは記録が無く不明である。「15 点」は登録格子の構造数で、欠測とは無関係である。値を無効にするものではなく、
> 欠測 attempt の時間を除いた再計算は行っていない。

> **追記 (T-2321、2026-09-18): 記録境界と旧所要の区別。** 上の「5 時間」の計測区間は引き続き未同定である。
> request `965996` の Started (2026-09-02 01:07:49 JST) からの秒表示差として、3 変種目の認証確定までは
> 16,387 秒、WAL 末尾 (4 変種目の本規模 3 反復目) までは 20,682 秒、Ended までは 20,946 秒 (scheduler の
> Elapse 記載は 20950S)。欠測 attempt の本規模 3 反復を含むことは WAL 末尾まで等の区間では確認できるが、旧所要
> への帰属は確定しない。根拠と精度は `docs/b10-multinode-formal-run-design.md` §1 の同名追記を参照。既存行と
> 当時の判定を保持し、値を無効にせず、欠測 attempt の時間を除いた再計算は行わない。

## 未確認の観察 (別タスク候補)

1 反復の所要が 655 万件を超えると 175 秒前後で頭打ちになる。トレースに上限があって
切り捨てられている可能性がある。その場合、検査が実際に覆っている取引の割合が主張と食い違う。
正しさ主張に関わるので確認が要る。

## 追記 (2026-09-02、[T-1905] 分散設計 wave)

本文は測定時点の記録なので書き換えない。分散設計を書く過程で、本文の 2 か所が現物と
食い違うことが分かったので追記で訂正する。設計側の正本は
`docs/b10-multinode-formal-run-design.md`。

1. **「壁時計の固定値が 4 か所」は 5 か所である。** 4 か所に加えて
   `orchestrator/campaign/b10_backoff_shape_sweep.py` の submission receipt 検査が
   `elapstim_req_s` の 43200 を直書きしている。4 か所だけ直すと残り 1 か所で全 request が拒否される。
2. **「ベンチマーク実体の時間は 1 workload で 4.5 分」は性能相の値ではない。** 登録値
   (3 block × 15 点 × 5 反復 × 3 秒) から計算すると性能相の名目実行時間だけで 675 秒 =
   11 分 15 秒である。4.5 分は 15 変種分に対応する値であり、45 セル分ではない。
   所要の内訳を「本体 4.5 分 + 残り」と読むと、性能相を 1 workload あたり 6.75 分過小に、
   検査側を同じだけ過大に見積もる。**「大半がトレース書き出しと検査である」という本文の結論は
   変わらない。**

## 主張しないこと

事前登録 §3 と §8 の制限をそのまま引く。`binary` は測っていない。3 水準の ladder は
比較していない。`binary` の除外は事前登録された判断ではなく probe 結果を見た後の改訂である。
待ち方と待ち量の直交切り分けを一般に閉じてはいない。**加えて本走は 3 workload のうち
1 workload しか完走しておらず、事前登録した 3 族の Holm 判定は行っていない。**
