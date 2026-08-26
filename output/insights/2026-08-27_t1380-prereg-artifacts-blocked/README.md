# [T-1380] 事前登録 artifact 3 件は現状では発行できない — D1077 の前提が成り立たない

**日付:** 2026-08-27
**wave:** `worktree-dev-wave-t1380-prereg-artifacts`
**base:** local main `9ebd340b26d32520af3b97d585ce68bc745b5e45`
**実装面の差分:** ゼロ (裁定により実装しない)

## 1 行で

裁定 D1077 は「正式系列を止めている 3 artifact を、設計文書を権威として機械的に導出して
発行する」と定めたが、**導出の権威が実在しない**ことを実測で確かめた。加えて **D549 / D959 /
D992 が同じ作業の着手順序を既に裁定しており**、本 wave はそれに抵触する。実装せず、
新事実を添えてユーザー再裁定へ戻す。

## 2. 発行対象と現状

`output/s8c-preregistration/` に不在なのは 3 件ではなく 4 件である。

|artifact|schema|不在|
|---|---|---|
|`trial-manifest.v1.json`|`p3-8c-trial-manifest/v2`|不在|
|`prereg-effective-binding.v1.json`|`p3-8c-prereg-effective-binding/v1`|不在|
|`schedule.v1.json`|`s8c-schedule/v1`|不在|
|`attempt-registry.jsonl` (genesis)|`p3-8c-attempt-registry/v2`|不在。**binding が必須 field で参照する**|

`git ls-files output/s8c-preregistration/` は 12 件を返し、その全部が `arm-inputs/` (2 件) と
`condition-freeze/` (10 件) である。

binding の必須 field `attempt_registry_path` / `attempt_registry_initial_sha256` は
genesis を指し、`load_effective_binding_at_commit` は**内容 commit `P` に置かれた genesis blob の
hash 一致**を要求する。したがって「3 件」という数え方自体が実態と合っていない。

## 3. 導出の権威が実在しないこと (実測)

### 3.1 schedule authority 18 field のうち 3 件が実運用の値と矛盾する

`s8c_schedule.validate_authority` は 18 field の閉じた集合を要求する。
そのうち `INITIAL_STATE_AUTHORITY_KEYS` の 8 件は、実運用では run 開始時に確定する値である
(`p3_autonomous_workload_trial` の role payload 閉 key 集合と同じ語彙)。
実運用の値をそのまま渡すと、次の 3 件が通らない。

|field|実運用の値|schedule 側の要求|
|---|---|---|
|`leakproof_context`|文字列 (`s8c_generation_projection.LEAKPROOF_CONTEXT`)|JSON object (`_MAPPING_AUTHORITY_KEYS`)|
|`whiteboard`|正式初期状態では空配列 (`_whiteboard()`)|非空配列 (`_validate_non_degenerate_value`)|
|`descriptor_binding`|cell (arm) ごとに異なる|全 cell 共通の単一 mapping|

さらに `p3_autonomous_workload_trial._load_s8c_schedule_authority()` は
**無条件に例外を送出する**。production の authority は 1 つも存在しない。

**この矛盾を projection 規則で埋めることは本 wave にはできない。** 段 3 レンズ B が
決定台帳を遡って確かめたところ、18 field の schema を導入した D530 が裁定したのは
「caller 供給・閉じた key 集合・型・非空性」までであり、**18 個の field 名と型対応は
実装著者の選択**である。schema 導入時のテストは production と異なる fixture 値
(`leakproof_context` を object、`whiteboard` を非空 sentinel) を使っていた。

### 3.2 3 つの値が設計文書から一意に決まらない

- **`campaign_id`**: production は実 site から `ident.campaign_id()` で再計算し exact 一致を
  要求する。正式 site が未確定なので導出できない。発明した値は launch 時に拒否されるか、
  特定 site を暗黙に選んだ manifest になる。
- **`freeze_id`**: 8b は「freeze identity」を要求するが、condition-freeze tip digest /
  manifest digest / ratified generation のどれを使うかを定めた規則が無い。
- **genesis の slot 集合**: 8b は全 (holdout, 構成, 反復, attempt) slot を最初の観測前に
  閉じた集合として割り当てることを要求する。反復数 `n` は事前登録 §5 の未記入欄で、
  8b は「`n` / `delta_min` / `sd_max` の値は凍結しない」と明記する。retry 理由の exact 列挙も
  事前登録の凍結範囲に無い。**genesis は create-only かつ freeze ごとに唯一**なので、
  濃度を発明して発行すると freeze が誤った割当へ恒久的に束縛される。発行しないより悪い。

## 4. 既裁定との抵触 (本 wave の最も重い発見)

|決定|日付|内容|本 wave との関係|
|---|---|---|---|
|**D549**|2026-08-19|`schedule.v1.json` の commit は「配線と権威の実体供給が完了する別 wave (T-1380) まで scope 外」。却下した選択肢に「暫定 authority で実装する — **段 3 の敵対相談 2 本が独立に不採用を推奨した**」|本 wave がやろうとしたことを名指しで却下済み。しかも D549 は T-1380 を「配線と権威供給を行う wave」と定義しており、本 wave の scope (C05 配線を除外) と食い違う|
|**D959**|2026-08-26|8c の閉塞は依存の層。(d) manifest・二段束縛 record・registry の不在、(e) schedule authority の無条件 raise は、(a) 発効判定に充足を返す終端の不在に**従属する下流症状**であり、**順序を入れ替えて先に解除してはならない**|本 wave が発行しようとする 3 artifact がまさに (d)(e)|
|**D992**|2026-08-26|判定用 schedule の権威を凍結 spec に置く実装は、**共有 8b ratified freeze が active になるまで着手しない**|実測: `load_ratified_freeze()` は `[no-active] live active pointer が無い (v2 未発効)`。前提未充足|
|**D930**|2026-08-26|却下した選択肢に「3 artifact を本 wave で生成して commit する — D549 が明示的に却下している」|同上|
|**D1077**|2026-08-27|3 artifact は設計文書を権威として機械的に導出して発行する|**本文にも、記録した worklog 1011 の 1 行にも、上記 4 件への言及が無い**|

**同じ問いに対して、2026-08-19 の敵対相談 2 本と 2026-08-27 の敵対相談 2 本が、
互いを知らないまま 4 本とも同じ答えを出している。**

## 5. 取り下げた主張 (親の当初の value 論)

親は段 2 の進行中に独立 probe を書き、
「`schedule.v1.json` を足すと C05 が `EVIDENCE_UNDEFINED / schedule-schema-absent` から
`UNSATISFIED / schedule-consumer-unreachable` へ進み、SATISFIED は 0 のまま」と実測した
(12 述語のうち差分は C05 の 1 行だけ)。これを本 wave の値打ちとして挙げた。

**段 3 レンズ A がこれを正しく攻撃した。`_evaluate_c05` は artifact を decode しない。
1 byte の blob でも同じ遷移が起きる。** したがってこの遷移は「正当な schedule を発行した」
ことの証拠にはならず、gap ledger が「schema は成立した」と誤読される危険すらある。

**親の value 主張は取り下げる。** 「発行すれば閂が 1 つ進む」は
「blob を置けば表示が変わる」でしかなかった。

## 6. 併せて記録する scope 外の real 所見

- **binding validator が genesis を parse しない。** `validate_preregistration_binding()` は
  genesis blob の hash 一致だけを見て `load_attempt_registry()` へ通さない。
  P の canonical path に任意 bytes を置きその SHA-256 を binding に書けば受理される。
  **使ってはならない**が、実装の穴として実在する。
- 証拠契約 C03 / C08 の `field_paths` は `cells[*].trial_id` だが、実装の manifest schema は
  `trials[*]` である ([T-1806] / D967 の担当)。
- 8b は「manifest は cell ごとに `n` を持つ」と要求するが、manifest schema v2 の key 集合は
  `trial_id / arm / holdout / campaign_id / generations` だけで `n` を持たない。
- `assert_effective_commit_exact_parent` は `C` の親集合だけを検査し、
  `C` が binding path **だけ**を導入したことは検査しない。設計の要求と実装に隙がある。
- 論文 §8 B-3 の「どちらの経路も 3 artifact の不在に阻まれている」は事実として正しいが、
  **D959 の層の記述と併記しないと「3 件を作れば進む」と誤読される。**
  実際には (d)(e) は (a) に従属する下流症状である。

## 7. 起動経路の整理 (次の wave のために)

非 certifying 経路 (`admit_registered_formal_noncertifying`) が要求するのは
明示 opt-in、manifest 読み込み、`validate_condition_freeze_at`、launch binding の 4 点で、
**12 述語を参照しない。schedule.v1.json も要求しない。**
必要なのは manifest + trial registry の registration + effective binding (+ genesis) である。

したがって「schedule を除いた 3 件で非 certifying 経路だけ開ける」形は構造的にはありうるが、
その 3 件も `campaign_id` / `freeze_id` / slot 集合が未確定なので現状は発行できない。

二段束縛の commit 構造 (anchor `A` → 内容 `P` → binding だけの直子 `C` → 記録 `R`) は
段 2・段 3 の 3 本とも妥当と判定した。`dev_wave_land.py` の ff-only は `C` の親集合を変えず、
spool fold commit は landing tip の後続なので `P` と `C` の間へ割り込まない。
**この構造は次の wave がそのまま使える。**

## 8. verbatim

- `verbatim/s2-plan.md` — 段 2 プラン
- `verbatim/s3-consult-sol.md` — 段 3 レンズ A (受理集合と正しさ防壁)
- `verbatim/s3-consult-luna.md` — 段 3 レンズ B (導出の権威・自己参照・二段束縛)
- `verbatim/s4-adjudication.md` — 段 4 裁定 (択一の表を含む)
