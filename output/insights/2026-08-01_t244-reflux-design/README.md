# [T-244] 規律 3 還流設計 draft v1 — 8c 自律ループの failure 還流 (2026-08-01)

本ディレクトリは dev-wave `[T-244] 還流設計` の逐語成果物である。可変状態の正本は worklog 末尾と
現行 phase doc、採用済み判断の正本は D116 であり、ここには凍結した逐語と設計本文 draft を置く。

## この文書の地位 (先に読むこと)

**これは draft であり、確定した設計ではない。** ユーザー裁定 (worklog (102)) が定めたのは
**軸 (i) を主軸・軸 (iv) を併用**という方向だけであり、本文書はその方向で起草した v1 である。

- **未裁定の設計択一が 5 件残る** (§8)。予算値と origin authority は確定していない。
- **実装はゼロである。** 本文書のどの機構も現行コードに存在しない。
- `MAX_APPROVED_GENERATIONS = 1` (D114) は**維持する**。本設計は多世代運転を解禁しない。
- 段 3 の敵対相談 2 本はいずれも **NO-GO** を返し、親はその所見 17 件を**すべて real と裁定した**。
  本文書はその所見を折り込んだ後の版である。所見の逐語は `s3-lensA.md` / `s3-lensB.md`。

## ファイル

| file | 内容 |
|---|---|
| `README.md` | 本文書 (設計 draft v1 + 裁定パッケージ) |
| `brief.md` | 段 1 brief (親の provisional 裁定 (P1)〜(P5)。うち (P3) は反証された) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only, reasoning=max) |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A = 情報フローと bit 会計の実効性・恒真性 |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B = 実装整合・gate 探索耐性・全層性 |
| `s4-adjudication.md` | 段 4 裁定 + plan v2 (本 wave の実装正本) |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー |

---

# 1. 問題の定義

規律 3 は「verifier は単なる pass/fail を返してはならない。**なぜ壊れたか**を構造化して返し、
それを次の variant 生成の入力にする」を要求する。8c 自律ループはこの消費の職務を実装していない
(D106 残余 1)。一方、規律 2 は「最適化圧力は必ず正しさを攻撃しに来る」前提で、正しさゲートを
緩める変異を許さないことを要求し、D39 決定 3 / D45 は**棄却理由から採用値を逆算する経路**
(structural inference) を構造的に塞いでいる。

したがって T-244 は「規律 3 を満たすために理由を還流させたいが、そのまま還流させると規律 2 を破る」
という設計上の緊張である。**この緊張は「理由を運ぶ」ことでは解けない。** 解くには
「理由を**機械が消費して候補空間を狭める**が、generator には理由を渡さない」形にする必要がある。
これがユーザーが選んだ軸 (i) であり、軸 (iv) はその副作用として残る oracle 照会を総量で縛る。

# 2. 現行の実測 (2026-08-01、コードから)

## 2.1 recipient matrix (現行)

| recipient | 見ている field | 出典 |
|---|---|---|
| planner | descriptor、`current_perf` (**絶対 throughput**)、leading indicators、abstract whiteboard | `p3_autonomous_workload_trial.py:816-825` |
| coder | 固定 `gating_spec`、planner の `axis/direction/magnitude` 3 field、`baseline` (**絶対 throughput**)、whiteboard | 同 `:843-860` |
| auditor | `working_diff` 全文、diff digest、designated source context、pre-build correctness digest | 同 `:897-905` |
| critic | harness outcome、metrics、**rejection 理由を含む critic digest 全文** | 同 `:957-967`、`p3_s4_loop.py:236-253` |
| trusted machine | preview 結果、diff 検疫、auditor verdict、WAL、loop state | `p3_s4_loop.py:634-668` ほか |

## 2.2 世代を跨ぐチャネルは 3 本 (親 brief の「2 本」は誤りだった)

1. **whiteboard** — `{iteration, direction, magnitude, result, delta_pct}` の 5 field。
   `result` は `success|fail|rejected` の 3 状態 = **最大 `log2(3) ≈ 1.585 bit/世代の failure 条件付き情報**。
   `delta_pct≡None` は load 側と射影側の二重で強制される (`p3_s4_loop.py:273-286`, `:394-398`)。
2. **`current_metrics`** — 前世代の outcome から更新され (`:951-953`)、次世代 planner の
   `current_perf`/`leading_indicators` と coder の `baseline` に入る。**絶対 throughput を含む。**
3. **`prior_reverse`** — critic が理由入り digest から作る**理由条件付き 1 bit**。次世代 payload には
   入らないが `drive()` を経て停止カウンタに効く (`p3_s4_loop.py:673-683`)。

**したがって「何も還流していない」も「理由は 1 bit も渡っていない」も偽である。**
正確には「**機序 (なぜ壊れたか) の自然文は generator へ 0 bit だが、失敗の有無と性能値は既に流れている**」。

## 2.3 現行の機械拒否面

`check_syntax_contract()` (`p3_s4_loop_trigger_gating.py:105-115`) は禁止識別子 5 個
(`thid_` / `result_` / `read_set_` / `write_set_` / `node_map_`) の regex blacklist であり、
pre-build で候補を落とす。**これは名前の blacklist であって、後述する mask enforcement ではない。**
coder の出力 parser は任意の一行 C++ 文字列を受理する (`p3_autonomous_workload_trial.py:261-284`)。

## 2.4 候補空間

gate 可能な abort 要因は 5 種 (`axis_trigger_gating.py` の `GATEABLE_REASONS`:
lock-conflict / update-absent / readvali-tid / readvali-locked / node-vali)。
`insert-node` / `scan-node` は YCSB で構造的にゼロと実証済みのため列挙から除外されている。
`kUnset` は fail-safe 契約で常に true。**したがって意味のある候補空間は `2^5 = 32` 点しかない。**

# 3. 設計 v1 の骨子

## 3.1 候補表現を固定 5-bit IR へ閉じる

coder の出力を自由な一行 C++ から、5 要因それぞれの「backoff 必須か否か」を表す
**正準 5-bit mask** へ閉じる。C++ 式は trusted machine の**正準 emitter** が mask から一意に生成する。

- 自由文字列を受理しないので、**コード表記そのものが side channel になる経路**が消える
  (空白・順序・同義表現による符号化)。
- emitter は全 32 mask 分を事前監査できる (有限で小さい)。
- 現行の禁止識別子 blacklist は残すが、**IR に識別子を書く場所が無い**ので二重の防壁になる。

## 3.2 failure → constraint 変換は「failed-singleton no-good cut」である

trusted machine だけが、次の条件をすべて満たすときに atom `r` を constraint 集合へ加える。

1. 候補が正準 5-bit IR である。
2. 直近 certified frontier から、未拘束 atom `r` を 1 つだけ `true→false` にした **singleton relaxation** である。
3. diff 検疫・構文 gate・auditor gate を通過している。
4. 同一 origin・同一 commit・同一 verifier policy で、WAL に `verify_done` と terminal `abort` があり、
   `certified=false`、`verdict=non-serializable`、trace integrity clean、構造化 anomaly が存在する。

**この変換が機械的に証明するのは「この singleton relaxation を含む候補が red だった」だけであり、
「`r` が failure の原因だった」ではない。** 他 atom との相互作用や因果単調性は証明されていない。
よって本設計はこれを **failed-singleton no-good cut** と呼び、**「failure reason constraint」とは名乗らない**。
規律 3 の「なぜ」を満たしたと主張できるのは、構造化 anomaly の edge/reason から同じ atom を
独立に再導出できることを機械実証したときだけである (§7 の前提条件 P6)。

build 失敗・trace timeout・環境起因の `aborted`・role-invalid・infrastructure failure から
atom を推測してはならない。これらは query を消費して origin を seal する。

## 3.3 強制と開示を分離する — ここが bit 会計の要

| 操作 | generator への開示 | 効果 |
|---|---|---|
| **強制** `E_t = P_t ∨ C_t` を machine が適用して build する | 0 bit (constraint 集合を見せない) | 過去に失敗した relaxation を再実行できない |
| **開示** constraint を generator に伝える | bit を払う | generator が無駄打ちを避けられる |

**既定は強制のみ。開示は origin seal 後に最大 `Kmax` class だけ**とする。
これが軸 (i) の実体である。generator は理由を読まないが、理由から導かれた制約は必ず効く。

段 2 が提案し親 brief (P3) が想定した「動的 constraint 文を coder の `gating_spec` へ追記する」案は
**不採用**である。文そのものが最大 `log2(5) ≈ 2.32 bit` の理由チャネルであり、順序・空白・同義語で
さらに符号化できる。`gating_spec` は全世代で byte-for-byte 同一に固定する。

## 3.4 単調性の厳密な定義と、その射程

atom 集合 `C_t ⊆ U` (`|U| = 5`)、実効 mask 集合 `A(C) = {m ∈ {0,1}^5 | C ⊆ m}` とし、

```
C_t ⊆ C_{t+1}   かつ   A(C_{t+1}) ⊆ A(C_t)
```

を要求する。constraint は追加のみで削除・弱化・expiry・成功による解除をしない。
iteration / query / disclosure counter も減らない。

**単調なのは「構文上の実効 mask 集合」であって、正しさ集合 (certified 可能な mask の集合) ではない。**
`A(C)` は verifier へ進める候補の集合にすぎず、各候補の verifier は省略できない (規律 2)。
また単調性が成立するのは**固定 universe・固定 emitter・固定 verifier policy・固定 origin の内側**だけで、
次では緩む: 新 origin の発行、IR schema / emitter / role bundle / verifier policy / environment contract の変更、
人手介入、supersede・migration、control ledger の削除・rollback、同一 UID による hidden state 編集。

## 3.5 予算は campaign より一段上へ束ねる (軸 iv)

**campaign ID に予算を置くのは自己矛盾である。** `ident.canonical_preimage()` は
`spec_content / ccbench_commit / search_tag / search_config / trial` を含む (`ident.py:76-103`) ため、
`trial` や `search_config` を 1 バイト変えれば別 campaign = 予算も新品になる。実測した回復経路:

| 回復経路 | 現行実装 |
|---|---|
| 別 run-root | no-build は `run_root/campaigns/<id>` を使うので即新品 (`p3_autonomous_workload_trial.py:779-783`) |
| 別 trial ID / config 微修正 | 別 campaign ID になる (`ident.py:76-103`) |
| programmatic 分割 | `drive=/providers=/preview=` 注入と `drive_iteration()` 直接反復は D114 の保証外 |
| checkpoint 削除 | `loop_state.json` が無ければ freshness gate は受理する (`p3_s4_loop.py:421-427`) |
| campaign 全削除 | lock/WAL とも local file で、hash chain も外部 anchor も無い |

よって予算は **`reflux-origin`** という campaign より上位の単位に置く。origin preimage に含めるもの:
authority が発行した immutable series ID、`spec_content` SHA、CCBench commit、axis semantics、
workload descriptor SHA・records・threads、verifier policy、environment contract、
IR schema と正準 emitter の SHA、role bundle と recipient projection schema の SHA、予算上限、
stock certification と structural-zero 証拠の参照。
**含めないもの:** `run_root`、`trial`、invocation ID、provider 呼び分け、1 回の CLI budget、process 分割名。

## 3.6 軸 (iii) は「後置可の補強」から「必須前提」へ格上げする

両レンズが独立に、**caller が選んだ singleton の accept/reject が 1 bit/query の membership oracle に
なる**ことを指摘した。`E_t = P_t ∨ C_t` の差 (`P_t ≠ E_t`) 自体が「その atom が既に constraint 済みか」を
教える。予算で回数は縛れるが、**1 query あたりの 1 bit は消えない**。
候補 batch を verifier 結果より前に凍結する軸 (iii) は、この adaptive 性を落とす唯一の手段である。
ユーザー裁定は「(iii) は (i) の補強として後置可」であり禁止ではないため、本 draft は
**多世代開放の必須前提**として格上げする (§7 の P4)。

# 4. 必須 7 項目

## ① 誰がどの field を見るか (設計後の recipient matrix)

| recipient | 現行 | 設計 v1 | 差分の理由 |
|---|---|---|---|
| planner | descriptor + 絶対 throughput + LI + whiteboard | descriptor + generation 番号 + 固定 IR schema SHA | 失敗と性能に条件づいた入力を外す。planner が符号化できる failure 情報を持たせない |
| coder | 固定 gating_spec + 3 field + baseline + whiteboard | 固定 `gating_spec_v2` (byte 固定) + 固定 IR schema + planner の 3 field | 出力は 5-bit mask。`baseline`・whiteboard・動的 constraint 文は渡さない |
| auditor | working_diff 全文 + digest | **raw IR から生成した diff のみ**。実効 diff・`E_t`・raw/effective IR の SHA は渡さない | 実効 diff は `C_t` を直接示す。低エントロピー (32 状態) なので SHA も総当たりで割れる |
| critic | outcome + metrics + 理由入り digest 全文 | 変更なし。ただし **report-only** とし、出力を次世代の制御に戻さない | 現行 `prior_reverse` は理由条件付き 1 bit を停止判定へ運ぶ |
| trusted machine | 個別に処理 | 加えて origin manifest、予約台帳、hidden `C_t`、certified frontier、raw/effective IR を保持 | 変換と予約の唯一の主体 |
| 公開 API / report | 多値の outcome / stop reason | active window 中は二値のみ。詳細は control ledger 側 | adaptive oracle の応答 alphabet を閉じる |

**whiteboard の 5 field は増やさない。** constraint は第 6 field ではなく origin control state に置く。
ただし 8c の generator projection からは whiteboard 自体を外す (D39 の保存形式は変えない)。

## ② 一世代・一 window あたりの最大公開 bit 数

**「4.585 bit/window」のような単一の上界を、現時点で正直に主張することはできない。**
面ごとに分けて書く。

| 面 | 容量 | 状態 |
|---|---:|---|
| hidden `C_t` (trusted 側の保持) | 5 bit | 公開量ではない |
| generator への failure 条件付き開示 (強制のみのとき) | **0 bit** | 設計目標 |
| accept/reject を caller が観測 | 1 bit / query | **消せない**。予算で回数だけ縛る |
| seal 後の class 公開 | `log2(1 + 5) ≈ 2.585 bit` | `Kmax` で縛る |
| planner→coder の `direction × magnitude` | `log2(9) ≈ 3.17 bit/世代` の**物理容量**は残る | planner に failure 情報を渡さない限り運ぶ中身が無い。**provider 注入や role 間 session 共有があると前提が崩れる** |
| 実効 diff / effective IR SHA | 最大 5 bit/query | **untrusted role から遮断する**ことが前提条件 (§7 P2) |
| constraint 件数・残予算・stop topology・自然文・時刻・artifact size | **上界が未定義** | 公開面から落とすか、明示的に受容残余とする |

前 wave が候補 B を否定した `log2(9) ≈ 3.17 bit` の符号化容量と、候補 C を否定した padding 攻撃は、
**本設計でも同じ形で成立しうる**。前者は provider 注入・session 共有経由で、後者は origin 分割経由で。
したがって bit 会計は「面の列挙 + 各面を閉じる前提条件」の形でしか成立せず、それが §7 である。

## ③ accept-reject query の総予算

**候補値** (未裁定、§8 択一 1): 事前登録済みの workload × treatment cell の origin ごとに
`Imax = 2` (総 iteration)、`Qmax = 2` (総 candidate query)、`Kmax = 1` (seal 後に公開できる class)。

計数規則:

1. planner 呼び出し前に iteration と query の slot を**原子的に同時予約**する。
2. malformed role output、preview reject、auditor reject、duplicate、infrastructure failure、
   provider crash も**消費し、返却しない** (no-refund)。
3. `preview()` や `drive_iteration()` の直接呼び出しにも一回限りの予約 token を要求する。
4. 予算超過は provider・preview・build のいずれにも到達させず fail-closed にする。
5. 早期停止時は残 slot を tombstone として消費し、公開 transcript の長さを固定する
   (停止位置そのものを追加記号にしない)。
6. active window 中の API 応答は `accepted | rejected` の二値だけとし、subtype を返さない。
7. **no-build の `dry-pass` や runbook の配線確認は診断 run として origin の外に置き、予算を消費しない**
   (消費させると配線確認だけで origin を使い切る)。

## ④ producer は誰か

**trusted machine の固定 translator のみ。** planner / coder / auditor / critic は producer にならない。
将来 LLM を補助的に通す場合も、machine が §3.2 の条件から同じ atom を独立再導出できたときだけ採用し、
不一致なら origin を seal する。

## ⑤ origin binding

§3.5 の preimage を持つ `reflux-origin/v1` を新設する。各 `CampaignConfig` の `search_config` には
`reflux_origin_id` / `reflux_policy_sha256` / `candidate_ir_schema` を追加し、個別 campaign は現行の
`canonical_preimage` に、複数 campaign は同一 origin ledger に、それぞれ束縛される。
新 origin は任意の programmatic caller が発行できてはならず、tracked registry または署名済み registry に
manifest SHA がある場合だけ admission する。origin reservation proof の無い artifact は
正式 8c report / certified proof chain に入れない。

**未解決:** ledger の一意な保存場所、同一の科学的 cell に複数 series ID を発行しない機械規則、
supersede をまたぐ累積、issuer 検証、削除・rollback・inode 置換への外部 anchor (§7 P3)。

## ⑥ 正式 report・WAL へ残す参照

`WAL_STAGES` は閉じた列挙なので (`model.py:20-32`)、terminal でない `reflux-control` stage を追加し、
固定 variant `"reflux-origin"` で `wal.log(origin_layout, "reflux-origin", STAGE_REFLUX_CONTROL, env_tag, payload)`
と記録する (現行シグネチャ `wal.py:499-506` に一致)。event:

| event | payload の骨子 |
|---|---|
| `origin-opened` | schema 版、origin ID、manifest path/SHA、policy SHA、I/Q/K、IR・projection SHA |
| `slot-reserved` | slot 連番、一回限り token の SHA、campaign ID、preimage SHA、workload、generation、予約後 counter |
| `query-bound` | slot 連番、proposal artifact SHA、raw IR SHA (effective IR SHA は公開面へ出さない) |
| `constraint-added` | opaque ID、`failed-singleton-no-good-cut/v1`、source refs、旧/新 state commitment (machine-owned nonce 付き) |
| `query-result` | slot 連番、公開二値、`verify_done`/`abort` record ref |
| `slot-tombstoned` | 早期停止で未使用 slot を無返却消費したこと |
| `origin-sealed` | 消費 counter、control ledger の byte 範囲と SHA、state commitment、公開 class または `none` |

source ref は `campaign_id / variant / stage / record_ordinal / payload_sha256` を含む。
`STAGE_ABORT` は従来どおり不採用記録であり、control event の代用にしない。
**`records_by_stage()` は stage 単位の last-wins なので control ledger の読取に使えない**
(`wal.py:586-601`)。順序付き `read_records()` + event grammar validator が要る。

**未解決 (重要):** 現行 `wal.append()` の flock は 1 record の追記しか覆わない (`wal.py:283-378`)。
count 検証・予約 append・fsync を同一 lock 下で行う primitive と、
`pending は最大 1` / state commitment の CAS / 未完 event の idempotent replay を含む状態機械が要る。
crash window (予約後 provider 前 / verifier red 後 `constraint-added` 前 / `constraint-added` 後
`query-result` 前 / query 完了後 seal 前) の畳み方も定義されていない (§7 P3)。

## ⑦ 受容する残余と、不採用案の再開条件

**受容する残余:**

- caller が選んだ singleton の accept/reject から得る **1 bit/query は消えない**。予算で回数を縛るだけ。
- timing、crash 位置、artifact size、生成時刻などの analog side channel は本予算で閉じない。
- no-good cut は構文上の保守化であり、実行時挙動の因果単調性を証明しない。verifier は毎候補で必須。
- 5-atom IR は trigger-gating / YCSB 限定であり、別軸へ一般化しない。
- 同一 UID の悪意ある caller から trusted control ledger を秘匿する保証は、現行の in-process 構造には無い。
- WAL の最終 SHA は外部 anchor なしに全面改竄を防がない。
- 人間が新 origin を正式発行すれば新しい予算が生じる。これは意図した escape hatch だが、
  **同じ科学的 cell に対する重複発行を機械で禁じない限り予算は骨抜きになる**。

**不採用案 (前 wave の候補 A〜D) の再開条件:**

| 案 | 再開条件 |
|---|---|
| A: 現状維持 (還流を増やさない) | 多世代運転を恒久的に行わないと人間が裁定した場合の containment としてのみ。規律 3 の設計解としては再開不可 |
| B: failure class を planner のみへ | planner→coder チャネルを固定・非適応にし、role 間の非干渉と「総開示 < class 情報量」を機械証明できる場合 |
| C: 非重複 window の集合還流 | 軸 (iii) を導入し、batch を結果取得前に immutable 凍結し、duplicate/既知 class も予算を消費し、結果を batch seal まで非公開にできる場合 |
| D: planner/coder 双方へ class | D39 / D45 を supersede する新たな人間裁定と、class が gate 探索に使えない形式的根拠が得られた場合。現状では再開不可 |

# 5. この設計が弱めるもの・弱めないもの (規律 2 の観点)

**弱める (改善する):**

- generator は failure class・whiteboard result・metrics・動的 constraint 文を読まない。
- hidden constraint は raw 提案を保守側へ閉包するので、理由を無視しても過去に失敗した relaxation を再実行できない。
- 自然文・表記揺れ・順序・padding を channel として使えない (IR が固定 mask のため)。
- 同一 origin 内では 3 件目以降の照会が fail-closed で止まる。

**弱めない (正直に書く):**

- caller が選んだ singleton の 1 bit/query は残る。`Qmax = 2` なら到達可能な constraint 状態は
  `1 + 5 + 10 = 16` 通り = 4 bit で、これは設計側の公開上限より大きい。
- 新 origin の発行、cell 横断の集約 (A/B/C を別 origin にすれば 3 origin で 6 query) は残る。
- timing・停止位置・artifact size は閉じない。
- provider 注入や role 間 session 共有があれば、planner→coder の 3.17 bit 容量が再び実情報を運ぶ。
- 5 atom 全体の探索不能性を証明したものではない。

# 6. 段 3 が real と判定した所見と、本 draft への反映

| # | 所見 | 反映 |
|---|---|---|
| A1/B1 | hidden constraint が auditor への実効 diff と低エントロピー SHA (32 状態) から復元できる | §4① で auditor から実効 diff と両 SHA を外した。§7 P2 |
| A2/B1 | provider 注入・role 間 session 共有で 6 状態 class を planner の 9 記号で一世代伝送できる | §4② に明記、§7 P5 で非干渉検査を前提条件化 |
| A3/B2 | 単調集合の差分が 1 bit/query の membership oracle になる | §3.6 で軸 (iii) を必須前提へ格上げ |
| A4 | 予算は ID 変更・削除・分割で新品に戻る | §3.5 に回復経路の表を実測付きで明記、§7 P3 |
| A5/B7 | 親 brief の 3 前提 (チャネル 2 本 / 理由 0 bit / 制約強制点あり) が誤り | §2.2、§2.3 で訂正 |
| A6 | 保証に対応する機械検査が無い | 本文書は draft と明示し、§7 を機械検査可能な前提条件として書いた |
| A7 | 単調性は構文上・origin 内に限る | §3.4 に射程を明記 |
| A8/B3 | 単一 red から因果は導けない | §3.2 で **no-good cut** と名乗りを訂正 |
| A9/B5 | control ledger の原子性・crash 復旧・seal の自己参照が未定義 | §4⑥ の「未解決」に明記、§7 P3 |
| B4 | D114 が保証外とした層が formal consumer (`layer3_report.py`) まで素通りする | §7 P7 で consumer gate を前提条件化 |
| B6 | 「設計確定」への状態遷移は不正 | 本文書を draft とし、D116 は軸と前提条件だけを確定する |
| B9 | 1 世代運転・runbook・ablation の契約が壊れる | §4③-7 で診断 run を分離、§7 P8 |

# 7. 多世代開放 (`MAX_APPROVED_GENERATIONS > 1`) の前提条件

**本 wave の実質的な成果はこのリストである。** すべて機械検査可能な形で書く。
D114 の承認上限の引上げは、D96 手続に加えて次をすべて満たしたときだけ許す。

| # | 前提条件 | 満たされたことの検査 |
|---|---|---|
| P1 | 候補表現が固定 5-bit IR に閉じ、正準 emitter が全 32 mask で監査済み | 自由文字列を渡す負例が拒否される。emitter の出力が mask ごとに固定 byte |
| P2 | 実効 diff・`E_t`・raw/effective IR の SHA が untrusted role の payload に現れない | payload bytes を hidden state の全変異に対して比較する **非干渉検査** |
| P3 | origin ledger が単一 in-flight・CAS・crash replay・削除耐性を持つ | 並行 2 process、各 crash window、ledger 削除・rollback が必ず赤になる境界検査 |
| P4 | 軸 (iii) の batch freeze が実装され、候補が verifier 結果より前に凍結される | 結果取得後に batch を変更する経路が拒否される |
| P5 | provider 注入・role 間 session 共有・未予約 token が正式経路で拒否される | 注入 run が originless として下流で拒否される負例 |
| P6 | no-good cut の名乗りを超えるなら、構造化 anomaly から同じ atom を独立再導出できる | 再導出の不一致で origin が seal される正例・負例 |
| P7 | formal consumer (`layer3_report.py` 等) が origin proof を要求する | proof 無し campaign が正式材料に入らない負例。**受理集合の変更なので D96 手続** |
| P8 | 1 世代運転・runbook 3 手順・reflux on/off ablation が壊れない | 現行 fixture provider・parser・driver・runbook の全経路の緑 |
| P9 | whiteboard の値域 (direction/magnitude/result) と iteration 整合が閉じている | 前 wave の裁定パッケージ X4。汚染 checkpoint の負例 |
| P10 | 予算値 `Imax/Qmax/Kmax` と origin authority がユーザー裁定で確定している | §8 の択一 1・2 |

**現時点で満たされているものはゼロである。**

# 8. 裁定パッケージ (ユーザー判断待ち)

| # | 択一 | 親の推奨 |
|---|---|---|
| 1 | 予算値を `Imax/Qmax/Kmax = 2/2/1` で採るか、軸 (iii) の必須化を先に確定してから再導出するか | **(iii) を必須前提にしたうえで値を再導出する。** 両レンズが独立に「値の正当化が無く origin 分割で回収される」と指摘した |
| 2 | origin authority を repo 内 tracked registry で担うか、別 service / ACL へ分離するか | **tracked registry から始め、「同一 UID の caller からの秘匿は不可」を残余として明示する。** 別 service は現行の実験規模に対して過剰 |
| 3 | 承認上限の引上げを P1〜P10 の充足検査へ機械束縛するか (計測 ID `V7` の拡張) | **択一 1・2 の確定後に独立 wave で実装する。** 今実装すると未裁定の設計を既成事実にする |
| 4 | formal consumer に origin proof gate を入れるか (受理集合の変更、D96 手続) | **入れる。** 入れないと P3・P5 を実装しても素通りする |
| 5 | 診断 run (no-build `dry-pass`、runbook 配線確認) を予算の外に置く扱いでよいか | **よい。** 予算に数えると配線確認だけで origin を使い切る |

# 9. 本 wave の射程 (実装していないこと)

- 本 wave は **docs のみ**である。コード・テスト・設定は 1 行も変更していない。
- したがって**変異 matrix は対象外**である (`DW-S04`: 実装差分が無い)。
- `MAX_APPROVED_GENERATIONS = 1` は変えていない。多世代運転は依然として 3 入口で機械拒否される。
- 本設計のどの機構も実装されていない。`reflux-control` stage、origin ledger、5-bit IR、
  正準 emitter、非干渉検査はすべて**未実装**である。
