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
- **段 8 の改善候補 1 件は `docs/dev-wave/**` の L1.5 予算に入らないため編集せず返した。**
  是正案を入れると L1.5 が **9667 bytes / 予算 9566 bytes = 101 bytes 超過**する
  (`DW-O01` 単節は 933 / 1000 bytes で通る)。予算値を上げる変更は自己改善に含めない規律であり、
  dev-wave 系への外出しは D94 で却下済みなので、編集を戻して `check_docs` 違反なしへ復帰させた。
  land 1 が S9 (a) で起票した **[T-789] (docs 予算の独立審査)** の 4 件目の実例として RP-5 で返す。
- **受入全走 rc=0 — 8629 passed / 20 skipped / 563.80 秒** (request `902565.nqsv`、
  tested tip = `5c68285e` = 待ち手が lease 内で main `67760fdb` を取り込んだ木)。
  **lease の取得に 90 分以上を要した** (他 wave が保持、`--poll-seconds 30`)。待ち手は
  `--max-wait-seconds 5400` で先に上限へ達したが producer は生存継続しており、待ち手だけを
  張り直して完走させた。本 session は land しないため、受入成功後に親が `release` した。
- **段 8 の記録追記は受入 tip より後の commit である** (受入は `5c68285e` で走り、本追記は
  その後に置いた)。本 session は land しないため tip 束縛の問題は起きないが、
  **最終 session は記録 commit を含む最終 tip で受入を走らせること**。
- 逐語 = `output/insights/2026-08-11_t139-manifest-land2/`。
  ユーザー裁定パッケージ (RP-1〜RP-5) は同 directory の `package.md`。

## 次の一手差分

### 更新

- [T-139] **P1・land 2 は session 1〜2 完了 (foundation-only)。次はユーザー裁定 Q1〜Q4 待ち**:
  branch `worktree-dev-wave-t139-manifest-w2` に、session 1 の erratum v2 対応 (2 operation、
  erratum_id 別 exact-key grammar、合成経路の承認 membership 検査)、`BlobRef` の digest 比較
  迂回封鎖、D282 承認 payload の parser (`approval_payload.py`) と、session 2 の
  **Git trust root 部分集合** (確定裁定 RP-2 (a): `PATH` 非継承・固定絶対 path 起動・
  commit-graph / fsmonitor / pager 無効・alternates / promisor / partial clone 拒否) が入った。
  **session 2 の実測: 焦点 4 file 110 passed、変異 8/8 一致 (MISMATCH 0)。land していない。**
  **ユーザー裁定 RP-1 (a) が求めた 7 件 (承認 manifest 実体 / `resolve_effective_preregistration` /
  `PreregBinding` / 受領証 writer / 固定 semantic validator / conformance vectors /
  raw snapshot API) は、段 2 と段 3 の 2 レンズが独立に NO-GO とし、親が段 4 で
  「本 session では実装しない」と裁定した。** 理由は 3 つ —
  (i) 承認済み文書だけでは受理述語が一意に決まらない箇所が 4 件ある
  (§6.3 の `CMakeCache.txt` raw pointer 不在、§4.13 の intent 母集合不在、
  §6.1 の peer receipt 同定契約不在、§6.8 の transcript byte grammar 不在)。
  `record-items-v2.md` と `receipt-schema-v1.json` は D282 で exact bytes 承認済みで変更できない。
  (ii) **D291 の land で承認根が `F_r` と `F_p` の 2 本になり manifest 表現が未裁定になった**
  (`addendum_b` の承認は D291 側にしか無い)。
  (iii) **D292 により、RP-4 (a) の条件が揃っても別の canonical decision なしには pilot は開かない。**
  D292 が定めたのは解除権限と手続きだけで、解除条件の中身は定めていない。
  なお **RP-4 (a) の「3 文書の凍結承認」は成立していない** — D291 が承認したのは 2 role ちょうどで、
  追補 P の blob は明示的に未承認である。
  `a13` consumer / submit 系 / PBS preflight / driver / collector / correctness 還流 /
  certified 側 consumer / pilot 投入は**未実装**で、D264 の非 export も維持している。
  **`orchestrator/preregistration/` を呼ぶ非 test caller は repo 全体で 0 件**であり、
  本 session が動かしたのは基盤層の受理集合であって production の受理集合ではない。
  裁定 4 問 = (Q1) 入力欠落 4 件をどう閉じるか (親推奨 = 1 本の canonical decision) /
  (Q2) manifest 表現 (親推奨 = role 別 namespaced projection) /
  (Q3) RP-4 (a) の解禁条件をどう記録するか (親推奨 = 条件候補として保持し別 decision で解除) /
  (Q4) 次 session の編成 (親推奨 = Q1・Q2 確定後に RP-1 (a) を再実行)。
  逐語 = `output/insights/2026-08-11_t139-manifest-land2/` と
  `output/insights/2026-08-11_t139-manifest-land2-s2/`
  base: 17290cdd8d0c915a1d8561d030280223120ce4638f3b042c999f0c76cb7f8463
