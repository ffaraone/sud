# SUD

![pyversions](https://img.shields.io/pypi/pyversions/sud.svg) [![PyPi Status](https://img.shields.io/pypi/v/sud.svg)](https://pypi.org/project/sud/) [![Test SUD](https://github.com/ffaraone/sud/actions/workflows/test.yml/badge.svg)](https://github.com/ffaraone/sud/actions/workflows/test.yml) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=sud&metric=alert_status)](https://sonarcloud.io/dashboard?id=sud) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=sud&metric=coverage)](https://sonarcloud.io/dashboard?id=sud) [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=sud&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=sud)


   > Sud, Sud nuie simme r'o Sud,  
   > nuie simme curt' e nire,  
   > nuie simme buone pe' canta  
   > e faticamm' a faticà  
   >  
   > [(Pietra Motecorvino)](https://en.wikipedia.org/wiki/Pietra_Montecorvino)


`SUD` (Scaleway Update Dns) is a small utility to add/update an "A" record in a DNS zone
managed by [Scaleway](https://scaleway.com).


## Install via Pip


```bash
$ pip install sud
```

## Configure

By default SUD search for a configuration file in `/etc/sud/sud-config.yml`.

A minimal configuration file need the hostname you want to add/update and
the API secret needed to talk with the Scaleway API like in the following example:

```yaml
hostname: myname.mydomain.com
api_secret: 1279bde5-150f-4113-ba37-c4c58e1dfece
```

It is possible to change the frequency with which SUD checks if an IP change has occurred
as well as receiving a telegram notification with the new IP address:


```yaml
hostname: myname.mydomain.com
api_secret: 1279bde5-150f-4113-ba37-c4c58e1dfece
frequency: 600 # each 10 minutes
notifications:
  telegram:
    token: 0987654321:tdCkfKaJooaIWMvebbKYeliLfLhlhvpKAB
    chat_id: -1234567890
```

## Run

To run sud just type:

```bash
$ sud run
```

if you want to place your config file somewhere else you can use:

```bash
$ sud -c /path/to/config.yml run
```

## Help

You can get help just typing:

```bash
$ sud --help
```

## License

`SUD` is released under the [Apache License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
