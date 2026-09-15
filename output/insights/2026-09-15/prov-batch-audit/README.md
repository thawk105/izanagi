# 全史 provenance 監査の per-commit データ取得を一括化する

2026-09-15、branch `worktree-dev-wave-prov-batch-audit`。
ユーザー依頼「リポジトリの成長で比例して大きくなる受入全走等の研究開発で必ず踏むコストを
解決してほしい。たとえば全史検査。1 万コミット近くあって何かするたびに 1 万コミット検査するのは
愚か」に対する wave。

## 何をしたか

`tools/check_ai_provenance.py` が commit ごとに `git show -s --format=%s` と `--format=%B` を
起動していたデータ取得を、`git log --no-walk=unsorted --stdin -z` 1 回の一括取得へ置き換えた。
**検査対象 commit 集合・判定・findings・rc・公開出力・隔離 trailer parser は変更していない。**
速くなったのは取得層の定数を下げたからであって、検査を減らしたからではない。

## 測定 (login node、2026-09-15)

### 段 1 の費目分解 (逐次 n=200)

| 費目 | ms/commit | 比率 |
|---|---|---|
| `git show -s --format=%s` | 36.67 | 45.9 % |
| `git show -s --format=%B` | 31.00 | 38.8 % |
| `_ai_agent_values` (repo cwd `interpret-trailers`) | 8.73 | 10.9 % |
| 隔離 parse × 2 (`_isolated_parsed_trailers`) | 3.46 | 4.3 % |

全史一括取得は 0.49 秒 (`git log` 1 回)。全史 1 走は 133.6 秒 / 10074 件 (CPU 344 秒)。

### 同条件の旧新比較 (同一 worktree・checker の版だけ差し替え・交互 2 ラウンド)

| 走 | 新 | 旧 | 比 | 削減 |
|---|---|---|---|---|
| round 1 | 117.723 秒 (load 149.83) | 174.150 秒 (load 183.26) | 1.4793 | 32.40 % |
| round 2 | 173.070 秒 (load 173.88) | 275.465 秒 (load 119.37) | 1.5916 | 37.17 % |
| 平均 | 145.4 秒 | 224.8 秒 | **1.5355** | **34.79 %** |

逐語は `verbatim/speed_ab.log`。復元は `git checkout HEAD --` で行い、
`git status --porcelain` 空・`git diff --stat HEAD` 空を確認した (`DW-O19`)。

**親の見積もりは 2 度過大だった。** 段 1 brief は「2 桁速くなる / 全史 5 秒」と書き、段 3 の
実効性レンズ (L-1) に撃たれて撤回した。その後「4〜6 倍」と見積もったが、実測は **1.5 倍**である。
原因は L-1 が指摘したとおりで、費目比率を**逐次**で測ったのに実行は `AUDIT_WORKERS=min(cpu,32)` の
並列であり、残存費目 (trailer 解析・隔離 parse) の重みが相対的に大きくなる。
**成果として書けるのは 1.5 倍 (35 % 減) と「取得 subprocess を 2N 本から 1 本へ」の構造的事実だけ。**

### 等価性

- 親の独立裏取り: 提案コマンドと現行 `git show` を **全史 10443 件**で突合し、
  subject / message とも **mismatch 0**。framing の NUL 数 31329 = 3N。
- 同一 worktree・同一 range (`HEAD~500..HEAD`、merge 3399 件のため実監査 **6378 件**)・同一経路
  (計算ノード) で旧新の child stdout が **22591 bytes 完全一致 (diff rc=0)**。
- commit 後の全史監査 rc=0、**10105 件・新規違反なし・known-violations=56** (従来と一致)。

## 検証

| 検査 | 結果 |
|---|---|
| 焦点走 (9 file) | 3149 passed / 8 skipped / 0 failed (72.60 秒) |
| 変異 matrix | baseline PASSED、**KILLED 7/7・SURVIVED 0・MISMATCH 0・matching 7** |
| 受入全走 | **23700 passed / 68 skipped / 赤 0**、`verdict=child-green` |
| test 関数名 | 基底 201 → 209 (+8)、**消失 0 / 改名 0** |

変異の逐語台帳は `verbatim/mutation-final-spec.json`。
`DW-M07` に従い probe (全件 SURVIVED 期待) で観測 node を集めてから本登録した。
観測 node は I-1=58, I-2=16, I-3=1, I-5=8, II-1=37, III-1=1, III-2=1。

## 親が自分で訂正した誤り (erratum)

1. **測定設計の誤り。** 旧新比較を「wave worktree (旧) 対 impl worktree (新)」で組んだため、
   checker の版だけでなく**実行経路**まで変わっていた。checker は
   `orchestrator.campaign.login_headroom.grant_budget()` の判定で計算ノードへ dispatch する。
   実測した判定は `Admission.DISPATCH` (観測余裕 179 MB / 使用量 16.2 GB / 実効天井 15 GB、
   物理メモリは 197 GB 空き) で、**負荷ではなく izanagi 自身の予算枠**である。
   1 回目の結果 (old 947 秒 / stdout 33612 B 対 new 65.6 秒 / stdout 4832 B) は無効。
   新側の出力実体は Pegasus dispatch のログだった。正しくは**同一 worktree で版だけを差し替える**。
2. **変異 spec の `category` を推測で書いた。** `CATEGORIES` は
   `frozenset({"negative", "positive", "both-layers"})` の閉集合で、`acceptance-set` 等は拒否される。
3. **anchor 検査 script の誤検出。** III-2 の `new` が `old` の部分文字列なので
   「`new` が既に現物に存在する」と警告したが、変異自体は有効である。

## 受入の非帰属赤 (4 回投げて 4 回目で緑)

| attempt | 結果 | 原因 | 投入時 |
|---|---|---|---|
| 1 | 12 error / 23688 passed | s8c 4 件が `git archive` の 10 秒 timeout、t1259 8 件が F945 同型の 30 秒 timeout | leader 9 本、load 154.27 |
| 2 | 1 error / 23699 passed | `real-repo lock deadline exceeded` (holders 4 プロセス READ) | leader 4 本、load 109.36 |
| 3 | 1 error / 23699 passed | 同上 (同じ node の再赤) | leader 3 本、load 108.18 |
| 4 | **23700 passed / 赤 0** | — | leader 1 本、load 116.70 |

**全件 `TimeoutExpired` / lock deadline であって assertion 失敗ではない。** 本 wave の差分
(checker とそのテスト 2 file) から s8c / t1259 への到達経路はない。単独再走は attempt 1 分が
269 passed、attempt 2/3 分が 218 passed でいずれも **rc=0・非再現**。
`flaky_test_holds.py` への hold 登録は**しなかった** — 一過性の輻輳に対して恒久的に suite を
弱めることになるため。受入が走っていない時点で lock holders が 0 であることを実測し、
**複数 wave の受入が共有 lock を奪い合う外部競合**であって自分の内部競合ではないことを確認した。

## 残したもの (次の一手・裁定パッケージ候補)

- **成長比例は消えていない。定数が下がっただけ。** 一括化後も `_ai_agent_values` の per-commit
  subprocess、隔離 parse の tempdir、実装 path 取得、祖先索引・pickaxe が残る。
  段 3 luna の調査順位は trailer subprocess → 隔離 parse → path 取得 → 祖先索引。
  祖先 bitset は長い履歴でメモリが二次的に増えうる。
- **差分監査 (incremental)** は本 wave の scope 外。D908 が「取り込み差分だけを対象とする独立監査を
  先に設計し、被覆が現行と等価であることを示してから置き換えよ」と条件付きで許可している。
- `_ai_agent_values` の `%(trailers)` 置換は**見送った**。理由は取り分の小ささではなく
  **証明面を拡大しないため**。段 3 sol は `trailer.inject.*` を実 commit へ与えても
  `--parse` と `%(trailers)` に差が出なかったと実測したが、全設定の等価性は未証明である。
- **実 object 欠落 / packed 形態からの復帰は実走確認していない。** 現 fixture の `missing` は
  出力 record の欠落、`log-error` は注入例外であって実 object 欠落ではない (段 6 Q-1)。
- 段 6 R-1: 変異 I-4 の赤は「重複 finding の消失」であって受理集合差ではないため、
  群 I から外して別枠にした。同一 correction OID を二重に含む監査列で「拒否 → 受理」を作る
  fixture は本 wave では足していない。
- 依頼の「受入全走**等**」の全体像は `verbatim/cost-inventory.md`。最大の未解決は
  受入 collection (shard あたり約 55 秒) で、**D1707 でユーザー裁定待ち**である。
