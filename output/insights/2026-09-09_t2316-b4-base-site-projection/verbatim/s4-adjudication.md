# 段 4 裁定 — [T-2316] base の B4 launcher へ site 射影を入れる

親が段 2 プランと段 3 敵対相談 2 本 (A=正しさ境界レンズ、B=波及・整合レンズ) の所見を
real / refuted・採用 / 不採用・scope 内 / 外で裁定した結果。**これが実装の正本である。**

## 裁定 inbox の再走査

wave 開始 (`cbcdb6c91`) から段 4 時点まで local main は 0 commit 進行。取り込む更新なし。

## real・採用 (scope 内、実装に反映する)

- **A1 (最重要)**: プランの負例は `_driver_configs` を通らないため、修正の有無に感応しない。
  さらに既存 `test_production_validator_requires_exact_campaign_and_arm`
  (`orchestrator/tests/test_p3_b4_launcher.py:808-831`) が同じ拒否力を既に検査しており重複。
  → **負例を「機構を通る」形へ設計し直す。** 下の N1 / N5 が正本。
- **A2**: 3 node すべてが「marker だけ足して `ident.bind_environment_contract` を省く」変異を
  殺せない。`bound_environment_contract` は campaign ID の正準 preimage に入らない
  (`orchestrator/campaign/ident.py:196-218`) ため ID 比較では検出できない。
  → **返り値の `bound_environment_contract` を直接 pin する** (N2)。
- **A3**: registry spy で driver を差し替える正例は launcher 分岐の証明にはなるが、
  実物 driver 経路の証明にはならない。→ **両者を同一視せず、`_driver_configs` 直呼びの
  pin (N1) を独立に置く。** spy を使う node は「launcher 分岐の証明」とだけ書く。
- **A4**: ID 照合の棚卸しが不完全。`p3_s4_loop.py:2001-2003` の layout 再導出照合が抜けており、
  COMMIT 側の実物 G4 は `p3_b4_launcher.py:470-534` の `verify_launch_context` である
  (`:425-435` は起動前の sidecar 検査)。→ **実物の G4 を launcher が作った context で呼ぶ node
  を置く** (N3)。テスト自身の算術で ID を比べるのでなく、production コードに比べさせる。
- **B2**: プランの拒否 test は実現不能。`_production_launch_context`
  (`orchestrator/tests/test_p3_b4_closed_critic.py:148-150,170-177`) は渡された cfg を
  context 生成に使わず、実 launcher を呼んだ後に campaign ID を assert する。修正後は
  helper 内の assert が先に落ちるので、狙った `"campaign id differs"` に到達しない。
  → **未射影 production context を作る設計を捨てる。** N1 / N5 が機構感応性を担う。

## real・採用 (記録のみ、コード変更なし)

- **B1**: 親の「consumer 8 箇所」は occurrence 一覧であって call graph ではない。正しい inventory は
  直接呼び出し 3 箇所 (`test_p3_b4_closed_critic.py:185,532,2702`)、
  `_marked_driver_configs` 経由 4 箇所 (`:819,1002,1029,2322`)、
  production 本体 `p3_b4_launcher.py:547`、`launch_bootstrap` / `launch_continuation` 経由の
  多数の test caller。B が静的破綻なしと判定 (B5/B6 と整合)。段 7 の記録で訂正する。
- **B3**: `projection_closure_manifest` は driver 分岐より前に `p3_b4_launcher.py` を
  全 driver 共通で含む (`p3_b4_closed_critic.py:632-650`)。したがって launcher の 1 byte 変更で
  base・sort・trigger の `projection_sha256` がすべて変わる。「sort の**挙動**は不変」は正しいが
  「sort/trigger の **proof bytes** も不変」は誤り。ただし B7 の実測どおり、現時点で
  その 3 値を pin している凍結記録は存在しない (事前登録の該当欄は `未記入`、
  production admission record JSON も不在)。→ **更新すべき凍結成果物は無い。段 7 の記録に書く。**
- **B4**: brief の「OTHER では ID 不変」を D125 / D261 が要求する恒久保証として書いたのは誤り。
  D261 はその文を前向きに失効させている。OTHER の ID を変えないこと自体は
  (a) 本依頼が明示した禁止事項であり、(b) 親が実測した事実である。
  → **根拠の書き方を訂正する。恒久保証としては引かない。**

## real・scope 外 (実装せず裁定パッケージへ返す)

- **B11**: 公開 `p3_s4_loop.run_one_iteration` は「将来の直接 API caller」ではなく、
  現に `orchestrator/tests/test_p3_s4_loop.py:205,296,995,2921,4714,6482,6520,6582,6625` の
  9 箇所から直接呼ばれている。特に `:4695-4724` は B4 marker 付き config を公開関数へ渡す
  明示的な負例である。段 2 プランの「正式化された場合だけ」という説明は事実と異なる。
  ただし現存 caller は境界が拒否することを検査する負例であり、`p3_s4_loop.py` や
  授権境界を変更する理由にはならない。**実装しない。** scope 説明の訂正として段 7 で記録し、
  射影前境界を残すか否かはユーザー裁定へ返す候補とする。

## refuted (採らない)

- A5 (修正が不一致を移すだけ)、A6 (受理集合が不当に広がる)、A7 (新 fail-close の握りつぶし)、
  A8 (正例の赤理由と hostname seam の妥当性)、A9 (test-only context からの一般化)。
- B5 (既存 test が login hostname を拾って赤)、B6 (frozen ID/hash literal との衝突)、
  B7 (更新必須の凍結値の存在)、B8 (sort に等価の site 射影)、B9 (T-2317 未移植による新分裂)、
  B10 (import・受入台帳の追加 blocker)。
- A9 が「PEGASUS_SUSPECT は未実測」と正しく指摘したので親が実測して閉じた。結果は下記。

## 親の追加実測 (A9 を閉じる)

`_has_nqsv()` = True (実測)。site 4 値すべてで `p3_s4_loop._admit_env_contract` の挙動を測った。

```
hostname='pegasus-mystery' site=PEGASUS_SUSPECT -> RAISED ExecutionGuardError
hostname=None              site=PEGASUS_SUSPECT -> RAISED ExecutionGuardError
hostname='bnode116'        site=PEGASUS_COMPUTE -> contract.env_tag=pegasus
hostname='pegasus02'       site=PEGASUS_LOGIN   -> RAISED ExecutionGuardError
hostname='test-host'       site=OTHER           -> contract.env_tag=linux-baremetal
```

計測用 env bytes を作れない 2 site (LOGIN / SUSPECT) はどちらも fail-close する。
修正後 base の launcher はこの 2 site で新たに早期拒否するが、trigger は現にそう振る舞っており
安全側である (A7 refuted)。

## プラン v2 (実装の正本)

### 変更 1 — `orchestrator/campaign/p3_b4_launcher.py` の `_driver_configs`

`configs` を作った後の射影分岐を `if base / elif trigger` にする。base は `p3_s4_loop` の
`_current_site()` → `_admit_env_contract(site)` → `_campaign_cfg_for_site(cfg, site, _contract=contract)`
を trigger 分岐と同じ順・同じ形で呼ぶ。`sort` はどちらの分岐も通らない。
driver 種の一般 dispatch 表へ畳まない。

### 変更 2 — `orchestrator/tests/test_p3_b4_launcher.py` に node を足す

**N1 (機構感応の中核・PEGASUS_COMPUTE)**
`site_policy.socket` を `bnode116` へ差し替えた状態で `B4L._driver_configs("base", ctx)` を呼び、
返る on/off 両 config の `ident.campaign_id` が
(a) 未射影 `L.default_cfg(...)` の ID と**異なり**、
(b) `L._campaign_cfg_for_site(未射影cfg, PEGASUS_COMPUTE, _contract=...)` の ID と**一致する**
ことを pin する。base 分岐を消すと赤になる。

**N2 (contract bind・A2)**
同じ呼び出しの返り値について `bound_environment_contract` が解決済み contract と一致することを
PEGASUS_COMPUTE と OTHER の両方で pin する。marker だけ足す変異を殺す。

**N3 (実物の境界・A4)**
launcher が作った context を使い、**実物の** `require_b4_production_context` および
`verify_launch_context` (G4) を PEGASUS_COMPUTE 下で通す。test 自身の算術で ID を比べない。
registry spy を使う場合、その node は「launcher 分岐の証明」とだけ書き、
実物 driver 経路を覆ったとは書かない (A3)。

**N4 (OTHER 非回帰)**
site=OTHER で `_driver_configs("base", ctx)` の ID が未射影 `default_cfg` の ID と一致し、
`measurement_env` が付かないことを pin する。

**N5 (sort 不変)**
site=PEGASUS_COMPUTE で `_driver_configs("sort", ctx)` の ID が未射影 sort `default_cfg` の
ID と一致する (射影されない) ことを pin する。分岐を sort へ広げる変異を殺す。

**seam**: `site_policy.socket` を差し替える (最下層 resolver)。`classify_site` は `environ` を
明示的に捨てるので環境変数は seam ではない。`current_site` に site 注入引数は無い。
`conftest.py:239-255` の中立化は autouse・function scope で setup 時に効き、
test body の再差し替えが後から勝つ (A8 で確認済み)。

### 触らない面

`p3_s4_loop.py` / `p3_s4_loop_sort.py` / `p3_s4_loop_trigger_gating.py` / `site_policy.py` /
`ident.py` / `p3_b4_closed_critic.py` / `campaign_lock.py` / 事前登録 doc /
`orchestrator/tests/acceptance_duration_ledger.json`。既存 test の期待値も変えない。

## 変異事前登録 (DW-M01、実装前に登録)

| ID | 変異 | 位置 | 期待 | 単一理由性 |
|---|---|---|---|---|
| M1 | base 射影ブロックを削除する | `p3_b4_launcher.py` `_driver_configs` の base 分岐 | N1 と N3 が RED | 前後・内側に同じ入力を拒否する層は無い (A5/A6 で確認)。理由は launcher ID が未射影であること 1 つ |
| M2 | base 分岐で `_campaign_cfg_for_site` を使わず marker だけ足す | 同上 | N2 が RED、N1 は GREEN のまま | ID は marker で変わるので N1 は通る。落ちるのは contract bind の欠落だけ |
| M3 | 分岐条件を `driver_kind in {"base", "sort"}` へ広げる | 同上 | N5 が RED | sort の ID 変化だけが理由 |
| M4 | `p3_s4_loop._current_site()` を literal `site_policy.OTHER` に置き換える | 同上 | N1 が RED (N2 も RED) | 複数 node が赤になるが原因は「site を解決していない」1 つ |

**等価変異クラス (gate に登録しない)**: base 分岐の helper を
`p3_s4_loop_trigger_gating._campaign_cfg_for_site` へ差し替える変異は、両実装が同一のため
SURVIVED が期待値である。gate として登録せず、等価クラスとして台帳に記録する。

## 不変条件 (緩めない)

- 規律 2: `require_b4_production_context` / `validate_production_context` / `require_any_context` の
  拒否力を弱めない。campaign ID の一致要求はそのまま。
- `_site_admits_measurement` の exact set を広げない。
- OTHER の campaign_id を変えない。
- `sort` の挙動を 1 bit も変えない。
- 既存 test の期待値を変えない。反転・緩和・skip・削除を禁じる。
