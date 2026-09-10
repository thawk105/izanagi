# 段 4 裁定とプラン v2 — 軸 driver の環境定数を env_contract 解決へ寄せる

入力は `s1-brief.md`、`s1-brief-addendum.md`、段 2 プラン
(`.../axis-env-contract-jobs/s2-plan/output.md`)、段 3 レンズ A
(`.../s3-barrier/output.md`) とレンズ B (`.../s3-reach/output.md`)。
両レンズとも **NO-GO**。段 2 案はそのままでは実装しない。

## 0. 親の provisional 裁定の最終処理

| # | 内容 | 裁定 |
|---|---|---|
| P1 | site_policy を seam にした非対称 guard で足りる | **限定採用**。「machine pin」とは称さず「認識済み Pegasus の deny guard」と限定して実装・記録する |
| P2 | env 選択 CLI を足さない | **採用**。ただし「これで env 混在問題が閉じる」という含意は**撤回**する (下記 U1) |
| P3 | reject 経路は計測しないので guard 対象外 | **棄却**。親が段 2 起動後に自己反証し、両レンズが BLOCKER として独立確認した |
| P4 | `p3_s4_loop.py` の `env_tag` 既定は scope 外 | **採用**。target は 3 箇所すべて明示渡しで基底既定に依存しない |

## 1. 所見の real / refuted と採否

### 採用する must-fix (scope 内)

- **A1 / B1 [BLOCKER] real・採用** — guard が env_tag 付き永続化より遅い。
  Pegasus 計算ノードで禁止識別子入り proposal を `do_build=False` で渡すと、
  `record_diff_reject` が `build_start` / `abort` の 2 行を `env_tag="linux-baremetal"` で
  WAL へ書いてから return し、`run_campaign` 直前の guard には到達しない。
  *成果物影響*: 台帳が偽タグで汚染され、`layer3_report` の env 検査は
  **一意性しか見ない** (`env_tags` 集合の要素数 != 1 で拒否) ため、全件が同じ偽タグなら素通りする。
- **B2 [BLOCKER] real・採用** — A1 を直すと既存 2 テストが受入環境依存で赤になる。
  段 2 案は `site` を `run_one_iteration` にしか通さないが、既存テストは `drive_iteration` を呼ぶ。
  *成果物影響*: 穴を残すか受入を壊すかの二択のまま実装すると、どちらでも成果物の env 整合が守られない。
- **A2 / B5 [HIGH] real・採用 (限定)** — 提案 guard は env/site の整合検査ではなく迂回可能な denylist。
  *成果物影響*: 保証名を過大に記録すると、後続 wave が「偽タグは塞がれた」と誤って前提にする。
- **A4 / B3 / B4 [HIGH] real・採用** — テスト計画が late-guard 変異を kill せず、
  positive control が「contract 由来であること」を固定しない。
  linux-baremetal の契約値が現行ハードコードと同値であるため、
  「lookup を呼んで結果を捨て literal を渡す」変異が緑のまま生き残る。
  *成果物影響*: contract 再校正が driver に届かないという本 wave の主故障をテストが守らない。
- **A5 [MEDIUM] real・採用** — 「完全一致」「拒否を足すだけ」は不正確。
  registry は tuple、driver の launch 面は list。`CLK` / `NUMA` の module attribute 削除は
  公開面の縮小であって拒否の追加ではない。
  *成果物影響*: 記録の正確性の問題であり、値そのものは変わらない。
- **A6 [MEDIUM] real・採用** — module-level lookup は S1 driver・test collection・CLI `--help` まで
  巻き添えにする。遅延解決を採る (段 2 案どおり)。親 brief の「一関数しか使わないから影響なし」は撤回。
- **A8 / B8 [MEDIUM] real・採用 (追補の訂正)** — 追補 A7 の言い換え。
  `run_cmd` は要求した argv を正しく記録する。誤るのは
  **その argv が物理機に適した contract か**と**env_tag が物理環境を表すか**である。
- **A9 / B7 [nit] real・訂正済み** — baseline は `bnode002` (訂正を追補へ記録済み)。
- **B10 [nit] real・採用** — 歴史 campaign identity の恒久テストは削り、実装後の一回限り静的確認にする。

### scope 外 (実装しない。裁定パッケージでユーザーへ返す)

- **A3 [HIGH] real・scope 外 → U1** — campaign identity と WAL replay が env 非依存。
- **A7 / B6 [HIGH] real・scope 外 → U2** — guard の到達範囲は target driver の正規 entrypoint だけ。
- **A2 の完全版 [HIGH] real・scope 外 → U3** — linux-baremetal の正の machine attestation。
- pegasus を本軸の runnable env にすること — **scope 外 → U4** (brief どおり)。

### refuted / 不採用

- **B9 [MEDIUM] 部分 refuted** — 「2 ファイルで閉じる」は成立させる。
  中央閉包 (`test_env_contract.py` の `V2_ENV_NEUTRAL_MODULES`) へ target を足すと 3 ファイル目になり、
  かつ本 wave が残す `ENV_TAG` literal を禁止してしまう。**中央閉包へは足さない**。
  literal scan は target 自身のテストから `env_contract.find_env_literals` を呼ぶ target-local 形とする。
  受入集合には `test_site_policy.py` を追加する (B9 の受入側指摘は採用)。
- **A10 [nit] refuted されず・確認のみ** — 凍結・pin 閉包にプラン内の違反なし。
  `env_contract.py` を編集しない限りこの判定は有効。実装子が同ファイルへ触れたら判定は失効する。

## 2. プラン v2 (実装する形)

### 2.1 admission funnel — env_tag を得る唯一の経路

`ENV_TAG` は module 定数として残す。`CLK` / `NUMA` の module attribute は削除する。
新設するのは次の 4 要素で、**site 実測と contract 解決を不可分にする**のが要点である。

- `_current_site` — module 属性。既定は `site_policy.current_site`。**テスト seam はここだけ**。
- `_lookup` — module 属性。既定は `env_contract.lookup`。sentinel contract 注入用の seam。
- `_site_admits_measurement(site) -> bool` — 純関数。`site == site_policy.OTHER` のときだけ True。
- `_admit_env_contract() -> ExecutionEnvironmentContract` — `_current_site()` を実測し、
  admit しなければ `execution_guard.ExecutionGuardError` を送出、admit すれば `_lookup(ENV_TAG)` を返す。

**production に caller override を作らない** (レンズ A の指摘)。`site` を関数引数にも CLI にも出さない。
テストからの注入は module 属性 `_current_site` の差し替えで行う。これは本テストファイルが既に
`monkeypatch.setattr(T, "INFORMATION_SOURCES", ())` で使っている同型の seam であり、
外部モジュールへの monkeypatch ではない (`DW-O14` の最後の手段に当たらない)。

これによりレンズ A の「引数で迂回できる」とレンズ B の「テストから注入できない」が同時に解ける。

### 2.2 admission の設置点

env_tag を持つ bytes が永続化される境界だけに置く。**`run_one_iteration` 冒頭の無条件拒否は採らない**
(clean な `do_build=False` は env bytes を書かないため、受理集合を余計に縮めない — レンズ A の最小修正案)。

- 現行 `:288` / `:296` / `:307` の 3 つの `L.record_diff_reject(...)` 呼出しを、driver 内の単一 helper
  `_record_diff_reject_admitted(...)` へ集約する。helper は `_admit_env_contract()` の戻り値の
  `contract.env_tag` を `L.record_diff_reject` へ渡す。
- 現行 `:388` の `run_campaign(...)` 直前で同じ `_admit_env_contract()` を呼び、
  `contract.env_tag` / `contract.clocks_per_us` / `list(contract.numactl)` を渡す。

結果として admission 点は 2 つだけになり、**`ENV_TAG` から env_tag を得る経路が admission を通らずには存在しない**。

### 2.3 `site` の貫通は行わない

段 2 案と レンズ B が求めた `drive_iteration(..., site=None)` → `run_one_iteration(..., site=site)` の
引数貫通は**採らない** (2.1 の理由)。既存 2 テストと `_quarantine_and_audit` 直呼びテストは
`monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)` で環境宣言する。

### 2.4 テスト設計 (target のテストファイル 1 本だけを編集)

- **sentinel flow (positive control の本体)** — `_lookup` を、registry のどの値とも異なる
  sentinel contract (例 `env_tag="sentinel-env"`, `clocks_per_us=4242`,
  `numactl=("numactl","--sentinel")`) を返す関数へ差し替え、`run_campaign` spy が
  受けた 3 実引数が sentinel と一致することを固定する。
  これが「値が 1800 か」ではなく「**contract 由来か**」を固定する唯一のテストである。
- **empty-numactl sentinel** — `numactl=()` の sentinel で `run_campaign` が `[]` を受けることを固定する
  (「解決済みで prefix なし」を `["numactl"]` へ誤展開する変異を kill する)。
- **lookup 失敗の伝播** — `_lookup` が `EnvContractError` を投げる sentinel で、
  同一例外が伝播し `run_campaign` 未到達かつ WAL 0 行であることを固定する。
- **reject sink の負例** — `_current_site` を `PEGASUS_COMPUTE` にし、禁止識別子入り proposal を
  `do_build=False` で通して `ExecutionGuardError` かつ **WAL 0 行**を固定する。
- **reject sink の正例** — `_current_site` を `OTHER` にし、同じ proposal で
  WAL が従来どおり 2 行書かれ `env_tag` が `ENV_TAG` であることを固定する (過剰拒否検出)。
- **site matrix (純関数)** — `OTHER` は True、`PEGASUS_LOGIN` / `PEGASUS_COMPUTE` / `PEGASUS_SUSPECT` は False。
- **production の `site=None` 分岐** — `_current_site` が既定で `site_policy.current_site` に束縛されていることを固定する。
- **clean dry-pass の受理** — Pegasus site でも clean な `do_build=False` は admission を通らず
  従来どおり `dry-pass` を返すことを固定する (受理集合を縮めていない証拠)。
- **target-local literal scan (補助)** — `env_contract.find_env_literals(driver_source, {1800, "--interleave=all"})`
  が空であることを固定する。`18 * 100` や文字列連結は検出外なので**補助**であり、
  主たる検出力は sentinel flow が担う。
- **既存テストへの追加は行わない方針の例外** — 既存 2 drive テストと `_quarantine_and_audit` 直呼び
  テストには `_current_site` の環境宣言だけを足す。期待値は緩めない。
- **削除** — 段 2 案 5 の歴史 campaign identity 恒久テストは作らない (B10)。

### 2.5 受入集合

`test_p3_s4_loop_trigger_gating.py`、`test_p3_s4_loop.py`、`test_env_contract.py`、
`test_site_policy.py`、`test_s1_direct_comparison.py`、`test_campaign.py`。
最終受入は全走。すべて Pegasus 計算ノードへ dispatch する。

### 2.6 所有と非回帰

編集は `orchestrator/campaign/p3_s4_loop_trigger_gating.py` と
`orchestrator/tests/test_p3_s4_loop_trigger_gating.py` の 2 ファイルだけ。
`env_contract.py` / `site_policy.py` / `execution_guard.py` / `p3_s4_loop.py` は編集しない。
`default_cfg()` は変更しないので `campaign_id` と `campaign.lock` の正準 pre-image は不変。

## 3. 変異事前登録 (`DW-M01`)

実装子は各変異について「その位置より前に同じ入力を拒否する検査がないこと」と
「無効化時の赤理由が一つに絞れること」をコードで確認し、確認できないものは登録しないで報告する。
親は段 6 で anchor を再検証する (`DW-M07`)。

| ID | 変異 | 期待 kill |
|---|---|---|
| M1 | reject helper から admission を外し `ENV_TAG` を直接渡す | reject 負例 (Pegasus site で WAL 0 行) |
| M2 | `_site_admits_measurement` を常に True (allow-all) | site matrix + reject 負例 + 計測負例 |
| M3 | `_site_admits_measurement` が `OTHER` も False (過剰拒否) | reject 正例 + clean dry-pass 受理 |
| M4 | `_admit_env_contract` が `_lookup` 結果を捨てて現行 literal の contract を返す | sentinel flow |
| M5 | 空 `numactl` を `["numactl"]` へ展開 | empty-numactl sentinel |
| M6 | `_admit_env_contract` が `EnvContractError` を握り潰して既定へ fallback | lookup 失敗伝播 |
| M7 | `run_campaign` 前の admission だけを外す | 計測負例 |
| M8 | `_current_site` の既定束縛を固定値 `OTHER` へ差し替え | production 束縛テスト |

受理集合を縮小する wave なので、過剰拒否を検出する正例 (M3 の kill 元) を必ず含める。

## 4. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

- **U1 — campaign identity と WAL replay が env 非依存**。`campaign_id` は
  `(spec_slug, search_tag, cfg_hash8)` だけ、`campaign.lock` の正準 pre-image にも env_tag はない。
  `docs/orchestrator-design.md` の「env は campaign 同一性に含めない」節は env を
  **読み出しフィルタ**と規定するが、`run_campaign` / `wal.replay` にそのフィルタは実装されていない。
  さらに `layer3_report` は「env_tag が一意でなければ拒否」であり、規定の「1 campaign に複数 env が
  正当に併存し射影時にフィルタする」と食い違う。
  *放置した場合の成果物影響*: 別 env の COMMIT による誤スキップ、critic 入力の混在、
  誤った certified 選択、同一タグに偽装された材料レポート。
- **U2 — 同型の穴が兄弟 driver と共通経路に残る**。`p3_s4_loop.py` / `p3_s4_loop_sort.py` /
  `s8a_trigger_sweep.py` ほか、repo 内の `run_campaign` caller と `screening_driver` の
  直接 `pipeline.evaluate`。admission を `loop.run_campaign` 側へ置く設計にすれば一括で塞げるが、
  報告済み・凍結済みの計測条件に触れるため独立裁定が要る。
  *放置した場合の成果物影響*: 本 wave 後も別 driver から同じ偽タグ WAL を作れる。
- **U3 — linux-baremetal の正の machine attestation が無い**。`site_policy` は Pegasus を否定できるが
  cygnus を積極同定できない。`pegasus02` でも `qsub`/`qstat` が PATH に無ければ `OTHER` になる。
  *放置した場合の成果物影響*: 未知の第三の機械での実行は検出できない。
- **U4 — pegasus を本軸の runnable env にする**。D59 の 4 条件、env スコープ付き campaign identity、
  attestation、isolation、noise floor 配線が要る。

## 5. 本 wave が主張してよい保証 (過大表現の防止)

「軸 driver 群の env integrity を確保した」とは**称さない**。

**erratum (段 6 レビュー C の所見 R9 により訂正)**: 本節の初版は
「環境定数が単一正本になり、認識済み Pegasus site では fail-closed で停止する」と書き、
§2.1 では「production に caller override を作らない」と書いていた。これは過大である。
レビュー C の計数によれば、関数引数 0 / CLI 0 だが、**環境変数由来が 1**
(`PATH` — `pegasus0N` で `qsub`/`qstat` を隠すと `OTHER` に落ちる) あり、
明示された module 面が 3 (`_current_site`、`_lookup`、可変な `ENV_TAG`) ある。
同一 process 内のコード書換えまで脅威モデルに含めれば、有限の「override ゼロ」保証は成立しない。
正しい表現は「**関数引数と CLI に supported な override はない**」である。

称してよいのは次だけである (レビュー C 提示の精密版を採用)。

> 未改変の `p3_s4_loop_trigger_gating.run_one_iteration` を通る正規経路では、
> reject WAL の `env_tag` と `run_campaign` の `env_tag` / `clocks_per_us` / `numactl` が
> `_lookup(ENV_TAG)` の返値から供給される。`site_policy.current_site()` が既知 Pegasus 状態を
> 返す場合、それら sink の前で停止する。既存 WAL の env 射影、正の machine attestation、
> 同一 process の module 書換え、兄弟 driver は保証しない。

## 6. 段 6 以降の訂正へのポインタ

本文書は段 4 時点の裁定である。段 6 レビュー C / D が出した must-fix と
変異事前登録の erratum (M7 / M8 の帰属不成立、M3 の kill 元誤り) は
同 dir の `s6-review-adjudication.md` が正本である。
