# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.5.0](https://github.com/GoogleCloudPlatform/functions-framework-python/compare/v3.4.0...v3.5.0) (2023-11-28)


### Features

* initial typing of the public API ([#248](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/248)) ([45aed53](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/45aed538b5e39655318c7841457399fa3376ceaf))


### Bug Fixes

* don't exit on reload if there is a syntax error ([#214](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/214)) ([46780da](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/46780dac88c8dfe715babe89f792d08e9ca482e7))
* reduce gunicorn concurrency to at most 4 * maximum available cor… ([#259](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/259)) ([2e04cc2](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/2e04cc28ae028b8facc85dbdf738e2b8076dbbf7))


### Documentation

* Fix broken Flask Request link in README.md ([#286](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/286)) ([6b9e9b5](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/6b9e9b56f2f364e9a19fd434d88a0fbe22808515))

## [3.4.0](https://github.com/GoogleCloudPlatform/functions-framework-python/compare/v3.3.0...v3.4.0) (2023-05-24)


### Features

* configure security score card action ([#216](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/216)) ([7868dc1](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/7868dc110c048d3e1acf082faf36b75c3770e3f3))


### Bug Fixes

* streaming requests cannot access request data ([#245](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/245)) ([c492b04](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/c492b04e87a55194b7709e471b0ec3e2c630f288))

## [3.3.0](https://github.com/GoogleCloudPlatform/functions-framework-python/compare/v3.2.1...v3.3.0) (2022-12-16)


### Features

* Support strongly typed functions signature ([#208](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/208)) ([aa59a6b](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/aa59a6b6839820946dc72ceea7fd97b3dfd839c2))


### Bug Fixes

* remove DRY_RUN env var and --dry-run flag ([#210](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/210)) ([f013ab4](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/f013ab4e4c00acae827ad85e6e2ac5698859605f))

## [3.2.1](https://github.com/GoogleCloudPlatform/functions-framework-python/compare/v3.2.0...v3.2.1) (2022-11-09)


### Bug Fixes

* Remove the 10MB limit ([#205](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/205)) ([34b8083](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/34b8083c53d88d378718916cc2c20de7665150d4))

## [3.2.0](https://github.com/GoogleCloudPlatform/functions-framework-python/compare/v3.1.0...v3.2.0) (2022-08-11)


### Features

* Scale gunicorn server to serve 1000 concurrent requests ([#195](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/195)) ([91e2efa](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/91e2efa9356b120a07906023119219d99a6a0791))

## [3.1.0](https://github.com/GoogleCloudPlatform/functions-framework-python/compare/v3.0.0...v3.1.0) (2022-06-09)


### Features

* Add more details to MissingTargetException error ([#189](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/189)) ([b7055ed](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/b7055ed838523cda71bf71bc0149f33271e60ebc))
* allow for watchdog>=2.0.0 ([#186](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/186)) ([b4ed666](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/b4ed66673b3dd762c371f755c493a381c8241b50))


### Bug Fixes

* Add functools.wraps decorator ([#179](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/179)) ([f2285f9](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/f2285f96072d7ab8f00ada0d5f8c075e2b4ad364))
* Change gunicorn request line limit to unlimited ([#173](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/173)) ([6f4a360](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/6f4a3608634debe0833d0ef5cd769050b5fecb01))
* for issue [#170](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/170) gracefully handle pubsub messages without attributes in them ([#187](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/187)) ([a820fd4](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/a820fd4cdb4bef6cffe0ef68a2d03af922f13d7e))
* Support relative imports for submodules ([#169](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/169)) ([9046388](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/9046388fe8c32e897b83315863ee57ccf7d0e8df))


### Documentation

* update README to use declarative function signatures ([#171](https://github.com/GoogleCloudPlatform/functions-framework-python/issues/171)) ([efb0e84](https://github.com/GoogleCloudPlatform/functions-framework-python/commit/efb0e84d3f8ada6ac305b216baa6632570c38495))

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
