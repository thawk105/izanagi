# 段 3 敵対相談 — レンズ A

結論は二つに割れる。現行 Pegasus 経路が事実上通らないという運用診断は強く支持される。一方、「帯外値は計算ノードでも必ず probe 自身の CPU」「どんな較正でも論理的に通らない」「α は検出力を失わない」という一般化は成立しない。

テストは実走していない。以下は静的検査と保存済み実データの再集計である。

## 実データの再集計

指定された job-staging 15 件と registered 1 件は次のとおりだった。

| node | probe | 帯外 index=value |
|---|---|---|
| bnode003 | 867865 static | 28=3068.375 |
| bnode003 | 867866 static | 24=3063.645 |
| bnode003 | 867867 static | 34=3072.574 |
| bnode003 | 867868 static | 28=3073.076, 43=3043.216 |
| bnode003 | 867869 static / pre | 38=3079.316 / 28=3069.254 |
| bnode003 | 867870 static / pre | 10=3046.300 / 1=3022.274 |
| bnode048 | 867872 static / pre | 5=3025.409 / 6=3033.215 |
| bnode048 | 867874 static / pre | 8=3041.294 / 11=3049.673 |
| bnode011 | 867876 static / pre / post | 0=2951.676 / 40=3079.456 / 44=3077.702 |
| bnode011 | registered internal probe | 40=3080.935 |

したがって、指定 16 件については「帯外 1〜2 個、残りは厳密に 2101.0」が確認できた。[registered artifact](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440) も中央値 2101.0、許容帯 `[2058.98, 2143.02]` に対し index 40 が帯外である。

ただし、親 brief の「repo 内の全成果物が 16 件」は誤りである。

- repo 内には direct profile artifact が 22 ファイルあり、registered と attempt 867876 の重複を除いて21回の独立 probe がある。
- 追加分には smoke 3 件（index 25、47、34）、attempt 867874 の internal probe（index 10）、silo ladder probe（index 10）がある。
- F97 の実行時 evidence には、brief が挙げた index 34=3076.13 に加え、もう一方の脚の index 27=3096.51 も保存されている。
- 合計23回の独立した計算ノード観測の全てに1〜2個の帯外値があり、残りは2101.0だった。値域は親の `2951.7〜3080.9` ではなく、少なくとも `2951.676〜3096.51` である。

つまり現象自体は親の16件より強く再現しているが、母集団数・値域・index 集合は不完全だった。

## 主張 2 — observer-self CPU との同一視は未立証

[probe](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:390) は `/proc/cpuinfo` 全文を一度 `read_text()` し、後から processor block を解析する。self CPU、各 block の読取時刻、読取中の migration は保存しない。

計算ノード成果物にも self CPU はない。親の「6/6」はログインノード上の要約しか残っておらず、手順・pre/post CPU・生の対応表を独立再検査できない。この状態では、96論理CPU・HTあり・共有のログインノードから、48物理CPU・HTなしの計算ノードへ causal identity を移せない。

index 分布については次の評価になる。

- 16件の17帯外位置は14種類。全48 CPUから一様に reader CPUが選ばれる仮説なら期待される distinct 数は約14.5なので、self CPU 仮説とは整合する。
- しかし、同じ分布は「最近 cpufreq 情報が更新されたコア」「PBS/kernel daemon」「reader の途中 migration」でも生じる。self CPU を記録していないため識別力がない。
- 同じ bnode003 でも index 1、10、24、28、34、38、43へ動くため、固定コアの個体差だけでは説明できない。
- bnode011 でも static=0、pre/internal=40、post=44であり、固定 daemon/core 仮説も単独では弱い。
- SMT 仮説は計算ノードの `physical=logical=48`、`smt_active=false`、topology の `ht_off=true` と矛盾する。
- index 0 と47の双方が帯外になっているため、「先頭または末尾を読む順序だけ」の固定 artifact でもない。ただし読取中 migration と順序の複合は残る。
- 867868 の2帯外は「常に reader 自身だけ」という単純モデルの反例候補である。reader migrationか外部実行主体かを区別できない。

さらにログインノードで静的に確認した同一CPUモデルの cpufreq は `acpi-cpufreq`、`performance`、boost=1で、`cpuinfo_max_freq/scaling_max_freq=2101000` に対して `scaling_cur_freq` は3.2GHz台だった。2101と3GHz台の二値的な形は「負荷そのもの」だけでなく、cpufreqの現在値・更新鮮度・報告仕様でも説明可能である。計算ノード成果物は scaling driver、boost、per-CPU `scaling_cur_freq` を保存していない。

したがって、self CPU は有力な第一仮説だが、親の因果同定は **refuted** である。

## 主張 3 — 現行再取得経路では real

現行 sanctioned job は affinity `0..47` の全48 CPUで probe を無拘束に起動し、`taskset` や probe 用 `numactl` は使わない。[certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/tools/pegasus/certify_calibration.sh:350) の shell probeだけでなく、[_certify_main](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:524) が cooldown 後にもう一度同じ probe を呼ぶ。

保存済み internal candidate profile も次の2回とも帯外だった。

- attempt 867874: index 10=3051.273
- attempt 867876: index 40=3080.935

新しい取得時検査を現在の経路へそのまま足せば、既知の candidate は両方とも拒否される。計算ノード観測全体でも23/23が帯外なので、「現在のジョブ・governor・probeのまま取り直せば、ほぼ確実に拒否」は **real** である。

ただし「構造的に決定的」までは立証されていない。観測は同じ構成へ偏っており、独立な reader binding・driver・boost 条件を試していない。

## 主張 4 — 現行経路の全面閉塞は real、普遍命題は refuted

実行時 comparator は期待中央値と期待 tolerance を使い、観測列の全値だけを見る。[述語](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:174) 自体に「必ず1個を帯外にする」論理はない。全48値が2101なら普通に通る。

実環境では F97 の2脚が index 34と27でそれぞれ落ち、保存済み観測も23/23で同型なので、現在の Pegasus 経路が全面閉塞している点は real である。しかし「どんな較正でも通らない」は次の理由で refuted である。

- cpuset/taskset/numactlだけでは解決しない。reader を測定対象CPUへ固定すれば、帯外位置を固定するだけである。
- 読取順の先頭・末尾も、実データで index 0と47が既に帯外なので解決根拠がない。
- boost無効化や周波数capで all-2101 になる構成は論理的には存在する。ただし計算ノードで未実測であり、外部負荷のクロック検出力も失い得るため採用案にはできない。
- schema上は tolerance 100の較正も作れて comparator を通せるが、これは防壁の明白な弱体化なので反例としてのみ挙げ、選択肢にはしない。

なお、S1の自己比較は candidate 自身の `tolerance_pct` を使う。凍結値2.0は過去 insightで決められている一方、`submit_certify.sh` と CLI は任意の `(0,100]` を受け入れる。S1だけでは「承認済み2.0の帯」を機械的に固定しないため、段4では tolerance authority の結線も確認すべきである。

## α・β・γの検出力を攻撃する

| 案 | 失う検出力 | 判定 |
|---|---|---|
| α: K回のCPU別最小値 | 現述語の「一つの観測で全CPUが帯内」を、`各CPUがK回中一度でも帯内`へ変える。外部processがCPU 7→8へ移動すれば、read 1では7、read 2では8が高くても、min後は両方2101になり、実在しなかったclean vectorを合成する。固定processでもsleep/duty-cycleを一度挟めば消える。Kを増やすほどfalse negativeが単調に増える。 | 「述語コードは不変」でもシステムの受理集合は広がる。防壁非緩和案ではない。 |
| β: self CPUを1要素除外 | 実際の競合processやdaemonがreaderと同じCPUに載った場合、その異常も一緒に捨てる。`/proc/cpuinfo`読取中にreaderがmigrationすれば、前後のself CPU idは非原子的で、誤った要素を除外する。 | 47/48への明示的緩和。採用不可。 |
| γ: 任意の帯外を1個許容 | 一つの固定コア異常、誤governor、競合process、熱異常を因果に関係なく許す。現データには2帯外もあるため運用上も完全には直らない。 | βより広い無根拠なblind spot。採用不可。 |

特にαについて、親 brief の「真に他processが走るコアは全読み取りで高い」は前提として成立しない。OS scheduler上、継続稼働processでもCPUを移動でき、block/sleepもする。

防壁を維持するなら、最低でも「各CPUをちょうど一度、readerがそのCPU上にいない状態で測る」ような off-core sampling を検討し、計算ノードで以下を先に実証する必要がある。

- reader CPUをpre/postで記録し、途中migrationを拒否する。
- readerを複数CPUへ明示的にpinし、対象CPUの値はreaderが別CPUにいる観測から一つだけ採る。minや要素除外はしない。
- clean時は48要素全てが帯内になる。
- 別CPUに固定した既知の競合processと、CPU間を移動する競合processの双方を必ず拒否する。
- scaling driver、boost、per-CPU周波数源をreceiptへ束縛する。

これはまだ設計候補であって、安全性が実証された案ではない。

## 再裁定の範囲

D143のユーザー裁定全体を再度開くのは過剰である。

既に確定しているのは次の二点で、覆す新事実はない。

- runtime述語を正とし、全要素を検査する。
- publish前にcandidate自身がその述語を通ることを検査する。

新事実が覆したのは「現行 `proc-cpuinfo` probeのまま取り直せば、受理可能な較正を作れる」という実行可能性だけである。

したがって再裁定へ返すなら、質問は「述語を緩めるか」ではなく、次へ限定すべきである。

- 全48要素を捨てず、時間方向のminも使わないprobe補正を既存裁定の実装範囲と扱えるか。
- それが不可能なら、管理CPUやplatform policyなど環境契約自体を変えるか、campaignを閉じたままにするか。

α・β・γしか残らないなら、いずれも検出力を失うため実装せず、裁定へ返すべきである。

## 主張 5 とfixtureの歴史

fixtureは commit `6b4fbdf5` で、実sealをofficial floor consumerへ通すD79(7)の部分E2Eとして導入された。[当時の記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/insights/2026-07-24_e2e-real-seal.md:18) は、初期実装がattestationで赤になり、親がcomparatorを読んで「in-tolerance観測」へ直したと明記する。目的は物理Pegasusの検証ではなく、seal→floorの後段経路を通すことだった。

[fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_s8b_floor_campaign.py:3446) の因果は次のとおり。

- registered profileの3080.935を上限2143.02へクランプするため、必ずruntime comparatorを通る。
- observed側の `tolerance_pct=100.0` は comparator が読まないsentinelであり、通過原因ではない。100を外してもclean samplesが残る限り赤くならない。
- クランプを外してregistered profileをそのまま返すと、`attest_and_build_receipt()` が index 40をfailとし、[_run_campaign_core](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/s8b_floor_campaign.py:2765) がbuild・measure前に `FloorCampaignError` で停止する。当該E2Eは `outcome["status"] == "completed"` へ到達せず赤になる。
- monkeypatch自体を外すと、テスト実行機の物理profileをPegasus契約へ比較する非portable testになるため、それも正しい修正ではない。

従って、当該E2EがF97を検出できないという主張は **real** である。ただしfixtureはその限界を当初から明記しており、欠落は「別のhash-bound registered artifact自己整合テスト／実probe controlが無かったこと」である。

## 総括

- **(a) 主張1〜5**
  - **主張1: real（指定16件の数値部分）**。全16件が1〜2帯外、残り2101.0。ただし「repo全体で16件」は **refuted**。独立観測は少なくとも23件あり、最大値3096.51、追加index 25・27・47もある。
  - **主張2: refuted**。self CPUは最有力仮説だが、計算ノードのself CPU対応が保存されず、ログインノード6/6からの因果一般化はできない。
  - **主張3: real（現行sanctioned経路に限定）**。同じprobe/configの計算ノード観測23/23が帯外で、既存internal candidate 2件も取得時検査に落ちる。
  - **主張4: refuted（普遍命題として）**。現行Pegasusの全面閉塞はrealだが、述語実装上all-in-band観測は通る。「どんな較正・構成でも不可能」ではない。
  - **主張5: real**。クランプが物理F97を構造的に隠す。observed tolerance 100は原因ではなく、samplesのクランプが原因。
- **(b) 親が見落とした対立仮説**
  - cpufreq driverの現在値／更新鮮度／boost報告仕様。
  - `/proc/cpuinfo`読取中のreader migration。
  - PBS/kernel daemonまたは非exclusive allocation上の別実行主体。
  - 固定コア差・SMT・固定読取位置は実データで弱いか反証されるが、self CPUとの直接同一性も未立証。
- **(c) 裁定へ返す範囲**
  - 述語と取得時全要素検査は再裁定不要。
  - 返すなら「全48要素を保つprobe補正を既存裁定の範囲とするか／platform契約を変えるか／閉塞維持か」だけに限定する。
  - α・β・γはいずれも検出力を失うため、そのまま採用してはならない。
- **(d) 段4で親が決めるべき択一**
  - **推奨: safety-only waveへ縮退する。** S1/S2と承認済みtolerance authorityの固定だけを実装し、「再発publishは防ぐがcampaignは開かない」と明記する。α・β・γは不採用とし、計算ノードでself CPU・driver・boost・既知競合を束縛したprobe実験を先行させる。
  - 対案は、現brief/planをinvalidateし、全48要素を捨てないoff-core probeが正負controlを通るまで段2から再設計し、同じwaveで再較正すること。現時点では安全性証拠がないため、この対案のまま段5へ進んではならない。