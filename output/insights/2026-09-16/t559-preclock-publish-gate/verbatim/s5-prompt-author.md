単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl

## 必読事項の射影

次の絶対パスだけを読む。**この節が列挙した file を読めなければ即停止する** (停止規則の射程は
この射影 file に限る。ここに無い path の不在は停止理由にしない)。

- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/ruling-stage4.md — **親の裁定。これが実装仕様の正本**
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/artifacts/t559-preclock-publish-gate/stage2-plan.md — 段 2 plan (参考)
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D191.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D218.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D155.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-F108.md
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl/orchestrator/calibrator/cli.py
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl/orchestrator/calibrator/effective_clock_policy.py
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl/orchestrator/calibrator/report.py
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl/orchestrator/calibrator/schema_v2.py
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl/orchestrator/campaign/execution_guard.py
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl/orchestrator/tests/test_calibrator_certify.py

## 作業場所

**編集してよいのは `/work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl` 配下だけ**である。
このうち編集してよい file は次の 2 つだけ。

- `orchestrator/calibrator/cli.py`
- `orchestrator/tests/test_calibrator_certify.py`

他の file を作らない・変えない・消さない。docs を編集しない。**commit しない。**
branch 操作・git の状態変更をしない。`.codex/` 配下に成果物を書かない。

## 実装するもの

親の裁定 `ruling-stage4.md` の「plan v2 (実装仕様)」節を**そのまま**実装する。
要旨は次のとおりだが、**食い違ったら裁定文を正とする**。

較正取得 CLI は benchmark 後の実効クロックを一度も検査せずに publish する。
既存の `_effective_clock_self_comparison_passes` は benchmark 前に凍結した profile の
**自分自身**を見るだけで、benchmark 後の観測値を見ない。
凍結 pre profile と benchmark 直後の post 観測 clock の canonical 比較を、**publish の前**に課す。

挿入位置は `cli.py` の `_certify_main` 内、既存 self 照合 (`:1015–1016`) の直後、
`status = "accepted" if not reasons else "rejected"` (`:1017`) の直前。

## 絶対に守ること

1. **canonical 述語 `effective_clock_comparison_passes` を経由し、その戻り値だけで受理を判断する。**
   帯計算を再実装しない。診断値 (`effective_clock_comparison_diagnostics`) を受理判断に使わない。
2. `orchestrator/campaign/execution_guard.py` と `orchestrator/calibrator/effective_clock_policy.py` を
   **変更しない** (編集許可 file にも入っていない)。
3. publish (rename) の位置・順序を変えない。`_published_self_comparison_receipt` を動かさない。
   拒否時に published artifact を削除しない。
4. 既存 reason を消さない・上書きしない・統合しない。新 reason は末尾へ append する。
5. **合格する attempt の published artifact の bytes を変えない。** calibration artifact に
   新しい field を足さない (`notes` を含め、既存 field にも post 情報を混入させない)。
6. **既存テストの期待値を変えない。** 反転・緩和・skip・削除を禁じる。唯一の例外は
   `test_calibrator_certify.py` の `_EARLY_CLOCK_NOT_EVALUATED` 定数 (`:34–45`) に
   新しい検査名を 1 つ足すことだけ。既存 fixture (`_pegasus_shaped_probe` `:253`、
   `_expect_48_physical_cores` `:286`、`_fake_calibrate` `:367`、`_invoke` `:379`) を変更しない。
   48 標本・3 回 profile 取得・tolerance を持たない observed profile という形を崩さない。
   期待値が誤っていると判断したら、**実装を変えずに報告して止まる**。
7. 指示外の受理集合変更をしない。
8. テストを甘くして緑にしない。fixture へ現行 hash を差し込まない。期待値へ揮発する値
   (作業ツリー hash、時刻、絶対 path) を焼き込まない。
9. 機構の正例・負例は実体を名指しする。依存先を stub して機構を通らない緑を作らない。

## テスト

裁定文「テスト要件」節の 6 種の入力をすべて実装する。とくに次の 2 つを落とさない。

- **policy 変更負例**: benchmark 中に `EFFECTIVE_CLOCK_TOLERANCE_PCT` が変わり、post は全標本帯内。
  canonical の戻り値は False (policy 不一致) だが `diagnostics["band_pass"]` は True になる。
  この入力で新 reason が出ることを要求する。これが「canonical の戻り値で判断している」ことの証拠になる。
  既存の self reason も同時に出るので、**両 reason の存在**を要求する。
- **canonical への spy**: 「呼ばれた」だけで足りない。expected が凍結 dynamic pre と、
  observed が `static_post` と**値一致**することを assert する。引数を入れ替える変異を殺せるようにする。

親が名指しした要件を網羅と見なさない。テストを新設・改名したら、その単位に掛かる
制約 meta-test (file 集合の列挙テスト、命名規約テストなど) を**自分で洗い出して走らせる**。

`_EARLY_CLOCK_NOT_EVALUATED` の定数を 1 つ更新すると
`test_calibrator_certify.py:841,959,1237,1454` の完全一致 assertion が追随する。4 箇所とも緑にする。

## 実走

このファイルの自走 harness を使う。

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl
PYTHONPATH=. python3 orchestrator/tests/test_calibrator_certify.py
```

`tools/run_tests.py` と `python -m pytest` は sandbox では走らない。使わない。
**緑を報告するときは実走した nodeid と範囲を併記する。** 走らせていないものを緑と書かない。
実走できなかったものは `closed` と申告せず「実装済み・未実走」と書く。

## 期待赤

親の docs は未 land である。自走 harness で**赤になってよいのは次だけ**とし、それ以外の赤は
回帰として報告する。

- なし。本 wave の変更面では `orchestrator/tests/test_calibrator_certify.py` が全件緑になるはずである。
  緑にならない赤が出たら、原因を切り分けて報告する。自分の実装が原因なら直す。

## 完了報告に必ず書くこと

1. 変更した file と、変更したハンクの行範囲。
2. 実走した nodeid と結果 (passed/failed の件数、実走コマンド逐語)。
3. **所有外 caller・共有 fixture・consumer test への波及可能性**を静的に列挙する
   (名前の推測でなく参照関係で引く)。
4. scope に入る前の**現行の受理・拒否挙動**と、変更後の受理・拒否挙動の差。
5. 実装しなかった裁定項目があれば、その理由。

## 出力形式

H2 見出しだけを使う。最後に必ず次の節を置く。

## 総括

- 実装した内容を 3 行以内。
- 実走結果 (コマンドと件数)。
- 未達・未実走・懸念。
