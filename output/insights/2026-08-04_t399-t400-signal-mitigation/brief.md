# 段 1 brief — dev-wave t399-t400-signal-mitigation (2026-08-04)

- `authority: none`
- `default_effect: no-state-change`

## 依頼と survey 結論

依頼 = 「dev-wave のツール・コマンドで、コア数を使い切る並列化が無く、入れたら速くなるものを実装せよ」。
段 1 前の実測 survey: run_tests.py (xdist + login 自動 dispatch)、check_ai_provenance.py
(ThreadPoolExecutor)、build `-j` (site 由来) は並列化済み。check_docs.py は実測 1.0 秒で対象外。
land / fold の直列は D102 の設計。**残る実測済み直列費用は変異本走の「1 変異 = 1 qsub」の順番待ち**
(T-357 生死確認: harness 外側 579.3 s → 束ね 2.5 s、GO。直近 t244-p5 でも 10 走行 × 約 27 s)。
恒久実装 [T-360] は**ユーザー裁定済み (択 (a)、(130))** だが、D130 決定 (3) の条件 3 が D139 で
危険側 (SIGKILL 直送・`finally` 不走) に決着し、**mitigation 構成の実測 [T-399] が唯一の未実測経路**。
[T-399] は controller の admissibility 欠陥 [T-400] が先行前提 ((149) が明記)。

## scope

- **[T-400]**: controller (`output/insights/2026-08-03_t361-t362-cluster-probes/driver/run_probes.py`)
  の admissibility 連言 (`:1757` `all(validity)`) を「**probe が有効に観測した**」と
  「**attempt が安全だった**」の 2 field へ分離する。SIGKILL で cleanup が走らない危険側の結末が
  構造的に authoritative になれない欠陥の是正。恒久停止からの leg 進行回復を含む
- **[T-399]**: mitigation leg (`--accept-sigterm=yes` + `elapstim_req="00:03:00,00:02:00"` +
  `--warning-signal=elapstim:SIGTERM`) と split-warning leg を投入し、
  **捕捉可能な signal と grace が得られる構成が存在するか**を実測で決着する
- **scope 外**: [T-360] 本体 (D131 前提 6 点 + D105 supersede は次 wave)、[T-402] (flock 確定)、
  [T-364]。survey で並列化済みと確認した各ツールへの変更もしない

## 確定済みユーザー裁定 (再裁定しない)

- [T-360] = 択 (a) ((130)、worklog archive 0803-130)。D130 条件 1 充足
- D130 条件 4 = [T-363] で修正済み ((133))
- 判定語彙の事前登録 ((149) の先例): 未観測 signal は `UNKNOWN`、スケジューラ明示出力だけを根拠

## 不変条件

1. 判定基準は実測前に事前登録し、実測後に緩めない (規律 2/3)
2. **分離は分類であって弱化ではない** — 「観測の有効性」の基準を 1 つも落とさない。
   危険側の観測 (cleanup 不走等) が『有効な観測』かつ『安全でない attempt』として記録できる形にする
3. probe は本番 harness・wave worktree・main を変異させない (使い捨て root、D139 却下案の踏襲)
4. qsub 投入は runbook §8 checklist (qstat -Q / pegasusinfo / walltime / 単独性) に従う
5. 実装面は codex author が書く (D95)。親は brief・裁定・投入・記録のみ

## provisional 裁定 (攻撃対象)

- **(P1)** [T-401] の会計項 (`accounting_valid`、racct 遅延で false) は T-400 の分離で
  「観測有効性」の連言から外し「attempt 証拠」側 field へ移す — 弱化でなく分類、という位置づけ
- **(P2)** mitigation / split-warning の両 leg を投入する。キュー混雑 (実測: gen_S QUE 223) が
  ひどい場合は mitigation を優先し、split-warning 未投入なら worklog に未実施と明記
- **(P3)** 変異 matrix と受入全走は対象外 — production コード差分ゼロ (probe driver は
  `output/insights/` 配下の使い捨て、repo テストの参照ゼロを grep で確認)。(128)/(149) と同じ射程。
  check_docs / provenance / spool 系検査は実施

## 成果物の形・環境・分割

- 成果物: (i) controller 差分 (T-400)、(ii) 両 leg の実測 verdict と evidence、(iii) worklog /
  decisions / failures fragment ([T-399] [T-400] [T-360] 前提の更新)、(iv) 本 brief 一式の凍結
- 環境: controller = pegasus02 (login)、probe job = gen_S。**リスク: gen_S QUE 223 本の混雑。**
  controller の bounded deadline を尊重し、期限内に完了しない attempt は fail-closed のまま報告
- 並列分割: 実装は controller 1 ファイル中心 → author 1 本。段 3 敵対 2 レンズ並列、
  段 6 レビュー 2 本並列。probe 投入は leg 単位で直列 (controller の設計どおり)

## DW-G05 成果物影響

[T-399] を放置すると [T-360] (変異本走 transport) が着手不能のまま残り、certified 選択を支える
変異 matrix の実測が wave あたり実測 3〜10 分の順番待ち直列費用を払い続ける。[T-400] を放置すると
危険側の結末が構造的に authoritative になれず、「捕捉可能な構成は無い」という決着すら記録できない。
