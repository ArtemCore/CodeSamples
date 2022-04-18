## Release policy

Ecosystem54 service releases are numbered with 4 digits. (Except submodule and auth service)

For example service release 5.7.3.4. We decrypt:
- 5 - compatibility diagram. Indicates the AP54 protocol version.
- 7 - the version of the submodule that is used in the release
- 3 - auth version with which this service release should be guaranteed to work
- 4 - the actual version of the release

That is, for release of version 5.7.3.4, the 5th version of the protocol, 7th submodule and 3rd auth service are required. This should ensure performance.

For release candidates, add at the end of the rc service. For example 5.7.3.4rc.

There are no other restrictions.

Submodule releases consist of 2 digits:
For example 5.7

Auth releases consist of 3 digits - 5.7.3

The rest of the service releases are designated with 4 digits.