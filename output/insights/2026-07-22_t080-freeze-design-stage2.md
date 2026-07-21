# [T-080] freeze 族恒久設計 第 2 設計段 wave の逐語凍結 (2026-07-22)

工程: 親 brief (P1..P5) → codex 草案 4 本並列 (A=topology/lineage、B=observation/統計/registry、
C1=closure/pin、C2=所有表+変異登録。gpt-5.6-sol / max / read-only) → 敵対相談 2 本並列
(X=正しさ境界 25 所見 NO-GO、Y=整合・実効性 28 所見 NO-GO) → 親裁定 (rulings-v2 — U-A1 のみ
ユーザー裁定へ、J1..J28 統合裁定) → codex 統合起草 (89KB) → 親正本化 + 第 1 段への波及適用 →
敵対レビュー 2 本並列 (R1 15 所見 NO-GO、R2 14 所見 NO-GO) → codex fix (親裁定 17 項) + 親ハンク
追加訂正 → fix 検証 (26/29 解消、残 7) → 親が残 7 反映 → 最終チェック (残 2) → 親反映 → 最終確認。

主要な親裁定: レビュー間衝突 (legacy g0 adapter の方向 — R1「full verifier 委譲」vs R2「raw root +
strict parse のみ」) は R2 を採用 (現物 3 legacy が dangling/drift で委譲は g0 構築不能)。
final check の所有は W-e 実装 + W-f 実行 (42 node は W-e land 時点で全 file 実在の算術による)。
42-node manifest は「実在 file のみ読む reader + W-f final check で完全性固定」で wave 単独 green と
両立。成果物正本 = docs/freeze-permanent-design-s2.md、第 1 段への波及は同 doc §S2-12 (適用済み)。

以下、各段の逐語。

---

# 段 1: 親 brief

# brief — [T-080] 第 2 設計段: freeze 族恒久設計 §13 の exact 化 + 変異事前登録

## scope

`docs/freeze-permanent-design.md` §13 の残課題 10 項目 (1, 2, 2b, 3, 4, 5, 6, 7, 8, 9) を、実装 wave
W-0..W-f が一意に実装できる exact 度まで仕様化する。成果物は設計 doc (第 2 設計段パッケージ)。
コード・テスト・凍結成果物は 0 byte 変更 (設計 wave)。

## 確定済みユーザー裁定 (動かせない)

- R1..R16 全項が推奨案で承認済み (2026-07-22、R7 = (b) 生成基準 tree H_gen の blob 照合)。
  §2..§10 の骨格は確定。第 2 設計段はその具体化であり骨格を変えない。骨格と矛盾する事実を
  見つけたら、設計を勝手に変えず所見として親へ返す
- [T-068]/[T-077]/[T-078] は開いたまま (R10/R11/R12 の処理形のみ確定)。本 wave で閉じない

## 不変条件

- exact schema・gate 記述は実物 (現物 JSON / 現行コード) を照合してからのみ書く (D75 (4) 恒久教訓。
  第 1 段では親合成の誤り 3 種がこれで混入した)
- 正しさゲートを緩めない (規律 2)。受理集合を広げる選択は §14 損失表への追記とセットでのみ許す
- 実測済み前提 (2026-07-22 本 wave 再確認): 3 freeze raw sha256 = 354f4b87 / 203de36b / 315b1eb8、
  FROZEN_MANIFEST 8 件、_TRANSITION_V1_TO_G1 13 pointer、V1_FREEZE_SHA256 = holdout 現物一致

## 親の provisional 裁定 (攻撃対象 — 一件ずつ否認/採用を返せ)

- (P1) 成果物の置き場: 新 doc `docs/freeze-permanent-design-s2.md` を新設。正本 §13 は状態行 +
  s2 doc へのポインタに更新し、裁定済み本文 (§1..§12, §14) は変更しない。docs/README.md の地図へ
  登録し、tools/check_docs.py の LIVING_DOCS 追加は実装 wave 送り (第 1 段 doc と同じ扱い)
- (P2) 起草分割: A = topology/lineage 系 (§13-1: lineage/approval/pointer/receipt schema、
  §13-2: bundle digest 符号化、§13-5: §7-G guard)、B = observation/統計/registry 系 (§13-2b:
  observations/analysis_results、§13-3: WAL/report/judge/calibration 伝播、§13-4: check-ID registry +
  required node manifest 初期集合)、C1 = §13-6: pre_oracle_head 内容 pin 化 + §13-7: source closure
  宣言確定。A/B/C1 は並列起草可。C2 = §13-8: §9 再列挙 + W-0..W-f exact ファイル所有表 +
  §13-9: 変異事前登録 — C2 は A/B/C1 の確定後
- (P3) 変異事前登録の対象は大半が未実装の新 module — 登録は「仕様レベルの変異点 + 無効化時に赤く
  なる単一理由 + 検出するテスト (仕様上の名前)」で行い、B-057 の単一理由性のコード実測確認は各実装
  wave 開始時の再確認として受入条件へ落とす。既存コードに対する変異 (W-0 hook、W-d consumer) は
  本 wave でコードを読んで手前検査の不在まで確認する
- (P4) 完了条件: field 名・型・件数・一意性・拒否規則・エラー reason code の全列挙。「実装時に
  決める」を残す場合はその旨と決定権者を明記した項目のみ許す
- (P5) 裁定境界: 骨格の具体化の範囲内 (符号化詳細、check-ID 命名、registry 初期集合等) は親裁定で
  確定し worklog へ記録。受理集合・承認境界・機械防壁を変える択一だけユーザー裁定パッケージへ返す

## 成果物の形

`docs/freeze-permanent-design-s2.md` (第 2 設計段パッケージ) + 正本 §13 状態更新 + docs/README 登録 +
worklog / insights (逐語凍結) / decisions (D76)。commit は親のみが行う。

## 関連所在 (実測済み)

- 正本: `docs/freeze-permanent-design.md` (§13 が対象、§3..§8 が骨格、§11 が裁定)
- 現物 JSON: `output/s1-freeze/known_axes_freeze.json`、`output/s1-freeze/measurement_freeze.json`、
  `output/s8b-freeze/holdout_freeze.json`
- コード: `orchestrator/campaign/` の s1_known_axes_freeze / s1_measurement_freeze / s1_stats /
  s8b_holdout_freeze / s8b_ratified_freeze (許可表 :115、承認 allowlist :1160 付近) /
  s8b_selector_freeze (pre_oracle_head) / s8b_freeze_io / wal、`orchestrator/tests/`
  の test_frozen_artifacts / conftest、`hooks/guard_write.py` (:91-94)
- 裁定記録: worklog 2026-07-22 (3)、decisions D75。現行 ratified-v2 の receipt/approval 機構は
  s8b_ratified_freeze.py が正本 (新設計はこれと「同等以上」が下限)

---

# 段 2a: codex 草案 A (topology/lineage)

# 草案 A — freeze 族恒久設計・第 2 設計段

> 対象: §13-1、§13-2、§13-5  
> 照合方法: 現行 JSON、Git object、現行 Python、hook 契約の静的照合のみ。テスト実行結果は主張しない。  
> 新設 record の field は「現物に既にある」とは扱わない。本草案の schema 自体を新設時の正本とし、現行 record は下限・命名根拠としてのみ用いる。

## 0. 実物根拠索引

- **E1 — 新 family 共通 field**: [freeze-permanent-design.md §3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:92)
- **E2 — loader / reason code / `H_v`**: [freeze-permanent-design.md §4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:164)
- **E3 — G / `H_gen` / tree 束縛**: [freeze-permanent-design.md §6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:221)
- **E4 — G/R/literal×2/A/X 骨格**: [freeze-permanent-design.md §7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:250)
- **E5 — g1 receipt / 旧8＋新4**: [freeze-permanent-design.md §8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:293)
- **E6 — 現行 governance schema**: [s8b_ratified_freeze.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:71)、[同:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:100)
- **E7 — 現行 canonical JSON**: [s8b_ratified_freeze.py:368](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:368)
- **E8 — Git hardening / immutable introduction**: [s8b_ratified_freeze.py:306](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:306)、[同:456](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:456)
- **E9 — 現行 A diff allowlist**: [s8b_ratified_freeze.py:1160](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1160)
- **E10 — 現行 active 解決**: [s8b_ratified_freeze.py:1185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1185)
- **E11 — 現行 transition 13 / 9 pointer**: [s8b_ratified_freeze.py:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:110)
- **E12 — legacy holdout 実物**: [holdout_freeze.json](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s8b-freeze/holdout_freeze.json:1)
- **E13 — legacy known 実物**: [known_axes_freeze.json](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:1)
- **E14 — legacy measurement 実物**: [measurement_freeze.json](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/measurement_freeze.json:1)
- **E15 — `FROZEN_MANIFEST` 8件**: [test_frozen_artifacts.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:25)
- **E16 — `guard_write` の無条件拒否**: [guard_write.py:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/hooks/guard_write.py:86)
- **E17 — hook の保証境界**: [hooks/README.md:49](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/hooks/README.md:49)、[同:183](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/hooks/README.md:183)
- **E18 — search 列挙・exact exemption**: [s8b_holdout_freeze.py:179](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:179)、[同:297](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:297)

## 1. 親 brief の P1..P5 判定

| 項目 | 判定 | 理由 |
|---|---|---|
| P1 | **条件付き採用** | s2 doc 新設、正本 §13 からの pointer、docs 地図登録は妥当。`tools/check_docs.py` はコードなので実装 wave 送りでよい。ただし既存 §12 は `docs/README.md` を W-f 所有としているため、C2 の exact file table で「今回の設計 wave 済み」に再分類すること。 |
| P2 | **一部否認** | A/B/C1 の「並列起草」は可能だが、独立確定は不可。measurement transition は B の `cells` / source pointer schema、known transition は C1 の source-record/closure pointer 集合に依存する。A/B/C1 後に merge barrier を置き、allowlist の実在 pointer 照合を再実施する。 |
| P3 | **条件付き採用** | 未実装 module は仕様レベル事前登録でよい。B-057 の単一理由性は実装 wave 開始時にコードで確認する。現物では `guard_write` は freeze を拒否する一方、`guard_bash` の防護 tree に freeze namespace が無いので、W-0 の既存コード変異対象には `guard_bash.py` も必要。 |
| P4 | **採用** | 本草案は全 required field、型、件数、一意性、拒否規則、reason code を列挙する。残す択一は approval expiry の意味だけで、決定権者をユーザーと明記する。 |
| P5 | **一部否認** | 符号化・path・ID は親裁定でよい。しかし approval expiry が「未発効承認の期限」か「発効後 lease」かは承認境界そのものであり、親だけでは確定できない。本草案は前者を推奨するが、ユーザー裁定を要する。 |

---

# §13-1. lineage / approval / active pointer / receipt

## 1.1 共通表現

### 1.1.1 hash、Git OID、時刻、path

- `sha256`: JSON string、`^[0-9a-f]{64}$`。
- `git_commit` / `git_blob_oid`: JSON string、`^[0-9a-f]{40}$`。実装開始時に `git rev-parse --show-object-format == sha1` を要求する。
- generation number: JSON integer、`N >= 0`。Python `bool` は拒否する。
- UTC: `YYYY-MM-DDTHH:MM:SSZ` のみ。fraction、UTC offset、日付だけの値は拒否する。
- repo path: 空でない POSIX 相対 path。先頭・末尾 `/`、`//`、`\`、`.` / `..` component、control character を拒否する。現行下限は E8 および [s8b_ratified_freeze.py:857](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:857)。
- governance record は全て mode `100644` の Git blob。symlink、gitlink、executable blob を拒否する。

### 1.1.2 record の canonical JSON

receipt、approval、pointer、revocation、cancellation、generation plan に共通する。

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

追加制約:

- raw bytes は上記 bytes と byte-for-byte 一致し、BOM・末尾改行を持たない。
- duplicate key、NaN、Infinity、top-level 非 object を拒否する。
- 全 string は Unicode NFC。U+0000..U+001F と U+007F を拒否する。
- governance record 内の JSON float と bool は、schema が個別に許可しない限り拒否する。本草案の record はいずれも float を持たない。

実物根拠: E7。実装 owner: **W-a**。

## 1.2 family generation の lineage header

別の「lineage JSON」は新設しない。lineage の正本は各 family artifact の共通 header と receipt/pointer である。

| field | 型・必須性 | exact 制約 | 根拠 | owner |
|---|---|---|---|---|
| `schema_version` | string、必須 | known=`s1-known-axes-freeze/v2`、measurement=`s1-measurement-freeze/v3`、holdout=`8b-holdout-freeze/v3` | E1 | W-b / W-c |
| `generation_number` | integer、必須 | `N >= 1`。3 family と path の N が全一致 | E1 | W-b / W-c |
| `supersedes_sha256` | sha256 string、必須 | g1 は対応 legacy raw hash。N>1 は同 family g(N-1) raw hash | E1、E11 | W-b / W-c |
| `provenance_unverified` | object、必須 | exact keys=`generator`, `python_version_at_generation`, `related_implementations`。G projection から除外 | E1 | W-b / W-c |
| `provenance_unverified.generator` | object、必須 | `{path,sha256_at_generation}` exact | E1、legacy `/generator` | W-b / W-c |
| `python_version_at_generation` | string、必須 | 非空、NFC。gate の再構成入力に使用禁止 | E1、legacy `/python_version` | W-b / W-c |
| `related_implementations` | array、必須 | 0件以上。各要素 `{path,sha256_at_generation}`、path 一意、path 昇順 | E1 | W-b / W-c |

generation path は以下に固定する。

```text
output/s1-freeze/known_axes_freeze.v2.g<N>.json
output/s1-freeze/measurement_freeze.v3.g<N>.json
output/s8b-freeze/holdout_freeze.v3.g<N>.json
```

各 N について artifact はちょうど3件。1 family 欠落、N の混在、複数 blob 履歴は拒否する。

g1 の `supersedes_sha256` は次の exact 値である。

```text
known       354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516
measurement 203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a
holdout     315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688
```

実物根拠: E12 `/`, E13 `/`, E14 `/` の raw SHA-256、E15 の literal 値。

## 1.3 g1 transition receipt

### 1.3.1 path と top-level schema

path は一件だけである。

```text
output/freeze-migrations/legacy-to-permanent-g1.receipt.json
```

top-level は exact 9 fields、全て必須。

| field | 型・件数 | exact 制約 | 根拠 | owner |
|---|---|---|---|---|
| `schema_version` | string | `freeze-family-transition-receipt/v1` | E5 の一回限り receipt | W-c |
| `transition_id` | string | `legacy-to-permanent-g1` | E5 | W-c |
| `generation_number` | integer | exact `1` | E1、E5 | W-c |
| `generation_commit` | git_commit | 3 artifact を追加した同一 G | E3、E4 | W-c |
| `h_gen` | git_commit | `G^`。`generation_commit` の唯一の parent | E3 | W-c |
| `legacy_inventory` | array | exact 9 elements | E5、設計 §1.1 | W-c |
| `successors` | array | exact 3 elements、family 固定順 | E5 | W-c |
| `projections` | array | exact 3 elements、family 固定順 | E5 | W-c |
| `holdout_confirmation` | object | exact 3 fields | E1 §3.3 | W-c |

### 1.3.2 `legacy_inventory`

各 element は exact 8 fields。

```text
family
emission_commit
path
git_blob_oid
raw_sha256
recorded_frozen_at_head
anchor_status
disposition
```

型:

- `family`: `"known" | "measurement" | "holdout"`
- `emission_commit`, `recorded_frozen_at_head`: 40hex
- `git_blob_oid`: 40hex
- `raw_sha256`: 64hex
- `anchor_status`: exact `"missing"`
- `disposition`: exact `"legacy-history-only"`

配列順と値を次で固定する。

| # | family | emission commit | blob OID | raw SHA-256 | `/frozen_at_head` |
|---:|---|---|---|---|---|
| 1 | known | `80b30107ea17397c0881818c54c12856d5e77dcb` | `701cd39ebeeb0e115e0772c91a00637a6b2d994c` | `1622ecadde1cf8fd432c804d198ded8f0b3ce89b19d02503c6b77fee86952cdd` | `c648bbe2aa8dff028411b3b53a3ba8e6767bdb15` |
| 2 | known | `15fcc08fb78d6067f21aaf564c03d60ec36de649` | `b31927be81e24d6801af6303cdf119ecbd37ea6f` | `e1b0a5348034b5bf6e938ff498802ccc2d43cd2b646ed745c5f3d803ca05fd8e` | `ca921338507ad66540ceae997b327e6c3ab3cb3d` |
| 3 | known | `8f7fca22043dff8002e11ae9f03b5cc60e71e428` | `90d987722021bc1d01daa10b0cdb6f0d541fcdc0` | `7a7458df4ee4350ff500f7b47662fe74ae8e3d0936430c1dda8c3a8fcb012f3e` | `c890e958acfc3e2456e0033648069a9f2f297b81` |
| 4 | known | `b4e5cb621e3f8f93de952e9400d4b8dcd34107e0` | `47fa327efe555d9113119daafc79706838b8ec9a` | `3eb808b4b751d5dc57e57e214fc6d7fea9a9c702a0208b5f0e87f094ae65bce1` | `0f304270954eacd6df136bbac50da649e289833d` |
| 5 | known | `e5dfa84c6e71824e2312af99b97d60dde11eca20` | `18346a35a00a71f8986f47d54afc1a2392fbfb27` | `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` | `2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1` |
| 6 | measurement | `4b9d86e3c50b9c48748e8935217d8a2ac500d74d` | `fd2bc0e52479cc1e352f172a99b2476d6355b507` | `09dd1585ca28aebfbae0e724e4bacb299452dbad1b21eb67e893795d999756f6` | `02c840c4a001f8df6810355471806cb251400fdf` |
| 7 | measurement | `b4e5cb621e3f8f93de952e9400d4b8dcd34107e0` | `8c15edcd9ff0d10b00145e2a137dd4cbeb92e69a` | `5c719c076e17f385a781933c081bf02abcd85b9edb01ad8c50a37740c134a191` | `0f304270954eacd6df136bbac50da649e289833d` |
| 8 | measurement | `e5dfa84c6e71824e2312af99b97d60dde11eca20` | `edfe2ed71b80b8aa44dabd2a7d669c4dcde18d26` | `203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a` | `2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1` |
| 9 | holdout | `911f6bc0407c6a6479b0edcb3d0c0b95ab1730e2` | `3803df1f63c84c3c9bf79e590b8a5b4a4943e02c` | `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` | `2e20d441aaf7ae267e941ecda09e4b53050943cf` |

`path` は family ごとに次の値。重複 path はこの配列だけで許す。

```text
known       output/s1-freeze/known_axes_freeze.json
measurement output/s1-freeze/measurement_freeze.json
holdout     output/s8b-freeze/holdout_freeze.json
```

一意 key は `(family, emission_commit, path)`。W-e は各 `emission_commit:path` の blob OID、raw SHA-256、JSON pointer `/frozen_at_head` を再導出しなければならない。

### 1.3.3 `successors`

exact 3 elements、順番は `known`, `measurement`, `holdout`。各 element は exact 7 fields。

| field | 型 | 制約 |
|---|---|---|
| `family` | string | 上記3値、重複禁止 |
| `path` | string | §1.2 の g1 exact path |
| `schema_version` | string | §1.2 の exact version |
| `generation_number` | integer | exact `1` |
| `raw_sha256` | sha256 | G tree の raw blob から再計算 |
| `git_blob_oid` | 40hex | G tree の blob OID |
| `supersedes_sha256` | sha256 | §1.2 の legacy hash |

### 1.3.4 `projections`

exact 3 elements、同じ family 順。各 element は exact 4 fields。

| field | 型 | 制約 |
|---|---|---|
| `family` | string | 3 family、一意 |
| `contract_id` | string | 下表の exact ID |
| `removed_claims` | string array | 下表の exact JSON Pointer |
| `metadata_sources` | string array | 下表の exact JSON Pointer |

| family | `contract_id` | `removed_claims` | `metadata_sources` |
|---|---|---|---|
| known | `known-legacy-to-v2/v1` | `["/frozen_at_head"]` | `["/generator","/python_version"]` |
| measurement | `measurement-legacy-to-v3/v1` | `["/frozen_at_head"]` | `["/generator","/python_version","/implementation_hashes/s1_measurement_freeze","/implementation_hashes/s1_stats"]` |
| holdout | `holdout-legacy-to-v3/v1` | `["/frozen_at_head"]` | `["/generator"]` |

`contract_id` は自己申告の pass flag ではない。verifier が legacy blob と successor blob から contract を再実行し、不一致なら拒否する。

実物根拠: E13 `/generator`, `/python_version`; E14 `/implementation_hashes`; E12 `/generator`; E1 §3.1–3.3。owner: **W-b / W-c、実 record 発行は W-e**。

### 1.3.5 `holdout_confirmation`

exact 3 fields。

```json
{
  "confirmed_by": "<non-empty NFC string>",
  "confirmed_at": "<RFC3339 UTC>",
  "holdout_sha256": "<64hex>"
}
```

- `confirmed_by` と `confirmed_at` は successor holdout `/confirmed_by`, `/confirmed_at` と完全一致。
- `holdout_sha256` は successor holdout raw hash と一致。
- approval の `approver` と同一人物である必要はない。A はこの confirmation を含む receipt hash を承認する。
- legacy 実物の `/confirmed_at` は `"2026-07-16"` という date-only string だが、新 v3 では UTC seconds へ強化する。legacy 値を新 schema の型根拠に流用しない。

根拠: E12 `/confirmed_by`, `/confirmed_at`; E1 §3.3。owner: **W-c**。

## 1.4 gN→gN+1 receipt（N≥1）

§6/§7 は各 G の後に receipt を要求するため、g1 一回限り receipt だけでは将来世代を承認できない。N≥2 は別 schema とする。

path:

```text
output/freeze-migrations/permanent-g<N-1>-to-g<N>.receipt.json
```

top-level exact 8 fields:

```text
schema_version
transition_id
generation_number
generation_commit
h_gen
predecessors
successors
holdout_confirmation
```

- `schema_version`: `freeze-family-generation-receipt/v1`
- `transition_id`: `permanent-g<N-1>-to-g<N>`
- `generation_number`: exact N
- `generation_commit`: G
- `h_gen`: G の唯一 parent
- `predecessors`: exact 3 elements
- `successors`: §1.3.3 と同じ exact 3 elements
- `holdout_confirmation`: §1.3.5

`predecessors` element は exact 4 fields:

```text
family
path
generation_number
raw_sha256
```

generation number は N-1、path/hash は直前 generation。family 順・一意性は successors と同じ。

owner: schema/verifier **W-c**、実 record 発行 **W-e**。

## 1.5 approval record

### 1.5.1 path と schema

expiry 後の再承認を可能にするため、path は bundle digest ではなく approval record 自身の raw hashで keyed する。

```text
output/freeze-permanent/approvals/<approval_raw_sha256>.json
```

exact 8 fields、全 required。

| field | 型 | exact 制約 | 根拠 |
|---|---|---|---|
| `schema_version` | string | `freeze-bundle-approval/v1` | 新 bundle record、E4 |
| `generation_number` | integer | N≥1、components/pointer と一致 | E4、E6 の現行 generation approval |
| `bundle_digest` | sha256 | §13-2 の再計算値 | E4 |
| `components` | array | exact 4 elements、固定順 | E4 |
| `approver` | string | 1..128 code points、NFC、trim 済み | E6 `_APPROVAL_KEYS` |
| `approved_at` | UTC string | exact UTC grammar | E6 |
| `expires_at` | UTC string | `approved_at < expires_at` | §13 expiry 残課題 |
| `scope` | string | `freeze-bundle-digest+verification-report+projection-report/v1` | R14、E4 |

`components` の各 element は exact `{kind,sha256}`。順序と kind は:

```text
0 known
1 measurement
2 holdout
3 receipt
```

filename は canonical raw bytes の SHA-256 と一致しなければならない。同じ bundle は expiry 後に別 `approved_at` / `expires_at` を持つ新 approval record で再承認できる。

件数:

- bundle あたり approval は 0件以上。
- approval raw hash は全 namespace で一意。
- A commit 1件につき追加できる approval はちょうど1件。
- X が参照できる approval はちょうど1件。

### 1.5.2 expiry 推奨仕様

推奨は「**未発効 approval の activation window**」であり、active bundle の lease ではない。

- X 実行時の実時計が `expires_at` 以後なら X CLI は拒否。
- X commit の raw committer epoch も `[approved_at, expires_at)` 内でなければ拒否。
- X の唯一 parent はその approval の導入 commit A。
- X 成立後は `expires_at` 経過だけでは active bundle を失効させない。失効には revocation record を要する。
- expiry 後は同じ bundle digest に対し新 A record を追加できる。

この「activation window / 非 lease」の意味は承認境界なので、**ユーザー裁定 U-A1** とする。決定前に W-c を開始しない。

owner: **W-c**。A record 実作成: **W-e**。

## 1.6 active-bundle pointer

### 1.6.1 path と schema

```text
output/freeze-permanent/active/<pointer_raw_sha256>.json
```

top-level exact 7 fields。

| field | 型 | exact 制約 |
|---|---|---|
| `schema_version` | string | `freeze-active-bundle-pointer/v1` |
| `generation_number` | integer | g0 は0、permanent は N≥1 |
| `parent_active_sha256` | sha256 or null | null は g0 のみ |
| `bundle_digest` | sha256 or null | null は g0 のみ |
| `approval_sha256` | sha256 or null | approval raw hash。null は g0 のみ |
| `artifacts` | array | exact 3 elements、family 固定順 |
| `receipt` | object or null | permanent は `{path,sha256}`、g0 は null |

artifact element は exact 5 fields。

```text
family
path
schema_version
generation_number
sha256
```

- `family`: `known`, `measurement`, `holdout`
- permanent pointer は3件とも generation N。
- `schema_version` は permanent では §1.2 の exact value。
- g0 の legacy known/measurement は成果物に `schema_version` が実在しないため `null`。holdout だけ `"8b-holdout-freeze/v1"`。
- artifact path/hash は H_v tree の blob と完全一致。

実物根拠: E13 と E14 の top-level に `schema_version` が存在しないこと、E12 `/schema_version`、E6 の現行 `_POINTER_KEYS`。

### 1.6.2 g0 exact record

g0 は legacy 3 hash だけから完全決定する。canonical raw は次である。

```json
{"approval_sha256":null,"artifacts":[{"family":"known","generation_number":0,"path":"output/s1-freeze/known_axes_freeze.json","schema_version":null,"sha256":"354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516"},{"family":"measurement","generation_number":0,"path":"output/s1-freeze/measurement_freeze.json","schema_version":null,"sha256":"203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a"},{"family":"holdout","generation_number":0,"path":"output/s8b-freeze/holdout_freeze.json","schema_version":"8b-holdout-freeze/v1","sha256":"315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688"}],"bundle_digest":null,"generation_number":0,"parent_active_sha256":null,"receipt":null,"schema_version":"freeze-active-bundle-pointer/v1"}
```

静的に導出される SHA-256:

```text
746fcafabaaef09f11bc945dafc63eb177c94df5c1fb2735aadb230be2260e4b
```

従って g0 path は:

```text
output/freeze-permanent/active/746fcafabaaef09f11bc945dafc63eb177c94df5c1fb2735aadb230be2260e4b.json
```

g0 は唯一の `parent_active_sha256=null` record。第二 genesis は拒否する。owner: **W-c**。

### 1.6.3 active 解決

resolver は開始時に `H_v` を一度だけ捕捉し、次を同じ H_v tree から一度だけ読む。

1. governance record 全件
2. unique live pointer chain
3. tip が指す3 artifact
4. receipt
5. approval

返却型は bundle 単位の `ActiveOfficialBundle` とし、family 別 public resolve を設けない。

pointer chain は:

```text
g0 → g1 → g2 → ... → gN
```

次を要求する。

- g0 は §1.6.2 と byte-for-byte 一致。
- child の generation は parent + 1。
- child `parent_active_sha256` は parent raw hash。
- child の3 family generation は pointer generation と全一致。
- receipt generation、approval generation、bundle digest が一致。
- current live tip はちょうど1件。
- 「最大 N」「最新 approval」「最新 commit」による選択は禁止。
- approved-inactive bundle が複数あっても pointer に参照されない限り official にならない。
- revocation・expiry・fork 時に旧 pointer へ fallback しない。

実物下限: E10。owner: **W-c**、consumer 切替: **W-d**、g1 X: **W-f**。

## 1.7 revocation と fork cancellation

### 1.7.1 revocation record

path:

```text
output/freeze-permanent/revocations/<bundle_digest>.json
```

exact 7 fields:

```text
schema_version = "freeze-bundle-revocation/v1"
bundle_digest: sha256
approval_sha256: sha256
revoked_by: non-empty NFC string
revoked_at: UTC string
scope = "bundle-only"
reason: 1..1024 code points
```

規則:

- bundle あたり0または1件。
- target bundle は既に pointer で一度発効済みでなければならない。approved-inactive の取消は expiry / 非Xで処理し、generation gap を作る revocation は拒否。
- revocation commit は target X の後裔、非 merge、diff は当該1 record の追加のみ、`AI-Agent: none`。
- revoked bundle が live tip なら active なし。旧世代へ fallback しない。
- independently approved な gN+1 が後に X された場合は復帰可能。revocation は descendant を自動失効させない。これは現行 resolver の「tip だけを revoked 検査」と同じ下限である（E10）。
- revocation record の削除・変更・再追加は禁止。

owner: **W-c**。

### 1.7.2 fork cancellation record

path:

```text
output/freeze-permanent/active-cancellations/<pointer_sha256>.json
```

exact 6 fields:

```text
schema_version = "freeze-pointer-cancellation/v1"
pointer_sha256: sha256
cancelled_by: non-empty NFC string
cancelled_at: UTC string
scope = "fork-loser-only"
reason: 1..1024 code points
```

有効な cancellation は次を全て満たす。

- target pointer が実在し、g0 ではない。
- target は leaf pointer であり、child を持たない。
- 同じ `parent_active_sha256` を持つ別 pointer が少なくとも1件ある。
- cancellation 適用後に surviving child がちょうど1件。
- target pointer の導入 commit が surviving pointer の導入 commit の祖先である場合、target の取消を拒否する。既に有効だった枝から後発枝への rollback を防ぐ。
- later challenger、または相互に ancestry のない branch fork の loser は人間 cancellation で除外できる。
- 唯一の live tip の cancellation、generation を下げる cancellation、g0 cancellation は `lineage.rollback.forbidden`。

owner: **W-c**。

## 1.8 generation transition allowlist

比較対象は `provenance_unverified` を除いた G projection。RFC 6901 leaf diff を使い、現行 `_leaf_pointers` / `_pointer_allowed` と同じ「列挙 subtree だけ変更可」の形を使う（E11）。

許可 pointer であっても、target generation の schema/semantic/cross-family verifier は全件通す。「allowlisted だから値は任意」ではない。

### 1.8.1 known gN→gN+1

許可:

```text
/generation_number
/supersedes_sha256
```

加えて、C1 が確定する宣言済み source-record registry に属する各 record の `/sha256` と、列挙 snapshot の digest/count field だけを許可する。path、key、selection rule、選択値、flags、pairing、`ccbench_pin` は不変。

この集合は A/B/C1 merge barrier で実在 JSON Pointer に展開し、symbolic wildcard のまま実装 brief に渡してはならない。

known の semantic selection を変える場合は同一 v2 lineage では受理しない。新 schema / 新ユーザー裁定を要する。

owner: **W-b**、source pointer 最終集合の決定 owner: **C1 設計草案**。

### 1.8.2 measurement gN→gN+1

許可:

```text
/generation_number
/supersedes_sha256
/known_axes_freeze/path
/known_axes_freeze/sha256
/cells
/s1b_pairing
/observations
/analysis_results
```

追加制約:

- `/cells` と `/s1b_pairing` は new known artifact からの機械再構成値との完全一致が必須。任意変更ではない。
- `/known_axes_freeze` は同一 bundle の known path/hash と一致。
- `comparisons` 12件、schedule、operating point、workload flags、master seed、ccbench pin は不変。
- `observations` / `analysis_results` は B の exact schema と独立再計算 gate を通る。

現物根拠: E14 `/cells` は18 keys、`/comparisons` は12 elements、`/s1b_pairing` は3 elements。owner: **W-b**。

### 1.8.3 holdout gN→gN+1

許可:

```text
/generation_number
/supersedes_sha256
/known_axes_freeze/path
/known_axes_freeze/sha256
/holdouts/rr80/variant_binding
/holdouts/rr20/variant_binding
/lifecycle_stage
/env_tag
/floor
/budget
/floor_protocol
/floor_source
/measurement_closure
/refreeze_note
```

追加制約:

- `variant_binding` は同 bundle の known artifact からの再構成と一致。
- `lifecycle_stage` は同値、または `pre-measurement → ratified-floor` のみ。逆遷移拒否。
- `env_tag` は `null → registry 登録済み string` を一度だけ許可。その後の変更拒否。
- `search`、holdout axes、unknownness snapshot、positive control、derangement、design source、confirmation は同 lineage 内で不変。
- `floor` 等は holdout v3 semantic verifier を通る。
- 現行 gN 表の `/frozen_at_head` は新 schema に field がないので継承しない。
- 現行 gN 表が9 pointerであるのに対し、新表は known bundle reference と derived variant binding を追加する。これは R15 lockstep により known path/hash が世代ごとに変わるため不可欠である。

現物対比: E11 の v1→g1 は13 pointer、gN→gN+1 は9 pointer。legacy holdout の `/known_axes_freeze` は E12。owner: **W-c**。

## 1.9 fork、gap、rollback、件数・一意性

- generation N が存在するなら、1..N の各番号について3 family が全件存在する。
- 同一 `(family,N)` path は追加1回だけ。別 bytes、delete/re-add、rename、同一 bytes の複数 branch introduction を全て拒否。
- 3 artifact は同じ G commit で導入される。
- 同一 predecessor から異なる successor bundle が履歴に現れた場合は fork。固定 path の blob 競合として拒否する。
- receipt は generation あたりちょうど1件。
- production root と `FROZEN_MANIFEST` は generation あたり artifact 3件＋receipt 1件を追加する。
- approval は bundle あたり0件以上、pointer が参照する approval は1件。
- live pointer は generation あたりちょうど1件。canceled pointer は件数に含めない。
- revocation は bundle あたり0/1。
- cancellation は pointer あたり0/1。
- generation N の active pointer から N-1 以下を指す pointer は rollback として拒否。
- revoked/expired/missing approval 時に旧世代へ fallback しない。

## 1.10 G/R/literal×2/A/X commit topology

commit を次の記号で固定する。

```text
H_gen <- G <- R <- L_prod <- L_manifest ... A <- X
```

`...` は同 bundle の期限切れ approval と再approvalを許すための first-parent commit 列。X の parent は、X が使用する A そのものでなければならない。

| commit | parent / ancestry | exact diff | merge | authorization | owner |
|---|---|---|---|---|---|
| G | parent exactly `H_gen` | generation N の3 artifactを `A` statusで追加のみ | 禁止 | valid non-`none` `AI-Agent` | W-e |
| R | parent exactly G | generation N receipt 1件を `A` statusで追加のみ | 禁止 | valid non-`none` `AI-Agent` | W-e |
| L_prod | parent exactly R | `orchestrator/campaign/freeze_permanent_roots.py` 1ファイルのみ `M` | 禁止 | project provenance 契約 | W-e |
| L_manifest | parent exactly L_prod | `orchestrator/tests/test_frozen_artifacts.py` 1ファイルのみ `M` | 禁止 | project provenance 契約 | W-e |
| A | L_manifest の first-parent 後裔 | approval record 1件を `A` statusで追加のみ | 禁止 | raw/parsed とも exact `AI-Agent: none` | W-e |
| X | parent exactly selected A | active pointer 1件を `A` statusで追加のみ | 禁止 | raw/parsed とも exact `AI-Agent: none` | W-f |

追加制約:

- G/R/L_prod/L_manifest/A/X は pairwise 非同一。
- 全 introduction commit は `H_v` の first-parent chain 上に存在しなければならない。
- `diff-tree --no-renames --name-status -r` で exact status/path set を検査する。
- A は G/R/literal commit と非同一であるだけでなく、diff が approval 1件のみ。現行の `{approval,pointer}` 2追加 allowlist（E9）より強い。
- X は A と分離し、pointer 以外の root、artifact、receipt、approval を変更できない。
- `L_prod` と `L_manifest` の同一 commit 化は禁止。
- g1 の L_manifest 後は、E15 の旧8 exact key-setと新 artifact 3＋receipt 1の和集合、計12件。件数だけの検査を禁止する。
- future N は既存 key を全て保持して4件追加する。
- A/X/RV/cancellation の `AI-Agent: none` は現行 `_is_none_commit` と同じ raw line 1本＋`interpret-trailers` 二重判定を使う（E8）。

## 1.11 Git 履歴検査

- `H_v` を1回捕捉し、全 query はその OID に固定する。`H_v != H_gen` が通常である。
- `--all` を使わない。
- shallow repository、replace ref の存在、grafts、unsupported object format を拒否。
- dedicated namespace の path は H_v tree だけでなく、H_v reachable commit 全件の diff から列挙する。現在 H tree から消えた record も検出する。
- governance/generation/receipt record は `A` status 1回だけ。その後の `M/D/R/C/T`、mode change、再追加を拒否。
- current worktree の generation/governance namespace が dirty なら official resolve を拒否する。
- unrecognized file を `output/freeze-permanent/{approvals,active,revocations,active-cancellations}` または `output/freeze-migrations/` に置いた場合は無視せず拒否する。

現行 `_collect_records` は H tree の現存 path から開始するため、削除済み record を発見できない。新設計は reachable diff 列挙でこれを強化する。

## 1.12 §13-1 reason code

共通 parser/schema code:

```text
document.read_failed
document.utf8_invalid
document.json_invalid
document.duplicate_key
document.non_finite_number
document.top_level_invalid
document.not_canonical
schema.keys_mismatch
schema.type_mismatch
schema.value_invalid
schema.cardinality_mismatch
schema.duplicate_item
schema.path_invalid
schema.hash_invalid
schema.timestamp_invalid
```

Git / output:

```text
environment.git.command_failed
environment.git.head_not_commit
environment.git.object_format_unsupported
environment.git.shallow_repository
environment.git.replace_refs_present
environment.git.grafts_present
environment.git.object_missing
environment.git.object_type_mismatch
environment.git.path_not_blob
environment.git.namespace_dirty
output.path_missing
output.mode_invalid
output.blob_hash_mismatch
output.root_missing
output.root_hash_mismatch
output.root_keyset_mismatch
```

lineage / receipt / pointer:

```text
lineage.record.unknown
lineage.record.deleted
lineage.record.mutated
lineage.record.multiple_introduction
lineage.generation.missing_family
lineage.generation.number_mismatch
lineage.generation.gap
lineage.generation.supersedes_mismatch
lineage.generation.fork
lineage.bundle.lockstep_mismatch
lineage.transition.disallowed
lineage.receipt.path_mismatch
lineage.receipt.generation_mismatch
lineage.receipt.commit_mismatch
lineage.receipt.inventory_mismatch
lineage.receipt.successor_mismatch
lineage.pointer.filename_mismatch
lineage.pointer.genesis_count
lineage.pointer.parent_missing
lineage.pointer.fork
lineage.pointer.disconnected
lineage.pointer.generation_gap
lineage.pointer.bundle_mismatch
lineage.rollback.forbidden
lineage.active.missing
lineage.active.ambiguous
```

contract / dependency / authorization:

```text
contract.commit.merge_forbidden
contract.commit.not_first_parent
contract.commit.parent_mismatch
contract.commit.diff_mismatch
contract.commit.order_mismatch
contract.projection.mismatch
contract.confirmation.mismatch
dependency.known_axes_mismatch
dependency.measurement_mismatch
authorization.commit.trailer_invalid
authorization.approval.missing
authorization.approval.filename_mismatch
authorization.approval.digest_mismatch
authorization.approval.component_mismatch
authorization.approval.scope_mismatch
authorization.approval.expired
authorization.approval.revoked
authorization.activation.parent_mismatch
authorization.activation.time_invalid
authorization.revocation.target_invalid
authorization.cancellation.target_invalid
```

reason code は check-ID ではない。VerificationReport は location/record hash と reason code を分離し、複数 record に同じ reason が出てもよい。

---

# §13-2. bundle digest の exact 符号化

## 2.1 component 値

入力は raw SHA-256 4件だけで、順番を固定する。

```text
0 known generation raw sha256
1 measurement generation raw sha256
2 holdout generation raw sha256
3 receipt raw sha256
```

path、generation、schema は各 raw bytes と receipt に既に束縛されるため、digest payload に重複投入しない。

## 2.2 canonical payload

JSON array を使用し、object key 順への依存をなくす。

```json
["<known64>","<measurement64>","<holdout64>","<receipt64>"]
```

符号化:

```python
payload = json.dumps(
    [known_sha, measurement_sha, holdout_sha, receipt_sha],
    ensure_ascii=False,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

- array length は exact 4。
- 各要素は lowercase 64hex string。
- 空白、末尾改行、BOM なし。
- `sort_keys` は array のため意味を持たない。固定順は index で表す。

## 2.3 domain separator と hash

```python
DOMAIN = b"izanagi.freeze-family.bundle-digest/v1\x00"
bundle_digest = hashlib.sha256(DOMAIN + payload).hexdigest()
```

- algorithm は SHA-256 のみ。
- NUL は domain と JSON の境界。
- hex は lowercase 64文字。
- domain separator の変更は schema version変更であり、同じ `/v1` のまま変更禁止。

## 2.4 record 間の一致

次が全て同値でなければ拒否する。

```text
recomputed digest
approval.bundle_digest
active pointer.bundle_digest
approval path から読んだ record の components の再計算値
```

approval `/components` は digest payload と同じ4 hash・同じ順でなければならない。

reason code:

```text
contract.bundle_digest.component_count
contract.bundle_digest.component_format
contract.bundle_digest.mismatch
authorization.approval.digest_mismatch
lineage.pointer.bundle_mismatch
```

実物根拠: E4 の「対象4 hash、固定順、canonical JSON、domain separator、sha256」、E7 の canonical serializer。owner: **W-a**、approval/pointer integration: **W-c**。

---

# §13-5. §7-G generation guard

## 3.1 generation plan

plan は worktree 検索対象へ置かない。path は:

```text
$(git rev-parse --git-path izanagi-freeze-generation)/<transaction_id>/plan.json
```

`transaction_id` は lowercase 32hex。plan は canonical JSON、exact 7 fields。

| field | 型・件数 | exact 制約 |
|---|---|---|
| `schema_version` | string | `freeze-bundle-generation-plan/v1` |
| `transaction_id` | string | `^[0-9a-f]{32}$`、directory 名と一致 |
| `generation_number` | integer | N≥1 |
| `h_gen` | git_commit | prepare 開始時の HEAD |
| `owned_paths` | array length 3 | known、measurement、holdout の generation N path、固定順 |
| `start_snapshot_sha256` | sha256 | §3.2 の snapshot canonical bytes hash |
| `search_exemptions` | array length N | g0..g(N-1) holdout artifact の exact `{path,sha256}` |

`owned_paths` は caller が任意指定できない。N から関数で導出し、record 値が導出結果と異なれば拒否する。

owner: **W-0**。

## 3.2 start snapshot

prepare 時に次を全て要求する。

- root HEAD は commit で `h_gen` と一致。
- root index は H_gen tree と一致。
- root worktree は untracked を含め clean。
- `external/ccbench` HEAD は H_gen の gitlink と一致。
- ccbench index/worktree も untracked を含め clean。
- 3 `owned_paths` は不存在。
- root と ccbench の全 tracked regular file / symlink の raw bytes、mode、path を canonical inventory にし、SHA-256 を `start_snapshot_sha256` とする。
- symlink は追従せず link target bytes を hash。gitlink は commit OID を snapshot header に含める。
- path は UTF-8 byte-order で昇順、一意。

次の各時点で、owned path を除く snapshot が開始時と完全一致しなければ停止する。

1. 各 family 生成前
2. holdout search 直前
3. holdout search 直後
4. final publish 直前
5. final publish 直後

追加・変更・削除・rename・mode change・symlink 化は全て同じ snapshot mismatch とする。

## 3.3 staging

staging directory は plan の sibling:

```text
$(git rev-parse --git-path izanagi-freeze-generation)/<transaction_id>/stage/
```

exact file set:

```text
known.json
measurement.json
holdout.json
```

条件:

- directory は新規、mode 0700、symlink 不可。
- stage file は mode 0600 の通常ファイル、O_EXCL/O_NOFOLLOW。
- resolved staging path は Git worktree の外、または Git directory 配下で `git ls-files` の列挙 domain 外。
- family generator に final output path を渡さない。
- 3 staged bytes を一度だけ読み、full candidate verify 後まで同じ bytes objectを保持する。
- staging file の追加・削除・bytes 変更を publish 前に再照合する。
- receipt は G 後に作るため staging/owned set に含めない。

## 3.4 holdout search の列挙対象

現行列挙の次の部分を維持する。

- root `git ls-files -z -s` の mode 100644/100755
- root `git ls-files -z --others --exclude-standard` の通常非 symlink file
- `external/ccbench` の tracked mode 100644/100755
- path sort と一意化

実物根拠: E18。

新 G では broad prefix exclusion を使わない。

```text
search.excluded_paths == []
```

代わりに `plan.search_exemptions` の exact path/hash だけを検索から免除する。generation N では次の N 件に固定する。

```text
g0 legacy holdout
g1 holdout
...
g(N-1) holdout
```

各 exempt path は:

- H_gen tree の verified holdout lineage artifact
- recorded raw SHA と H_gen blob SHA が一致
- exemption に含まれるが enumeration/file_count からは除外しない
- hash 不一致なら免除せず検索するのではなく、generation guard では即拒否する

approval、pointer、receipt、revocation、known、measurement は exemption に入れない。

この形は現行の `output/s8b-freeze/` prefix 全除外より狭く、受理集合を広げない。現行 exact exemption の動作根拠は E18 の `exempt_exact`。

列挙 path array 自体も canonical JSON で SHA-256 を取り、search 前後の完全一致を要求する。staging path または plan path が列挙結果へ現れたら、digest が偶然一致していても `contract.search.staging_visible` で拒否する。

## 3.5 search と publish の順序

```text
prepare/snapshot
→ known stage
→ measurement stage
→ search（final path はまだ不存在）
→ user confirmed_by/confirmed_at
→ holdout stage
→ 3 candidate full verify
→ final publish
→ snapshot delta verify
→ G commit
```

publish は3 final pathに対し:

- 全 parent component を `lstat` し、symlink を拒否
- repo root からの realpath escape を拒否
- O_CREAT|O_EXCL|O_NOFOLLOW、mode 0644
- staged bytes と final bytes の一致
- publish 後の root deltaは「owned path 3件の新規通常ファイル」だけ
- partial publish が起きた場合、同 transaction が作成し staged hash と一致する owned fileだけを cleanup可能。既存 file、hash不一致 file、他 path は削除禁止

G commit 後の履歴 verifier が3 pathの同一 G introduction、G^=`H_gen`、diff exact を再検査する。process guard の自己申告を receipt の correctness proof として扱わない。

## 3.6 hook 契約

### `guard_write.py`

E16 の拒否を維持し、次を全て protected freeze namespace とする。

```text
output/s1-freeze/
output/s8b-freeze/
output/freeze-migrations/
output/freeze-permanent/
```

- Write/Edit/MultiEdit/NotebookEdit は plan が存在しても常に拒否。
- plan を capability token として任意 Write を通してはならない。
- final publish は専用 CLI の内部 writerだけが行う。
- hook は認証防壁に数えない。E17 の既知限界を維持する。

### `guard_bash.py`

現物では freeze namespace が防護対象でないため、W-0 で上記4 treeを追加する。

許可する writer は次の exact CLIだけ。

```text
python3 orchestrator/campaign/freeze_bundle_generate.py generate \
  --generation <N> \
  --confirmed-by <NAME> \
  --confirmed-at <UTC>
```

- caller supplied `--output`, `--staging`, `--owned-path`, inline Python、stdin script は拒否。
- shell redirection、cp/mv/rm/sed/tee/git checkout/git clean 等による protected tree 更新を拒否。
- `git add` と `git commit` は worktree bytes を生成しないため許可する。
- CLI 自身は plan schema、snapshot、O_EXCL publish を再検査する。hook の文字列判定だけを correctness gate としない。

### reason code

```text
authorization.hook.direct_write_forbidden
authorization.hook.command_forbidden
contract.generation_plan.schema_invalid
contract.generation_plan.path_set_mismatch
contract.generation_plan.exemption_invalid
environment.git.start_not_clean
environment.git.snapshot_changed
output.generation.path_exists
output.generation.path_escape
output.generation.non_regular
output.generation.publish_partial
contract.search.staging_visible
contract.search.enumeration_changed
contract.search.exemption_mismatch
```

owner: hook・guard core **W-0**、family stage writer **W-b/W-c**、実 G 実行 **W-e**。

---

## §14 追記要否

本草案の選択は次の理由で現行・確定骨格より受理集合を広げない。

- search exemption は現行の `output/s8b-freeze/` prefix 全除外より狭い exact path/hash 集合。
- cancellation は fork loser 専用で、唯一 tip の取消・fallback を禁止。
- approval expiry、first-parent topology、record immutability は現行より厳しい。
- known の semantic selection change は同一 lineage で拒否する。
- measurement の変更可能 subtree は独立再計算・known projection 一致を引き続き要求する。

従って本草案採用だけを理由とする §14 追記は不要。

ただし、今後次のいずれかを採る場合は受理集合を広げるため、§14 損失行を同時追加する。

- revoked/expired/fork 時の旧世代 fallback
- 「最新」「最大 N」による active 選択
- known の selection values 全体を同じ v2 lineage で任意変更可能にする
- search staging / governance namespace の prefix 一括除外

# 所見

1. **P2 の「A/B/C1 は並列確定可」は否認。** known transition の source SHA pointer 集合は §13-7、measurement の `cells`/source pointer は §13-2b の exact schema が決まらないと実在照合できない。並列起草後の merge barrier が必須。

2. **§6/§7 と §8 の receipt 範囲が曖昧。** §7 は各 G の後の receipt を要求する一方、§8 は g1 の一回限り path しか列挙しない。本草案は g1 receipt と N≥2 receipt を分離した。これを採らない場合、g2 以後の A digest を構成できない。

3. **approval expiry の意味は未裁定。** 現行 approval schema E6 に expiry field・clock gate はない。本草案の「未発効 activation window、発効後は非 lease」を推奨するが、承認境界なので決定権者はユーザー（U-A1）。

4. **W-0 の現行責務案は不足。** `guard_write.py` は freeze を拒否するが、`guard_bash.py` の防護対象は campaign/ccbench だけであり、README も Bash 経由の freeze 書込みを既知限界としている。`guard_bash.py` とその test を W-0 所有へ追加しなければ §7-G の hook 契約は閉じない。

5. **現行 ratified lower bound は削除済み governance record を発見できない。** `_collect_records` は H tree の現存 path から始めるため、過去に追加後削除された record は検査対象外になる。本草案は H_v reachable diff 全列挙に強化した。

6. **R15 lockstep により `/known_axes_freeze` の変更許可は不可欠。** known gN の path/hash は世代ごとに変わるため、measurement/holdout がこの2 leafを保護したままでは g2 が構造的に生成不能になる。現行 holdout `_TRANSITION_GN_TO_GN1` の9 pointerをそのまま流用してはならない。

7. **legacy known/measurement に `schema_version` は存在しない。** g0 pointer で文字列 schema を捏造せず `null` とした。holdout のみ実物 `/schema_version = "8b-holdout-freeze/v1"` を持つ。

8. **legacy `/confirmed_at` は date-only。** 新 approval/receipt の RFC3339 UTC gateへそのまま流用できない。g1 はユーザー同席で新 UTC 値を発行する必要がある。

9. **P3 の W-d consumer「手前検査不在」は、本 A 草案では確認していない。** 親が C2/変異 registry に記す際、W-d consumer 全件を別途静的照合せず「確認済み」と主張してはならない。

10. **P1 と既存 W-f 所有表に軽微な競合がある。** 今回 `docs/README.md` を更新するなら、C2 の exact file table で W-f 所有から除外する。`tools/check_docs.py` はコードなので W-f 維持でよい。
---

# 段 2b: codex 草案 B (observation/統計/registry)

# 草案 B — freeze 族恒久設計 第 2 設計段

> 対象: §13-2b、§13-3、§13-4  
> 照合方法: 現行コード・現物 JSON・Git tree の静的照合のみ。テスト実行結果は用いていない。  
> 規範語: 「必須」「拒否」は実装契約を表す。JSON object は明記した exact key-set 以外を拒否する。

## 0. 共通符号化規約

- JSON は UTF-8、top-level object、duplicate key・`NaN`・`Infinity`・`-Infinity` を拒否する。
- `integer` は `bool` を含まない。
- SHA-256 は小文字 64 桁 `[0-9a-f]{64}`。Git commit/blob OID は現 repo の SHA-1 object format に合わせ小文字 40 桁。
- repo path は `/` 区切りの正規化済み相対 path。空、絶対 path、空 segment、`.`、`..`、NUL、`\` を拒否する。
- binary64 の文字列表現 `h` は、有限値であり、`float.fromhex(h).hex() == h` となる ASCII string のみを canonical とする。大文字、短縮表現、十進表現、非有限値を拒否する。
- 浮動小数値を JSON number として凍結しない。以下で明記する全浮動小数 field は canonical `float.hex()` string とする。
- check result は後述の closed-world registry 順に並べる。unknown / duplicate / missing check-ID はそれ自体を verification failure とする。

実物根拠: strict WAL key/型検査は [wal.py:48](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:48)、oracle artifact の duplicate/non-finite 拒否は [s8b_oracle_artifacts.py:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_artifacts.py:60)、第 1 設計段の検査順・reason namespace は [freeze-permanent-design.md:164](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:164)。

---

## 1. §13-2b — `observations`

### 1.1 top-level schema

`measurement v3` の `/observations` は次の exact 6 keys を持つ。

| field | 型・exact 制約 |
|---|---|
| `schema_version` | string literal `"s1-measurement-observations/v1"` |
| `unit` | string literal `"transactions_per_second"` |
| `value_encoding` | string literal `"python-float.hex/binary64"` |
| `rounding` | string literal `"source-json-to-binary64-roundTiesToEven;no-decimal-rounding"` |
| `wal_sources` | array、ちょうど 3 件 |
| `records` | array、ちょうど 288 件 |

288 は `18 cells × (floor 8 + test_block_1 4 + test_block_2 4)`。現物 `/cells` は object 18 件、`/schedule/floor` は 8 lap、他 2 schedule は各 4 lapで、各 lap が18 cellである。

現行 measurement freeze は top-level 14 keys であり、`/observations` と `/analysis_results` は存在しない。根拠: [measurement_freeze.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/measurement_freeze.json:1) の `/cells`、`/comparisons`、`/schedule`。生成側の18件・12比較・schedule invariant は [s1_measurement_freeze.py:282](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:282)。

所有 wave: **W-b**。

### 1.2 `wal_sources[3]`

順序と値域は次で固定する。

| index | `wal_source_id` | `schedule_name` | `campaign_role` |
|---:|---|---|---|
| 0 | `"floor"` | `"floor"` | `"floor"` |
| 1 | `"block1"` | `"test_block_1"` | `"block1"` |
| 2 | `"block2"` | `"test_block_2"` | `"block2"` |

各要素の exact key-set:

| field | 型・制約 |
|---|---|
| `wal_source_id` | 上表の string。3件で一意 |
| `schedule_name` | 上表の string |
| `campaign_role` | 上表の string |
| `wal_path` | 正規化 repo-relative path。3件で一意 |
| `wal_blob_oid` | 40桁 Git blob OID |
| `wal_sha256` | WAL blob 全 bytes の SHA-256 |
| `env_tag` | 空でない string |
| `campaign_start` | 下記 `WalRecordLocator` |

`WalRecordLocator` は exact 2 keys:

```json
{
  "record_ordinal": 1,
  "raw_record_sha256": "<64 lowercase hex>"
}
```

- `record_ordinal`: 1-based physical record ordinal、`1..2^64-1`。
- `raw_record_sha256`: 当該 record の bytesから末尾のちょうど1 byteの LFを除いた bytesの SHA-256。
- WAL blob は全 record が LF 終端でなければ拒否する。CRLF、空行、不正な末尾 prefix は A 前照合では受理しない。
- `campaign_start.record_ordinal` は3 WALすべて `1`。
- record top-level は現行どおり exact `{variant,stage,env_tag,ts,payload}`。campaign-start は `variant=="s1-campaign"`、`stage=="s1-session"`、payload の現行値が `event=="campaign-start"`、`campaign_role` が表と一致すること。

G1 生成に使う現行 tree の照合値:

| source | path | Git blob OID | raw SHA-256 | records |
|---|---|---|---|---:|
| floor | `output/campaigns/s1-direct-floor-direct-comparison-b82b9229/runs/wal.jsonl` | `07bde4386bc9a0acae3e8f22921d4c7de91b68c8` | `a5542d6cba6b4470a828e96e77f826dcd553ce38fe635a7a4c88141c03d99c38` | 1009 |
| block1 | `output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2/runs/wal.jsonl` | `63b7b8ec8f8c10caade711a533a2a01870f590ef` | `57726aadb08b1833cd2a8e919c9f766ac83c1cdce551c4bc82ad4fdeb1f2ad20` | 505 |
| block2 | `output/campaigns/s1-direct-block2-direct-comparison-9645b16a/runs/wal.jsonl` | `3d5f1b172727934c42a9290b4626ff12d9417d40` | `2194ca8936bb0d6f812e6ad94ffbd1f278ab40386abc5123c36d0ea75c7342bd` | 505 |

これは G1 projection の値であり、将来世代の schema literal ではない。

実物根拠: floor の campaign-start / session-start / commit / result は [wal.jsonl:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/campaigns/s1-direct-floor-direct-comparison-b82b9229/runs/wal.jsonl:1)。現行 WAL には record ID field がなく、物理行番号を返すのは [wal.py:95](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:95)。writer の LF 付加は [wal.py:109](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/wal.py:109)。

所有 wave: schema / locator parser は **W-b**、Git tree blob reader は **W-a** 共通基盤を使用する。

### 1.3 `records[288]`

各要素は exact 8 keys:

| field | 型・制約 |
|---|---|
| `observation_id` | `schedule_name + ":" + schedule_indexを3桁zero-pad`。例 `"floor:000"`。全288件で一意 |
| `schedule_name` | `"floor"`, `"test_block_1"`, `"test_block_2"` |
| `lap` | 1-based integer。floor=`1..8`、他=`1..4` |
| `position` | integer `0..17` |
| `schedule_index` | integer。floor=`0..143`、他=`0..71` |
| `cell_id` | string。対応する `/schedule/<schedule_name>/<lap-1>/<position>` と完全一致 |
| `value_tps_hex` | 正の有限 binary64 の canonical `float.hex()` string |
| `source` | 下記 exact object |

配列順は `floor`、`test_block_1`、`test_block_2` の順に、各 schedule を lap-major / position-minor で平坦化した順。以下をすべて要求する。

- `schedule_index == (lap-1)*18 + position`
- `(schedule_name,schedule_index)`、`observation_id`、`(wal_source_id,value_record.record_ordinal)` はそれぞれ一意。
- 各 cell は floor 8件、block1 4件、block2 4件。
- 欠落・余剰・並べ替えも拒否する。

`source` は exact 7 keys:

| field | 型・制約 |
|---|---|
| `wal_source_id` | 対応する `"floor"`, `"block1"`, `"block2"` |
| `attempt` | non-negative integer |
| `variant` | 空でない string |
| `session_start` | `WalRecordLocator` |
| `value_record` | `WalRecordLocator` |
| `session_result` | `WalRecordLocator` |
| `value_json_pointer` | literal `"/payload/fitness_tps"` |
| `value_origin_sha256` | 下記 domain-separated SHA-256 |

`value_origin_sha256` は次の bytes の SHA-256 とする。

```text
b"izanagi.freeze-observation-origin/v1\0"
|| bytes.fromhex(wal_source.wal_sha256)
|| uint64_be(value_record.record_ordinal)
|| bytes.fromhex(value_record.raw_record_sha256)
|| b"\0/payload/fitness_tps\0"
|| value_tps_hex.encode("ascii")
```

session binding は次をすべて満たす。

- `session_start` payload の `schedule_index/campaign_role/lap/cell_id/variant/attempt` が frozen record と一致。
- `value_record` は同じ session の `stage=="commit"` で、`payload.fitness_tps` が数値・有限・正。
- `session_result` は同じ識別値を持ち、`event=="session-result"`、`status=="success"`。
- 3 locator は順序が `session_start < value_record < session_result`。
- `float(payload.fitness_tps).hex() == value_tps_hex`。
- 同一 session に利用可能な commit / success result が複数ある場合は曖昧として拒否する。

拒否 reason code:

| 条件 | reason code |
|---|---|
| top keys / literal / 型 / 件数違反 | `schema.measurement.observations` |
| `wal_sources` shape・順序・一意性違反 | `schema.measurement.wal-sources` |
| record shape・範囲違反 | `schema.measurement.observation-record` |
| hex 非canonical・非有限・非正 | `schema.measurement.float-hex` |
| scheduleとの非全単射 | `contract.measurement.observation-bijection` |
| locator shape違反 | `schema.measurement.wal-pointer` |
| origin hash不一致 | `contract.measurement.value-origin` |

所有 wave: **W-b**。

---

## 2. §13-2b — `analysis_results`

### 2.1 top-level schema

`/analysis_results` は exact 5 keys:

| field | 型・制約 |
|---|---|
| `schema_version` | literal `"s1-measurement-analysis/v1"` |
| `n_permutations` | integer literal `4900` |
| `reference_alpha` | exact rational `{ "numerator": 1, "denominator": 80 }` |
| `comparisons` | array、ちょうど12件 |
| `families` | array、ちょうど2件 |

`comparisons` は measurement `/comparisons` と同じ順序・同じ12 `comparison_id`。現物は S-1a 9件、S-1b 3件で、全件 `left_cell` が `system_gate`、`alternative=="greater"`。[measurement_freeze.json:809](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/measurement_freeze.json:809)

所有 wave: schema / generator / verifier は **W-b**、独立参照計算は **W-a**。

### 2.2 comparison result

各要素は exact 9 keys:

| field | 型・制約 |
|---|---|
| `comparison_id` | `/comparisons/<i>/comparison_id` と一致、12件で一意 |
| `statistic_rank_sum_x2` | non-bool integer、`40..104` |
| `p_permutation` | `{numerator,denominator}`、denominator=`4900`、numerator=`1..4900` |
| `gates` | 下記 exact object |
| `p_star` | denominator=`4900`。両 gate passなら p numerator、他は4900 |
| `reference_below_alpha` | `p_star.numerator * 80 <= 4900` と同値の bool |
| `judgment` | `"established"` または `"not_established"`。上記 bool と一対一 |
| `effect_sizes` | 下記 exact 5 fields |
| `alternative` | literal `"greater"` |

`gates` は exact 2 keys。

```json
{
  "relative_median": {
    "passed": true,
    "relative_difference_hex": "<hex>",
    "floor_left_cv_hex": "<hex>",
    "floor_right_cv_hex": "<hex>",
    "required_strictly_greater_than_hex": "<hex>"
  },
  "direction_consistency": {
    "passed": true,
    "pooled_sign": 1,
    "stratum_signs": [1, 1]
  }
}
```

- `relative_median` は exact 5 keys。
- `direction_consistency` は exact 3 keys。
- sign は `-1|0|1`。`stratum_signs` は block1, block2 の順でちょうど2件。
- threshold は `max(floor_left_cv, floor_right_cv, 0.03)`。
- gate 1 は `relative_difference > threshold` の厳密不等号。
- gate 2 は `pooled_sign != 0` かつ2 stratum signが pooled sign と同一。
- floor CV は各 cell の floor 8観測だけから求める。

現行式の根拠は [s1_report.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:116) と [s1_report.py:574](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:574)。

### 2.3 効果量

`effect_sizes` は現行 `EffectSizes` と同じ exact 5 keys:

| field | 型 |
|---|---|
| `median_difference` | canonical finite hex string |
| `probability_superiority_stratified` | canonical finite hex string、復号値 `0..1` |
| `probability_superiority_pooled` | canonical finite hex string、復号値 `0..1` |
| `target_cv` | canonical finite hex string または `null` |
| `control_cv` | canonical finite hex string または `null` |

定義:

- target は comparison の left/system_gate。
- control は right。
- target/control の各 strata は test_block_1 と test_block_2 の4件ずつ。
- `median_difference = median(target 8件) - median(control 8件)`。
- stratified superiority は各 stratum の `P(target>control)+0.5P(tie)` の平均。
- pooled superiorityは全8×8 pair。
- CV は各群の8件をpoolした標本標準偏差 `(n-1)` / mean。
- 観測値は正を要求するため、正常な v3 artifact で CV が `null` になることはない。型としての `null` は現行 `Optional[float]` 射影のため残すが、独立再計算が非nullを返す場合の `null` は不一致で拒否する。

実物根拠: field 5件は [s1_stats.py:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_stats.py:39)、計算は [s1_stats.py:124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_stats.py:124)。

### 2.4 statistic・p・family

- 各 stratum で target 4 + control 4 を結合し、binary64 の完全一致を tie とする。
- 1-based average rankを2倍した整数にし、target 4件の和を取る。
- 2 strata の和が `statistic_rank_sum_x2`。
- 各 stratum の `C(8,4)=70` 全割付の直積4900件を列挙する。
- greater tail は `T >= T_obs`。同値を含む。
- `p_permutation.numerator` は該当割付数。distribution 自体は凍結しない。
- family は `p_star` numerator の最大。Holm補正ではない。

`families` は順に次の2件で、各要素は exact 6 keys:

| field | 制約 |
|---|---|
| `family` | `"S-1a"` または `"S-1b"` |
| `method` | literal `"intersection-union/max-p-star"` |
| `comparison_ids` | S-1a は対応9件、S-1b は3件。measurement順 |
| `p_family` | denominator=4900、numerator=`max(member p_star numerator)` |
| `reference_below_alpha` | `p_family.numerator * 80 <= 4900` |
| `judgment` | `"established"` / `"not_established"` |

実物根拠: 2倍整数 rank-sum と4900件は [s1_stats.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_stats.py:1)、inclusive tail は [s1_stats.py:144](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_stats.py:144)、family max は [s1_stats.py:175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_stats.py:175)。現行 report も max を使用し、Holm を未実施と明記している。[s1_report.py:704](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:704)

### 2.5 浮動小数演算

独立参照実装の規範は以下とする。

- 入力は frozen hex から binary64 へ一度だけ復号する。
- 加減乗除、平方根の各指定結果を IEEE-754 round-to-nearest, ties-to-even で binary64へ丸める。
- mean は入力 binary64を正確な有理数として合計し、`n` で割った結果を一度丸める。
- sample standard deviation は正確な有理数上の `Σ(x-mean_exact)^2/(n-1)` の平方根を一度丸める。
- CV は丸め済み standard deviation / 丸め済み mean。
- even-size median は中央2値を加算して丸め、2で除算して丸める。
- superiority は勝ち数と tie 数から正確な有理数を作り、最終値だけ丸める。
- 保存時に十進桁丸め、表示桁切捨てを行わない。

W-a は production の `statistics.*` を import せずこの定義を実装する。G1 projection が現行 `statistics.fmean/stdev/median` と一致しなければ、値を都合よく変更せず所見として設計へ戻す。

拒否 reason code:

| 条件 | reason code |
|---|---|
| schema / key / count / type | `schema.measurement.analysis-results` |
| comparison ID・順序・alternative不一致 | `contract.measurement.comparison-set` |
| statistic不一致 | `output.measurement.statistic-mismatch` |
| p numerator不一致 | `output.measurement.p-mismatch` |
| gate値・pass bool不一致 | `output.measurement.gate-mismatch` |
| 効果量不一致 | `output.measurement.effect-mismatch` |
| family構成・max不一致 | `output.measurement.family-mismatch` |
| 独立計算自体が完了不能 | `dependency.measurement.reference-evaluation-failed` |

---

## 3. A 前照合 audit

### 3.1 実行主体・時点

- 実行主体は **W-e の A 作成コマンドを操作する人間承認者**。
- A 作成コマンドは approval bytesを生成する前に audit を毎回実行し、全 check passでなければ A を作成しない。
- `H_v` は audit 開始時に一度だけ捕捉し、履歴到達可能性・replace/grafts/shallow検査にだけ使う。
- WAL bytes は worktree または `H_v` の treeから読まず、receipt が示す G の第1 parent **`H_gen=G^`** の tree blobから読む。

### 3.2 入力と照合順

1. `H_v`、receipt、G、`H_gen` を確定する。
2. G tree にある measurement v3 blob と receipt の hashを一致させる。
3. `/observations/wal_sources` の各 pathを正規化する。
4. 各 pathを `H_gen:path` の regular blobとして解決し、blob OID、raw SHA-256を一致させる。
5. blob bytesを全件 strict parseする。途中不正行、空行、CRLF、非LF終端、末尾切断をすべて拒否する。
6. 唯一の campaign-start、`env_tag`、campaign roleを照合する。
7. schedule順に session-start / unique commit / unique success resultを結合する。
8. 288件について locator ordinal、record hash、cell、lap、attempt、variant、value、origin hashを照合する。
9. frozen `/records` と WAL由来集合が順序を含め全単射であることを確認する。
10. 全 check passのときだけ A 作成へ進む。

A 側 receipt schema は `/observation_audit` に少なくとも次の exact interface objectを持たなければならない。この field の採否・配置確定はA草案との親合成が所有する。

```json
{
  "schema_version": "s1-observation-audit/v1",
  "generation_commit": "<40hex G>",
  "generation_basis_commit": "<40hex H_gen>",
  "measurement_sha256": "<64hex>",
  "wal_sources": [
    {
      "wal_source_id": "floor",
      "wal_path": "...",
      "wal_blob_oid": "<40hex>",
      "wal_sha256": "<64hex>",
      "record_count": 1009
    }
  ],
  "observation_count": 288,
  "status": "pass"
}
```

`wal_sources` は3件で、measurement の順序・値と同じ。失敗 reportを receipt に「pass」として格納する経路は禁止する。

Audit reason code:

| 条件 | reason code |
|---|---|
| path違反 | `input.wal.path-invalid` |
| H_genにblobなし | `input.wal.blob-missing` |
| regular blobでない | `input.wal.blob-type` |
| blob OID / raw hash不一致 | `input.wal.blob-mismatch` |
| WAL record不正 | `input.wal.record-invalid` |
| campaign-start不正・複数 | `contract.wal.campaign-start` |
| env/role不一致 | `contract.wal.campaign-binding` |
| session topology不一致 | `contract.wal.session-binding` |
| schedule不一致 | `contract.wal.schedule-binding` |
| fitness source不一致 | `contract.wal.value-binding` |
| 288件の非全単射 | `contract.measurement.observation-wal-mismatch` |
| 上記のいずれかによりAを拒否 | `authorization.observation-audit-failed` |

所有: audit implementation は **W-b**、H_gen tree readerは **W-a**、G1実物照合とAへの強制接続は **W-e**。

---

## 4. §13-3 — observation 伝播

`measurement /observations` と verifier の観測結果を区別するため、伝播 field 名は `freeze_verification_observation` とする。

### 4.1 `freeze_identity`

exact 10 keys:

| field | 型・制約 |
|---|---|
| `schema_version` | literal `"freeze-bundle-identity/v1"` |
| `lane` | `"legacy"` / `"permanent"` |
| `generation_number` | non-negative integer |
| `pointer` | exact `{path,raw_sha256}` |
| `receipt` | legacyは`null`、permanentは `{path,raw_sha256}` |
| `approval` | legacyは`null`、permanentは `{path,raw_sha256}` |
| `bundle_digest_sha256` | legacyは`null`、permanentは64hex |
| `generation_commit` | legacyは`null`、permanentは40hex G |
| `generation_basis_commit` | legacyは`null`、permanentは40hex H_gen |
| `artifacts` | exact keys `known`,`measurement`,`holdout` |

各 artifact ref は exact 3 keys:

```json
{
  "path": "<repo-relative>",
  "raw_sha256": "<64hex>",
  "schema_version": null
}
```

- legacy: `generation_number==0`、receipt/approval/digest/G/H_gen はすべて `null`。known/measurement の `schema_version` は現物に field がないため `null`、holdout は `"8b-holdout-freeze/v1"`。
- permanent: `generation_number>=1`、全 ref非null。artifact schemaは known v2 / measurement v3 / holdout v3。
- artifacts は同一 resolver 呼出しで一度だけ解決し、family別再読を禁止する。
- g1以降で legacy用 nullを許容しない。

現物根拠: knownとmeasurementに `/schema_version` はなく、holdoutだけ `/schema_version=="8b-holdout-freeze/v1"`。[known_axes_freeze.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:1)、[measurement_freeze.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/measurement_freeze.json:1)、[holdout_freeze.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s8b-freeze/holdout_freeze.json:1)。

### 4.2 `freeze_verification_observation`

exact 4 keys:

| field | 型・制約 |
|---|---|
| `schema_version` | literal `"freeze-verification-observation/v1"` |
| `validation_head` | 40hex `H_v` |
| `status` | campaignを開始できる値は literal `"pass"` |
| `reports` | legacyは4件、permanentは6件 |

report順:

- legacy: `pointer, known, measurement, holdout`
- permanent: `pointer, approval, receipt, known, measurement, holdout`

各 report は exact 5 keys:

| field | 型・制約 |
|---|---|
| `subject` | 上記 enum |
| `raw_sha256` | subject bytesの64hex |
| `schema_version` | stringまたは legacy未装備時のみ`null` |
| `status` | campaign-startでは literal `"pass"` |
| `passed_check_ids` | 当該 registry の全IDをregistry順に1回ずつ |

error / not-evaluated reportは loader の診断戻り値には存在できるが、campaign-start payloadへ書いて実行を続けてはならない。

所有 wave: schemaは **W-a**、resolverと全 consumer配線は **W-d**。

### 4.3 WAL campaign-start

WAL wrapper `{variant,stage,env_tag,ts,payload}` は変更しない。payloadだけをversioned exact schemaにする。

S-1 payload exact 6 keys:

```json
{
  "event": "campaign-start",
  "event_schema": "s1-campaign-start/v2",
  "campaign_role": "floor",
  "ts": "<RFC3339 string>",
  "freeze_identity": {},
  "freeze_verification_observation": {}
}
```

8b payload exact 8 keys:

```json
{
  "event": "campaign-start",
  "event_schema": "8b-oracle-campaign-start/v2",
  "manifest_sha256": "<64hex>",
  "block_id": "<string>",
  "campaign_id": "<string>",
  "execution_receipt": {},
  "freeze_identity": {},
  "freeze_verification_observation": {}
}
```

- S-1の現行 payload `{event,campaign_role,ts}` との差分は3 field追加。
- 8bの現行 `{event,manifest_sha256,block_id,campaign_id,execution_receipt}` との差分は3 field追加。
- active g1で v1 payload、field欠落、非pass観測を受け入れて実行してはならない。
- 歴史 WAL reader が v1を読むことは legacy/history専用 tagged branchに限る。

実物根拠: 現行S-1 campaign-startは [s1_direct_comparison.py:642](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:642)、8b payloadは [s8b_oracle_driver.py:1027](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1027)。

所有 wave: **W-d**。

### 4.4 S-1 report

新 report schema `"s1-direct-comparison-report/v2"` の top-level exact key-set:

```text
schema_version
freeze_identity
freeze_verification_observation
hard_gates
comparisons
families
effect_sizes
budget
generated_at_head
```

現行の `freeze_ref` は削除し、上記2 objectへ置換する。残りの nested schemaは現行 v1から変更しない。

- report対象3 performance WALの campaign-start identity / observationが canonical JSONとして完全一致しなければ、全比較を判定不能にする。
- 欠落・不一致を単なる report warningとして継続しない。
- 現行 reportは `freeze_ref`、hard gates、comparisons、families、effect sizes等を返す。[s1_report.py:750](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:750)

所有 wave: **W-d**。

### 4.5 Oracle report / judge

Oracle observations v2 の top-level exact key-set:

```text
schema_version
manifest_kind
manifest_sha256
n_per_cell
expected_cells
rows
freeze_identity
freeze_verification_observation
freeze_contract_reason_codes
```

- `schema_version=="8b-oracle-observations/v2"`。
- 先頭6 fieldは現行 v1 contractをそのまま維持する。
- `freeze_contract_reason_codes` は重複なし・昇順の string array。
- 全 campaign-startで identity / observation が一致し、全 reportがpassなら2 objectをcopyし reason arrayは空。
- 欠落・schema違反・campaign間不一致・非passなら2 objectを `null`、reasonを記録し、該当する全 rowを `protocol_violation` にする。

Oracle verdict v2 の exact key-set:

```text
schema_version
manifest_sha256
n_per_cell
status
reasons
holdouts
freeze_identity
freeze_verification_observation
freeze_contract_reason_codes
```

- `schema_version=="8b-oracle-verdict/v2"`。
- 後3 fieldは observationsから完全一致でcopyする。
- nullまたはreason非空なら `status=="indeterminate"`。
- judge側でidentityを再解決して都合よく置換してはならない。

伝播 reason code:

- `dependency.freeze-observation-missing`
- `schema.freeze-observation-invalid`
- `contract.freeze-identity-mismatch`
- `contract.freeze-observation-mismatch`
- `contract.freeze-observation-nonpass`

実物根拠: 現行 observations の6 keysは [s8b_oracle_report.py:1271](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1271)、現行 verdict の6 keysは [s8b_oracle_judge.py:259](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_judge.py:259)。現行 schema literalsは [s8b_oracle_artifacts.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_artifacts.py:20)。

所有 wave: **W-d**。

### 4.6 calibration successor

歴史物 `output/env/linux-baremetal/calibration/s1_verify_extime.json` は変更しない。

後継 path:

```text
output/env/<env_tag>/calibration/s1_verify_extime.v2.g<generation_number>.json
```

後継 top-level exact 12 keys:

```text
schema_version
config_name
env_tag
ccbench_commit
genome
freeze_identity
freeze_verification_observation
configuration_provenance
candidates
chosen_extime
limit_s
decision_rule
```

- `schema_version=="s1-verify-extime-calibration/v2"`。
- v1の `configuration_provenance` から `freeze_path`、`freeze_frozen_at_head`、`freeze_system_gate` を削除。
- 代わりに `known_entry_pointer` を追加する。値は literal `"/entries/read-heavy/system_gate"`。
- 他の exact keysは `workload,workload_flags,subset_name,gate_predicate,template_patch,src_token,binary_hash,build_cached,configure_cmd,build_cmd,free_disk_gb_at_start,known_entry_pointer`。
- candidates は1～3件で、extimeが `[3]`、`[3,6]`、`[3,6,10]` のいずれかのprefix。各 candidate の exact keysは現行11 keysを維持する。
- v2でidentity/observation欠落または非passなら calibrationを生成しない。

現物の top-level 9 keys、provenance 14 keys、candidate 11 keysは [s1_verify_extime.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/env/linux-baremetal/calibration/s1_verify_extime.json:1)。現行builderは [s1_verify_extime_calibration.py:393](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:393)。

所有 wave: **W-d**。

---

## 5. §13-4 — closed-world check registry

### 5.1 report共通規則

各 check resultは exact 4 keys:

```json
{
  "check_id": "measurement.cells",
  "status": "pass",
  "reason_code": null,
  "blocked_by": []
}
```

- `status`: `"pass"|"error"|"not_evaluated"`。
- pass: `reason_code==null`、`blocked_by==[]`。
- error: 当該IDに割り当てた単一reason、`blocked_by==[]`。
- not_evaluated: `reason_code=="dependency.blocked"`、`blocked_by` は1件以上。
- `blocked_by` は全件が同じregistry内で当該IDより前にあり、重複なし、registry順。これにより循環を構造的に禁止する。
- 全IDをregistry順にちょうど1回含む。error / not_evaluatedが1件でもあれば report全体を失敗とする。
- family-specific IDの通常失敗reasonは exact `contract.<check_id>`。下記common mappingだけ例外とする。

Common artifact IDs `C`、10件:

| ID | error reason |
|---|---|
| `document.raw-readable` | `document.read-failed` |
| `output.literal-root` | `output.root-mismatch` |
| `document.strict-json` | `document.json-invalid` |
| `schema.version` | `schema.version-mismatch` |
| `schema.exact-keys` | `schema.keys-mismatch` |
| `schema.generation-fields` | `schema.generation-invalid` |
| `lineage.supersedes` | `lineage.supersedes-mismatch` |
| `lineage.introduction` | `lineage.introduction-invalid` |
| `input.generation-tree-blob` | `input.tree-blob-mismatch` |
| `contract.reconstruction` | `contract.reconstruction-mismatch` |

ID grammarは `[a-z][a-z0-9]*(\.[a-z][a-z0-9-]*)+`。表示文言を変更してもIDとreasonを変更しない。

所有 wave: **W-a**。

### 5.2 known v2

exact setは `C` と次の11件の和、計21件。

```text
known.what
known.ccbench-pin
known.selection-rules
known.entries
known.s1b-pairing
known.reference-values-note
known.source-records
known.source-paths
known.source-tree-blobs
known.enumeration-snapshot
known.final-record-count
```

通常失敗reasonは `contract.<ID>`。

ただし後半5件のJSON pointerは §13-7/C1 の source-closure schema確定に依存する。親合成時にC1がこのID分割を採用し、各IDに一意な field pointerを割り当てるまでは「exact registry確定」と記録してはならない。

所有 wave: registry実装 **W-a**、predicate実装 **W-b**、source fieldとの最終結合は **C1親合成**。

### 5.3 measurement v3

exact setは `C` と次の20件の和、計30件。

```text
measurement.what
measurement.known-reference
measurement.ccbench-pin
measurement.cells
measurement.comparisons
measurement.s1b-pairing
measurement.operating-point
measurement.workload-flags
measurement.master-seed
measurement.schedule
measurement.schedule-hash
measurement.observations-shape
measurement.observations-bijection
measurement.wal-source-pointer-shape
measurement.analysis-shape
measurement.analysis-statistics
measurement.analysis-p-values
measurement.analysis-gates
measurement.analysis-effects
measurement.analysis-families
```

通常失敗reasonは `contract.<ID>`。WAL blobとの照合は static verifierには入れず、別のA前 audit check集合で扱う。

所有 wave: registry **W-a**、predicate **W-b**。

### 5.4 holdout v3

exact setは `C` と次の14件の和、計24件。

```text
holdout.what
holdout.lifecycle-stage
holdout.design-source
holdout.known-reference
holdout.match-convention
holdout.search-declaration
holdout.search-enumeration
holdout.holdouts
holdout.unknownness-snapshot
holdout.positive-control
holdout.derangement
holdout.confirmation
holdout.lifecycle-fields
holdout.measurement-closure
```

通常失敗reasonは `contract.<ID>`。`holdout.unknownness-snapshot` は凍結snapshot再計算だけを指し、launch時live searchを混ぜない。

所有 wave: registry **W-a**、predicate **W-c**。

### 5.5 receipt / approval / pointer

以下はA草案へ渡す必須 predicate 名である。

Receipt候補:

```text
receipt.inventory
receipt.inventory-completeness
receipt.successors
receipt.g-hgen-binding
receipt.output-tree-blobs
receipt.input-tree-closure
receipt.projection
receipt.removed-claims
receipt.metadata-moves
receipt.observation-audit
receipt.commit-topology
```

Approval候補:

```text
approval.bundle-digest
approval.receipt-reference
approval.verifier-reports
approval.observation-audit
approval.expiry
approval.commit-ancestry
approval.commit-diff
approval.human-trailer
approval.revocation
approval.unique-selection
```

Pointer候補:

```text
pointer.bundle-lockstep
pointer.approval-reference
pointer.parent
pointer.generation-step
pointer.no-fork
pointer.no-gap
pointer.no-rollback
pointer.revocation
pointer.approval-expiry
pointer.unique-tip
pointer.x-commit-diff
```

これらは現時点では **exact registryではない**。理由は、A担当の receipt / approval / pointer exact field schema、bundle digest、expiry表現がまだ提示されておらず、各IDを実在 field pointerへ結び付けられないためである。D75 (4) に従い、件数だけを先に確定したと主張してはならない。

親合成の停止条件:

1. A草案の各 fieldへ上記predicateを一対一で割り当てる。
2. predicateの分割・統合後に exact ID集合と件数を再発行する。
3. 各IDへ単一 reason codeを割り当てる。
4. B registry表とA schema表の相互参照を機械的に比較可能にする。

現行 ratified-v2 の下限根拠は approval/pointer key検査と一意chainを持つ [s8b_ratified_freeze.py:1050](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1050) および commit diff / ancestry検査 [s8b_ratified_freeze.py:1160](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1160)。新schemaのfield実物ではないため、そのfield名を恒久schemaへ流用していない。

---

## 6. `REQUIRED_FREEZE_NODES` 初期集合

型は `frozenset[str]`。各文字列は `test_file.py::test_function` 形式で、重複・parameter suffix・class nodeを禁止する。meta-testは collection結果に各nodeがちょうど1件存在することを検査する。

### 6.1 現在実在する node — 12件

```text
test_frozen_artifacts.py::test_frozen_artifacts_match_manifest
test_frozen_artifacts.py::test_manifest_shape_is_exact
test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes
test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control
test_s1_stats.py::test_three_fixed_distributions_match_independent_enumeration
test_s1_stats.py::test_effect_sizes_use_registered_definitions
test_s1_stats.py::test_p_star_and_family_p
test_s8b_ratified_freeze.py::test_root_bytes_scan_rejects_a_leaked_root
test_s8b_ratified_freeze.py::test_non_ancestry_user_commit_rejected
test_s8b_ratified_freeze.py::test_approval_commit_with_extra_file_rejected
test_s8b_ratified_freeze.py::test_generation_and_approval_same_commit_rejected
test_s8b_ratified_freeze.py::test_pointer_fork_and_cancellation_recovery
```

実在根拠: [test_frozen_artifacts.py:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:61)、[test_s1_stats.py:119](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_stats.py:119)、[test_s8b_ratified_freeze.py:937](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:937)。

### 6.2 新設予定 node — 14件

```text
test_freeze_permanent_io.py::test_check_registry_is_closed_world_for_every_schema
test_freeze_permanent_io.py::test_not_evaluated_blocked_by_is_existing_unique_and_acyclic
test_freeze_permanent_stats.py::test_conformance_vectors_match_independent_reference
test_s1_measurement_freeze_v3.py::test_observations_are_schedule_bijection_with_canonical_float_hex
test_s1_measurement_freeze_v3.py::test_analysis_results_match_independent_reference_for_all_twelve_comparisons
test_s1_measurement_freeze_v3.py::test_wal_source_audit_uses_h_gen_tree_blobs
test_s8b_holdout_freeze_v3.py::test_external_positive_control_baseline_mutant_revert
test_freeze_permanent_lineage.py::test_receipt_rederives_g_h_gen_and_all_input_blobs
test_freeze_permanent_lineage.py::test_approval_and_pointer_reject_fork_gap_rollback_expiry_and_revocation
test_freeze_bundle_resolver.py::test_bundle_is_resolved_once_without_family_mixing
test_freeze_observation_propagation.py::test_identity_and_observation_survive_wal_report_judge_and_calibration
test_frozen_artifacts.py::test_permanent_bundle_matches_literal_roots_and_exact_keyset
test_frozen_artifacts.py::test_g1_observations_match_h_gen_wal_blobs
test_frozen_artifacts.py::test_required_freeze_nodes_are_collectable_exactly_once
```

所有:

- W-a: 最初の3件。
- W-b: measurement 3件。
- W-c: holdout / lineage 3件。
- W-d: resolver / propagation 2件。
- W-e: `test_frozen_artifacts.py` 3件と `REQUIRED_FREEZE_NODES` literal本体。

最終集合は26件。新設nodeをmanifestへ入れるのは当該test実在後とし、W-e終了時に26件 exact setへ到達させる。

---

## 7. 所見

1. **P1 — 条件付き採用。** 新doc、正本§13からのpointer、`docs/README.md`登録は採用できる。ただし現時点で第1設計段自身も `tools/check_docs.py` の `LIVING_DOCS` に含まれていない。[check_docs.py:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:26) 一方、地図には登録済み。[docs/README.md:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/README.md:37) したがって「第1段と同じ扱い」は「lint済み」を意味しない。W-fで両docを登録するか、凍結文書として対象外にする根拠を明記する必要がある。

2. **P2 — 否認。** A/B/C1の完全並列は成立しない。Bのreceipt/approval/pointer registryはAのexact field schemaに、known source checkはC1のsource-closure fieldに依存する。並列にできるのは候補ID起草までであり、exact registry確定はA+C1後でなければならない。C2だけを後段に置く分割ではD75 (4)を再発させる。

3. **P3 — 条件付き採用。** 未実装moduleの変異を「仕様変異点・単一reason・検出test名」で事前登録する方式は採用できる。本草案で静的確認できた既存面は、WAL / S-1 report / oracle report / judge / calibrationに恒久identity/observation fieldが存在しないことまでである。W-0 hookおよびB範囲外consumerの「手前検査不在」を本草案だけから確認済みと扱ってはならない。

4. **P4 — 採用。** 本草案に「実装時に決める」は残していない。receipt/approval/pointer registryの未確定は実装者への委任ではなく、A/C1草案受領後に親が合成裁定する明示的停止条件である。

5. **P5 — 条件付き採用。** 符号化、field名、check-IDは親裁定でよい。ただし g1でcampaign-startの新field欠落を許す、WAL auditをH_genでなくworktree/H_vへ向ける、非pass observationでもjudgeをdeterminateにする変更は承認境界・機械防壁を弱めるため親裁定範囲を越える。その場合はユーザー裁定と§14損失行が必要。本草案はそれらを全て拒否するため、新たな損失表追記は不要。

6. **briefの「実在するWAL record識別子」はそのままでは誤り。** 現行WAL recordに `record_id` は存在しない。実在するのは物理行番号とraw record bytesであるため、本草案は blob SHA-256 + 1-based ordinal + raw-record SHA-256 の派生識別子を採った。

7. **現物 measurement freeze に `observations` / `analysis_results` は存在しない。** `/cells` はarrayではなく18-key objectである。第1段で混入した「既存field扱い」を再利用してはならない。

8. **統計 family は Holmではない。** 現行実装も `max(p_star)` で、reportのHolm fieldは `"not_performed..."` である。briefの「intersection–unionのmax」は採用、Holm解釈は否認する。

9. **`H_v` と `H_gen` は別用途。** audit時HEADをWAL blobの基準にするとR7に反する。WAL path/blob/value照合は必ず `H_gen=G^`、履歴到達可能性だけを捕捉済み `H_v` で行う。

10. **calibration歴史物は変更不可。** 現物は `freeze_path`、`freeze_frozen_at_head`、`freeze_system_gate` を持つ。後継schemaを同じpathへ上書きせず、generation付きv2 pathへ分離する必要がある。

11. **用語衝突がある。** measurementの凍結入力 `/observations` と、D73由来のverifier observationは別物である。同じ field 名 `observations` をWAL/reportへ使うと誤結合を招くため、後者を `freeze_verification_observation` とした。

12. **骨格との未解消矛盾は1件。** §13-4はreceipt/approval/pointerを含む「schemaごとの全列挙」を要求する一方、親briefはそのexact schemaをAとBで並列起草するとしている。Aのfield schemaなしにBが全列挙を確定することはD75 (4)と両立しない。親合成でP2を修正しない限り、第2設計段パッケージをexact完了として閉じてはならない。
---

# 段 2c: codex 草案 C1 (closure/pin)

# 草案 C1 — freeze 族恒久設計「第 2 設計段」§13-6 / §13-7

> 本草案は read-only の静的照合による。テスト結果は主張しない。`MUST` は拒否条件を含む規範、`観測値` は 2026-07-22 の checkout に対する参考値であり schema の固定件数ではない。

## 1. §13-6 — `pre_oracle_head` の内容 pin 化

### 1.1 現行経路の実測

| 経路 | 現行動作 | 実物根拠 |
|---|---|---|
| schema | top-level 11 field の一つとして `pre_oracle_head` を要求 | `orchestrator/campaign/s8b_selector_freeze.py:73-77` |
| 生成 | 呼出側が渡した値を 40 桁 lowercase hex とだけ検査して格納 | 同 `:554-589` |
| runner | `materialize_predictions(..., pre_oracle_head: str)` がそのまま builder へ転送 | `orchestrator/campaign/s8b_prediction_runner.py:535-559` |
| verify | 形式検査後、`git cat-file -e <sha>^{commit}` による「任意の実在 commit」だけを要求。tree/blob 内容との対応、HEAD、ancestor、生成入力との対応は検査しない | `s8b_selector_freeze.py:158-172,618-623` |
| consumer | `s8b_verdict.verify_prediction()` が全体 verifier を呼ぶが、`pre_oracle_head` 自体を意味消費しない | `orchestrator/campaign/s8b_verdict.py:186-213` |
| test | 空 commit を正例としており、内容を持たない commit でも通る | `orchestrator/tests/test_s8b_selector_freeze.py:42-58,456-465` |
| 成果物 | `output/s8b-freeze/selector_predictions.json` は tracked tree に存在しない | `s8b_selector_freeze.py:52-53` の予定 path。`git ls-files` 実測では absent |

repository-wide `git grep` では、上記以外の production 消費はない。したがって現行 field は「oracle 前であること」も「生成に使った内容」も証明せず、rebase で SHA だけが失効し得る。

### 1.2 採用形: commit field を tree 内容 anchor に一対一置換する

#### Exact 定義

prediction schema を `"8b-selector-prediction-freeze/v2"` に上げ、既存 path `output/s8b-freeze/selector_predictions.json` の初回生成に用いる。tracked v1 成果物は存在しないため bytes 上書きは生じない。既存ファイルが作業 tree に存在する場合は従来どおり exclusive-create で拒否する。

v2 top-level は次の **exact 11 field** とし、未知・欠落 field を拒否する。

```json
{
  "schema_version": "8b-selector-prediction-freeze/v2",
  "generated_at": "...",
  "pre_oracle_tree": {
    "schema_version": "8b-pre-oracle-tree/v1",
    "git_object_format": "sha1",
    "tree_oid": "<40 lowercase hex>",
    "entry_count": 1,
    "manifest_sha256": "<64 lowercase hex>"
  },
  "sources": {},
  "selector_basis_sha256": "...",
  "execution_policy": {},
  "static_default": {},
  "derangement": {},
  "rows": [],
  "swapped_follow_expectations": [],
  "body_sha256": "..."
}
```

`pre_oracle_tree` は exact 5 field object。

- `schema_version`: string、literal `"8b-pre-oracle-tree/v1"`。
- `git_object_format`: string、literal `"sha1"`。現 repo の `git rev-parse --show-object-format` 実測値。object format 移行時は schema bump を要し、長さの自動推測は禁止。
- `tree_oid`: string、40 桁 lowercase hex。生成時の `HEAD^{tree}`。
- `entry_count`: bool を除く正整数。下記 manifest の要素数と一致。
- `manifest_sha256`: 64 桁 lowercase hex。下記 canonical manifest bytes の SHA-256。

`pre_oracle_head` は v2 では禁止 field であり、両 field の併存も認めない。

#### tree manifest の exact 符号化

`tree_oid` を再帰走査して directory 自体を除く全 leaf entry を列挙する。path は UTF-8 で decode できる NFC 未変換の repo-relative POSIX path とし、UTF-8 bytes の昇順で並べる。重複 path、絶対 path、空 component、`.`、`..`、NUL、backslash を拒否する。

通常 blob と symlink は次の object。

```json
{"mode":"100644","path":"path/to/file","sha256":"<raw blob sha256>"}
```

`mode` は `"100644"`, `"100755"`, `"120000"` のいずれか。`sha256` は blob raw bytes の SHA-256。

gitlink は次の object。

```json
{"commit_oid":"<40 lowercase hex>","mode":"160000","path":"external/ccbench"}
```

未知 mode、mode/type 不一致、読めない blob/gitlink を拒否する。manifest 全体を JSON array とし、現行 `_canonical_bytes()` と同じ

```text
UTF-8 / ensure_ascii=false / sort_keys=true / separators=(",",":") / allow_nan=false
```

で直列化する。その要素数が `entry_count`、SHA-256 が `manifest_sha256` でなければならない。現行 canonical JSON 根拠は `s8b_selector_freeze.py:98-113`。

#### 一意性

- schema 内の `pre_oracle_tree` は 1 件のみ。
- manifest path は全件一意。
- official prediction path の導入 commit `G_pred` は、verifier-view commit `H_v` から到達可能な履歴上で `--diff-filter=A` がちょうど 1 件。
- `G_pred` は非 merge、diff は `output/s8b-freeze/selector_predictions.json` 1 ファイルの追加だけ。
- delete/re-add、rename 導入、複数追加候補を拒否。
- `H_pred = G_pred^` とし、`pre_oracle_tree.tree_oid == H_pred^{tree}` を要求する。

この形なら commit SHA は成果物へ格納せず、rebase で commit ID だけが変化しても parent tree 内容が同一なら field は不変である。parent tree 内容が変化した rebase は、旧 prediction を再利用せず再生成する。

#### 実物根拠

- commit 自己 field 廃止と `G^` 入力 tree 束縛の骨格: `docs/freeze-permanent-design.md:221-246`。
- 現行 field が caller-supplied: `s8b_selector_freeze.py:554-575`、`s8b_prediction_runner.py:541-555`。
- 現行 source は exact 5 key、各 `{path, sha256}`: `s8b_selector_freeze.py:63-65,398-412`。
- 現行 body hash は field 全体を覆う: 同 `:571-589,602-606`。
- 導入 commit を一意導出する設計の同型元: `freeze-permanent-design.md:227-240`。

#### 実装 wave

**W-d 所有**。W-e 開始の hard prerequisite とし、W-f 発効時には v1 official consumer を残してはならない。

### 1.3 生成 gate

#### Exact 定義

`materialize_predictions()` から `pre_oracle_head` 引数を削除し、caller が tree anchor を自己申告する API を廃止する。

生成順は次のとおり。

1. `sources` の exact 5 record、非 null の全 `rows[*].raw_response_path/raw_sha256`、journal 射影を確定する。
2. 現 `HEAD^{tree}` を一度取得して `H0` とする。
3. 全 `sources` と raw response path が `H0` に mode `100644` または `100755` の blob として存在し、記録 SHA-256 と一致することを確認する。symlink、gitlink、worktree-only file を拒否する。
4. 同 path の worktree bytes も `H0` blob と一致させる。これは使用 bytes と記録 tree の TOCTOU 防止であり、official static verify の worktree gateではない。
5. `pre_oracle_tree` と document/body hash を構築する。
6. atomic link の直前に再度 `HEAD^{tree}` を取得し、`H0` と異なれば書き込まず拒否する。
7. exclusive-create する。
8. publish 時は `G_pred` を prediction file 1 件追加だけの commit とし、`G_pred^` tree が `H0` であることを post-commit verifier が確認する。

raw response を parent tree に置けない現在の runner 配置はこの gate を満たさない。W-d は raw evidence を `G_pred` より前に tracked、immutable な path へ確定する必要がある。prediction と raw response の同一 commit 追加は `H_pred` 入力 tree 束縛を満たさないため禁止する。

#### 拒否 reason code

| reason code | 単一拒否理由 |
|---|---|
| `selector-pre-oracle-legacy-field` | v2 に `pre_oracle_head` が存在する |
| `selector-pre-oracle-field-set` | `pre_oracle_tree` の field 集合が exact 5 field でない |
| `selector-pre-oracle-object-format` | `git_object_format != "sha1"` |
| `selector-pre-oracle-tree-oid` | `tree_oid` の型・40hex が不正 |
| `selector-pre-oracle-tree-missing` | tree object を読めない |
| `selector-pre-oracle-path` | manifest path が UTF-8/正規 repo-relative path でない |
| `selector-pre-oracle-entry-duplicate` | manifest path が重複 |
| `selector-pre-oracle-mode` | mode/type が許可集合外または不一致 |
| `selector-pre-oracle-entry-count` | `entry_count` が正整数でない、または再列挙件数と不一致 |
| `selector-pre-oracle-manifest-sha256` | canonical manifest SHA-256 が不一致 |
| `selector-pre-oracle-source-missing` | source/raw path が parent tree にない |
| `selector-pre-oracle-source-mode` | source/raw path が通常 blob でない |
| `selector-pre-oracle-source-sha256` | source/raw blob と記録 SHA-256 が不一致 |
| `selector-pre-oracle-worktree-drift` | 生成に使う worktree bytes と parent tree blob が不一致 |
| `selector-pre-oracle-head-changed` | capture 後、exclusive-create 前に HEAD tree が変化 |
| `selector-pre-oracle-introduction-count` | `G_pred` 候補が 1 件でない |
| `selector-pre-oracle-introduction-merge` | `G_pred` が merge |
| `selector-pre-oracle-introduction-diff` | `G_pred` が prediction 1 file 追加以外を含む |
| `selector-pre-oracle-readd` | delete/re-add または rename 導入 |
| `selector-pre-oracle-parent-tree` | `G_pred^` tree と記録 `tree_oid` が不一致 |

複数所見は全件収集するが、同じ破壊点について上表の reason code を複数重ねない。

#### 実物根拠

現行は build 時に形式しか見ず、verify 時も commit 実在だけである (`s8b_selector_freeze.py:565-566,618-626`)。source の現物照合は current root file 読みである (`:130-155,624-626`)。これを parent tree blob 読みに置換する。

#### 実装 wave

W-d。post-commit `G_pred` 検査の共通 git helper は W-a の四型/error carrier を利用してよいが、この reason code 集合と selector schema の所有は W-d。

### 1.4 検証・consumer gate

#### Exact 定義

- candidate verifier と published verifier を分ける。
  - candidate verifier: schema/body/tree manifest/source blob を検査。
  - published verifier: candidate 検査に加え `G_pred/H_pred` 一意導出を検査。
- official consumer は published verifier が返す typed object だけを受理する。
- `s8b_verdict.PREDICTION_SCHEMA` は v2 literal に更新し、`verify_prediction()` は published verifier を呼ぶ。
- v1 dict、candidate-only typed object、生 dict の fallback 受理を禁止する。
- `pre_oracle_tree` を downstream judge が直接意味消費してはならない。tree 検査は verifier 境界で完結させる。

現行 typed boundary は `s8b_verdict.py:186-213` に存在するため、置換先がある。

#### 実物根拠

- `VerifiedPrediction` 境界: `s8b_verdict.py:186-213`。
- CLI も現在は同じ verifier を呼ぶ: `s8b_selector_freeze.py:723-768`。
- floor/oracle launch 側には prediction 必須 gate が存在しない。これは後記所見 2。

#### 実装 wave

W-d。W-f の X 前受入条件に「official selector consumer が v2 published verifier 以外を通らない」ことを置く。

### 1.5 移行

#### Exact 定義

1. W-d で v2 schema、tree capture、candidate/published verifier、runner/verdict consumer を dormant 導入。
2. tracked v1 JSON は存在しないため変換・削除は 0 件。既存 path にファイルがあれば上書きせず停止。
3. W-e より前に W-d の code path と direct tests を完了させる。W-e は v1 prediction を生成しない。
4. W-f は v2 published typed object のみ active にする。
5. `G_pred` を rebase 予定のある wave branch で canonical publish しない。`G_pred` 確定後に parent tree が変わる操作をした場合は prediction を再生成する。

#### 実物根拠

§12 は本項を W-e/W-f の前提とするが owner を未確定としている (`freeze-permanent-design.md:440-442`)。本草案は owner を W-d に確定する。

#### 実装 wave

W-d 実装、W-e prerequisite 検査、W-f activation。

---

## 2. §13-7 — source closure の宣言確定

### 2.1 現行 record の exact 実測

現行 source record は `_source()` が作る次の二型である。

```json
{"path":"<string>","sha256":"<64hex>","key":"<string>"}
```

または

```json
{
  "path":"<string>",
  "sha256":"<64hex>",
  "key":"<string>",
  "lines":["<string>", "..."]
}
```

実物根拠:

- builder: `orchestrator/campaign/s1_known_axes_freeze.py:99-106`。
- recursive 収集: 同 `:682-697`。
- current worktree bytes 照合: 同 `:729-744`。
- JSON pointer: `output/s1-freeze/known_axes_freeze.json` の `/entries/*/*/sources/*`。

現物集計は 63 record、31 unique path。field 組は `{path,sha256,key}` が 57 件、`lines` 付きが 6 件。`lines` 付きは `/entries/*/stock_common/sources/{0,1}` で、5 行または 3 行の string array。

24 record / 6 実装ファイルは次の exact multiset。

| path | record 件数 | JSON pointer |
|---|---:|---|
| `orchestrator/campaign/axis_trigger_gating.py` | 6 | `/entries/*/{system_gate,ident_all}/sources/*` |
| `orchestrator/campaign/s8a_trigger_sweep.py` | 6 | 同上 |
| `orchestrator/campaign/backoff_sweep.py` | 3 | `/entries/*/backoff_fixed_best/sources/1` |
| `orchestrator/campaign/genome.py` | 3 | `/entries/*/p2_2_flag_opt/sources/1` |
| `orchestrator/campaign/s6_sort_sweep.py` | 3 | `/entries/*/sort_best/sources/*` |
| `orchestrator/campaign/p3_s4_loop_sort.py` | 3 | 同上 |

合計 24。これは R7(b) の対象である (`docs/freeze-permanent-design.md:391-396`)。

### 2.2 known v2 `/source_closure` schema

#### Exact 定義

known v2 に新しい `G` field `/source_closure` を 1 件追加する。

```json
{
  "schema_version": "s1-known-source-closure/v1",
  "records": [
    {
      "record_type": "implementation_dependency",
      "path": "orchestrator/campaign/model.py",
      "sha256": "<64 lowercase hex>",
      "key": "Genome;Genome.__post_init__;Genome.canonical"
    }
  ],
  "file_enumerations": [
    {
      "enumeration_id": "p2_2_wal/balanced",
      "algorithm": "git-tree-glob/v1",
      "pattern": "output/campaigns/p2-2-silo-balanced-enumerate-*/runs/wal.jsonl",
      "members": [
        {
          "path": "output/campaigns/.../runs/wal.jsonl",
          "disposition": "included"
        }
      ],
      "file_count": 1
    }
  ]
}
```

`source_closure` は exact 3 field。

- `schema_version`: literal string。
- `records`: array。最終件数は H_gen から導出し、literal 固定しない。
- `file_enumerations`: **exact 8 element**。ID 集合は後記の 8 件。

`records[*]` は exact 4 field。

- `record_type`: `"implementation_dependency" | "campaign_lock" | "enumeration_classifier"`。
- `path`: nonempty、正規化済み repo-relative POSIX string。
- `sha256`: raw blob の 64 lowercase hex SHA-256。
- `key`: nonempty string。型別の exact 値は下表。

records は `path` 昇順、path 一意。同じ path が既存 `/entries/.../sources` にもある場合、重複 occurrence は許すが SHA-256 は完全一致しなければならない。

既存 `/entries/*/*/sources/*` は上記の現行二型を維持し、未知 field を拒否する。`lines` は存在する場合、1 件以上の nonempty string array。source array 内の完全重複 record を拒否する。異なる entry 間の意図的な重複は、24 record の意味を維持するため許す。

#### implementation dependency の exact 初期集合

| path | `key` | 根拠 |
|---|---|---|
| `orchestrator/campaign/pipeline.py` | `variant_id` | known generator の import `s1_known_axes_freeze.py:27`、実体 `pipeline.py:44-50` |
| `orchestrator/campaign/model.py` | `Genome;Genome.__post_init__;Genome.canonical` | direct import `s1_known_axes_freeze.py:26`、実体 `model.py:31-55` |
| `orchestrator/campaign/source_digest.py` | `STOCK` | `variant_id` default が `source_digest.STOCK`、`pipeline.py:44-50`、定義 `source_digest.py:60,73` |

この 3 path は exactly 1 record ずつ。標準 library は record に含めず、Python version は §3 の `M` 契約に従う。

pipeline のその他の direct import (`calibrator`, `verifier`, `buildcache`, `wal`, `layout`, `lock`, `env_contract` 等、`pipeline.py:29-41`) は、`variant_id` の値導出 sliceから参照されないため初期集合へ含めない。この除外は R16 の「宣言済み closure」のレビュー限界として扱い、機械的完全証明とは主張しない。

#### 実物根拠

- known generator direct import: `s1_known_axes_freeze.py:24-27`。
- `variant_id` の全値依存: `pipeline.py:44-50`。
- `Genome.canonical`: `model.py:31-55`。
- `STOCK`: `source_digest.py:60,73`。
- §3.1 はこの 3 code path と campaign.lock を不足として明記: `freeze-permanent-design.md:105-119`。

#### 実装 wave

W-b。reason carrier の型だけ W-a を利用する。

### 2.3 列挙 snapshot

#### Exact 定義

`file_enumerations` の `enumeration_id` と `pattern` は次の exact 8 組。

| `enumeration_id` | exact `pattern` | member 基数 |
|---|---|---|
| `p2_2_wal/balanced` | `output/campaigns/p2-2-silo-balanced-enumerate-*/runs/wal.jsonl` | 1 以上 |
| `p2_2_wal/write-heavy` | `output/campaigns/p2-2-silo-write-heavy-enumerate-*/runs/wal.jsonl` | 1 以上 |
| `p2_2_wal/read-heavy` | `output/campaigns/p2-2-silo-read-heavy-enumerate-*/runs/wal.jsonl` | 1 以上 |
| `backoff_wal/balanced` | `output/campaigns/backoff-sweep-silo-balanced-sweep-*/runs/wal.jsonl` | 1 以上 |
| `backoff_wal/write-heavy` | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-*/runs/wal.jsonl` | 1 以上 |
| `backoff_wal/read-heavy` | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-*/runs/wal.jsonl` | 1 以上 |
| `sort_remeasure_provenance/balanced` | `output/campaigns/p3-s6-sort-sweep-balanced-sweep-*/reports/s6_sort_sweep_provenance.json` | 1 以上 |
| `sort_remeasure_provenance/write-heavy` | `output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-*/reports/s6_sort_sweep_provenance.json` | 1 以上 |

`algorithm` は literal `"git-tree-glob/v1"`。その意味は、H_gen superproject tree の mode `100644/100755` leaf path 全件から、`*` を「`/` を含まない 0 文字以上」に写す上表 pattern の完全一致集合を得ること。worktree `Path.glob()` は static verify の入力にしない。

`members` は path 昇順、path 一意。各 element は exact 2 field `{path, disposition}`。`file_count` は bool を除く非負整数で `len(members)` と一致する。

p2/backoff の disposition:

- `included`
- `screening-excluded`

各 member `.../runs/wal.jsonl` について sibling `.../campaign.lock` を必須とし、strict JSON として duplicate key、非 object、非有限値を拒否する。`/search_config` は object 必須。その key 集合に `"screening"` が存在すれば `screening-excluded`、存在しなければ `included`。値の truthiness は見ない。各 enumeration は `included` を 1 件以上持つ。

これは現行 `_exclude_screening_campaigns()` の実際の判定である (`s1_known_axes_freeze.py:147-167`)。

sort の disposition:

- `trial-mismatch`
- `missing-wal`
- `screening-excluded`
- `eligible-remeasure`

順序は次のとおり。

1. provenance `/trial` が string で `"p3-s6-sort-sweep-remeasure"` prefix でなければ `trial-mismatch`。
2. prefix 一致だが sibling `runs/wal.jsonl` が H_gen tree に無ければ `missing-wal`。
3. WAL があれば campaign.lock を上記と同じ規則で読む。`screening` key があれば `screening-excluded`。
4. それ以外を `eligible-remeasure`。
5. balanced/write-heavy はそれぞれ `eligible-remeasure` が exactly 1。

現行経路は `s1_known_axes_freeze.py:361-373,386-455`。

#### `records` の動的 exact 集合

`records[*].path` の集合は次の union と完全一致しなければならない。

1. 上記 implementation dependency 3 path。
2. p2/backoff の全 member に対応する全 `campaign.lock`。
3. sort member のうち `/trial` prefix 一致かつ companion WAL が存在するものの全 `campaign.lock`。
4. sort 2 enumeration の全 provenance member path。

型と key:

- 1: `record_type="implementation_dependency"`、前表の key。
- 2/3: `record_type="campaign_lock"`, `key="/search_config"`。
- 4: `record_type="enumeration_classifier"`, `key="/trial"`。

したがって record 数は

```text
|implementation dependency 3 path ∪ 実際に読んだ campaign.lock path ∪ sort enumeration member path|
```

であり、生成時に H_gen から決まる。`63+4`、`76`、その他の整数 literal を schema gate にしてはならない。

2026-07-22 checkout の観測値は 8 snapshot / 12 member、実際に読む campaign.lock は 10 path だが、これは schema 固定値ではない。

#### 実物根拠

- p2 glob: `s1_known_axes_freeze.py:241-266`。
- backoff glob: 同 `:276-315`。
- sort glob/classifier: 同 `:361-373`。
- 現物 campaign.lock の判定対象 field: JSON pointer `/search_config`。
- 現行 holdout の `/search/file_enumeration` は string であり member array ではない: `output/s8b-freeze/holdout_freeze.json:18-37`、generator `s8b_holdout_freeze.py:94-99,345-352`。本 schema はその列挙規約文字列ではなく、member 集合まで固定する強化形である。

#### 実装 wave

W-b。

### 2.4 H_gen tree blob 照合

#### Exact 定義

official static verify では、既存 `/entries/.../sources` 63 件相当の再構成集合と新 `/source_closure/records` の全件を、receipt から得た **H_gen tree** に対して検査する。current HEAD/worktree を source correctness gate にしてはならない。

superproject record:

1. `H_gen:path` を引く。
2. mode `100644/100755` の blob 1 件であること。
3. raw blob SHA-256 が record `/sha256` と一致すること。

`external/ccbench/...` record:

1. H_gen superproject tree の `external/ccbench` が mode `160000` gitlink であること。
2. gitlink OID が known `/ccbench_pin` の 40 桁 SHA と完全一致すること。
3. submodule repository の `<ccbench_pin>:<subpath>` が mode `100644/100755` blob であること。
4. raw blob SHA-256 が record と一致すること。

H_gen superproject tree は `external/ccbench/cmake/Options.cmake` 等の blob を直接持たず gitlink のみなので、この二段解決を省略してはならない。現物 gitlink と `/ccbench_pin` はともに `d706650cdb31e442bef45b9b4216951d4fb40969`。

worktree 照合の扱い:

- 24 record / 6 実装ファイル: **全件 H_gen tree blob 照合**。R7(b)。
- 残りの既存 source record: **全件 H_gen tree または ccbench pin tree 照合**。§6。
- 新 `source_closure.records`: **全件 H_gen tree blob 照合**。
- static verify で worktree 照合を残す record 型: **0 件**。
- worktree 比較は §7-G の生成前 guard としてのみ実行し、record bytes と H_gen blob の一致を確認する。これは official artifact の受理条件を current worktree drift に結び直すものではない。
- `provenance_unverified` 内の generator/related implementation hash は `M` なのでこの照合対象外。

#### 拒否 reason code

| reason code | 単一拒否理由 |
|---|---|
| `known-source-closure-field-set` | `/source_closure` または子 object の field 集合不一致 |
| `known-source-record-field-set` | record field 集合不一致 |
| `known-source-record-type` | `record_type` が許可集合外 |
| `known-source-record-path` | path が正規 repo-relative POSIX string でない |
| `known-source-record-order` | records/source member が規定順でない |
| `known-source-record-duplicate` | 一意性違反 |
| `known-source-record-sha256` | SHA-256 の型・64hex が不正 |
| `known-source-alias-sha256` | 同じ path の既存/new occurrence で hash が異なる |
| `known-source-implementation-set` | implementation dependency 3 path/key 集合不一致 |
| `known-source-enumeration-id-set` | 8 ID に未知・欠落・重複がある |
| `known-source-enumeration-contract` | ID と algorithm/pattern の対応不一致 |
| `known-source-enumeration-member` | member path/schema/順序/重複が不正 |
| `known-source-enumeration-count` | `file_count` と member 数が不一致 |
| `known-source-enumeration-tree-mismatch` | H_gen 再列挙集合と snapshot が不一致 |
| `known-source-disposition` | disposition が再導出結果と不一致 |
| `known-source-included-empty` | p2/backoff の included が 0 件 |
| `known-source-remeasure-cardinality` | sort eligible が exactly 1 でない |
| `known-source-lock-missing` | 必須 campaign.lock blob がない |
| `known-source-lock-json` | campaign.lock が strict JSON object でない |
| `known-source-lock-search-config` | `/search_config` が object でない |
| `known-source-tree-missing` | H_gen に record path がない |
| `known-source-tree-mode` | record path が通常 blob でない |
| `known-source-tree-sha256` | H_gen blob raw SHA-256 不一致 |
| `known-source-ccbench-gitlink` | gitlink と `/ccbench_pin` が不一致 |
| `known-source-ccbench-blob` | submodule pin tree の path/mode/hash 不一致 |
| `known-source-worktree-drift` | 生成時 worktree bytes と H_gen blob が不一致 |

#### 実物根拠

- §6 は全 source record、campaign.lock、ccbench gitlink の H_gen 束縛を要求: `freeze-permanent-design.md:234-240`。
- R7(b): 同 `:391-396`。
- 現行 verifier の worktree resolver は `s1_known_axes_freeze.py:729-744` であり、置換対象。
- 現行 `ccbench_pin` 検査は submodule current HEAD 依存: 同 `:755-757`。これも H_gen gitlink 起点へ置換する。

#### 実装 wave

W-b が generator/verifier/direct testsを所有。W-e receipt verifier が同じ H_gen を渡し、g1 projection audit を実行する。

### 2.5 g1 移行と件数規則

#### Exact 定義

- g1 は raw hash で固定された legacy known artifact を読み、既存 `/entries/.../sources` 全 occurrence を path/sha256/key/lines の順序込みで 1:1 射影する。
- generic verifier に `len == 63` を置かない。g1 transition audit は legacy artifact から導出した件数との一致を検査するため、現物では結果的に 63 となる。
- 24 record / 6 implementation path の legacy subset は同じ occurrence 数を維持し、照合先だけを worktree から H_gen tree へ変更する。
- `/source_closure` の final records 数は H_gen 列挙から生成する。
- G の publish base が変わり H_gen の enumeration/member/hash が変化した場合、hash の手編集ではなく known v2 全体を再生成する。
- receipt の projection audit は、legacy source multiset、追加 closure set、8 enumeration snapshot の三面を独立に照合する。

#### 実物根拠

- 現行 63 record は JSON pointer `/entries/*/*/sources/*` の全列挙。
- 最終件数を生成時確定とする骨格: `freeze-permanent-design.md:111-119`。
- g1 は legacy 現物からの機械射影: 同 `:307-314`。

#### 実装 wave

W-b で dormant generator/verifier、W-e で最終 H_gen に対する生成・receipt audit。W-f は approved bundle の activation のみ。

---

## 3. 親 provisional 裁定 P1..P5 への回答

### P1 — 部分採用、一部否認

新設 `docs/freeze-permanent-design-s2.md`、正本 §13 の状態行＋pointer、`docs/README.md` 登録は採用。

`tools/check_docs.py` の `LIVING_DOCS` 追加を W-f まで送る案は否認する。現物では第1段 `freeze-permanent-design.md` 自体も `LIVING_DOCS` に入っておらず、これは「同じ扱い」の安全な前例ではなく lint 網の欠落である (`tools/check_docs.py:26-47`; `docs/README.md:37`)。

決定権者は親。選択肢は次の二つに限定する。

1. 第1段・第2段を living design として本設計 wave で両方 `LIVING_DOCS` に追加する。
2. 第2段を裁定時点で凍結 package と明記し、living lint 対象外とする。

「living のまま W-f まで lint 対象外」は採らない。

### P2 — 条件付き採用

A/B/C1 の並列起草と、C2 を統合後に行う順序は採用。ただし C1 は A の receipt schema 完成を待たず、§13-6 を tree 内容 anchor として閉じる。C1 の reason code は B の registry が後から改名するのではなく、上記 literal を registry 初期集合へ取り込む。C2 は W-d/W-b の owner と file 衝突を解消する。

### P3 — 採用

未実装 module は仕様レベルの変異点＋単一 reason code＋仕様上の test node を事前登録し、実コードでの単一理由性は各実装 wave 受入で確認する形を採用。

既存 C1 面については静的確認済み。

- `pre_oracle_head` の手前検査は build の 40hex と verify の commit 実在だけ。
- `s8b_verdict.verify_prediction()` は verifier を迂回しない。
- floor/oracle launch は prediction を要求していない。

### P4 — 採用

本草案に field 名・型・件数規則・一意性・拒否規則・reason code・owner を列挙した。「実装時に決める」は残さない。

唯一の親判断事項は、現物と矛盾する「holdout と同型」の文言を、本草案の member snapshot 強化形へ訂正するかどうか。決定権者は親であり、W-b 実装者へ委譲しない。

### P5 — 採用

符号化、ID、初期集合、tree manifest は受理集合を広げない強化なので親裁定範囲。

次の代替は受理集合を広げるため親裁定では不可。

- `pre_oracle_head` を単純削除し、tree/導入 topology gate を置かない。
- enumeration member を格納せず、holdout 現物と同じ説明文字列＋件数だけにする。
- H_gen blob の代わりに current worktree を許す fallback。

これらを選ぶ場合だけ、§14 損失表への追記とユーザー裁定が必要。本草案の採用形には §14 追記を要しない。

---

## 4. 所見

1. **brief／§3.1 の「holdout `search.file_enumeration` と同型の列挙 snapshot」は実物と不一致。** `/search/file_enumeration` は string で、member path を一件も持たない。`top_level_dirs/file_count/skipped_binary_count/excluded_paths` も集合を一意に復元できない。literal 同型採用は不可。親が本草案の member snapshot 強化形へ文言を訂正する必要がある。

2. **`pre_oracle_head` は pre-oracle 順序 gate ではない。** 任意の空 commit でも受理され、floor/oracle 出力の不存在・生成順序を検査しない。また oracle/floor launch に prediction 必須 consumer がない。tree 内容 pin は dangling を解消するが、情報閲覧順序そのものは別の launch gate／運用規律である。これを tree field だけで「HARKing を機械排除」と主張してはならない。

3. **公式 selector prediction artifact は未生成。** migration 対象となる v1 bytes は 0 件。したがって v2 初回生成が可能だが、ローカル既存ファイルを削除して進める運用は認めない。

4. **campaign.lock は「1 record」ではない。** 現 checkout では実際に読む lock は p2 3、backoff 5、sort 2 の計 10 path。glob/member 状態で変化するため、`63+4` その他の total literal は誤り。

5. **§6 の「H_gen tree blob」は ccbench 内ファイルへ直接適用できない。** superproject tree が持つのは `external/ccbench` gitlink だけである。ccbench source record は H_gen gitlink → pinned submodule tree → blob の二段解決が必要。

6. **P1 の「第1段 doc と同じ扱い」は lint coverage の根拠にならない。** 第1段 doc は現在 `LIVING_DOCS` 外である。

7. **§12 は `pre_oracle_head` 作業を W-e/W-f 前提とするが owner を持たない。** 本草案は W-d 所有に確定した。C2 の exact file ownership 表はこれを反映しなければならない。

8. **pipeline の full import graph と値依存 slice は同一ではない。** 初期 closure は `variant_id → source_digest.STOCK / Genome.canonical` の実際の値依存へ限定した。pipeline の他 import を含めないことは R16 の宣言 closure 限界であり、完全 import 証明とは呼ばない。
---

# 段 2d: codex 草案 C2 (所有表+変異登録)

# 草案 C2 — freeze 族恒久設計「第 2 設計段」§13-8 / §13-9

> 基準: 2026-07-22、`HEAD=6a8f5524bfa82410937cc72a8393a76c0005e5d8`。  
> 照合方法: 現行コード・現物 JSON・Git tree の静的照合のみ。テスト実行結果は用いていない。  
> 以下の ownership 表で確定できた 72 path は相互重複しない。ただし末尾所見の未確定 path／owner が残るため、変更対象全体の素集合はまだ主張しない。

## §13-8 — §9 の再列挙と W-0..W-f の exact ファイル所有表

### 8.1 機械的再列挙

親の 3 パターンを HEAD で再照合した結果は次のとおり。

| pattern | `.py` file 数 | 照合結果 |
|---|---:|---|
| `known_axes_freeze\|measurement_freeze\|holdout_freeze` | 35 | 親素材の全 per-file 件数と一致。計148行 |
| `s1-freeze\|s8b-freeze` | 28 | 親素材の path 集合と一致 |
| `FROZEN_MANIFEST\|V1_FREEZE_SHA256\|pre_oracle_head` | 11 | 親素材の path 集合と一致 |
| 3 集合の和 | 44 | 過不足なし |

各 path の最初の一致位置は次である。

```text
hooks/guard_write.py:86
orchestrator/campaign/s1_direct_comparison.py:43
orchestrator/campaign/s1_known_axes_freeze.py:5
orchestrator/campaign/s1_measurement_freeze.py:5
orchestrator/campaign/s1_report.py:761
orchestrator/campaign/s1_verify_extime_calibration.py:17
orchestrator/campaign/s8b_approved.py:29
orchestrator/campaign/s8b_floor_campaign.py:84
orchestrator/campaign/s8b_holdout_freeze.py:5
orchestrator/campaign/s8b_oracle_driver.py:44
orchestrator/campaign/s8b_oracle_manifest.py:34
orchestrator/campaign/s8b_prediction_runner.py:4
orchestrator/campaign/s8b_ratified_freeze.py:21
orchestrator/campaign/s8b_run_marker.py:8
orchestrator/campaign/s8b_selector_freeze.py:38
orchestrator/tests/conftest.py:71
orchestrator/tests/test_frozen_artifacts.py:26
orchestrator/tests/test_hooks.py:122
orchestrator/tests/test_plain_runner_coverage.py:6
orchestrator/tests/test_real_repo_serialization.py:47
orchestrator/tests/test_s1_direct_comparison.py:110
orchestrator/tests/test_s1_known_axes_freeze.py:20
orchestrator/tests/test_s1_measurement_freeze.py:17
orchestrator/tests/test_s1_report.py:117
orchestrator/tests/test_s1_verify_extime_calibration.py:101
orchestrator/tests/test_s8b_approved.py:68
orchestrator/tests/test_s8b_budget.py:20
orchestrator/tests/test_s8b_descriptor.py:24
orchestrator/tests/test_s8b_floor_campaign.py:156
orchestrator/tests/test_s8b_freeze_io.py:237
orchestrator/tests/test_s8b_holdout_freeze.py:20
orchestrator/tests/test_s8b_oracle_driver.py:46
orchestrator/tests/test_s8b_oracle_manifest.py:26
orchestrator/tests/test_s8b_oracle_report.py:37
orchestrator/tests/test_s8b_prediction_runner.py:4
orchestrator/tests/test_s8b_protocol_builder.py:54
orchestrator/tests/test_s8b_ratified_freeze.py:5
orchestrator/tests/test_s8b_ratified_verify.py:5
orchestrator/tests/test_s8b_repo_scan_invariant.py:18
orchestrator/tests/test_s8b_selector_freeze.py:34
orchestrator/tests/test_s8b_selector_input.py:18
orchestrator/tests/test_s8b_verdict.py:693
orchestrator/tests/test_task_run_ledger.py:911
tools/task_runs/ledger.py:50
```

§9 との照合結果:

1. `tools/task_runs/ledger.py` と `orchestrator/tests/test_task_run_ledger.py` は単なる文字列一致ではない。`_BANNED_OUTPUT_NAMESPACES` を `_assert_safe_root()` が実際に参照し、`output/<namespace>/task-runs` を拒否している (`tools/task_runs/ledger.py:49-51,144-156`)。新 namespace `freeze-migrations` / `freeze-permanent` を同じ拒否集合へ追加する変更対象であり、W-0 所有とする。直接テストは `orchestrator/tests/test_task_run_ledger.py:911-914`。
2. `orchestrator/tests/test_plain_runner_coverage.py:6` は過去の test 名を説明するコメント、`orchestrator/tests/test_s8b_descriptor.py:23-24` は holdout search への自己一致を避ける注意書きである。いずれもその grep hit 自体は freeze path consumer ではない。
3. §9 に列挙済みだが 3 パターンでは拾えない実依存は残る。主なものは `s8b_freeze_io.py:41-68`、`s8b_floor_contract.py:161-164`、`s8b_launch_cert.py:18-100`、`s8b_verdict.py:806-839`、`s8b_budget.py:27,208-222`、`s8b_oracle_artifacts.py:20-21`、`s8b_oracle_report.py:1004-1037`、`s8b_oracle_judge.py:123-145`、`s8b_materialization.py:49-94` である。grep 三集合を完全性の根拠にしてはならない。
4. `hooks/guard_bash.py` と同ファイルを検査する `orchestrator/tests/test_hooks.py` は親指示どおり W-0 へ追加する。現行の protected tree は `output/campaigns` / `external/ccbench` だけで、freeze namespace は存在しない (`hooks/guard_bash.py:56-75,264-291,361-370`)。
5. `docs/README.md` は本設計 wave で更新済みになるため W-f から除外する。`tools/check_docs.py` は後記所見の C1 との時期衝突を残したまま、第1設計段 §12 と草案 A の指定に従い W-f 欄へ置く。

### 8.2 ownership の境界

ownership は「その wave が追加・変更してよい tracked path」の集合である。参照するだけの legacy code/artifact は含めない。

新設 production module は、草案 B が定義した direct-test basename をそのまま production basename に写す。

```text
test_freeze_permanent_stats.py    -> freeze_permanent_stats.py
test_s1_measurement_freeze_v3.py  -> s1_measurement_freeze_v3.py
test_s8b_holdout_freeze_v3.py     -> s8b_holdout_freeze_v3.py
test_freeze_permanent_lineage.py  -> freeze_permanent_lineage.py
test_freeze_bundle_resolver.py    -> freeze_bundle_resolver.py
```

根拠は `draft-B.md:808-833`。known v2 には対応する direct-test 名が定義されていないため、この規則を適用できない。所見へ出す。

### 8.3 確定できた ownership レコード

形式は一行一 path の `wave<TAB>path`。この72レコード内に重複 path はない。

```text
W-0	hooks/guard_write.py
W-0	hooks/guard_bash.py
W-0	hooks/README.md
W-0	orchestrator/tests/test_hooks.py
W-0	tools/task_runs/ledger.py
W-0	orchestrator/tests/test_task_run_ledger.py

W-a	orchestrator/campaign/freeze_permanent_io.py
W-a	orchestrator/campaign/freeze_permanent_stats.py
W-a	orchestrator/tests/test_freeze_permanent_io.py
W-a	orchestrator/tests/test_freeze_permanent_stats.py
W-a	orchestrator/tests/conftest.py

W-b	orchestrator/campaign/s1_measurement_freeze_v3.py
W-b	orchestrator/tests/test_s1_measurement_freeze_v3.py

W-c	orchestrator/campaign/s8b_holdout_freeze_v3.py
W-c	orchestrator/campaign/freeze_permanent_lineage.py
W-c	orchestrator/campaign/freeze_bundle_resolver.py
W-c	orchestrator/tests/test_s8b_holdout_freeze_v3.py
W-c	orchestrator/tests/test_freeze_permanent_lineage.py
W-c	output/freeze-permanent/active/746fcafabaaef09f11bc945dafc63eb177c94df5c1fb2735aadb230be2260e4b.json

W-d	orchestrator/campaign/s1_direct_comparison.py
W-d	orchestrator/campaign/s1_report.py
W-d	orchestrator/campaign/s1_verify_extime_calibration.py
W-d	orchestrator/campaign/s8b_approved.py
W-d	orchestrator/campaign/s8b_freeze_io.py
W-d	orchestrator/campaign/s8b_floor_contract.py
W-d	orchestrator/campaign/s8b_floor_campaign.py
W-d	orchestrator/campaign/s8b_launch_cert.py
W-d	orchestrator/campaign/s8b_oracle_driver.py
W-d	orchestrator/campaign/s8b_oracle_manifest.py
W-d	orchestrator/campaign/s8b_selector_freeze.py
W-d	orchestrator/campaign/s8b_prediction_runner.py
W-d	orchestrator/campaign/s8b_verdict.py
W-d	orchestrator/campaign/s8b_budget.py
W-d	orchestrator/campaign/s8b_run_marker.py
W-d	orchestrator/campaign/s8b_oracle_artifacts.py
W-d	orchestrator/campaign/s8b_oracle_report.py
W-d	orchestrator/campaign/s8b_oracle_judge.py
W-d	orchestrator/campaign/s8b_materialization.py
W-d	orchestrator/tests/test_s1_direct_comparison.py
W-d	orchestrator/tests/test_s1_report.py
W-d	orchestrator/tests/test_s1_verify_extime_calibration.py
W-d	orchestrator/tests/test_s8b_approved.py
W-d	orchestrator/tests/test_s8b_freeze_io.py
W-d	orchestrator/tests/test_s8b_floor_contract.py
W-d	orchestrator/tests/test_s8b_floor_campaign.py
W-d	orchestrator/tests/test_s8b_launch_cert.py
W-d	orchestrator/tests/test_s8b_oracle_driver.py
W-d	orchestrator/tests/test_s8b_oracle_manifest.py
W-d	orchestrator/tests/test_s8b_selector_freeze.py
W-d	orchestrator/tests/test_s8b_prediction_runner.py
W-d	orchestrator/tests/test_s8b_verdict.py
W-d	orchestrator/tests/test_s8b_budget.py
W-d	orchestrator/tests/test_s8b_oracle_artifacts.py
W-d	orchestrator/tests/test_s8b_oracle_report.py
W-d	orchestrator/tests/test_s8b_oracle_judge.py
W-d	orchestrator/tests/test_s8b_materialization.py
W-d	orchestrator/tests/test_s8b_protocol_builder.py
W-d	orchestrator/tests/test_s8b_selector_input.py
W-d	orchestrator/tests/test_s8b_binding_driftguards.py
W-d	orchestrator/tests/test_real_repo_serialization.py
W-d	orchestrator/tests/test_freeze_bundle_resolver.py
W-d	orchestrator/tests/test_freeze_observation_propagation.py

W-e	orchestrator/tests/test_frozen_artifacts.py
W-e	output/s1-freeze/known_axes_freeze.v2.g1.json
W-e	output/s1-freeze/measurement_freeze.v3.g1.json
W-e	output/s8b-freeze/holdout_freeze.v3.g1.json
W-e	output/freeze-migrations/legacy-to-permanent-g1.receipt.json

W-f	orchestrator/tests/README.md
W-f	tools/check_docs.py
W-f	docs/phase3.md
W-f	docs/worklog.md
W-f	docs/decisions.md
```

根拠:

- W-0: 第1設計段 `freeze-permanent-design.md:426`、草案 A `draft-A.md:814-836,953-1008,1039`、現行 hook `guard_write.py:78-96` / `guard_bash.py:56-75`、ledger `ledger.py:49-51,144-156`。
- W-a/W-b/W-c: 第1設計段 `freeze-permanent-design.md:427-431`、草案 B の新設 node `draft-B.md:808-833`。g0 pointer の bytes と path は草案 A `draft-A.md:374-394`。
- W-d: 第1設計段 `freeze-permanent-design.md:337-351,432-434`、observation node は `draft-B.md:820-832`、selector owner は `draft-C1.md:98-108,158-204`。`test_s8b_binding_driftguards.py` は W-d の3 moduleを直接 importする統合テスト (`:36-38`)。
- W-e: g1 artifact は `freeze-permanent-design.md:96-98`、receipt は同 `:311-314`、manifest owner は同 `:435-436` と草案 B `draft-B.md:822-833`。
- W-f: `freeze-permanent-design.md:437-442`。`docs/README.md` の除外は親中間裁定を適用済み。

### 8.4 ownership 対象外として固定する legacy／歴史物

次は照合元または legacy lane であり、本移行では変更しない。

```text
orchestrator/campaign/s1_known_axes_freeze.py
orchestrator/campaign/s1_measurement_freeze.py
orchestrator/campaign/s1_stats.py
orchestrator/campaign/s8b_holdout_freeze.py
orchestrator/campaign/s8b_ratified_freeze.py
orchestrator/campaign/wal.py

orchestrator/tests/test_s1_known_axes_freeze.py
orchestrator/tests/test_s1_measurement_freeze.py
orchestrator/tests/test_s1_stats.py
orchestrator/tests/test_s8b_holdout_freeze.py
orchestrator/tests/test_s8b_ratified_freeze.py
orchestrator/tests/test_s8b_ratified_verify.py
orchestrator/tests/test_s8b_repo_scan_invariant.py
orchestrator/tests/test_plain_runner_coverage.py
orchestrator/tests/test_s8b_descriptor.py

output/s1-freeze/known_axes_freeze.json
output/s1-freeze/measurement_freeze.json
output/s8b-freeze/holdout_freeze.json
output/env/linux-baremetal/calibration/s1_verify_extime.json
output/reports/s1_direct_comparison/report.json
docs/phase3-8b-descriptor-design.md

output/insights/2026-07-16_s8b-floor-protocol-package.md
output/insights/2026-07-16_s8b-freeze-v2-design-material.md
output/insights/2026-07-16_s8b-floor-protocol-consultations.md
output/insights/2026-07-16_s8b-freeze-consultations.md
output/insights/2026-07-16_s8b-ruling-prep-consultations.md
```

旧8件の exact 根拠は `orchestrator/tests/test_frozen_artifacts.py:33-50`。legacy lane を一切変更しない根拠は `freeze-permanent-design.md:297-300`。`wal.py` は wrapper keyを変更せず payloadのみversion化する草案 B の契約 (`draft-B.md:441-480`) により変更対象外とする。

## §13-9 — 実装 wave の変異テスト事前登録

### 9.1 共通規則

1. 「単一理由」は、変異 fixture の不正条件が表の一項だけであり、その位置より前の parser・root・schema predicateを全て通ることをいう。
2. 実装 wave 開始時に、実コード上の predicate 順・例外変換・fixture が本当に当該位置へ到達することを再確認する。別の先行 predicate が同じ入力を落とす場合、そのまま受入せず fixture または変異位置を改訂する。
3. diagnostic sensitivity pin は防壁全体の安全証明ではない。多層防御によって end-to-end では等価変異になる層を、当該 predicate が消えていないことだけ個別に固定する。
4. production 統計と独立統計、production root と `FROZEN_MANIFEST` は F28 対応として両側の個別変異に加え、指定した同時変異も実施する。

### W-0

| ID | (i) 変異点 | (ii) 無効化時に赤くなる単一理由 | (iii) 検出 node | (iv) wave 開始時の再確認 |
|---|---|---|---|---|
| `M0-write` | `guard_write.decide()` の4 freeze namespace拒否から対象1件を外す | `output/freeze-permanent/active/x.json` は campaign/build-cacheではなく (`guard_write.py:78-85`)、ccbenchでもない。namespace predicate (`:91-96`) だけが拒否する | `test_hooks.py::test_s8b_freeze_namespace_denied` を4 namespaceへ拡張 | 各 namespaceについて Write/Edit/MultiEdit/NotebookEdit が同じ predicateへ到達すること。CLI内部guardとの重複があるため diagnostic sensitivity pin とする |
| `M0-bash` | `guard_bash` の freeze tree mention/tree-destruction判定を無効化 | 現行 `_LEAF_RE` / tree root は freezeを含まず (`guard_bash.py:56-75,264-291`)、`rm output/freeze-migrations/x` は追加 predicate以外では拒否されない | `test_hooks.py::test_bash_direct_writes_denied` | exact generator CLIだけが許可され、rm/cp/mv/sed/tee/redirectionが1理由で拒否されること。CLI自身との多層防御なので diagnostic sensitivity pin |
| `M0-ledger` | `_BANNED_OUTPUT_NAMESPACES` から新 namespaceを1件削除 | `_assert_safe_root()` の唯一の namespace拒否は当該集合参照 (`ledger.py:144-156`)。path traversal・symlink条件を含まない通常directory fixtureを使う | `test_task_run_ledger.py::test_evidence_namespace_root_is_rejected` | `freeze-migrations` / `freeze-permanent` の各 parameterが他のpath安全検査で落ちていないこと |

### W-a

| ID | (i) 変異点 | (ii) 無効化時に赤くなる単一理由 | (iii) 検出 node | (iv) wave 開始時の再確認 |
|---|---|---|---|---|
| `Ma-registry` | unknown/missing/duplicate check-ID の exact-set拒否を無効化 | document/root/schemaはvalidで、reportのID集合だけがregistryと異なる fixtureにする。前段parserは同じ入力を拒否しない | `test_freeze_permanent_io.py::test_check_registry_is_closed_world_for_every_schema` | schemaごとのregistryが実装定数からではなく独立goldenと比較されること |
| `Ma-blocked` | `not_evaluated.blocked_by` の既存ID・前方参照・非循環検査を1つ無効化 | check-ID集合とstatus型はvalid。後方参照または2-node cycleだけが不正 | `test_freeze_permanent_io.py::test_not_evaluated_blocked_by_is_existing_unique_and_acyclic` | cycle fixtureが別のmissing/duplicate IDになっていないこと |
| `Ma-stat-ref` | 独立実装の greater tailを `T >= T_obs` から `T > T_obs` へ変更 | strict shape・有限値・alternativeは全てvalid。観測統計と同値の割付だけが numerator差を作る | `test_freeze_permanent_stats.py::test_conformance_vectors_match_independent_reference` | `s1_stats.py` やproduction builderをimport/monkeypatchして期待値を作っていないこと。W-bのproduction側変異と対になる相互変異 |

### W-b

| ID | (i) 変異点 | (ii) 無効化時に赤くなる単一理由 | (iii) 検出 node | (iv) wave 開始時の再確認 |
|---|---|---|---|---|
| `Mb-observation` | `/observations/records[*].cell_id` と schedule の全単射検査を無効化 | 288件、型、順序、locator、float hexはvalidで、1件のcell_idだけが対応scheduleと異なる | `test_s1_measurement_freeze_v3.py::test_observations_are_schedule_bijection_with_canonical_float_hex` | origin hashまで同時に追随させ、origin mismatchが先に落とさないこと |
| `Mb-stat-prod` | production側の family集約を `max(p_star)` から `min(p_star)` へ変更 | observationsと個別comparisonはvalidで、family判定だけが変わる | `test_s1_measurement_freeze_v3.py::test_analysis_results_match_independent_reference_for_all_twelve_comparisons` | expectedをproduction出力から作らず、W-a独立実装から得ること。`Ma-stat-ref`との相互変異 |
| `Mb-wal-basis` | A前auditのblob基準を `H_gen` から `H_v` またはworktreeへ変更 | receipt/G/H_gen到達性はvalidで、H_genと後続treeの同じpathだけbytesを変えたfixtureを使う。static artifact verifyはWALを読まないので先行拒否なし | `test_s1_measurement_freeze_v3.py::test_wal_source_audit_uses_h_gen_tree_blobs` | 実装がaudit開始時にH_vを捕捉しても、WAL読取引数へH_vを渡していないこと |
| `Mb-known-tree` | known source closureのH_gen blob照合をworktree照合へ戻す、または1 recordを省略 | worktreeはrecord hashと一致、H_gen blobだけが異なるfixtureにする。path/mode/schema/enumerationはvalid | `test_freeze_permanent_lineage.py::test_receipt_rederives_g_h_gen_and_all_input_blobs` | このnodeがW-b開始時に利用可能かを確認する。現状はW-c所有nodeであり、direct test欠落を所見に残す |

### W-c

| ID | (i) 変異点 | (ii) 無効化時に赤くなる単一理由 | (iii) 検出 node | (iv) wave 開始時の再確認 |
|---|---|---|---|---|
| `Mc-positive` | root registryにpinされた外部positive-control fixtureのmutant fail predicateを無効化 | fixture path/hash、search schema、baselineはvalid。単一mutantだけが期待hitを作らない | `test_s8b_holdout_freeze_v3.py::test_external_positive_control_baseline_mutant_revert` | fixtureと期待値を同じbuilderから生成していないこと。baseline→mutant→revertの3点を同一fixtureで行うこと |
| `Mc-receipt` | `G^ == H_gen` またはG exact diff検査を無効化 | artifact 3件とhashはvalidで、Gのparentまたは余剰diffだけを変える | `test_freeze_permanent_lineage.py::test_receipt_rederives_g_h_gen_and_all_input_blobs` | wrong-parent fixtureでtree hash差まで混入しないこと。extra-diff fixtureは追加無関係file 1件だけにする |
| `Mc-digest` | approval componentsの固定順またはdomain separator照合を無効化 | 4 hashは全てvalidで、順序またはdomainだけが不正。schema/parserは通る | `test_freeze_permanent_lineage.py::test_approval_and_pointer_reject_fork_gap_rollback_expiry_and_revocation` | failure reasonが `authorization.approval.digest_mismatch` だけであること |
| `Mc-resolve-once` | 捕捉済みpointer後にfamily pathを個別再読する | 1回目と2回目がそれぞれvalidだが異なるbundleを返すseamを使い、再読回数だけを観測する | `test_freeze_bundle_resolver.py::test_bundle_is_resolved_once_without_family_mixing` | 後段hash mismatchでも赤くなるため、これは call-countを固定する diagnostic sensitivity pin と明記する |
| `Mc-expiry` | A草案推奨のactivation windowで、X時刻の `[approved_at, expires_at)` 検査を無効化 | approval・digest・ancestry・X diffはvalidで、committer epochだけが`expires_at`と同値 | `test_freeze_permanent_lineage.py::test_approval_and_pointer_reject_fork_gap_rollback_expiry_and_revocation` | U-A1をユーザーが裁定した後にのみ有効化する。意味の決定権者は実装者でなくユーザー |

### W-d

現行の手前検査不在は次の実物で確認した。

- S-1 direct comparisonは最初にpathを直接読み、legacy `verify_document()`を呼ぶ (`s1_direct_comparison.py:115-127`)。`run_role()`でもこの呼出しが他のfreeze predicateより前 (`:589-605`)。
- S-1 reportはpath hashを直接作り、legacy measurement verifierを呼ぶ (`s1_report.py:750-770`)。
- calibrationはknown JSONを直接読み、legacy verifierを呼ぶ (`s1_verify_extime_calibration.py:193-229`)。
- 8b legacy branchはまず `s8b_freeze_io` でpathを読み (`s8b_oracle_driver.py:201-226`)、現行ratified active照合はfloor/budget非null branchだけ (`:228-247`)。knownもrecorded pathから直接検証する (`:249-261`)。
- manifest builderもcaller pathを直接読む (`s8b_oracle_manifest.py:616-628`)。run markerはpathを再読してhash化する (`s8b_run_marker.py:32-48`)。

| ID | (i) 変異点 | (ii) 無効化時に赤くなる単一理由 | (iii) 検出 node | (iv) wave 開始時の再確認 |
|---|---|---|---|---|
| `Md-s1-cutover` | S-1 consumer 1件をbundle resolverではなく旧path直読へ戻す | g0 pointerとcaller pathを別のvalid legacy bundle seamへ向ける。現行コードには上記のとおり前段resolverがない | `test_freeze_bundle_resolver.py::test_bundle_is_resolved_once_without_family_mixing` | direct-comparison/report/calibrationを別subcaseにし、各subcaseでresolver呼出し1回・family直読0回を確認 |
| `Md-8b-cutover` | oracle/floor/manifest/budget/run-marker consumer 1件を旧family loaderへ戻す | g0 legacy branchでは現行ratified active検査が先行しない (`s8b_oracle_driver.py:201-247`)。caller pathだけを差し替える | 同上 | §9の8b consumer全件を固定したconsumer registryからparametrizeし、登録漏れをテスト自身のexact setで拒否 |
| `Md-propagation` | WAL→report→judge→calibration のいずれか1 hopで `freeze_identity` または `freeze_verification_observation` を落とす／再解決値で置換する | upstream objectはvalid。対象hopの欠落・不一致だけを作る | `test_freeze_observation_propagation.py::test_identity_and_observation_survive_wal_report_judge_and_calibration` | 各hopを独立subcaseにし、指定reason 1件だけを要求。多層伝播のため diagnostic sensitivity pin |
| `Md-preoracle-hash` | `pre_oracle_tree.manifest_sha256` 再計算一致を無効化 | tree OID、entry count、modes、sources、body hashはvalidで、manifest digestだけを1bit変更 | `test_s8b_selector_freeze.py::test_v2_published_verifier_binds_parent_tree_manifest_and_introduction` | 現行の形式→commit実在だけの検査 (`s8b_selector_freeze.py:565-566,618-626`) が完全に置換され、旧field fallbackがないこと |
| `Md-preoracle-type` | official consumerがcandidate-only objectまたは生dictを受理する | candidate schema/tree/sourceはvalidだが、`G_pred/H_pred` introductionが存在しない | 同上 | `s8b_verdict.verify_prediction()` の現行typed boundary (`s8b_verdict.py:186-213`) がpublished型へ置換され、型偽装fixtureが別schema失敗にならないこと |

### W-e

| ID | (i) 変異点 | (ii) 無効化時に赤くなる単一理由 | (iii) 検出 node | (iv) wave 開始時の再確認 |
|---|---|---|---|---|
| `Me-exclusive-G` | 既存generation pathの変更を許し、`A`追加だけというG diff制約を無効化 | 既存bytesをvalid successor bytesへ変更し、他のartifact/schema/hashはvalidにする。G diff statusだけが`M` | `test_freeze_permanent_lineage.py::test_receipt_rederives_g_h_gen_and_all_input_blobs` | process側O_EXCLとpost-commit diff検査を別々に変異する。前者は diagnostic sensitivity、後者はauthoritative gate |
| `Me-audit` | observation audit失敗時にもA recordを作れるようにする | measurement/artifact/receipt schemaはvalidで、H_gen WALの1 locatorだけが不一致 | `test_frozen_artifacts.py::test_g1_observations_match_h_gen_wal_blobs` | A作成CLIがtest用 seamでも必ずauditを通り、`status:"pass"` 自己申告だけで進まないこと |
| `Me-keyset` | `len==12`だけを残し、旧8∪新4 exact key-set検査を削除 | 旧key 1件を未知keyへ差し替えて件数12を維持する | `test_frozen_artifacts.py::test_permanent_bundle_matches_literal_roots_and_exact_keyset` | literal expected setをproduction registryから導出していないこと |
| `Me-root-pair` | production rootと`FROZEN_MANIFEST`の同じsuccessor hashを同時に誤値へ変更 | 単層変異は他方に落ちるためF28の同時変異とする。両rootは相互一致するがreceipt successorだけが不一致 | `test_freeze_permanent_lineage.py::test_receipt_rederives_g_h_gen_and_all_input_blobs` | 片面だけの2 diagnostic subcaseに加え、両面同時変異subcaseを必須にする |
| `Me-A-diff` | A commitのapproval 1file追加allowlist、または`AI-Agent: none`検査を無効化 | approval/digest/expiryはvalidで、余剰file 1件またはtrailerだけが不正 | `test_freeze_permanent_lineage.py::test_approval_and_pointer_reject_fork_gap_rollback_expiry_and_revocation` | extra-fileとtrailerを別fixtureにし、同時に壊さないこと |

### W-f

| ID | (i) 変異点 | (ii) 無効化時に赤くなる単一理由 | (iii) 検出 node | (iv) wave 開始時の再確認 |
|---|---|---|---|---|
| `Mf-X-parent` | `X^ == selected A` を「Aの任意descendant」へ緩和する | AとXの間に内容無変更の通常commitを1件置く。pointer、approval、bundle digest、X diffは全てvalid | `test_freeze_permanent_lineage.py::test_approval_and_pointer_reject_fork_gap_rollback_expiry_and_revocation` | intermediate commitが他のtopology ruleを破らず、failureが `authorization.activation.parent_mismatch` だけであること |
| `Mf-X-diff` | X commitへpointer以外の変更を許す | valid g1 pointerに無関係file 1件だけを追加する | 同上 | A/X parent、human trailer、pointer contentを全てvalidに保つこと |
| `Mf-active-observation` | g1 active時にnon-passまたは欠落したverification observationでもcampaign開始を許す | pointer/artifact/report schemaはvalidで、observation statusだけを`error`にする | `test_freeze_observation_propagation.py::test_identity_and_observation_survive_wal_report_judge_and_calibration` | resolver、WAL writer、report、judgeの各拒否を個別subcaseにする。多層防御なので diagnostic sensitivity pin |

## 所見

1. §9 に無かった `tools/task_runs/ledger.py` / `orchestrator/tests/test_task_run_ledger.py` は実依存であり、W-0変更対象に追加が必要である。文字列一致扱いで除外してはならない。

2. `test_plain_runner_coverage.py` と `test_s8b_descriptor.py` の grep hit はコメント由来であり、freeze consumerとしてのownership根拠にはならない。

3. known v2 のproduction module名とdirect-test file名がA/B/C1のどこにも定義されていない。第1設計段は「新規ファイル + direct test」を要求する (`freeze-permanent-design.md:429-430`) が、草案 B の新設14 nodeにはmeasurementしかない (`draft-B.md:814-816`)。この2 pathを発明して72-path表へ混ぜていない。決定権者は親統合者であり、確定までW-b集合は不完全である。

4. exact CLI path `orchestrator/campaign/freeze_bundle_generate.py` は草案 A に存在する (`draft-A.md:975-987`) が、generation-plan/guard coreはW-0、family stage writerはW-b/W-c、実行はW-eとされる (`:836,1008`)。一file一ownerへ落ちないためownership表から除外した。親が「CLI shell=W-0、family writerは各family module」のようにfile境界を裁定する必要がある。

5. `orchestrator/campaign/freeze_permanent_roots.py` は草案 A でW-eの`M` statusと指定される (`draft-A.md:597-604`) が、HEADには存在しない。W-eで初出ならstatusは`A`、先行waveで追加するなら同fileをW-eも変更して一file一ownerを破る。親裁定なしにW-e集合へ入れられない。

6. approval path `output/freeze-permanent/approvals/<approval_raw_sha256>.json` は人間入力の`approver/approved_at/expires_at`を含むraw hash依存 (`draft-A.md:281-302`)、g1 X pointer pathもそのapproval hash依存 (`:336-370`) であり、第2設計段時点ではexact filenameを列挙できない。W-e/W-fの変更対象ではあるが、path templateをexact path表へ偽装していない。

7. 草案 A のg1 receiptはtop-level exact 9 fields (`draft-A.md:114-132`) だが、草案 B は同receiptへ `/observation_audit` を必須追加する (`draft-B.md:338-369`)。両方を同時には満たせない。receipt schemaとW-e audit mutationを親が統合裁定するまで§13-1/2bは閉じない。

8. approval expiryの意味はR1..R16で裁定されていない。草案 A はactivation windowを推奨し、決定権者をユーザーU-A1と明記する (`draft-A.md:322-334`)。`Mc-expiry`はこの裁定前に実装してはならない。

9. 外部固定positive-control fixtureはexact test nodeだけが定義され、fixtureのtracked pathとroot-registry keyが未定義である。§10の「exact path + bytes hash」を満たす新設fileを72-path表へ列挙できない。

10. C1が要求するselector raw evidenceの「`G_pred`より前にtracked、immutableなpath」もexact pathが未定義 (`draft-C1.md:118-127`)。W-dの未所有変更対象として残る。

11. `conftest.py` は第1設計段でW-a、対応する独立golden `test_real_repo_serialization.py` はW-dである (`freeze-permanent-design.md:427-434`)。現行meta-testは両集合の即時一致と全node収集可能性を検査する (`test_real_repo_serialization.py:89-187`)。W-aが未実在W-d nodeを先行追加すればgreenを保てず、W-dが後から`conftest.py`も直せば一file一ownerを破る。所有表は原案どおり記録したが、wave単独greenは未証明である。

12. 新設testがpytest-onlyなら `orchestrator/tests/README.md` allowlist更新が各導入waveで必要になる (`orchestrator/tests/README.md:43-57`)。同fileをW-fだけが所有する現案と両立させるには、W-a..W-dの全新設testへ自走harnessを持たせる必要がある。A/B/C1はこれを規定していない。

13. `tools/check_docs.py` の時期は草案間で矛盾する。第1設計段と草案 A はW-fを支持する一方 (`freeze-permanent-design.md:437-438`, `draft-A.md:1051`)、C1は「livingのままW-fまでlint外」を否認する (`draft-C1.md:507-518`)。表は親中間指示と第1設計段を優先してW-fに置いたが、矛盾自体は未裁定である。

14. W-0後は4 freeze namespaceへの通常Write/Bashが拒否されるが、草案 A が明記する唯一の許可CLIはgN bundle生成だけである。W-cのg0 pointer、W-eのapproval、W-fのX pointerを作成するexact writer commandが無い。hookを迂回せず実装するには各record用CLI契約を追加する必要がある。

15. C1のtree anchorは`pre_oracle_head`のdanglingを解消するが、oracle前に情報を見ていないこと自体は証明しない (`draft-C1.md:556-560`)。W-d/W-fの受入で「HARKingを機械排除」と主張してはならない。

16. 第1設計段の「holdoutと同型の列挙snapshot」は現物と一致しない。現行holdout `/search/file_enumeration` は説明stringでmember集合を持たないため、C1のmember snapshot強化形を採るか親裁定が必要 (`draft-C1.md:326-406,556`)。

17. `docs/README.md` は親中間裁定どおりW-fから除外した。これ以外の未確定・複数owner対象が解消されるまでは、72-path部分集合が重複なしであっても「W-0..W-fの全変更対象が素集合」とは記録しない。
---

# 段 3a: 敵対相談 X (正しさ境界)

1. (i) 所在: 草案 A §1.3.1、草案 B §3.2/§5.5、草案 C2 所見7、親 P2/P4。(ii) 攻撃: A の receipt は exact 9 fields だが、B は `/observation_audit` を必須追加し、receipt/approval/pointer registry 自体も「exact ではない」と明記する。A 実装なら audit 欠落を受理し、B 実装なら A 準拠 record を誤拒否する。(iii) 深刻度: **BLOCKER**。(iv) 修正案: 統合済み単一 schema、全 check-ID、reason code、依存順を再発行する。

2. (i) 所在: 草案 A §1.5/§2.4、草案 B §3/§5.5。(ii) 攻撃: approval は4 component hashと `scope` 文字列しか持たず、verifier/projection/WAL-audit report を束縛しない。偽造 observations と自己整合する analysis を作り、A 作成コマンドの audit を迂回すれば、`scope` を名乗るだけで X まで到達する。(iii) 深刻度: **BLOCKER**。(iv) 修正案: canonical audit/report 本文の hash と対象 `H_v/H_gen` を receipt・approval に含め、resolver が再検証する。

3. (i) 所在: 骨格 §4、草案 A §3.5、草案 B §5.1。(ii) 攻撃: G 前の staged candidate は literal root 未登録なのに、全 artifact 共通 registry は `output.literal-root` を必須とするため必ず失敗する。実装者が root 不在を pass 扱いすると、その分岐が official 型にも漏れて fail-open になる。(iii) 深刻度: **BLOCKER**。(iv) 修正案: candidate と registered/official の registry を型ごとに分離し、candidate から official への暗黙昇格を禁止する。

4. (i) 所在: 骨格 §3.3/§14、草案 B §4.2–§4.5/§5.4、草案 C2 W-f。(ii) 攻撃: static verify から外した live search の exact gate、check-ID、reason、typed return、伝播 field、変異が一件もない。X 後に新しい holdout hit を追加しても snapshot は通り、campaign-start は live scan の証拠なしで `"pass"` を記録できる。(iii) 深刻度: **BLOCKER**。(iv) 修正案: lifecycle 別 expected-hit 契約を持つ `LaunchValidatedOfficialBundle` と live-scan reportを定義し、全実走 consumer に要求する。

5. (i) 所在: 骨格 §8 step 1/3、草案 A §1.6、草案 B §4.2/§5。(ii) 攻撃: legacy loader は raw bytes exact のみとされる一方、g0 pointer 化は現行 refusal 集合保存を主張する。しかし legacy artifact/check registry は未定義であり、source driftやlive hitを現行 verifierは拒否してもg0 resolverは通し得る。(iii) 深刻度: **BLOCKER**。(iv) 修正案: legacy 3 verifier と live search を包む exact adapter/registryを定義し、g0拒否集合の完全一致を固定する。

6. (i) 所在: 草案 C1 §2.4/P5、草案 A「§14追記不要」、骨格 §14。(ii) 攻撃: 現行 known verifier は current worktree の全 source と submodule HEAD driftを拒否するが、新形式は全件を過去の H_gen treeだけで通す。G 後に実装sourceまたはccbench checkoutを変更すると、現行は拒否、新 static は受理し、実走は変更後コードを使い得る。(iii) 深刻度: **BLOCKER**。(iv) 修正案: §14へ明示行を追加し、実走時コード・gitlink・binary identityをactive bundleへ束縛する。

7. (i) 所在: 骨格 §3/§6、草案 C1 §1.2/§1.5/P5、骨格 §14。(ii) 攻撃: dangling `frozen_at_head` の削除と、`pre_oracle_head` から同一tree anchorへの置換は、現行ならcommit欠落で拒否する状態を新形式が受理する変更である。§14にどちらも載っていない。(iii) 深刻度: **BLOCKER**。(iv) 修正案: commit identityを失いtree内容同値を受理する交換とreceiptによる回収を§14へ追加する。

8. (i) 所在: 草案 C1 §1.2「tree manifest」。(ii) 攻撃: manifestはH_pred treeの全leafをhashするため、selector checker自身や無関係checkerもG fieldへ混入する。checkerの1 byte変更を含む新parent treeではcandidate再生成が必須となり、§2原則2のchecker pinを間接再導入する。(iii) 深刻度: **BLOCKER**。(iv) 修正案: Gには宣言済みsemantic input closureだけを置き、全tree manifestはMへ降格する。

9. (i) 所在: 草案 C1 §1.2「一意性」/§1.4/拒否reason。(ii) 攻撃: `G_pred` の追加一回は検査するが、その後の `M` と現在blob＝導入blobの一致を要求していない。後続commitで `generated_at` 等を変更し `body_sha256` を再計算しても、追加回数・parent tree・自己hashは通る。(iii) 深刻度: **MAJOR**。(iv) 修正案: H_v到達履歴で導入後のM/D/R/C/Tを全拒否し、current blobをG_pred導入blobへ固定する。

10. (i) 所在: 草案 A §1.2/§1.3.4、草案 B §5.5 `receipt.metadata-moves`。(ii) 攻撃: legacy generator等から `provenance_unverified` への「移動」を値比較すればMがgateへ逆流し、比較しなければ `metadata_sources` は自己申告だけの恒真checkになる。(iii) 深刻度: **BLOCKER**。(iv) 修正案: Mの値をprojection predicateから完全除外し、receiptでは「旧Gから除去したpointer」だけを歴史metadataとして記録する。

11. (i) 所在: 草案 B §1.3。(ii) 攻撃: `source` は「exact 7 keys」と書く一方、表には8 keysある。また選択したsession-start/commit/session-resultのtop-level `env_tag`・`variant`・`stage`を全て同一campaignへ束縛していない。campaign-startだけenv A、値recordはenv BというH_gen WALを凍結してもauditを通し得る。(iii) 深刻度: **BLOCKER**。(iv) 修正案: exact 8-key schemaへ訂正し、3 locatorすべてのwrapper/payload identityを完全一致させる。

12. (i) 所在: 草案 B §4.2、§5.1。(ii) 攻撃: `passed_check_ids` は常に「registryの全ID」で、実際のcheck resultやreport hashを持たない。実装がregistryを列挙して `"status":"pass"` を付けるだけでも同じ観測値になり、下流伝播は検査実行を証明しない。(iii) 深刻度: **MAJOR**。(iv) 修正案: actual result列からのみ導出し、全resultを含むcanonical report hashとaggregate判定を伝播する。

13. (i) 所在: 草案 B §5.1、草案 C2 `Ma-blocked`。(ii) 攻撃: `blocked_by` はpassしたcheckも指せる。さらに「常に前方IDのみ」で既にcycle不能なので、acyclic検査を単独無効化する変異は等価変異であり、2-node cycleは先に前方参照違反へ落ちる。`error/not_evaluatedが1件でも全体失敗` 自体の変異も未登録である。(iii) 深刻度: **MAJOR**。(iv) 修正案: blockerを非pass statusへ限定し、aggregate fail変異と、順序規則を外した上でのcycle変異を別登録する。

14. (i) 所在: 骨格 §10、草案 C2 `Mc-positive`/所見9、草案 B §6.2。(ii) 攻撃: 外部positive-control fixtureのtracked path、root key、bytes hash、literal期待値が未定義である。同じsearch/builderからfixtureと期待値を生成すれば、壊れたsearchでもbaseline/mutant/revertを自己整合させられる。(iii) 深刻度: **BLOCKER**。(iv) 修正案: search domainとの関係を含むexact fixture path・bytes・root key・3点期待値を事前凍結する。

15. (i) 所在: 骨格 §5、草案 B §2.5/§6.2、草案 C2 `Ma-stat-ref`。(ii) 攻撃: conformance vectorの分類名だけで具体入力とliteral出力がない。独立実装自身から期待値を作るtestなら、`>=`→`>`変異後も緑になる。(iii) 深刻度: **MAJOR**。(iv) 修正案: 各vectorの入力hex、統計量、p numerator、gate、効果量hexを独立literal goldenとして列挙する。

16. (i) 所在: 草案 C2 `Me-keyset`、現行 `test_frozen_artifacts.py`。(ii) 攻撃: exact key-set predicateを弱める変異の検出nodeが、そのpredicateを実装する同じtestである。assertを `len==12` だけへ変異すれば、そのtest自身が緑になり検出器にならない。(iii) 深刻度: **BLOCKER**。(iv) 修正案: manifest literal、production validator、独立golden testを別ファイル・別値源へ分離する。

17. (i) 所在: 草案 A §1.8.1、草案 C1 §2.3。(ii) 攻撃: C1はH_genのglob変化に応じて`members`と`records.path`集合を動的exact化するが、AはSHAとcount/digestしか変更許可せずpath/member変更を禁止する。g2前にmatching campaignを1件追加すると、C1準拠documentはtransition拒否され、旧集合維持ならclosure検査に落ちる。(iii) 深刻度: **BLOCKER**。(iv) 修正案: membershipを世代不変にするか、H_gen再導出済みsubtree全体の変更をsemantic制約付きでallowlistする。

18. (i) 所在: 骨格 §7-G、草案 A §1.4/§1.8.3。(ii) 攻撃: 各Gで新しいholdout確認を要求する一方、transitionはconfirmationを不変とする。g2で新しい`confirmed_at`を記録すると拒否され、g1値を再利用すると未実施確認を記録する。(iii) 深刻度: **MAJOR**。(iv) 修正案: 各generationでfresh confirmationを必須変更fieldとし、当該search reportへ束縛する。

19. (i) 所在: 草案 A §3.2/§3.5。(ii) 攻撃: start snapshotはtracked fileだけをinventory化しているのに、後段でuntracked追加も検出すると主張する。checkpoint直後にuntracked fileや一時改変を投入しgenerator/search読取後に戻せばsnapshotは一致する。またHEADはtree OIDしか再確認せず、同一treeの別commitへ交換できる。(iii) 深刻度: **MAJOR**。(iv) 修正案: generatorを捕捉済みH_genの隔離tree/FDからのみ読ませ、各境界でcommit OIDと全untracked状態も再検査する。

20. (i) 所在: 草案 A §1.5.2、草案 B §5.5 `pointer.approval-expiry`、C2 `Mc-expiry`。(ii) 攻撃: Xのcommitter epochは任意にbackdateできる。実際にはexpiry後でもtimestampだけwindow内へ置けばstatic verifierを通るうえ、Aは発効後非lease、Bはpointer expiry checkを列挙して意味も衝突する。(iii) 深刻度: **MAJOR**。(iv) 修正案: U-A1を先に裁定し、信頼可能なreceive timestampが無いならexpiryを運用規律としてのみ表現する。

21. (i) 所在: 草案 A §1.7.2/§1.10。(ii) 攻撃: revocationには非merge・exact diff・ancestry制約があるが、cancellationには同等のcommit diff/parent制約がない。valid target cancellationを無関係変更と同一commitへ混ぜても、target predicateと`AI-Agent:none`だけでbranchを消せる。(iii) 深刻度: **MAJOR**。(iv) 修正案: cancellationにも単一record追加、非merge、target/survivor後裔、immutable introductionを必須化する。

22. (i) 所在: 草案 A §1.12、草案 B §5.1、草案 C1 §1.3。(ii) 攻撃: 同じ分類が `document.read_failed`、`document.read-failed`、`selector-pre-oracle-*` と競合する。unknown reasonをreport変換時に捨てればcheckが欠落し、厳密実装なら同一失敗がschemaごとに誤拒否される。(iii) 深刻度: **MAJOR**。(iv) 修正案: 単一のtyped reason enumを発行し、未知reasonは必ずreport全体errorにする。

23. (i) 所在: 草案 C2 §9全体。(ii) 攻撃: live scan削除、predicateとregistry IDの同時削除、report aggregateのfail-open、W-d consumer一件の旧直読残存が未登録である。`Mb-known-tree` はW-b開始時に存在しないW-c所有testへ依存し、当該waveで赤を確認できない。`Md-preoracle-hash` はtree OID束縛にマスクされる等価層である。(iii) 深刻度: **BLOCKER**。(iv) 修正案: wave内で実在する独立nodeと、mask層を同時に外すcoupled mutantを再登録する。

24. (i) 所在: 草案 C2 §8.3/所見3–14、草案 A §3.6、親P4。(ii) 攻撃: known v2 module/test、generation CLI、root registry、positive fixture、selector raw evidence、approval/X/revocation/cancellation writerが未所有・未確定である。一方hookはprotected treeへの通常書込を全面拒否するため、実装時にgeneric CLI例外や任意path引数を足す誘因が残る。(iii) 深刻度: **BLOCKER**。(iv) 修正案: 全tracked path/template、一file一owner、record別exact writer commandを実装前に確定する。

25. (i) 所在: 草案 C1 §1.2/§4所見2、草案 C2 所見15。(ii) 攻撃: H_pred treeに既にoracle/floor結果が存在してもtree内容一致は通るため、`pre_oracle_tree` は情報閲覧順序を一切保証しない。名称だけがpre-oracleの機械保証を示唆する。(iii) 深刻度: **MAJOR**。(iv) 修正案: chronological launch gateを別途実装するか、fieldを単なる`prediction_basis_tree`へ改名する。

親 provisional 裁定: **P1 採用 / P2 否認 / P3 否認 / P4 否認 / P5 否認**。

総評: **NO-GO**。
---

# 段 3b: 敵対相談 Y (整合・実効性)

再計数では、3 raw SHA、9 legacy blob、63 source record / 31 unique path、24 record / 6 implementation file、18 cell、12 comparison、288 observation、WAL 1009/505/505 record、transition 13/9 pointer、`FROZEN_MANIFEST` 8件、grep 和集合44 file、既存 required node 12件、C2所有表72行は現物と一致した。以下はそれでも残る破綻である。

1. **所在:** A §1.3.1、B §3.2、C2 所見7  
   **矛盾:** A は receipt を「`top-level は exact 9 fields`」として `observation_audit` を持たない。一方 B は「receipt schema は `/observation_audit` を…持たなければならない」と要求する。両 schema は同時に成立しない。  
   **深刻度:** BLOCKER  
   **修正案:** receipt を単一の exact schema に再発行し、audit を入れるなら field 名・全子field・件数を A に統合する。

2. **所在:** B §3.1–3.2、骨格 §7-R、A §1.10  
   **矛盾:** B は audit を「A 作成コマンド」が実行するとしながら、既に R で固定済みの receipt に `"status":"pass"` を格納する。骨格は「receipt に自己申告 (`verified: true` 等) は置かない」、topology は `G <- R <- ... <- A` である。A 時点の結果を R に後付けすることも、`status:"pass"` を信頼することも不能。  
   **深刻度:** BLOCKER  
   **修正案:** R には audit 入力だけを束縛し、A が同入力から再実行した構造化 report を照合する契約に変える。

3. **所在:** 骨格 §7-A / R14、A §1.5.1、B §5.5  
   **矛盾:** 骨格の A は「verifier 全緑・projection 一致の添付レポート確認」を意味するが、A の approval exact 8 fields は4 component hashしか持たず、report path/hashを束縛しない。`scope="...verification-report+projection-report..."` は自己申告にすぎない。B の `approval.verifier-reports` も「候補」で未確定。  
   **深刻度:** BLOCKER  
   **修正案:** report の exact schema/hashを receipt に束縛し、A が receipt hash経由でその bytesと再導出結果を承認する形に固定する。

4. **所在:** B §5.5、親 brief P4、骨格 §4  
   **矛盾:** B 自身が receipt/approval/pointer について「**exact registryではない**」と明記している。revocation/cancellation registry は候補すらない。さらに各 check の exact `blocked_by` 依存グラフもないため、同じ失敗で評価継続か `not_evaluated` かを実装者が決めることになる。  
   **深刻度:** BLOCKER  
   **修正案:** 全 governance schemaについて ordered check-ID集合、単一reason、field pointer、依存辺を完全列挙する。

5. **所在:** B §4.2、B §5.2–5.4、A §1.6.2  
   **矛盾:** legacy campaign-start report は `pointer, known, measurement, holdout` の4件を要求し、各々に「当該 registry の全ID」を入れる。しかし B が定義するのは known v2 / measurement v3 / holdout v3だけで、schema_versionすらない legacy known/measurement 用 registry が存在しない。g0 observation を実装不能。  
   **深刻度:** BLOCKER  
   **修正案:** g0 pointerと3 legacy artifact専用の exact adapter registryを追加する。

6. **所在:** A §1.12、B §5.1、C1 §1.3・§2.4  
   **矛盾:** 同じ失敗の reason code が A=`document.read_failed`、B=`document.read-failed`、A=`schema.keys_mismatch`、B=`schema.keys-mismatch` と競合する。C1 は `selector-pre-oracle-*` / `known-source-*` という、骨格 §4 の stable namespace外の codeを固定し、Bによる改名も拒否している。  
   **深刻度:** MAJOR  
   **修正案:** 一つの reason-code grammarと対応表を正本化し、A/B/C1の全codeを機械比較可能な単一集合へ統合する。

7. **所在:** A §1.8.1、C1 §2.2–2.3  
   **矛盾:** A は known 世代遷移で source recordの `/sha256` と列挙snapshotの「digest/count」だけを変更可とする。一方 C1 の snapshot に digest fieldはなく、動的な `members[].path/disposition` と動的な `records[].path` を持つ。H_genの列挙集合が変わる正常な次世代を A が拒否する。既存 sourceの `lines` 更新規則もない。  
   **深刻度:** BLOCKER  
   **修正案:** C1 のH_gen再列挙アルゴリズムから許可pointer集合を動的導出し、members/disposition/records/linesの再導出変更だけを許す。

8. **所在:** B §1.3  
   **矛盾:** 「`source` は exact 7 keys」と書きながら、表は `wal_source_id, attempt, variant, session_start, value_record, session_result, value_json_pointer, value_origin_sha256` の **8 keys**。  
   **深刻度:** MAJOR  
   **修正案:** exact件数を8へ訂正し、schema testにも8-key literalを置く。

9. **所在:** A §3.1–3.2  
   **不能:** `start_snapshot_sha256` は「rootとccbenchの全tracked file/symlink inventory」のhashとされるが、inventory objectのfield、root/submodule path表現、gitlink header、mode、symlink bytes、canonical payloadが未定義。実装ごとに別hashになる。  
   **深刻度:** MAJOR  
   **修正案:** snapshot manifestのexact JSON schemaとdomain separatorを全文定義する。

10. **所在:** B §1.3  
    **曖昧:** WALにはsession IDがないのに、`value_record` を「同じ session」とだけ定義している。commit recordにはschedule/lap/attemptがなく、どの start/result 区間へ属するか、session重複・入れ子・途中startをどう拒否するかが未定義。  
    **深刻度:** MAJOR  
    **修正案:** `session_start` から対応 `session_result` までの非重複区間をexactに定義し、その区間内の唯一commitとして結合する。

11. **所在:** 骨格 §5、B §2.1・§2.5、C2 `Ma-stat-ref` / `Mb-stat-prod`  
    **不能:** B は独立計算をW-a、generator/verifierをW-bとするだけで、W-b producerがW-a独立実装を呼ぶことを禁止していない。C2は「production側」と「独立側」が別実装である前提の相互変異を登録しており、現仕様では同一実装を両側が共有できる。  
    **深刻度:** BLOCKER  
    **修正案:** producerは既存 `s1_stats`/production adapter、verifierは `freeze_permanent_stats` のみを使い、相互import禁止を明記する。

12. **所在:** C2 冒頭・所見3–10  
    **不能:** C2 自身が「変更対象全体の素集合はまだ主張しない」と認める。未所有なのは known v2 module/test、`freeze_bundle_generate.py`、production root、approval/X/revocation/cancellation record、positive-control fixture、selector raw evidenceなど。§13-8の成果物になっていない。  
    **深刻度:** BLOCKER  
    **修正案:** 全未確定pathを実pathまたは排他的path-templateとしてowner表へ追加してから72件表を置換する。

13. **所在:** A §1.10、C2 所見5  
    **矛盾:** A は `freeze_permanent_roots.py` を L_prod で status `M` と固定するが、HEADに同fileは存在しない。W-e初出なら `A`、先行wave追加ならW-e再変更で一file一owner違反。  
    **深刻度:** BLOCKER  
    **修正案:** registry shellと世代別literal dataを別fileに分離し、先行waveとW-eのownerを分ける。

14. **所在:** C2 ownership §8.3、C2 mutations `Mb-known-tree` / `Mc-resolve-once`、C2 所見11  
    **矛盾:** W-b変異がW-c所有の `test_freeze_permanent_lineage.py` を要求し、W-c変異がW-d所有の `test_freeze_bundle_resolver.py` を要求する。さらにW-aの `conftest.py` 更新はW-dの独立goldenと即時一致が必要。依存順と各wave greenを同時に満たせない。  
    **深刻度:** BLOCKER  
    **修正案:** known direct testをW-b、resolver direct testをW-c、conftestと独立goldenを同一waveへ移す。

15. **所在:** C2 所見12、C2 ownership §8.3  
    **不能:** 新設test群に自走harnessの指定がなく、pytest-onlyなら各導入waveで `orchestrator/tests/README.md` 更新が必要になるが、同fileはW-f専有。W-a..W-dのgreen条件が未確定。  
    **深刻度:** MAJOR  
    **修正案:** 全新設testに自走harnessを必須化するか、README所有戦略を再設計する。

16. **所在:** A §3.6、C2 所見4・14  
    **不能:** hookが許すwriterは `freeze_bundle_generate.py generate` だけで、そのfile自体にownerがない。g0 pointer、approval、X pointer、revocation、cancellation、selector prediction用のexact writer commandもない。W-0後の正規生成経路が閉じる。  
    **深刻度:** BLOCKER  
    **修正案:** 各record種別の専用CLI、許可argv、owner、O_EXCL/post-commit検査を列挙する。

17. **所在:** 骨格 §10、C2 所見9、C2 `Mc-positive`  
    **不能:** positive-control fixtureは「exact path + bytes hash」が不変条件なのに、tracked path、bytes、root-registry key、ownerが全て未定義。`Mc-positive` は対象fixtureすら存在しない仕様変異である。  
    **深刻度:** BLOCKER  
    **修正案:** fixture path・literal hash・root key・baseline/mutant bytesを本段で固定する。

18. **所在:** C1 §1.4–1.5、C2 ownership §8.3  
    **矛盾:** C1はW-dで `PREDICTION_SCHEMA` をv2へ更新しつつ「dormant導入」、W-fで「v2のみactive」とする。しかし selector/verdict fileはW-d専有で、W-fが切替えるdata/config条件がない。実際にはW-d時点でv1拒否になる。  
    **深刻度:** BLOCKER  
    **修正案:** g0ならv1、g1以降ならv2というbundle-generation分岐をW-dにexact実装し、Xだけで切替わる契約にする。

19. **所在:** A §1.5.2、C2 `Mc-expiry`、親 brief P5  
    **不能:** approval expiryの意味は未裁定U-A1であり、A自身が「決定前にW-cを開始しない」とする。P5の「具体化は親裁定」の境界では閉じず、実装wave開始条件を満たさない。  
    **深刻度:** BLOCKER  
    **修正案:** activation windowかleaseかをユーザー裁定へ返し、裁定後にschema・check-ID・mutationを再固定する。

20. **所在:** 親 brief P3、C2 §9.1、`docs/failures.md` F28  
    **矛盾:** P3/C2は未実装moduleの単一理由確認を実装waveへ延期するが、F28の恒久対応は「確認できない変異は登録せず、実効gateへ再照準」と明記する。現行表はB-057登録ではなく未検証候補にすぎない。  
    **深刻度:** BLOCKER  
    **修正案:** spec候補とB-057確定登録を別状態にし、predicate/control-flow実装後のコード読解までは確定扱いしない。

21. **所在:** B §5.1、C2 `Ma-blocked`  
    **矛盾:** Bは `blocked_by` を「当該IDより前」に限定し、それだけで非循環を構造保証する。C2の「2-node cycleだけが不正」というfixtureは必ず前方参照規則にも落ちるため、acyclic検査を消しても等価変異になる。  
    **深刻度:** MAJOR  
    **修正案:** cycle変異を削除し、existing-ID／strict-earlier／順序の各実効predicateだけを別fixtureで登録する。

22. **所在:** A §1.9・§1.11、C2 `Me-exclusive-G`  
    **矛盾:** C2は既存generation pathを `M` statusで変更しG diff検査だけを狙うが、Aは同じ入力を `lineage.record.mutated`、追加一回、一意 introductionでも拒否する。G diff predicateを消しても赤いままのF28等価変異。  
    **深刻度:** BLOCKER  
    **修正案:** process O_EXCLはdiagnostic扱いに限定し、post-commit変異は他の履歴predicateを通る独立fixtureへ再設計する。

23. **所在:** A §1.5.1・§2.4、C2 `Mc-digest`  
    **矛盾:** C2は「component固定順またはdomain separator」を一つの変異に束ね、失敗reasonを `authorization.approval.digest_mismatch` 一つとする。しかしAには固定順/schemaと `component_mismatch` が別predicateとして存在し、reorder入力は先にそちらへ落ち得る。  
    **深刻度:** MAJOR  
    **修正案:** component-order変異とdomain-separator変異を分離し、それぞれ第一失敗reasonを一つに固定する。

24. **所在:** B §6、C2 §9  
    **矛盾:** Bは最終 `REQUIRED_FREEZE_NODES` を26件と固定するが、C2が実効性を依存する4 node—2件の`test_hooks`、`test_task_run_ledger`、新selector published-verifier node—が集合にない。manifestごとgateが蒸発できる。  
    **深刻度:** MAJOR  
    **修正案:** 全登録変異のdetector nodeをmanifestへ入れ、最終件数を再計数する。

25. **所在:** 親 brief P3、C2 §8.3・§9 W-d  
    **不能:** P3は既存W-d consumerの「手前検査不在まで確認」を要求するが、C2の実測記述はS-1 3経路と8b数経路だけ。ownership上の19 production file全件に対するpredicate順はなく、`Md-8b-cutover` が参照する「固定consumer registry」も未定義。  
    **深刻度:** MAJOR  
    **修正案:** W-d全consumerのexact registryと各入口の先行predicate順を表にし、各mutation fixtureへ一対一対応させる。

26. **所在:** 親 brief P1、C1 P1、C2 所見13、現物 `tools/check_docs.py`  
    **矛盾:** P1/C2は`check_docs.py`をW-fへ送るが、C1は「livingのままW-fまでlint外」を否認する。現物では第1段docも `LIVING_DOCS` 外なので「第1段と同じ扱い」はcoverage根拠にならない。設計waveの「code 0 byte」と即時lintも両立しない。  
    **深刻度:** MAJOR  
    **修正案:** 第2段を裁定時凍結packageとしてlint対象外にするか、scopeを改裁定して本waveで両docを登録する。

27. **所在:** 親 brief「関連所在」末尾  
    **不一致:** 「現行 ratified-v2 の receipt/approval 機構は `s8b_ratified_freeze.py` が正本」とあるが、現行governance parserは generation/approval/pointer/revocation/cancellationであり、transition receipt recordは存在しない。`receipt` hitはcampaign execution receiptという別物。  
    **深刻度:** MINOR  
    **修正案:** 「generation introduction / approval / pointer機構が下限」と訂正し、transition receiptは完全な新設schemaとして扱う。

28. **所在:** A §1.7.2・§1.10、B §5.5  
    **曖昧:** revocationには人間commit・exact diff・非merge制約があるが、fork cancellationには同等のcommit parent/diff/merge/時刻制約がない。A §1.10表にもRV/cancellation行がなく、B registryにも両recordのID集合がない。  
    **深刻度:** MAJOR  
    **修正案:** revocation/cancellationのcommit topology、human trailer、導入順、check-ID、writer CLIをexact列挙する。

**総評: NO-GO**
---

# 段 4: 親裁定リスト

# 親裁定リスト (第 2 設計段 v2 統合の確定事項) — 2026-07-22

相談 X (25 所見、NO-GO)・Y (28 所見、NO-GO) と草案 4 本の所見を統合した親裁定。
統合版 (s2 doc) はこのリストに従う。番号 J* は統合起草への指示 ID。

## ユーザー裁定パッケージ行き (本 wave では確定しない)

- **U-A1: approval expiry の意味** (A 所見 3、X20、Y19)。選択肢: (a) 未発効の activation window
  (A→X までの有効期限。推奨) / (b) 発効後 lease (X 後も期限で失効)。推奨 (a) + 「committer time は
  backdate 可能なため機械 gate は static 検査に限り、真正性は人間承認の運用規律」と限界明記。
  **expiry 依存の field/check/変異は s2 doc で「U-A1 裁定待ち hole (決定権者ユーザー)」と明示し、
  W-c の開始条件に U-A1 裁定を含める。**

## 骨格正本への追記 (裁定済み帰結の明文化 — 親が実施し worklog へ明示)

- **J28: §14 損失表へ 3 行追記** (X6/X7)。(i) G 後の worktree source drift を新 static verify は
  受理する (R7=(b) 裁定の直接帰結 — 現行は worktree 照合で拒否)。回収層 = launch/audit 層 +
  レビュー。(ii) commit identity (frozen_at_head / pre_oracle_head) → tree 内容同値への交換
  (R1 裁定の帰結 + §13-6 の同型適用)。回収層 = receipt の G/H_gen 束縛。(iii) 実走時のコード・
  gitlink identity は active bundle に機械束縛されない (限界節へ)。
- **J24: §12/関連記述の訂正** (Y27): 現行 s8b_ratified_freeze の下限は generation introduction /
  approval / pointer / revocation / cancellation 機構。transition receipt は完全新設 schema。

## P1..P5 の最終形

- P1 → 修正採用: s2 doc 新設 + 正本 §13 ポインタ化 + docs/README 登録。LIVING_DOCS へは非編入 —
  「設計段 doc は段完了で凍結する design 族」(check_docs.py の phase3-s*-design-* と同じ整理) を
  s2 doc 冒頭と worklog に明記 (Y26 選択肢 1)。コード変更なし。
- P2 → 修正採用: 並列起草は完了。exact 確定は本統合 (merge barrier) で親が行う。
- P3 → 修正採用 (Y20/F28): 本 wave の変異登録は**「事前登録候補 (draft)」という明示の別状態**。
  B-057 確定登録は各実装 wave 開始時のコード読解後。s2 doc に candidate/confirmed の 2 状態を定義。
- P4 → 修正採用: 「exact 完了」を全項では主張しない。U-A1 依存 hole・生成時確定値・W-d 開始時
  再確認事項は決定権者を明記して残す。それ以外は全列挙で閉じる。
- P5 → 修正採用: U-A1 のみユーザーへ。他は親裁定で確定 (本リスト)。

## 統合裁定 (BLOCKER/MAJOR の解消形)

- **J1 (X1/Y1/Y2/Y3)**: receipt は A §1.3 の exact schema を基底とし、B の observation_audit は
  「audit 入力束縛」field として統合する — R は audit の入力 (WAL blob sha256 群・H_gen) を束縛
  するだけで status/pass を持たない (自己申告禁止)。A (人間承認) は同入力から再実行した
  構造化 report (verification / projection / WAL-audit) の canonical bytes sha256 を approval
  record の field として承認し、bundle digest の component に 3 report hash を追加する
  (4 hash → 7 hash、固定順)。resolver は X 後も report hash の存在と型を再検査する。
- **J2 (X3)**: check registry は §4 の四型 (candidate / registered-inactive / approved-inactive /
  active-official) ごとに exact 定義する。candidate 型 registry に output.literal-root 系 check を
  含めない。型昇格は明示の型変換 (追加 check の実行) のみ。fail-open 分岐の構造的排除。
- **J3 (X4)**: launch 層の exact 契約を新設 — LaunchValidatedOfficialBundle 型 + live-scan report
  schema + lifecycle 別 expected-hit 契約。全実走 consumer (oracle driver 系) に要求。W-d 所有。
- **J4 (X5/Y5)**: legacy (g0) 用 exact adapter registry を新設 — legacy known/measurement (schema_version
  無し) / holdout v1 の 3 adapter。検査は「raw bytes exact + 現行 verifier への委譲結果の型変換」。
  g0 campaign-start observation はこの registry の check-ID 集合を使う。W-a 所有。
- **J5 (X8/X25/C2-15)**: C1 の全 tree manifest は G から M へ降格。G には宣言済み semantic input
  closure のみ。field 名は `prediction_basis_tree` へ改名し、「HARKing 機械排除」を主張しない
  (chronological gate は別途の運用規律と明記)。
- **J6 (X10)**: metadata-moves 検査は「旧 G から除去した pointer の列挙が receipt に在ること」のみ。
  M の値を projection predicate に使わない (逆流禁止)。
- **J7 (X11/Y8/Y10)**: WAL source pointer は exact 8 keys に訂正。3 locator (session_start /
  value_record / session_result) の wrapper identity (env_tag / variant / stage) の相互完全一致
  検査を追加。session 区間 = session_start から対応 session_result までの非重複区間として exact
  定義し、value_record はその区間内で唯一であることを検査する。
- **J8 (X12)**: 伝播 field は passed_check_ids でなく「actual result 列から導出した canonical
  report bytes の sha256 + aggregate 判定」。
- **J9 (X13/Y21)**: blocked_by は非 pass status の check のみ指せる + 「前方 (先行) ID のみ」規則を
  正とする。cycle 単独変異は登録から削除 (前方参照規則にマスクされる等価変異)。aggregate fail
  (error/not_evaluated 1 件で全体失敗) の変異を独立登録。
- **J10 (X14/Y17)**: positive-control fixture を本段で exact 固定 — tracked path
  (orchestrator/tests/data/ 配下)、手書き固定 bytes (search/builder 実装から独立に作る)、
  root-registry key、baseline pass / 単一理由 mutant fail / revert pass の 3 点期待値。
- **J11 (X15)**: conformance vector は入力を s2 doc に literal 固定。期待出力は W-a 実装時に
  「独立実装とは別の第三手段 (外部参照実装) で導出して literal 化 + レビュー確認」と規定
  (決定権者: W-a 実装時の親)。独立実装自身からの期待値生成を禁止。
- **J12 (X16)**: literal 3 面分離 — production root registry (registry shell と世代別 literal data
  file を分離、Y13) / FROZEN_MANIFEST (テスト側) / 独立 golden test (新設、別値源)。
  Me-keyset 変異の detector を変異対象と別ファイルにする。
- **J13 (X17/Y7/A 所見 6)**: known 世代遷移の許可面は「H_gen 再列挙アルゴリズムからの動的導出」形 —
  再導出で変わりうる subtree (members / records[].path / lines / sha256 / count) は「再導出一致」を
  検査し、それ以外は不変を要求する。measurement/holdout の gN→gN+1 表には known 2 leaf
  (path/sha256) の変更を lockstep 前提で許可する (現行 9 pointer は流用しない)。
- **J14 (X18)**: holdout の confirmed_by/confirmed_at は世代ごとに fresh 必須の変更 field とし、
  当該世代の search report に束縛する。
- **J15 (X19/Y9)**: G guard の start snapshot は inventory の exact canonical JSON schema +
  domain separator を全文定義。範囲は tracked file/symlink/gitlink のみと正直に限定し、untracked
  検出の主張は削除。各境界で tree OID に加え commit OID を再検査。
- **J17 (X21/Y28)**: fork cancellation にも revocation と同一の commit topology 制約 (単一 record
  追加 diff、非 merge、対象の後裔、AI-Agent: none) を課す。A §1.10 表と registry に RV/CX 行を追加。
- **J18 (X22/Y6)**: reason code は単一 grammar `<namespace>.<snake_case>` (dot 1 個、kebab 禁止) に
  統一。C1 の selector-pre-oracle-* / known-source-* は §4 namespace (lineage.* / input.*) 配下へ
  改名。統合版に全 code の単一対応表を置く。未知 reason は report 全体 error。
- **J19 (X23/Y14/Y22/Y23/Y24)**: 変異候補表を再設計 — (i) 等価変異の除去 (Mc-cycle、Me-exclusive-G
  の post-commit 変異は独立 fixture へ再設計、Md-preoracle-hash は tree OID 束縛と coupled で登録)、
  (ii) detector node の wave 帰属を修正 (known direct test = W-b、resolver direct test = W-c)、
  (iii) 全 detector node を REQUIRED_FREEZE_NODES に含め再計数、(iv) component-order と
  domain-separator の変異を分離。
- **J20 (X24/Y16/C2-4)**: record 種別ごとの writer CLI を exact 列挙 — 単一 file
  `orchestrator/campaign/freeze_permanent_cli.py` (W-c 所有、W-b/W-c module を dispatch) に
  generate / pointer-init / receipt / approval-record / activate / revoke / cancel subcommand。
  各 subcommand の許可 argv・書込 path template・O_EXCL・post-commit 検査を列挙。hook 許可は
  この CLI 経由のみ。W-e/W-f はコード変更なしで CLI を実行するだけ。
- **J21 (C2-3)**: 新設 module/テストの命名を統合版で一元確定 (known v2 の module/direct test を含む
  全新設ファイルの exact path 表)。命名は既存規約から導出し、所有表 (§13-8) と 1:1。
- **J23 (Y25)**: W-d consumer の exact registry (19 production file) を統合版に置く。各入口の先行
  predicate 順は「W-d 開始時に再実測して確定」(決定権者: W-d 実装 wave の親) と明記。
- **J25 (Y18)**: PREDICTION_SCHEMA の v1/v2 は bundle-generation 分岐 (pointer g0 → v1 受理、
  g1+ → v2 のみ) として W-d で dormant 実装し、X の pointer 更新だけで切替わる契約。
- **J26 (Y11)**: 独立統計実装は producer (s1_stats 系) と verifier (新 module) の相互 import 禁止を
  仕様化 (test で機械検査)。
- **J27 (X9)**: selector 後継 record の導入後不変性 — H_v 到達履歴で導入 commit 後の M/D/R/C/T を
  拒否し、current blob = 導入 blob を要求する check を追加。
- **J-conftest (Y14/C2-11)**: conftest の node manifest は W-a で「登録 data file 読込」構造へ
  一回だけ拡張し、各 wave の node 追加は wave 所有の data file 側で行う (conftest 再変更なし)。
- **J-tests-readme (C2-12/Y15)**: 新設テストは全件自走 harness 必須 (pytest-only allowlist に
  載せない) — orchestrator/tests/README.md の変更を W-f 1 回に保つ。
- **J-ledger (C2-1)**: 新設 output namespace (freeze-permanent / freeze-migrations) の
  tools/task_runs/ledger.py:50 namespace 列挙への追加を W-0 の変更対象に含める。
- **J-fixture-hermetic**: 変異候補の期待値には揮発する診断 payload を焼き込まない (dev-wave 定型)。

## 統合版に残してよい明示 hole (決定権者つき)

1. U-A1 依存の field/check/変異 (決定権者: ユーザー)
2. conformance vector の期待出力 literal (決定権者: W-a 実装時の親、J11 の手順で)
3. W-d consumer の先行 predicate 順 (決定権者: W-d 開始時の親、J23)
4. 生成時確定値 (record 総数、observation 件数等 — 骨格どおり事前確定しない)

---

# 段 6a: fix 対応表 (codex)

変更した節: 冒頭、§S2-1.1/1.5/1.6/1.8/1.11/1.12/1.14、§S2-2b.2/2b.4、§S2-3.1〜3.5、§S2-4.1〜4.5、§S2-5.3/5.4、§S2-7、§S2-8.1〜8.3、§S2-9.2、§S2-10、§S2-11.1、§S2-12.1/12.4/12.5、「レビュー R1/R2 対応表」。

- R1-1: 冒頭で第1段の訂正済み7-component契約を§S2-2が具体化・置換すると明記。
- R1-2: §S2-3.5/§S2-10でR2方向を採用し、g0をraw root・strict parse・型変換だけに限定。
- R1-3: §S2-1.8/1.14/2b.4/5.4で3 reportをcontent-addressed tracked artifactとQ commitへ固定。
- R1-4: §S2-1.5/1.6でgeneration-search reportをtracked化し、confirmationとのraw hash束縛を追加。
- R1-5: §S2-8.3/§S2-9でMe-keysetのdetectorを独立golden testへ変更。
- R1-6: §S2-8.3にfinal 42 nodeを逐語列挙し、§S2-9にregistry/predicate/manifest同時削除変異を追加。
- R1-7: §S2-4/§S2-9でreport、RV、CX、Aのschema・diff・merge・trailer変異を単一理由fixtureへ分割。
- R1-8: §S2-1.12/§S2-7でsource_closure配列全体のH_gen exact-union再導出規則へ一本化。
- R1-9: §S2-1.11/1.14でCXをtarget・survivor双方の後裔とし、CX^時点のfork集合を固定。
- R1-10: §S2-3.1/3.4でfreeze_identityと全伝播schemaの型・literal・null規則を確定。
- R1-11: §S2-12.1へuntracked一時除去・復元で偽confirmationを承認しうる損失行を追加。
- R1-12: §S2-11.1へlease案のclock、use-time、伝播、cache禁止、version分離holeを追加。
- R1-13: 冒頭状態行をU-A1とconformance期待出力literalの2未了gateへ訂正。
- R1-14: §S2-12.1でfrozen anchor、pre-oracle、一般source driftを別行・限定回収層へ分離。
- R1-15: §S2-7/§S2-12.4でenumeration snapshotをexact 5-field表記へ統一。
- R2-1: §S2-3.5/§S2-10でfull verifier委譲を除去し、g0 refusal集合を3種類に固定。
- R2-2: §S2-1.1でg1+の3 family artifact本体へexact canonical encoderを適用。
- R2-3: §S2-1.8/1.14/2b.4でreport path、hash、subjects、aggregate、validation_head、Q topologyを固定。
- R2-4: §S2-2b.2でgates・families・効果量・CV丸めを含むnested schemaを復元。
- R2-5: §S2-1.12/§S2-7でrecords順序・一意性・型別key・glob・disposition優先順を確定。
- R2-6: §S2-4.5に173行のcheck-ID TSVを置き、field pointer・直接依存・単一reasonを固定。
- R2-7: §S2-3.1〜3.4でWAL、S-1 report、Oracle、calibrationのexact契約を復元。
- R2-8: §S2-3.4にg1 source WAL専用の旧campaign-start grammarを分離。
- R2-9: §S2-8/§S2-9でresolver単体testをW-c、19 consumer直読検査をW-dの新testへ分離。
- R2-10: §S2-8.3でdata-file exact schemaと既存12・新規29・meta-testの全42 nodeを固定。
- R2-11: §S2-10のlive-scan reportをexact 12 fieldsへ整合。
- R2-12: 冒頭と§S2-8.1で非LIVING design族およびW-f非所有の契約へ整合。
- R2-13: 冒頭は可変状態を索引へ再掲せず、凍結design族としての安定した役割だけを保持。
- R2-14: 不正確な「未解消0件」を削除し、全29所見のレビュー対応表へ置換。
---

# 段 6b: 敵対レビュー R1

1. (i) 所在: [s2 冒頭 L7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:7)「衝突時は第1設計段が上位」、第1段 [§7 L280](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:280)「対象4 hash」、s2 [§S2-2 L562](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:562)「raw SHA-256 7件」。 (ii) 問題: 上位規則に従えば4-componentが勝ち、X2で追加した3 report hashのdigest束縛が無効になる。親裁定J1が上位正本へ反映されていない。 (iii) 深刻度: **BLOCKER**。 (iv) 修正案: 第1段§7を7-componentへ訂正し、s2のexact仕様が旧プレースホルダを置換する旨を明記する。

2. (i) 所在: 第1段 [§8 L303-L306](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:303)「legacy loaderはraw bytes exactのみ保証」、s2 [§S2-3.5 L962-L971](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:962)「現行verifierへ委譲」。 (ii) 問題: X5の元の矛盾が上位・下位正本間に残る。現物実行では3 legacy verifierすべてがdangling anchor/design-source driftで拒否する一方、raw-root loaderは受理するため、g0のrefusal集合も一意に定まらない。 (iii) 深刻度: **BLOCKER**。 (iv) 修正案: 第1段§8をexact adapter委譲へ訂正し、3 delegateの呼出引数・成功/失敗型変換も固定する。

3. (i) 所在: [§S2-1.8 L324-L334](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:324)「report SHA-256のみ」「resolverは…存在、string型、64 lowercase hex」、[§S2-2b.4 L843-L847](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:843)。 (ii) 問題: verification/projection/WAL-audit report本文のtracked path、導入commit、lookup規則がない。resolverは本文・aggregate・`validation_head/H_gen`を再検査せず、任意64hexを並べたapprovalと自己整合digestを受理できる。X2は構文束縛に縮退している。 (iii) 深刻度: **BLOCKER**。 (iv) 修正案: 3 reportをcontent-addressed tracked artifactとして追加し、A/X resolverが本文hash、対象head、subjects、aggregateを再検証する。

4. (i) 所在: [§S2-1.5 L233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:233)「report自体はreceiptへ埋め込まず…SHA-256をconfirmationが束縛」、[§S2-1.6 L250-L253](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:250)。 (ii) 問題: generation search reportにも保存pathもcanonical本文の再構築predicateもない。holdoutとreceiptで同じ任意hashを記録するだけの実装が仕様適合となり、X14/X18のpositive-control・fresh confirmation証拠が空洞化する。 (iii) 深刻度: **BLOCKER**。 (iv) 修正案: search reportをtracked immutable recordにするか、artifact/H_genから全7 fieldsを再構築してhash一致を必須化する。

5. (i) 所在: [§S2-9 `Me-keyset` L2034](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2034)「len 12だけ… detector=`test_frozen_artifacts.py::…exact_keyset`」。 (ii) 問題: 変異対象もdetectorも同じtest predicateである。exact集合assertを`len==12`へ変異すると、そのdetector自身が緑になり、X16が未解消である。別値源のgolden testはこの候補のdetectorに使われていない。 (iii) 深刻度: **BLOCKER**。 (iv) 修正案: keyset literalを独立golden fileへ置き、`test_freeze_permanent_literal_golden.py`からproduction/test manifestを照合する。

6. (i) 所在: [§S2-8.3 L1973-L1974](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1973)「既存12 node + 新規detector 29 node = final exact 41」、[§S2-9 `Ma-registry` L2002](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2002)。 (ii) 問題: 29 detectorは再計数できるが、land本文には既存12 nodeの文字列集合がない。またX23が要求した「predicateとregistry IDの同時削除」変異もなく、production registry・predicate・data manifestを同時削除するcoupled mutantを独立値源が捕捉しない。 (iii) 深刻度: **BLOCKER**。 (iv) 修正案: final 41 nodeを逐語列挙し、schema別IDの独立goldenとpredicate+ID同時削除mutantを追加する。

7. (i) 所在: [§S2-9 L2018-L2022](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2018)の`Mc-report/Mc-rv/Mc-cx`、[L2036](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2036)の`Me-A-diff`。 (ii) 問題: `Mc-report`の欠落は先行する`approval.schema`にマスクされ得る。さらにRV/CX/Aの「diff/merge/trailer」を一候補へ束ねているが、trailer変異の第一失敗は明示的な`*.human-trailer`であり、表の`commit-topology/commit-diff`ではない。単一理由性が成立しない。 (iii) 深刻度: **MAJOR**。 (iv) 修正案: schema欠落・semantic hash mismatch・diff・merge・trailerを別mutant/fixtureへ分割する。

8. (i) 所在: [§S2-1.12 L459-L465](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:459)「`records[*]`のpath/sha256」、[§S2-7 L1727](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1727)「recordはexact `{record_type,path,sha256,key}`」。 (ii) 問題: member追加時は`record_type/key`も新規leafになるが、許可面はpath/hashだけで、別文ではtype/keyを再導出するとする。厳密実装は正当な集合変化を拒否し、緩い実装はarray全体を任意変更できる。X17の動的世代遷移が一意でない。 (iii) 深刻度: **MAJOR**。 (iv) 修正案: `/source_closure/records`全体を「H_genから再導出したexact unionと一致する場合のみ」変更可と定義する。

9. (i) 所在: [§S2-1.11 L442-L447](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:442)、[§S2-1.14 L547-L552](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:547)「CXはtarget pointer introductionの後裔」。 (ii) 問題: survivorの後裔条件がない。CX導入時にはsiblingが存在しなくても、後から別branchのsiblingを取り込めばH_v時点の条件だけで事前取消が有効になる。X21の修正案の半分が落ちている。 (iii) 深刻度: **MAJOR**。 (iv) 修正案: CXをtargetとselected survivor双方の後裔とし、CX tree時点でfork集合を検査する。

10. (i) 所在: [§S2-3.1 L857-L873](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:857)「freeze_identity exact 10 keys」。 (ii) 問題: `schema_version` literal、`lane` enum、`pointer/receipt/approval`参照のexact shape・nullabilityが未定義である。鍵集合だけexactでも、任意dict/stringを受理する実装が可能で、X12の観測伝播はclosed-worldにならない。 (iii) 深刻度: **MAJOR**。 (iv) 修正案: 10 fieldすべての型・enum・reference object・g0/g1+ nullabilityを逐語定義する。

11. (i) 所在: [§S2-5.2 L1536-L1545](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1536)「untracked fileをsnapshotで検出するとは主張しない」「§14追記案へ明示」、[§S2-5.3 L1561](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1561)「root untracked regular列挙を維持」。 (ii) 問題: untracked hitをsearch直前に除去し直後に戻しても全snapshot境界を通る。launchで最終実走は止められるが、G/Aは偽のgeneration confirmationを承認し得るうえ、約束された損失行は§S2-12にも親§14ハンクにも存在しない。 (iii) 深刻度: **MAJOR**。 (iv) 修正案: untracked集合を境界snapshotへ含めるか隔離treeからのみ生成し、残余を§14へ明記する。

12. (i) 所在: [§S2-11.1 L2127-L2137](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2127)の裁定待ち一覧、[§S2-10 L2055-L2066](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2055)のdeep-immutable launch型。 (ii) 問題: lease案では期限前に作った型を期限後に保持・実走できるが、`validated_at/expires_at`、use-time再検査、clock capture、observation/report伝播、cache禁止がhole一覧にない。また同じapproval schema/scopeにactivation-windowとleaseの二意味を持たせる。 (iii) 深刻度: **MAJOR**。 (iv) 修正案: schema/scopeを案別version化し、clock capture・型の有効期限・全consumerのuse-time check・伝播field/変異をU-A1依存面へ追加する。

13. (i) 所在: [§S2-2b.3 L809-L825](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:809)「期待出力literalは許可hole」、[§未解消所見 L2202-L2207](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2202)「未解消所見0件」、[docs/README L38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/README.md:38)「未了=U-A1の1件」。 (ii) 問題: X15が要求したliteral outputは存在せず、`Ma-stat-ref`のoracleもまだ成立しない。親が延期を許したことと「実質解消」「未了1件」は同義でなく、状態表示が未完了条件を隠す。 (iii) 深刻度: **MAJOR**。 (iv) 修正案: literalをland前に確定するか、状態行へW-a開始前の未了gateとして明記する。

14. (i) 所在: [parent-edits.diff L71-L72](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-s2/parent-edits.diff:71)の§14二行、現行 [s8b_selector_freeze.py L618-L623](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:618)。 (ii) 問題: 現行`pre_oracle_head`は40hexかつ「何らかの実在commit」であれば通り、意図した時点とのidentity mismatchを検査しないため、「commit identity不一致を現行は拒否」は過大主張である。また一般のcurrent source driftをlaunch/auditが回収する検査もなく、同ハンクL80-L82の「実走code/binary/gitlinkは未束縛」と矛盾する。 (iii) 深刻度: **MAJOR**。 (iv) 修正案: frozen anchorとpre-oracle存在検査を別行にし、source driftの回収層をreview/実行環境規律へ限定する。

15. (i) 所在: [parent-edits.diff L36-L39](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-s2/parent-edits.diff:36)「algorithm ID・exact pattern・members・file_count」、s2 [§S2-7 L1758-L1761](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1758)「exact `{enumeration_id,algorithm,pattern,members,file_count}`」。 (ii) 問題: 親§3.1訂正はs2のexact objectに必須の`enumeration_id`を落としており、一字一句・field集合とも一致しない。なお親§7-R訂正は現物コードと一致した。 (iii) 深刻度: **MINOR**。 (iv) 修正案: 親§3.1へ`enumeration_id`を追加し、s2と同じ5-field表記にする。

総評: **NO-GO**
---

# 段 6c: 敵対レビュー R2

再計数では 9 blob、63/31、24/6、18/12/288、WAL 1009/505/505、transition 13/9、`FROZEN_MANIFEST` 8、grep 和集合44、g0 pointer hashは一致した。所有表も91行すべて一意、変異41候補の detector は29 uniqueだった。以下は計数誤差ではない。

1. **(i) 所在:** [§S2-3.5 L962](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:962)「root一致後に現行verifierへ委譲」、対して[第1段 §8 L303](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:303)「legacy loader は raw bytes exact のみ保証」。  
   **(ii) 問題:** Y5は解消していない。指定HEADで三adapterを実走すると、known/measurementはdangling `frozen_at_head`、holdoutは`design_source` driftで全件失敗する。既存の正しいlegacy型も[source/headを再検証しない契約](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:729)であり、S2方式ではg0 bundleを構築できずW-dの挙動保存が成立しない。  
   **(iii) 深刻度:** **BLOCKER**  
   **(iv) 修正案:** legacy三adapterを「raw root照合＋strict parseのみ」に直し、現行full verifier委譲をgateから外す。

2. **(i) 所在:** [§S2-1.1 L34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:34)「governance record と後記 report の canonical bytes」。  
   **(ii) 問題:** canonical raw-byte契約の対象からknown/measurement/holdout本体が抜けている。三artifactのraw SHAがreceipt・literal root・bundle digestを決めるため、compact JSON、indent付き、末尾LFありの複数実装が全てschema上有効になり、Gが一意にならない。  
   **(iii) 深刻度:** **BLOCKER**  
   **(iv) 修正案:** g1+三family artifactにもexact encoderとraw-byte一致拒否を明記する。

3. **(i) 所在:** [§S2-1.8 L324](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:324)「A作成CLIは…再実行」、[L333](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:333)「resolverは…report hash fieldの存在、string型…を検査」、[§S2-2b.4 L843](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:843)。  
   **(ii) 問題:** Y2/Y3/Y16の核心が残る。三reportには永続path・owner・writer・導入topologyがなく、Aはapproval一ファイルしか追加できない。後日resolverが検査するのは64hexとcomponent一致だけなので、人間が任意hashを置いてもpass report由来か証明不能である。  
   **(iii) 深刻度:** **BLOCKER**  
   **(iv) 修正案:** 三reportをcontent-addressed pathへ永続化してAに先行導入するか、`validation_head=A^`を束縛してresolverが三reportを決定的に再計算する。

4. **(i) 所在:** [§S2-2b.2 L730](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:730)「analysis_results は exact 5 keys」、[L740](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:740)「各要素は exact 9 fields」。  
   **(ii) 問題:** `gates`の子field・型、`families`がarrayかobjectか、family要素のfield・順序、CVの最終丸めが未定義で、canonical `analysis_results`を一意に生成できない。草案にあったexact nested schemaが統合時に落ちている。  
   **(iii) 深刻度:** **BLOCKER**  
   **(iv) 修正案:** gates二型とfamily二要素の全field・型・順序・算術をliteral表として復元する。

5. **(i) 所在:** [§S2-7 L1727](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1727)「records elementは exact `{record_type,path,sha256,key}`」、[L1782](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1782)「records path集合は…union」。  
   **(ii) 問題:** Y7は実質未解消。recordsの順序・path一意性、campaign lockの`key="/search_config"`、classifierの`key="/trial"`、globの`*`意味、sort dispositionの優先順が消えている。さらに§S2-1.12は動的recordの追加削除をleaf変更として扱うため、正常な世代遷移のarray diffも一意でない。  
   **(iii) 深刻度:** **BLOCKER**  
   **(iv) 修正案:** record全体の動的再導出規則、型別key、path順、glob意味、disposition優先順をexactに列挙する。

6. **(i) 所在:** [§S2-4.2 L1132](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1132)「semantic IDは…互いには依存しない」、[§S2-4.3 L1219](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1219)「dependencyは上から順に…same-stage」。  
   **(ii) 問題:** Y4が要求したexact `blocked_by` graphではない。「same-stage」の所属も各IDの直接依存辺も列挙されず、同じ入力を`error`にするか`not_evaluated`にするか実装者依存になる。また§S2-1.12の世代diff、L_prod/L_manifest topologyに対応する明示check-IDもない。  
   **(iii) 深刻度:** **BLOCKER**  
   **(iv) 修正案:** 各check-IDへexact field pointer・直接依存ID集合・単一reasonを持たせた機械読取可能表に置換する。

7. **(i) 所在:** [§S2-3.1 L857](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:857)「freeze_identity exact 10 keys」、[§S2-3.4 L942](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:942)「現行v1のfreeze_refを削除し…追加」、[L945](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:945)。  
   **(ii) 問題:** §13-3のexact化が失われている。`freeze_identity.schema_version` literalとpointer/ref型、Oracle observations/verdictのtop-level exact keyset、`freeze_contract_reason_codes`の型・code集合、calibration v2のschemaがない。W-dは複数の非同値schemaを実装できる。  
   **(iii) 深刻度:** **BLOCKER**  
   **(iv) 修正案:** WAL、S-1 report、Oracle observations/verdict、calibrationごとの全key・型・null規則・reason集合を復元する。

8. **(i) 所在:** [§S2-2b.1 L652](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:652)「現行g1候補の観測値」、対して[§S2-3.4 L916](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:916)はcampaign-start v2のみを定義。  
   **(ii) 問題:** 指定された三WALの実物は、例えば[block1 WAL L1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2/runs/wal.jsonl:1)のように`event_schema`・三freeze objectを持たない旧payloadである。`audit.campaign-start`が旧schemaをどう受理・検査するか未定義なので、g1 A-auditは実装不能または実装差になる。  
   **(iii) 深刻度:** **BLOCKER**  
   **(iv) 修正案:** g1 source WAL専用の旧campaign-start exact grammarを、将来の伝播v2 grammarと分離して追加する。

9. **(i) 所在:** [§S2-8.1 L1850](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1850)でresolver testはW-c専有、[§S2-9 L2023](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2023)でW-d cutoverのdetectorも同test。  
   **(ii) 問題:** Y14の各wave単独greenを再び破る。W-c時点では現行consumerが実際に旧pathを直読している（[s1_direct_comparison.py L43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:43)、[s8b_oracle_driver.py L53](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:53)等）。実物を検査すればW-cが赤、fixtureだけならW-d mutationをkillできず、W-dはW-c所有testを直せない。  
   **(iii) 深刻度:** **BLOCKER**  
   **(iv) 修正案:** resolver単体testはW-cに残し、19 consumer直読検査をW-d所有の別testへ分離する。

10. **(i) 所在:** [§S2-8.3 L1969](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1969)「data file読込」、[L1973](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1973)「既存12 + 新規29 = 41」。  
    **(ii) 問題:** 29 detectorのunique再計数は正しいが、既存12のnode名とdata-file JSON schemaが正本中にない。現行repoにも`REQUIRED_FREEZE_NODES`は存在せず、`base.json`を一意に作れない。collectability meta-test自身も29 detector集合に含まれない。  
    **(iii) 深刻度:** **BLOCKER**  
    **(iv) 修正案:** data-file exact schemaと既存12を含むfinal 41 nodeのliteral完全集合を本文へ置く。

11. **(i) 所在:** [§S2-10 L2068](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2068)「exact 11 fields」、[L2086](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2086)「exact field countは12」。  
    **(ii) 問題:** 再計数は12であり、同一schemaに相反するnormative countが残る。  
    **(iii) 深刻度:** **MINOR**  
    **(iv) 修正案:** L2068を`exact 12 fields`へ訂正する。

12. **(i) 所在:** S2は[冒頭 L7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:7)で「衝突時は第1設計段が上位」、[L10](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:10)でLIVING_DOCS非編入。一方、上位文書は[§9 L359](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:359)でLIVING_DOCS追加、[§12 L443](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:443)でW-fの`docs/README.md`/`check_docs.py`変更を要求。  
    **(ii) 問題:** check_docs契約と所有表が上位/下位で正反対であり、親ハンクもこの二箇所を訂正していない。S2非編入自体は凍結design族として妥当だが、land後の実装指示が一意でない。  
    **(iii) 深刻度:** **BLOCKER**  
    **(iv) 修正案:** 親ハンクで第1段§9/§12を「非編入・README登録は設計waveで完了・W-f変更なし」へ訂正する。

13. **(i) 所在:** 親ハンク[diff L11](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-s2/parent-edits.diff:11)、現物[docs/README.md L38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/README.md:38)「未了 = U-A1 の1件」。  
    **(ii) 問題:** `docs/README.md`はLIVING_DOCSであり、[CLAUDE.md L153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/CLAUDE.md:153)が禁じる可変状態の再掲そのもの。`check_docs.py`は意味的ずれを検出しないため現状passするが、U-A1裁定直後に腐る。  
    **(iii) 深刻度:** **MAJOR**  
    **(iv) 修正案:** READMEから`未了 = ...`を削り、安定した文書種別と役割だけを記載する。

14. **(i) 所在:** 親ハンク[diff L26](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-s2/parent-edits.diff:26)・[L60](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-s2/parent-edits.diff:60)「未了はU-A1の1件のみ」、S2自身も[§未解消所見 L2202](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2202)「0件」。  
    **(ii) 問題:** 上記BLOCKERはいずれも許可された4 holeの外であり、この状態行・§13 pointer・README説明は事実に反する。親が直接書いた未レビューhunkをlandさせる根拠が崩れている。  
    **(iii) 深刻度:** **BLOCKER**  
    **(iv) 修正案:** 全BLOCKER解消と再レビュー完了まで「U-A1のみ」「0件」の三記述を削除する。

総評: **NO-GO**
---

# 段 6d: fix 検証 (1 巡目)

## 結論

**NO-GO**。29件中、**解消 26 / 部分 3 / 未解消 0**。ただし、部分残存と fix 新規の BLOCKER があるため land 不可です。

再計数値は、legacy 9 blob、63/31 source、24/6 implementation、18/12/288、WAL 1009/505/505、transition 13/9、manifest 8、grep 和集合44、g0 pointer hashが一致。新設分も7 components、Q report 4件、所有表93行・全一意、consumer 19、node 42・全一意、変異49候補・detector 29 unique、TSV 173行・173 ID uniqueでした。明記されたfield/key数にも計数不一致はありません。

## 1. R1 判定

| 所見 | 判定 | 根拠 |
|---|---|---|
| R1-1 | 解消 | 第1段が7 componentsへ訂正され、本書の固定順7件と一致した。[第1段](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:281)、[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:614) |
| R1-2 | 解消 | 親裁定どおりR2方向を採用し、g0 gateをraw root・strict parse・型変換の3種に限定した。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1286) |
| R1-3 | 解消 | 3 reportはcontent-addressed artifactとなり、Q導入、bytes、subjects、aggregate、validation headを再検査する。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:343) |
| R1-4 | 解消 | generation-search reportもtracked化され、confirmation・filename・raw hashが一致必須になった。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:218) |
| R1-5 | 解消 | `Me-keyset` は独立golden testをdetectorに使用する。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2807) |
| R1-6 | 解消 | 42 nodeが逐語列挙され、registry/predicate/manifest同時削除mutantも追加された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2659) |
| R1-7 | 解消 | report schema/semantic、およびA/RV/CXのdiff・merge・trailerが別候補・別checkへ分割された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2786) |
| R1-8 | 解消 | `records` はH_genからのexact union全体と一致する場合だけ置換可能になった。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:500) |
| R1-9 | 解消 | CXはtargetとsurvivor双方の後裔で、`CX^`時点のexact fork集合を要求する。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:479) |
| R1-10 | 解消 | `freeze_identity` 10 fieldの型・literal・lane別null規則が逐語化された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:991) |
| R1-11 | **部分** | 一時除去攻撃はS2の損失案には明記されたが、同節自身が「第1段を書き換えた扱いにしない」とし、実際の上位§14には未反映。[S2案](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2944)、[上位§14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:478) |
| R1-12 | 解消 | lease案のclock、use-time再検査、cache禁止、伝播、schema/scope分離がholeへ追加された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2909) |
| R1-13 | 解消 | S2状態行はU-A1とconformance literalの2件を表示し、READMEは状態を再掲せずS2へ指す。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:3)、[README](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/README.md:38) |
| R1-14 | 解消 | frozen anchor、pre-oracle identity、一般source driftが別々の交換として第1段§14へ反映された。[第1段](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:484) |
| R1-15 | 解消 | 上位・下位ともenumeration snapshotを同じ5-field objectとして定義する。[第1段](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:115) |

## 2. R2 判定

| 所見 | 判定 | 根拠 |
|---|---|---|
| R2-1 | 解消 | full verifier委譲は除去され、現物3件でg0 bundleを構築できる契約になった。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1292) |
| R2-2 | 解消 | g1+の3 family artifact本体にもcanonical raw-byte一致が必須化された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:38) |
| R2-3 | 解消 | report path・owner・Q topology・subjects・aggregate・validation headが固定された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:916) |
| R2-4 | 解消 | gates、families、effect fields、CV最終丸めまでexact化された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:816) |
| R2-5 | 解消 | records順序・一意性・型別key・glob・disposition優先順が固定された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2335) |
| R2-6 | **部分** | 173行表は追加されたが、report field pointerと5 dependency配列が自書契約に違反する。下記新規問題1・2。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1639) |
| R2-7 | 解消 | freeze identity、WAL、S-1、Oracle、reason集合、calibrationのexact schemaが復元された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:991) |
| R2-8 | 解消 | 旧WAL専用grammarがv2と分離され、実物3 WALの先頭recordとも一致した。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1126) |
| R2-9 | 解消 | resolver単体testはW-c、19 consumer直読検査はW-dの別testに分離された。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2623) |
| R2-10 | 解消 | data-file schemaと42 node完全和集合が本文に存在し、全42件は一意・各file内sortedだった。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2628) |
| R2-11 | 解消 | live-scan reportは両箇所ともexact 12 fieldsで一致した。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2845) |
| R2-12 | 解消 | 第1段§9/§12は非LIVING・W-f非所有へ訂正済み。[第1段](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:362) |
| R2-13 | 解消 | READMEは可変件数を再掲せず、S2冒頭を正本として指すだけになった。[README](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/README.md:38) |
| R2-14 | **部分** | S2の「0件」は除去されたが、上位第1段の冒頭と§13は依然「U-A1の1件のみ」。S2の2件表示と矛盾する。[第1段冒頭](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:3)、[第1段§13](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:454) |

## 3. fix が新規に導入した問題

1. **BLOCKER — check-ID TSVのreport pointerが実schemaを指さない。** TSVは `/report/results` と `/report/aggregate` を指定するが、3 reportのexact schemaはtop-level `/results` と `/aggregate` であり、`report` wrapperはどこにも定義されていない。[TSV](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1661)、[report schema](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:940)

2. **BLOCKER — TSV自身が要求するdependency順に5行が違反。** 例えば `measurement.schedule` より後の`observations-shape`を先に記載している。違反は `measurement.observations-bijection`、`analysis-statistics`、`analysis-gates`、`analysis-effects`、`approval.report-topology`。複数dependency失敗時のcanonical `blocked_by`が本文内で二通りになる。[順序契約](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1641)、[違反行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1717)

3. **BLOCKER — 42-node manifestはwave単独greenと両立しない。** W-aでexact 7 file readerへ切り替える一方、`wb/wc/wd/we.json`は後続wave所有で、空arrayも禁止される。W-a時点では「欠落」「W-aによる他wave file先行作成」「空placeholder」の全てが本文契約に反する。[7-file契約](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2630)、[空array禁止](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2653)、[所有表](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2495)

4. **MINOR — staleな4-component説明。** normative仕様は7件で一致したが、§S2-2末尾だけが現在も「第1段§7の4-component骨格」と記述している。[S2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:660)

## 4. 総評

**NO-GO**。

少なくとも、R1-11の上位§14未反映、R2-6の無効なmachine-readable表、R2-14の上位状態行不整合に加え、新規BLOCKER 3件があります。数値・列挙数は概ね正しいものの、実装可能性とfail-closed性を担う本文がまだ一意ではありません。
---

# 段 6e: 最終チェック (2 巡目)

| # | 判定 | 根拠 |
|---|---|---|
| 1. R1-11 | 解消 | [第1段 §14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:488) に untracked 一時除去、偽 confirmation、live-scan 回収と残余限界があり、S2-12.1 と同旨。 |
| 2. TSV pointer | 解消 | 3 report は top-level `results` / `aggregate` で、TSV も `/results...` / `/aggregate`。`/report/...` は 0 件。残る `@report/...` は明示された拡張 pointer で wrapper 前提ではない。 |
| 3. 依存順 | 解消 | TSV 173 行・173 ID を機械検査し、配列順違反 0、未知依存 0、後方依存 0。指定された5行も registry 出現順。 |
| 4. manifest wave green | 未解消 | W-0〜W-e の段階的 green、42 node（12+3+7+5+7+6+2）、collectability meta-test、限界の同型性は成立するが、final check は W-f 所有なのに配置先 `test_frozen_artifacts.py` は [W-e 専有](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2559)であり、single-owner 契約に反する。 |
| 5. stale 文言 | 解消 | [§S2-2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:660) は訂正済み 7-component 契約を実物根拠としている。 |
| 6. R2-14 | 解消 | 第1段冒頭・§13は未了2件を明記し、S2冒頭も同じ2件。`docs/README.md` は件数を再掲せずS2冒頭へ委譲しており、三者に矛盾なし。 |
| 7. §S2-12 の位置づけ | 未解消 | 12.1/12.2/12.4/12.5と12.3本文の意味は適用済みだが、12.3は「第1段 §12訂正案」とされる一方、実文は [第1段 §7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:271) に配置されているため、「差分は表現調整のみ」は厳密には不正確。 |

新規問題:

- **BLOCKER:** [W-f final check](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2663) の所有先が存在しない。W-eで実装してW-fは実行だけを所有する等、file ownershipとの整合が必要。
- **MINOR:** S2-12.3の適用先見出し（§12）と実配置（§7）が不一致。

**総評: NO-GO。** 5件解消、2件未解消で、特に W-f final check の所有矛盾が land を阻む。
---

# 段 6f: 最終確認 (3 巡目、GO)

1. **解消** — 12+3+7+5+7+6+2=42 で W-e 時点に全7 manifestが揃い、§S2-8/9の所有・detector帰属と整合し、W-f は受入全走で通常収集される W-e 所有 check を実行する一経路のみ。
2. **解消** — S2-12.3 は適用先を第1段 §7-R と正しく示し、両本文とも receipt を「現行機構の拡張ではない完全新設 schema」としており同旨。

**総評: GO。**