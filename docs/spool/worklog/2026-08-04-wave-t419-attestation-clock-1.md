---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t419-attestation-clock
seq: 1
title: [T-419] 較正の取り直しでは開かないことを実測で確定し、取得時の自己整合 gate だけを入れた — 帯外サンプルは probe 自身の観測者効果 (コード + docs、branch worktree-wave-t419-attestation-clock)
---

## 本文

- **ユーザー裁定 (2026-08-04) の一次控えは `rulings-inbox/2026-08-03-task-def-rulings.md` §4 で、
  台帳へは (171) が既に写していた。** 本 wave はその裁定を実行しようとして、
  **裁定の前提が現行 probe では成立しないこと**を実測した。
- **段 1 の前提実測 (追加計測ゼロ + ログインノードの読み取りのみ)。**
  `/proc/cpuinfo` の `cpu MHz` を読む probe は、**読み取っているプロセス自身が乗るコアが
  turbo にいる**ため必ず帯外サンプルを生む。`/proc/self/stat` の processor field を同時に採ると
  6 回中 6 回、自分の走行 CPU が帯外側に現れた。
  Pegasus 由来の観測は、重複を除いた **23 の標本列すべて**が 2% 帯外の要素を 1〜2 個持ち、
  残る 46〜47 要素は例外なく厳密に 2101.0 だった (内訳: `output/` 配下の JSON 成果物由来 21 +
  実行時 observed 列 2。出現回数 24 のうち、登録済み較正の列が 4 箇所に複製されている)。
  実行時 2 脚の帯外位置は index 34 と 27 で互いに異なり、登録済み較正の index 40 とも異なる。
- **したがって裁定が期待した効果は現行 probe では達成されない。** 較正を取り直しても
  同じ効果が焼き込まれ、かつ **observed 側も毎回帯外要素を出す**ため実行時述語は通らない。
  (171) は「較正の再取得と受入検査の実装が済めば開く」と記録したが、**これは訂正が要る。**
  {{F:attestation-probe-observer-effect}} に記録した。
- **親 brief の 2 つの過剰主張を段 3 の敵対レンズが反証した。** (a) 観測件数を 16 と数えたが
  実際は相異なる 23 (親の glob が `calibration/**` に閉じていた)、(b) 「原理的に不可能」と書いたが、
  述語自体は全要素帯内の観測を通すので、正しくは「現行 probe と config では塞がれたまま」である。
  **計算ノードでの自 CPU 因果は未立証**のままで、成果物が probe の走行 CPU を保存していないためである。
- **本 wave は封じ込め (containment) だけを行った。** 取得時 (CLI publish 経路) の自己整合 gate、
  契約 registry 全走査の不変条件、canonical 述語の golden vector を入れた。
  **Pegasus の campaign は開いていない。** 判断は {{D:effective-clock-self-consistency-gate}}。
- **段 6 の敵対レビュー 2 本と焦点再レビュー 2 巡。** レビュー B が
  「gate は CLI publish しか守らない」「`tolerance_pct` は手入力で権威束縛がなく 100 を渡せば
  gate も実行時述語も恒真化する」「単純な事実 pin は将来の反転を強制しない」を摘出した。
  1 巡目の焦点再レビューは **NO-GO** で、CLI テストが実 probe の形を写しておらず
  「CLI が渡す許容幅を定数へ固定化する変異」が生存すると判定した。2 巡目の fix で
  2 つの異なる許容幅を通す pin を入れ、3 巡目で GO になった
  ({{F:attestation-e2e-fixture-clamped-observation}})。
- **E2E fixture が観測を帯内へクランプしていた。** 実 probe が決して作らない観測で防壁を通しており、
  E2E は構造的にこの型を検出できない。除去は本 wave の変更面でないため未実施。
- **段 8 の dev-wave 改善候補 1 件は予算に入らなかった。** 計算ノードへ dispatch する検査に
  外側 timeout を掛けて自分で殺した (`signal 15`、ジョブ 1 本を無駄にした) ため、
  `DW-M05` と同じ「外側の実行時間上限に掛からない経路で起動する」義務を `DW-O18` へ足したいが、
  `docs/dev-wave/` は合計 25,199 / 25,200 bytes で**残り 1 byte** である。
  **上限引き上げは提案せず、追記しない。** (169) の V5 に続く 2 例目であり、
  `DW-G03` の「独立 2 例」を満たすため裁定へ返す。
- **実測 (2026-08-04、worktree `wave-t419-attestation-clock`)。**
  local main 取り込み (`4f0d020`) 後の受入全走 = **5483 passed / 19 skipped / 0 failed**。
  対象テストの走 = **158 passed** (段 6 の 1 巡目 fix 後)。
  `python3 tools/check_docs.py` = 違反なし。`python3 tools/check_ai_provenance.py` は
  incoming (10 件) と full (1044 件) の双方で違反なし。
- **変異 matrix と、2 巡目 fix 後の受入全走は未実施である。** Pegasus のスケジューラが
  14:40 頃から系全体で停止し (全キューで実行中ノード 0、`qstat -Q` の STS が INA、gen_S に 230 待ち)、
  計算ノードへ dispatch する検査が 1 本も走らなくなったためである。
  変異 spec は事前登録済みで `--plan-only` の preflight は緑 (6 変異 + baseline = 7 走、
  anchor はいずれも逐語 1 箇所)。**この 2 つを実測して緑にするまで land しない。**
  ログインノードで pytest を走らせて代替することはしない (runbook の分割線)。

## 次の一手差分

### 更新

- [T-419] **P1・封じ込めを実装 (land 未了)、campaign は開いていない → probe 是正の裁定待ち**:
  取得時 (CLI publish 経路) の自己整合 gate、契約 registry 全走査の不変条件、
  canonical 述語の golden vector を実装した ({{D:effective-clock-self-consistency-gate}})。
  **裁定が期待した「較正を取り直せば開く」は現行 probe では成立しない** —
  帯外サンプルは probe 自身の観測者効果であり、較正側にも実行時観測側にも乗る
  ({{F:attestation-probe-observer-effect}}、相異なる 23 の標本列すべてが帯外要素を持つ)。
  **U-1 (probe 是正の方式) がユーザー裁定待ち**で、候補は (α) 走行 CPU を移しながら K 回読み
  論理 CPU ごとに最小値を採る (述語を緩めない)、(β) 走行 CPU を記録して 1 要素だけ除外する
  (受理集合が 47/48 へ緩む)、(γ) 帯外 1 個まで許容する (根拠が弱い)。**推奨は (α)。**
  先に計算ノードで走行 CPU・cpufreq driver・boost 設定・同居プロセスを束縛した probe 実験を置く
  (計算ノードでの因果が未立証のため)。**U-2 (較正の再取得と pin 更新) は U-1 の後** —
  `method` 文字列が動くので凍結 bytes と `env_contract.py` の path + sha256 pin を同時に更新する。
  一次資料 = D143 / F97 / `output/insights/2026-08-04_t419-attestation-clock/`
  base: 185a98e807cb7cce4785cf9c90b26bde2c8478d757244ae3c1181bfe0bf37d82

### 新規

- {{T:effective-clock-tolerance-authority}} **P2・新規**: `effective_clock.tolerance_pct` に
  権威束縛が無く、取得時に 100 を渡せば取得時 gate も実行時述語も恒真化する。
  境界検査は (0, 100] だけである。権威の出所 (policy 値か smoke 分布か) を決める。
  **較正を再登録する前の blocker** である。
- {{T:silo-ladder-clock-consumer}} **P3・新規**: `silo_ladder_rung1` に
  実効クロックの median 同士を比べる別 consumer が残っており、本 wave が触れた受理集合と別系統である。
  同じ観測者効果に対して何を保証するのかを決める。
- {{T:dev-wave-docs-budget-second-case}} **P2・新規**: `docs/dev-wave/` が上限 25,200 bytes に
  対し 25,199 bytes で、正当な自己改善が 2 回続けて入らなかった ((169) の V5 と本 wave)。
  上限を上げずに空ける方法 (陳腐化ルールの削除・テスト化・外出し) を決める。
