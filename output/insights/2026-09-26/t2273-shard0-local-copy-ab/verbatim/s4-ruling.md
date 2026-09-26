# 段 4 裁定 — [T-2273][T-2560] 可視 output 複製元の局所化

入力: s1-brief.md、codex/s2-plan-out.md、codex/s3-consult-a-out.md (レンズ A、修正後 GO)、codex/s3-consult-b-out.md (レンズ B、修正後 GO)。
裁定 inbox 再走査 (2026-09-23、第 32・33 回): 本件に影響する新裁定なし (T-2845 は「T-2273 が進んでから再提示」のまま)。

## 所見の裁定

| 所見 | 内容 | 裁定 | 採否・扱い |
|---|---|---|---|
| A1 | session snapshot: 写し生成後の実 repo output/ の変更が後続 builder に届かず、三軸 conjunction の拒否経路が消えうる | real (意味の差として) / 受理集合の変化としては refuted | 不採用 (gate を足さない)。理由: (1) 現行でも共有 7 key の builder は約 t=130 秒にほぼ同時に始まり、各自 90〜111 秒かけて Lustre を読むので、「その session の output/ の 1 時点」を読む点は同じで、写しは読む時点を session 内で 1 つに揃えるだけ。(2) 共有 base は key ごとに session で 1 回しか作らない (既存 `get()`) ので、写しの生成後に始まる builder は失敗後の作り直し以外に無い。(3) fixture は production scan の「設計された入力」を与えるもので、実 repo の走行中の変更を検出する役ではない (三軸の未知性負例は fixture 作成後に file を置く形、D2068)。実 repo 全体の scan は `@real-repo` test が直接行う。(4) 受入中に output/ を変えないのは既存の親規律 (failures の supersede 2026-08-26)。仮想リスク向け gate は依頼で scope 外。**是正は code comment 1 つ**: 写しは session で 1 回の snapshot であり、生成後の変更は後続 builder に反映しないことを写し生成メソッドの docstring に書く。 |
| A2 / B1 | 正例が builder の複製元を観測しない (写しを作って ROOT から直接複製する変異を殺せない) | real, must-fix | 採用。plan v2 の §3 |
| A3 | −123.9 秒は事前 staging 済みの対照値で今回方式の期待値ではない | real | 採用 (記述)。brief・insight で「期待値ではない」と明記。写し生成時間・非共有 builder の複製時間を実受入で別記録する件は不採用: 実受入に計器が無く、計器を足すのは scope 外。W_0・O_max・L だけを判定・補助に使う |
| A4 | 変異 5 本の帰属 | real | 採用。下の変異事前登録で経路と kill node を固定 |
| A5 / B6 | brief の数値の出所 (±0.3 秒は検算不能、29,885 は除外前の可視 path 数、310.7〜344.9 は T-2825 B 3 走) | real | 採用 (brief 訂正) |
| A6 / B5 | 完了判定が「land してから測る」と読める | real, must-fix | 採用。下の land 条件を系列投入前に固定 |
| B2 | 専用 lock・marker・残骸処理は必要だが `get()` と同型の短い処理に | real | 採用 |
| B3 | 新規 test は 1 本 + 既存実 builder 検査への assert 1 つで足りる | real | 採用 |
| B4 | `get()` に写しを載せる案は等価でない | real (plan を支持) | 現案を維持 |
| B7 | 計算量見積りの余白が小さい | real | 採用。変異の実測 Elapse を得た時点で見積りを取り直し、2 node 時間以上ならユーザー確認 |

## プラン v2 (実装単位 L: `orchestrator/tests/test_s8b_oracle_driver.py` のみ)

1. `_T080SharedBases` にメソッド `copy_visible_output(self, source_root, destination)` を足す。
   - 写しは `self.parent / "visible-output-cache" / <sha256(str(source_root.resolve()))[:16] 等> / "output"`。完成 marker `ready.json` は `output` の外 (同じ cache dir 直下)、flock は `self.parent / "visible-output-cache" / "<digest>.lock"` 等 (名前は `*/complete.json` の glob に掛からないこと)。
   - lock 下で marker が無ければ残骸を `_t080_remove_tree` で消し、**実関数 `_copy_git_visible_output(source_root, <写し>/output)` をそのまま 1 回呼び**、`ready.pending` → `ready.json` の rename で完成を示す (`get()` と同型)。完成後は lock を離してから `shutil.copytree(<写し>/output, destination)` (既定の copy2、symlinks 既定) で複製する。
   - docstring: 写しは session で 1 回の snapshot であり、生成後の output/ の変更は後続 builder に反映しない (A1 の裁定)。列挙・除外・全件性の検査は実関数が実 repo に対して行う。
2. builder (1458 行) は `_T080_SHARED_BASES` が None でなければ `_T080_SHARED_BASES.copy_visible_output(ROOT, root / "output")`、None なら従来の `_copy_git_visible_output(ROOT, root / "output")`。
3. test (最小):
   - 新規 1 本: 小さい git repo (tracked / modified tracked / untracked / ignored / 実 `_copy_git_visible_output` が除外する receipt を 1 つ) と test 局所の `_T080SharedBases` で `copy_visible_output` を 2 回 (別 destination) 呼ぶ。2 回目の前に source を変更する。検査: (a) 両 destination の regular file 集合と bytes が、変更前に同じ source へ直接 `_copy_git_visible_output` した結果と一致、(b) 実関数の呼出しは 1 回 (`mock.patch.object(..., wraps=...)` で実物へ委譲する観測)、(c) mtime が写しと一致 (`copy_function` の変異を殺す)。
   - 既存 `test_t080_shared_base_builds_real_builder_once_across_processes` に assert を足す: 実 builder が作った base の `output` の複製元が完成した写しであること (`copy_visible_output` の呼出し観測、または写しの marker と `shutil.copytree` 観測)。既存の `(first, second) == (1, 0)` 等の期待値は変えない。
4. 変えないもの: `_copy_git_visible_output`・`_git_visible_output_paths` の本体、全件性検査 2 か所 (1983〜1984 / 1994〜1998 行) と同 test、既存 test の期待値、`get()` の key lock と `complete.json`、`close()`、単独走の経路。

受理・拒否の含意 (DW-S04 の署名形): 禁止 = builder が共有 session 下で実 repo の output/ を直接複製すること、写しを経由せず/写しと異なる集合を渡すこと。通る正例 = 同じ session の 2 回目以降の builder が、1 回目に実関数が作った写しから同じ集合・bytes・mtime を受け取ること。

## 変異の事前登録 (DW-M01、単一理由性は実装後に確認し、成立しなければ再照準して erratum)

| ID | 位置 | 変異 | 期待 kill node |
|---|---|---|---|
| M1 | builder 1458 付近の分岐 | 共有時も `_copy_git_visible_output(ROOT, root / "output")` を直接呼ぶ | `test_t080_shared_base_builds_real_builder_once_across_processes` |
| M2 | `copy_visible_output` の最後の copytree | 複製元を写しでなく `source_root / "output"` にする | 新規 test (2 回目の前に source を変えるので bytes 不一致) |
| M3 | `copy_visible_output` の marker 書込み | `ready.json` を書かない (毎回生成) | 新規 test (実関数の呼出し回数) |
| M4 | 写し→destination の copytree | `copy_function=shutil.copy` | 新規 test (mtime 不一致) |
| M5 | 写し生成 | 実関数の代わりに `shutil.copytree(source_root / "output", <写し>/output)` (全件、ignored も含む) | 新規 test (ignored file が集合に入る) |

## 計測の事前登録 (系列投入前に固定)

1. 比較: A = 測定時 local main の clean worktree (SHA 固定)、B = wave tip (= A + 実装差分、clean、SHA 固定)。記録 commit は測定後。
2. 順序: `A,B / B,A / A,B` の隣接 3 対を逐次投入。測定中は自分の他 job を走らせない (D357)。門番 = 他 session の受入 leader ≤ 1 ∧ load1 ≤ 60 (T-2825 と同じ)。温めは両 tree 同じ手順 (T-2825 の warm に準じる)。
3. 有効性: 各走の 3 shard 緑、HEAD・clean の前後一致、両 tree の collection 一致。infra 由来の赤は本文で分類しその対全体を同順序で取り直す。実装由来の赤は捨てず、直して系列を最初からやり直す。
4. 判定量: 対差 Δi = W_0(Ai) − W_0(Bi) (shard-0 JUnit wall)、対率 ri = Δi / W_0(Ai)。対差の中央値と対率の中央値を別々に報告。
5. **land 条件:** 3 対すべて Δi > 0 かつ対率中央値 ≥ 10 % (10 % は T-2825 の運用閾値で、D357 の 1 走比較の閾値に揃えたもの。統計的有意差ではない)。満たせば land。満たさない (方向不一致・対率中央値 10 % 未満・判定不能) なら性能改善として land せず、結果を記録してユーザーへ返す。
6. 5 分目標は別判定: B の W_max (3 shard の最大) 3 走の中央値 ≤ 300 秒。land 条件を満たし 5 分未達なら「未達、段階的改善として land」と記録する。
7. 補助量 (判定に使わない): W_max と最遅 shard、shard-0 の O_max・L・O_max − L、最大占有 worker の item 列。−123.9 秒 (診断の対照 X) は今回方式の期待値として使わない。
8. 限界として書くこと: 固定 2 tree は同一 node・同一 allocation ではない。同時刻性は隣接逐次投入による。

## 段 5 の分割

- 単位 L (実装): 上のプラン v2。Codex author、子 worktree。
- 単位 P (計測 probe): T-2825 の probe (run-series.sh / run-measure.sh / run-warm.sh / t2825_ab_analyze.py / gate.conf) を本 wave 用に改作。job dir・slug を替え、台帳固有の検査 (台帳 hash・予測負荷・shard 移動・旧 L 候補) を集計器から外し、上の事前登録 (順序、判定、land 条件、5 分別判定) を出力する。Codex author、子 worktree の repo 外に出す前提で worktree 内の scratch dir (`probe-t2273lc/`) に書かせ、親が job dir へ退避。repo には入れない。
- 所有は素集合 (L = test file 1 つ、P = probe dir のみ)。
