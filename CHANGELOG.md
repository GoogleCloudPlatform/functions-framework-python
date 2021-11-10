# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.0.0] - 2021-11-10
### Fixed
- refactor: change declarative function signature from `cloudevent` to `cloud_event` ([#167])

## [2.4.0-beta.2] - 2021-11-01
### Fixed
- fix: remove debug statements

## [2.4.0-beta.1] - 2021-10-29
### Added
- feat: Support declarative function signatures: `http` and `cloudevent` ([#160])

## [2.3.0] - 2021-10-12
### Added
- feat: add support for Python 3.10 ([#151])
### Changed
- fix: update event conversion ([#154])
- fix: Move backwards-compatible logic before function source load ([#152])
- fix: Add a DummyErrorHandler ([#137])

## [2.2.1] - 2021-06-01
### Changed
- Update GCF Python 3.7 backwards-compatible logging ([#131])

## [2.2.0] - 2021-05-24
### Added
- Relax constraint to `flask<3.0` and `click<9.0` ([#129])

## [2.1.3] - 2021-04-23
### Changed
- Change gunicorn loglevel to error ([#122])

### Added
- Add support for background to CloudEvent conversion ([#116])

## [2.1.2] - 2021-02-23
### Added
- Add crash header to 500 responses ([#114])

## [2.1.1] - 2021-02-17
### Fixed
- Add backwards-compatible logging for GCF Python 3.7 ([#107])
- Document `--dry-run` flag ([#105])

## [2.1.0] - 2020-12-23
### Added
- Support Python 3.9

### Fixed
- Execute the source module w/in the app context ([#76])

## [2.0.0] - 2020-07-01
### Added
- Support `cloudevent` signature type ([#55], [#56])

## [1.6.0] - 2020-08-19
### Changed
- Add legacy GCF Python 3.7 behavior ([#77])

### Added
- Improve documentation around Dockerfiles ([#70])

## [1.5.0] - 2020-07-06
### Changed
- Framework will consume entire request before responding ([#66])

## [1.4.4] - 2020-06-19
### Fixed
- Improve module loading ([#61])

## [1.4.3] - 2020-05-14
### Fixed
- Load the source file into the correct module name ([#49])

## [1.4.2] - 2020-05-13
### Fixed
- Fix handling of `--debug` flag when gunicorn is not present ([#44])

## [1.4.1] - 2020-05-07
### Fixed
- Fix Windows support ([#38])

## [1.4.0] - 2020-05-06
### Changed
- Use gunicorn as a production HTTP server

## [1.3.0] - 2020-04-13
### Added
- Add support for running `python -m functions_framework` ([#31])

### Changed
- Move `functions_framework.cli.cli` to `functions_framework._cli._cli`
- Adjust path handling for robots.txt and favicon.ico ([#33])

## [1.2.0] - 2020-02-20
### Added
- Add support for `--host` flag ([#20])

## [1.1.1] - 2020-02-06
### Added
- Add support for `--dry-run` flag ([#14])

### Changed
- Make `--debug` a flag instead of a boolean option

### Fixed
- Better support for CloudEvent functions and error handling

## [1.0.1] - 2020-01-30
### Added
- Add Cloud Run Button ([#1])
- Add README badges ([#2])
- Add `debug` flag documentation ([#7])
- Add `watchdog` dependency ([#8])

### Fixed
- Fix `--signature-type` typo ([#4])
- Fix `install_requires` typo ([#12])

## [1.0.0] - 2020-01-09
### Added
- Initial release

[Unreleased]: https://github.com/GoogleCloudPlatform/functions-framework-python/compare/v3.0.0...HEAD
[3.0.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v3.0.0
[2.4.0-beta.2]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.4.0-beta.2
[2.4.0-beta.1]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.4.0-beta.1
[2.3.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.3.0
[2.2.1]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.2.1
[2.2.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.2.0
[2.1.3]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.1.3
[2.1.2]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.1.2
[2.1.1]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.1.1
[2.1.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.1.0
[2.0.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v2.0.0
[1.6.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.6.0
[1.5.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.5.0
[1.4.4]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.4.4
[1.4.3]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.4.3
[1.4.2]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.4.2
[1.4.1]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.4.1
[1.4.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.4.0
[1.3.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.3.0
[1.3.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.3.0
[1.2.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.2.0
[1.1.1]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.1.1
[1.0.1]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.0.1
[1.0.0]: https://github.com/GoogleCloudPlatform/functions-framework-python/releases/tag/v1.0.0

[#167]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/167
[#160]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/160
[#154]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/154
[#152]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/152
[#151]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/151
[#137]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/137
[#131]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/131
[#129]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/129
[#122]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/122
[#116]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/116
[#114]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/114
[#107]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/107
[#105]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/105
[#77]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/77
[#76]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/76
[#70]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/70
[#66]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/66
[#61]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/61
[#56]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/56
[#55]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/55
[#49]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/49
[#44]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/44
[#38]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/38
[#33]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/33
[#31]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/31
[#20]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/20
[#14]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/14
[#12]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/12
[#8]:  https://github.com/GoogleCloudPlatform/functions-framework-python/pull/8
[#7]:  https://github.com/GoogleCloudPlatform/functions-framework-python/pull/7
[#4]:  https://github.com/GoogleCloudPlatform/functions-framework-python/pull/4
[#2]:  https://github.com/GoogleCloudPlatform/functions-framework-python/pull/2
[#1]:  https://github.com/GoogleCloudPlatform/functions-framework-python/pull/1
