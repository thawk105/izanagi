## 所見

1. **must-fix — `run-pair.sh:102–117`**  
   shard の対応付けが `wt in first` という部分一致です。例えば K が `/.../K`、H が `/.../K2` なら、H の login log も K に一致し、K が `multiple` になります。同時に走る別 wave の path が接頭辞関係でも同じです。1 行目の `command=` JSON から対象 path を取り出し、worktree の正規化済み path と完全一致で照合してください。

2. **must-fix — `run-pair.sh:15–33`**  
   clean・同一 HEAD・対象 pyc 0 は調べますが、4 本が fresh worktree であること、submodule を指定ツールで初期化したこと、HEAD が投入直前の local main であることを調べません。既存の clean な木を渡しても事前登録に適合した走として進みます。作成・初期化の証跡と local main の commit を記録して照合するか、runner が4本を作成してください。

3. **must-fix — `run-pair.sh:48–56,107–110`**  
   `K/H.env.txt` は設定する予定の値を書いたものです。login collection が受け取った実効 `PYTHONDONTWRITEBYTECODE` は成果物に記録されず、`aggregate.py:83–86` も予定値だけを検査します。呼出元の環境が残った場合などを実測で判別するという段4裁定の記録条件を満たしません。login 子に渡す環境の実測値を記録し、集計はその値で H の残留を判定してください。

4. **should — `aggregate.py:146–157`**  
   対の再実施関係を持たず、渡された valid な先頭2件だけで総合判定します。同じ pair ID を2回渡せば、実質1対でも「2対支持」になります。原対1・原対2と各1回までの取り直しを識別し、別々の有効な2対で判定してください。

5. **should — `run-pair.sh:8–10,41–42`**  
   出力 dir が K/H の worktree 内でも受け付けます。その場合、runner 自身の `mkdir` と記録が木を汚し、投入前 clean 検査と後続の対を壊します。また `<pair>.pid` は既存でも上書きします。出力先が両木の外であることを確認し、pid も排他的に作成してください。

6. **should — `run-pair.sh:34–40`**  
   「同時刻の他の受入 leader 数」の代わりに、起動前の全 `run_tests.py` 数と `dev_wave_wait.py acceptance` 数を記録しています。他 wave の leader 数を投入時点で示せず、対の競合状況を評価できません。K/H の投入時刻に、他の受入 leader を識別して記録してください。

7. **should — `aggregate.py:46`**  
   login 完了前開始を `junit timestamp < login-collection.log mtime` で判定します。提示された実物では log の mtime が秒単位です。同じ秒内に shard が log 書込みより先に始まると、除外対象を適格扱いにし得ます。十分な精度の完了時刻を記録するか、同秒の境界を判定不能として扱ってください。

## 反証できず

- 共有雛形の差分は指定のコメント追加と export 削除だけで、門番の閾値・周期・再投入、後段の heredoc・receipt 経路に別の byte 差分はありません。
- `run_tests.py` の login collection と shard dispatch は `os.environ` を継承します。runner の K/H の設定と unset は両経路に届き、dispatch request の値は `environment.PYTHONDONTWRITEBYTECODE` に記録されます。
- 実物の shard 成果物で、junit の `timestamp`・`time`・`hostname`、report の collection 完了・worker 占有、confirm と request の各 path は集計コードの読取先と一致しました。
- Δpre がちょうど30秒なら支持、H の全 shard が早期開始なら判定不能、shard 欠落なら無効、という集計上の境界処理は裁定に沿っています。
- 対照の実走は確認していません。

## 総括

**NO-GO。** shard の誤対応と、事前登録した木・実効 env の証跡不足により、現状の対照結果は効果判定に使えません。