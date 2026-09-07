## 所見

1. **must-fix 候補 — source の非保証を捨てた後で、成果物全体を「検査済み」に昇格している。**  
   `p3_b4_floor_artifact_issuer.py:616-623` は summary の `proof_limitations` を型検査するだけで、その後の dataclass や `_authority_value()` へ伝播しない。同 `:827-854` が発行する非保証は固定 2 文だけである。実際、`test_p3_b4_floor_artifact_issuer.py:154-157` の `"not a measurement"` を持つ summary からも成果物を発行できる。一方、loader は `source_summary` の path/hash を実在照合せず形だけ検査する (`p3_b4_floor_artifact_issuer.py:1073-1102`) のに、材料レポートは `"authoritative_floor_artifact"` を `not_guaranteed` から削除して `checked` へ移す (`p3_b4_material_report.py:992-998`)。手製 fixture も存在しない source とダミー hash のまま受理される (`test_p3_b4_material_report.py:114-126,929-934`)。  
   **放置時:** floor の数値・受理集合自体は変わらないが、成果物の出所と upstream 非保証が消え、機械可読な保証だけが実態より強くなる。D1696 の validator を増やさず、source limitations を残すか `checked` の名称を実際の「§5 hash・schema 検査」に狭める必要がある。

2. **段 4 からの良方向だが未裁定の wire 逸脱 — present 時の新しい report token を発明している。**  
   `p3_b4_material_report.py:983-990` は `expected_analysis_verdict` と `expected_analysis_reason` を新値 `"not_fixed_by_floor_presence"` に変更し、`:1061-1069` でそれを exact contract にしている。段 4 §D-4 が固定したのは `floor.availability`、`analysis.status`、`analysis.floor_argument` の 3 列で、この新 token は要求されていない。さらに schema は v1 のままである。  
   **放置時:** floor 値は変わらないが、present report の JSON 値域・bytes と downstream consumer の受理集合が裁定外に広がる。

3. **scope 逸脱候補 — 段 4 が明示していない一般的な hardening/gate がまとまって追加されている。**  
   具体的には、canonical JSON・duplicate key・再帰的 non-finite gate (`p3_b4_floor_artifact_issuer.py:178-221`)、window/campaign/drop/proof を含む summary 全体の closed-schema/type validator (`:362-465,588-623`)、canonical path・全 symlink component・regular-file gate (`:291-360`)、tempfile＋fsync＋hard-link の durable publisher (`:867-918`)、材料レポートの二重 projection validator (`p3_b4_material_report.py:1040-1082`)。  
   D1696 が列挙した exact 2 window・n・24 時間・校正・セル集合・journal・JSONL・finalize 束縛などの **9 項目そのものは検査していない**。五要素は issuer が名前を生成するが、loader は path と identity の一致を検査しないため、D1696 の filename validator にまではなっていない。  
   **放置時:** 正常 producer の floor 値は変わらないが、malformed/拡張入力の受理集合と I/O failure 集合が段 4 の明示範囲より狭くなる。

## scope 外だが real

- **正規 producer から権威成果物を発行できない。** `p3_b4_floor_artifact_issuer.py:693-727` は build receipt の top-level `protocol` を必須にするが、実 producer 経路の試験は必ず `missing_identity_elements == ("protocol",)` となり発行を拒否する (`test_p3_b4_floor_artifact_issuer.py:186-218`)。present 配線試験は issuer を通さず authority JSON を手書きしている (`test_p3_b4_material_report.py:77-143`)。段 4 §E-3 が明示的に裁定パッケージへ残した事項なので本変更の must-fix ではない。  
  **放置時:** legitimate な present 集合は空のままで、実 repo の材料レポートは floor absent／`protocol_violation` から進まない。

- **事前登録の事実記述が実装後は偽になる。** doc `:901-905,1091-1092` は「生成器は本書を読まず無条件に floor 不在」と記すが、新実装は `p3_b4_material_report.py:214-220,267-278` で §5 を読み floor を渡す。もっとも段 4 §C が doc 非改変を明示しているため、修正は本 scope 外である。  
  **放置時:** 実行値・受理集合は変わらないが、人間が参照する現在地説明が逆になる。

## 反証できなかった点

- D1377 の再侵入は確認できない。issuer CLI は `--repo-root` と `--summary` だけ (`p3_b4_floor_artifact_issuer.py:1177-1186`)、材料レポート CLI/API に floor 引数・既定値はない (`p3_b4_material_report.py:1228-1232,1557-1561,1600-1615`)。summary caller は候補成果物を選べるが、分析へ実効化する値を選ぶのは固定 repo の §5 を編集する者である。
- D1383 の既成事実化は、上記「非保証消失」以外には確認できない。数値 fixture は `"synthetic"`／`"not a measurement"`、present fixture の `[0,1]` は `"zero-boundary-control"` と明記され、sample artifact や既定 floor はない。
- integrated.patch には issuer と材料レポート配線の両方が含まれ、T-2289 closure receipt 接続はない。実際に 1 commit へなるかは patch だけでは証明できない。
- exact ratio、binary64 同順序再導出、bool 拒否、単一 v2 pin、4 状態の `floor_argument` 射影は段 4 と一致する。
- 非保証 2 文は `p3_b4_floor_artifact_issuer.py:41-50` に逐語であり、present 材料レポートの両非保証欄へ伝播する (`p3_b4_material_report.py:992-999`)。absent bytes を不変にするため absent report には追加されない。
- §D-6 grammar は regex の完全一致 (`p3_b4_floor_artifact_issuer.py:60-62,1160-1174`) で、sentinel も逐語 `未記入` (`:55`)。doc の現物も `未記入` (`docs/phase3-b4-reflux-ablation-preregistration.md:162`)。
- integrated.patch に事前登録 doc の diff はなく、非改変を確認した。pytest は指示どおり未実行。

## 総括

must-fix 候補は、upstream の `proof_limitations` を捨てながら成果物全体を `"checked"` と表現する非保証の過大表示。  
次点は、schema v1 のまま `"not_fixed_by_floor_presence"` という未裁定 token を wire contract に追加した点。  
一般 hardening 群は D1696 の 9 項目 validator ではないが、厳密 scope なら明示承認か削減が必要。  
`protocol` 欠落による正規発行不能と stale doc は real だが、段 4 が明示的に本 wave 外へ残した事項である。