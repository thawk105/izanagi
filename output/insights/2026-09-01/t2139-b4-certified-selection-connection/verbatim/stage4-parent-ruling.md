## 段 4 裁定 (親)

**裁定: 本 wave では実装しない。** 段 5・6 を飛ばし `4→7→8→9` とする (`DW-S04`)。
プランは設計メモとして保存し、設計択一はユーザー裁定へ返す。

### 決め手 (親が独立に実測した)

**certified 側の受け口は、この checkout では構造的に発火しない。**

- `certifying_input: True` を作る唯一の箇所は `layer3_report.py:768`
  (`build_accepted_report` 内)。
- そこへ入るには `layer3_report.py:701` の `verified.certifying is not True` を通す必要がある。
- `VerifiedAcceptanceReceipt` を作る唯一の parser は
  `s8c_acceptance_receipt.py:420-423` で
  「Both generations structurally record unresolved approval authority.
  No accepted bytes can turn either generation into a certifying receipt.」と明記し、
  `certifying` が `False` 以外なら必ず拒否する。
- `build_accepted_report` を成功させている既存 test は 6 本すべて
  `require_current_verified_receipt` を monkeypatch している
  (`test_layer3_report.py:1802,1833,1868,1920,1956,1995`)。
  repository 自身が「stub 無しでは到達しない」ことを示している。
- production の唯一の呼び手 `render_accepted` (`layer3_report.py:829`) も
  検証済み receipt を caller から要求するだけで、この閉鎖を開けない。

したがって「certified 選択へつなぐ」相手は未実装なのではなく**構造的に閉じている**。
接続を発火させる唯一の方法は何かを certifying にすることであり、それは**規律 2 の緩和**である。
やってはならない。

### 適用した gate

- `DW-G04` — 発火条件を満たす既存 artifact path も計測 ID も書けない
  (`find output -name report.complete` = 0 件、production callsite = 0 件)。
  書けなければ**設計メモに留める**。
- `DW-G05` — 実装しても certified 選択の受理集合・材料レポート・台帳は 1 bit も変わらない。
  成果物影響を 1 行で示せない。
- `DW-S04` — 承認済み裁定 (ユーザーの実装指示) は裁定時の未見事実でだけ止める。
  親は不採用にせず、**新事実を添えてユーザー再裁定待ちへ戻す**。

### 所見の real / refuted

real (採用):
- A/B 共通 blocker: 成果物は certified-selection connection ではない → **real**。上記で確定。
- A blocker: `Literal[False]` の許可判定は恒真 → **real**。実装するなら
  「阻害理由集合が空か」で計算し、理由集合が到達入力で実際に変わる形にする。
- B blocker: `DW-G04` の発火 gate を書けない → **real**。
- A/B: 親 brief の一般化 2 件が広すぎた → **real**。訂正済み。
  (i)「下流 consumer 不在」→ 正しくは「B-4 材料レポートを読む consumer が不在」かつ
  「現行の権威 producer から certifying input を発行できない」。
  (ii)「到達可能 verdict は 1 つ」→ 正しくは「材料レポートの正規コマンドに限れば 1 つ」。
  分析経路自体は `floor=0` で `established` へ到達する
  (`test_p3_b4_analysis_path.py:274` で確認)。
- A: 返り値 dataclass の truthiness で `if decision:` が真になる → **real**。
- A: 変異 C07 / C08 / C09 は Markdown 層に mask される → **real**。
  実装するなら `DW-M03` の冗長 gate として扱うか `DW-M04` の両層同時変異で登録する。
- B: `test_p3_b4_raw_record_producer.py:881` の fixture は
  「1 real block + 200 replica (fsync patch 下)」であり real artifact ではない → **real**。
- B: 識別子 `certified_selection_connection` が既に「非保証」の意味で
  `p3_b4_material_report.py:739` に存在し、逆向きの意味が併存する → **real**。
- B: 正例が推移的に `p3_b4_closed_critic` / `p3_b4_launcher` /
  `p3_b4_admission_record` を import し、稼働中 wave の所有面と実行依存で重なる → **real**。
- B: 親 brief の行番号 3 件がずれ (735→739、68-74→67-73、308-314→310-315) → **real**。訂正済み。
- A/B: 3 file 束縛は内容整合だけで subject / issuer / 配置を束縛しない → **real**。
  実装するなら非保証として宣言する層と、権威で束縛する層のどちらを採るかがユーザー裁定。

refuted / 格下げ:
- A: 「P2 の docstring が記録との矛盾」→ A 自身が nit へ格下げ。
  `p3_b4_analysis_path.py` の文面は "This module" の scope 外と言っており、
  別 module に責務を置いても真のまま。**矛盾ではない**。
- B: 「既存被覆と重複」→ 部分的に refuted。材料レポートは非認証を**宣言**するが、
  それを**検査**する consumer は無い。ただし実装しない裁定により moot。

### ユーザーへ返す裁定パッケージ

3 択。詳細は insight と worklog に残す。

1. **T-2139 を上流待ちにする (親の推奨)。** floor 発効 ([T-2140]) と
   approval authority の解消が済むまで、プランを設計メモとして保持する。
   接続は sink が発火可能になった wave で callsite ごと実装する。
2. **成果物を validator へ降格して実装する。**
   `certified_selection_connection` を名乗らず、5 語目を埋めたとも記録しない。
   「材料レポートの publish 後 integrity validator」として実装する。
3. **scope を拡張する。** sanctioned callsite・耐久 decision・sink の必須入力・
   wire lifecycle 更新まで同一 wave に含める。**別 wave 所有境界を越えるためユーザー裁定が要る。**
   ただし sink は現在 certifying になり得ないので、
   **この案は規律 2 に触れない範囲では完成しない。**
