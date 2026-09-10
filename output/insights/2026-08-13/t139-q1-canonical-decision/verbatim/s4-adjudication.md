# 段 4 裁定 — dev-wave-t139-q1-canonical-decision

```text
裁定者: 親 (dev-wave manager)
日時: 2026-08-13 08:1x JST
入力: s2-plan.md (25,182 B) / s3-lensA.md (12,542 B) / s3-lensB.md (9,634 B)
      + 親が段 1 で実測した s1-brief-appendix-pins.md / s1-brief-appendix-b1b4.md
```

## 裁定 — **実装しない (canonical decision 本文を land しない)。実装差分ゼロで裁定へ返す。**

`DW-S04` の「実装しない」裁定であり、段 5・6 を飛ばして `4→7→8→9` へ進む。
**land するもの:** 裁定パッケージ、段 1〜4 の逐語、worklog fragment、scope 外所見。
**land しないもの:** decisions fragment (canonical decision 本文)。

段 2 と段 3 の 2 レンズ (`sol` / `luna`) が**独立に NO-GO** を返し、親が段 4 で追認した。
親は 3 子の主張のうち決定打 4 件を一次資料で自ら再検査し、いずれも成立することを確認した。

## なぜ止めたか — 一次資料で裏取りした blocker 4 件

### K-1. 起草した B4 契約が、承認済み追補 A の数値契約を書き換えていた

プランは transcript の数値結果を `2^-80` 格子の dyadic 区間、端点を `{numerator, exponent2}` と
固定した (`s2-plan.md:133-135`)。**承認済み追補 A はこれと異なる契約を既に固定している。**

```text
output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:724-748 (親が直接読んだ逐語)
  各 p_k(J) は認証区間 [p_k^L, p_k^U] として評価する
  (非心 t の CDF を、外向き丸めの区間演算で p_k^L ≤ 真値 ≤ p_k^U かつ
   p_k^U − p_k^L ≤ 1e-9 となるまで評価する)
  L_J^cert = max(0, 1 − Σ p_k^U) / U_J^cert = max(0, 1 − Σ p_k^L)
  J = min { j ∈ {4,…,13} : L_j^cert ≥ 0.80 }
  [L_j^cert, U_j^cert] が 0.80 を跨ぐ候補が 1 つでもあれば design_not_feasible
```

**成果物影響:** `2^-80` 格子を canonical に書けば `J`、`design_not_feasible` の発火点、
main の `consumed_cluster_slots` 要素数、conformance vector の期待値がすべて動く。
**これは受理集合を変える変更であり、絶対規律 2 が禁じる方向である。**

**手当ての方向 (次 wave へ):** decision は数値契約を**書き直さず**、
追補 A `a10`/`a11` の定義を三つ組で参照して束縛するだけにする。B4 が閉じるべきは
「transcript の canonical byte grammar と authority binding」であって数値契約ではない。

### K-2. B1 の起草が §8 の禁止を「単独では使わない」へ弱めていた

プラン決定 (1) は「`cmake_cache`、`trace_enabled`、`analysis_enabled` は引き続き申告値であり、
**単独では**受理入力にしない」と書いた (`s2-plan.md:66`)。
承認済み §8 の逐語は「消費側が次のいずれかを**受理条件の入力**に使ったら落ちるテストを置く」であり、
単独か併用かを区別していない (`record-items-v2.md:784-799`)。

**成果物影響:** 「単独では」を canonical に書くと、最弱実装は申告値を他入力と併用して受理判定に
使え、別実装は完全に無視する。同じ受領証の受理・拒否が engine ごとに分岐し、
§7 の「engine の差で受理集合が変わってはならない」に直接抵触する。

**手当ての方向:** 申告値は**常に**受理入力から外し、raw `CMakeCache.txt` の再 parse 結果だけを
3 者目の入力にする。申告値との一致は「拒否条件」としてのみ使う (一致しなければ拒否、
一致しても受理の根拠にしない)。これなら弱化なしに B1 を閉じられる。

### K-3. 起草が実在しない field 名で契約を書いていた

プラン決定 (1) は `correctnessCompile` にも `configure_argv` がある前提で書いている
(`s2-plan.md:64-66`)。**実測:**

```text
correctnessCompile.required =
  ['identity_sha256', 'argv', 'trace_enabled', 'analysis_enabled', 'cmake_cache', 'compile_commands']
```

field 名は `argv` である。**直前 wave の K4 (R5 の起票内容が現物と食い違っていた) と同型の事故が、
同じ T-139 系列で独立に 2 度目である。**

### K-4. approval manifest 自身の authority が循環している

`approval_manifest` は承認済み schema の**必須 field** であり、型は `blobRef` である
(`receipt-schema-v1.json` の `preregistration.required` に含まれる。親が直接確認)。
一方、その manifest の bytes を承認する role は **D282 の 6 role にも D291 の 2 role にも無い**。
`conformance_vectors` の期待 digest も manifest 自身にしか pin されない
(`s2-plan.md:192-214` の root mapping に `conformance_vectors` が無い)。

**成果物影響:** manifest と弱い vector index を同時に差し替えれば自己整合し、
必要な負例を欠く validator が「conformance 済み」として certified 経路へ入る。

**手当ての方向:** 有効な approval payload 側に conformance-vector index の三つ組を置き、
manifest の外に trust edge を作る。ただしこれは K-5 (D320) の答えに依存する。

## K-5. 止めた最大の理由 — D320 の例外範囲がユーザー未裁定である

**2 レンズが独立にここへ到達した** (`A-6-1` / `B-1-3`)。親の段 1 暫定裁定 (P2) は**誤りだった。**

**時系列 (実測):**

| 時刻 (JST) | 出来事 |
|---|---|
| 2026-08-12 | D320 が land。bytes 級 provenance 機構の新設・維持を既定で見送り |
| 2026-08-13 00:0x〜00:1x | **第 7 束**。T-139 Q1〜Q6 を「推奨どおり」で全問確定。**D320 も K1 も名指ししていない** |
| 2026-08-13 02:0x | land2-q4 wave が **K1 を起票** (D320 と Q1/Q2 (a) の衝突)。ユーザー未回答 |
| 2026-08-13 07:2x〜08:1x | 本 wave。起草して初めて、衝突が回避不能であることが判明 |

**K1 はユーザー裁定より後に起票されており、一度もユーザーへ問われていない。**

**親の (P2) は 2 層に分けると、片方が成立し片方が成立しない。**

- **成立する側:** approval manifest **そのもの**は新設物ではない。D320 の前日に D282 が exact bytes
  承認した schema の**必須 field** であり、§7 と §7.1(19) が 2 箇所で明示的に要求している。
  D320 は既承認 artifact の必須 field を遡って削除する文言を持たない。
- **成立しない側:** B1 を閉じるには `record_items` / `receipt_schema` role を supersede する
  **新しい exact-byte approval payload** が要る。これは D320 が列挙する「commit への束縛」
  「承認への署名」そのものである。`conformance_vectors` の digest pin も同様である。

**そして回避経路が無いことが、本 wave の起草で初めて実証された。**

- 新 payload を作らずに B1 を閉じる案は 2 つしかない。
  (a) validator を常時拒否にする → 受理集合が空。R3 (a) が禁じた当のもの。
  (b) §7.1(12) の CMakeCache leg を落とす → **受理述語の弱化。絶対規律 2 違反。**
- したがって **D320 の例外範囲を決めない限り、Q1 は原理的に閉じられない。**

**これは `DW-S04` の「承認済み裁定を裁定時の未見事実で止める」に該当する。**
親は Q1/Q2 (a) を不採用にしない。新事実を添えてユーザー再裁定へ戻す。

## 親が採用した所見 (fix 方向つき)

| ID | レンズ | 判定 | 扱い |
|---|---|---|---|
| B-1-1 | B | **real / blocker** | K-1。次 wave は数値契約を書かず追補 A を参照束縛する |
| A-2-1 | A | **real / blocker** | K-2。申告値は常に受理入力外、raw 再 parse だけを入力にする |
| B-2-1 | B | real | K-3。`argv` が正。field 名は実 schema から取る |
| B-3-1 / A-3-1 | B / A | **real / blocker** | K-4。vector index の trust edge を manifest 外へ |
| A-6-1 / B-1-3 | A / B | **real / blocker** | K-5。ユーザー裁定へ返す |
| A-1-1 | A | real | D234 (iii) の祖先 root は D234 の fold commit へ literal 固定する |
| A-5-1 | A | real | decision の題を単独引用しても gate 完成と読めない形にする |
| A-2-2 | A | real / scope 外 | `series_id` の authority は投入経路 wave の設計事項 |
| A-4-1 | A | real / scope 外 | create-only の検証可能性 (履歴性まで要るか) は裁定事項 |
| A-2-3 / B-3-3 | A / B | real / scope 外 | B4 の完全 grammar と binding 入力写像は別成果物 |
| A-7-1 | A | real | 完成条件を「consumer」一語にせず層ごとに列挙する |
| B-4-1 | B | real / 本 wave 内 | slug drift。**decisions fragment を land しないので消える** |
| B-5-1 | B | real | Q2 が B1 に人質を取られる構造。裁定パッケージの問いへ含める |
| B-7-1 | B | real | 前提 #4〜#6 を独立 gate として列挙する |

## 親が refuted と裁定したもの

- **「Q1/Q2 を取り違えている」** — refuted。レンズ B が独立に照合し、
  親の F31 適用 (本文優先で Q1 = 受理述語 4 件、Q2 = envelope) が正しいことを確認した。
- **「既存承認 blob を in-place 書換えする案になっている」** — refuted (レンズ A)。
  プランは新版 + supersession を要求しており、既存 bytes を変えない。
- **「D292 を暗黙解除している」** — refuted (レンズ A)。本文は解除を明示的に却下している。
  ただし題の曖昧性は A-5-1 として残る。
- **「`submission.py` に short-write 検査と fsync が無い」** — refuted (レンズ B + 親の実測)。
  `orchestrator/qualification/submission.py:143-164` に `O_EXCL` + `O_NOFOLLOW` +
  書込みループ + file `fsync` + directory `fsync` が実在する。欠けるのは read-back だけ。
- **「D305 が単一 role 公開 API を要求している」** — refuted (レンズ B)。
  `approval_d291.py` は exact 2 role の batch resolve であり、Q2 (a) の内部固定写像と整合する。

## 変異事前登録 (`DW-M01`)

**実装差分ゼロのため変異 matrix を免除する** (`DW-S04` の明文)。**受入全走は免除しない。**

## 本 wave が前進させたもの (前回 wave との差)

前回 (land2-q4) の NO-GO は「**どちらの裁定が有効か**」という手続の問いだった。
本 wave は**実際に起草して独立に攻撃させた**ため、返す問いが具体になった。

- D320 の例外範囲を、`F_r*` / manifest fold root / vector digest pin の **3 対象ごと**に問える。
- 「回避経路が無い」ことが実証された (常時拒否 = 空受理集合、leg 削除 = 規律 2 違反)。
- 起草が踏んだ落とし穴 4 件 (数値契約の上書き、§8 の弱化、実在しない field 名、
  manifest の authority 循環) が、次 wave の brief にそのまま入る。
