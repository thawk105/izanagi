# 段 4 裁定 — [T-1116] 受入の非帰属 checker

wave `dev-wave-t1116-nonattrib-checker` / base `7c83eeac` / 2026-08-17 02:40 JST

## 裁定の結論

**実装しない。** 裁定パッケージをユーザーへ返す (`DW-S04`)。
段 5・6 を飛ばし `4→7→8→9` とする。変異 matrix は実装差分ゼロにより免除、受入全走は実施する。

## 本 wave が確定させた事実 (一次資料)

**Q. 8a2b735b は [T-1116] 裁定 (択 2) とユーザー裁定 R2 をどこまで果たしたか。**
**A. checker 層だけを果たし、end-to-end では 1 mm も果たしていない。**

1. **checker 層は直っている。** 2026-08-15 に旧 checker が `attributable` と判定して受入全走
   1 本を捨てた実履歴 log を、現 main の checker へかけ直すと `flake` になり rc=0 を返す。
   一次資料 = `probe2-receipt.json`
   (node `orchestrator/tests/test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler`、
   `main_rerun_rc=0` / `wave_rerun_rc=0` / `classification=flake`、status `non-attributable-only`)。
   **限定**: この走行は `--tested-main` と `--wave-tip` に同一 SHA を渡しており、
   両 probe は同じ tree を別 worktree で走らせただけである。したがってこれは
   「現 checker が実履歴の signal 赤を `flake` に分類する」ことの証拠であって、
   実運用 (A≠T) の分類差や後述 (P3) の実効性の証拠ではない (段 3 レンズ A の指摘を採用)。
2. **消費層が取り残されている。** `tools/dev_wave_wait.py:2803-2812` は checker 受領証の
   **全 node** に `set(node) == {"classification","nodeid","rerun_rc"}` かつ
   `classification == "non-attributable"` を要求する。`flake` node は 5 field なので
   `_StageFailure` になり、**受領証は発行されない**。
   実測: probe2 の実受領証を同述語にかけて REJECT。
   文字列 `flake` の出現数は `tools/dev_wave_wait.py`=0、`tools/dev_wave_land.py`=0、
   `orchestrator/tests/test_dev_wave_wait.py`=0、`orchestrator/tests/test_dev_wave_land.py`=0。
   8a2b735b が触ったのは checker とその test の 2 file だけである。
3. **したがってユーザー裁定 R2**「確率的なフレークで受入全走を何度も無駄にする構造は
   全てのセッションに対して許さない」**は一度も発効していない。**
   フレーク 1 件で受入全走 1 本が捨てられる構造は、8a2b735b の前後で変わっていない。
   8a2b735b の commit body は「既存の呼び手は壊れない」を root field と `--wave-tip` flag
   だけで確認しており、node 形の exact 検査を見落としている。
   これは規律 6 が監査発火条件に挙げる **consumer 取り残し**の型である。

## 所見の裁定 (段 3 レンズ A / B、親が独立に検算)

| # | 所見 | 判定 | 処遇 |
|---|---|---|---|
| 1 | (P3)「test file 非接触」は差分起因 flake の閉包にならない。production / conftest / fixture / plugin の 4 経路で全走限定赤を作れる (lens A:3-14, lens B:15) | **real** | 採用。(P3) 単独では受理集合拡大を正当化できない |
| 2 | 待ち手と runner は main 側と照合されない。checker だけが main==tip を要求し、`_verify_waiter_source_bytes` は running bytes と tip blob しか比べない (`tools/dev_wave_wait.py:1584-1663`、land は `tested_tip:tools/dev_wave_wait.py` のみ、`tools/run_tests.py` は存在確認のみ) | **real** | **scope 外・重大**。裁定パッケージ #3 として返す |
| 3 | land は「変更不要」ではない。flake nodeid が `accepted_nodeids` → `acceptance_red_nodeids` に非帰属赤として混ざる。別 field を足すと land の root exact が拒否する | **real** | 採用。拡大 scope に land と outer receipt schema を含める |
| 4 | 拡大の実 scope は wait + outer receipt schema + land + 3 test file + runbook / D371 / D389。「production 2 + test 2」では足りない | **real** | 採用。裁定パッケージ #2 の費用として明記 |
| 5 | checker を編集する wave は child-green の受入走行でしか land できない。待ち手編集には同種の main/tip 一致要求は無い | **real** | 採用。親も独立に実測済み |
| 6 | probe2 は (P3) の証拠にならない (A==T なので差分は構造的に空) | **real** | 採用。上記「限定」に反映済み |
| 7 | 「89 赤のうち 4 件接触 → 95.5% が救済される」は無根拠。集計の分母 89 は旧 checker の分類であり、wave 単独 rc を 1 件も測っていない | **real** | **採用。95.5% を撤回する。**残すのは上界のみ — 「(P3) は 89 件のうち最大 4 件にしか作用しない」 |
| 8 | 待ち手の rc 値 pin が緩い。`non-attributable` は `type(rerun_rc) is int` だけを要求し、`rerun_rc` が 0 / 2 / -1 でも通る (本来 1 のはず) | **real** | **scope 外**。裁定パッケージ #4 として返す |
| 9 | 変異は層別に登録しないと帰属が崩れる。過剰拒否変異は既存 `test_main_green_wave_green_is_recorded_as_flake` が既に殺すので新規検出力に数えられない | **real** | 実装時に適用。今回は実装しないため保留 |
| 10 | docs 契約 (runbook / D371 / D389) が受領対象を `non-attributable-only` と書いており flake を記述していない | **real** | 採用。拡大 scope に含める |
| 11 | 段 2 プランの land 行番号が stale (`1490` は別検査)、特殊 nodeid 形 (`@group` / parametrize / ` - detail` / 同名 basename) は `collection.path` を使う限り問題なし | **nit** | 記録のみ |

**refuted は 0 件。** 親 brief 側の誤りが 2 件 ((P2) の向き、95.5% の一般化) で、どちらも
レンズが正しく、親が撤回した。

## 実装しない理由

- 穴を閉じる = 受理集合を**広げる**ことである (現在は全 flake が拒否される)。
- 独立な 2 レンズが**別々の根拠で** NO-GO に到達した。拡大を正当化する述語 ((P3)) は
  差分起因赤の閉包ではなく、production / conftest / fixture / plugin の 4 経路が残る。
  この残余を受容するか否かは規律 2 の受理集合の話であり、**親が決めてよい範囲を超える**。
- 実 scope は wait + outer receipt schema + land + 3 test + docs 契約であり、
  親 brief の 4 file 見積りの倍以上である。
- `DW-S04`: 承認済み裁定 (R2) は親が不採用にせず、新事実を添えてユーザー再裁定待ちへ戻す。
  ここでの新事実は「R2 は一度も発効していない」「発効させるには 4 クラスの迂回路を明示受容
  する必要がある」「受入証拠の連鎖は checker 以外すべて wave tip の自己証明である」であり、
  いずれも R2 の裁定時には未見だった。

**実装しないことの成果物影響 (`DW-G05`)**: フレーク 1 件で受入全走 1 本が捨てられる構造が続く。
本 wave の実測では、この構造が原因で捨てられた受入は履歴上 44 走行分ある。
ただし**これは現状維持であって後退ではない** — 8a2b735b の時点で既にそうだった。

## ユーザーへ返す裁定パッケージ

**#1 [T-1116] を終端してよいか。** 択 (2) の「対象 wave より前から main に存在する entry を
批准と見なす」は、registry ではなく live probe (`main 単独再走が赤 → non-attributable`) として
**8a2b735b より前から実装済み**である。裁定が明示受容した「AI による 2 wave 事前登録が残る」
リスクは、registry が存在しないため別形 (main へ赤を land させる) に変わっている。
併合された [T-1055]「registry 由来 nodeid を非帰属と区別して受領証へ書く」は**未達**
(`red_nodeids` は由来を区別しない)。
→ 択: (a) 終端する (残存リスクと [T-1055] の no-op 理由を明記して閉じる) /
(b) 未終端のまま残し、下記 #2 の裁定に従属させる。**親の推奨は (b)** — #2 が決まるまで
[T-1055] の可否が決まらないため。

**#2 R2 を実効化するか。** 現在フレークは 1 件で受入全走を捨てる。実効化には
`tools/dev_wave_wait.py` + outer receipt schema + `tools/dev_wave_land.py` + 3 test file +
runbook / D371 / D389 の同時改訂と、**production / conftest / fixture / plugin 経由の
全走限定赤が `flake` として通る残余の明示受容**が要る。
→ 択: (a) 受容して実効化する / (b) fail-closed を維持し R2 を「実装不能として撤回」する /
(c) 中間 — flake を通すが `red_nodeids` とは別集合で受領証・land・台帳へ記録し、
land 後に人間が読める形で残す。**親の推奨は (c)** — R2 の目的 (受入窓を捨てない) を果たしつつ、
[T-1055] が求めた「区別して書く」も同時に満たし、残余を台帳で追跡可能にできる。

**#3 受入証拠の自己証明を塞ぐか (新規・重大)。** [T-1131] は checker だけを tested_main へ
束縛した。`tools/dev_wave_wait.py` は running bytes と tip blob の一致しか検査されず、
`tools/run_tests.py` は tip での存在しか検査されない。したがって wave は待ち手または runner を
書き換えるだけで、実 child rc=1 を `child_rc=0 / verdict=child-green` として land できる。
**[T-1131] が塞いだ穴と同型が、隣接する 2 層で開いたままである。**
→ 択: (a) 待ち手と runner も main 側 blob と照合する ([T-1131] と同じ代償を受容) /
(b) tested_main 固定の外側 launcher を別途設ける / (c) 現状維持。**親の推奨は (a)** —
代償 (これらを直す wave は次 wave からしか効かない) は [T-1131] で既に受容済みの型である。

**#4 待ち手の rc 値 pin (小).** `non-attributable` node の `rerun_rc` は本来 1 のはずだが、
検査は int 型しか見ない。純粋な縮小で安全だが、#3 が開いている間は防御深度に留まる。
→ 択: (a) #3 と同じ wave で直す (親の推奨) / (b) 単独起票。

## 変異事前登録

実装差分ゼロのため `DW-S04` により変異 matrix を免除する。
将来 #2 を実装する wave のために、本 wave が確定した登録要件だけ凍結して引き継ぐ。

- **過剰受理の正例 (必須、投げ文の制約)**: wave が対象 test file を変更し、単独再走は
  main / wave tip 双方で緑、全走でのみ赤になる node を fixture で作る。
  `flake` へ落として受理する実装は KILLED でなければならない。
- **過剰拒否の正例 (`DW-M01`、縮小側)**: wave が `tracked.txt` のような無関係 file だけを
  変更した場合に `flake` が維持されること。**ただしこれは既存
  `test_main_green_wave_green_is_recorded_as_flake` (`orchestrator/tests/test_check_acceptance_reds.py:571`)
  が既に殺すため、新規検出力として数えてはならない** (段 3 レンズ A の指摘)。
- **層別分離 (`DW-M04`/`DW-M08`)**: checker 側変異と待ち手側変異を別登録する。
  checker 変異を実 acceptance で走らせると main/tip blob 不一致が先取りして落とすため、
  kill は `test_check_acceptance_reds.py` の単体 node でだけ数える。
  待ち手の flake 分岐削除を殺す正例は、valid な 5-field 受領証を渡す待ち手単体 test でなければ
  ならない (touched-file fixture では checker rc=1 が `tools/dev_wave_wait.py:2754-2756` で先に止める)。

## 段 7 以降の予定

worklog / decisions fragment、`output/insights/2026-08-17_t1116-nonattrib-checker/`、
受入全走 (docs-only なので `non-attributable-only` 経路で land 可能)、段 8、段 9 land。
