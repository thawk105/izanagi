## 1. プラン v2 を超えた変更

**判定：refuted。実装の scope 逸脱は見当たらない。**

job body は指定位置への export 1 行だけ。launcher は arm→tree の選択、command ごとの tree 保持、4 必須引数への置換であり、v2 が変更禁止とした関数は差分に含まれない。互換層・追加拒否・本走への一般化もない。

`Mapping` は `launch` の注釈で使用されており、不要な import ではない。読み取りだけの引数を表す型として妥当で、実行時の一般化機構を追加していない。周辺には `dict[str, str]` が使われているため、最小化だけなら次も可能だが、修正必須とは判定しない。

**残す最小の差分（任意）：** `Mapping` の import を削り、引数を `trees_by_arm: dict[str, SubmitTree]` にする。冒頭 docstring の変更は v2 の明示指示どおりで、そのまま残す。

## 2. test の過剰

**判定：real（軽微な重複）。helper と lock 観測は refuted。**

- `_read_driver_environment` は B-5・default・pair の共通読取りであり、重複実装を避けている。B-5 の独立した期待 path は M1・M2・M4、非 B-5 の未設定観測は M3 に対応する。削らない。
- submit test の runner 内に追加した env の解析と `repo root == cwd` は、後段の `(argv, cwd)` 完全一致と重複する。M5・M6 の検出に追加の寄与がない。
- main dry-run の env 全体・argv 全体の比較は、v2 が要求する CLI→各 tree の配線確認より広い。全体比較は既存の launcher 単体 test に残せる。ただし validator stub が `thirdparty_source_root=None` を返す点は、main の `replace` を通すため合理的。

**残す最小の差分：**

1. runner 内の次の2行だけ削除し、`calls.append((argv, cwd))` と後段の完全一致を残す。

   ```python
   env = dict(value.split("=", 1) for value in argv[argv.index("-v") + 1].split(","))
   assert env["IZANAGI_S4_REPO_ROOT"] == str(cwd)
   ```

2. main test は validator の4回・順序・共通 HEAD、出力4件、既存の副作用不在確認を残し、出力比較を次に絞る。

   ```python
   for record, job in zip(records, jobs):
       assert record["arm"] == job.arm
       assert record["environment"]["IZANAGI_S4_REPO_ROOT"] == str(
           trees_by_arm[job.arm].repo
       )
   ```

この削減後も登録変異への検出経路は静的には残る。変異実走による確認はしていない。

## 3. test の不足による過剰な主張

**判定：refuted。ただし commit message に条件の省略がある（軽微）。**

README は lock の設定位置と排他範囲を説明し、専有を保証しないと明記している。「実際に flock が効いた」「本走全体を投入可能にした」とは述べていない。launcher の docstring も試走と本走認可を区別している。

commit message の「非 B-5 は未設定であることを検査する」は、harness が入力の lock 値を除去する条件下では正しい。任意の継承環境まで検査した意味には広げられない。

**残す最小の差分：** 当該文を「入力の `IZANAGI_BENCH_LOCK` を除去した条件で、非 B-5 driver には未設定のまま届くことを検査する」とする。継承値専用 test は追加しない。

fake driver の環境観測から言えるのは driver 起動境界までの伝播であり、実際の lock 取得・競合待ち解消・性能改善の実測ではない。

## 4. README

**判定：scope 逸脱は refuted。短縮は可能。**

4 checkout の準備と共通 HEAD は、確定した job ごとの tree 配置に必要な既存手順の適用である。新しい検査・義務の独立した追加ではない。排他範囲の限定も s4 の A3 に従っている。

「別 path」は呼出し側が用意する条件として読めるため、launcher が重複を拒否するという主張ではない。

**残す最小の差分：** 4 引数の実行例と checkout の説明を維持し、lock 部分は次まで縮められる。

> B-5 mode は driver 直前に `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を設定する（B-10 / A-5 と同じ job 固有 scratch）。排他は同一 job 内に限られ、ノード専有は保証しない（`docs/pegasus-runbook.md` §1）。非 B-5 の3経路では変更しない。

これで「既定の home 共有 lock」という補足の条件省略も避けられる。

## 5. scope 外の記録

**判定：refuted。除外判断は妥当で、実装も従っている。**

`main` は4 path を個別に既存 validator へ渡すだけで、path 相互の重複判定や common repo の比較を追加していない。既存の ledger/evidence 相互排他検査は、submit-tree 重複拒否の混入ではない。

launcher は引き続き `write-heavy`・series 1・block 1・4 job に固定され、本走108系列への一般化、walltime 統一、Tier0 の追加もない。同じ tree を4回渡せば共有配置に戻る点は、s4 で明示的に除外された境界であり、本レビューで新たな欠陥として起票しない。

**裁定パッケージ候補：なし。** 新しい gate・検査・台帳の提案は scope 外であり、今回は追加を提案しない。

## 総括

**実装の scope 逸脱はなし。real はテストの軽微な重複で、具体的な削減案を上記に示した。** 文書には条件の明確化と短縮余地があるが、実測成功や本走認可を過剰に主張してはいない。

本レビューは静的検査のみ。親の f1 log は **2,074 passed / 9 skipped、rc=0** を記録しているが、受入全走ではない。f2 の完了結果と M1〜M9 の kill は未確認であり、wave 全体の完了判定はしない。