単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s4-ruling.md`
  — 親の段 4 裁定。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s5-impl-diff.txt`
  — 実装子が作った差分の全文。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s5-impl-out.md`
  — 実装子の完了報告。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py`
  — 変更後の production。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py`
  — 変更後の test。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_condition_meaning_gate.py`
  — gate 側の既存 test (**変更されていないことの確認にも使う**)。読めなければ即停止。

## 依頼 — レンズ D: 波及・実行環境・テストの費用

**敵対レビュー**である。実装を守らず攻撃せよ。実装・修正はするな。書込み可能な tmp が無いので
pytest 緑は要求しない。静的検査で足りる。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

1. **consumer の取り残し。** 変更した識別子・fixture (`_condition_gate_receipts`、`_good_s6`、
   `_good_stages`、`_condition_gate_receipt_summary`、`condition_gates`) を**参照関係で**引き、
   波及先を全列挙せよ。名前の推測をするな。新しい `comparison` field で赤になる既存 assert が
   無いかを行番号つきで示せ。
2. **実行環境の前提。** 新 test は C++ compiler / cmake / fixture の copy / 実 preprocess を
   必要とするか。必要なら、それらが無い環境で **skip でなく赤**になる形になっていないか。
   逆に、無条件 skip で恒真緑になっていないか。既存 `_condition_gate_family` の
   `assert cxx is not None` と同じ扱いか。
3. **テストの所要。** 新 test が実 preprocess を何回起動するか数え、既存の同型 test
   (`test_condition_meaning_gate.py` の root-location-only 系、`test_t316_sandbox_probe.py` の
   condition-gate 系) の所要から所要を見積もれ。`lru_cache` などで重複起動を避けているか。
   **この repo は「開発するほどテストが遅くなる構造を作らない」を規律にしている。**
   秒単位で不必要に増えるなら所見にせよ。
4. **決定性。** 新 test が `tmp_path`、環境変数、file system 順序、compiler 版に依存して
   flaky にならないか。`lru_cache` を `tmp_path` 依存の値へ掛けて session 間で汚染しないか。
5. **monkeypatch の後始末。** 交叉負例が `require_condition_gate_family` を差し替えるなら、
   その差し替えが当該 test の外へ漏れないか (pytest の monkeypatch fixture 経由か、手書きの
   setattr で復元漏れがないか) を確かめよ。
6. **触ってはいけない file が触られていないか。** 差分に gate 本体・policy・hooks・
   受入所要台帳・docs・`test_condition_meaning_gate.py` が含まれていないか。
7. **受入所要台帳。** 新規 nodeid を列挙せよ (parametrize の id を含む完全な形で)。
   親が受入後に `tools/update_acceptance_duration_ledger.py --add-only` で足す。

## 禁止

- 実装・修正・commit・git 操作・ファイル書き換えをしない。
- 新しい gate・検査・台帳・互換層・一般化を提案しない。
- scope 外の real 所見は「裁定パッケージ候補」と明記して返す。

## 出力形式

```
## 所見
（所見 ID / must-fix か nit か / 対象 file:line / なぜ壊れるか）
（must-fix には「放置すると成果物の値・受理集合・参照がどう変わるか」を 1 行で必ず書く。
  書けないものは nit にせよ）

## 波及一覧
（参照関係で引いた consumer と、通るか落ちるか）

## 新規 nodeid の完全列挙

## 所要の見積り
（新 test が増やす秒数と根拠）

## 裁定パッケージ候補

## 総括
（3〜6 行。GO / NO-GO を明示する）
```
