## 変異ごとの追跡

- **M-A1: KILLED。** C-2 の非 ASCII 前置 fixture (`test_p3_b4_wiring_probe.py:205-214`) は byte offset を渡す。文字 slice にすると取得範囲が右へずれ、`:203` の stdlib 等価 assert が破れる。C-1 は実データ条件上殺せない。
- **M-A2: KILLED。** C-2 の form feed fixture (`test_p3_b4_wiring_probe.py:238-248`) で、form feed 分割後は後続文字を取得できず、`:203` が破れる。C-1 は対象 module に form feed がないため殺せない。
- **M-A3: KILLED。** C-1 の複数行 `if.test` で、製品値 `:172` から改行が消え、stdlib 値 `:173` との比較 `:174` が破れる。C-2 の LF/CRLF/CR fixture `:226-236` も同じ変異を殺すため、C-1 だけの検出ではない。
- **M-A4: KILLED。ただし C-4 のみではない。** 完全な旧経路復帰で `_split_source_lines` 呼び出しも消えれば C-4 の `split_calls == 1` (`test_p3_b4_wiring_probe.py:334`) が `0` で破れる。死んだ一回呼び出しを残して C-4 を逃れても、C-3 が `_get_source_segment` を `None` / `""` に差し替える `:287-293` のに旧経路はそれを呼ばず、fallback 期待 `:295-298` が `"cond"` のままで破れる。
- **M-A5: 通常形は KILLED、意味論全体には survivor あり。** 製品関数を visitor ごとに呼べば3回、`if` ごとなら4回となり、C-4 の `:334` が破れる。fixture の3 function、4 `if` は `:330-333` で確認される。ただし後述の死んだ一回呼び出しと別 splitter の組み合わせは通る。
- **M-A6: KILLED。** fallback を落とすと、C-3 の最初の `None` ケース `test_p3_b4_wiring_probe.py:287-293` で `guard.strip()` (`p3_b4_wiring_probe.py:805`) が `AttributeError` となり、assert 前に赤になる。空文字だけなら期待 `:295-298` が破れる。

C-1 の reference は `ast._splitlines_no_ff` を先に保存 (`test_p3_b4_wiring_probe.py:157`)、その保存値を cache wrapper から使用 (`:160-165`) し、期待値は `ast.get_source_segment` (`:173`) で得ている。`P._split_source_lines` は actual 側 `:168` だけであり、共通故障にはなっていない。

## 所見

### C-2 は無変異の現実装でも終端境界で赤になる — must-fix

- 根拠: `_split_source_lines` は残余が非空のときだけ追加するため (`p3_b4_wiring_probe.py:741-742`)、空 source は `[]`、末尾改行は終端空要素なしになる。一方、契約は終端空要素を明記している (`stage4-adjudication.md:37-40`)。C-2 の空 source と終端空行 `test_p3_b4_wiring_probe.py:255-256` は `_get_source_segment` の `lines[lineno]` (`p3_b4_wiring_probe.py:760`) で `IndexError` になる。
- 成果物への影響: 無変異 baseline が赤なので、C-2 による M-A1/M-A2 の mutation-red を有効な受領証として扱えない。
- 推奨対応: splitter の最後で `source[start:]` を無条件に追加し、空 source と末尾改行でも stdlib と同じ終端空要素を作る。実装子報告の補助確認済みという記述 (`stage5-author-out.md:11`) も再確認する。

### C-4 は splitter 出力の dataflow を pin していない — must-fix

- 根拠: spy は製品が現在呼ぶ `P._split_source_lines` を正しく差し替えている (`test_p3_b4_wiring_probe.py:316-324`、製品呼び出し `p3_b4_wiring_probe.py:888`)。しかし assert は回数だけ (`test_p3_b4_wiring_probe.py:334`) で、その返却 object が visitor に渡り (`p3_b4_wiring_probe.py:908-913`)、helper が受け取ったことを検査しない。死んだ一回呼び出しを残し、別 splitter を visitor または `if` ごとに使えば C-4 は通る。C-3 の helper stub も `_lines` を無視する (`test_p3_b4_wiring_probe.py:291`)。
- 成果物への影響: 意味論としての M-A5、つまり二乗分割が復活しても全テストが緑になる実装形が残り、受入時間が改善しない成果物を受領しうる。
- 推奨対応: C-4 で splitter の返却 object を記録し、`_get_source_segment` も spy して全4回の第一引数がその同一 object であることを assert する。

### mutation の帰属が一部過剰決定 — nit

- 根拠: C-2 の複数行 fixture `test_p3_b4_wiring_probe.py:226-236` も M-A3 を殺す。また newline と separator fixture `:226-248` は非 ASCII と改行種別を同じ入力へ載せているため、C-2 内で複数の変異軸が交差する。M-A4 も C-3 と C-4 の双方で殺される。
- 成果物への影響: 検出力は低下しないが、「どの検査がどの単一理由で赤になったか」という事前登録上の帰属が不正確になる。
- 推奨対応: separator と改行保持用に ASCII だけの fixture を追加または分離し、M-A4 の殺し手を C-3/C-4 と記録する。

## 未実走・未確認

pytest と実変異の適用は未実走。所要時間も未計測である。静的には C-1 は45 module を一度 loadし、stdlib splitter を source 単位で cache (`test_p3_b4_wiring_probe.py:153-179`) しており、約1〜2秒という見積りから大幅に逸脱する構造は見当たらない。C-2からC-4は小さい合成 source のみである。

新テストに working tree hash、時刻、固定絶対 path の焼き込みはない。`len(static) == 45` (`test_p3_b4_wiring_probe.py:155`) は repo 構成への固定だが、契約された45 module の網羅性 pin と解釈できる。

## 総括

- M-A1、M-A2、M-A3、M-A4、M-A6 は静的に KILLED と追跡できる。
- M-A5 の通常実装は C-4 が殺すが、splitter 出力の dataflow 未検査に survivor がある。
- C-1 の reference は製品 splitter と独立している。
- C-2 は現実装の終端空要素欠落により、無変異でも赤になる。
- よって終端修正と C-4 の identity/dataflow pin は受領前の must-fix である。