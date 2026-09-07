---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: rulings-full15-verdicts
seq: 1
title: /rulings 全件 第 15 回の裁定 — 索引 21 件のうち推奨のある 17 件を、ユーザー委任により Fable が再検討した推奨で裁定した。持ち越し stub の本文を archive まで遡っていなかった収集漏れ 14 件を回収し、相談と再検討が起草推奨 6 件を覆した (docs のみ、branch worktree-rulings-full15-verdicts)
---

## 本文

- **ユーザー裁定は委任の形である** —「モデルを切り替えました。あなたは fable ですが、この裁定推奨一覧は
  opus, sol で出されたものです。あなたが再度検討し、推奨を考え、その通りに main land まで行ってください」。
  索引 21 件のうち推奨のある 17 件を Fable が再検討し、確定した推奨をそのまま裁定として記録した。
  推奨を付けない 4 件 (稼働中 wave の scope 外所見、実行場所分類の実測、別 OS 利用者の配置、未 push 132 commit)
  はユーザー手番のままで、本回では動かない。裁定の出所と scope 制約は
  {{D:rulings15-delegated-reexamination-minimal-scope}}。
- **収集漏れ 14 件を回収した。** 末尾エントリの次の一手 528 項のうち 510 項は carry stub で、本文は
  `docs/archive/` にある。初回走査は stub 行にしか語を当てておらず、実体側の『ユーザー裁定待ち』
  『裁定する』『択一』が 14 件落ちていた。別系統相談 (B) と、親が carry 鎖を archive まで再帰解決した
  全走査が独立に同じ 14 件を出し、各件を decisions で主題照合してから索引へ載せた。F888 の再発として
  記録し、入口の是正は同 file を所有する [T-2440] へ合流させた (第 14 回が F897 の是正を別 wave へ送った先例)。
- **起草索引の 2 件は既裁定で除外した。** masstree の autotools ビルドで CC/CXX が manifest へ束縛されない件と
  第三者 header の bytes 束縛は、D1648 (compiler identity は契約閉包に含めない) と D1657 (関門と測定 build の
  第三者 header 閉包は束縛しない) が既にユーザー裁定済みだった。相談 (A) は「D1679 の誤引用、正しくは D601」と
  して起票を推奨したが、D601 は観測 manifest を build 要求へ伝播させる決定であって閉包を第三者 compile 入力へ
  広げる決定ではなく、既裁定 3 件に反するので採らなかった。相談は既裁定照合の代替にならない (D1680 の再確認)。
- **相談と再検討が起草推奨を 6 件覆した。** いずれも現物で裏を取ってから覆している —
  (1) B-4 事前登録 §11.1 / §11.2 の採否は D1641 決定 3 で既裁定 (新規の採否ではない)、
  (2) paired-session driver の 4 穴は probe 状態の生値からの再導出だけ閉じる (`_probe_payload_status` は
  内部整合しか見ない)、(3) 床値は exact 有理数で再凍結する (`block_score` の `<= exact_floor` が等号込み)、
  (4) C04 の `field_paths` は判定器が完全一致で読む (D1375 の同型先例)、
  (5) 受入台帳 `nodeid_count` は衝突減の実測を着手条件にする、(6) 上記 masstree の除外。
- **Fable の再検討で加えた形は「段階化」である。** growth hold は赤 0 件なら追加裁定なしで解除
  ({{D:growth-hold-release-after-measuring-reds}})、1000 マイクロ秒超は探索 3 点を先に
  ({{D:static-backoff-tail-grid-two-stage}})、`nodeid_count` は merge 比較の条件付き
  ({{D:ledger-nodeid-count-conditional-removal}})。往復を減らしつつ、結果を見る前に規則を置く。
- **自己改善 gate は発火した** (収集漏れの実測)。入口 `.claude/commands/rulings.md` は byte 予算が満杯で、
  同 file の是正を [T-2440] が持つため、本 wave は記録に留め入口を編集しない。[T-2373] が入れた検査
  (語走査の件数と索引件数の突き合わせ) は、語を実体に当て直して初めて働いた。
- **相談の子は 3 本とも launcher の受理形で `not_accepted` になった** (read-only の子は出力 file を書けない)。
  中身は成果物 `attempt-0001.output.md` から 3 本とも回収した。第 14 回と同じ受理形の問題であり、子の失敗ではない。
- **worktree 作成直後に main 側の欠陥を踏んだ。** 本 wave 開始 20 分前に land した docs commit が
  `.codex/worktrees/*` の gitlink 110 件を tree に含めており、新規 worktree の submodule 初期化が
  `No url found for submodule path` で全滅する。混入元の稼働 session (T-2412 wave) へ通知したところ、
  原因は主 checkout に cwd を残したままの `git add -A` で、是正は別 session「next-tasks skill relocation」が
  着手済みとの返信を得た。是正の閉包は (a) index からの除去、(b) 当該 commit の known-violation 登録
  (`.codex/` は実装 prefix なので Codex author) の 2 点で、`.gitignore` への `.codex/worktrees/` 追記は
  F599 (変異 harness が主 checkout の status bytes を観測面にしている) に触れるため含めず、可否は
  ユーザー裁定パッケージへ回す — 同 session の訂正で親も同意した。F と T の起票はその wave に任せ、
  本 wave は二重に起票しない。本 wave は index から
  一時的に外して本物の init tool を通し、直後に index を HEAD へ戻す回避で gate を通した
  (marker は tool が書いたもので、手書きしていない)。
- 工数: codex 子 3 本 (consult)。実装子ゼロ。計算ノード投入は受入と provenance 監査のみ。

## 次の一手差分

### 完了

- [T-2361] A-5 の job 本体は親リポジトリ側の登録簿も prune しないと裁定した ({{D:a5-job-no-superproject-prune}}、D1700 と同じ理由)。残件なし。
  remaining: none
  base: 1dcd533a97b3dcea3cf9d6265e11b060c76fed9ce2863fb631cf86255705c68a
- [T-2373] 第 15 回で効果を確認した。語走査の件数と索引件数の差は 0 にならず、原因は語でなく corpus (stub 行に当てて実体に当てていない) だった。F888 の再発として記録し、是正は [T-2440] の範囲へ合流した。
  remaining: none
  base: 593d10500e6b443582463fd5ca9cbebfd8fa7e32122053219c8c39d6e7392aae

### 更新

- [T-2140] **P1・裁定済み ({{D:b4-prereg-four-fields-settled}}、第 15 回) → 実装待ち**: (a) §5.1 の「その artifact」は分析 source file と読み本 wave の記入を維持、(b) 開始予定日時は固定せず D1477 の順番付けに委ね実投入時刻を投入時に追記、(c) §11.1 / §11.2 は D1641 決定 3 と D1695 の反映であって新規の採否ではない、(d) §7.2 / §10 の陳腐化は D1765 の正誤表で直す。残るのは B-4 事前登録への反映作業。
  base: 86d22e7e318f2cf5bf2417c1f8c1744d3ccc6c331ad52d20f9cd8f7eb2946a27
- [T-2418] **P1・裁定済み ({{D:static-backoff-tail-grid-two-stage}}、第 15 回) → 探索走の実装・投入待ち**: 2000 / 4000 / 9999 マイクロ秒の 3 点を既存 sweep と同じ反復数・walltime 枠で探索し、探索値は正式へ混ぜず開示する。本格格子と停止基準は探索結果を見た後・本格 cohort 投入前に事前登録する。
  base: 698619ed6b866b6fa317143f5583ef7591190b87811fe6171e4487c921c8b9e2
- [T-2423] **P1・裁定済み ({{D:floor-name-protocol-field-added}}、第 15 回) → 実装待ち**: 凍結 spec に `protocol` を明示 field として足す (択 (a))。対照対 driver の凍結作業に含める。
  base: 98ef45ca47714e2e68b9884f8224f20c8d7a2f58f0cd29fe244189f8768e16c6
- [T-2417] **P2・裁定済み ({{D:policy-arm-perf-measured-uncertified-not-headline}}、第 15 回) → 事前登録・実装待ち**: 全 identity への認証は行わない。巡回順の block 設計と独自の事前登録で trace 無効の性能測定を行い、未認証を成果物へ明記し headline へ入れない。認証は昇格させたくなった時点で選定腕だけ諮る。
  base: 2e58725e71110985d7123da64e9670bd59cbdcdb8529ef4c35c9d5f4a8cd1f79
- [T-2431] **P2・裁定済み ({{D:a1-uncooperative-same-uid-writer-out-of-boundary}}、第 15 回) → 明記待ち**: 非協調な同 uid writer は正しさ境界に含めない。現行の決定的順序を維持し、宛先確認と unlink の間の競走を既知限界として明記する。
  base: 86bc1f3694b9855154f696557dbc379b15d49e56e56621093ddcfa63f0f7890f
- [T-2400] **P2・裁定済み ({{D:cli-check-claim-narrowed-no-structural-pin}}、第 15 回) → 文言修正待ち**: 構造 pin は足さない。検査の主張範囲を「CLI と library の transport 等価性 (出力の一致)」へ書き換える。
  base: a8ea9fe209d617b33544d0baf10fcbe12297b13fe0e979d3090df12dd6489644
- [T-2436] **P2・裁定済み ({{D:verifier-reason-order-sorted}}、第 15 回) → 実装待ち**: `_reasons()` の WW intersection を key 順に整列する。着手前に enforcement closure の digest 変化と凍結成果物の再発行要否を pin 閉包で確かめる (相談の当たり: 既存 anomaly 5 件は再発行不要、live resume は D1388 で再走対象)。
  base: 90133d01ccd46694bafc30ba8619a2c5d7440573f47bab244976a0eebb714851
- [T-2415] **P3・裁定済み ({{D:paired-driver-raw-status-rederive-only}}、第 15 回) → 実装 1 件 + 明記待ち**: probe の status を生の returncode / stdout / stderr から既存分類器で再導出して照合する修正だけ入れる。spec 差替え・path 差替え・`probe_fn` 差替えの 3 件は限界として明記する。
  base: 0e2cd360b5326fc779407380cdc065a18ebaea46346b2e50e07f83cfcbcc31af
- [T-2425] **P3・裁定済み ({{D:floor-exact-rational-refreeze}}、第 15 回) → 実装待ち**: 床値 D は exact な有理数で凍結し直す (択 (b))。`block_score` の等号込み比較で引き分けが勝敗へ変わる経路が実在するため。driver 側の凍結作業に含める。
  base: 58cc10ffc6c4ffb4652c031515104018b2d8da1293a94cfd312e3566d8f70286
- [T-2427] **P3・裁定済み ({{D:c04-reachability-only-and-field-paths-exact}}、第 15 回) → 文言修正待ち**: C04 の machine-checkable claim は到達可能性に限定し、契約側の文言を実検査の範囲へ合わせる。位置・支配関係の検査は足さない。
  base: 9b0ac252c996a2343a347d5477732561e1bafa19605922b96de145c098509bae
- [T-2428] **P3・裁定済み ({{D:c04-reachability-only-and-field-paths-exact}}、第 15 回) → 実装待ち**: (a) callee 本体の検査は足さず射程を明記。(b) `field_paths` 2 件は判定器が C04 固有の exact-set 照合と既存 AST helper で完全一致で読む最小修正を入れる (D1375 の向き)。
  base: 265a7e7af42f833b028ea5cbcc99030da98a3f4c67821349cae1d162aaf795c0
- [T-2432] **P3・裁定済み ({{D:submission-failure-receipt-stays-as-is}}、第 15 回) → 明記待ち**: `submission-failure.json` は原子的公開へ揃えない。千切れた failure receipt の占有を現状限界として明記する。
  base: 6e609161771dda8403e885174fba75a05b54705a036ac7be898ce1465d752789
- [T-2434] **P3・裁定済み ({{D:dev-wave-reasoning-doc-matches-cli}}、第 15 回) → docs 修正待ち**: worker 契約の記述を「値は xhigh (docs 権威導出)、`--reasoning` は CLI 引数として渡さない」へ改め、adoption pin を同じ変更単位で更新する。byte 超過は既存文面の組替えで吸収し予算は上げない。
  base: c749903ad872bc8e430045cd88921078708c66c9141c23d99719e296876c0b41
- [T-2438] **P3・裁定済み ({{D:witness-exact-int-bool-negative-case}}、第 15 回) → テスト追加待ち**: bool を使う負例を足し、登録 SURVIVED の変異 2 件 (`b060.m23` / `b060.m24`) を KILLED へ移す。
  base: efed5e00a783ac687c3904d9bd359d09a4730ca7b4018fbbd6cba543815cc0d8
- [T-2403] **P3・裁定済み ({{D:growth-hold-release-after-measuring-reds}}、第 15 回) → 実測待ち**: hold を外したときの赤 node 数と理由を 1 回観測する。赤 0 件なら追加裁定なしで解除してよい。赤があれば件数と理由を添えて再提示する。
  base: 9218b59c453fdc7f79042ca84eed3cb1ec468fedac6f4ddae939f59e3391c2c4
- [T-2440] **P2・新規 → 是正範囲を 1 件広げた**: `/rulings` の入口の出力規則を直す (F897)。加えて、第 15 回で実測した収集漏れ (F888 再発: 走査語を carry stub 行にしか当てず、`docs/archive/` の実体本文に当てていなかった) の是正として、収集 §1 に「carry 鎖を archive まで解決した実体本文へ当てる」を明記する。入口の byte 予算 (5,623、現在 5,607) の中で 2 件を同時に直し、予算の引き上げは独立審査対象なので行わない。
  base: 8076a60b016592dd78e3b7e814dbf03a03d7320910bb92415ecd4771776882fa

### 新規

- {{T:ledger-nodeid-count-conditional-removal}} **P3・裁定済み ({{D:ledger-nodeid-count-conditional-removal}}、第 15 回) → 条件付き相乗り待ち**: 受入所要台帳の `nodeid_count` (`len(durations)` の派生値) を台帳から外して consumer が数える方向。専用 wave は立てず、次に台帳を触る wave へ相乗りさせる。着手条件 = 同一 base から相異なる nodeid を足す 2 枝の 3-way merge を現行形と count 無し形で比較し、衝突 hunk が実際に減ること。減らなければ現状維持で終端する。
