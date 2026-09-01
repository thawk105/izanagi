---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t2027-root-class2
seq: 3
---

## 新規

### {{F:root-resolution-required-where-unused}}. 使いもしない根の解決を先に必須化し、環境の stale な要素 1 つで経路全体を止めた [恒真ゲート] [手順漏れ]

- 事象: compiler input manifest に新しい根クラスを足した実装が、入力のタグを見る前に
  **渡された根の列の全要素**を canonical directory として解決していた。その結果、
  (1) 新しい根タグの入力を 1 件も持たない manifest でも、根の列に存在しない要素が 1 つあれば
  拒否され、(2) 新タグの入力があり有効な根に file が実在していても、兄弟要素が存在しなければ
  拒否された。production はその run が configure した `CMAKE_PREFIX_PATH` の全要素を渡すので、
  stale な要素が 1 つ紛れ込むだけで収集・cache hit 検証・受領書発行が止まり、
  built record と certified 選択と後続レポートがまるごと発行されなくなる。
- 根本原因: 根の解決を「入力を分類するために必要になった時点」ではなく
  「validator に入った時点」で行った。**根の実在は環境の状態であって caller の誤用ではない**
  のに、綴りの不正と同じ扱いにした。設計時に「その根を使わない入力に対しても解決が要るか」を
  問わなかった。**同型は 2 例目である** — 根クラス 1 の実装でも
  「masstree 根の解決が external input を admit しない build まで必須化されていた」形で
  発生し、着地後の独立監査が見つけている
  (`output/insights/2026-09-01_t2027-d1192-rebind-audit/README.md` の欠陥 B)。
  1 例目は F 台帳に登録されておらず、そのため 2 例目の設計時に参照されなかった。
- 恒久対応: 解決できない根要素は「その entry に match しない」として扱い、全体を落とさない。
  綴りの不正 (非 str・空・NUL・相対 path) は致命のまま分ける。
  `orchestrator/tests/test_s8b_compiler_input.py` の
  `test_v3_probe_snapshot_only_accepts_existing_and_missing_roots`、
  `test_v3_probe_dependency_entry_accepts_matching_and_missing_roots`、
  `test_v3_dependency_entry_rejects_only_missing_root_as_zero_matches`、
  `test_v3_invalid_dependency_root_spelling_is_rejected_by_validator_and_collector` が
  受理側と拒否側の両方を固定する。
- 再発検知: 根・base・prefix を caller から受け取る validator を新設する wave では、
  **その根を必要としない入力を負例ではなく正例として登録する**。
  「根が要る入力だけを試す」設計では、この型は最後まで見えない。

### {{F:redundant-none-guard-counted-as-strengthening}}. 受理面を変えない冗長 gate を、レビュー所見の是正として強化に数えかけた [恒真ゲート]

- 事象: 敵対レビューが「`None` (context 未提示) と明示的な空 tuple を区別せよ」と指摘し、
  親は採用と裁定した。実装は明示的な `None` 拒否の条件を足したが、**その直後に呼ばれる
  canonical 化関数が同じ条件で同じ入力を既に拒否していた**。両者の発火条件は完全に一致し、
  変わるのは診断文言だけで受理集合は 1 bit も動かない。変異事前登録の単一理由性検査で
  初めて分かった。
- 根本原因: 所見を「受理面の穴」として読み、**既に同じ入力を拒否している層があるか**を
  コードで確かめずに採用裁定を出した。レビューの指摘自体は正しい (診断は明確になる) が、
  受理面の強化ではない。
- 恒久対応: `DW-M01` の単一理由性検査を、変異登録の直前ではなく**所見の採用裁定の時点**で
  当てる。本 wave では m06 を kill 変異から外し、`DW-M08` の diagnostic sensitivity pin へ
  別枠記録したうえで、両層同時変異 (m06b) を kill 期待つきで登録し直した。
  経緯は `output/insights/2026-09-01_t2027-root-class2/mutation-erratum.md`。
- 再発検知: レビュー所見を「受理集合を変える」と裁定する前に、その入力を先に拒否する層が
  前後に無いことを確かめる。無ければ「診断の明確化」と裁定し、強化として数えない。
