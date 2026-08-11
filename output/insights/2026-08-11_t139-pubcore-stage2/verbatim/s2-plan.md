# 段 2 プラン — [T-139] 公表 core 段階 2

判定は **GO**。ただし、dev-wave の「段 2」と文書の「段階 2」は別物である。本 wave は 3 文書を承認候補として再提出するところまでで、文書上の段階 2 へは進めない。

新規成果物には実在行番号がないため、行番号を捏造せず見出しで指定する。既存ファイルの参照だけを実測済み file:line とする。

## P1〜P7 の判定

| 項目 | 判定 | 根拠・補正 |
|---|---|---|
| P1 | 賛成 | exact bytes の承認はユーザーへ返し、その承認を canonical 台帳へ fold した後にだけ発効する。[publication-core.md:100–106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/publication-core.md:100) |
| P2 | 賛成 | core も B も `authority: none` の未凍結草案なので erratum ではなく新 path の v2 とする。旧版は歴史記録として不変。 |
| P3 | 賛成 | `0.05/[k(k+1)]`、`α_pub=0.025` を独立記述し、§5.3 の等式で定義された `α*` と比較する。[publication-core.md:277–304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/publication-core.md:277) |
| P4 | 賛成 | `candidate_cap: 1`、`admissible_ordinals: [1]` を公表 study の値として独立記述する。 |
| P5 | 条件付き賛成 | `reservation_mode` / `release_on_failure` は残す。ただし意味は `candidate_cap` の消費・非復元という候補数会計に限定し、公表台帳の同定・原子予約の権威として読ませない。外すと失敗後に cap を復元できる読みが生じ、受理集合を広げる。 |
| P6 | 賛成 | 固定 literal と caller 入力排除だけで source core §14 の `b03` 義務を満たす。ordinal の一意性・非再利用は同義務に含まれない。[preregistration.md:339–344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:339) |
| P7 | 賛成、分担を明確化 | core §8.1/§8.2 が entry と予約の意味、`p03` は canonical main + land lock という台帳 authority と transaction 境界だけを持つ。受領証 schema・validator の受理条件は持たせない。 |

## S-A — 新 core v2

出力先:

`output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md`

現行ファイルを複製し、変更する現行行は **104、105、569、570、571 の 5 行だけ**とする。行数を変えないため、v2 側でも同じ行番号になる。

### §0 の置換

現行 [publication-core.md:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/publication-core.md:104):

```text
| 1 | 草案。`authority: none`。承認待ち | **← ここ** |
```

置換後:

```text
| 1 | 承認候補。`authority: none`。凍結承認と canonical fold の完了待ち | **← ここ** |
```

現行 [publication-core.md:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/publication-core.md:105):

```text
| 2 | 文書として発効 (承認決定を canonical 台帳へ fold した commit 以後)。機械 gate 未実装 | 承認後 |
```

置換後:

```text
| 2 | 文書として発効 (承認決定を canonical 台帳へ fold した commit 以後)。機械 gate 未実装 | 承認決定の fold 後 |
```

本 wave 自身では段階 2 へ進めない。ユーザーの byte-level 承認発話も単独では発効点ではなく、その決定を canonical 台帳へ fold した commit が必要である。

### §8.1 blockquote の置換

実際の重複 blockquote は brief 記載の 565–568 ではなく、[publication-core.md:569–571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/publication-core.md:569) にある。

現行逐語:

```text
> **重複する記述がある。**追補 B 草案 (`b03`) も `ledger_kind = individual_publication` を
> 提案している。**どちらが公表系列の正本かは未確定であり、承認時のユーザー裁定に委ねる**
> (`package.md` の C-2)。本書はこの重複を自分の側で一方的に解決しない。
```

置換後の逐語案:

```text
> **公表系列の予約の正本は本書と追補 P である。**本書 §8.1 が根と種別、§8.2 が予約の規範を定め、
> 追補 P の `p03` が台帳の同定と原子性の実装契約を確定する。公表系列の予約はこの二者だけから
> 解決し、この二者以外の文書を予約の権威として継承・参照・合成しない。
```

追補 B の名称・path・field への参照を置かない。

### 不変行

変更集合は厳密に次だけとする。

```text
{104, 105, 569, 570, 571}
```

タイトル、metadata、source binding、§1〜§7、§8.2以降、§9〜§11は 1 文字も変えない。旧 `publication-core.md` も変更しない。

## S-B — 追補 P

出力先:

`output/insights/2026-08-11_t139-pubcore-stage2/addendum-p.md`

### Envelope

追補 A は metadata fence → §0 preamble → `## fields` → 末尾 disclaimer の順である。[addendum-a-reissue.md:31–75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:31) 追補 B も同型である。[addendum-b.md:3–61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:3)

追補 P は次の外形にする。

```text
# title
metadata fence
## 0. 本書の位置づけ
core_ref
envelope grammar
---
## fields
### p01 ...
### p02 ...
### p03 ...
---
## 本書が主張しないこと
```

機械実体は [addendum_envelope.py:114–180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/orchestrator/preregistration/addendum_envelope.py:114) であり、

- UTF-8 を要求する。
- fence 外に `## fields` がちょうど 1 件必要。
- 次の fence 外 H2 までにある fence 外 H3 の先頭 token だけを key とする。
- duplicate、missing、extra を別々に拒否する。

追補 B の「grammar は fence を除外しない」という説明とは実装が異なる。P は実装に合わせつつ、既存文書より厳しい慣行として fenced block 内にも `## ` / `### ` 行を置かない。実装変更は提案しない。

### 従属先三つ組と鶏卵の閉じ方

`core_ref` は次の形にする。山括弧は計画上の placeholder であり、literal のまま commit してはならない。

```yaml
core_ref:
  path:   output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md
  commit: <C_core の 40-hex>
  sha256: <C_core の tree にある同 blob の SHA-256>
```

commit 構成は三段に分ける。

1. `publication-core-v2.md` だけを commit `C_core` にする。
2. `C_core` の tree から core blob の SHA-256 を計算し、実値を P の `core_ref` へ書いて P・B v2・spool fragments を commit `C_docs` にする。
3. `C_core` と `C_docs` から 3 文書の path / commit / digest を得て、裁定 package を commit `C_package` にする。

3 commit は同じ wave land に含めてよい。`C_core` は内容を固定する commit であって承認 fold commit ではない。後続のユーザー承認を canonical 台帳へ fold した `F_approval` が別に発効点となる。この二段構成は「自分の fold commit を本文へ書けない」ため payload を先に固定する D262 の先例と同型である。[decisions.md:12138–12149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/decisions.md:12138)

### `p01` 逐語案

```markdown
### p01 — 公表系列の候補数上限と許容 ordinal

```yaml
candidate_cap: 1
admissible_ordinals: [1]
immutable_in_this_addendum: true
```

公表系列の候補数上限を `K_pub = 1` とする。許容 ordinal は `{1}` だけであり、
ordinal `2` 以降を公表候補として受理しない。

この値は資源と governance の裁定値であり、観測値・検定統計量・公表結果から導出しない。
上限を変更する場合は、本書を書き換えず、対象データを 1 点も見る前に新しい study と追補を承認する。
```

### `p02` 逐語案

```markdown
### p02 — 公表系列の累積 spending 関数の数値割当て

```yaml
familywise_alpha: 0.05
spending:
  domain: k = 1, 2, 3, …
  alpha_pub_k: 0.05 / (k * (k + 1))
current_study:
  k: 1
  alpha_pub: 0.025
unspent_tail:
  reclaim: false
  redistribute: false
affects_primary_q: false
```

```text
Σ_{k≥1} 0.05 / [ k(k+1) ] = 0.05
```

本 study は `k = 1` を占め、`α_pub = 0.025` とする。未使用の tail は既存候補へ戻さず、
primary 系列の有意水準、臨界値 `q`、受理条件、標本数の入力に用いない。

本書が従属する core §5.3 の等式により、

```text
α* = 6 · [ 1 − F_{t,12}( q(13, 0.025) ) ] = 0.014415014983…
α_pub = 0.025 > α*
```

である。したがって §5.3 の限定を満たす。比較は等式で定義された `α*` の値に対して行い、
`0.0144150` 等へ丸めた表示値を判定の閾値として用いない。
```

### `p03` 逐語案

```markdown
### p03 — 公表台帳の同定と原子性の実装契約

```yaml
ledger_authority:
  canonical_history: land_serialized_main_history
  serialization_boundary: land_lock
  clone_local_or_fixed_ref_is_authority: false
atomic_reservation:
  entry_definition: publication_core_section_8_1
  reservation_semantics: publication_core_section_8_2
  check_absent_and_append_under_one_lock: true
  publish_before_unlock: true
```

`canonical_history` は、共有 land lock の内側で main へ反映された commit 列を意味する。
clone-local branch、未 land commit、または固定 Git ref は予約の権威にならない。

entry の key・create-only の意味・失敗時の非解放・欠落または重複時の帰結は
core §8.1 / §8.2 だけを正本とし、本 field では再定義しない。本 field が追加するのは、
entry 不在の確認、追記、main で可視になる commit の発行を 1 回の land lock の内側で完了するという
authority と原子性の要件だけである。

本 field は受領証の field を 1 つも追加せず、validator の受理条件を定めない。
台帳 path、entry の保存 schema、受領証上の field 名、照合 API は producer 実装 wave の責務である。
```

P の本文では `b01` / `b02` / `b03`、追補 B の名称・path、「同じ値」「引き継いだ値」を一度も書かない。「同じ値である」は比較対象を外部文書へ求めるため参照に当たり、禁止する。

### 末尾 disclaimer

```markdown
## 本書が主張しないこと

- **本書が機械的に執行されている、とは主張しない。**
- **本書が受領証 schema または validator の受理集合を定めた、とは主張しない。**
- **本書が source study の pilot / main admission、失敗分類、primary 判定を変更した、とは主張しない。**
- **本書が発効した、とは主張しない。**承認決定が canonical 台帳へ fold されるまでは
  `authority: none`、`default_effect: no-state-change` のままである。
- **本書は自分自身の digest を本文へ書かない。**
```

## S-C — 追補 B v2

出力先:

`output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md`

旧版はそのまま残す。`b01`・`b02` は [addendum-b.md:63–146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:63) を逐語保存する。

### `b03` の行単位差分

| 現行行 | 処置 | 理由 |
|---|---|---|
| 148–153 | 逐語で残す | heading と固定 root literal。`ledger_kind` は root namespace の値。 |
| 154–163 | 外す | current ordinal、予約 mode、失敗時非解放、別台帳の操作規定。 |
| 165–169 | 逐語で残す | 固定 literal からの根の導出と caller 入力排除。source core §14 の義務本体。 |
| 171–183 | 外す | 別台帳、create-only、ordinal 1、一意性、投入 deny という予約規定。 |
| 185–191 | 逐語で残す | 受領証 schema・validator 受理条件を増やさない保護境界。 |
| 193–203 | 外す | 予約 deny の時相、外部台帳、予約操作、正経路に関する規定。 |
| 205–210 | 残す | field 終端と一般 disclaimer。 |
| 211–216 | 下記へ置換 | `b03` の縮小後に古い create-only・一意性説明を残さない。 |

置換後の `b03` 全文案:

```markdown
### b03 — 累積台帳を束縛する正規の根の同定方法

```yaml
publication_family_root:
  fold_commit: 88d68f9127b31df5aafc3d59607896626a1652e8
  ledger_kind: individual_publication
```

個別公表系列の累積台帳を束縛する**正規の根**は、上の `publication_family_root` の literal から
導出する。**caller の引数、受領証の申告値、親系列 ID、試行 ID を入力にしない。**
`fold_commit` は限定例外の決定 (D234) を canonical 台帳へ fold した commit `F` である。
新しい正規の根を作れるのは、新しい study を承認する canonical なユーザー裁定だけであり、
**候補数上限の引き上げは新しい根を作る理由にならない** (`b01`)。

**本 field は core §12 の必須記録項目を増やさず、validator の受理条件を追加しない。**
core §12 が列挙する必須項目に、公表台帳の path・予約 entry の digest・予約 commit は含まれていない。
これらを受領証の必須記録に加えることは、必須 schema と受理集合を変える **core の変更**である。
core §12 は producer が宣言できる閉集合の種別について「field 名は実装 wave の新 D で確定する」と
定めており、`b03` はその決定を先取りしない。**受領証にどの field を置くか、validator がどの照合を
行うかは producer 実装 wave の責務である。**追加の受領証 schema が必要になったなら、
それは新しい core を伴う**別 study** の裁定対象とする (core §14)。
```

末尾 [addendum-b.md:211–216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:211) は次へ置換する。

```markdown
- **本書が受領証 schema や validator の受理集合を定めた、とは主張しない。**`b03` の規範範囲は
  正規の根の同定方法までであり、core §12 の必須記録項目を 1 つも増やさない。
  台帳の実体化・予約操作・照合手順は producer 実装 wave の責務である。
- **本書が公表手続きの正本である、とは主張しない。**公表セルの identity、検定統計量、`p` 値の構成、
  多重性の調整方式、同時区間の構成は本書の閉集合の外であり、本書から一意には定まらない。
```

### P5 と受理集合

`b01` の次は残す。

```yaml
reservation_mode: create_only
release_on_failure: false
```

これは「候補が cap を消費する時点」と「失敗しても cap が復元しないこと」の会計である。公表台帳の path、entry key、authority、atomic transaction は一切ここから導出しない。producer がこの二値を公表台帳操作の権威として読む実装は拒否対象とする。

### Source core §14 適合

source core が `b03` に要求する逐語は「累積台帳を束縛する正規の根の同定方法（親系列 ID の自己申告でリセットできないこと）」だけである。[preregistration.md:339–344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:339)

残す文章は、

- root を `(fold_commit, ledger_kind)` の固定 literal から導出し、
- caller、受領証、親系列 ID、試行 IDを入力から除外し、
- 新しい root は canonical なユーザー裁定だけが作れる、

と定める。したがって親系列 ID の自己申告による root reset は閉じている。ordinal の予約・一意性・非再利用までは保証しないが、それは source core §14 が `b03` に課した義務ではない。

### Exact-key

H3 は引き続き `b01`、`b02`、`b03` のちょうど 3 個である。既存 parser は H3 本文の長短や YAML subkey を field key と数えない。[addendum_envelope.py:123–149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/orchestrator/preregistration/addendum_envelope.py:123)

静的検査では generic な `require_exact_fields` に明示的に `{b01,b02,b03}` を渡す。既定集合は A 専用なので、引数なしの成功を B/P の検証と誤認しない。

## S-D — C-1 worklog fragment

出力先:

`docs/spool/worklog/2026-08-11-dev-wave-t139-pubcore-stage2-1.md`

`## 本文` に置く逐語案:

```markdown
- **C-1 の設計帰結を事前に記録した。**凍結 source core
  `output/insights/2026-08-07_t139-mainrun-design/preregistration.md`
  (`sha256 = ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9`) と、
  凍結 追補 A reissue
  `output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md`
  (`sha256 = f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec`)
  は **1 byte も変更していない**。追補 A `a10` の固定規則では、候補
  `J ∈ {4,…,13}` のうち最も緩い `J=13` でも
  `q(13,0.025)=3.449997`、`d⁻=1.0` の成分検出力は `0.57628` であり、
  `L_J ≤ 0.57628 < 0.80` となるため適格な `J` は存在しない。
  必要条件は `d⁻ ≥ 1.2210`、6 成分が同水準の場合の十分条件は `d ≥ 1.5623` である。
  これは凍結文書・受理条件・失敗分類を変更する裁定ではなく、既存設計が
  `design_not_feasible` に終端しうる事実の記録である。
```

並行 land 1 の fragment も `[T-139]` を更新しているため、本 fragment から `[T-139]` 自体を更新せず、本文記録と新規 task だけにする。これにより同じ `base:` を競合更新する必要がない。

## S-E — C-3 decisions fragment

出力先:

`docs/spool/decisions/2026-08-11-dev-wave-t139-pubcore-stage2-2.md`

逐語案:

```markdown
## {{D:t139-publication-downstream-boundary}}. 検証済み cluster 値の公表解析は paired measurement 例外の再行使ではない

**決定:** [T-139] の個別公表 study が入力にしてよいのは、source study の独立 validator が
適格と確定した全 cluster の `Y_j` だけとする。この downstream 解析は新しい測定、cluster の再選別、
paired 設計の再行使、または別 study への例外の一般化ではない。したがって roadmap は改訂しない。

**理由:**

- roadmap §3.6 (3'') は paired measurement の例外を [T-139] の RF 3-arm study に限り、
  他 study や通常の campaign compare へ自動一般化しない。
- 本公表 study は新しい割当て・arm 測定・cluster 内 contrast を作らず、source validator が確定した
  cluster-level 値を全件そのまま読む。
- 推定・検定・区間は cluster 間の標本平均と標本共分散だけから構成し、cluster 内の値を追加自由度として
  数えないため、限定例外の保護条件も弱めない。

**却下した選択肢:**

- 公表 study を roadmap の限定例外へ追記する — 測定例外を再行使しない解析まで列挙すると、
  例外が別 study へ広がったように読める。
- roadmap と抵触すると扱う — 検証済み出力を読む downstream 解析と、新しい paired measurement を
  同一視することになる。
```

対応する roadmap 条文は [roadmap.md:228–242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/roadmap.md:228)。とくに line 228 の限定、line 232 の fold 後発効、line 233 の source core 指定、line 234 の cluster-level 推論、line 238 の validator 権威をそのまま維持する。

## S-F — producer 実装 wave への起票

slug 案:

```text
{{T:t139-publication-analysis-layer}}
```

worklog fragment の `### 新規` に置く逐語案:

```markdown
- {{T:t139-publication-analysis-layer}} **P1・C-5 (a)・既存 T-139 producer land 2 へ合流**:
  承認済み公表 core と追補 P の三つ組を caller 非選択で解決し、`p01`〜`p03` の
  exact-key を approved 集合として検査する。source validator が確定した全適格 cluster の
  `J`・`Y_j`・workload ごとの `qualification_status` を権威入力として受け、
  publication validator が `T_k`、片側未調整 `p`、Holm、Bonferroni 同時下限を再計算する。
  consumer は固定順 6 行を欠落なく生成し、`qualification_status` を逐語複写して正分母 guard を適用する。
  core の無効化条件、同一 dataset の再解析禁止、source への結果逆流禁止、pilot 前の時点条件を守り、
  core §10.4 の 11 変異を publication 固有の受入事例として拒否する。
  公表台帳の実体化は land 2 §S7 項 7 の既存所有であり、本 task は予約台帳を重複実装せず、
  同項が返す権威ある予約結果だけを消費する。
```

producer wave に渡す要件は次に限定する。

1. 公表 core / P の承認済み三つ組解決と、caller 非選択の `p01`〜`p03` exact-key。
2. source validator の権威出力 `J`・全件 `Y_j`・`qualification_status` の受け渡し。
3. publication validator による統計量・Holm・同時下限の独立再計算。
4. 固定 6 行、正分母 guard、結果逆流禁止を守る consumer。
5. invalidation、pilot 前時点、同一 dataset 再解析禁止。
6. §10.4 の publication 固有 11 変異。単一理由帰属機構そのものは既存 land 2 側を使う。

### land 2 §S7 との非重複

実物は [land 1 package.md:155–167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/package.md:155)。

| §S7 | 既存所有 | 新 task の扱い |
|---:|---|---|
| 1 | 台帳 → manifest の trust-root 矢印 | 実装し直さず、解決済み binding を入力にする |
| 2 | `PATH` 差替え不能な Git trust root | 依存条件のみ |
| 3 | symlink / TOCTOU | 既存 path 防壁を利用 |
| 4 | correctness anomaly の構造化還流 | source producer 側に残す |
| 5 | 変異の単一理由帰属 | harness を再実装せず publication 固有 mutant だけ追加 |
| 6 | `a05` build 手順 | 対象外 |
| 7 | 公表台帳の実体化 | §8 / `p03` を規範入力として既存項が実装。新 task は予約結果の consumer のみ |

§S7 項 7 の「`b03` 個別公表系列台帳」という記載は定義ではなく未凍結要件へのポインタである。実装時の規範入力は新 core §8 + `p03`、source B の `b03` は root 同定だけ、と handoff で明示する。歴史 package 自体は書き換えない。

## S-G — 裁定 package

出力先:

`output/insights/2026-08-11_t139-pubcore-stage2/package.md`

問うのは次の **1 問だけ**とする。

```markdown
### Q-FREEZE — 3 文書の exact bytes を一体の承認束として凍結承認するか

次の path / commit / blob SHA-256 の三つ組で同定した 3 文書を、一体の承認束として承認するか。

1. 個別公表 core v2
2. 追補 P
3. source study 用 追補 B v2

- **(a) 3 文書を exact bytes で一括承認する (推奨)。**
  承認決定を canonical 台帳へ fold した commit 以後にのみ文書上の段階 2 が発効する。
  この回答だけでは pilot・本走・公表解析・機械 gate のいずれも発火しない。
- (b) 承認を保留し、修正を要する blob と逐語を指定する。
```

C-1、C-2、C-2b、C-3、C-4、C-5、B4、B8、P1〜P7 の方針は再度問わない。Q-FREEZE は C-4 の設計方針を再裁定する問いではなく、生成後の exact bytes を批准する問いである。

## 二重定義の検査

| 規範 | `b03` | 新 core §8 | P `p03` | land 2 §S7 | 最終判定 |
|---|---|---|---|---|---|
| source 個別公表系列の固定 root、caller による reset 禁止 | 定義する | 同じ `F` と非 reset を公表 study 側でも独立記述 | 再定義しない | 定義なし | **同値規範が b03 と core の 2 箇所に残る。**別 study が文書を参照せず値と guard を独立固定するための意図的重複 |
| `ledger_kind=individual_publication` | root literal の値として記載 | 公表 entry namespace として記載 | core §8.1 を pointer で指定 | 定義なし | 値が 2 箇所。文書参照ではなく独立再記述 |
| primary と公表の台帳分離 | 削除 | §8.1 だけ | 再定義しない | 定義なし | 1 箇所 |
| ordinal・create-only・失敗時非解放・欠落/重複時の帰結 | 削除 | §8.2 だけ | §8.2 を pointer で指定 | 定義なし | 1 箇所 |
| canonical main / land lock / clone-local 非権威 | 削除 | 「canonical・atomic」という抽象要件だけ | 具体的 authority と transaction 境界を定義 | 定義なし | 抽象規範と具体値の分担で、同一逐語の重複なし |
| 同一 dataset の再解析禁止 | なし | §8.3 だけ | なし | なし | 1 箇所 |
| 受領証 schema・validator 受理条件 | 明示的に定めない | §11 で未実装と記録 | 明示的に定めない | 未凍結要件への pointer | 4 箇所のいずれにも定義しない。producer wave の専有 |
| 実装責務 | 実装しない | §11 で未実装 | 実装しない | 要件 pointer | S7/producer task が唯一の実装所有者 |

現行版で実際に二重定義されているのは、`b03` の ordinal・create-only・非解放・原子予約・一意性 ([addendum-b.md:154–183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:154)) と、新 core §8.1/§8.2 ([publication-core.md:545–581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/publication-core.md:545)) である。提案差分はこれを除く。

`b01` の `create_only` / `release_on_failure` は語が重なるが、候補数 cap の会計に限定する。公表台帳操作へ alias した時点で二重定義になるため、producer の publication namespace はこれを読まない。

## 静的検査

親が実装後に次を確認する。pytest 緑は本段の要件にしない。

- source core と追補 A reissue の SHA-256 がそれぞれ `ac939af4…`、`f7db96ce…` のまま。
- core v2 と旧 core の差分が `{104,105,569,570,571}` だけ。
- P に `追補 B`、`addendum_b`、`b01`〜`b03`、「同じ値」の出現がない。
- `require_exact_fields` を明示集合で呼び、P が `{p01,p02,p03}`、B v2 が `{b01,b02,b03}`。
- B v2 の `b01`・`b02` block が旧版と byte 一致。
- 3 文書とも自己 SHA-256・自己 commit を本文に持たない。
- package の三つ組は `C_core` / `C_docs` の tree から再計算した値と一致。
- `authority: none` と stage 1 の矢印が、ユーザー承認 fold 前には残っている。

## リスク

### (a) 受理集合が黙って広がる箇所

- `b03` から投入 deny・ordinal 一意性を除くため、旧 B 本文を admission gate としていた consumer があれば広がる。ただし現時点に機械 consumer は無く、source core §14 の委譲も root 同定だけである。将来実装は新 core/P/S7 から予約を読む。
- P5 の 2 key を削除すると、失敗後に `candidate_cap` を復元できる読みが生じるため残す。
- `p03` へ受領証 schema や validator 条件を足すと source core §12 の受理集合を変更する。明示的に禁止する。

### (b) 凍結文書の bytes が動く箇所

なし。`ac939af4…` の source core、`f7db96ce…` の追補 A reissue、旧 publication core、旧 B は全て不変。変更は新 path の 3 文書と spool/package だけ。

### (c) 自己参照 digest が生じる箇所

- P と core を同一 commit に置き、P がその commit を `core_ref` に書こうとすると自己参照になる。
- package と P/B を同一 commit に置き、package がその commit を三つ組に書こうとしても同様。
- `C_core → C_docs → C_package` の三段 commit で閉じる。各文書は自分自身の digest を持たない。

### (d) 承認が「発効」へ滑る箇所

- core §0 の矢印を段階 2 へ移すこと。
- package の Q-FREEZE を「回答時点で発効」と書くこと。
- B の既裁定 C-2 を理由に、未確定 v2 bytes を発効済みと扱うこと。
- worklog / decisions fragment の fold を 3 文書の承認 fold と混同すること。

いずれも stage 1 維持、`authority: none`、Q-FREEZE の明記、後続 `F_approval` の分離で防ぐ。

## 総括

- core v2 の変更は現行 104・105・569〜571 行だけで、段階 1 を維持する。
- P は `p01`〜`p03` を独立記述し、`0.025 > 0.014415014983…` を丸めず記録する。
- B v2 の `b03` は固定 root と caller 非選択だけに縮め、予約規定を core §8 + Pへ一本化する。
- 最大のリスクは exact-byte 承認を発効と誤認することと、同一 commit に三つ組を書いて自己参照させることである。