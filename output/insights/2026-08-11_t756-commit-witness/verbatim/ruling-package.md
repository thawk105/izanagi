# 裁定パッケージ — trace 形式 v2 の C++ 半分 (FN-2) は新 pin の人間承認を要する

```text
authority: dev-wave (背景 job) が [T-755] Q1 (a) の実装中に起票 (2026-08-11)
wave: dev-wave-t756-trace-v2 / branch worktree-dev-wave-t756-trace-v2
根拠: [T-755] Q1〜Q3 全問 (a) (dev-wave-jobs/dev-wave-s1-design-choice/ruling-package.md)
性質: 権限境界。本 wave は external/ccbench を 1 byte も変えていない (gitlink = d706650 のまま)
一次資料: 同 directory の brief.md / s2b-plan.md / s3-lens1.md / s3-lens2.md
並走ガード: (i) 計算ノード未使用、(ii) キュー投入なし、(iii) 裁定帯域は他パッケージ優先で可
```

## 0. 結論 — trace v2 は 2 つの半分に割れ、片方だけが AI の権限内にある

[T-756] の負債は独立した偽陰性 2 件である。**実装してみて、この 2 件は必要な権限が違うと判明した。**

| | 偽陰性 | 塞ぐ機構 | 権限 |
|---|---|---|---|
| **FN-1** | 末尾欠番 (txid 最大側の trx が丸ごと消えても欠番 0 と数える) | trace 外の**独立 witness** = CCBench 自身の `commit_counts_` と C 行数の突き合わせ | **AI の権限内。本 wave で実装する** |
| **FN-2** | trx 尾部欠落 (C 行だけ残り R/W 行が消える) | C 行に R/W 件数を持たせる = **trace 形式そのものの変更** | **権限外。本パッケージで返す** |

FN-1 の機構は当初案 (「C 行に R/W 件数 + txn 終端マーカー」) と違うが、**FN-1 に対しては当初案より
強い** — 終端マーカーは末尾切りだけを捕えるのに対し、witness は欠落位置に依らず、thread の trace
file が丸ごと消えた場合も捕える。裁定 Q1 は *wave の分割* についての裁定であり、機構は
2026-07-02 台帳のコメント由来なので、機構の差し替えは実装レベルの判断として本 wave で行った。

## 1. FN-2 が塞がれている理由 (実測、file:line)

FN-2 を塞ぐには `external/ccbench/include/trace.hh` の `emit_commit` と、その呼び出し側
(`cc/silo/transaction.cc:596`、`cc/si/transaction.cc:526` 付近) を変える必要がある。
D16 によりこれは submodule `izanagi-trace` 行きであり、**gitlink 前進を伴う。** そこに 4 つの壁がある。

1. **承認定数の追認禁止 (always-on gate)。** `orchestrator/campaign/s8b_approved.py:67` の
   `CCBENCH_FULL_SHA = "d706650…"` は承認定数で、`orchestrator/tests/test_s8b_approved.py:58`–`64`
   の `test_ccbench_full_sha_matches_real_gitlink` が**実 gitlink と完全一致**を要求する
   (コメント: 「submodule 前進の検出」)。`orchestrator/campaign/pin.py:28` の
   `CURRENT_PIN = "d706650"` も prefix 一致を二重に固定する。**AI がこの 2 定数を書き換えるのは
   「現在値の追認」であり、`s8b_floor_campaign.py:462`–`464` が名指しで禁じている形である。**
2. **push が人間手番。** `origin/izanagi-trace` は現在 d706650 であり、新 commit は local に
   しか存在しない。gitlink が origin に無い commit を指すと再現性が壊れる。
   push は AI が行わない (CLAUDE.md / Pegasus 運用)。
3. **`pin.CURRENT_PIN` を使う driver が 7 本ある。** `s1_verify_extime_calibration.py:56`、
   `axis_trigger_gating.py:27`、`s8a_trigger_coverage.py`、`s5_permutation_coverage.py:49`、
   `s6_sort_sweep.py:77`、`backoff_sweep.py:46`、`s3_lock_coverage.py:52`。pin を進めると
   これらが build する commit が変わる。
4. **diff-of-diffs は新 pin を baseline にしてしまう。**
   `source_digest.py:699`–`724` の `assert_trace_diff_matches_head` は
   「working tree の TRACE=1/0 差分 == pinned HEAD の TRACE=1/0 差分」を検査する。
   pin 自体が動くと baseline も一緒に動くので、**新 pin の trace-hook 変更そのものは検査されない。**
   前 wave の敵対レンズ 1 が blocker 認定した「旧 pin 対新 pin の TRACE=0 翻訳単位同一検査」が
   最後の防壁として必要になる (規律 1 を機械で守る唯一の経路)。

**逃げ道の不在**: D16 の「trace-hook → patch」例外は [T-109] の**試作 1 回限り**であり
(2026-07-26 の survey が親の「gate 待ちなら patch に置ける」を誤りと認定済み)、本件には使えない。
親 repo 側に独自 header を置いて `-I` で注入する案は、buildcache の観測者効果検査を通らない
手動 cmake 経路になるため同 survey §3.5 が否定している。

## 2. 再凍結の実コスト (実測 — 当初想定より小さい)

D16 の注記は「新 pin の再承認 + `known_axes_freeze` / `floor_protocol` の再凍結」を確定コストと
書いているが、**既存の凍結成果物は無効化されない**ことを実測した。

- `output/s1-freeze/known_axes_freeze.json:4` と `output/s8b-freeze/floor_protocol.json` は
  `ccbench_pin: d706650…` を**記録**しているが、これを現在の gitlink と照合する live 検査は無い
  (`s8b_oracle_manifest.py:384` は形式検査のみ、`t080_freeze_migration.py:1066` は記録された
  pin で blob を解決するだけで、その commit は新 pin の祖先として残る)。
- pin 照合が発火するのは (a) `test_s8b_approved.py` の always-on gate と
  (b) `s8b_floor_campaign.build_protocol_document` = **新しい floor protocol を凍結するとき**だけ。
- したがって **floor の実機再測は不要**。必要なのは承認定数 2 個の更新承認である。

**ただし規律 1 の担保として、旧 pin / 新 pin の TRACE=0 翻訳単位が同一であることの実測は必須**
(§1-4)。これは build 1 組で済み、計算ノードを要しない見込みだが未実測である。

## 3. 提案する手順 (順序が本質)

新 pin の SHA は commit を作るまで存在しないので、承認は事後にしかできない。

1. 別 wave が `include/trace.hh` + `cc/silo/transaction.cc` (+ `cc/si/transaction.cc`) の
   v2 化を submodule の `izanagi-trace` に **local commit** し、SHA を報告する。gitlink は動かさない。
2. 同 wave が **旧 pin 対新 pin の TRACE=0 翻訳単位同一検査**を実装・実行し、結果を報告する。
   赤なら 1 に戻る (規律 1)。
3. **ユーザーが** submodule を push し、新 pin の SHA を承認する。
4. 承認後の wave が gitlink を前進させ、`s8b_approved.CCBENCH_FULL_SHA` と `pin.CURRENT_PIN` を
   承認済み値へ更新し、verifier 側を v2 必須へ切り替え、`test_characterization_txn_tail_loss_is_false_green`
   を反転する。

## 4. 裁定を求める 3 問

### Q1: FN-2 を進めるか (主問)

- **(a) 推奨: 上の 4 段手順で進める。別 wave として起票する。** 理由: FN-2 は現行 silo の
  certified 結果にも乗っている偽陰性であり、S1 移植を採らなくても返す価値がある。
  再凍結コストが実測で「承認定数 2 個」に縮んだので、当初想定より安い。
- (b) S1 移植 wave (mocc) と束ねる。どちらも gitlink 前進を要するので承認手番が 1 回で済む。
- (c) FN-2 は残債として台帳に残し、当面塞がない (characterization テストで可視化を維持)。

### Q2: 手順 1 の submodule local commit を誰が作るか

- **(a) 推奨: AI (別 wave の Codex 実装子) が作り、SHA と TU 同一検査の結果を報告する。**
  push と定数承認だけをユーザー手番にする。
- (b) 変更内容を patch として提示し、commit もユーザーが行う。

### Q3: 手順 4 で v1 trace を拒否するか

- **(a) 推奨: 拒否する (v2 必須)。** v1 を受理し続けると FN-2 が残り、「古いビルドの trace なら
  素通り」という fail-open が恒久化する。
- (b) 移行期間だけ v1 を受理し、integrity note で可視化する。

## 5. この裁定で変わらないこと

- 絶対規律 1〜6。本 wave が実装する FN-1 の witness 検査 (別途 land 済み/予定)。
- CCBench の pin d706650 と、それに束縛された既存の凍結成果物・certified 結果。
- cross-protocol 比較の実測 (ユーザー明示により本 wave の射程外)。
