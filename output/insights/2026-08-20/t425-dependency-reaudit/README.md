# [T-425] 8b H1/H2 between-run floor 実験路の依存鎖再監査 — 結論と裁定パッケージ

dev-wave (2026-08-20)。branch `worktree-dev-wave-t425-floor-dependency-audit`、起点 main
`0b963567` → wave 中に `f677ae65` へ ff-only 追随 (2026-08-20 /rulings セッションの D581/D582 を含む)。
**実装差分ゼロ (docs のみ)。** command 引数の (a)〜(d) を実測で裏取りし、H1/H2 本体を続 wave で
起票してよいかを判定した。

## 総括

command 引数の前提「T-419 は 2026-08-17 付で解決済み・主要 blocker は解消済み」は **誤り**。
T-419 には別時期・別内容の2つのサブ課題があり、2026-08-17 に解決したのは「較正 artifact の
世代有効化まわりの周辺技術3件」で、U-6 の依存鎖が実際に必要とする「較正再取得(取り直し+活性化)」
の**活性化**は 2026-08-19 (D547) 時点でも未実施のまま。

一方、command 引数が前提にしていなかった**新事実**が2つ見つかった。

1. **本 wave 実行中 (2026-08-20) に D581 が land した。** 床値 (floor value) 測定を
   `official` mode 相当の事前登録儀式なしで、粗い provenance だけで成立させてよいという標準変更。
   理由文が名指しで「[T-419] の生成移行 chain という無関係な前提条件へ床値測定を従属させ続ける
   結果になっていた」と述べており、まさに本監査が特定した U-2 活性化ブロッカーの一部を
   直接指している。
2. **U-6 の完全な依存項目は (i)〜(vi) の6件** (T-425 package 自身の `02-ruling-package.md`)
   であり、command 引数が要約した「[T-419]→較正再取得→[T-424]/[T-272]→floor infra」は
   このうち (v)(iii)(iv) だけを取り出した簡略形だった。(ii) workload 署名は決定済みだが
   **H1/H2 (rr80/rr20) 向け calibration が1件も登録されていない** (登録済み2件はいずれも rr50)
   という新しい gap を含む。(vi) T-422/F98 は狭い意味では実装・land 済みと確認した。

結論として、**「H1/H2 実験本体 (公式 receipt・受理登録を伴う実走) は今も起票不可」**は変わらないが、
**「floor infra に関する実装を一切できない」という理解は言い過ぎ**だった、というのが本監査の
最終的な補正である。実データ・受理集合・certified 選択には一切触れていない。

## 段0の4問への回答

### (a) 較正再取得は何を指し、完了しているか

**部分完了、かつ「完了」の中身が2つの別事象と混同されやすい。**

T-419 の U-2 (較正再取得) は3部構成: (i) 較正を取り直す、(ii) 取得時受入検査、(iii) 登録し直す
= 活性化。(i)(ii) は 2026-08-06 前後に land 済み ({{既存 commit、`ce2736e8` 等}})。
(iii) 活性化だけが未実施のまま — g1→g2 の切替は D272/D437 が定める「環境世代の活性化は
承認・発効ともに人間 lockstep」という恒久設計ゲートに従属しており、dev-wave が単独で
決定できる範囲ではない。

2026-08-16 の T-419 U-2 世代移行 wave (`output/insights/2026-08-16_t419-generation-migration/`、
実装差分ゼロ) が、g1/g2 の受理帯が中央値 2101.0・tolerance 2.0 で完全一致することを実測しており、
活性化未了そのものが**現在の較正受理挙動を歪めてはいない**。2026-08-17 rulings 第4回が扱った
(1)(2)(3) は、この 08-16 wave が返した裁定パッケージ中の**周辺技術3件** (attestation method の
実体一致・ever-active 第1世代の自己不整合 gate・床値 protocol path の resolver 配線) であり、
**活性化そのものではない** ((1)(2) は見送り、(3) だけ実施)。command 引数の「T-419 は
2026-08-17 付で解決済み」はこの (3) を指しており、活性化 (U-2 本体) とは別事象。

2026-08-19 の D547 (`docs/decisions.md:22358` 付近) も g1→g2 活性化が今も未実施・
人間 lockstep 待ちと確認している (段2 codex plan による独立裏取り)。

**2026-08-20 の新事実 (D581)**: 床値測定を official/pilot の事前登録儀式なしで実施してよいと
標準変更し、理由文で「[T-419] の生成移行 chain という無関係な前提条件へ床値測定を従属させ続ける」
ことを明示的に問題視した。これは U-2 活性化が floor 測定をブロックする根拠を実質的に弱める。
ただし D581 の直接の適用対象は `s8b_floor_campaign.py` の `official` mode (8b 公式 per-pair floor
の凍結儀式) であり、T-425 が使う `between_run_floor.py` (もともと official mode を経ない設計、
`output/insights/2026-08-04_t425-floor-scoping/00-parent-brief.md:3-4`) への機械的な適用は
未検証。次 wave の段1 brief で確認すべき最優先の新事実。

### (b) T-424(P2)/T-272(P3) は本当に floor infra 着手の必須前提か・迂回可能か

**必須前提であることは正しいが、「未実装」は不正確。部分実装あり・要求は未閉包。**

D145 決定5 (`docs/decisions.md:7048`) が定める floor 専用 infra の前提4件のうち、
K=15 固定・workload 署名 (H1/H2) は 2026-08-05 裁定で解決済み。残る interpreter 版数 gate
(T-272) と job script bytes 束縛 (T-424) は D145 が名指しする正規の前提であり、恣意的な
依存ではない。

commit `950757e2` が T-424 の一部 (submit_certify.sh の `--job-script` 受理と script hash の
pre-submit/submit receipt への記録、`tools/pegasus/submit_certify.sh:20-26,75-85,127-150,
208-220`) を実装しているが、`job-result.json` に `job_script_sha256` が無く
(`tools/pegasus/certify_calibration.sh:752-765`)、override した script と実行結果の
結び付きを最終成果物では検証できない — **要求は閉じていない**。

commit `419d59b1` が T-272 の一部 (`floor_campaign.sh` の Python 3.10+ 版数 gate、
`tools/pegasus/floor_campaign.sh:166-177`) を実装しているが、certify/submit 経路
(`tools/pegasus/submit_certify.sh:49-60`、`tools/pegasus/certify_calibration.sh:180-206`) は
依然として裸 `python3` を呼んでおり、`floor_campaign.sh` だけが版数 gate を持つ非対称が残る。

さらに U-6(iii) には interpreter 版数 gate だけでなく **perf 実体のノード個体差**
(bnode074 不在 / bnode011・bnode138 実在) も含まれており (`02-ruling-package.md:159-163`)、
これも certify 経路は未対応のまま — 親 brief・段2 plan のどちらも当初これを独立項目として
拾えていなかった (段3 レンズA の指摘)。

**バイパスには D145 決定5 を明示的に再訪する裁定が要る** (dev-wave が自律的に決めない)。
ただし D581 の「粗い provenance で足りる」という新しい project 標準は、D145 決定5 自体を
再訪する動機にもなりうる (T-424/T-272 が守ろうとしている厳密な provenance の水準が、
D581 が floor 測定一般に要求しなくなった水準と整合するかは未検討)。

### (c) D555/[T-1336] の射程は T-425 の対象に及ぶか、別概念で無関係か

**別概念、ただし「完全に無関係」は言い過ぎ。用語の重なりに注意が要る。**

D555 (`docs/decisions.md:22604` 付近) が撤去したのは `orchestrator/campaign/s8b_verdict.py`
の `judge_combined` の旧条件3 (frozen 履歴値との比較としての per-pair floor 超過判定)。
T-425 の floor は `orchestrator/campaign/between_run_floor.py` 系統 (T-425 自身の
`00-parent-brief.md` scope(1) が明記) であり、`s8b_verdict.py` との直接の import/call 関係は
無い (双方向とも確認)。

T-425 自身の裁定済み設計 (U-7 択a、2026-08-05 採用、`02-ruling-package.md:170,174`) が
「層 C の generic scalar は 8b の per-pair frozen protocol・8c の per-pair floor 欄には
触れず、充足もしない」と明記しており、この分離は D555 とは無関係に T-425 が最初から
意図したもの。

ただし2点、注意が要る。

- `s8b_verdict.py:61` は `s8b_floor_stats` を import しており、`floor_source` を
  measurement condition (session context・preflight receipt・oracle の測定条件との整合)
  の検証に使っている (`s8b_verdict.py:448-560,611-621,653-655`)。旧条件3 の判定値としては
  使わないが、共有 leaf としての接点は残る。
- `orchestrator/campaign/s8b_floor_campaign.py` は名前が `between_run_floor.py` と似ており、
  測定ヘルパーの型も同型だが、実体は**「公式 8b の per-pair floor producer」**であり、
  T-425 の floor 系統ではなく D555/verdict 側の系統に属する (段3 レンズA)。親 brief が
  当初これを T-425 系統に一括りにしていたのは不正確だった。

§10.2 (`docs/phase3-8b-descriptor-design.md:466-484`) が要求する pilot 要件
(`n`/`delta_min`/`sd_max` を結果を見る前に決める、対計画用の完全 block pilot) と T-425 の
K=15 floor 測定が将来接続しうるかは未検討の論点として残す。現在の実装では T-425 の generic
scalar が §10.2 の paired floor を満たすという解釈は成立しない (段3 レンズA)。

### (d) 現在稼働中の wave と編集面が重複しないか

**floor 中核ファイルへの実害ある重複は無い。ただし関連ファイルへの部分的な接触が2件見つかり、
1件は無害 (古い診断 checkout)、1件は無関係な1行変更。**

t1337 (launcher-timing-proof) は main との diff ゼロ。稼働中 worktree 6件・active agent 10件
(2026-08-20 実測) を確認したが、floor 関連8ファイル
(between_run_floor.py, s8b_verdict.py, s8b_floor_campaign.py, screening_driver.py,
trial_registry.py, s8b_holdout_freeze.py, p3_autonomous_workload_trial.py,
holdout_observation.py) への実質的な重複は無い。

段3 レンズA/段2 plan が検出した2件はいずれも実害なしと確認済み:

- `dev-wave-jobs/t1363-c06-budget-consumer/.../worktree` (detached HEAD `5ec4b69b`) は
  main の祖先 (2026-08-18 時点の古い診断 checkout、`main..HEAD` = 0 commit) — 生きた
  並行作業ではない。
- `worktree-t1356-sort-closed-region-wiring` の `p3_autonomous_workload_trial.py` 差分は
  1行 (auditor gallery code 定数 16→21、floor 無関係)。

なお、T-422/F98 の広い意味 (campaign-form 実行の land 経路 end-to-end) は未完了で、
`orchestrator/campaign/layer3_report.py:575-621` が `generated_from_head` 欠如時に
campaign directory へ直接 `git -C ... rev-parse HEAD` する経路が現に壊れうる
(`docs/archive/worklog-phase3-0817-612.md:40-53` に実例)。この `layer3_report.py` は
本監査の時点で **worktree `dev-wave-t470-accepted-consumer` が編集中** — floor infra
そのものではないが、T-422/F98 残余に触れる続 wave を設計する場合はこの重複に注意する。

## DW-G05 (成果物影響)

certified 選択・既登録 calibration bytes・H1/H2 の受理集合は本 wave で不変。材料レポートは
本監査の結論と裁定条件の追記のみとし、試行台帳に新規 H1/H2 trial・receipt・floor 値は
追加していない (実測・実装ゼロ)。

## 裁定パッケージ (ユーザーへ返す、優先度順)

1. **[最優先] D581 が T-425/U-6 の依存鎖に及ぼす具体的な影響を、次 wave の段1 brief で確認する。**
   `between_run_floor.py` が official mode を経ない設計である以上、D581 の相対的な意味
   (「もともと不要だった儀式の話」なのか「floor 測定一般への標準変更として T-425 にも
   直接効く」のか) を実コードで裏取りする。
2. **T-425 floor infra の bounded preparation (code-only) は、公式実験の起票を待たずに
   着手可能。** `between_run_floor.py` の入力検証・receipt schema・failure path・
   screening 接続など、実験を起動せず certified artifact を生成しない範囲に限る
   (段3 レンズB の指摘、real 判定)。rr80/rr20 registration の readiness/preflight や
   U-1〜U-3/U-5 (T-425 package 自身の未実装部分、floor infra wave の scope) の棚卸しも
   このカテゴリに入る。
3. **公式 H1/H2 実験の起票 (実行・receipt 生成・受理登録) は、T-424/T-272 の要求全体閉包
   または D145 決定5 の明示的再訪裁定、かつ rr80/rr20 較正の登録 (人間 lockstep) が
   揃うまで不可。** 3択 (排他的ではなく組合せ可):
   - T-424/T-272 の残余 (override 禁止・`$0`/HEAD blob 束縛・hash の job-result.json までの
     伝播・certify/submit 全経路の interpreter gate・perf ノード個体差 gate) を閉じる
     専用 wave。
   - D145 決定5 を再訪し、現行 floor wrapper の部分的束縛で十分と認めるか、残余を
     明示的に bypass するかをユーザー裁定へ返す (D581 の「粗い provenance」標準との
     整合性も併せて検討材料にする)。
4. **T-434 (8c 側 cap-lift receipt) の scope 外境界は編集面では妥当だが、概念面で
   「無関係」と言い切らない。** `s8b_verdict.py` が `floor_source`/`s8b_floor_stats` を
   共有 leaf として使う以上、T-425 の schema/leaf 変更は測定条件検証を壊してはならず、
   layer C scalar を 8c の per-pair floor receipt の代替にしない、という1文を今後の
   floor infra wave の不変条件に含める。

## 段2/3 codex 成果 (本 wave の裏取り経路)

| ファイル | 内容 |
|---|---|
| `02-stage2-output.md` | 段2 codex plan (read-only, reasoning=max)。P1〜P5 の初期裏取り |
| `05-stage3-lensA-output.md` | 段3 敵対レンズA (`--lane sol`、正確性)。file:line 精度で
  段2 の訂正をさらに補正 (T-424/T-272 部分実装の詳細、U-6(iii) の perf ノード個体差、
  rr80/rr20 loader 不統一、T-422 の広い意味での未完了、s8b_floor_campaign.py の系統違い) |
| `06-stage3-lensB-output.md` | 段3 敵対レンズB (`--lane luna`、実効性・論理)。
  「実装なし」の過度な一般化を指摘し、bounded preparation の道を開いた |

正本は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t425-floor-dependency-audit/`
(00-parent-brief.md 〜 06-stage3-lensB-output.md、prompts 含む)。repo 外のため、
本 README が逐語の代替となる形で結論を保全している。

## 変異 matrix・受入

**変異 matrix は免除** (`DW-S04`: 実装しないと裁定済みで実装差分ゼロの wave)。
受入全走は免除せず、本 wave の commit 後に投入する (結果は worklog を参照)。
