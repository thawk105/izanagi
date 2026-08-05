# 段 4 裁定 — [T-419] 方式 α の本番結線

親裁定。real/refuted、採否、scope、plan v2、変異事前登録を確定する。

## 1. 所見の裁定

| # | 所見 (出所) | 裁定 | 採否 |
|---|---|---|---|
| A1 | 実測済み α と本番案は取得プロトコル (target 規則・時間窓) が別物 | **real** | 一部採用 (下記 2.1) |
| A2 | `method` は K 回取得の証拠にならない | **real** | 採用 (表現の是正 + 裁定へ返す) |
| A3 | affinity mask 復元は観測者効果の復元ではない (走行 CPU・暖機の残留) | **real** | 一部採用 (順序固定のみ。process 隔離は scope 外) |
| A4 | `/proc/self/stat` は thread-group leader の stat で、pin した thread を見ていない | **real** | **採用 (must-fix)。(P4) を撤回** |
| A5 | 「set は成功、affinity は変わらない」経路がテストから抜けている | **real** | 採用 |
| A6 | 変異の赤が別 fail-closed 層で作れる (単一理由性の破れ) | **real** | 採用 (変異事前登録で再照準) |
| A7 | `min` は上向き一過性だけを吸収し、下向き 1 回で誤拒否する非対称性がある | **real** | 採用 (性質として固定。述語は変えない) |
| A8 | 親 brief の「拒否理由が method 不一致へ変わる」と login 一般化は成立しない | **real** | 採用 (brief の成果物影響を訂正) |
| B1 | 保存済み profile / receipt を再検算する consumer がプランから落ちている | **real** | 採用 (no-touch として明示 + 受入で走らせる) |
| B2 | 述語不変でも物理的な受理集合は変わる | **real** | 採用 (表現是正 + 両方向の characterization test) |
| B3 | pin 閉包は path/SHA だけでなく役割 key にもある | **real** | 採用 (no-touch 一覧へ) |
| B4 | method 不一致は必ず含まれるが唯一の拒否理由とは限らない | **real** | 採用 (表現是正) |
| B5 | (P2) は正しい — observed-only の生 K ベクトル追加も採れない | **real** | 採用 ((P2) 確定) |
| B6 | T126 は α consumer として機能していない (型不整合が 2 層) | **real** | **scope 外** (裁定パッケージへ) |
| B7 | 世代機構とは矛盾しないが g2 履歴 consumer 結線は未実装 | **real** | **scope 外** (T-506 / T-529) |

## 2. 親の裁定 (根拠つき)

### 2.1 A1 — 取得プロトコルの差は「時間窓」に集約し、identity へ載せる

実験の α 群は、randomized pin sweep の各 target の先頭 read を 5 つ束ねたもので、群の時間幅は
read cadence (50 ms 級) と per-target 反復のぶんだけ広い。本番案の 5 読みは連続実行で ~100 ms に
集中する。**機序 (reader が居る CPU は必ず busy) の除去は時間窓に依存しないが、一過性の吸収
(9/9 の should-pass) は依存する。** よって:

- 取得に**宣言された最小時間窓**を入れる。read 開始を `interval` の deadline へ揃え、
  K 読みの horizon が最低 `(K-1) * interval` になることを構造で保証する。`interval = 50 ms`
  (実験の read cadence と同位) を採り、K と併せて method identity に載せる。
  遅延 (lateness) は**拒否しない** — 遅れは horizon を伸ばす方向であり、過剰拒否を新設しない。
- **9/9 を本番手続きの妥当性根拠に使わない。** 記録では「機序の除去は移る。should-pass 率は
  本番手続きでは未測定」と書く。bnode での本番手続き検証は裁定パッケージへ返す。

### 2.2 A2 / B5 — (P2) 確定: schema key 集合は変えない

レンズ B が具体証拠を出した。必須 key を足せば旧 probe corpus と登録較正が method 比較に届く前に
schema 不正で落ち、optional にすれば exact schema を弱める。observed 側だけに足しても
calibrator が observed dict を expected へ転用する経路 (`cli.py:528-555`) で `_CLOCK_KEYS` の
exact 検査に当たる。**よって schema は変えない。** 同時に、これは証拠上の損失であると明記する:

- 成果物には「CPU ごとの最小値」と method しか残らず、**K 回取得したことの事後証拠は残らない**。
- したがって本 wave の完了を「α の実行証拠が成果物に残る」とは書かない。U-2 entry condition (i)
  は「probe 実装の完了」として満たすが、取得 transcript の凍結は別 wave (probe-output v3) として
  裁定パッケージへ返す。

### 2.3 A4 — (P4) を撤回し `/proc/thread-self/stat` にする

`sched_setaffinity(0, ...)` は呼び出し **thread** に効き、`/proc/self/stat` は thread-group leader の
stat である。worker thread から probe すると別 task の走行 CPU を検査して誤拒否・誤裏付けになる。
親の (P4) は誤りだったので撤回する。検査は `/proc/thread-self/stat` を読み、
読みの直前・直後の両方で target と一致することを要求する。

### 2.4 A3 — 順序だけ固定し、process 隔離は scope 外

affinity 復元後も走行 CPU・cache・P-state は戻らない。提案された「短命 helper process への隔離」は、
attest する主体が親 process でなくなるという意味変更を伴うため本 wave では採らない。採るのは:

- 巡回 (pin → K 読み → 復元) を単一 helper に閉じ、**TSC 測定は復元完了後に行う**順序をコードで固定する。
- 復元は「試みた」ではなく「元集合と exact 一致を再取得で確認」まで要求し、失敗は profile を返さず拒否。
- 残留 (暖機の持ち越し) は既知限界として記録し、ablation は裁定パッケージへ返す。

### 2.5 A7 / B2 — 受理集合の変化を性質として固定する

述語 (`∀i. M[i] ∈ B`) は変えないが、`M[i] = min_k S_k[i]` なので単読みに対する受理集合とは違う。
非対称性 (上向きは K−1 回まで消える / 下向きは 1 回で残る) を仕様として明記し、両方向を
characterization test で固定する。**述語自体は変えない** (変えるなら R-1 の再裁定が要る)。

### 2.6 scope 外として裁定パッケージへ返すもの

B6 (T126 の 2 層型不整合)、B7 (g2 履歴 resolver 結線)、A3 の process 隔離と暖機 ablation、
A1 の bnode 本番手続き検証、A2 の取得 transcript (probe-output v3)。いずれも本 wave では実装しない。

## 3. plan v2 (段 5 への確定指示)

段 2 プランを土台に、次を差し替え・追加する。

1. `EFFECTIVE_CLOCK_ALPHA_K = 5`、`EFFECTIVE_CLOCK_ALPHA_INTERVAL_NS = 50_000_000`、
   規則 ID に選択規則と最小 interval を含め、method は K・interval・規則 ID から組み立てる。
2. 走行 CPU の検査は `/proc/thread-self/stat`。読みの直前・直後の両方。
3. pin 後に `get_affinity()` を再取得し `== {target}` を exact 検査する (A5)。
   この検査、pre 検査、post 検査は**独立に消せる 3 箇所**として書く (A6 の単一理由性)。
4. K 読みは deadline 方式で `interval` 以上の間隔を空ける。lateness は拒否しない。
5. TSC 測定は affinity 復元後。順序をコードで固定する。
6. no-touch 一覧 (触らない): `schema_v2.py` の clock key 集合、`execution_guard.py` の comparator、
   `env_contract.py` の pin と世代、登録済み較正 bytes、`FROZEN_MANIFEST`、
   保存済み receipt を再検算する `silo_ladder_rung1.py` / `s8b_ratified_freeze.py` /
   `s8b_oracle_report.py`、旧 v1 probe corpus の replay test。
7. テストは段 2 の表に加え、A5 (set 成功・mask 不変)、A6 (直接 parser への fallback spy)、
   A7/B2 (4/5 高値の受理・1/5 低値の拒否)、interval の下限、TSC 順序を追加する。

## 4. 変異事前登録 (DW-M01)

すべて `orchestrator/campaign/env_attestation.py` の新規領域を対象とし、期待 kill は新規テストで取る。
既存 330 件はこの面を検出しないことを段 1 で実測済みなので、検出力はすべて純増分に帰属する。

| ID | 変異 | 期待 |
|---|---|---|
| M01 | method 定数を `"proc-cpuinfo"` へ戻す | kill (identity test) |
| M02 | K を 1 にする | kill (identity + reader-outlier 受理 test) |
| M03 | 巡回を止め全読みを同一 target へ pin | kill (distinct target 検査 + reader-outlier) |
| M04 | 位置ごと `min` を `max` にする | kill (reader-outlier 受理 test) |
| M05 | pin 後の `get_affinity() == {target}` 検査を削る | kill (set 成功・mask 不変の負例) |
| M06 | 読み直前・直後の走行 CPU 検査を削る | kill (wrong reader 負例) |
| M07 | `set_affinity` 失敗時に単読みへ fallback する | kill (直接 parser spy の負例) |
| M08 | read 間の CPU 集合・identity 一致検査を削る | kill (drift 負例) |
| M09 | `finally` の復元を削る | kill (restore 負例) |
| M10 | affinity が K 未満のとき K を切り下げる | kill (K 未満拒否の負例) |
| M11 | 帯外がちょうど 1 CPU のとき受理する (γ 化) | kill (persistent outlier 拒否 test) |
| M12 | **正例 (過剰拒否検出)**: K 読みの MHz ベクトルが完全一致することを要求する | kill (静穏 fixture の受理 test) |

単一理由性: M05/M06 は 3 検査を独立に書かせるため互いに mask しない。M07 は runtime spy と
直接 parser spy の両方を張り、fallback が実際に profile を返すところまで負例を閉じる (A6)。
M08 は reducer の純関数テストへ再照準する。

## 5. 成果物影響 (DW-G05、A8/B4 を反映した訂正版)

- **実装する場合:** certified 受理集合は閉鎖のまま変わらない。live probe と登録 g1 較正の突合せは、
  取得が成功すれば `effective_clock.method` を**必ず含む** comparison failure、取得が失敗すれば
  `strict attestation probe failed` になる (どちらか一方に確定はしない)。U-2 entry condition (i) が
  実装として成立する。
- **実装しない場合:** U-2 は着手不能のまま。再取得しても観測者効果を焼き直した較正しか作れず、
  certified campaign を再開できない。
