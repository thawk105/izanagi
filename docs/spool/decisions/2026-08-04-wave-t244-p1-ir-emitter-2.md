---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: wave-t244-p1-ir-emitter
seq: 2
---

## {{D:reflux-ir-p1-component}}. D121 P1 の機械部品は「独立 golden を先に凍結する順序」で監査し、P1 充足とは名乗らない

**背景:** D121 決定 (7) の前提条件 P1 は「候補表現が固定 5-bit IR に閉じ、正準 emitter が
全 32 mask で監査済み」である。同 D 自身が「emitter は自己参照だと恒真なので独立 golden が要る」と
書いていたが、独立 golden をどう得るかは未設計だった。

**決定 (1): campaign 記録と凍結 freeze を独立 anchor に数えない。** 段 3 の敵対 2 レンズが
独立に指摘し、親が実測で裏取りしたとおり、証拠の系譜は
`predicate_for` → campaign provenance (`_write_provenance` が `candidates()` の出力を格納) →
freeze (`_trigger_entries` が provenance を複写) → `s1_expected_goldens` (freeze から転記) の
**一本**である。これらは「歴史的 materialization の記録」であって独立な期待値ではない。
点数として加算してはならない。

**決定 (2): 独立性は「順序」で担保する。** 実装子を所有分離した 2 体・直列とする。
① 子 G が golden 台帳だけを書く (旧 emitter・campaign 記録・freeze・既存 golden・未作成の leaf を
読むことを禁止し、規範仕様と骨格 patch だけから導出させる)、② **親が emitter 実装前に
golden の sha256 を凍結記録**、③ 子 E が golden 非参照で emitter を実装する。
**主張してよいのは「完全 blind」ではなく順序保証**である — 恒真化 (emitter から golden を
生成すること) が構造的に起きていないこと、golden の hash が実装後も不変であることまでを言う。

**決定 (3): 規範仕様の正本は骨格 patch とし、順序規則は親が宣言する。** C++ の代入先変数・
要因変数・enum 型名・sentinel を含む 6 member は
`patches/silo-backoff-trigger-gating-variant.patch` が正本である。
選言の並び (sentinel を先頭に固定し、続けて要因定義順) は**親が段 4 で宣言した規則**であり、
軸定数の定義順に由来する。旧実装との一致は差分結果であって恒真ではない。
テストは patch を読んで token の実在を検算し、patch 単独の drift も検出する。

**決定 (4): 拒否は単一例外型・固定文言とし、`__context__` も残さない。** D121 決定 (3) の
「強制は 0 bit」を leaf の API 契約として実装する。型不正と値不正を例外型で区別しない。
メッセージへ入力本文・長さ・位置・失敗種別を入れない。`except` の中で送出すると
元例外が `__context__` に残るため、ハンドラを抜けてから送出する。
テストは全拒否入力について型・`str`・`repr`・`args`・`vars`・`__cause__`・`__context__` の
一致を、二重 import 経路の両方で検査する。

**決定 (5): sink は毎回 mask を再検証し、型同一性だけに依存しない。** frozen dataclass は
unforgeable ではなく、`object.__new__()` / `object.__setattr__()` で exact 型のまま範囲外 mask を
作れる。また本 repo は 2 つの import 形を支えるため `type() is` は同値な値を誤って拒否する。
`isinstance` で受けたうえで mask の不変条件を毎回再検証することで、両方を 1 つの是正で閉じる。
`mask` 取得の失敗は例外の種類を問わず固定拒否へ畳む (subclass の property が任意の例外を
投げうるため)。

**決定 (6): P1 を充足したとは名乗らない。** P1 は「候補表現が閉じる」かつ「emitter が監査済み」の
連言であり、本 wave は production へ wiring しないため前者が偽である。台帳には
**P1 未充足・production 到達性ゼロ**と書く。実装してもなお cap-lift は FAIL であり、
D114 の承認上限 1 は変わらない。P2 / P3 / P5 / P7 / P9 / P10 も本 wave では充足しない。
wiring は受理集合の縮小なので、その時点で D96 手続 (新しい設計判断の記録と境界テストの
同一変更単位での更新) が要る。

**決定 (7): 検出力を入力点数で数えない。** 独立な証拠系譜は 2 系譜 (別所有・実装前 hash 固定の
literal golden と、既存別実装との全点差分) である。32 は入力点数であって vector 数ではない。
静的な fault-class vector 数で会計する。

**却下した選択肢:**

- 単一の実装子が golden と emitter を同時に書く — 監査が恒真になる (段 3 の中心所見)。
- leaf が既存 emitter を呼ぶ — 差分照合が自己比較になり、凍結 pin 済みファイルへの依存も増える。
- campaign 記録と freeze を独立 anchor として点数に加算する — 系譜が旧実装へ収束する。
- 本 wave で production へ wiring する — 受理集合の縮小であり、consumer 閉包と D96 手続を
  同一変更単位で満たす必要がある。ユーザーが指定した「新規 leaf に閉じる」scope にも反する。
- 「JSON 由来の入力を拒否する」と契約に書く — decode 後の文字列は通常の文字列と区別できず、
  実装不能な受入条件になる。拒否できるのは非文字列・container・封筒付き text・非正準文字列までである。

**研究状態への影響:** production 挙動、実験の受理集合、certified 選択、材料レポート、
proof chain、凍結 bytes はいずれも不変である。新 leaf は production のどこからも参照されない。
変わるのは、将来の wiring wave が使える監査済み部品と、その監査の主張範囲が台帳に載ることだけである。
