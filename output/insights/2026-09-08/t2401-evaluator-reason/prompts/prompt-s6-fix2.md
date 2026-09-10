単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling2.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling2.md` — **段 6 裁定 2 巡目 (この段の正本)。fix scope はここが確定版である。**
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling.md` — 段 6 裁定 1 巡目
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md` — 段 4 裁定 (設計 v2・不変条件 1〜7。**不変**)
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-focus.md` — 焦点再レビューの所見と生存変異 S7〜S15
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py`

repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない・書かない。現在の tip は commit `8789ea89a`。

## この段の仕事

段 6 裁定 2 巡目の「fix の scope」1〜5 を**そのまま**実装する。**それ以外を実装しない。**

**これは原則としてテストだけの fix である。** production コードの挙動を変えてはならない。
唯一の例外は、scope 1 が要求する「`_DIAGNOSTIC_TEXT_MAX_LENGTH == 128` を直接固定する assertion」を
テスト側から書くことであり、production 側の定数と検査ロジックは 1 byte も変えない。

### 編集してよい file (これ以外を 1 byte も変更しない)

- `orchestrator/tests/test_s8c_cli_entrypoints.py`
- `orchestrator/tests/test_s8c_preregistration_core.py`

**`orchestrator/campaign/s8c_preregistration.py` を変更しない。新規 file を作らない。docs を編集しない。`git add` / `git commit` / push をしない。**

### 実装 (裁定「fix の scope」1〜5)

1. **境界テストを literal 化する。** 現在の 128 / 129 文字の入力は production 定数
   `_DIAGNOSTIC_TEXT_MAX_LENGTH` から生成されており、定数を 127 や 129 に変える変異が
   緑のまま通る (派生値の pin は生成器の検査にならない)。入力長を **literal の 128 と 129** で書き、
   さらに `_DIAGNOSTIC_TEXT_MAX_LENGTH == 128` を直接固定する assertion を足す。
2. **4 つの catch 地点の負例を、構造的に無関係な例外型で parametrize する。**
   既に試している型に**加えて 1 つ以上**を足すこと。対象は
   production evaluator 側 / production normalize 側 / test-registry evaluator 側 /
   test-registry normalize 側 の 4 箇所。
   **`PreregistrationError` は `RuntimeError` の subclass である。**「無関係な型」として
   `RuntimeError` の subclass を選んではならない。
   各負例は、12 件の exact fallback (status / reason_code / evidence / effective) と
   診断 3 field の両方を固定すること。
3. **診断 helper の 2 つの `except BaseException` に、`SystemExit` 以外の `BaseException`
   (例: `KeyboardInterrupt`) を送出する負例を足す。** 現在は `SystemExit` しか試していないため、
   guard を `except SystemExit` へ狭める変異が生存する。
4. **CLI 診断出力の guard に、`OSError` 以外の例外を `write` が送出する負例を足す。**
   現在は `OSError` しか試していないため、guard を `except OSError` へ狭める変異が生存する。
   この負例でも `main()` が現行の終了値を返し stdout が不変であることを固定する。
5. **既存の実 process CLI 負例を例外型で parametrize する。** live evaluator が
   `RuntimeError` を直送する現行 fixture に加えて、**`ValueError` を直送する場合**も通し、
   stdout bytes が不変であることと evaluator 側 callsite の exact stderr を固定する。
   **新しい fixture file や新規 test file を作らない。** 既存 fixture の構造上 parametrize が
   できないと判明したら、実装せず `## 未了・懸念` にその理由を書いて止まれ。

### 変えてはならないもの

- `orchestrator/campaign/s8c_preregistration.py` の中身 (この fix では 1 byte も変えない)。
- 段 4 裁定の不変条件 1〜7。
- **既存テストの期待値。** 反転・緩和・skip・削除を禁じる。既存 assertion は純増で残す。
  境界テストの literal 化は「期待値の変更」ではなく oracle の独立化だが、
  **固定している命題 (128 は受理、129 は sentinel) を変えてはならない。**
- 赤になったら実装側が誤りである。期待値の方が誤りだと判断したら、変えず**報告して止まれ**。

fixture へ現行 hash を差し込んでテストを甘くしない。期待値へ揮発 payload
(temporary path、時刻、working tree hash) を焼き込まない。
機構の正例・負例は実体を名指しし、`_default_registry_results` / `_normalize_predicate_results` /
診断 helper / sibling API を stub しない。

### テストの走らせ方 (この sandbox の実測済み制約)

- `tools/run_tests.py` は使わない (dispatch preflight で rc=16 になる)。
- `python3 -m pytest` は使わない (guard が拒否する)。
- 走らせられるのは **`PYTHONPATH=. python3 orchestrator/tests/<file>.py`** の自走 harness だけである。
- 実走した nodeid と結果を報告に書く。実走できなかったものは「緑」と書かず「実装済み・未実走」と書く。

## 禁止

- `orchestrator/campaign/s8c_preregistration.py` の変更。
- 上記 2 file 以外の変更、新規 file の作成、docs 編集、`git add` / `git commit` / push。
- 裁定の「scope 外」に挙げた変更。
- 既存テストの期待値の変更・反転・緩和・skip・削除。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。

- `## 追加したテスト` — 各テストが固定する命題と、裁定「fix の scope」1〜5 との対応表
- `## 実走した nodeid と結果`
- `## 受理・拒否の含意` — 受理側と拒否側を 2 文に分け、通る正例を 1 つ添える
- `## production 無変更の確認` — `s8c_preregistration.py` を変更していないことの根拠
- `## 未了・懸念`
- `## 総括`

予算が尽きそうなら、その時点の実装状態をこの出力形式どおりに書いて終われ。無出力が最悪である。
