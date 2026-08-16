# 段 4 裁定 — [T-1155] + [T-1178]

2026-08-16 15:0x JST / wave `dev-wave-t1155-t1178-floor-receipt`

## 0. 親 brief の訂正 (段 3 の反証を親が独立実測して受理)

### R1. 「floor の実成果物 0 件」は**誤り**

実測 (親):

```
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t748-pilot-path/w2-evidence/bundle/
  output/env/pegasus/calibration/s8b-floor-pilot/
    20260812T072101Z-261cec1c/result.json  schema=s8b-floor-result/v2 mode=pilot sessions=120 binaries=12
    20260812T072934Z-261cec1c/result.json  schema=s8b-floor-result/v2 mode=pilot sessions=120 binaries=12
    20260812T064624Z-261cec1c/            (result.json なし)
```

- brief §0 の「0 件」は**現 worktree の `output/` だけを探索した結果**であり、探索範囲が狭かった。
- ただし**結論は変わらない**: 実在する 2 件は schema `v2` で、現行 main は既に `v3` を要求する
  (`s8b_floor_contract.py:31`)。v4 へ上げても**新たに壊れる実成果物は無い**。
  根拠を「0 件だから」から「実在 2 件は既に現行 v3 が拒否する legacy だから」へ差し替える。
- 記録義務: worklog へ「探索範囲を repo 内 `output/` に限った実測は不十分」と、この 2 件の実在を書く。

### R2. 「編集面に bytes pin 無し」は**誤り**

実測 (親):

- `output/s8b-freeze/holdout_freeze.json` の `/generator` =
  `{"path": "orchestrator/campaign/s8b_holdout_freeze.py",
    "sha256": "1910fff38edf0e58f5bff221c29660a8f85dd0ed1b5c980234ec1af098584e5f"}`
- 現行 bytes = `6ba57a5ae6b8892cdf77caeefdb5f265c21c3a4ed52c841d15200cda438b14bf` → **既に不一致**。
- `freeze_verification_hold.HELD = True` かつ `HELD_CHECK_IDS` に
  `s8b-holdout.generator-implementation-bytes` があるため、現在は赤にならない。
- brief の pin 閉包が見落とした理由: `grep` から `output/` を除外していた。
  **DW-O09 の pin 閉包は成果物側 (`output/`) も検索対象に含めなければならない** (F30 型の再発)。
- 裁定: 本 wave の `s8b_holdout_freeze.py` 編集は**新たな破壊ではない** (既に不一致)。
  hold の解除・世代移行は**ユーザー明示命令のみ**という既裁定に従い、本 wave では触らない。
  worklog へ「pin は実在し既に不一致・hold 下」と明記する。

## 1. 適用する既裁定

- **凍結 pin・承認署名・commit 束縛・台帳の原子性強化の類は、新設を既定で見送る**
  (2026-08-12 ユーザー裁定、`{{D:freeze-verification-hold}}` 系)。
  ただし**正しさゲート (verifier・admission・変異テスト) と規律 1〜3 は対象外＝不変**。
  → 本 wave の T-1155/T-1178 は admission ゲートの proof chain を閉じる作業であり実施する。
  → レンズ A 所見 1 の「署名付き oracle authority」と所見 3 の「外部 WORM registry」は
    **この裁定に直接該当するため実装しない**。裁定パッケージへ送る。
- 床値 campaign は現在 **pilot 固定・official は無条件拒否**
  (裁定 inbox `2026-08-16-t1140-t330-claim-identity-reruling.md`、`s8b_floor_campaign.py:342-352`)。
  → 成果物影響の記述で「official が現状到達不能」を隠さない。

## 2. 所見の裁定表

### レンズ A (正しさ防壁)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | SWO receipt は全 field が公開・決定的で、oracle 未実行でも手書きできる | **real** | **部分採用**。下記 §3-A |
| A2 | pure verifier に artifact 自身の receipt を expected として渡せる (自己申告の自己照合) | **real** | **採用**。§3-B |
| A3 | 台帳の削除→同一 bytes 再構成は unkeyed digest では検出不能 | **real** | **実装しない**。§1 の既裁定。保証外と明記し裁定パッケージへ |
| A4 | `s8b_holdout_freeze.py` の generator source pin を見落とし | **real** | **受理**。§0-R2 |
| A5 | 「実成果物 0 件」は探索範囲で覆る | **real** | **受理**。§0-R1 |
| A6 | standalone verifier は重複 binary cell を余分と認識しない | **real** | **採用**。§3-C |
| A7 | 空集合分岐の positive control 不足 | **real** | **採用**。§3-D |
| A8 | central exact-key gate を直接固定するテストがない | **real** | **採用**。§3-E |
| A9 | brief の grep が逐語では再現しない | **real (nit)** | **受理**。worklog へ正確な command を記録 |

### レンズ B (到達範囲)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B1 | `s8b_holdout_freeze.py` / `s8b_oracle_driver.py:930-964` が scope 外 | **real** | **採用**。U2 へ入れる |
| B2 | P1 の `receipt_sha256` は下流が検算できず保証が閉じていない | **real** | **採用 (再設計)**。§3-A |
| B3 | `compiler_version` は外部 compiler 出力の任意文字列 (最大 4096 bytes) で軸漏洩の迂回路 | **real** | **採用**。§3-A |
| B4 | central validator は top-level exact key を検査せず、portable/runtime helper 分離が要る | **real** | **採用**。§3-E |
| B5 | fixture 破損 10 箇所以上 | **real** | **受理**。U0 の共有 fixture へ集約 |
| B6 | 分割は U0→U1∥U2、U2 に oracle driver を足せ | **real** | **採用** |

## 3. プラン v2 の確定内容 (プランからの差分だけ)

### A. portable SWO receipt の再設計 (A1 / B2 / B3 を反映)

プラン §A-1 の射影を次へ変更する。

1. **identity 束縛を足す** (receipt 移植の拒否):
   `cell_id`、`holdout_id`、`configuration_id`、freeze の `entry_sha256`、`binary_sha256` を
   portable receipt の exact key に加え、`_validate_portable_built` が binary record 側の
   同名値と**完全一致**を要求する。これにより「別 comparator の PASS receipt を移植」は落ちる。
2. **`compiler_version` を raw で載せない**: `compiler_version_sha256`
   (raw 文字列 UTF-8 bytes の sha256) だけを載せる。raw 文字列は private evidence 側だけ。
   ratified の pointer 許可は `/binaries/*/sort_swo_oracle/*` の**固定 key 列挙**に限り、
   subtree 一括 allow は禁止する。
3. **`receipt_sha256` は残すが、保証境界を明記する**:
   これは private evidence への **commitment** であり、raw が到達可能な環境でだけ検算できる。
   到達不能環境では検算できない — この性質を docstring と worklog に明記する
   (既存 `s8b_floor_stats.py:409` の保証境界 docstring と同じ書式)。
4. **保証境界の明文化 (必須)**: 「この receipt は『床値 record がどの oracle 実行 receipt を
   主張しているか』の durable な辺であって、**oracle が実際に走ったことの証明ではない**」を
   docstring・worklog・insights に書く。書かずに land しない。

### B. 公開 verifier API の分離 (A2)

プラン §B-5 の「`expected_holdout_admission` を必須 keyword にする」だけでは不足。

- `verify_floor_artifact(...)` は **pure projection verifier** として残し、
  docstring に「live admission を保証しない」と明記する。
- **公開 consumer が呼ぶ入口を別関数にする**:
  `verify_floor_artifact_with_live_admission(artifact, expected_protocol, *, repo_root, ...)`
  が **自分で inspector を呼び**、`expected_holdout_admission` を caller から受け取らない。
  ratified closure / holdout freeze / report はこの入口だけを使う。
- positive control: 「artifact の `holdout_admission` を expected として自己投入」しても
  公開入口では拒否されること (そもそも渡せない署名であること) を meta test で固定する。

### C. binaries の cell 集合検査 (A6)

`verify_floor_artifact` は external `expected_cells` から canonical cell ID 集合を作り、
`set(binaries)` と**完全一致 + 件数一致**を要求する。`expected_binaries is None` でも発火させる。

### D. 縮退入力の positive control を 8 nodeid へ分解 (A7)

root 不在 / `claims/` 空 / main ledger 不在 / main ledger zero byte /
foreign campaign 行のみ / `cells=[]` / attempt ledger zero byte かつ消費期待 1 件 /
全 pre-probe competing で attempt 0 行を許す唯一の正例 — を**別 nodeid**にする。

### E. central exact-key gate (A8 / B4)

- `validate_portable_binary_record` の冒頭で configuration 条件付き exact key 集合を検査する。
- portable 用 `portable_built_keys_for(configuration_id)` と、
  runtime 用 `_runtime_built_keys_for(configuration_id, stored, fetchcontent)` を**分離**する。
- positive control: sort / non-sort の双方で `record["unexpected"]=...` を central validator 単体へ
  渡して拒否させる。

### F. scope 内に確定するプランの追加項目

- `_validate_binaries_cover_cells` (producer 側): **採用**。
  成果物影響 = 無いと空 binaries / cell 欠落の result が producer 自身を通り、
  下流の全検査が恒真化する。
- `enumerate_cells` の「各 holdout に `sort_best` がちょうど 1 件」gate: **採用**。
  成果物影響 = 無いと sort_best ゼロの freeze で A scope の receipt 検査が丸ごと恒真化する。
  実 freeze (rr20 / rr80 とも 6 configuration に `sort_best` を含む) を壊さないことを実測済み。
- `s8b_floor_stats.py:897-904` の後方互換 skip 削除: **採用**。成果物影響 = A6 と同じ。

### G. scope 外 → 裁定パッケージ (実装しない)

1. **oracle 実行の証明** (検証時 oracle 再実行 / 署名付き追記専用 oracle authority)。
   理由 = §1 の既裁定。本 wave は「束縛」までを主張し、「実行証明」は主張しない。
2. **台帳の削除→再構成攻撃への耐性** (外部 WORM / 別権限の署名付き monotonic registry)。
   理由 = §1 の既裁定 (「台帳の原子性強化」は名指しで見送り対象)。保証外と明記する。
3. `s8b_holdout_freeze.py` の generator pin と freeze hold の世代移行。
   理由 = hold 解除はユーザー明示命令のみ (既裁定)。

## 4. 変異事前登録 (DW-M01)

各変異は「同じ入力を拒否する層が前後に無い」ことを実装後に確認してから本走する。
本走は `--runner-mode dispatch`、runner argv に `--force-dispatch` を入れる (DW-M07)。

| # | 位置 | 変異 | 期待赤 (完全集合は fix 後に再導出) |
|---|---|---|---|
| M1 | `s8b_floor_campaign.py` built record 組立 | `prepared.oracle_attempt` を読まず receipt key を落とす | sort_best receipt の manifest/result 到達テスト |
| M2 | `s8b_sort_swo_receipt.py` 射影 | 絶対パス / raw `compiler_version` を射影に残す | 射影のホスト値排除テスト |
| M3 | 同上 | identity 束縛 (`cell_id` / `entry_sha256` / `binary_sha256`) を落とす | receipt 移植拒否テスト |
| M4 | `s8b_binary_admission.py` central validator | exact key 集合の呼出しを削除する | 余分 key 拒否テスト (sort / non-sort 両方) |
| M5 | 同上 | sort receipt を `.get()` の optional 扱いにする | sort_best 必須テスト |
| M6 | `s8b_floor_stats.py` binaries 節 | 「binaries と expected_binaries が共に無ければ成功」を戻す | 空 binaries 拒否テスト |
| M7 | 同上 | cell ID 集合の完全一致を pair set 比較へ戻す | 重複 binary cell 拒否テスト |
| M8 | admission inspector | `campaign_run_id` filter を除き共有 file 全体を hash | 他 campaign 追記の digest 不変テスト |
| M9 | 同上 | `claims/<digest>.claim` の内容照合を省く | claim 改竄拒否テスト |
| M10 | 同上 | 欠落 / zero-byte `ledger.jsonl` を空列として受理 | ledger 不在テスト + zero-byte テスト (別 nodeid) |
| M11 | 公開 verifier 入口 | 公開入口が `expected_holdout_admission` を caller から受け取る形へ戻す | 自己投入拒否の meta test |
| M12 | `s8b_ratified_freeze.py` | inspector 呼出しを削除、または unavailable を skip | ratified の unreachable 拒否テスト + report 伝播テスト |

**過剰拒否の正例 (受理集合を縮小する wave の義務)**:
正直な artifact + 完全な admission filesystem + sort_best receipt 一式で
`problems == []` かつ ratified reverify が緑になる end-to-end 正例を 1 本登録する。

## 5. 段 5 の実装単位 (確定)

- **U0 (契約 spine、逐次先行)**: `s8b_sort_swo_receipt.py` (新設)、`s8b_binary_admission.py`、
  `s8b_floor_contract.py`、`s8b_holdout_admission.py`、対応 unit test、
  共有 fixture `orchestrator/tests/s8b_floor_evidence_fixture.py` (新設)。
- **U1 (producer)**: `s8b_floor_campaign.py`、`test_s8b_floor_campaign.py`、
  `test_s8b_materialization.py`、`test_s8b_freeze_io.py`。
- **U2 (consumers)**: `s8b_floor_stats.py`、`s8b_ratified_freeze.py`、`s8b_holdout_freeze.py`、
  `s8b_oracle_driver.py` (conditional key 受理の互換検査のみ)、`s8b_v2_freeze_fixture.py`、
  ratified / stats / freeze / report の各 test。

U0 完了後に U1 と U2 を並列投入する (ファイル所有は素集合)。
`test_s8b_floor_campaign.py` は並行 wave `dev-wave-t1142-oracle-n-pilot` が所有するので、
U1 の起動直前に local main を再取り込みして衝突を確認する。

## 6. 成果物影響 (DW-G05)

- **A を実装しない**: certified 選択の根拠から「その comparator がどの oracle 実行 receipt を
  主張しているか」への durable な辺が無いまま床値が確定し、oracle 実行痕跡を差し替えても
  成果物の値・受理集合が変わらない。
- **B を実装しない**: 実測後に admission 台帳を消した run の `result.json` が
  verifier・ratified closure・report のすべてを通過し、一回性の主張が成果物側の証拠を持たない。
- **A1/A3 を実装しない (裁定済み)**: receipt は「主張の束縛」であって「oracle 実行の証明」ではなく、
  台帳の削除→再構成には耐えない。この 2 点は保証範囲外として明記する。書かなければ
  成果物が実際より強い保証を持つと読まれる。
