## 総括

**must-fix 2 件。現状のままでは、hydrate 済みでも silo と T-126 の標準経路が止まります。**

- silo：scratch にコピーするのは 3 依存だけなのに、gflags/glog も同じ scratch から解決する。
- T-126：submit helper の一時展開先を repo root と誤認し、存在しない staging を読む。

加えて、Mocc の hydrate 順序と既存の F88 該当箇所を指摘します。37 file の差分全文と現物を静的に確認しました。編集・commit・テスト実行はしていません。以下の相対パスはすべて指定 worktree 内です。

## 1. 既定 path の一致

**文字列不一致の攻撃：不成立／重大度 nit。** 正本は `orchestrator/campaign/silo_ladder_rung1.py:68`。14 本の既定相対パスは、次の文字列と完全一致します。

`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src`

| job（`tools/pegasus/` 配下） | root の定義行 | source root の解決行 |
|---|---:|---:|
| `a5_second_boot_backoff_sweep.sh` | 233：`REPO_BASE`＝PBS 作業 checkout | 514 |
| `b10_backoff_grid.sh` | 239：`REPO_ROOT`＝PBS 作業 checkout | 513 |
| `certify_calibration.sh` | 46：同上 | 155 |
| `floor_campaign.sh` | 46：同上 | 529 |
| `floor_scoping.sh` | 28：同上 | 188 |
| `mocc_trace_pilot.sh` | 53：同上 | 893 |
| `oracle_n_pilot.sh` | 81：同上 | 215 |
| `paper_story_a1_paired.sh` | 127：同上 | 1218 |
| `silo_ladder_rung1.sh` | 66：同上 | 443 |
| `t126_qualification.sh` | 56：同上 | 560 |
| `t141_region_profile.sh` | 371・376：指定 `IZANAGI_ROOT` の実パス | 412 |
| `probes/t1683_rr5_cost_probe.pbs` | 30：PBS 作業 checkout | 80 |
| `probes/t2187_adaptive_const_probe.pbs` | 87：同上 | 441 |
| `probes/t2228_driver_gate_liveness_probe.pbs` | 38：同上 | 160 |
| `p3_s4_loop_pegasus.sh` | 109：指定専用 checkout | 399：専用 env、既定値なし |

成果物への影響：**文字列誤記や root 変数そのものの scratch 化による参照変更は確認できませんでした。**

**B1：silo の実効 root は 3 依存だけの scratch。成立／must-fix。**

根拠：`tools/pegasus/silo_ladder_rung1.sh:348` は `third_party_policy()` の 3 本だけを列挙し、`:376` でコピー、`:383` で `IZANAGI_THIRDPARTY_SOURCE_ROOT` をその scratch へ上書きします。変更箇所の [silo_ladder_rung1.sh:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t548-versioned-dep-procurement/tools/pegasus/silo_ladder_rung1.sh:443) はこの env を優先するため、`:466` の `git -C "$dep_source"` は存在しない scratch/gflags を参照します。

永続 staging に 5 本 hydrate しても、このコピー処理が 2 本を落とすため失敗します。submit 側も `submit_silo_ladder_rung1.sh:157`・`:165` で 3 本しか準備しません。

成果物への影響：**正常な調達入力でも rung1 の新規走行が dependency stage で失敗し、成功 evidence を追加できません。**

是正：共通調達の 5 本が job の実効 source root まで届くよう、submit・scratch 引渡しを接続する必要があります。FetchContent 専用の 3 本集合を無条件に 5 本へ変更する是正ではありません。

## 2. hydrate の書き先

**書き先不一致の攻撃：不成立／nit。**

根拠：`tools/pegasus/fetch_third_party.py:67` が gflags/glog の `source_name` を各名称に固定し、`:729` で既存 3 本へ結合、`:646` で `staging_root / source_name`、`:670` で公開します。従って `<staging-root>/gflags` と `<staging-root>/glog` に届きます。

既定値は同 file `:150` の `repo_root / staging_relative`。`--staging-root` 指定時はその絶対パスです。consumer 用 env の設定だけでは hydrate の書き先は変わりません。

成果物への影響：**hydrate 自体の配置ミスによる材料参照の破損は確認できませんでした。**

## 3. p3_s4 の入口

**3 本だけの root を渡す現行手順という攻撃：不成立／nit。**

根拠：`tools/pegasus/README.md:374` は §6 の hydrate 出力 `.source_root` を要求し、`:391` で `IZANAGI_S4_THIRDPARTY_SOURCE_ROOT` に渡します。job の `p3_s4_loop_pegasus.sh:399` はその root の gflags/glog を直接使用します。

`:471` の scratch コピーは 3 本ですが、これは後段の FetchContent 用です。silo と違い、gflags/glog の source root をこの 3 本用 scratch へ差し替えていません。

成果物への影響：**現行 hydrate 出力を渡す手順では、2 依存欠落による試行開始拒否は確認できませんでした。**

## 4. Python consumer の解決時点

**B2：T-126 の submit helper が一時展開先を根にする。成立／must-fix。**

根拠：

- `tools/pegasus/submit_t126_qualification.sh:142` は `orchestrator` と policy だけを一時 directory に archive 展開する。
- 同 `:145` で展開した helper に切り替え、`:368` で login node 上から実行する。
- [submission.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t548-versioned-dep-procurement/orchestrator/qualification/submission.py:163) は `Path(__file__).resolve().parents[2]` を既定 root にする。

結果は `<一時展開先>/output/env/pegasus/.../gflags` です。`--repo-root "$REPO_ROOT"` は渡されていますが、`prepare_toolchain()` の source 解決には使われません。checkout の既定位置へ hydrate 済みでも `:100` で拒否されます。

成果物への影響：**標準 submit が series identity／toolchain manifest の生成前に失敗し、新規 qualification 試行と certified 候補を追加できません。**

是正：既に渡されている `repo_root` を dependency 解決まで渡す必要があります。

また、`identity.py:228` は呼出し時に再解決します。`t126_driver.py:1376` の計算ノード側と `collector.py:1515` の収集側の双方で使われます。必要なのは submit 前の hydrate と、後続検証時にも読める source です。README の一般的な hydrate 手順では、上記の一時 root 誤認は解消しません。

## 5. b4_binary_record の順序

**順序・引数・cache 必須検査の破損：不成立／nit。**

根拠：`orchestrator/campaign/b4_binary_record.py:70` に cache 必須検査が残り、`:75` で `<work>/third-party` へ hydrate、`:84` で名前による辞書化、`:88` から gflags → glog の build です。build に渡す source は hydrate JSON の `resolved_path` です。

成果物への影響：**順序逆転や source 引数の取り違えによる材料生成失敗は確認できませんでした。**

**B3：Mocc の自己 hydrate は新しい依存参照より後。成立／should-fix。**

根拠：`tools/pegasus/submit_mocc_trace.sh:361` は計算ノード側 hydrate 用 cache を要求・転送します。一方、job は `mocc_trace_pilot.sh:893` で checkout staging を選び、`:1531` で gflags を要求します。自己 hydrate は `:1636` まで実行されません。

成果物への影響：**5 本入り cache だけを準備した投入は、自己 hydrate に到達せず停止し、Mocc の新規材料を生成できません。**

是正：この経路でも hydrate → その出力から gflags/glog build の順に接続するか、submit 前に同じ source root を準備する前提を実際の投入経路で満たす必要があります。

## 6. JSON 出力の形の変化による破損

**5 件の JSON を 3 件固定で読む直接 consumer の攻撃：不成立／nit。**

根拠：

- `b4_binary_record.py:84` は名前による辞書化。
- `s3_mocc_lock_coverage.py:235`、`mocc_trace_pilot.sh:1647` は `.source_root` を読む。
- `submit_floor.sh:433` の 3 件検査は policy の FetchContent 集合が対象。
- `p3_s4_loop.py:264`・`:287` の 3 件検査は別形式の masstree prebuild receipt が対象。

`_load_policy()` は変更前から 3 要素を返していました。変更されたのは第 2 要素の内容です。現行 caller は `fetch_third_party.py:728` と同 tool のテスト内で、旧 `path` を読む残存 caller は確認できませんでした。

成果物への影響：**JSON の件数・位置変更そのものによる受理集合の意図しない縮小は確認できませんでした。B1 はコピー集合の欠落です。**

## 7. 廃止命令を案内する文書の残存

修正せず列挙します。

| 根拠 | 残存内容 | 重大度・成立 | 成果物への影響 |
|---|---|---|---|
| `docs/pegasus-runbook.md:330` | gflags/glog は helper 管理外、旧 `*_source_path` が所在の正本 | should-fix・成立 | 手順が存在しない locator を参照し、新規材料の準備が止まる |
| `docs/pegasus-runbook.md:797` | build 元を旧 policy locator で案内 | should-fix・成立 | job が使う hydrate source と手順上の参照先が一致しない |
| `docs/pegasus-runbook.md:679` | `verify-deps` を測定表に掲載 | nit・成立 | 歴史測定表の残存だけでは成果物の値・受理集合への影響は確定できない |

`docs/decisions.md:7536`・`:9657`・`:52836` と archive worklog にも旧名がありますが、過去の決定・観測記録です。**現行命令への誘導という攻撃は不成立／nit、成果物への変更は未確認**です。

## 8. 計算ノードで動くか

**F88 該当の既存 import が残る。成立／should-fix。ただし今回の差分による新規導入ではありません。**

根拠：

- `tools/pegasus/certify_calibration.sh:227` → `:235`：既定 `python3` から `orchestrator.calibrator.schema_v2` を import。3.10 の選択は後の `:425`。
- `tools/pegasus/mocc_trace_pilot.sh:1496` → `:1507`：既定 `python3` から `orchestrator.campaign.toolchain_binding` を import。
- `tools/pegasus/t141_region_profile.sh:1104` → `:1112`、`:1542` → `:1565`：既定 `python3` から `profiler_directive` を import。

成果物への影響：**提示された F88 の環境では、certify／Mocc は依存 build 前、T-141 は解析段階で停止し、成功した測定・解析材料を追加できません。**

**今回の変更で inline Python に orchestrator import を追加したという攻撃、および F660：不成立／nit。** 差分の shell 変更は source 解決の置換で、`tools/pegasus/` 配下の新規 file はありません。

成果物への影響：**この差分に帰属する新しい Python バージョン依存や新規入口による変更は未確認です。**

## 9. 攻めたが成立しなかったもの

- **全 15 本の文字列誤記**：§1 の各行。nit・不成立。文字列誤記による参照変更なし。
- **hydrate が gflags/glog を別名に配置する**：`fetch_third_party.py:646`。nit・不成立。配置による材料欠落なし。
- **p3_s4 が 3 本用 scratch から gflags を読む**：`p3_s4_loop_pegasus.sh:399`・`:471`。nit・不成立。silo の断線を p3_s4 に一般化できない。
- **b4 が hydrate 前に build する**：`b4_binary_record.py:75`・`:88`。nit・不成立。順序による受理集合の縮小なし。
- **3 件固定の別 JSON 検査を本変更の破損とする**：`p3_s4_loop.py:264`。nit・不成立。異なる receipt の契約であり影響なし。

探索時に想定した `submit_mocc_trace_pilot.sh`、`submit_floor_scoping.sh`、`submit_t141_region_profile.sh` は不在でした。停止理由にはせず、Mocc は実在する `submit_mocc_trace.sh` を追跡しました。