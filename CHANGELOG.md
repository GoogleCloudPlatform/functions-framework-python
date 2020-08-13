# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/GoogleCloudPlatform/functions-framework-python/compare/v1.5.0...HEAD
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

[#66]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/66
[#61]: https://github.com/GoogleCloudPlatform/functions-framework-python/pull/61
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
