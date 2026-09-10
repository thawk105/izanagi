# 段 4 裁定 — [T-1180] pilot 実測の承認を投入引数で渡す

親裁定。2026-08-16 19:15 JST。

## 0. 裁定 inbox の再走査 (段 4 直前の義務)

wave 開始後に 2 件が更新されていた。

- `2026-08-16-rulings-full3-28rulings.md` (18:50) — 「[T-1180] は同日 07:1x の一括裁定 #43 で
  決着済み。`flagship-cc-experiment-blockers.md` §4 は台帳反映前の情報で書かれており、
  **再裁定していない**」と明記。
- `2026-08-16-flagship-cc-experiment-blockers.md` (18:52) §4 — 択 (a) 「承認 receipt (repo 外) が
  実在するときだけ flag を渡す」を推奨しているが、**上記により旧情報**。

→ **#43 §3.3 が有効**。scope 変更なし。

## 1. 所見の real / refuted と採否

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 / B2 | P2 (receipt field) は先行する static admission (`certified_writer_admission._FLOOR_KEYS`) の exact key 集合で拒否され、承認付き実 job が driver 前に全滅する | **real** (親が `certified_writer_admission.py:184` と `_FLOOR_KEYS` を独立に確認) | **採用 → P2 不採用** |
| A2 | gate が証明するのは人間性でなく argv token の存在だけ | **real** | 採用 (保証文を限定) |
| A3 | 迂回路は 4 系統 (automation 経由の submitter、raw qsub、driver 直接、Python API) | **real** | 採用 (scope 外と明記) |
| A4 | dry-run / resume / 同一 job 再実行からの暗黙承認は無い | **real (肯定的)** | 記録 |
| A5 | 既定拒否と exact bool は plan の骨格では緩んでいない | **real (肯定的)** | 採用 (ambient env 非継承テストを追加) |
| A6 / B6 | brief の M8 / M9 は反証 — job script bytes は既に動的束縛済み | **real** | 採用 (M8/M9 を訂正) |
| A7 | `submit_floor.sh` 自身は commit blob 照合を持たず `assume-unchanged` drift に無防備 | **real** | **scope 外** (次の一手へ起票) |
| A8 / B7 | M10 の「実害ゼロ」は一般化しすぎ。投入 3 件と queue 消費は既発生 | **real** | 採用 (M10 を訂正) |
| A10 / B5 | runbook 未更新では人間が承認経路を実行できない | **real** | **採用 (段 7 で親が docs 更新)** |
| B1 | 実 scheduler への env 到達は未証明 | **real** | 採用 (残余リスク明記 + 設計で緩和 = P4) |
| B3 | `/v1` 維持は自動的な後方互換ではない | **real** | P2 不採用により moot |
| B8 | 過去の失敗型 F22 / F30 / F332 / F334 / F341 が再発しうる | **real** | 採用 (F30 型は A1 として実際に発火した) |

## 2. P2 (receipt への承認 field) — **不採用**

理由は 3 本。

1. **既裁定と衝突する。** D356 は「**receipt を足せば人間承認を表現できるとする**」を
   却下済みであり、「同じ実装担当 (AI を含む) が bytes・hash・receipt・pin をすべて作成でき、
   値の一致検査はすべて通る」と確定している。receipt field は承認の authority にならない。
2. **攻撃面を増やさない。** env を立てられる主体は、より直接的に
   `s8b_floor_campaign.py --confirm-irreversible-pilot-holdout` を起動できる (所見 A3-3)。
   receipt 束縛は、より弱い経路だけを塞ぎ、強い経路を塞がない。
3. **実行不能かつ scope 膨張。** 採るなら `certified_writer_admission.py` +
   `certified_writer_fixtures.py` + `test_campaign.py` + schema 版方針まで広がる (所見 A1/B2)。
   裁定 #43 の「最小形」に反する。

## 3. P4 — 承認 env の値は submission nonce にする (親の追加設計裁定)

段 2 プランは値を exact literal `1` にしていた。**これを nonce に変える。**

- **理由**: NQSV の既定 env export 挙動は未実測で、`#PBS -V` 不在だけでは login 環境の
  非継承を証明できない (所見 B1)。値が固定 literal `1` だと、誰かの shell profile に
  `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=1` が残っているだけで全投入が承認済みになりうる。
  **nonce は `submit_floor.sh` が実行時に生成するため、ambient env には構造的に存在し得ない。**
- **新機構ではない**: 既存の submission nonce を再利用するだけで、新しい artifact・schema・
  store・署名を作らない。裁定 #43 の「最小形」に収まる。
- **挙動**:
  - 承認 env 未設定 → driver flag を渡さない (既定拒否、現行と 1 byte も変わらない argv)。
  - 承認 env が設定済みかつ `IZANAGI_SUBMISSION_NONCE` と exact 一致 → flag を末尾に 1 個 append。
  - 承認 env が設定済みかつ不一致 (空文字を含む) → 既存 `write_failure 2 submit_binding` で
    **fail-closed 停止**。build も driver も走らせない。

## 4. 保証文の限定 (所見 A2 の帰結)

本 wave が作るのは **「標準投入経路で明示 token を要求する運用 gate」**であって、
**人間性を認証する gate ではない**。worklog / decisions には次だけを書く。

> 標準投入経路 (`submit_floor.sh` → `floor_campaign.sh`) では、投入時に
> `--confirm-irreversible-pilot-holdout` を渡さない限り、driver へ承認 flag は渡らない。

書いてはならない: 「人間承認を機械確認した」「承認主体を認証した」(D356)。

保証の範囲外 (明記する): automation が submitter を承認引数付きで起動する経路、
raw `qsub`、driver 直接起動、Python API 直接呼出し、`submit_floor.sh` 自身の
`assume-unchanged` drift (所見 A7)。

## 5. brief の実測訂正 (親の自己訂正)

- **M8 訂正**: 「path 束縛のみ、bytes 束縛なし」は誤り。
  `certified_writer_admission._validate_source_blob` が receipt の `job_script_sha256` と
  commit blob を照合し、`floor_campaign.sh:508-555` が実行中 bytes・receipt・commit blob を
  三者照合している。**job script bytes は動的に束縛済み**である。
- **M9 訂正**: 「両 script の pin が 0 件」は一括表現として誤り。正しくは
  「固定 digest literal の trust root は無い。floor job script は source commit と
  per-submission receipt に**動的**束縛済み。submitter 自身は未束縛」。
  なお**この訂正は編集面を変えない** — 動的束縛は再凍結を要求しないため、
  DW-O09 の結論 (再 pin 不要) は維持される。
- **M10 訂正**: 「floor run 実績 0 件、実害は将来のみ」は分解が必要。正しくは
  「**完了測定と一回性 key の消費は 0 件。投入は 3 件あり、queue 資源消費は既発生**」。

## 6. plan v2 (実装子への確定指示)

編集面は 3 file。`orchestrator/campaign/` は 1 byte も触らない。

1. `tools/pegasus/submit_floor.sh`
   - usage に `[--confirm-irreversible-pilot-holdout]` を追加。
   - `CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=0` を他の既定値と同じ場所で**リテラル初期化**する
     (ambient env から初期化しない)。
   - `case` に zero-arity flag として追加。値を取らないので `--confirm-... true` は
     `true` が unknown argument で rc=2 になる。
   - override 制限 (`--dry-run` 必須の 3 つ) には**加えない**。実投入で必要な引数である。
   - `export_spec` は承認時だけ `,IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=$NONCE` を append。
     未承認時は初期代入と qsub argv が現行と exact 一致。
   - **pre-submit.json / submit-receipt.json は 1 byte も変えない** (P2 不採用)。
2. `tools/pegasus/floor_campaign.sh`
   - 冒頭の `unset` に承認 env を加えない。
   - nonce bootstrap 検査の後で、承認 env が「未設定」または「`$IZANAGI_SUBMISSION_NONCE` と
     exact 一致」のどちらかであることを検査する。`${VAR+x}` で未設定と空文字を区別する。
     不一致は `write_failure 2 submit_binding` で停止 (新しい失敗記録機構を作らない)。
     停止位置は build・driver より前。
   - driver 起動を bash 配列にし、承認時だけ `--confirm-irreversible-pilot-holdout` を
     末尾に 1 個 append。`"$PY" -I -B` の文字列と Python 呼出し回数は変えない。
   - receipt の `top_keys` は**変更しない**。
3. `orchestrator/tests/test_pegasus_floor_tools.py`
   - 未承認正例: qsub argv と driver argv が現行と exact 一致。
   - 承認正例: `-v` が `IZANAGI_SUBMISSION_NONCE=<n>,IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=<n>`、
     driver argv は現行 4 引数の末尾に flag ちょうど 1 個。
   - 承認 env 不一致 (空文字 / `1` / 別 nonce / `true`) → rc=2、stage=`submit_binding`、
     driver 未起動。parameterize する。
   - **ambient env 非継承**: submitter の環境に `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=1` を
     置いて承認引数なしで実行し、qsub argv にも driver argv にも承認が現れないこと。
   - `--dry-run --confirm-...` が scheduler を呼ばず、receipt bytes が未承認時と同一であること。
   - receipt schema の key 集合が**変わっていない**ことを固定する回帰テスト。

## 7. 変異事前登録 (DW-M01)

**禁止署名** (これらが成立したら赤でなければならない):

- S1: 承認 env が未設定のとき、driver argv に `--confirm-irreversible-pilot-holdout` が現れる。
- S2: 承認 env が設定済みかつ nonce と不一致のとき、job が driver 起動まで到達する。
- S3: `submit_floor.sh` が承認引数なしで `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT` を
  `export_spec` に載せる。
- S4: `submit_floor.sh` が承認状態を ambient env から初期化する。

**通る正例** (署名に触れず緑であるべきもの): 承認引数なしの投入 (qsub argv・driver argv が
現行と exact 一致) と、承認引数ありの投入 (driver argv 末尾に flag 1 個)。

**登録変異** (negative = KILLED 期待):

| ID | 対象 | 変異 | 期待赤の単一理由 |
|---|---|---|---|
| N1 | floor_campaign.sh | driver argv の条件を外し flag を無条件 append | S1 (未承認正例が flag を見る) |
| N2 | floor_campaign.sh | 承認 env の一致比較を「非空なら承認」に緩める | S2 (不一致 parameterize が通る) |
| N3 | floor_campaign.sh | 不一致時に `write_failure` / `exit` せず続行 | S2 (driver 到達) |
| N4 | submit_floor.sh | 承認既定値を `0` から `1` にする | S3 (未承認の qsub argv に env) |
| N5 | submit_floor.sh | 承認引数の有無に関わらず `export_spec` へ append | S3 (同上) |
| N6 | submit_floor.sh | 既定値を ambient env から初期化する | S4 (ambient 非継承テスト) |
| N7 | floor_campaign.sh | 承認照合の通過後・driver 起動前に承認 env を nonce で再代入する | S1 (段 6 レビュー A 所見 1 で追加登録) |
| N8 | floor_campaign.sh | 冒頭 27 行の `unset` に承認 env を加える | S2 (同上) |

**正例変異** (過剰拒否の検出 = positive control):

| ID | 対象 | 変異 | 期待赤の単一理由 |
|---|---|---|---|
| P1 | floor_campaign.sh | env が nonce と一致していても常に `write_failure` する | 承認正例が rc=2 になる |

単一理由性は段 6 で matrix 実走時に確認する。前後に同じ入力を拒否する層が無いことは、
`orchestrator/campaign/` を 1 byte も触らないこと (driver gate は最後段にしか無いこと) から成立するが、
実測で裏を取る。

## 8. scope 外として親が持ち帰る項 (裁定パッケージ候補)

- **[T-1180-a] `submit_floor.sh` 自身の bytes 束縛** (所見 A7)。job script は動的束縛済みだが
  submitter は未束縛で、`assume-unchanged` drift が clean-tree gate を通る。
- **[T-1180-b] 実 scheduler への env 到達の実測** (所見 B1)。`qsub -v` で 2 本目の env が
  計算ノードへ届くことは本 wave では未証明。最初の実投入時に確認する。
- **人間性の機械確認** — D356 により現状の枠組みでは実装不能。外部 trust root の新設は
  ユーザー裁定事項であり、本 wave では扱わない。

## 9. 成果物影響 (DW-G05 再掲)

実装後: 人間が `submit_floor.sh --confirm-irreversible-pilot-holdout` を実行したときだけ
床値 pilot が起動でき、床値 protocol の実走証拠が初めて得られる経路が開く。
未実装なら床値実測は永久に 0 件のままで、下流の refreeze 適格性判断と certified 選択レポートの
床値欄が埋まらない。
