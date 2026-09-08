# 段 1 brief — [T-2401] 評価器例外の理由を fail-closed のまま構造化して残す

- **研究前進 (土台):** 8c 事前登録の発効判定は certified 選択・測定認可の入口 gate である。いま止めているのは「残る不充足条件をどの順で潰すか」の判断で、判定器が理由を捨てると切り分けができない。F631 では判定器 CLI が 12 条件すべてを `ERROR / evaluator-exception` に倒し、親が「12 条件すべて評価不能」とユーザーへ誤報告した。真因は `PreregistrationError("predicate-result-type")` で、それが構造化されて残っていれば 1 手で分かった。最小差分は「fail-closed の終端は 1 bit も変えず、捨てている例外理由だけを構造化して残す」。
- **完了判定:** 評価器が例外を送出する負例を人工的に作り、(a) `status` / `reason_code` / `effective` / CLI stdout が現行と完全一致し、(b) 例外型名と `PreregistrationError.reason` が構造化 reason として取得でき、(c) 人間が打つ CLI からその reason が読める、を実走で示す。
- **規律:** 規律 3 (正しさシグナルは pass/fail でなく「なぜ壊れたか」を構造化して返す) に直接効く。規律 2 は緩めない。

## scope (本題の実装だけ)

- 対象 file: `orchestrator/campaign/s8c_preregistration.py`。
- 一次対象 (F631 の実際の発火点): `_default_registry_results` の `except Exception` (l.1855)。`evaluator(commit, repo_root=root)` と `_normalize_predicate_results` の例外を捨て、12 件を一律 `ERROR/evaluator-exception` に倒す。
- 同型の候補 (段 2 で file:line 粒度に洗い出し、段 4 で採否を裁定する):
  - l.1895 `registry.evaluate_all` (test registry 経路、`registry-exception`)
  - l.1819 / l.1834 `_projection_module_identity` の import / read (`projection-import-error` / `projection-file-read-error`)
  - `_default_registry_module` の import 例外 (`evaluator-import-error`)
  - l.1885 付近 `except PreregistrationError: pass` (契約 parse。理由が完全に消える)
  - `orchestrator/campaign/s8c_preregistration_evidence.py` l.3464 の内側 per-predicate catch-all (`EVALUATOR_INTERNAL_ERROR`)
- **scope 外:** 新しい gate・検査・台帳・一般化の追加、reason code 語彙の拡張、他 module の広い except 一掃、`s8c_gate_report.py` の CLI 終端 (すでに `exc` を束縛して `_error_json` に出している)。

## 不変条件 (破ったら停止)

1. **受理集合を 1 bit も広げない。** 現行で `ERROR` に倒れるものは `ERROR` のまま、`reason_code` の文字列も現行のまま、`effective` の値も不変。通らなかったものは通らない。
2. **`ActivationReport` / `PredicateResult` / `EvidenceRef` の dataclass field を増減しない。** `_activation_report_digest` は `_jsonable(report)` の全 field から digest を作り、それが `EffectivePreregistration.report_digest_sha256` になり、`orchestrator/campaign/trial_registry.py` の台帳 field `activation_report_digest_sha256` として永続化・再照合されている。field を足すと過去に記録した試行の再導出が全件不一致になる (規律 7)。
3. **CLI `check --json` の stdout の形と bytes を変えない。** `orchestrator/tests/test_s8c_cli_entrypoints.py` が library report と突き合わせている。
4. **stderr に traceback 全文を出さない。** 同 test の `assert "Traceback" not in completed.stderr`。
5. **新規 file を足さない。** `campaign_lock.py` l.64/133、`test_artifact_admission.py` l.61/87、`test_t671_source_binding.py` l.52 が path 集合 pin を持つ (既存 file の編集は抵触しない)。テスト追加は既存 test file への追記を既定とし、新規 test file が要るなら段 4 で裁定する。
6. **自由文を `reason_code` へ入れない** (`s8c_preregistration_evidence.py` l.3464 の既存コメントの規律)。構造化 reason は reason_code とは別の場所に置く。
7. 例外理由に repo path・環境依存値をそのまま載せない (成果物の再現性と、揮発 payload の焼き込み禁止)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 構造化 reason の置き場所は「digest に入らない側 channel」とする。具体形 (返り値の第 2 要素 / 明示 out-parameter / 例外 chain の保持) は段 2 が起草し段 4 で確定する。module 大域変数と暗黙状態は不採用を既定とする。
- **(P2)** 人間への可視化先は CLI の **stderr** とする。stdout を変えないため。
- **(P3)** 診断の内容は「例外型名 + `PreregistrationError.reason` (あれば) + 発火した呼び出し点の識別子」の 3 項に限る。message 全文・traceback は載せない。
- **(P4)** 実装単位は 1 つ (同一 file 群、素集合に割れない)。並列分割しない。

## 成果物の形

- コード + テスト (`orchestrator/campaign/s8c_preregistration.py` と既存 test file への追記)。
- `output/insights/2026-09-08_t2401-evaluator-reason/` に brief・plan・敵対相談・裁定・レビュー・変異台帳の逐語。
- 段 7 で worklog / decisions / failures は `docs/spool/` の fragment として書く。F631 には「再発検知」の更新を追記する候補がある (段 8 で裁定)。

## 既存被覆の検索結果 (純増のみ)

- `docs/decisions.md` に本件を裁定済みの D は無い。D1363 は「条件 12 の証拠契約が例外の非握り潰しを証明しない」と限界を宣言する別件。D438 は「評価器の終端を一律に充足へ倒す」ことの却下で、本件は終端を変えないので抵触しない。
- module blob の literal sha256 pin は repo 内に無い (blob `4b835378` / sha256 `feddbbbe…` で全走査、hit 0 件)。
