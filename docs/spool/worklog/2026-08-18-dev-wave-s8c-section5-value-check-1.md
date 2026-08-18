---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-s8c-section5-value-check
seq: 1
title: 8c §5 判定パラメータ欄に値 validator を置いた — 違反値を発効判定の内部で倒す最後の一手は凍結本文と衝突し裁定へ返す (コード + テスト、branch worktree-dev-wave-s8c-section5-value-check、変異 matrix = baseline PASSED・10/10 KILLED・SURVIVED 1 (事前登録どおり)・MISMATCH 0)
---

## 本文

引数が指示した「§5 の値セルを機械検証する consumer」を実装した。設計判断は
{{D:section5-value-violation-reporting}}。

**起動時の重複検査。** 引数の指示どおり
`git diff --name-only main...worktree-dev-wave-t822-c02-receipt-v2` を実行し空を確認した。
t822 は (656) で着地済みで、二重着手は無い。同 file を触る生存 branch も無かった。

**引数の素直な実装 (A) を親が不採用にした。** 引数は「違反値は本書を未発効へ倒す形にする」と
書いていたが、一次資料 2 点がこれを塞ぐ。(1) `docs/phase3-8c-preregistration.md` の
「発効の判定と条件契約の凍結」節は**凍結範囲**であり、「記入済み」を canonical JSON か否かだけで
定義したうえで「**欄ごとの型・単位・範囲の検証は本手続きの対象外である**」と明記している。
違反値を `FieldStatus.INVALID` へ倒す形はこの凍結本文と正面から食い違う。(2) 同節の D458 は
判定器の受理集合・拒否理由を変える変更に `DECIDER_VERSION` の bump と新世代 record を要求するが、
新世代 record の `ruling_reference` はその commit 時点の `docs/decisions.md` に `## D<N>.` 見出しの
実在を要求し (`_assert_rulings_exist`)、D 番号は land の fold でしか採番されない。並行 8c wave も
複数走っており世代番号の衝突は merge で解けない。凍結 record の更新は引数が scope 外と明示している。
そこで採ったのが設計 E — 記入済み判定と `effective` の連言式を一切変えず、値制約違反を
`Section5ValueViolation` として構造化報告し、**実効的な閂は repo 不変検査へ置く**形である。
受理集合は不変なので bump も新世代も発生しない。

**この wave が達成していないこと。** 違反値が判定器の内部で `effective` を偽へ倒す形は
実装していない。文書自身の設計はそれを §6 条件 7 経由で行う構造 (条件 7 は
「validator が production 経路から到達可能でなければ充足しない」と名指しする) だが、条件 7 は
`machine_checkable: false` であり、反転は引数が scope 外と指定した項目に一致する。**裁定は
ユーザーへ返す** ({{T:s8c-section5-violation-effective-wiring}})。現行 checkout では 12 条件の
いずれも充足を返さないため、違反値があっても発効はしない。

**段 3 の敵対レンズ 1 本が 2 回とも成果物ゼロで落ちた。** 1 回目は wall-clock 3600 秒で SIGTERM
(model call 26、読み込みに予算を使い切った)。読む範囲を行範囲で限定し 40 分の締め切りを書いた
prompt で再投入したが、2 回目は **model call 4 件で 3000 秒** — 読みすぎではなく外部応答の停滞で、
計 6600 秒を失った。3 回目は投入せず、同レンズ (fail-open / 恒真化) の担当を段 6 の敵対レビューへ
移した。段 3 の敵対は実質レンズ B 1 本 + 親の一次資料確認で成立させている。詳細は
{{F:codex-consult-stall-zero-output}}。

**段 6 のレビュー 2 本が出した所見。** レンズ B (受理) は「この差分に `DECIDER_VERSION` bump は
不要」を独立に確認し、8b §10.2 の制約の写しに過不足がないこと、`n` と観測反復数の exact 一致を
manifest 側の責務として混ぜていないことを検証した。レンズ A は `## 総括` を fence 内に書いたため
機械受理されなかったが (output 3141 bytes、`validator_rc=1`)、内容は有効で **real 所見を 1 件**
当てた — 生き doc の検査は当該欄が未記入である限り validator を一度も呼ばず、validator を丸ごと
削除しても緑のままになる。fix で positive control を足した (生き doc の bytes へ 1 軸だけ違反する値を
差し込み、置換の空振りも検出する)。**refuted は 1 件** — 空の `{}` が validator へ届かない件は、
空 container を `UNFILLED` とする既存規約どおりであり、変えると触ってはならない既存判定の変更になる。

**段 3 レンズ B が親の (P2) を 1 点覆した。** `sd_max` の `-0.0` を拒否する計画は過剰拒否である。
8b §10.2 は「有限の非負」としか要求しておらず `-0.0` は非負である。実装は `-0.0` を受理し、
`delta_min` は正値判定により `-0.0` を落とす形にした。過剰拒否を検出する正の対照も変異へ登録した。

**変異 matrix が親の申告を 1 度覆した。** attempt 1 は baseline PASSED・7 KILLED・1 SURVIVED
(事前登録どおり) だったが 3 件が MISMATCH になった。いずれも変異が生き残ったのではなく、**親が
申告した期待 node 集合が不完全**だったためである。特に過剰拒否の正の対照 (`sd_max` の下限を誤って
厳しくする) は 22 件が赤くなり、想定より広く検出できることが分かった。実測 node で再登録した
attempt 2 が baseline PASSED・10/10 KILLED・SURVIVED 1・MISMATCH 0 で完全一致した。
attempt 1 は erratum として残す。

**main 取り込みで来歴検査が merge を止めた。** main 側の別 wave が
`test_s8c_preregistration_invariant.py` の `WAVE_REQUIRED_PATHS` へ 2 行を足しており、本 wave も
同 file を編集していたため、3 方向結合の結果が両親のいずれとも異なり
`check_ai_provenance --message-file` が rc=1 (実装面に Codex role=author が無い) を返した。
記録済みの恒久手順どおり merge を abort し、main 側 2 行だけを先取りする Codex 実装子を投入して
から merge し直したところ preflight は緑になった。なお同子は正常終了 (exit 0、84 秒) したものの
報告が 327 bytes で 500 bytes 下限に届かず機械受理されていない。作業が極小で「2〜5 行で書け」と
指示した親の側の誤りであり、差分は親が `git show main:` と逐語照合して採った。

**親の実測の限定。** 「executable な pin は無い」は現行 checkout の `_classify_section5_value` /
`_parse_section5` について正しく、過去 insight の記述は実行 callsite ではない。
`_markdown(filled=True)` の呼び出しは 16 箇所だが fixture は 1 箇所に集約されており、設計 E では
その 1 箇所すら変更不要だった。既存テストの期待値は 1 つも動いていない。現存する 8c の実測成果物は
無く、本 wave は certified 選択・レポート・台帳の値を 1 つも変えない。

**T-1352 との重なりを起動後に発見した。** 本 wave が実装した validator は [T-1352] の項目本文が
明示的に含む「数値欄の型・有限性・符号・単位・向きを検査する validator を production 経路へ置く」に
一致する。新規 T は作らず [T-1352] の部分完了として記録する。残件は judge・3 表・完全 block の
復元・反復数の exact 一致・条件 7 の機械検査化であり、これらは別 wave の scope に残る。

## 次の一手差分

### 更新

- [T-1352] **P1・部分実装済み ([T-1336] の実装面)**: 反復単位の対比とその分散を計算する
  judge と、順位事実表・公式性能表・独立した選択評価表の 3 表生成を実装する。manifest の反復添字と
  observations の schedule 添字から完全 block を復元し、登録した反復数との exact 一致を検査する。
  **数値欄の型・有限性・符号・単位・向きを検査する validator は本 wave で production 経路へ置いた**
  (`_SECTION5_VALUE_VALIDATORS`、生き doc の不変検査と positive control 付き)。残件は judge と 3 表、
  完全 block の復元、反復数の exact 一致、および条件 7 の機械検査化である。最終判定層の現用実装は
  旧条件 3 と scale gate を使い続けているため、その撤去も同 wave の scope に入る。
  base: d7d46332b6fe35eecbb4f354d86bb6079b7d67f25eb3f0e989b474ea9ea20634

### 新規

- {{T:s8c-section5-violation-effective-wiring}} **P1・ユーザー裁定待ち**: §5 の値制約違反を
  判定器の内部で `effective` を偽へ倒す形にするかを裁定する。倒すなら (a) 凍結本文
  「欄ごとの型・単位・範囲の検証は本手続きの対象外である」の改訂、(b) `DECIDER_VERSION` の
  v4 bump、(c) 新世代 record の発行、(d) その record が引く D 番号の事前確保が同時に要る。
  文書自身の設計は条件 7 経由で倒す構造であり、その道を採るなら judge・3 表・完全 block を
  含む [T-1352] と一体で裁定するのが自然である。現状は違反値があっても 12 条件が充足を
  返さないため発効しない。
