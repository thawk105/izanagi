# 焦点走 3 本の要約 (raw log は job dir に残す)

raw log は pytest 出力の末尾空白を含み `git diff --check` に抵触するため insight へは置かない。原本は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/focus-f{1,2,3}.log` で、sha256 を下に束縛する。

## f1 — fix 前 (65e94a3a7)、23 file

- raw log sha256 `a9e4e7c5179173324b3975b7ea1fedffdde9eb5123ec045d573db32d61552d23` (34792 bytes)
- Request ID:             13633.nqsv
- Elapse:               39S
- 結果: 3 failed, 3112 passed in 34.23s
- 結果: IZANAGI_FAILURE_DIGEST_ACCOUNT failures=3 failed=3 errors=0 selected=3 omitted_failures=0 source_bytes=11841 retained_bytes=10932 omitted_bytes=909 budget_bytes=49152 rendered_bytes=13069 omitted_manifest_sha256=-
- 赤 node:
  - `orchestrator/tests/test_t671_source_binding.py::test_batch_reader_rejects_one_missing_path_of_sixty_two`
  - `orchestrator/tests/test_t671_source_binding.py::test_capture_batches_blobs_but_reads_all_sixty_two_disk_paths`
  - `orchestrator/tests/test_t671_source_binding.py::test_committed_verification_rejects_one_digest_mismatch`

## f2 — fix 後 (5bfb5fec0)、23 file

- raw log sha256 `54b57ee4cd42512abcc327bedc8152d2fab3481d7cf32ab8a260fb9ad1247585` (8117 bytes)
- Request ID:             13649.nqsv
- Elapse:               40S
- 結果: 3115 passed in 34.39s

## f3 — merge 後 (32c4921d4)、変更 test 5 file + DW-O26 改訂版の inventory 4 群

- raw log sha256 `d68d8a4c5a039431fda993ba39d74b59212bdd9aceb87bd87ff4ee7df61e62d5` (6444 bytes)
- Request ID:             13858.nqsv
- Elapse:               44S
- 結果: 1721 passed, 3 skipped in 38.09s

## f4 — fix 2 後 (95b5d8d3d)、`test_b10_backoff_static_tail_formal.py` 単独走

- raw log sha256 `f6de37418d516514baa08ec3d83f5204fa462ea0f0168a2ba4a03680acbb5148` (4589 bytes)
- Request ID:             13908.nqsv
- Elapse:               14S
- 結果: 69 passed in 8.27s
