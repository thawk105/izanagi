# 段 4 裁定 — [T-2356] 段 4 loop の事前構築成果を driver が消費する seam

段 2 plan と段 3 敵対相談 2 本 (lens A = 到達性、lens B = 受理集合と scope) の所見を
real/refuted・採用/不採用・scope 内/外で裁定し、プラン v2 を確定する。

## 段 4 直前の再走査

- local main は wave 開始時の `f486ff13c` から `b2f92aebe` へ進んだ。差分は worklog fold、
  archive、T-2266 の insight、`tools/t2216_backoff_walk_model.py` とその test で、
  **本 wave の編集面 7 file とは 1 file も重ならない** (実測)。
- 裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) に wave 開始 (2026-09-07 10:2x) 以降の
  追加は無い (最新は 2026-09-05)。
- 承認済み裁定 (D1679 / D1524 / D1689 / D1690) の前提を覆す新事実は出ていない。

## 親が現物で裏取りした事実

以下は子の主張をそのまま採らず、親が repo の現物を読んで確認した。

1. `buildcache.py:2801-2807` — `dependency_receipt` を渡した build では実効 masstree source root が
   `os.path.join(canonical_fetchcontent_base, "masstree-src")` と exact 一致することを要求し、
   不一致は `BuildCacheError`。**現状の job body の配置 (`prebuild-sources/masstree` +
   別 `fetchcontent-base`) では必ず拒否される。**
2. `test_p3_s4_loop_job_contract.py:251-259` — `prebuild-{masstree,mimalloc,googletest}-copy-root` が
   `$prebuild_source_root/<name>` を literal で pin している。`-src` 改名で赤になる。
3. 同 `:293-297` — driver 起動行の pin は substring 照合であり、**option を 1 本挿入しても赤にならない**
   (pin の穴)。
4. `loop.py:527-531` — terminal な variant は `evaluate` より前に `skipped` として飛ばされる。
5. `loop.py:602-624` — `evaluate` の例外は広い `except Exception` に捕まり `eval-exception` の
   abort レコードになる。**引数の配線欠落もここで variant の terminal 化に化ける。**
6. `pipeline.evaluate` の docstring と `pipeline.py:1224-1289` — `env_contract` 未指定の caller は
   FetchContent 引数を持たない legacy `buildcache.build` に落ちる。

## 所見の裁定

### 採用 (real、scope 内)

| # | 所見 | 出所 | 成果物影響 (DW-G05) |
|---|---|---|---|
| C1 | job body の source 配置を `<base>/<name>-src` へ揃え、`fetchcontent_base_dir=$prebuild_source_root` にする | plan | これが無いと build が `BuildCacheError` で必ず落ち、段 4 loop の実走が 1 件も成立しない |
| C2 | 5 本の all-or-nothing + `env_contract` 必須検査を `run_campaign` 冒頭 (副作用の前) にも置く | lens A / lens B | 配線欠落時に WAL へ terminal abort が焼かれ、訂正後の走行が duplicate skip されて **古い abort が certified 判定の材料になる** |
| C3 | receipt file 自体を non-symlink regular file として開く | lens A | 別 file を指す symlink 経由で、job が書いたのでない依存が build に入る |
| C4 | receipt reader の負例を 5 種そろえる (config hash 不一致 / exact key 集合違反 / source 名の重複・欠落 / noncanonical・symlink path / 型不正) | lens B | reader を素通しした不整合 receipt が configure argv へ入り、記録と実体が食い違う |
| C5 | fixture 分岐と proposal 分岐の **両方**に production positive を置く | lens B | 片方の `main` 受け渡しが落ちても緑になり、seam が半分死ぬ |
| C6 | presence 判定は base が `bool(base)`、source dir と receipt が `is not None` | lens B | 既定 `""` を「指定あり」と数える実装が通り、既定経路の argv が変わる |
| C7 | 契約テストへ copy destination の required fragment と復帰変異を足す | lens B | 変数名だけ `-src` にして実体は旧 dir へコピーする実装が全 fragment を満たして通る |
| C8 | 契約テストの driver 起動 pin を、receipt option と後続 option の**連続** fragment に補強する | plan / 親の実測 | 現行 pin は option 挿入を検出できない (穴) |
| C9 | 生死確認は production `_v2_commands` を wrap し、**捕捉した argv を直接 assert** する。sentinel の伝播や driver の rc に依存しない。fresh / non-terminal candidate を保証する | lens A | sentinel は `pipeline` の `build-error` abort に吸収され、duplicate だと wrapper が 1 度も呼ばれないため、確認になっていない probe になる |
| C10 | `tools/pegasus/README.md` §7 と `docs/pegasus-runbook.md` §7.0 の「seam が無い / 消費配線は後続 wave」の記述を同じ commit で更新する | lens B | 実装後も台帳が「seam は無い」と表示し、一次資料が実体と食い違う |

### real だが scope 外 (実装しない、裁定パッケージへ返す)

| # | 所見 | 理由 |
|---|---|---|
| R1 | **既 terminal な variant は receipt を渡しても duplicate skip され、prebuild が消費されない。** 同じ REPO_ROOT で同じ fixture 値の job を 2 度流すと 2 度目は build へ到達しない (`loop.py:527-531`) | 塞ぐには campaign identity へ receipt transport を足すか、duplicate の意味論を変えるしかない。**どちらも受理集合と identity を動かす変更**であり、D1679 の「局所修正で閉じる」を超える。本 wave では (a) 現行挙動を pin する test、(b) insight の保証範囲への明記、(c) runbook への運用注記 1 行で可視化し、実装はユーザー裁定へ返す |
| R2 | receipt の `pbs_jobid` 非空検査は別 job の receipt を拒否しない (正規 producer に対して恒真) | D1679 が見送った「bytes 級 provenance」の側。job 束縛を主張しないことを明記して閉じる。`PBS_JOBID` との一致を要求すると login node の生死確認が成立しなくなる副作用もある |
| R3 | cache hit 時に記録される configure argv は、その binary を実際に作った過去の argv と異なりうる。base/source の path と mimalloc・googletest の内容は build identity に入らない | **D1690 が「本 wave では是正しない」と裁定済み。** insight の保証範囲へ書く |

### refuted (採らない)

| # | 所見 | 判定 |
|---|---|---|
| F1 | 「optional 引数を足すので Python の公開 signature は 1-bit 不変ではない」(lens A) | 不変条件の読み方が違う。brief の「既定経路を変えない」は**既存 caller の呼出し式と下流 kwargs・argv・cache key**を指す。signature への optional 追加は `dependency_prefix` などの先例どおり |
| F2 | duplicate skip / abort でも driver が rc=0 を返しうる (lens A) | 本 wave が導入する挙動ではなく、driver の既存 rc 規約。R1 の可視化で足り、rc 規約の変更は別件 |

## プラン v2 (確定)

1. **job body** (`tools/pegasus/p3_s4_loop_pegasus.sh`)
   - `fetchcontent_base_dir=$prebuild_source_root` とし、`destination=$prebuild_source_root/${source_name}-src`、
     `masstree_source_dir=$prebuild_source_root/masstree-src` ほか 2 本を同じ形にする (C1)。
   - fresh 検査 (`config.h` 不在) と receipt の create-only はそのまま。
   - driver 起動の 2 分岐に `--fetchcontent-prebuild-receipt "$prebuild_receipt"` を足す。
   - qsub の `-v` と required env は変えない。
2. **driver** (`orchestrator/campaign/p3_s4_loop.py`)
   - receipt loader を 1 本追加。**non-symlink regular file として開き** (C3)、top-level を
     現 producer が書く 10 field の exact 集合として検査し、`schema_version` を exact 照合、
     `fetchcontent_base_dir` と `source_root` の canonical・非 symlink・equality、
     `config_h_path` が `source_root/masstree-src/config.h` と一致すること、
     `config_h_sha256` を現物 bytes から**再計算して照合**すること、`sources` が
     `{masstree, mimalloc, googletest}` の exact 集合で `head_commit` が lowercase 40 hex であることを要求する。
     **5 値 (base / source dir 3 本 / 2 key receipt) を原子的に返すか、例外を投げるかのどちらかにする。**
   - `pbs_jobid` は非空 str の schema 検査だけ。**job 束縛は主張しない** (R2)。
   - CLI は `--fetchcontent-prebuild-receipt PATH` の 1 本。`--no-build` / `--emit-planner-context`
     との併用は **build 経路へ入る前に** rc=2 で拒否する。
   - 5 値は `_run_one_iteration_resolved` と `drive_iteration` の両方へ通し、**receipt があれば
     site に依らず `env_contract` と 5 値を `campaign_options` へ入れる**。既存の
     `dependency_prefix` の site 条件は変えない。
3. **`loop.run_campaign`** — 5 個の optional keyword-only 引数を追加。**関数冒頭 (authorization /
   layout / WAL recovery より前) に all-or-nothing + `env_contract` 必須の検査**を置く (C2)。
   非既定時だけ `evaluate_options` へ足す。presence 判定は C6 の形。
4. **`pipeline.evaluate` / `_prepare_evaluation_core`** — 5 引数を受け、build/WAL より前に
   同じ all-or-nothing を検査し、非既定時だけ `common` へ入れて `buildcache.build_v2` へ渡す。
5. **`buildcache.py` は変更しない。**
6. **テスト** — C4〜C9 のとおり。加えて既定互換 spy (未指定時に `evaluate_options` /
   `common` / `build_v2` kwargs へ新 key が 1 つも現れない) と、R1 の現行挙動 pin。
7. **docs** — C10 (親が書く)。

## gate の禁止 (署名) と通る正例

**禁止 1 (C2):** `run_campaign(..., fetchcontent_base_dir=<非空>, masstree_source_dir=<path>,
mimalloc_source_dir=<path>, googletest_source_dir=<path>, fetchcontent_dependency_receipt=None)`
→ 関数冒頭で `ValueError`。authorization contract の解決、layout の作成、WAL recovery、
source identity の解決を **1 つも行わない**。

**禁止 2 (C2):** 上記 5 本がそろっていて `env_contract=None` → 同じく関数冒頭で `ValueError`。

**禁止 3 (driver):** `--fetchcontent-prebuild-receipt PATH` と `--no-build` の併用、
`--fetchcontent-prebuild-receipt PATH` と `--emit-planner-context PATH` の併用 → rc=2。

**通る正例:** `run_campaign(..., env_contract=<contract>, fetchcontent_base_dir="<canonical base>",
masstree_source_dir="<base>/masstree-src", mimalloc_source_dir="<base>/mimalloc-src",
googletest_source_dir="<base>/googletest-src",
fetchcontent_dependency_receipt={"masstree_head": "<40 hex>", "config_sha256": "<64 hex>"})`
→ production `buildcache.build_v2` が exact 同値の 5 kwargs を受け取り、
`_v2_commands` の configure argv に `-DFETCHCONTENT_BASE_DIR=` と
`-DFETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}=` が各 1 本入る。

**通る正例 (既定経路):** 上記 5 本すべて未指定の既存 caller → `evaluate_options`、`common`、
`build_v2` kwargs のいずれにも新 key が現れず、configure argv も cache key も従来どおり。

## 変異事前登録 (DW-M01)

実装前に登録する。期待 node は段 6 の probe (DW-M07) で実測して確定する。
各変異は「同じ入力を拒否する層が前後にも内側にも無い」ことを実装後に確認する。

| ID | 位置 | 変異 | 単一理由で殺す検査 |
|---|---|---|---|
| M1 | job body の copy loop | `destination=$prebuild_source_root/${source_name}-src` を `${source_name}` へ戻す | 契約テストの copy destination fragment |
| M2 | job body | `fetchcontent_base_dir=$prebuild_source_root` を別 root へ戻す | 契約テストの base equality fragment |
| M3 | job body の proposal 分岐 | `--fetchcontent-prebuild-receipt` 行を削除 | proposal 分岐の連続 fragment |
| M4 | job body の fixture 分岐 | 同上 | fixture 分岐の連続 fragment |
| M5 | driver の receipt loader | `config_h_sha256` の再計算照合を削除 | reader 負例 (hash 不一致) |
| M6 | driver の receipt loader | top-level の exact key 集合検査を「必須 key の包含」へ緩める | reader 負例 (未知 key) |
| M7 | driver の receipt loader | receipt file の non-symlink 検査を削除 | reader 負例 (symlink receipt) |
| M8 | driver の `campaign_options` | receipt 指定時の `env_contract` 注入を Pegasus 分岐内へ戻す | OTHER site での production `build_v2` 正例 |
| M9 | driver の CLI 検査 | `--no-build` との併用拒否を削除 | 組合せ拒否の負例 |
| M10 | `loop.run_campaign` 冒頭 | all-or-nothing 検査を削除 | loop-level 負例 (partial 入力で layout / WAL / authorization が作られないこと) |
| M11 | `loop.run_campaign` | 5 値を `evaluate_options` へ入れる行を削除 | production `build_v2` kwargs の正例 |
| M12 | `pipeline` の `common` 構築 | 5 値を入れる行を削除 | 同上 |
| M13 | `pipeline` の検査 | all-or-nothing (`env_contract` 必須を含む) を削除 | D1689 の負例 (base + source 3 本、receipt なし) |
| M14 | presence 判定 | 未指定時にも新 key を下流 kwargs へ出す | 既定互換 spy |

## 生死確認 (DW-G01) の形

login node で production 経路を通す probe を 1 本。100 行以内。

1. 一時 root に third-party 3 本を `<root>/<name>-src` で用意し、同じ root を base として
   production `buildcache.prepare_masstree_fetchcontent` を 1 度実行する。
2. job body と同じ schema の receipt を書く。
3. production `buildcache._v2_commands` を wrap し、**元関数を実行して configure argv を保存**した
   直後に sentinel を投げる (configure subprocess より前で止める)。
4. production `p3_s4_loop.main` を `--fetchcontent-prebuild-receipt` と fixture `--value` で呼ぶ。
   **fresh な campaign layout と non-terminal な candidate を保証する** (C9 / R1)。
5. sentinel の伝播や rc ではなく、**保存した argv** に 4 つの define が各 1 本あることを assert する。

この probe は「production `_v2_commands` の argv まで 5 値が届く」ことを反証しうる。
実 Pegasus site での挙動、configure 後に CMake が事前構築物を実際に再利用すること、
別 job receipt の拒否は反証しない (保証範囲へ明記する)。
