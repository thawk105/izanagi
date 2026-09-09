# 段 4 裁定 — dev-wave t2265-cohort2

段 2 プラン (`s2-plan.md`)、段 3 レンズ A (`s3-lensA.md`、因果推論と事前登録)、
段 3 レンズ B (`s3-lensB.md`、実装規律と凍結境界) を読み、親が現物で検算して裁定した。

## 0. 覆した親 brief の裁定

- **(P2) 「時間 cap を観測長以上にすれば 0 commit が構成上起きえない」は無条件では誤り。**
  現行比較は `elapsed >= clocks_per_us_ * cap_us` で両者が `size_t`。cap を巨大にすると積が
  桁あふれして cap が即発火する (レンズ B 所見 3、段 2 プラン)。さらに保証は「count 閾値へ到達して
  受理された窓」に限られ、commit が止まった run の非閉鎖は残る (レンズ A 所見 2)。
- **(P3) 「末尾の部分窓を flush」は撤回。** 部分窓は count で閉じないので 0 になりうるうえ、
  最後の 1 対だけ別の閉鎖規則と分散を持つ (レンズ A 所見 3)。count-closed terminal に一本化する。
- **(P4) 「patch C の改訂は局所的」は撤回。** C の bytes 変更は `counterfactual_patch_sha256` と
  `patch_stack_sha256` を動かし、成果物 identity へ波及する。旧 pin は歴史的束縛として残す。
- **(P5) 「cohort 2 が実際に使う policy≠0 cell を認証する」は表現が広すぎる。** 認証できるのは
  既定 seed の実行体と 48 スレッドだけである。
- **本 wave の完了判定を書き換える。** cohort 2 は cohort 1 の主判定を確定させない。
  窓構成を変えると推定対象が変わるからである (レンズ A 所見 1)。

## 1. 推定対象の位置づけ (最重要)

**cohort 2 は「cohort 1 を pilot とした、関連する新しい count-closed 推定対象に対する前向き確認試験」
である。cohort 1 の主仮説の厳密な確認ではない。**

- cohort 1 の推定対象は「count 閾値または 10,240 µs cap のどちらか早い方で閉じる混合窓」の上の局所 ITT。
- cohort 2 の推定対象は「約 10,000 commit への到達で閉じる窓」の上の局所 ITT。
- **cohort 1 の主判定は `inconclusive` のまま永久に確定する。** 本 wave はそれを覆さない。

**なぜ同一推定対象で決着させられないか (親が実測)。** cohort 1 主層では 12 run のうち 1 run が
0 commit 窓で無効化された。同じ設計を繰り返すと、12 run のどれかで再発する確率は
`1 - (11/12)^12 ≈ 0.65` である。**同一推定対象のままでは判定を安定して出せない。**
この計算と結論を insight と事前登録の開示節に書く。

## 2. 実装の裁定

### R1. 時間 cap — 巨大 cap + 除算比較。**変更は patch C 内に限る**

cap は `9223372036854775807`。比較を `elapsed / clocks_per_us_ >= cap_us` へ変える。
正整数では `floor(e/c) >= cap` と `e >= c*cap` は厳密に同値なので既存 cell の挙動は変わらない。
この行を `+` として持つのは patch B (`patches/cicada-adaptive-dynamic.patch:227-232`) だが、
**patch B は B-10 の全 campaign と認証が使うので触らない。** patch C が同じ
`include/backoff.hh` を触るので C 側で `-`/`+` にする。
`clocks_per_us_ == 0` で 0 除算になる経路が無いことを現物で確かめ、無ければ守りを入れる。

**cap と比較は計装ではなく CC 本来の機構である** (レンズ B 所見 3)。`#if BACKOFF_TRACE` の外に
あり、trace 無効 build にも効く。**trace on / off で同じ値を使う。**「計装」と書かない。

### R2. terminal event — count-closed、1 回だけ、**patch C は 2 file のまま**

**`common/runner.hh` を触ってはならない。** `orchestrator/campaign/source_digest.py:97-100` の
ALLOWLIST は `cmake/Options.cmake` / `include/backoff.hh` / `cc/silo/transaction.cc` /
`cc/mocc/transaction.cc` の 4 つだけで、driver は patch 適用後に `resolve_evidence` で
allowlist 外の tracked 改変を拒否する (レンズ B 所見 1、親が現物で確認)。
**runner を触る設計は build 前に必ず止まり、成果物が 1 件も出ない。**

採る形は次のとおりで、すべて `include/backoff.hh` と `cmake/Options.cmake` に閉じる。

- `cmake/Options.cmake` へ `CCBENCH_BACKOFF_TRACE_TERMINAL_US` を追加 (既定 0 = 無効)。
- `#if BACKOFF_TRACE` の内側に `start_time_` (init で記録) と `terminal_recorded_` を持つ。
- leader が count 閉鎖を検出した時点で、`terminal_recorded_` が偽かつ
  `now - start_time_ >= clocks_per_us_ * terminal_us` なら、**通常の更新を行う前に**その窓の統計だけを
  terminal event として記録し、`terminal_recorded_` を真にする。以後は記録しない。
- **terminal では LCG を進めず、割当を当てない。** `assigned_invert = -1`、`terminal_flush = 1`、
  trigger は terminal 専用値。
- `terminal_recorded_` が真なら、二度目以降は記録も追加 flush もしない (レンズ B 所見 2)。
- run は `extime` で通常どおり終わる。世界を止めない。

**この形で成立しないと実装子が判断したら、第 3 の file を足さずに親へ戻すこと。**

### R3. cohort 2 の cell と観測長

```text
cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0
cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1
cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2
```

- `extime = 6` 秒、terminal 期限 `CCBENCH_BACKOFF_TRACE_TERMINAL_US = 5000000`。
  terminal が必ず run 内に入るよう 1 秒の余裕を取る。
- 既存 2 literal の extime 3 束縛は 1 文字も変えない。cell ごとに exact な extime を引く閉じた表にする。
- schema は `izanagi-dynamic-backoff-trace/v4`、事前登録 sha は cohort 2 の新規文書のもの。
- **どちらの literal にも一致しない trace には事前登録 field を付けない。**

### R4. 割当整合性検査 (LCG)

名前は **assignment-integrity check** とする。**「無作為化を検証した」と書かない** (レンズ A 所見 6)。
事前固定 LCG が物理過程と同期しないという as-if 仮定は未検証のまま引き継ぐ。

不一致は成果物の適格性違反として `ValueError` を送出し、判定を返さない。
terminal では state を進めず `assigned_invert = -1` を要求する。
**負例 fixture は `inversion_realized = 0` の event を反転させる** — `inversion_realized = 1` のまま
反転すると producer parser が LCG より先に拒否し、帰属が成立しない (レンズ B 所見 14)。

### R5. plot 拡張

exact set を分ける。**単に `TRACE_CELLS` へ 3 label を足すと既存 18 row を 54 row と誤認する。**
波及先は `_common_identity`、row / grid 検査、figure loop、`extime_s == 3` pin を含む。
親 brief の anchor `:474` は `:477-478` へ訂正する (レンズ B 所見 15)。
段 2 が親の `:1202` を誤りとした批判は成立しないので撤回する。

### R6. 直列性認証 — 実施する。ただし射程を逐語で限定する

新 certification cell は cohort 2 の p1 / p2 の 2 本。`CERT_CELLS`、raw allowlist、claim、
namespace、row、group、payload、PBS の**全箇所**で exact cell から extime と claim を引く閉じた表にする。
prefix 一致・任意の正の extime・parsed 値だけの受理を導入しない。

**認証するのは既定 seed の実行体と 48 スレッドだけである。** cohort 2 が使う 12 本の seed 別実行体
でも 24 スレッド条件でもない。全 binary の認証には 312 job が要る。
**「cohort 2 を認証した」と書いてはならない。**

### R7. 段 5 の所有分割 — 3 unit (プランどおり)

- Unit A: `patches/cicada-adaptive-counterfactual.patch`、`patches/README.md`、
  `orchestrator/tests/test_dynamic_backoff_transitions.py`
- Unit B: `tools/pegasus/probes/t2187_adaptive_const_probe.py` / `.pbs`、
  `orchestrator/tests/test_t2187_adaptive_const_probe.py`、`orchestrator/tests/test_ccbench_spawn_sites.py`
- Unit C: `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py` (新規)、
  `orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py` (新規)、
  `tools/plotting/plot_dynamic_backoff.py`、`orchestrator/tests/test_plot_dynamic_backoff.py`

`common/runner.hh` を触らないので `source_digest.py` 側の owner は不要になった (レンズ B 所見 16 は解消)。

## 3. 事前登録に必ず書く規則 (レンズ A の採用分)

- **推定対象の定義**: 「初回更新を除き、terminal 期限より前に発生した割当について、次の count 閾値
  閉鎖までの rate 変化を測り、最後の割当も count-closed terminal を following として含める ITT」。
- **terminal 非閉鎖の扱い**: 固定 seed が terminal 閉鎖に到達しない場合、**その seed を outcome に
  基づいて置換も除外もせず、主判定全体を `inconclusive` にする。** 設備・queue・build の
  outcome-blind な不成立とは区別する。
- **pilot の永久除外**: 凍結前の生死確認 job は別 output namespace とし、確認集合から永久に除外する。
  見た field と集約値をすべて開示する。
- **検出力**: 「R = 12 が十分」と書かない。「真値 0、独立で概ね正規な run 差、cluster SD <= 0.032、
  12 run 完備という条件下で、旧計画モデルの等価判定力は約 0.823。新推定対象に対する SD は未検証。
  実測 `s_D`、CI 半幅、decision を報告する。実用優越については効果量仮定を置かず検出力を主張しない」。
- **判定の読み方**: レンズ A 所見 8 の「書いてはいけない文」の列挙をそのまま insight へ載せる。
- **開示**: レンズ A 所見 2 の逐語ブロックを §0.1 へ入れる。cohort 1 の 11 run 集計
  (平均 0.0684、SD 0.0283、その規則を当てると優越になること) も数値ごと開示する。

## 4. 計測の裁定

- **12 job を 1 つの共有 detached submit-tree から同時投入する。** t2187 は共有 build cache の
  claim を使わず、`isolated_checkout` は `$TMPDIR` へ `git clone --shared` する node ローカルの木を
  作る (`t2187_adaptive_const_probe.py:551-575`)。**claim 衝突は起きないので 1+11 の段取りは不要**
  (レンズ B 所見 11、親が現物で確認)。job ごとの checkout も不要。
- 投入前に実装と新事前登録を commit し、submit-tree をその exact commit へ detached、
  submodule pinned-clean にし、`cd -P` した canonical root から qsub する (レンズ B 所見 10)。
- seed は cohort 1 の 12 値をそのまま使わず、cohort 2 用の生成規則
  `izanagi-t2265-cohort2-policy2-seed-NN` (NN = 00..11) の SHA-256 先頭 8 byte big-endian uint64 とする。
  12 値を事前登録へ逐語で載せ、相異なり 0 でないことを親が独立に検算する。
- 認証 49 job は cohort 2 の 12 job と別に投入する (trace 無効 build、規律 1)。

## 5. scope 外

- D1515 の上流還元 (再訪条件が未充足)。
- cohort 1 の事前登録・解析器・12 成果物への一切の変更。
- 将来 cohort 用の互換層。
- 12 seed 別 binary の全認証 (312 job) と 24 スレッド条件の認証。
- `common/runner.hh` を patch 対象へ足すこと、`source_digest.ALLOWLIST` の拡張。
