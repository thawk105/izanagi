---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1668-classify-collector
seq: 3
title: [T-1668] scheduler accounting collector と信頼側の起動器を同じ変更単位で作る (コード + docs、branch worktree-dev-wave-t1668-classify-collector)
---

## 本文

- **裁定の前提が 1 つ崩れた。** brief は「この計算機の scheduler は失敗理由を名指しする
  情報を出さない」と書いたが、親が実測して誤りと確認した。`qstat -J -f <request>` は
  request block ごとに `Execution Host` と `Exit Code` を出す。job 自身が書けない
  login 側の surface であり、D510 決定 4 の言う「性能出力の外側の証拠」に当たる。
  会計エピローグ (`<script>.e<ID>`) に exit status が無いのは事実だが、
  それが証拠源の全体ではなかった。収集器の証拠源をこの surface へ変更した。
- **ただし値と理由の対応表は未確立で、規則表は空のまま land する。**
  `Exit Code` の実測値域は `(none)` 263 / `1100` 4 / `F` 3 / `9` 2 / `A` 1 で、
  すべて過去の cluster probe が意図的に作った条件の観測である。どの値が
  `node_failure` / `scheduler_external_interruption` を名指しするかを裏付ける資料が repo に無い。
  `9` は SIGKILL を思わせるが D740 が walltime kill と SIGKILL の自己申告を閉集合から
  除いており、scheduler が報告した `9` がそのどちらでないと言える根拠が無い。
  DW-O13 の「値を実測して到達可能性を確かめるまで述語を採用しない」に従った
  ({{D:no-authority-registration-without-value-to-reason-table}})。
- **床値 campaign の配線は取り下げた。** 段 6 の敵対レビュー 2 本が独立に同じ構造問題を
  指摘し、親が現物で確認した。`S8B_RETRYABLE_FAILURE_REASONS` は空で、transition policy は
  `require_previous_terminal` と `require_terminal_reason_equals_classification` を要求する。
  統計的に無効な session の pre-output 分類理由は `None` なので `retryable-failure` terminal を
  作れず、`attempt_ordinal > 0` は terminal 経路から永久に開かない。recovery 経路も
  規則表と authority が空なので発火しない。**床値 campaign の通常の測り直しが台帳の slot を
  取れない。** これは D880 が「既知で、別裁定へ回す」と明記した不整合であり、
  解消には受理集合を広げるしかないため親の裁定範囲を超える
  ({{D:trusted-launcher-lands-unconnected-with-stated-blocker}})。
- **段 3 の最重要所見は refuted だった。** sol レンズは
  「observation 後の recovery を core が受理する」を規律 2 の穴として挙げ、親も一度
  real と裁定した。段 5 の実装子が既存テストとの矛盾を理由に無編集で停止したため
  再確認したところ、`test_verified_recovery_closes_slot_and_opens_exact_next_ordinal` は
  `node-before-observation` と `scheduler-interruption-after-observation` の**意図的な対**で
  あり、観測後の recovery を受理するのが設計だった。D739 が recovery を作った動機は
  「計測 process の消失で terminal を書けなくなった attempt」であり、process は観測を
  始めた後に消えうる。値を見てから障害を騙る経路を塞いでいるのは観測の不在ではなく、
  外部 scheduler 証拠と recoverer の fencing の 2 つである。共有 core の編集を取り下げた。
- **子の「完了」報告を実走で検証して 1 件外れた。** fix2 は 6 項目すべてを `closed` と
  報告したが、親が計算ノードで実走すると自分たちが足したテストが落ちていた
  (rep 間の一時領域の後片付けが効いていない)。fix3 の prompt では
  「実走していない項目は `closed` でなく `unverified` と書け」と明示し、fix3 は全項目を
  `unverified` で返してきた。子は計算ノードへ dispatch できないため実走できない。
- **段 8 の docs 追記が byte 予算で入らなかった。** 実測に基づく手順改善 2 件
  ({{F:adversarial-prompt-blocked-by-content-filter}} と
  {{F:background-launch-output-discarded-hides-start-failure}} の恒久対応) を
  `docs/dev-wave/workers.md` の `DW-S03` と `docs/dev-wave/operations.md` の `DW-O01` へ
  入れようとしたが、L1.5 層の unique footprint 予算 (9566 bytes) に空きが無く、
  60 bytes の追記でも超過した。予算のために既存の安全義務を削らない規律に従い、
  追記を撤回して memory へ置いた。予算の扱いはユーザー裁定へ返す。
- **エージェント工数**: codex 子 12 本 (plan 1 / consult 3 (うち 1 は内容フィルタ拒否、
  1 は provider の容量エラーで中断) / author 6 (うち 1 は既存テストとの矛盾で無編集停止) /
  fix 3 / review 2)。dispatch した焦点走 6 回、変異走 2 回 (probe + 本走、各 8 走行)。

## 次の一手差分

### 完了

- [T-1668] 収集器と信頼側の起動器を同じ変更単位で作った。分類は create-only の受領証へ
  封じてから出力を開く順序で確定し、収集器は login 側 `qstat -J -f` を読む。
  変異 7 件すべてが固有のテストに撃たれ、他層に mask されたものは無い。
  床値 campaign の配線・値と理由の対応表・authority 登録は本項の scope 外として
  下の新規 3 件へ分離した。
  remaining: none
  base: 26fa9f4553ff561de3c00697e3a3340df84a6d81cd7c03147c26965fc48fc5cb

### 新規

- {{T:floor-retry-ordinal-axis}} **P1・ユーザー裁定待ち**: 床値 campaign の統計的
  測り直しと attempt registry の `attempt_ordinal` が別軸で、`S8B_RETRYABLE_FAILURE_REASONS`
  が空のため配線できない。D880 が別裁定へ回した不整合の解消。
- {{T:exit-code-to-reason-table}} **P1・新規**: `qstat -J -f` の `Exit Code` が
  `node_failure` / `scheduler_external_interruption` のどちらを名指しするかを確立する。
  共有計算環境で故障を意図的に起こせないため、運用中の偶発事例の収集か事業者資料の確認が要る。
- {{T:recovery-authority-registration-timing}} **P1・ユーザー裁定待ち**:
  `_FLOOR_RECOVERY_AUTHORITIES` への登録時期。D880 は本作業へ割り当てたが、
  対応表が未確立のままでは正当な発行 0 件のまま受理 bytes だけが広がる。
- {{T:classification-crash-window}} **P2・新規**: 分類受領証を封じた後、出力を開く前の
  crash で封じた bytes が復元不能になり slot が停止する。恒久解は durable な
  raw-output store の新設。fail-closed 側で誤った成果物は作らない。
- {{T:classification-receipt-reference-chain}} **P2・新規**: 分類受領証が certified
  artifact の参照鎖へ入っていない。受領証を削除・差し替えても result / report / floor 値の
  受理集合が変わらない。exact key pin の改訂を伴う。
- {{T:output-snapshot-test-side-effect}} **P2・新規**: `output/` の棚卸し検査 2 件が
  `output/runs/` の実在に依存し、それを作るのは別 file のテストの副作用である。
  fresh worktree の焦点走で常に赤になる。検査が要求する状態を同じ file の中で作る形へ直す。
- {{T:dev-wave-l1-5-budget-full}} **P2・ユーザー裁定待ち**: dev-wave reference の L1.5 層が
  予算満杯で、実測に基づく手順改善が 60 bytes でも入らない。予算値の引き上げは
  通常の自己改善に含めず独立審査とする規約のため裁定へ返す。
