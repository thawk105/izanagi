## 正しさ境界の所見

1. **stdin 列から実 header 内の真偽は結論できない。**
   根拠：`source_digest.py:1662`、`:1666`、`s2-plan-out.md:48`、`:89`、`external/ccbench/include/backoff.hh:11`。
   GCC の quoted 探索は現在ファイルのディレクトリ、`-iquote`、通常の探索列という順序になる。stdin のファイル名は空文字で、そのディレクトリからの相対探索はプロセスの cwd に帰着する。相対 `-iquote` も cwd 基準であり、元 source/header のディレクトリへ自動補正されない。[GCC 探索規則](https://gcc.gnu.org/onlinedocs/gcc/Directory-Options.html)、[libcpp 実装](https://raw.githubusercontent.com/gcc-mirror/gcc/master/libcpp/files.cc)。

   **成果物への影響：** `build-search` が代表するのは、保存した cwd・argv・環境下での人工 stdin の評価である。`backoff.hh` 内の `"tsc.hh"` が持つ隣接探索、先行 include が供給するマクロ、実 include 経路は代表しない。stdin 同士の一致を「実 build と一致」と読む結論は無効。計画の `build-header` はこの区別に有効だが、実 TU 全体の再現ではない。

2. **`-I S/include` を便宜的に追加しない判断は正しい。**
   根拠：`external/ccbench/CMakeLists.txt:68`、`cmake/ProtocolHelpers.cmake:36`、`cc/silo/include/transaction.hh:9`。
   common が公開するのは `S`。実 header は相対 include で `S/include/backoff.hh` に入り、そこから隣接 header を探索する。

   **成果物への影響：** `-I S/include` の追加は隣接 quoted 探索の再現にならず、angle 探索にも新しい経路を与える。`<tsc.hh>` や next の結果まで変えうる。ただし「実 command に絶対に現れない」とまでは言えない。環境・依存 target 等が供給した実測フラグは保存すべきである。

3. **再構成列は、生成 command を得た場合以上に限定される。**
   根拠：`s2-plan-out.md:52`、`buildcache.py:1937`、`:1952`、`external/ccbench/CMakeLists.txt:71`、`cmake/ThirdParty.cmake:58`、`:66`、`:85`。
   dependency prefix による imported target の探索先、FetchContent source override、推移的 include の順序が食い違う具体経路がある。また masstree の `config.h` は build の custom command の出力なので、configure 成功だけでは本 build 時点のファイル存在状態を保証しない。

   **成果物への影響：** 再構成した環境の値としては有効でも、admission 実 build の値には昇格できない。生成 command を取得した列でも「configure 後に存在した header 集合」という時点の限定が残る。

## 整合・実効性の所見

1. **正負・反転対照には歯があるが、探索環境の取り違えには歯がない。**
   根拠：`s2-plan-out.md:186`〜`:192`。
   全セルを常に `1`／`0` にする壊れ方は正負対照で、同一 path の古い値を再利用する壊れ方は反転対照で検出できる。一方、絶対 path の対照は `-I`・`-iquote`・標準探索順に依存しない。build 列にも checker argv を使う、cwd を取り違える、といった壊れ方でも対照は通りうる。

   **成果物への影響：** 対照成立は「列の探索条件が実 build と対応した」証拠にはならない。保存された実 argv・cwd と生成 command の対応が別途根拠になる。

2. **抽出対照の成立だけでは compiler 起動を証明しない。**
   根拠：`s2-plan-out.md:87`、`:139`、`:189`、`:211`。
   未起動で空 stdout なら計画の条件で排除できる。しかし入力には両 sentinel があるため、入力から片方を選ぶ誤実装、以前の正常な stdout/rc の再利用、対照の期待値を観測欄へコピーする誤実装は、対照だけでは排除できない。これは未実装 harness の**故障仮説であり、発生確認ではない**。

   **成果物への影響：** `value` は今回の subprocess の rc/stdout から導出された場合だけ実測値になる。対照成功を起動証跡の代用にはできない。

3. **(P1-d) の関数は実際に受理判定を駆動する。ただし直呼びは全経路実走ではない。**
   根拠：`source_digest.py:2409`、`:2448` → `:1894`〜`:1898` → `:1813`。
   両 resolver は公開 guard を呼び、公開 guard は対象 source ごとに内部関数を呼ぶ。休眠関数を叩く計画ではない。ただし直呼びは先行する allowlist/include 検査、repo 不在マクロ確認を通らず、`known_absent` も既定の空集合になる。

   **成果物への影響：** 「対象 fixture で内部 guard が拒否した＋resolver の静的配線を確認した」は成立する。「実 variant が resolver でこの拒否点へ到達した」は未測である。

4. **同じ fixture の結果マクロが、目的の拒否より先に preprocess を発生させる。**
   根拠：`s2-plan-out.md:79`、`:82`、`source_digest.py:1858`、`:1861`、`:1866`。
   fixture に `IZ_T1643_RESULT` の `#define` があるので、literal 条件でも `_dump_macros` が先に走る。そこで operator 非対応・探索診断等による失敗が起きれば、専用の条件 operator 拒否へ到達しない。診断に `__has_include` が含まれるだけで `reject_condition_operator` と分類すると誤計上する。

   逆に define 本体・貼り合わせの拒否は `:1845`、`:1851` で compiler 起動前に成立する。compiler 不在でもこの拒否は観測できる。また compiler ごとの新 process でも、同じ process 内の後続行には `:1736` の環境マクロ cache が効く。

   **成果物への影響：** 拒否分類は発生箇所に従い、前段の失敗は `other_error`。字句拒否を「当該 compiler で式を実測した」と数えない。計画の traceback 保存方針は妥当である。

## 親 brief への反論

1. **manifest 以外にも「同じ compiler を共有する」の例外経路がある。**
   根拠：`s1-brief.md:38`、`pipeline.py:1938`、`:1992`、`:2002`、`buildcache.py:3140`。
   site 選択した compiler を build へ渡すのは `env_contract` がある分岐。`common is None` の legacy 分岐は `cc/cxx` を渡さず、`build()` の既定 `gcc-13/g++-13` を使う。

   **成果物への影響：** 対象 admission がどちらの分岐か未確定なら、compute `g++` を build 側 compiler と断定できない。この配線の存在だけから、誤った binary の受理が起きるとは結論しない。

2. **選択される名前 `g++` は `/usr/bin/g++` の保証ではない。**
   根拠：`buildcache.py:1841`、`:1177`、`:1969`、`source_digest.py:1668`、`verbatim-rulings.md:128`。
   site helper は名前を返し、PATH 解決で実体が決まる。v2 configure は解決後の realpath を使う。compute の PATH に別 installation や wrapper が先行すれば、login の `/usr/bin` 調査とは別の実体になる。

   **成果物への影響：** login の不在・version 観測は、その時点の host/PATH の観測に限定される。compiler 本体が一致しても標準 header 配置・環境が異なれば、include 探索 pair の同一性は未確定である。

3. **「拒否の実測は一式だけ」は、引用した根拠と逆である。**
   根拠：`s1-brief.md:8`、`verbatim-rulings.md:27`。
   引用した一式は、当時の guard が**受理してしまった反例**であり、現行 blanket reject の発火実測ではない。さらに `orchestrator/tests/test_campaign.py:11963`、`:11972`、`:12082` には literal・define・貼り合わせについて resolver 拒否を確認する既存コードがある。今回そのテストは実行していない。

   **成果物への影響：** 既存の真偽差観測、既存の拒否被覆、今回の実 pair 観測を分ける必要がある。「一式だけ」は提示された旧真偽差記録の範囲に限定すべきである。

4. **純増 (b)(c) は一部過大、既測式の再測定価値は一部過小である。**
   根拠：`s1-brief.md:21`、`:23`、`verbatim-rulings.md:27`、`:94`、`:119`、`s2-plan-out.md:72`。
   `#define` 間接形には既測の貼り合わせが含まれる。g++-13 不在も既記録なので、新規性は今回の環境での再確認にある。一方、既測式でも exact argv・cwd・実 header 文脈を揃えた再測定は、旧記録の「既定 path」より射程を明確にする純増になりうる。

   **成果物への影響：** 式名や compiler 列数ではなく、今回新しく確定した環境・文脈・拒否箇所を純増として数える。

## 裁定パッケージ候補 (scope 外の real 所見)

- **legacy 分岐の compiler 引数の非対称。**
  根拠：`pipeline.py:1790`、`:2002`、`buildcache.py:3140`。
  checker の site 選択と legacy build の既定 compiler 使用は、静的に確認できる非対称である。今回の成果物では対象分岐の限定に使える。それ以上の到達可能性・既存防壁との関係の評価は別裁定候補であり、本 wave の実装修正案にはしない。

## 総括

計画は測定可能だが、**stdin の探索表、header 文脈の補助観測、内部 guard の拒否確認を合わせても、そのまま admission 実 pair 完了にはならない**。実 build の分岐・compiler・探索条件が対応した範囲だけを結論にできる。

静的検査のみ実施。書き込み・compiler probe・configure・pytest は実行しておらず、真偽差や checker の欠陥の存在は断定していない。