単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling.md` — **段 6 裁定 (この段の正本)。fix の scope と追加変異はここが確定版である。**
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md` — 段 4 裁定 (設計 v2・不変条件 1〜7。**不変**)
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-revA.md` — 段 6 レビュー A
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-revB.md` — 段 6 レビュー B
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py`

repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない・書かない。実装済みの差分は commit `134e5926d` である。

## この段の仕事

段 6 裁定の「fix の scope」1〜3 を**そのまま**実装する。**それ以外を実装しない。**

### 編集してよい file (これ以外を 1 byte も変更しない)

- `orchestrator/campaign/s8c_preregistration.py`
- `orchestrator/tests/test_s8c_cli_entrypoints.py`
- `orchestrator/tests/test_s8c_preregistration_core.py`

**新規 file を作らない。docs を編集しない。`git add` / `git commit` / push をしない。** 統合と commit は親が行う。

### 実装 (裁定「fix の scope」)

1. **sentinel を受理正規表現に一致しない値へ変える。** 現在の
   `_DIAGNOSTIC_EXCEPTION_TYPE_SENTINEL` と `_DIAGNOSTIC_PREREGISTRATION_REASON_SENTINEL` は、
   それぞれの受理正規表現に一致してしまうため、外部由来の値が sentinel を偽装できる。
   受理正規表現に一致しない文字 (例: `<` と `>`) を含む値へ変える。**受理正規表現そのものは変えない。**
   sentinel は診断専用であり `reason_code` 語彙ではない。
2. **CLI の診断出力が終了値を変えないようにする。** 現在、診断の `json.dumps` と
   `print(..., file=sys.stderr)` は外側の `except PreregistrationError` の内側にあるため、
   stderr の閉鎖・broken pipe・容量不足による `OSError` が未処理例外になる。
   **変更前なら定義済みの値を返した評価が、診断の追加で未処理例外に変わってはならない** (不変条件 7)。
   診断出力全体を `except Exception` で囲み、出力に失敗しても **stdout と終了値を現行のまま**返す。
   握り潰しの理由を 1 行コメントで書く。
3. **テストを足す。** 裁定「fix の scope」3 の 7 項目をすべて実装する。
   - evaluator が `ValueError` を直送する負例 (12 件の exact fallback と診断 3 field)。
   - 遅延 iterable が materialize 中に `TypeError` を出す負例 (同上、callsite は normalize 側)。
     この 2 件は、`except Exception` を `except RuntimeError` へ狭める変異を殺すためのものである。
     **`RuntimeError` の subclass でない例外**を使うこと (`PreregistrationError` は `RuntimeError` の subclass である)。
   - **live evaluator が `RuntimeError` を直送する実 process CLI 負例。**
     既存の実 process CLI fixture と同じ構成 (一時 repo 自身を実行・import root にする) で、
     evaluator を「直接 `RuntimeError` を送出する版」に差し替えた repo を作る。
     stdout bytes が現行と完全一致すること、stderr が evaluator 側 callsite の
     exact な診断 1 行であることを固定する。
   - 128 文字ちょうどの reason と type 名が**そのまま受理される** assertion、
     129 文字が sentinel になる assertion。
   - `_` を含む reason が sentinel になる assertion (受理 charset に `_` を足す変異を殺す)。
   - stderr の `write` が `OSError` を出す状況で `main()` が現行の終了値を返し、
     stdout が不変である assertion。
   - 両 sentinel がそれぞれの受理正規表現に**一致しない**ことを直接固定する assertion。

### 変えてはならないもの

- 段 4 裁定の不変条件 1〜7 (受理集合、dataclass field、CLI stdout の形と bytes、
  stderr の危険 payload 非包含、新規 file 無し、`ReasonCode` / `REASON_CODES` 非拡張、
  fail-closed 終端)。
- `except Exception` の**捕捉集合**。狭めても広げてもいけない。
- **既存テストの期待値。** 反転・緩和・skip・削除を禁じる。赤になったら実装側が誤りである。
  期待値の方が誤りだと判断したら、実装を変えず**報告して止まれ**。
- `activation_report_at` / `_activation_report_at` / `_activation_report_at_for_test` /
  `effective_at` / `require_effective_preregistration` の signature と返り値。

fixture へ現行 hash を差し込んでテストを甘くしない。期待値へ揮発 payload
(temporary path、時刻、working tree hash) を焼き込まない。機構の正例・負例は実体を名指しし、
`_default_registry_results` / `_normalize_predicate_results` / 診断 helper / sibling API を stub しない。

### テストの走らせ方 (この sandbox の実測済み制約)

- `tools/run_tests.py` は使わない (dispatch preflight で rc=16 になる)。
- `python3 -m pytest` は使わない (guard が拒否する)。
- 走らせられるのは **`PYTHONPATH=. python3 orchestrator/tests/<file>.py`** の自走 harness だけである。
- 実走した nodeid と結果を報告に書く。**子の実走は親の全走を代替しない。**
  実走できなかったものは「緑」と書かず「実装済み・未実走」と書く。

## 禁止

- 上記 3 file 以外の変更、新規 file の作成、docs 編集、`git add` / `git commit` / push。
- 裁定の「scope 外」に挙げた変更 (既存 CLI 終端の `str(exc)` 出力、reason 語彙を閉じる変更、
  gate・検査・台帳・一般化の追加)。
- 既存テストの期待値の変更・反転・緩和・skip・削除。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。

- `## 実装した差分` — file:line で何をどう変えたか
- `## 追加したテスト` — 各テストが固定する命題と、裁定「fix の scope」3 の 7 項目との対応表
- `## 実走した nodeid と結果` — 自走 harness の実走範囲と結果。未実走はそう書く
- `## 受理・拒否の含意` — 受理側と拒否側を 2 文に分け、通る正例を 1 つ添える
- `## 不変条件の自己検査` — 段 4 裁定の不変条件 1〜7 について満たした根拠を 1 行ずつ
- `## 未了・懸念`
- `## 総括`

予算が尽きそうなら、その時点の実装状態をこの出力形式どおりに書いて終われ。無出力が最悪である。
