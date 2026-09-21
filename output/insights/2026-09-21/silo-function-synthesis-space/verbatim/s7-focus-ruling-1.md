# 焦点再レビュー 1 巡目の裁定 (2026-09-21 22:3x JST)

- 入力: codex review `codex/s7-review-A.md` (NO-GO、must-fix 8 + nit 1)、auditor 再確認 `codex/s7-auditor-focus.md` (adopt_with_conditions 維持、must-fix R1・R2、should R3〜R7、nit N1〜N6)。
- 判定: 全所見を real として採用する。どれも既に予定した文法・接続・probe・見積りの具体化で、新しい gate・台帳の追加を求めるものではない (両者が明記)。

| # | 所見 | 処置 (README の節) |
|---|---|---|
| r1 = U-R1 | bool・比較結果の `int` 昇格で signed overflow と負値 shift が残る。複合代入の右辺制約が未記載 | §2.7 を型付き規則に: 算術・bit・shift の各部分式の被演算子は U32 / U64 だけ、bool は `! && || == != ?:` と `static_cast` だけ、複合代入にも同じ右辺制約、shift 量は左辺型の幅未満の literal |
| r2 = U-R1 | 初期化子必須は初期化前読出しの排除でない (`x = helper(x)`) | §2.7: 初期化子の中で宣言中の変数を参照しない |
| U-R1 | `-fsyntax-only` では return 欠落が警告されない | §2.7: 非 void 関数の最後の文を `return` にする構文規則 (loop・goto がないので全経路で return する) |
| U-R2 | 代替綴り (`bitand` 等) と digraph (`<:` `:>` `%:`) で禁止を迂回 | §2.7: 字句段で全拒否、識別子は名前解決して許可先だけを指す |
| r3 | hole 境界 (namespace の外枠) と許可文法の producer / consumer 不一致、「変数を一切定義しない」の矛盾、列挙子・集約初期化・メンバ読出しが未明示 | §2.4: namespace の開き・閉じを marker 外の骨格に置き、implementation は本体だけ。§2.5 / §2.7: 「静的・thread 記憶域の変数を定義しない」、列挙子の完全修飾、`LockResponse{...}` の集約初期化の形、`s.` / `c.` のメンバ読出し、必須 3 関数はちょうど 1 つずつ |
| r4 | 成功通知 hook が C 段の検査から漏れた | §3.3: probe に成功通知の計数、配線解除の変異を 3 hook に、成功時に 1 回・失敗時に 0 回・次 txn で状態更新が見える焦点試験 |
| r5 | LLM×IR arm の生成経路が未記載 | §4 / §5: LLM×IR の coder は IR JSON (同じ schema) を出し、同じ IR admission と trusted renderer を通す。LLM×C++ の coder と別の出力形 |
| r6 = U-R6 | 状態射程の理由と「3 レンズ一致」の帰属が逐語を超える、auditor の型 3 の留保と txn 内支持が落ちた | §2.5 と fragment を各レンズの判定と親の推論に分けて書き直す。A6 (txn 内でも局所適応は表現できる) を明記、auditor の条件 9 (txn 内支持) と留保 (型 3 と組むと認証した経路と計測した経路が別になる) を明記、性能構成の verify を LLM×C++ の全候補に適用 |
| r7 | 単独 TU の自己試験「CC ヘッダを足せば負例が通る」は全件に成立しない | §3.3: 検査段ごとの自己試験に分ける (大域宣言を誤って公開する TU 変異 ↔ 大域参照の負例、マクロ供給を誤る変異 ↔ TRACE 参照の負例、型付き規則を外した構文検査器 ↔ 型負例) |
| r8 | C 段の合計と受入上限の出所・式が揃っていない | §6: 項目を揃える (評価 6 + 骨格負例 6 + 機構変異・probe 9 = 21 session、受入は前 wave の実績 1 回 (17:16:22→17:39:05、3 shard) から 3 shard が各 22.7 分ノードを占めたと仮定して 1.14 h)、合計 2.41〜4.12 h、「2 node 時間以上」の表記 |
| r9 (nit) | lock 漏れの timeout は読み手の到達が前提、上限削除の「等価変異」、build_admission の導出根拠 (:656-701)、B11 と permutation 負例の不整合 | §2.1 / §3.3 / §4 を訂正。permutation-erase は変更面に無関係なので負例から外す (B11 を採用) → 骨格負例は 3 × 2 方策 = 6 走 |
| U-R3 | 軸 ON の abort hook が `BACK_OFF` に従属 | §2.4 / §2.6: 軸 ON かつ `BACK_OFF != 1` を `#error` |
| U-R4 | 公平性の観測が機械 IR の系列で沈黙 | §3.4: 発火条件をコードの形 (単調増加の状態が待機上限・abort に至る経路) で書き、IR の系列も含めて endpoint 候補と勝ち候補に auditor の公平性目視を課す |
| U-R5 | lock 方策の見送りに既定ラベル | §3.4: 報告の既定で lock 方策を「verify 中の発火証拠なし」と表示、発火証拠を添えた場合だけ解除 |
| U-R7 | T3 見送りの前提と観測点 | §3.4: 型付き規則の後なら見送り妥当。C 段で 1 回だけ、手書き方策と契約負例に UBSan 付き単独 TU harness を login で回す (秒単位) |
| U-N1〜N6 | 文言の衝突、必須 3 関数の一意性、`std::min` / `std::max` の形、api header の単一正本、noipa、`LockResponse` の構築 | §2.4 / §2.5 / §2.7 に反映 (wrapper は `__attribute__((noipa))`) |
| U T5(d) 注 | timeout 前提は読みを含む workload | §2.1 / §3.3 に「読み手がその lock に到達する workload (legacy verify は RMW)」と明記 |

- 3 巡上限 (DW-O16) の 1 巡目。訂正後、codex focus 1 本で閉包を確認する。
