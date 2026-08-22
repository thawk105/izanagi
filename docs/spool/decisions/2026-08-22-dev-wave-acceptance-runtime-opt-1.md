---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-acceptance-runtime-opt
seq: 1
---

## {{D:acceptance-wall-model-needs-refresh}}. 受入全走の wall は D531/D532 時代より大幅に伸びており、鎖モデルだけでは説明できない

**決定:** D531 (wall=real-repo直列鎖+固定費約26秒) の**モデル自体**は正本のまま維持するが、
2026-08-18 時点の実測値 (鎖77.5〜94.9秒、逆算 wall≈99〜128秒) は現在の状態を代表しないと
記録する。改善提案の要否判断は、今回実測した新しい基準値 (下記) を出発点にする。

**理由:**
- 2026-08-22 の受入全走 6 件で pytest wall 220.89〜274.22 秒を実測した
  (branch dev-wave-t1314-layer3-report-external-campaign / t1479-known-violation-merge-authorship-job /
  rulings-20260821-calibration-registration の各 acceptance-child ログ)。D531/D532 時代の逆算値
  (約99〜128秒) の約2倍である。
- 一方、real-repo直列鎖はD636 (2026-08-21) の直後測定で66-node相当76.46秒まで戻っている
  (D591基準79.02秒と3%以内で一致)。**鎖は縮小方向にあるにもかかわらず wall は伸びている** —
  D531/D532が前提とした「鎖以外の仕事は鎖の下に隠れる」が現在は成立していない可能性が高い。
- 本 wave の診断走行 (`--durations=60`、2026-08-22、273.14秒) で、鎖 (`REAL_REPO_SERIAL_NODES`、
  現在67件) に属さない個別テストが単独60秒級 (test_dev_wave_wait.py の signal テスト)・
  87秒級 (test_real_repo_serialization.py のメタテスト)・42〜50秒級×10件
  (test_s8b_floor_campaign.py) で見つかった。うち1件を単独実行すると18秒程度で終わり、
  全体スイート内 (48-way並列) では50秒超に増える実測差 (2.8倍) も確認した — 48並列での
  CPU/IO競合が、鎖以外の要因としてwallに寄与している可能性を示す新しい観測である。

**却下した選択肢:**
- 何もせずD531/D532の数値をそのまま最新の基準として使い続ける — 上記の通り2倍の乖離があり、
  今後の改善提案の費用対効果判断を誤らせる。

再訪条件: 鎖以外のテスト群 (非chain slow tests) の並列実行下でのwallへの寄与を、D600が要求する
「因果的指標」(実際に対象を除外したA/B比較) で測定できたとき。単発のspan/wall差の観測だけでは
再訪材料にしない (D600と同じ基準)。

## {{D:dev-wave-wait-timeout-not-reduced-without-measurement}}. test_dev_wave_wait.py の受入直列待ち短縮は、実測なしでは採用しない

**決定:** `test_producer_waiter_kill_requires_later_check_only_receipt` (SIGTERM/SIGKILL、直列約120秒)
内の `deadline = time.monotonic() + 30` を15秒 (または20秒) へ短縮する案を、**本waveでは採用しない。**
30秒を維持する。

**理由:**
- 段2 codexプランは15秒 (poll周期5秒の3周期分+マージン) を安全な第一案として提示したが、
  段3敵対相談レンズA (正しさ境界) が、`docs/failures.md` の既知事例
  (2026-08-06、48-worker全走中に外部subprocessを待つテストが個別には十分な余裕を持つ
  timeout値でも contention 下で timeout した再発群、単独再走では再現しない) を根拠に、
  「15秒が十分」という主張には直接の実測的裏付けが無いと指摘した。
- 親が独自に確認したところ、production `tools/dev_wave_wait.py` の `producer` サブコマンドは
  poll loop中に readiness を示す観測可能な出力を一切持たず、テスト側だけでの安全な短縮
  (production コード変更なしの readiness marker 導入) は不可能と判明した。
- D531の方法論 (「配布順の変更でwallが下がるという主張は、実装したうえで同一branch上のA/B対測定で
  示す」) に照らし、共有計算ノードでの代表的負荷下でのA/B実測、またはproduction側への
  readiness marker追加のいずれも本waveでは投資していない。
- 30秒→15秒の直列短縮見積り (約30秒、SIGTERM/SIGKILL 2ケース×15秒) 自体は
  `grep -n "time\.monotonic() + 30" orchestrator/tests/test_dev_wave_wait.py` で
  該当箇所が1箇所だけと確認済みで正確だが、値の安全性が未証明のまま採用しない。

**却下した選択肢:**
- 20秒という「より安全側」の値を採用する — 段3レンズAが「単独では保証にならない」と指摘した
  とおり、根拠は依然として推論であり実測ではない。中途半端な安全性向上のために正しさ検証テストへ
  タイミング不確実性を持ち込む理由にならない。
- readiness marker機構を本waveでproduction側 (`tools/dev_wave_wait.py`) へ追加する — 対象は
  dev-wave全体が使う共有インフラであり、影響範囲の精査・独立レビューを要する規模の変更で、
  本waveのbrief外 (段階導入、規律5)。

再訪条件: (a) 共有負荷下でのA/B実測 (複数回、現実的な並行度) で15〜20秒の安全性を示すデータが
得られる、または (b) production側にreadiness marker機構を追加する専用waveが先行着地する。

## {{D:floor-campaign-build-cache-sharing-deferred}}. test_s8b_floor_campaign.py の build cache 共有は計測・安全設計を先行させ、本waveでは実装しない

**決定:** `test_s8b_floor_campaign.py` の10テスト (42.90〜50.39秒、直列約467秒) が
production `build_cells` (`orchestrator/campaign/s8b_floor_campaign.py:2933`) の
`cache_root = str(out_root / "s8b-build-cache")` (同2945行) によりテストごとに孤立した
コールドキャッシュで実CCBenchビルド (`buildcache.py` の `cmake -S/-B` + `cmake --build`) を
毎回やり直している、という構造的仮説を確認した。ただし共有 build cache の実装は本waveでは行わない。

**理由:**
- 構造は確認済み: `cache_root` は各テストの `tmp_path` 配下で非共有、`buildcache.cache_key(genome,
  ccbench_commit, trace, ...)` はcontent-addressed設計であり原理的には共有可能。
- 親が対象テストの1つを単独実行すると17.96〜18.16秒で完了するが、全体スイート内 (48-way並列) では
  50.39秒かかることを実測した (2.8倍)。「redundant cold build」仮説を支持する signal だが、
  段2 codexプラン自身が指摘した通り、profiler/logによる直接の内訳確認 (cache lookup / 実ビルド /
  artifact validation の区間別計測) はまだ行っていない。
- 段3敵対相談レンズB (整合性・scope) は、fresh-build系テスト (意図した build failure・
  no-side-effect・cold-cache検査) を除外し resume/certificate系テストだけを対象にする
  「resume-onlyの小さなpilot」なら、10テスト全体共有より明確に安全性を限定できると指摘した。
  この指摘は正しいが、それでも cross-worker/cross-process のcache lock・atomic publish安全性・
  run ID衝突回避という、dev-wave全体で前例のない新規同期機構の設計が残る (段2プラン自身が
  規模「大」と自己申告)。
- 誤って実装した場合の失敗モードが重大: 共有cacheのhitが、`test_official_build_failure_leaves_
  durable_launch_start` 等が意図する「build failureを実際に発生させる」検査を迂回し、
  false green (規律2違反) を生みうる。D585の教訓 (per-test snapshotのhardlink化は却下、
  ただし規模はcopytreeという別の話) と同様に、実装コストと安全設計の精査を先行させるべき対象。

**却下した選択肢:**
- resume-onlyのpilotだけを本waveで実装する — 段3レンズBの指摘は妥当だが、cross-process
  lock安全性の検証を欠いたまま実装へ進むと、false-green経路を残したまま「速くなった」と
  誤って記録するリスクがある。この検証は専用のbrief・段2・段3敵対相談 (false-green経路を
  専任で攻撃するレンズを含む) を持つ独立waveに値する規模であり、本waveのbriefが対象としなかった
  設計対象 (規律5、段階導入)。
- 何も記録せず放置する — 構造根拠+実測signalの両方が揃っており、専用waveの起票価値がある
  発見を次waveへ承継しないのは規律5の「段階導入」の趣旨に反する (投資判断材料を捨てることになる)。

再訪条件: (a) `build_cells` の区間別計測 (cache lookup/実ビルド/validation) で実ビルドが
40〜50秒の大半を占めると確認され、かつ (b) resume系テストだけを対象にした最小pilotの
cross-process lock安全性・false-green回避を専任で検証する段3敵対相談を経た専用waveが
brief・段2・段4裁定を完了したとき。

## {{D:real-repo-collection-triple-invocation-not-reduced}}. real-repo優先順位メタテストの3回collectionは、冗長性の証拠なしには削減しない

**決定:** `test_real_repo_serialization.py::test_real_repo_priority_order_is_literal_and_writers_
follow_barrier` (87.46秒、本wave診断走行の単独最長) が `_collect_xdist_group_report` を
base/`--ff`/`--nf` の3variantで毎回スイート全体収集していることを構造として確認したが、
削減は本waveでは行わない。

**理由:**
- 本テストはreal-repo排他閉包の優先順位・barrier順序という正しさ機構自体を検証するメタテストで
  あり、3variantが異なる検査意図 (通常経路・`--ff`・`--nf` それぞれの収集順序保証) を持つ可能性が
  高い。段3敵対相談レンズBも「いずれか1回を省略できるという同値性の証拠がない」と指摘した。
- D634 (xdist collection固定費の削減は controller-only/manifest共有いずれも実装不能と結論) は
  xdist本体のworker側collectionを扱ったもので、本テストが自発的に3回collectionを呼ぶ設計とは
  別の問題である。D634を根拠にした「同じく無理」という判断はできないが、逆に「D634と無関係だから
  安全に削れる」という判断もできない — 未検証は未検証のままである。

**却下した選択肢:**
- 3回のうち1回を親の判断だけで省略する — 各variantが検出する異常の対応表と、variant固有の
  negative control (削った場合に本当に検出漏れが起きないかの反証実験) を用意していない状態での
  削減は、正しさ防壁を検証する機構自体を弱める可能性があり規律2に抵触しうる。

再訪条件: 3つのcollection variant (base/`--ff`/`--nf`) それぞれが独立に検出する異常の対応表を作り、
各variant固有のnegative control (削減した場合に検出漏れが実際に起きることを示す反証実験) を
用意した専用waveが、削減の安全性を実証したとき。
