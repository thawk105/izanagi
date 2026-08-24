# Stage 6 review 裁定

- correctness cache-axis所見: real / scope内 / must-fix。genome, commit, trace, src token, admissionを固定し、cxx要求名だけの差でcache keyが分かれる正例を追加する。実compiler版横断digest保証には広げない。
- compiler realpath/versionがfocused receiptに無い所見: real / 証拠不足。コードfixでreceipt schemaを広げず、親が実在 `/usr/bin/g++-12` とversionを別証拠として記録し、最終受入は後段で取得する。
- leaf-nameだけのconsumer censusとnested decoy所見: real / scope内 / must-fix。qualified calleeを限定し、対象test function自身の実行scopeを歩いてnested function/lambdaを除外する。
- positional index表の未実効所見: real / scope内 / must-fix。対象呼出しをすべて明示 `cxx=cxx` keywordへ統一し、position表を削除する。signature一般検査は作らない。
- missing-define診断の `undef` 自己充足所見: refuted。完全defineの同compiler positiveが先に成功し、唯一の入力差がBACKOFF_FIXED除去で、macro名も同時必須。追加の行parserは新保証機構の過剰化。
- helperのg++-13-only/g++-only不足: real / scope内 / small fix。両module helperの4状態を表駆動する。
- docstring逐語過剰固定: realだが成果物影響なし / nit。今回のfix対象外。機械marker新設はscopeを越える。
- README旧node名: real / scope外。active T-1593所有を尊重し、段7前に再照合する。
- mocc fixture、selected cxxのcurrent/HEAD配線、13 pass/2 skip件数: refuted / fix不要。

一枚岩理由: cache test側とconsumer meta側は `test_campaign.py` の新しいcall形を `test_skip_classification.py` が固定する依存関係にあり、別fixで中間赤を作るため1 Codex fix単位にする。

fix後の期待: 対象9 node + meta全体が13 pass/2 conditional skipのまま。cache-axis正例が追加されるためmeta pass総数は増えうるが、対象9件の受理集合は不変。
