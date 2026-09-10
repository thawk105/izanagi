# [T-782] 査読済み spec の凍結発行 — 裁定パッケージ (2026-08-26)

本 wave は **実装差分ゼロ**で終える。D840 の向き (b) は不採用にせず維持し、
新事実を添えてユーザー再裁定へ返す。一次資料は `verbatim/` 配下。

- `verbatim/s2-plan.md` — 段 2 のプラン起草 (codex, read-only)
- `verbatim/s3-consult-sol.md` — 段 3 レンズ「正しさ境界」
- `verbatim/s3-consult-luna.md` — 段 3 レンズ「整合・実効性」
- `verbatim/s4-adjudication.md` — 段 4 の親裁定 (所見ごとの real/refuted と採否)

## 1. なぜ実装しないか

**この wave が触れる全機能は、今日発火しない gate の下流にある。** `DW-G04` は
「条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を brief に書ける場合だけ
実装する。書けなければ設計メモに留める」と定める。書けなかった。

決め手は 3 つある。

1. **D959 (2026-08-26、本 wave 走行中に main へ着地) の順序規定。**
   8b の閉塞を依存の層として記録し、(e) schedule authority の無条件 raise —
   本 wave の対象そのもの — を「(a) に従属する下流症状」と位置づけ、
   **順序を入れ替えて先に解除してはならない**と明記した。
   同時に「(f) 共有 8b ratified freeze だけは (a) と独立に進められる別線」とも書いている。
2. **候補 bytes を読む production consumer が repo 内に 1 つも無い** (段 3 luna L3)。
   manifest builder・driver・report・judge・verdict はすべて固定 path の bytes を
   `load_approved_spec` で読む。producer の戻り値や標準出力を読む呼び手は存在しない。
   D841 が名指しした「受領証はあるが誰も読まない」型になる。
3. **凍結しようとしている値が生成 site 依存である** (段 3 luna L7)。
   `src_token` は `source_digest` 自身が cxx / 環境依存と明記する値で、
   生成した site と実走 site が違えば実走時の再実体化と一致せず `binding-refused` になる。
   「先に凍結する」ためには、どの site の identity を凍結するかを先に決める必要がある。

実装しないことの成果物影響は **1 bit も変わらない**。承認 pin は `None`、durable spec は 0 件、
official manifest は 0 件、certified 選択・レポート・台帳の値はすべて不変である。
実装した場合に増えるのは休眠 capability と休眠 test state だけである。

## 2. D840 の前提のうち、今日成立しないもの

D840 の理由文は 2026-08-11 時点の状態記述を引き写している。

- 「現状は鍵の一致しか検査していない」は**偽**。`verify_manifest` は schedule の cell 集合が
  freeze の holdout × configuration の完全積と一致しなければ拒否し、承認済み spec から
  schedule を再生成して完全一致を要求する。D840 が名指しした攻撃
  (各 holdout を 1 構成へ間引いて唯一の勝者を作る) は既に塞がっている。
- 択 (b) の機構自体も 2026-08-11 に実装済みである
  (`orchestrator/campaign/s8b_oracle_spec.py`: strict schema、承認 pin、指紋照合 loader、
  snapshot validator)。未了は durable 発行だけだった。
- D840 は **D480 (2026-08-17) に言及していない**。D480 は
  「durable な reviewed spec を発行して承認 SHA を記入する」を却下済みで、
  却下理由に挙げた前提のいくつかは今日も成立している。

## 3. ユーザー再裁定へ返す論点

### Q1 — D840 の逐語をどう読むか

D840 は「CLI 側は凍結 spec の指紋照合だけを行い、**内容の再導出や束縛検査を持たない**」と書く。
しかし現行実装は既に内容を再導出している。**逐語どおり実装すると、動いている正しさ検査を
撤去することになり、絶対規律 2 に反する。**

親の推奨: **「消費側へ *新たな* spec 解釈を足さない」と読む。** 既存の再導出は D302 が
「hash は識別子にすぎず、承認は内容の再導出を伴う」と裁定済みであり、撤去は受理集合の拡大になる。
親が裁定文の逐語を黙って弱めるのは禁じられているため、読み替えの可否を返す。

### Q2 — 順序: T-782 と (f) 批准凍結のどちらを先に動かすか

D959 は T-782 の対象を下流症状と位置づけ、順序の入れ替えを禁じた。同時に (f) を独立線と明記した。

親の推奨: **T-782 は (f) の後へ送る。** (f) が発効すれば binding identity の権威が定まり、
生成 site 依存も批准された値で解決し、consumer 不在も 6 cell manifest の配線で埋まる。

### Q3 — 凍結する bytes の再現性

凍結は実走する計算ノード上で行い、spec に生成 site を記録するのが筋だが、
これは schema の追加であり D355 の v1 据え置きに触れる。(f) と同じ変更単位で扱うのが妥当。

### Q4 — 既存設計資産の起点化

`output/insights/2026-08-12_t499-spec-producer-design/verbatim/s2-plan.md` に、
T-499 の段 2 が producer 設計を既に書き終えている — `preview` と `install-approved` の分離、
create-only、任意 `--output` を持たせない、既存 writer の安全性を踏襲、まで。
実装 wave はこれを起点にすべきで、再設計から始めない。

### Q5 — dev-wave docs の byte 予算が満杯で、実測に基づく手順改善が入らない

段 8 で 2 件の改善候補を出したが、どちらも予算に阻まれた。

- 段 2 プラン起草の節へ「親 brief の前提実測に反証があれば plan にも出させる」を足す案。
  本 wave で実際に起きた (親の一般化を段 2 のプラン子が覆した) ため実測の裏づけがあるが、
  L1.5 層の unique footprint が予算ちょうどで、144 bytes の追加が超過した。
- 凍結 bytes の pin 閉包の節へ「検査値そのものを literal で持つ側」という 3 番目の検索方向を
  足す案。当該 L2 節は 997 bytes で単節予算 1000 bytes に対し余地が 3 bytes しかない。

自己改善契約は「予算のために安全義務を削除・弱化してはならない」「予算値を上げる変更は
通常の自己改善に含めず、理由付きの独立審査対象にする」と定めるため、どちらも実装していない。
恒久対応の記述自体は failures 台帳の再発追記に残っている。

親の推奨: **予算値の見直しを独立審査として 1 度立てる。** 実測に基づく改善が 2 件連続で
入らなかったことが、予算が現に効いている証拠である。

## 4. 実装 wave へ引き継ぐ既知の穴 (段 3 が挙げ、親が実在確認した)

| 穴 | 実在確認 |
|---|---|
| v1 freeze の trust root 照合を producer が迂回しうる | `V1_FREEZE_SHA256` が `s8b_ratified_freeze.py` に実在 |
| canonical path を symlink にすると査読 diff 外の bytes を承認済みにできる | loader が `read_bytes()` で link を辿る |
| 「pin はあるが file が無い」状態を現行検査が受理する | 現行 zero-file 検査は pin を見ない |
| hash が合っても generator source が drift した spec を lifecycle が緑にする | D480 が数日単位の失効を実測済み |
| 新規 test file は自走 harness か allowlist が無いと偽緑ガードで赤 | `test_plain_runner_coverage.py` が実在 |
| 既存 fixture の assembler と producer が二重化し、交差検査が serializer にしか効かない | `s8b_oracle_spec_fixture.py` の `make_reviewed_spec` |

## 5. 各軸を拘束する層 (実装 wave の設計入力)

「導出できる / できない」の二分ではなく、**どの層が値を拘束するか**で整理するのが正しい。

| 軸 | spec validator | driver 実走 |
|---|---|---|
| holdout / configuration | freeze と突合しない | freeze の完全積と突合 |
| generator_versions | live source bytes と一致必須 | — |
| reps / extime / verify / screening / bench_max_rounds | 承認凍結値へ完全一致必須 | — |
| clocks / contract_sha256 / env_tag / ccbench_pin | 型のみ | env 契約と完全一致必須 |
| allowed_excluded_reasons | 型のみ | report の受理集合を決める |
| n / master_seed / block_sizes / campaign_ids | 型と整合のみ | — |
| binding_identity | 内部整合のみ | 再実体化と完全一致必須 |

承認凍結の除外理由 4 行は **floor protocol の権威**であって oracle spec の権威ではない。
oracle spec の承認経路 positive fixture は別の値を意図的に通している。
