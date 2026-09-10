# 段 4 裁定 — [T-139] land 2 / Q4 組み替え scope

wave `dev-wave-t139-land2-q4` / branch `worktree-dev-wave-t139-land2-q4`、base = local main `adf7997f`。
裁定日時 = 2026-08-13 02:0x JST。

## 0. 判定

**Q4 scope を本 wave で実装しない。実装面差分ゼロ。**

段 2 のプラン起草と段 3 の敵対 2 レンズが**独立に NO-GO** を返した。親はこれを支持し、
`DW-S04` の定めどおり親が不採用にせず、**裁定時点で未見だった事実 4 件 (N1〜N4) を添えて
ユーザー再裁定へ戻す**。

先行 wave (worklog archive エントリ 470) が同じ Q4 scope で NO-GO を返したときの閂 2 件は、
本 wave の実測では**いずれも解消している**。本 wave の NO-GO はそれとは**別の根**による。

| エントリ 470 の閂 | 本 wave の実測 |
|---|---|
| (i) `a12` が実装・実走 0 件 | **解消**。R1 (a) の裁定に従い独立 wave が完走 (2026-08-12、job `907407.nqsv`)。pass artifact は tracked |
| (ii) `a09` serialization が §10 未承認閉包 4 | **解消**。R2 (a) が「canonical を名乗らず `operational-only` とする」で回避経路を確定。段 3 レンズ B も「計画文面上の R2 (a) 違反は確認していない」と追認 |

## 1. 未見の新事実 (N1〜N4)

### N1 — 承認済み契約が `PreregBinding` を必須引数にしている (最も硬い閂)

**D234** (`docs/decisions.md:10960` 以降) が固定する契約は次である。

```text
submit_pilot(*, binding: PreregBinding) -> submission_id
```

同 decision は「`submit_pilot` は、次をすべて満たす `binding` が
`resolve_effective_preregistration` から返っていない限り**実行してはならない**」と書き、
(i)〜(vii) の 7 条件を課す。

**`PreregBinding` と `resolve_effective_preregistration` は pilot 投入前提 #6 そのものであり、
Q1 / Q2 の下流として本 wave の scope 外である。**
したがって**契約どおりの `submit_pilot` は本 wave では書けない**。
段 2 が提案した `submit_pilot(*, submission_id: str)` は D234 と別物であり、
段 3 レンズ B が [B-01] で blocker と判定した。

これは「恒真かどうか」以前の問題である。承認済み API 契約の必須引数が存在しない。

### N2 — R1 (a) の裁定理由が実測で反証された

裁定パッケージ land2-s4 の R1 (a) は理由欄に
「完走すれば正例が構成可能になり、**R3 の恒真問題が自然に解消する**」と書いた。
ユーザーはこの理由込みで R1 (a) を裁定した。

**実測はこれを反証する。** `a12` は完走したが、その成果物自身が
`claim_scope.pilot_ready = false` / `remaining_unmet_pilot_prerequisites = [1,4,5,6,7,8,9]` を
宣言している (`output/env/pegasus/t139-a12-stress-check/full-v1/stress-check-simulation.json`)。
`a12` の完走が満たすのは前提 **#3 だけ**であり、#4〜#6 (受領証 schema の digest 束縛 /
approval manifest / resolver + `PreregBinding` + receipt writer) は未実装のまま残る。

**したがって `submit_pilot` の最終受理集合は依然として空であり、R3 の恒真問題は解消していない。**
段 2・段 3 レンズ A がともに独立にここへ到達した。レンズ A は
「現 scope 内でこの区別不能性を消す設計は無い」と断言した。

具体的には、次の 2 実装が**観測上区別できないまま残る**。

- 正しい staged gate (#1〜#3・#8・#9 を再導出し、#4〜#6 で block する)
- 所有層の診断だけ計算し、binding を一度も検査せず最後に定数 deny を追加する実装

### N3 — 第 7 束 (2026-08-13) が第 2 束 (2026-08-12) の Q1 / Q2 を後発上書きしている

同じ T-139 Q1 / Q2 に対し、**選択肢集合が同一で結論が正反対の裁定が 2 つ**存在する。

| 束 | 日時 | Q1 | Q2 |
|---|---|---|---|
| 第 2 束 (`2026-08-12-second-batch-11rulings.md`) | 2026-08-12 12:38 | **機構を新設しない** (受理述語の入力欠落 4 件を閉じる canonical decision は起こさない) | **機構を新設しない** (namespaced projection 等の新表現は作らない) |
| 第 7 束 (`2026-08-13-rulings8-batch.md`) | 2026-08-13 00:41 | **(a) canonical decision 1 本** | **(a) 固定 envelope + namespaced projection** |

第 7 束は第 2 束が却下した当の機構を選んでいる。段 3 レンズ A は [A-11] で
**「scope 裁定としては第 7 束が後発であり、第 2 束を上書きしたと判定する」**とした。

この読みを採ると、**#4〜#6 は「実装禁止」から「Q1 の canonical decision 後に実装」へ動く**。
すなわち正しい実行順は次になり、**Q4 の「1 session」編成はそもそも成立しない**。

```text
Q1 の canonical decision (ユーザー裁定 → fold)
  → #4〜#6 の実装 wave (manifest + resolver + PreregBinding + receipt writer)
    → 投入経路 wave (submit_pilot + PBS driver + collector + 解除 decision + 束縛検査)
```

**ただしユーザー指示自身が両方を併記している** — Q1/Q2 を (a) と書きつつ
「D320 により承認機構は新設しない」とも書く。**親はこの矛盾を一存で解けない。** K1 として返す。

### N4 — R5 の起票前提が事実として誤っている

R5 は `orchestrator/qualification/submission.py:150` の `_durable_json` を
「単発 `os.write` で short-write 検査も read-back も持たない」とした。

**親の実測 (`:143-164`) では、現物は short-write ループ + `os.fsync(fd)` + 親 directory の
`os.fsync` を既に持つ。** 欠けているのは read-back 検証だけである。
R5 は「(a) 別タスク起票」で裁定済みだが、**起票内容の前提が崩れている**。

## 2. 所見の real / refuted 裁定

段 2 + 段 3 の 2 レンズが挙げた所見を裁定する。**scope 外の real 所見は実装しない** (`DW-S04`)。

| ID | 所見 | 裁定 | 扱い |
|---|---|---|---|
| 段 2 §(B) 骨子 1 | R3 が縛るのは admission の受理集合 `A` であって所有層の補助観測 `O` ではない | **real** | 採用。判定の中核 |
| 段 2 §(B) 骨子 2 | 「常時 deny」実装と正しい gate が区別できない | **real** | 採用 (レンズ A [A-02] が独立に追認) |
| 段 2 §(B) 骨子 3 | durable intent は「認可成功後・qsub 前」に書く | **一部 refuted** | レンズ A [A-04] / レンズ B [B-09] が独立に「承認済み逐語は `intent < qsub` までで、認可との前後は設計解釈」と実測。**ただし deny 前に intent を書くと §4.13 の exact 被覆と `qsub_result` 契約に収まらず孤児化する、という結論自体は real** |
| 段 2 §(B) 骨子 4 | fixture の解除 decision は parser の正例であって D292 の authority 正例ではない | **real** | 採用。親の (P1b) を撤回する |
| 段 2 §(B) 骨子 5 | D264 が空実装・恒真 deny stub を明示却下 | **real** | 採用 |
| [A-05] | D264 のテスト期待値を先に緩めるのは規律 2 違反 | **real / blocker** | 採用。**実 binding 正例が通るまで `submit_pilot` の export も既存期待値も変えない** |
| [A-06] | D308 は pilot 解除の直接根拠ではない (床値 build の compiler site 依存化に限定) | **real** | 採用。**親 brief §2 / §5 の D308 引用は誤り。同一 land 義務の根拠は Q4 裁定そのものである** |
| [A-11] | 第 7 束が第 2 束を後発上書き。現 brief の scope は stale | **real / blocker** | 採用。ただし**上書きの成否はユーザー裁定事項**として K1 で返す (レンズ A は「追加裁定不要」としたが、ユーザー指示が両論併記のため親は同意しない) |
| [A-12] / [B-06] | 代案 2 (scope 縮小) は D264 上安全だが発火しない | **real** | 採用。`DW-G04` により**設計メモに留める**。実装しない |
| [B-01] | 計画の `submit_pilot` 署名が D234 の承認済み契約と別物 | **real / blocker** | 採用。N1 の根拠 |
| [B-02] | `DW-G04` の production caller が存在しない | **real** | 採用 |
| [B-03] | #4〜#6 の前段拒否が後段変異を先取りする | **real** | 採用。変異の帰属が成立しない |
| [B-04] | `a12` の pass を pilot readiness へ一般化できない | **real** | 採用。親 brief は §3.1 で既に「#3 だけを満たす」と書いており、**過大主張はしていない**が、記述をより明示的にする |
| [B-05] | 親の一次資料 2 本 (precheck handoff と a12 artifact) で #3 の状態が矛盾 | **real** | 採用。**precheck handoff の #3 行は superseded である**と本裁定で明記する |
| [B-07] | `a09` の seed / byte 規約が実装可能な粒度で固定されていない (計画側の省略) | **real** | 実装しないため本 wave では不発火。**次 wave の必須要件へ送る** |
| [B-08] | operational JSON の transport contract が未固定 | **real** | 同上 |
| [B-10] [B-11] [B-13] [B-14] | `FileRecord` 共有 API 不在 / 注入境界不足 / 所有が素集合でない / 既存資産との重複 | **real** | 同上 (次 wave の必須要件) |
| [B-12] | Pegasus 既存固定テストへの波及を落としている | **real** | 同上 |
| [B-15] | `admission_registry.json:160` は既存 a12 entry で新規挿入箇所ではない | **real / nit** | 同上。**行番号を実装契約にしない** |
| [A-08] 系 | safe-history 漏れによる authority bypass | **real** | 次 wave の必須要件 |
| [A-01] [A-03] | 最終受理集合が空 / 発火しない保証が 6 件残る | **real / blocker** | 採用。判定の中核 |

**反証できた親の主張 (レンズが確認)**: D292 が禁じる権威経路 (spool fragment・handoff・環境変数・
caller 供給 root・wave 自己申告) の混入は無い。§8 否定検査の申告値を admission 入力にする設計も無い。
D282 / D291 の承認 bytes を編集する経路も無い。`skip` / `xfail` や production fail-open の提案も無い。
親 brief の M1〜M5・M7・M9 は一次資料と一致した。

## 3. 親 brief の訂正 (本裁定が正本)

1. **(P1) を撤回。** 「層を分ける / 所有 6 前提で正例を構成 / `authorized` を名乗らない」の 3 点セットは
   R3 (a) に適合しない。R3 が縛るのは最終 admission の受理集合であり、所有層の観測を非空にしても
   受理集合は空のままである。
2. **(P1b) を撤回。** テスト fixture の解除 decision は parser の正例であって、
   D292 が要求する「canonical 台帳へ fold された decision」の正例ではない。
3. **D308 の引用を撤回。** D308 の決定本文は床値 build の compiler site 依存化と toolchain 束縛検査に
   限定されており、pilot 解除の同一 land 義務の直接根拠ではない。根拠は Q4 裁定の逐語である。
4. **§3.1 の「scope 外」分類に注記を付ける。** 第 7 束を後発有効と読むなら、#4〜#6 は
   「実装禁止」ではなく「Q1 decision 後に実装」である。
5. **precheck handoff の #3 行は superseded。** 同 handoff は `a12` を「実装も実行結果も 0 件」と
   記録するが、これは a12 wave 完走前の実測である。現況の正本は tracked artifact である。

## 4. 変異事前登録 (`DW-M01`)

**変異 matrix を免除する。** 根拠は **D301** の連言 —
「実装しない」裁定済み **かつ** 実装面差分ゼロ。本 wave は両方を満たす。

**受入全走は免除しない** (D301 が明示)。記録 commit を含む最終 tip で実走する。

なお段 3 レンズ B [B-03] が「#4〜#6 の前段拒否が後段変異を先取りする」と実測しており、
**仮に実装していたとしても変異の単一理由帰属は成立しなかった** (`DW-M01` の登録要件を満たさない)。
これは免除の理由ではなく、Q4 scope が現時点で実装不能であることの独立した傍証である。

## 5. 段 5・6 を飛ばす

`DW-S04` の定めにより、「実装しない」と裁定した本 wave は `4→7→8→9` とする。
