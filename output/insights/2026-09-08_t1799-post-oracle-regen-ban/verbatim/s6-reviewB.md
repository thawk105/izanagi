## 所見 (real/refuted + 成果物影響)

- [real, must-fix] 同一根を保護する 2 context が非 LIFO 順で終了すると、先に入った context の復元が後続 build 中の write bit を戻し、後続 context は読取専用 mode を最終状態として復元します。[実装の mode 採取と復元](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/sort_swo_dependency_material.py:578)から決定的に導けます。  
  成果物影響: 後続 build は D984 が禁じた再生成を実行して binary を publish でき、その後 source tree は恒久的に読取専用になり得ます。

- [real] `restore_modes()` の例外は `finally` から投げられ、build 例外を active exception として置換します。元例外は `__context__` に残りますが、floor の永続診断は最上位の復元例外しか記録しません。  
  成果物影響: 本来の compile/build 失敗理由が durable failure record から失われ、staging binary は破棄されます。

- [real] build 自体が成功しても復元が失敗すれば、後段の材料再照合、binary copy、`completion.json` 作成へ到達しません。[buildcache.py:2750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2750)以降が全て飛ばされます。  
  成果物影響: 成功した staging binary は [外側 cleanup](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2941)で削除され、cache completion と sort_best の成功 record は作られず、stale `.building` claim が残ります。

- [refuted] `<base>` directory 自身を chmod する経路はありません。列挙開始点は exact `<base>/masstree-src` で、symlink directory も再帰しません。`<base>` への操作は path 解決だけです。  
  成果物影響: sibling dependency や `<base>/izanagi-masstree-prebuild` の新規作成を mode 変更で妨げる実装上の経路はありません。

- [real] 読取専用 mount 上で既に write bit が無い node に対しても無条件に `chmod` するため、`EROFS` で正当な build を拒否します。別 owner でも、既に process から書込不能な nodeなら同じ過剰拒否です。  
  成果物影響: D984 を既に満たす source からも binary、completion、admission 入り cache receipt が作られません。

- [refuted] 実物 144 node での `RecursionError` は通常の Python recursion limit では起きません。最大深さは node 数未満であり、保存 fixture は 103 node、最大深さ 2 でした。  
  成果物影響: 現材料の深さを理由に build artifact が失われる経路は認められません。

- [real] path を identity 確認前に chmod するため、保護中に既存 path が別 inode へ置換されると、復元処理は置換後 inode に旧 mode を設定してから identity mismatch を検出します。  
  成果物影響: build は拒否される一方、競合 process が作った replacement node の permission を壊し得ます。

## 失敗経路の分類 — 正しい拒否と巻き添え

| 例外、detail code | 実際の発火条件 | 分類 | 成果物影響 |
|---|---|---|---|
| [real] `canonical-source-unavailable` | root の欠落、ancestor の検索権限不足、symlink loop、I/O error | 正しい前提拒否。保護対象を確定できない | configure 済み staging を破棄し、completion なし、claim は stale |
| [real] `canonical-source-invalid` | root 自身が symlink、非 directory、または lexical path が canonical absolute path でない | 正しい前提拒否 | 同上 |
| [real] `post-oracle-effective-root-mismatch` | CMake が示す実効根と binding の `<base>/masstree-src` が不一致 | 正しい拒否。既存後段でも拒否される入力を build 前へ移しただけ | build は起動せず staging を破棄、claim は stale |
| [real] `post-oracle-permission-inspection-failed` | `scandir`: directory の read 不足、`EMFILE/ENFILE`、削除や rename、NFS/Lustre の `ESTALE/EIO`。`lstat`: parent の execute 不足、走査中の消滅、I/O error | 混在。根や必要 node を観測不能なら正しい fail-closed。無関係な `.git`/untracked node、FD 枯渇、分散 FS の一過性失敗なら正当 build の巻き添え | 初回走査なら mode 不変で build なし。保護後走査なら復元後に build なし |
| [real] `post-oracle-permission-protection-failed` | symlink への no-follow chmod 非対応、`EROFS`、別 owner の `EPERM`、immutable policy、race による `ENOENT`、NFS/Lustre の権限または I/O failure | 書込可能 node の write bit を除去できないなら正しい拒否。既に書込不能な RO mount、非 writable な別 owner node、無害な symlinkなら巻き添え | build なし。先に変更済みの node は best-effort 復元される |
| [real] `post-oracle-permission-tree-changed` | 最初と 2 回目の走査間に別 process が node を作成、削除、rename、型変更 | build はまだ起動していないため、D984 が禁じた build 内再生成の検出ではない。無関係 node の作成なら偽赤。compiler input の置換なら安全上の拒否 | build なし、staging 破棄、claim stale。置換 race では replacement mode を壊し得る |
| [real] `post-oracle-write-bits-remain` | chmod が成功扱いでも mode に `0222` が残る、または別 actor が直後に chmod を戻す | 保護を確立できていないので正しい拒否。分散 FS の stale attribute 表示なら巻き添え | build なし、復元後 staging 破棄 |
| [real] `post-oracle-permission-restore-failed` | 復元時の `EROFS`、owner 変更、削除/置換、NFS/Lustre error、復元 mode/identity 不一致 | D984 違反の拒否ではなく、build 後 cleanup failure による巻き添え。ただし状態不明なので fail-closed 自体には理由がある | 成功 binary も破棄。completion なし、claim stale、floor failure record のみ |
| [real] consumer/build 例外 | `_run()` の任意の build 失敗。保護による `EACCES` なら D984 の正しい発火、通常の compile/link error は元々失敗する入力 | 原因依存 | partial binary を含む staging は破棄。復元失敗時は元例外が表面から消える |
| [real] 非正規化例外 | 深い再帰の `RecursionError`、列挙/辞書作成の `MemoryError`、consumer の任意の例外。`KeyboardInterrupt` 等の `BaseException` も `yield` から伝播 | D984 とは無関係な実行基盤失敗 | `Exception` は外側 cleanup 対象。`BaseException` は外側 `except Exception` を迂回し、staging と claim が残り得る |

この環境では `os.chmod` は `follow_symlinks=False` 対応集合に入っていません。したがって tree 内 symlink は理論上ではなく、この runtime では `NotImplementedError` による確定拒否です。ただし保存 fixture には symlink、hardlink、特殊 node はありません。

読取専用 NFS/Lustre は `EROFS`、別 owner や UID mapping は `EPERM/EACCES`、競合や server/MDT 障害は `ESTALE/EIO` になり得ます。通常の rw mount 上で current owner が chmod するだけなら、NFS/Lustre であること自体は失敗条件ではありません。repository は Lustre 上でしたが、official scratch の protected real root は存在せず、そこでの chmod 成功は実測していません。

## finally の中の raise が成果物へ与える影響

[helper の `finally`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/sort_swo_dependency_material.py:610)は無条件に `restore_modes(changed)` を呼びます。

- [real] build が失敗し復元も失敗した場合、最終的に投げられるのは `post-oracle-permission-restore-failed` です。元の `BuildError` は `__context__` にだけ残ります。  
  成果物影響: floor が保存する `build_exception` は復元例外を原因として記録し、真の build failure は record から落ちます。

- [real] build 成功後に復元だけ失敗した場合も同じ例外になります。binary copy は 2869 行、completion 作成は 2888 行以降なので未到達です。  
  成果物影響: staging binary は削除され、成功 cache entry、receipt、returned `BuildResult` は存在しません。

- [refuted] restore failure なら必ず tree 全体が読取専用のまま、とは限りません。全 `changed` node を最後まで best-effort 復元し、1 件でも失敗すれば最後に raise します。  
  成果物影響: 成功した node は元 mode、失敗した同一 inode だけが保護 mode のまま残り得ます。mount が途中で RO 化した場合は全 node が残り得ます。

- [real] root は走査列の最後なので、root 自身の復元失敗では `<base>/masstree-src` が write bit なしで残ります。  
  成果物影響: 後続 prepare、cleanup、別 build が source tree を更新または削除できなくなります。

## 並行実行での破れ

初期 mode を `M`、write bit を外した mode を `R` とすると、非 LIFO 交差は次のとおりです。

| 時点 | context A | context B | 実 mode |
|---|---|---|---|
| A enter | `M` を採取 | - | `R` |
| B enter | active | `R` を採取 | `R` |
| A exit | `M` を復元 | active/build 中 | `M` |
| B exit | exited | 採取済み `R` を復元 | `R` |

- [real, must-fix] A exit から B exit まで B の保護が消えます。B がこの間に custom command を起動済みなら、`config.h`、archive、tracked source を再生成できます。  
  成果物影響: B の binary と receipt が D984 違反の入力から publish され得ます。

- [real, must-fix] B は A が設定した `R` を「元 mode」として採取しているため、最後に tree を `R` へ戻します。fixture の通常 mode は file `0644`、directory `0755` なので実害があります。  
  成果物影響: source tree が恒久的に読取専用となり、後続 build と scratch cleanup を壊します。

- [real] cache claim は build digest 単位であり dependency root 単位ではありません。異なる variant の build は別 claim を取りながら同じ masstree root を共有できます。  
  成果物影響: claim 機構は上の交差を防がず、binary provenance と source lifetime の両方が壊れます。

これは単に「交差中に一時的な保護 gap がある」という明記済み限界を超え、最終 mode まで破壊します。ユーザー指定の判定基準どおり real の must-fix です。

## 段 4 裁定の誤り

- [real] 裁定表 7 の事実認定は正しい一方、「限界として明記」だけで受理した扱いが誤りです。実装は交差復元後に `R` を恒久化し、B の build 中に `M` を露出します。  
  成果物影響: D984 違反 binary の publish と source tree poison が同時に起こり得ます。

- [real] 裁定表 8 の「private snapshot でも lock なしでは同型」という主張は過大です。build ごとに異なる private root を使うなら mode stack は共有されず、この実装固有の `M -> R -> M -> R` は起きません。同じ private root を意図的に共有した場合だけ同型です。  
  成果物影響: 選択方式間のリスク差を消して評価したため、現在方式の artifact 汚染経路を documentation-only と誤裁定しました。

- [real] 裁定表 4 の「chmod 不能 node は保護失敗」という一般化は広すぎます。既に write bit が無い RO mount の node は保護済みであり、chmod 不能は protection 不成立を意味しません。  
  成果物影響: D984 を満たす既存材料からの正当な binary を拒否します。

- [real] 裁定表 10 の「up-to-date build は保護と両立」は、「全 node を scan、chmod、restore できるなら」という条件付きでのみ正しいです。protected real CMake build は author 報告でも skip されています。  
  成果物影響: official real material を受理できるという実証済み成果物主張にはできません。

- [refuted] 裁定表 3 の `<base>` 巻き添え回避、表 5 の build 後 root 再取得、表 14 の protected real build 未実走の記載は実装と一致します。  
  成果物影響: これらに由来する追加の binary/receipt 破損はありません。

## must-fix と nit の切り分け

- [real, must-fix] 同一根 context の非 LIFO 交差による保護解除と最終 read-only 化。裁定済みの単なる残存限界ではなく、D984 の保証と source lifetime を直接破壊します。  
  成果物影響: 禁止された再生成を含む binary が受理され得て、共有 source も poison されます。

- [real, nit/backlog] restore failure が元 build exception を top-level から置換し、floor の durable diagnostic が元原因を保存しないこと。  
  成果物影響: binary は受理されませんが、失敗 record の診断精度が落ちます。

- [real, nit/backlog] RO mount、既に非 writable な別 owner node、symlink による過剰拒否。official staging は fresh copy で current owner になるため、現行実材料での発火証拠はありません。  
  成果物影響: 該当配置では正当 binary が生成されません。

- [real, nit/backlog] identity 確認前の path-based restore による replacement inode の mode 上書き。現 official flow に同時 writer の保存済み証拠はありません。  
  成果物影響: build 拒否に加えて、競合 node の permission を壊し得ます。

- [refuted, 対応不要] 再帰深さと 144 node の走査コスト。fresh post-oracle cache miss 1 回につき概算 2 tree walk、288 chmod、約 432 lstat です。cache hit は 2628 行で return するため保護へ入りません。pack の byte 内容も読みません。  
  成果物影響: metadata latency は未計測ですが、現 node 数から recursion failure や容量比例の pack 読出しは発生しません。

- [real, test gap] 新設 5 node は overlap、tree change、部分 protection failure、restore failure、例外 masking、RO mount、symlink、path replacementを検出しません。M2 は fake build 後の 2 file 書込み試行であり、protected real CMake build ではありません。  
  成果物影響: must-fix の交差汚染と、成功 binary 破棄の回帰が緑のまま残ります。

## 総括

`<base>` 巻き添えは refuted、通常材料の深さと 144 node のコストも blocking ではありません。sequential、current-owner、rw filesystem という条件下では狙った保護を実装しています。

ただし同一 root の交差 context は、保護 gapだけでなく「後続 build が禁止再生成を通せる」「最終 mode が恒久的に読取専用になる」という二重の実害を持ちます。段 4 の documentation-only 扱いでは閉じず、この commit には real の must-fix が 1 件あります。

pytest は指示どおり実走していません。file の変更、patch、commit も行っていません。