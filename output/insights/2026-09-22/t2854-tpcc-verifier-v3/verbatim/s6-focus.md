**判定：NO-GO。B1〜B3 は closed、B4 は partial です。** 型 assertion 自体は有効ですが、予期しない legacy fallback で検査を迂回できます。production の不具合を認定したものではなく、採用所見 B4 の試験が閉じていないという判定です。

以下の行番号は最終 worktree 基準です。

| 所見 | 判定 | 根拠 file:line | 残る穴 |
|---|---|---|---|
| B1 | **closed** | [test_verifier.py:3799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3799)：parse／edge の task 0 を子内で `os._exit(71)`。3815〜3826 は毎回マーカーを除去し、対象呼出し直後に親 PID 集合、子 PID のマーカー、結果と v3 出力の一致を確認。3828 の helper は障害注入を維持したまま、3436〜3442 の辺・versions・producer・取引・結果比較を実行する。 | 採用所見の範囲ではなし。障害なしなら子 PID 集合またはマーカー確認で失敗するため恒真ではない。cycle fixture の両取引は比較対象に入り、表・取引種別の比較も空ではない。 |
| B2 | **closed** | [test_verifier.py:3417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3417)：legacy 1 設定、packed／tuple 各 workers=1／2 の計5設定。3435 以降で残る4設定を legacy と比較。3645、3653 も同じ削減。 | 比較設定の欠落なし。ただし、設定名どおりの実経路を強制する不足は B4 に記載。 |
| B3 | **closed** | [test_verifier.py:3665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3665)：R／W を reads／writes 引数で生成。3381 の宣言件数が実行数に一致し、W 版も commit と一致する。 | 別の構文・件数違反は見つからない。`"1 0"` は意図した余剰 token 拒否。X／I は意味上の違反記録だが、table を直せば ParseError を代替しない。 |
| B4 | **partial** | [test_verifier.py:3426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/tests/test_verifier.py:3426)：packed は実クラスの `isinstance`、tuple は対象 graph の同一性と `dict` 型を確認しており、文字列比較による恒真ではない。 | **両方とも `not isinstance(parsed, _LegacyTrace)` の内側。** `expect_packed=True` でも parser が legacy を返すと肯定 assertion をすべて飛ばし、legacy 同士の比較で通りうる。 |

**B4 の具体的な抜け**

`test_v3_packed_mapping_and_read_bounds` は負の read tid `-1` を含み、packed の read 境界を検査します。しかし、この入力だけ列化時に `OverflowError` となる退行を考えると、[parse.py:665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/orchestrator/verifier/parse.py:665) から legacy fallback へ進みます。helper は packed／tuple の肯定 assertion を飛ばし、当該試験に残る mapping・orphan・辺の assertion は legacy 実装でも満たせます。

これは**静的に導ける検出漏れの例**です。変異は実行しておらず、試験全体での生存は未実証です。現在の production がこの退行を起こしているという主張でもありません。

通常 fixture では、compact モードに対して `_CompactTrace` を肯定 assertion してから表現を検査すれば閉じられます。意図的な overflow fixture の許可は別に残せます。

**回帰と規模**

[fix2.diff](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/fix2.diff:5) の全7 hunk は、段5で追加された v3 helper／試験内です。production、既存試験、自走 runner の変更はありません。削除された経路比較は legacy の workers 重複分で、残る比較 assertion の削除・弱体化は見つかりません。`expect_packed=False` の追加先も、従来から非 packed を要求する overflow 試験だけです。B4 は新たな退行ではなく、強化の取りこぼしです。

差分ヘッダーを除いて `+`／`-` 行を直接再集計しました。

| 対象 | 追加 | 削除 | 追加＋削除 |
|---|---:|---:|---:|
| fix2 の test_verifier.py | 71 | 21 | 92 |
| wave 起点からの test_verifier.py | **486** | **0** | **486** |

[integrated-final.diff:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/integrated-final.diff:5) は試験ファイルについて単一の追加 hunk です。報告の「追加486行」と一致し、R9 の **800行以内、余裕314行**です。旧報告436行とも `436 + 71 − 21 = 486` で整合します。

親の [solo-2.log:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/solo-2.log:9) は **132 passed in 4.01s、rc=0**。ログ冒頭の指定どおり、受入全走・変異 KILLED の証拠には扱いません。本レビューでは変更・テスト実行を行っていません。

## 総括

B1 は子の異常終了と対象呼出し直後の逐次復帰を観測しており、closed。
B2 は legacy の重複だけを除き、compact の workers 別比較を維持しており、closed。
B3 は R／W の宣言件数を修正し、別の構文拒否理由を残しておらず、closed。
B4 の型・同一性 assertion は有効だが、予期しない legacy fallback で迂回できるため partial。
fix2 は新規 v3 試験内に限定され、production・既存試験の変更はない。
wave 全体の試験差分は再計算でも486行で、R9 の800行以内。
親の実測は132 passed・rc=0だが、B4 の検出漏れを否定する証拠ではない。
判定は **NO-GO**。通常 fixture の compact 経路到達を肯定 assertion する修正が必要。