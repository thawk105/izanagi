## 所見 (real 候補)

**P1 の prefix 除去自体に破綻は確認できなかった。ただし、修正後にも別プログラムを同じ identity にする具体的経路が残る。** 以下の実測は pegasus02 の GCC 11.4.0／12.3.0 による stdin 前処理であり、pytest・実 TU・製品経路の実走ではない。

**A-1 — include と指令の相対位置が失われ、異なる variant 同士が衝突する。**

- **根拠:** `source_digest.py:381,1662,2140`、`external/ccbench/cc/silo/transaction.cc:5`、同 `include/atomic_tool.hh:15`、`s2-plan-out.md:289`。
- **real と主張する理由:** 次の二つは include 行列が同じであり、include 除去後の `-dD` 出力も両 GCC で一致した。

  ```c
  // A
  #define desired expected
  #include "include/atomic_tool.hh"
  #undef desired

  // B
  #include "include/atomic_tool.hh"
  #define desired expected
  #undef desired
  ```

  実 include では A だけが header を書き換える。これは M4 の「stock との衝突」を修正しても、別 variant との衝突が残ることを示す。M4b の CAS 置換でも同じ構造になる。allowlist・include 一致・条件マクロ検査は相対位置を検査しない。

  **prefix を剥がす前から一致するため、P1 が新しく作る欠陥ではない。** 全 file の実 `resolve` は未実走だが、消去処理と現物 header による静的な成立根拠がある。
- **是正案:** **scope 内:** 「登録済み M4／M4b と基準 template の区別」を修復範囲として記述する。**scope 外:** 相対位置の情報消失そのものの解消。今回、別方式や gate の追加は提案しない。

**A-2 — macro stack の保存時点が異なっても、`-dD` 出力が一致する。**

- **根拠:** `source_digest.py:1663,1857,2109`、`external/ccbench/include/backoff.hh:12`、`external/ccbench/cc/silo/transaction.cc:278`、`s2-plan-out.md`「親 brief への反論」項 4。
- **real と主張する理由:** `-DSLEEP_READ_PHASE=0` で、次の A を前処理した。

  ```c
  #pragma push_macro("SLEEP_READ_PHASE")
  #undef SLEEP_READ_PHASE
  #define SLEEP_READ_PHASE 1
  #pragma push_macro("UNUSED")
  #pragma pop_macro("SLEEP_READ_PHASE")
  int a;
  ```

  B は二つの `push_macro` の名前を交換する。両 GCC で **A/B の `-dD` 出力は完全一致**した。出力には共通の define/undef と空白行が残るが、復元した値は記録されない。末尾へ `int later=SLEEP_READ_PHASE;` を追加すると、A は `0`、B は `1` になった。

  backoff 本文はこのマクロを使わず、後続 silo 本文は使う。したがって、backoff の include 後にこの対を置くと、独立前処理では区別できず、実 TU では効果が分かれる構造になる。条件検査でもこの名前は実供給済みである。これは単なる「pragma 未検証」より強い具体的反例候補。ただし pin 全文への適用・TU 実走は未実施。
- **是正案:** **scope 内:** plan の「GCC 出力未実測」をこの断片実測で補い、「任意のマクロ状態操作を被覆する」と書かない。**scope 外:** macro stack に関する区別不能の解消。裁定 (a) を取りやめる理由や、限界記載だけで修復を代替する提案にはしない。

**A-3 — trace 検査の式は不変でも、受理集合は不変ではない。**

- **根拠:** `source_digest.py:2163,2168,2202,2436`、`s1-brief.md:14`、`s2-plan-out.md:95`。
- **real と主張する理由:** 次の未使用マクロ操作は本文の展開結果を変えない。

  ```c
  #if TRACE
  #define T2731_UNUSED 1
  #undef T2731_UNUSED
  #endif
  int a;
  ```

  両 GCC で、旧正規化の TRACE 差分は空。新正規化では次が追加された。

  ```text
  +#define T2731_UNUSED 1
  +#undef T2731_UNUSED
  ```

  HEAD にこの操作がなければ、旧 trace 検査は通過し、新 trace 検査は RuntimeError になる。無害な template 編集でも起きる受理変更である。

  **これは `resolve()` 自体の拒否ではない。** `resolve:2436` は trace 検査を呼ばず、別 token を返す経路である。coder の生指令は既存の HOLE_ESCAPE に別途拒否される。
- **是正案:** **scope 内:** 「述語不変」は比較式 `D_variant == D_stock` の維持と限定し、受理集合まで不変と書かない。**scope 外:** 任意の無害な指令を識別して除外する処理。規律 2 を緩める除外案は提案しない。

## 親の実測値の一般化

**A-4 — prefix の局所的健全性は支持できるが、全文・全 compiler の byte 同一性までは実証されていない。**

- **根拠:** `s1-brief.md:7`、`s2-plan-out.md:19,84,93`、`source_digest.py:370,1662,1683,1698,2071,2085`、`buildcache.py:1863`。
- **real と主張する理由:** 今回の追加断片実測は以下のとおり。

  | 入力 | 結果 |
  |---|---|
  | command-line と同名同値の再定義 | prefix 後に source の define が残る |
  | builtin を undef 後に再定義 | 両指令が残る |
  | `__COUNTER__` 2 回 | 本文は `0,1`、prefix 一致 |
  | `__DATE__`／`__TIME__` | 展開値は本文側、prefix 一致 |
  | push/pop／`GCC system_header` | prefix 一致。後者は stdin では警告付きで無視 |
  | undef 後の `#if BAR` | 従来どおり `-Werror=undef` で失敗 |
  | 未定義名の単独 undef | 指令が残り、正常終了 |

  同文の source define が prefix 末尾に続いても、`removeprefix` は環境部分を一度だけ除去する。剥がしすぎ／剥がし残しは確認できなかった。現行 argv に `-imacros` はなく、通常 include は `_INCLUDE_RE` で除去される。

  現物の対象 3 file・Options・silo CMake は pin `511c953` との差分がなく、対象 3 file に define/undef はない。template も同様。既存 `#pragma once` については、断片で旧出力と prefix 除去後の新出力が一致した。ただし全文と実 defines の組合せ比較は未実行。

  compiler ごとの predefined 行数・順序の違いは、それぞれの同一 argv の prefix を取るため吸収される。残る本文の空白・展開差は compiler 間の digest 差になり得る。**同じ cxx を使う compute/baseline の stock 比較と、異なる compiler 間の token 一致は別の保証**である。T-2630 の計算ノード実測 compiler は login と同じ GCC 11.4 だった（insight README:76）が、将来まで固定とは言えない。
- **是正案:** **scope 内:** F-4 を対象 pin・template・compiler 条件付きの予測とする。plan:93 の限定は妥当。

正常な実 file の編集だけで `startswith` が不成立になる正例は**無し**。具体的に不成立となり得るのは、cache 取得後に同じ `cxx` 名の実体・wrapper 設定や BUILD_FLAGS が変わり、環境出力が変化する場合である。現行運用でその発生は確認していない。未知条件や供給漏れによる既存 RuntimeError と混同しない。

## 不変条件と規律 7

**A-5 — P2 は恒真ではない。golden 不変でも identity 関数の変更は残る。**

- **根拠:** `s2-plan-out.md:260,271,282`、旧 `mutation-spec.json` の M3a／M3b／M6、insight README:94、`test_campaign.py:11051,11078`、`verbatim-rulings.md:25`。
- **real と主張する理由:**

  | 条件 | 判断 |
  |---|---|
  | inert template = stock | 支持。追加供給は `BACKOFF_FIXED` **と `BACKOFF_NOINLINE`**。各自の環境 prefix を除けば source 本文の一致を保つ設計 |
  | compute == baseline ⇔ 同一 pre-image | SHA-256 衝突を除く前提で維持。「同じ実プログラム」との同値ではない |
  | CONTEXT_MACROS | `GLOBAL_VALUE_DEFINE=1` の command-line 行は当該文脈の prefix として除去。文脈タグと本文差は残る |
  | M6 の trace 検査 | source の同じ undef/define が両 TRACE 値に現れるため、既存 M6 の通過予測は妥当 |
  | nm／HOLE_ESCAPE | 変更対象外。M6 の binary 検査実走済みとは言えない |

  recipe の期待集合には明確な検出力がある。

  | 変異 | 修正前の署名 | v2 の予測 |
  |---|---|---|
  | M3a | N2b | N1b＋N2b |
  | M3b／M4／M4b／M6 | N2a＋N2b | 全 4 node |
  | M0 | 空集合 | 空集合 |

  したがって旧 HEAD に v2 spec を当てれば期待不一致になる。新 unit test も plan の A/B/F/H が旧 identity を検出し、G は新しい停止契約を検出する。**単に KILLED だったことではなく、失敗 node と赤理由の一致が必要**である。全 4 node は resolve の一律失敗でも得られるため、「別 identity を返した」という観測を省略してはいけない。

  `_GOLDEN_VID` は canonical genome の ID、pre-refactor golden は固定文字列の結合ハッシュであり、これらが不変でも正規化の互換性を単独では証明しない。今回変わるのは、source 指令を含む入力間の同値関係である。
- **是正案:** **scope 内:** 段 4 の事前登録を維持する。既存 stock／指令を含まない template variant の記録を一律無効化する根拠はない。一方、golden 不変を理由に裁定済み再検証を省く読みは成立しない。対象記録の無効化と、identity 実装の再検証を分ける。

## 主張の限定 (書いてよい / 書いてはいけない)

以下の肯定形のうち修正後の成果を述べるものは、親の実走結果が一致した後に使用する。

| 書いてよい | 書いてはいけない |
|---|---|
| 「登録済み M3b／M6 は stock と別 identity になった」 | 「file 間のマクロ効果をすべて identity が被覆した」 |
| 「登録済み F1016 の衝突を修復した」 | 「F1016 の原因となる非再帰境界を全面的に閉じた」 |
| 「M4／M4b を基準 template と区別した」 | 「include と指令の相対位置も区別する」 |
| 「対象 stock／template の token は維持された」 | 「全既存 variant・全 compiler で token 不変」 |
| 「M6 は trace 差分検査を引き続き通過し、nm 層が残る」 | 「今回の probe が最終 binary の nm 拒否まで確認した」 |
| 「有限 matrix の期待署名が一致した」 | 「mocc・pragma・computed 系に残存経路はない」 |
| 「同名同値の source 再定義も別 identity にする」 | 「意味的に同じプログラムは必ず同 identity」 |

A-1／A-2 は、一般的な不存在を主張できない理由を具体化する所見である。裁定 (a) の実装を限界記載で代替してよい、という意味ではない。

## 親 brief への反論

- **P1:** 採用を覆す prefix 破綻は無し。source の再定義を残す方法として妥当。
- **F-3:** BACKOFF_NOINLINE の追加供給も含める。plan は訂正済み。
- **F-4:** 対象を限定すれば支持するが、「指令数ゼロ」だけから全文の byte 同一を実測済みとしない。plan:93 の留保を brief にも反映する。
- **不変条件:** trace の比較式と受理集合を区別する（A-3）。M6 の通過予測だけでは全入力の受理不変を証明しない。
- **完了主張:** 登録済み衝突の修復と、identity の全面的健全性を分ける。A-1／A-2 が後者への反例候補となる。
- **規律 7:** 記録済み測定の一律無効化は導かないが、事前登録済み再検証は必要。

## 総括

**裁定 (a)＋P1＋P2 は進められる。ただし「F1016 の全面閉塞」「trace 受理集合不変」は支持できない。** include 相対位置と macro stack に具体的な区別不能が残る。修正範囲の説明に反映し、登録済み変異の修復と混同しないこと。

書き込み・commit・push・pytest は行っていない。GCC 断片実測と静的検査による所見である。

全文＋template の追加比較コマンドは、自動承認レビュー（`guard_bash`）が拒否した。理由は保護対象 `external/ccbench` と heredoc を含む構文を分類不能としたためで、この比較結果は未取得である。