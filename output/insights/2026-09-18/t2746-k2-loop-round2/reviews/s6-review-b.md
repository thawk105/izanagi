## 所見

以下、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/`。読取りと静的確認のみ実施し、pytest・変異は実行していません。

### must-fix

1. **real — critic の取込みと再射影で、先頭空白の扱いが異なる。**

   根拠: `C/p3_s4_loop.py:2597–2606` は見出し行の改行を除いて `rstrip()`、`C/layer3_report.py:188–195` は改行を含む範囲を `strip()` して比較する。既存の新設正例 `T/test_p3_s4_loop.py:9027,9081` は、実際に先頭が空白 2 個の attribution を保存する。

   **成果物影響:** CLI が正常保存した critic を renderer が拒否し、材料レポートを生成できない。

   最小是正: 原文保持を維持し、renderer の範囲選択・末尾処理を取込み側に合わせる。先頭空白・空行・CRLF を含む CLI 保存結果を renderer に渡す結線正例を追加する。既存期待値を `strip()` に合わせて緩めない。

2. **real — code block 内の偽見出しを実見出しとして数える。**

   根拠: `C/p3_s4_loop.py:2598` と `C/layer3_report.py:188` は、いずれも行頭 `##` の正規表現だけで走査する。負例は `T/test_p3_s4_loop.py:9136–9137,9167`、`T/test_layer3_report.py:5388–5405` の欠落・重複までで、code block のケースがない。

   **成果物影響:** 欠落した節を code block 内の文字列で補って受理でき、逆に正しい節とコード例が共存すると重複として拒否する。attribution の抽出範囲も変わる。

   最小是正: 両抽出処理で fenced code block 内を見出し候補から除外する。「実節欠落＋コード内だけの偽節」は拒否、「実節あり＋コード内の同名文字列」は原文を保って受理する対を追加する。

3. **real — D830 の閉包検査が初期辞書に限定され、後続変更を検査しない。**

   根拠: `T/test_layer3_report.py:5448–5458` は `verify_payload` の `AnnAssign` 一つから初期キーを取り、単一実行結果と比較するだけ。`update`・alias・再束縛等を拒否する解析と負例がない。実 producer にも後続 `update` がある (`C/pipeline.py:644`)。今回の実行 fixture は `include_qualification_evidence=False` 固定 (`T/test_layer3_report.py:5437`)。

   **成果物影響:** 未通過分岐で producer が追加するキーを閉包検査が見逃し、実成果物だけが schema 拒否される変更を検出できない。

   最小是正: 対象の producer 辞書について、許可する変更経路を解析し、それ以外の mutator・alias・再束縛を拒否する負例を追加する。`commit_witness` と `ProofSurfaceAssessment.as_record()` のキーも producer 由来で照合する。qualification 経路の受理拡大は本件の是正に混ぜない。

4. **real — planner/coder の variant について取込みと renderer の受理集合が異なる。**

   根拠: `C/p3_s4_loop.py:2683–2685` は planner/coder なら WAL に実在すれば受理する。一方 `C/layer3_report.py:172,179` は全 stage に WAL **commit** の存在を要求する。裁定の非 null variant 条件は WAL 実在である。

   **成果物影響:** build_start や abort にだけ現れる variant に紐づく planner/coder 出力を保存できるが、その AO を含む report は生成できない。

   最小是正: renderer の planner/coder 判定を裁定の WAL 実在条件に合わせ、commit がない実在 variant の正例を追加する。critic にも commit 条件を要求する現実装は裁定の「WAL 実在」より強いため、同時に裁定との整合を確認する。

### nit・反証済み・帰属確認

5. **refuted — 双射が report の自己追認になっている。**

   根拠: `C/layer3_report.py:160,335,342,995`。期待 Counter は独立に読み取った AO、一次走査は `agent_outputs` のみ (`324–326`)、view は独立再射影との exact 比較、`source_refs` も Counter 比較する。

   負例も適切である。

   - 欠落: `T/test_layer3_report.py:5322` は本体と `source_refs` を同時に削る。
   - 等件数置換: `5343` は有効 planner envelope に替え、schema 通過後に双射へ入る。
   - 別 ref: `5356` は実在する critic 2 件の参照を交換する。
   - attribution 改変・view 欠落・重複: `5365,5373` は primary Counter を変えず view 比較へ入る。

   **成果物影響:** これらの変異は、別の schema 拒否に隠れず対象の完全性検査で拒否される。最小是正: 不要。

6. **refuted — verification schema の形・版・既存 pin が差分で壊れる。**

   根拠: `C/layer3_schema.json:319–373` は witness を exact 2 integer key、proof を exact `protocol/X/P/I` とし、protocol は string|null、X/P/I は指定 3 値。`C/pipeline.py:575,598,633`、`orchestrator/verifier/model.py:66–90` と整合する。追加 property は optional、v3 と既存 required は不変。v2 導出処理 (`C/layer3_report.py:380–388`) も未変更。

   pin の差分確認結果:

   | 対象 | 判定 |
   |---|---|
   | `test_t126_pegasus_tools.py:464–478` の exact 文字列 | 対象ハンクは未変更 |
   | official perf 対象集合・`_validate_schema` の共有 validator 呼出し | 維持 |
   | loop の `run_campaign` 呼出し | 1 本のまま |
   | renderer `_git_head` の spawn | 1 本のまま |
   | layer3 の空 MH fixture・v3/runs required fixture | 未変更 |
   | conftest の既存 public-drive 分類・serialization probe | 対象 node と結線は未変更 |
   | 新規 `test_agent_outputs.py` | `_run()` と `__main__` があり、二重 runner の静的条件を満たす |

   **成果物影響:** 指定 pin を差分が破る根拠はない。最小是正: 不要。ただし実走成功を意味しない。

7. **real・nit — 受入費用は小さい AO 単体検査だけではない。**

   根拠: `T/test_layer3_report.py:5238` は各負例で admission 付き `_certifying_campaign` と `build_report` を作る。静的展開では新設部に約 30 campaign fixture、約 39 回の `build_report` 呼出しがある。`T/test_p3_s4_loop.py:9237,9300,9325` の drive 到達は計 7 回相当で、実評価本体まで進む正例は no-build 1 回。他は停止・評価 stub・追記失敗経路である。新規の実 repo 複製や性能測定はない。

   **成果物影響:** AO reader 自体より admission・artifact 走査の反復が受入時間を増やす。

   最小是正: 親の所要測定で超過傾向が出た場合、結線正例を残し、純粋な Counter/view 負例の fixture を縮小する。追加費用は秒〜数十秒規模を見込むが、環境依存があり 5 分以内とは未判定。

8. **refuted — 新設テストが現行 hash 差込みや全面 stub だけで緑になる。**

   根拠: AO writer/reader、CLI、renderer は実体を呼ぶ。`T/test_p3_s4_loop.py:9300` は実 `drive_iteration` と実 no-build 経路を通す。現行 hash を追加 fixture に流し込む新変更は見当たらない。隔離検査の reader trap、書込み失敗注入、評価境界の stub は目的が限定されている。

   **成果物影響:** 基本機構への結線はある。ただし所見 1 の CLI→renderer 結線が欠けている。最小是正: 所見 1 の正例追加。

9. **real・既知の赤への帰属確認。**

   `C/layer3_report.py:338` の文言変更と、`T/test_layer3_report.py:5464` の WAL fixture 順序が親報告と一致する。

   **成果物影響:** 前者は診断互換の赤、後者は schema 結線検査へ到達する前の赤。最小是正: 指定どおり実装文言を戻し、fixture の topology を直す。前者を受理集合変化の mutation kill と数えない。

A2 の既存 artifact 報告は「v3 1 件・v2 6 件通過、v1 1 件は既存不一致」であり、**8 件すべて通過ではない**。optional 追加と v2 導出鎖の維持から報告内容は静的に整合するが、本レビューでは再 validate していない。v1 全文 reader と保存 report の fresh 比較は、既存の裁定パッケージ候補として残る。

## 変異提案

以下の `old` は現在の対象ファイル内で各 **1 箇所**であることを読取りスクリプトで確認した。各案は独立適用する。

期待 node は、**その node だけを runner 対象にする場合の完全集合**。全テストを走らせた場合の失敗集合ではない。すべて未実走の静的予測であり、fix 後の anchor 再確認が必要。

node 接頭辞:

- `A::` = `orchestrator/tests/test_agent_outputs.py::`
- `R::` = `orchestrator/tests/test_layer3_report.py::`
- `L::` = `orchestrator/tests/test_p3_s4_loop.py::`

1. **M1 — stage 白名簿**

   - file: `C/agent_outputs.py`
   - old: `if env["stage"] not in STAGES:`
   - new: `if False and env["stage"] not in STAGES:`
   - 期待 node: `{L::test_agent_reader_unknown_stage}`

   reader を直接呼び、CLI choices・report schema を通らない。

2. **M2 — 最終行の終端**

   - file: `C/agent_outputs.py`
   - old: `if frames[-1]:`
   - new: `if False and frames[-1]:`
   - 期待 node: `{A::test_unterminated_last_frame}`

   最終 frame はループ外なので、後段の duplicate 検査には届かず、未終端末尾を黙って捨てる変異になる。

3. **M3 — semantic 重複**

   - file: `C/agent_outputs.py`
   - old: `if key in semantic_seen:`
   - new: `if False and key in semantic_seen:`
   - 期待 node: `{A::test_semantic_duplicate_append}`

   ts が異なり canonical envelope 重複にはならない。完全重複の fixture は単一理由の証拠から除外する。

4. **M4 — planner/coder 一次配置の欠落**

   - file: `C/layer3_report.py`
   - old:
     ```python
     "agent_outputs": sorted(agent_outputs or (), key=lambda env: canonical_record_ref("ao", env)),
     ```
   - new:
     ```python
     "agent_outputs": sorted((env for env in (agent_outputs or ()) if env["stage"] == "critic_attributed"), key=lambda env: canonical_record_ref("ao", env)),
     ```
   - 期待 node: `{R::test_ao_canonical_bytes_and_three_stage_report}`

   `source_refs` は変異後の本体から生成されるため区画不整合ではなく、独立入力 Counter との不一致で拒否する。

5. **M5 — view の二重計数**

   - file: `C/layer3_report.py`
   - old:
     ```python
             refs[canonical_record_ref("ao", env)] += 1
         return refs
     ```
   - new:
     ```python
             refs[canonical_record_ref("ao", env)] += 1
         refs.update(row["source_ref"] for row in report.get("mechanism_hypotheses", ()))
         return refs
     ```
   - 期待 node: `{R::test_ao_canonical_bytes_and_three_stage_report}`

   正常入力の生成中に Counter 不一致となる。既に scanner を monkeypatch する負例を、この変異の主要証拠にはしない。

6. **M6 — 期待側の自己追認**

   - file: `C/layer3_report.py`
   - old:
     ```python
     expected.update(canonical_record_ref("ao", env) for env in (agent_outputs or ()))
     ```
   - new:
     ```python
     expected.update(canonical_record_ref("ao", env) for env in report.get("agent_outputs", ()))
     ```
   - 期待 node: `{R::test_ao_equal_count_valid_replacement_is_rejected}`

   planner 置換なので critic view は不変。schema と `source_refs` も整合し、当該期待 Counter だけが防壁になる。

7. **M7 — 別 critic への参照付替え**

   - file: `C/layer3_report.py`
   - old:
     ```python
     if report.get("mechanism_hypotheses", []) != _mechanism_view(records, agent_outputs or ()):
     ```
   - new:
     ```python
     if False and report.get("mechanism_hypotheses", []) != _mechanism_view(records, agent_outputs or ()):
     ```
   - 期待 node: `{R::test_ao_two_critic_view_ref_swap_rejected}`

   実在 ref 2 件を交換するため、存在検査による二重拒否がない。

8. **M8 — 不在時 provenance**

   - file: `C/layer3_report.py`
   - old:
     ```python
     "mechanism_hypotheses_provenance": "absent" if agent_outputs is None else "agent_outputs",
     ```
   - new:
     ```python
     "mechanism_hypotheses_provenance": "agent_outputs",
     ```
   - 期待 node: `{R::test_ao_absent_and_empty_independent_of_whiteboard[False-False]}`

   enum 内の値を使うため schema は通り、入力との provenance 比較で拒否する。

9. **M9 — 入力 builder の AO 読取り**

   - file: `C/p3_s4_loop.py`
   - old:
     ```python
         payload: Dict[str, Any] = {"whiteboard": whiteboard_for_planner(state)}
     ```
   - new:
     ```python
         agent_outputs.read_agent_outputs("/forbidden-agent-output-input.jsonl")
         payload: Dict[str, Any] = {"whiteboard": whiteboard_for_planner(state)}
     ```
   - 期待 node: `{L::test_agent_input_execution_isolation}`

   reader trap が実 builder からの呼出しを捕捉する。パス不在の例外を kill 理由にしない。AST 検査も同時に走らせる集合は、この単一理由案から外す。

10. **M10a — K2 外側 metadata の脱落**

    - file: `C/p3_s4_loop.py`
    - old:
      ```python
      "output": record[role + "_output"],
      ```
    - new:
      ```python
      "output": ({key: value for key, value in record[role + "_output"].items() if key != "knowledge_use"} if role == "coder" else record[role + "_output"]),
      ```
    - 期待 node: `{L::test_agent_live_actual_no_build}`

    role 検証済みの capture から保存時だけ削る。取込み前に削る案は role schema に拒否されるため除外する。

11. **M10b — input hash の計算元変更**

    - file: `C/p3_s4_loop.py`
    - old:
      ```python
      "output": output, "input_sha256": agent_outputs.canonical_sha256(declared_input),
      ```
    - new:
      ```python
      "output": output, "input_sha256": agent_outputs.canonical_sha256(output),
      ```
    - 期待 node: `{L::test_agent_ingest_three_stages_preserve_campaign}`

    SHA の形は有効なので envelope 検証は通り、独立した入力 hash の期待値との比較で落ちる。

12. **M11 — witness の null 許容**

    - file: `C/layer3_schema.json`
    - old:
      ```json
      "commit_counts": {
                      "type": "integer"
                    }
      ```
    - new:
      ```json
      "commit_counts": {
                      "type": ["integer", "null"]
                    }
      ```
    - 期待 node: `{R::test_verification_witness_and_proof_invalid_schema[null_count]}`

    完成した payload を schema に直接渡すため、producer の null 拒否や admission が先に働かない。

13. **M0 — 等価変異、SURVIVED 期待**

    - file: `C/agent_outputs.py`
    - old:
      ```python
      # A directory lock also covers initial creation: no extra persistent lock
      ```
    - new:
      ```python
      # The directory lock also covers initial creation: no extra persistent lock
      ```
    - 実行 node: `{A::test_roundtrip_three_stages}`
    - 期待失敗 node: `{}`

    コメントだけの変更。注入後 diff の実在確認を省略しない。

## 総括

**追加 must-fix は 4 件**: critic の空白処理不一致、code block の偽見出し、D830 検査の不足、非 null variant の受理条件不一致です。

双射と指定 pin は静的に成立しています。M1〜M11・M0 は一意な置換案を提示しましたが、kill・SURVIVED と 5 分上限への適合は未実測です。コード編集・テスト実行・commit・push は行っていません。