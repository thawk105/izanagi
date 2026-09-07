---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-backoff-static-ceiling
seq: 3
title: 静的 backoff の表現可能上限を 999 から 9999 マイクロ秒へ広げ、B-10 事前登録を v5 にした — 実測は次 wave (コード + テスト + docs、branch worktree-dev-wave-backoff-static-ceiling、変異 12/12 KILLED)
---

## 本文

- **測定は一切していない。** 本 wave が主張できるのは「静的値 1000〜9999 マイクロ秒を測れる状態に
  なった」までである。右側の打ち切りは 999 から 1000 へ 1 点動いただけで、**abort の抑制が
  飽和する領域には到達していない。** 一次資料は
  `output/insights/2026-09-08_backoff-static-ceiling/README.md`。
- 設計判断は {{D:static-backoff-ceiling}}、{{D:prereg-artifact-rebind}}、
  {{D:frozen-series-binding-must-be-literal}}。失敗は
  {{F:legacy-binding-derived-from-current-registration}} と
  {{F:object-identity-proxy-breaks-when-values-converge}}。
- **依頼の二択のうち (A) を採った。** 段 3 の敵対相談 2 本が独立に (A) を推し、(B) が正解になる
  条件も探したが、「999 超は物理的に無意味」「適応軸が同領域を覆う」「trigger gating が代替する」の
  3 反論はいずれも現物で成立しなかった。
- **親が現物で新事実を 1 件見つけ、裁定に組み込んだ。** B-10 の driver は「作業ツリーの patch の
  中身が事前登録 commit の blob と一致すること」を preflight で要求する。符号化を変えると
  新しい登録 commit なしには正式走行が必ず止まるので、事前登録の版立ては同一の変更単位に入れた。
  動かしたのは schema 版と 2 つのハッシュだけで、判定規則は 1 文字も変えていない。
- **段 3 の相談が段 2 のプランを 4 点で差し戻した。** 最大は「静的値に上限を置かない」案で、
  倍精度への丸めと符号なし 64 bit の桁あふれが現物で示された。上限 9999 はこの指摘を受けた裁定である。
- **段 6 の敵対レビュー 2 本が、独立に同じ最大欠陥を挙げた。** 完了済み 135 cell を読む adapter が
  期待束縛を現行の登録から組み立てており、v5 化した瞬間に旧行を拒否する状態だった。
  裁定した「v4 は v4 のまま残す」と両立しない。旧束縛を記録された v4 の値へ固定して閉じた。
- **親の焦点走が実装子の予告になかった赤を 1 件捕まえた。** 「要求した点と実際に測れた点は別の欄」を
  オブジェクト同一性で確かめる検査が、両者の値が一致したため落ちた。親は「誤っているのは実装では
  なく期待値」と裁定し、定数をわざと作り分けて通す直し方を禁じた。
- **子は 4 単位とも pytest を 1 件も走らせられなかった** (`qstat -Q` の認証失敗で rc=16)。
  親の焦点走が本 wave の最初の実測である。
- **段取りのつまずきを 1 件記録する。** author 段へ `--reasoning` を渡して rc=2 で即死した。
  effort は段 5 / 6 では docs 権威から導出されるので caller 指定できない。
- 変異は probe → 本走の 2 段。probe は全件 SURVIVED で登録して観測 node を集め、観測された完全
  集合を期待集合として本走した。**baseline PASSED、12/12 KILLED、MISMATCH 0、SURVIVED 0。**
  段 3 と段 6 が「変異しても全緑」と予測した 2 箇所は修正後には両方とも塞がっていた。
  C++ の復号式に触る 3 変異は意味判定器の一族 11〜12 node を巻き込むので、単独変異の独立証拠には
  数えない。

## 次の一手差分

### 新規

- {{T:backoff-static-tail-grid-above-1000}} **P1・ユーザー裁定待ち**: 静的 backoff の 1000 マイクロ秒
  超の測定格子を決める。どの点を、いくつ、どの停止基準 (abort 抑制の飽和判定) で測るか。
  追加点数と walltime 予算。符号化の上限は 9999 まで開いたので、あとは科学的設計と計算資源の裁定だけである。
  これを決めない限り右側の打ち切りは 1000 のままで、飽和域は測れない。
- {{T:nonnegative-backoff-meaning-declaration}} **P2・新規**: 非負 `BACKOFF_FIXED` に production の
  意味宣言を渡す。意味判定器は実在し、生値 3000 が実測 1000.0 になる正例も生値 1000 が 0 になる
  負例も張れるが、現行の driver は非負値に宣言を渡しておらず `unestablished` のまま admission される。
  F718 型を production 経路で捕まえられるのはこの結線が入ってからである。
