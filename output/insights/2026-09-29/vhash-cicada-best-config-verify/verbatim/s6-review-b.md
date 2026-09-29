### B1 正例 job が対照 cell を再走する

重大度: **must-fix**
根拠: `launch_cicada_run.py:161-164,1423-1429`
放置すると: J1 の `BEST/W2/t48` と L0 の `BEST100/W4/t4` を POS で再走し、R4 の重複除外に反する。正例の「同じ cell の stock が合格」という主張も、どの走行を対照にしたか曖昧になる。
推奨対処: POS は正例 2 run だけにし、L0・J1 の保存済み対照 record を build、cell、flags、照合結果付きで明示的に参照する。参照できなければ「期待した経路で検出」に分類しない。

### B2 W4 の第二尺度が L0 と重なる cell で欠落する

重大度: **must-fix**
根拠: `launch_cicada_run.py:153-160,1385-1397`
放置すると: L0 の `BEST100/W4/GC1000/t4` または `CTRL/W4/GC10/t4` が 1,000 commit 未満でも、J1 ではその cell を除外するため tuple 1,000 の追加 run が発生しない。R4 の事前登録した第二尺度を満たせない。
推奨対処: L0 の commit 数を J1-W4 に渡し、該当 cell の追加 run を同じ W4 job に登録して、元の L0 run との対応を保存する。

### B3 W4 追加 run の例外で元 run の記録が消える

重大度: **should**
根拠: `launch_cicada_run.py:1384-1413`
放置すると: 追加 run が例外を出した場合、外側の `except` が元 run の key を例外 record で上書きする。元 run の commit 数、診断、判定結果が JSON から失われ、追加理由も残らない。commit 数を読めなかった場合も `None or 0` により追加 run が起動する。
推奨対処: 元 run を保存してから追加 run を別の例外処理で実行する。追加条件は commit 数が整数で 1,000 未満の場合に限定し、元 run と追加 run の record をそれぞれ逐次保存する。

### B4 J2 の投入条件と総 Elapse 予算を起動器が検査しない

重大度: **should**
根拠: `launch_cicada_run.py:165-170,1518-1555,1607-1612`
放置すると: L0・J1 の trace 行数、判定器秒数、job Elapse による R4 の予測を経ずに J2 を起動でき、600 秒・6,000 秒の投入条件と 7,200 秒の総予算を破りうる。run record 自体には trace 行数、判定器秒数、run 秒数がある。
推奨対処: 親の dispatch 側で投入前の計算と記録を必須にするか、起動器にその記録を要求する。

### B5 大きい trace と正例 stderr を全量メモリへ読む

重大度: **should**
根拠: `launch_cicada_run.py:1155-1176,692-715,846-873`
放置すると: J2 の trace や正例の事象が大きい場合、`capture_output`、`read_text().splitlines()`、事象と W の全件保持で計算ノードのメモリを圧迫し、判定前に失敗しうる。失敗時には正例の全件保存も成立しない。
推奨対処: stdout・stderr を直接ファイルへ流し、trace と帰属の走査を逐次処理にする。判定器の timeout 900 秒は維持されている。

## 総括

**このまま J1 以降の実走に使うべきではない。** B1 と B2 を直さないと、正例の対照関係と W4 の第二尺度が裁定 R4・R5 を満たさない。B3 の記録消失も先に直すのが妥当である。L0 の 5 cell、J1 の基本 GC・thread 展開、J2 の cell 定義、CUSTOM の登録済み 1 軸 build 選択、CMake・FLAGS の照合、診断 patch の適用順には、静的確認の範囲で別の重大な齟齬は見つからなかった。repo の tracked file と `external/ccbench` の作業状態は clean で、repo 外 patch を `patches/` 全件走査へ加える変更もない。build・実走・判定器の成否は未確認として扱う。