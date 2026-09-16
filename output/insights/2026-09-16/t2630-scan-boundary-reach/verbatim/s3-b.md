## 所見 (real 候補)

**plan の spec・patch 構文は整合している。主な不足は、失敗後の再開、計算ノードへの出力先伝達、二 branch の監査証拠の分離である。** pytest・configure・前処理・コンパイルは実走していない。

**B-1 — 再投入時に attempt 番号と path を変えるだけでは回復できない。**

- **根拠:** `s2-plan-out.md:286`、`tools/mutation_harness.py:974–1008, 2782–2788`、`docs/dev-wave/mutation.md:44–48`。
- **real と主張する理由:** `--resume` は既存 sidecar の内容を要求し、未完了 attempt があれば拒否する。また、`PARSE_ERROR` は履歴へ移して再走するが、`TIMEOUT` と `MISMATCH` は終端記録として保持する。「timeout 後に resume すれば当該変異を再走する」という回復は成立しない。
- **是正案（scope 内）:** 回復手順を結果別に追記する。resume では旧 sidecar を新 path に複写し、HEAD/spec/runner 束縛を維持する。終端 TIMEOUT の再測定は旧台帳を保存した別 run とする。orphan は後述の既存復旧順序に従う。harness の変更は不要。

**B-2 — job 外部証拠 directory と scratch の伝達方法が未確定。**

- **根拠:** plan の「保存する証拠」、`tools/pegasus/dispatch_compute.py:118–132, 1442–1453, 1622–1633, 3470–3473`、`orchestrator/campaign/patchharness.py:361`。
- **real と主張する理由:** tests の request allowlist に独自の証拠出力先変数や `TMPDIR` はない。`env_mode="inherit"` が継承するのは**計算ノードの job 環境**であり、submitter の全環境を転送する契約ではない。さらに `checkout()` は clone の配置場所とは独立に、`TMPDIR` または `/tmp` に worktree を作る。親の `$JOB` やローカル一時 path に依存すると、出力先不明・誤配置・終了後の証拠消失が起こり得る。
- **是正案（scope 内）:** probe 内で共有 filesystem 上の証拠保存先を確定し、run ごとの一意 directory を作る方法を明記する。compute 内で scratch と `TMPDIR` を確定し、hostname・実 path・filesystem を記録する。allowlist の変更は不要。

**B-3 — probe tip の監査と wave tip の受入を混同できる余地が残る。**

- **根拠:** `s1-brief.md:25–28`、`tools/mutation_harness.py:775–847`、`tools/dev_wave_land.py:2962–2974, 3038–3058, 5107`。
- **real と主張する理由:** mutation 台帳は probe HEAD に束縛される。一方、land は tested wave tip と provenance・acceptance receipt の一致を要求する。probe の4 node PASSED は docs wave の受入証拠にはならない。また probe commit の後で test を削除して wave を作ると、最終差分が docs のみでも probe commit が land 履歴に入る。
- **是正案（scope 内）:** probe と wave を共通の main SHA から分岐させ、probe commit を wave の祖先へ入れない。probe tip の provenance と、最終 wave tip の docs/checker/受入を別々に記録する。insight に両 SHA とそれぞれの証拠を対応付ける。

## harness argv と spec の逐一検証

### spec

`tools/mutation_harness.py:532–650` と一致する。

| 対象 | 検証結果 |
|---|---|
| root | `schema, estimated_run_seconds, timeout_seconds, hang_timeout_seconds, mutations` の5キー |
| mutation | `id, category, replacements, expected_nodes, expected_status, hang_risk` の6キー |
| replacement | `file, old, new` の3キー |
| M0 | `SURVIVED` と `expected_nodes=[]` は正しい |
| KILLED 期待 | 非空の完全 node 集合が必要 |
| category | 指定値は許容される。ただし到達・原因を証明する値ではない |
| 数値 | 240/8100/3000 は正数。240 は1 run 当たり |
| node 名 | `N1a` 等を残さず完全名へ展開する必要がある |

`_normalize_node` は repo 絶対 prefix・先頭 `./`・区切りを正規化する。略称から完全名への展開はしない。比較時には `_match_key` が xdist group suffix を処理する（`mutation_harness.py:1230–1250`）。

### anchor と hunk

現物 bytes を読み、plan の replacement を**変異ごとに元 patch から累積適用**した。

| 変異 | 各 old の累積 count | `git apply --numstat -` |
|---|---:|---:|
| M0 | 1 | rc=0 |
| M1 | 1, 1 | rc=0 |
| M2 | 1, 1, 1 | rc=0 |
| M3a | 1, 1 | rc=0 |
| M3b | 1, 1, 1 | rc=0 |
| M4 | 1 | rc=0 |
| M6 | 1, 1, 1 | rc=0 |

H1/H2/TOP/BRANCH/ELSE/END は単独でも各1箇所だった。根拠は `patches/silo-backoff-fixed.patch:32,34,48,69,71,77` と `mutation_harness.py:1076–1097`。

- M1 の第2 hunk 新行数30、M3a の31は整合する。
- M2 の第1 hunk 新行数16、M3b/M6 の17は整合する。
- M4 は旧7行・新9行で整合する。
- 未変異 patch は、現 checkout の pin `511c9538…` に対する `git apply --check` が **rc=0**。

M2/M3b/M6 の第2 hunk `+c` を101/102へ動かす計算は正しい。ただし、**動かさなければ git apply が必ず拒否するという必要性までは確認できていない**。変異版の context 適合と、new start 据え置き時の挙動は未検証として残す。numstat 成功を適用成功へ読み替えない。

### argv

`mutation_harness.py:3006–3030`、`run_tests.py:1343–1373` と照合した。

| token / 引数 | 判定・条件 |
|---|---|
| `env`＋3つの `IZANAGI_DISPATCH_*_OVERRIDE` | すべて実在。WALLTIME も有効 |
| `python3 "$REPO/tools/mutation_harness.py"` | 有効 |
| `--repo "$REPO"` | clean な probe tip の別 worktree が必要 |
| `--spec …` | checkout 外の通常 file |
| `--expected-spec-sha256 …` | 最終 spec bytes の SHA が必要 |
| `--out …` | checkout 外。fresh run では既存出力不可 |
| `--attempt-out … --wrapper-attempt 1` | 対指定は正しい。回復条件は B-1 |
| `--runner-mode dispatch` | 正しい |
| `--detached` | 自己申告。実際の detach はしない |
| `--` | runner argv の区切りとして正しい |
| `python3 tools/run_tests.py` | harness と同一 executable、固定 HEAD の runner が必要 |
| `-rf` | FAILED summary の抽出に適合 |
| probe file | 固定 HEAD に tracked である必要がある |
| `-n 0` | serial 実行指定として適合 |
| `--force-dispatch` | runner の指定として適合 |

dispatch 既定値は walltime 3600秒、queue-wait 900秒、grace 300秒（`dispatch_compute.py:67–69`）。plan は後二者を3600秒・600秒へ変更する。8100秒はその envelope に余裕を持つ。

collection は別 dispatch で、計 **9 request**。collection の生成経路は queue/grace を渡すが WALLTIME override は直接渡さない。今回は指定値と既定値がともに1時間なので不一致は生じない（`mutation_harness.py:1421–1492`）。

8 run の1920秒は処理時間の仮置きである。各 run が240秒、各 queue 待ちが3600秒なら、collection を除いても **8時間32分**。全9 request に8100秒ずつ確保する規模なら約20時間15分となる。生死実験・再走は別枠である。

## 計算ノード実行の前提

- **cwd:** 計算ノード側も `repo_root`。repo 全体をローカル scratch へ複製する dispatch ではない（`dispatch_compute.py:1622,1671`）。
- **compiler:** `compilers_for_current_site()` は compute で `gcc/g++`、それ以外では既定 compiler を返す。g++ 11.4.0 という版まで保証しない（`buildcache.py:1861–1865`）。
- **git:** 今回確認できたのは login の `/usr/bin/git`。compute の git 可用性は未確認。
- **scratch:** conftest は TMPDIR を設定しない。未設定なら `checkout()` は `/tmp` を使う。現在の compute filesystem は実走時に確認する（`conftest.py:1–26`）。
- **clone 負担:** 現 object store は loose 25個・132 KiB、packed 22,119個・6,931 KiB、3 pack。巨大な object 転送ではないが、checkout の小 file I/O と configure 時間をこの容量から秒単位には推定できない。
- **副作用:** `worktree add/remove` が書く先は独立 clone の `.git`。通常終了では remove/prune と `_worktree_paths` による登録残留検査がある。ただし強制終了では finally が走らず、clone・worktree・lock file が残り得る（`patchharness.py:346–383`）。

**未登録 node は単独走を直ちには壊さない。** collection hook は登録済み node だけに access/group を付ける。未登録 node も protocol では `(node_id, None)` を `_PYTEST_NODE` に設定される。独立 clone は common-dir の path/inode が異なるので guard を通る（`conftest.py:2145–2152,2227–2239`、`patchharness.py:315–328`）。

確認した serialization メタテストには、新規 file が存在するだけで全件登録を要求する根拠は見つからなかった。既存 fixture consumer の閉包・golden は検査する。probe 単独 runner はそのメタテストを実行しないため、単独成功から全走成功は推論できない。

**FAILED 署名の設計は成立する。** 観測例外を保存し、各 test の call 内で例外化すれば FAILED になる。fixture setup/teardown、import、collection で漏れた例外は別である。`_failed_nodes` が読むのは `FAILED ` 行だけなので、`ERROR` だけなら非ゼロ rc・node 空となり PARSE_ERROR になる（`mutation_harness.py:1253–1268,2083–2096`）。共有 helper の一括失敗で全 node を同じ原因にしないよう、結果は genome・reference/current・観測段階ごとに保持する必要がある。

**cache 直指しは条件付きで支持する。**

- masstree の source 内生成 command は build 時の custom command（`ThirdParty.cmake:66–77`）。
- mimalloc の `configure_file(mimalloc.pc.in mimalloc.pc @ONLY)` は binary 側出力（cache 内 `mimalloc/CMakeLists.txt:735`）。
- googletest の package 生成先も binary 側で、当設定では `INSTALL_GTEST=OFF`（cache 内 `googletest/googletest/CMakeLists.txt:90–104`）。

確認した経路に、configure だけで cache source を書く処理は見つからなかった。ただし scratch の `FETCHCONTENT_BASE_DIR` だけでは masstree の build 時書き込みを移せない。plan の「build しない」「既存 config.h を使う」「前後 inventory/hash を採る」は維持すべきである。

walltime 終了は、harness 自身の待機 timeout と同義ではない。dispatcher が異常 rc を返して終了すれば PARSE_ERROR になり得る。orphan 発生時は **対象 job の不在／終端確認 → dirty path 復元 → clean/HEAD 確認 → hold/sidecar 処理**の順であり、先に hold を消して再走しない（`mutation_harness.py:2848–2884`）。

## 二 branch 構成と provenance

B-3 を満たせば両立できる。

- probe `.py` commit は実装面であり、Codex `role=author` が必要。probe-only は免除されない（`docs/ai-provenance.md:44–54`）。
- wave の docs commit にも適切な AI-Agent trailer を付ける。
- insight の `.diff.txt` と verbatim `.md` は、この配置では実装 suffix に該当しない。`.diff` / `.patch` は該当する（`check_ai_provenance.py:75–81,1583–1596`）。
- wave の provenance 監査は、非祖先の probe branch を監査した証拠にはならない。
- docs checker や受入全走の成功も、probe 台帳の実測内容を自動的に保証しない。

probe branch は証拠参照のため保持し、tip SHA を insight に固定するのが妥当。bundle は長期保存の選択肢だが必須とは確認できない。作る場合も台帳の canonical stdout・spec・artifact の保存を代替しない。branch 名だけに依存した保存は避ける。

## 親 brief への反論

- **P1:** 独立 clone が shared-checkout guard の対象外という説明は支持する。ただし実共有 submoduleを clone source として読む以上、brief の「実共有 submodule に触れない」は「書き込まない」と明確化した方がよい（`s1-brief.md:10,22`）。
- **P2:** 「build しない → cache は汚れない」という一般的な断定は強すぎる。今回確認した CMake 経路と前後観測に限定する（`s1-brief.md:11,52`）。
- **P3:** 署名だけでは環境失敗・前処理差・実行可能な別挙動を識別できない。段2の原因別証拠保存は必要である。
- **P4:** template carrier は今回の全 anchor と構文検査を通る。採用を否定する根拠はない。ただし変異版の pin 適用確認は残る。
- **P5:** 二 branch は成立するが、履歴と受入証拠を分ける B-3 が必要。
- **成果物影響:** `s1-brief.md:18` の certified 結果・binary・receipt 継承は、この probe が直接観測する範囲を超える。実測できた identity 受理と TU 差、消費側への影響推論を分けて記載する。
- **「許された variant」:** patch 自身が macro 定義追加を coder 編集契約で禁止している（`silo-backoff-fixed.patch:62–67`）。名指した digest/TRACE 検査の通過を、編集契約や pipeline 全体の受理と同一視できない。

## 総括

**B-1〜B-3 を実行手順へ補えば、既存機構だけで進められる設計である。** gate の変更・新設は不要。

今回確認した成功は、全7変異の累積 anchor 一意性と numstat、未変異 patch の apply-check に限る。到達、pytest 緑、cache 不変、変異版 apply-check は未確認である。

変異版の一括 apply-check は PreToolUse の `guard_bash` が「保護 path と不透明構文の同居を分類不能」として拒否した。回避せず、許可された読み取り・メモリ内置換・numstat に検査を限定した。