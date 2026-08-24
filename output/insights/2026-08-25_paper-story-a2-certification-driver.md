# paper-story A-2 — P2-4 同一 workload certification driver の実装と監査

- 日付: 2026-08-25
- wave: `dev-wave-paper-story-a2-cert-20260824`
- 実装 tip: `a12a705c8a477dc238169feafa39e852d9c48293`
- 取り込んだ main: `671ca6cf7bcde721fc73fc8a1e2ca4cf67c6222a`
- **計測は未実施。** 本文書は driver・compute job body・検査の監査記録であり、性能値も
  certification 結果も含まない。

## この wave が作ったもの

P2-4 の採用点だけを既存 verifier / pipeline の capability で再評価するための exact 4-cell
protocol を実装した。cell は write-heavy (`rratio=5`) と balanced (`rratio=50`) の 2 workload と、
stock の no-backoff (`BACK_OFF=0, BACKOFF_FIXED=-1`) および採用 static backoff (順に 10us と 5us)
の直積である。performance workload は records=1,000,000 / threads=48 / skew=0.9 / rmw=0 /
max_ope=10 / extime=3 / reps=5 に固定した。

correctness は legacy scale (tuple=200 / thread=4 / rmw=true / extime=1) と、その cell の
performance workload に exact 一致する full-scale trace の **AND** とする。performance は
trace-disabled の別 build・別 run で測る。

## 実測して確定した 2 つの環境事実

いずれも計算資源を消費する前に判明した。どちらも「想定で書いた実装が実環境を取りこぼす」型である。

1. **公式 build には toolchain manifest が必須。** build cache は
   `declared_use_class == "official"` かつ `expected_toolchain_manifest` が未指定の組合せを
   build 前に必ず拒否する。初版の driver はこれを渡しておらず、全 cell が `build-error` に
   なる状態だった。
2. **実 producer は run command を文字列で記録する。** 再現用 command は空白連結の**文字列**で
   保存され、perf 計測時は `perf stat -e ... --` を前置する。初版の consumer は list を前提とし
   `argv[0]` を binary と見なしていたため、実測が成功しても証拠を読めず必ず indeterminate に
   なる不一致があった。

## scheduler の request 消滅形式 (login node での実測)

```
$ qstat 999999.nqsv
rc     = 0
stdout = Batch Request: 999999.nqsv does not exist on nqsv.
stderr = (空)
```

存在しない request の照会は**非 0 でも空でもなく**、rc=0・stderr 空・stdout に "does not exist"
行を返す。**その行は request ID を含む。** 初版の実装は消滅終端に対して「request ID を含んでは
いけない」という逆向きの条件を持っており、実形式を拒否していた。合成した空 stdout の fixture が
この不一致を隠していた。取りこぼすと、正常終了した測定が終端として認識されない。

## 変異台帳 (逐語)

- harness: `tools/mutation_harness.py`、`--runner-mode dispatch`、`--detached`
- runner argv: `python3 tools/run_tests.py --force-dispatch -rf` +
  `orchestrator/tests/test_paper_story_a2_certification.py`
  `orchestrator/tests/test_paper_story_a2_job_contract.py`
  `orchestrator/tests/test_campaign.py`
  `orchestrator/tests/test_p3_s4_loop.py`
- spec SHA-256: `a95603db8021dc8725fbb4395193cf47f394def6d25ae7361edc5356d4c84686`
- repo head: `a12a705c8a477dc238169feafa39e852d9c48293`
- baseline: `PASSED`
- 集計: `KILLED 12 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0`
  (registered 12、recorded 12、completed 12、matching 12)

| ID | 単一変異 | 判定 | 期待 node 数 |
|---|---|---|---:|
| `M1` | 未知 verify mode を legacy-only へ縮退させる | KILLED | 28 |
| `M2` | performance workload の records を固定値へ置換する | KILLED | 28 |
| `M3` | campaign preimage と PerfConfig の比較を無効化する | KILLED | 1 |
| `M4` | legacy 単独 pass で cell を certified にする | KILLED | 2 |
| `M6` | global_minimality_established を true にする | KILLED | 1 |
| `M7` | job body の compute-only gate を無効化する | KILLED | 2 |
| `M9` | binary 位置検査を任意位置一致へ緩める | KILLED | 1 |
| `M10` | submission receipt の必須 evidence field を 1 件落とす | KILLED | 20 |
| `M11` | completion marker を rename 後に書き込む | KILLED | 1 |
| `M12` | attempt root の durable base 直下 predicate を無効化する | KILLED | 1 |
| `M5P` | 未知 cell ID の membership 検査と最終集合一致検査を同時に無効化する | KILLED | 1 |
| `M8P` | argv 完全列比較と controlled define map の exact 比較を同時に緩める | KILLED | 3 |

### erratum — 初回 probe で生存した 2 件

事前登録した M5 (未知 cell ID の membership 検査だけを無効化) と M8 (controlled define map の
exact 比較だけを包含判定へ緩める) は、初回 probe で **SURVIVED** した。原因はいずれも検出漏れでは
なく冗長層による mask である。

- M5 は手前の membership 検査を潰しても、後段の集合一致検査が同じ入力を拒否する。
- M8 は define 比較を緩めても、直前の argv 完全列比較が同じ入力を拒否する。

両層を同時に変異させた M5P / M8P は上表のとおり kill される。すなわち両 gate とも検査されており、
単層変異では観測できなかっただけである。初回の SURVIVED 結果はこの erratum として保存する。

### 期待 node 数が大きい 2 件について

`M1` と `M2` は変異対象がいずれも contract loader に pin された source である。pin された file の
disk bytes が HEAD blob と食い違うと、ratification fixture が多数の campaign test を setup error に
落とすため、kill 集合が 28 node に膨らむ。意図した node
(`test_m1_closed_verify_mode_wires_performance_and_rejects_unknown` と
`test_m2_performance_constructor_is_exact_and_rejects_shrinkage`) は**両方とも観測集合に含まれて
おり**、残りはこの drift の波及である。期待 node は推測でなく probe の観測集合をそのまま完全集合
として pin した。

## 成果物が主張しないこと

- **compile-out を artifact 単体で証明したとは書かない。** trace-disabled build の証拠は
  build_done hashes と source commit に束縛された source-routed 証拠に留まる。D751 が対象とする
  TRACE=0 前処理同一性検査は、その consumer が MoCC pilot とその test だけであり本 driver の
  証拠経路に配線が無い。同検査の 3 穴は本 wave の証拠に掛からない代わりに、本 wave の
  compile-out 証拠も同検査の強度を持たない。
- **legacy correctness の workload argv は独立に観測されていない。** 既存 pipeline の記録面に
  残らないため、成果物は該当 field を空とし、policy が宣言した値は観測でないと分かる名前で出す。
  `global_minimality_established` は常に false である。
- **historical campaign の値を新しい比較へ流用しない。** historical pin は protocol の由来を
  示す参照としてのみ持つ。

## 次に必要なこと

land 済み実装で 4-cell を実走する。投入直前に scheduler と CCBench の占有、および A-1 wave の
非活性を再確認する。full-scale trace を縮小せず、資源・timeout・trace 完全性のいずれかが欠けた
cell は indeterminate として記録し、legacy だけが通った結果を成功へ昇格させない。
