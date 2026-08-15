---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1140-claim-identity
seq: 1
title: 床値 claim identity の protocol 単位化を実装差分ゼロで再裁定へ返す (docs のみ、branch worktree-dev-wave-t1140-claim-identity)
---

## 本文

- 2026-08-16 のユーザー一括裁定 #14 (「[T-1140]・[T-330] 択 (c)・予約照合の 3 つを同層として
  1 wave で扱う」) と #12 (「[T-330] は (c) を先に (F321)、択 (a) は F321 修正後に再提示」) に従い
  着手した。段 2 プラン + 段 3 敵対レビュー 2 本 (レンズ A = 正しさ境界 / reward hack、
  レンズ B = scope 整合 / 実効性) を回し、**両レンズとも NO-GO**。
  親は裁定文の前提 2 件が偽であることを独立に実測し、**実装差分ゼロで再裁定へ返す**。
  裁定を不採用にしたのではなく、実行しようとした結果として前提が崩れた。
- **決め手 (親の実測)**: identity を protocol 単位にすると、床値 campaign は
  **1 回で永久に停止する**。`campaign_claim.acquire_claim` は release も stale 回収も持たない
  永久 one-shot であり、identity が run 単位である現状はそれで整合していた。
  production wrapper は protocol を固定 1 本 (`tools/pegasus/floor_campaign.sh:947`)、
  mode を pilot 固定 (`:962-964`) で投入し、official は core が無条件拒否する
  (`orchestrator/campaign/s8b_floor_campaign.py:342-352`)。実投入は既に 3 件ある
  (`output/env/pegasus/floor/attempts/submissions/`、うち 1 件は実ジョブ 873200.nqsv)。
  したがって最初の 1 回が成功でも crash でも preflight 失敗でも protocol を永久占有し、
  以後の投入がすべて拒否される。規律 2 違反ではないが**承認外の過剰拒否**である。
- **裁定文の前提 2 が偽**: 材料が言う「scheduler 所有の create-only receipt」は存在しない。
  実在するのは submitter 所有の create-only receipt (`tools/pegasus/submit_floor.sh:466-495`) で、
  それが計算ノード側で `PBS_JOBID` と照合されている (`tools/pegasus/floor_campaign.sh:452`)。
  この `PBS_JOBID` 照合だけが scheduler 所有の錨である。加えて**照合そのものは既に実装済み**
  だった — Python ではなく shell wrapper の中に (`floor_campaign.sh:406-555`)。
  Python 側にも receipt 検査が実在する (`orchestrator/campaign/certified_writer_admission.py:177-204,297-381`)。
  よって真の問いは「照合できるか」ではなく「Python leaf は wrapper の照合を信じてよいか」であり、
  wrapper を通らない呼び手 (oracle driver、将来の計測 sink) には照合が無い。
- **新事実 (レンズ A の実測)**: Pegasus login ノードでは非特権のまま UTS namespace を作れ
  (`/proc/sys/kernel/unprivileged_userns_clone=1`、`/proc/sys/user/max_user_namespaces=2147483647`)、
  hostname と FQDN を呼び手が変更でき boot_id は不変だった。したがって live hostname 照合は
  drift 検出であって authority ではない。計算ノードでの可否は未実測。→ {{F:hostname-forgeable-in-userns}}
- **親 brief の誤りを子が 6 件倒した。訂正して記録する。** 最も実害があったのは親の (P5)
  「排他の単位を leaf 側で強制すれば、call site の identity が merge で run 単位へ戻っても
  leaf が拒否できる」で、**成立しない** — leaf は identity 文字列しか受け取らず、
  caller が protocol/freeze digest と record を同期して偽装すれば通る。
  他に DW-O13 充足の過大主張、resume 拒否理由の取り違え (実際は `allow_resume=False`)、
  probe の過剰一般化、Unit 分割の不完全、成果物影響の射程過大。
- **親の M2 表を撤回**: host を「caller 支配外」としたのは偽。予約照合 3 件のうち caller の支配を
  完全に外れる source は現時点で 1 つも確認できていない。
- 稼働中の worktree-dev-wave-t523-holdout-admission が `s8b_floor_campaign.py:4716-4719` の
  `claim_identity` 式を同時に書き換えているため、着手前に差分を実測して scope を切った。
  `campaign_claim.py` / `reservation.py` はどの稼働 wave も触っておらず、
  衝突面は当該 4 行に限定できていた。実装へ進まなかったため衝突は発生していない。
- 段 8 自己改善: 候補 1 件を裁定したが**入口・reference は編集しない**。候補は
  「稼働 wave との編集面の重なりを着手前に実測する手順が dev-wave 正本にない」。
  `docs/dev-wave/` を意味検索した結果、`DW-O18` の「並行 wave が自分の編集 file を所有するなら
  main を取り込んだ木で既存走行へ相乗りさせる」は受入走行の話で、scope 決定の話ではなく、
  被覆は無い。ただし本件は単発かつ事故ではない (command 引数が指示しており実際に機能した) ため、
  DW-G03 の「族一般化には独立 2 例」に従い制度化しない。**1 例目としてここに残す** —
  同型が別 wave で再発したら 2 例目として節の新設を裁定できる。
- 子の工数: 段 2 plan 1 本 (codex, reasoning=max, read-only)、段 3 consult 2 本 (sol / luna)。
  いずれも `tools/check_codex_output.py` rc=0。実装子・fix 子は起動していない。
- 受入: docs のみ・実装差分ゼロだが DW-S04 に従い免除しない。段 7 記録前に全走した
  (結果は下記「受入」)。変異 matrix は DW-S04 の「実装しない裁定 + 実装差分ゼロ」により免除。
- 裁定パッケージ (問 1 = 排他の寿命、問 2 = 予約照合の範囲、問 3 = 繰り越し) を
  `output/insights/2026-08-16_t1140-claim-identity/ruling-package.md` に置き、
  裁定 inbox へも控えた。親の推奨は問 1 が (a) 生存プロセス単位 → (c) scheduler 照合の 2 wave 分割、
  問 2 が (a) submitter 所有 receipt を `PBS_JOBID` 束縛つきで authority と明示裁定。

## 次の一手差分

### 更新

- [T-1140] **P1・ユーザー裁定待ち (再裁定)**: 実装差分ゼロで返す。
  claim identity を protocol 単位にする指示は、そのままでは床値 campaign を
  **1 回で永久停止**させる — `campaign_claim.acquire_claim` が release も stale 回収も持たない
  永久 one-shot であり、production wrapper は同一 protocol・pilot mode を繰り返し投入する
  (実測: `floor_campaign.sh:947,962-964`、既存投入 3 件)。
  排他の寿命を (a) 生存プロセス単位 / (b) protocol 生涯 1 回 / (c) scheduler へ生死を問う /
  (d) 現状維持 から裁定する必要がある。親の推奨は (a) → (c) の 2 wave 分割。
  ただし (a) 単独では別 out_root 間の排他は成立せず
  (`campaign_claim.py:170-173`)、「protocol 単位の global 排他」とは表現できない。
  材料 = `output/insights/2026-08-16_t1140-claim-identity/`。
  base: 5b76b0eade67bb68b297605a2b493f7e8a4909e864fe7abdde718c5049e4279a
- [T-330] **P1・ユーザー裁定待ち (再裁定)**: 択 (c) の対象である予約照合を実装差分ゼロで返す。
  裁定材料が前提にした「scheduler 所有の create-only receipt」は**存在しない** —
  実在するのは submitter 所有 receipt (`submit_floor.sh:466-495`) で、
  `PBS_JOBID` 照合 (`floor_campaign.sh:452`) だけが scheduler 所有の錨である。
  かつ照合は既に shell wrapper 側に実装済みで (`floor_campaign.sh:406-555`)、
  Python 側にも receipt 検査が実在する (`certified_writer_admission.py:177-204,297-381`)。
  真の問いは「Python leaf は wrapper の照合を信じてよいか」であり、
  wrapper を通らない呼び手 (oracle driver、将来の計測 sink) には照合が無い。
  hostname 照合は非特権 UTS namespace で偽装可能なため authority に数えない
  ({{F:hostname-forgeable-in-userns}})。択一と親推奨は
  `output/insights/2026-08-16_t1140-claim-identity/ruling-package.md` の問 2。
  base: b1a9dbbcbd7ac50c0e138522f89b06656d6882f906efa1c015779bf610efd272

### 新規

- {{T:claim-exclusion-lifetime}} **P1・新規 ([T-1140] の再裁定で分離)**: 排他の寿命が裁定されたら、
  claim record へ protocol digest を持たせ、生存する持ち主がいるときだけ拒否する形を実装する。
  record には既に pid・proc_starttime・boot_id・job_id があり判定材料は揃っている。
  別ノードの生死は `/proc` から判定できないため、scheduler への照会 (`qstat`) を伴うかを
  同時に決める。変異は「leaf 単体 / wrapper を通らない呼び手 / 実運用 end-to-end」の
  3 分割で事前登録し、過剰拒否を検出する正例を必ず含める ({{D:exclusion-lifetime-constraints}})。
