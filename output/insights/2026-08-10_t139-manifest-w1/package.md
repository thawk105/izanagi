# [T-139] 第 1 波 — ユーザー裁定パッケージ (2026-08-10)

wave `dev-wave-t139-manifest-w1`。段 3 の敵対レンズ 2 本 (`gpt-5.6-sol` / `gpt-5.6-luna`) が
ともに NO-GO を返し、親が全 19 所見を real と裁定した結果、
**依頼された (i)〜(v) のうち 4 つは本 wave では実装できない**という結論になった。
その理由と、判断を要する 5 問を返す。

---

## R1. Q-D の「同一 land」は manifest の構造要件と両立しない ★最重要

### 事実

1. Q-A は「record-items へ**承認済み修正**として入れる」を求める。
2. 現行 record-items (`1957026c…8fd3`) は **D262 が承認済み blob として digest 固定している**。
3. **`F_e` (= D262 を fold した commit `dce4ae4f…`) より後に生まれた blob を、`F_e` が
   承認することはできない。** 承認済み manifest は canonical decision を上書きする権限を持たない。
4. したがって再発行版 record-items と受領証 schema を manifest へ pin するには、
   **それらを承認する新しい decision を先に台帳へ fold** しなければならない (これを `F_r` と呼ぶ)。
5. **manifest は自分自身が fold される commit の SHA を literal で持てない** — D262 自身が
   この理由で「payload を先に fold し、manifest をその子孫に置く」二段構成を採った。
6. よって必要な fold は最低 **2 回**である: `F_r` (新 blob の承認) → manifest。
   fold は land lock 内でしか起きないので、**fold 2 回 = land 2 回**である。

### 帰結

Q-D の「manifest + 受領証 + 投入・測定を**同一 land**」は、この構造と両立しない。
第 1 波を land しない限り `F_r` が生まれず、`F_r` が無い限り manifest は書けない。

### 選択肢

- **(a) 承認 fold だけを先に land する 2 段 land を認める (親の推奨)。**
  land 1 = 新 blob の承認 decision + 再発行 record-items + schema blob + 第 2 erratum
  (**コードは含めない。受理仕様の凍結でもない** — 承認された「要件文書」が台帳に載るだけで、
  それを読む resolver も gate も存在しない)。
  land 2 = manifest + producer 本体 + 投入・測定。
  Q-D が禁じた「受理仕様のみの先行凍結」は **schema の digest を `PreregBinding` に固定して
  gate を動かすこと**を指すと読み、文書承認の fold はそれに当たらないと解する。
- (b) Q-D を字義どおり守り、manifest を**永久に諦める**。
  → 承認済み erratum §5 が「manifest が存在しない状態で本 erratum を適用してはならない」と
  課しているので、**pilot は永久に投入できない。**
- (c) 再発行をやめ、現行 record-items のまま Q-A の第三分岐を**実装側の解釈で入れる**。
  → 承認済み文書と実装が食い違う。前 wave の Q-A (N5) がまさにその食い違いで、
  それを解消するための裁定だったので、元の問題へ戻る。
- (d) 新しい core を起こして study を作り直す。→ 最も保守的だが事前登録のやり直しを伴う。

**親の推奨は (a)。** ただし Q-D の再解釈にあたるので親が決めてよい範囲を超える。

---

## R2. Q-A 第三分岐が開ける捏造余地を、承認時に引き受けるか

裁定どおり第三分岐を実装した (再発行版 §3.1 経路 3)。恒真化を避けるため
「raw から失敗が導けること」を含む 6 条件で拘束した。それでも次が残る。

**producer は preflight の観測窓で意図的に malformed な raw (7 列の `cpu` 行・負差分・窓長逸脱) を
書けば、marker も性能 run も持たない attempt を正当な `post_performance_failure` として
記録できる。**その raw が実際のカーネル出力かは producer 権限内では判別できない。

段 6 のレビュー A が具体的な構成を示した。**6 条件をすべて満たしながら、実際には性能 run を
実行済みの attempt を作れる。**

```text
1. scope = preflight の observation を 1 件置く
2. producer が作った 7 列の偽 /proc/stat bytes を stat_before_raw / stat_after_raw に pin する
3. validator は short_columns を raw から再計算できる (条件 3 成立)
4. monotonic 時刻を単調かつ 10 秒窓にする              (条件 4 成立)
5. malformed_reason_or_null = short_columns とする      (条件 5 成立)
6. marker を null にし、actual_runs[] から当該 attempt 参照を削除する (条件 6 成立)
```

**実 run の存在とは独立に全条件が成立する。**すなわち第三分岐は
「`a03` が不成立だった」ことは示せても「**性能 run を実行しなかった**」ことは示せない。
条件を足して閉じられる種類の穴ではない — producer 権限内の証拠だけでは原理的に閉じない。

- certified 値を直接上げることは**できない** (固定 `J` の完全性 gate が別に効く)。
- しかし **試行台帳の「この試行は実行されなかった」という事実が偽造可能**になり、
  不利な実 run を `design_not_feasible` へ隠せる。

選択肢: **(a) 残余として引き受け、非保証として明記したまま進む (親の推奨。既に §6 へ明記済み)** /
(b) producer 権限外の collector が raw を独立採取する層を先に作る (投入・測定層と同じ規模) /
(c) 第三分岐を marker 必須へ戻す (= preflight 失敗を記録できない状態へ戻る)。

---

## R3. `a13` 予約台帳の保証境界と、`b03` による 2 本目の台帳

### R3-1. land lock は canonical 台帳を作らない

land lock は **Git common dir 内の `flock`** である (`dev_wave_land.py`)。防げるのは
同じ common dir を共有する linked worktree・`dev_wave_land` を通る writer・同じ local main 上の
競合だけで、**独立 clone の別 common dir、`dev_wave_land` を通らない直接 commit、
過去予約行の削除後の再利用は防げない。**

追補 A `a13` は「producer が選べない canonical な台帳で原子的に」を要求する。
Q-C の方向 (land lock 直列化による main 台帳) がこれを満たすのは
**「指定された 1 つの canonical main と、その trusted consumer だけが権威」という運用境界を
機械的に束縛したとき**に限る。

選択肢: **(a) 運用境界を manifest / report / resolver の全てで同一 wording に固定し、
append-only 全履歴検査を課したうえで採る (親の推奨)** /
(b) remote ref または共有 CAS を権威にする (新しい基盤が要る) /
(c) 台帳を諦める → 同じ根に対し複数 study が `k=1` を主張でき、
全体誤り率が `1 − (1 − 0.025)³ ≈ 0.0731 > 0.05` になる。

### R3-2. 追補 B `b03` が台帳を 2 本にした (段 1 の後に land した新事実)

`b03` は **primary 台帳とは別の「個別公表系列の累積台帳」**を要求する
(根は同じ `F` だが `ledger_kind: individual_publication`、残高・entry・ordinal を混合しない)。
同時に `b03` は「**core §12 の必須記録項目を増やさず、validator の受理条件を追加しない**」と課す。

→ 本書 §4.5 では公表台帳の予約を**受領証の必須記録から外した** (入れると core の変更になる)。
その結果、公表台帳の一意性は**投入前 admission 側の検査**だけが担う。
この非対称 (primary は受領証に記録・公表側は記録しない) を承認するかを問う。

> **本 wave の受入直前に land した追加裁定を反映 (2026-08-10)。** 追補 B は
> **段階 1 (草案、`authority: none`) に留め置かれ** (B8 (a) 承認保留)、公表の検定手続きの正本は
> **新しい core を起こす別 study** で凍結してから追補一式を再提出することになった。
> よって `b03` の値は再提出の出発点であり、**R3-2 の問いは新 core 側で公表台帳の記録要件が
> 定まった時点で再評価する**のが正しい順序になる。
> 同裁定は「Q-A〜Q-E の裁定は不変」「producer 実装 = manifest wave と pilot 準備は独立に進む」と
> 明記しているため、**R1・R2・R4・R5 と本 wave の成果物は影響を受けない。**

---

## R4. gate が効くために必要な未実装層 (名指しで返す)

`verify_receipt` が `accepted` を返しても、次が無ければ certified 選択・レポート・
試行台帳の値は 1 つも変わらない。すなわち「gate が効いた」と記録できない。

- `submit_pilot` と durable submission intent
- PBS preflight・実 driver・collector
- `PreregBinding` を必須にする receipt writer
- **iteration 毎の correctness verifier** (絶対規律 3。前 wave が撤回した (P1) の訂正先)
- certified 適格性判定・選択・材料レポート・試行台帳の consumer

これらを次 wave 群のどこへ置くかは R1 の裁定に従属する。

---

## R5. `verify_receipt` は既に別概念で実在する (同名衝突)

`orchestrator/campaign/t080_freeze_migration.py:1956` に `verify_receipt` が実在し、
`s8b_oracle_driver.py` と `s8b_floor_campaign.py` が consumer になっている。
これは s8b freeze receipt の検証であり、T-139 の受領証とは**別概念**である。

`DW-O13` / D75 は同名識別子の二義化を禁じる。選択肢:
**(a) T-139 側を別名にする (例 `verify_prereg_receipt`。親の推奨)** /
(b) namespace を明示分離して同名を許す /
(c) s8b 側を改名する (既存 consumer に波及)。

なお承認済み erratum §5 は `verify_receipt` という**名前を逐語で指定している**ため、
(a) を採る場合は「erratum が指す機能と実装名の対応」を manifest 側へ明記する必要がある。

---

## 付録: 本 wave が実際に land 候補として作ったもの

| 成果物 | 状態 |
|---|---|
| `record-items-reissue.md` | Q-A 第三分岐 + 未閉包 nested object の exact-key 閉包 + 非保証の明記。**未承認** |
| `erratum-core-s7-stresscheck.md` | core §7 の較正義務 → 事前固定 stress check。1 operation (221 行)。**未承認** |
| D263 の事実文を supersede する decision fragment | erratum の状態を `validator_registered` / `draft_unapproved` / `approved` の三値へ |
| 第 2 erratum の機械化 (registry + `DRAFT_ERRATA`) | 「登録済み ≠ 承認済み」を型と検査で分離 |

**承認 manifest・受領証 JSON Schema・予約台帳・producer 本体は作っていない** (R1 の裁定待ち)。
**pilot は投入不可のままである** — これは本 wave の作為ではなく、T-139 の投入 API が
1 つも実装されておらず D264 の非 export 検査が機械固定していることによる。
