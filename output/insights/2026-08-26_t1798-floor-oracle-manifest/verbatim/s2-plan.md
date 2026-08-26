### 現状の構造

- `sort_swo_oracle.py:1741-1929` は、`SHA256SUMS` の構文、Python `sorted()` 順、宣言集合と全 regular file 集合の完全一致、各 file hash、`config.h` 宣言を検査する。`_prepare_verified_dependency` は manifest hash を `DEPENDENCY_MANIFEST_SHA256` と比較してから private copy を作り、copy 元と copy 先を再検査する。
- `sort_swo_oracle.py:2092-2109` は oracle 用 private copy を closure scan 前後と compile 後に再検査する。
- `resolve_oracle_environment` は `config.h` の存在までしか見ず、完全な manifest 検証は `check_materialized_sort_swo` 内の `sort_swo_oracle.py:2753` で行う。
- `s8b_floor_campaign.py:2738-2928` は実 source root の Git top-level、HEAD、`config.h`、`libkohler_masstree_json.a`、directory identity を binding に保持する。
- 現在は `s8b_floor_campaign.py:3946` から実 source root を oracle に渡す。その root は 196 file なので、101 path の manifest gate を通れない。
- `buildcache.py:939-973` も同じ実 source root に `_verify_dependency_root` を掛ける。したがって現在の production 成功集合は空である。
- buildcache の cache identity は既に manifest hash、HEAD、`config.h`、archive hash を含む。`s8b_floor_campaign.py:3409-3638` は build 後に実効 source root、HEAD、tracked clean、`config.h`、archive、directory identity を再検査する。
- read-only 追加確認では、production root の `git ls-files` は 99 path で、`fixture-declared-101.txt` から `PIN` と `config.h` を除いた集合との差は 0 件だった。親の bytes 実測と合わせると、P1 の正例は実在する。

### プラン (file:line 粒度)

#### 新規 `orchestrator/campaign/sort_swo_dependency_material.py:1-約330`

production と tests の境界外に共有 module を新設する。

- `:1-45`
  - `CanonicalDependencyMaterialError` を定義し、内部 `detail_code` と対象 path を保持する。
  - `CanonicalDependencyMaterial` を frozen dataclass とし、少なくとも `root`、`lease_root`、`manifest_sha256`、`config_sha256`、`files`、`source_root`、`head` を保持する。
- `:46-115`
  - Git probe helper を置く。
  - `git -c core.fsmonitor= -c core.hooksPath= -c core.useReplaceRefs=false -C <root> ls-files --cached -z --` を、Git 関連環境を除去した環境、`stdin=DEVNULL`、30 秒 timeout、bytes 出力で実行する。
  - launch/timeout、非 0、空 stdout、非空 stderr、末尾 NUL 欠落をすべて拒否する。
  - NUL 分割後に UTF-8 strict decode し、重複、空 path、絶対 path、CR/LF、backslash、`PIN`、`SHA256SUMS`、`PurePosixPath` 正規化で表現が変わる path、`.` または `..` component を拒否する。
  - HEAD も前後で再取得し、top-level と期待 HEAD の一致を検査する。floor 側の既存 HEAD probe を信用して一度きりにしない。
- `:116-185`
  - root fd から各 path component を `O_DIRECTORY | O_NOFOLLOW` で辿り、末端を `O_RDONLY | O_NOFOLLOW` で読む helper を置く。
  - symlink、非 regular file、root 外 escape、read 前後の inode、size、mtime、ctime の変化を拒否する。
  - `shutil.copy2` は使わず、取得した bytes を destination に `O_CREAT | O_EXCL`、mode `0o600` で保存する。
- `:186-225`
  - 宣言集合を `set(tracked_paths) | {"config.h", "PIN"}` として一意化する。
  - `PIN` は検査済み HEAD の ASCII 40 hexと末尾改行から生成する。source root にある `PIN` は読まない。
  - `SHA256SUMS` は各 file の SHA-256 と正規化済み相対 path から、`f"{digest}  {relative}\n"` の UTF-8 bytes を連結する。
  - path は Python の `sorted()` にだけ通し、locale sort や filesystem 列挙順を使わない。
  - manifest は必ず末尾改行あり。空 directory は列挙も複製もしない。file の親として必要な directory だけ作る。
- `:226-285`
  - owner が実効 UID と一致する validated parent の下に `tempfile.mkdtemp` で mode `0o700` の job/process 一意 lease を作る。
  - まず `lease/generated` に上記 bytes を materialize する。
  - pin 比較の新しい実装を複製せず、既存の `sort_swo_oracle._prepare_verified_dependency(generated, lease/canonical)` を呼ぶ。これにより既存の pin consumer のまま、生成 manifest の pin 不一致を preflight で検出し、最終 canonical root も既存 verifier が作る verified copy になる。
  - `_prepare_verified_dependency` の `dependency-manifest-not-canonical` は generator の manifest pin mismatch に変換する。他の検証失敗も fail-closed で変換する。
- `:286-330`
  - canonical root の宣言から `PIN` を除いた全 path と、実 source の同名 path の bytes を再照合する。
  - tracked path 集合、HEAD、top-level も再取得し、生成開始時との一致を要求する。
  - 正常時は一時 `generated` を除去し、`canonical` と lease を返す。
  - 処理済み例外では lease を best-effort cleanup する。SIGKILL などで残っても名前はランダムで、次回は再利用しない。

#### `orchestrator/campaign/s8b_floor_campaign.py`

- `:94` 付近
  - 新 module を import する。
- `:205-248`
  - canonical materialization 用の新しい preflight detail code を閉じた集合へ追加する。
- `:2084-2131`
  - `_FloorOracleDependencyBinding` に optional な `oracle_root`、`canonical_lease_root`、`dependency_manifest_sha256` を追加する。
  - `source_root` は実 build source の意味のまま変更しない。
  - `private_dict()` は既存の `dependency_root` を実 root のまま残し、`oracle_dependency_root` と `dependency_manifest_sha256` を追加する。portable artifact へ path は出さない。
- `:2134-2161`
  - `_post_oracle_dependency_binding` で、oracle receipt の manifest hash が binding の canonical manifest hashと一致し、receipt の config hash が実 source の事前観測 hash と一致することを要求する。
  - 戻り値へ `oracle_dependency_root` を追加する。`fetchcontent_base_dir` は実 source root の親のままにする。
- `:2738-2928`
  - 既存の Git root、HEAD、config、archive、directory identity 検査は変更しない。
- `:3138-3158`
  - 実 source binding の作成後、return 前に新 generator を一度呼ぶ。
  - 成功した material の root、manifest hash、lease root を `replace()` で binding に追加する。
  - generator error は後述する `_FloorOraclePreflightError` へ変換する。
- `:3240-3252`
  - phase marker でも `dependency_root` は実 root のままにし、`oracle_dependency_root` と manifest hash を追加する。
- `:3374-3406`
  - `_verify_floor_tracked_source_unchanged` の既存 HEAD、tracked clean 検査は変更しない。
- `:3409-3638`
  - build 後の既存検査に続けて、実 source が canonical root の tracked path、`config.h`、HEAD と一致することを新 module で再照合する。
  - canonical root 自体の drift と実 source の canonical material drift は別 detail code にする。
- `:3888-3909`
  - dependency marker 作成前までに canonical binding が完全であることを assert する。
  - legacy の `fetchcontent_base = dependency_binding.source_root.parent` は変更しない。
- `:3937-3949`
  - `oracle_dependency_root=_dependency.source_root` を `_dependency.oracle_root` へ変更する。
- `:4019-4031`
  - build の FetchContent base、receipt、archive は実 source の値を渡し続ける。
  - post-oracle capability だけに canonical root path を追加する。
- `:3920-4197`
  - cell loop 全体を `try/finally` または `ExitStack` で囲み、全 build と postflight が終わるまで canonical lease を保持する。
  - 正常終了と通常例外では lease を削除する。cleanup 対象は materializer が返した exact lease root だけとし、既存 directory や FetchContent base 全体は削除しない。

#### `orchestrator/campaign/buildcache.py`

- `:28` 付近
  - 新 material module を import する。
- `:55-58`
  - `_POST_ORACLE_DEPENDENCY_BINDING_KEYS` に `oracle_dependency_root` を追加する。旧 5-key capability は拒否される。
- `:743-772`
  - `oracle_dependency_root` を canonical、absolute、non-symlink directory として検証する。
  - この path は run-local capability であり、cache preimage へは入れない。
- `:939-973`
  - `_assert_post_oracle_dependency_material` を二根検査へ変更する。
  - `buildcache.py:948` の `_verify_dependency_root` 対象は `binding["oracle_dependency_root"]` にする。
  - canonical manifest/config を oracle binding と比較する。
  - 続けて実 `fetchcontent_base/masstree-src` の tracked path、HEAD、`config.h` が canonical root と一致することを新 helper で検査する。
  - `libkohler_masstree_json.a` は manifest に含めず、既存の独立 hash 比較を維持する。
- `:1252-1313`
  - `_v2_identity` の `fetchcontent_dependency_manifest_sha256`、population policy、HEAD/config receipt、archive hash の構造は変更しない。
  - canonical path は preimage に入れず、同じ bytes の job-local root 間で cache identity が変わらないようにする。
- `:2063-2127`
  - capability 検証後、cache lookup より前にも完全な二根検査を呼ぶ。これで cache hit も canonical/source binding を省略できない。
- `:2228-2262`
  - cache hit の return 直前に、archive 単独再検査ではなく完全な二根検査を再実行する。
- `:2304-2320`
  - fresh build の configure 前、configure 後の既存二回の検査位置は維持する。
- `:2332-2362`
  - build subprocess 完了後、completion publish 前にも完全な二根検査を追加する。
- `:2187-2202`
  - cache preimage には oracle receipt の manifest hashを従来どおり入れる。新 path や lease identity は入れない。

#### 変更しない production file

- `orchestrator/campaign/s1_direct_comparison.py:593-686`
  - signature と `resolve_oracle_environment(... dependency_root=oracle_dependency_root)` は変更しない。floor caller が渡す値だけ canonical root へ変わる。
- `orchestrator/campaign/sort_swo_oracle.py:81,1741-2026,2086-2114,2345-2449,2700-2795`
  - pin、parser、inventory、root verifier、private copy、unchanged check、closure、resolver、oracle 本体を一切変更しない。
- `orchestrator/campaign/s8b_sort_swo_receipt.py:114-137`
  - manifest pin 検査を変更しない。
- `orchestrator/critic/digest.py:643-681,930-993`
  - current receipt の pin 検査を変更しない。
- `orchestrator/tests/sort_swo_masstree_fixture.py` と `orchestrator/tests/fixtures/sort_swo_masstree/`
  - verifier も fixture bytes も変更しない。

### 論点への回答 (上の 1〜8 に番号で対応)

1. canonical generator は新規 production module に置く。floor 固有 error や campaign 制御を混ぜず、buildcache からも実 source 対 canonical の照合を再利用できるためである。tracked 一覧は hardened な `git ls-files --cached -z` から取得し、HEAD は前後で再取得する。失敗、空、stderr、非 NUL 終端、invalid UTF-8、重複、reserved path、非正規 path はすべて拒否する。

2. 出力は 64 lowercase hex、空白 2 個、正規化済み相対 path、改行 1 個で固定する。全行を Python `sorted()` 順に生成し、末尾改行を必須とする。`PurePosixPath` で表現が変わる入力は拒否する。空 directory は manifest に現れず、最終 root にも作らない。

3. materialize は validated FetchContent base 内の job/process 一意な `0o700` lease とする。既存 directory は再利用しない。通常失敗では cleanupし、強制終了の残骸も次回は採用しない。生成 staging rootを既存 `_prepare_verified_dependency` で job-wide canonical rootへ変換し、oracle はそこからさらに per-invocation private copy を作る。二段は維持する。前者は実 source と build capability の橋、後者は候補 compile から隔離された oracle snapshot で、寿命と信頼境界が異なる。

4. build 材料の binding は次の組にする。

   `canonical manifest/config` → `actual tracked files/config/HEAD` → `actual archive` → `cache preimage` → `binary sha256`

   `buildcache.py:948` は canonical root を見る。ただしそれだけでは不十分なので、同じ関数内で実 source の tracked path と bytes を canonical へ照合し、archive は従来どおり別 hash で束縛する。

   - canonical のみを見る案は、実 source の非 config tracked file が変わっても通るため D953 を壊す。
   - 実 source のみを見る案は 196 file 対 101 declaration で成功集合が空。
   - 両方へ同じ exact verifier を掛ける案も実 source 側で必ず落ちる。
   - 推奨案は canonical へ既存 exact verifier、実 source へ tracked集合と内容の等価検査、archive へ独立 hash 検査である。

5. `_assert_verified_dependency_unchanged` は oracle private copyを closure scan 前後と compile 後に検査する。実 source は見ない。`_verify_floor_tracked_source_unchanged` は build 後に HEAD と tracked clean を検査する。

   新経路では、canonical 生成後から build 前までに実 source が変わる窓が開く。これを generator 完了時、cache lookup 前、configure 前後、build 後、floor postflight で再照合する。job-local `0o700` base により他 UID からの変更も遮断する。

   同一 UID の別 process が build 中だけ変更し、検査前に完全に戻す攻撃までは hash の前後検査では証明できない。完全に閉じるには、archive を含む verified full build snapshot を作り、CMake の実効 source root 自体をその snapshotへ変える追加設計が必要である。本変更では既存 T-1749 の保証境界を維持し、それ以上の耐性は主張しない。

6. 新設する floor detail code は次を推奨する。

   | 状況 | detail_code | origin | outcome |
   |---|---|---|---|
   | Git launch、timeout、非 0 | `floor-dependency-canonical-tracked-list-unavailable` | `floor-dependency-canonical:git-ls-files` | `execution-failed` |
   | 空、stderr、malformed、重複、危険 path | `floor-dependency-canonical-tracked-list-invalid` | `floor-dependency-canonical:git-ls-files` | `identity-mismatch` |
   | private lease 作成失敗 | `floor-dependency-canonical-root-create-failed` | `floor-dependency-canonical:materialize` | `execution-failed` |
   | source file read/copy 不能 | `floor-dependency-canonical-copy-failed` | `floor-dependency-canonical:masstree` | `execution-failed` |
   | copy 中または copy 後の source drift | `floor-dependency-canonical-source-drift` | `floor-dependency-canonical:masstree` | `identity-mismatch` |
   | 生成 manifest の pin 不一致 | `floor-dependency-canonical-manifest-mismatch` | `floor-dependency-canonical:manifest` | `identity-mismatch` |
   | canonical root のその他の検証失敗 | `floor-dependency-canonical-verification-failed` | `floor-dependency-canonical:root` | `identity-mismatch` |

   source root、HEAD、`config.h`、archive の materialization 前の失敗には既存 code を再利用する。新しい outcome 語彙は追加しない。

   成功正例は実在する。read-only 確認で production の tracked path は 99 件で、fixture 宣言から `PIN` と `config.h` を除いた 99 件と完全一致した。親実測ではその99件と `config.h` の bytes が一致し、HEAD から作る `PIN` も一致する。したがって生成 101 行は pin 済み manifest と byte-identical になり、archive の独立 hash も取得できる。

7. テスト計画は次のとおり。

   - 新規 `orchestrator/tests/test_sort_swo_dependency_material.py`
     - Git output の非 0、空、stderr、非 NUL 終端、invalid UTF-8、重複、危険 path を拒否。
     - manifest の空白 2 個、Python sorted 順、末尾改行、path 正規化、空 directory 無視を exact bytes で検査。
     - symlink、非 regular、copy 中 mutation、copy 後 tracked 集合変更を拒否。
     - 同じ parent から二回 materialize して異なる private root になること、mode、既存 root 非再利用、失敗 cleanup を検査。
     - synthetic root では Git probe seam と pin 検査を分離し、正負双方を検査する。
     - real-repo test は明示環境変数で production Masstree root を受け、生成 manifestを test fixture の manifest bytes と比較する。未設定時は通常 suite から分離し、親が nodeid と環境を明示して実走する。
   - `orchestrator/tests/test_s8b_floor_campaign.py:2277-2494`
     - oracle へ `source_root` でなく `oracle_root` が渡ること。
     - post-oracle capability が actual base と canonical root の両方を持つこと。
     - receipt manifest/config と binding 不一致を build 前に拒否すること。
   - 同 `:2629-2895`
     - prebuild、actual binding、canonical materialize、oracle の順を検査。
     - materialize は job ごと一回で、複数 sort cell が同じ canonical root を使うこと。
   - 同 `:3388-3638`
     - build 後の actual tracked/config/archive/canonical driftを個別に拒否すること。
   - 同 `:3797-4195`
     - 新 detail code ごとに private failure artifact が保存され、oracle/build が呼ばれないこと。
   - 同 `:4682-4728`
     - private marker が actual root と oracle rootを区別して記録すること。
   - `orchestrator/tests/test_buildcache_v2.py:359-421`
     - synthetic fixture を「actual Git root + canonical manifest root」の二根へ分離する。
   - 同 `:723-908`
     - 旧 5-key capability の拒否、canonical manifest 改変、actual tracked file 改変、config 改変、archive 改変を configure 前に拒否。
   - 同 `:911-1018`
     - canonical path が cache preimage に入らず、manifest hash は入り、別 job rootでも同じ identityになること。
   - cache hit、configure 中、build 中の persistent driftをそれぞれ拒否するテストを追加する。
   - `test_sort_swo_oracle.py` の既存 verifier、contract snapshot、fixture E2E は変更しない。これらは oracle 受理集合が変わっていないことの回帰になる。

   既存受理集合を狭める変更は、post-oracle capability に canonical root が必須になる点と、cache hitでも二根検査を省略できなくなる点である。generic build caller の受理集合は変えない。

8. `sort_swo_oracle.py` の verifier、pin、source bundle、contract IDは変更しない。fixture verifier と fixture bytes も変更しない。`s8b_sort_swo_receipt.py` と `critic/digest.py` の既存 `DEPENDENCY_MANIFEST_SHA256` consumer も変更しない。preflight の pin 検査には既存 `_prepare_verified_dependency` を再利用するため、pin 比較の第二実装も作らない。

### 親 brief への異論

- P1 の集合規則には賛成する。ただし「規則が誤れば pin で落ちる」だけでは不十分である。Git output の malformed、path escape、symlink、copy 中 mutation は manifest pin 比較より前に fail-closed にする必要がある。
- P2 の materialize 位置と、実 source を build に使う方針には賛成する。実装は floor file に直書きせず、buildcache も再利用できる production module に分離すべきである。
- P3 の「buildcache.py:948 を canonical rootへ変える」だけには反対する。それだけでは oracle と build が異なる材料でも通る。canonical exact verification と actual-to-canonical equivalence verification の両方が必要である。
- P4 の job-local private directory と copy 後再検査には賛成する。ただし一度の再検査では oracle から build までの窓を閉じない。cache lookup、configure 前後、build 後、floor postflight の再検査も同じ変更に含めるべきである。

### 残るリスク

- 同一 UID の別 process による一時改変と完全な巻き戻しは、前後 hashだけでは検出できない。現在の job-local private base と単一 process運用の境界外である。
- `_prepare_verified_dependency` は private function なので、新 moduleとの結合は強い。ただし複製 verifierや第二の pin consumerを作らず、oracle contractを不変にできる利点を優先する。
- SIGKILL 後の lease 残骸は完全には回収できない。ランダム名、非再利用、`0o700` により成功入力として誤採用されない。
- real-repo test は production cache の存在を前提とするため、通常の合成 testとは分離して明示実行する必要がある。

## 総括

採るべき形は、P1、P2、P4を強化し、P3を「canonical rootへの単純置換」から「canonical exact検証と実 source等価検証の二根 binding」へ修正する案である。oracle の101 file受理集合、pin、fixture、receipt consumerは不変のまま、production の99 tracked file、`config.h`、HEAD、独立 archive hashを実 buildへ因果的に束縛できる。

pytest は実行していない。実施したのは指定資料とコードの静的確認、および production rootの tracked path集合に対する read-only照合だけである。