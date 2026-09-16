# 段 1 brief — [T-2288] B-4 床値 spec 凍結の binder precheck (実装差分ゼロ)

2026-09-17 06:46 JST。親 (Claude Opus 5)。起点 local main `abc7085ae6e1a69dc294c4f827ed7949e6df5305`。

## 研究前進

論文主張: B-4 reflux ablation の事前登録 §5 floor 欄が権威 artifact で埋まると、材料レポートの分析 verdict が
1 分類 (`floor_domain_error` → protocol violation) から §7.1 の 4 分類へ実効化する。その floor 欄を埋める
測定は凍結 spec (`floor-pair-spec/v3`) から始まり、凍結 wave は A-5 (ユーザー裁定待ち) の値を入れて spec を
commit し `--validate-only` を通す。**本 wave は凍結 wave が踏む binder (spec ⇔ HEAD tracked blob、
`source_commit` の祖先性、binary sha256 ⇔ 配置 bytes、build receipt の tracked 束縛と strict 検証、較正の
tracked 束縛 + admission + cell 一致) を、実 checkout・実 record・実較正・実 binary で初めて通し、落ちる箇所を
凍結前に前出しする。** 完了判定: 3 spec (rr95 / rr50 / rr5) の `--validate-only` が rc=0 で plan を返す、
または落ちた箇所を再現手順・エラー文つきで特定して insight に返す。裁定前 precheck は凍結時の成功保証に
ならない (次 wave 提案の codex 判断のとおり)。価値は binder 欠陥の早期発見に限る。

## scope

1. 捨て branch `precheck-t2288-placeholder-specs` (起点 = local main `abc7085ae`) に placeholder 値の 3 spec を
   1 commit で置く。実装面 (D95 決定 2) は 1 byte も変えない。
2. 同 checkout で `python3 -m orchestrator.campaign.b4_binary_record place --record <T-2636 record>
   --source-root /work/1/SFC/tanab/izanagi-b4-floor-binaries --env-tag pegasus --repo-root <worktree>` を実行
   (出力先 `output/env/pegasus/binaries/<sha256>` は ignored、D2069 項 3)。
3. `python3 -m orchestrator.campaign.floor_pair_driver --repo-root <worktree> --spec <spec> --expected-sha256
   <sha> --validate-only` を 3 spec で実行し、rc・stdout (plan)・stderr を保全する。
4. 負対照 3 本 (実装面の追加なし、実走のみ): (a) 期待 sha256 を 1 桁変える、(b) spec を uncommitted に
   1 byte 変えて HEAD blob 不一致にする (`DW-O19` で即時復元)、(c) `source_commit` = HEAD の spec を作り
   「真の祖先」拒否を確かめる。いずれも rc≠0 と落ちた検査名を記録する。
5. 成否と落ちた箇所を insight `output/insights/2026-09-17/t2288-binder-precheck/` (README + verbatim) に返し、
   worklog fragment を spool へ置く。wave branch に載せるのはこの docs だけ。
6. 捨て branch は land しない。placeholder spec を凍結にも正式 evidence にもしない (§11.1「AI が起草した候補値を
   無裁定の既定値として凍結へ入れない」)。

scope 外: A-5 の値の起草 (裁定待ち)、gate・検査・test の追加、driver / record / place の修正、本番一式の
再構築 (build・較正の再取得)。準備が本番一式の再構築になる場合は中止して理由だけ返す (依頼文)。

## 確定済みユーザー裁定と既決

- D2069: binary 配置規則 `output/env/<env_tag>/binaries/<sha256>` (ignored 複写)、`place` CLI。
- D2088: `perf_config` = `extime 3 / reps 5 / ycsb_max_ope 10`。
- D2089: 3 cell = 3 workload × (t48・skew 0.9・rmw 0)、records rr95 1M / rr50 1M / rr5 2M、各 spec 1 cell。
- D2090: rr50 の較正は g2 `94a4b79f…`。rr95 `5c836a22…`、rr5 `2b7ba072…` は唯一の適格。
- D1641 決定 3: site Pegasus 計算ノード、env_tag `pegasus`、clocks_per_us 2100、統計関数・欠測規則 (driver 定数)。
- §11.1 (D1383): AI 起草値を無裁定で凍結へ入れない。本 wave は A-5 の値を書かない。

## 不変条件

- 実装面差分 0 (変異 matrix 免除、DW-S04)。受入全走は免除しない。
- 規律 2: binder のどの検査も緩めない。落ちたら spec 側や driver 側を「通るように」直さず、落ちた箇所を報告する。
- placeholder は placeholder と分かる値 (2030 年の窓、`precheck-placeholder-*` の識別子、ゼロ seed) にし、
  A-5 の候補値と読める値を置かない。
- main へ載るのは insight と spool fragment だけ。`output/env/pegasus/binaries/` を tracked にしない。
- 捨て branch の名前・commit SHA・spec sha256 を insight に残し、bytes は捨て branch と job dir にだけ置く
  (insight verbatim には spec の sha256 と field の要約を置き、spec JSON 全文は複製しない — 凍結候補と誤読
  される bytes を main へ入れないため)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) placeholder spec の置き場は `output/env/pegasus/floor-pair/precheck-placeholder-t2288/spec-rr{95,50,5}.json`
  とする。較正 (tracked、`output/env/pegasus/calibration/registered/`) と binary (`…/binaries/`) の兄弟で、
  env 軸に揃える。**本番 spec の置き場・命名は凍結 wave の決定であり、本 wave の path を先例にしない。**
- (P2) 出力 relpath (窓 2 本 + summary) は spec と同じ dir に置く (`_validate_output_path` が parent dir の
  実在を要求し、git は空 dir を持たないため)。
- (P3) candidate / reference は別 `artifact_id` で同じ binary path・sha256・receipt を指す (D2069 項 1、
  driver は同一 artifact_id を拒否するが同一 bytes は許す)。
- (P4) `source_commit` = local main `abc7085ae` (spec commit の親)。凍結 wave も同型 (spec commit の親を書く)。
- (P5) 負対照は driver の既存拒否を実走で確認するだけで、test・gate の追加はしない。
- (P6) 軽量版・子ゼロ (実装面なし、設計択一なし、受理集合の変化なし)。

## 成果物

- insight README: 成否、落ちた箇所、binder の各検査が実際に何を読んだか (path・sha256・commit)、負対照の結果、
  凍結 wave への注意点 (place を凍結 checkout で先に実行、source_commit の取り方、policy の時間依存 D2069 項 6)。
- verbatim: `s1-brief.md`、`place.log`、`validate-rr{95,50,5}.{out,err}`、`negative-{a,b,c}.log`、
  `placeholder-specs.sha256` (3 spec の sha256 と捨て branch commit SHA)。
- spool fragment: worklog 1 件。decisions は起こさない (新しい設計判断なし)。failures は binder が実欠陥で
  落ちた場合だけ候補にする。

## 並列分割方針

子ゼロ。親が実走・記録する。受入全走は段 7 の記録 commit 後に 1 回 (`dev_wave_wait.py acceptance`)。

## 段 1 で実測した前提 (模擬なし、すべて実物)

- record `rr20--stock_common.json` は tracked、`validate_portable_binary_record(expected_policy=None)` OK、
  receipt `policy_sha256` = 現行 policy `949ddcc2…` (place の policy 検査は今日通る)。
- durable binary 701,760 bytes 実在。worktree に `output/env/pegasus/binaries/` は無い (未配置)。
- 較正 3 件は driver と同じ入口 `load_verified_calibration(pegasus, 2100, required)` を通り、値は D2089 と一致。
- `store_binaries` に site gate 無し、`--validate-only` は `_assert_live_environment` を呼ばない → login node で
  実走できる。計算ノード job は不要 (F660 の新規 Pegasus 実行体も不要)。
- 先例: 2026-09-09 の [T-2288] cellset wave は「実 checkout で凍結 spec は作れない」(receipt 0 件・較正 rr95/rr5
  0 件) と実測。その後 T-2636 (receipt)・較正 3 件・D2069 (配置) が揃い、`load_frozen_spec` の source_commit
  契約も「真の祖先」へ変わった。実 checkout で `load_frozen_spec` を通した記録は 0 件 (純増)。
