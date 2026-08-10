must-fix は 0 件です。以下の 3 件を should-fix、1 件を nit と判定します。pytest は実行せず、HEAD 差分と既存ログを静的に監査しました。

## 所見

[severity: should-fix] [攻撃シナリオ] `str` の subclass が `__format__` を上書きすると、検査時の `text` には CR/LF がなくても、`f"{resolved}:{text}"` の構築時だけ CR/LF を出力できる。段 4 の「Git に渡す同じ値を検査」という保証を迂回する。既存 production consumer は JSON 由来または固定定数の通常 `str` なので、現行正常経路への実害は確認していない。  
[根拠 orchestrator/campaign/s8c_preregistration.py:963, orchestrator/campaign/s8c_preregistration.py:964, orchestrator/campaign/s8c_preregistration.py:968]  
[提案] `text = f"{path}"` で一度だけ最終表現を作って検査し、`spec = resolved + ":" + text` として再 format しない。`str` subclass の `__format__` 正負例も追加する。

[severity: should-fix] [攻撃シナリオ] 段 4 plan v2 は standalone の埋め込み CR、すなわち `alias-\r-target.txt` 相当を要求しているが、`embedded-cr` の実値は `"\r\n"` である。将来 guard が「末尾 CR と LF は拒否するが、埋め込み CR は通す」実装へ退行しても、末尾 CR テストと CRLF テストは双方通り得る。  
[根拠 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s4-adjudication.md:49, /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s4-adjudication.md:51, orchestrator/tests/test_s8c_preregistration_core.py:992, orchestrator/tests/test_s8c_preregistration_core.py:1000]  
[提案] `"\r"` 単独の埋め込み CR 正式 node を追加する。Git が standalone 埋め込み CR を alias しない場合は、別 blob alias の主張を無理に置かず「旧経路で正確に読めても policy として拒否する」テストに分離する。現状、plan v2 項目 2 は部分実装である。

[severity: should-fix] [攻撃シナリオ] 実 Git fixture は、CR/LF と `:` を含むファイルを実際に `git add -A` し、旧 Git の batch framing が別 blob を返すことまで acceptance assertion にしている。将来 Git がこの入力を安全に拒否した場合、production guard が正しく残っていても `_legacy_unframed_blob` の事前 assertion が偽赤になる。[推測] NTFS/Win32 系 filesystem または `core.protectNTFS=true` でも、controlled filename の index 登録前に落ちる可能性がある。  
[根拠 orchestrator/tests/test_s8c_preregistration_core.py:198, orchestrator/tests/test_s8c_preregistration_core.py:205, orchestrator/tests/test_s8c_preregistration_core.py:1000, orchestrator/tests/test_s8c_preregistration_core.py:1005, orchestrator/tests/test_s8c_preregistration_core.py:1010]  
[提案] guard の検出力テストと「現 Git で旧 alias が再現する」という characterization を分離する。後者は対応 Git/platform 契約を明示し、安全拒否へ変わった Git では説明付きにする。現在環境は Git 2.34.1、`core.autocrlf`・`core.protectNTFS` の明示設定なし、`/tmp` は XFS で、親実測では通っている。`core.autocrlf` はファイル名に作用せず、今回の blob 内容も LF のため問題を認めない。

[severity: nit] [攻撃シナリオ] 生 path は漏れていないが、`read_blob_at` の例外は `path-control-char` だけで、どの入力が拒否されたか追跡不能である。対して `blob-missing` と `path-not-blob` は commit と path を含む spec を出す。contract 側は required path なら安全な論理位置を出すが、consumer は全条件共通の `'consumer.path'`、registry 経由ではさらに `evidence-contract-invalid` へ畳まれる。複数契約を扱う運用では診断が痩せすぎている。  
[根拠 orchestrator/campaign/s8c_preregistration.py:965, orchestrator/campaign/s8c_preregistration.py:973, orchestrator/campaign/s8c_preregistration.py:976, orchestrator/campaign/s8c_preregistration_evidence.py:185, orchestrator/campaign/s8c_preregistration_evidence.py:252, orchestrator/campaign/s8c_preregistration_evidence.py:690]  
[提案] CR/LF を含まない安全な locator を付ける。contract は `Cxx.consumer.path`、直接 API は UTF-8 byte 長と短い SHA-256 fingerprint が適切である。生 path や実制御文字は引き続き出さない。

## consumer・波及監査

`read_blob_at` の production consumer は独立検索で次を確認した。

- `parse_preregistration_at` の固定 `SOURCE_PATH`。
- `_module_blob` 経由の固定 `CORE_MODULE_PATH` / `EVALUATOR_MODULE_PATH`。
- `_activation_report_at` の固定 `SOURCE_PATH`。
- `prepare_revision` の検査済み整数から作る `generation_path(...)`。
- `PredicateRegistry.evaluate_all` の固定 `EVIDENCE_CONTRACT_PATH`。
- `_ConditionProbe.read_kind` の契約由来 `required_evidence[*].path`。

根拠は `s8c_preregistration.py:990,1490,1558,1564,1715` と `s8c_preregistration_evidence.py:378,679`。現契約の path はすべて通常の ASCII relative path で、新拒否が既存正常値へ発火する箇所はない。

`_safe_path` の consumer は `load_contract_bytes` 内の required path と consumer path の 2 箇所だけである（`s8c_preregistration_evidence.py:225,252`）。`load_contract_bytes` は直接 API、`semantic_contract_sha256`、`PredicateRegistry.evaluate_all`、`get_registry().evaluate_all`、module-level `evaluate_all` から到達する（同:270,690,743）。

公開波及は次のとおり。

- preregistration CLI `check` → `activation_report_at`、`prepare-revision` → `prepare_revision`。
- `p3_autonomous_workload_trial` の manifest 経路 → `effective_at`（`p3_autonomous_workload_trial.py:2348`）。
- `trial_registry` の launch/accept → `require_effective_preregistration`、CLI `accept` → `effective_at`（`trial_registry.py:1223,2211,2484`）。
- `campaign.*` と `orchestrator.campaign.*` は同じ物理 source を読み、evidence module の relative/fallback import と core の二候補 import も残っている（`s8c_preregistration_evidence.py:18`, `s8c_preregistration.py:1503`）。
- `t080_freeze_migration.py` はこの 3 API の consumer ではない。固定 source repin 集合にも変更された 2 module は入っていない（`t080_freeze_migration.py:87-121`）。migration receipt・known-axes・holdout の受理集合は変わらない。

module bytes の変更により activation report の module hash と report digest は変わる。一方、freeze record が保護する契約 JSON/markdown は不変である。旧 commit を現在の live module で評価すると既存設計どおり `core-blob-mismatch` になり得るが、現 repo に既存 effective manifest／trial ledger の実 artifact は見つからず、壊れる正常登録経路は確認できなかった。

## テスト品質・受入コスト

追加 13 node は各 node 固有の `tmp_path` を使い、共有 module/global を変更しない。xdist の順序・worker 数依存は認めない。6 個の tmp repository、11 commit、静的には約 93 回の Git subprocess を追加するが、`REAL_REPO_SERIAL_NODES` には登録されず、重い `real-repo` group の直列和には載らない。

既定では `TMPDIR` は未設定で `/tmp` が使われ、controlled filename は wave repo の外に作られる。したがって親 repo の `git add`、`git status`、untracked/clean-tree gate には現れない。現在の HEAD も clean だった。[推測] 明示 `TMPDIR` を repo 配下へ向ければ既存の全 `tmp_path` テスト同様に clean-tree gate を壊し得るが、今回固有の経路ではない。

親実測は対象 3 ファイルで `167 passed in 49.98s` だが、ログ自身が「受入形でない」と明記している（`s5-targeted.log:1,9`）。変更前との隔離比較や `--durations` がないため、追加分だけの秒数は確定不能である。少なくとも 483 秒の real-repo critical chainへ直列加算される構造ではない。

テスト差分は core が `+91/-0`、predicates が `+85/-0`。既存 test body、期待値、assert、skip/xfail は一切変更・緩和・削除されていないため、項目 4 の must-fix はない。

## plan v2・変異表

- plan v2: 項目 1・3・4・5 は実装済み。ただし項目 1 に `str` subclass の残余、項目 2 に standalone 埋め込み CR の欠落がある。
- M01〜M06: core の末尾 CR、LF、reason、message、非 `str` テストに静的 detector がある。
- M07〜M12: required/consumer の埋め込み CR/LF、末尾 reason、message、registry 統合テストに detector がある。
- M13/M14: 通常 path の正例が過剰拒否を検出する。
- M01〜M14 に名指しされた変異の未被覆はない。ただしこれは静的帰属であり、変異本走の kill を主張するものではない。

## 総括

must-fix は 0、should-fix は 3、nit は 1。  
既存 consumer の通常 path、CLI、trial、migration に新拒否の誤爆は見つからなかった。  
主な残余は `str` subclass、standalone 埋め込み CR のテスト欠落、実 Git fixture の移植性である。  
既存テストの弱体化はなく、追加 node は tmp repo 内で real-repo 律速 group へ入らない。