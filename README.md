# Paymaster
[![Maintainability](https://api.codeclimate.com/v1/badges/4481ecf0fcbcab01225b/maintainability)](https://codeclimate.com/github/IDilettant/paymaster/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/4481ecf0fcbcab01225b/test_coverage)](https://codeclimate.com/github/IDilettant/paymaster/test_coverage)
![Actions Status](https://github.com/IDilettant/paymaster/actions/workflows/tests_and_linters.yaml/badge.svg)
[![Updates](https://pyup.io/repos/github/IDilettant/paymaster/shield.svg)](https://pyup.io/repos/github/IDilettant/paymaster/)
[![Python 3](https://pyup.io/repos/github/IDilettant/paymaster/python-3-shield.svg)](https://pyup.io/repos/github/IDilettant/paymaster/)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)


## Description
Paymaster is a completely asynchronous service that provides the ability to create a user wallet with a cash balance and
interacting with it as part of the microservice architecture using the REST API request structure

## Features
- Create user account
- Delete user account
- Change user balance: replenishment and withdrawal
- Transfer funds between user accounts
- Get user account balance with the ability to convert the balance value into an optionally selectable currency
- Get user account transactions history with the ability to sort by date and/or total and with paging pagination
- Update currencies rates in background auto mode

A more detailed description of the documentation can be found in the automatically generated [openapi file](https://github.com/IDilettant/paymaster/blob/main/doc/openapi.yml).
Or in interactive documentation mode after deploying the application using the link like "http://{hostname}/openapi.json"

## Usage
Copy repository to system.
```bash
$ git clone https://github.com/IDilettant/paymaster.git
```

### Configuration
Check `.env` file and tweak configs if you need.
| env | purpose | example | 
| --- | ------- | ------ |
| TRIGGER_TIME | time for updating currency rates table | `00:00` | 
| API_KEY | key for currency rates source authentication | `f68e13y36190f4928a4cf279` (https://v6.exchangerate-api.com) | 
| DSN | PostgreSQL connection url | `postgresql://user:password@tcp(localhost:5432)/treasury` |

## Deploy
Docker must be installed. Just execute from paymaster root directory:
```bash
$ make compose
```
