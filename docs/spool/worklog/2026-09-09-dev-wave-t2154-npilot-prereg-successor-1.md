---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2154-npilot-prereg-successor
seq: 1
title: [T-2154] n-pilot driver の後継事前登録を発行して測定条件の関門を配線した — 凍結解除ゼロ、関門の live 被覆は 12 cell 中 8 cell と正直に記録した (コード + テスト + 事前登録成果物、branch worktree-dev-wave-t2154-npilot-prereg-successor、変異 6/6 KILLED・期待 node 完全一致)
---

## 本文

- D1461 の実装。繰延べ台帳に残っていた最後の「事前登録が driver digest を束縛している」member を、
  凍結解除ではなく後継の事前登録を発行して配線した。凍結済み 4 file は 1 byte も触っていない。
- **段 3 の敵対相談は 2 本とも NO-GO を出した。** レンズ B は段 2 プランが後継 JSON へ書き写そうとした
  `contract_sha256` が **63 桁** (真値は 64 桁) であることを見つけた。そのままなら後継は読み込めず
  配線全体が無効になる。親は値を訂正するのではなく、**書き写しを機構から外した** —
  後継は先行の document を読み込んで `source.commit` と `source.driver_sha256` の 2 key だけを
  上書きして生成し、全 field の再帰比較で他が動いていないことを確認する。
  さらに「後継は 2 key を除いて先行と一致する」をテストで固定した。これは同時に
  「後継関係が exact schema に表現できない」という指摘への答えでもある — 継承を schema の
  新 field ではなくテスト側の関係として機械検査する形にした。
- **親が実測して brief を 2 か所訂正した。** (a)「`injected-*` sink の被覆経路は returned-evidence
  だけ」は一般化しすぎで、正しくは「macro の字面を 1 つも持たないこの sink では」である。
  (b)「r33 の bytes を pin する consumer は 2 つ」は不正確で、driver 側の照合は渡された任意の
  protocol に効く汎用 consumer である。**r33 の bytes を pin しているのはテスト 1 本だけ**だった。
  この訂正は本 wave に不利な向きである — 錨が 1 本しかないからこそ、その書き換え方が要だった。
- **先行の事前登録が記録している commit はこの repo に存在しない** (`git cat-file -e` が非 0、
  到達可能 commit 9591)。この欄は記録専用で実行時に照合されないため誰も踏んでいなかった。
  帰結として先行の driver digest を歴史 blob から再導出する経路は無く、成果物側の sha は
  literal 定数として持つしかない。後継が同じ型を再生産しないよう、記録した commit の実在・
  HEAD 祖先性・その時点の driver blob との一致をテストで固定した ({{D:successor-prereg-commit-binding}})。
- **配線の実効範囲を丸めずに記録した。** 実 12 cell のうち gated macro を持つのは 8 cell
  (BACKOFF_FIXED 2、BACKOFF_TRIGGER_GATING 4、SORT_VARIANT 2)。そのうち実行側の意味まで確立するのは
  `BACKOFF_FIXED` の 2 cell だけで、残り 6 cell の意味の節は `unestablished` のまま admitted になる
  (D1198 の設計どおり。意味 witness は別項の backlog)。gated macro を持たない 4 cell では期待 digest が
  空集合になるが、型検査と digest 等値検査は空集合の早期 return より前に走る。
  閉包検査が 37 macro 全件を被覆済みと数えるのは動的被覆の規則によるもので、
  **「37 macro を守った」とは書かない。**
- **変異が閉包検査の盲点を実測で暴いた。** 例外を握り潰す変異 (m04) では負例テストだけが赤になり、
  閉包検査は緑のままだった。閉包検査の injected 特殊経路が call の名前 suffix と第 1 引数しか
  見ていないという段 3 の指摘が、議論ではなく測定で裏付けられた ({{F:closure-injected-path-blind-to-swallowed-rejection}})。
- **変異の初回は期待 node 集合が不完全で MISMATCH 4 件だった。** 期待した node は 6 件すべて
  発火しており、不一致はすべて「余分に赤くなった」側。余分の 1 つは後継事前登録が driver の
  現在 bytes を固定しているための冗長 gate で、driver をどう変異させても赤くなる。
  もう 1 つは親の登録漏れ (閉包の分類件数を固定する別テスト) だった。初回を probe として保存し、
  観測した完全集合で再登録して 2 巡目で 6/6 KILLED・期待 node 完全一致。
- 段 4 で scope 外と裁定した real 所見 2 件をユーザー裁定へ返す (下記「次の一手差分」の新規項)。
- 段 5 の初回投入は `--reasoning` を author 段へ渡して rc=2 で即死した (段別の argv 制約)。
  引数を外して再投入し、1 巡で完了した。

## 次の一手差分

### 完了

- [T-2154] 後継の事前登録を発行して driver digest 束縛の member を配線した。
  凍結解除は行っていない。残り 3 member は所有 wave のままで、繰延べ台帳には 7 entry が残る。
  remaining: none
  base: f5b54670c9c6cdc36d07ad17d8842c4fc13c5275e8076ecc36d275c792ca5135

### 新規

- {{T:build-identity-not-bound-to-condition-evidence}} **P2・新規・ユーザー裁定要**: 条件 evidence は
  「要求した測定条件が供給され実効化したか」しか言わず、「その条件で建った binary か」を言わない。
  注入された build 関数が正しい record を運びながら別の binary を返す経路は、この関門では閉じない。
  注入 seam を持つ driver 全体に共通する性質で、配線前から存在する。閉じるには条件 evidence を
  binary 同一性へ束縛する新しい関門が要るため、本 wave では scope 外とした。
- {{T:closure-injected-coverage-is-positional-only}} **P2・新規・ユーザー裁定要**: 閉包検査の
  `injected-*` 特殊経路は、sink の直後に「名前の suffix が一致し第 1 引数が sink の代入名である
  call」が 1 つあれば patch macro 全件を被覆済みと数える。import の真正性・shadow・支配関係・
  例外の握り潰しを検査しない。本 wave の変異 m04 が実測で示した
  ({{F:closure-injected-path-blind-to-swallowed-rejection}})。族全体に効く共有機構の変更なので
  本 wave では scope 外とした。
