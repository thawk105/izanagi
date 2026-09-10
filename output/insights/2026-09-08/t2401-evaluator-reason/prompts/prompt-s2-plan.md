単独段 dispatch: stage=plan; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/brief.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/brief.md` — 親の段 1 brief (scope・不変条件・provisional 裁定)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py` — 一次対象
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration_evidence.py` — 内側の評価器 (reason code 語彙と既存の except 規律)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_gate_report.py` — 判定を再利用する consumer
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py` — CLI と library の等価性を固定する既存 test
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py` — core の既存 test
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_predicates.py` — predicate の既存 test
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_invariant.py` — 不変条件の既存 test

上記以外の repository 内 file は、上の file から辿って必要と判明した場合だけ読んでよい。
repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない。

## この段の仕事

段 2 のプラン起草である。**実装はしない。file を書き換えない。commit しない。** 出力は最終メッセージ本文にすべて書く (file へ書けない sandbox である。省略記号で途中を切らない)。

sandbox は read-only で書込み可能な tmp が無いため、**pytest の実走は要求しない。静的検査でよい。**実走は親が行う。実走していない結果を「緑」と書かない。

`file:line` 粒度で、次を含む実装プランを起草せよ。

1. **現行挙動の逐語的な確定。** 対象の各 `except` について、(a) 捕捉する例外の実際の集合、(b) 現在返す `status` と `reason_code`、(c) その結果 `effective` がどうなるか、を行番号つきで書く。
2. **どこで理由が消えているかの列挙。** brief の「同型の候補」を file:line で確定し、各々について「例外理由が消えるか、既に別 reason_code へ写っているか」を判定する。既に写っているものは対象外だと明記する。
3. **構造化 reason の設計。** brief の (P1)(P3) を出発点に、具体形を 1 つ推奨し、代替を 1〜2 つ挙げて却下理由を書く。次を必ず満たすこと。
   - `ActivationReport` / `PredicateResult` / `EvidenceRef` の dataclass field を増減しない (`_activation_report_digest` が全 field から digest を作り、それが `trial_registry` の台帳へ永続化されているため)。
   - `activation_report_at` の既存呼び出し側 (`s8c_gate_report.py`、`trial_registry.py`) の呼び出し規約を壊さない。壊すなら全呼び出し点を列挙する。
   - 受理集合を広げない。現行 `ERROR` は `ERROR` のまま、`reason_code` 文字列も不変。
   - 自由文を `reason_code` へ入れない。診断は別の場所に置く。
   - module 大域の可変状態・暗黙 state を使わない (使うなら理由と thread 安全性を書く)。
4. **CLI への可視化。** `check` サブコマンドで、診断を **stderr** へ出す形を file:line で書く。stdout の bytes と JSON の形は 1 bit も変えない。traceback 全文を出さない。`--json` 指定時と非指定時の双方で挙動を書く。
5. **テスト計画。** 追記先の既存 test file と、各テストが固定する命題を書く。次の 2 種を必ず含める。
   - **負例:** 評価器が例外を送出する状況を実際に作り、`status` / `reason_code` / `effective` / stdout が現行と完全一致することを固定する (受理集合を広げていない証拠)。
   - **正例:** 同じ状況で、構造化 reason に例外型名と `PreregistrationError.reason` が現れることを固定する。**依存先を stub せず、実体を名指しする。**
   新規 test file は既定で作らない (path 集合 pin があるため)。どうしても要るなら理由を書き、親の裁定に回す。
6. **波及の静的列挙。** 変更する関数の呼び出し側、共有 fixture、consumer test を repository 内から grep で洗い出して列挙する。
7. **変異事前登録の候補。** この変更を無効化しうる変異を 3〜6 件、`file:line` と変異内容で挙げ、どのテストが殺すかを書く。

## 禁止

- 実装・編集・commit・push。
- 新しい gate・検査・台帳・一般化の追加提案 (親 brief の scope 外。思いついたら「scope 外の所見」節に分けて書き、プラン本体へ混ぜない)。
- reason code 語彙 (`ReasonCode` enum、`REASON_CODES`) の拡張。
- 既存テストの期待値の変更・反転・緩和・skip・削除の提案。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。

- `## 現行挙動`
- `## 理由が消える箇所`
- `## 設計 (推奨と却下)`
- `## file:line プラン`
- `## テスト計画`
- `## 波及`
- `## 変異事前登録候補`
- `## scope 外の所見`
- `## 総括`

予算が尽きそうなら、その時点の途中結論をこの出力形式どおりに書いて終われ。無出力が最悪である。
