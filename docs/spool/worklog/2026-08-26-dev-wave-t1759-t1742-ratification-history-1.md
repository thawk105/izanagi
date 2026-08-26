---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1759-t1742-ratification-history
seq: 1
title: [T-1759] [T-1742] 批准台帳の履歴検査を DAG として読み直し、gate の終端を正直な未批准へ戻した (コード + テスト + docs、branch worktree-dev-wave-t1759-t1742-ratification-history、変異 matrix = baseline PASSED・10/10 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **gate の終端が変わったことを実測で確定した。** 修理前は台帳の中身と無関係に
  `ratification history is not a strict prefix extension` で落ち、批准行を足しても開かなかった。
  修理後は受理集合を正しく読み (`db511c3d...` の 1 件)、終端が
  `enforcement-source-closure-unratified` になる。**これが正しい終端であり、A-2 の批准が
  開くことではない。** 修理した module 自身が closure の 25 path の 1 つなので、
  この修理で closure digest は必ず動く (実測 `dabeada3...`)。[T-1647] の項目本文が書いていた
  「人間が批准行を 1 行足しても gate は開かない」という障壁は、検査側については解けた。
  残るのは D905 の執行主体の設計と、批准対象の exact digest の確定である。

- **ユーザーが束ねを指示し、codex の分割案を採らなかった。** codex は [T-1742] を
  「[T-1759] と同じ checker 面なので同時投入を避ける」として次点に回していたが、
  ユーザーは「同じ関数を触るからこそ束ねる。分けると 2 本目が必ず編集面で衝突する」と裁定した。
  実際に両者は `_committed_ratification_digests()` の同じ書き換えで閉じており、
  分けていれば 2 本目は同じ関数を再度書き換えることになった。束ねは正しかった。

- **親の provisional 規則は 3 か所で誤っており、実装前に段 2・3 が覆した。** (a) 「1 親で
  0 行増を許す」は、blob 同一で tree mode だけ変える commit を受理してしまう
  (現行規則は拒否する)。(b) 「blob bytes と行 tuple は 1 対 1」は偽だった
  ({{F:canonical-jsonl-splitlines}})。(c) 「導入 commit の一意性」を課さないと、
  独立した台帳導入 2 件を合流させて未批准 digest を入れられる。
  いずれも親が repo 外の使い捨て probe で裏取りしてから裁定へ反映した。

- **合流で全親の行順を同時に保存させる案は、解の存在しない履歴を作る。**
  `[a,b]` と `[b,a]` を親に持つ合流には、重複行を許さない限り共通の supersequence が無い。
  octopus では循環も作れる。行順は受理集合の値に入らないため、合流は集合の一致だけを求め、
  順序保存は実親がちょうど 1 つのときだけに限定した ({{D:ratification-history-dag-append}})。

- **末尾追記の強制は正しい cherry-pick と rebase を偽赤にする。** 部分列へ緩めても
  置換・欠落・並べ替え・複数行追加はすべて拒否のまま残ることを、既存 12 テストが
  1 件も変わらずに緑であることで確かめた。

- **scope 外と裁定して実装しなかった real 所見が 4 件ある。** (1) この gate は新規 lock 作成
  経路にしか届かず、artifact 受入と dispatch には届いていない。(2) 撤回 (revocation) の
  意味づけが未裁定で、既定は「批准は永久」であり行を落とす revert は拒否のままである。
  (3) shallow と graft の存在確認は check-then-use であり、検査中に履歴境界を書き換える
  攻撃には対応していない。(4) 合流が示すのは「親に行があったこと」だけで、
  各追記が人間批准であることは示さない — これは D526 が既に定めた線であり、
  認証は D905 の執行主体が担う。(1) と (2) は裁定パッケージとしてユーザーへ返す。

- **性能の must-fix は実測で棄却した。** レンズ B は「全世代の行 tuple 保持と
  `6+D+B` の process 数が二次・三次量になる」を must-fix としたが、D (台帳を持つ commit に
  現れる異なる `hooks` tree 数) の上界は全史 6469 commit にわたって 44 であり、
  B は批准回数で現在 1 である。実 main の実測は 0.436 秒・git 呼出し 9 回 (= 6+2+1) で
  式と一致した。1 process あたり 10 秒の timeout とは桁が違う。
  三次量の原因だった `_load_rows` の list 重複検査だけ set 化した。

- **tree mode の allowlist は確定契約より強いまま残した。** 段 4 は「entry が blob である
  こと」だけを求めたが、実装は `100644` / `100755` の 2 値に限る。symlink の object type は
  blob なので、mode の allowlist が実質的な type 検査になる。git が通常経路で他の
  regular file mode を書くことはなく、実 main は通る。契約側を
  {{D:ratification-history-environment-guards}} で明記して揃えた。

- **親の作法違反が 3 件あった。** (a) 段 6 の review 子へ `--reasoning` を渡し、
  rc=2 で 2 本とも即死させた (DW-C01 に明記済みの制約)。名前を変えて再投入し回復した。
  (b) 変異走行中に同じ作業木へ spool fragment 2 件を置いた (DW-M05 違反、F383 と同型)。
  走行末尾より前に退避したが、初回 probe は `shared_snapshot_matches=false` で無効化された。
  (c) 段 2 の待ち手へ `--receipt-file` として codex の受領証 path をそのまま渡し、
  plan 子の受領証を上書きして工数記録を失った。

- **子の工数 (receipt 実測、schema v4、全件 `accepted`)。** 段 2 plan = 受領証を親が
  上書きしたため欠測。段 3 レンズ A (sol) = 827.8 秒 / 6 call / 215,115 token。
  段 3 レンズ B (luna) = 766.8 秒 / 19 call / 1,259,365 token。
  段 5 実装 = 1339.5 秒 / 33 call / 3,101,022 token。
  段 6 レビュー A = 601.7 秒 / 12 call / 560,767 token。
  段 6 レビュー B = 627.6 秒 / 8 call / 379,515 token。
  段 6 fix = 585.7 秒 / 15 call / 880,520 token。
  段 6 焦点再レビュー = 362.6 秒 / 7 call / 344,388 token。

## 次の一手差分

### 完了

- [T-1759] 批准台帳の履歴検査が merge commit を台帳の改版と数える件を直した。
  到達可能 DAG を自前で列挙する形へ置き換え、実 main で検査が通ることと、
  終端が `enforcement-source-closure-unratified` になることを実測した。
  remaining: none
  base: 6976db46e274e377a65b94cea871b2d0725e585422b4f90d9c172492c222a5cb

- [T-1742] 全史検査を並行批准と shallow clone の両方向で閉じた。
  分岐した 2 branch がそれぞれ 1 行足して合流する履歴を受理し、行の欠落・置換・
  並べ替え・複数行追加は拒否のまま残した。shallow と実効 graft は fail-closed で拒否する。
  remaining: none
  base: a605fbe067bf319ecd3e2464ece5bf57a9a6fc582ce95d9e42ba50495a9ccb07

### 更新

- [T-1647] **P1・裁定待ちでなく AI 側の作業待ち**: A-2 の 4-cell certification 実走。
  コストは解消済み (1 反復 695.95 秒、5 反復で約 58 分、4 cell が 6 時間に収まる)。
  **台帳の履歴検査の障壁は解けた** — 検査は実 main で通り、終端は
  `enforcement-source-closure-unratified` という正直な理由になった。
  残るのは D905 の執行機構と、批准対象の exact digest の確定である。
  検査を直した module 自身が closure の member であるため、closure digest は
  この修理で動いた。批准対象は執行機構が着地した時点の値で確定する。
  base: 3389f4e6eba29a24a101e225597757e363483e513d44e07ab0716360cd51b265

### 新規

- {{T:ratification-gate-reach}} **P1・新規**: 批准 gate の射程を artifact 受入と dispatch へ
  広げるかを裁定する。現行の `require_ratified_closure()` は新規 lock 作成経路
  (`ident.ensure_campaign_identity()`) からしか呼ばれず、既存 lock を読む受入経路は
  記録 commit blob と記録 digest の一致しか見ない。正しい blob map を持つ未批准 lock が
  受入側を通りうる。D906 の偽造不能な受領証が着地すればそちらへ寄せられる。

- {{T:ratification-revocation}} **P2・新規**: 批准の撤回 (revocation) の意味づけを裁定する。
  現行規則は行を落とす revert を拒否する。批准が永久ならこれは正しい拒否だが、
  人間による撤回を正当操作とするなら偽赤である。撤回を許すなら行削除ではなく
  対象 digest と人間権限を束縛する tombstone schema が要る。
