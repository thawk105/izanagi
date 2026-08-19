# 裁定パッケージ — [T-139] Q1 canonical decision の起草 (V1〜V5)

正本。wave `dev-wave-t139-q1-canonical-decision` が段 4 で確定させた、ユーザー手番の設計択一 5 件。

```text
authority: parent (dev-wave manager)。**ユーザー裁定はまだ無い。**
wave: dev-wave-t139-q1-canonical-decision / branch worktree-dev-wave-t139-q1-canonical-decision
作成: 2026-08-13 08:2x JST
repo 外の控え: /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-t139-q1-canonical-decision.md
```

**前提:** 指示は「第 7 束 Q1 (a) が定めた canonical decision を起草して land する」だった。
本 wave はそれを実行し、**起草してみて初めて判明した事実**により land しないと判断した。
`DW-S04` の定めどおり親は Q1/Q2 (a) を不採用にせず、新事実を添えて再裁定へ戻す。

---

## 先に、確定できたこと (次 wave はここから始めてよい)

**指示文の要約に誤りが 1 件あった。** 指示は Q1 (a) を「固定 envelope + namespaced projection」と
書いていたが、canonical worklog エントリ 516 の逐語では**それは Q2 (a)** であり、
**Q1 (a) は受理述語の穴 4 件 (B1〜B4) を 1 本の canonical decision で閉じること**である。
`DW-S01` の F31 (裁定要約と本文が食い違えば本文優先) に従い本文を採った。
レンズ B が独立に照合し、この解決が正しいことを確認した。

**B1〜B4 の 4 件はすべて実在の欠落である** (親が凍結成果物を直接読んで確認)。
うち **B1 は「欠落」ではなく承認済み 2 文書の矛盾**である。

- §7.1(12) は CMakeCache の再読を validator の必須責務と定める (`record-items-v2.md:775`)。
- schema が持つ CMakeCache 由来の値は `arms.*.compile.cmake_cache` だけで、
  これは `{trace, add_analysis}` の 2 boolean の**申告値**である。`cmake_cache_raw` は 0 件。
- §8 はその field を受理条件の入力に使うことを**明示的に禁じ、落ちるテストを要求する**
  (`record-items-v2.md:784-799`)。

**使ってよい唯一の入力が、使ってはならないと名指しされている。**

**approval manifest は承認済み schema の必須 field である** (親が直接確認)。
`preregistration.required` に `approval_manifest` が含まれ、型は `blobRef` である。
散文の言及ではなく、この field が無い受領証は schema 検査を通らない。

---

## V1 (最上流). D320 の既定を、T-139 のどの対象について上書きするか

**これが決まらない限り Q1 は原理的に閉じられない。** 本 wave の起草がそれを実証した。

### 事実 (時系列。すべて実測)

| 時刻 (JST) | 出来事 |
|---|---|
| 2026-08-12 | D320 が land。bytes 級 provenance 機構の**新設・維持は既定で見送り** |
| 2026-08-13 00:0x〜00:1x | **第 7 束**。T-139 Q1〜Q6 を「推奨どおり」で全問確定。**D320 も K1 も名指ししていない** |
| 2026-08-13 02:0x | land2-q4 wave が **K1 を起票** (D320 と Q1/Q2 (a) の衝突)。**ユーザー未回答** |
| 2026-08-13 07:2x〜08:1x | 本 wave が起草。**衝突が回避不能**であることが判明 |

**K1 はユーザー裁定より後に起票されており、一度もユーザーへ問われていない。**
段 3 の 2 レンズ (`sol` / `luna`) が**独立に**ここへ到達し、ともに
「暗黙 supersession で処理せず裁定へ返せ」と判定した。

### 対象は 3 つあり、性質が違う

| # | 対象 | D320 の列挙に該当するか | 親の読み |
|---|---|---|---|
| ア | **approval manifest そのもの** | **しない** | D320 の**前日**に D282 が exact bytes 承認した schema の**必須 field**。§7 と §7.1(19) が 2 箇所で明示要求。D320 は既承認 artifact の必須 field を遡って削除する文言を持たない |
| イ | **新 exact-byte approval payload** (`record_items` / `receipt_schema` role を supersede する `F_r*`) | **する** | D320 の「commit への束縛」「承認への署名」そのもの |
| ウ | **conformance vector index の digest pin** | **する** | D320 の「bytes 同一性」。ただし §7 が「その digest を approval manifest が pin する」と明示要求している |

### 回避経路が無いことの実証

**イを作らずに B1 を閉じる案は 2 つしかない。**

- (a) semantic validator を常時拒否にする → **受理集合が空**。R3 (a)「受理集合が空の gate は
  land しない」が禁じた当のものである。
- (b) §7.1(12) の CMakeCache leg を落とす → **受理述語の弱化**。絶対規律 2 の直接違反。

### 問い

- **(a) ア・イ・ウの 3 つとも、T-139 の範囲に限り D320 の既定を上書きする** (親推奨)。
  canonical decision 本文へ「D320 の既定を T-139 の投入承認経路に限り上書きする。
  D320 全体を supersede しない」と明記する。
  **理由:** この 3 つが揃わないと `submit_pilot` は D234 の承認済み契約どおりに作れず、
  RF study の適格 verdict が 1 件も生成されない。第 7 束が Q1/Q2 = (a) と定めた以上、
  実行可能な唯一の読みがこれである。
- (b) アだけ認め、イ・ウは作らない。
  → **pilot は構造的に永久に投入不可**になる。B1 が閉じないので受理述語が定まらない。
  これを受け入れる (= pilot 系列を畳む) なら一貫した判断だが、Q4 とは両立しない。
- (c) D320 を優先し 3 つとも作らない。
  → (b) と同じ帰結に加え、承認済み schema の必須 field を満たせない受領証しか作れなくなる。
- (d) ア・ウは認め、イの代わりに **D282 の payload 自体を改訂する** canonical decision を起こす。
  → 親は評価できない。D282 は「既存 bytes を変えない」ことを前提に組まれており、
  改訂が既存 pin (`approval_payload.py` の `D282_DECISIONS_REF`、literal test) へ及ぶ範囲を
  本 wave は測っていない。

---

## V2. B4 の数値契約をどう扱うか

### 事実

起草は transcript の数値結果を `2^-80` 格子の dyadic 区間として固定した。
**承認済み追補 A はこれと異なる契約を既に固定している** (`addendum-a-reissue.md:724-748` 逐語)。

```text
各 p_k(J) は認証区間 [p_k^L, p_k^U] として評価する
(非心 t の CDF を、外向き丸めの区間演算で p_k^U − p_k^L ≤ 1e-9 となるまで評価する)
L_J^cert = max(0, 1 − Σ p_k^U)  /  U_J^cert = max(0, 1 − Σ p_k^L)
J = min { j ∈ {4,…,13} : L_j^cert ≥ 0.80 }
[L_j^cert, U_j^cert] が 0.80 を跨ぐ候補が 1 つでもあれば design_not_feasible
```

**レンズ B が検出し、親が一次資料で確認した。** これを canonical に書けば `J`、
`design_not_feasible` の発火点、main の `consumed_cluster_slots` 要素数、
conformance vector の期待値がすべて動く。**受理集合を変える変更である。**

### 問い

- **(a) decision は数値契約を書き直さず、追補 A `a10`/`a11` を三つ組で参照束縛するだけにする**
  (親推奨)。B4 が閉じるべきは transcript の **canonical byte grammar と authority binding**
  であって数値契約ではない。
- (b) 数値契約も decision で書き直す。
  → 親は反対する。承認済み契約の上書きであり、絶対規律 2 が禁じる方向である。

---

## V3. B1 の「申告値」の扱いをどう書くか

### 事実

起草は「`cmake_cache` / `trace_enabled` / `analysis_enabled` は**単独では**受理入力にしない」と
書いた。承認済み §8 の逐語は「**受理条件の入力に使ったら**落ちるテストを置く」であり、
単独か併用かを区別していない。

**レンズ A が「受理集合を静かに広げている」と検出した。**「単独では」を canonical に書くと、
最弱実装は申告値を他入力と併用して受理判定に使え、別実装は完全に無視する。
同じ受領証の受理・拒否が engine ごとに分岐し、§7 の
「engine の差で受理集合が変わってはならない」に抵触する。

### 問い

- **(a) 申告値は常に受理入力から外し、raw `CMakeCache.txt` の再 parse 結果だけを 3 者目にする**
  (親推奨)。申告値との一致は**拒否条件としてのみ**使う (一致しなければ拒否、
  一致しても受理の根拠にしない)。これなら弱化なしに B1 を閉じられる。
- (b) 「単独では」の形で書く。
  → 親は反対する。上記のとおり engine ごとに受理集合が分岐する。

---

## V4. conformance vector index の trust edge をどこに置くか

### 事実

`conformance_vectors` の期待 digest が manifest 自身にしか pin されない設計になっていた。
**レンズ A と B が独立に検出した。** manifest と弱い vector index を同時に差し替えれば
自己整合し、必要な負例を欠く validator が「conformance 済み」として certified 経路へ入る。

`approval_manifest` の bytes を承認する role は **D282 の 6 role にも D291 の 2 role にも無い。**

### 問い

- **(a) 有効な approval payload 側に conformance-vector index の三つ組を置く** (親推奨)。
  manifest の外に trust edge を作る。**V1 が (a) であることに依存する。**
- (b) manifest 自身の pin で足りるとする。
  → 親は反対する。自己整合する偽 manifest を止められない。
- (c) vector index を承認対象にしない (conformance vectors を pin しない)。
  → §7 の「その digest を approval manifest が pin する」という承認済み要求に反する。

---

## V5. Q1 と Q2 を 1 本の decision に収める構成を維持するか

### 事実

第 7 束 Q1 (a) は「4 件を閉じる canonical decision を **1 本**起こす」と定めている。
**レンズ B が構造的な問題を指摘した** — Q2 の manifest root は B1 の新 approval payload
(`F_r*`) に依存するため、**Q2 が B1 の後続 land に人質を取られる**。
`F_r*` を literal に持つ manifest は、その payload の fold の**後**にしか作れない。
Q4 の「1 session で manifest + resolver + writer + validator + vectors を組む」を
単一 land で成立させる方法が未整理である。

### 問い

- **(a) 1 本を維持し、manifest の root を `base_approval_fold_commit` (= `F_r`) と
  `approval_fold_commit` (= 実効 payload の fold) の 2 段で書く** (親推奨)。
  版が進んでも Q2 の契約文は変わらない形にする。
- (b) Q1 と Q2 を 2 本に分ける。
  → 第 7 束 Q1 (a) の「1 本」を動かすことになる。親は一存で提案しない。
- (c) 1 本のまま、`F_r*` の literal を持たない形の manifest 契約を書く。
  → 親は評価できない。D282/D291 がともに「manifest だけを trust root にしない」と
  要求している以上、literal を持たない manifest が何を根拠に検証されるかが定まらない。

---

## 次 wave への必須要件 (起草が実際に踏んだ落とし穴)

本 wave の起草は次の 4 つを踏んだ。次の brief に必ず入れること。

1. **承認済みの数値契約を decision で書き直さない。** 追補 A `a10`/`a11` は
   認証区間・選択規則・終端条件をすべて固定済みである (V2)。
2. **`受理入力に使わない` を `単独では使わない` へ言い換えない** (V3)。
3. **field 名は実 schema から取る。** 起草は `correctnessCompile` に `configure_argv` があると
   書いたが、実際は `argv` である
   (`correctnessCompile.required = ['identity_sha256', 'argv', 'trace_enabled',
   'analysis_enabled', 'cmake_cache', 'compile_commands']`)。
   **直前 wave の K4 と同型の事故が、同じ T-139 系列で独立に 2 度目である。**
4. **D234 (iii) の祖先 root は D234 の fold commit へ literal 固定する。**
   起草は「承認 decision の fold」と書き、`F_r*` とどちらか二義的になった。
   `F_r*` を選ぶと固定 core ref が条件を満たせず、**全 receipt が恒久拒否**される。

加えて、次は**投入経路 wave の設計事項**として残る (本 wave は手を出していない)。

- `series_id` の authority と、B2 sealed set・`receipt-set.json` の create-only publication の結線
- create-only の意味を「trusted API の実行契約」に限るか、検証可能な履歴性まで要求するか
- B4 の `q_derivation` / `certificates` / `result` を含む完全 grammar
- intent set / receipt set / transcript / manifest の discovery 結果を D234 の
  単一 `PreregBinding` へ束ねる入力写像
- 完成条件を「consumer」一語にせず、producer / resolver / validator / selector /
  材料 report / 試行台帳 sink を層ごとに列挙する

## 状態

**pilot / 本走は依然として投入不可である。**
D292 の `pilot_submission = forbidden` / `main_submission = forbidden` は 1 bit も動いていない。
D264 の 4 名非 export も維持されている (`test_module_exports_no_admission_api` が生きている)。
本 wave は解除 decision も投入経路も land しないため、窓は開いていない。

## 本 wave が land したもの / しなかったもの

**land した:** 本裁定パッケージ、段 1〜4 の逐語、worklog fragment、
scope 外所見 (`s1-startup-gate-deadlock.md`)。**実装面差分はゼロ。**

**land しなかった:** canonical decision 本文 (decisions fragment)。

## 追記 (2026-08-20、後続 wave `dev-wave-t139-q1-canonical-decision-land`)

上記 V1〜V5 は 2026-08-13 /rulings 第9回#8 (K1〜K4) + 第10回#1 (V1〜V5) で全問 (a) 裁定された
(`/work/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-rulings{9-29,10-15}rulings.md`)。
本 wave はこの裁定どおりに canonical decision 本文を起草し、`docs/decisions.md` へ land する
fragment を `docs/spool/decisions/2026-08-20-dev-wave-t139-q1-canonical-decision-land-1.md`
(placeholder `{{D:t139-q1-canonical-predicate}}`、fold 時に実 D 番号確定) として書いた
(段2 codex plan 起草 + 段3 敵対相談2レンズで fact-check・scope 整合性を検証、real 所見は非拘束の
付録のみで fragment 本体は無修正)。**land 後にこの段落を実 D 番号へ amend すること
(fold 前は forward reference を確定値として書かない)。**

**B1〜B4 の状態:** 本 decision が閉じたのは B1 (V3。§7.1(12)/§8 の矛盾を raw `CMakeCache.txt`
独立再 parse で解消) と B4 (V2。追補 A `a10`/`a11` への参照束縛)。**B2
(`series_id`/sealed set/`receipt-set.json`、本文 211 行) は投入経路 wave (K2) へ委譲されたまま
未着手。** B3 は本 package 内に個別定義が無い。

**pilot / 本走は依然として投入不可である。** D292 の解除は本 wave の対象外であり 1 bit も
動いていない。次の一手は `output/insights/2026-08-13_t139-land2-q4/package.md` の K2/K3 に従う
投入経路 wave (manifest+resolver+writer+validator+vectors の実装)。
