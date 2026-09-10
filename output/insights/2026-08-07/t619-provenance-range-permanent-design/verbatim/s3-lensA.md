結論として、blocker 2 件、must-fix 3 件、nit 1 件です。pytest と checker 本走は行っていません。件数は Git plumbing の実測、rc と受理集合はコード上の静的判定です。

## 所見

### P2 の lineage 据え置きは将来 epoch でも違反を通す

severity: blocker

具体的な発火入力:

```text
P(base)──M──E(implementation epoch)────────H
  \──────────C(tools/x.py、Claude authorのみ)──/
```

`C` の branch は `P` 後・`E` 前に分岐し、`E` land 後に `C` を作って `H` で merge する。`P` は `C` の祖先なので `C` は現行 base 選択にも入るが、`E` は `C` の祖先ではない。現行の `descends(implementation_epoch)` が False となり、Codex author 検査全体が省略される。scope と CAB でも同じ topology で再現できる。

該当: [brief.md:63–67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/brief.md:63)、[check_ai_provenance.py:942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:942)、[check_ai_provenance.py:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:951)

成果物影響: 本来 `missing-codex-author` による rc=1 となる履歴が、静的には rc=0 となり、receipt に finding が出ない。非 fatal gap 診断だけでは rc=0 のままである。plan の reachability 推奨はこの blocker を閉じているため、最終決定では P2 を明示的に撤回する必要がある。[plan.md:175](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:175)

### 選択集合拡大と forward-correction 受理集合不変は両立しない

severity: blocker

具体的な発火入力: T-618 台帳反映後かつ `333605d6…` を既知化する選択をした状態の disposable clone で、base policy の親から side branch を作る。

```bash
git switch -c rogue 50c1ef4e5078ba54e0d00cee18eb01ddb6c2149a^
# docs-only、通常 provenance は valid、
# 固定 AI-Agent-Correction 物理1行も exact な commit R を作る
git switch main
git merge --no-ff rogue
```

固定 target `6b64d217…` と正規 carrier `6d7141dc…` はどちらも base policy の子孫で、target は carrier の祖先であることを Git で確認した。一方 `R` は policy の子孫でない。

- 旧 `--ancestry-path`: `R` は除外され、candidate は正規 carrier 1 件。target 欠落が相殺される。
- 新 plain range: `R` も選ばれ、candidate は 2 件。1078–1082 行の exact-one finding が発生し、target 欠落も相殺されない。

該当: [brief.md:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/brief.md:51)、[plan.md:78–85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:78)、[plan.md:336](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:336)、[check_ai_provenance.py:1063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:1063)

成果物影響: 静的に rc=0→rc=1、`forward-corrected=1` が消え、target の欠落と `candidates=2` が finding になる。防壁は強くなるが、brief の不変条件 3 と plan の「forward correction は不変」が偽になる。PR-C01 の selected-set exact-one を守る限り回避不能なので、不変条件をユーザー裁定で改める必要がある。

### 共通 epoch resolver の探索 tip が未定義で off-HEAD CAB を fail-open にできる

severity: must-fix

具体的な発火入力: 既存テスト 862–893 行の topology。

1. main に legacy policy path を置く。
2. merge しない別 branch で CAB needle を導入する。
3. 同 branch の `C` に raw=1 / canonical=0 の split `Co-Authored-By` を置く。
4. main に戻り `--range C^!` を監査する。

現行 CAB 判定は selected tip `C` から pickaxe するため finding を生成する。plan の「共通 resolver」を scope/implementation と同じ暗黙 `HEAD` 探索で実装すると epoch が見えず、`check_cab=False` となる。

該当: [plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:97)、[plan.md:165–169](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:165)、[check_ai_provenance.py:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:643)、[test_check_ai_provenance.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:862)

成果物影響: explicit range の静的 rc=1→rc=0、CAB finding が receipt から消える。共通 resolver は default では pinned `H`、explicit range では selected tips を探索対象とする、と設計へ明記する必要がある。

### HEAD race を rc=2 にするとの約束に snapshot 境界がない

severity: must-fix

具体的な発火入力:

1. `H1` は base policy と `C` を含むが implementation epoch `E` を含まない。
2. 別 branch に `E` がある。
3. checker が `H1` で `_commit_range(None)` を終えた直後、別 process が `HEAD` を `merge(H1,E)=H2` へ fast-forward する。
4. epoch resolver と authoritative tip は `H2` を見るが、ancestry index は `Anc(H1)` だけなので `E` と `H2` が未知になる。
5. `R_E(C,H2)` で本来適用対象の `C` が、未知値 False によって非適用になる。

該当: [plan.md:69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:69)、[plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:97)、[check_ai_provenance.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:820)、[check_ai_provenance.py:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:857)、[check_ai_provenance.py:1045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:1045)

成果物影響: 現在の `HEAD=H2` に対して本来 rc=1 の `C` を含むのに、H1 snapshot の件数で「違反なし」rc=0 を返せる。最初に full SHA の `H` を一度だけ取得し、policy/range/epoch/ancestry の全 query に渡したうえで、終了時の HEAD drift を rc=2 にする検査が必要。

### epoch gap の stdout 追加は D221 の receipt 不変契約を変更する

severity: must-fix

具体的な発火入力: known entry を一件も選ばない合成履歴で、implementation epoch と lineage-incomparable な docs-only・valid commit `C` を merge する。finding は 0 だが gap は 1 件になる。

現行 receipt は `check_ai_provenance: N 件、違反なし` の 1 行。plan は gap を stdout に先行出力するため、known violation 0 件でも逐語出力が変わる。

該当: [decisions.md:10428–10430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/decisions.md:10428)、[plan.md:170–173](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:170)、[plan.md:342](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:342)

成果物影響: rc と G は不変だが、gap receipt 数が 0→1 となり stdout の逐語値が変わる。plan 自身が挙げる新規ユーザー裁定か、D221 を明示的に supersede する後続決定が必要。

### 選択拡大により stale が既存 rc=1 を rc=2 で飲み込む

severity: nit

具体的な発火入力: 新たに選ばれる side commit `K` を台帳へ置き、checker 退行によって期待 finding が消えた状態と、旧選択内の新規違反 `N` を併存させる。

旧選択では `K` が範囲外なので `N` により rc=1。新選択では `K` が stale となり、1169 行で例外を送出して rc=2になる。`N` の finding と known 一覧は出力されない。

該当: [check_ai_provenance.py:1146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:1146)、[check_ai_provenance.py:1154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:1154)、[decisions.md:10431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/decisions.md:10431)

成果物影響: rc=1→rc=2、receipt から `N` が消える。ただし非ゼロは維持され、D221 が stale 優先を要求しているため gate の受理集合は広がらない。設計・テストで意図した優先順位として固定すればよい。

## Git plumbing 再検証

基準 HEAD は `bb824d8b7fff427eb61d09cf3d9354359914c99c` だった。

M1:

```bash
git rev-list --count --ancestry-path 50c1ef4e5078ba54e0d00cee18eb01ddb6c2149a..HEAD
# 1701
git rev-list --count 50c1ef4e5078ba54e0d00cee18eb01ddb6c2149a..HEAD
# 1701
```

差は 0。なお `_commit_range` の返却数は policy 自身を足すため 1702 件であり、policy 前置を落とす変更は導入 commit の監査を消す。

M3:

```bash
git rev-list --count --ancestry-path 8c6d3f3bdc716c1ede8febb83ced1b0351a99118..HEAD
# 1238
git rev-list --count 8c6d3f3bdc716c1ede8febb83ced1b0351a99118..HEAD
# 1240
```

`comm -13` の出力は正確に次の 2 件だった。

```text
333605d680ec15f3f74b00e9e2746ae317b85dc5
6a9c97c46a4e6812c8966437a6b62b6a31b64521
```

両方とも base policy の子孫かつ HEAD の祖先、implementation epoch の子孫ではなかった。

M5:

```bash
git diff-tree --root --no-renames --no-commit-id --name-only -r \
  333605d680ec15f3f74b00e9e2746ae317b85dc5
git show -s --format=%B 333605d680ec15f3f74b00e9e2746ae317b85dc5 |
  git -c trailer.separators=: interpret-trailers --parse
```

実装面は次の `.py` 2 本。trailer は Claude author、Codex researcher、Codex reviewer で、Codex author と waiver はない。

```text
output/insights/2026-07-28_t142-review-verbatim/count_abort_reasons.py
output/insights/2026-07-28_t142-review-verbatim/count_frontier.py
```

したがって [check_ai_provenance.py:696–717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:696) の静的経路では `missing-codex-author` 1 件となる。`6a9c97c4…` は `docs/failures.md` だけで実装面非該当。

全 epoch の再計数結果:

| epoch | ancestry | plain | 差 | 新規 finding の静的件数 |
|---|---:|---:|---:|---:|
| base `50c1ef4e…` | 1701 | 1701 | 0 | 0 |
| scope `2f0245c1…` | 1579 | 1579 | 0 | 0 |
| implementation `8c6d3f3b…` | 1238 | 1240 | 2 | 1 |
| CAB `9b26b3bd…` | 1182 | 1206 | 24 | 0 |

CAB の差 24 SHA は [plan.md:116–139](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-range/s3/plan.md:116) の列挙と完全一致した。各 message の raw/canonical 数は 12 件が `1/1`、12 件が `0/0` で、不一致は 0。よって M13 の「現行 HEAD で全 4 層 strict 化が新たに生成する通常 finding は `333605d6…` の 1 件だけ」は静的に支持される。別件 `3f2c43d7580b8c26724d90278589862057508965` はこの増分に含まれない。

## refuted

- 安定した完全 DAG・固定 `P/E/H` では、core の単調性反例は構成できなかった。`S_old ⊆ S_new` かつ、旧 lineage 適用 `L_E(C)` は新 `R_E(C,H)` に包含される。policy 前置も plan が保存している。
- 完全 DAG の既定監査では `HEAD` が selected tips に入り、`_build_ancestry` は `Anc(HEAD)` を復元するため、選択拡大そのものが未知 commit を増やす反例は refuted。例外は上記 HEAD race と、拒否対象にした shallow/replace/graft。
- D221 台帳は full SHA・種別・1 finding だけを消費するため、追加 commit が既存 commit の新規 finding を既知化する反例は refuted。二件目の同種 finding も新規に残る。
- `--message-file` は 2016–2041 行の独立分岐であり、plan の preflight を `_commit_range(None)` 内に限定する限り、message、merge parents、prospective `rev-list` の受理 bit は変わらない。
- `3f2c43d7…` は既裁定、`333605d6…` は新規裁定待ちと明示されており、未裁定台帳追加の混入は refuted。ただし `333605d6…` を追加すれば strict counterfactual に対して rc=1→rc=0、known 件数 +1 の恒久免除になる。
- brief P4 の「D221 が全 legacy 違反の受け皿」は refuted。台帳種別は `missing-ai-agent` と `missing-codex-author` だけで、scope/CAB/形式違反は登録不能。plan 30–31 行の訂正が正しい。

## 総括

blocker あり（P2 の恒久据え置きと、plain 選択拡大／PR-C 受理集合不変の契約矛盾）— 現状のまま land してはならない。