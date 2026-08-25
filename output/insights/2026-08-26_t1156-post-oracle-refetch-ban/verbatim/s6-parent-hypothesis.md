# 親が実装差分を読んで立てた仮説 (段 6 レビューの攻撃対象)

**この文書は確定事実ではない。親の推論であり、誤っている可能性がある。子は反証を優先して探すこと。**

## 仮説 H1 — 新しい capability は fail-open で落ちる

`s8b_floor_campaign.py` の新規箇所は次の条件で capability を渡している。

```python
if build_fn is buildcache.build_v2:
    build_kwargs["post_oracle_dependency_binding"] = ...
```

**この条件が偽になると、flag も事前検査も実効値検査も identity policy も一切効かないまま
build が進む。** 拒否されるのではなく、禁止が黙って消える。親の判断ではこれは fail-open であり、
ユーザーが要求した fail-closed に反する。

正しい形は「sort_best cell かつ依存 binding があるなら、capability が付くか、さもなくば build を
拒否する」であるはずだ。子はこの判断が正しいかを検算し、正しいなら file:line で修正位置を示せ。

**反証の余地:** production の official core が `build_fn` を `buildcache.build_v2` に固定しており、
この条件が production で偽になりえないなら、fail-open ではない可能性がある。
固定が本当に閉じているかを実コードで確かめよ。

## 仮説 H2 — capability の発火条件 (oracle PASS) が production で成立しない可能性がある

親が読んだ範囲では次の連鎖が成立するように見える。子はこれを検算せよ。

1. floor は `oracle_dependency_root = <base>/masstree-src` を SWO oracle へ渡す
   (`s8b_floor_campaign.py` の `floor_prepare`、`s1_direct_comparison.py:682-693`)。
2. oracle は `_verify_dependency_root()` (`sort_swo_oracle.py:1796`) でその root に
   `SHA256SUMS` を要求し、**宣言された file 集合と実在 regular file 集合の exact 一致**
   (`declared != actual` で拒否、同 file 1829-1831) と、manifest 本体 hash が定数
   `DEPENDENCY_MANIFEST_SHA256` (同 file 81) と一致することを要求する。
3. `<base>/masstree-src` は git checkout であり (`s8b_floor_campaign.py:2840-2880` が
   `git rev-parse` で top-level と HEAD を検査している)、prebuild 後は `config.h`・
   `libkohler_masstree_json.a`・`.o` 群も持つ。`.git` 配下の regular file も `os.walk` に
   数えられる (`_dependency_file_inventory` は除外していない)。
4. `SHA256SUMS` を production 側で生成する経路を親は見つけられなかった
   (`git grep SHA256SUMS -- tools docs` が 0 件)。実在する `SHA256SUMS` は
   `orchestrator/tests/fixtures/sort_swo_masstree/SHA256SUMS` (91 entry) だけである。

**もし 1〜4 が正しいなら、production の floor `sort_best` で oracle は PASS せず、
新 capability は一度も渡らない。** すなわち禁止は production で恒真になる。

**反証の余地 (子はここを重点的に探せ):**

- Pegasus 側の staging 手順が repo 外で `SHA256SUMS` を配置している可能性。
- `dependency_root` が `<base>/masstree-src` 以外へ解決される経路の存在。
- `_dependency_file_inventory` が `.git` を実際には拾わない、または staged root が
  git checkout でない可能性。
- floor `sort_best` の production 実走記録 (durable record / 台帳) が存在し、
  oracle PASS が実際に出ている証拠。

**H2 が real なら**、これは実装の欠陥ではなく**発火条件の欠陥**である。その場合の
親の想定する扱いは次のとおりで、子はこれも攻撃してよい。

- 禁止そのものは正しいので実装は残す。
- ただし **H1 の fail-closed 化を必須にする** — capability が付かない sort_best build を
  拒否すれば、oracle が PASS しない間は build が止まる (安全側) のであって、
  禁止が黙って消えることはなくなる。
- oracle 依存検証が production で成立しない件は本 wave の scope 外の別欠陥として
  裁定パッケージへ返す。

## 仮説 H3 — dispatch の副作用ファイル

焦点走の dispatch が worktree 内へ untracked file を作った
(`output/pegasus-dispatch/orphan-holds/*.json`)。これは実装差分ではなく実行副作用である。
親が commit 前に扱う。子は実装差分の一部と数えないこと。
