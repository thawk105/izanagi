## 所見

### blocker 1 — 追補 B の差分主張が bytes と一致しない

初版→v2 は `37 additions / 31 deletions` であり、`b03` 外にも変更があります。

- 題名を変更し、再発行説明を6行追加: [addendum-b-v2.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:1)
- `b03` 外の末尾 disclaimer を追加・変更: [addendum-b-v2.md:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:209)
- それにもかかわらず「変更は `b03` の縮小1点だけ」と断定: [addendum-b-v2.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:7)、[package.md:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/package.md:173)、[README.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/README.md:31)

`b01`〜`b02` の field slice は双方5186 bytesで完全一致しました。しかし「文書全体の変更は1点だけ」は偽です。ユーザー指定により1行でも違えば blocker です。

**成果物影響:** 承認される追補Bの blob digest と、試行台帳・材料レポートが記録する `addendum_b` 三つ組が、提示されたレビュー範囲外の bytes を含むものへ変わる。

### blocker 2 — 初版の投入前一意性 gate が孤児化している

初版の次の規範は、core+追補Pへ移設されたのではなく、source study の受理条件から消えています。

> 「この一意性が成立しないまま本走を投入してはならない」

初版 [addendum-b.md:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:181) にありましたが、v2は投入 gate が1つ減ると明記しています: [addendum-b-v2.md:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:212)。

新 core §8.2 と追補Pは「公表表を生成しない」側しか止めません。source core の `submit_main` は公表 core/Pに依存しないため、代替 gate ではありません。これは package Q1にも書かれていますが、推奨は喪失を受け入れる (a) です。

同じ台帳実体のままでも、さらに次が通ります。

- 予約なしで `submit_main` を開始する。
- 非原子的な read-then-write を2つ並行実行し、両方が ordinal 1 を得たとして本走を開始する。
- 同じ物理台帳に `(R,1,physical_id=A)` と `(R,1,physical_id=B)` を create-only で作る。根も台帳実体も同じだが、論理 `(R,1)` が重複する。

**成果物影響:** 公表予約が欠落・重複してもsource本走が受理され、certified primary選択とsource試行台帳は生成される一方、公表表の予約参照は欠落・多義になる。

### blocker 3 — `p03` は「同じ根の台帳取り替え」を閉じない

[p03:160-173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md:160) は、

- callerが引数・環境・checkoutで台帳を変えない
- 台帳実体の同定は本field外
- producer waveが後で実体を決める

を同時に定めています。

したがって、次の経路は5要件すべてを満たしたまま通ります。

1. producer v1 が台帳 `L1` をコードに固定し、`(R,1)` を原子的・create-onlyで予約する。
2. 結果を見た後、producer v2 が空の台帳 `L2` をコードに固定する。
3. callerは台帳を選んでおらず、各台帳内では一意・非解放・非再利用である。
4. `L2` で再び `(R,1)` を予約する。

これは caller選択ではなく、実装裁定による台帳差し替えです。`ledger_identity.status: undetermined_by_this_addendum` のままでは、根から唯一の台帳実体へ束縛する規範がありません。「この経路を閉じるのは本fieldの責務」という [同:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md:162) の保証は過大です。

**成果物影響:** 同じ根・ordinal 1・`α_pub=0.025` を空台帳ごとに再取得でき、公表系列の候補受理集合、Holm判定、公表表の値と累積FWER会計が変わる。

### must-fix 1 — unresolved marker は機械的な承認防壁ではない

判定は次のとおりです。

- (a) literalを知っていれば `rg` 等で検出可能。
- (b) 誤承認を機械的には塞がない。禁止は本文だけで、承認/fold gateに検出器がない。
- (c) landも止めない。実走した `python3 tools/check_docs.py` は `違反なし / rc=0`。

`check_docs.py` のplaceholder検査は `«反映»`、`«受入結果を反映»`、`«受入全走結果を反映»` の3 literalだけです: [check_docs.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/tools/check_docs.py:114)。さらにinsights列挙は再帰でなく `output/insights/*.md` だけです: [check_docs.py:1263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/tools/check_docs.py:1263)。三軸走査も当該文書に対し `rr80=[] / rr20=[]` でした。

**成果物影響:** marker入りPを誤ってfoldしてもlandは緑のままで、公表表のcore参照が未解決になり生成不能になるか、緩い将来resolverなら未特定coreを受理する。

### must-fix 2 — READMEが「不変の追補A」として別blobを指している

[README.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/README.md:22) は初版ディレクトリ `2026-08-08_t139-addendum-a/` を指します。しかし新 core が束縛するのは `2026-08-08_t139-r4-env-probe/addendum-a-reissue.md` です: [publication-core-v2.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:38)。

両者のSHA-256は異なります。

- 初版A: `1f561258…`
- reissue A: `f7db96ce…`

**成果物影響:** READMEから追跡した材料レポート・試行台帳の事前登録参照が、effectiveなreissueではなく旧A blobへ向く。

### nit — envelope説明とparserのfence規則が逆

Bは「grammarはfenceを除外しない」と書きますが、実装は `_outside_fences()` でfenced行を除外します: [addendum-b-v2.md:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:53)、[addendum_envelope.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/orchestrator/preregistration/addendum_envelope.py:83)。

**成果物影響:** 現bytesのfence内には見出しがないため値・受理集合は変わらないが、将来fence内見出しを置いた際のfield参照が文書記載と逆になる。

## 落とした規範の追跡

| 初版から落ちた規範 | 現在地 |
|---|---|
| `current_study.ordinal: 1` | P `p01` の許容ordinalと`p02.current_study.k=1`へ分散 |
| `reservation.mode: create_only` | B `b01`、新 core §8.2、P `p03` |
| `reservation.chosen_by_caller: false` | 根についてはB `b03`、台帳実体についてはP `p03` |
| `reservation.release_on_failure: false` | B `b01`、新 core §8.2、P `p03` |
| `separate_ledger` の非共有・primary非書込 | B v2 [168-171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:168) と新 core §8.1 |
| producer非選択canonical台帳、原子性、`(root,ordinal)`一意 | 新 core §8.2 + P `p03`。ただし台帳identity未確定の穴あり |
| 失敗・中断・未公表時の削除・解放・再利用禁止 | B `b01`、新 core §8.2、P `p03` |
| 宣言は権威でなく台帳側予約が権威 | 新 core §8.2 + P `p03` |
| 一意性成立前の`submit_main`禁止 | **どこにもない。孤児化** |
| 上記禁止が投入前admissionであるという時相境界 | **gateとともに消滅** |
| 開始後は既存分類のみ・予備置換禁止・新分類禁止 | B v2 [187-190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:187) |
| 開始後の失敗を開始前infra failureへ写さない | B v2 [190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:190) に逐語保存 |
| 「外部台帳が実在して初めて防壁」 | 新 core §8.2/Pへ移動したが、実体identityは未確定 |
| 「本書はprimary台帳へ書かず、a13へ要件を足さない」 | B v2 [168-169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:168) に逐語保存 |

末尾の「落とした5項目」は概念的要約であり、上記すべての逐語列挙ではありません。

## exact-key、digest、凍結bytes

- core v2差分は主張どおり旧版の104、105、569〜571行だけ。`5 additions / 5 deletions`、双方698行。
- parser実走結果:
  - B v2: `('b01','b02','b03')`
  - P: `('p01','p02','p03')`
  - B初版: `('b01','b02','b03')`
- Pの`## fields`は66行、次のvisible `## `は184行。その間のvisible `### `は68、93、144行の3個ちょうど。
- B v2のfields境界は67〜204行、visible field見出しは69、100、154行の3個。
- 5成果物の実SHAはどの本文にも現れず、自己参照digestはありません。`package.md`も他成果物のdigestを書いていません。
- Git作業木とHEADのblobは次の4文書ですべて一致し、`git diff HEAD -- ...` はrc=0:
  - source core: `ac939af4…`
  - 追補A reissue: `f7db96ce…`
  - core初版: `9b7bc193…`
  - 追補B初版: `5071acbd…`

## `p03` 5要件の反例

5要件はいずれも意味上の違反入力を構成でき、単独では恒真ではありません。

1. caller非選択違反: `--ledger=/tmp/empty` または環境変数で予約先を指定。
2. create-only・原子性違反: 既存entryを上書き、または無lockの並行read-then-writeを双方成功扱い。
3. 一意性違反: 同一台帳に同じ `(R,1)` の物理rowを2件置く。
4. 非解放・非再利用違反: failure後にrowを削除し、再び`(R,1)`を予約。
5. 宣言非権威違反: 台帳entryなし、または重複ありのまま6行公表表を生成。

ただしblocker 3のとおり、producer版の変更で台帳実体を差し替える入力は、これら5要件を全部満たしたまま累積をリセットできます。

## 総括

**NO-GO**  
blocker: **3件**。  
coreの5行差分と凍結既存bytesは正しいが、追補Bのexact-bytes説明は偽。  
最大の穴は、`p03`が台帳identityを固定せず、5要件を満たしたまま空台帳へ差し替えられること。  
加えてsource本走の投入前一意性gateが代替なしで孤児化している。