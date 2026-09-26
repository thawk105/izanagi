## プラン

1. **写しの生成と接続。** [`test_s8b_oracle_driver.py:920`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:920) の `_T080SharedBases` に、完成した可視 output の写しを返すメソッドを追加する。配置は `self.parent / "visible-output-cache" / "output"` とし、同じ cache ディレクトリ内の `ready.json` を完成 marker、`self.parent / "visible-output-cache.lock"` を flock 対象にする。lock 下で marker がなければ `_t080_remove_tree` で未完成の cache を消し、実関数 `_copy_git_visible_output(ROOT, cache / "output")` を一度呼び、`ready.pending` の rename で完成を示す。marker は複製対象の `output` の外に置く。異なる base key の `get()` が同時に入っても、写しの生成だけをこの lock で直列化し、完成後の局所複製中は lock を保持しない。`get()` の key 別 lock と `complete.json` はそのまま残す。cache は [`close():929–942`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:929) が `self.parent` ごと削除する。builder の [`1458 行`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1458) は、共有 bases があれば完成した `cache / "output"` から `shutil.copytree`、なければ従来の直接 `_copy_git_visible_output` とする。列挙・複製関数の本体は変更しない。

2. **既存経路への波及。** `_T080_SHARED_BASES is None` の単独走は直接複製を続ける。[`t080_shared_cache_probe:1036–1045`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1036) が bases を差し替えた間は、その `bases.parent` に独立した写しを作る。実 builder を呼ぶ非共有検査 [`1079–1099 行`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1079) では Lustre からの生成が一回残る。`t080_small_cache_builder` は実 builder 自体を mock するため写しを作らず、既存期待値は変わらない。新しい lock は base key lock の内側で builder が実行されたときだけ取得する。したがって全 `LOCK_EX` を観測する [`test_t080_shared_base_waits_for_builder_lock:1155–1204`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1155) にも、mock builder 経路で余分な lock 観測を生じさせない。

3. **複製結果。** 写し生成と builder への複製はどちらも標準の `shutil.copytree`、すなわち通常 file と directory に `copy2` を使う。生成時点の mode・mtime は二段目にも引き継がれる。元関数が選ぶのは regular file で、最終要素の symlink は除外するため、写しの `output` 内に複製対象 symlink はない。fixture のそれ以外の symlink を扱う [`base→test の `symlinks=True`:1032`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1032) は変更しない。`_copy_git_visible_output` の戻り値は現行 builder と同じく使わない。写しのディレクトリそのものを複製元とし、別の visible 集合や index は作らない。inode・ctime と、生成後に元 tree が変わった場合の metadata は同一を主張しない。

4. **作業木と時刻。** [`_git_visible_output_paths:814–844`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:814) は tracked の index と untracked の作業木を列挙し、[`_copy_git_visible_output:847–899`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:847) は作業木の bytes を読む。よって初回生成時に可視な modified tracked と untracked は従来どおり含む。時刻上の差は、初回生成後に行われる file の追加・削除、bytes・mode・mtime の変更、regular file／symlink の変更、index・ignore 規則の変更が後続 builder に反映されないこと。従来は各 builder がそれぞれ列挙・検査・読取りを行い、途中で tracked file が消えれば後続 builder が失敗しえた。新経路では初回生成が成功した後、後続 builder はその時点の写しを使う。これは session 内 snapshot という仕様上の時刻差として明記する。

5. **最小テストと事前登録する変異。** 新規正例は一〜二本に絞る。一つは小さい Git source に modified tracked、untracked、ignored、symlink を置き、共有 bases の写しから二回複製する。二回目の前に source を変更し、初回の集合・bytes・mode・mtime が両複製先で一致すること、実 `_copy_git_visible_output` の呼出しが一回であることを確認する。もう一つは既存の実 builder 検査 [`1079 行`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1079) に「実 builder が局所 cache を完成させた」assert を加え、接続を確認する。既存の `(1, 0)` などの期待値は変えない。

   | 変異位置 | 変異 | 期待 kill node・単一理由 |
   |---|---|---|
   | builder 1458 | 共有時も `ROOT` から直接複製 | 実 builder 検査。cache marker が作られない |
   | 写し生成メソッド | 完成 marker を書かない | 小 Git 正例。二回目にも元関数が呼ばれる |
   | builder 1458 | 写しを作るが複製元を `ROOT / "output"` にする | 小 Git 正例を builder 経由に接続した場合、変更後 bytes が二回目に現れる。helper 単体の試験だけでは殺せないため、実 builder の複製元観測も必要 |
   | 写し生成メソッド | untracked／modified bytes を落とす別のコピーにする | 小 Git 正例。期待集合または bytes の不一致 |
   | 写し→builder の `copytree` | `copy_function=shutil.copy` にする | 小 Git 正例。mode・mtime の不一致 |

   三番目の変異を確実に殺すには、正例を単なる cache メソッド直呼びで終えず、builder の複製元を観測すること。実 builder 検査で `shutil.copytree` の当該呼出し元が `bases.parent / "visible-output-cache" / "output"` であることを確認すれば、他層の検査結果に依存しない。四番目も、元関数を stub に置き換えず実関数を使う。

6. **静的な波及。** [`1392–1434 行の consumer AST 検査`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1392) は `_t080_stub_free_e2e_repo` と `_build_t080_active_v2_repo` の直接呼出しを数える。追加メソッドやテストからこの二名を直接呼ばなければ inventory は変わらない。`bases.parent.glob("*/complete.json")` を使う [`1145、1159 行`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1145) に cache marker が混ざらないよう、名前は `ready.json` とする。cleanup、key identity、単独走、境界拒否の既存テストと、[`1899–1998 行の全件性検査`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1899) の期待値は据え置く。

7. **効果の見込み。** 共有七 key の builder について、実 repo からの可視 output 複製は最大七回から一回になり、残りは node-local の写しから読む。第4回診断の対照一対は shard-0 の `W_0` が 123.9 秒短く、この方向の効果を支持する。一方、今回の方式で**一回の写しを Lustre から作る時間は未測定**であり、非共有検査の独立した一回も残る。診断の 43.9 秒は git clone を使った staging で、今回の費用へ代入できない。実装後、brief の同時刻 A/B 隣接三対の実受入で対差を記録するまでは、改善秒数や五分以内達成を確定しない。

## brief への異議

(P1)・(P2)・(P4) は上記の形で採用できる。(P3) の「読む時刻だけ」は集合・bytes に限れば要点を捉えるが、初回後の消失で後続 builder が失敗するかどうか、mode・mtime にも差が及ぶため、上記 4 のように具体化する。(P5) は独立した test 局所 bases の一回を残す扱いが簡潔で、共有 session 側へ寄せる必要はない。計測計画と不変条件への異議はない。

## 総括

変更は原則 [`test_s8b_oracle_driver.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py) 一ファイルに収まる。既存の可視集合列挙、全件性検査、受理集合を保ち、共有 builder の複製元だけを session 内の完成済み写しへ切り替える。今回は read-only の静的検討であり、テスト実測と効果判定は親段で行う。