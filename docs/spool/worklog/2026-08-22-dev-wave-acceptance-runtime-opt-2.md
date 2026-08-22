---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-acceptance-runtime-opt
seq: 2
title: 受入全走の時間内訳を実測し、3件の高速化候補を特定したが安全性未証明のため本waveでは実装しない (docsのみ、branch worktree-dev-wave-acceptance-runtime-opt)
---

## 本文

- ユーザー依頼「受入全走の時間改善。最も時間がかかっているところはどこなのか？それを論理的に
  より賢い処理の仕方やより賢い並列実行の仕方で改善できないか？陳腐化したテストを削除して
  早くできるか？やってくれ。リワードハック禁止」を受け、事前に特定のT番号は無い状態で開始した。
- 一次資料を精読し、この主題が D531/D532/D585/D591/D600/D612/D620/D634/D636 と
  `output/insights/2026-08-11_t813-acceptance-sharding/` package という極めて濃密な既決定の
  蓄積を持つと判明した。**「テストの削除・skip・selection縮小で速くする」はD532が既に規律2違反
  として検討対象外と明記**しており、本waveもこれを再提案しなかった (ユーザーの「リワードハック
  禁止」指示と正確に一致)。
- 新事実として、2026-08-22の受入全走6件でpytest wallが220.89〜274.22秒と、D531/D532時代
  (2026-08-18、逆算wall≈99〜128秒) の約2倍に伸びていることを実測した。一方D636直後の
  66-node鎖再測定は76.46秒 (D591基準と3%以内一致) で、**鎖自体は縮小方向にある** —
  詳細は {{D:acceptance-wall-model-needs-refresh}}。
- `--durations=60` 診断走行で、鎖に属さない個別テストが60秒級・87秒級・42〜50秒級×10件で
  見つかった。3候補を段2 codex (read-only、reasoning=max) がfile:line粒度でプラン化し、
  段3敵対相談2レンズ (正しさ境界／整合性・実効性・scope) で攻撃させた。
- **候補1** (`test_dev_wave_wait.py`の防御的30秒待ちを15秒へ短縮): レンズAが
  `docs/failures.md`の既知事例 (48-worker全走中の外部subprocess待ちが個別には十分な
  timeout値でもcontention下でtimeoutした再発群) を根拠に安全性未証明と指摘。親も
  production側にreadiness marker機構が無いことを確認し、実測なしでの採用を見送った
  ({{D:dev-wave-wait-timeout-not-reduced-without-measurement}})。
- **候補2** (`test_s8b_floor_campaign.py`の10テストがproduction `build_cells`のtest-local
  build cacheで実CCBenchビルドを毎回やり直している疑い): 親が対象テストを単独実行すると
  17.96〜18.16秒、全体スイート内では50.39秒 (2.8倍) と実測し、構造仮説を補強する signal を
  得た。レンズBは「resume-onlyの小さなpilot」ならより安全と指摘したが、cross-process lock安全性・
  false-green回避 (D585と同型の教訓) が未検証のため専用waveへ送った
  ({{D:floor-campaign-build-cache-sharing-deferred}})。
- **候補3** (`test_real_repo_serialization.py`のreal-repo優先順位メタテストが毎回3回
  collectionする、87.46秒で単独最長): 正しさ機構自体を検証するメタテストであり、
  3variantの冗長性の証拠が無いため削減を見送った
  ({{D:real-repo-collection-triple-invocation-not-reduced}})。
- 別セッション「stage 7 optimization catalog research」(worktree
  `dev-wave-tictoc-cicada-catalog-card-i5-fix`) が投入した受入ジョブ (`932594.nqsv`) が
  CPU Time凍結でハングしているのを発見し、SendMessageで通知した。先方が独立に確認・qdel実行、
  こちらから`dispatch-qdel-arms-f47-latch`memoryの知見も共有した。本waveの受入とは無関係。

## 次の一手差分

### 新規

- {{T:acceptance-wait-readiness-marker}} **P2・新規**: `tools/dev_wave_wait.py`の
  `producer`サブコマンドへ、poll loop到達を示すreadiness marker機構 (production側の変更) を
  追加し、`test_dev_wave_wait.py::test_producer_waiter_kill_requires_later_check_only_receipt`
  の防御的30秒待ちを、固定マージンではなくreadiness観測ベースの短い待ちへ置き換える。
  代替として、共有負荷下でのA/B実測 (複数回) で15〜20秒の安全性を直接示す経路でもよい。
  正本 = {{D:dev-wave-wait-timeout-not-reduced-without-measurement}}。
- {{T:floor-campaign-build-cache-pilot}} **P2・新規**: `test_s8b_floor_campaign.py`の
  `build_cells`呼出しの区間別計測 (cache lookup/実ビルド/validation) をまず行い、実ビルドが
  支配要因と確認できたら、fresh-build系テストを除外したresume/certificate系テストだけの
  build cache共有pilotを、cross-process lock安全性とfalse-green回避を専任で攻撃する段3レンズ
  付きで設計する。正本 = {{D:floor-campaign-build-cache-sharing-deferred}}。
- {{T:real-repo-priority-collection-redundancy-audit}} **P3・新規**: `test_real_repo_
  serialization.py::test_real_repo_priority_order_is_literal_and_writers_follow_barrier`が
  行う3回のcollection (base/`--ff`/`--nf`) それぞれの検出対象を対応表にし、削減可能な
  variantがあるかnegative controlで検証する。正本 =
  {{D:real-repo-collection-triple-invocation-not-reduced}}。
