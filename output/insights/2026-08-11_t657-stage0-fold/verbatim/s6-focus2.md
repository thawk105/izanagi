判定は **NO-GO**。fix 2 巡目は元の backtick-info 経路を閉じましたが、tab indentation による 3 つ目の fence decoy が残っています。

### FOCUS6R2-01

- **所見 ID:** FOCUS6R2-01
- **主張:** fence の indent を表示 column ではなく文字数で数えており、行頭 tab を「indent 1」と誤認する。CommonMark では tab は 4-column indent なので fence ではないが、validator だけが fence として扱う新しい decoy が成立する。
- **file:line 根拠:** opener は `[ \t]{0,3}` で tab を 1 文字として受理する。[contract.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:76)。closer も `len(fence_line) - len(stripped)` で文字数を使う。[contract.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:363)。比較元 `check_docs.py` も同じ欠陥を持つ。[check_docs.py:3281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/tools/check_docs.py:3281)、[check_docs.py:3288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/tools/check_docs.py:3288)
- **具体的な失敗シナリオ:** §7.5 表を次の並びへ置換する。

~~~text
<TAB>```text
可視な緩和表
```
canonical 表
<TAB>```
```
~~~

  validator は最初の tab 行で fence を開いて緩和表を捨て、最初の無 indent marker で閉じて canonical 表を読み、2 組目で状態を同期して正常受理する。CommonMark 側では tab 行は indented code なので緩和表が可視、最初の無 indent marker から canonical 表が fence 内となる。
- **深刻度:** **blocker**
- **成果物影響:** 人間が読む設計正本と validator の権威 bytes を再分離でき、§7.5 schema または同型の段 6 契約を可視側で緩和できる。

### FOCUS6R2-02

- **所見 ID:** FOCUS6R2-02
- **主張:** F3 の新しい陰性 node は現行コードでは狙った `_read_design` 層で落ちるが、その層を外しても別理由で拒否されるため、変異に対しては診断差だけの赤になる。
- **file:line 根拠:** node は relaxed 表と canonical 表を同時に残す。[test_contract.py:975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:975)。invalid-info 検査を外すと raw text に表 prefix が 2 個残り、extractor が duplication で拒否する。[contract.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:467)。テストは診断 substring の違いだけで赤になる。[test_contract.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:124)
- **具体的な失敗シナリオ:** M1 の `fence_match = None` では `invalid backtick fence info string` ではなく `revocation table is missing or duplicated` になる。入力は引き続き拒否されるが node は失敗する。
- **深刻度:** **must-fix**
- **成果物影響:** FOCUS6-01 防壁について、受理集合差による変異証拠を新設 node が提供せず、再び診断だけの KILL を記録しうる。

### FOCUS6R2-03

- **所見 ID:** FOCUS6R2-03
- **主張:** mutation-spec は M3 が生存し、M5 が診断だけで赤くなり、M1・M6・M7 の expected failure 集合も現行 bytes と一致しない見込みである。
- **file:line 根拠:** spec の各置換と期待 node は [mutation-spec.json:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/mutation-spec.json:7)。M3 が外すのは execution-boundary 比較だが、期待 node が変更するのは control 文である。[contract.py:971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:971)、[test_contract.py:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:1070)。M5 の後段には独立 hash pin が残る。[contract.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:696)、[contract.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:701)
- **具体的な失敗シナリオ:** 静的帰属は次のとおり。

| mutant | 真に KILL する node | expected_nodes 判定 |
|---|---|---|
| M1 | §7.5 削除型 2 node、段 6 削除型 2 node、未閉じ・短い closer・異種 closer node | **不一致**。新 `test_design_invalid_backtick_info_decoy_is_rejected` も診断差で赤になるが未登録 |
| M2 | constraint relaxation、既存 fenced decoy | 一致見込み。双方とも受理へ倒れる |
| M3 | **なし** | **不一致**。control suffix は残った control 比較に殺され、node は緑のまま |
| M4 | live-tip relaxation | 一致見込み |
| M5 | **なし（意味上）** | raw failure 集合は登録 6 node と合いそうだが、独立 hash pin の診断へ変わるだけで DW-M03 上の KILL ではない |
| M6 | required-gate reorder node のみ | **不一致**。独立 module pin を直接 assert する node は mutation 後も緑 |
| M7 | 少なくとも real-repository 正例 | **不一致**。登録 4 node に加え adjudicated projection、tilde-info 正例、longer-closer 正例など多数が前段 schema 拒否で赤になる |
- **深刻度:** **must-fix**
- **成果物影響:** 変異 ledger が MISMATCH/SURVIVED になるか、診断 sensitivity を KILL と誤記し、段 6 の検出力証明が成立しない。

### FOCUS6R2-04

- **所見 ID:** FOCUS6R2-04
- **主張:** §12.3 自体は中立化されたが、§7.5 に「対応する上位 record」の存在を前提にした古い文が残り、(b) と矛盾する。FOCUS6-03 は consumer 取り残しとして未閉鎖である。
- **file:line 根拠:** §12.3 は専用 record の有無を未裁定と明記する。[bundle-design.md:864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:864)。一方 §7.5 は「対応する上位 record は、置き場・粒度とも未確定」と書き、record の存在自体を既成事実化している。[bundle-design.md:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:504)
- **具体的な失敗シナリオ:** ユーザーが (b) を選ぶと、§12.3 は「上位 record を持たない」となる一方、§7.5 は「対応する record の置き場・粒度を未確定」と残り、後続実装者が record の存在を先取りできる。
- **深刻度:** **must-fix**
- **成果物影響:** R4 のユーザー決定権と設計正本の一意性が失われ、裁定後の実装対象が節によって分岐する。

### FOCUS6R2-05

- **所見 ID:** FOCUS6R2-05
- **主張:** invalid backtick info 行を文書全体の拒否理由にする処理は意図的 fail-closed だが、CommonMark 上は通常本文になりうる合法文書まで拒否する。
- **file:line 根拠:** invalid opener を visible line に残した後、存在だけで文書全体を拒否する。[contract.py:372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:372)、[contract.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:383)
- **具体的な失敗シナリオ:** 設計本文で、行頭から malformed fence の例 ` ```python`bad` を通常テキストとして説明すると、Markdown としては ordinary text だが契約検査は文書全体を拒否する。
- **深刻度:** **nit**
- **成果物影響:** 不正な成果物を受理する経路ではないが、正当な設計文書の編集可能集合を不必要に縮小する。

補足照合では、§7.5 削除型 2 node は修正後 helper が表 terminator の空行を closer より前へ残すため、raw M1 で canonical 表が正常受理される側へ倒ります。[test_contract.py:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:856)、[contract.py:470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:470)。FOCUS6-02 は閉じています。

tilde info の backtick 正例は現実装で受理され、backtick を含む info を marker 種別にかかわらず拒否する過剰修正を検出できます。CRLF、closer の info、4-space indent、真正な fence 内の invalid opener には独立の bypass を確認しませんでした。真正な fence 内の invalid opener を無視すること自体は、CommonMark と同じく fence 内容として捨てるため妥当です。

段 0 は現行 bytes の直接算出でも `required_gates=13`、blocking 5、`status=incomplete`、`pending=5`、`applicable_unresolved=2`。manifest・canonical entries・module pin の hash も一致しています。stage 6 extractor の caller 取り残し、hash 自己参照、fix 2 による既存期待値の緩和は確認しませんでした。

## 総括

- 判定: **NO-GO**
- blocker の所見 ID: **FOCUS6R2-01**
- FOCUS6-01: **open** — invalid backtick-info 経路は閉じたが、tab を indent 1 と数える scanner-only fence decoy が残る
- FOCUS6-02: **closed** — §7.5 削除型 2 node は raw M1 で正常受理へ倒れ、段 6 側と同じ受理集合差になった
- FOCUS6-03: **open** — §12.3 は中立化されたが、§7.5 が「対応する上位 record」の存在をなお前提化している
- M1〜M7 の expected_nodes に修正が要るものの ID: **M1、M3、M6、M7**（M5 は node 集合より KILL 意味論の修正が必要）