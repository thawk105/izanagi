# [T-2159] C05 の schedule 正本 — 実装しない裁定と、実装に必要な 5 件の択一

**日付:** 2026-09-02
**wave:** `worktree-dev-wave-t2159-c05-schedule-authority`
**base:** local main `24b31d2a37353d63a4f715ed2170d13e25df3fe3`
**実装面の差分:** ゼロ (裁定により実装しない)

## 1 行で

裁定 D1448 は「引数を捨てて必ず例外を送出する schedule 権威の解決経路について、C05 の
schedule 正本を新設する」と定めたが、**実装すると権威のない仕様を 4 件その場で決めることになり、
かつ D1448 の前提 (これを直せば正式経路が生きる) が成り立たない**ことを実測で確かめた。
実装せず、新事実を添えてユーザー再裁定へ返す。runbook の stale 記述だけを訂正した。

## 2. 先行 wave が「3 矛盾」と記録した点は、いまは 1 件だけである

T-1380 (2026-08-27) は schedule authority 18 field のうち 3 件が実運用の値と矛盾すると記録した。
本 wave が `validate_authority` へ production 実値を通して測ったところ、**落ちるのは 1 件だけ**だった。

|field|T-1380 の記録|本 wave の実測|
|---|---|---|
|`leakproof_context`|文字列 vs object 要求で矛盾|`{"text": ...}` で包めば通る。射影で解ける|
|`descriptor_binding`|cell ごと vs 全 cell 共有で矛盾|型としては通る。意味の妥当性は別問題 (§4 R2)|
|`whiteboard`|正式初期状態の空配列を非空要求が拒否|**唯一の不合格。ここを開けない限り authority は組めない**|

残り 15 field は production 実値または健全な代用値で受理された。逐語は
`verbatim/s4-measurements.md` の M12 にある。

## 3. 12 述語の実測 (runbook 訂正の根拠)

`s8c_preregistration_evidence.evaluate_all("HEAD", repo_root=...)`:
**C10 = SATISFIED、C03 = UNSATISFIED、残り 10 件 = EVIDENCE_UNDEFINED。**
C05 は `EVIDENCE_UNDEFINED / schedule-schema-absent` (artifact 不在の第 1 分岐)。
runbook の「12 述語の SATISFIED が 0 件」は stale で、正しくは 1 件である。本 wave で訂正した。

## 4. 実装しない理由

### 4.1 権威のない仕様を 4 件、実装が決めることになる

- **R1/R2.** `whiteboard` の空配列を受理する規則、`leakproof_context` を包む field 名、
  `descriptor_binding` の表形式。18 field の名と型対応は D530 が裁定した範囲の外で、
  実装著者の選択だったことが記録に残っている。schedule の hash はこの形から決まるので、
  **実装が決めた形を実装が検証する**構図になる。
- **R3.** 事前登録 §5 の予算欄は「総上限と arm ごと・holdout ごとの上限」だけを定め、
  cell ごとの予約値を含まない。プランはこの欄へ 4 つ目の key を人に書かせる設計で、
  consumer が規範側の欄書式を決めることになる。
- **R4.** 予算台帳の正本 path が未裁定。`reserve_all_cells` は呼び手の path をそのまま使う。

段 3 の 2 レンズは別々の主題 (受理集合と恒真化 / 権威の出所と順序) から独立に同じ結論に達した。
先行 T-1380 でも独立した敵対相談 4 本が暫定権威を不採用と勧告している。

### 4.2 D1448 の前提が不完全である

- `registered-effective` の admission は発効済み事前登録 capability を要求し、発効は
  **12 述語すべての SATISFIED** を要求する。`_evaluate_c05` は全条件を満たしても終端が
  `EVIDENCE_UNDEFINED` であり、`SATISFIABLE_CONDITION_IDS = {"C10"}` が C10 以外の
  SATISFIED を ERROR へ倒す。**したがって本件を実装しても正式起動は 1 ビットも近づかない。**
- 共有 8b ratified freeze は今も未発効 (`[no-active] live active pointer が無い (v2 未発効)`)。
- D959 は同じ経路を「上流に従属する下流症状であり、順序を入れ替えて先に解除してはならない」と
  定めている。D1448 は同じ対象を名指しした後発裁定だが、**D959・上流閉塞・未発効の批准凍結への
  言及が裁定文にも worklog 1184 の該当行にも無い。**

## 5. 併せて実測した既存の穴 (本 wave の変更に起因しない)

- **R5. 試行 slot の `schedule_row_sha256` が C05 の schedule と結線されていない。**
  検査 (`attempt_registry_core.py:1077`) は slot 自身が記録した値を読み返すだけで、
  schedule artifact から当該 hash を導く producer が存在しない。C05 の権威を実装しても、
  どの slot がどの schedule 行に対応するかは誰も保証しない。
- **R6. 全 cell の予約値 0 が受理され、予算保証が恒真化する。**
  `_check_limit_state` は「予約の和 ≤ 上限」しか見ないので、全ゼロ予約は `held` になり run が続く。
  事前停止にならない。規範が要求する「arm 上限の対称性」「holdout 上限の和 = 総上限」を
  検査する consumer も無い。
- **R7. C05 の評価器は artifact の中身を一切検証しない。** 空 bytes でも非 JSON でも第 1 関門を通る。
  D549 自身が「artifact/authority の中身の正当性を問わない」と明記している。
  したがって「artifact を置けば C05 の理由コードが進む」ことは、正しい schedule を発行した
  証拠にならない。先行 wave も同じ理由で自らの value 主張を取り下げている。
- **R8. schedule と予算の検証位置が遅い。** attempt slot の予約・分類・lifecycle 開始の後に
  検証される。「実走前に固定・検証」の失敗境界になっていない。

## 6. 実装を再開するために決める 5 件

いずれも受理集合か正本の形を変えるので、AI は既成事実にしない。親の推奨を添えて返す。

1. **順序** — D959 の「上流を先に解く」を D1448 が明示的に上書きするか。
   **推奨: 上流 (許可リスト側) を先に片付ける。** 本件だけを実装しても正式起動は近づかず、
   未裁定の schema だけが source へ固定される。
2. **`whiteboard` の扱い** — (a) authority から外す / (b) 空を表現できる versioned schema へ改訂 /
   (c) 呼び手供給のまま据え置く。**推奨: (b)。** 観測が 0 件であることは初期状態の本質なので
   digest に入れる価値があるが、それは空配列の特例ではなく明示的に表現できる形であるべきである。
3. **cell ごとの予約値の置き場所** — §5 の予算欄か、6 cell manifest か。
   **推奨: manifest。** §5 は総量の欄で、cell 単位は manifest の担当である。
   あわせて規範が要求する対称性・合計一致の検査を予算 consumer へ入れる。
4. **予算台帳の正本 path** — 単一固定か manifest 由来の派生名か。台帳の再利用単位と
   identity の意味を同時に決める。
5. **schedule 行 hash の正本形** — slot の `schedule_row_sha256` の preimage を定め、
   genesis producer と C05 schedule を同じ digest で結線する。

## 7. 親が訂正した自分の誤り

段 1 brief の実アンカー表で `test_p3_autonomous_workload_trial.py:9053` を
「現状の raise を固定する test」と書いたが、実際は loader を成功 lambda へ差し替える monkeypatch で、
**無条件 raise を期待値として pin するテストは存在しない**。段 3 レンズ A が指摘し、親が現物で確認した。
この誤りは裁定の向きを変えない (実装しても既存テストの期待値を変える必要は生じない、という向きに効く)。

## 8. verbatim

- `verbatim/s1-brief.md` — 段 1 brief (誤りを含む。§7 参照)
- `verbatim/s1-measurements.md` — 段 1 の実測 M1〜M7
- `verbatim/s2-plan.md` — 段 2 プラン
- `verbatim/s3-lens-a.md` — 段 3 レンズ A (受理集合と恒真化)
- `verbatim/s3-lens-b.md` — 段 3 レンズ B (権威の出所と順序裁定との抵触)
- `verbatim/s4-adjudication.md` — 段 4 裁定
- `verbatim/s4-measurements.md` — 段 4 のための追加実測 M8〜M14

### erratum — 逐語 3 件へ加えた可逆最小正規化 (DW-S07)

子の出力には markdown の強制改行 (行末の連続空白) が含まれ、`git diff --check` が赤になった。
**可視文字を変えない行末空白の除去だけ**を行い、原文を次のとおり記録する。復元は各行の
行末へ半角空白 2 個を戻せばよい (対象は下記 4 行で、いずれも `## 総括` 節の結論行)。

|file|正規化前 sha256|正規化前 bytes|除去した行|
|---|---|---|---|
|`verbatim/s2-plan.md`|`424dc44cb0d3ac4c3876a7b7fd285b53d05d33f228f29be9d1b9792f078e4340`|25130|2 行 (推す案・理由)|
|`verbatim/s3-lens-a.md`|`df2fc7c6d1265461b6ccd402f22754c593146278f3f8ae4ffe696ff842719659`|18080|1 行 (実装可否)|
|`verbatim/s3-lens-b.md`|`96ee22882e48c40ae1e7d432839932ff4764a99e4d2eaed86a94eaff93355d93`|16309|1 行 (実装可否)|
