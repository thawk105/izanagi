---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-prov-incremental-audit
title: provenance 全史監査で検証済み prefix を再利用し、per-commit 監査を取り込み差分へ限った (コード + docs、branch worktree-dev-wave-prov-incremental-audit、変異 matrix = baseline PASSED・12/12 KILLED・期待 node 完全一致)
seq: 1
---

## 本文

- ユーザー依頼は「provenance 全史監査を差分監査にして、リポジトリ成長に比例するコストを構造的に
  断つ。D908 の条件 (取り込み差分だけを対象とする独立監査を先に設計し、被覆が現行と等価であることを
  示してから置き換える) を満たす。祖先でない / checker の bytes が違う / 受領証が読めない・壊れて
  いるときは全史へ fallback し fail-open にしない。受領証を書く主体と検査する主体が同じである以上、
  改竄への完全な防壁にはならない (D387 と同型の限界) ことは主張せず明記する」。
- **段 1 の実測が依頼の前提を裏づけた。** 監査対象は 10,104 commit で F365 記録時点 (3,727 件) の
  2.7 倍。load 187 の login node で `_audit_history` 本体が 559.572 秒を要し、D254 が定める land の
  480 秒予算を超えた。ただし同じコードが load 124 では 19〜21 ms/commit で、**予算を跨ぐかは混雑
  次第**である。単調に増えるのは履歴長の項だけであり、本 wave が断ったのはそこ。
- **親が段 1 brief に書いた等価性の骨子は段 2 で崩れた。** 「checker の bytes が同じなら prefix の
  判定も同じ」は成立しない。git の alias 設定だけで trailer の解釈が変わる反例があり、既存テスト
  `test_legacy_ai_parser_keeps_repo_cwd_alias_and_default_divider` がその挙動を現契約として固定して
  いる。束縛対象を checker bytes から 13 項目へ広げて塞いだ ({{D:provenance-incremental-audit}})。
- **段 3 の 2 レンズが real 所見を 8 件出し、2 件を裁定パッケージへ送った。** とくに
  `merge-history-provenance` は `git merge --no-ff --no-commit` の直後・`git commit` の前に走るため、
  監査 HEAD は claim 前のままで、取り込んだ main の commit を選択集合に含めない。F365 の説明文と
  実装が食い違う。checker 単独では閉じないので別 scope とした。裏返しの含意として、この呼び手は
  差分 0 件になり、D908 が「削るな」と述べた冗長は削らずに費用だけ消える。
- **段 4 の親の裁定が 2 箇所誤っており、段 6 のレビューが訂正させた。**
  (1) 束縛の限定列挙から `.gitattributes` を落としたのは誤り。属性は外部 driver ではなく普通の
  repo file で、変更すると過去 merge の combined diff が空から非空へ変わり、prefix の判定が緑から
  赤へ動く。**受領証を偽造せず、通常の commit 追加だけで全史の赤を差分の緑にできた。** レンズが
  実在 merge `a5bbdbbfba54b3a1757155e5524ceb561ec7ee31` で出力 0 bytes → 114 bytes の変化を実測した。
  (2) 「区画内で受領証が積み上がる」と書いたが、実装は環境 digest だけで保存先を決めており
  `os.replace` が上書きしていた。どちらも erratum として裁定へ追記し fix で閉じた。
- **fix は 7 巡になった。内訳は出所が違う。** 1〜3 巡目はレビュー由来 (属性束縛の欠落 → 属性の出所の
  漏れ → symlink 同一視と、2 巡目 fix が作った作業ツリー全走査の費用の穴)。**4 巡目は親の実測由来**、
  5 巡目は親の再裁定、6〜7 巡目は**変異走行が暴いた被覆の穴**である。
- **4 巡目の回帰はレビュー 4 本が 1 件も検出していない。** fix3 後に cold/warm を測り直したところ、
  差分 971 commit の warm が 40.326 秒で全史 (36.173 秒) と変わらなかった。束縛を項目ごとに
  突き合わせると食い違いは `attributes` 1 項目だけで、その範囲の `.gitattributes` 変更は 0 件。
  属性 fingerprint が**監査 tip の tree**に依存しており、属性が変わらなくても tip が違えば不一致に
  なっていた。git が tree-to-tree diff で読むのは作業ツリー / index / info / global / system であって
  監査 tip の tree ではない。**静的には正しく、実 repo の実データで測って初めて出る型**で、
  差分監査の目的そのものが壊れていた。
- **5 巡目は親が期待値を再裁定した。** fix3 が本 wave で足した
  `test_attribute_candidate_directories_cover_git_paths[tip-only]` が、index から消えた directory の
  属性被覆を要求していた。git 自身が読まない入力であり、基底の期待値ではないので case を外した。
- **変異は 12 件を事前登録し、probe で観測 node を集めてから本走した。**
  **12/12 KILLED・期待 node 完全一致・baseline PASSED。** probe で 2 件が生存し、どちらも本物だった。
  (a) `git config --list` を空にする変異が生存 = **cold と warm の間で git config を変えて fallback を
  要求するテストが 1 件も無かった**。config を束縛した理由そのものが守られていなかったので
  `test_git_config_change_falls_back` を足した。
  (b) 「失敗監査は受領証を publish しない」は 3 層で守られており単層変異では暴けない (F28 型)。
  両層変異に再照準しても生存したが、原因は実装ではなく assertion の狭さで、
  `test_failure_never_publishes_receipt` が **1 つの受領証 file の bytes しか見ていなかった**。
  HEAD が変われば別名で publish されるので素通りする。directory 全 entry の照合へ強めて KILLED。
- **性能の実測 (load 約 9〜10、worker 32、10,257 commit、cold と warm を連続実行した同時刻の対照):**
  差分 1 件で 53.260 → 1.105 秒、152 件で 40.994 → 1.259 秒、971 件で 36.815 → 4.754 秒。
  warm の増分は 4.24 ms/commit で cold の 4.08 ms/commit と一致する。**差分ぶんだけ比例し、
  履歴長には比例しない。**
- **主張しないこと。** 総費用の履歴長非依存は達成していない (全選択集合の列挙、祖先 bitset の構築、
  append-only 検査は残る)。改修後に land が 480 秒へ収まることは未実測。受入の claim 前監査は
  新しい wave HEAD に祖先の受領証が無いので cold のままである。受領証は同一 OS user による改竄の
  防壁ではない。淘汰順序には残余があり、別枝の publish 時に着地済み受領証が消えうる (費用だけの
  問題で誤った受理は作らない)。
- 工数: codex 子 13 本 (plan 1、consult 2、author 1、review 2、focus 2、fix 5)。

## 次の一手差分

### 新規

- {{T:merge-history-audit-position}} **P1・裁定待ち**: `merge-history-provenance` の監査位置が
  merge commit 作成前にあり、取り込んだ main の commit を選択集合に含めない。F365 の説明文と実装が
  食い違う。位置を動かすと abort / cleanup 契約も変わるため checker 単独では閉じない。
- {{T:audit-environment-alignment}} **P2・裁定待ち**: 受入と land で checker の実行環境が違うため
  受領証が跨がらない。揃えれば preclaim も warm になるが、環境は trailer の解釈に効きうるため
  受理集合を変える変更である。
- {{T:cold-audit-venue}} **P2**: cold / fallback が 480 秒を超える場合の実行場所。admission は
  バイト予算だけを見て CPU 時間を入力にしないため、混雑した login に留まる (D1996 が既に記録)。
- {{T:receipt-retention-landed-tips}} **P3**: 受領証の淘汰が、別枝の publish 時に着地済み tip の
  受領証を非祖先として捨てうる。誤った受理は作らないが warm 連鎖が切れる。
