## must-fix

成果物の予定 README は未作成だったため、以下は**これから採用する文面への必須修正**であり、既存成果物に違反があるとの判定ではない。根拠は段 4 裁定、親の `probe-login-parent.json`、checker 本体、既存 T-148 記録。

1. **「checker と実 build の真偽差」は、再構成した stdin 列間の観測へ限定する。**
   根拠：`g++/atomic-quote`・`root-quote`・`system-quote` は checker ２列で `value=0, rc=0`、`build-search-reconstructed` で `value=1, rc=0`。ただし configure は全10回失敗し、両探索列の入力は stdin。`build-header` も `/tmp` の補助構造で、元の TU・先行 include・実 header 位置を再現していない。段 4 の S-1／S-3 が適用される。
   **成果物への影響：** 「記録した stdin fixture の checker 列と再構成探索列で 0/1 を観測」とし、「実 build の枝が逆転」「admission 実 pair を確認」は削る。

2. **angle の preprocess error を偽値や checker の欠陥へ変換しない。**
   根拠：`g++/system-angle` の checker ２列は `value=null, rc=1`、診断は `no include path in which to search for vector`。`source_digest.py:372-373` の「常に 0」はこの観測を説明できない。一方、preprocess 非ゼロは例外になり、guard の拒否と同様に fails-closed 側である。
   **成果物への影響：** 「コメントの一律な説明と観測が一致しない」と記載し、表は `error(rc=1)` とする。受理集合の破れ・偽 cache hit・checker の欠陥とは書かない。

3. **guard 件数を resolver 到達例へ昇格させない。**
   根拠：500件の内訳は条件演算子拒否204、define演算子拒否60、貼り合わせ拒否20、受理36、`other_error`180。実施したのは `_assert_conditional_macros_covered` への fixture 直呼びである。条件演算子の拒否前にも環境マクロ照会があり、前段失敗は専用拒否と異なる。走査対象は３ファイルで非再帰。
   **成果物への影響：** 「渡した fixture に対する拒否箇所別件数」と明示し、「実 variant 204件を resolver が遮断」「全500件で guard 発火」「族全体が安全」は使わない。

4. **requested name 数を独立 compiler 数と数えない。**
   根拠：`g++`／`g++-11` は realpath と sha256 が同一。`g++-9` は今回の `-std=c++20` で評価不能、`g++-13` は login の探索範囲で不在。
   **成果物への影響：** 列名は保持して別名を注記し、DW-G03 の独立２例に数えない。g++-9 は「今回の argv では真偽未取得」とし、「差なし」「演算子非対応」としない。

5. **純増を「未測の式を追加」「compiler を追加」で数えない。**
   根拠：既存 T-148 の `review-focus-claude-closed-partial-table.md:15` に貼り合わせ形の明示的0/1、`review-B-codex-layers-and-test-teeth.md:59` に literal 間接形、同`:101` に `<atomic>` の preprocess error がある。ただし当時の反例記録は、現行 guard の拒否発火実測とは異なる。段 4 §2-(2) は exact な条件・文脈・拒否箇所・compiler 対応を純増の単位に定める。
   **成果物への影響：** 「間接形・angle・system header を初めて被覆」「既存は１式だけ」「g++-13 不在を初発見」は避け、今回の環境記録と現行拒否箇所の確認を差分として示す。

6. **login 観測を admission toolchain の結果へ読み替えない。**
   根拠：親 JSON の hostname は `pegasus02`。compute は `environment_unavailable` の placeholder。対象 admission の呼出しは供給されておらず、compiler sweep は明示指定による。compute で generic 実行できても、本番 admission との対応は別途未証明である。
   **成果物への影響：** 「admission toolchain で実測済み」「compute にも g++-13 が無い」は削り、未測範囲を明記する。

7. **対照の部分成立を、全体の結論成立へ読み替えない。**
   根拠：g++／g++-11／g++-12 は各164件すべて成立。g++-9／g++-13 は各156件不成立・8件成立で、全体は508/820成立、`controls_passed=false`、`conclusion=null`。段 4 §3-(7)・§4 は不成立時の結論保留を明記し、部分集合による完了認定は明示していない。
   **成果物への影響：** 成立した３列の値・診断・対照成立は観測事実として書けるが、全体の結論・完了認定は保留する。

   不成立は別 compiler に局在しているため、成立列の観測まで「無効」「何も分からない」とするのは過小評価。一方、結果を見てから不成立列を除き「対照成立、結論確定」とするのは裁定の緩和になる。**限定観測の記載は可、wave 全体の結論は保留**が現裁定に沿う。

## nit

- **「docstring」より「コメント」が正確。**
  根拠：`:372-373` は `#` コメント。ただし guard の docstring・拒否診断にも「header 未発見 = dead 枝」という説明がある。
  **成果物への影響：** 引用元を「コメント」とし、拒否診断の説明文を今回の真偽実測の証拠として扱わない。

- **2002 cells を2002件の真偽実測と呼ばない。**
  根拠：末尾２件は compute 未測 placeholder。他にも preprocess error・compiler 不在が含まれる。
  **成果物への影響：** 「2002セルの記録」と表記し、真偽取得・エラー・不在・未測を区別する。

## 成果物に書いてよい文・書いてはいけない文

| 書いてよい文 | 書いてはいけない文 |
|---|---|
| pegasus02 の記録した条件で、quote ３ケースの stdin fixture は checker 列で0、再構成探索列で1だった。 | checker と実 build で真偽が食い違うことを実証した。 |
| angle ケースは checker 列で preprocess error となり、真偽値を取得しなかった。 | angle も checker では0になる。 |
| 「常に0」というコメントは今回の angle 観測と一致しない。受理集合の破れは未証明である。 | コメントと違うため checker の欠陥が確定した。 |
| 実 guard 関数は、渡した fixture に対して条件演算子の拒否点で204件拒否した。 | resolver が実 variant 204件をこの拒否点で遮断した。 |
| g++ と g++-11 は同一実体への別名だった。 | 独立した２ compiler で再現した。 |
| g++-9 は今回の argv では真偽未取得だった。 | g++-9 では食い違いがなかった。 |
| 成立列の限定観測を保存した。全体の対照は不成立で、結論は保留する。 | 不成立列を除けば全対照成立なので実 pair 検証は完了した。 |

compute が測れなかった場合の記載例：

> compute の実測結果は取得できなかった（理由は実際の投入・実行記録に記載）。当該セルは `environment_unavailable` とし、compiler の有無・真偽・拒否結果は未確定とする。
> 本表の観測は login node pegasus02 に限定され、admission toolchain の実 pair 実測完了を意味しない。

## 裁定パッケージ候補 (scope 外の real 所見)

- **既裁定 R-1：legacy 分岐の compiler 引数の非対称。**
  根拠：段 4 §6 が静的確認済みの非対称として採用している。
  **成果物への影響：** 対象 admission の分岐を特定しない compiler sweep を、本番との対応証明に使わない。今回、新たな到達証拠は得ていない。

- **既裁定 R-2：非再帰走査の境界。**
  根拠：`EVOLVE_BLOCK_SOURCES` の３ファイルのみを走査し、normalize は include 行を除去する。
  **成果物への影響：** include 先一般の安全性を主張範囲から除く。許可された variant からの別挙動・stock identity 継承は未証明のままとする。

いずれも checker 変更、受理集合変更、新規 gate・検査・台帳・恒久 test の提案には進めない。

## 総括

**記載できるのは、exact な login 条件下の値・診断・fixture 拒否箇所と、未測範囲である。** 実 build／admission の真偽差、欠陥、安全性、全体の検証完了は今回の証拠から確定できない。

静的レビューと保存済み JSON の集計のみ実施。ファイル書込み、テスト実走、commit・push は行っていない。