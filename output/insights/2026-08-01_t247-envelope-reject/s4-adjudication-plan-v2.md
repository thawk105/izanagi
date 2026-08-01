# 段 4 裁定 + プラン v2 — [T-247]

親が段 2 プランと段 3 敵対相談 2 本 (ともに NO-GO) を real/refuted・採用/不採用・scope 内外で裁定した。

## A. 所見の裁定

| # | 出典 | 判定 | 採否 | scope | 根拠 |
|---|---|---|---|---|---|
| A1 | lens A #1 | **real (親が実測で確認)** | 採用 | **内** | `contract.py:236-244` の `validate_protocol` が timing の prologue/attestation/finalize を正数性のみ + 和 29100 でしか固定しない。親が実行して `(attestation=1199, finalize=1)` の **ACCEPT を実測**。この timing こそ driver が実消費する値 (`t126_driver.py:566,683,689-690,773,861,1109`)。`validate_protocol` は driver・collector・submission の共通受理 gate |
| A2 | lens A #2 | real | **不採用** | **外** | consumer (collector / public verifier) が**予約 policy** の意味論を検証せず identity/blob hash だけを見る件。新しい層への gate 新設であり「宣言済みの拒否を実発火させる」を超える。裁定パッケージへ。ただし A1 を採ることで**制御 protocol 側の consumer 穴は閉じる** (collector が `validate_protocol` を呼ぶため) |
| A3 / B1 | lens A #3, lens B #1 | real | 採用 | 内 | submit 負例が `1500/0/600` の 1 方向だけでは、2 比較同時削除の変異が生存する。表駆動の複数方向が要る |
| B2 | lens B #2 | real | 採用 | 内 | job 正例が最初の dependency で止まるため、3 出力と配列 index の対応を一度も観測しない。出力順の交換変異が生存する |
| B3 | lens B #3 | **未実証** | 条件付き採用 | 内 (受入前提) | 「計算ノード全走が T-248 で既知赤」は worklog (93) の実測 (request `876439` で 4316 passed) と整合しない。**推測で赤と決めず親が実測する**。新テストは fake bin の python3 wrapper で解決系を固定し、T-248 の production 修正には踏み込まない |
| A4 | lens A #4 | real | **採用 (限定)** | 内 | submit 側の予約 block も producer status を捨てる。**予約 block 2 箇所だけ**対称に直す。他 7 block へは広げない (DW-G03: 族一般化しない) |
| A5 | lens A #5 | real | **不採用** | **外** | job が `json.load` (last-wins)、submit が `no_dups` という重複 key 非対称。別軸の hardening。**新 D に非対称として明記**し、コードは変えない |
| A6/A7/B5 | lens A #6,#7, lens B #5 | **real (親の brief が誤り)** | 採用 | 内 | 親 brief の DW-G05 因果は誤り。実測で確認: job の deadline は `WMAX_FIXED_S=29100` の **hardcode** (`t126_qualification.sh:29-30`)、policy の `WMAX_S` は `L625` の qstat 下限比較だけ、`PROLOGUE_CAP_S` は `L697` の prologue cap にのみ使う。「wmax=2 → member kill → finalize reserve 消失」は**成立しない**。DW-G05 を下記へ差し替える |
| A8 | lens A #8 | real | 採用 (記述のみ) | 内 | 予約 policy は 9 設定。`member_term_grace_s` は両 script 未参照の orphan。「8 key 全部」でなく「submit が列挙する 8 key への射影」と限定表記する |
| A9 | lens A #9 | real (限定) | 採用 (記述のみ) | 内 | 親の「pin 0 件」は**現 repository / worktree 内の literal pin が 0 件**へ射程を限定する |
| B4 | lens B #4 | real | 採用 | 内 | late-failure fixture の wrapper は、版数 probe・monotonic・receipt を委譲し予約 parser の 1 回だけを失敗させ、以降を再委譲する必要がある。注入の一意性と呼出し回数を assert する |
| B6 | lens B #6 | real | 不採用 (記述のみ) | 外 | 全 9 block が producer status を失う。新 D に「束縛したのは予約 block 2 箇所だけ」と残存限界を明記し、他 7 block は変えない |
| B7 | lens B #7 | real | 採用 (記述のみ) | 内 | プランの変更で必然的に赤になる既存テストは静的に 0 件。既存境界テストの更新は「壊れるから」でなく **D96 の純増 coverage として**行う。既存回帰の緑を新 guard の発火証拠に数えない |

段 2 プランの本体方針 (P1 = command substitution + `if !` で python rc を明示検査、8 key へ揃える、
submit は個別 3 cap を純増し和を残す) は **採用**。上記で補強する。

## B. scope の確定 (プラン v2)

### 実装子が編集する (コードとテストのみ。docs 編集と commit はしない)

1. `tools/pegasus/t126_qualification.sh:453-468`
   - process substitution をやめ `if ! OUT=$( "$PY" ... ); then exit 2; fi` + here-string `readarray` にする。
   - python 内は「8 key 個別比較 → 全部通ったときだけ既存と同じ順序で 3 値を print」。
   - 代入後に **mapping assert** を純増: `[[ "$WALLTIME_S" == 36000 && "$WMAX_S" == 29100 && "$PROLOGUE_CAP_S" == 900 ]] || exit 2` (B2 対策。配列 index と変数の束縛を非恒真にする)。
   - 既存の `[[ ${#RESERVATION_VALUES[@]} -eq 3 ]]` と downstream 代入は残す。
2. `tools/pegasus/submit_t126_qualification.sh:187-232`
   - `216-220` の条件へ `prologue_cap_s != 900` / `attestation_cap_s != 600` / `finalize_reserve_s != 600` を `or` で純増。既存条件は 1 つも外さない。
   - 予約 block も **A4 対称化**: process substitution をやめ producer status を明示検査する。
   - `187-188` のコメント (「same rejection conditions as before」) を実態へ更新。
3. `orchestrator/qualification/contract.py` の `validate_protocol` timing 検査 (`236-244`)
   - `prologue_cap_s != 900` / `attestation_cap_s != 600` / `finalize_reserve_s != 600` を `or` で純増。
   - 既存の正数性・member/gap・和・wmax closure・walltime 条件は 1 つも外さない。
4. `orchestrator/tests/test_t126_pegasus_tools.py`
   - `test_reservation_policy_and_job_headers_freeze_wmax_and_walltime` (1209-1225) に 8 key の個別 assert を純増 (D96 の境界更新①)。
   - 新設 subprocess テスト (D96 の境界更新②、下記 C の変異を殺す形で書く)。
5. 制御 protocol の境界テスト (既存 `validate_protocol` 系テストの所在は実装子が同定する)
   - timing の個別 3 値を assert する境界テストを純増。

### 実装しない (real だが scope 外 → 裁定パッケージ)

- A2 残余: consumer による**予約 policy** の意味論検証 (新層の gate 新設)。
- A5: job/submit の重複 key hook 非対称 (`json.load` vs `no_dups`)。
- B6: 予約 block 以外の 7 個の readarray の producer status 切断。
- A8: `member_term_grace_s` (両 script 未参照の orphan 設定)。

## C. 変異事前登録 (DW-M01)

各変異は「その位置より前に同じ入力を拒否する検査がないこと」「無効化時の赤理由が 1 つ」を確認して登録する。

### submit 側 (和を残すため、単独削除は等価変異)

**解析結果 (事前に記録する)**: 和 `calculated == 29100` を残す限り、個別比較を**1 つだけ**外しても受理集合は
広がらない (他 2 cap が正値に固定され、和が prologue を一意に決めるため)。よって単独削除は**等価変異**であり、
生存を検出力不足と数えない。受理集合を実際に広げるのは **2 比較以上の同時削除**である。

| ID | 変異 | 殺す負例ベクトル (prologue/attestation/finalize) | 期待 |
|---|---|---|---|
| M-S1 | prologue + attestation の比較を削除 | 1500 / 0 / 600 | KILL |
| M-S2 | prologue + finalize の比較を削除 | 1500 / 600 / 0 | KILL |
| M-S3 | attestation + finalize の比較を削除 | 900 / 1200 / 0 | KILL |
| M-S4 | 3 比較すべて削除 | 上記いずれか | KILL |
| M-S5 | 予約 block を process substitution へ戻す | 完全出力後に rc≠0 を返す producer | KILL |

### job 側 (和の等式を持たないので単独削除が有効変異)

| ID | 変異 | 殺す負例 | 期待 | 備考 |
|---|---|---|---|---|
| M-J1〜M-J5 | `walltime` / `member_cap_s` / `round_gap_s` / `attestation_cap_s` / `finalize_reserve_s` の比較を個別削除 | 当該 key だけを drift | KILL | 単一理由 (bash mapping assert の射程外) |
| M-J6〜M-J8 | `walltime_s` / `wmax_s` / `prologue_cap_s` の比較を削除 **かつ** bash mapping assert の該当項も削除 (両層変異) | 当該 key だけを drift | KILL | DW-M04 に従い両層変異として登録。単層削除は他層が拒否する冗長 gate |
| M-J9 | 配列 index の交換 (`RESERVATION_VALUES[0]` ↔ `[1]`) | canonical policy (正例) | KILL | mapping assert が殺す。B2 対策の実証 |
| M-J10 | 明示 status 検査を process substitution + 長さ guard へ戻す | 完全 3 行出力後に rc=73 を返す producer | KILL | P1 と「print を後ろへ移すだけ」を区別する |

### contract.py `validate_protocol` 側 (正数性 >0 の制約下)

| ID | 変異 | 殺す負例 (prologue/attestation/finalize) | 期待 |
|---|---|---|---|
| M-C1 | attestation + finalize の比較を削除 | 900 / 1199 / 1 | KILL (親が ACCEPT を実測済み) |
| M-C2 | prologue + attestation の比較を削除 | 1499 / 1 / 600 | KILL |
| M-C3 | prologue + finalize の比較を削除 | 1499 / 600 / 1 | KILL |
| M-C4 | 3 比較すべて削除 | 上記いずれか | KILL |

### 正例 (過剰拒否の検出。DW-M01: 負例だけでは拒否しすぎる変異が生き残る)

| ID | 正例 | 期待 |
|---|---|---|
| P-J | canonical 予約 policy で job が予約検査を越え downstream marker へ到達 | PASS |
| P-S | canonical 予約 policy で submit が scheduler 呼出しへ到達 (既存 `test_fake_qsub_qstat_exact_visibility_and_durable_receipt`) | PASS |
| P-C | canonical `t126_control_v1.json` を `validate_protocol` が受理 | PASS |

## D. DW-G05 成果物影響 (段 1 の記述を実測結果で差し替え)

**段 1 brief の因果 (「wmax=2 → member kill → finalize reserve 消失 → ledger 試行欠落」) は誤りだった。**
実測で確認した正しい影響:

- 予約 policy の drift が実際に効くのは 2 点だけ — `t126_qualification.sh:697` の **prologue cap**
  (認可外の prologue 予算) と `L625` の **qstat 下限比較** (実 Wmax を下回る queue 許容でも投入が通る)。
  job の deadline は `WMAX_FIXED_S=29100` の hardcode なので policy からは動かない。
- **実消費される cap は制御 protocol (`t126_control_v1.json` の `timing`) 側**であり、そこが和だけで
  凍結されている (A1)。`finalize_reserve_s=1` は driver の finalize reserve をそのまま 1 秒にし
  (`t126_driver.py:566,683,773,861`)、`attestation_cap_s=1199` は attestation cap を変える (`:1109`)。
  これが **series-result / final-receipt の値と受理集合を、どの gate も個別に検証しないまま変える**経路である。
- 放置した場合の受理集合: submit・job・consumer のいずれも、和 29100 を保つ限り任意の
  cap 配分を受理し続ける。宣言済みの拒否は job 側で一度も発火しない。

## E. D96 手続

- 新 D を親が書く (採番は commit 直前に再確認)。記録内容: 受理集合を 8 key 個別値へ縮小、job は
  producer status を明示検査し出力行数を status の代用にしない、submit と制御 protocol は個別 cap 比較と
  既存和 closure を併用、**制御 protocol 層まで広げた理由** (裁定文の literal な射程は予約 policy だが、
  実消費される cap を和だけで凍結したままでは「個別に凍結した」保証が恒真になるため)、
  scope 外 (A2 残余 / A5 重複 key 非対称 / B6 残り 7 block / A8 term grace) の明記、却下案。
- 境界テストは**静的 freeze テスト + 新設 subprocess テスト + 制御 protocol の個別 assert の 3 点**を
  同じ変更単位で更新する (P4 単独では script 境界テストにならない = 段 2・段 3 の一致した指摘)。

## F. 受入

- 焦点テスト → 変異 matrix → test file 全体 → 計算ノード全走 (`tools/pegasus/dispatch_compute.py --task tests`)。
- B3 は推測で赤と決めず実測する。新テストは fake bin の python3 wrapper で解決系を固定する
  (テスト fixture の hermeticity であり T-248 の production 修正ではない)。
