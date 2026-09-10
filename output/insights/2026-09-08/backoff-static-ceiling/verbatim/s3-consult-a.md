## 判定

案 A の方向性は支持しますが、現 plan はそのまま author へ渡せません。少なくとも次の 4 点を修正する必要があります。

- stock の `source_digest` と `variant_id` は不変だが、現行 `cache_key` は変わる。
- `µ >= 1000` を無上限にした符号化は、C++ と Python の不一致および待機閾値の桁あふれを起こす。
- 凍結束縛に `applied_tree_sha256`、`analysis_code_sha256`、`binding_sha256` などの列挙漏れがある。
- 正例・負例は単体 witness としては有効だが、現行 extended driver の production admission には意味 witness が接続されていない。

## 所見 1 — stock の cache identity

**判定: real / scope 内。**

`BACKOFF_FIXED=-1` では `#else` の stock 行が選ばれるため、preprocess 後ソースが原本と一致する性質は保たれます。[patch:69-73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-fixed.patch:69) と [source_digest.py:2063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/source_digest.py:2063) が根拠です。`current == baseline` なら `src_token="stock"` になるため、`variant_id` も不変です。[source_digest.py:2222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/source_digest.py:2222)、[pipeline.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/pipeline.py:124)

しかし、patch の dead branch 1 行が変われば、HEAD に対する tracked diff SHA は変わります。[source_digest.py:2292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/source_digest.py:2292) の値は `SourceEvidence` に入り、admission receipt 全体の SHA に伝播します。[source_digest.py:2344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/source_digest.py:2344)、[build_admission.py:662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/build_admission.py:662)

現行の legacy cache key は `admission.receipt_sha256` を含み、v2 identity も admission 全体を含みます。[buildcache.py:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/buildcache.py:624)、[buildcache.py:1314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/buildcache.py:1314)

したがって案 A 後は次になります。

- preprocess source digest: 不変
- `src_token`: `stock` のまま
- `variant_id`: 不変
- `cache_key`: 変化

plan の「stock identity は不変」は cache key まで含めると誤りです。B-10 の inert preflight も digest/token しか検査せず、cache key 不変を証明していません。[b10_backoff_shape_sweep.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:893)

cache admission を変更して旧 key を温存する作業は今回の scope を越えるため、plan は「挙動と variant ID は inert、cache は安全側へ miss」と正直に記録すべきです。

## 所見 2 — 無上限符号化

**判定: real / scope 内。**

plan の

\[
E(\mu)=\mu+2000\quad(\mu\ge1000)
\]

には上限がありません。[plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/artifacts/backoff-static-ceiling/plan.md:9) `Genome` にも整数の上限検査はありません。[model.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/model.py:39)

具体的には、

- `µ = 2^53+1 = 9007199254740993`
- raw `V = µ+2000 = 9007199254742993`

で、提案 C++ は整数 `µ` を `double` に変換して `9007199254740992` へ丸めます。一方、提案 Python model の `Fraction(encoded - 2000)` は `9007199254740993` を返します。C++ と Python が同じ関数ではなくなります。提案変更点は [plan.md:82-85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/artifacts/backoff-static-ceiling/plan.md:82)、現行 Python domain は [b10_backoff_shape_sweep.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:722) です。

さらに実待機は `clocks_per_us * now_backoff` を `uint64_t` に変換します。[backoff.hh:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/external/ccbench/include/backoff.hh:100) Pegasus の `clocks_per_us=2100` では、整数積だけを見ても `µ=8784163844623597` から `UINT64_MAX` を越えます。[env_contract.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/env_contract.py:253)

実装契約は「全 `µ>=1000`」ではなく、今回実際に供給する有限域を明示すべきです。少なくとも 1000–1999 µs など、必要な上限を設計判断として固定する必要があります。全 Genome 向け汎用 range gate の新設は scope 外なので提案しません。

## 所見 3 — 既存 0..2999 の数値不変

**判定: refuted（破れるという疑いを棄却）/ scope 内。**

最後の fallback だけを変える限り、`0..2999` の三領域は新しい式へ到達しません。[patch:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-fixed.patch:70)

- `0..999`: 第1項
- `1000..1999`: `q==1`
- `2000..2999`: `q==2`

この範囲では剰余最大 999、`2r+1` 最大 1999 で、内部の unsigned 演算にも桁あふれはありません。repo 内の active input に raw 3000 以上も見つかりませんでした。

ただし、この三領域の検査だけでは所見 2 の新規高値域を保証できません。「既存測定の意味を保つ」には十分ですが、「新 API が全 `µ>=1000` で正しい」根拠にはなりません。

負値については提案による意味移動はありません。`BACKOFF_FIXED=-2` も C++ では stock 枝ですが、Python `exact_model(-2, …)` は拒否します。これは既存の C++/Python domain 差であり、案 A の回帰ではありません。[patch:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-fixed.patch:69)、[b10_backoff_shape_sweep.py:726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:726)

## 所見 4 — 凍結束縛の列挙漏れ

**判定: real / scope 内。**

親の closure には次が不足しています。

- `applied_tree_sha256`: hole を sentinel 化する frame hash と異なり、実 hole を含む source 全体を hash するため必ず変わります。[b10_backoff_shape_sweep.py:903](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:903) 旧正式成果物にも `450293f8...` が記録されています。[provenance.json:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json:546)

- `analysis_code_sha256` と派生 `binding_sha256`: `exact_model` や B-10 module を変更すれば前者が変わり、binding core を通じ後者も変わります。[b10_backoff_shape_sweep.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:314)、[b10_backoff_shape_sweep.py:1540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:1540)

- coder baseline 文書: `silo-backoff-fixed.patch` の bytes を「不可触」と明記し、B-10 の固定式を current baseline としています。[coder-spec.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/src/coder-spec.md:33) 新決定による supersede または記述更新が必要です。

- 旧 requested-us 診断の値 literal pin: raw 1000 を歴史的 F718 汚染点として除外する consumer とテストが残っています。[backoff_requested_us.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_requested_us.py:451)、[test_backoff_requested_us.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_requested_us.py:636) ここは新 decoder に追随して書き換えず、旧系列の解釈として維持すべきです。

- 旧 official 系列の analysis/binding/record digest 群: write-heavy と balanced の固定値が module 内にあります。[b10_backoff_shape_sweep.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:112)、[b10_backoff_shape_sweep.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:172) これも旧系列として不変です。

一方、plan の候補 hash は正しいことを stream 計算で確認しました。

- patch: `a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a`
- formula: `1205b1ffb4fa6740873f1aa1ecf50bfc484239fb74aa28464dcb2e3a19fbe8df`

したがって「候補 hash が誤り」という所見は **refuted / scope 内** です。

## 所見 5 — 正しさゲートと受理集合

**判定: real / scope 内。**

| surface | 変更前 | 変更後 | 照合 |
|---|---|---|---|
| B-10 `decode()` | `{code∈{0,1}} × MEANS_US` | 同一 | 「B-10 grid は広げない」と一致。[b10_backoff_shape_sweep.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:656) |
| patch/hole pin | `{P_old,H_old}` | `{P_new,H_new}` | singleton の置換で、範囲緩和ではない。 |
| 定数として表現可能な物理値 | `{0,…,999}` | `{0,…,999} ∪ {1000,…,M}` | 真の受理集合拡張。`M` は所見2により要固定。 |
| extended raw grid | raw `1000` | raw `3000` | exact 1 点の置換。 |
| T-2266 raw tail | `…750,999` | `…750,3000` | exact 1 点の置換。 |
| condition family | supply green、meaning は green または unestablished | plan のままなら同一 | 正しさゲートは強くならない。[condition_meaning_gate.py:4058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:4058) |

したがって「R1–R5 と B-10 correctness gate を緩めない」は一致します。しかし、新しい定数意味の受理集合は広がるため、全体を「受理集合不変」「緩めていない」と呼ぶことはできません。現行 D1721 も、入力言語への追加は制御された拡張として記録するよう要求しています。[decisions.md:52390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/decisions.md:52390)

## 所見 6 — runtime-meaning witness の未接続

**判定: real / scope 内。ただし新 gate の実装提案ではない。**

detector 自体は存在しますが、extended driver が使う共通 helper は `BACKOFF_FIXED=-1` にしか declaration を渡しません。他の全値は `declaration=None` です。[backoff_sweep.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_sweep.py:133)

その `unestablished` は admission で許可されます。[condition_meaning_gate.py:4022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:4022)

したがって plan の raw 3000 正例・負例をテストへ追加しても、production T-2266 の raw 3000 が runtime-meaning witness を通ることにはなりません。plan は次のどちらかを明記すべきです。

- witness は静的な実装検査だけであり、production admission の保証ではない。
- 既存 witness の declaration を既存 driver 経路から使う。

後者も既存機構の利用であり、新規 gate・一般化ではありません。

## 正例・負例の恒真性

**判定: 一部 real / scope 内。**

負例の発火点は実効です。

- raw 1000 は `q=1,r=0` なので observed 0。expected 1000 と異なり、[condition_meaning_gate.py:4291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:4291) の `decoded-meaning-mismatch` で落ちます。既存テストもこの理由を pin しています。[test_condition_meaning_gate.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_condition_meaning_gate.py:403)

- fallback を旧 `%1000` に戻す変異は raw 3000 を 0 にし、expected 1000 と不一致になります。

- `-2000` を `-1999` にする変異は raw 3000 を 1001 にし、同じ mismatch 行で落ちます。

一方、3001/3999 の C++ 値を同時更新した Python `exact_model` と比較するだけでは共通誤実装が通ります。また既存 helper は `BACKOFF_FIXED` を runtime `uint64_t` 変数としてコンパイルするため、production の macro literal・`#if`・負値境界は検査しません。[test_b10_backoff_shape_sweep.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:627)

少なくとも 3000/3001/3999 は、Python model との相互比較だけでなく `1000/1001/1999` の独立期待値でも固定する必要があります。これは既存テストの補強であり、新規検査枠組みではありません。

## 親 brief の P1–P4

| 前提 | 判断 | 根拠 |
|---|---|---|
| P1 | **覆す（事実部分は支持）** | 999 でも throughput と abort 率が下がり続ける事実は一致します。[T-2266 README:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/output/insights/2026-09-04_t2266-backoff-static-tail/README.md:296) ただし brief 自身が B を正規の二択として scope 内に置いているため、「B は依頼目的を満たさない」は強すぎます。[brief.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/verbatim/brief.md:3) B は right-censored な設計判断として依頼を満たし得ます。 |
| P2 | **支持（有限な新域に限定）** | fallback だけの変更で 0..2999 は不変。raw 3000 以上の active input も現物にはありません。ただし無上限 `µ` は支持しません。 |
| P3 | **条件付き支持** | global patch/formula を変える以上、将来 B-10 を再実行するなら新 prereg binding が必要です。[b10_backoff_shape_sweep.py:1528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:1528) ただし B-10 grid は code 3 を拒否するため、新 raw 3000 点を登録するものではありません。T-2266 の新 schema/campaign identity と B-10 の再登録を混同してはいけません。 |
| P4 | **支持** | `EXTENDED_SWEEP_US` は現在 1000 を含み、テストも末尾 1000 を pin しています。[backoff_extended_sweep.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:55)、[test_backoff_extended_sweep.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:279) |

## 「実測した新事実」4点の照合

| 点 | 照合 |
|---|---|
| 1. T-2266 requested/realized 分離は main 済み | **一致。** requested は末尾1000、realized は999、F718理由も存在します。[backoff_extended_sweep.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:64)、[t2216_backoff_walk_model.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/t2216_backoff_walk_model.py:53) |
| 2. `EXTENDED_SWEEP_US` は1000のまま | **一致。** 上記 P4 のとおりです。 |
| 3. q=0/1/2/>=3 の復号 | **一致。** C++ と Python は非負かつ通常の uint64 域で同じ分岐です。[b10_backoff_shape_sweep.py:730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:730) |
| 4. F718 detector が既存 | **存在は一致、production coverage は不一致。** compiler-evaluated witness は実在します。[condition_meaning_gate.py:4220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:4220) ただし extended driver の非負値は現在 unestablished のまま admission されます。 |

## scope 外の real 所見

次は実装要求にせず、**裁定パッケージ候補**として扱うべきです。

- 全 Genome / 全 CMake define に共通する整数上限 gate の一般化。
- 過去の F718、T-1941、T-2266、paper-story を新 decoder の意味へ遡及的に書き換えること。
- cache admission の preimage を変更して、dead branch 変更後も旧 cache key を強制維持すること。
- 完了済み B-10 135 cell の再測定・再ラベル。

歴史資料は旧意味のまま維持し、新決定と新系列だけを分離すべきです。

## 検証状態

ファイル変更・commit・pytest・build・実測は行っていません。指定 worktree の `git status --short` は空でした。

## 総括

案 A は、有限な対応域を明示する条件付きで妥当です。しかし現 plan は、stock の cache key 不変を誤認し、新域を無上限にし、凍結 closure と production meaning-witness 接続を取りこぼしています。

author へ渡す前に、少なくとも以下へ直すべきです。

- 「stock は preprocess/variant ID 不変、cache key は変化」と訂正する。
- 対応する物理上限 `M` を明示する。
- `applied_tree_sha256`、analysis/binding SHA、coder baseline、旧 requested-us pin を closure に追加する。
- B-10 再登録と新 T-2266 identity を別物として記述する。
- 高値テストを独立期待値で固定し、runtime witness の保証範囲を明記する。