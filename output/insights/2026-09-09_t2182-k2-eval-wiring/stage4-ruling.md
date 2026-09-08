# [T-2182] 段 4 裁定 / plan v2 / 変異事前登録

段 2 プラン (`stage2-plan.md`)、段 3 相談 2 本 (`stage3-sol.md` / `stage3-luna.md`)、および親の
独立実測に基づく。裁定時点の local main = a96a48fef (wave 起点 2143a49c0 から前進。受入前に取り込む)。

## 裁定 1 (real・採用・親 brief を改訂) — condition gate が評価経路の実際の停止点である

luna 所見 1。親が独立に裏取りして **confirmed**。

`_run_one_iteration_resolved` は `_require_condition_gate(sub, genome)` を
`orchestrator/campaign/p3_s4_loop.py:1679` で呼ぶ。この関数は `source_root` と `genome` だけを
受け取り、cmake configure を自前で起動する (`同:324-347`)。offline の FetchContent 情報
(`fetchcontent_base_dir`、3 本の source dir、`dependency_prefix`) は同じ scope の
`同:1683-1697` で `run_campaign` にだけ渡され、condition gate には渡らない。

計算ノードには network が無いので、condition gate の configure は masstree / mimalloc /
googletest を clone しようとして失敗する。これは 2026-09-02 の実測で 6 回投入して到達した
停止点そのものである (`output/insights/2026-09-02_t2182-k2-arm-liveness/README.md:63-72`、
supply=preprocess-failed)。**env seam だけを足しても評価経路は同じ場所で止まる。**

**親 brief の「driver 側は scope 外」を改訂する。** 理由は 2 つ。(a) 依頼の目的は
「評価経路を Pegasus で通す配線」であり、condition gate は評価経路上の停止点である。
(b) これは新しい gate の追加ではなく、既存 gate へ既にある入力を供給する配線である。
仮想リスク向けの追加ではない。

**子の scope 判定は不採用。** luna は「`condition_meaning_gate.py` は別 wave 所有なので依存待ち」
と結論したが、これは 2026-09-02 の記述 (「condition gate の cmake argv には `-D` を足せない」)
に依拠しており stale である。親が現物を確認したところ、
`condition_meaning_gate.capture_define_inputs` は既に `configure_args: Sequence[str] = ()` を
受け取り (`同:802-813`)、それを configure argv へ展開する (`同:1656-1667`)。**受け口は main に既存で、
本 wave は `condition_meaning_gate.py` を 1 byte も変えない。** 依存待ちではない。

## 裁定 2 (real・**段 5 で撤回**・裁定パッケージへ) — driver 入口の manifest / coder role 相互必須

sol 所見 1。親が裏取りして **confirmed** (`orchestrator/campaign/p3_s4_loop.py:2473-2481` の
`knowledge_input if a.coder_role is not None else None`)。

`--knowledge-manifest` を渡し `--coder-role` を省くと、campaign identity と知識受領証は K2 に
束縛される一方、coder 出力は非 K2 schema で読まれ、K2 consumer (schema・anomaly・参照 index) を
通らない。K2 として記録された候補が K2 検査を受けずに WAL の BUILD_START と certified 選択へ入る。

**これは「仮想リスク向けの新設 gate」ではない。** 本 wave は K2 アームを Pegasus で初めて実走
可能にする wave であり、その aim の正しさシグナル経路に開いている fail-open である。ユーザーが
名指しで緩めるなと指定した規律 3 に直接かかる。採用する。

**撤回 (2026-09-09、段 5 の実測を受けて)。** 実装子が停止し、既存テスト
`test_main_manifest_only_accepts_legacy_flattened_proposal` が manifest 単独 + legacy flattened
proposal の受理を**意図して登録した正例**であることを示した。その fixture は
`retrieval_result.status = "completed_empty"` / `sources: []` の manifest であり、
「K2 と宣言したが取得結果が 0 件」という意味のある経路を守っている。ユーザーは本 wave の scope を
「本題の配線だけ、gate の追加は scope 外」と明示しているので、親はこの裁定を撤回し、
**実装せずユーザーへの裁定パッケージとして返す** (DW-S04 の scope 外 real 所見の扱い)。
推奨案は「manifest の sources が非空のときだけ `--coder-role` を必須にする」で、これなら
上記の正例 (sources 空) を 1 件も壊さずに sol が示した fail-open を閉じられる。
Pegasus の production 経路は単位 B が既に閉じている。

以下は撤回前の本文である。

実装は argparse 後の非整合 argv の拒否 1 箇所に限る。**`--emit-planner-context` 経路は現状維持**
— この経路は coder role を使わず、2026-09-02 の実測もこの経路を通した。制約は
`--run-iteration` 経路にだけ掛ける。

## 裁定 3 (real・採用・親 brief の (P2) を改訂) — 必須は 2 値、宣言 2 値は任意

luna 所見 3。親が裏取りして **confirmed**。`--knowledge-classification` と
`--knowledge-de-novo-claim` は campaign identity に入らず (`同:1311-1319` は knowledge level と
manifest digest だけを足す)、受領証にしか届かない (`同:1321-1326`)。driver 既定
(`reproduction_or_selection` / `false`) は現行 run card の宣言と同値である。

親 brief の (P2)「4 つとも env で受ける」を改訂する。job body の必須束は
**{manifest, coder-role} + proposal path** とし、宣言 2 値は任意 (設定時のみ転送、
**設定済みで空なら拒否**) とする。4 つ必須は同じ成果物を作れる入力を不受理にするだけで、
受理集合を不要に狭める。

## 裁定 4 (real・採用) — 変異事前登録を意味的に load-bearing なものへ再照準

sol 所見 3・luna 所見 4。段 2 の候補 5 件のうち 2 件は登録しない。

- **不登録: manifest pair と role pair の順序交換。** flag と値の組を保った交換は argparse 上
  同義であり、成果物の値・受理集合・参照を変えない。argv 書式の規約であって正しさ防壁ではない。
- **不登録: 完全性検査 `-n` → `-v` (空 role を通す)。** driver の
  `choices=("coder-v4-autonomous-k2",)` が同じ入力を拒否する (`同:2301-2303`)。単一理由性が
  成り立たない (DW-M01 / F28)。

## 裁定 5 (real・実装項目ではない) — 未実測の範囲を主張しない

luna 所見 2。README §7 が明記するとおり、gflags/glog prologue 以後 (prologue の build 時間、
receipt を通した build の成立、attestation の exact 照合、walltime 03:00:00 の充足) は未実測で、
`_assert_single_tenant` も計算ノードで未実測である。`compute-result.json` の `driver_rc` は
job body 全体の rc である。**本 wave は「配線した」までしか主張しない。「評価済み」とは書かない。**
worklog と insight にこの境界を明記する。

## 裁定 6 (real・nit へ) — 深い K2 検査は事前構築後である

sol 所見 2。sol 自身が「この所見単独では certified 受理集合は広がらない」と認めている。
driver を build 前に 2 度起動する形は費用が見合わない。nit として記録し実装しない。

## 裁定 7 — `buildcache.py` は編集しない

親の独立実測。`orchestrator/campaign/buildcache.py` は `campaign_lock.py:83` の enforcement
source closure の member である。closure member を変更すると campaign lock を作る全テストが
contract-loader-drift で落ちる (2026-09-02 に `wal.py` で 48 件のマスクを実測)。

condition gate へ渡す define は `p3_s4_loop.py` 側で組む。ただし **文字列書式を手で複製しない** —
`buildcache` の既存 producer を呼んで導出するか、それが不可能なら「condition gate の configure
引数と campaign build の configure argv が同じ FetchContent token を持つ」ことを同一入力で
突き合わせるテストを置く。派生値を pin するのではなく生成器を束ねる。

## plan v2 (確定)

### 単位 A — driver 側 (`orchestrator/campaign/p3_s4_loop.py` + `orchestrator/tests/test_p3_s4_loop.py`)

1. `_require_condition_gate` に offline dependency 情報を渡せるようにし、
   `_run_one_iteration_resolved` (`同:1679`) の呼び出しで
   `fetchcontent_base_dir` / `masstree_source_dir` / `mimalloc_source_dir` /
   `googletest_source_dir` / `dependency_prefix` から configure 引数を組んで渡す。
   引数の形は campaign build と同じ
   (`-DCMAKE_PREFIX_PATH=`、`-DFETCHCONTENT_BASE_DIR=`、
   `-DFETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}=`)。
   `capture_define_inputs(..., configure_args=...)` へ渡す。
2. **条件付きにする。** prebuild の情報が無い走行 (linux-baremetal を含む既存の全経路) では
   `configure_args` を空のままにし、現行と同一挙動を保つ。
3. `--run-iteration` 経路で `--knowledge-manifest` と `--coder-role` を相互必須にする。
   `--emit-planner-context` 経路は変えない。
4. `condition_meaning_gate.py`、`buildcache.py`、`screening_driver.py` は変更しない。

### 単位 B — job body 側 (`tools/pegasus/p3_s4_loop_pegasus.sh` + `orchestrator/tests/test_p3_s4_loop_job_contract.py` + `tools/pegasus/README.md`)

段 2 プランの §1〜§4 を、裁定 3 で改訂して実装する。

- 必須束: `IZANAGI_S4_KNOWLEDGE_MANIFEST` と `IZANAGI_S4_CODER_ROLE` は all-or-none の非空、
  かつ `IZANAGI_S4_PROPOSAL_PATH` が非空であること。
- 任意: `IZANAGI_S4_KNOWLEDGE_CLASSIFICATION` と `IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM` は
  設定されていれば非空を要求して転送し、未設定なら転送しない (driver 既定に委ねる)。
- 拒否は既存 `refuse` (rc=2) を使い、repository path 解決より前・trap 設置より前に置く。
- argv は proposal 分岐にだけ渡す。fixture 分岐には渡さない。
- 契約テストは逐語 pin・段順 marker・refusal pin を**追加方向で**更新する。既存期待値の反転・
  緩和・skip・削除は禁止。
- README §7 の義務一覧と qsub fence を更新する。fence は 1 block・1 command 行・`-o`/`-e` を保つ。

編集 path は単位 A と B で素集合である。並列投入する。

## 変異事前登録 (6 件)

各変異は runner を表の単一 nodeid に絞って走らせる。

| # | 変異位置 | 変異内容 | 狙う防壁 | 期待して赤になる node |
|---|---|---|---|---|
| M1 | `p3_s4_loop.py` `_require_condition_gate` 呼び出し | configure 引数を渡さず常に空にする | prebuild 情報が condition gate へ届くこと | 新設: prebuild 情報ありのとき condition gate の configure argv に FetchContent token が入る正例 |
| M2 | 同上 | prebuild 情報の有無を見ず常に渡す | 既存経路 (receipt 無し) の挙動保存 | 新設: receipt 無しの走行で configure 引数が空である負例 |
| M3 | `p3_s4_loop.py` main の相互必須検査 | 検査を除去する | K2 identity と K2 consumer の結合 | 新設: `--run-iteration` + manifest あり + role 無しが rc 非 0 で拒否される負例 |
| M4 | job body の K2 要求検出 | 設定済み検出を非空検出へ変える | 設定済み空値も部分指定として拒否する境界 | 新設: manifest のみ設定済み空・role/宣言 2 値未設定・proposal 非空が rc=2 |
| M5 | job body の proposal path 必須拒否 | 拒否行を無効化する | K2 束が proposal 経路でだけ使えること | 新設: 完全束・proposal path 無しが rc=2 |
| M6 | job body の proposal 分岐 | `"${k2_argv[@]}"` の展開を除く | 検証済み束が実際の driver argv へ届くこと | 新設: 完全束のとき driver argv に 2 (または 4) flag が現れる正例 |

M4 の負例は env vector を「manifest のみ設定済み空、role と宣言 2 値は未設定、proposal 非空」に
固定する。他の K2 env を非空にすると後段の完全性検査が同じ拒否を出し、単一理由性が壊れる
(luna 所見 4)。

## 不変条件 (段 5・6 で守る)

- 既存テストの期待値を変えない。反転・緩和・skip・削除を禁じる。赤なら実装側が誤り。
- `condition_meaning_gate.py` / `screening_driver.py` / `buildcache.py` / `wal.py` を変更しない。
- prebuild 情報の無い走行の挙動を変えない (linux-baremetal の既存成果物に影響させない)。
- 規律 3・規律 6 を緩めない。
- 新しい台帳・framework・互換層・一般化を足さない。
