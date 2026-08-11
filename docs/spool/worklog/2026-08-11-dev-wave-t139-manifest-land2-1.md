---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t139-manifest-land2
seq: 1
title: land 2 の基礎層を作った — erratum v2 対応・digest 迂回封鎖・D282 承認 payload parser (foundation-only、land しない、branch worktree-dev-wave-t139-manifest-w2)
---

## 本文

- **land 2 は複数 session に跨る (S6 (a))。本 session は land しない。** land 1 の fold commit
  `F_r` = `39d760985a5e37d20464c394760bf65596156566` の後、同一 branch を継承した第 1 session である。
- **本 session の状態は `foundation-only` である。`package.md` §S7 の #1〜#3 を「満たした」とは
  記録しない。** 段 3・段 6 の 4 レンズが独立に「resolver を書いても呼ぶ側が本 session の scope に
  無い以上、防壁は 1 度も発火しない」と判定した。承認済み `record-items-v2.md` §6.10 は
  **受領証 writer が支配点**であると定めており、writer は後続 session の scope である。
- **親が段 4 で確定した順序制約 (新事実):** 承認 manifest は **conformance vectors の digest を
  pin する義務がある** (`record-items-v2.md` §7)。vectors は §6 の cross-field 制約と §7.1 の
  20 制約に対応する試験資材で、固定 semantic validator と同じ session に属する。したがって
  **manifest 実体は validator と同じ session でなければ承認契約を満たせない。**
  これは「consumer 不在」とは独立の、承認文書由来の制約である。段 4 でこれを見つけたため、
  manifest と resolver を本 session の scope から外し、確定している基礎層 3 lane に絞った。
- **段 4 の変異事前登録 10 件のうち 7 件が実効 gate に当たっていなかった。**
  段 4 の時点では実装が存在せず、親は段 2 プランから変異位置を書いた。段 6 レビュー D が静的追跡で
  「単独 KILL を書けるのは 3 件だけ」と判定し、残りを mask / equivalent / テスト自身を弱めるだけ /
  受理集合を動かさない診断赤に分類した。段 6 の fix 子 3 本へ「その検査を消したとき赤くなる nodeid を
  名指しせよ」と要求して 9 件へ照準し直した。**実装が段 5 で生まれる wave では、段 4 の登録は暫定で
  あり段 6 での再導出を要する** ({{F:mutation-preregistration-before-implementation}})。
- **変異 1 巡目は期待 node の誤りで MISMATCH 3 件だった** (`mutation-ledger-round1-erratum.json`)。
  9 変異とも赤くなっており生存は 0 だったが、親が期待 node を fix 子の報告から書き写し、実測で
  完全集合を再導出しなかった。2 件は過少申告 (fix 子が自ら新設した node を報告に含めていなかった)、
  1 件は過剰申告 (`approved_blobs` の role 集合検査を消しても「重複 role」は**前段の duplicate key
  検査に先取りされて**赤くならない)。訂正版で **9/9 KILLED、期待 node 完全一致、rc=0**。
- **敵対レンズが実行で裏付けた実欠陥を 6 件閉じた。**最も重いのは
  **合成後 digest 比較が `str` subclass で迂回できたこと** (レビュー C の must-fix)。
  `blobref.py` を直した lane はこのファイルを所有せず、`erratum.py` を書いた lane は自分の担当所見で
  なかったため、**分割の副作用で同型欠陥が残った** ({{F:split-leaves-isomorphic-defect}})。
  次に重いのは **承認 payload の負例 14 件が基底例外を捕捉していたこと** (レビュー D の must-fix) —
  「拒否された」は見えるが「正しい理由で拒否された」を見ておらず、変異の帰属を証明できない。
  ほかに、`compose_core` が承認 membership を確認せず全 registered ID を適用していた
  (謳うだけで発火しない恒真な保証)、見出し境界が先頭空白 1〜3 の ATX 見出しを認識しなかった、
  `BlobRef` の構築後 subclass 再注入、wave 前にあった `old_text` bytes 束縛の負例が等価物なしで
  消えていた、の 4 件。
- **段 5 の実装子 3 本は 1 件もテストを走らせられなかった** (計算ノード投入が `EACCTAUTH` で拒否、
  login のメモリ枠も他 wave で逼迫)。3 本とも「実装済み・未実走」と正直に申告し、緑を騙らなかった。
  **親からは dispatch が通り実測できた。** 子の sandbox と親で dispatch の可否が異なる。
- **親の投入ミスで段 6 の敵対レビュー 2 本を空費した。** `--lane` は `--stage consult` でだけ
  指定できるという `dev_wave_codex.py` の制約を見落とし、両方とも argv error で即死した (成果物ゼロ)。
  `.done` は消さず新 artifact 名で再投入した。
- **親の provisional 裁定を 3 件撤回し、brief の事実誤り 2 件を訂正した。**
  (P1) A/B 2 lane 並列 → 所有面不足で不成立、(P2) Git を絶対 path で解決して実体 digest を受領証へ
  記録 → 順序が逆で記録先 field も承認済み schema に無い、(P3) leaf の fd 再利用で足りる →
  component walk 等が必要かつ consumer 不在で閉じない。事実誤りは「D282 の承認 blob は 6」
  (正は target core 1 + approved blobs 6 = **7 三つ組**) と「承認 blob path を pin する `*.py` は
  2 箇所」(当該 2 箇所は**草案** path の pin で、承認 v2 path の pin は **0 箇所**だった)。
- **land 前に直す必要がある残件:** 第 1 波の fragment
  `docs/spool/worklog/2026-08-10-dev-wave-t139-manifest-w1-1.md` の `base:` が stale で
  `spool_fold.py --dry-run` が `invalid` だった。同 fragment の `更新` 節は land 1 前の状態を
  書いており本 fragment に置き換わるため、構造として重複する `更新` 節を外した (本文は残した)。
  **後続 session と最終 session は、自分の `base:` も carry 解決後に再算出すること。**
- 逐語 = `output/insights/2026-08-11_t139-manifest-land2/`。
  ユーザー裁定パッケージ (RP-1〜RP-4) は同 directory の `package.md`。

## 次の一手差分

### 更新

- [T-139] **P1・land 2 の基礎層まで完了 (foundation-only)。次はユーザー裁定 RP-1〜RP-4 待ち**:
  branch `worktree-dev-wave-t139-manifest-w2` に erratum v2 対応 (2 operation、erratum_id 別
  exact-key grammar、合成経路の承認 membership 検査)、`BlobRef` の digest 比較迂回封鎖、
  D282 承認 payload の parser (`approval_payload.py`、機械可読の拒否理由つき) が入った。
  **焦点 3 file 86 passed / 0 failed、変異 9/9 KILLED (期待 node 完全一致)。land していない。**
  `resolve_effective_preregistration` / `PreregBinding` / 承認 manifest 実体 / 受領証 writer /
  固定 semantic validator / conformance vectors / `a13` consumer / submit 系 / certified 側
  consumer / pilot 投入は**未実装**で、D264 の非 export も維持している。
  **承認 manifest は conformance vectors の digest を pin する義務があるため、manifest 実体は
  semantic validator と同じ session でなければ承認契約を満たせない** (本 wave が確定した順序制約)。
  裁定 4 問 = (RP-1) resolver を呼ぶ側をどの session で作るか (親推奨 = manifest + resolver +
  受領証 writer + semantic validator + vectors を 1 session にまとめる。D234 署名を変えないこと、
  `alpha_reservation` を manifest へ再掲しないことを同束で問う) /
  (RP-2) Git・resolver の trust root policy (**本環境の `/usr/bin/git` は owner nobody** のため
  「root 所有必須」は環境ごと拒否する。親推奨 = `operational_boundary` の解釈として明文化し
  安価な部分集合だけ実装) / (RP-3) raw snapshot consumer の閉包時期 (親推奨 = RP-1 と同 session) /
  (RP-4) 公表 core `b03` と pilot の解除条件 (親推奨 = 3 文書の凍結承認 + fold を条件とし、
  §S7 #7 は [T-793] へ委譲)。
  **pilot 投入は依然不可** — 公表 core 段階 2 は land 済み (main `d6f2c836`) だが 3 文書とも
  `authority: none` で未発効であり、凍結承認はユーザー手番として返されている。
  逐語 = `output/insights/2026-08-11_t139-manifest-land2/`
  base: e345ae22475ca6421ead84cdea285081fb650b06ed4b87b0340014d3562f8fa7
