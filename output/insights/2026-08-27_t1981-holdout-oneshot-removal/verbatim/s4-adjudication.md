# 段 4 裁定 — T-1981 性能測定の一回性強制の撤去

親が段 2 プランと段 3 の 2 レンズを real/refuted で裁定し、プラン v2 と変異事前登録を確定する。
親自身の brief と実測も裁定対象に含めた (2 件を訂正した)。

---

## 0. 親の暫定裁定の結末

| 暫定 | 結末 | 根拠 |
|---|---|---|
| (P1) `:1391-1394` だけ外す | **棄却** | finalize 側 `:1553-1599`、旧 claim identity `:1411-1448` でも止まる (段 2 / レンズ B が独立に指摘) |
| (P2) attempt ticket は残す | **棄却** | 台帳に 96 件の marker が現存し、marker path は cell claim digest 由来。親が実物を数えて確認 |
| (P2) の D893 帰属 | **誤り。訂正する** | 下記 2 |
| (P3) 承認 flag の identifier 閉包 | **一部採用**。下記 5 で scope を分ける | R33 pin |
| (P4) 実 qsub で確かめる | **採用。ただし合格条件を引き上げる** | 下記 6 |

親の実測の訂正 2 件 (どちらも段 3 が捕らえた):
- `evidence-deadlock.md`「2026-08-24 の run は途中死し成果物なし」→ **誤り**。完走していた。
- `evidence-failed-resubmit.md`「投入元は main repo の worktree だった」→ **成立しない推論**。
  同じ親 directory 下の独立 clone でも証拠 root は同じ値になる。判定不能。

---

## 1. 段 2 の代案 (測定世代の分離) を採用する — real

**裁定: real / 採用 / scope 内。**

cell の効果 key (`_key_fields` の 6 field) は座標として維持し、
**予約ごとの測定世代**を新たに発行して、`O_EXCL` と attempt 一回性を世代の内側へ限定する。
過去の cell 観測は予約の可否に影響しない。台帳は追記を続ける。

これは D1124 の「台帳は観測の履歴として追記を続けてよいが、予約の可否を決める権限を持たない」
の直訳である。

### 1-A. 識別子の命名 — 既裁定 D197 / D75 に従う

**無修飾の `generation` を field 名に使ってはならない。** D197 が既に却下している
(「契約世代と LLM 提案世代が同一 document 内で無修飾に混在しうる」)。
`env_contract_generation` のような namespace 付きにせよという既裁定に従い、本 wave では
**`measurement_generation_*`** を接頭辞とする (例 `measurement_generation_digest`)。
`activation_generation` が同じ repo 内に既に存在するため、この分離は必須である
(実在: `output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json` の
`environment.activation_generation`)。

### 1-B. `O_EXCL` を防壁と称さない — レンズ A 所見 5 は real

世代 claim の `O_EXCL` は、予約ごとに新しい ID を発行する限り通常経路で衝突しない。
**恒真に近いので「これが同一世代競合を守る」と書いてはならない** (規律: 恒真ゲートを作らない)。
非恒真なのは**同一世代の attempt marker 二重消費**の側であり、そこを正例・負例で固定する。

---

## 2. attempt ticket の帰属を訂正する — レンズ A 所見 2 は real

**裁定: real / 採用。親の brief (P2) の帰属は誤りだった。**

attempt ticket の一回性の出所は **D434** (「許可は attempt と回数に束縛する」) であって
D893 ではない。D893 が要求した機構 (launch reservation / run nonce / terminal tombstone) は
**T-469 として未実装のまま carry 中**である (2026-08-05 に「現状維持の追認 → 設計 wave 待ち」で
裁定され、現行 worklog でも `[T-469] (1037)` として持ち越されている。親が台帳で確認した)。

**帰結 (2 つ、向きが逆):**

1. attempt ticket の一回性は D434 の測定一回性であり、**D1124 の撤去射程に入る**。
   世代化してよい。D893 の防壁を外すことにはならない。
2. しかし同時に、**D893 が塞ぐはずだった「複数実行先から良い値を選ぶ」経路には、
   現在いかなる実装防壁も無い**。一回性がその代役を偶然果たしていた面がある。
   これは下記 3 で扱う。

---

## 3. best-of-N 選択の穴 — レンズ A 所見 1 は real、ただし現時点で到達不能。scope 外

**裁定: real / 実装しない / 裁定パッケージで記録して T-1982 へ渡す。**

### real である部分

`s8b_holdout_freeze.py:1884` の `--floor-result` は **呼び手が指定する必須引数**である。
複数の完走測定があれば、値を見た後にどれを freeze へ渡すか選べる。
反復を可能にすると、同じ 12 cell について完走した測定が 2 組以上存在しうる
(1 組は既に存在する)。

### しかし現時点で成立条件を満たせない — 親が確認した

レンズ A 自身が成立条件を「**official** fresh 測定が複数完走し」と書いている。
その official が今日は走らない。

1. `s8b_floor_campaign.py:453-462` の `_assert_official_permitted()` は
   **production で official を無条件拒否**する
   (「official mode は §8 (承認束縛方式) 未裁定のため core で無条件拒否する」)。
   bypass 用の flag・環境変数・引数を持たない。呼び出しは `:6989` と `:7096` の 2 箇所。
2. `s8b_holdout_freeze.py:1617-1618` は `result.eligible_for_refreeze is not True` なら
   `FreezeError` を投げる。pilot の結果は `eligible_for_refreeze=false` である
   (`s8b_floor_campaign.py:6590,7060-7073`、実測でも 2026-08-24 の result は false)。

したがって「反復 pilot の良い方を freeze へ入れる」経路は**今日は 2 重に塞がっている**。
穴が開くのは official が解禁されたときであり、それは §8 の裁定と D1161 の人間承認を要する
別の手番である。

### scope 外とする理由

ユーザーは順序を明示している。worklog (1029) の T-1982 が
「一回性を撤去した後、『holdout の値を見てから選択・凍結・主張を変えない』がどこで守られているかを
棚卸しする。一回性が実質的な防壁として働いていた面があれば、選択経路側へ移す。
**無ければ『守られていない』と正直に記録する — 恒真な保証を作らない**」である。
本 wave でにわか作りの防壁を足すことは、この指示に反する。

**本 wave の義務は、T-1982 が机上から始めなくて済むように証拠を残すことである。**
上記の file:line と「official が塞がっている限り到達不能」という条件を insights へ記録する。

---

## 4. 旧 schema の reader を残す — レンズ A 所見 3 / レンズ B 所見 1・7 は real

**裁定: real / 採用 / scope 内。**

旧 v1/v2 claim・ledger・marker の bytes は台帳に現存する (claim 36、marker 228、ledger 36 行)。
`s8b_ratified_freeze.py` の consumer は選択済み `floor_source` の bytes を再取得して
同じ live inspector を必須実行する。**旧 reader を消すと既存 proof chain の受理集合が狭まる。**

したがって:

- 新世代の schema は**新しい namespace** として足し、旧 v1/v2 の exact reader は
  **read-only の historical decoder として温存**する。
- 「全 source から承認 identifier が 0 件」を要求するテストを書いてはならない。
  historical decoder を巻き添えにする。**active な CLI・env・shell・production 呼び出し面に
  限定**した不在検査にせよ。
- 旧 claim を新予約の権威にしない。履歴として読めるだけにする。

---

## 5. 撤去 scope を 2 つに分ける — R33 pin が現に一致しているため

**裁定: 一部を scope 外とし、裁定パッケージでユーザーへ返す。**

### 本 wave で撤去するもの

- `s8b_holdout_admission.py` の予約拒否・attempt 一回性の世代化・**承認要求 (拒否) の撤去**。
  floor / oracle / n-pilot legacy / n-pilot R33 の 4 系統すべて。ここが「予約経路」の本体である。
- floor の driver と shell の承認 flag と env 伝播の**完全撤去**:
  `s8b_floor_campaign.py`、`tools/pegasus/submit_floor.sh`、`tools/pegasus/floor_campaign.sh`。
- 対応するテストと fixture。

### 本 wave で撤去しないもの (理由つき)

`orchestrator/campaign/s8b_oracle_n_pilot.py`、`tools/pegasus/oracle_n_pilot.sh`、
`tools/pegasus/submit_oracle_n_pilot.sh` からの identifier 撤去。

**理由 (親が実測):** R33 事前登録 protocol
(`output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json`) は
`source.driver_sha256` と `source.job_script_sha256` で上記 2 file の bytes を pin しており、
**現在の bytes と exact に一致している** (親が `sha256sum` で確認:
`d447688a...` / `566698b3...`)。`s8b_oracle_n_pilot.py:590-595` の `load_inputs()` は
不一致なら `driver sha256 が protocol と不一致` で落ちる。
かつ **R33 campaign は未実行**である (台帳に `n_pilot_r33` role の claim が 0 件)。
つまりこの pin は歴史記録ではなく、**これから走る campaign への生きた束縛**である。

1 byte でも変えると、回復には successor 事前登録の発行が要る。
**事前登録の再発行は、D1124 が命じていない新しい設計行為**であり、
事前登録という機構の趣旨からしてユーザー裁定に属する。

**この分割の帰結:** oracle / n-pilot 側に残る `--confirm-irreversible-pilot-holdout` は、
`s8b_holdout_admission.py` 側の承認要求が消えるため**何も gate しない引数**になる。
承認としては本 wave で既に無効化される。残るのは identifier の掃除だけである。

**これを「死んだ引数」のまま放置しない。** True を渡しても False を渡しても
admission の挙動が exact に同じであることを固定するテストを足し、
「承認としては無効」を明示的に pin する。

---

## 6. P4 の合格条件を引き上げる — レンズ B 所見 3・4 は real

**裁定: real / 採用。**

### 6-A. 前提条件 (親が確認した blocker)

wave worktree には `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/` が
**存在しない**。`submit_floor.sh:414-421,485-505,514-521` はこの root と 3 repo の
pin-clean を必須とし、欠落なら qsub しない。
cache は `/work/1/SFC/tanab/izanagi-thirdparty-cache/` に
`googletest` / `masstree` / `mimalloc` として現存する (親が確認)。
**投入前に `tools/pegasus/fetch_third_party.py` の hydrate を実行する。**
hydrate 先は `output/` 配下なので clean gate の対象外である。

### 6-B. 恒真な受入にしない条件

台帳 root は `git rev-parse --git-common-dir` から決まる。
**独立 clone から投入すると台帳が空に見えて、一回性が残っていても素通りする。**
投入元 checkout で `git rev-parse --git-common-dir` を実行し、
`/work/1/SFC/tanab/izanagi/.git` であることを**記録する** (推論しない)。
台帳の 12 claim と 96 marker は**そのまま残す**。退避も削除もしない。

### 6-C. 合格条件

予約通過だけでは不十分である。`floor-driver/run-linked` は build と予約より前に出るため、
それを合格条件にすると予約前に止まった job を誤受理する
(`s8b_floor_campaign.py:7391-7406` vs 実予約 `:7660-7685`)。

**合格条件 (すべて):**
1. `already consumed` 系の拒否が出ない。
2. runner の `campaign-start` が新 journal に出る (`:6276-6299`) — 予約通過の陽性証拠。
3. **最初の attempt 消費が通る** — 旧 96 marker と衝突しないことの証拠。ここが本項の核心。
4. `job-result.driver_rc=0`、terminal completed、96 session、`result.json.floors` が有限。

過去の完走は約 48 分だった。350 秒は**予約失敗までの時間**であって完走時間ではない
(親の `evidence-failed-resubmit.md` の読み違いをレンズ B が訂正した)。

---

## 7. 実装子の分割 — レンズ B 所見 8 は real

**裁定: real / 採用 (形を変えて)。**

file 所有は重複しないが、予約 API の署名が両側を同時に変えるため独立実装にならない。
直列化すると時間を無駄にするので、**親が共通 API contract を本裁定で固定し、並列で走らせる**。

### 固定する API contract (両子はこの署名に実装せよ)

- `reserve_floor_holdout_observations(...)` から
  `confirm_irreversible_pilot_holdout` / `irreversible_pilot_approved` 相当の
  キーワード引数を**削除する**。
- 返り値の `FloorHoldoutReservation` に `measurement_generation_digest: str` を**追加する**。
  既存 field は削除しない。
- n-pilot / oracle の予約 entry point は、呼び手 (`s8b_oracle_n_pilot.py`) が pin により
  変更不可であるため、**現行の呼び出し署名を維持する**。承認引数は受け取るが何も gate しない。

### 所有

- **実装子 A**: `orchestrator/campaign/s8b_holdout_admission.py`、
  `orchestrator/tests/test_s8b_holdout_admission.py`、
  `orchestrator/tests/s8b_floor_evidence_fixture.py`、
  `orchestrator/tests/test_s8b_oracle_driver.py`
- **実装子 B**: `orchestrator/campaign/s8b_floor_campaign.py`、
  `tools/pegasus/submit_floor.sh`、`tools/pegasus/floor_campaign.sh`、
  `orchestrator/tests/test_s8b_floor_campaign.py`、
  `orchestrator/tests/test_pegasus_floor_tools.py`、
  `orchestrator/tests/test_s8b_freeze_io.py`

`s8b_oracle_n_pilot.py` / `test_s8b_oracle_n_pilot.py` / oracle shell は**どちらの所有でもない**
(scope 外、上記 5)。

---

## 8. テストの粒度 — レンズ A 所見 6・7 は real

**裁定: real / 採用。** 既存テストの単純反転を禁じ、独立 nodeid へ分割する。

- `test_two_worktrees_parallel_fresh_runs_cannot_both_claim_the_same_keys` の反転は、
  「両方 admitted・24 行」だけを固定してはならない。次を別 nodeid に分ける。
  (a) 別世代の admission が通る (b) 同一世代の attempt 二重消費が拒否される
  (c) 旧 bytes の historical inspection が通る
- `test_protocol_master_seed_change_does_not_reset_cell_key` は、
  **旧予約と新予約の cell effect digest が exact に同じで、異なるのは測定世代 digest だけ**
  であることを assert せよ。単に「2 回目が通る」にすると、protocol を effect key へ混入させる
  変異を見逃す (D434 が effect key に protocol hash を入れない理由がここにある)。

---

## 9. scope 外だが記録する (裁定パッケージ候補)

1. **best-of-N 選択の穴** (上記 3)。T-1982 へ渡す。
2. **oracle / n-pilot の identifier 撤去と R33 successor 事前登録の発行** (上記 5)。
3. **floor 予算の drift** — レンズ B 所見 9。コードは `_floor_reservation_budget()` が
   30000 を返す一方、`floor_campaign.sh:9-14` と `tools/pegasus/README.md:233-235` は
   28200/28800 のままである。本 wave の scope 外。backlog へ。

---

## 10. 変異事前登録 (DW-M01)

段 2 の 10 件を基礎に、上記裁定を反映して確定する。
各変異は「前後に同じ入力を拒否する層が無いこと」と「赤理由が一つに絞れること」を
実装子が実装時にコードで確認し、確認できないものは登録しない (F28)。
**`expected_nodes` は ASCII の nodeid だけを使う。**

| # | 対象 | 変異 | 殺すはずの nodeid |
|---|---|---|---|
| 1 | `s8b_holdout_admission.py` floor 予約 | 旧 effect claim があれば fresh を拒否する分岐を復活 | `test_s8b_holdout_admission.py::test_floor_rereservation_ignores_legacy_cell_claims` |
| 2 | 同 floor finalize | ledger を再び effect digest で一意化する | `test_s8b_holdout_admission.py::test_floor_fresh_rereservation_appends_generation_rows` |
| 3 | 同 floor marker path | marker filename から測定世代 digest を除き旧 effect digest へ戻す | `test_s8b_holdout_admission.py::test_floor_attempt_single_use_is_scoped_to_measurement_generation` |
| 4 | 同 attempt 消費 | 同一世代の既存 marker を無視して再発行する | `test_s8b_holdout_admission.py::test_attempt_ticket_is_durably_single_use` |
| 5 | 同 oracle 予約 | oracle の世代 path を effect claim path へ戻す | `test_s8b_oracle_driver.py::test_oracle_repeated_reservation_is_admitted` |
| 6 | 同 n-pilot legacy 予約 | claim を effect digest の singleton へ戻す | `test_s8b_holdout_admission.py::test_legacy_n_pilot_repeated_reservation_is_admitted` |
| 7 | 同 R33 予約 | ledger intersection による過去 cell 拒否を復活 | `test_s8b_holdout_admission.py::test_r33_repeated_reservation_uses_new_generation` |
| 8 | 同 effect key | protocol hash を `_key_fields` へ混入させる | `test_s8b_holdout_admission.py::test_effect_key_is_stable_across_measurement_generations` |
| 9 | 同 historical reader | 旧 v1/v2 claim の exact reader を削除する | `test_s8b_holdout_admission.py::test_legacy_claim_bytes_remain_inspectable` |
| 10 | `s8b_floor_campaign.py` CLI | 削除した承認 CLI option を復活させる | `test_s8b_floor_campaign.py::test_floor_driver_rejects_removed_confirmation_option` |
| 11 | `s8b_holdout_admission.py` n-pilot 承認 | 承認未指定なら拒否する分岐を復活 | `test_s8b_holdout_admission.py::test_n_pilot_approval_argument_is_inert` |
| 12 | `submit_floor.sh` | 承認 env を `qsub -v` へ再び載せる | `test_pegasus_floor_tools.py::test_submit_floor_export_spec_has_no_confirmation_env` |

**受理集合を広げる wave なので、広げすぎを検出する負例も要る。**
変異 4 と 11 がそれに当たる (前者は同一世代の二重消費を許してしまう変異、
後者は承認が実は生きている変異)。

---

## 11. 不変条件 (実装子への拘束)

1. 規律 2 を 1 つも緩めない。未知 `observation_role` の拒否、freeze 由来 signature の
   exact 集合一致、gflags 型意味論と `--flagfile`/`--fromenv`/`--tryfromenv` 拒否、
   保護比率の admission 要求、canonical JSON bytes 検査、`_write_exclusive` の
   `O_CREAT|O_EXCL` は**すべて現状のまま**。レンズ A 所見 4 がこれらの独立性を確認済み。
2. 規律 1 に触れない。
3. `s8b_holdout_freeze.py` は**変更しない** (一回性の hit が 0 件であり、
   触る必要が無いことを段 2 が確認済み)。
4. D1161 の予算承認と `_assert_official_permitted` は**変更しない**。
5. 台帳への追記と座標記録は残す。
6. 恒真な保証を作らない。`O_EXCL` を防壁と称さない (上記 1-B)。
