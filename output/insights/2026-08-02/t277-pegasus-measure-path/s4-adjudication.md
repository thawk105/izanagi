# 段 4 裁定 — [T-277] Pegasus 計測パスを開く

親が段 2 プランと敵対レンズ 2 本 (ともに NO-GO) を real/refuted に裁定し、plan v2 と変異事前登録を確定する。
**レンズの所見は親が独立に裏取りしたものだけを real とした。**

## 1. 親が独立に実測した新事実 (裁定時点で未見)

- **(N1) campaign identity に env が入らない。** 既定 campaign
  `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/` は既に
  `loop_state.json` が iteration=2、`runs/wal.jsonl` の全 record が `env_tag":"linux-baremetal"`。
  受理集合だけ開けると Pegasus 実行が同一 campaign root を指す。
- **(N2) ambient `CMAKE_PREFIX_PATH` が無記録で build に効く。** `buildcache._run` は
  `subprocess.run(cmd, capture_output=True, text=True, timeout=...)` で `env=` を渡さない。
  `tools/pegasus/floor_campaign.sh:856` はこれを唯一の依存 seam として export し、
  `tools/pegasus/README.md:174-176` が「floor driver は `-DCMAKE_PREFIX_PATH` を渡さない」と明記する。
- **(N3) `site` は注入値が無検査で信頼される。** `buildcache._resolve_site` は
  `site_policy.current_site() if site is None else site`。`_run` の heavy-work gate もこの値を見る。
- **(N4) `source_digest.resolve` の既定 cxx は `g++-13`** (`source_digest.py:702`、同種既定が計 7 箇所)。
  `loop.py:103-105` が build より前に呼ぶため、Pegasus では identity 計算で停止する。
  さらに非 stock の `src_token` は preprocess 出力の hash なので、compiler が変わると
  **同一 genome・同一ソースでも variant_id が環境間で分岐する。**
- **(N5) D108 決定 (1) が compute 上の `claude -p` を禁じ**、8c は provider を同一 process で呼ぶ。
- **(N6) prefix / claim root / reservation を p3 経路へ供給する caller が存在しない** (プランも
  発見できなかったと認めた)。
- **(N7) 登録済み Pegasus calibration は 1M records / 48 threads**
  (`calibration-753f535a8d024727.json` の `saturation.records`/`threads`) だが、trigger の動作点は
  **100k / 4** (`p3_s4_loop_trigger_gating.py:369-370`)。一致する floor が無い。

## 2. 所見の裁定

| # | 所見 | 判定 | 扱い |
|---|---|---|---|
| A-1 | 注入 `site` で build gate を偽装できる | **real** (N3) | **採用 (形を変えて)**: `site` を `evaluate`/`run_campaign` の公開引数にしない。identity に入れるのは sink 側 `_resolve_site()` の実解決値。既存 `build_v2(site=)` の gate 挙動は本 wave の新設でないため変えず、gate 迂回そのものは裁定へ |
| A-2 | LOGIN は PATH から qsub が消えると `OTHER` へ fail-open | **real・既存** | **scope 外 → 裁定へ**。本 wave は悪化させない (今日も `OTHER` は受理側)。site 分類の強化は consumer が広く別 wave |
| A-3 | caller 構築の `AcquiredClaim` は取得証明でない | **real** | **採用**: lease を caller から受け取る設計を却下。claim は sink 内取得のみ。ただし S5 の claim 強制自体を本 wave では実装しない (下記) |
| A-4 | fixture provider + programmatic `do_build=True` の bypass | **real・既存 (D106 既知残余)** | **scope 外 → 裁定へ**。本 wave で compute capability を足さないので悪化しない |
| A-5 | D108 の禁止と domain result 未解決 | **real** (N5) | **採用**: 8c の compute 運転を本 wave の scope から外す |
| A-6 | reservation が host/authority を検証しない | **real** | S5 を実装しないので**本 wave では非適用**。裁定へ |
| A-7 | durable proof の path enforcement がない | **real** | 一部採用: 本 wave は WAL/成果物の置き場を変えない。`--run-root` の durable 強制は裁定へ |
| A-8 | dependency prefix は path 文字列で内容 hash でない | **real** | **採用 (限定)**: 本 wave は「実際に効いた prefix 文字列を identity に束縛する」までを射程とし、依存 bytes の hash 束縛は裁定へ。**謳わない** |
| A-9 | certify は planned route の生死確認にならない | **real** | **採用 — 親 brief (P3) を撤回する。** 生死確認は本 wave で計算ノード上に実際に取る (下記 4) |
| B-1 | fresh なのは cache だけで campaign は既存成果物へ衝突 | **real** (N1) | **採用・実装する。** これが無いと S1/S2 は成果物を壊す |
| B-2 | 空 prefix 互換逃げで誤 hit が残る | **real** (N2) | **採用・実装する。** プランの「ambient を読まない」を却下し、**読んで identity に束縛する** |
| B-3 | prefix/claim/reservation/`/scr` を供給する実 caller が無い | **real** (N6) | **採用**: S4/S5 を本 wave から外し、成果物名を「routing + identity + gate」へ格下げする |
| B-4 | 兄弟 driver 不変は片肺 | **real** | **一部採用**: 兄弟 driver の移行はしないが、**COMPUTE を明示拒否**して「sanctioned は trigger/8c のみ」を機械化する (レンズの提案どおり、移行より小さい) |
| B-5 | env_tag が critic/screening/renderer で落ちる | **real** | **scope 外 → 裁定へ**。ただし B-1 の env 分離により「混ざった digest」は構造的に発生しなくなる |
| B-6 | calibration 不一致で calibrated certified 選択にならない | **real** (N7) | **採用**: worklog と D に「exploratory throughput までであり floor 認証選択ではない」と明記する |
| B-7 | 新テストが先行 gate に mask される | **real** | **採用**: 変異事前登録で先行 gate を neutral 化した fixture を要求する (下記 5) |
| B-8 | login 実測の compute への一般化 | **partial** | gcc-13 不在は runbook が compute でも裏付ける。「module に gcc なし」の一般化は brief から**撤回**する |

## 3. plan v2 (実装する範囲)

### 実装単位 A — `buildcache.py` / `pipeline.py` / `loop.py`

- **A-a build identity**: `_v2_identity` の pre-image へ `site` (sink 側 `_resolve_site()` の実解決値) と
  `dependency_prefix` (下記の実効値) を常時追加する。legacy `cache_key` は触らない。
- **A-b ambient seam の束縛 (N2)**: `build_v2` に `dependency_prefix: str = ""` を足す。
  - 非空なら configure argv へ `-DCMAKE_PREFIX_PATH=<prefix>` を渡し、**その値を identity に入れる**。
    このとき build subprocess の環境から `CMAKE_PREFIX_PATH` を除去し、実効値を一意にする。
  - 空なら ambient `CMAKE_PREFIX_PATH` を読み、canonical 化して **identity に入れる** (argv は従来どおり)。
    「読まない」は採らない — 読まなければ floor の実 build 条件が identity から落ちる。
- **A-c compiler の site 解決**: `PEGASUS_COMPUTE` のときだけ `("gcc","g++")`、他は既存
  `DEFAULT_CC/CXX` を返す helper を `buildcache` に置く。解決は sink 側の実 site で行う。
- **A-d `source_digest` 配線 (N4)**: `loop.py` と `pipeline.py` の `source_digest.resolve` 呼びへ
  同 helper の `cxx` を渡す。
- **A-e 素通し**: `run_campaign` / `evaluate` に足すのは `env_contract` だけ。**`site` は足さない** (A-1)。

### 実装単位 B — driver 2 本 + テスト

- **B-a 受理集合**: `_site_admits_measurement` を `{OTHER, PEGASUS_COMPUTE}` の exact set にする。
- **B-b contract 解決**: site→tag の閉じた対応 `{OTHER: "linux-baremetal", PEGASUS_COMPUTE: "pegasus"}`
  で lookup する。環境変数 override は作らない。
- **B-c campaign の env 分離 (N1)**: Pegasus contract のときだけ `search_config` へ env を足し、
  campaign_id を別空間にする。OTHER は既存 campaign_id を 1 bit も変えない (`src_token` の
  stock 後方互換と同型の規則)。
- **B-d attestation の実発火**: `run_one_iteration` の `do_build` 分岐で、contract 解決後・
  `run_campaign` 直前に `attestation_mode=="required"` なら
  `env_attestation.load_verified_calibration` → `execution_guard.attest_and_build_receipt` →
  `receipt_matches_contract` を発火させ、receipt を provenance へ記録する。
  `_admit_env_contract` の中では発火させない (reject 記録に hardware probe を要求しない)。
- **B-e resume 拒否**: Pegasus contract で既存 loop state があれば拒否する。
  **先行 freshness gate に mask されるため**、変異検査は freshness を neutral 化した fixture で行う。
- **B-f 兄弟 driver の明示拒否 (B-4)**: `p3_s4_loop.py` / `p3_s4_loop_sort.py` / `s8a_*` /
  `s6_sort_sweep.py` / `backoff_sweep.py` の legacy 経路は、`PEGASUS_COMPUTE` を**明示的に拒否**する。
  移行はしない。これで「Pegasus 値が linux-baremetal として台帳に入る」旧入口を塞ぐ。

## 4. 本 wave の scope から外すもの (新事実つきでユーザー再裁定へ返す)

親は独断で不採用にしない。**裁定済み (a) のうち次を保留し、新事実を付けて再裁定へ戻す。**

1. **S4 `/scr` fresh namespace と S5 の claim/reservation による `single_process` 強制** —
   供給する caller が存在せず (N6)、caller から lease を受ければ偽造可能 (A-3)、
   reservation は host/authority を検証しない (A-6)。実装すれば発火しない gate になる (`DW-G04`)。
2. **8c を計算ノードで運転すること** — D108 決定 (1) と正面衝突する (N5)。
   これは [T-276] の裁定対象であり、T-277 が独断で supersede しない。
3. **calibrated certified 選択** — 登録 calibration の動作点が trigger と一致しない (N7)。
   本 wave の成果は **exploratory throughput までであり、floor 認証選択ではない**と明記する。

**成果物名を格下げする。** 本 wave は「Pegasus 計測パスの routing・build identity・受理 gate を実装した」
であって「live 計測が開通した」ではない。worklog と D に同じ言葉で書く。

## 5. 生死確認 (DW-G01) — 親 brief (P3) の撤回と代替

親 brief (P3) は `certify_calibration.sh` の既存実績を生死確認に代替しようとしたが、
A-9/B-3 のとおり configure 条件も入口も異なるため**撤回する**。

代替として、本 wave は**計算ノード上で実際に次を通す**:
`site` が `PEGASUS_COMPUTE` に解決され、`_admit_env_contract` が `pegasus` contract を返し、
diff 検疫 reject が `env_tag="pegasus"` で記録されること。これは build を必要としない最安の経路で、
S1/S2/B-c の発火条件を満たす実 artifact になる (`DW-G04`)。build を通す live pilot は
T-276 land と dependency 供給 wrapper の後とする。

## 6. 変異事前登録 (DW-M01)

各変異は「その位置より前に同じ入力を拒否する検査がないこと」「無効化時の赤理由が一つに絞れること」を
実装後にコードで確認してから本走する。確認できない変異は登録から外し実効 gate へ再照準する。

| # | 変異 | 期待 kill 理由 (単一) |
|---|---|---|
| M1 | `_site_admits_measurement` を `{OTHER}` へ戻す | compute admission 正例が赤 (受理集合の縮小) |
| M2 | 同集合へ `PEGASUS_LOGIN` を足す | LOGIN 拒否負例が赤 (過剰拡大の検出) |
| M3 | site→tag 対応の `pegasus` を `linux-baremetal` にする | compute で `contract.env_tag` 期待が赤 |
| M4 | attestation 呼び出しを削る | required contract の measurement 前 attestation 正例が赤 |
| M5 | attestation 例外を握り潰す | 失敗時に `run_campaign` へ到達しない検査が赤 |
| M6 | `allow_resume` 検査を削る | **freshness gate を neutral 化した fixture** での resume 拒否が赤 |
| M7 | v2 pre-image から `site` を落とす | site 差で digest が変わる検査が赤 |
| M8 | v2 pre-image から `dependency_prefix` を落とす | prefix 差で digest が変わる検査が赤 |
| M9 | ambient `CMAKE_PREFIX_PATH` の束縛を落とす | ambient 差で digest が**変わらない**ことを検出する検査が赤 |
| M10 | configure argv から `-DCMAKE_PREFIX_PATH` を落とす | argv 検査が赤 |
| M11 | campaign の env 分離を落とす | pegasus と OTHER の campaign_id が同一になる検査が赤 |
| M12 | `source_digest.resolve` の cxx 配線を落とす | compute で `g++-13` が要求される検査が赤 |
| M13 | identity に caller 注入 site を使う | 注入 site が digest を変えない検査が赤 |
| M14 | 兄弟 driver の COMPUTE 拒否を削る | 兄弟 driver の compute 拒否負例が赤 |

**正例 (過剰拒否の検出)**: OTHER 経路が従来どおり legacy build を使い、campaign_id・cache key・
configure argv が 1 bit も変わらないこと。

## 7. 成果物影響 (DW-G05)

- A-a/A-b 未実装 → 別環境・別依存で作った binary が同 key で hit し、台帳の数値と実バイナリが食い違う。
- B-c 未実装 → Pegasus の record が既存 linux-baremetal campaign の WAL へ混ざり、
  Layer3 の env 一意検査が落ちるか、混合値でレポートが出る。
- B-d 未実装 → attestation なしの数値が proof chain に載り、受入が恒真になる。
- B-f 未実装 → 兄弟 driver 経由の Pegasus 値が `env_tag=linux-baremetal` として台帳とレポートに入る。
