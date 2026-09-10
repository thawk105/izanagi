# 段 4 裁定 — plan v2 と実装契約 (段 5 の両実装子が共有する唯一の正本)

親が段 2 プラン + 敵対レンズ 2 本 (sol / luna) を裁定した結果。
**この文書が schema/API 契約の正本であり、段 5 の実装子 A/B は逸脱してはならない。**

## 0. 裁定の要旨

- ユーザー裁定 4 件 ([T-798] 統合案 / [T-799] (a) / [T-820] (a) / [T-821] (a)) は不変。
- 親の provisional (P5) は **「phase を権威にしない」原則だけ採用し、事実集合を強化して採る**。
  両レンズが独立に「P5 単独では不十分」と判定した (LUNA-P5-01 / A-01)。**phase の代わりに
  fold commit の identity (author・message・親との diff の path/status/mode/blob OID) を権威にする。**
- 親 brief の一般化 3 件は**縮小する** (下記 §6)。

## 1. 所見の裁定表

| 所見 | 判定 | 採否 | 対応 |
|---|---|---|---|
| LUNA-P5-01 `applied`+fold child が finalize へ到達しない | real | **採用** | recovery は phase repair (`mark_fold_committed`) → verify → finalize の順で進む |
| LUNA-P5-02 / A-01 phase は commit の身元を証明しない・手動 commit を受理 | real | **採用 (最重要)** | **commit identity gate** を新設 (§3.4) |
| A-02 trusted cutoff / audited closure が未束縛 | real | **採用** | origin へ `trusted_main_cutoff` と `audited_digest` を足し transaction_id に含める |
| A-03 `kind="land"` は申告値 | real (語の問題) | **採用 (縮小)** | `kind` を capability と呼ばない。実効 gate は commit identity。auto-recovery は `kind=land` に限定 |
| A-04 closure が rendering engine の bytes を束縛しない | real | **採用** | closure に `tools/spool_fold.py` と `tools/check_docs.py` の bytes を足す |
| A-05 legacy receipt が時期不問で受理される | real | **採用** | **位置的 cutover**: v2 record が 1 つ現れたら、それ以降の record は全て v2 exact でなければ拒否 |
| A-06 receipt の OID が durable に再検証されない | real | **部分採用** | 書込み時に実 object/ref を観測して検査。読取り時は形式のみ。**「durable 再検証」とは書かない** |
| A-07 一般 `check_docs` が complete active state を健康形として受理 | real | **採用** | active state の受理には**明示宣言が必要**。`check_docs.py --expect-active-transaction <id>` を land だけが渡す。既定は従来どおり拒否 |
| A-08 wave identity の adoption が広い | real | **採用** | auto-recovery は `kind=land` かつ `origin.wave_ref` == 現 wave_ref かつ `origin.tested_tip` == request tested_tip のときだけ |
| A-09 GC の parent directory を fsync していない | real | **採用** | GC unlink 後に全 parent directory を fsync してから次相へ進む |
| A-10 / LUNA-FIN-04 finalize 失敗が journal 無し rollback へ流れる | real | **採用** | finalize を fallible な `try` の**外**へ出す。finalize 失敗は rollback を起動せず専用 rc |
| A-11 dangling symlink state で `_discover` だけ fail-open | 疑い→real | **採用** | `_discover` の判定を `exists() or is_symlink()` にし専用 test |
| LUNA-RB-03 rollback 途中失敗の committed state | real (一部既存) | **部分採用** | rollback の state unlink に dir fsync を足す。残骸の自動復旧は [T-800]/[T-801] scope → 裁定パッケージ |
| LUNA-RACE-05 standalone と land の二重 writer | real (既存) | **部分採用** | rollback が unlink してよい state を **transaction_id 一致**に限定。直列化本体は裁定パッケージ |
| LUNA-CLOSURE-07 resume 正規化の抜け道 | real | **部分採用** | resume でも `_git_clean_preflight` を通す (前 wave が実測した非対称の解消)。byte 同一の外部巻き戻しは content では判別不能 = 限界として明記 |
| LUNA-LIFE-06 standalone state が次 wave を詰まらせる | real | **採用 (理由語)** | 拒否理由語に state path と取るべき手順を書く ([T-798] の主目的)。lock-aware finalize command は裁定パッケージ |
| LUNA-VERIFY-08 finalize が verifier 層を飛び越えうる | 疑い→real | **採用** | commit identity gate を `finalize_fold` の契約に必須で入れる |
| LUNA-REF-09 git ref の fsync | real (電断) | **不採用** | git 側の durability。裁定パッケージ |
| LUNA-V1-10 v1 state 復旧不能 | real (意図) | **仕様どおり** | 裁定「厳格側を既定」の帰結。限界として worklog に明記 (Q2-b は未裁定) |
| LUNA-TEST-11 / A の恒真指摘 | 採用 | **採用** | テストは**独立に観測した git 値**と比較する。渡した object の伝播確認だけにしない。helper の前後で phase を assert |

## 2. 裁定パッケージへ回す (本 wave では実装しない)

1. standalone 由来 state を安全に finalize / inspect する lock-aware command ([T-799](b) の同伴条件)。
2. standalone と land の直列化 (standalone が land lock を取らない)。
3. git ref の fsync / 電断時の ref 巻き戻り (LUNA-REF-09)。
4. rollback 途中失敗残骸の自動復旧 ([T-800]/[T-801])。
5. FOLDED receipt の OID を台帳読取り時に repo と突き合わせる durable 再検証 (A-06)。
6. 旧 v1 in-flight state の扱い (裁定パッケージ Q2-b、**未裁定のまま**)。

## 3. 実装契約 (段 5 の A/B が共有)

### 3.1 `FoldOrigin` (exact field 集合)

```python
@dataclasses.dataclass(frozen=True)
class FoldOrigin:
    kind: str              # "land" | "standalone"
    base: str              # land = lock 内 locked_main / standalone = plan repo HEAD
    tested_tip: str        # land = tested wave tip / standalone = plan repo HEAD
    wave_ref: str          # full symbolic ref (refs/heads/...)
    rollback_ref: str      # land = locked_main / standalone = HEAD
    trusted_main_cutoff: str   # land = tested_main / standalone = base   (A-02)
    audited_digest: str        # 順序保存の audited commit 列の sha256 / standalone = 空列の sha256 (A-02)
```

`plan_fold` は束縛前に git で照合する: `tested_tip` == plan repo の HEAD、`wave_ref` == plan repo の
symbolic HEAD かつ ref SHA == `tested_tip`、`base` / `rollback_ref` / `trusted_main_cutoff` が実在 commit。
不一致は `SpoolValidationError`。**`kind` は申告値であり capability ではない** (A-03)。

### 3.2 入力 closure (A-04 反映)

```python
{
  "files": {"<repo 相対 POSIX path>": "<sha256(raw bytes)>", ...},
  "worklog_rotate_bytes": <正の int>,
}
```

`files` の全集合 = `docs/worklog.md`, `docs/decisions.md`, `docs/failures.md`, `docs/phase3.md`,
`docs/archive/README.md`, plan 時点の全 `docs/archive/worklog-*.md`, `docs/spool/FOLDED.md`,
plan 時点の全 fragment, **`tools/spool_fold.py`**, **`tools/check_docs.py`**。

resume 時の正規化 (段 2 プランの 5 規則を踏襲):
transaction 所有 target は `before_sha256` を使う / GC 済み fragment は「全 target after」のときだけ
state の `content_sha256` で代用 / `rotation_path` は入力集合から除外 / それ以外は現 bytes /
第三状態は closure 計算前に拒否。

**resume でも `_git_clean_preflight` を通す** (LUNA-CLOSURE-07)。

### 3.3 transaction state (version 2)

top-level exact set = `{version, phase, transaction_id, origin, input_closure_sha256, fold_date,
fragments, gc_paths, projected_worklog_bytes, rotation_path, targets}`。
型 coercion (`str(...)`, `int(...)`, `bool(...)`) は全廃し exact 型で検査する。

`transaction_id` の payload = `fold_date`, `origin` (全 7 field), `input_closure_sha256`,
`fragments`, `gc_paths`, `projected_worklog_bytes`, `rotation_path`,
`targets` (`path`/`before_exists`/`before_sha256`/`after_sha256`)。
**`version`・`phase`・`transaction_id` 自身・`after_bytes_b64` は除外**する
(phase 書換えで ID が変わらないため)。

phase 遷移: `absent → applied` (apply 前に write) → `committed` (land が commit 成功後) →
`absent` (land が postcondition 全通過後)。`committed → applied` は禁止。

### 3.4 commit identity gate (新設、A-01 / LUNA-P5-02 の実効 gate)

fold commit `C` を受理する条件 (**すべて**満たすこと):

1. `C^` が 1 つだけ存在し `C^ == origin.tested_tip`。
2. `C` の author identity == `FOLD_AUTHOR_IDENTITY`。
3. `C` の commit message の bytes == `FOLD_COMMIT_MESSAGE`。
4. `git diff-tree -r C^ C` の記録集合が、state から導いた期待集合と**完全一致**する:
   - 各 target: status `M` (before_exists) または `A` (not before_exists)、mode `100644`、
     new blob OID == `git hash-object` の after_bytes の OID。
   - 各 gc_path: status `D`。
   - それ以外の path が 1 件でもあれば拒否。
5. `verify_declared_fold_commit` が受理する (既存の path 形状検査は残す)。

この gate は `mark_fold_committed` と `finalize_fold` の両方、および land の recovery 分岐で使う。

### 3.5 land の recovery 分岐 (受理する形はこの 2 つだけ)

**前提 (両形共通、1 つでも欠けたら `RC_FOLD_RECOVERY_FAILED`):**
`origin.kind == "land"` / `origin.wave_ref` == 現 wave_ref / `origin.tested_tip` == request tested_tip /
transaction_id 再計算一致 / closure 一致 / 全 target が after / 全 gc_path が不在。

| 形 | 追加条件 | 行うこと |
|---|---|---|
| A | main HEAD == `origin.tested_tip` | `apply_fold` で収束 → commit → `mark_fold_committed` → postcondition → verify → finalize |
| B | main HEAD が §3.4 を満たす fold commit `C` | **再 apply も再 commit もしない。** phase が `applied` なら `mark_fold_committed` で修復 → postcondition → verify → finalize |

`origin.kind == "standalone"` の state は auto-recovery しない。
理由語に **state の絶対 path と「lock-aware finalize command が未実装であること」**を書く (A-08 / LUNA-LIFE-06)。

### 3.6 その他の確定事項

- `finalize_fold` は `_fold_main_locked` の fallible な `try` の**外**で呼ぶ。失敗は rollback を
  起動せず、専用の postcondition failure として返す (A-10 / LUNA-FIN-04)。
- GC unlink 後、**全 GC parent directory を fsync** してから commit 相へ進む (A-09)。
- `_rollback_fold` の state unlink は (i) parent directory を fsync し、(ii) **state の
  transaction_id が rollback 対象 plan と一致するときだけ**行う (LUNA-RB-03 / LUNA-RACE-05)。
- `_discover` の state 判定は `exists() or is_symlink()` (A-11)。
- `validate_spool_tree` は既定で active state を拒否する。land だけが
  `check_docs.py --expect-active-transaction <transaction_id>` を渡し、
  **その ID と完全一致する active state のみ**受理する (A-07)。
- `_receipt_records`: 旧 5-field exact / 新 8-field exact の 2 集合のみ受理し、
  **v2 record が 1 つ現れたら以降は v2 exact 必須** (位置的 cutover、A-05)。
- `_load_rotate_limit` の `except Exception` → `except BaseException` ([T-820])。

## 4. 変異事前登録 (DW-M01、実装前に確定)

**「wave 前の実コードの形」を必ず含める** (ユーザー明示指示)。M01/M04/M05/M07 がそれに当たる。

| ID | 変異 (old 逐語 → new) | 単一理由性の確認 | 期待 |
|---|---|---|---|
| M01 | `apply_fold` 末尾へ **wave 前の実コードの形** `state_path.unlink()` を復活 | 前後に同じ入力を拒否する層が無いこと (finalize が唯一の削除者) | KILLED |
| M02 | `_plan_transaction_id` payload から `"input_closure_sha256"` 行を落とす | closure 検査は ID と独立に走るので理由が 2 つにならないか要確認 → 落ちるのは ID 束縛 test のみ | KILLED |
| M03 | resume の `apply_head`/HEAD 照合を `if False` へ | — | KILLED |
| M04 | `_load_rotate_limit` の `except BaseException` を **wave 前の形** `except Exception` へ戻す | SystemExit を投げる fixture は 1 経路のみ | KILLED |
| M05 | `_receipt_records` の必須集合を **wave 前の形** (5 field のみ) へ戻す | 位置的 cutover 検査が先に発火しないか要確認 | KILLED |
| M06 | `_discover` の受理条件から「全 gc_path 不在」を落とす (受理集合の拡大) | — | KILLED |
| M07 | commit identity gate の diff 集合比較を **wave 前の形** (比較なし = `verify_declared_fold_commit` のみ) へ戻す | A-01 の手動 commit fixture が唯一の理由 | KILLED |
| M08 | `validate_spool_tree` の `--expect-active-transaction` 照合を恒真化 | — | KILLED |
| M09 (正例) | 変異なしの正常 land 1 回 (受理すべき形を拒否していないこと) | 過剰拒否の検出 | 正例テストとして登録 |

`expected_nodes` は fix 後の最終 commit で完全集合を再導出する (DW-M07/M08、memory の実測)。

## 5. 段 5 の所有分割

| worker | 排他的所有 |
|---|---|
| A | `tools/spool_fold.py`、`tools/check_docs.py`、`orchestrator/tests/test_spool_fold.py`、`orchestrator/tests/test_check_docs.py` |
| B | `tools/dev_wave_land.py`、`orchestrator/tests/test_dev_wave_land.py` |
| 親 | docs (実装子は docs を触らない)、commit、変異、受入 |

共有 interface (§3.1〜§3.4) は本文書が正本。A が先行して `FoldOrigin` / `plan_fold(origin=)` /
`mark_fold_committed` / `finalize_fold` / commit identity gate を実装し、
B はその signature をこの文書どおりに前提してよい (実体は統合時に照合)。

## 6. 親 brief の一般化の縮小 (両レンズが独立に指摘、採用)

1. 「post-commit crash の残骸は**完全に健全**」→ **「測った fixture では commit と tree が durable かつ
   clean だった。ただし形の検証 (`verify_declared_fold_commit` を含む postcondition) は
   1 つも走っていないので、certified に健全とは言えない。」**
2. 「**現行の窓は commit で閉じている**」→ **「測った 1 注入点 (fold commit の ref 更新直後) では
   残骸が durable だった、という存在証明である。」** 他相・電断・rotation・mode は未測定。
3. 「実 checker は archive 跨ぎ T 重複を**止めない**」→ **「測った 1 形 (末尾へ archive 専有 ID の
   新規項を 1 行) では rc=0 だった、という存在証明である。」** D/F・見送り台帳・別配置は未測定。
