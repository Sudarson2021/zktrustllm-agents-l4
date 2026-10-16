# Tool verification, 16 October 2026

This records local software checks, not live experimental results.

* The uploaded provenance archive matches the reported SHA-256
  `724b943a5eea534f5cc85fc18a3f4e5994f52700c4563dd9fad552ceebe182cc`.
  Its 14 internal checksum entries were verified. The pinned gateway source
  matches `952fbbf87d1fc59a9e600718c9cf5ff6d2bc5c3eb24a3673a5203322921ed65e`.
* 25 new unit tests passed. These cover frozen input/source binding,
  oracle-label exclusion, common requests, scheduling and token caps,
  parallel assessments, sequential role context, explicit single-assessor
  quorum, review-only gating, fatal-error retention, protocol/manifest
  tampering, finite timers, model metadata and private launcher stdin.
* The existing revision Python suite passed all 43 tests.
* A complete offline synthetic run executed 240 trials and 1,080 fixture
  calls. The analyzer verified 3,723 manifest entries, found no missing
  trial and correctly marked the run synthetic and publication-ineligible.
  Those fixture times are deliberately omitted from this document.
* The host launcher was tested using mocked Docker subprocesses. Actual
  image startup, UID permissions, provider model availability, billing,
  endpoint compatibility and response validity remain to be checked on
  the user's Linux machine. No hosted provider call was made in these checks.

The synthetic fixture does not use the oracle to choose its answer. It
tests data flow, not model quality. These checks do not complete the reviewer
requested empirical ablation. Only a separately frozen and audited live
study can supply new latency evidence.
