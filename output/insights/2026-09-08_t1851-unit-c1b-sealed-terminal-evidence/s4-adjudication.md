# [T-1851] C1b やり直し — 段 4 裁定

base `8193eefdb` (継承 tip `89605bb39` + local main `645d0d663` の merge)。
branch `worktree-dev-wave-t1851-unit-a`。**land しない (D1341)。**
段 2 plan (`verbatim/s2-plan.md`)、段 3 レンズ A (`verbatim/s3-lensA.md`) / B (`verbatim/s3-lensB.md`)、
親の裏取りを突き合わせて裁定する。

## 0. 裁定 (DW-S04)

**本 wave は実装しない。段 5・6 を飛ばし `4 → 7 → 8 → 9` とする。**
**成果物は契約 v3.1 (`contract-v3.1.md`) と、そのまま段 5 へ入れる plan v2 (`plan-v2.md`) である。**

理由は 3 つある。順に重い。

### (1) 段 3 の 2 レンズが独立に「この plan では契約 v3 を実体化できない」と判定した

段 2 plan は「1 wave に収める」と自己判定したが、レンズ A も レンズ B も判定は **no** である。
前 wave も 3 者一致の no で実装を止めており、同じ形の一致がここでも出た。

### (2) 所見のうち 3 件は plan ではなく**契約そのもの**を変える

親が現物で裏取りした。plan だけを直しても契約が誤ったままになる。

| # | 内容 | 親の裏取り |
|---|---|---|
| A-01 | 証拠の identity 群を「reservation と全件等値」で束縛する条項が、**呼び手が選べる値を権威に据えている** | durable claim (`s8b_holdout_admission.py:1703-1728`) が持つのは `cell_id` `records` `threads` `workload` `campaign_run_id` `run_relpath` `mode` `attempt_ids` だけ。`seq` `round` `kind` `trigger` `event` には durable な権威が**無い**。契約 1.5 の「identity 13 field を全件等値」は成立しない |
| A-02 | E1 の正本を「campaign の実 semantics」と書いたが、**launcher の受理集合のほうが広い** | launcher は `(RuntimeError, TimeoutExpired, OSError)` を捕捉 (`s8b_floor_attempt_launcher.py:777`)。campaign は `(RuntimeError, TimeoutExpired)` だけ (`s8b_floor_campaign.py:6264`)。`OSError` は launcher では terminal になるが campaign では session 行が生まれない |
| B-07 | 契約 9 節と probe P-7 の「pin 追加不要」が **semantic inventory を閉じていない** | `test_official_perf_closure.py:44` の `_REVIEWED_PERF_FILES` は exact frozenset で、`:531` の `_production_perf_files()` が production を AST 走査し `:903` が集合等値を assert する。新 leaf に perf 述語の分岐を置くと `unreviewed:` で落ちる |

**A-01 は本 wave で最も価値のある所見である。** 契約 v3 は `exec_failures` について
「等値束縛だけで、rep ごとの実行成否は証明しない」と正しく射程を切ったのに、identity 群では
同じ切り方をしていなかった。v3.1 で権威のある群と無い群に分け、後者は
**digest でのみ束縛し、権威であるとは主張しない**形に直す (規律 3)。

### (3) レンズ B が規模超過を具体で示した

plan は unit 1 の leaf を `new:1-850` と自分で宣言しながら、見積り表では `+500〜700` と書いている。
それだけで上限を約 150 行超える。さらに B-03 の draft→validated ABI、B-04 の transition callback
10 本、B-07 の semantic pin 補修が見積り外である。レンズ B の再見積りは
production 1,580〜2,120 / test 1,900〜2,850 で、裁定済みの上限 (1,000〜1,600 / 1,500〜2,400) を超える。

ユーザーは「収まらないなら切る判断は次の親に任せる。ただし中途半端な分割は却下済みで、
切るなら契約の文書だけまで戻る」と事前に定めている。**中途半端な分割はしない。**

## 1. 所見の裁定表

### レンズ A (正しさ境界)

| # | 判定 | 採否 | 扱い |
|---|---|---|---|
| A-01 | **real / blocker** | 採用 | 契約 v3.1 の 1.5 を書き換える。権威のある identity と無い identity を分ける |
| A-02 | **real / blocker** | 採用 | 契約 v3.1 の 4 節に「E1 の入力値域は launcher の捕捉集合であって campaign の捕捉集合ではない」を明記し、`OSError` 由来 failure の扱いを固定する |
| A-03 | **real** | 採用 | 契約 v3.1 の 7 節へ `finished_at` を row/file 全件等値の対象に加える |
| A-04 | **real (親の記載不備)** | 採用 | `parent-probes.md` へ erratum を追記する。probe P-1 は v2 の無条件拒否 hook を無効化して測っており、その記載が抜けていた (下記 3 節) |
| A-05 | **real / blocker** | 採用 | 契約 v3.1 の 5.3 を書き換える。`not-consumed` 枝の正例は sealed 経路に存在しないので、D1522 に従い**下層を直接呼ぶ test** で正例を作る |
| A-06 | refuted | 記録のみ | 生成 bytes は同一で正しさ上の受理集合は広がらない。公開 API の呼出し形が増えるのは事実なので plan v2 へ注記 |
| A-07 | refuted | 記録のみ | 照合対象内の破れを `observed` に落とす経路は無い |
| A-08 | refuted | 記録のみ | interface 模倣だけの偽 registry は validated capability を作れない |

### レンズ B (整合・実効性・所有範囲)

| # | 判定 | 採否 | 扱い |
|---|---|---|---|
| B-01 | **real** | 採用 | brief のアンカー 5 件を訂正する (下記 2 節) |
| B-02 | refuted | 記録のみ | 3 digest の綴りは plan が正しい。ただし terminal 行 field 名 `observation_start_event_sha256` と `_AttemptState` 属性 `observation_event_sha256` の対応づけを契約へ明記する |
| B-03 | **real / blocker** | 採用 | 契約 v3.1 の 6.1 へ、draft 時点で欠ける 3 digest の表現 (null か欠落か) と、adapter が補う private ABI の形を書く |
| B-04 | **real / blocker** | 採用 | plan v2 は transition callback の呼出し閉包 (直接 4 / `_atomic_update` 7 / marker 付き 3、callable production 6 + test 4) を数える |
| B-05 | refuted | 記録のみ | keyword-only 既定を守る限り既存 caller は壊れない |
| B-06 | **real / blocker** | 採用 | **単位 2 と単位 3 は双方向に依存しており素集合でない。** plan v2 は実装子を 3 本から **2 本**へ変える |
| B-07 | **real / blocker** | 採用 | 上記 (2) のとおり契約 9 節を訂正 |
| B-08 | refuted | 記録のみ | literal / path / whole-file hash の pin は 0 件。親の「7 file」が plan の 8 file を覆っていなかった点は plan v2 で 10 file へ直す |
| B-09 | **real** | 採用 | production caller 0 件は正しいが test caller (public 2 / test seam 13 / 共通 2) を数えていなかった。plan v2 へ記載 |
| B-10 | refuted | 記録のみ | C2 境界の侵犯なし |
| B-11 | **real / blocker** | 採用 | **terminal-failure 枝だけ旧 field のまま残す変異が生存する。** 契約 v3.1 の 5.1 へ「両枝が同じ field を読む」ことを下層直呼び test で固定する条項を足す |
| B-12 | **real / blocker** | 採用 | replay 8 箇所の個別照準は old/candidate の二重 replay で冗長化する。plan v2 は reader call 数を固定する seam を要求する |
| B-13 | **real / blocker** | 採用 | 規模超過。上記 (3) |

## 2. 段 1 brief の訂正 (B-01)

| 誤 | 正 |
|---|---|
| 「契約 v3 の 4 節 = 単位を分割しない」 | 契約 v3 の 4 節は E1 再導出。単位分割は `rulings-resolved.md` の 4 節 |
| `_S8B_V2_EVENT_KEYS` `:495` | `:490` (`:495` は `S8B_V2_SCHEMA_PROFILE`) |
| validator 呼出し `:1434` | `:1437` (`:1434` は label 引数) |
| `_require_handle` `:279` | `:280` |
| `attempt_registry_core.py` 2,131 行 | 現物 2,160 行 |

## 3. 親の実測の訂正 (A-04) — 規律 7 の追記訂正

**probe P-1 の記載は不完全だった。** parent-probes.md は一時変異を「4 点だけ」と書いたが、
probe は同時に `dataclasses.replace(v2, terminal_row_validator=None)` を使い、
**v2 の無条件拒否 hook `_reject_unsealed_s8b_v2_terminal` を無効化していた。** その記載が抜けていた。

**測定そのものは有効である。** この hook は C1b が封印証拠 validator へ**置き換える対象**であり、
probe が測ったのは「hook を置き換えたあと、その手前にある core の等値検査と null matrix を
5 形が通るか」である。前 wave が「1 行も書けない」と測ったのはまさにこの手前の 2 検査なので、
probe はその問いに答えている。

**しかし一般化は取り消す。** 「契約 v3 の 5 形が consumer を端から端まで通った」とは言えない。
probe が示したのは generic core の reason / null matrix / exact key までで、
leaf・adapter・durable evidence 経路は測っていない。契約 v3.1 の 5 節はこの射程で書き直す。

レンズ A が挙げた例も採る。`observed` 行へ任意の `primary_value=999` を入れても現行 null matrix は
受理する。したがって「core を通った」は「証拠 validator を通った」を含意しない。

## 4. 変異の事前登録 (DW-M01)

**実装面の差分が 0 なので変異 matrix は免除される (DW-S04)。受入全走は免除されない。**

次 wave のために、レンズ B が照準し直した結果を記録する。

- **殺せる**: M1 (outer extra key)、M2 (binding extra key / 旧綴り置換)、M3 (LF 追加と separator 変更を
  別変異に分離)、M4 (非有限を有限列へ残す / `nonfinite_count` を増やさない)、M5 (競合を failure より後へ)、
  M6 (failure/full-exec 枝削除)、M7 (partial exec の誤分類)、M8 (`nonfinite_count` 再計数・
  rep-integrity 再導出・合計式を個別変異に)、M9 (高 CV を observed へ)、M10 (primary を先頭値から)、
  M11 (handle/state 照合を 1 箇所削除)、M12 (digest を self-report からコピー)
- **生存する (再照準が要る)**:
  - **terminal-failure 枝だけ `failure_reason` 固定のまま残す変異** (B-11)。v1 は既定が同じで差が出ず、
    canonical v2 は E1 が terminal-failure を出さないので後段で隠れる。→ 下層直呼び test で固定する
  - **`:1687` の old replay だけ evidence 再読を省く変異** (B-12)。`:1698` の candidate replay が
    同じ破損を拒否するため通常 test では生存する。→ reader call 数を固定する seam が要る
- M13〜M18 は「通常 test へ置く」だけでは kill を実測したことにならない。次 wave の事前登録集合へ戻す。

## 5. 次 wave の出発点

- **`contract-v3.1.md` が契約の正本である。** v3 は本 wave 内で supersede した (追記訂正、規律 7)。
- **`plan-v2.md` はそのまま段 5 へ入れられる。** 実装子は **2 本** (leaf、統合)。
- 段 2 / 段 3 の成果物は変更面の骨格が同じなので流用できる。再検査は段 6 レビューへ寄せる
  (読み込み契約の規定)。**次 wave は段 5 から始めてよい。**
- C2 は runner の構造化 `execution_failure` と campaign の算出変更を持つ。C1b へ混ぜない。
