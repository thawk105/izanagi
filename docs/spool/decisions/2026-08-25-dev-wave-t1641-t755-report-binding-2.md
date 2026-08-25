---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1641-t755-report-binding
seq: 2
---

## {{D:bind-report-to-invocation}}. 検査 report を受領証へ束縛するときは、report の自己申告を producer の実引数と照合する

**決定:** 検査の report を受領証・実行結果へ束縛する場合、report が名乗る値を写すだけでは足りない。
report が自分の invocation identity として持つ field (対象 commit、対象 repo、compiler、対象 path) を、
producer が実際に渡した引数と照合し、食い違えば fail-closed にする。

照合は **realpath 同士**で行う。checker 側が引数を正規化していることがあり、渡した値をそのまま
比較する述語は偽陰性になる (本 wave の実測: `--cxx /usr/bin/g++-12` を渡すと report は
`/usr/bin/x86_64-linux-gnu-g++-12` を名乗る)。

schema は**版を固定せず族の接頭辞で受ける**。版は実際に上がる (同じ checker の report が v1 から
v2 へ上がった実測がある) ため、定数一致を強制すると版上げのたびに producer が赤くなる。
一方で「任意の非空文字列」まで広げると、無関係な検査の report が受理される。

**理由:**
- 4 項目を写すだけの形では、所定 path に偽の report を置けば内容述語がすべて通る。SHA-256 は
  偽の自己申告を含む bytes を正確に束縛するだけで、証拠の鎖にならない。
- invocation identity の照合は、偽の report が producer の実行と整合していることまで要求する。
  これは受領証の外に根拠を置かないという要件そのものである。
- 族の接頭辞で受ける形は、観測済みの版を両方受理しつつ、識別子そのものを無効化しない。

**却下した選択肢:**
- report の自己申告をそのまま写す — 主張と根拠が結合しない。
- schema を現行定数と完全一致で照合する — 実測済みの旧版 report を拒否し、版上げのたびに壊れる。
- schema を「非空文字列」だけで受ける — 無関係な検査の report が受理され、受理集合が識別子ごと消える。

## {{D:immutable-path-for-check-and-use}}. 検査と使用のあいだには、外から書き換えられない経路を 1 本通す

**決定:** 生成物を検査してから使うまでのあいだに、対象が差し替えられうる場合、検査結果を
可変ファイルへ置いて読み直す形にしない。次のいずれかで、検査した対象と使う対象を結合する。

1. 生成側 process が値を **stdout などのプロセス内経路**で返し、呼び手が変数として保持する。
2. `os.open(..., O_NOFOLLOW)` で開いた **同一 fd** に対して `fstat` し、同じ fd から読む。
   pathname を 3 回引く (`islink` / `stat` / `open`) 形にしない。

**理由:**
- 可変ファイルに値を書いて読み直す形は、対象とその値を辻褄を合わせて同時に差し替えれば通過する。
  照合点を増やしても、全部が同じ可変面を見ているなら防壁は 1 枚である。
- pathname lookup を分けると、検査した inode と読んだ inode が同一である保証が無い。
- 同じ attempt directory を別の書き手が触る事象は、この計測系で実際に起きている
  (前 job が共有先へ残した成果物を次 job が検出して fail-closed した実例がある)。

**却下した選択肢:**
- 照合点を増やす — 同じ可変面を見ている限り枚数は増えない。
- 検査後に読み直す前提で運用注意を書く — 機械が守らない防壁は防壁ではない。

## {{D:no-3-10-only-api-in-compute-job-writers}}. 計算ノードの job body が使う埋め込み script に、解決先未固定の interpreter の新しい API を書かない

**決定:** 計算ノードの job body から `python3` を素の名前で起動する埋め込み script では、
その計算ノードで解決される version が固定されていない限り、新しい version でしか動かない
API を使わない。同じ拒否が古い API で書けるなら古い側を選ぶ。

**理由:**
- この計測系は、計算ノードの既定 `python3` が要求 version 未満だったために実際に落ちている。
  同じ経路で受領証が書けなくなれば、計測は成功しても記録が残らない。
- 本 wave で使いかけた `os.path.realpath(..., strict=True)` は、`os.open(..., O_NOFOLLOW)` で
  元の path を開いて `ENOENT` に落とす形へ置き換えられ、拒否の中身は変わらなかった。
  版依存だけを外せる場合がある。

**却下した選択肢:**
- 受領証 writer 用に interpreter resolver をもう 1 本足す — 起動経路が増え、
  resolver 自身の失敗経路も増える。拒否の中身を変えずに版依存を外せるなら不要である。
- 計算ノードの version を前提として書く — 前提が破れた実例がある。
