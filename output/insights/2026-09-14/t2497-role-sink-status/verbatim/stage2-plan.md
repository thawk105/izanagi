## 前提の確認

必読 5 ファイルはすべて読めた。以下の行番号は現 checkout 基準。brief の位置にはずれがあり、`_InvalidPlanner` は 1998 行、status 算出は producer の 3762 行からである。

変更対象は `orchestrator/tests/test_p3_autonomous_workload_trial.py` のみ。以下では同ファイルを `T`、読むだけの `orchestrator/campaign/p3_autonomous_workload_trial.py` を `A` と記す。

親の実測では既存 node が `1 passed in 9.77s`、32 report すべて complete。本段では静的確認だけを行い、編集・テスト実行・commit はしていない。

## プラン (file:line 粒度)

1. **`T:1845`：この検査専用の module-local helper を追加する。**

   ```python
   def _assert_role_sink_report_complete(report, wire) -> None:
       assert report["status"] == "complete", (
           f"role-sink report incomplete: wire={wire}, "
           f"status={report['status']!r}"
       )
   ```

   判定は status の一条件のみ。同ファイルの本 test と負例だけが呼ぶ。汎用 gate、共有 helper module へは展開しない。P2 の局所 helper 方針に同意する。

2. **`T:1914` 直後：実 report を helper に渡す。**

   ```python
   _assert_role_sink_report_complete(report, wire)
   ```

   `A.run_trial()` の返値を加工せず渡し、payload と cells を読む前に検査する。P4 に同意する。worker の失敗には wire が残り、`T:1962` の `executor.map` 結果取得時に伝播する。

   `T:1915` 以降の既存 assert、32 反復、4 role、横断比較、64 回の real admission、並行度定数 `T:56` は変更しない。

3. **`T:1997`：負例 node を追加する。**

   名前は例えば `test_role_sink_report_complete_rejects_fatal_partial` とする。既存 `T:4306` の構成を必要部分だけ使用する。

   - providers は `_RecordingFixture` の planner・coder・auditor のみ。critic を用意しない。
   - 実 `A.run_trial()` を一度呼ぶ。`workloads=["ycsb-a", "ycsb-b"]`、`generations=1`、`provider_kind="fixture"`、専用 `tmp_path`、`sub="/unused"`、`do_build=False`、`drive=_fake_drive`、`preview=_fake_preview`、`allow_unregistered_exploratory=True` を指定する。
   - 返値について、`status == "partial"`、`fatal_error["type"] == "KeyError"`、`len(cells) == 1`、先頭 cell の `stop_reason == "supervisor-error"` を確認する。これらは負例の成立条件である。
   - **成立条件の確認と実 run は `pytest.raises` の外に置く。** 捕捉対象は次の呼出しだけにする。

   ```python
   with pytest.raises(
       AssertionError,
       match="role-sink report incomplete: wire=00000",
   ):
       _assert_role_sink_report_complete(report, "00000")
   ```

   report の合成・差し替え・status 書換えは行わない。第二 workload は実行されず、実行量は一 cell・一 generation。数秒という所要は親の実測で確認する。

4. **親による検証と同一 commit への収容。**

   `tools/run_tests.py` 経由で既存 node と新規 node を実行する。新規 node の所要も確認する。

   helper の assert を一時的に無効化する変異では、新規 node が `DID NOT RAISE` で失敗することを確認し、復元する。最終差分が `T` 一ファイルへの追加のみで、既存検査を保存していることを確認し、両追加を同じ commit に含める。

## (P1) への態度

**status 検査だけに同意する。ただし「自己矛盾」という説明は強すぎる。**

`A:3762` の complete 条件は `fatal_error is None` を必要とし、`A:3832` は非 None の場合だけ report に `fatal_error` を載せる。この実 producer では、complete 検査を通過した後の `"fatal_error" not in report` に独立した検出力はない。

これは条件付きで冗長なのであって、fatal_error 不在という命題自体が常に真なのではない。将来の producer 不整合を検出する用途は考えられるが、本 wave の実在する partial 受理穴を塞ぐためには不要である。

## (P3) への態度

**`_InvalidPlanner` を既定にする案には反対し、fatal_error 付き経路を一つ採用する。両方の追加は不要と判断する。**

根拠となる実経路は次のとおり。

- `A:5133`：渡された providers をコピーする。欠落 critic は補完されない。
- `A:3694` → `A:3410`：pending critic 実行で `providers["critic"]` が `KeyError` を送出する。
- `A:3701`：例外を捕捉して `fatal_error` を設定する。
- `A:3716`：cell を `supervisor-error` にし、`A:3724` で後続 workload を打ち切る。
- `A:3762`：partial を算出し、`A:3832` で fatal_error を report に載せる。

既存 `T:4329`〜`T:4333` もこの結果を検査している。依頼が名指した fatal_error と cell 未完走を、一回の軽い実 trial で再現できる。

`_InvalidPlanner` の role-invalid partial も拒否対象だが、追加判定は原因によらず complete だけを受理するため、今回の負例を二形に増やす必要はない。

## 想定される破れ

- **誤った例外を捕捉する：** run 全体を `pytest.raises` で囲むと別の assert でも通りうる。helper 呼出しだけを囲み、専用メッセージも照合する。
- **helper の assert が消える：** 負例が `DID NOT RAISE` で赤になる。単なる partial 再確認にはしない。
- **本 test の helper 呼出しだけが消える：** この負例単独では検出できない。P2 の同一 callee は判定本体の削除を守るが、接続の削除まで保証しない。`T:1914` 直後の無条件呼出しは差分レビューで確認し、この限界を隠さない。
- **負例構成が将来別経路で失敗する：** raises の外に置く partial・KeyError・cell 数・stop reason の検査で、意図した実経路が維持されているか確認する。
- **所要超過：** 軽量構成という静的根拠はあるが、数秒以内とは未実測。親の測定結果で判定する。

## 総括

局所 helper に complete 検査を一つ置き、32 wire の各実 report に適用する。同じ helper を、実 producer が返す fatal_error 付き partial で拒否検証する。既存被覆と production を保存し、二つの追加を一ファイル・同一 commit に収める。実走結果は本段では主張しない。