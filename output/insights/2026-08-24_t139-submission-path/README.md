# [T-139] CC 自動合成の private receipt admission / publish gate 実装

## 結論

worklog entry 874 の起票可と D574 / D597 / D626 に従い、manifest、固定resolver、writer、semantic
validator、conformance vectors を private gate として結線した。D292 の
`pilot_submission = forbidden` / `main_submission = forbidden`、D264 の4名前非export、PBS/qsub、
計算資源投入、driver / collector、解除decisionは変更していない。

実装commitは `6d431a60`（新vector世代）、`dcc76fe0`（manifest / approval projection）、
`d619419a`（private gate結線）、`c7a8f1e3`（段6所見fix）の4本。最新main取り込みmergeは
`fb71caf1` で、combined差分は空だった。

## trust chain

```text
D282 fixed payload (base fold 39d76098)
        |
D574 canonical authority (fold b261b293)
        |
source-pinned vector approval projection (dcc76fe0)
        |                         \
        |                          source-pinned manifest (dcc76fe0)
        |                                      |
        +------ index-v2 BlobRef ---------------+
                           |
                  sealed ApprovedManifest
                           |
                   sealed _PreregBinding
                           |
       schema + semantic raw reread + writer guard
                           |
          fixed create-only receipt namespace (private)
```

- `approval_payload.py` は manifest / projection のhistorical BlobRefだけをsource側でpinする。
  index digestをsourceへ受理根拠として直書きせず、payload内BlobRefをauthority、manifest内BlobRefを
  照合対象とする。
- fixed wrapperだけがsealed `ApprovedManifest`をmintする。explicit-ref seamはunsealed projectionの
  parse / mismatch検査に限定し、caller選択refをauthorityへ昇格しない。
- new receiptの`preregistration.approval_manifest`はD282 docs refではなく固定manifest refを記録する。
  legacy D282 fixtureは既存consumer互換にだけ残り、writerはpublish前に拒否する。
- raw `CMakeCache.txt` は`compile_commands` siblingをno-followで再読する。configure argv、実compile
  argv、raw cacheの3脚でpositive factを導き、申告`trace_enabled` / `analysis_enabled` /
  `cmake_cache`は不一致拒否にだけ使う。

## vectors / review / mutation

既存`index-v1.json`と42 vectorのbytesは不変。新`index-v2.json`は旧42 entryを順序・全fieldごと
保存し、writer positive、manifest片側不一致、payload片側不一致、historical index digest不一致の
4 vectorを追加した。index-v1はcommit `383bd3f2` / sha256 `c66953be...0643`、index-v2はcommit
`6d431a60` / sha256 `b4a86912...9099`で独立pinした。

段6 review 2本は初回にblocker 3件・must-fix 5件・nit 2件を返した。fixed-only mint、receipt manifest
ref、canonical全field再導出、HEAD差替え、pretty raw bytes、V2独立pin、private型をfixし、焦点再reviewは
closed 13 / partial 3 / regressed 0、blocker 0 / must-fix 0と判定した。partialは既存raw evidence TOCTOU、
legacy consumer fixtureの検出力境界、6,199行での可読性nitで、本成果の受理をblockしない。

final mutation resultは`mutation-result.json`。baseline PASSED、8/8 KILLED、SURVIVED 0、MISMATCH 0、
TIMEOUT 0。probe時にM6がmappingproxy直列化不能で落ちた結果はkillに数えず、thaw後のmeaning-equivalent
compact JSON再serializeへ再照準して、writer positiveのraw-byte exact検査だけが赤になることをfinalで
確認した。

## 実測

- 関連9 test file: 345 passed / rc=0（Pegasus request `941800.nqsv`）。
- mutation final baseline: 122 passed。8/8 KILLED（spec sha256
  `56256cdb767f1b55a16a1aee9d4f18b089c7cab3246dd0269831e692b7e29b9d`）。
- intermediate acceptance: 14,972 passed / 60 skipped / 0 failed、`verdict=child-green`、tested main
  `d8b5cb33`、tested tip `fb71caf1`、receipt
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/acceptance-intermediate/receipt.json`。
- `orchestrator/submission_gate/*.py`: 6,053行から6,199行（D509絶対上限6,200内）。
- 各実装commitとmerge後のfull-history provenance: known violations 53、new violation 0。

## 明示的な非成果 / scope外

- D292解除、pilot/main実走、計算資源投入、`submit_pilot` / `submit_main`、D264の4名前exportは行っていない。
- B2のsealed series / `receipt-set.json`、production producer、driver、collector、材料report、試行台帳
  consumer、generic future successor chain、AST alias hardeningは未実装。
- raw evidenceをsemantic検査した直後からpublishまでのrepository-level TOCTOUは既存保証境界のまま。
  single-fd snapshotと後続consumer再検証は維持するが、本waveでrepository lockや全raw再読を追加していない。
- `orchestrator/tests/test_spool_fold.py`、worklog entry 874の[T-139]本文、旧index/vector bytesは変更していない。

段2/3/4/6の逐語は`verbatim/`、final matrixの機械記録は`mutation-result.json`を参照する。

### verbatim末尾空白の可逆正規化

`git diff --check`のため、次の2出力だけMarkdown hard-break用の行末ASCII空白2 byteを除いた。
可視文字・改行・行順は不変。生出力は記載したrepo外pathに保全済みで、復元は列挙行の末尾へ
ASCII space 2文字を追加する。

- `verbatim/stage3-feasibility.md`: 原文15,507 bytes / sha256
  `fd4bd03b8e57420d1444f63887f1fd96a3e39cc68b9425426a3c5965a475692d`、正規化後15,467 bytes /
  `0edee868a9d856f53af755e900d2bd8e7f6af78cdfcd7265d391c1dfb033ed3a`。対象行=
  3,6,9,10,13,14,17,20,21,24,27,30,31,34,37,38,41,44,47,48。原文=
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/lensB/output.md`。
- `verbatim/stage6-review-detection.md`: 原文13,887 bytes / sha256
  `eae36d116fcdf79702179a8377afe48fae54a16b4fd60106dce15fdd6e285d75`、正規化後13,823 bytes /
  `8e9995b4b995abc56e4beee66a70845e380b652a50cfe6380ad1aa521875a7fb`。対象行=
  3,4,5,6,9,10,11,12,15,16,17,18,21,22,23,24,27,28,29,30,33,34,35,36,39,40,41,42,45,46,47,48。
  原文=`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage6/lensB/output.md`。
