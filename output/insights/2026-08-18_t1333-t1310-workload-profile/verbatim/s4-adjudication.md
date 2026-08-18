# 段 4 裁定 — [T-1333] / [T-1310] / [T-1349]

裁定日時 2026-08-18 13:24 JST。起点 main `a160f4aa` (段 4 直前に再確認、変化なし)。
裁定 inbox を再走査し、wave 開始後の追加は `2026-08-18-t688-codex-quota-exhausted.md` の 1 件のみ
(codex 枠の運用連絡で本 wave の scope 外)。

## 0. 結論

**裁定 [T-1333] 形 1 と [T-1349] は全面実装する。[T-1310] 択 (β) は「源の受理」までを実装し、
「正式 run の起動可能化」は実装しない — 起動が構造的に不可能であることが実測で判明したため、
新事実を添えてユーザー再裁定へ返す。**

`DW-S04` は「承認済み裁定は裁定時の未見事実でだけ止め、親は不採用にせず新事実を添えて
ユーザー再裁定待ちへ戻す」と定める。下記 R-01 / R-02 がその未見事実である。

## 1. real / refuted 裁定

| 所見 | 出所 | 裁定 | 処置 |
|---|---|---|---|
| A-01 起動不能 | lensA + 親実測 | **real** | scope 外へ。裁定パッケージ R-01 |
| A-02 run 自身が 0-hit を壊す | lensA + 親実測 | **real・未記録の新事実** | scope 外へ。裁定パッケージ R-02 |
| A-03 scale literal が第三 authority | lensA + lensB(B-02) | **real** | 一部実装 (下記 2.4)、C01 改訂は scope 外 |
| A-04 provenance が自己整合のみ | lensA + lensB(B-07) | **real** | 実装 (下記 2.5) |
| A-05 frozen pin は held | lensA | **real (should-fix)** | 実装 (下記 2.6)。brief の「緑のまま」を「held」へ訂正 |
| A-06 M4 の「同一 object」は過度な一般化 | lensA | **real (nit)** | brief を訂正済み扱い。実装は四 key canonical 比較 |
| B-01 Layer-3 が descriptor scale を再投影しない | lensB | **real・本 wave 最大の収穫** | 実装 (下記 2.3) |
| B-02 oracle が freeze 文書から別 scale を読む | lensB + lensA(A-03) | **real** | scope 外へ。裁定パッケージ R-03 |
| B-03 formal spec_content が Layer-3 で固定 | lensB + 親 C3 | **real** | 形 A 採用により**消滅** (下記 2.7) |
| B-04 selector 検査位置が admission 順序と矛盾 | lensB | **real** | 形 A 採用により縮退 (下記 2.7) |
| B-05 manifest helper が別 identity sink | lensB | **real (should-fix)** | 実装 (下記 2.3 に同梱) |
| B-06 formal pilot_scope の consumer 取り残し | lensB | **real** | 形 A 採用により**消滅** (下記 2.7) |
| B-08 validator 直呼びテストの漏れ | lensB | **real** | 形 A 採用により**消滅** (下記 2.7) |

**refuted は 0 件。** 両レンズの「反証済みの攻撃」欄 (C01 の遷移予測、non-certifying の漏れ、
T-1349 の二経路非同一、親 M3 / M6) はいずれも親の実測と一致しており、
親側の主張が保たれた形であって所見の反証ではない。

## 2. プラン v2 (実装する形)

### 2.1 [T-1333] 形 1 — 単一 authority (全面実装)

`p3_autonomous_workload_trial.WORKLOADS` の entry を
`{"ycsb": {...}, "records": int, "threads": int}` の構造体にし、
producer の 3 sink (`_campaign_for` / `_perf_for` / `_descriptor_for`) と
Layer-3 の `_check_cell_campaign_identity` の `expected_search_values` が
**同じ entry から** records / threads / ycsb を導出する。

**(P1) を採る (段 2 プランと lensB が独立に支持)。** `cells[].workload_flags` は
entry の `ycsb` 面だけを射影し、探索側の bytes を 1 bit も変えない。
台帳 [T-1333] の「cell に載る値の形と campaign identity が変わる」という予測は、
entry 全体を `workload_flags` として渡す実装を採った場合にだけ成立する。採らない。

非回帰は `m3-baseline.json` の canonical sha256 で pin する
(ycsb-a `8e7d4c37…` / ycsb-b `c749c201…` / ycsb-c `36be6867…`)。

### 2.2 探索既定の保護

`--workloads` の default を `list(WORKLOADS)` から `list(DEFAULT_WORKLOADS)` へ変える。
正式 entry を表へ足しても既定起動が 3 workload から拡大しないため。
親の実測で、この literal を pin する箇所は当該 1 行のみと確認済み。

### 2.3 B-01 の閉塞 (本 wave の主要な正しさ改善)

Layer-3 は現在 descriptor について `descriptor_schema` と `descriptor_sha256` の
自己整合しか見ておらず、`descriptor["scale"]` を entry から**再投影していない**。
`_perf_for` だけの scale 変異は cell から不可視ですらある。

`_check_cell_campaign_identity` に、cell の descriptor から `scale.records` /
`scale.threads` を取り出して entry と完全一致を要求する検査を足す。
`_prepare_manifest_campaign_identity` (B-05) も同じ entry 導出を通す。

**成果物影響**: これが無いと、accepted campaign の descriptor と実測 benchmark の scale が
分離したまま両方緑になり、探索結果の比較対象が誤る。**探索側で今日発火する。**

### 2.4 [T-1349] の同一 bytes assert (全面実装)

三者の関係を次の水準で束縛する。

| 対象 | 要求 |
|---|---|
| module 表 `HOLDOUTS` と producer 正式 entry | `candidate_id` / `records` / `threads` / `ycsb` の四 key canonical bytes 同値 |
| legacy freeze 文書の `holdouts[name]` と module 表 | 同じ四 key の canonical bytes 同値 (legacy は上位集合なので全体同値は要求しない) |
| producer 正式 entry を `_descriptor_for` へ通した content digest と arm resolver の封印 digest | 完全一致 |

最後の一致は親が M8 で実測済み
(rr80 = `80501db0235d88314edd4a4c29a1949e67acc2b466ae426fbbb1cb3da4b7d843`、
rr20 = `53230b8b1f0e0d82def3c384f4d8d8b050a1ce872afd2ed9e2a403c61c3c550b`)。
producer は `project_from_search_config` を、arm resolver は `descriptor_for_holdout` を
呼んでおり**呼ぶ関数が違う**ため、恒真な自己比較にはならない (lensA が確認)。

**A-06 を受けて (P2) を訂正する。** 正式 entry の `ycsb` を module 表と `is` 同一 object に
することは要求しない (records / threads は値コピーで `is` が成立しないため、
「同一 object」の一般化は四 key 全体には成立しない)。四 key の canonical bytes 同値で束縛する。
併せて **A-03 / B-02 を受け、entry へ入れた `records` / `threads` は module 表から取り、
producer 側に第三の scale authority を作らない。** 3 sink 内の
`1_000_000` / `48` literal は C01 が要求するため置くが、**受理条件ではなく
「entry 由来の値が正式 profile の期待値と一致するか」の照合にのみ使う**
(段 2 プランの runtime rejection 形をそのまま採ると literal 自身が authority になり
A-03 の指摘どおり第三 authority を作ってしまうため)。

正式 read 比率は producer file に literal で書かない。producer 本文を
`holdout_conjunction_hits` に通して全 holdout の hit が空であることを pin するテストを置く。

### 2.5 legacy-v1 provenance (A-04 / B-07 を織り込んで実装)

`load_legacy_freeze` を実際に呼び、その戻り値から source record を構築する。
`path` は `V1_FREEZE_PATH`、`sha256` は `LegacyFreeze.sha256` から取り、
**producer 側で path や hash を再記述しない。**
`load_ratified_freeze` は呼ばない。

A-04 / B-07 が指摘した「三箇所の自己一致だけでは同時改変を通す」問題に対しては、
**consumer が `load_legacy_freeze` を独立に呼び直して path / sha256 / 四 key 射影を
再導出して比較する**形にする。byte 同値だけの検査にしない。

non-certifying は**新しい flag を作らない**。既存の強制連鎖
(`trial_registry` が `certifying=False` を発行 → `autonomous_trial_completeness.py:1574` →
`s8c_acceptance_receipt.py:275`) をそのまま使う (親 M7、lensA が漏れなしを確認)。

### 2.6 凍結 bytes (A-05)

`output/s8b-freeze/holdout_freeze.json` と `V1_FREEZE_SHA256` は本 wave で不変。
ただし brief の「`test_frozen_artifacts.py` の pin は緑のまま」は不正確で、
正しくは **held** (`freeze_verification_hold.HELD = True`、holdout freeze は
`HELD_FROZEN_MANIFEST_KEYS` に属し held 時は KEEP 側しか hash 照合しない)。
**訂正する。** land 前に親が両 path の非変更を直接実測する。

### 2.7 正式 run の起動配線は実装しない (形 A)

正式 profile 専用の Layer-3 受理枝 — `search_config.workload_profile` key の追加、
正式 `pilot_scope`、正式 `spec_content` — を**実装しない**。理由は 3 つ。

1. **発火しない。** A-01 により正式 run は admission を通れない (下記 R-01)。
   `DW-G04` は「発火条件を満たす既存 artifact path か計測 ID を brief に書けない
   条件付き機能は実装せず設計メモに留める」と定める。書けない。
2. **[T-822] 第 6 回ユーザー裁定に反する。** 「空振りする検査を置いて保証があるように
   見せる方が、保証が無いことを明示するより悪い」。
3. **裁定の射程外。** (β) は「源の受理」の裁定であって、launch admission に
   新しい mode を足す裁定ではない。admission mode の新設は受理集合を launch gate で
   広げる変更であり、独立のユーザー裁定が要る。

代わりに、正式 selector を渡した経路は **fail-closed で明示的に止める** —
「formal launch is not admissible: effective preregistration unavailable」を
blocker 参照つきで送出する。これは検査であって空振りではなく、
R-01 が解けた時点で 1 箇所を外せば通る形にする。

**この形 A により B-03 / B-06 / B-08 は消滅し、B-04 は縮退する** (selector 検査は
admission より前の closed-set 検査だけになる)。波及も段 2 プランが列挙した
`test_trial_registry.py` の 24 件を含む 40 件超から大幅に縮む
(正式 campaign identity を一度も発行しないため)。

## 3. ユーザーへ返す裁定パッケージ

### R-01 — 正式 run は今日いかなる経路でも起動できない (新事実の精密化)

`admit_registered_launch` は `EffectivePreregistration` を要求し、それは
`s8c_preregistration.py:1730-1757` で **12 predicate 全部が SATISFIED** であることを要求する。
現 snapshot の SATISFIED は **0 件** (`test_s8c_preregistration_predicates.py` が
`sum(SATISFIED) == 0` を assert している)。未登録の探索経路は
`trial_registry.py:1390-1394` で holdout workload を明示的に拒否する (`u4-holdout-workload`)。

[T-1310] 正本の塞ぐ点 (3) は「manifest が無い」までを記録していたが、
**全 predicate SATISFIED という形の要求**は記録されていない。
C01 を UNSATISFIED のまま残す (β) の設計と正面から衝突する。

**択**:
- (a) 正式 non-certifying 専用の launch admission mode を新設する
  (lensA の A-01 提案)。受理集合を launch gate で広げるため独立裁定が要る。
- (b) 8c registered 経路を通さず、oracle driver 側または手動で正式 scale を測る。
  ただし oracle 側も `LaunchValidatedFreeze` → `RatifiedFreeze` を要求し v2 未発効で塞がる (R-03)。
- (c) 択 (α) へ戻り、v2 世代の発行と承認を先に置く。
- **親の推奨 = (a)**。(β) を選んだ意図 (自作の証拠水準を下げて実測を始める) を
  実際に実現するのは (a) だけである。(b) は別の同じ壁に当たり、(c) は (β) の撤回に等しい。

### R-02 — 正式 run は自分が書く artifact で repo scan の 0-hit を壊す (完全に新規)

正式 rr80 run が書く `campaign.lock` は compact canonical JSON で
`ycsb_rratio` / `ycsb_zipf_skew` / `ycsb_rmw` を**同一ファイルに**並べる。
凍結文書自身の positive control が
`output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50/campaign.lock` を
rratio=50 の conjunction hit として記録しており、これは実証済みの形である。
`output/exploration/` は `.gitignore` に無く、repo scan は untracked 非 ignore file も列挙する。

前 wave の敵対レンズは source / test / fixture / golden / docs までしか見ておらず、
**run 自身の生成物は射程外だった。未記録の新事実である。**

即時の赤にはならない (live の全 repo scan `launch_validate` は `RatifiedFreeze` を要求し
v2 未発効で到達不能)。しかし v2 発効時に起動を塞ぐ。

**択**: (a) 正式 run の run root / campaign root を repo 外へ強制する。
(b) 凍結の unknownness 主張を「凍結時点の歴史的記録」と明示し、事後 scan を要求しない。
(c) 明示的な exempt path を裁定する。**親の推奨 = (a)** (規律 6 の「指示に見える artifact を
未信頼入力側へ置かない」と同型の、生成物を検査空間へ置かないという構造的な解)。

### R-03 — oracle driver が freeze 文書から別 scale を読む

`s8b_oracle_driver._perf_for_holdout` は freeze **文書**から `PerfConfig` を作り、
module 表とも producer entry とも束縛されていない。schema-valid な `records=2_000_000` を
入れると通過する。`DW-G03` (族一般化には独立 2 例) は producer + oracle の 2 例で満たすが、
oracle は本 wave の編集面外であり、scope 拡張の裁定が要る。

## 4. 変異事前登録 (`DW-M01`)

実装後の最終 commit で anchor と期待 node を再検証してから本走する (`DW-M07`)。
本走は `--runner-mode dispatch`、runner argv に `--force-dispatch` を入れる。

| # | 位置 | 変異 | 単一理由性 |
|---|---|---|---|
| M1 | `p3_autonomous_workload_trial.py` `WORKLOADS` 定義 | 構造化 entry を wave 前の flat flags dict へ戻す (**wave 前の実コードの形**) | 前後に他層なし。entry schema テストだけが拒否 |
| M2 | `_campaign_for` の scale 射影 | entry 読取を wave 前の `"records": 100_000, "threads": 4` literal へ戻す (**wave 前の形**) | 探索では等価なので探索テストは緑のまま。正式 entry の三 sink 射影テストだけが赤 |
| M3 | `_perf_for` の scale 射影 | 同上 (**wave 前の形**) | 同上 |
| M4 | `_descriptor_for` の scale 射影 | 同上 (**wave 前の形**) | 同上 |
| M5 | Layer-3 `workload_flags = producer.WORKLOADS[workload]` | entry 全体を flags として扱う (台帳が予測した形) | 探索 cell 比較が赤 |
| M6 | Layer-3 `expected_search_values` の records/threads | entry 導出を wave 前の固定値へ戻す (**wave 前の形**) | 正式 entry の Layer-3 導出テストだけが赤 |
| M7 | 2.3 の descriptor scale 再投影検査 | 検査を削除 | 前後に他層なし (現状この検査は存在しない = 純増検出力) |
| M8 | 2.4 の四 key canonical 比較 | 比較を削除、または三者のうち 1 者を外す | 前後に他層なし |
| M9 | 2.4 の descriptor digest 束縛 | producer own digest と arm resolver 封印 digest の比較を削除 | 前後に他層なし |
| M10 | 2.5 の provenance 独立再導出 | consumer の再導出を三箇所 byte 同値比較へ弱める | A-04 / B-07 が指摘した形。同時改変で通ることを正例で示す |
| M11 | 2.7 の formal fail-closed | 正式 selector を素通しさせる | admission 側が別理由で落とす可能性あり → **両層変異まで裏取りする** (`DW-M02`) |
| M12 | producer source へ正式 read 比率 literal を追加 | repo scan invariant 変異 | `holdout_conjunction_hits` テストだけが赤。records/threads だけの追加は赤にしない (負の control) |

**正例 (受理集合を縮小する wave のため `DW-M01` が要求)**: 探索 3 workload の
既存 run が wave 後も Layer-3 を通ること、および合成 entry
(`records=123_457`, `threads=13`) を 3 sink へ渡すと 3 つともその値を出すこと
(出力側 hardcode を殺す正例)。

期待 node は probe 走行 (全件 SURVIVED 期待) で観測集合を集めてから完全集合として再登録する
(`DW-M08`)。

## 5. brief の訂正

- **DW-G05 の成果物影響を撤回・差し替え。** 誤: 「実装すると rr80/rr20 の実測が起動可能になる」。
  正: 「実装しても正式 run は起動できない (R-01)。本 wave が変えるのは、
  scale の権威が 1 か所になること、Layer-3 が descriptor scale を独立再投影するようになること
  (探索側で今日発火)、正式 profile と arm resolver の descriptor が同一を指すことが
  機械検査されるようになること」。
- **不変条件の訂正。** 「`test_frozen_artifacts.py` の pin は緑のまま」→「pin は **held**。
  land 前に両 path の非変更を親が直接実測する」。
- **(P2) の訂正。** 3 sink 内 literal は受理条件ではなく照合値とする (A-03)。
- **(P3) の訂正。** provenance は三箇所 byte 同値ではなく consumer 独立再導出 (A-04 / B-07)。
- **(P5) の撤回。** 正式 `pilot_scope` は導入しない (形 A)。
- **M4 の表現訂正。** 「同一 object 同一性が取れる」は `ycsb` 面にだけ成立する (A-06)。

## 6. 分割方針 (段 5)

一枚岩の 1 単位。entry 型と射影規約を producer / Layer-3 が共有するため、
所有を分けると型定義が競合する。実装は Codex `role=author`。
