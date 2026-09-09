## real 所見

1. 正例の C++ 編集を解析した証拠が出力にも test にもない

   - 何が壊れるか: checker が `include/backoff.hh` の編集を丸ごと取り落としても、CMake から 2 macro を抽出して closure 参照を空にすれば正例が PASS し、負例 2 本も予定どおり FAIL できる。したがって正例 PASS が「全 hunk を region へ写した結果」と保証されない。
   - 根拠: `s2-plan.md:42-52` の JSON schema には、非交差だった編集領域や全 edit span の消費証拠がない。正例 test も `s2-plan.md:62-65` で rc、verdict、CMake macro、空の closure 参照しか固定しない。一方、正例の C++ 本体は `silo-backoff-fixed.patch:32-77` にある。
   - 具体的な反例入力: 現物 `silo-backoff-fixed.patch`。実装が誤って `cc/silo/transaction.cc` 以外の C++ edit span を捨てても、CMake leg だけで `PASS` でき、負例は両方 transaction.cc なので赤のままになる。
   - 直し方の方向: JSON に `classified_edits` と `unconsumed_edits` を出し、正例で `Backoff::backoff/1`、属性、file-scope guard の各 span が分類済み、未消費 0 であることを固定する。

2. 部分的な「transaction.cc 丸ごと扱い」を排除する対照が足りない

   - 何が壊れるか: `commit`、`writePhase`、`abort` だけを除外し、それ以外の同一 file 関数を過大に closure へ入れる実装でも全予定 test を通せる。`lockWriteSet` の depth 1 表示だけでは BFS による最小閉包を証明しない。
   - 根拠: closure の除外 test は `s2-plan.md:66-68,135-141` の名指し対象だけである。実体には validation から呼ばれない `read_internal` (`transaction.cc:243-283`) や `update` (`transaction.cc:524-555`) がある。
   - 具体的な反例入力: `read_internal()` の `while (expected.lock)` を `if (expected.lock)` に変える patch。定義された call closure では PASS すべきだが、`read_internal` を誤って closure に入れる粗い実装は FAIL し、それでも現在の予定 test には検出されない。
   - 直し方の方向: 同じ transaction.cc 内の非到達関数を触る PASS 用 decoy patch を加える。また `unlockWriteSet(iterator)` を触る depth 2 の FAIL patch も置き、再帰が表示だけでないことを固定する。

3. 「純 timing」の結論は判定式から導けない

   - 何が壊れるか: PASS が証明するのは Silo validation call graph との構文上の非交差だけであり、abort 側変更が timing だけであること、状態・制御・liveness を壊さないことは証明しない。brief が期待する D22 の根拠へ結論を持ち上げると過大主張になる。
   - 根拠: brief は `brief.md:5-11` で「純 timing」を研究上の結論に結び付けるが、判定式 `s2-plan.md:81-108` は region と raw macro token の交差しか見ない。`Backoff::backoff` は `backoff.hh:94-108`、その Silo 呼出しは abort 内の `transaction.cc:27-53` にある。
   - 具体的な反例入力: `Backoff::backoff()` 冒頭へ `throw 0;` を加える patch。validation closure とは交差せず予定式では PASS だが、abort 時にプロセス制御を壊し、純 timing ではない。
   - 直し方の方向: 今回の verdict を「Silo validation call-closure との構文的非交差」に限定する。純 timing を主張するなら、Backoff edit surface の許可操作、外部副作用、終了・例外・書込みを別検査する裁定パッケージが必要。

4. 共有 header の全 owner TU に対して証明を一般化できない

   - 何が壊れるか: patch は Silo 専用でなく、共有 `include/backoff.hh` と universal definitions を変える。checker は Silo の root TU しか解析しないため、結果を CCBench 全体や backoff 軸全体へ一般化すると層落ちになる。
   - 根拠: CMake define は全 protocol target へ配る構造 (`ProtocolHelpers.cmake:29-43`) で、共有 runner も `backoff.hh` を include する (`common/runner.hh:54-55`)。明示的な `Backoff::backoff` 呼出しは repo 内に 10 箇所あり、例として Cicada `cc/cicada/include/transaction.hh:166`、MVTO `cc/mvto/include/transaction.hh:134`、Oze `cc/oze/include/transaction.hh:146` がある。
   - 具体的な反例入力: 現物 `silo-backoff-fixed.patch` を Cicada、MVTO、Oze の証明にも用いる場合。checker はそれらの owner TU や経路を一行も解析せず同じ PASS を返す。
   - 直し方の方向: verdict に `owner_tus=["cc/silo/transaction.cc"]` と claim boundary を明記する。全 CCBench を主張するなら、全 owner TU と protocol ごとの validation/commit 経路を列挙する別裁定パッケージにする。

5. 「ccbench root 不在」の予定 test は現在の interface では構成できない

   - 何が壊れるか: 未初期化を空 closure とする退行を防ぐと記した branch が、実際には test されないままになりうる。
   - 根拠: repo root と source は checker 自身から固定導出する (`s2-plan.md:7-10`)。CLI は PATCH だけ (`s2-plan.md:43-47`)、`_invoke` も常に実 repo の CHECKER を使う (`s2-plan.md:58-60`)。これと「source dependency は stub しない」を保ったまま、`s2-plan.md:70-72,139` の root 不在を作れない。
   - 具体的な反例入力: 実配置から `external/ccbench` が欠落した状態。予定 test にはその状態を注入する経路がない。
   - 直し方の方向: CLI 固定 root は維持しつつ、内部の `analyze(repo_root, patch)` を分離し、存在しない root を渡す unit test と実 CLI integration test を分ける。

## refuted 所見

- 負例が patch 適用失敗で赤になる疑いは否定した。3 patch とも現物に対する `git apply --check` は rc 0 だった。これは pytest 緑ではなく、適用可能性だけの静的確認である。
- `norw` が既定 OFF のため消える疑いは、プラン上は否定できる。追加行は `broken-silo-norw-validation.patch:9-23` で、raw branch を残せば `validationPhase` (`transaction.cc:383-493`) の depth 0 region 内にある。directive を除いて両 branch を並べても brace は崩れない。
- `lockskip` の FAIL が例外由来になる疑いも否定した。追加行は `broken-silo-lockskip-validation.patch:9-17` で `lockWriteSet` (`transaction.cc:145-193`) 内にあり、root からの実 callsite は `transaction.cc:437`。予定機構なら depth 1 の region intersection が発火する。
- transaction.cc 全体を一領域にする単純な偽装は、`commit`、`writePhase`、`abort` の非包含 test により検出される。ただし real 所見 2 の部分的過大閉包は残る。
- 主な現物 anchor は一致する。`validationPhase:383`、`commit:706`、Silo の Backoff 呼出し `:47`、leader 呼出し `:720`、`transaction.hh:35-36`、`silo_op_element.hh:67-71`、`tuple.hh:30`、atomic/trace の各範囲に食い違いはない。
- 未適用 tree の `.cc/.hh/.h` に `BACKOFF_FIXED` と `BACKOFF_NOINLINE` が出現 0 件という実測も正しい。

## 親 brief への異議

- `brief.md:5` の `(D2)` は誤記で、`docs/decisions.md:403` が属する見出しは D22 (`docs/decisions.md:395`)。
- 同じ `docs/decisions.md:403` 内の古い `transaction.cc:517-540` と `:154-157` は現在の現物とずれている。現在の validation は `383-493`、lock の該当部は `145-193` である。
- 「Backoff 呼出し 1 箇所」は `brief.md:40` の文脈どおり Silo transaction.cc 内に限れば正しい。しかし共有 patch の到達面へ一般化すると誤りで、CCBench 全体には明示呼出しが 10 箇所ある。
- 「patch が触る file は 2 本」「変更関数は Backoff::backoff 1 本」「新 macro のコード出現 0 件」は再確認でき、異議なし。
- 標準 CMake 経路については universal definitions が protocol targets、Silo replay test、SS2PL test へ供給されており、具体的な供給漏れ target は今回の静的調査では見つからなかった。

## 総括

負例 2 本は予定機構の depth 0 / 1 分岐へ実際に到達する。  
ただし正例の全編集消費、部分的過大閉包、純 timing への昇格、共有 owner TU の一般化には歯が足りない。  
pytest は実走しておらず、緑とは報告しない。