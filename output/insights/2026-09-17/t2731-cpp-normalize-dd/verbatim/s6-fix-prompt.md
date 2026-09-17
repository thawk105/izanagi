単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md`
  — 親の段 4 裁定 (plan v2、gate の署名、主張の限定)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s6-a-out.md`
  — 段 6 レンズ A の所見 (A6-1、A6-2 が本 fix の対象。A6-3 は親の記録側)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s5-author-prompt.md`
  — 段 5 実装子の契約 (所有・権限・禁止をすべて継承する)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/campaign/source_digest.py`
  — 編集対象 (`_cpp_normalize` の docstring :1647-1673)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py`
  — 編集対象 (`test_source_digest_cpp_environment_prefix_mismatch_fails_closed` :11965-11987)

## 所有と権限 (段 5 契約を全文継承)

- 編集してよい file は `orchestrator/campaign/source_digest.py` と `orchestrator/tests/test_campaign.py` の 2 つだけ。
  docs・登録簿・他 test・`external/ccbench` に書かない。commit・push・stash をしない。
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。受理集合を変えない (今回の fix は挙動を変えない)。
- 規律 2 を緩めない。gate・helper・一般化を足さない。

## この段の仕事 (2 件、いずれも挙動不変)

1. **A6-1 (test G の署名固定)**: `test_source_digest_cpp_environment_prefix_mismatch_fails_closed` の
   `pytest.raises(RuntimeError)` を `pytest.raises(RuntimeError, match="環境 prefix と不一致")` にして、拒否理由の署名
   (実装の message `source_digest: preprocess 出力が空入力の環境 prefix と不一致 — identity を確定できないため fails-closed`)
   を固定する。偽 compiler の起動失敗や非ゼロ終了で偶然通らないようにするのが目的。
   さらに `finally` の cleanup を、修正前 HEAD (cache 属性が無い版) に新 test だけを載せても `AttributeError` で赤理由を
   覆わないよう `getattr(source_digest, "_CPP_ENV_PREFIX_CACHE", {}).pop((cxx, ()), None)` の形にする
   (DW-M08 の新旧両走で「例外が出ない」赤を見えるままにする)。
2. **A6-2 (docstring の受理集合注記)**: `_cpp_normalize` の docstring の「残る限界」の直後に 1〜2 行で、
   `_trace_pair_diff` (diff-of-diffs) の比較式 `D_variant == D_stock` は不変だが、`#if TRACE` 内の未使用 `#define` / `#undef`
   も差分素材になるため受理集合は狭まる (規律 2 と同方向) 旨を追記する。除外処理は足さない。

変更後に `python3 -m pytest orchestrator/tests/test_campaign.py -k "cpp_environment_prefix_mismatch" -q -p no:cacheprovider`
を試みてよいが、sandbox で起動できなければ「実装済み・未実走」と書く (親が計算ノードで実走する)。
`git diff --stat` が 2 file だけであること、`git diff --check` が通ることを確認する。

## 出力形式

Markdown。次の H2 節をこの順で必ず置く。所見ごとに closed / partial / regressed を表で示す。

## 所見ごとの対応表 (A6-1 / A6-2)
## 変更した file と差分の要約
## 実走した nodeid と結果 (緑 / 赤 / 未実走)
## 総括

予算が尽きそうなら、途中までの結論をこの出力形式どおりに書いて終える。**無出力が最悪である。**
