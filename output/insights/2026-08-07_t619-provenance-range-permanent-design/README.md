# provenance 既定監査の範囲 — 恒久形の設計と裁定パッケージ ([T-619]、2026-08-07)

依頼: 「[T-619] — provenance 既定監査の範囲が `--ancestry-path` で side-branch を見ない穴。恒久形の設計まで」

計測 checkout = `.claude/worktrees/dev-wave-t619-provenance-range` (branch
`worktree-dev-wave-t619-provenance-range`、起点 `bb824d8b`)。submodule `external/ccbench` は
`d706650c` で pinned-clean。実行環境は Pegasus のログインノード。**本 wave は実装差分を持たない。**
段 4 で「実装しない」と裁定したため段 5・6 を飛ばし、変異 matrix と受入全走は対象外である
(`DW-S04`)。値の出所は Git plumbing の直接実測と、出荷済み関数への直接呼び出しである。

## 結論

**穴は実在するが、依頼が指した base 層では今日も no-op である。同型の穴は 1 つ下の
「epoch 適用述語」層で現に開いており、そちらは実測で 26 commit が規約適用外にある。**

恒久形は、選択集合と 4 層の epoch 適用述語を**同じ 1 つの述語**へ揃える形になる。現行 main での
一回性コストは新規違反ちょうど 1 件で、その種別は既知違反台帳が受けられる 2 種の一方である。
ただし恒久形は (a) 契約本文の改訂、(b) 既知違反台帳への 1 件追加、(c) forward correction の
受理集合変更、の 3 つを伴い、いずれもユーザー裁定の領分なので**実装は裁定へ返す**。

## 何が起きているか

既定監査の選択集合は `tools/check_ai_provenance.py` の `_commit_range(None)` が決める。

```python
descendants = _git("rev-list", "--reverse", "--ancestry-path", f"{policy}..HEAD").splitlines()
return [policy, *descendants]
```

`--ancestry-path A..B` は「A の子孫**かつ** B の祖先」に限る。素の `A..B` は「B から到達可能で
A から到達不能」である。両者の差は **policy より前で分岐し、後日 merge された branch 上の commit**
であり、これらは HEAD から到達できるのに既定監査の選択集合へ入らない。

同じ「lineage 対 reachability」の非対称は、選択集合の**中**でも再出現する。scope 規則・
実装面 Codex author 契約・Co-Authored-By 配置規則は、いずれも
`ancestry.is_descendant(epoch, C)` / `has_cab_policy(C)` という lineage 述語で適用可否を決めている。

## 実測

すべて起点 `bb824d8b` で測った。段 2・段 3 の独立 3 子が同じ値を再現している。

| 層 | epoch commit | `--ancestry-path` | 素の range | 差 | 新規違反 |
|---|---|---:|---:|---:|---:|
| base policy | `50c1ef4e5078ba54e0d00cee18eb01ddb6c2149a` | 1701 | 1701 | **0** | 0 |
| scope | `2f0245c196f82dddef91a9966e19b78a4b3f62e9` | 1579 | 1579 | **0** | 0 |
| implementation | `8c6d3f3bdc716c1ede8febb83ced1b0351a99118` | 1238 | 1240 | **2** | **1** |
| CAB | `9b26b3bd3acc10df95ef6ef6684a91d2ff3fa2ec` | 1182 | 1206 | **24** | 0 |

- **base 層は今日も no-op。**[T-619] 起票時の 1659 = 1659 と同じ状況が続いている。
  依頼が指した穴は将来の穴であって、現に発火してはいない。
- **epoch 層は現に発火している。** implementation 層の 2 件と CAB 層の 24 件、計 26 commit が
  「既定監査の対象ではあるが、その規則の適用対象と判定されていない」状態にある。
- implementation 層の 2 件は `333605d680ec15f3f74b00e9e2746ae317b85dc5` と
  `6a9c97c46a4e6812c8966437a6b62b6a31b64521` (どちらも 2026-07-28 の [T-142] wave)。
- CAB 層の 24 件は全件について raw `Co-Authored-By` 数と隔離 parser の認識数が一致した
  (12 件が `1/1`、12 件が `0/0`)。**CAB 違反は 0 件。**

### 差が生まれる理由は dev-wave の land topology そのもの

合成 repo を作らなくても、実 repo の任意の anchor で再現できる。anchor
`f85e16e2416197adc2c24b1af7784db9bb807b87` では `--ancestry-path` が 62、素の range が 79 で
差 17 件、その中身は `f85e16e2..bb40c870` = [T-503] wave branch の 7 commit を含む。
wave 側で local main を merge し、main を wave tip へ ff-only する現行の land 手順は、
「main のある時点の tip から見て子孫でない commit が、後から main へ入る」形を**毎回**作る。

### 一回性コスト

述語を統一したとき現行 main で新たに赤になるのは 1 件だけである。出荷済み
`validate_implementation_author` に実 message と実 path を渡して直接測った。

```text
333605d680ec15f3f74b00e9e2746ae317b85dc5
  → 実装面に Codex role=author がない
    output/insights/2026-07-28_t142-review-verbatim/count_abort_reasons.py
    output/insights/2026-07-28_t142-review-verbatim/count_frontier.py
```

この commit は Claude author・Codex researcher・Codex reviewer を持つが Codex author を持たない。
`.py` は所在不問で実装面である ([T-596] の裁定で insights 配下も現状維持と確定済み)。
2026-07-28 の commit なので実装面契約 (2026-07-29 導入) の**前**に書かれており、
真の legacy である可能性が高い。もう 1 件の `6a9c97c4` は `docs/failures.md` だけで非該当。

## 恒久形 (設計)

### 統一述語

規則 R の **seed 集合** `seeds(R)` を、R の導入を内容検出した commit の集合とする
(base は `--diff-filter=A` の hit、他 3 層は pickaxe hit)。権威 tip を `H`、`Anc(X)` を X 自身を
含む祖先集合とする。

```text
applies_R(C) := C ∈ Anc(H) かつ
                ( (∃p ∈ seeds(R): p ∈ Anc(C))  または  (¬∃p ∈ seeds(R): C ∈ Anc(p)) )
```

- 第 1 項が現行の lineage 述語。第 2 項が今回足す「どの seed の祖先でもない」= 側枝分である。
- `C = p` は第 1 項で真になり、**導入 commit 自身にも規約が適用される** (契約の「導入 commit 自身と
  以後」を保つ)。
- **seed が複数でも一意な root を要求しない。** これが要点である。CAB 規則は branch ごとに独立した
  seed を持ちうるため「全 hit の祖先である一意 root」を要求する設計は成立しない (下記 B1)。
- base 層へ当てると `{policy} ∪ (Anc(H) \ Anc(policy))` = 素の `policy..HEAD` に policy を前置した
  集合に一致する。**選択集合と適用述語が同一の式になる**。
- lineage で適用可否が決まらない commit は第 2 項で「適用する」に確定するので、
  「判定不能」として公開すべき残余が存在しない。

### 適用境界

- **権威ある既定監査 (`--range` なし) だけ**に適用する。明示 `--range` は一意な権威 tip を持たないので
  現行 lineage 述語を残す。
- `--message-file` 経路は 1 bit も変えない。
- `H` は起動時に一度だけ full SHA へ解決し、policy 解決・range・epoch 解決・ancestry 構築の
  全 query へ同じ値を渡す。終了時に HEAD が動いていれば rc=2。
- shallow clone / graft / replace / 非一意な policy add は既定監査で rc=2 とする。
  「権威ある full-history」を名乗れない状態で緑を返さないためである。
- `--reverse` と policy 前置は保存する。出力順は既存テストが固定しており、policy 前置を落とすと
  導入 commit 自身の監査が消える。
- stale (rc=2) は新規違反 (rc=1) より優先する。受理集合は広がらない。

### なぜ「lineage 据え置き + 診断だけ公開」を採らないか

据え置き案は rc を変えないので安全に見えるが、**将来の epoch でも同じ topology で違反が通る**。
実装面契約のように後から追加される規則がある以上、「epoch 導入前に分岐した wave branch が
epoch 導入後に実装面 commit を書いて land する」形は再発する。診断だけの公開は、
D221 が定めた「既知 0 件のときの逐語出力は完全に不変」という receipt 契約も破る。

### git だけでは決められないこと

同じ DAG は次の 2 つを区別できない。

- 側枝 commit が epoch 導入**前**に書かれ、長期間後に merge された (真の legacy)。
- branch は epoch 前に分岐したが、commit 自体は epoch 導入**後**に書かれた (規約違反)。

author/committer date は任意に設定・改変できるので信頼根拠にならない。reflog や branch 作成時刻は
commit object に束縛されず失効する。署名は object の同一性を認証するが、作者がどの規約を認識して
いたかは証明しない。厳密な時点拘束には信頼できる timestamp か merge 時 attestation が要り、
これは D205 のプロトタイプ基準では過剰である。**reachability は「HEAD へ取り込まれた時点で
現行 policy 下として扱う」という運用上の保守的近似**であり、その代償が「真の legacy を拒否しうる」
ことである。代償の受け皿は SHA ごとのユーザー裁定 (既知違反台帳) しかない。

## ユーザー裁定へ返す項目

1. **統一述語を既定監査へ入れるか。** 入れる場合、`333605d6` を D221 の既知違反台帳へ足して緑を
   保つか、既定監査を rc=1 のまま運用するか。台帳追加は防壁の恒久緩和なので裁定が要る
   (D221 が同じ理由で却下した項と同型)。
2. **契約本文 (`docs/ai-provenance.md`) の改訂を許すか。** 現行本文は「導入 commit 自身と以後の
   commit に適用」「導入前の欠落は legacy」と書いており、これは lineage 読みである。統一述語は
   側枝 commit を拘束するので本文が実装と食い違う。**family (`docs/ai-provenance.md` +
   `docs/provenance/**`) の byte 余は 6 のみ**なので、純増の加筆は物理的に不可能で、
   等価縮約が要る (下記)。
3. **forward correction の受理集合が変わることを受け入れるか。** 選択集合が広がると
   `AI-Agent-Correction` の candidate が増えうる。増えれば `PR-C01` の exact 1 件規則に当たり、
   今まで緑だった既定監査が赤になる。方向は strict 化なので規律 2 には整合するが、
   「correction の受理集合は変えない」という当初の不変条件は**偽**である。
4. **scope / CAB / 形式 kind の legacy 違反に受け皿が無いことを受け入れるか。** D221 台帳が
   受けられるのは `missing-ai-agent` と `missing-codex-author` の 2 種だけで、forward correction は
   固定 target で消費済みである。現行 main では該当 0 件だが、将来 pre-policy fork が land すると
   既定監査が恒久的に rc=1 となり `DW-O17` の full 監査が land を止める。
5. **明示 `--range` を lineage のまま残す境界**を採るか。

### 裁定 2 に伴う等価縮約案 (採否も裁定)

`docs/ai-provenance.md` の次の 4 箇所 (計 348 bytes) は、いずれも「導入 commit 以後だけ適用し
遡及しない」を別々の語で 4 回書いている。

- `本規約は導入 commit 自身と以後の commit に\n適用し、既存履歴を書き換えない。` (104 bytes)
- `この規則は内容検出した導入 commit 以後へ適用する (F25)。` (77 bytes)
- `導入 commit 以降にのみ適用して遡及せず、\n  checker も内容検出した導入 commit 以後だけ検査する。` (129 bytes)
- `本節を導入する commit 以後、` (38 bytes)

これを次の 1 文 (180 bytes) へ統合すると net −168 bytes となり、entry 6,119 / family 8,826 になる。

```text
既定監査は各規則の内容検出 commit 自身と、その祖先でない HEAD 到達 commit に適用する。導入祖先は legacy とし、履歴を書き換えない。
```

`PR-A02` の「導入 commit から `HEAD` まで」も同じ意味へ揃える必要がある。**この縮約は
安全義務の削除ではなく、同一義務の 4 重記述を 1 本化するものである**が、契約本文の書き換えなので
実施は裁定に従う。

## 段 3 の敵対レビューで確定した所見

段 2 のプランと親の brief を、read-only の codex 2 本で異なるレンズから攻撃させた。
blocker 6 件・must-fix 5 件・nit 2 件が出て、全件を real と裁定した。裁定表は
`s4-adjudication.md`、逐語は `verbatim/` にある。設計を変えた主なものだけ挙げる。

- **A1**: epoch 述語を lineage のまま据え置く親の暫定裁定は、将来 epoch で違反を通す。撤回した。
- **A2**: 選択集合の拡大と「forward correction の受理集合不変」は両立しない。不変条件が偽だった。
- **A3 / B1**: 段 2 が提案した「4 epoch を共通 resolver で単一 epoch へ畳む」案は成立しない。
  CAB は branch ごとに独立した seed を持ちうるため一意 root が存在せず、fail-closed なら rc=2、
  片方を任意採用すれば他方の明示 range が rc=1 から rc=0 へ緩む。**seed 集合を保つ統一述語へ
  差し替えた**のはこの所見による。
- **A4**: HEAD race。監査の途中で HEAD が進むと、新しい tip で epoch を解決しながら古い snapshot の
  ancestry で判定してしまう。`H` の一度きり解決と終了時 drift 検査を恒久形へ入れた。
- **A5**: gap 診断を stdout へ足すと D221 の receipt 不変契約を破る。統一述語では判定不能が
  残らないので、診断ごと設計から落とした。
- **B3**: 恒久形は文書契約の改訂を必須にする。0 byte 方針では land できない。
- **B5**: 真の legacy 違反のうち scope / CAB / 形式 kind には受け皿が無い。
- **B7**: 親の「`_audit_history` は順序非依存」は verdict にのみ成立し、出力順は既存テストが
  固定している。`--reverse` は保存する。

## 本 wave が実装しない理由

3 つあり、どれも単独で十分である。

1. ユーザーが scope を「恒久形の設計まで」と指定した。
2. 恒久形は契約本文の改訂を要する (B3)。文書契約の変更は裁定の領分であり、family 余 6 bytes では
   等価縮約の採否も裁定が要る。
3. 恒久形は `333605d6` を新規違反にする。緑を保つには既知違反台帳へ 1 件足す必要があり、
   台帳追加は防壁の恒久緩和としてユーザー裁定の領分である。

## 新規に起票する所見 (scope 外・本 wave が作った欠陥ではない)

- `_scope_policy_commit` の `-S "scope="` は意味的に一意でない。実 repo でも hit は既に 2 件
  (`2f0245c1` と `6d7141dc`) あり、現在は `--reverse` の最古が偶然正しい導入 commit になっている
  だけである。契約本文の非規範的な箇所に `scope=` が現れると、そこが epoch と誤認され、
  本来 legacy の commit が scope 違反として拒否されうる。scope finding は既知違反台帳に登録できない。
- `_build_ancestry` の pickaxe は選択集合の全 SHA を positional argv へ展開する。約 51,151 commit で
  `ARG_MAX` (この環境で 2,097,152 bytes) を超え、既定監査が rc=2 で実行不能になる。現行は
  1,702 commit なので約 49,000 commit の余裕がある。bitset のメモリも commit 数の二乗で伸び、
  4 GiB を初めて超えるのは約 253,565 commit である。

## 一次資料

- `s4-adjudication.md` — 段 4 の裁定表と恒久形 v2 の全文。
- `verbatim/s1-brief.md` — 親の段 1 brief (実測 M1〜M13、暫定裁定 P1〜P5)。
- `verbatim/s2-plan.md` — 段 2 の設計プラン (codex `gpt-5.6-sol`、`reasoning=max`、read-only)。
- `verbatim/s3-lensA.md` — 敵対レンズ A (正しさ防壁と受理集合)。
- `verbatim/s3-lensB.md` — 敵対レンズ B (機構整合・消費者・予算)。
