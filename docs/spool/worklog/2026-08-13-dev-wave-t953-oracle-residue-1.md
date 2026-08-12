---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t953-oracle-residue
seq: 1
title: SWO oracle の残余 5 件を閉じた — contract ID へ実装 bytes と走査範囲を束縛し、finding validator を exact schema にした (コード + docs、変異 12/12 KILLED、branch worktree-dev-wave-t953-oracle-residue)
---

## 本文

- **wave は 2 セッションに分かれた。** 前セッションが段 6 の fix 子を投入した直後に使用量上限で
  中断し、後継セッションが**走行中の子を引き継いだ**。子は生存していたので再投入せず、
  待ち手だけを張り直した (前セッションは投入と待ち手を対にできないまま落ちていた)。
- **段 1 の親の実測が 1 件誤っており、敵対レビュー 2 本が独立に是正した。** 親は
  「finding の `observations` を生成する箇所は 0 件」と brief に書いたが、実際は producer に
  3 箇所ある。原因は**完全性を要する grep を `head -20` で切ったこと**で、campaign 側の hit が
  truncate されていた。schema は誤った前提でなく実 producer の emit 形から作り直した。
  この near miss は {{F:brief-search-truncated}} として記録した。段 8 で `DW-S01` へ 1 文を
  統合しようとしたが、`docs/dev-wave/**` の L1 unique footprint が予算を 106 bytes 超えて
  `check_docs.py` が赤になったため取り消し、恒久対応は memory に置いた
  (**予算引き上げは自己改善の範囲外**)。L1 の残余は約 9 bytes しかなく、
  段 1 の実測規律をこれ以上 L1 へ足す余地は無い。
- **引き継がれた「既知赤 1 件を見込む」という申告は、実測で成り立たなくなっていた。**
  前セッションは main 由来の octopus merge による恒久赤を実測しており、handoff は受入結果に
  それを明記するよう指示していた。後継セッションが投入直前に測り直したところ、判定器は
  新旧どちらの main sha でも rc=0 を返し、`octopus-merge` の literal は repo から消えていた。
  main の `ff41d6c0` (履歴契約の n 親一般化) が既に直しており、その commit は本 wave の tip の
  祖先である。**申告を継承せず自分で測り直したので、受入結果に嘘の既知赤を書かずに済んだ。**
- **焦点再レビューは 2 巡した。** 1 巡目は NO-GO (partial 1 件)。第 1 巡の fix が
  「候補成果物の削除に失敗しただけで postflight を実行せず UNAVAILABLE を返す」早期 return を
  入れており、有効な REJECT を取りこぼしていた。レビュー子は「候補がその削除失敗を作る経路は
  確認できなかった」と正直に書いた。**親の独立評価**では、この時点で候補は compile に失敗した
  だけで**一度も実行されていない**ため候補由来の梃子は無く、規律 2 の穴ではない。ただし
  postflight が既に別 directory で走る以上、削除失敗は postflight を飛ばす理由にならないので、
  今 wave が自ら入れた過剰な保守化として 2 巡目の fix で戻した。2 巡目のレビューは GO。
- **refuted した所見が 1 件ある。** 段 3 レンズ A の BLOCKER 主張 (「(a) の再分類で再試行後の
  PASS が certified され得る」) は、UNAVAILABLE の retry 可能性が本 wave 以前からの既存契約で
  あり、再試行された候補も公理検査を通らねば certified されないため、規律 2 の穴ではなく
  証拠保持の問題と裁定した。証拠保持の部分だけ採用した。
- **変異 matrix は 12 件すべて KILLED、MISMATCH 0。** 期待赤 node は親が fix 後の最終 commit の
  実コードから導出した完全集合 (計 36 node) で、初回走行で全件一致した。負例 9 件は gate を
  1 つ無効化すると赤になること、正例 3 件は受理集合を過剰に縮めていないことを見る。
  contract digest を動かす 3 件 (M3/M4/M5) は、それぞれの直接検査に加えて contract literal の
  exact snapshot テストも赤になるため、期待 node に算入した。
- **oracle の限界表記は弱めていない。** 有限 corpus 上の反例発見器であって全入力に対する
  SWO の証明ではない、という記述は producer・runbook の両方で維持した。postflight についても
  「候補 compile の後に trusted control も落ちた」という**相関**であって候補から独立した環境判定
  ではない (quota / cgroup / host 状態は共有) と docstring に明記した。
- 段 3・段 6 のレビューが挙げた real 所見のうち 8 件は scope 外と裁定し、下の新規項目として
  ユーザーへ返す。いずれも受理集合・台帳意味論・consumer 層の択一を含み、本 wave の
  指示範囲では決められない。
- **受入全走 1 回目は 2 failed / 10,512 passed / 65 skipped (124.85 秒、Pegasus request
  908839.nqsv)。赤 2 件は本 wave の差分に帰属する。** node は
  `test_s8b_oracle_manifest.py::test_build_approved_valid_fixture_output_depends_only_on_spec_pin`
  と `::test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`、例外は
  `ReviewedSpecError: [invalid-reviewed-spec] generator_versions.materializer.sha256 が
  実 byte hash と不一致`。s8b の承認 spec が `materializer` として
  `orchestrator/campaign/s1_direct_comparison.py` の bytes を pin しており、項目 (d) が
  そのファイルを編集したため hash が動いた。golden が焼いていた `dc67d934...` は main 版の
  sha256 と完全一致し、現版は `a69422f8...` — フレークでも main 由来でもない。
  **これは F30 の五度目の再発** (編集面 source を pin している側を段 1 で数え落とす向き) で、
  段 1・段 3・段 6 のいずれも検出できず受入で初めて出た。golden literal 2 個の値だけを
  現ファイルへ揃えて閉じた (production 無変更、assert の削除・緩和なし、golden を
  production serializer の出力から再生成していない)。この記録を含む最終 tip で受入を再走する。
- 工数は Codex 12 本 (plan 1 / consult 2 / author 2 / review 2 / fix 3 / focus 2、すべて
  `gpt-5.6-sol`、evidence complete、rc=0)。model call 354、wall clock 合計 8,103 秒。

## 次の一手差分

### 完了

- [T-953] (a)〜(e) を実装した。(a) 候補 compile 失敗時に trusted control を事後にも走らせ、
  候補成果物を除去してから専用の別一時 directory で postflight する。除去に失敗しても
  postflight は飛ばさず、併発時は専用 detail code で証拠を残す。(b) contract ID を再構成し、
  公理判定 4 関数の実装 bytes と走査範囲の意味論定数を束縛した。(c) critic の finding validator を
  kind ごとの exact key 集合・閉じた reason_code 集合・producer 正準形の corpus_id・
  observations 要素 schema へ狭め、producer の存在しない protocol kind を拒否した。
  (d) S1 の oracle REJECT を session ledger へ耐久化した。(e) S6 の docstring を実体へ是正した。
  remaining: none
  base: 7855838c5245f8d4cf61f2ea23ef20a21bc8fe127d0670121cbe7633fa04c042

### 新規

- {{T:oracle-reject-terminal-status}} **P2・ユーザー裁定待ち**: oracle REJECT に終端 status を
  与えるか。現状の「記録して止める」では再開のたびに未終端 start が積まれる。`verifier-red` 相当に
  すると schedule が先へ進み certified 母集合が変わるため、単独裁定が要る。
- {{T:oracle-reject-tombstone}} **P2・ユーザー裁定待ち**: 再試行を止める REJECT tombstone を
  置くか。proposal / materialized hash で受理前に検査する案。台帳意味論の変更を伴う。
- {{T:critic-contract-id-exact}} **P2・ユーザー裁定待ち**: critic loader の contract ID 受理を
  現行世代の exact 一致へ狭めるか。現状は prefix だけで旧世代・偽形式も通る。旧世代 artifact の
  read-only 互換経路をどう分けるかが択一の中身。
- {{T:contract-id-overflow-fail-closed}} **P2・ユーザー裁定待ち**: critic が contract ID の
  長さ上限超過を例外なく空文字化し receipt も連鎖消失させる挙動を fail-closed へ倒すか。
  上限の引き上げは受理集合を広げるため単独裁定が要る (現行 ID は上限内で発火しない)。
- {{T:oracle-finding-schema-producer-boundary}} **P3・ユーザー裁定待ち**: oracle finding の
  exact schema を producer / WAL 境界へも展開するか。現状は critic の reader 側だけが硬い。
- {{T:oracle-evidence-into-materials}} **P3・ユーザー裁定待ち**: S1 report と critic digest が
  oracle の証拠 (finding / observations / postflight detail) を読むようにするか。
  現状は台帳に残るだけで材料レポートへ出ない。
- {{T:s1-ledger-nested-oracle-schema}} **P3・ユーザー裁定待ち**: S1 ledger の nested な oracle
  field を読み側で exact schema 検証するか。旧 ledger 互換と fail-closed 境界の択一を伴う。
- {{T:dq-reason-charset-limit}} **P3・ユーザー裁定待ち**: 外側の quarantine reason 文字列に
  文字集合制限を掛けるか。finding を invalid にしても外側 reason は描画されるため、
  規律 6 の運び屋が 1 経路残っている。
