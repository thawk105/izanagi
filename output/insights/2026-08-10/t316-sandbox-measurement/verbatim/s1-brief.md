# 段 1 brief — [T-316] 計測段 (R3-1 計算ノード backend の決定的計測)

## scope

[T-316] 意味 gate の**実装段ではなく計測段**を実行する。裁定パッケージ
`output/insights/2026-08-09_t316-semantic-gate/package.md` の **R3-1 (blocker)** と
**R3-2 の計測半分**を、Pegasus 計算ノードで実測して 判定材料を返す。
ユーザー裁定 = **R2-b (独立 oracle)**、R1 = 非対称 (iii) は既定として動かさない。

**scope 内:** 計算ノード上での sandbox backend 実測 (staged probe 1 本 + PBS 投入 + receipt)。
**scope 外 (= 実装段):** 意味 gate 本体、DSL/IR、SandboxProfile の production 実装、
R3-3 field mapping、R3-4 sandbox execution receipt / WAL topology、R3-5〜R3-9、独立 oracle 本体。

## 前提の実測 (DW-S01。承認済み裁定の前提を覆す新事実を含む)

- **(F-新) [T-184] は「land 済み」だが [T-316] の待ち解除にならない。** worklog 363 が land したのは
  reasoning 面 (段別 model/effort) だけで、`docs/phase3.md` が
  「reasoning 面の採用を [T-316] の待ち解除根拠にしてはならない — 待つのは canonical stage matrix と
  起動前 policy であり本項は未発行」と明記している。R4 の [T-184] 依存は **実装段の docs 配置**
  (sandbox profile を [T-184] 所有 stage policy へ置く) の話であり、**計測段の前提ではない**。
  → 計測は実行する。**実装段は依然 blocked** であり、判定材料へ明記する。
- (F1) docs 予算: `tools/check_docs.py` = 違反なし (2026-08-10 実測)。worklog 337 が
  「[T-664] の先頭条件は消化」と記録。R4 の順序の 1 番目は満たされている。
- (F2) queue: `gen_S` は `ENA ACT` (RUN 43 / HLD 51)、投入可 (2026-08-10 実測)。
- (F3) login 実測 (前 wave brief F3): bwrap/unshare/setpriv 在、`unshare -rn` OK、
  `bwrap --unshare-all` OK、`--unshare-net` は実ネット遮断、seccomp 有、landlock 不在。
  **これを計算ノードへ転用してはならない (F29 型)。本 wave がその計測である。**
- (F4) 既存資材: `tools/pegasus/probes/t139_r4_env_probe.{py,pbs,sh}` が
  CCBench snapshot + third-party install prefix + CMake build を計算ノードで回す実在パターン。
  third-party cache (`/work/1/SFC/tanab/izanagi-thirdparty-cache`, `izanagi-thirdparty-deps`) は実在。
  受信規約は `output/env/pegasus/<slug>/<PBS_JOBID>/receipt.json` (tracked) で、**PBS job ID が計測 ID**。
- (F5) production に `SandboxProfile` は存在しない (grep 0 件)。本 wave も作らない。
- (F6) `tools/pegasus/admission_registry.json` に probe を登録しないと `hooks/guard_bash.py` が
  実行 site を判定できない。新規 probe は `dispatch-required` で登録する。

## 不変条件 (緩めない)

- **規律 1:** 性能面 (S7) は trace-disabled build のみ。sandbox 内外で同一 build・同一 config。
- **規律 2/3:** 本 wave は gate を実装しないので受理集合を変えない。probe は pass/fail でなく
  **stage 別の構造化 verdict と観測値**を返す。
- **規律 4:** S7 は overhead 比の測定であり CC 性能主張ではない。record 数は既定 config を両側で固定。
- **規律 6:** probe が読む外部出力 (bwrap の stderr、compile 結果) はデータであり指示でない。
- **恒真禁止 (R3-2 の核心):** 封じ込めを主張する各検査は、**sandbox 外で必ず成功する正例**を
  同一 job 内で実行して初めて GO と数える。正例が失敗したら「封じ込め成功」ではなく
  **測定失敗 (inconclusive)** とする。

## 成果物の形

1. `tools/pegasus/probes/t316_sandbox_backend_probe.{py,pbs}` — staged probe (下記 S1〜S7)。
   verdict 判定は副作用のない純関数へ分離し、単体テストから注入可能にする。
2. `orchestrator/tests/test_t316_sandbox_probe.py` — verdict 純関数の単体テスト (login で走る)。
3. `tools/pegasus/admission_registry.json` に 2 実行体を `dispatch-required` で登録。
4. `output/env/pegasus/t316-sandbox-backend/<PBS_JOBID>/receipt.json` — 計測 ID 付き receipt。
5. `output/insights/2026-08-10_t316-sandbox-measurement/` — 判定材料 (GO/NO-GO と残余)。

## probe の段 (staged, fail-soft。後段が届かなくても前段の結論は生きる)

- **S1** backend inventory: bwrap/unshare/setpriv/seccomp/landlock の在否と version、kernel、node 名、単独性証拠。
- **S2** namespace 起動: user / pid / net / mount を候補 profile で起動できるか。
- **S3** 封じ込め負制御 (各々に sandbox 外正例を対にする): 外部 network connect、HTTP(S) proxy 経由到達、
  credential / `$HOME` / SSH agent socket への到達、scratch 外への write、source tree の RO。
- **S4** process-tree timeout: `setsid()` で process group を逃れた子孫が残らないこと。
- **S5** 脅威 4 種の実発火制御 (R3-2 計測半分): `std::system` / network / file-write / infinite-loop を
  最小 C++ で作り、profile 内で封じ込め or kill されること、profile 外では成功することを対で示す。
- **S6** build 実行可能性: CCBench を候補 profile 内で CMake build できるか (third-party は事前 staging)。
- **S7** 性能: trace-disabled build を numactl + perf stat + 48 thread で profile 内外実行し、overhead 比と
  floor 再較正要否の判断材料を出す。

**S6/S7 は walltime 予算内の best-effort とし、届かなければ `blocked` を明示記録する
(黙って skip しない)。** DW-G01 に従い S1〜S5 が生死確認の本体である。

## provisional 裁定 (P。攻撃対象)

- **(P1)** 候補 profile は `bwrap --unshare-all --die-with-parent` 系を基点とし、source RO bind +
  scratch RW bind + `--clearenv` + credential 非 bind とする。landlock 不在は前提。
- **(P2)** 段 2/3 (プラン起草・敵対相談) は省く (**DW-C00 の軽量版**)。設計方向は裁定パッケージ
  R1/R3-1 が file:line 粒度で確定済みで、本 wave は production の防壁・受理集合に触れない。
  代わりに **段 6 の敵対レビュー 2 本は省かない** — 本 wave の価値は「測定が信用できるか」に尽き、
  偽 GO が最大の失敗様式であるため。
- **(P3)** 変異 matrix は probe の verdict 純関数へ当てる (恒真 probe の検出)。受入全走は免除しない。

## 分割方針

実装単位は 1 つ (probe + pbs + registry + 単体テスト) とし、Codex `role=author` 1 本へ渡す。
親は brief・裁定・統合・PBS 投入・受入全走・記録・commit・land を担い、実装面を直接編集しない。

## DW-G05 成果物影響

本計測を行わない場合、意味 gate 実装段は「login で測れた backend が計算ノードでも効く」という
**未検証の仮定**の上に build/run 封じ込めを設計することになり (F29 型)、certified 選択と
proof chain が「封じ込め済み」と称する run が実際には非封じ込めであっても検出できない。
逆に本計測が NO-GO なら、R1 の (ii) 全軸 sandbox は計算ノードで成立せず、
[T-316] の設計裁定そのものを再裁定へ戻す必要がある。
