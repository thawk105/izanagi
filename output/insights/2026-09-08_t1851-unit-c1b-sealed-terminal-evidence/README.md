# [T-1851] 単位 C1b やり直し — 契約 v3.1 を確定させ、次 wave が段 5 から始められる状態にした

base `8193eefdb` (継承 tip `89605bb39` + local main `645d0d663` の merge)。
branch `worktree-dev-wave-t1851-unit-a`。**land しない (D1341)。**

## 1. この wave が出した結論

**契約 v3.1 を確定させた。本 wave では実装しない (`4 → 7 → 8 → 9`)。**

前 wave (`2026-09-07_t1851-unit-c1b-contract-v2-defects`) は契約 v2 が実体化不能だと確定させ、
実装 0 行で終わった。本 wave はその訂正を契約 v3 として書き下ろし、**条項ごとに束縛先の
consumer へ probe を通してから固定した** — これが前 wave の直接の失敗原因だったためである。

その契約 v3 に対し、段 2 の plan と段 3 の敵対レンズ 2 本を当てた。**両レンズとも判定は no** で、
うち 3 件は plan ではなく契約そのものを変える所見だった。親が現物で裏取りして採用し、
契約 v3.1 へ畳み込んだ。

**前 wave との違いは、次 wave が段 5 (実装) から始められることである。**
契約 v3.1 と plan v2 が揃っており、段 2・3 をやり直す必要がない。

## 2. 段 1 で通した consumer probe (7 本)

正本は `parent-probes.md`。契約 v3 の各条項に probe 番号が付いている。

| probe | 何を測ったか | 結果 |
|---|---|---|
| P-1 | 「観測後の理由を別 field に載せる」設計が core の等値検査と null matrix を通るか | **正例 5/5 通過。**前 wave が「1 行も書けない」と測った状態が解消。負例 7 件のうち 2 件が素通り (下記 3 節) |
| P-2 | 証拠文書が guarded writer の三軸走査を通るか | v2 の literal 形は**必ず拒否**。v3 の平文/digest 分離は通過。平文へ戻す負例 2 本は両方また拒否 |
| P-3 | `campaign_record` の key 集合 | **exact 30 key。**前 wave の列挙 29 語には `binary_sha256_at_measure` が抜けていた |
| P-4 | 非有限値の扱い | 有限のみ列 + 元の `reps_expected` で意図どおり。**落とした本数だけ `reps` を減らすと欠測が消えて健全に見える** |
| P-5 | 封印の発行経路 | `_AttemptState` の 3 digest は `observation_event_sha256` の綴り。test seam は adapter 経由だけでは塞がらない。handle 機構が前例になる |
| P-6 | E1 の枝順 | campaign `_run_session` の 6 枝と一致 |
| P-7 | pin 閉包と gate 入力の実在 | identifier / path / whole-file hash は 0 件。`launch_floor_attempt()` の production 呼び手は依然 0 件。**ただし閉包として不完全だった (下記 3 節)** |

## 3. 段 3 が出した blocker (親が裏取りして採用した 6 件)

正本は `s4-adjudication.md`。**このうち 3 件は契約そのものを変えた。**

| # | 内容 | 裏取り |
|---|---|---|
| A-01 | 証拠の identity 群を「reservation と全件等値」で束縛する条項が、**呼び手が選べる値を権威に据えていた** | durable claim が持つのは `cell_id` `records` `threads` `workload` `campaign_run_id` `run_relpath` `mode` `attempt_ids` だけ。`event` `kind` `seq` `round` `trigger` `retry` には権威が**無い** |
| A-02 | E1 の正本を「campaign の実 semantics」としたが、**launcher の受理集合のほうが広い** | launcher は `OSError` も捕捉 (`:777`)、campaign は捕捉しない (`:6264`)。`OSError` は launcher では terminal、campaign では session 行が生まれない |
| B-07 | 「pin 追加不要」が **semantic inventory を閉じていない** | `test_official_perf_closure.py:44` の `_REVIEWED_PERF_FILES` は exact frozenset、`:531` が production を AST 走査、`:903` が集合等値を assert |
| A-03 | crash 後の row/file 全件等値に `finished_at` が無い | core は `finished_at` を text としか見ない (`:1039`)。file 据え置きで行の時刻だけ改竄できる |
| A-05 | `not-consumed` 枝の拒否条項に**同じ枝の正例が存在しない** | E1 は `not-consumed` を出さず、証拠 validator は状態一致を要求する。恒真な拒否になりうる |
| B-11 | **`terminal-failure` 枝だけ旧 field のまま残す変異が生存する** | v1 は既定が同じで差が出ず、canonical v2 は E1 が terminal-failure を出さないので後段で隠れる |

A-05 と B-11 はどちらも **D1522 (上流が拒否する形でも下層の実体を直接呼ぶ test を置く)** で閉じる。

構造の所見も 3 件採った。B-03 (draft→validated の private ABI が閉じていない)、
B-04 (transition callback の呼出し閉包 10 本を数えていない)、
B-06 (**旧単位 2 と旧単位 3 は双方向に依存しており素集合でない**)。

## 4. 親が撤回・訂正した主張 (規律 7 の追記訂正)

- **probe P-1 の記載は不完全だった。** probe は v2 の無条件拒否 hook を無効化して測っており、
  その 1 点が抜けていた (A-04)。**測定自体は有効** — その hook は C1b が置き換える対象で、
  probe が測ったのは「その手前の core 2 検査を 5 形が通るか」= 前 wave が測ったまさにその箇所。
  ただし「端から端まで通った」という一般化は取り消した。射程の正本は契約 v3.1 の 5.2.1。
- **probe P-7 の閉包は不完全だった。** identifier / path / whole-file hash の 3 種類しか
  引いておらず、semantic inventory 型の pin を落としていた (B-07)。
- 段 1 brief のアンカー 5 件を訂正した (B-01)。

## 5. 規模の判定 — 1 wave に収まらない

段 2 plan は「収まる」と自己判定したが、**leaf を自分で `new:1-850` と宣言しながら見積り表には
`+500〜700` と書いており内部矛盾していた。** レンズ B の再見積りは
production 1,580〜2,120 / test 1,900〜2,850 で、裁定済み上限
(production 1,000〜1,600 / test 1,500〜2,400) を超える。

ユーザーは「収まらないなら切る判断は次の親に任せる。中途半端な分割は却下済みで、切るなら
契約の文書だけまで戻る」と事前に定めていた。**中途半端な分割はしていない。**

## 6. 次 wave の出発点

- **契約の正本は `contract-v3.1.md`。** `contract-v3.md` は本 wave 内で supersede した。
- **`plan-v2.md` はそのまま段 5 へ入れられる。** 実装子は **2 本** (leaf → 統合)、**直列**。
  leaf は他の 8 file を import しない純関数層なので単独で閉じる。
- **次 wave は段 5 から始めてよい。** 変更面の骨格が同じなので段 2・3 の成果物を流用でき、
  再検査は段 6 レビューへ寄せる (読み込み契約の規定)。
- 段 5 の途中で規模超過が判明した場合も production の途中分割はしない。
  **leaf が閉じた時点を checkpoint とし、統合子は次 wave へ送る。**
- 変異は生存 2 件 (terminal-failure 枝、old replay) に専用の kill 手段を割り当ててから登録する。
- C2 は runner の構造化 `execution_failure` と campaign の算出変更を持つ。C1b へ混ぜない。

## 7. 受入全走 — `child-green` にならなかった (帰属は本 wave に無い)

- 投入 (01:27 JST): `tools/dev_wave_wait.py acceptance`、`claimed_main=736cb35c7`。
- 結果 (01:35 JST): **rc=70 `child-verdict`。21,594 passed / 68 skipped / 1 failed** (collected 21,663)。
- 赤は `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
  の 1 件だけ。**被覆率 26 / 29 = 89.655172%** で閾値 0.90 を 1 node 分割った。
  単独再走でも同じ数字が出る**決定的な赤**で flake ではない。
- **帰属は本 wave に無い。** 本 wave の commit 4 本は `docs/` と `output/insights/` だけを触り、
  test file も production file も 1 行も変更していない。同じ branch の前 wave の受入は
  21,414 passed で緑だった。以降 branch に加わったのは文書 commit と local main 取り込み 2 回だけである。
- **既知の型の再発である (F684)。** 台帳 `orchestrator/tests/acceptance_duration_ledger.json` の
  最終更新は main の `d53c91a2b` (2026-09-07) で、以降 main は test file を 20 本以上変えている。
  F684 が定めた恒久対応は「凍結 pin の 8 suite に触れず、その外側の未登録 node だけを
  実測所要つきで足す部分更新」であり、**これは main 側の台帳保守である。**
- 本 wave は D1341 により land しないため修復せず記録に留めた。**緑として扱っていない。**
- lease は走行後に別 wave が取得しており (main も再前進)、他者の保持を解放していない。

## 8. 収録物

- `contract-v3.1.md` — **契約の正本**
- `contract-v3.md` — 段 1 版 (supersede 済み。追記訂正の記録として残す)
- `plan-v2.md` — 次 wave が段 5 で使う実装 plan
- `parent-probes.md` — 段 1 の consumer probe 7 本 (erratum 2 件を追記)
- `s1-brief.md` — 段 1 brief
- `s4-adjudication.md` — 段 4 裁定 (所見の real/refuted 表、変異の照準)
- `verbatim/` — 段 2 plan、段 3 レンズ A / B の逐語出力と各 receipt
- `prompts/` — 全 3 子へ渡した prompt の逐語
