# 段 1 実測 A — source binding 非対称 (Explore 子、read-only、2026-08-09)

主張 ([T-671]) は正確・反証なし。

## silo の binding

- ファイル集合: `orchestrator/campaign/silo_ladder_rung1.py:254-277` `_runtime_module_paths()`。
  `env_contract.py` :263、`env_contract_activation.py` :264。
- hash 集約: `runtime_modules_binding()` :280-287 (各 {path, sha256}、live working-tree bytes を
  `sha256_file()` :246-251)、`runtime_modules_sha256()` :290-294。
- 保存先: submit-receipt `bindings.runtime_modules_sha256` (:2416, :2438)、campaign-root (:2519)、
  submit document `binding.runtime_modules` (:4456、schema 検査 :1271, :1284-1297)。
- 検証: `verify-result` (:4817, :4838) → `validate_current_bindings()` :3517-3539、
  不一致で fail-closed (:3538-3539)。

## qualification の binding (silo と独立実装、共通 helper なし)

- パス集合: `orchestrator/qualification/contract.py:38-76` `REQUIRED_CODE_IDENTITY_PATHS`
  (:64-65 に同 2 module)。
- 束縛先: `series_identity()` の `preimage["code_identity"]` (contract.py:485, :528-530)。
- 検証: `qualification/identity.py:112-144` `verify_recorded_series_identity` —
  `git cat-file blob {commit}:{path}` の sha256 と exact 照合 (:137-144)。**git blob 照合**
  (silo は live bytes、機構が異なる)。

## 汎用 certified 経路 — いずれも loader source bytes を束縛しない

| 経路 | file:line | 束縛 identity | loader bytes hash |
|---|---|---|---|
| campaign loop COMMIT 認可 | `loop.py:61-89` → `execution_guard.py:107-170` | contract_sha256 (field 値 hash)、activation_serial / activation_state_sha256 (record JSON hash) | 含まない (`execution_guard.py:44-104` は :77-78 の state hash 照合と :96 の contract 照合のみ) |
| certified_writer_preflight | `certified_writer_preflight.py:85-126` `_verify_loaded_repo_modules` (sys.modules vs commit blob) | 起動時 import 済み repo module 全部 | 理論上含むが **floor/t126 の PBS 投入前 gate 限定** (`tools/pegasus/t126_qualification.sh:101`、`floor_campaign.sh:83`)。campaign loop へ未配線 |
| certified_writer_admission (floor/t126) | `certified_writer_admission.py:18, :370` | contract_sha256 のみ | 含まない |
| 材料レポート | `layer3_report.py` 全体 | WAL/whiteboard record の source_ref (genome hash) | 含まない (env_contract 参照ゼロ) |
| WAL | `wal.py:792-902` | `source_bytes_sha256` は genome source | 含まない |
| build admission | `build_admission.py` | generator/review receipt の provenance | 含まない (env_contract 未 import) |

## activation 参照の中身

- `_ACTIVATION_HEAD_SERIAL = 1` / `_ACTIVATION_HEAD_STATE_SHA256 = f78072…` (`env_contract.py:373-376`)。
- `_state_sha256()` の入力は activation record JSON 自身のみ (`env_contract_activation.py:130-133`)。
  loader の Python source は入らない。
- `validate_activation_records` (`env_contract_activation.py:332-422`) は record chain・registry
  一致・serial 連番・head pin — すべて data レベル。loader 改変の検査は存在しない。
- T-529 設計メモが既に明示: 「定数は record の hash であって env_contract.py 自身の hash ではない」
  (`output/insights/2026-08-08_t529-activation/s4-adjudication.md` §3)。

## 既存 source closure 機構とカバレッジ

silo runtime_modules / qualification REQUIRED_CODE_IDENTITY_PATHS / certified_writer_preflight /
`known_axes.source_closure` (`s1_known_axes_freeze.py:974-1054`、genome 生成器のみで env_contract 系は
対象外) / FROZEN_MANIFEST (テスト fixture) — **いずれも汎用 certified 経路を覆っていない**。

## 補足

g2 は未活性化 (`env_contract_activations/` は 00000001.json の serial 1 のみ)。
