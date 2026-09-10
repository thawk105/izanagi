# [T-434] cap-lift receipt と consumer 結線 — 設計案 v2 (blocked design memo)

```
status: PROPOSED_UNRATIFIED        # 提案。ユーザー裁定を経ていない
machine_effect: NONE               # 本 wave の実装差分ゼロ。機械受理集合・凍結 bytes・proof chain 不変
MAX_APPROVED_GENERATIONS: 1        # 不変 (D114)
depends-unratified: 本文書の設計択一 1〜10, [T-433] 意味的充足契約, V1 (NOT_CLAIMED の射程), [T-435] 再事前登録
```

これは D150 決定 (6)(c)「承認 receipt が無い」への設計回答の**案**であり、規範ではない。
設計済み ≠ 裁定済み ≠ 結線済み。cap-lift の現況は「発行可能な receipt が存在しない」であり、
前提 10 件 (D121 決定 (7)) のうち充足は P10 のみ。段 4 裁定は `s4-adjudication.md`、
攻撃済み初稿は `s2-draft.md` (履歴)。

## 0. 位置づけ — blocked design memo (DW-G04)

発火条件を満たす既存 artifact path・計測 ID が 1 件も現存しないため (D150 決定 (6)(c))、
本設計は実装 wave へ直送しない。**再開条件** (すべて成立するまで実装を起票しない):

1. 本文書の設計択一 1〜10 のユーザー裁定。
2. [T-433] (P6 意味的充足契約) と V1 (`NOT_CLAIMED` の射程) の裁定 — P6 field の schema 凍結に必要。
3. [T-435] (8c 再事前登録) の実施 — 事前登録面の結線順序の前段。
4. 前提条件 P1〜P9 のうち、witness が束縛すべき実 artifact を生む実装の land
   (各 P の評価器・正負 calibration が実在しない間、receipt は発行不能のまま)。

## 1. receipt schema v1 案

strict canonical JSON。未知 key・重複 key・非 UTF-8・非正準 bytes を拒否。

| field | 型・語彙 | 値の出所 | 検証法 / 限界 |
|---|---|---|---|
| `schema_version` | const `izanagi-cap-lift-receipt/v1` | 本設計の裁定後の新 D | exact 一致。未知版は拒否。**v1 の凍結は [T-433]/V1 裁定後** (P6 表現が依存) |
| `scope` | const `p3-autonomous-workload-trial` | D114 の 3 入口 | 保証射程は「3 入口の `generations` 引数」**のみ**。D114 の保証外 (drive/providers/preview 注入、`drive_iteration()` 直接反復、TOCTOU race。`docs/decisions.md:5390-5398`) は逐語で継承し、receipt はそれらを承認しない |
| `decision` | const `APPROVED` | 発効 commit | 文字列は自己申告であり単独では証拠でない。§3 の発効 topology と組で検証 |
| `target_revision` | `^[0-9a-f]{40}$` full commit OID | 承認対象 revision | **exact-pin (既定案)**: runtime HEAD の tree = 承認 revision の tree を要求。descendant 再利用は択一 9 |
| `approved_max_generations` | exact int、`2..MAX_GENERATIONS` (絶対上限 10、`p3_autonomous_workload_trial.py:133`) | 人間裁定 | 実効 cap は「receipt が無ければ literal 1、有れば receipt 値」からだけ導出。**対象 revision の `MAX_APPROVED_GENERATIONS` 定数値との一致検査は証拠に数えない** (申請側自己一致になるため。段 3 所見 A8) |
| `prerequisite_statuses` | 長さ 10、`P1`〜`P10` を一度ずつ | 独立評価 (下記) | receipt/witness 間の写し一致は**改竄検出**であって充足証拠ではない。status は typed evidence から独立評価器が再導出する。評価器が実在しない P は `SATISFIED` と書けない (発行不能) |
| P10 の status | `HUMAN_RATIFIED` の別型 (bool 系に畳まない) | ユーザー裁定 3 点 (予算値・origin authority・軸 (iii)) | 機械は裁定文の存在・bytes 同一性までしか検証できないと明記 |
| P6 の status | **provisional / opaque** | [T-433] + V1 裁定 | D138 4 値型と D150 の 2 語彙 (`NOT_IMPLEMENTED`/`NOT_CLAIMED`) を参照するが、**global receipt に単一 P6 status を凍結できるかは V1 (global 免責か per-run gate か) に依存**。`semantic_contract_hash`・claim scope・構成 identity を予約 field とし、v1 凍結は T-433 後 |
| `ruling_ref` | 構造化裁定 record | cap-lift を承認する新 D | D 番号 + blob hash だけでは「その D がこの revision・cap を承認したか」を機械判定できない。record に decision kind / target revision / witness hash / cap / policy version / supersedes / 境界テスト manifest を構造化して束縛する |
| `witness_sha256` | `^[0-9a-f]{64}$` | witness manifest | **v1 で確定するのはこの field の存在と形式のみ**。manifest の strict schema は各 P の実 artifact・評価器が実在してから確定する (DW-O13。現存しない path を schema に書かない) |

`approved_by` 文字列・自由記述 `reason` は置かない (自己申告になるため)。

## 2. 実効 cap の導出規則

```
effective_cap = 1                                  (receipt 指定なし)
effective_cap = min(receipt.approved_max_generations, MAX_GENERATIONS)   (検証済み receipt 指定あり)
```

- `MAX_APPROVED_GENERATIONS = 1` の literal は **no-receipt fallback として恒久維持**。
- budget=1 の運転は receipt 不要のまま (現行受理を変えない)。budget=1 で receipt を指定したら
  曖昧さ回避のため拒否。
- `generations > 1` は、検証済み receipt が無い限り**常時拒否**。1 への silent downgrade はしない。
- 依存順条項 (段 3 所見 A1): 意味評価器・独立検査・境界変異テストが land するまで、
  receipt reader / consumer 結線が先に land しても `generations > 1` は常時拒否のまま。
  「形式検査だけ通る receipt」で cap が開く実装順を禁止する。

## 3. 発効 — 人間承認の topology と trust root の限界

1. 実装 wave (裁定後) が candidate revision `G` に schema・validator・境界テスト・consumer 結線を置く。
   この時点で receipt は存在せず、多世代要求は全入口で拒否される。
2. 人間が `G` を検分し、子 commit `A` で receipt 1 ファイルだけを追加する。
   `A` は非 merge・親がちょうど `G`・diff は receipt の create-only 追加のみ・
   commit message は `AI-Agent: none` をちょうど 1 回持つ。
3. receipt / witness は content-addressed + create-only。同一 path の別 bytes・削除後再導入・
   複数導入 commit は拒否。改訂は新 witness + 新 receipt の発行で行う。

**trust root の限界 (明記義務):** この topology + trailer は「push は人間だけが行う」という
**運用上の trust root** に依存し、暗号学的な本人確認ではない。悪意ある committer は
threat model 外である。署名済み commit + 許可鍵 registry へ強化するかは択一 8。

## 4. consumer 結線 6 面 (アンカーは段 3/4 で検証済み)

共通 envelope: `{receipt_raw_sha256, receipt}` (canonical bytes) を一度だけ定義し、
面ごとに「envelope を持つ / SHA のみ持つ」を固定する (同名二義化の禁止、D75)。

| 面 | 現状 (file:line) | 結線案 | 不在・不整合時 |
|---|---|---|---|
| 1. runbook | `docs/phase3-s8c-autonomous-trial-runbook.md:104,118,131,150` | 多世代コマンドだけ `--cap-lift-receipt-sha256` 必須。事前確認・実行・事後再検証の 3 箇所で同 SHA | 開始しない。silent downgrade せず明示エラー。事後判明は protocol-invalid |
| 2. 事前登録 | **正本 = `docs/phase3-8c-preregistration.md`** (69–72 行が多世代化の 3 条件を既記)。`docs/phase3-main-experiment.md` + S-1 freeze は **no-touch** (段 3 所見 B3 で初稿の取り違えを訂正) | [T-435] の再事前登録に要求事項を渡すのみ (T-434 は文書改訂を所有しない)。順序 = **T-435 再事前登録 commit → その子孫で G → A**。文書は特定 receipt hash を自己参照せず「対象 revision を人間 receipt が承認していること」を条件化 | 多世代 cell は事前登録不適合。後付け receipt・1 世代への格下げ流用を認めない |
| 3. journal | `AttemptJournal` append-only (`p3_autonomous_workload_trial.py:461`)、`run-start` (`:1624`)、event 閉集合 (`autonomous_trial_completeness.py:40`) | 新 event を増やさず `run-start.cap_lift_receipt` に envelope。budget=1 は field 不在、budget>1 で必須 | run root / journal 作成前に拒否。開始後の bytes 消失・変異は terminal report 非公開 + 不完全試行として保持 |
| 4. report | supervisor report 構築 `p3_autonomous_workload_trial.py:1168`、completeness 後の書出し `:1201` | schema version を上げ budget>1 で top-level に journal と同一 envelope (exact 一致) | `_write_json_atomic()` に到達させない。保存済み report の独立再検証で receipt 消失・stale なら不受理 |
| 5. 層 3 | budget 挿入 `p3_autonomous_workload_trial.py:510-518`、search_config 消費 `layer3_report.py:416-418,434-435,459`、v3 schema に field なし (`layer3_schema.json:5`) | `search_config` に `cap_lift_receipt_sha256` (campaign ID preimage へ束縛) + Layer 3 v4 で envelope 必須。**v2/v3 は明示的 legacy 分岐で読み続ける** (現行は current=v3/legacy=v2 の一分岐、`layer3_report.py:39,190-200`)。**trust root は campaign `output_root` と独立の定数** (production = repository root 固定。exploration root を authority にしない、`:322` 対策) | renderer は `Layer3ReportError` で create-only 出力を作らない。歴史 v2/v3 は多世代承認の証拠に使わない |
| 6. producer + completeness | 共通 validator `p3_autonomous_workload_trial.py:249`、3 入口 `:1245,:1554,:1740`、completeness 2 gate `autonomous_trial_completeness.py:438,:1030` | CLI は receipt SHA 引数、2 つの programmatic API も同引数を明示必須。環境変数・自動探索・provider 例外なし。3 入口は副作用前に同じ pure verifier。completeness は保存 SHA から独立再読 | `generations>1` は常時拒否。定数 monkeypatch だけでは開かない (§2 の導出規則) |

## 5. 実装 wave への引き渡し条件 (裁定後)

- **D96**: この結線は「裸の定数引上げで開く集合」を receipt 必須へ**狭め**、同時に
  「検証済み receipt による 2..N」を**新設**する受理集合変更である (基準集合を明記して二方向を
  書き分ける — 初稿 Q2 の「狭めるだけ」は撤回済み)。新 D + 境界テスト同時更新が必須。
- **D114 決定 (1) の明示 supersede**: 同決定は解除手続を「この定数 1 個と境界テストの同時変更だけ」
  と定める (`docs/decisions.md:5331-5333`)。receipt/witness/consumer を新たな必要条件にする新 D は、
  この逐語を明示 supersede し遷移契約を書かない限り効力を持たない (D150 決定 (2-b) と同型)。
- **変異事前登録** (DW-M01): 欠落 receipt・偽 hash・別 revision 流用・P4 非適用申請・
  P6 `NOT_IMPLEMENTED`・wrong parent・AI trailer 付き発効 commit・witness drift の負例に加え、
  **過剰拒否を検出する正例** (valid receipt + 全前提充足で 2 世代が通る) を登録する。
  既存テストの追随: `test_p3_autonomous_workload_trial.py:644` 等の定数 monkeypatch は
  receipt fixture 必須へ更新、`test_autonomous_trial_completeness.py:808` は
  「上限超過を拒否する負例」として維持 (受理テストと誤読しない)。
- Layer 3: v4 generator + v2/v3 legacy reader + 三版の正負 reader テスト。

## 6. 設計択一 (裁定パッケージ — ユーザー裁定を求める 10 件)

| # | 問い | 選択肢 | 推奨 |
|---|---|---|---|
| 1 | receipt と証拠の構成 | (a) 単一巨大 receipt / (b) 小さい人間 receipt + content-addressed witness 分離 | **(b)** 人間判断と機械証拠の分離。consumer には小さい envelope だけ運ぶ |
| 2 | 発効の形 | (a) `approved_by` 文字列 / (b) 発効 commit topology (`A` 非 merge・親一意・create-only・`AI-Agent: none`) | **(b)**。(a) は自己申告で不採用。暗号強化は択一 8 へ分離 |
| 3 | receipt の選択 | (a) latest/最大 cap の自動選択 / (b) caller が SHA 明示 + 固定 path 導出 / (c) active pointer 連鎖 | **(b)**。暗黙再活性化を避ける。(a) 不採用、(c) は複数 policy が要るときだけ再検討 |
| 4 | journal 結線 | (a) `run-start` に envelope / (b) 新 event `cap-lift-admission` | **(a)**。event 閉集合と開始順序を変えない |
| 5 | 層 3 表現 | (a) search_config の SHA のみ / (b) campaign identity 束縛 + v4 top-level envelope | **(b)**。材料レポート単体で承認対象・cap・status を監査可能 |
| 6 | `NOT_CLAIMED` 構成の cap-lift 可否 | (a) T-434 で先取り / (b) schema は語彙を保持し V1 裁定まで admission 拒否 | **(b)**。D150 決定 (6)(b) の未裁定を尊重、fail-closed 維持 |
| 7 | 事前登録の順序 | (a) receipt 発行後に文書追記 / (b) T-435 の再事前登録 commit → 子孫 G → 発効 A | **(b)**。自己参照回避 + [T-435] の所有権尊重。(a) は不採用 |
| 8 | 発効の trust root | (a) 運用 trust root (「push は人間」) + 検証不能範囲の明記 / (b) 署名済み commit + 許可鍵 registry 新設 | **(a)** を v1 とし、(b) は必要と裁定されたら独立 wave。(b) は新機構であり盛らない規律と衝突しうる |
| 9 | revision 束縛と失効 | (a) exact-pin (runtime tree = 承認 revision) + 改訂は新 receipt 発行のみ / (b) descendant 再利用 + closure 機構 + revocation tombstone | **(a)** を v1 に。 (b) の closure は申請側定義になり検出穴が残る (段 3 所見 A5/A10/B13)。revocation は 6 面外の追加 policy であり、必要になったら独立裁定 |
| 10 | 注入 seam の扱い | (a) D114 carve-out を逐語維持し scope 外と明記 / (b) admission record に provider/build mode を束縛して拡張 | **(a)** を v1 に。注入閉鎖は P5 系 (U-1 裁定済み wave) の所有。receipt を「全プロジェクトの多世代承認」と名乗らせない |

## 総括

cap-lift receipt は「人間が発効する、機械 admission gate の policy input」であり、
発行可能になる条件 (評価器・実 artifact・T-433/V1/T-435 裁定) が揃うまで blocked design memo に留める。
v1 の骨格 = 小 receipt + witness 分離、exact-pin、receipt からだけの cap 導出、
6 面への同一 envelope 投影、D96 + D114 明示 supersede を実装 wave の必須条件とする。
本 wave の機械的効果はゼロで、`MAX_APPROVED_GENERATIONS = 1` は不変である。
