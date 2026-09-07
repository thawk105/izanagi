# 段 4 裁定 — dev-wave-t2365-a2-plot-schema

段 2 プラン 1 本、段 3 敵対相談 2 本 (lensA=正しさ境界、lensB=実効性) を受けた親の裁定。
本文の file:line は wave worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema` を基準とする。

## 0. wave 開始後に判明した新事実 — 取り直しは現行コードでは走らない

親は段 3 と並行して A-2 attempt `t2364-20260907a` を実投入した。**2 workload とも約 50 秒で
`driver_rc=2` で失敗した。**

- 本文 (rr5 / rr50 とも同一):
  `paper-story A-2 indeterminate: [Errno 22] Invalid argument: <attempt root>/receipts/condition-gate-<workload>.admissions.jsonl`
- 機序: `_write_condition_gate_admissions_x` (`orchestrator/campaign/paper_story_a2_certification.py:978`)
  が `_atomic_write_bytes_noreplace` (同 `939`) を呼び、これが `_rename_noreplace` (同 `4135`) 経由で
  `renameat2(RENAME_NOREPLACE)` を使う。**計測領域も repo も lustre であり、lustre は同フラグを
  実装せず EINVAL を返す。** 親が `stat -f` で両方 lustre であることを実測した。
- 同じ `_rename_noreplace` は `materialize` (同 `4522`) でも使われるが、そちらには
  `_publish_staging_after_einval` (同 `4194`) という EINVAL 退避が既にある。**新しい file 用 writer が
  同じ穴を退避なしで再導入した。**
- 導入は T-2337 の commit `1e22c4cbd`。同型事故は `5dcea6e56 fix(a2): Lustre の EINVAL で
  materialize を継続する` で一度直されている。**test が緑なのは pytest の一時領域が xfs
  (同フラグ実装あり) だからで、production は初回実走で落ちた。**
- lensB が独立に同じ結論へ到達し、実走 stderr と compute-result を一次資料として引いた。

**裁定 0-1 (real、blocker、scope 内):** この修正を **単位 D** として新設する。ユーザーが scope 外と
した「仮想リスク向けの gate・検査・台帳・一般化」ではなく、ユーザーが明示的に指示した
[T-2364] 取り直しそのものの阻害要因だからである。

**裁定 0-2:** 単位 D は `orchestrator/campaign/paper_story_a2_certification.py` 本体に触れる。
これは稼働中 `dev-wave-t2341-b4-floor-driver` が予定編集面に挙げていた file である。段 5 投入直前と
統合直前に、全 worktree の未 commit 差分まで含めた重複検査をやり直す。競合が出たら停止して報告する。

**裁定 0-3:** 失敗 attempt `t2364-20260907a` は受領証が create-only なので再利用しない。
submit tree を更新すると job-body bytes が変わって閉じられなくなるため、**裁定と同時に
`finish-group` で completion / acquisition を書いて閉じた (rc=0)。** 新 ID は `t2364-20260907b`。

## 1. lensA の所見

### 所見 1 — CLI で hash を渡す設計は pin を自己申告に落とす: **real・採用**

改変した成果物に自分で計算した hash を添えるだけで、偽の判定を載せた図を publish できる。
`status` は文字列であることしか検査されず effect から再導出されない
(`tools/plotting/plot_a2_certification.py:274`)。親の (P1-2)「pin を省略できる形にしない」は
**文面上しか守られていなかった。** 段 2 プランの「任意の legacy pin でも旧受理集合は広がらない」は
refuted。

**プラン v2:** **pin を CLI 引数で受け取らない。** plotter が repo 所有の pin 表を持ち、CLI は
「どの成果物か」を選ぶだけにする。表の key は certification の repo 相対 path、値は
certification と raw manifest の SHA-256 の組とする。新しい attempt を図にするには **repo へ entry を
足す commit が要る** — これが凍結物の所定手続きであり、査読を通る。
`main(expected_hashes=...)` の kwargs は test 専用の既存 seam として残す (CLI からは到達しない)。

**「台帳の追加は scope 外」との関係:** これは新設の台帳ではなく、既存の `CANONICAL_SHA256`
(同 `33-37`) を 1 段だけ深くしたものである。新規 file も新規 gate も作らない。

### 所見 2 — caption が証拠より強い主張になる: **real・採用**

受領証から言えるのは「manifest に束縛された canonical record が `use_class="paper"` /
`admitted=true` と記録している」までで、「D1198 の関門を実施し通過した」ではない。元の
supply / meaning records は保存されない (`orchestrator/campaign/paper_story_a2_certification.py:978`)。

**プラン v2:** 新版の gate 文は受領証の観測として書く。「関門を通した」とは書かない。

### 所見 3 — 旧経路から落ちる検査は bytes authority だけ: **real・記録**

所見 1 の裁定でこの欠落は閉じる。

### 所見 4 — `bound` は最上位 `status` ではなく cell の `source_binding_status`: **real・採用**

そのまま実装すると新しい成果物を全部拒否する
(`orchestrator/campaign/paper_story_a2_certification.py:2594`、`4249`)。exact field path を実装子へ渡す。

### lensA の裁定パッケージ候補 — **scope 内へ引き取る (単位 E)**

新しい図の prefix、新しい日付の results 節、`docs/paper-story/figures/README.md` への登録、
新しい図に対する closure 検査の担当が段 2 プランに無かった。これは本 wave の成果物そのものなので
scope 外へ送らず **単位 E** とする。図・results・README は親が docs として書き、closure 検査は
単位 A の所有 file (`orchestrator/tests/test_plot_a2_certification.py`) へ入れる。

## 2. lensB の所見

### 所見 1 — lustre の EINVAL: **real・採用**

裁定 0-1 のとおり単位 D とする。最小ハンクは `939-953` の file 公開だけに EINVAL 時の
create-only hard-link 公開と staging の unlink を足すもの。**親が lustre 上で実測した:
`ln` は成功し、既存名への `ln` は EEXIST で失敗する。** よって hard link は求める
「既存なら失敗する不可分な公開」をこの FS で正確に満たす。directory 用の
`_publish_staging_after_einval` を流用しない (hard link 不可のため claim file を使っており、
file にはリンク方式の方が強い)。

### 所見 2 — 投入時 policy と収集時 policy がずれると provenance が成立しない: **real・採用**

受領証 chain は `policy_sha256` を照合しない。別木の新 policy で collect すると
`certification.json` の `policy_sha256` / `policy_bytes_base64` と公開先が
「投入時 policy ではなく収集時 policy」を表す偽の provenance になる。

**プラン v2:** 新しい attempt は **単位 B と単位 D を含む固定 HEAD の submit tree から投入する。**
親が段 3 と並行して行った先行投入 (旧 policy・main HEAD) は、この理由からも正式な取り直しには
使えない。**先行投入は破棄する。** ただしそれが lustre の阻害要因を発見したので、
判断としては誤りでなかったと記録する (node 時間の損失は約 50 秒 × 2)。

### 所見 3 — 投入元は固定 submit tree、収集も同 tree の Python から: **real・採用**

`collect --repo-root` は materialize 先にしか使われない
(`orchestrator/campaign/paper_story_a2_certification.py:4452`)。よって collect も submit tree の
Python と policy から起動し、`--repo-root` だけ wave worktree に向ける。**wave worktree は投入後も
編集してよい。** 固定するのは submit tree である。

### 所見 4 — 失敗 attempt の再利用条件: **real・採用**

裁定 0-3 のとおり。

### 所見 5 — 広い変異は単一理由に帰属しない: **real・採用**

§4 の事前登録で狭い照準に分割する。

### lensB の pin 閉包 — **採用**

段 2 プランとの差分は非 pin の使い捨て probe path 1 件だけ。実際に張り直す live golden は
`orchestrator/tests/test_paper_story_a2_certification.py:1767-1770` の SHA assertion 2 箇所。
`protocol_sha256` の golden は張り直さない。fixture の destination
(同 `984-991`) は赤にならないが live policy と揃えるため更新する。

## 3. 確定した scope と分割

| 単位 | 所有 file | 内容 |
|---|---|---|
| A | `tools/plotting/plot_a2_certification.py`、`orchestrator/tests/test_plot_a2_certification.py` | 新旧 2 profile の schema 対応、repo 所有 pin 表、gate 文の成果物由来化、新図の closure 検査 |
| B | `orchestrator/campaign/paper_story_a2_certification.v2.json`、`orchestrator/tests/test_paper_story_a2_certification.py` | `tracked_destination` を新 leaf へ、golden 2 箇所を張り直し |
| D | `orchestrator/campaign/paper_story_a2_certification.py`、`orchestrator/tests/test_paper_story_a2_certification.py` | EINVAL 時の hard-link 公開 |
| E | docs (親が書く) + 単位 A の test | 新図・新 results 節・figures README 登録 |

**B と D は同じ test file を所有するので 1 単位に統合する (単位 BD)。** A と BD は編集 file が
交わらないので並列投入する。単位 E の docs は親が段 7 で書く。

新しい宛先は `output/insights/2026-09-07_t2364-paper-story-a2-certification`。
新しい policy bytes SHA-256 は段 2 と lensB が独立に一致した
`67dce5a785dfc52d5df9b773f7a65905a030b7bd61ab7706704e2ed8e85a0487` だが、**実装子は自分で再計算し、
一致しなければ自分の値を使って報告する。**

## 4. 変異の事前登録 (DW-M01)

実装前に登録する。lensB 所見 5 に従い、複数 node が同時に落ちる広い変異は登録しない。

| # | 位置 | 変異 | 単一理由で赤にする期待 node |
|---|---|---|---|
| M1 | `paper_story_a2_certification.py` の EINVAL 退避 | 退避を消して EINVAL を送出したままにする | EINVAL 注入の正例 1 本 |
| M2 | 同 退避の公開手段 | hard link を「既存を置換する rename」に変える | 既存宛先ありの負例 1 本 |
| M3 | plotter の pin 表引き | 表を引かず呼び手が渡した値をそのまま期待値にする | pin 自己申告の負例 1 本 |
| M4 | plotter の profile 判定 | 新版 cert と旧版 manifest の交差を許す | schema 交差の負例 1 本 |
| M5 | plotter の gate 文 | 新版でも旧の固定文を出す | 新版 caption の正例 1 本 |
| M6 | plotter の `source_binding_status` 検査 | 検査を消す | 非 `bound` の負例 1 本 |
| M7 | policy の `tracked_destination` | 旧 leaf へ戻す | policy bytes golden 1 本 |

**実装後に単一理由性を確認する。** 前後や内側に同じ入力を拒否する層があって理由が絞れない変異は
登録から外し、実効 gate へ再照準する。

## 5. 実行順序

1. 段 5 で単位 A と単位 BD を並列実装。
2. 段 6 で敵対レビュー 2 本、fix、変異本走。
3. 単位 A / BD を統合 commit。
4. submit tree をその tip へ進め、`t2364-20260907b` を投入。
5. 終端後 `finish-group`、次いで submit tree の Python から `collect --repo-root <wave worktree>`。
6. 新しい pin entry を足す commit、図の生成、results 節、README 登録 (単位 E)。
7. 段 7 記録 → 最終受入全走 → 段 9 land。

**投入から収集までの間、wave worktree は編集してよい。固定するのは submit tree である。**

## 6. 追記 — 同じ族の 2 例目が独立に出た (段 5 投入直前に判明)

段 5 投入直前に local main を見たところ、12 commit 進んでおり、その中に
`79707198f docs(a1-pilot): attempt-0002 の投入結果を記録する` があった。

**A-1 の wave が、本 wave の失敗の約 20 分前に、同じ `renameat2(RENAME_NOREPLACE)` が lustre で
EINVAL になる件を独立に踏んでいる。** 失敗箇所は A-1 driver の group submission receipt の公開で、
向こうも同じ directory で実測し、`RENAME_NOREPLACE` は errno 22、`flags=0` は成功、と記録している。
向こうは実装面の差分ゼロで、修正を新タスクへ送り裁定パッケージとして返している。

**裁定 6-1:** 対象 file が別 (`paper_story_a1_paired.py` と `paper_story_a2_certification.py`) なので
競合しない。本 wave は A-2 の実例だけを直す。A-1 側には触れない。

**裁定 6-2:** `DW-G03` が族一般化に求める「同型欠陥が異なる producer / consumer で独立に 2 件
再現」は**これで満たされた。** ただし一般化は A-1 driver に触れることになり、それは稼働中の
別 wave の編集面である。またユーザーは本 wave の scope を明示的に絞っている。
**したがって本 wave では一般化しない。族一般化は裁定パッケージとしてユーザーへ返す。**

**裁定 6-3:** 向こうの記録は `flags=0` の成功を退避候補として挙げているが、`flags=0` は
既存を黙って置換する。**file の公開に対しては hard link の方が強い** (既存名へのリンクは
EEXIST で失敗し、置換が起きない)。本 wave の単位 D は hard link を採る。この差は
族一般化の裁定でも保たれるべき点として記録する。
