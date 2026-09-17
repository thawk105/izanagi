---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2288-a5-freeze
seq: 1
---

## {{D:b4-floor-a5-freeze}}. B-4 床値 spec 3 本の A-5 (2 窓・campaign・seed・出力 path・集約対応) を D2120 項 4 の委任で確定し、凍結 spec と同じ commit に期待 spec 列を記録する

**決定 (D2120 項 4 = D1641 決定 1〜3 / D1638 の委任の下で AI が確定):** 事前登録 §11.1 手順 6 の「結果を見る前の測定手順の凍結」として、
`floor-pair-spec/v3` の spec 3 本を次の値で tracked file として置き、本決定と同じ commit で凍結する。既決値 (artifacts = D2069、
cells・perf_config = D2088 / D2089、calibration = D2090、statistics・failure_policy・format ID = driver 定数) は再裁定せず逐語で継承する。

1. **置き場と命名。** directory は `output/env/pegasus/floor-pair/t2288-f1/` (`output/env/<env_tag>/` の兄弟。`t2288-f1` は凍結集合の
   識別子で、日付・commit を意味しない)。名前は issuer の `__key-value` 様式に揃え、D1641 決定 3 の 5 成分 (env_tag・protocol・threads・
   workload・campaign 識別子) を成果物 (窓・summary) の名前に含める。spec 名にも同じ成分を含めるのは可読性のための本 wave の選択であり、
   D1641 決定 3 が spec の命名を定めたとは読まない。`<wl>` ∈ {rr95, rr50, rr5}。
   - spec: `spec__env-pegasus__protocol-silo__threads-48__workload-<wl>-s0.9-rmw0__campaign-t2288-f1-<wl>-c1c2.json`
   - 窓 (JSONL、`floor-pair-jsonl/v1`): `window__env-pegasus__protocol-silo__threads-48__workload-<wl>-s0.9-rmw0__campaign-t2288-f1-<wl>-c1.jsonl`
     と同 `-c2.jsonl`
   - summary (JSON、`floor-pair-summary-json/v1`): `summary__env-pegasus__protocol-silo__threads-48__workload-<wl>-s0.9-rmw0__campaign-t2288-f1-<wl>-c1c2.json`
   - 出力は spec と同じ directory に置く (git は空 directory を持たないので、tracked spec が出力 directory の実在を担う)。
2. **窓 (UTC、半開区間、3 spec 共通)。** w1 = [2026-09-19T00:00:00Z, 2026-09-27T00:00:00Z)、w2 = [2026-09-29T00:00:00Z, 2026-10-07T00:00:00Z)。
   各窓 `sample_count = 62` (D1695)、pair 1 つ。開始許容帯の差は 48 時間。**これは session 開始時刻の許容帯であり、w1 の終了から w2 の
   開始までの分離を機械保証しない** (driver は session 開始時刻だけを窓と照合し、session 全体の締切を持たない)。実 campaign の
   24 時間以上の分離 (終了→開始を含む保守的な確認) は D1974 項 3 のとおり証拠確認者が実 timestamp で確認する。窓幅 8 日は
   後続の job body 着地・queue 待ち・走行を包むための運用余裕で、独立反復の回数を増やさず、所要時間を保証もしない。
3. **識別子。** campaign_id = `t2288-f1-<wl>-c1` / `t2288-f1-<wl>-c2` (6 件すべて相異)、window_id = `<wl>-w1` / `<wl>-w2`、pair_id = `pair-<wl>`、
   cell_id = `<wl>-t48-s0.9-rmw0`。campaign は D1641 決定 3 のとおりセルごとに数える。
4. **seed。** `seed_hex = SHA-256(UTF-8 "izanagi floor-pair-spec/v3 seed|<spec_relpath>|<source_commit>")` (改行なし)。公開式で再現できる。
   randomization (`hmac-sha256-rank/v1`) は窓内の標本順・side session 順・session 内の candidate / reference 順の 3 箇所を決める。
   親 commit や path を試行して seed を選別しない。式は再現性を与えるだけで、選別不能性や事前性を証明しない。
5. **実行設定 (本 wave の運用選択、既決値ではない)。** `site PEGASUS_COMPUTE`・`env_tag pegasus`・`clocks_per_us 2100` (D1641 決定 3・D2089)、
   `numactl_argv []` (較正の certify 経路は NUMA node 数 1 で numactl を付けず、3 較正とも NUMA 1 node。「生成 command の numactl
   prefix が空」の意味で較正時と同等)、`extra_env {}` (親環境を継承し `FLAGS_` だけ除く)、`use_perf false`、`timeout_s 120`
   (calibrator の bench timeout と同値。較正時の rep wall 3.5〜4.5 秒に対する余裕であって成功率の保証ではない。短くすると標本が
   落ちて 5% 判定 (D1697) に効くので根拠なく縮めない)、`probe_timeout_s 30`。後続の実測結果を見てこれらを変えない。
6. **`source_commit`** は spec を含む commit の親 = `d2ebef7a407dc6be61622ed596cf08b8b518f606` (凍結時点の local main)。
7. **凍結 spec の実 bytes と期待 sha256 (集約の期待 spec 列 = `expected_specs`、この順で渡す)。**

   | spec (relpath は上記 directory 直下) | sha256 | seed_hex | 束縛する較正 |
   |---|---|---|---|
   | `spec__…__workload-rr95-s0.9-rmw0__campaign-t2288-f1-rr95-c1c2.json` | `990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619` | `7fa738507efad5105c6545e85bacde4f21c36a95e3c7b654b2e145077a9bf99e` | `calibration-5c836a22eff9ab40.json` |
   | `spec__…__workload-rr50-s0.9-rmw0__campaign-t2288-f1-rr50-c1c2.json` | `b582d20c37268f491e4c47bb7436731197c18e737cdcca43694c64fa3e0d5e37` | `d956c31f4b17552463838626f80768873aa2c9f15757804c2e3989a228e3eb73` | `calibration-94a4b79fa31bba3c.json` |
   | `spec__…__workload-rr5-s0.9-rmw0__campaign-t2288-f1-rr5-c1c2.json` | `d13c384473a5d24170e929f7e17aad9cc24479a5487ed0da21d06bc45430d8c4` | `b011f2af789c63afbf206f69fee0c2bd1e202dc36dcd06cf5c943d4a3074094f` | `calibration-2b7ba072b88023ae.json` |

   `…` は `env-pegasus__protocol-silo__threads-48` の省略で、実 file 名は省略しない。sha256 は commit 前の実 bytes から計算し、
   spec 自身には spec の hash も凍結 commit の OID も書かない。
8. **集約との対応 (§5.1 追補 (b)、D1974 項 2)。** 集約発行器へ渡すのは、上表の 3 組 (relpath, sha256) を `expected_specs`、3 spec の
   `outputs.summary_relpath` を `summary_paths`、`output/env/pegasus/floor-pair/t2288-f1/` を `output_dir` とする組で、summary から期待列を
   導出しない。全 6 campaign・3 cell・2 窓の閉包を集約側が照合する。identity は env_tag `pegasus`・protocol `silo` (build receipt の
   genome から導出)・threads 48。期待される集約 file 名は
   `b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json`
   (workload 3 件を canonical bytes 順、campaign_id 6 件を文字列順に並べて canonical JSON の SHA-256 先頭 20 hex)。これは予測値で、
   成果物の存在・採用・内容 hash を確定しない。別の manifest・台帳は新設しない (D1936 項 7)。
9. **D2088 の訂正。** D2088 は `reps = 5` が AI の選択であることを「spec の非保証欄と本決定に残す」と書いたが、`floor-pair-spec/v3` には
   その欄が無く、未知 key は loader が拒否する。欄を足す実装変更はせず、AI の選択 (reps と本決定の項 5) は凍結 spec の path / sha256 に
   対応付けた本決定と insight に残す。これは D2088 の記録先の訂正であり、値の変更ではない。

**理由:**
- A-5 の各値は D2120 項 4 が列挙して AI 確定を委任した範囲にあり、対象集合・統計関数・欠測規則・時間分離要件は変えていない。
  段 3 の敵対相談 2 本は「授権は十分、ユーザーへ返す事項なし」で一致した。
- 期待 spec 列を凍結 spec と同じ commit に置くのは、spec の sha256・HEAD blob 一致・祖先性だけでは「後から spec と期待 hash を
  差し替える」経路を閉じられないため。同じ commit に置いても機械的に後変更不能にはならず、後続はこの pin を使うと決めることで
  事前性を運用として保つ。
- 窓を 3 spec 共通にしたのは、3 cell を別々の割当てで走らせても同じ 2 つの許容帯に収めるため。並走できることは資源と admission に
  依存し、本決定は保証しない。
- 48 時間の隙間は「24 時間以上離した 2 campaign」を開始許容帯の構成で読み取れるようにするための余裕である。session 全体の
  上限を driver が持たないので、終了→開始の分離は人手確認に残す (D1974 項 3・6)。
- 現物で確かめた: 3 spec とも loader の parse 関数を通り、凍結 checkout で `--validate-only` が通ることは本決定を含む commit の
  後に実走して insight へ記録する (本決定は結果を書かない)。

**却下した選択肢:**
- summary から期待 spec 列を導出する — 欠けた入力を期待集合からも消せる循環になる (D1974)。
- 仮置き wave の値 (2030 年の窓、ゼロ seed、`timeout_s 600`) を先例として継承する — 仮置きは先例でないと当該 insight が明記している。
- spec に非保証欄や説明 field を足す — 未知 key は拒否され、実装変更が要る。
- 結果や進捗を見て窓・対象・seed を延長・差替えする — §5.1 追補 (b)(f)、§11.1 手順 7 に反する。窓を使えずに終わった場合は
  未実施の凍結として記録を残し、新しい凍結を別 commit で行う。
- 窓の隙間を 24 時間にとどめる — 開始許容帯の差としては条件を満たすが、session の終了が窓を越えうるため、分離の読み取りが
  人手確認の結果に全面依存する。48 時間でも人手確認は残るが、読み取りの余裕が増える。

**本決定が主張しないこと:** 期待集合・seed・凍結の事前性の機械証明。n = 62・実 campaign の分離・対象集合の意味的一致の機械保証。
標本の統計的独立性、残存標本での 95% 被覆、contention 域の網羅。session の wall 上限、将来の割当て・環境の同一性、別 node 並走、
admission、実走の成功。binary の将来の可用性、trace 不在の完全な検出、実行中 module bytes と記録 commit の対応。成果物の削除・改変の
防止。床値の生成・採用・§5 の記入・本書の発効。
