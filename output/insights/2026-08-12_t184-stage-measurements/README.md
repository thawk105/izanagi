# [T-184] dev-wave 段別 実測一覧 と resource envelope 択一の再提示

2026-08-12 のユーザー裁定「段別の所要時間・失敗率の実測一覧を作ってから resource envelope の
択一を再提示する」に対する成果物である。

**本 wave は択一を決めない。実装面差分ゼロ (docs + 分析) で終端する。**
以下に現れる実装の記述はすべて **ユーザー裁定後の別 wave の話であり、本 wave の scope 外**である。

不変の前提: reasoning 面は D266 のまま (値を 1 つも変えていない)。retry policy は [T-183] 依存の
まま、本 wave は触れない。本項を他タスクの待ち解除根拠にしない。

一次資料と集計器は repo 外の `dev-wave-jobs/dev-wave-t184-stage-measurements/`
(`aggregate.py` / `strata.py` / `analyze2.py` / `slices.py` / `coverage3.py`、
`receipts.csv` / `summary.json` / `strata.json` / `analysis2.json` / `slices.json` /
`coverage3.json`)。

---

## 1. 一次資料の同定

`tools/codex_worker_launch.py` は job ごとに `receipt.json` (schema v3) を書いており、
段名・所要時間・上限・失敗の全 field がそこに揃っている
(`stage` / `lane` / `sandbox` / `recorded_model` / `recorded_effort`、
`actuals.*`、`limits`、`outcome` / `stop_reason` / `validator_rc` / `codex_exit_code`、
`attempts[].limit_trigger` / `evidence_status` / `metering_status` / `termination_verified`)。

**これが「段別の所要時間・失敗率・失敗型」の canonical な一次資料である。**
`.done` file や mtime からの推定は不要だった。
2026-08-10 の前回提示が「台帳に資源上限の証拠は無い」と書いたのは、
**証拠が無かったのではなく、この所在を把握していなかったためである。**

## 2. 母集団の作り方

| 段階 | 件数 |
|---|---:|
| `find dev-wave-jobs -name receipt.json` の全 hit | 1,362 |
| mutation worktree 内の repo 複製を除外 | 1,346 |
| 別種 artifact を path で除外した残り (= 内容検査の対象) | 518 |
| うち codex worker receipt の必須 field を欠き内容判定で落とした | 121 |
| **母集団 (physical receipt)** | **397** |

path で除外した別種 artifact (マーカー重複あり): dispatch submission receipt 493、
計算ノード job 出力 (`*.nqsv/`) 325、pytest 一時 directory 内の複製 291、
`output/insights/` 内の凍結複製 105、環境 probe receipt 63。

内容判定の必須 field は `job_id` / `stage` / `codex_version` / `attempts` / `limits`。
**path だけで母集団を決めると 3 倍以上に膨れる。** 段名は receipt の `stage` field を権威とし、
artifact 名・`.done` 名・directory 深さから推定していない
(job artifact の深さは wave ごとに 3〜5 とばらつく)。

**内容判定は必須 field の存在検査である。** producer 自身の `check-receipt` による
完全性検証 (closed schema、manifest、sealed rollout、output hash、truth table) は
**本 wave では実施していない。** 破損 receipt を発見したという主張はしないが、
証拠境界は「存在検査を通った 397 件」までである。

## 3. 観測単位 — receipt は launch でも logical job でもない

`job_id` は wave・stage/lane・prompt の SHA から決まり、完全な receipt は上書きされない
(`tools/codex_worker_launch.py:1895-1901`)。したがって:

- **同じ prompt を同じ artifact root へ再投入しても新しい receipt は生まれない。**
  receipt 数は launch 数ではない。
- artifact root を変えれば同一 logical job の receipt が複数できる。
  **実データに 1 件ある** — `dev-wave-t657-stage0-rulings` の plan が
  初回 `not_accepted`、別 root での再投入で `accepted`。

したがって physical receipt 397 に対し **logical job は 396** である。
`attempt_count = 1` が全件であることは「launcher 内 retry が無い」ことしか言わず、
**外側の再投入は少なくとも 1 件実測されている。**

## 4. 被覆 — この一覧が数えていないもの

**「全投入に対する被覆率」は算出しない。** 投入の registry が存在せず、分母を定義できない。
数えられるのは次だけである。

| 数えたもの | 値 |
|---|---:|
| 検証済み receipt 行 | 397 |
| それが属する `dev-wave-jobs/` 直下の directory | 52 |
| receipt が名乗る `manifest_wave_id` の異なり数 | 61 |
| 管理用を除いた job directory | 234 |
| うち検証済み receipt を持つもの | 52 |
| receipt を持たないが `.done` file を持つもの | 154 |

directory 52 と wave_id 61 が一致しないのは、同一 wave の artifact が複数 dir に散っている、
または dir 名と `wave_id` が異なるためである。

**欠測の向きは経路ごとに違う。**

| 欠落経路 | 失敗率への向き |
|---|---|
| wrapper / producer の起動前 `rc=2` (argv 契約違反、prompt 不読、既存 output) | **必ず失敗が消えるため下向き** |
| launcher を経ない起動 | 成否とも消えるため **不定** |
| directory の撤去・root 外保存・path filter | 成否とも消えるため **不定** |
| receipt 公開前の launcher kill / host 障害 | 失敗が消えるため下向き |

**したがって本一覧の率は「残存 receipt 条件付きの非受理率」であり、
全投入の失敗率に対する上界とも下界とも言えない。**

## 5. 段別 実測 (physical receipt 397 件)

所要時間は **launcher が観測した 1 job の elapsed** である
(`wall_clock_scope = launcher_start_to_receipt_fields_finalized`)。
段の所要時間ではなく、投入待ち・lease 待ち・親の prompt 作成と成果物統合を含まない。

| 段 | n | 非受理 (物理) | 率 | 論理 job | 非受理 (論理) | elapsed p50 | p90 | p95 | max | wave 数 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plan | 46 | 3 | 6.5% | 45 | 2 (4.4%) | 1,124 s | 1,955 | 2,184 | 2,452 | 42 |
| consult | 102 | 12 | 11.8% | 102 | 12 | 984 s | 1,479 | 1,546 | 2,650 | 44 |
| author | 84 | 1 | 1.2% | 84 | 1 | 695 s | 1,269 | 1,479 | 2,063 | 35 |
| review | 63 | 2 | 3.2% | 63 | 2 | 539 s | 750 | 786 | 1,098 | 34 |
| fix | 82 | 2 | 2.4% | 82 | 2 | 326 s | 866 | 1,020 | 1,561 | 31 |
| focus | 20 | 2 | 10.0% | 20 | 2 | 444 s | 697 | 751 | 755 | 13 |
| **計** | **397** | **22** | **5.5%** | **396** | **21** | | | | | **61** |

消費 job-hours の合計は 83.3 h だが、**これは wave の経過時間ではない。**
段は並列に走るため、段の完了時間はおおむね並列 job の最大値と親側 overhead である。

### 分位の読み方 (n が支える強さ)

`p95` は nearest-rank であり、上側に残る観測数は plan 2 / consult 5 / author 4 /
review 3 / fix 4 / **focus 1** である。focus の既定層 (n=12) では **p95 = p99 = max = 755 s**
に潰れており、この n で最大値に潰れない上限は p90 までである。
**focus は p50 / p90 / max だけを読むこと。**

また 397 行は 61 wave に属し、上位 10 wave が 153 行 (38.5%) を占める。
**独立標本数として 397 をそのまま使うと不確実性を過小評価する。**

### 段は他の層と交絡している

- **sandbox と完全交絡:** author / fix は全件 `workspace-write`、
  plan / consult / review / focus は全件 `read-only`。分離できない。
- **model:** sol 344 / luna 52 / 不明 1。**effort:** high 248 / max 147 / medium 1 / 不明 1。
- **CLI 版:** `codex-cli 0.146.0` が 348 件 (非受理 21)、`0.147.0` が 49 件 (非受理 1)。
  **時代層が違う。**
- `base_commit` は 2026-08-10 18:39 〜 08-12 14:20 の短期間に分布するが、
  実装が高速に変化した cohort である。

**したがって段間の差は記述であって、段への帰属ではない。**
「plan は fix の 3 倍時間がかかっている」は言えるが、「plan だから 3 倍かかる」は言えない。

## 6. 段内でプールすると tail が消える (consult の実例)

| consult | n | 非受理 | elapsed p95 | calls p95 | tokens p95 | tokens max |
|---|---:|---:|---:|---:|---:|---:|
| luna | 52 | 6 | 1,476 s | 60 | 1,017,768 | 1,101,163 |
| sol | 50 | 6 | 1,733 s | 79 | 515,701 | 642,979 |
| プール | 102 | 12 | 1,546 s | 72 | 649,938 | 1,101,163 |

**プールした p95 は sol の時間 tail と luna の token tail を同時に隠す。**
さらに後述のとおり、**token 上限で殺された consult 3 件は全件 luna である。**
段だけで括った上限は、段内の一方の lane を選択的に殺しうる。

## 7. 非受理の内訳 (multi-label、receipt の field 値そのもの)

`accepted` は `tools/codex_worker_launch.py:1221-1230` の 8 条件の連言であり、
同 `:1541` が「`accepted` な job に `limit_trigger` があれば例外」を強制するため、
**上限で切られた job が `accepted` に紛れ込む経路はない**
(現標本の `accepted` 内に、最終 attempt の上限・metering・termination 問題は見つからなかった)。

1 行が複数の受理条件を同時に破りうるため、下表は排他分類ではなく **multi-label** である。

| 段 | 非受理 | label (重複あり) |
|---|---:|---|
| plan | 3 | `resource:max_model_calls` ×2、`codex_exit_code=-15` ×1 |
| consult | 12 | `codex_exit_code=1` ×4、`evidence_status=invalid` ×3、`resource:max_cli_reported_tokens` ×3、`validator_rc=1` ×2 |
| author | 1 | `validator_rc=1` ×1 |
| review | 2 | `evidence_status=invalid` ×2 |
| fix | 2 | `evidence_status=invalid` ×1、`validator_rc=1` ×1 |
| focus | 2 | `evidence_status=invalid` ×1、`codex_exit_code=1` ×1 |

**非受理 22 件のうち資源上限は 5 件だけである。**
残り 17 件は出力・evidence・Codex 終了に起因し、**上限値を変えても解消しない。**
5.5% を「資源不足率」と読むと、上限引き上げの効果を約 4 倍に過大評価する。

**これは field 値の頻度表であって、失敗型の taxonomy ではない。**
D100 が [T-183] へ送った「失敗型の早期分類・safety-filter 判定・回復経路」は本一覧の対象外であり、
本表から retry / 早期停止 / 回復の判断を導いてはならない。

## 8. 発効していた上限と、上限に当たった 5 件

397 件の上限組は **既定 306 / 引き上げ 90 / 引き下げ 1** である
(引き下げは `t798-t799-finalize` の author が wall 1800 s・calls 60)。
「非既定 = すべて引き上げ」ではない。

既定 (`wall 3600 s` / `calls 100` / `tokens 1e6`) が効いていた 306 走での上限到達:

| 段 | n | 非受理 | elapsed max / 上限 | calls max / 上限 | tokens max / 上限 |
|---|---:|---:|---:|---:|---:|
| plan | 41 | 3 | 0.681 | **1.000** | 0.675 |
| consult | 88 | 10 | 0.736 | 0.920 | **1.101** |
| author | 62 | 1 | 0.444 | 0.970 | 0.343 |
| review | 50 | 1 | 0.305 | 0.460 | 0.397 |
| fix | 53 | 0 | 0.288 | 0.600 | 0.275 |
| focus | 12 | 2 | 0.210 | 0.380 | 0.235 |

打ち切られた 5 件:

| wave | 段 | lane | 打ち切り軸 | elapsed | calls | tokens | CLI |
|---|---|---|---|---:|---:|---:|---|
| dev-wave-t139-manifest-land2-s2 | consult | luna | `max_cli_reported_tokens` | 1,384 s | 50 | 1,101,163 | 0.146.0 |
| dev-wave-t812-lease-self-renew | consult | luna | `max_cli_reported_tokens` | 1,025 s | 41 | 1,017,768 | 0.146.0 |
| t810-node-variance | consult | luna | `max_cli_reported_tokens` | 964 s | 42 | 1,030,999 | 0.146.0 |
| dev-wave-t756-trace-v2 | plan | — | `max_model_calls` | 992 s | 100 | 419,857 | 0.146.0 |
| dev-wave-t786-docs-budget | plan | — | `max_model_calls` | 1,377 s | 100 | 470,559 | 0.146.0 |

**5 件とも `codex-cli 0.146.0` であり、`0.147.0` の 49 件には資源打ち切りが無い。**

### この表から言えること・言えないこと

**言えること:** 現行の 3 軸同時上限の下で、`max_wall_clock_s` の発火は **0 件**であり、
実際に job を殺したのは D100 が「observable proxy であって hard cap とは名乗らない」と
明記した 2 軸だけである。

**言えないこと:** 「wall-clock には余裕がある」。これは **competing risk 下の観測**である。
proxy 2 軸で 964〜1,384 秒の時点で殺された 5 件が、その上限が無ければ 3,600 秒までに
完了したかは観測できない。同様に、打ち切られた軸の最大値は censoring されており、
plan の `calls max = 100` は「100 で足りた」ではなく「100 で殺した」である。

また上限の上書きは **内生的**である (難しい workload を見越して親が上げる)。
既定層と上書き層を単純比較してはならない。

## 9. 親が選んだ非既定値の分布 (90 件の引き上げ + 1 件の引き下げ)

| 軸 | 選ばれた値 (件数) |
|---|---|
| `max_wall_clock_s` | 5400 (49)、3600 (26)、7200 (15)、1800 (1) |
| `max_model_calls` | 220 (25)、200 (23)、100 (20)、160 (14)、300 (4)、他 5 値 (5) |
| `max_cli_reported_tokens` | 1e6 (55)、3e6 (24)、2e6 (7)、4e6 (5) |

**これは「親が必要と判断した値」の実測であって、必要量そのものの実測ではない。**
上限値は receipt の `limits` に記録されている。
**記録がないのは値ではなく、その値を選んだ理由と、選ぶ前に何を見たかである。**

## 10. 主張上限 (この一覧から言ってはならないこと)

- receipt の値は `recorded_values_semantics` が明記するとおり
  **Codex CLI rollout の記録値であり served model の attest ではない。**
- elapsed は 1 job の launcher 観測値であり、段の所要時間でも wave の経過時間でもない (§5)。
  rate limit 待ちと compaction が含まれうるが、receipt に発火 field がないため
  **どの job に何秒含まれたかは確認できない。**
- 失敗率は残存 receipt 条件付きであり、全投入への上下界ではない (§4)。
- 段間差は段への帰属ではない (§5)。
- 小標本段の p95 を強く読んではならない (§5)。
- 上限到達値は competing risk と censoring の下にある (§8)。
- 本一覧は canonical stage matrix ではない。**model × reasoning × resource × retry の
  policy を発行していない。** 他タスクの待ち解除根拠に使ってはならない。

---

# 択一の再提示

## 11. 実測が支持する結論 (親の選好を含まない)

1. **既定値は名目である。** 397 起動のうち 91 件 (22.9%) が非既定の上限組で走った
   (引き上げ 90、引き下げ 1)。値は receipt に記録されるが、
   **選んだ理由と選ぶ前に見たものは記録されていない。**
2. **現行 3 軸同時上限の下で、実際に job を殺したのは proxy 2 軸だけである** (§8)。
   `max_wall_clock_s` の発火は 0 件。ただしこれは wall の余裕の証拠ではない。
3. **上限引き上げで救えるのは非受理 22 件のうち 5 件だけである** (§7)。
4. **段だけで括った上限は段内の一方の lane を選択的に殺しうる** — token 打ち切り 3 件は
   全件 luna (§6、§8)。
5. **打ち切られた軸の必要量は観測できない** (censoring、§8)。
6. **前回の延期理由 (証拠なし) は消えた** (§1)。

## 12. 実測が答えないこと (裁定が要る理由)

- 資源上限が何のためにあるのか (暴走の安全網か、予算配分か)。
- 段別化が必要かどうか。実測が示すのは段別の**記述差**であって、段が原因だという証拠ではない。
  そもそも打ち切りの偏りは lane (model) 側にも同じだけ現れている。
- 権威をどこに置くべきか。**resource authority の drift は一度も測っていない。**
  D266 が段 5 pin 拡大を却下したときの「drift 未観測」は `docs/dev-wave/workers.md` の
  reasoning 値についての観測であり、resource へは及ばない。
- **具体的な上限値。** competing risk と censoring のため、本一覧からは導けない (§14)。

## 13. 択一 (直交する 5 軸に分解する)

前回提示の案は、権威の所在・既定の形・override の可否・軸の選択を 1 つの選択肢に混ぜていた。
これらは併用可能であり排他ではない。**組合せて 1 つの構成を選ぶ形へ分解する。**

### 軸 1 — いつ決めるか

| | 選択肢 | 実測がどう関わるか |
|---|---|---|
| 1a | **今決める** | 前回の延期理由 (証拠なし) は消えた |
| 1b | **[T-183] 完了後へ延期** (前回の親推奨) | 非受理 22 件のうち 17 件は資源以外であり、その分類は [T-183] 所有。resource 単独で決めても救える範囲は狭い |
| 1c | **§14 の測定を先に行ってから決める** | 値を決めるには censoring を解く測定が要る |

### 軸 2 — 権威をどこに置くか

| | 選択肢 | 実測がどう関わるか |
|---|---|---|
| 2a | **権威を置かない** (非権威の運用既定のまま) | 現状。receipt に値は残るが docs 側の正本がない |
| 2b | **docs 権威 (`DW-O01`) + launcher 導出 + `authority_snapshot` 束縛** | reasoning と同じ結線。**必要性は未測定** |

### 軸 3 — 既定の形

| | 選択肢 | 実測がどう関わるか |
|---|---|---|
| 3a | **全段共通の単一既定** (現状) | 22.9% が非既定で走っている実態と合っていない |
| 3b | **段別の既定表** | 段別の記述差は大きいが、段への帰属は不可 (§5) |
| 3c | **段 × lane 別の既定表** | 打ち切りの偏りは lane 側にも現れる (§6)。ただし lane は段 3 にしか無い |
| 3d | **既定なし・投入時に明示必須** | 非既定が常態である実態とは整合するが、argv 契約違反 (`rc=2`、receipt すら残らない失敗) の面を広げる |

### 軸 4 — どの軸を段別化するか

| | 選択肢 | 実測がどう関わるか |
|---|---|---|
| 4a | **3 軸すべて** | wall の発火 0 件は competing risk 下の観測であり、wall を触らない根拠にはならない |
| 4b | **`model_calls` と `tokens` だけ** | 実際に殺したのはこの 2 軸 |
| 4c | **段別化しない** | 現状維持と同じ |

### 軸 5 — 親の override

| | 選択肢 | 実測がどう関わるか |
|---|---|---|
| 5a | **許す** (現状) | 91 件が実際に使っている (引き下げ 1 件を含む) |
| 5b | **許すが理由の記録を要求する** | 記録されていないのは値ではなく選択理由 (§9) |
| 5c | **禁止する** | 既存 91 件の運用を止める。実測に支持も反対もない |

### 成立する組合せの例

- **現状維持** = 1a + 2a + 3a + 4c + 5a
- **延期** = 1b ([T-183] 後に再評価)
- **測定先行 (親推奨)** = **1c** + 2a + (3・4 は測定後に決める) + 5a
- **hybrid** = 1a + 2a + 3b + 4b + 5a
- **権威化** = 1a + 2b + 3b + 4b + 5a
- **明示必須** = 1a + 2a + 3d + 4b + 5c

## 14. 親の推奨 — 測定先行 (1c)

**推奨 = 1c + 2a + 5a。段別化 (軸 3) と対象軸 (軸 4) は、下記の測定の後に決める。**

前回 (2026-08-10) の推奨は「[T-183] 完了後にまとめて 1 本の設計 wave で扱う」だった。
**実測を経て、これを「測定先行」へ改める。** 理由:

- 上限値を今決めるための情報が足りない。打ち切られた 5 件の必要量は censoring されており、
  「p95 × 2」も「親の上書き最頻値」も必要量の測定ではない (§8、§9)。
- 一方、[T-183] を待つ理由も弱まった。resource で救えるのは 22 件中 5 件で、
  残りは [T-183] 所有だが、**resource の測定自体は [T-183] と独立に実行できる。**

### 値を決めるために要る測定 (設計)

1. **打ち切られた job の追走。** `stop_reason` が資源 3 軸のいずれかだった 5 件を、
   同一 prompt・同一 base commit で **上限を外して** 再走し、完走に要した
   `model_calls` / `cli_reported` / elapsed を測る。これが唯一の直接的な必要量測定である。
   n=5 と小さいが、censoring を解く唯一の経路である。
2. **事前登録した cap sweep。** 段 × lane を層にし、上限を段階的に下げて
   打ち切り率が立ち上がる点を探す。事前登録 (対象段・水準・停止規則) を先に凍結する。
3. **層の固定。** 測定は CLI 版を固定して行う (現データは 0.146.0 と 0.147.0 が混在し、
   非受理率が 6.0% と 2.0% で異なる)。

**これは [T-180] の機構を変えない。** 上限を外した再走は既存の `--max-*` 引数で行える。

### 2a (権威を置かない) を維持する理由 — これは運用上の選好である

2b は docs 権威・hash 束縛・pin テストを増やす防御的堅牢化であり、**その必要性を測っていない。**
未測定の機構を先に作らない、というのが本 repository の既定である。
drift の実害が観測されたら 2b へ移るべきである。

### この推奨が誤りうる点

測定 1 は n=5 で、しかも 5 件とも `codex-cli 0.146.0` かつ 4 件が特定の段・lane に偏っている。
追走しても一般化できる保証はない。測定 2 は wave を止めずに走らせられないなら費用が大きい。
**「測定してから決める」が「決めない」に転化する危険**が最大のリスクである。

## 15. 成果物影響 (DW-G05)

**certified な選択結果・材料レポート・試行台帳の値は、いずれの選択肢でも変わらない。**
資源上限は correctness 判定・受理集合・proof chain のいずれにも関与せず、
D100 自身が予算・可観測性の機構と位置づけている。
ただし **下流の証拠集合は条件付きで変わる。**

| 選択肢 | 変わるもの |
|---|---|
| 現状維持 | 何も変わらない。既定層 306 走で 1.6% の打ち切りが続き、その分 wave が 1 巡やり直しになる |
| 1c (測定先行) | 追走 5 件分の receipt が増える。既存 397 件の値は変わらない |
| 3b / 3c (段別既定) | receipt の `limits` field の値。打ち切り境界が動くため **`accepted` / `not_accepted` の集合が変わりうる** |
| 2b (docs 権威) | `authority_snapshot.sections` が増え、**receipt の `digest` が変わる**。既存 receipt との digest 比較が世代を跨げなくなる |
| 3d (明示必須) | 起動前 `rc=2` が増えれば **receipt を残さない投入が増え、本一覧のような集計の証拠が薄くなる** |
| 5b (理由の記録) | receipt に新 field が増えれば `schema_version` が上がり、既存 397 件との突合に版差が入る |

## 16. 本 wave の限界

- 段 3 の 2 レンズは read-only sandbox で静的検査のみを行った。pytest を実走していない。
- 内容判定は必須 field の存在検査であり、producer の `check-receipt` による完全性検証は
  行っていない (§2)。
- 打ち切られた job の追走を行っていないため、必要量は測っていない (§8)。
- 集計器は repo 外にあり、テストを持たない。本一覧の数値は集計器の正しさに依存する
  (段 3 で 1 件の実装バグ — 被覆率の分子が内容判定前の path から作られていた — が
  発見され、修正した)。

## 17. 追加の裁定項 — dev-wave 文書に receipt.json の所在がない

本 wave が探索的に一次資料を見つけたこと自体が、手順側の欠落を示している。
`docs/dev-wave/` のどの節も `receipt.json` の所在と field に触れていない。
2026-08-10 の前回 [T-184] wave が「台帳に資源上限の証拠は無い」と誤った直接原因である。

**反映を試みたが予算に入らなかった。** 反映先として適当な `DW-O02` (job artifact) は
単節予算 1,000 bytes に対し 508 bytes で余裕があるが、`docs/dev-wave/**` の
**L1.5 層は予算 9,566 bytes に対し実測 9,564 bytes、残余 2 bytes** である。
3 行 (273 bytes) の追記で L1.5 が 9,837 bytes となり `check_docs` が赤になった
(編集は revert 済み)。

自己改善契約は「予算値を上げる変更は通常の自己改善に含めず、理由付きの独立審査対象にする」と
定めるため、次をユーザー裁定へ返す。

| | 選択肢 |
|---|---|
| a | **見送る** (現状維持)。次に工数を数える wave も一次資料を自力で探すことになる |
| b | **L1.5 の他節を縮約して 273 bytes を空ける**。どの節を縮めるかは別途裁定が要る |
| c | **`docs/README.md` の地図へ書く** (dev-wave の層予算の外)。ただし dev-wave の読み込み導線には乗らない |
| d | **L1.5 予算を引き上げる**。独立審査対象であり、本 wave の権限外 |

親の推奨 = **c**。receipt は artifact であり、その所在は文書地図の担当である。
dev-wave の層予算を触らずに済み、`docs/README.md` は
「文書・成果物・運用スクリプトの地図」を明示的に担っている。

## 18. 本 wave が発行していないもの

- canonical stage matrix (model × reasoning × resource × retry) — **発行していない**
- 起動前 policy — **発行していない**
- retry policy — [T-183] 依存のまま、**触れていない**
- 失敗型の早期分類器・safety-filter 判定・回復経路 — [T-183] 所有、**設計していない**

したがって [T-316] / [T-665] / [T-662] の待ちは解除されない。
