## 総括

1. **Critical — P3 の受領証は retry 権威を閉じていない。** `classify_attempt(...reason=None)` 後、性能値を見てから terminal の `failure_reason="preempted"` を後付けでき、次 slot が受理される。受理 attempt・session median・床値が変わる。S4/core adapter の scope 内。`trial_registry.py:3134-3169,3385-3418,2253-2262,2361-2383`

2. **Critical — P4 の「後続 attempt は診断専用」が集計へ接続されていない。** 現行 `assemble_result()` は全 `session` を `cell_stats()` に渡すため、成功した診断 attempt が欠測 repetition を置換できる。`n_valid`、medians、標準偏差、floor が変わる。S5 の scope 内。`s8b_floor_campaign.py:5528-5529,5679-5703`; `s8b_floor_stats.py:273-295`

3. **High — §10.5 の単一 registry は P2 では満たせない。** 既存 shared root は現存 inode 間の競合しか防がず、削除・同一 bytes 再構成を明示的に検出不能とする。同一 freeze の第二 root に別 slot 履歴を持たせられる。§10.5 実装完了を主張するなら scope 内。`s8b_holdout_admission.py:4-11,4054-4058`; `src-design-10.5-10.6.md:21-26`

4. **High — D672 の受理集合チェック C01–C12 は列挙不完全かつ一部誤読。** 特に `create_attempt_registry_genesis` の後段 rebinding は C03 を落とさず、C09/C10 の call は live でなく dead code でも数えられる。facade の実 callable と acceptance reason が乖離し得る。S2/D672 の scope 内。`s8c_preregistration_evidence.py:293-298,1624-1646,1695-1746,2207-2214,2250-2257`

5. **High — completion-conditioned selection は「偏り得る」が、親 brief の「床値が楽観側へ偏る」は一般化不能。** floor は分散 RSS と stock median の max であり、選択で上にも下にも動く。欠測固定なら数値は偏らず null になるが、nonnull cell だけを見る下流解析には survivorship bias が残る。`brief.md:25-26`; `s8b_floor_stats.py:325-405`

6. **Medium — P5 の per-round slot と既存 cell-global retry ticket の対応が未定義。** `(round, attempt_ordinal)` は各 round で ordinal 1 を持つ一方、既存 `cell::retryN` は cell 全体で N が増える。この全単射が無いと別 round の slot/ticket を誤消費する。S3/P5 の scope 内。`s2-plan.md:259-279`; `s8b_floor_campaign.py:5114-5126,5518-5521`; `s8b_holdout_admission.py:1133-1141`

7. **Medium — 親 brief の実測表には誤アンカーと検査漏れがある。** C03 は `:1613-1778` まであり、`brief.md:55` の `:1613-1730` は top-level 名・module 属性集合を落としている。また I1 は実 attempt registry のある `output/s8c-preregistration/**` を対象に含めていない。`brief.md:33,45-62`; `trial_registry.py:54-65`; `s8c_preregistration_evidence.py:1748-1778`

以下、`brief.md` と `s2-plan.md` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/` 配下を指す。

## 1. 絶対規律 2 — 値を見た後の理由付け替え

### 攻撃手順 A: terminal reason の後付け

現行状態機械を共通 core としてそのまま抽出すると、次が成立する。

1. `reserve_attempt_slot()` で attempt 0 を開始する。
2. `classify_attempt(pre_observation_failure_reason=None, ...)` を呼ぶ。受領証は create-only で作られるが、理由は `None` である。`trial_registry.py:3134-3181`
3. `begin_attempt_observation()` を呼ばず、同一 process または直接 raw path から性能値を見る。現行 API 自身も OS レベルの read-before-event を証明しないと明記している。`trial_registry.py:3143-3150,3247-3253`
4. 値が望ましくなければ、`record_attempt_terminal(terminal_status="retryable-failure", failure_reason="preempted", report_sha256=<非null>)` を呼ぶ。
5. terminal builder は明示 `failure_reason` を分類理由より優先する。`trial_registry.py:3385-3408`
6. null matrix は terminal 側の理由が retryable 集合に入ることだけを検査し、分類受領証の `None` と一致することを要求しない。`trial_registry.py:2253-2262`
7. observation-start が無いため、次 slot の start は受理される。`trial_registry.py:2361-2383`

したがって、plan の「create-only classification receipt だけから retry を認可」は、terminal の retryable status/reason が受領証理由と exact 一致しない限り成立しない。`s2-plan.md:9,373-398`

しかも 8c の現受理集合は、閉集合外の `"correctness-failure"` を classification 段では受理し、terminal 段で初めて拒否する。これを共通 core で classify-time 拒否へ変えると D672 を破る。`test_trial_registry.py:5733-5753`; `src-D672.md:3-8`

plan の `TransitionPolicy` にはこの差を表す policy が無い。`require_previous_terminal`、`forbid_retry_after_observation` 等だけで、分類理由の検査時点・terminal echo 一致を表せない。`s2-plan.md:120-124`  
したがって P1 の profile は、現状のままなら「8c を締めて受理集合を変える」か「8b を緩いままにする」の二択になる。

### P3 の 7 穴は完全でない

少なくとも次の二件が追加である。

- **8件目: receipt→registry row の crash cut。** receipt は `:3176-3181` で先に作られ、classification row は `:3230-3234` で後から append される。この間の crash で orphan receipt が残る。receipt 単独を権威にすれば不正 retry、再分類を試みれば create-only 衝突になる。plan の `AttemptStore` も `create_receipt()` と `atomic_update()` が別操作である。`trial_registry.py:3170-3181,3199-3234`; `s2-plan.md:136-145,400-412`

- **9件目: terminal reason override。** 上記攻撃 A のとおり、分類理由と別の retryable 理由を terminal で付けられる。plan の7件は同一 process の read 問題には触れるが、この受理述語上の不一致を列挙していない。`trial_registry.py:3385-3408`; `s2-plan.md:402-410`

さらに現行 8b では、pre-probe 競合時は `measure_fn` wrapper 内の ticket 消費へ到達せず session を invalid terminal にできる。`s8b_floor_campaign.py:4980-5014,5235-5248`  
その invalid session は retry trigger になる。`s8b_floor_campaign.py:5155-5169,5381-5391`  
新 registry が「slot reserve」と既存 ticket consumption を同一 transaction にしなければ、registry と admission で消費済み attempt 集合がずれる。

## 2. D672 — C01–C12 の漏れ・誤読

### C03

plan が列挙した13関数、canonical tuple、runtime fields、acceptance/producer reachability、top-level 6名、module属性集合は概ね実コードと一致する。`s2-plan.md:226-251`; `s8c_preregistration_evidence.py:1624-1773`

ただし、次の誤りがある。

- plan は「`_functions()` が後段 rebinding を除外する」と書くが、C03 の存在検査が使う module-level `_functions()` は単に最後の `FunctionDef` を辞書化するだけである。`s2-plan.md:207`; `s8c_preregistration_evidence.py:293-298`
- rebinding を除外するのは reachability explorer 内の別 `_functions()` だけである。`s8c_preregistration_evidence.py:825-846`
- `create_attempt_registry_genesis` は required function ではあるが、acceptance reachability 8件にも producer reachability 4件にも含まれない。`s8c_preregistration_evidence.py:1624-1641,1695-1708,1731-1741`

従って次の mutation は C03 を落とさない。

```python
def create_attempt_registry_genesis(...):
    ...
create_attempt_registry_genesis = malicious_replacement
```

plan の「six facade 全てについて同名 rebinding がないこと」「re-export/rebinding fixture が C03 UNSATISFIED」という想定は、少なくともこの関数では evaluator の実受理集合と一致しない。`s2-plan.md:479-483`

### C02/C04/C08/C09/C10 の未列挙要求

- C02 は trial_registry の live calls/文字列だけでなく、proposal producer の `_invocation_namespace` が `arm` と `digest` を f-string に使用し、3 consumer がその関数を live call することも要求する。`s8c_preregistration_evidence.py:2029-2047`  
  `s2-plan.md:214` の表は「trial_registry への要求」としては正しいが、C01–C12 全要求の列挙ではない。

- C04 は `forbid_trial_restart` だけでなく、workload graph が `mark_experiment_indeterminate` にも到達することを要求する。`s8c_preregistration_evidence.py:2055-2074`; `s2-plan.md:216`

- C08 は関数存在・一般的な P/C dataflow だけではない。`effective_commit` の live assignment 禁止、exact-parent call がちょうど1件、引数 AST の形、全 reachable validator call の effective argument 制約がある。`s8c_preregistration_evidence.py:1811-1868,1875-1924`; `s2-plan.md:220`

- C09/C10 の acceptance call 検査は `_called_names()` であり `_live_called_names()` ではない。literal-false branch や return 後の call でも存在扱いになる。plan の「直接 live call」という表現は実受理述語より強い。`s8c_preregistration_evidence.py:301-311,2207-2214,2250-2257`; `s2-plan.md:221-222,253`

- C03 の top-level 6名は値・型・文字列内容を検査せず、名前の存在しか見ない。module field 集合も全 AST の属性名・文字列の和であり、dead code の文字列で満たせる。`s8c_preregistration_evidence.py:1499-1513,1748-1768`

したがって C01–C12 の `(id,status,reason)` current-tree snapshot は必要だが、「8c の受理集合不変」の十分条件ではない。`s2-plan.md:479-485`

### `orchestrator/tests/` にある追加 pin

`test_trial_registry.py` 以外にも影響する test がある。

- `test_p3_autonomous_workload_trial.py` は genesis bytes hash を effective binding に入れ、facade 呼出し順序を monkeypatch で監視し、attempt/lifecycle row の値と例外文言を pin する。`test_p3_autonomous_workload_trial.py:6482-6540,6962-7041,7309-7370,7502-7586`
- `test_s8c_preregistration_predicates.py` は HEAD の production source blobs を snapshot へ複製し、C01–C12 の exact status/reason と C03/C08 negative controls を pin する。`test_s8c_preregistration_predicates.py:140-167,187-249,2883-3134`
- `test_s8c_preregistration_invariant.py` は condition ごとの function/path 集合を exact に固定する。`test_s8c_preregistration_invariant.py:45-108,459-498`
- `test_ccbench_spawn_sites.py` は `trial_registry._git` の process spawn がちょうど1件である構造を pin する。`test_ccbench_spawn_sites.py:130-156`
- `test_reflux_formal_consumer.py` は `trial_registry.py` を固定14-file source scan の対象に含める。新 core はその固定集合外になる。`test_reflux_formal_consumer.py:22-37,815-841`

full `trial_registry.py` source bytes の literal SHA pin は見つからなかった。一方、event canonical hash の独立 golden は存在する。`test_trial_registry.py:6170-6186`

## 3. S5 — 再抽選バイアスと現行統計

plan の「完了条件が性能と相関すれば informative censoring」という主張は正しい。ただし、`C ⟂ Y`、すなわち crash が性能値・負荷・温度等から独立なら \(P(Y\mid C=1)=P(Y)\) であり、completion-conditioned であることだけから偏りは導けない。`s2-plan.md:416-418`

さらに、親 brief の「床値が楽観側へ偏る」は一般には誤りである。

- floor は `max(sqrt(s_c²+s_stock²), wired_min_rel_floor*m_stock)`。`s8b_floor_stats.py:325-390`
- 完了 attempt の選別で分散が縮めば floor は小さくなり得る。
- stock の低 throughput が欠落して `m_stock` が上がれば相対 floor は大きくなり得る。
- よって方向はデータ依存で、保証できるのは「estimand が変わり得る」までである。

### plan の代案 1–5 と現行集計

| plan 項目 | 現行統計との整合 |
|---|---|
| 1. attempt 0 を主 attempt に固定 | 単独では集計規則にならない。primary-only projection が必要。 |
| 2. post-observation crash を欠測にする | fail-closed 集計と整合。`n_valid<n_sessions` となり cell は invalid。 |
| 3. 後続 attempt は診断専用 | 現行のままでは不整合。全 `session` を集計するため、成功診断が主値へ昇格する。別 `attempts` 投影へ隔離すれば整合可能。 |
| 4. 同一 attempt の checkpoint continuation | 現行 admission/集計とは不整合。per-rep cursor と capability recovery が無い。 |
| 5. 最初の完了値へ置換 | 現行 retry 集計と機械的には整合するが、元の床値 estimand は保たない。 |

現行 retry は invalid planned session の後、同じ round に valid session が現れるまで実行する。`s8b_floor_campaign.py:5381-5391`  
`cell_stats()` は invalid session を除外し、valid median がちょうど `n_sessions` 個なら cell を valid にする。`s8b_floor_stats.py:273-295`  
例えば planned 3件中1件 crash、診断 retry 1件成功なら、valid median は再び3件となり、診断値が完全に欠測を置換する。

### 欠測を固定した場合の床値

欠測は artifact 全体の schema errorにはならず、数値 floor が fail-closed になる。

- non-stock cell の欠測: その pair は `null`。一つでも pair が `null` なら `scalar_alt` も `null`。`s8b_floor_stats.py:374-403`
- stock cell の欠測: 当該 holdout の全 pair、`scalar_alt`、`scale_ref` が `null`。`s8b_floor_stats.py:342-365`
- verifier は raw sessions から同じ invalid/null を再計算できれば受理する。`s8b_floor_stats.py:913-1012`

従って「欠測 repetition を受け入れるか」への答えは、**artifact としては受け入れるが、cell は失格し数値 floor は得られない**、である。

欠測自体が性能依存なら missingness は informative である。ただし null を値として代入しない限り、当該 cell の数値 floor を直接押し上げたり下げたりはしない。nonnull cell だけを後段で集計すれば、そこで survivorship bias が生じる。

## 4. rep 単位の部分観測と観測不変性

8b の1 session/attempt は `measure_point(..., reps=self.reps)` の一呼出しで複数 rep を実行する。`s8b_floor_campaign.py:6790-6817`  
返却後に throughputs を取り出し、`assess_session()` が完全な rep 列の median を作る。`s8b_floor_campaign.py:5263-5303`; `s8b_floor_stats.py:126-164`

問題は、journal の session record が全 rep 完了後にしか書かれないことである。`s8b_floor_campaign.py:5340-5376`  
したがって途中 crash では、registry/journal 上は primary 未確定でも、先行 rep の値が raw output、ログ、operator 画面等へ既に露出している可能性がある。

その後続 slotを primary にすれば、まさに「部分値を知った後の再抽選」である。plan の診断専用方針自体はこれを避けるが、前節のとおり現行 `assemble_result()` が診断値を集計から除外しない。`s8b_floor_campaign.py:5679-5703`

checkpoint continuation も現行では成立しない。

- ticket consumption marker は create-only で、一度 crash すると再消費を拒否する。`s8b_holdout_admission.py:3819-3826`
- capability はその場で `protocol_reps` 回分として発行されるが、残り rep 数を永続化しない。`s8b_holdout_admission.py:3828-3838`
- resume 時に「同一 attempt の rep k+1 からのみ継続」を証明する cursor/WAL が無い。

よって plan の代案4は現状では推測上の選択肢であり、実装可能な既存経路ではない。部分 rep の再実行禁止、completed rep hash、next rep index、残余 capability の復元が無ければ観測不変性を証明できない。

## 5. §10.5 の単一 registry

P2 の裏取り結果は正しい。

- shared root は Git common dir から決まり、linked worktree 間で同じ inode を競合させる。`s8b_holdout_admission.py:427-444`
- `_locked()` は既存 `ledger.lock` に `flock` を取るだけで、履歴を保存しない。`s8b_holdout_admission.py:504-524`
- current-state inspector は削除・同一 bytes 再構成を検出不能と自認する。`s8b_holdout_admission.py:8-11,4054-4058`

この wave が §10.5 を「満たした」と言える条件は、最低でも次の三点が同時に成立すること。

1. freeze identity を key とする binding が canonical root path と genesis exact bytes hash を持つ。`src-design-10.5-10.6.md:21-24`
2. binding が content commit または effective binding record に固定され、全 Git history/ref を走査して同一 freeze の別 path/genesis、削除再構成、別 ref の第二 rootを拒否する。8c の既存実装は相当する全-history scan を持つ。`trial_registry.py:2778-2837`
3. measurement と結果 acceptance の live entrypoint が、その履歴 gate と current shared-root bytes の一致を必ず通る。

これを実装しないなら、adapter/core 完成とは記録できても「§10.5 完了」とは記録できない。brief の scope-out は正式測定と design-source pin であり、registry root の履歴 pin は scope-out に含まれていない。`brief.md:28-29`  
§10.6 により正式 gate を閉じたままにすることは必要だが、それ自体は §10.5 を満たした証拠ではない。`src-design-10.5-10.6.md:28-38`

## 6. P5 の追加境界

plan は `campaign_id` を除外して freeze-wide identity を保つ点では親 P5 より正しい。`brief.md:78-79`; `s2-plan.md:23,259-270`

ただし、次の対応が未定義である。

- 新 slot: `(cell, round, attempt_ordinal)`。各 round に attempt 1 が存在する。`s2-plan.md:263-279`
- 現行 ticket: `cell::retry1 ... cell::retryR`。cell 全体で ordinal は一度しか存在しない。`s8b_holdout_admission.py:1133-1141`
- runner の retry ordinal も cell-global で増える。`s8b_floor_campaign.py:5114-5126,5518-5521`

例えば round 0 の slot a1 が `retry1` を消費した後、round 1 の slot a1 は `retry2` に対応しなければならない。この対応を v2 ledger に一対一で封印しないと、同じ ticket の二重束縛または wrong-round consumption が起きる。global cap を数えるだけでは不十分である。

## 7. 親 brief の実測値検算

| 親の主張 | 静的検算 |
|---|---|
| `trial_registry.py` 全5,992行 | 正しい。 |
| attempt 全体 `1818-3555`、約1,738行 | physical 1,738行で正しい。 |
| state `1818-3431`、1,614行 | physical 算術は正しいが、最後の関数は `3429` で終わり、`3430-3431` は空行。実 function span は1,612行。 |
| acceptance `3432-3557`、126行 | 関数は `3432-3555` の124 physical行、123 nonblank行。`3556-3557` は空行。D672 の「約123行」は nonblank 数として正しい。 |
| `_parse_attempt_slot :1869-1908` | 実関数は `1869-1906` の38行。`1907-1908` は空行。 |
| receipt dir 直書き `:2523,:3173` | `:2523` は receipt の**読取 path**、書込 path 構築は `:3173`、実 create-only write は `:3176-3181`。 |
| C03 `:1613-1730` | 不完全。実 evaluator は `:1613-1778`。top-level 名と module 属性/文字列集合が `:1748-1773` にある。 |
| C02 `:1967-2000` 付近 | call map 前半だけ。field literal と producer namespace 要求は `:2001-2052`。 |
| oracle ticket `:1806-1860` | 実関数は `:1806-1859`。 |
| 8b reason 定数 `:305-308` | 実定数は `:305-307`、`:308` は空行。 |
| output後分類 `:5254-5322` | 正しい。 |

consumer 件数は「`1818-3555` の32 top-level symbol 名が現れる distinct line 数」で再計数すると以下だった。

- `p3_autonomous_workload_trial.py`: **13**。親の15は再現しない。主な範囲は `:1285-1320,3394,3967-4719`。
- `s8c_preregistration_evidence.py`: **11**。親と一致。`:1633-1736`
- `test_trial_registry.py`: **58**。親の60は再現しない。
- `test_s8c_preregistration_predicates.py`: **23**。「13+」とは矛盾しないが精確値ではない。
- `test_p3_autonomous_workload_trial.py`: **5**。親と一致。

最も重要な bytes 検査漏れは、brief I1 が `output/s8c-preregistration/**` を含めない点である。attempt registry と effective binding の既定 path はそこにある。`brief.md:33`; `trial_registry.py:54-65`  
plan の最終 diff 指示はこの directory を追加しており、この点だけは plan 側で補われている。`s2-plan.md:506`

pilot wave との重複主張は静的 Git 検査では再現した。対象 branch の `main...` 変更は0件で、当 branch との交差も0件だった。`brief.md:95-97`

pytest は制約どおり実走しておらず、緑は主張しない。