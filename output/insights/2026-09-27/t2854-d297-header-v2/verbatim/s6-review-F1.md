## 対応表

静的レビュー対象は HEAD `de51469e` です。「closed」は現 HEAD の実装で修正を確認できた、という意味です。テストと判定 job は実行していません。

| 所見 | 判定 | 現 HEAD の根拠 |
|---|---|---|
| F1 予定集合と実行済み集合 | **closed** | [検査器:1004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1004) で予定を固定し、比較の成功 evidence と所属 configure から `done` を作って厳密照合する（同:1023–1033）。最後の比較を省く V9 なら不一致で拒否する。変異の再実走は未確認。 |
| F2 `-Werror` と builtin probe | **closed** | [検査器:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:827) の probe argv だけに `-Wno-builtin-macro-redefined` を追加。通常の完全展開・include 活性比較は同:838–845 のまま。 |
| F3 discovery の範囲と打ち切り | **closed** | [検査器:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:940) で target に絞り、同:977–984 で発見時に打ち切る。選定後は同:988–991 で全 entry を列挙する。 |
| F4 既存 caller の検査順序 | **closed** | header 引数が全て無い場合、[検査器:1065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1065) から `_resolve_commit`、macro 検査２回、ancestor、diff、`_validate_diff` の順。旧実装と同じ。 |
| F5 V2 の登録 | **closed** | 段６裁定が V2 を登録から除外。残る [テスト:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_header_rule.py:188) は生成 header 経由の負例であり、V2 の kill 証拠とは扱えない。 |
| F6 裁定 OID の固定 | **closed** | [判定 script:13](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/judge/run_judge.sh:13) に C・C2′ の完全 OID を固定し、不一致を exit 2 にする。 |
| F7 代表 fixture | **closed** | [テスト:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_header_rule.py:68) の正例 target に `-Werror`、同:70–83 に TRACE token の無い gamma を追加。同:117–128 で正例と gamma の非 consumer 性を確認する。 |
| F8 局所整理 | **closed** | [検査器:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:736) で同一 root を一度だけ登録。同:889–893 に target 形式検査を集約し、同:977–984 の discovery に未使用結果の保持はない。 |
| 焦点走の consumer test 赤 | **closed（静的）** | [検査器:1127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1127) は `ast.Dict` を直接 return する形に戻った。[consumer test:5212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_mocc_trace_job_contract.py:5212) の AST 条件に合う。再実走は未確認。 |

header 引数なしの起動では、共通 diff の受理・拒否文言、検査順序、返却 dict のキーを旧実装と照合し、差を見つけませんでした。`**` による `header_rule` 展開は header がある場合だけで、引数なしの返り値には加わりません（[検査器:1127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1127)）。修正による新たな過剰拒否や偽緑も、この範囲では見つけませんでした。

## 新しい所見

- **must-fix — F9 の不採用理由には反証がある。** [検査器:739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:739) は root の直後に path 境界があるかを見ず、任意の bytes を置換する。例えば CMake が configure 時に `#define P "${CMAKE_SOURCE_DIR}-extra"` を生成し、変更 header の consumer が `P` を展開する入力を作れる。旧新の実出力はそれぞれ `…/src-old-extra` と `…/src-new-extra` だが、同:845 では両方 `<SOURCE>-extra` となる。乱数 path を**事前に commit する必要はない**。configure が実際の source root から生成できるため、段６裁定の「作る主体が存在しない」は成立しない。root 置換の対象を path 境界のある値に限定し、この入力を負例として固定する必要がある。これは今回の fix が導入した問題ではなく、残存する偽緑経路である。

F10 については反証を見つけませんでした。`supply is None` による hydrate・masstree 複製・`config.h` 確認の分岐は残る（[検査器:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:877)、同:904–918）。裁定が根拠とする実 CCBench 判定 job の結果は、今回の入力にはまだありません。

数値は、提示された単価を使うと `17 × 2 × 54秒 = 30.6分`、`48 × 2側 × 11秒 × 2 compiler = 35.2分` で、親の「約31分」「約35分」と一致します。17 configure、48 genome、135 entry、54秒・11秒という**単価や母数そのもの**を独立に検算できる原データは指定資料にありません。焦点走ログから確定できるのは **325 passed、1 failed、計326件**であり、受入全走ではありません。

## scope 外候補

D780 項２に関わる実 compile command・全 TU・link object・trace symbol/data・build receipt の別防壁、および選定外 genome・opt-in target への拡張。

## 判定

**NO-GO。** F1〜F8 と consumer test の修正は静的に確認できますが、F9 に反証可能な偽緑経路が残ります。実 CCBench 判定 job の結果も未受領です。

## 総括

fix 後の主要な修正はコード上で成立しています。判定を進めるには、F9 の境界問題を解消し、焦点走の再実行結果と実 CCBench 判定結果を確認する必要があります。