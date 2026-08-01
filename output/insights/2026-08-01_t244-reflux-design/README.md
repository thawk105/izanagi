# [T-244] 規律 3 還流設計 draft v1 — 8c 自律ループの failure 還流 (2026-08-01)

```text
authority: none
default_effect: no-state-change
```

本ディレクトリは dev-wave `[T-244] 還流設計` の逐語成果物である。可変状態の正本は worklog 末尾と
現行 phase doc、採用済み判断の正本は D119 であり、ここには凍結した逐語と設計本文 draft を置く。
**本文書は可変状態の正本ではない。**

## この文書の地位 (先に読むこと)

**これは draft であり、確定した設計ではない。** ユーザー裁定 (worklog (102)) が定めたのは
**軸 (i) を主軸・軸 (iv) を併用**という方向だけであり、本文書はその方向で起草した v1 である。

- **未裁定の設計択一が 7 件残る** (§8)。予算値・origin authority・軸 (iii) の扱い・**cut の適用範囲**は確定していない。
- **実装はゼロである。** 本文書のどの機構も現行コードに存在しない。
- `MAX_APPROVED_GENERATIONS = 1` (D114) は**維持する**。本設計は多世代運転を解禁しない。
- 段 3 の敵対相談 2 本と段 6 の敵対レビュー 2 本はいずれも **NO-GO** を返した。段 3 の所見 18 件と
  段 6 の所見 20 件を親が裁定し、本版はその反映後である。反映状況は §6 の台帳が正本で、
  **partial のまま残っているものが多数ある**。
- 逐語は `s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` / `s4-adjudication.md` /
  `s6-revA.md` / `s6-revB.md`。

## ファイル

| file | 内容 |
|---|---|
| `README.md` | 本文書 (設計 draft v1 + 裁定パッケージ) |
| `brief.md` | 段 1 brief (親の provisional 裁定 (P1)〜(P5)。うち (P3) は反証された) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only, reasoning=max) |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A = 情報フローと bit 会計の実効性・恒真性 |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B = 実装整合・gate 探索耐性・全層性 |
| `s4-adjudication.md` | 段 4 裁定 + plan v2 |
| `s6-revA.md` | 段 6 敵対レビュー レンズ A = 過大表現・恒真な主張・事実誤り |
| `s6-revB.md` | 段 6 敵対レビュー レンズ B = consumer 取り残し・正本整合・運用破壊 |

**凍結逐語の読み方:** `brief.md` / `s2-plan.md` / `s3-*.md` / `s4-adjudication.md` は各段時点の記録で
あり書き換えない。したがってそれらは改番前の **D116** や、撤回した「軸 (iii) の必須化」「要因を
全候補で必須化する cut」を含む。**現在の正本は本 README と D119 である。**

---

# 1. 問題の定義

規律 3 は「verifier は単なる pass/fail を返してはならない。**なぜ壊れたか**を構造化して返し、
それを次の variant 生成の入力にする」を要求する。8c 自律ループはこの消費の職務を実装していない
(D106 残余 1)。一方、規律 2 は「最適化圧力は必ず正しさを攻撃しに来る」前提で正しさゲートを
緩める変異を許さず、D39 決定 3 / D45 は**棄却理由から採用値を逆算する経路** (structural inference) を
構造的に塞いでいる。

したがって T-244 は「規律 3 を満たすために理由を還流させたいが、そのまま還流させると規律 2 を破る」
という設計上の緊張である。**この緊張は「理由を運ぶ」ことでは解けない。** 解くには
「理由を**機械が消費して候補空間を狭める**が、generator には理由を渡さない」形にする必要がある。
これがユーザーが選んだ軸 (i) であり、軸 (iv) はその副作用として残る oracle 照会を総量で縛る。

# 2. 現行の実測 (2026-08-01、コードから)

## 2.1 recipient matrix (現行、D118 反映後)

| recipient | 見ている field | 出典 |
|---|---|---|
| planner | descriptor、`current_perf` (**絶対 throughput**)、leading indicators、abstract whiteboard | `p3_autonomous_workload_trial.py` の planner payload |
| coder | 固定 `gating_spec`、planner の `axis/direction/magnitude` 3 field、`baseline` (**絶対 throughput**)、whiteboard | 同 coder payload |
| auditor | `working_diff` 全文、diff digest、designated source context、pre-build correctness digest | 同 auditor payload |
| critic | harness outcome、`harness_result.metrics`、**rejection 理由を含む critic digest 全文** | 同 critic payload、`p3_s4_loop.py` の `make_critic_digest` |

**metrics の recipient は 4 者である** (planner / coder / critic + 機械)。単位は D118 が recipient ごとに
分けた (planner/coder は percent 名 field を percent、critic は率名 field を ratio)。
`delta_pct≡None` は **whiteboard 射影経路の `delta_pct` field だけ**の防壁であり、
planner へ性能値を渡さない保証ではない (D118 決定 3)。

## 2.2 世代を跨ぐチャネルは 3 本 (親 brief の「2 本」は誤りだった)

1. **whiteboard** — `{iteration, direction, magnitude, result, delta_pct}` の 5 field。
   `result` は設計上 `success|fail|rejected` の 3 語彙だが、**これは規約であって機械契約ではない** —
   `project_whiteboard(..., result: str)` は任意文字列を受け、`state_from_dict()` は key 集合と
   `delta_pct` しか検査せず direction/magnitude/result の値域を閉じていない。
   3 語彙が守られている限りの情報量は最大 `log2(3) ≈ 1.585 bit/世代`である。
2. **`current_metrics`** — 前世代の outcome から更新され、次世代 planner の
   `current_perf`/`leading_indicators` と coder の `baseline` に入る。**絶対 throughput を含む。**
3. **`prior_reverse`** — critic が理由入り digest から作る**理由条件付き 1 bit**。次世代 payload には
   入らないが `drive()` を経て停止カウンタに効く。

**したがって「何も還流していない」も「理由は 1 bit も渡っていない」も偽である。**
正確には「**機序 (なぜ壊れたか) の自然文は generator へ 0 bit だが、失敗の有無と性能値は既に流れている**」。

## 2.3 現行の機械拒否面

`check_syntax_contract()` は禁止識別子 5 個 (`thid_` / `result_` / `read_set_` / `write_set_` /
`node_map_`) の regex blacklist であり、pre-build で候補を落とす。**これは名前の blacklist であって
mask enforcement ではない。** coder 出力の parser は**任意の非空 1 行 C++ 文字列**を受理する。

## 2.4 候補空間 — 「32 点」は列挙空間であって現行の受理集合ではない

gate 可能な abort 要因は 5 種 (`axis_trigger_gating.py` の `GATEABLE_REASONS`:
lock-conflict / update-absent / readvali-tid / readvali-locked / node-vali)。
`insert-node` / `scan-node` は YCSB で構造的にゼロと実証済みのため列挙から除外され、
`kUnset` は常に true とする **prompt / コメント上の契約**である (機械強制はされていない)。

`2^5 = 32` は**偵察の列挙空間**であって、production が受理する候補集合ではない。
**parser の受理集合は「任意の非空 1 行 C++」**であり、production の受理集合はそこから
diff 検疫・禁止識別子 gate・auditor gate の 3 段を通った集合である。**いずれも有限に閉じていない。**
したがって設計 v1 が候補表現を 5-bit IR へ閉じることは正準化ではなく**受理集合の縮小**であり、
実装時に **D96 手続**を要する。

# 3. 設計 v1 の骨子

## 3.1 候補表現を固定 5-bit IR へ閉じる (受理集合の変更、D96 手続)

coder の出力を自由な 1 行 C++ から、5 要因それぞれの「backoff 必須か否か」を表す
**正準 5-bit mask** へ閉じる。C++ 式は trusted machine の**正準 emitter** が mask から一意に生成する。

- コード表記そのものが side channel になる経路 (空白・順序・同義表現) が消える。
- emitter は全 32 mask 分を独立 golden として事前監査できる (有限で小さい)。
- 現行の禁止識別子 blacklist は残すが、IR に識別子を書く場所が無いので二重の防壁になる。

## 3.2 failure → constraint 変換は「exact-mask no-good cut」である

trusted machine だけが、次の条件をすべて満たすときに **その候補 mask `p` そのもの**を
禁止集合 `C` へ加える。

1. 候補が正準 5-bit IR である。
2. diff 検疫・構文 gate・auditor gate を通過している。
3. 同一 origin・同一 commit・同一 verifier policy で、WAL に `verify_done` と terminal `abort` があり、
   `certified=false`、`verdict=non-serializable`、trace integrity clean、構造化 anomaly が存在する。

**禁止するのは失敗した mask 1 点だけである。** 段 6 の両レンズが独立に、
「atom `r` を全候補で必須化する」案は**単一の red から座標全体 (無拘束時なら 32 点中 16 点) を削る
過剰一般化**であり、相互作用も因果単調性も証明されていないと指摘した。これを採用し、
初版の「atom 全域を禁止する」定式化は**撤回**する。

atom 全域 (座標 cut) へ一般化してよいのは、**その atom を戻すと同じ anomaly が消えることを含む
独立な単調性の実証**が得られたときだけである (§7 の P6)。

**この変換が機械的に証明するのは「その mask のその実走を certify できなかった」ことだけであり、
「何が原因だったか」ではない。** よって本設計はこれを **no-good cut** と呼び、
**「failure reason constraint」とも「規律 3 の『なぜ』を満たした」とも名乗らない。**

build 失敗・trace timeout・環境起因の `aborted`・role-invalid・infrastructure failure から
constraint を作ってはならない。これらは query を消費して origin を seal する。

### 3.2.1 正直な帰結 — exact-mask cut だけでは軸 (i) を満たしていない

焦点再レビューが指摘したとおり、**1 点の禁止は「既知 red の重複実行防止」であって規律 3 の還流ではない**。
構造化された anomaly は「存在するか」の確認にしか使われず、禁止範囲の決定に関与しない。
5 要因 universe では機械側の受理領域が 32 → 31 点へ縮むだけで、**generator の提案分布は変わらない** —
`C` を見せず拒否時も query を消費するため、同じ候補の再提案や Hamming 距離 1 の近傍 5 点を防げない。

つまり本 draft は、安全側 (過剰一般化しない) を選んだ結果、**強度としては候補 A (現状維持 = 封じ込め) に
近いところまで後退している**。これは T-244 の**中心的な未解決点**であり、§8 の択一 7 として返す。

軸 (i) を名乗るには、**構造化 anomaly から禁止範囲 (どの候補集合が同じ理由で危険か) を機械が独立に
再導出する契約**が要る。それが前提条件 P6 の実体であり、本 draft はそこを設計しきれていない。
座標 cut (要因を全候補で必須化) は、その再導出が成立したときにだけ許される一般化である。

## 3.3 強制と開示を分離する — ここが bit 会計の要

| 操作 | generator への開示 | 効果 |
|---|---|---|
| **強制** 禁止集合 `C` に入る候補を build 前に拒否する | 0 bit (集合を見せない) | 過去に失敗した候補を再実行できない |
| **開示** constraint を generator に伝える | bit を払う | generator が無駄打ちを避けられる |

**既定は強制のみ。開示は origin seal 後に最大 `Kmax` class だけ**とする。
これが軸 (i) の実体である。generator は理由を読まないが、理由から導かれた制約は必ず効く。

exact-mask cut では「機械が候補を安全側へ書き換える」閉包 (`E = P ∨ C`) を行わない。
禁止集合に当たった候補は**開示なしで拒否し、query slot を消費する**。書き換えを行うと、
提案 mask と build された mask が食い違い、fitness の帰属が汚染される (D39 決定 7 と同型の問題)。

段 2 が提案し親 brief (P3) が想定した「動的 constraint 文を coder の `gating_spec` へ追記する」案は
**不採用**である。文そのものが最大 `log2(5) ≈ 2.32 bit` の理由チャネルであり、順序・空白・同義語で
さらに符号化できる。`gating_spec` は全世代で byte-for-byte 同一に固定する。

## 3.4 単調性の厳密な定義と、その射程

禁止 mask 集合 `C_t ⊆ {0,1}^5` について

```
C_t ⊆ C_{t+1}   かつ   受理可能集合 {0,1}^5 \ C_t は広がらない
```

を要求する。constraint は追加のみで削除・弱化・expiry・成功による解除をしない。
iteration / query / disclosure counter も減らない。

**単調なのは「構文上の候補集合」であって、正しさ集合 (certify 可能な mask の集合) ではない。**
禁止していない候補が certify される保証はなく、各候補の verifier は省略できない (規律 2)。
また単調性が成立するのは**固定 universe・固定 emitter・固定 verifier policy・固定 origin の内側**だけで、
次では緩む: 新 origin の発行、IR schema / emitter / role bundle / verifier policy / environment contract の
変更、人手介入、supersede・migration、control ledger の削除・rollback、同一 UID による hidden state 編集。

## 3.5 予算は campaign より一段上へ束ねる (軸 iv)

**campaign ID に予算を置くのは自己矛盾である。** `ident.canonical_preimage()` は
`spec_content / ccbench_commit / search_tag / search_config / trial` を含むため、
`trial` や `search_config` を 1 バイト変えれば別 campaign = 予算も新品になる。実測した回復経路:

| 回復経路 | 現行実装 |
|---|---|
| 別 run-root | no-build は `run_root/campaigns/<id>` を使うので即新品 |
| 別 trial ID / config 微修正 | 別 campaign ID になる |
| programmatic 分割 | `drive=/providers=/preview=` 注入と `drive_iteration()` 直接反復は D114 の保証外 |
| checkpoint 削除 | `loop_state.json` が無ければ freshness gate は受理する |
| campaign 全削除 | lock/WAL とも local file で、hash chain も外部 anchor も無い |

よって予算は **`reflux-origin`** という campaign より上位の単位に置く。**origin preimage の正本は本節**とし、
D119 はその骨子だけを引く。preimage に含めるもの:

- authority が発行した immutable series ID
- `spec_content` SHA、CCBench commit、axis semantics
- workload descriptor SHA、records、threads
- verifier policy、environment contract
- candidate IR schema と正準 emitter の SHA
- **role bundle と recipient projection schema の SHA** (P2 の非干渉の意味がこれで決まる)
- 予算上限 (`Imax` / `Qmax` / `Kmax`)
- **stock certification と structural-zero evidence の参照** (5 要因 universe の正当性がこれで決まる)

**含めないもの:** `run_root`、`trial`、invocation ID、provider 呼び分け、1 回の CLI budget、process 分割名。

## 3.6 軸 (iii) の扱い — 親の推奨であり、確定ではない

両レンズが独立に、**caller が選んだ候補の accept/reject が 1 bit/query の membership oracle になる**
ことを指摘した。予算で回数は縛れるが、**1 query あたりの 1 bit は消えない**。
候補 batch を verifier 結果より前に凍結する軸 (iii) は、この adaptive 性を落とす手段である。

段 4 の親裁定は (iii) を「多世代開放の必須前提」へ格上げしたが、段 6 レンズ A が
**ユーザー裁定 (「(iii) は後置可」) の逸脱**と判定した。「後で置いてよい」は
「必須 gate に変えてよい」という承認ではない。**この判定を採用し、必須化は撤回する。**
(iii) は §8 の択一 3 として**ユーザー裁定へ返す**。

採る場合に必要な内容も段 6 が指摘した — batch サイズ 1 の逐次実行では恒真になるため、
**batch cardinality の下限、全候補の事前 commit、batch seal までの結果非公開**をセットで定義する必要がある。

# 4. 必須 7 項目

## ① 誰がどの field を見るか (設計後の recipient matrix)

| recipient | 現行 (D118 反映後) | 設計 v1 | 差分の理由 |
|---|---|---|---|
| planner | descriptor + 絶対 throughput + LI + whiteboard | descriptor + generation 番号 + 固定 IR schema SHA | 失敗と性能に条件づいた入力を外す。符号化できる failure 情報を持たせない |
| coder | 固定 gating_spec + 3 field + baseline + whiteboard | 固定 `gating_spec_v2` (byte 固定) + 固定 IR schema + planner の 3 field | 出力は 5-bit mask。`baseline`・whiteboard・動的 constraint 文は渡さない |
| auditor | working_diff 全文 + digest | **raw IR から生成した diff のみ**。禁止集合・実効 mask・両 SHA は渡さない | 実効 diff は `C` を直接示し、32 状態しかないので SHA も総当たりで割れる |
| critic | outcome + metrics + 理由入り digest 全文 | **未解決** (§8 択一 4)。report-only 化と現行 ablation は両立しない | 現行 `prior_reverse` は理由条件付き 1 bit を停止判定へ運ぶ |
| trusted machine | 個別に処理 | 加えて origin manifest、予約台帳、禁止集合 `C`、certified frontier、raw IR を保持 | 変換と予約の唯一の主体 |
| 公開 API / report | 多値の outcome / stop reason | active window 中は二値のみ。詳細は control ledger 側 | adaptive oracle の応答 alphabet を閉じる |

**whiteboard の 5 field は増やさない。** constraint は第 6 field ではなく origin control state に置く。
ただし 8c の generator projection からは whiteboard 自体を外す (D39 の保存形式は変えない)。

## ② 一世代・一 window あたりの最大公開 bit 数

**単一の上界を現時点で正直に主張することはできない。** 面ごとに分けて書く。

| 面 | 容量 | 状態 |
|---|---:|---|
| 禁止集合 `C` (trusted 側の保持) | 最大 32 点の部分集合 | 公開量ではない |
| generator への failure 条件付き開示 (強制のみのとき) | **0 bit** | 設計目標 |
| accept/reject を caller が観測 | 1 bit / query | **消せない**。予算で回数だけ縛る |
| seal 後の class 公開 | `Kmax` で縛る | 値は未裁定 |
| planner→coder の `direction × magnitude` | `log2(9) ≈ 3.17 bit/世代` の**物理容量**は残る | planner に failure 情報を渡さない限り運ぶ中身が無い。**provider 注入や role 間 session 共有があると前提が崩れる** |
| 実効 diff / IR SHA | 32 状態なので最大 5 bit/query | **untrusted role から遮断する**ことが前提条件 (§7 P2) |
| **D51 の逐次 provenance** (`reports/` の proposal_path / auditor_diff_digest / variant / outcome) | 上界未定義 | 毎 iteration 書かれる**公開面**であり、P2 の観測面に必ず含める |
| driver の戻り値、artifact path、constraint 件数、残予算、stop topology、自然文、時刻、file size | **上界が未定義** | 公開面から落とすか、明示的に受容残余とする |

前 wave が候補 B を否定した `log2(9) ≈ 3.17 bit` の符号化容量と、候補 C を否定した padding 攻撃は、
**本設計でも同じ形で成立しうる**。前者は provider 注入・session 共有経由で、後者は origin 分割経由で。
したがって bit 会計は「面の列挙 + 各面を閉じる前提条件」の形でしか成立せず、それが §7 である。

## ③ accept-reject query の総予算

**候補値** (未裁定、§8 択一 1): 事前登録済みの workload × treatment cell の origin ごとに
`Imax = 2` (総 iteration)、`Qmax = 2` (総 candidate query)、`Kmax = 1` (seal 後に公開できる class)。
**値の正当化はまだ無い。** `Qmax = 2` でも到達可能な禁止集合の状態数は `1 + 32 + C(32,2)` と大きく、
A/B/C を別 origin にすれば 3 origin で 6 query になる。

計数規則:

1. planner 呼び出し前に iteration と query の slot を**原子的に同時予約**する。
2. malformed role output、preview reject、auditor reject、duplicate、infrastructure failure、
   provider crash も**消費し、返却しない** (no-refund)。
3. `_preview()` や `drive_iteration()` の直接呼び出しにも一回限りの予約 token を要求する。
4. 予算超過は provider・preview・build のいずれにも到達させず fail-closed にする。
5. 早期停止時は残 slot を tombstone として消費し、公開 transcript の長さを固定する。
6. active window 中の API 応答は `accepted | rejected` の二値だけとし、subtype を返さない。
7. **no-build の `dry-pass` や runbook の配線確認は診断 run として origin の外に置き、予算を消費しない**
   (消費させると配線確認だけで origin を使い切る)。この扱いは §8 択一 5 として裁定へ返す。

## ④ producer は誰か

**trusted machine の固定 translator のみ。** planner / coder / auditor / critic は producer にならない。
将来 LLM を補助的に通す場合も、machine が §3.2 の条件から同じ結論を独立再導出できたときだけ採用し、
不一致なら origin を seal する。

## ⑤ origin binding

§3.5 が正本。各 `CampaignConfig` の `search_config` には `reflux_origin_id` /
`reflux_policy_sha256` / `candidate_ir_schema` を追加し、個別 campaign は現行の `canonical_preimage` に、
複数 campaign は同一 origin ledger に、それぞれ束縛される。新 origin は任意の programmatic caller が
発行できてはならず、tracked registry または署名済み registry に manifest SHA がある場合だけ admission する。
origin reservation proof の無い artifact は正式 8c report / certified proof chain に入れない。

**未解決:** ledger の一意な保存場所、同一の科学的 cell に複数 series ID を発行しない機械規則、
supersede をまたぐ累積、issuer 検証、削除・rollback・inode 置換への外部 anchor (§7 P3)。

## ⑥ 正式 report・WAL へ残す参照

`WAL_STAGES` は閉じた列挙なので、terminal でない `reflux-control` stage を追加し、
固定 variant `"reflux-origin"` で
`wal.log(origin_layout, "reflux-origin", STAGE_REFLUX_CONTROL, env_tag, payload)` と記録する
(現行シグネチャに一致)。event: `origin-opened` / `slot-reserved` / `query-bound` /
`constraint-added` / `query-result` / `slot-tombstoned` / `origin-sealed`。
source ref は `campaign_id / variant / stage / record_ordinal / payload_sha256` を含む。
`STAGE_ABORT` は従来どおり不採用記録であり、control event の代用にしない。

**未解決 (重要):**

- `records_by_stage()` は stage 単位の last-wins なので control ledger の読取に使えない。
  順序付き `read_records()` + event grammar validator が要る。
- 現行 `wal.append()` の flock は 1 record の追記しか覆わない。count 検証・予約 append・fsync を
  同一 lock 下で行う primitive と、`pending は最大 1` / state commitment の CAS /
  未完 event の idempotent replay を含む状態機械が要る。
- crash window (予約後 provider 前 / verifier red 後 `constraint-added` 前 / `constraint-added` 後
  `query-result` 前 / query 完了後 seal 前) の正規回復状態が未定義。
- **`layer3_report.py` は独自の固定 stage 集合を持ち未知 stage を拒否する。**
  `model.WAL_STAGES` に `reflux-control` を足すだけでは正式材料レポートが壊れる。
- **さらに `layer3_report.py` は全 WAL record を `variant` で集約し、`commit` の無い variant を
  `commit-event-absent` の reject として数える。** stage allowlist を広げるだけでは、control plane の
  固定 variant `"reflux-origin"` が**実在しない棄却候補**として材料レポートに混入する。
  control event を候補集計から分離する区画 (`control_events`) と分離規則が要る。
  consumer の実装地図に必ず含める。

## ⑦ 受容する残余と、不採用案の再開条件

**受容する残余:**

- caller が選んだ候補の accept/reject から得る **1 bit/query は消えない**。予算で回数を縛るだけ。
- timing、crash 位置、artifact size、生成時刻などの analog side channel は本予算で閉じない。
- no-good cut は構文上の保守化であり、実行時挙動の因果を証明しない。verifier は毎候補で必須。
- 5 要因 IR は trigger-gating / YCSB 限定であり、別軸へ一般化しない。
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
- 禁止集合は raw 提案を build 前に落とすので、理由を無視しても過去に失敗した候補を再実行できない。
- 自然文・表記揺れ・順序・padding を channel として使えない (IR が固定 mask のため)。
- 同一 origin 内では予算超過の照会が fail-closed で止まる。

**弱めない (正直に書く):**

- caller が選んだ候補の 1 bit/query は残る。
- 新 origin の発行、cell 横断の集約は残る。
- timing・停止位置・artifact size は閉じない。
- provider 注入や role 間 session 共有があれば、planner→coder の 3.17 bit 容量が再び実情報を運ぶ。
- 候補空間全体の探索不能性を証明したものではない。

# 6. 敵対所見の反映台帳 (closed / partial / regressed)

段 3 = BLOCKER 11 + MAJOR 7 = **18 件**、段 6 = BLOCKER 9 + MAJOR 9 + MINOR 2 = **20 件**。
段 4 の裁定文が「所見 17 件」と書いたのは計数誤りであり、ここで訂正する。

## 段 3 (18 件)

| # | 所見 | 本版での状態 |
|---|---|---|
| A1/B1 | hidden constraint が auditor の実効 diff と低エントロピー SHA から復元できる | **partial** — auditor から遮断する設計にしたが、P2 の観測面 (D51 provenance 等) を閉じきっていない |
| A2 | provider 注入・session 共有で class を planner の 9 記号に載せられる | **partial** — P5 に置いたが検査は注入 run のみ |
| A3/B2 | 単調集合の差分が 1 bit/query の oracle になる | **partial** — (iii) を推奨に留めた (必須化は撤回)。oracle は残る |
| A4 | 予算が ID 変更・削除・分割で新品に戻る | **partial** — 回復経路と上位 origin を書いたが authority・重複発行・rollback は未決 |
| A5/B7 | 親 brief の 3 前提が誤り | **closed** — §2.2 / §2.3 で訂正 |
| A6 | 保証に対応する機械検査が無い | **partial** — draft と明示し §7 の検査可能度を正直に書いたが、検査自体は無い |
| A7 | 単調性は構文上・origin 内に限る | **closed** — §3.4 に射程を明記 |
| A8/B3 | 単一 red から因果は導けない | **closed** — §3.2 で no-good cut と名乗り、atom 全域禁止も撤回 |
| A9/B5 | control ledger の原子性・crash 復旧・seal 自己参照が未定義 | **partial** — §4⑥ の未解決に明記、P3 |
| B4 | D114 保証外の層が formal consumer まで素通り | **partial** — P7 に置いたが proof schema・consumer 閉集合は未決 |
| B6 | 「設計確定」への状態遷移が不正 | **closed** — draft を維持し、確定表現を撤回 |
| B8 | 実シグネチャと実装地図が不足 | **partial** — `layer3_report.py` の stage 拒否を §4⑥ へ追加。全 consumer 地図は未完 |
| B9 | 1 世代運転・runbook・ablation の契約が壊れる | **partial** — §4③-7 と §8 択一 4・5 へ。on/off の意味は未定義のまま |

## 段 6 (20 件、主要なもの)

| # | 所見 | 本版での対応 |
|---|---|---|
| revA-1 / revB-4 | atom 全域禁止は過剰一般化 | **closed** — exact-mask cut へ縮小 (§3.2) |
| revA-2 / revB-7 | P1〜P10 は機械 predicate でなく cap-lift に結線もされていない | **closed (表現)** — 「機械検査可能」の主張を撤回し §7 に検査可能度を明記。結線自体は未実装 (択一 2) |
| revA-3 | (iii) の必須化はユーザー裁定の逸脱 | **closed** — 必須化を撤回し §8 択一 3 へ |
| revA-4 | 32 点・whiteboard 3 状態の事実認定が誤り | **closed** — §2.4 / §2.2 で訂正、D96 手続の必要も明記 |
| revA-5 / revB-2 / revB-6 | 「解いた・確定・supersede」が draft と矛盾 | **closed** — 全 docs の表現を弱めた |
| revA-6 / revB-3 | critic report-only と reflux on/off が両立しない | **partial** — 未解決として §4① と §8 択一 4 に明記 |
| revA-7 | origin preimage が D と本文で不一致 | **closed** — §3.5 を正本と宣言し D119 は骨子のみ |
| revA-8 | 件数の算術誤りと B8 脱落 | **closed** — 本節で訂正 |
| revA-9 / revB-6 | runbook の事実誤り (metrics・run-root) | **closed** — runbook を訂正 |
| revB-1 | D116 の採番衝突 | **closed** — local main を取り込み **D119** へ改番 |
| revB-5 | D51 の逐次 provenance が公開面として取り残し | **closed** — §4② の観測面に追加 |
| revB-8 | runbook 3.3 は現在の Pegasus 運用では実行不能 | **closed** — runbook に blocked 注記、P8 の射程も限定 |
| revB-9 | insights の authority marker 欠落 | **closed** — 冒頭に付与 |
| revB-10 | main-experiment の path が repo 相対でない | **closed** — 訂正 |
| revB-11 | X1〜X7 / I2/I3 の対応表が無い | **closed** — §10 に追加 |
| revB-6 (コード側) | 実装のエラーメッセージが「裁定まで」と主張 | **未着手 (scope 外)** — 実装面の変更になるため次の一手へ起票 |

# 7. 多世代開放 (`MAX_APPROVED_GENERATIONS > 1`) の前提条件

D114 の承認上限の引上げは、D96 手続に加えて次をすべて満たしたときだけ許す。
**「すべて機械検査可能」とは主張しない** — 各条件の検査可能度を正直に併記する。

| # | 前提条件 | 検査可能度 |
|---|---|---|
| P1 | 候補表現が固定 5-bit IR に閉じ、正準 emitter が全 32 mask で監査済み | **部分的**。自由文字列の拒否は書ける。emitter は自己参照だと恒真なので独立 golden が要る |
| P2 | 禁止集合・実効 mask・IR SHA・D51 逐次 provenance・driver 戻り値が untrusted 面に現れない | **定義後なら可能**。観測面の閉集合をまず定義しないと恒真化する |
| P3 | origin ledger が単一 in-flight・CAS・crash replay・削除耐性を持つ | **現状は不可**。authority と外部 anchor が未裁定。ローカル ledger 全削除は外部錨なしに検出できない |
| P4 | (択一 3 で (iii) を採る場合) batch cardinality・全候補の事前 commit・seal までの結果非公開 | **書けるが定義依存**。batch=1 なら恒真になる |
| P5 | provider 注入・role 間 session 共有・未予約 token が正式経路で拒否される | **3 要件のうち検査を書けているのは 1 件**。session 共有と token replay は未定義 |
| P6 | no-good cut を超えて座標 cut を主張するなら、anomaly からの独立再導出と相互作用の実証 | **条件文であり現状は非適用**。主張しない限り真。予め満たすべき条件ではなく、主張の前提 |
| P7 | formal consumer (`layer3_report.py` 等) が origin proof を要求する | **部分的**。proof schema・issuer・consumer 閉集合・正負例が未定義。**受理集合の変更ゆえ D96 手続** |
| P8 | 1 世代運転と **runbook 3.1 / 3.2 のみ**、reflux ablation が壊れない | **部分的**。runbook 3.3 は現在の Pegasus 運用では実行不能 ([T-276] / [T-277] 待ち) なので射程外 |
| P9 | whiteboard の値域 (direction/magnitude/result) と iteration 整合が閉じている | **定義後なら可能**。前 wave X4 / [T-287] |
| P10 | 予算値・origin authority・(iii) の扱いがユーザー裁定で確定している | **機械検査ではない**。人間 gate である |

**P4 と P6 は条件付き義務**である。(iii) を採らない場合の P4、座標 cut を主張しない場合の P6 は
**非適用**として扱い、cap-lift の失敗には数えない (無条件必須にすると cap が永久に解除不能になる)。
**無条件の義務 (P1・P2・P3・P5・P7・P9・P10) は現時点で 1 件も満たされていない。**

# 8. 裁定パッケージ (ユーザー判断待ち)

| # | 択一 | 親の推奨 |
|---|---|---|
| 1 | 予算値 `Imax/Qmax/Kmax` をどう決めるか (候補は 2/2/1 だが正当化が無い) | **択一 3 の結論を待ってから再導出する。** 単独では origin 分割で回収される |
| 2 | 承認上限の引上げを P1〜P10 の充足検査へ機械束縛するか | **択一 1・3 の確定後に独立 wave で実装する。** 今実装すると未裁定の設計を既成事実にする |
| 3 | 軸 (iii) (候補 batch の事前凍結) を多世代開放の必須前提にするか | **必須にすることを推奨する** (両レンズが独立に oracle の残存を指摘)。ただし親が独断で格上げするのは裁定の逸脱なので返す。採る場合は batch cardinality・事前 commit・結果非公開をセットで定義する |
| 4 | critic を report-only にするか、現行の reflux on/off ablation を維持するか | **両立しないため裁定が要る。** report-only にすると 8c の on/off treatment label が意味を失い、bool を残すと critic は report-only でなくなる |
| 5 | 診断 run (no-build `dry-pass`、runbook 配線確認) を予算の外に置く扱いでよいか | **よい。** 予算に数えると配線確認だけで origin を使い切る |
| 6 | origin authority を repo 内 tracked registry で担うか、別 service / ACL へ分離するか | **tracked registry から始め、「同一 UID の caller からの秘匿は不可」を残余として明示する** |
| 7 | **cut の適用範囲をどう正当化するか** — exact-mask (安全だが封じ込め相当) と座標 cut (軸 (i) を満たすが根拠が要る) の中間をどう設計するか | **構造化 anomaly から禁止範囲を再導出する契約 (P6) を先に設計することを推奨する。** それが無い限り本設計は規律 3 の還流を実現しておらず、T-244 本体は未解決のままである |

# 8.5 事前登録文書は触れない (段 6 で実測)

`docs/phase3-main-experiment.md` は S-1 freeze (`output/s1-freeze/known_axes_freeze.json`) が
sha256 で bytes を pin する**事前登録文書**である。docs だけを変える wave でも、この 1 ファイルを
編集すると T-080 freeze migration の closure 検査 (`known_axes.source_closure` の
`changed 12 / unchanged 51`) が破れ、10 件のテストが赤くなる。**本 wave は段 6 の受入全走でこれを
実測し、同ファイルへの編集を撤回した。**

したがって D39 決定 4 の ablation 記述 (critic の機序帰属を coder/planner へ還流する on アーム) は
事前登録のまま残る。本 draft が 8c について提案する還流形はそれとは別物であり、**8c で on/off
treatment をどう定義するかは未裁定** (§8 択一 4) である。

# 9. 本 wave の射程 (実装していないこと)

- 本 wave は **docs のみ**である。コード・テスト・設定は 1 行も変更していない。
- したがって**変異 matrix は対象外**である (`DW-S04`: 実装差分が無い)。
- `MAX_APPROVED_GENERATIONS = 1` は変えていない。`generations > 1` という**引数**は 3 入口で
  拒否されるが、`drive` 注入・`drive_iteration()` 直接反復・並行 race は D114 のとおり**保証対象外**であり、
  「cross-generation 還流を機械的に禁止した」とは名乗らない。
- 本設計のどの機構も実装されていない。`reflux-control` stage、origin ledger、5-bit IR、
  正準 emitter、非干渉検査はすべて**未実装**である。

# 10. 前 wave の裁定パッケージ項目との対応

| 前 wave の項目 | 本 wave での扱い |
|---|---|
| X1 (`run_trial` 注入 seam) | P5 の一部として前提条件化。実装は未着手 |
| X2 (`drive_iteration()` 直接反復) | 同上 (P5)。8c formal wrapper に token を要求する設計 |
| X3 (freshness の TOCTOU) | P3 の一部 (単一 in-flight・CAS)。未実装 |
| X4 (`state_from_dict()` の値無検証) | **P9** として前提条件化。[T-287] が保持 |
| X5 (`delta_pct≡None` の説明誤り) | **[T-288] が D118 で解決済み。** 本文 §2.1 に反映 |
| X6 (100 倍の単位ずれ) | **[T-288] が D118 決定 1・2 で解決済み** |
| X7 (`WhiteboardEntry.result` の閉 enum 化) | P9 と同じ変更単位。未着手 |
| I2 / I3 (dev-wave 自己改善 2 件) | [T-291] が保持。**本 wave では扱わない** |
