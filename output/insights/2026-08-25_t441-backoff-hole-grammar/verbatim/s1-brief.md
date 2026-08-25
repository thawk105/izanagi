# 段 1 brief — [T-441] backoff 軸 EVOLVE-BLOCK hole の受理文法

wave = `dev-wave-t441-backoff-hole-grammar` / branch = `worktree-dev-wave-t441-backoff-hole-grammar`
基準 main = `8e2ea461` (worktree 作成時。`check_wave_startup.py` OK)

## scope

backoff 軸 (`silo-backoff-magnitude`) の EVOLVE-BLOCK hole に**受理文法 (allowlist)** を新設し、
`orchestrator/campaign/p3_s4_loop.quarantine()` の backoff 経路で機械執行する。
編集面は EVOLVE-BLOCK の `#if` 合成枝の受理判定だけであり、骨格・stock 枝・trigger 軸・sort 軸には触らない。

## 確定済みユーザー裁定

[T-409] 択一 4 (2026-08-04 /rulings、親推奨どおり) = 受理文法の scope は trigger 軸で閉じ、
**backoff 軸は [T-441] が所有**。trigger 側の文法 v1 は
`output/insights/2026-08-04_t409-evolve-hole-allowlist/` に凍結済み。

## brief 前の実測 (DW-S01。すべて本 worktree で実行)

**(実測 1) 生死実験 — 今日の backoff hole は敵対形をほぼ全部受理する (DW-G01)。**
pin `028f34d` の実 `include/backoff.hh` へ実 `patches/silo-backoff-fixed.patch` を適用した
tree を repo 外に作り、実 `quarantine(write=False)` を通した。7 形すべてが `passed=True`。

| implementation | quarantine | 帰属整合 |
|---|---|---|
| `double now_backoff = 50;` (正例) | 受理 | pass |
| `+ Backoff_.store(0, ...)` (共有適応状態への書込み) | **受理** | pass |
| `static double s; s = s * 0.9;` (隠れ適応) | **受理** | pass |
| `50 + (rdtscp() & 1)` (非決定合成) | **受理** | pass |
| `now_backoff_unused = 50; now_backoff = 0;` | **受理** | REJECT |
| `goto izanagi_skip;` | **受理** | pass |
| `(clocks_per_us > 1000) ? 50 : 25` | 受理 | pass |

拒否は 1 件だけで、それは quarantine ではなく `assert_value_literal_consistent` (帰属整合) が出した。
`value` を実際に走る literal へ合わせれば同形も通る。**quarantine 自身が拒否した敵対形は 0 件。**

**(実測 2) 既存被覆と純増検出力 (DW-S01「性質で検索」)。** backoff hole に現在かかっているのは
(a) 構造 diff 検疫 (フレーム改変・領域外・行頭指令・marker 偽装)、
(b) `coder_effect_gate` の**有限 denylist** (process-shell / file-stdio / network / sleep-block-thread /
escape-hatch の 5 category + 無条件 loop + byte/token 上限)、(c) 帰属整合 (value ↔ literal) の 3 つ。
(b) は自身の docstring で「host-security boundary ではない」「意味的に完全ではない」と宣言している。
**純増検出力 = 「領域内・host-effect 非該当・C++ として合法だが、合成軸の意味を壊す形」**であり、
実測 1 の 6 形がその実例である。denylist の外側を allowlist で閉じるのが本 wave の仕事。

**(実測 3) DW-O09 pin 閉包。** `output/s1-freeze/known_axes_freeze.json` が live source の
sha256 を pin するのは 7 file — `axis_trigger_gating.py` / `backoff_sweep.py` / `genome.py` /
`p3_s4_loop_sort.py` / `s1_known_axes_freeze.py` / `s6_sort_sweep.py` / `s8a_trigger_sweep.py`。
**`p3_s4_loop.py` はこの 7 件に含まれない。** `test_frozen_artifacts.FROZEN_MANIFEST` (23 件) は
`output/` 配下の成果物だけで実装面を 1 件も含まない。→ 主編集面は pin 閉包の外にある。

**(実測 4) consumer 閉包。** `quarantine()` の呼び手は 4 module あるが、**backoff marker で呼ぶ
live consumer は `p3_s4_loop.run_one_iteration` の 2 箇所だけ**である。
`s1_verify_extime_calibration` と `p3_autonomous_workload_trial._preview` は trigger 専用、
`s1_direct_comparison` は `backoff_fixed_best` 構成で EVOLVE-BLOCK を置換しない (CMake flag が枝を選ぶ)。
→ `quarantine()` 1 点に置けば backoff 経路は全部閉じる。

**(実測 5) role 契約。** `.claude/agents/coder-v4-autonomous.md` は既に
`"implementation": "double now_backoff = <式>;"` という出力テンプレートと、
`//` `/*` 行末 `\` の禁止を**宣言済み**である。機械執行が無いだけである。

**(実測 6) 実コーパス (DW-O13)。** `output/` 全走査で `now_backoff = ...` の実出現は 6 形のみ
(`Backoff_.load(...)` = stock 枝 63 回、`static_cast<double>(BACKOFF_FIXED)` = 骨格、
`5.0` / `42` / `913579` / `20.5` は docs・レビュー中の例)。
**段 4 の自律 backoff campaign が生成した実 `implementation` の凍結コーパスは `output/` に存在しない。**
trigger 軸が `positive-controls.txt` 26 件を持っていたのと状況が違う。正例コーパスは
役割テンプレート + 既存テスト fixture + 実測 6 形から構成し、**「26 件全部通す」型の恒真な回帰にしない。**

## §8 B-1 との関係 (依頼要求。前提を 1 点訂正する)

依頼は本 wave を「合成軸そのものを広げる作業」と位置づけているが、**実際には広げない — 狭める。**
受理文法は backoff 軸の受理集合を縮小する関門であって、新しい軸も新しい合成能力も生まない。
`docs/paper-story/2026-08-23.md` §8 の B-1 (合成軸が既知軸最良を超える証拠) は S-1a で不成立が
確定しており、同節は「新しい軸か、既知軸を組み合わせた構成でしか埋まらない」と書いている。
本 wave は B-1 の証拠を 1 件も増やさない。関係は**前提条件の側**にある。S-1a では合成軸が
静的 backoff 最良に −36.0%〜−51.9% で負けたので、backoff 軸は「既知軸を組み合わせた構成」の部品
として残る道がある。その道を将来使うとき、hole が実測 1 のとおり素通しのままだと、
出た利得が合成の手柄なのか hole 逸脱 (共有適応状態の書換え・隠れ適応・非決定) の副産物なのかを
機械的に切り分けられない — 規律 2 が要求する「正しさゲートを緩める変異を許さない」が
backoff 軸では現在**未成立**である。加えて [T-409] must-fix B-6 が
「有限 policy 選択は headline synthesis evidence ではない」と釘を刺しており、
受理集合を有限化するほど backoff 軸も同じ限定を負う。したがって本 wave の成果物影響 (DW-G05) は
「B-1 の証拠を増やす」ではなく、**「将来 backoff 軸を B-1 の部品に使う場合に、その利得の帰属を
機械で守れる状態にする」**であり、材料レポート側には同じ限定を書く義務が生じる。

## 不変条件

1. **規律 2**: 文法は受理集合を**狭める方向にだけ**動く。既存の拒否を 1 件も緩めない。
   既存 3 検査の拒否理由を置き換えず、独立に積む。
2. **恒真禁止**: 明示負例 (実測 1 の 6 形 + 境界形) を pin し、allowlist が恒真でないことを
   段 4 の変異事前登録で確かめる。負例が 1 件も無い allowlist は緑と数えない。
3. **凍結 7 file 不可触** (実測 3)。`.claude/agents/` と `.codex/role-adapters/` も不可触
   (変更にはユーザー明示承認が要る。`docs/decisions.md` の role 変更規定)。
4. **trigger / sort 経路の受理集合を 1 bit も変えない。** 回帰テストで pin する。
5. 骨格・marker・stock 枝・`Backoff::backoff` 呼び出しは coder の編集面でなく、文法の対象外。
6. 拒否理由に候補由来 bytes を載せない (`coder_effect_gate` と `trigger_gate_binding` の
   disclosure-free 方針を継承。識別子・リテラルを evidence へ流すと critic 経路へ漏れる)。

## 判断が割れうる前提 (親の provisional 裁定。攻撃対象)

- **(P1)** 文法は `.claude/agents/coder-v4-autonomous.md` が既に宣言している契約
  (`double now_backoff = <式>;` の単一宣言文 + コメント/継続行の禁止) の**機械化にすぎず、
  契約を狭めない**。したがって [T-409] が実装を止めた理由 1 (role 定義変更のユーザー承認 gate) は
  本 wave では発火しない。— 反証されれば scope は「設計凍結 + 裁定パッケージ」へ落ちる。
- **(P2)** 受理単位は**単一の宣言文 1 個**に限る (複文・追加宣言・制御フローを拒否)。
  実測 1 の 6 形はこれだけでほぼ全部落ちる。
- **(P3)** `<式>` の受理範囲は「数値リテラルと、骨格が既に読んでいる `clocks_per_us` を
  含む副作用なしの算術・比較・三項」までとし、`Backoff_` などの共有状態、`rdtscp` などの
  非決定ソース、`static` 記憶域、関数呼び出し一般を拒否する。
  [T-409] 択一 3 は trigger で数値を排除したが、backoff では数値が軸の本体なので**転移しない**。
- **(P4)** 判定順を固定する: `type → raw size → character → token → parse → semantic`
  (trigger v1 の凍結順を踏襲)。資源上限も明示する。

## 成果物の形

- 新 module (backoff hole の受理文法。判定順・資源上限・disclosure-free な拒否理由)
- `p3_s4_loop.quarantine()` の backoff 分岐への配線 1 点 (trigger 分岐と対称な位置)
- 拒否 subtype の追加 (`DiffRejectSubtype` に 1 値)
- テスト: 正例 / 明示負例 (実測 1 の 6 形を含む) / 判定順 / 資源上限 / trigger・sort 非影響
- 段 4 の変異事前登録 (allowlist の恒真性検査を含む)
- 段 7 の spool fragment (worklog / decisions)

## 分割方針

`DW-C00` の軽量版例外は成立しない — 本 wave は**受理集合を変える**ので独立の敵対検証子を省けない。
段 2 プラン子 1 本、段 3 敵対 2 レンズ、段 5 実装子 1 本 (単一 module + 配線 1 点 + test 1 file)、
段 6 敵対レビュー 2 本 + fix。受入・実測環境は Pegasus login node (`tools/run_tests.py` 経由)。
