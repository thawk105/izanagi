## 段 3 反例が塞がったか

結論は「元の 2 例そのものは塞がったが、反例の型は塞がっていない」です。

裸の `"/srv/ccbench"` は `requested_root + b"/"` に一致せず、`"/srv/ccbench-v2"` も一致しないため、段 3 の逐語例は赤になります。しかし、閉包 member と同じ path を通常の意味文字列に使えば、置き場所由来でない差が緑になります。

具体例:

```python
requested_source_root = b"/srv/ccbench"
control_source_root = b"/srv/ccbench/stock"

requested_dependency_identities = frozenset({
    "source/cc/silo/transaction.cc",
    "source/include/probe.hh",
})
requested_root_dependent_builtin_paths = (
    "source/cc/silo/transaction.cc",
)
control_root_dependent_builtin_paths = (
    "source/cc/silo/transaction.cc",
)

requested = (
    b'static constexpr const char *semantic_mode = '
    b'"/srv/ccbench/include/probe.hh";\n'
)
control = (
    b'static constexpr const char *semantic_mode = '
    b'"/srv/ccbench/stock/include/probe.hh";\n'
)
```

`transaction.cc` のコメントまたは inactive branch に `__FILE__` があるだけで builtin tuple は非空になります。raw token 検索だからです（[condition_meaning_gate.py:2028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2028)）。一方、`semantic_mode` の候補は `source/include/probe.hh` と閉包一致し、requested root が置換されます（[condition_meaning_gate.py:2300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2300)）。結果は `replacement_count=1`、`has_residual=False`、builtin 非空なので green です（同:2331）。

これは実行時に観測可能な通常の文字列リテラル差であり、builtin 展開由来ではありません。閉包 membership は「その名前の依存 file がある」ことしか証明せず、「この出力 span がその file の `__FILE__` 展開である」ことを証明していません。

成果物影響: 意味の異なる個体が supply green になり、meaning arm が別の限定 witness を通れば certified selection の受理集合へ入り、材料レポートと試行台帳が誤った green record を参照します。

正例については、置換ゼロで新 reason が緑になる経路はありません。分類器と validator の双方が `replacement_count >= 1` を要求しています（同:2335、[同:3539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:3539)）。正例テストも正の値を確認しています（[test_condition_meaning_gate.py:645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/tests/test_condition_meaning_gate.py:645)）。ただし、その置換が目的の `__FILE__` span だったことまでは確認していません。

## 置換許可条件の穴

- **must-fix: 字句正規化は「実際に閉包 file を指す」を保証しません。** 空成分と `.` を無条件に捨て、`..` を stack 操作だけで処理しています（[condition_meaning_gate.py:2307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2307)）。例えば次は `source/include/other.hh` が閉包にあれば緑になります。

  ```python
  requested = (
      b'const char *semantic = '
      b'"/srv/ccbench/include/probe.hh/../other.hh";\n'
  )
  control = (
      b'const char *semantic = '
      b'"/srv/ccbench/stock/include/probe.hh/../other.hh";\n'
  )
  ```

  `probe.hh` が通常の file なら、この path はそこから `..` を辿れない不正 path です。それでも字句上は `include/other.hh` へ畳まれます。末尾 `/` も空成分として消されるため、通常 file の `include/other.hh/` も member と一致します。先頭へ出る通常の `..` は `escapes_root=True` になるので、その限定では反証なしです。symlink を含む場合も字句結果と実際の参照先は一致しません。

- **must-fix: `path_bytes` は token 全体ではなく member 接頭辞を許可します。** `@`、`=`, `%`, `~` など POSIX file 名に使える byte が集合外で、そこで走査を止めた後の境界検査がありません（同:2283-2306）。また、root の直前にも token 境界条件がありません。次は `source/include/probe.hh` が閉包 member なら green です。

  ```python
  requested = (
      b'const char *semantic = '
      b'"tag:/srv/ccbench/include/probe.hh@policy";\n'
  )
  control = (
      b'const char *semantic = '
      b'"tag:/srv/ccbench/stock/include/probe.hh@policy";\n'
  )
  ```

  分類器は `tag:` 内部から root を見付け、`@` の直前までだけを閉包照合します。全 token は root 起点の閉包 path ではありません。

- **must-fix: control 側の対応 file は検査されません。** helper は requested closure identity しか受け取らず（同:2256）、validator は両 closure の形式を検査しても、置換対象 `rel` が control closure に存在することを要求しません（[同:3508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:3508)）。上の `probe.hh` が control closure に存在しなくても green です。

- `startswith` の同一位置二重消費については反証なしです。root の空は事前拒否され、成功時も `index` は root 長だけ必ず増えます。出力 buffer も再走査されません。suffix 内に別の root があれば別の非重複位置として置換され得ますが、同一位置の再消費ではありません。

- `decode("ascii")` 失敗については反証なしです。`relative_bytes` は ASCII byte だけから成る `path_bytes` で切られるため、当該 decode は失敗しません。

- requested root が control root の子である逆向きの入れ子について、走査と再置換には反証なしです。`/srv/ccbench/patched` から `/srv/ccbench` へ置換しても、生成された出力は再走査されません。なお capture は相異なることしか要求せず、入れ子自体は許可します（[同:747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:747)）。この向きでも、通常の semantic literal を閉包 member と誤認する上記の穴は残ります。

成果物影響: 上記 3 つの許可条件の穴はいずれも、本来 red の supply record を green に変え、certified selection、材料レポート、試行台帳の値と参照を広げます。

## 負例の単一理由性

| 負例 | 現在の値 | 1 条件ずつ無効化した結果 | 判定 |
|---|---|---|---|
| semantic difference | replacement 正、builtin 有、residual 有 | residual 判定だけを無効化すると green。他の無効化では red | 単一理由 |
| outside closure literal | real `__FILE__` により replacement 正、builtin 有。閉包外 literal が residual | membership 制限を無効化しても green。residual 判定を無効化しても green | 厳密な意味では非単一 |
| builtin なし | replacement 正、residual 無、builtin 無 | builtin 非空要求だけを無効化すると green | 単一理由 |

outside-closure 負例（[test_condition_meaning_gate.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/tests/test_condition_meaning_gate.py:701)）は、membership 拒否が residual を発生させるという単一の因果鎖にはなっています。ただし、依頼どおり各条件を個別に無効化する機械的基準では、membership と residual の 2 変更がそれぞれ green を作るため、M1 専用の正例対照ではありません。

さらにこの負例は、閉包に全く無い `not-a-dependency.hh` しか検査しません。閉包 member と同じ接頭辞を持つ semantic literal、`@policy` など集合外 byte を伴う token、無効な `file/../other` は被覆していません。

成果物影響: 非単一性それ自体は現時点の受理集合を変えないため nit です。ただし、未登録の閉包 member semantic literal は前節の material な誤受理を残します。

## 赤へ倒れない箇所

- 上記の閉包 member semantic literal、member 接頭辞 token、不正な字句 path は、想定外入力を red にせず green にします。規律 2 への実質的な反例です。
- root が空、LF/CR を含む場合は明示的に red 相当を返します。反証なしです（[condition_meaning_gate.py:2261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2261)）。
- 行数差、置換後の 1 byte 以上の残差、置換ゼロはいずれも新 reason では red です。反証なしです。raw bytes 完全一致だけは既存の `stock-inert-preprocess-identical` として置換ゼロでも green ですが、分類器へ入らない意図された別契約です（同:2546）。
- `decode("ascii")` の例外は構成上到達不能です。production の exact type 入力について、他に具体的な分類器例外は見付かりませんでした。反証なしです。
- red record の 4 field は digest 計算前に追加され、record digest はその evidence 全体から作られます（[同:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:940)）。検証時も同じ payload から再計算されます（[同:3867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:3867)）。内部不整合はありません。旧実装と比べれば同じ red 観測の digest/id は変わりますが、evidence 拡張による正規の変更です。
- `comparison` の上書きは location-only green の直前だけです（同:2577）。既存の identity green は更新前に return し、requested/default green も非 inert 分岐で return します。既存 2 reason の evidence 汚染には反証なしです。

## 親裁定への反証

親裁定の「`source/<rel>` が requested closure に実在すれば、その path は実際に閉包 file を指す」という推論は反証されます。実装が証明するのは正規化後の文字列 equality だけです。出力 span の生成元、token 全体の境界、control 側の対応 member、実 filesystem 上の参照先を証明していません。これは親裁定 4.2 の許可条件そのものの誤りです。

成果物影響: この裁定を維持すると、D1523 が却下した「誤った畳み方で意味差を隠す」事故が新 reason の下で再現します。

build root を除外した判断については、現行 CCBench での具体的な artifact path または計測 ID を、射影資料からは確認できませんでした。したがって現在の実運用に対する反証なしです。

条件付きの false red 経路はあります。requested/control build は実際に別 root で構成されるため（[同:1758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:1758)）、build tree の生成 header が active `__FILE__` を展開すれば、差は build root だけでも residual になります。ただし親裁定はこの可能性を認識した上で、既存到達例が無いとして除外しており、新しい反証にはなりません。

条件付き成果物影響: その生成 header が将来到達すれば、本来同じ inert 個体が red のまま残り、certified selection と後続レポート、台帳が作られません。

## must-fix 一覧

1. 閉包 membership を builtin 展開 provenance の代用にしないこと。各置換 span を active な `__FILE__` または `__BASE_FILE__` の compiler observation に束縛できなければ red に倒す必要があります。
2. 少なくとも token 左右境界、集合外 byte 後の prefix acceptance、末尾空成分、通常 file を跨ぐ `..`、control closure member の不在を red にすること。ただし、これだけでは通常 literal と builtin 展開の区別は直りません。
3. 「実在する閉包 member を指す semantic literal + inactive/comment の `__FILE__`」を red にする負例を追加すること。`@policy` 接尾辞と `probe.hh/../other.hh` も独立した負例が必要です。
4. M1 負例について、membership 拒否と residual の構造的結合を明記し、「各条件を個別に無効化しても M1 だけが反転する」という単一理由性の主張は修正すること。

## 総括

正しさ境界では差し戻しです。元の裸 root 反例は塞がりましたが、「閉包 file と同じ名前を持つ bytes」と「builtin が生成した path span」の混同が残っています。具体的な preprocess bytes で意味差を green にできるため、D1523 の禁止条件はまだ満たしていません。

親実測の 94 件、個別 6 件、consumer 692 件が green でも、この反例群は既存テスト入力に含まれていないため反証にはなりません。pytest の再実行は求めません。