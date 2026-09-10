# 受入lease claim待ちのstaleness事後定量化 — 小母数(n=7)では85.7%が「claim前merge」を無駄にしていた (2026-08-21)

- wave: `dev-wave-t1469-acceptance-lease-timing`
  (branch `worktree-dev-wave-t1469-acceptance-lease-timing`)
- base main: `46fbce3d7151044c9450bdf3f422ea839e7fcc0f`
- 依頼: 「claim前にmerge・受入テストを済ませていたら実際にどれくらいの頻度でmain advanceにより
  無駄になっていたか」を、新規lease claim・新規acceptance投入・production code変更をせず、
  既存artifactの事後解析だけで定量化する。D631 (`docs/decisions.md:25286-25288`) が明示した
  「実測が無い」というgapを埋める。
- **結論:** 既存artifactから機械的に再現できる最小の母集団 (n=7、後述) では、
  **6/7 (85.7%) の試行で、claim前にmerge・受入テストを済ませる設計だったなら
  待ち時間中の他waveのlandによって無駄になっていた**と推定される。待ち時間の中央値は
  約42分 (2530秒)、その間に中央値2件・平均2.0件の他waveのlandが発生していた。
  唯一「無駄にならなかった」1件 (t1372) は待ち時間がわずか115秒だった。
  母数が小さく統計的な決定力は無いが、**D631が再訪の条件とした「陳腐化率は十分低い」を
  現時点のデータは支持しない** — これは「D631/D270を緩めよ」という推奨ではなく、
  観測されたデータの記述である (規律2)。

## erratum — 本記録は待ち行列が在った時期の観測である (2026-08-23 追記)

**本 insight が測った運用は、観測の翌日に廃止された。** D662 (2026-08-22 ユーザー裁定) が受入
lease の待ち行列を廃止し、D691 (2026-08-23) がその待ち機構を実装から除去した。現在の `claim` は
待ち札を作らず `queued` を返さず、他 wave が保持中でも `held` を返して即投入する。したがって
本記録が前提とする「claim 成立までの待ち区間 `[T0, T1]`」という構造そのものが、いま存在しない。

**歴史記録として取り消されないもの:** §1〜§3 の母集団選定・待ち時間・`Δlands` の実測値と、§5 の
限界の議論。これらは 2026-08-19〜21 の待ち行列運用下で実際に観測された事実であり、D662 が
「受入待ちだけで main land が数時間止まる」と判断した根拠と同じ現象を独立に定量化している。
`git log` の committer date ではなく `git reflog show main` を一次資料に採る手法 (§1) も、
待ち行列の有無と独立に成立する。

**現行運用では成立しないもの (逐語で読まないこと):**

- §4 の「claim に成功した wave 自身が stale な main でテストされることは構造的に無い」という
  保証。`held` でも投入する現在は、この排他性が無い。
- §4 の「無駄が発生しうるのは claim 成立前の待ち区間に限られる」「現行の『claim 後に merge』
  設計 (D270)」という記述、および §5 で D270 を現行設計と呼ぶラベル。D662 が運用を置き換えた。
- §4 の `tools/dev_wave_wait.py` の file:line。本文の「2026-08-21 時点」注記どおり、現行 main では
  別の実装を指す。参照するなら base main `46fbce3d` 時点の blob を見ること。

**D631 の再訪について:** 本記録は「D631 が再訪の条件とした『陳腐化率は十分低い』を支持しない」と
結論した。その結論自体は当時のデータの記述として有効だが、D662 が待ち行列ごと廃止した以上、
D631 が扱った設計択一 (claim 前に merge するか否か) は現在の運用には存在しない。回収 wave は、
この点を「D270 を維持し supersede は検討しない」と canonical の decisions 台帳へ書き足すのは
現況に反すると判断し、対応する decision fragment を land せずに取り下げた。

## 1. 対象母数

母集団の起点は `/work/1/SFC/tanab/dev-wave-jobs/` (537 wave dir、
`find /work/1/SFC/tanab/dev-wave-jobs -maxdepth 1 -type d | wc -l` = 538 から親dir自身を除く)。
T-870 と同じ一次資料系列 (`acceptance-run.pid` のmtime = 「claim試行開始」、
[[T-870insight]] 1-2節、`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md:22-29`)
を使うため、`acceptance-run.pid` を持つ wave dir だけを候補にした
(`find /work/1/SFC/tanab/dev-wave-jobs -maxdepth 2 -iname acceptance-run.pid` = **11件**)。
残り526 waveは新しい `acceptance-child-N.log` (175 dirで観測、
`find ... -iname acceptance-child-*.log | sed 's#/[^/]*$##' | sort -u | wc -l` = 175) だけを持ち、
「claim試行開始」に対応する時刻artifactが無いため対象外 (§5-2)。

候補11件のうち、`acceptance-child-N.log` が **1本だけ** (単一試行、再試行なし) の7件を
「clean母数」として採用した。単一試行の場合だけ、`acceptance-run.pid` のmtimeがどの試行の
開始かを一意に確定できる。複数試行 (再試行) が記録された4件は、単一の `acceptance-run.pid`
がどの試行に対応するか、mtimeの前後関係だけからは一意に確定できないと実際に確認したため
除外した (§5-3で詳述)。

**clean母数 (n=7、時系列順):**

| wave | acceptance-run.pid (mtime) | acceptance-child-1.log |
|---|---|---|
| dev-wave-artifact-dir | 2026-08-19 00:09:59 | あり (1本) |
| dev-wave-t497-worker-launch-projection | (対象外・§1.2) | 2本 |
| dev-wave-t1372-oracle-perf-binding | 2026-08-20 19:34:48 | あり (1本) |
| dev-wave-t1441-unit3-d574-audit | 2026-08-20 20:09:59 | あり (1本) |
| dev-wave-t1442-c06-reachability | 2026-08-20 20:53:19 | あり (1本) |
| dev-wave-t1445-buildcache-toolchain-hit-check | 2026-08-20 20:20:47 | あり (1本) |
| dev-wave-t1461-lease-window | 2026-08-21 12:35:36 | あり (child-2のみ、§5-3) |
| dev-wave-t870-lease-timing | 2026-08-21 05:19:03 | あり (1本) |

### 1.2 対象外 (11件中4件)

| wave | acceptance-child-N.log | 除外理由 |
|---|---|---|
| dev-wave-t1444-pegasus-env-tag | 3本 (7,8,9) | pid mtime (06:23:05) が attempt-7 の受理 (06:20:27) より後、attempt-8開始 (08:15:55) より前に位置し、どちらの試行にも一意対応しない |
| dev-wave-t338-unit5-d574 | 2本 (1,2) | pid mtime (07:41:00) が attempt-1 終了 (07:25:26) より後に位置し、attempt-1 開始の証拠にならない |
| dev-wave-t497-worker-launch-projection | 2本 (1,2) | pid mtime (19:20:41) は attempt-1 開始に先行し単体としては整合するが、複数試行間でのpid上書き規約が一次資料から確認できないため、他の複数試行waveと扱いを揃えて除外 (機械的な一貫性を優先) |
| dev-wave-t870-congestion-nproc | 3本 (1,5,6) | pid mtime (06:31:06) は attempt-5 の受理 (06:26:30) より後、attempt-6 の受理 (06:40:59) の直前に位置し、attempt-5/6のどちらの開始かが一意でない |

**除外の実務上の含意:** 複数試行 = 少なくとも1回reds/リトライがあった wave であり、
一般に単一試行waveより「手間取った」waveである可能性が高い。もし複数試行waveの方が
待ち時間も長い傾向にあるなら、この除外はstale率・待ち時間の両方を**過小評価する方向**に
働く (§5-1)。

## 2. staleの判定規則

**規則:** wave Wの「claim試行開始」(T0) から「claim成立」(T1) までの区間 `[T0, T1]` の間に、
他waveのland (mainブランチのref更新) が1件でも存在すれば、Wは stale と判定する。

**根拠:** D270が採用した設計 (`docs/decisions.md:12435-12439`) は「claim後にmainを取り直し、
`HEAD..main`が非0のときだけ merge commitとして取り込む」という前提に立つ。D270が却下した
「claim前にmerge・受入テストを済ませる」設計 (`docs/decisions.md:25257-25259`) は、claim後を
「前提再確認 + fast-forward + fold だけ」にする、すなわち claim前に作った pre-merge が
fast-forward可能なままである (＝mainが1コミットも動いていない) ことを前提にする。
区間内に他waveのlandが1件でもあれば、このfast-forward前提が崩れ、pre-mergeの再作成・
再受入が必要になる。したがって「1件以上」を stale の閾値とした。

**T0/T1の定義:**
- T0 = `<job-dir>/acceptance-run.pid` の mtime。`dev_wave_wait.py acceptance` 起動直後に
  自身のPIDを書く定型 ([[T-870insight]]、`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md:24-25`)。
- T1 = 該当waveの唯一の `acceptance-child-1.log` (t1461のみ`-2.log`) 内、
  `| Created Request Time:` 行のPBS submit時刻。dispatchはclaim成立後に初めて行われる
  一体型CLIのため ([[T-870insight]] 2節、同README:43-46)、この時刻が claim成立の代理指標になる。

**他waveのland検出:** `git log` のcommitter dateは「commit作成時刻」であり「main反映時刻」
と一致しない場合があると判明したため (§5-4)、`git reflog show main` の各エントリの時刻
(=mainのref更新が実際に起きた壁時計時刻) を使用した。`main`のreflogに現れるエントリは
定義上すべて`main`ref自体への変更であり、`merge <sha>: Fast-forward`エントリが1件の
landに対応する (`commit: Fold landed documentation fragments`が直後に対で現れる、
§4で詳述)。

## 3. 実測結果 (経過時間分布)

| wave | T0 (claim試行開始) | T1 (claim成立) | 待ち時間 Δt_wait | 区間内の他wave land数 Δlands | stale |
|---|---|---|---|---|---|
| t1372-oracle-perf-binding | 19:34:48 | 19:36:43 | 115s (1分55秒) | 0 | いいえ |
| t1461-lease-window | 12:35:36 | 12:59:45 | 1449s (24分9秒) | 2 | はい |
| t1441-unit3-d574-audit | 20:09:59 | 20:42:33 | 1954s (32分34秒) | 3 | はい |
| t870-lease-timing | 05:19:03 | 06:01:13 | 2530s (42分10秒) | 1 | はい |
| t1445-buildcache-toolchain-hit-check | 20:20:47 | 21:09:40 | 2933s (48分53秒) | 3 | はい |
| dev-wave-artifact-dir | 00:09:59 | 00:59:33 | 2974s (49分34秒) | 3 | はい |
| t1442-c06-reachability | 20:53:19 | 22:07:24 | 4445s (74分5秒) | 2 | はい |

**要約統計 (n=7):**
- stale率: 6/7 = **85.7%**
- Δt_wait: 最小115s、中央値2530s (42分10秒)、平均2343s (39分3秒)、最大4445s (74分5秒)
- Δlands: 最小0、中央値2、平均2.0、最大3
- 唯一 stale でなかった t1372 は Δt_wait が2番目に短いt1461 (1449s) の1/12強しかなく、
  「待ち時間が短いほどstaleしない」という直感と整合する (n=7では回帰分析はしない)。

## 4. claim-before-mergeとacceptanceの関係 (file:line、2026-08-21時点)

現行実装は claim → main_sha 固定 → test という順序を厳格に保持しており、
**claimに成功したwave自身が stale なmainでテストされることは構造的に無い**。

- `_claim_once()` (`tools/dev_wave_wait.py:2917-3059`) は claim primitiveが返す
  `claimed_main_sha` を `_ClaimContext.main_sha` として保持する (同ファイル3056-3059行)。
  claim成立の瞬間のmain SHAがここで固定される。
- 受入完了時 (`tools/dev_wave_wait.py:4280-4296`) は、その時点のmain SHAを再取得し
  `final_main_sha != claim_context.main_sha` なら `receipt-main-moved` として
  失敗させる。claim中にmainが動いていないことを実行時に検査している。
- したがって「main advanceによる無駄」が発生しうるのは、**claim成立前の待ち区間
  `[T0, T1]` に限られる**。これは本insightが§3で測った区間そのものであり、
  D270が却下した「claim前にmerge」設計だけがこのリスクに晒される。現行の
  「claim後にmerge」設計 (D270) は、そもそもこの待ち区間でmergeをしないため、
  §3の Δlands 分だけの無駄を**発生させていない**。

言い換えると、本insightの数値は「現行設計が実際に無駄にした回数」ではなく
「却下された設計を採用していたら無駄になっていた回数」という反実仮想の定量化であり、
実際に観測された失敗事例ではない (§5-6)。

## 5. 解釈上の限界

1. **n=7は小さい。** 2項比率85.7%の95%信頼区間は (Wilson score, 手計算) およそ
   [42%, 100%] 相当まで広がりうる幅であり、統計的な決定力は無い。個々の実測値としては
   file:lineで裏付けられるが、「母集団全体でのstale率」を精度良く推定するものではない。
2. **候補選定バイアス (過小評価方向)。** §1.2 で除外した4 waveは複数回試行 (retry) を
   経ており、一般に単一試行waveより手間取った可能性が高い。除外により、待ち時間・stale率
   ともに実際より低く出ている可能性がある。
3. **母数はAug19-21の3日間に偏る。** `acceptance-run.pid` を持つ11件は全て2026-08-19〜21
   に集中しており (§1のtable)、それ以前の期間のデータは無い (dev-wave-jobs保持期限・
   `acceptance-run.pid`運用開始時期のどちらが原因かは未調査、production調査になるため
   本waveのscope外)。より長い期間・より高い/低い並行度での傾向は不明。
4. **git reflogは有限保持。** `git reflog show main` は本waveの実行時点 (2026-08-21) で
   2026-08-02のclone以降を保持していたが、reflogは既定でexpireする。将来この
   insightのΔlands算出を追試する場合、reflogが該当期間を保持していない可能性がある
   (commit sha自体は永続するが、land発生の壁時計時刻はreflogにしか無い)。
5. **Δlandsは land の中身を区別しない。** 区間内の他waveのlandには、docsのみ (fold等) と
   実装面ありの両方が混在する (§3の生データは個別landのcommit messageで確認可能、
   例: `dev-wave-t1442-c06-reachability`の区間には`fix(campaign): [T-1444]`のような
   実装commitと`Fold landed documentation fragments`のようなdocsのみcommitが両方含まれる)。
   「fast-forward前提が崩れる」という意味では区別不要だが、「pre-mergeの再作業コストが
   どれだけ深刻か」を厳密に見るなら、docsのみlandとの遭遇は実装面landとの遭遇より
   打撃が小さい可能性があり、本insightはこの重み付けをしていない。
6. **反実仮想の定量化である。** §4で述べたとおり、D270が却下した設計は実装されていない。
   本insightの数値は「もしその設計を使っていたら」という反実仮想シナリオに、
   実際に発生した他waveのland頻度を当てはめた推定であり、その設計を実際に動かして
   観測した失敗事例ではない。
7. **T0は「code ready」ではなく「acceptance投入開始」。** `acceptance-run.pid`のmtimeは
   `dev_wave_wait.py acceptance` プロセスの起動時刻であり、waveのコードが実際に
   「準備完了」した時刻より遅い可能性がある。もしD270が却下した設計が
   「コード準備完了と同時にmerge」を意味するなら、真の暴露区間は本insightの
   Δt_wait よりさらに長い可能性がある (§3の数値は下限側の推定)。
8. **D270/D631が引用する「24分待って15commit遅れ、4回空振り」(`docs/decisions.md:12444`,
   `docs/decisions.md:25263-25264`) とは別の実例である。** 本insightのt1461の
   Δt_wait (24分9秒) がこの anecdote の「24分」に近いが、waveも日付も異なり
   (t1461は2026-08-21、Δlandsは2件)、同一事例ではない。混同しないこと。

## 6. 一次資料 (file:line)

- 依頼原文・実測方針: `docs/archive/worklog-phase3-0821-793.md:553-559` ([T-1469]のP2起票)
- D631 (却下判断・閉じない残余): `docs/decisions.md:25255-25288`
  (実測gapの明記は`docs/decisions.md:25286-25288`)
- D270 (現行設計の決定・理由・却下した選択肢): `docs/decisions.md:12433-12456`
  (「24分待って15commit遅れ」は`docs/decisions.md:12444`)
- T-870 insight (同手法の先例): `output/insights/2026-08-20_t870-acceptance-lease-timing/README.md`
  (実測方法1節: 14-29行、結果表2節: 31-38行、コード実測3節: 62-89行)
- 現行claim実装:
  `tools/dev_wave_wait.py:2917-3059` (`_claim_once`、main_sha固定)、
  `tools/dev_wave_wait.py:4280-4296` (受入完了時のmain_sha再検証、`receipt-main-moved`)
- clean母数7件のT0/T1一次資料 (全て`stat`のmtimeと`grep -n "Request Time"`の出力):
  - `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-artifact-dir/acceptance-run.pid` (mtime),
    `.../acceptance-child-1.log:35-37`
  - `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1372-oracle-perf-binding/acceptance-run.pid` (mtime),
    `.../acceptance-child-1.log:35-37`
  - `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1441-unit3-d574-audit/acceptance-run.pid` (mtime),
    `.../acceptance-child-1.log:35-37`
  - `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1442-c06-reachability/acceptance-run.pid` (mtime),
    `.../acceptance-child-1.log:35-37`
  - `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1445-buildcache-toolchain-hit-check/acceptance-run.pid` (mtime),
    `.../acceptance-child-1.log:35-37`
  - `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1461-lease-window/acceptance-run.pid` (mtime),
    `.../acceptance-child-2.log:47-49`
  - `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t870-lease-timing/acceptance-run.pid` (mtime),
    `.../acceptance-child-1.log:35-37`
- 除外4件の一次資料 (§1.2):
  `dev-wave-t1444-pegasus-env-tag/acceptance-child-{7,8,9}.log`,
  `dev-wave-t338-unit5-d574/acceptance-child-{1,2}.log`,
  `dev-wave-t497-worker-launch-projection/acceptance-child-{1,2}.log`,
  `dev-wave-t870-congestion-nproc/acceptance-child-{1,5,6}.log`
  (各`Request Time`行と`acceptance-run.pid`のmtimeを`ls -la --time-style=full-iso`で比較)
- Δlands算出: `git reflog show main --date=iso-local` (2026-08-21実行、2026-08-02clone以降を
  保持)。§3の各land commitのsha (`git log -1 --format='%cI %s' <sha>`で個別に再確認可能):
  dev-wave-artifact-dir区間 = `f0cbf395`,`ee98013f`,`f185b693`;
  t1441区間 = `2addb1b9`,`b910682c`,`b7e0fedd`;
  t1442区間 = `24464277`,`fc020d86`;
  t1445区間 = `b910682c`,`b7e0fedd`,`17bb99f3`;
  t1461区間 = `3e15be0b`,`5165c957`;
  t870-lease-timing区間 = `4dfbed5c`。
- canonical worklog: `docs/worklog.md:3989` ([T-1469]が(805)から変更なしで持ち越されている
  最新の確認点、**本wave着手時点 (2026-08-21、base main `46fbce3d`) のスナップショット**。
  worklogはfoldで随時追記されるため、後続waveのland後は行番号がずれている可能性が高い —
  内容照合は行番号でなく `grep -n "\[T-1469\]" docs/worklog.md` で行うこと)

## 関連

- [[D631]] (実測gapを要求した決定)
- [[D270]] (却下された「claim前merge」設計の対照)
- [[T-870insight]] (同一手法の先例、別の指標=lease TTLとの余裕)
- 手元memoryを2件更新済み (dev-wave docs本文でなくAI個人のmemory system、段8のdev-wave
  改善候補とは別枠): `git-log-committer-date-not-land-time.md` (新規、§2の手法訂正の経緯)、
  `dev-wave-bg-worktree-startup-checks.md` (追記、本wave自身がDW-O20の読み落としを
  段9直前に自己発見・是正した実例)
