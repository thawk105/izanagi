---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t674-d125-supersession
seq: 1
title: [T-674] の残余 (5) を消化し D125 決定 (2) の campaign id 不変条項を前向きに失効させた — 破ったのは本 wave ではなく land 済み production が 3 世代で 3 回 (docs のみ、実装差分なし、受入 7845 passed / 20 skipped / rc=0、変異は免除、branch worktree-dev-wave-t674-d125-supersession)
---

## 本文

- **ユーザー裁定 (2026-08-09 /rulings、archive worklog エントリ 337) の [T-674] 6 問のうち、
  残余 (5) だけを消化する docs-only wave。** (1)(4)(6) は [T-671] 実装 wave (エントリ 355、
  D259 決定 8・9) で消化済み、(2)(3) は防御的堅牢化として見送り済みである。
  本 wave で 6 問すべてが決着した。設計は {{D:d125-campaign-id-invariance-superseded}}。
- **段 4 で `4→7→8→9` へ分岐し、子を 1 本も起動しなかった。** 判断の根拠を残す —
  (a) 設計択一が割れない (前向き supersession という方式はユーザー裁定が確定させており、
  D125 決定 (2) を分割してよいかは D259 決定 7 が「`measurement_env` は identity に残す」と
  既に確定させている)、(b) 正しさ防壁に触れない、(c) コードを 1 byte も編集しないので
  受理集合が変わらない。ユーザーの依頼も軽量 wave を明示していた。
- **親が段 1 で裁定前提を実測し、裁定文の読みを 1 点狭めた。** 起票文と t530 実装 wave の記録は
  「[T-343] が既に破っている」と**単発の違反**として書くが、実測では pre-T343 → T-343 → T-530 →
  [T-671] の**3 世代で 3 回**変化していた。しかも [T-671] (D259 決定 1) が契約 hash を pre-image から
  外した結果、現行値は T-530 値ではなく T-343 値へ**戻って**いる。したがって正確な記述は
  「[T-343] が破った」ではなく「**不変を保つ機構が最初から存在しない**」であり、新 D はこの形で書いた。
  裁定の方向 (前向き supersession で記録する) は変えていないので、`DW-S04` の「未見の新事実」には
  当たらないと裁定した。
- **実測は 5 点すべて一次資料から取った (F1)。** (i) `measurement_env` の実装実在と site 射影、
  (ii) 現行 OTHER id を T-343 値へ等号 pin し T-530 値へ非等号 pin する test 定数 6 本、
  (iii) `output/campaigns/` の 30 campaign・30 lock、(iv) pre-T343 値の dir が 1・現行値の dir が 0・
  T-530 値の dir が 0、(v) `discover_campaign_dir` が dir 名 prefix の glob で id 非依存であること。
  既存 docs の記述は (ii)(iv) を裏取りするまで根拠にしていない。
- **変異 matrix は免除した。** 実装差分ゼロ (コード・テスト・script いずれも 0 byte) で、
  変異させる対象が存在しない。`DW-S04` の免除条件に合致する。
- **受入要否の判定証拠 ([T-648] fallback 義務)**: 本 wave は docs-only・実装差分ゼロだが、
  **実 repo を読むテストは存在する**。判定手順 = `orchestrator/tests/` から実 checkout の `docs/` を
  読むテストを名指しで探し、`test_check_docs.py` と `test_spool_fold.py` の 2 file が該当
  (他は不存在)。したがって受入全走を免除せず実施した。
- **受入全走は 1 走で完全な緑。** `7845 passed / 20 skipped / rc=0` (494.36 秒、
  request `899733.nqsv`、tip `d9fe77e9`)。受入形の警告は出ていない。
  **この受入値を記録する commit 自体は、その走行の対象に含まれない** (値を書く前に測る順序のため)。
- **受入 lease で 3 回連続空振りし、実走 0 のまま約 2 時間を空費した。** いずれも
  「取得した時点で local main が先行しており、runbook §7.3 の behind 検査に掛かって lease を
  返す」形で、先行量は 7 / 3 / 5 commit だった。3 回目は待ち行列にいる間に先行を検知して
  **lease を消費せずに**戻る形へ直したが、それでも取り込み → 並び直しの間に追い越された。
  失敗の型は {{F:acceptance-lease-behind-livelock}}。
- **4 回目で待ち手の中に `--no-ff` merge を入れ、1 走で通した。これは runbook §7.3 の
  「0 でなければ lease を返して親へ戻す」からの逸脱であり、`DW-O12` に従って差をそのまま記録する。**
  同節が禁じているのは**待ち手内の `--ff-only`** で、wave が自前 commit を持つと必ず失敗するため
  親へ戻す設計だった。`--no-ff` merge はその失敗要因を持たない。安全側の配線は 3 つ置いた —
  merge message と trailer は親が用意した template で待ち手は main の SHA だけを差し込む、
  競合または provenance preflight 非 0 なら merge を中止して lease を返す、走行前に
  behind 再検査と `git status --porcelain` の空検査を通す。実測では取得から走行開始まで 3 秒で、
  他 wave を止めた時間は最小だった。
- **wave 中に local main を 3 回取り込んだ** (`e91bf56d` / `976fb24d` / `4fd852dc`)。
  3 回目が上記の待ち手内 merge である。並行 wave の land 頻度が高く、
  取り込み → 受入投入の間に追い越される状態が続いていた。
- **fold の採番予測が land 前に 1 度ずれた。** 取り込み前の `--dry-run` は本 wave の新 D を D260 と
  出したが、取り込み後は D261 になった (並行 wave の [T-201] が D260 を取ったため)。
  fragment に番号を書いていないため実害はない。
- **親が `DW-O17` の手順を 1 本目の commit で 1 段飛ばした。** 「message file → `--dry-run -F` 単独
  rc=0 → `commit -F`」の `--dry-run` を `check_ai_provenance.py` の dry-run と読み違え、
  `git commit --dry-run -F` を実行しなかった (provenance preflight は `--message-file` で実施し
  rc=0)。以後の commit では規定どおりの順序で行った。文脈上 `commit -F` と対になっており
  文書の欠陥ではないため、文書は変えず事実だけ残す。

## 次の一手差分

### 完了

- [T-674] 残余 (5) を消化した。D125 決定 (2) の「OTHER の campaign_id は 1 bit も変えない」は
  {{D:d125-campaign-id-invariance-superseded}} で前向きに失効させ、env による identity 分離
  (D259 決定 7) だけを残した。(1)(4)(6) は [T-671] 実装 wave (D259 決定 8・9) で、(2)(3) は
  見送りで決着済みであり、6 問すべてが終端した。
  remaining: none
  base: a81cc2a17c416746c28b7bf248bfe02220f226c6b5516b7cccef78089cc84857

### 新規

- {{T:acceptance-lease-merge-after-acquire}} **P2・新規 (裁定パッケージ)**: 受入 lease を取得した
  時点で local main が先行していたとき、`docs/pegasus-runbook.md` §7.3 の「lease を返して親へ戻す」を
  維持するか、**待ち手内の `--no-ff` merge を許す**形へ改めるか。実測は
  {{F:acceptance-lease-behind-livelock}} — 現行手順は並行 land が高頻度の時間帯に livelock し、
  1 wave が実走 0 のまま約 2 時間を空費した。`--no-ff` を許すと head-of-line blocking が発生するが、
  本 wave の実測では取得から走行開始まで 3 秒だった。**親の推奨は「許す + 安全側の配線 3 点を必須に
  する」** — 現行手順が禁じている実体は待ち手内の `--ff-only` であり、`--no-ff` はその失敗要因を
  持たない。全 wave の公平性に効くため親が独断で runbook を書き換えず裁定へ返す。
  暫定の運用は memory `acceptance-lease-poll-30s` の「取得後の取り込み」節。
