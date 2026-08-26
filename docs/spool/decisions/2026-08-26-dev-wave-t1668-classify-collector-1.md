---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1668-classify-collector
seq: 1
---

## {{D:read-before-output-means-before-derivation}}. 「性能出力を読む前」は「性能量が導出される前」と読む

**決定:** D510 決定 4 の「出力を読む前に分類を確定する」は、**性能量が分類器から
到達可能になる前**と読む。OS レベルの read より前という literal な解釈は採らない。
成果物には literal な read 前ではないことを明記し、誇張しない。

**理由:**

- `subprocess.run(capture_output=True)` は return 前に pipe を読む。capture 方式である限り
  literal な「OS-level read 前」は達成できない。段 3 の敵対相談がこれを file:line で示した。
- 決定 4 が防いでいるのは「性能値を見てから分類を選ぶ」ことである。bytes が封じられた
  buffer に在るだけでは性能量は 1 つも導出できない。防いでいる性質は導出時点で決まる。
- 実装上の帰結として、return code は**流量制御に使ってよいが分類には使わない**。
  失敗した rep の後に後続 rep を起動しない旧挙動は、rc を分類器へ渡さない限り
  この決定と両立する。これを崩すと絶対規律 1 (観測者効果の分離) 側で
  spawn 総数と一時領域の生存期間が変わる。

**却下した選択肢:**

- literal な OS-level read 前を要求する — stdout/stderr を起動器が管理する file へ
  直接 redirect する設計になり、一時領域の生存期間と観測者効果の再監査が要る。
  得られる強度の差は「封じた buffer から性能量を導出できるか」であり、そこは
  型と所有で塞げる。費用に見合わない。
- 解釈を書かずに実装する — 後続の wave が「閉じた」と誤認しうる。D797 が
  同じ誤認を名指しで警戒している。

## {{D:no-authority-registration-without-value-to-reason-table}}. 値と理由の対応表が確立するまで復帰 authority を登録しない

**決定:** scheduler accounting collector は作るが、
`_FLOOR_RECOVERY_AUTHORITIES` へ authority を登録しない。空のまま維持し、
空である理由 (実測した値域と、未確立の対応表) をコードのコメントとテストで固定する。
登録の時期はユーザー裁定へ返す。

**理由:**

- 本環境の scheduler は `qstat -J -f <request>` で `Exit Code` と `Execution Host` を
  出す。job 自身が書けない surface であり、外部証拠として使える。
  会計エピローグ (`<script>.e<ID>`) に exit status が無いのは事実だが、
  「理由を名指しする情報が無い」わけではなかった。
- ただし `Exit Code` の実測値域は `(none)` 263 / `1100` 4 / `F` 3 / `9` 2 / `A` 1 で、
  すべて過去の cluster probe が意図的に作った条件の観測である。**どの値が
  `node_failure` / `scheduler_external_interruption` を名指しするかを裏付ける資料が無い。**
  `9` は SIGKILL を思わせるが、D740 は walltime kill と SIGKILL の自己申告を
  閉集合から除いており、scheduler が報告した `9` がそのどちらでないと言える根拠は無い。
- 対応表が未確立のまま登録すると、収集器が正当に発行できる受領証は 0 件のまま、
  admission が受理する bytes の集合だけが広がる。admission が検査するのは
  authority pair と schema であって「収集器が作った」ことではない。
  **正当な発行が 0 件のまま受理集合だけを広げるのは絶対規律 2 が禁じる向きである。**
- D880 は本作業へ登録を割り当てたが、それは「収集器を作れば分類できる」ことを
  前提にしていた。前提が崩れたので、親が不採用にせず新事実を添えて再裁定へ返す。

**却下した選択肢:**

- 値の意味を推測して規則表を書く — 到達可能性を実測せずに述語を採用する形で、
  gate が恒真または恒偽になる。実測した値域を裁定へ書くのが正しい。
- 収集器も作らない — D843 が「同じ変更単位で作る」と裁定した対象そのものであり、
  受領証契約を 2 度設計することになる。

## {{D:trusted-launcher-lands-unconnected-with-stated-blocker}}. 信頼側の起動器は未接続のまま land し、阻む不整合を明記する

**決定:** 信頼側の起動器と収集器を 1 つの変更単位として land する。
床値 campaign を起動器へ配線する作業は本変更に含めない。
「床値 campaign はまだ起動器を使っていない」ことと、その理由を成果物へ明記する。

**理由:**

- 配線は構造的に成立しない。`S8B_RETRYABLE_FAILURE_REASONS` は空であり、
  transition policy は `require_previous_terminal` と
  `require_terminal_reason_equals_classification` を要求する。統計的に無効になった
  session の pre-output 分類理由は `None` なので `retryable-failure` terminal を作れず、
  `attempt_ordinal > 0` は terminal 経路から永久に開かない。recovery 経路も
  規則表と authority が空なので発火しない。**床値 campaign の通常の測り直しが
  台帳の slot をひとつも取れない。**
- 床値 protocol は cell ごとの測り直し枠を前提に組まれているため、これは
  稀な経路の破れではなく、protocol が計画している運用が成立しないことを意味する。
- この不整合は D880 が「既知で、別裁定へ回す」と明記した事項である。
  解消するには受理集合を広げるしかなく、親が決めてよい範囲を超える。
- D843 の決定文が「同じ変更単位で作る」と結んだ対象は**起動器と収集器**である。
  両者は 1 つの変更単位として作られており、決定の要求は満たしている。

**却下した選択肢:**

- 配線まで押し通す — 最初の測り直しで campaign が止まる実装を land することになる。
- 何も land しない — 起動器と収集器は完成しており、受領証契約を共有する形で
  作られている。破棄すると同じ設計をもう一度やり直すことになり、D843 の理由に反する。
- 起動器だけを後回しにする — D843 が名指しで却下した「片方だけ先に作る」形である。
