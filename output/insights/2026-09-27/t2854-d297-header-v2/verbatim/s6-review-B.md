## 所見

1. **must-fix — P-4 は real。実 CCBench の正例が完了条件に到達しない。** [検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:830) は volatile builtin の検出時に `-U__DATE__` などを加える。親の事前所見にある実 CCBench の `-Werror` と GCC 11.4 の実測を踏まえると、builtin 再定義警告がエラーになり、比較結果を出す前に拒否する。合成 test の compile argv には `-Werror` がない（[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_header_rule.py:70)）。**直し方:** probe に `-Wno-builtin-macro-redefined` を加え、`-Werror` を持つ fixture でも検出が働くことを確かめる。

2. **must-fix — P-1 は real。予定集合と実行済み集合の照合が恒真。** [検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1004) の `done` は予定を走査するだけで増え、実際の `pool.map` はその後である。比較を予定から落とす変異を検出できず、[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_header_rule.py:121) も同じ値を数え直している。**直し方:** 完了した `unique_jobs` の結果から、集約先の configure を展開して実行済み集合を作り、予定集合と照合する。V9 の単独変異で test が赤になることを確認する。

3. **should — P-2 は real。未選定 protocol の調査が裁定 S4(b) より大きい。** [検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:938) は全 entry を列挙し、[調査呼び出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:980) でもそれを使う。さらに一度 `choose=True` になっても残りの調査を続ける。放置すると不要な compiler 実行が増え、2 node 時間の線を圧迫する。**直し方:** discovery では当該 production target の entry に絞って旧新・TRACE 両状態を列挙する。選定が確定した後は、残りを調査せず選定 configure として処理する。

4. **should — P-3 は real。既存拒否の順序が変わった。** 親 commit では `_assert_proven_repo_absent_macros` が祖先検査より前だったが、現在は diff 検証後で、header だけなら呼ばない（[検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1064)）。複数の不正条件がある入力では既存 caller が受け取る拒否理由が変わる。**直し方:** `.cc` の既存経路では元の呼び出し順序を保ち、header 経路の扱いを明示して分岐する。

5. **should — P-5 は、事前登録 V2 の kill 条件としては不成立。** [検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:796) は依存と macro 状態を一回の `-E -dM -MD` で取得する。生成 build を飛ばす V2 は未生成 header で前処理が失敗し、期待する「偽緑」に達しないという親の実測と整合する。[V2 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_header_rule.py:161) は現実装の拒否を確かめるが、登録済み V2 の識別を証明しない。**直し方:** V2 の不成立理由を記録し、変異登録から外す。生成 build 単独の V3 は維持する。

## 削れるもの

- **should — 使用しない結果の保持。** [検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:976) の `discovered` への追加結果は後で読まれない。放置すると調査中の依存集合を保持し続ける。**直し方:** `discovered` と追加行を削る。
- **should — target 形式の二重検査。** production provider は [検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:726) で確認し、configure 後の [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:909) と調査前の [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:965) で繰り返す。放置時の主な影響は保守時の判定ずれ。**直し方:** test 供給も含めた provider の返り値を一か所で検証する。
- **should — `supply is None` が本体処理を切り替える。** [検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:879) は production だけ hydrate し、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:900) は production だけ masstree を複製・`config.h` を確認する。合成 test は production の生成物経路を通らず、P-4 のような差を見逃す。**直し方:** S3 の seam を configure argv・生成 target の供給に限定し、hydrate や生成物確認を供給関数側の明示的な契約にする。実 CCBench 判定で production 経路を検証する。
- **nit — 正規化 root の重複。** [検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:734) は `generated` と `third["masstree"]` が同じ path の場合にも両方登録する。長さが同じなら先の `<GENERATED>` が使われ、後者は無効になる。**直し方:** root 登録時に同一 path を一度だけ入れる。
- **nit — 既存部品は一部再利用できている。** `_comparison_evidence`、`_compiler_identity`、`_decode_path`、既存 `_sha256`、buildcache `_v2_commands` は使用されている。`_h_run` を丸ごと `_run_git` に置換すると timeout と binary 出力の扱いが失われるため、そこは単純な削除対象ではない。

## 所要の見積り

生死確認の単価をそのまま当てると、選定 17 configure × 旧新対 × 2 compiler は **34 対 × 約54秒 ≈ 31分の node 時間**。現実装の未選定 48 genome の調査は、全135 entry × TRACE 2 を旧新で実行するため、**48 × 2側 × 約11秒 × 2 compiler ≈ 35分**をさらに使う。configure 自体と負例対照を加えると、判定 job 一走は概ね **1.5〜1.8 node 時間**、正例二本の並行部分の wall は概ね **35分前後以上**と見込む。負例は選定処理を終えてから比較へ進むため、即座には終わらない（[検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:992)、[job](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/judge/run_judge.sh:118)）。受入・焦点走まで含む裁定の2 node 時間の線は、このままでは超える見込みが強い。

新 test は11件あり、通常でも stock と genome の旧新 configure、V5・V6 では追加の discovery を行う（[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_header_rule.py:95)）。静的には追加60秒目標も全 suite 5分上限も保証できない。実測が必要であり、今回は指示どおり実行していない。

## 判定 (GO / NO-GO)

**NO-GO。** P-4 により実 CCBench の正例が拒否される見込みで、P-1 により予定集合の完了検査も機能しない。判定 job は未実行であり、所要は上記の外挿である。

## 総括

先に P-4 と P-1 を修正し、discovery を裁定どおり production target の entry に絞る必要がある。その後、実 CCBench job の Elapse と新 test の所要を記録して、2 node 時間と全 suite 5分の線を判定する。