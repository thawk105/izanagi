# T-2000 段4裁定

## 結論

段5へ進み、production build経路を変更しないT-2000専用probe 1ファイルだけを実装する。実走は既存tests dispatcherを1回だけ使い、結果から「移行候補材料」「現状維持候補材料」「裁定不能」のいずれかを返す。このwaveでは移行しない。

## real / refuted

- **real・採用:** legacy no-proxyへGit遮断を重ねるとproxy感応性を識別できない。legacy arm間の唯一の差は既存B-10 build経路が使うproxy値の有無にする。
- **real・採用:** legacy `build()`にはtimeout引数がなく、外側process group supervisorが必要。production関数、PATH、CMake/Git wrapperは変更しない。
- **real・採用:** probeを`orchestrator/tests/`へ置くと通常全走へ混入する。`tools/pegasus/probes/test_t2000_legacy_build_probe.py`の明示nodeidだけに置く。
- **real・採用:** CMakeの`fetchcontent_ref`とpolicy ref、取得後HEADとpolicy pinは別々に照合する。mimalloc tagを40桁pinと誤読しない。
- **real・採用:** same dependencyは3 repoのHEAD、commit tree、tracked/untracked/ignored clean、alternates不在、legacy観測値とprivate copy値の一致で主張する。取り逃しは裁定不能。
- **real・採用:** rawでは`ambient_proxy_env_sensitivity`、`non_file_git_transport_needed`、`arbitrary_external_network=not-measured`を分離する。
- **real・採用:** wallは単発診断値だけであり、性能優劣・倍率・正式性能値へ使わない。
- **refuted:** `-n 0`が無効という懸念。現行run_testsは明示0をxdist無効として扱う。
- **refuted:** production factory名が実在しないという懸念。`BACKOFF_REPRO`、build context/admission、required attestation contract/authorizeは実在する。
- **scope外 real:** arbitrary network不存在の強い証明、proxyの前後bracketing/反復、dispatcherへのproxy transport、legacy timeout seam、汎用3依存receipt拡張。必要なら別変更単位へ返す。

## plan v2

1. 新規実装面は`tools/pegasus/probes/test_t2000_legacy_build_probe.py`だけ。production module、dispatcher、policy、既存testは編集しない。T-2000専用で、汎用APIを公開しない。
2. compute/PBS/node/siteをfail-closedで確認し、CCBench HEAD、stock genome、trace=false、compiler/toolchain、source evidence、build context/admission、Pegasus contractを一度確定する。arm前後のidentity hash一致を必須にする。
3. proxy controlは既存`tools/pegasus/b10_backoff_grid.sh`の単一`BUILD_NETWORK_PROXY_URL`をメモリ内で読み、既存経路と同じlowercase `http_proxy` / `https_proxy`へ設定する。値、URL、hostname、PBS job IDはartifactへ保存せずhashだけにする。Git config隔離とPATHは全armで同一にする。
4. 検証済み永続cache 3本をjob-local private baseの`masstree-src` / `mimalloc-src` / `googletest-src`へcopyする。private copyだけをpinへreset/cleanし、tracked/untracked/ignored、alternates、tree IDを検査する。共有cacheは変更しない。
5. v2 setupはproduction `prepare_masstree_fetchcontent()`へ3 SOURCE_DIR、toolchain manifest、正のconfigure/target timeoutを渡す。private masstreeのreceiptと必要なarchive SHAをproduction observerから作る。setup wallはarm wallへ混ぜない。
6. 単一pytest coordinatorが各armを別process groupで固定順に実行し、arm deadline後はTERM/KILLして親がtimeoutを固定enumで記録する。production build関数はchildから直接呼び、mock/monkeypatch/wrapperを使わない。
7. armはexact 3件: (a) legacy + proxy、(b) legacy + proxy値だけ除去、(c) build_v2 + 3 SOURCE_DIR + proxy除去 + `GIT_ALLOW_PROTOCOL=file`。各armは独立した不存在cache rootからfresh missを要求する。
8. legacyのstagingは親observerが監視し、3 sourceのroot/HEAD/treeをclone完了後とbuild終端前に安定再確認する。観測取り逃し、親repoへの誤解決、pin不一致は裁定不能。
9. raw/digestはPBS job hashとrun nonce hashを含むcreate-only名へpublishする。rawを先、raw basename/hashだけを参照するdigestを最後にpublishする。endpoint、URL、stdout/stderr、例外本文、traceback、完全argvは保存しない。
10. 分類は、proxy legacy成功・no-proxy legacyが3依存の外部Git取得段で失敗・v2 offline成功・全identity一致の場合だけ「移行候補材料」。no-proxy legacy成功なら「現状維持候補材料」。control不成立、v2 setup/arm失敗、timeout、observer欠落、identity不一致は「裁定不能」。単発運用感応性を因果証明へ昇格しない。
11. 規模上限はT-2000に必要なprobe/schema/self-testだけとし、汎用driver化しない。実装がproduction変更や別fileを要求した時点で停止する。

## 変異事前登録 (B-057)

同じ1ファイル内にpureなclassification/redaction/identity self-testを置き、実build nodeidとは分離する。変異本走はpure node群へ向け、3-arm buildを反復しない。

| ID | 単一変異 | 期待する単一赤理由 |
|---|---|---|
| M1 | fresh cache miss必須を外す | cache hit fixtureが移行/維持候補へ入るためclassification testだけが赤 |
| M2 | legacy no-proxyの失敗stage条件を外す | setup/unknown失敗fixtureが移行候補へ入るためclassification testだけが赤 |
| M3 | v2 remote-attempt=0条件を外す | network利用v2 fixtureがoffline成功扱いされるためclassification testだけが赤 |
| M4 | dependency tree/pin一致条件を外す | same-dependency不一致fixtureが候補へ入るためidentity testだけが赤 |
| M5 | URL/proxy値のredaction拒否を1箇所外す | secret fixtureのpublish前検査だけが赤 |
| M6 | control不成立を裁定不能にする分岐を外す | legacy proxy失敗fixtureが候補へ入るためclassification testだけが赤 |

正例は、3 arm・fresh miss・identity一致・proxy control成功・no-proxy外部Git取得失敗・v2 remote attempt 0成功のfixtureが「移行候補材料」へexactに入ること。各変異の前後に同じ入力を拒否する別層がないことをauthorが確認し、maskがあれば登録せず実効判定へ再照準する。

## 受入

- pure self-testを`tools/run_tests.py --force-dispatch -n 0`で先に実走する。
- 実probeを同runner/既存tests dispatcherで明示nodeid指定し、queue混雑だけでは投入を止めない。
- raw/digest検収後、probe fileの関連pure test、Codex agents、docs、spool dry-run、全受入、provenanceを規定順で行う。
