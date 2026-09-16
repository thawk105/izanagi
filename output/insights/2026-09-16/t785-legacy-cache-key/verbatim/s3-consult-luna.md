## 所見

以下、`plan` は指定の `s2-plan.md`、`brief` は指定の `s1-brief.md`、コードの相対パスは指定 repo root 基準。静的検査と在庫・Git 履歴の読取を行った。ファイル編集、pytest、probe、実コンパイルは実施していない。

**L-1・MUST — 親の実編集手順は、提示された Bash 制約ではそのまま実行できない。**

- **主張:** plan:114 の shell 関数＋heredoc、:133 の複数コマンドを含む検査関数、:178 の復元照合 heredoc は、単文実行の制約に適合しない。:106 の変数と関数を後続の Bash 呼出へ保持する前提も成立が確認されていない。:173 の `try/finally`／trap は要求だけで、実行可能な手順になっていない。
- **根拠:** plan:100–188。`docs/dev-wave/operations.md:144–151` は diff、`git checkout --`、復元 bytes の commit 照合を要求する。
- **最小修正:** 親の許可された編集手段で DEFAULT の一行を編集し、検査・probe・復元をそれぞれ独立した単文で実行する。引数には絶対パスを渡す。途中失敗時の復元も具体的な単文列にする。汎用 wrapper の追加は不要。
- **成果物影響:** 手順が拒否されると修正前後 JSON が欠落し、再現・修正済みという台帳記録を支える証拠が得られない。

**L-2・MUST — seed 相から hit 相への直接再編集は、DW-O19 の変異前 clean 要求を満たさない。**

- **主張:** plan:156 で `gcc-12/g++-12` に変異した後、復元せず :163 で `gcc/g++` に再編集している。二つ目の変異前には tracked diff が残る。また :102 の `git status --short` は表示するだけで、規定の `--porcelain` 空確認が明示されていない。
- **根拠:** plan:156–176、`docs/dev-wave/operations.md:146–151`。
- **最小修正:** seed 後に単一変異を確認→`git checkout --`→commit bytes 照合→`--porcelain` 空確認→新既定へ変異→hit 相、という順にする。cache と seed JSON は repo 外に保持できる。
- **整合している部分:** plan の HEAD との byte 比較は単一変異の確認として有効。:191 の「F を含む HEAD」を基準にする方針も正しい。ただし本走基準は単なる commit 済みではなく、DW-O19 の**統合 commit 後**と明記する。
- **成果物影響:** 修正前後の観測がどの commit と一時変異に対応するかという、再現台帳の参照を確定できなくなる。

**L-3・MUST — 「衝突条件不成立」を記録した後の分岐が未定義。偽 hit 未再現なら F へ進めない。**

- **主張:** plan:94 は digest／receipt 不一致を記録するとしているが、:355 はその場合の停止・別組試行を定めていない。`cached=False` だけを修正成功と扱うと、もともと衝突しない組を測ることになる。
- **根拠:** `source_digest.py:2408–2410`、`:2425`、`build_admission.py:657–675`、`buildcache.py:640–641`。source bytes digest は admission receipt を経由して key に入る。brief:26 の訂正は正しい。
- **必要な分岐:**  
  1. 前処理／admission が失敗したら「再現前提未成立」として復元する。  
  2. receipt が異なったら「この組では衝突条件不成立」。別の利用可能な**異なる compiler** の組を試す場合も、同じ実 evidence・実 admission を維持する。  
  3. 修正前に key 同一、`cached=True`、seed binary 同一、報告 compiler の変更を確認できた組だけで F と修正後比較を行う。  
  4. 再現できる組がなければ、今回の依頼では**修正しない**。未再現という結果と不足条件を返す。
- **成果物影響:** この分岐がないと、非衝突による miss を修正効果と誤帰属したレポート・変異台帳になる。

**L-4・SHOULD — production caller 表で pipeline の legacy と build_v2 を取り違えている。s1 の「stock control」も誤記。**

- **主張:** plan:8、:284 と brief:10 の `pipeline.py:1945→:2002` は同じ compiler 伝播経路ではない。
- **根拠:** `pipeline.py:1938–1963` の compiler を含む `common` は `env_contract is not None` の分岐。`:1993–2008` の legacy 呼出は `common is None` であり、**cc/cxx を渡していない**。compiler を含む common は :2010 以降の build_v2 に渡る。一方、evidence は :1790–1809 で site 等から解決した cxx を使う。
- **追加の訂正:** brief:5 の s1「stock control」は、引用された `s1_verify_extime_calibration.py:390` の説明として不正確。`:376–395` は patch・condition gate・generator receipt を伴う生成物の build である。
- **caller 側変更の判定:** 本件の key 衝突を閉じるには中央の `cache_key` 修正で足りる。これらを理由に caller の compiler 解決まで変更する必要はない。s1/s2/s3/s5 の evidence 側既定が `g++-13` のままという別問題も、今回の修正必須事項にはしない。ただし probe が各 CLI 全体の動作を再現したとは書けない。
- **成果物影響:** 修正そのものの効果は変わらないが、影響を受ける caller と compiler provenance の説明がレポート上で誤る。

**L-5・SHOULD — compiler 在庫と probe 完走可能性を分ける。g++-9 と g++-11 は無条件の代替組にならない。**

- **根拠と静的判定:**

| 経路 | 判定 |
|---|---|
| `assert_includes_match_head` | `source_digest.py:2139–2148` は include 行と pinned source の比較。compiler は起動しない。 |
| `assert_conditional_macros_covered` | `:1894–1899` で全3 source を検査し、`:1707–1712` の実 compiler 照会が残る。 |
| `compute`／`baseline` | `:2111–2114`、`:2223–2227` から `-E -P -nostdinc -Werror=undef` を使う。 |
| hit／fresh の source 再検査 | `buildcache.py:3490`、`:3555`、`:3645–3648`。probe 入口と同じ cxx が必要。 |
| trace diff | `buildcache.py:3670–3685`、`source_digest.py:2196–2200`。TRACE 両値の前処理が残る。 |
| trace symbol | `buildcache.py:3770–3777` は `nm -C /proc/self/fd/...` と `pass_fds`。`_run` 差し替えでは消えない。 |
| 重処理拒否 | 調査した legacy 経路では `require_heavy_work_site` 呼出は `_run` 内の :3796。`jobs=1` の解決は :1896–1897 で返る。差し替え以外に同拒否が残る箇所は見つからない。 |

- **compiler 別:** `g++-12` と `g++`／`g++-11` について、対象ソースの include は除去され、条件マクロには CMake の供給値がある。`MQLOCK` も `source_digest.py:357` の既知不在集合に含まれる。今回の clean source に、静的に特定できる `-Werror=undef`／`-nostdinc` の停止原因は見つからなかった。ただし前処理出力の一致と完走は未実測。
- **g++-9:** `source_digest.py:370` の固定フラグは `-std=c++20`。GCC 9 の C++20 草案指定は `-std=c++2a` であり、在庫があってもこの probe の無変更候補として扱えない（ローカル資料 `/usr/share/doc/gcc-9/NEWS.html:584–586`）。このためだけに production の BUILD_FLAGS を変えるのは scope 外。
- **g++ と g++-11:** 両方とも実体は `/usr/bin/x86_64-linux-gnu-g++-11`。この二名の比較では「別 compiler の binary」を実証できない。
- **極小 C++:** plan:69 のコンパイルには `-nostdinc` を付けないので、source digest の include 除去と混同してはいけない。`nm`、`readelf` は在るが、ELF 作成と検査の成功は未確認。
- **成果物影響:** compiler 起動失敗や同一 compiler の別名比較を、偽 hit の再現／修正証拠として数えると台帳の受理対象が変わる。

**L-6・NIT — 一箇所の行番号がずれている。他の主要参照は以下のとおり検算した。**

plan:45 の `buildcache.py:3644` は閉じ括弧。正しくは **:3645–3646**。説明する引数 `cxx=cxx` 自体は正しい。成果物の値・受理集合への影響はなく、参照位置だけの問題。

| plan の参照 | 現物との照合 |
|---|---|
| `buildcache.py:622` | DEFAULT 定義、一致 |
| `:627` | `cache_key` の cc/cxx 定義時既定、一致 |
| `:635–639` | docstring と省略条件、差分対象は一致 |
| `:3410–3411` | `build` と cc/cxx 定義時既定、一致 |
| `:3474–3512` | legacy entry の hit 分岐、一致 |
| `:3585` | publish 直前の既存 entry 拒否、一致 |
| `:3795–3796` | configure/build の重処理拒否、一致 |
| `:1861–1865` | compute のみ gcc/g++、一致 |
| `:1319–1328` | v2 の cc/cxx・toolchain hash、一致 |
| `build_admission.py:627` | trigger predicate 検査、一致 |
| `:633–635` | stock の3条件、一致 |
| `:633–675` | stock 分岐から receipt 生成、一致 |
| `source_digest.py:249–260` | receipt に source bytes digest を含む、一致 |
| `:2307–2334` | tracked status、untracked 除外、一致 |
| `pin.py:28` | `CURRENT_PIN="511c953"`、一致 |
| `test_campaign.py:3184–3202` | compiler 名分離テスト、一致 |
| `:11040–11042` | `_T816_GOLDEN_CK0`、1要素、一致 |
| `:11177–11197`／`:11193` | golden 検証／assert、一致 |
| `test_build_site_gate.py:290–331` | `_fake_legacy_build`、一致 |
| `s1:390` | compiler 省略は一致。stock という説明は L-4 |
| `s2:354–355` | 両 build とも compiler 省略、一致 |
| `s3:258` | compiler 省略、一致 |
| `s5:293` | compiler 省略、一致 |
| `pipeline:1945→2002` | **伝播関係が不一致。L-4** |
| `backoff_profile:273,307→857` | runtime.cc/cxx を渡す、一致 |
| `between_run_floor:316–324` | Pegasus 分岐のみ明示 compiler、一致 |
| `pegasus_floor_scoping:214→218` | 解決組を明示、一致 |
| `t2187:3925,4346` | 直接 key 呼出、cc/cxx 明示、一致 |
| `t2187:3941,4334` | legacy build、同じ cc/cxx 明示、一致 |
| `t1683:248` | legacy build、cc/cxx 明示、一致 |
| `test_t2000_legacy_build_probe:1876` | 手動 probe の legacy build、一致 |
| `test_buildcache_v2:2302,2879` | 指定された両テスト名、一致 |
| `s8b_floor_campaign:4694,7340–7342` | build_v2 選択、一致 |
| `s8b_floor_campaign:20` | 古い legacy 記述が残るという指摘、一致 |
| `package.md:91` | M4 節の位置、一致 |

probe の提示呼出についても、`build` の `cache_root`、`ccbench_dir`、`jobs`、`admission`、`build_context`、`source_evidence`、`resolve_evidence` の `cxx`、`build_run_context` の `generator_id`、`derive_build_admission(context, evidence)` は現物の signature と一致する。

**L-7・scope 外候補 — 回帰テスト3本・変異8本は、この一行修正には縮小できる。**

- **主張:** DEFAULT 変更で要求組の key が移動しないテストが本件の中心。5組×stock/non-stock×trace の独立 pre-image 再実装と、さらに compiler 名の各軸分離を追加する構成は重複が多い。
- **根拠:** plan:226–274。既存の `test_campaign.py:3184` が cxx 分離、`:11177` が歴史的 golden、`:3167` が trace/genome/commit 分離を検査する。
- **推奨:** DEFAULT 変更の回帰テストを残し、歴史的 golden と既存分離テストを再利用する。変異は旧条件への差戻しを必須とし、互換性を確認する「常に suffix」を追加する程度で本題に対応できる。片側比較や suffix の各要素脱落まで新規テスト・変異を広げる必要性は示されていない。
- **成果物影響:** 重複ケースを削っても、今回の compiler 誤帰属を防ぐ key と歴史的 entry 参照は変わらない。したがって追加分を MUST にする理由は DW-G05 上ない。既存の受入・consumer 確認を免除する提案ではない。

## 親の実測の検算

**編集面重複:** 指定された T-548・T-2237 については反証できなかった。現時点の T-548 親、a-procure、b-shell、c-python、merge-verify と T-2237 の各 worktree で、対象3ファイルは現在の main と byte 一致。T-548 branch と main の差分にも対象3ファイルはない。ただし、これは調べた worktree・3ファイル・観測時点に限定した結果であり、全稼働作業の重複ゼロではない。作成時刻の前後関係は未検証。

**compiler 在庫:** host は `pegasus02`。`--version` による確認は brief 追記と一致した。

| compiler | 確認結果 |
|---|---|
| gcc/g++-13 | 不在 |
| gcc/g++-12 | 12.3.0 |
| gcc/g++、gcc/g++-11 | 11.4.0。同じ実体への解決 |
| gcc/g++-9 | 9.5.0 |
| clang++ | 14.0.0 |
| nm／readelf | GNU Binutils 2.38 |

これは在庫確認であり、probe 完走確認ではない。追加の `g++-9 --help=c++` は本検査環境で rc=-6 となったため、compiler 適合性の証拠には使っていない。

**既定の履歴:** `git log -G '^DEFAULT_CC, DEFAULT_CXX'` は `9cde78124`（2026-07-02）だけを返した。同 commit と現在の `buildcache.py:622` はともに `gcc-13/g++-13`。本 worktree の HEAD に至る committed history について、brief の主張を支持する。一時編集や全 branch の不変までは意味しない。

**checkout／cache:** ccbench HEAD は `511c9538e4e8efa54b45cda62e72389ed3b706ec`、status は空。`CURRENT_PIN` の短縮文字列を使う計画は stock admission の完全一致条件に適合する。既定 root `external/ccbench/build-variants` は不在で、brief:29 の訂正も支持する。superproject の status も空だった。

**L-8・NIT — 「止まっている研究は無い」は、T-785 に起因する停止に限定すべき。**

- **主張:** brief:5 を研究全体の現状として読むと反証がある。
- **根拠:** `docs/phase3.md:585–592` は official 床値3走行が condition gate で停止し、試行台帳側の実値域が未取得と記す。`docs/handoff/2026-08-28-t1998-balanced-stock-inline-precheck.md:3` も中断状態。T-2000 の `RESULT.md:10` は admission 前提不成立による全 arm 未実行を記す。
- **訂正:** 「T-785 の既定変更衝突に起因すると確認された研究停止は、提示資料にはない」とする。これら別原因の停止を本 wave の scope に取り込まない。
- **成果物影響:** key や certified 受理集合は変わらない。研究前進・停止原因を説明するレポートの記述だけが変わるため NIT。

## 総括

P1 の歴史的 literal 組への固定は、本件を閉じる最小修正として妥当で、caller の変更は不要。ただし、**現 plan は実行手順と未再現時の分岐を直してから進めるべき**。

優先事項は、単文で実行できる編集・復元手順、各変異前の clean 確認、修正前偽 hit の成立確認。再現できなければ今回は F を実装しない。再現できた場合にだけ、同じ compiler 組・同じ evidence 条件で修正後 miss を確認する。

現時点で確認したのは静的な妥当性と上記の誤記・手順不整合であり、偽 hit、修正後 miss、テスト緑、変異 KILLED は未確認。