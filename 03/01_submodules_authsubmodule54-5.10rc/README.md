# Auth Perms Submodule

The module implements the registration, authentication and issuance of permissions for users.

## 1. Release info

### 5.10rc

## 2. Features

#### Removed socket functionality

#### Added Single-Sign-On functionality

#### Added enterprise features and [usage guide](release_info/enterpriseusageguide.md)

#### Added [settings sample](settings_sample.py)

## 3. Requirements

- [Python](https://www.python.org)>=3.9
- [Python requirements list](requirements_full_list.txt)
- [PostgreSQL](https://www.postgresql.org)>=9.6
- [PostgreSQL uuid-ossp](https://www.postgresql.org/docs/9.6/uuid-ossp.html)

## 4. License

- [License file](release_info/LICENSE)

## 5. Acceptance tests

- [Acceptance tests list](release_info/acceptancetests.md)

## 6. Documentation

- [API calls](release_info/api_calls.md)

## 7. Deploy

- Initialize local configuration file: `git submodule init`
- Fetch all data from repository: `git submodule update`
- Install requirements list: `pip install -r requirements.txt`
- Apply the migrations: `python manage.py migrate`
- Pass necessary data to local_settings.py
