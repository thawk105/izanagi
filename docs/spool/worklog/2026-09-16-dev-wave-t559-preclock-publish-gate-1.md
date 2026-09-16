---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t559-preclock-publish-gate
seq: 1
title: [T-559] 凍結 pre profile と post observed clock の照合を publish 前に課した — 外側 post probe の窓は残ると明記 (コード + docs、branch worktree-dev-wave-t559-preclock-publish-gate、変異 matrix = baseline PASSED・9/9 KILLED・期待 node 完全一致)
---

## 本文

- **ユーザー裁定 (2026-08-25 /rulings 全件、推奨どおり) の択 (a) をそのまま実装した。** publish
  transaction 自体を後ろへ移す案は裁定が採らないと定めており、本 wave も採っていない。設計判断は
  {{D:pre-post-clock-publish-gate}}。
- **この穴は本 wave が作ったものではなく、D191 自身の「射程」節が逐語で記録していたものである。**
  benchmark 前後に 2 つある既存の clock gate は、どちらも凍結 pre profile の自分自身を見る。
  静的 profile の比較は `effective_clock` を除外するため、benchmark 後に取り直したクロックは
  どの gate にも入らなかった。
- **段 3 の敵対レンズが親の実測の一般化を止めた。** 親は実 attempt 7 件の pre/post を照合し、
  直近 6 件が乖離 0.000% であることから「新 gate は実環境で通る」と書いたが、この post は
  **外側 wrapper が CLI 終了後に撮ったもの**で、新 gate が読む CLI 内の post とは観測時点が違う。
  到達可能性の証拠にはなるが通過実績ではない。F108 の 23 は標本列数、こちらの 7 は attempt 数で
  単位が違い、包含関係も不明である。次の取得 job が benchmark 後に落ちる確率は推定できない。
  worklog に書ける形へ限定した。
- **反実仮想は正直に 0 件だった。** 既存の自己照合が通って新 gate だけが落ちる attempt は、
  実データ 7 件の中に 1 件も無い。唯一落ちる 0:867876 は既存の早期自己照合でも落ちる。
  新 gate の価値は歴史的実例ではなく、benchmark 後の状態を見る gate が 1 つも無いという
  構造的欠落を塞ぐことにある、と記録した。
- **段 6 の敵対レビュー 2 本は must-fix ゼロで、fix 子を起動していない。** 代わりに変異で裏取りした
  (`DW-M02`)。ただしレビューは**事前登録した変異定義 2 件の帰属不成立**を先に摘出した。
  M02 (dict 丸ごと逆転) は shape 違反で常時拒否になり、M04 (expected の全参照を static pre へ) は
  `tolerance_pct` が無く `KeyError` になる。どちらも「意図とは別の理由」で赤になるため、
  **標本列だけを入れ替える形へ変異定義を直してから本走した。**
- **変異は `DW-M08` の probe 手順を使った。** 初回は期待 node を確定できないので全 9 件を
  SURVIVED 期待で登録して観測 node を集め (全件 MISMATCH)、観測集合を完全集合として再登録・再走した。
  初回 spec と結果は erratum として insight に残した。
- 段 3 レンズ A の 2 所見が実装を変えた。(a) sidecar に**照合時 policy 値**を足した — benchmark 中に
  policy 定数が変わると帯内でも canonical は False を返すため、この値が無いと sidecar だけでは
  判定を再現できない。(b) canonical への監視 wrapper に「expected が凍結 dynamic pre、observed が
  post profile と値一致」の assert を課した — 標本列の逆転を撃つため。
- **「canonical を呼んだこと」と「戻り値が受理判断を支配すること」は別**という段 6 の指摘に対し、
  policy 変更負例 (帯内だが policy 不一致) を足して後者を撃てるようにした。診断の `band_pass` は
  True、canonical の戻り値は False になるので、戻り値を使わない実装ではこの負例の reason が出ない。
  変異 M05・M07 がこの経路で撃たれている。
- **段 8 の自己改善候補 2 件のうち、1 件は台帳へ送り、1 件は予算の壁で当てられなかった。**
  1 件目は {{F:submodule-init-false-ok-before-worktree-add-completes}} として登録した。
  2 件目は「隔離 session は他 worktree へ `git -C` も `cd` も不可なので、`DW-S05-A` が書く
  `git add -A`→`git diff --cached` の取出し手順を親が実行できない」という記載と実挙動の食い違いで、
  実測で確認した (両形とも guard が拒否する)。回避は `diff -u` で patch を作って自分の worktree で
  `git apply` すること。`DW-S05-A` へ 70 bytes 追記すると L1.5 層予算 (9696 bytes) を 70 bytes
  超過し、`DW-C01` へ 54 bytes 追記すると単節予算 (1000 bytes) 超過に加えて節の exact 契約と
  不一致になる。**安全義務を削って枠を作ることはせず、どちらも差し戻した。** 上限引き上げが要る
  ため報告に留める。
- **受入 attempt 1 は非帰属赤で、attempt 2 を投げ直した。** 40 件すべてが
  `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` の **setup error** で、本文は
  `subprocess.TimeoutExpired` — fixture が呼ぶ `git ls-files --others` と
  `git status --porcelain=v1` が 30 秒で切れていた。assertion ではなく、本 wave の差分
  (較正 CLI のクロック照合) からは到達しない。同 file の単独再走は **51 passed / rc=0** で
  非再現だった (`DW-O18` の「差分到達不能は単独再走」)。投入時の load average は 14.99 と低く、
  効いていたのは**同時に走っている受入の本数**で、実測 6 本だった。3 本以下へ空くのを待ってから
  attempt 2 を投げた。hold 登録はしていない。
- 逐語・変異台帳・実測表は `output/insights/2026-09-16/t559-preclock-publish-gate/`。

## 次の一手差分

### 完了

- [T-559] 凍結 pre profile と post observed clock の canonical 比較を publish の前に課した。
  判定は canonical 述語の戻り値だけで行い、失敗時は既存 reason 列の末尾へ足して publish より前に
  止める。publish transaction の位置・順序と publish 後の bytes 再読は動かしていない。
  裁定が採らないと定めた「publish を後ろへ移す」案は採っていない。残る窓 (外側 wrapper の
  post attestation、成功時の証拠) は別項として新規登録した。
  remaining: none
  base: a6a008ee5b175f6c401f16b8d554a3bfc72332787ec277e94ff520b4bcde576c

### 新規

- {{T:preclock-success-evidence}} **P3・新規・ユーザー裁定待ち**: 成功した pre→post 照合の証拠が
  成果物に残らない。診断 sidecar は失敗時だけ書くため、accepted な較正から「この照合を通った」ことを
  再計算できない。受理集合・published bytes・参照を変えないので {{D:pre-post-clock-publish-gate}} の
  must-fix にはしなかったが、段 6 の両レンズが real と判定した。成功時にも staging へ同形の
  receipt を書く案と、主張を「失敗時の再計算可能性」に限定したままにする案の択一。
- {{T:outer-post-attestation-evaluation}} **P3・新規・ユーザー裁定待ち**: 外側 job wrapper が CLI 終了後に
  撮る post attestation は、依然として canonical 述語を通らず publish を取り消さない。
  {{D:pre-post-clock-publish-gate}} が塞いだのは CLI 内で取得した post だけであり、
  [T-559] 原文が指す窓のうち CLI 外の部分は残る。wrapper 側で評価する案は publish 済み artifact の
  事後取り消しを伴うため、D191 が却下した「拒否時に published artifact を削除する」と衝突する。
  設計択一としてユーザーへ返す。
- {{T:dev-wave-doc-budget-for-isolated-patch-extraction}} **P3・新規・ユーザー裁定待ち**: 段 8 の
  自己改善候補 1 件が `docs/dev-wave/` の層予算に収まらない。隔離 session からの実装子成果の
  取出し手順 (`diff -u`→`git apply`) を `DW-S05-A` へ書くと L1.5 予算を 70 bytes 超え、
  `DW-C01` への追記は単節予算超過と節 exact 契約の不一致になる。予算のために既存の安全義務を
  削らない方針で差し戻した。上限引き上げか、既存文の意味等価な縮約かの択一。
