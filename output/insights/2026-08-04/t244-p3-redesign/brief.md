# 段 1 brief — [T-244] D121 P3 origin ledger の再設計 + 再実装 (2026-08-04、wave dev-wave-t244-p3-redesign)

- **依頼 (command 引数、worklog 候補より優先):** P3 の再実装 — (165) の敵対 2 レンズ NO-GO 所見を踏まえて設計し直す。
- **確定済みユーザー裁定:** 択一 1 = 予算値を下限式 `Q >= 1 + 32R + E_min` から再導出 ((161))、択一 3 = 軸 (iii) 必須 ((126))、D150 (P4 無条件化・非適用二分)、D147 (前回差し戻しの裁定)。P10 (予算値・origin authority・軸 (iii)) は 3 点成立。
- **(P1) provisional・攻撃対象:** 本 wave のユーザー起票を「(165) 裁定パッケージ U-A〜U-G を親推奨どおり採用する」の意思表示と読む。rulings-inbox に個別控えは無い (2026-08-04 実測)。
- **設計拘束 (U-A〜U-G 推奨の具体化):**
  - U-A: `origin_id` = authority manifest の canonical digest。manifest schema は設計本文 §3.5 の列挙を固定。caller handle 禁止。
  - U-B: cell key = (descriptor SHA・axis semantics・verifier policy・environment contract) で registry が同一 cell の 2 件目発行を拒否。
  - U-C: authority root は repo 内固定 path 1 点、ledger root はそこから導出。注入は test fixture 限定。flock の適用範囲・再入契約 (A-6) をここで決める。
  - U-D: batch を ledger の第一級にする — batch-committed event で cardinality (下限含む) と全候補 digest を事前 commit、seal まで結果非公開。FSM は batch > 1 を表現する。
  - U-E: static な authority record は `git cat-file` committed bytes 照合。mutable runtime head は分離し「削除検出」と名乗らない。
  - U-F: 予算 policy は floor 制約 1 件以上を必須。値は authority 注入、ハードコード禁止。
  - U-G: 名乗りは「P3 用 origin-ledger prototype (codec / FSM / registry)」まで。**「P3 充足」と記録しない。** producer / consumer 結線 (P7) と正式 report / proof chain への配線は scope 外 (受理集合の変更 = D96 手続、別 wave)。
- **設計メモ must-fix の継承:** A-3 (`head-prepared` を state commitment の中へ)、A-4/A-5 (replay の idempotency、provider 副作用は leaf の外であることの明記)、A-8 (テスト vector V1/V2/V4/V7/V9/V12/V14 の是正)。変異事前登録候補 6 件 (A-11) は本 wave の段 4 で事前登録する。
- **(P2) provisional・攻撃対象:** `DW-G04` は U-G の名乗り格下げと「ユーザーが直接起票した再実装」で満たすと読む。発火 (production 結線) は D96 wave に属し、本 wave の成果物は結線されない。
- **既存被覆 (性質、`orchestrator/tests/test_t126_qualification_artifacts.py`):** 重複投入拒否 (m7a)・retry-of-retry 拒否 (m7b)・観測後 retry 拒否 (m7c)・publish 境界ごとの crash 回復・生存成果物からの台帳欠落拒否は既存。**純増検出力** = state commitment による CAS、全 root 削除への committed-bytes anchor、同一 cell への重複 origin 拒否、batch freeze (seal まで非公開を含む)、floor 必須 policy。
- **不変条件:** `FROZEN_MANIFEST` (output/ 23 path) に触れない。cap-lift 上限 (`MAX_APPROVED_GENERATIONS = 1`) 不変。production 挙動・受理集合不変 (未結線 leaf + 新規テストのみ)。既存 qualification 台帳は import 共有化しない (D147 却下案 (c))。campaign WAL (`wal.py`) に触れない。`DW-O13`: manifest の各 field (descriptor SHA / axis semantics / verifier policy / environment contract / IR schema・emitter SHA 等) が実成果物のどの field に実在するかを段 2 で逐条確認する。
- **成果物の形:** 新規 leaf (`orchestrator/campaign/` 配下、具体名は段 2)、専用テスト、insight 逐語 (`output/insights/2026-08-04_t244-p3-redesign/`)、spool fragment (worklog + decisions)、変異 matrix + 受入全走。
- **`DW-G05`:** 実装しなければ cap-lift 無条件義務 P3 が引き続き未充足で、多世代開放は開かない。現時点の certified 選択・レポート・台帳の値は実装有無で不変 (未結線のため)。
- **分割方針:** 軽量版にしない (NO-GO 再設計 = 設計択一が割れた面) — 段 2 プラン起草 1 本、段 3 敵対 2 レンズ、段 5 実装子 1 (leaf + registry + テスト所有)、段 6 敵対レビュー 2 本 + fix。受入は login node、`tools/run_tests.py` 全走 + 変異 matrix。性能計測なし。
